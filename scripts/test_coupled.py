#!/usr/bin/env python3
"""T-21 迴歸測試：複合場景引擎（F-17，路徑串接近似）。

跑法：`python scripts/test_coupled.py`（固定 seed、小房間場景，不依賴模型下載，
任何 clone 可重跑；全部通過 exit 0，任一失敗 exit 1）。
"""

import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.signal import sosfiltfilt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import ir_metrics  # noqa: E402
from src.image_reverb.coupled import (  # noqa: E402
    export_coupled,
    get_transmission,
    load_scene_file,
    load_transmission,
    resolve_room,
    synthesize_coupled,
)
from src.image_reverb.materials import load_materials  # noqa: E402
from src.image_reverb.scene_text import load_scene_presets  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def band_energy_db(ir: np.ndarray, fs: int, freq: int) -> float:
    sos = ir_metrics._bandpass_sos(freq, fs)
    band = sosfiltfilt(sos, ir)
    return 10.0 * np.log10(float(np.sum(band**2)) + 1e-30)


# 測試用小場景（兩個小房間，跑得快）
def tiny_scene(paths):
    return {
        "name": "test_scene",
        "source_room": {"preset": "generic_room"},
        "listener_room": {"preset": "bedroom"},
        "paths": paths,
    }


def main() -> int:
    trans = load_transmission()
    presets = load_scene_presets()
    materials = load_materials()

    # ---------- 1. 傳輸損失表健全性 ----------
    print("【1】傳輸損失表健全性")
    bands = trans["band_center_freqs_hz"]
    ok_shape = all(len(e["tl_db"]) == len(bands) for e in trans["paths"])
    check("每個類型都有六頻段 TL", ok_shape, f"{len(trans['paths'])} 種類型")

    concrete = get_transmission("concrete_wall_20cm", trans)["tl_db"]
    glass = get_transmission("glass_single", trans)["tl_db"]
    opening = get_transmission("opening_open", trans)["tl_db"]
    check("常識排序：混凝土 > 玻璃 > 開口（500Hz TL）",
          concrete[2] > glass[2] > opening[2],
          f"{concrete[2]} > {glass[2]} > {opening[2]} dB")
    check("質量定律：混凝土牆 TL 隨頻率單調上升",
          all(a < b for a, b in zip(concrete, concrete[1:])),
          f"{concrete}")
    check("開口 TL ≈ 0（各頻段 ≤ 3dB）", max(opening) <= 3, f"{opening}")

    # ---------- 2. TL 濾波真的生效（牆悶、開口亮）----------
    print("【2】TL 濾波生效（頻譜對比）")
    r_wall = synthesize_coupled(tiny_scene([{"type": "gypsum_partition"}]),
                                presets, materials, trans)
    r_open = synthesize_coupled(tiny_scene([{"type": "opening_open"}]),
                                presets, materials, trans)
    fs = r_wall.sample_rate

    def hf_lf_ratio(ir):
        return band_energy_db(ir, fs, 4000) - band_energy_db(ir, fs, 125)

    ratio_wall, ratio_open = hf_lf_ratio(r_wall.ir), hf_lf_ratio(r_open.ir)
    check("牆路徑的 高頻/低頻 能量比顯著低於開口路徑（≥15dB 差）",
          ratio_open - ratio_wall >= 15.0,
          f"開口 {ratio_open:+.1f}dB vs 牆 {ratio_wall:+.1f}dB（差 {ratio_open - ratio_wall:.1f}dB）")

    # ---------- 2b. eq_db 調音生效 ----------
    print("【2b】eq_db 調音生效")
    r_eq = synthesize_coupled(
        tiny_scene([{"type": "gypsum_partition", "eq_db": [-12, 0, 0, 0, 0, 0]}]),
        presets, materials, trans)
    lf_drop = (band_energy_db(r_wall.ir, fs, 125) - band_energy_db(r_wall.ir, fs, 500)) - \
              (band_energy_db(r_eq.ir, fs, 125) - band_energy_db(r_eq.ir, fs, 500))
    check("eq_db 125Hz -12dB → 125/500 能量比下降 ~12dB（±3dB）",
          abs(lf_drop - 12.0) <= 3.0, f"實測下降 {lf_drop:.1f}dB")
    try:
        synthesize_coupled(tiny_scene([{"type": "gypsum_partition", "eq_db": [0, 0]}]),
                           presets, materials, trans)
        check("eq_db 長度錯誤 → 報錯", False, "沒有報錯")
    except ValueError:
        check("eq_db 長度錯誤 → 報錯", True, "有報錯")

    # ---------- 3. 延遲生效 ----------
    print("【3】extra_delay_ms 生效")
    r_d0 = synthesize_coupled(tiny_scene([{"type": "opening_open", "extra_delay_ms": 0}]),
                              presets, materials, trans, normalize=False)
    r_d50 = synthesize_coupled(tiny_scene([{"type": "opening_open", "extra_delay_ms": 50}]),
                               presets, materials, trans, normalize=False)

    def onset(ir):
        peak = np.max(np.abs(ir))
        return int(np.argmax(np.abs(ir) > peak * 0.01))

    shift_ms = (onset(r_d50.ir) - onset(r_d0.ir)) / fs * 1000.0
    check("延遲 50ms → 到達時間位移 ≈ 50ms（±2ms）",
          abs(shift_ms - 50.0) <= 2.0, f"實測位移 {shift_ms:.1f}ms")

    # ---------- 4. 線性疊加（多路徑 = 各單路徑之和）----------
    print("【4】線性疊加自檢")
    pA = {"type": "gypsum_partition"}
    pB = {"type": "opening_open", "gain_db": -6, "extra_delay_ms": 20}
    r_ab = synthesize_coupled(tiny_scene([pA, pB]), presets, materials, trans, normalize=False)
    r_a = synthesize_coupled(tiny_scene([pA]), presets, materials, trans, normalize=False)
    r_b = synthesize_coupled(tiny_scene([pB]), presets, materials, trans, normalize=False)
    n = len(r_ab.ir)
    summed = np.zeros(n)
    summed[: len(r_a.ir)] += r_a.ir
    summed[: len(r_b.ir)] += r_b.ir
    err = float(np.max(np.abs(summed - r_ab.ir))) / float(np.max(np.abs(r_ab.ir)))
    check("兩路徑輸出 = 兩個單路徑輸出之和（正規化前，相對誤差 <1e-9）",
          err < 1e-9, f"最大相對誤差 {err:.2e}")

    # ---------- 5. 決定性與示範場景 ----------
    print("【5】決定性與示範場景")
    r2 = synthesize_coupled(tiny_scene([pA, pB]), presets, materials, trans, normalize=False)
    check("同場景同 seed → bit-identical", bool(np.array_equal(r_ab.ir, r2.ir)), "兩次合成逐點相同")

    for fname in ("stadium_corridor.json", "neighbor_voices.json"):
        scene = load_scene_file(PROJECT_ROOT / "assets" / "scenes" / fname)
        try:
            for key in ("source_room", "listener_room"):
                resolve_room(scene[key], presets, materials, key)
            for p in scene["paths"]:
                get_transmission(p["type"], trans)
                if p.get("via_room"):
                    resolve_room(p["via_room"], presets, materials, "via_room")
            check(f"示範場景 {fname} schema 有效", True,
                  f"{len(scene['paths'])} 條路徑（完整合成在 gen_ir_coupled.py）")
        except (ValueError, KeyError) as e:
            check(f"示範場景 {fname} schema 有效", False, str(e))

    # ---------- 5b. 閉環比對警示真的接上了（T-21 修正輪）----------
    # 退回理由第 3 點：`export_coupled()` 原本只把 target/measured 並列寫進 rooms、
    # 從不比對，巨蛋聲源空間 2k/4k −94% 因此安靜地過關。這裡拿 neighbor_voices
    # 當對象——它的臥室 125Hz 與家用小走廊低頻有**已知的量測混頻偏差**（>20%），
    # 那些偏差本來就該出現在警示裡（誠實回報，不是修掉），正好用來驗機制通不通。
    print("【5b】export_coupled() 閉環比對警示（T-21 修正輪）")
    scene_nv = load_scene_file(PROJECT_ROOT / "assets" / "scenes" / "neighbor_voices.json")
    r_nv = synthesize_coupled(scene_nv, presets, materials, trans)
    with tempfile.TemporaryDirectory() as tmp:
        _, js = export_coupled(r_nv, Path(tmp) / "t21_warn_check")
        payload = json.loads(js.read_text(encoding="utf-8"))

    over_tol = [w for w in payload["warnings"] if "超出 ±20%" in w]
    check("輸出 JSON 的 warnings 含 >20% 頻段警示（已知混頻偏差不再靜默）",
          len(over_tol) > 0,
          f"{len(over_tol)} 條，例：{over_tol[0] if over_tol else '（無）'}")

    rooms = payload["rooms"]
    check("每個空間（含 via_room 中繼空間）都有 closed_loop 報告",
          len(rooms) == 3 and all("closed_loop" in r for r in rooms),
          f"{len(rooms)} 個空間：{[r['role'] for r in rooms]}")
    check("警示標注是哪個空間出問題（不是一坨無主訊息）",
          all(w.startswith("[") for w in over_tol),
          over_tol[0].split("]")[0] + "]" if over_tol else "（無）")

    # ---------- 6. 錯誤處理 ----------
    print("【6】錯誤處理")
    try:
        synthesize_coupled(tiny_scene([{"type": "no_such_wall"}]), presets, materials, trans)
        check("未知路徑類型 → 報錯", False, "沒有報錯")
    except ValueError as e:
        check("未知路徑類型 → 報錯＋列出可用類型", "可用" in str(e), "訊息含類型清單")
    try:
        synthesize_coupled({"name": "x", "source_room": {"preset": "bedroom"},
                            "listener_room": {"preset": "bedroom"}, "paths": []},
                           presets, materials, trans)
        check("空 paths → 報錯", False, "沒有報錯")
    except ValueError:
        check("空 paths → 報錯", True, "有報錯")

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-21 複合場景引擎測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
