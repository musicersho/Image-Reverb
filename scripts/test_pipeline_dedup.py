#!/usr/bin/env python3
"""T-41 迴歸測試：透視照 SegFormer 重複載入去重（插卡 2/4）。

背景（外部掃描 P1，已對碼核實）：`run_photo()` 對一張透視照會載入 SegFormer
兩次、完整推論兩次——`surfaces_from_preprocess()`（`surfaces.py:284`）已跑過
一次 `_load_segmenter()`＋`segment_roles()`，並把結果存進
`detail["class_ratios"]["single"]`；`pipeline.py` 的 scene_cues 段舊碼又對
**同一張** `summary["cropped"]` 重新跑一次，只為取 `floor_pixel_ratio`／
`person_pixel_ratio`。修法：scene_cues 段直接重用 `detail["class_ratios"]["single"]`，
刪掉第二次 `_load_segmenter()`／`segment_roles()`。

本測試分兩部分：

  A. **呼叫次數**：樁 `surfaces._load_segmenter`，用一張真實透視照走完
     `run_photo()`，斷言全程恰好呼叫 1 次。樁是「計數後轉呼叫真本體」的
     wrapper（不樁掉推論本身），確保斷言的是「真的只跑一次推論」而不是
     「跳過了推論所以測不出差異」（卡片紅旗）。
  B. **scene_cues 零漂移直證**（陷阱 1：`analysis.json` 不落盤 scene_cues，
     光比對 JSON 證明不了數值沒變）：對 13 張基線集合裡目前判定為透視照的
     每一張，各算一次舊路（`segment_roles(Image.open(cropped)..., *_load_segmenter())`）
     與新路（`surfaces_from_preprocess()` 回傳的 `detail["class_ratios"]["single"]`），
     斷言 `floor_pixel_ratio`／`person_pixel_ratio`／`out_of_domain`／
     `out_of_domain_label` 四鍵逐值 bit-identical（`out_of_domain` 兩鍵本來就不
     經 ratios，理論上不可能變，一併驗證只是誠實地把四鍵都覆蓋到）。

跑法：`python scripts/test_pipeline_dedup.py`；全部通過 exit 0，任一失敗 exit 1。
需要真實跑 SegFormer／CLIP 推論（13 張裡的 9 張透視照 × 2 條路），沒有 GPU 也能跑
（本專案模型走 CPU/MPS），但會花數分鐘。

診斷力（舊碼必須 fail 的最小重現）：本測試的部分 A 對修正前的 `pipeline.py`
（`_load_segmenter` 呼叫次數為 2）必定 fail；已用 `git worktree` 對舊碼實測，
原始輸出見交接筆記。
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from PIL import Image  # noqa: E402

from src.image_reverb import pipeline  # noqa: E402
from src.image_reverb import surfaces as surfaces_mod  # noqa: E402
from src.image_reverb.preprocess import preprocess_image  # noqa: E402

from t36_clip_accuracy import GATE_ITEMS  # noqa: E402  （唯讀引用，13 張清單）

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


# ------------------------------------------------------------------
# 部分 A：一張真實透視照走完 run_photo()，SegFormer 恰好載入 1 次
# ------------------------------------------------------------------

def part_a_call_count() -> None:
    print("【A】一張真實透視照走完 run_photo()，斷言 _load_segmenter 恰好呼叫 1 次")

    src_photo = REPO_ROOT / "assets" / "photos" / "bathroom_tiled.png"
    if not src_photo.is_file():
        check("找到測試素材", False, f"缺少 {src_photo}")
        return

    call_count = {"n": 0}
    real_load_segmenter = surfaces_mod._load_segmenter

    def counting_load_segmenter():
        call_count["n"] += 1
        return real_load_segmenter()

    with tempfile.TemporaryDirectory() as tmp:
        # 用獨立 stem 複製一份，避免跟 output/bathroom_tiled/ 的既有正式輸出撞名。
        test_photo = Path(tmp) / "_test_t41_dedup_photo.png"
        shutil.copyfile(src_photo, test_photo)
        out_dir = pipeline.OUTPUT_ROOT / test_photo.stem
        preprocess_out_dir = surfaces_mod.config.OUTPUT_DIR / test_photo.stem
        for d in (out_dir, preprocess_out_dir):
            if d.exists():
                shutil.rmtree(d)

        surfaces_mod._load_segmenter = counting_load_segmenter
        try:
            rc = pipeline.run_photo(
                str(test_photo),
                override_dims="4x3x2.5",  # 跳過深度模型，本卡不測幾何、只測分割去重
                no_viz=True,
                force_low_confidence=True,  # 確保不被 gate 擋下，走完整段材質＋scene_cues
            )
        finally:
            surfaces_mod._load_segmenter = real_load_segmenter
            for d in (out_dir, preprocess_out_dir):
                if d.exists():
                    shutil.rmtree(d)

    check("run_photo() 正常結束（exit 0）", rc == 0, f"rc={rc}")
    check(
        "_load_segmenter 全程恰好呼叫 1 次（舊碼是 2 次：surfaces_from_preprocess 一次＋"
        "scene_cues 段重複一次）",
        call_count["n"] == 1,
        f"count={call_count['n']}",
    )


# ------------------------------------------------------------------
# 部分 B：scene_cues 新舊路逐值 bit-identical（陷阱 1 直證）
# ------------------------------------------------------------------

def _build_scene_cues(ratios: dict[int, float], detail: dict) -> dict:
    """複製 pipeline.py 的 scene_cues 組裝公式，供新舊路各建一份比對用。"""
    ood = [
        v
        for v in detail["views"].get("single", {}).values()
        if v.get("method") == "out_of_domain"
    ]
    return {
        "floor_pixel_ratio": ratios.get(3, 0.0) + ratios.get(28, 0.0),
        "person_pixel_ratio": ratios.get(12, 0.0),
        "out_of_domain": bool(ood),
        "out_of_domain_label": (
            ood[0]["top3"][0][0].lstrip("_") if ood and ood[0].get("top3") else ""
        ),
    }


def part_b_scene_cues_dual_path() -> None:
    print("【B】13 張基線集合裡的每一張透視照：新舊路 scene_cues 四鍵逐值比對")

    from src.image_reverb.surfaces import _load_segmenter, segment_roles, surfaces_from_preprocess

    seg = _load_segmenter()  # 舊路共用同一個已載入模型（重複載入不影響推論結果，只省時間）

    with tempfile.TemporaryDirectory() as tmp:
        tested = 0
        for item in GATE_ITEMS:
            name = item["name"]
            photo_path = REPO_ROOT / item["photo"]
            if not photo_path.is_file():
                check(f"{name}: 找到素材", False, f"缺少 {photo_path}")
                continue

            summary = preprocess_image(photo_path, output_dir=Path(tmp) / name)
            if summary["is_equirect"]:
                continue  # 環景路徑本來就不算 scene_cues（卡片明文不得順手改）
            tested += 1

            # 新路：surfaces_from_preprocess() 內部只跑一次 segment_roles()，
            # 本測試直接讀它回傳的 detail["class_ratios"]["single"]（本卡改動後
            # pipeline.py 實際使用的值）。
            _surf, detail = surfaces_from_preprocess(summary)
            new_ratios = detail["class_ratios"]["single"]

            # 舊路：pipeline.py 修正前的做法，對同一張 cropped 圖重新開檔＋重新推論。
            img = Image.open(summary["cropped"]).convert("RGB")
            _, old_ratios = segment_roles(img, *seg)

            check(
                f"{name}: class_ratios 全 dict 逐值 bit-identical",
                old_ratios == new_ratios,
                f"old={old_ratios} new={new_ratios}" if old_ratios != new_ratios else "相同",
            )

            old_cues = _build_scene_cues(old_ratios, detail)
            new_cues = _build_scene_cues(new_ratios, detail)
            for key in ("floor_pixel_ratio", "person_pixel_ratio", "out_of_domain", "out_of_domain_label"):
                check(
                    f"{name}: scene_cues.{key} bit-identical",
                    old_cues[key] == new_cues[key],
                    f"old={old_cues[key]!r} new={new_cues[key]!r}",
                )

        check("至少測到一張透視照（否則本部分是空驗證）", tested > 0, f"tested={tested}")


def main() -> int:
    part_a_call_count()
    print()
    # --part-a-only：鐵則 5 舊碼最小重現只需要碰 pipeline.py 的部分 A（呼叫次數）；
    # 部分 B 只呼叫 surfaces.py／preprocess.py 的既有函式，不經過本卡改動的
    # pipeline.py scene_cues 段，對舊碼跑一樣會過，不是有效的舊碼 fail 重現，
    # 略過可省下重複的 9 張真實推論耗時。
    if "--part-a-only" not in sys.argv:
        part_b_scene_cues_dual_path()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-41 SegFormer 重複載入去重測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
