#!/usr/bin/env python3
"""T-14 試聽檔生成：合成引擎的 small（逐表面地毯房）與 hall 兩組 IR ＋ wet 檔。

跑法：`python scripts/gen_t14_listen.py`（固定亂數種子，重跑結果 bit-identical）。

產出（`output/` 不進 git，新視窗/新 clone 要重跑本腳本）：
- output/ir_synth/T14_small_surf_carpet.{wav,json} — 4×3×2.5m，floor=carpet＋其餘石膏板
- output/ir_synth/T14_hall.{wav,json}              — 30×20×12m，wood_panel/concrete/gypsum
- output/listen_T14_small_carpet.wav — clap × small IR（--mix 0.6）
- output/listen_T14_hall.wav         — clap × hall IR（--mix 0.6）
- output/listen_T14_hall_T01baseline.wav — clap × T-01 純 image-source hall IR（對照組；
  需要 output/ir_hall_large.wav，沒有就先跑 `python scripts/gen_ir_manual.py hall`）

hall 材質組合（wood_panel 地板＋concrete 牆＋gypsum_board 天花板）給出 RT60 mid ≈ 7.8s、
125Hz ≈ 3.3s——與 T-01 hall（α=0.08 均勻，Sabine 6.04s）同一個「音樂廳」量級，
且逐表面組合符合約束 A（不是六面同材質）。
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config, ir_synth  # noqa: E402
from src.image_reverb.acoustics import compute_acoustics  # noqa: E402
from src.image_reverb.geometry import RoomEstimate  # noqa: E402
from src.image_reverb.materials import load_materials, parse_surface_spec  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DRY = PROJECT_ROOT / "assets" / "dry" / "clap_synth.wav"

CASES = [
    # (輸出名, 尺寸, 逐表面材質 spec)
    ("T14_small_surf_carpet", (4.0, 3.0, 2.5), "floor=carpet,walls=gypsum_board"),
    ("T14_hall", (30.0, 20.0, 12.0), "floor=wood_panel,walls=concrete,ceiling=gypsum_board"),
]


def main() -> int:
    if not DRY.exists():
        print(f"❌ 找不到乾聲檔 {DRY}（T-02 的合成拍手）")
        return 1

    data = load_materials()
    for name, dims, spec in CASES:
        est = RoomEstimate(*dims, confidence="high", dims_source="manual")
        surfaces = parse_surface_spec(spec, data)
        ac = compute_acoustics(est, surfaces, data)
        print(f"=== {name}：{dims[0]}×{dims[1]}×{dims[2]}m，{spec} ===")
        print(f"    Sabine 目標：{[round(v, 2) for v in ac.rt60_bands_sabine]}")
        result = ir_synth.synthesize_ir(ac, data)
        wav, js = ir_synth.export_ir(result, config.IR_SYNTH_OUTPUT_DIR / name)
        print(f"    已輸出 {wav.name} / {js.name}（長度 {len(result.ir) / result.sample_rate:.2f}s）")

        wet = OUTPUT_DIR / ("listen_T14_small_carpet.wav" if "small" in name else "listen_T14_hall.wav")
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "convolve.py"),
             str(DRY), str(wav), str(wet), "--mix", "0.6"],
            check=True,
        )
        print(f"    試聽檔：{wet.name}")

    # T-01 純 image-source hall 對照組（自我檢查：不得明顯劣化）
    t01_hall = OUTPUT_DIR / "ir_hall_large.wav"
    if not t01_hall.exists():
        print("（output/ir_hall_large.wav 不存在，先跑 gen_ir_manual.py hall 重生 T-01 對照組）")
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "gen_ir_manual.py"), "hall"],
            check=True,
        )
    baseline = OUTPUT_DIR / "listen_T14_hall_T01baseline.wav"
    subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / "convolve.py"),
         str(DRY), str(t01_hall), str(baseline), "--mix", "0.6"],
        check=True,
    )
    print(f"    T-01 對照組試聽檔：{baseline.name}")

    print()
    print("🎧 請使用者試聽（T-14 卡步驟 5，AI 不能代勞）：")
    print("    afplay output/listen_T14_small_carpet.wav   # 地毯小房間：短殘響、無鐵筒子聲")
    print("    afplay output/listen_T14_hall.wav           # 音樂廳：長殘響")
    print("    afplay output/listen_T14_hall_T01baseline.wav  # T-01 純 image-source 對照")
    print("    基準線：T-02 的「還算自然」。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
