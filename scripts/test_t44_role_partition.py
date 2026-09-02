#!/usr/bin/env python3
"""T-44 迴歸測試：role-aware 候選子集——分區完整性＋`role=None` 逐位元等價。

依 output/clip_treatment/PLAN_T44.md §3 設計。全部用合成資料與樁函式，
不下載、不跑真模型（不需要 CLIP／SegFormer 權重）：
1. 分區完整性檢查——`ROLE_MATERIAL_CANDIDATES` 與
   `data/material_ground_truth.json`（T-39 重對映後）程式化統計出的
   「每個角色實際出現過的材質」逐一相符，不多不少。
2. `role=None`／不帶 `role` 參數 兩種呼叫方式，餵給 CLIP 的候選提示詞字典
   （送進 `clip_processor` 的 `text=` 內容）逐字串相同——不是「最後材質 id
   碰巧一樣」，是模型輸入本身相同。
3. `analyse_image(role_aware=False)`（預設值）對
   `classify_region_material()` 的呼叫，字面上**不帶 `role` 這個關鍵字**，
   證明是同一行程式碼，不是傳了 `role=None` 才「碰巧」等價。
4. 三個角色個別呼叫時，候選集都含全部 4 個 `CLIP_OOD_PROMPTS`。
5. 既有 12 條 `CLIP_MATERIAL_PROMPTS` 字串逐位元不變（T-44 範圍紅線：
   本卡只動「哪些候選參賽」，不動「怎麼描述」）。

跑法：`python scripts/test_t44_role_partition.py`；全部通過 exit 0，
任一失敗 exit 1。

**對舊碼（T-44 之前）必然 fail**：舊碼 `classify_region_material()` 沒有
`role` 參數、`analyse_image()` 沒有 `role_aware` 參數，【2】【3】【4】
呼叫時會直接 `TypeError`；`ROLE_MATERIAL_CANDIDATES` 不存在，【1】會
`AttributeError`。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import surfaces  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH_PATH = REPO_ROOT / "data" / "material_ground_truth.json"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


# ------------------------------------------------------------------
# 既有 12 條 CLIP_MATERIAL_PROMPTS 字串（逐位元寫死，來源同
# test_t39_materials_invariant.py FROZEN_PROMPTS，T-44 範圍紅線：一字不動）
# ------------------------------------------------------------------
FROZEN_PROMPTS = {
    "concrete": "a smooth poured concrete surface",
    "brick": "a bare unglazed brick surface",
    "wood_panel": "a wooden panel or wood plank surface",
    "gypsum_board": "a painted plasterboard drywall surface",
    "glass": "a pane of clear glass or a window",
    "marble": "a polished marble or ceramic tile surface",
    "carpet": "a thick carpet or textile floor covering",
    "curtain_fabric": "a heavy fabric curtain or drape",
    "acoustic_panel": "a fibrous acoustic absorption panel",
    "audience_seating": "rows of upholstered seats with an audience",
    "grass_soil": "natural grass or bare soil ground",
    "generic_wall": "a plain smooth plastered wall",
}

ROLE_OF_FACE = {
    "floor": "floor", "ceiling": "ceiling",
    "north": "wall", "east": "wall", "south": "wall", "west": "wall",
}


# ------------------------------------------------------------------
# 【1】分區完整性檢查
# ------------------------------------------------------------------

def compute_reachable_materials_per_role() -> dict[str, set[str]]:
    """對 ground truth 逐面統計每個角色實際出現過的材質（非 unknown），
    只保留在 12 條 CLIP_MATERIAL_PROMPTS 內的（不在 12 條內的材質——
    T-39 未採用的候選——在任何分區下都判不出來，不算分區表的責任）。
    """
    gt = json.loads(GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    twelve = set(FROZEN_PROMPTS.keys())
    reachable: dict[str, set[str]] = {"floor": set(), "ceiling": set(), "wall": set()}
    for _photo, faces in gt["photos"].items():
        for face, entry in faces.items():
            mid = entry["material_id"]
            if mid == "unknown" or mid not in twelve:
                continue
            reachable[ROLE_OF_FACE[face]].add(mid)
    return reachable


def test_partition_completeness() -> None:
    print("【1】分區完整性：ROLE_MATERIAL_CANDIDATES 涵蓋每個角色 ground truth 實際出現的所有材質")
    # 卡片原文（分區完整性鐵則）規定的是下限（子集必須「涵蓋」該角色 ground
    # truth 出現過的材質），不是上限——PLAN_T44.md §7（round16）刻意保留
    # 多餘候選（floor 加回 generic_wall／wall 全還原）來稀釋搶答者的 softmax
    # 佔比，這是完整性鐵則允許的合法調整，所以檢查用 issubset（⊆）而不是
    # 相等；「只含 12 條已有材質、不新增候選字串」才是必須逐位元卡死的上限。
    reachable = compute_reachable_materials_per_role()
    for role in ("floor", "ceiling", "wall"):
        candidate_set = set(surfaces.ROLE_MATERIAL_CANDIDATES[role])
        check(
            f"{role} 候選子集涵蓋（⊇）ground truth reachable 材質集合（完整性鐵則下限）",
            reachable[role] <= candidate_set,
            f"候選={sorted(candidate_set)}，reachable={sorted(reachable[role])}，"
            f"缺漏={sorted(reachable[role] - candidate_set) or '無'}",
        )
        check(
            f"{role} 候選子集只含 CLIP_MATERIAL_PROMPTS 已有的材質（不新增候選字串，上限）",
            candidate_set <= set(surfaces.CLIP_MATERIAL_PROMPTS.keys()),
            f"候選={sorted(candidate_set)}",
        )


# ------------------------------------------------------------------
# 樁 CLIP：不下載模型，用真 torch 張量跑 softmax，只記錄送進去的 prompt 字串
# ------------------------------------------------------------------

class _FakeCLIPProcessor:
    def __init__(self) -> None:
        self.last_text: list[str] | None = None

    def __call__(self, text, images, return_tensors, padding):  # noqa: ANN001
        self.last_text = list(text)
        return {"n": len(text)}


class _FakeCLIPModel:
    def __call__(self, **inputs):  # noqa: ANN003
        n = inputs["n"]

        class _Out:
            logits_per_image = torch.zeros((1, n))

        return _Out()


def _make_mask() -> np.ndarray:
    mask = np.zeros((10, 10), dtype=bool)
    mask[2:8, 2:8] = True
    return mask


def _make_img() -> Image.Image:
    return Image.new("RGB", (10, 10), color=(128, 128, 128))


# ------------------------------------------------------------------
# 【2】role=None 與「不帶 role 參數」兩種呼叫方式，送進 CLIP 的候選字串逐字相同
# ------------------------------------------------------------------

def test_role_none_matches_no_role_kwarg() -> None:
    print("【2】classify_region_material(role=None) 與不帶 role 參數：送進 CLIP 的候選字串逐字相同")
    img, mask = _make_img(), _make_mask()

    proc_no_role = _FakeCLIPProcessor()
    surfaces.classify_region_material(img, mask, proc_no_role, _FakeCLIPModel(), 0.4)

    proc_role_none = _FakeCLIPProcessor()
    surfaces.classify_region_material(img, mask, proc_role_none, _FakeCLIPModel(), 0.4, role=None)

    check(
        "兩種呼叫方式送進 CLIP 的 text= 列表逐字相同",
        proc_no_role.last_text == proc_role_none.last_text,
        f"不帶 role={proc_no_role.last_text}\n      role=None ={proc_role_none.last_text}",
    )
    expected = list(surfaces.CLIP_MATERIAL_PROMPTS.values()) + list(surfaces.CLIP_OOD_PROMPTS.values())
    check(
        "候選字串＝全域 12 種材質 ＋ 4 個 OOD（T-44 之前唯一行為）",
        proc_no_role.last_text == expected,
        f"實際={proc_no_role.last_text}",
    )


# ------------------------------------------------------------------
# 【3】analyse_image(role_aware=False) 對 classify_region_material 的呼叫
#      字面上不帶 role 關鍵字（不是傳 role=None 才「碰巧」等價）
# ------------------------------------------------------------------

def _fake_segment_roles(img, processor, model):  # noqa: ANN001
    labelmap = np.zeros((20, 20), dtype=np.int32)
    labelmap[:7, :] = 0    # wall
    labelmap[7:14, :] = 3  # floor
    labelmap[14:, :] = 5   # ceiling
    total = labelmap.size
    ids, counts = np.unique(labelmap, return_counts=True)
    ratios = {int(i): float(c) / total for i, c in zip(ids, counts)}
    return labelmap, ratios


def test_analyse_image_default_calls_without_role_kwarg() -> None:
    print("【3】analyse_image(role_aware=False，預設值)：呼叫 classify_region_material 字面上不帶 role")
    calls: list[dict] = []

    def _recording_classify(*args, **kwargs):
        calls.append({"n_positional": len(args), "kwargs": dict(kwargs)})
        return "gypsum_board", 0.9, [("gypsum_board", 0.9)], "clip"

    real_segment_roles = surfaces.segment_roles
    real_classify = surfaces.classify_region_material
    surfaces.segment_roles = _fake_segment_roles
    surfaces.classify_region_material = _recording_classify
    try:
        img = Image.new("RGB", (20, 20))
        surfaces.analyse_image(img, seg=("stub_proc", "stub_model"), clip=("stub_proc", "stub_model"))
    finally:
        surfaces.segment_roles = real_segment_roles
        surfaces.classify_region_material = real_classify

    check("預設呼叫命中 floor/ceiling/wall 三個角色", len(calls) == 3, f"實際呼叫次數 {len(calls)}")
    for c in calls:
        check(
            f"呼叫式不帶 role 關鍵字（kwargs={c['kwargs']}）",
            "role" not in c["kwargs"],
            f"kwargs={c['kwargs']}",
        )
        check(
            "呼叫式維持 5 個位置參數（img/mask/clip_processor/clip_model/threshold）",
            c["n_positional"] == 5,
            f"n_positional={c['n_positional']}",
        )


def test_analyse_image_role_aware_true_passes_role() -> None:
    print("【3b】analyse_image(role_aware=True)：呼叫 classify_region_material 帶正確的 role")
    calls: list[dict] = []

    def _recording_classify(*args, **kwargs):
        calls.append(dict(kwargs))
        return "gypsum_board", 0.9, [("gypsum_board", 0.9)], "clip"

    real_segment_roles = surfaces.segment_roles
    real_classify = surfaces.classify_region_material
    surfaces.segment_roles = _fake_segment_roles
    surfaces.classify_region_material = _recording_classify
    try:
        img = Image.new("RGB", (20, 20))
        surfaces.analyse_image(
            img, seg=("stub_proc", "stub_model"), clip=("stub_proc", "stub_model"), role_aware=True
        )
    finally:
        surfaces.segment_roles = real_segment_roles
        surfaces.classify_region_material = real_classify

    roles_passed = {c.get("role") for c in calls}
    check(
        "role_aware=True 時三次呼叫各帶正確角色",
        roles_passed == {"floor", "ceiling", "wall"},
        f"實際={roles_passed}",
    )


# ------------------------------------------------------------------
# 【4】三個角色個別呼叫，候選集都含全部 4 個 OOD 候選（不得被分掉）
# ------------------------------------------------------------------

def test_ood_prompts_kept_for_every_role() -> None:
    print("【4】三個角色分別呼叫，候選集都含全部 4 個 CLIP_OOD_PROMPTS")
    img, mask = _make_img(), _make_mask()
    for role in ("floor", "ceiling", "wall"):
        proc = _FakeCLIPProcessor()
        surfaces.classify_region_material(img, mask, proc, _FakeCLIPModel(), 0.4, role=role)
        ood_values = set(surfaces.CLIP_OOD_PROMPTS.values())
        sent = set(proc.last_text or [])
        check(
            f"role={role}：候選字串含全部 4 個 OOD",
            ood_values <= sent,
            f"缺少 {ood_values - sent}" if not (ood_values <= sent) else "OK",
        )
        expected_material_count = len(surfaces.ROLE_MATERIAL_CANDIDATES[role])
        check(
            f"role={role}：候選字串總數 == 子集材質數 + 4 個 OOD",
            len(proc.last_text or []) == expected_material_count + 4,
            f"實際 {len(proc.last_text or [])}，預期 {expected_material_count + 4}",
        )


# ------------------------------------------------------------------
# 【5】既有 12 條 CLIP_MATERIAL_PROMPTS 字串逐位元不變
# ------------------------------------------------------------------

def test_existing_prompts_unchanged() -> None:
    print("【5】既有 12 條 CLIP_MATERIAL_PROMPTS 字串逐位元不變（T-44 範圍紅線）")
    for mid, expected in FROZEN_PROMPTS.items():
        actual = surfaces.CLIP_MATERIAL_PROMPTS.get(mid)
        check(f"CLIP_MATERIAL_PROMPTS['{mid}']", actual == expected, f"{actual!r} == {expected!r}")
    check(
        "CLIP_MATERIAL_PROMPTS 恰好 12 條（本卡不新增候選字串）",
        len(surfaces.CLIP_MATERIAL_PROMPTS) == 12,
        f"實際 {len(surfaces.CLIP_MATERIAL_PROMPTS)} 條",
    )


def main() -> int:
    test_partition_completeness()
    test_role_none_matches_no_role_kwarg()
    test_analyse_image_default_calls_without_role_kwarg()
    test_analyse_image_role_aware_true_passes_role()
    test_ood_prompts_kept_for_every_role()
    test_existing_prompts_unchanged()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-44 role-aware 分區完整性與 role=None 逐位元等價測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
