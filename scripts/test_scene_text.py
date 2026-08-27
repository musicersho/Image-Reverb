#!/usr/bin/env python3
"""T-20 迴歸測試：文字場景解析器（F-16）。

跑法：`python scripts/test_scene_text.py`（純資料與公式，不依賴模型下載，
任何 clone 可重跑；全部通過 exit 0，任一失敗 exit 1）。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb.acoustics import compute_acoustics  # noqa: E402
from src.image_reverb.materials import get_material, load_materials  # noqa: E402
from src.image_reverb.scene_text import (  # noqa: E402
    load_scene_presets,
    parse_scene_text,
)

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def main() -> int:
    presets = load_scene_presets()
    materials = load_materials()

    # ---------- 1. preset 庫健全性 ----------
    print("【1】preset 庫健全性")
    n = len(presets["presets"])
    check("preset 數量 ≥ 10", n >= 10, f"{n} 個")

    all_ok = True
    uniform_violations = []
    for p in presets["presets"]:
        for name, mid in p["surfaces"].items():
            try:
                get_material(mid, materials)
            except KeyError:
                all_ok = False
                print(f"      preset '{p['id']}' 的 {name}={mid} 不在 materials.json")
        ids = set(p["surfaces"].values())
        # 約束 A：除了「物理上真的六面同材質」的空間（樓梯間/洞窟），不得全域單一材質
        if len(ids) == 1 and p["id"] not in ("stairwell", "cave"):
            uniform_violations.append(p["id"])
    check("全部材質 id 都存在於 materials.json", all_ok, f"{n} 個 preset 檢查完")
    check(
        "逐表面材質（約束 A；樓梯間/洞窟為物理豁免）",
        not uniform_violations,
        "無違例" if not uniform_violations else f"違例：{uniform_violations}",
    )

    # ---------- 2. 三個代表描述 ----------
    print("【2】代表描述解析")
    bath = parse_scene_text("浴室", presets, materials)
    check(
        "「浴室」→ bathroom preset",
        bath.preset_id == "bathroom" and bath.estimate.dims_source == "text_description",
        f"preset={bath.preset_id}, dims={bath.estimate.length_m}×{bath.estimate.width_m}×{bath.estimate.height_m}",
    )

    carpet_room = parse_scene_text("4x3x2.5 的房間，地板鋪地毯", presets, materials)
    ok = (
        carpet_room.estimate.length_m == 4.0
        and carpet_room.estimate.width_m == 3.0
        and carpet_room.estimate.height_m == 2.5
        and carpet_room.surfaces.floor == "carpet"
        and carpet_room.estimate.confidence == "high"
    )
    check(
        "「4x3x2.5 的房間，地板鋪地毯」→ 顯式尺寸＋地毯覆寫＋confidence high",
        ok,
        f"dims=({carpet_room.estimate.length_m},{carpet_room.estimate.width_m},"
        f"{carpet_room.estimate.height_m}), floor={carpet_room.surfaces.floor}, "
        f"confidence={carpet_room.estimate.confidence}",
    )

    church = parse_scene_text("大教堂", presets, materials)
    check("「大教堂」→ church preset（不被「大」誤觸放大規則）",
          church.preset_id == "church" and church.estimate.length_m == 25.0,
          f"preset={church.preset_id}, length={church.estimate.length_m}")

    # ---------- 3. 聲學合理性（教堂殘響應明顯長於浴室）----------
    print("【3】聲學合理性")
    ac_bath = compute_acoustics(bath.estimate, bath.surfaces, materials)
    ac_church = compute_acoustics(church.estimate, church.surfaces, materials)
    ratio = ac_church.rt60_mid_sabine / ac_bath.rt60_mid_sabine
    check("教堂 RT60(mid) > 浴室 × 3", ratio > 3.0,
          f"教堂 {ac_church.rt60_mid_sabine:.2f}s vs 浴室 {ac_bath.rt60_mid_sabine:.2f}s（{ratio:.1f} 倍）")

    ac_carpet = compute_acoustics(carpet_room.estimate, carpet_room.surfaces, materials)
    err = abs(ac_carpet.rt60_bands_sabine[0] - 0.348) / 0.348
    check("文字地毯房 125Hz Sabine ≈ T-14 地毯房 0.348s（同輸入同公式）",
          err < 0.10, f"{ac_carpet.rt60_bands_sabine[0]:.3f}s（差 {err*100:.1f}%）")

    # ---------- 4. 拒絕與報錯（禁止安靜 fallback）----------
    print("【4】拒絕與報錯")
    try:
        parse_scene_text("asdf qwerty", presets, materials)
        check("亂打的描述 → 報錯", False, "沒有報錯（安靜 fallback！）")
    except ValueError as e:
        check("亂打的描述 → 報錯＋列出可用場景", "可用的場景" in str(e), "訊息含場景清單")

    try:
        parse_scene_text("車內聽音樂", presets, materials)
        check("「車內」→ 明確拒絕", False, "沒有報錯（安靜輸出了一個房間！）")
    except ValueError as e:
        check("「車內」→ 明確拒絕並導向照片＋手動覆寫", "非建築空間" in str(e), "訊息含拒絕原因")

    try:
        parse_scene_text("", presets, materials)
        check("空字串 → 報錯", False, "沒有報錯")
    except ValueError:
        check("空字串 → 報錯", True, "有報錯")

    try:
        parse_scene_text("0x3x2.5 的房間", presets, materials)
        check("零尺寸 → 報錯", False, "沒有報錯（T-13 Opus 建議 1 的缺口型態）")
    except ValueError:
        check("零尺寸 → 報錯（不安靜跑完）", True, "有報錯")

    # ---------- 5. 修飾詞與歧義警示 ----------
    print("【5】修飾詞與歧義警示")
    big = parse_scene_text("很大的教室", presets, materials)
    check("「很大的教室」→ 教室 ×1.3", big.preset_id == "classroom" and abs(big.estimate.length_m - 9.0 * 1.3) < 1e-9,
          f"length={big.estimate.length_m}")

    multi = parse_scene_text("體育館旁的走廊", presets, materials)
    check("多場景命中 → 有歧義警示（不安靜選）",
          any("同時命中" in w for w in multi.surfaces.warnings),
          f"採用 {multi.preset_name_zh}，警示 {len(multi.surfaces.warnings)} 條")

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-20 文字場景解析測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
