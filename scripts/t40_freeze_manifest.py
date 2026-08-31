#!/usr/bin/env python3
"""T-40：產生 `output/clip_accuracy/` 凍結基線的 FREEZE_MANIFEST.md
（插卡 1/4；鐵則 4 的唯一允許例外——純新增一個 manifest 檔）。

跑法：`python scripts/t40_freeze_manifest.py`

只讀取 `output/clip_accuracy/` 下既有檔案計算 sha256，寫出（或覆蓋重寫）
`FREEZE_MANIFEST.md` 本身；`FREEZE_MANIFEST.md` 以外的既有檔案完全不會被
本腳本寫入一個 bit。之後任何時候都能用同一份指令重跑驗證凍結基線是否被
覆寫過（`build_freeze_manifest_text()` 是純函式，兩次跑在同一批檔案上
內容 bit-identical）。
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from eval_cache import build_freeze_manifest_text  # noqa: E402

OUT_DIR = REPO_ROOT / "output" / "clip_accuracy"
COMMAND = "python scripts/t40_freeze_manifest.py"


def main() -> int:
    if not OUT_DIR.is_dir():
        print(f"🔴 卡關：找不到 {OUT_DIR}，凍結基線目錄不存在。", file=sys.stderr)
        return 1

    manifest_text = build_freeze_manifest_text(OUT_DIR, COMMAND)
    manifest_path = OUT_DIR / "FREEZE_MANIFEST.md"
    manifest_path.write_text(manifest_text, encoding="utf-8")
    print(f"✅ 已寫出 {manifest_path}（記錄 {OUT_DIR} 下的既有檔案 sha256）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
