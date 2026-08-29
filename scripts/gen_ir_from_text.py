#!/usr/bin/env python3
"""T-20：文字場景描述 → IR ＋ 試聽檔（F-16）。

用法：
    python scripts/gen_ir_from_text.py "浴室"
    python scripts/gen_ir_from_text.py "4x3x2.5 的房間，地板鋪地毯"
    python scripts/gen_ir_from_text.py "大教堂" -o my_cathedral
    python scripts/gen_ir_from_text.py --list-scenes

輸出：`output/ir_synth/text_<場景>.wav/.json`（IR＋閉環報告）與
`output/listen_text_<場景>.wav`（clap 卷積試聽檔，--mix 0.6）。
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config, ir_synth  # noqa: E402
from src.image_reverb.acoustics import compute_acoustics  # noqa: E402
from src.image_reverb.materials import load_materials  # noqa: E402
from src.image_reverb.scene_text import (  # noqa: E402
    available_scenes_text,
    load_scene_presets,
    parse_scene_text,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DRY = PROJECT_ROOT / "assets" / "dry" / "clap_synth.wav"


def main() -> int:
    parser = argparse.ArgumentParser(description="文字場景描述 → IR（T-20 / F-16）")
    parser.add_argument("text", nargs="?", help="場景描述，例：「4x3x2.5 的房間，地板鋪地毯」")
    parser.add_argument("-o", "--out-name", default=None, help="輸出檔名（預設用場景 preset id）")
    parser.add_argument("--no-listen", action="store_true", help="只出 IR，不產生卷積試聽檔")
    parser.add_argument("--list-scenes", action="store_true", help="列出可用場景後結束")
    args = parser.parse_args()

    if args.list_scenes:
        print("可用的文字場景（data/scene_presets.json）：")
        print(available_scenes_text())
        return 0
    if not args.text:
        parser.error("要給場景描述（或用 --list-scenes 查可用場景）")

    try:
        presets = load_scene_presets()
        materials = load_materials()
        parsed = parse_scene_text(args.text, presets, materials)
    except (ValueError, FileNotFoundError) as e:
        print(f"❌ 錯誤：{e}", file=sys.stderr)
        return 2

    est, surf = parsed.estimate, parsed.surfaces
    print(f"=== 文字場景：{parsed.preset_name_zh}（preset: {parsed.preset_id}） ===")
    print(f"尺寸：{est.length_m}×{est.width_m}×{est.height_m} m"
          f"（dims_source={est.dims_source}, confidence={est.confidence}）")
    print("六面材質（逐表面，約束 A）：")
    for name, mid in surf.as_dict().items():
        print(f"    {name:<8} {mid:<16} 來源 {surf.sources.get(name, '-')}")
    for note in parsed.parse_notes:
        print(f"  ・{note}")
    for w in surf.warnings:
        print(f"  ⚠️ {w}")

    ac = compute_acoustics(est, surf, materials)
    print(f"Sabine 目標 RT60：{[round(v, 2) for v in ac.rt60_bands_sabine]} s")

    result = ir_synth.synthesize_ir(ac, materials)
    out_name = args.out_name or f"text_{parsed.preset_id}"
    wav, js = ir_synth.export_ir(result, config.IR_SYNTH_OUTPUT_DIR / out_name)
    print(f"已輸出：{wav}（{len(result.ir) / result.sample_rate:.2f}s）與 {js.name}")
    for w in result.warnings:
        print(f"  ⚠️ {w}")

    if not args.no_listen:
        if not DRY.exists():
            print(f"❌ 找不到乾聲檔 {DRY}，略過試聽檔", file=sys.stderr)
            return 1
        wet = OUTPUT_DIR / f"listen_{out_name}.wav"
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "convolve.py"),
             str(DRY), str(wav), str(wet), "--mix", "0.6"],
            check=True,
        )
        print(f"🎧 試聽檔：{wet}（afplay 播放；數字合理 ≠ 聽起來對，請實聽）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
