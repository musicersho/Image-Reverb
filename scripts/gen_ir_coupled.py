#!/usr/bin/env python3
"""T-21：複合場景 JSON → IR ＋ 試聽檔（F-17，路徑串接近似）。

用法：
    python scripts/gen_ir_coupled.py assets/scenes/stadium_corridor.json
    python scripts/gen_ir_coupled.py assets/scenes/neighbor_voices.json
    python scripts/gen_ir_coupled.py --list-types      # 列出可用傳輸路徑類型

輸出：`output/ir_synth/coupled_<場景名>.wav/.json` 與 `output/listen_coupled_<場景名>.wav`。
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config  # noqa: E402
from src.image_reverb.coupled import (  # noqa: E402
    export_coupled,
    load_scene_file,
    load_transmission,
    synthesize_coupled,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
DRY = PROJECT_ROOT / "assets" / "dry" / "clap_synth.wav"


def main() -> int:
    parser = argparse.ArgumentParser(description="複合場景 JSON → IR（T-21 / F-17）")
    parser.add_argument("scene", nargs="?", help="場景 JSON 檔路徑（見 assets/scenes/）")
    parser.add_argument("--no-listen", action="store_true", help="只出 IR，不產生卷積試聽檔")
    parser.add_argument("--list-types", action="store_true", help="列出可用傳輸路徑類型後結束")
    args = parser.parse_args()

    if args.list_types:
        data = load_transmission()
        print("可用的傳輸路徑類型（data/transmission.json）：")
        for e in data["paths"]:
            tl = "/".join(str(v) for v in e["tl_db"])
            print(f"  {e['id']:<20} {e['name_zh']:<16} TL(dB)={tl}（信心 {e['confidence']}）")
        return 0
    if not args.scene:
        parser.error("要給場景 JSON 檔路徑（或用 --list-types 查傳輸類型）")

    try:
        scene = load_scene_file(args.scene)
        result = synthesize_coupled(scene)
    except (ValueError, FileNotFoundError, KeyError) as e:
        print(f"❌ 錯誤：{e}", file=sys.stderr)
        return 2

    print(f"=== 複合場景：{result.scene_name}（method: path_cascade_v1，工程近似） ===")
    if scene.get("description_zh"):
        print(f"  {scene['description_zh']}")
    for room in result.rooms_summary:
        print(f"  [{room['role']}] {room['name']}：{room['dims_m'][0]}×{room['dims_m'][1]}×{room['dims_m'][2]} m，"
              f"T30 量測 {room['t30_measured_s']} s")
        # T-21 修正輪：逐空間閉環比對結果一定要印出來（原本只在 JSON 並列數字、
        # 從不比對，巨蛋 2k/4k −94% 因此安靜地過關）。誤差是量測 vs 目標，誠實列出。
        cl = room["closed_loop"]
        worst = max(cl["bands"], key=lambda b: abs(b["error_pct"]))
        flag = "✅ 全部在 ±20% 內" if cl["all_within_tolerance"] else "⚠️ 有頻段超差"
        print(f"      閉環比對 {flag}（最大誤差 {worst['freq_hz']}Hz "
              f"{worst['error_pct']:+.1f}%：目標 {worst['rt60_target_s']}s "
              f"vs 量測 {worst['t30_measured_s']}s）")
    for p in result.paths_summary:
        extra = f"，經 {p['via_room']}" if p["via_room"] else ""
        print(f"  路徑{p['index']}：{p['name_zh']} ×{p['tl_times']}，gain {p['gain_db']}dB，"
              f"延遲 {p['extra_delay_ms']}ms{extra}")

    out_name = f"coupled_{result.scene_name}"
    wav, js = export_coupled(result, config.IR_SYNTH_OUTPUT_DIR / out_name)
    print(f"已輸出：{wav}（{len(result.ir) / result.sample_rate:.2f}s）與 {js.name}")
    for w in result.warnings:
        print(f"  ⚠️ {w}")

    if not args.no_listen:
        if not DRY.exists():
            print(f"❌ 找不到乾聲檔 {DRY}，略過試聽檔", file=sys.stderr)
            return 1
        wet = OUTPUT_DIR / f"listen_{out_name}.wav"
        # ⚠️ 複合場景必須全濕（mix 1.0）：聽者與聲源在不同空間，聽到的每一分聲音
        # 都穿過了牆/門/開口——混入乾聲等於讓聲音「未經阻隔直達耳朵」，物理上不存在。
        # （2026-08-27 使用者實聽抓到的缺陷：mix 0.6 的 40% 乾聲讓穿牆聲「太亮、
        # 沒有被阻隔的聽感」。同房間殘響的試聽檔才適用乾濕混合。）
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "convolve.py"),
             str(DRY), str(wav), str(wet), "--mix", "1.0"],
            check=True,
        )
        print(f"🎧 試聽檔：{wet}（全濕 mix=1.0——穿牆聲不該混入任何乾聲）")
        print("   （乾聲目前只有合成拍手；隔壁人聲情境用真實說話聲會更有感，"
          "之後有真實乾聲放進 assets/dry/ 再重跑）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
