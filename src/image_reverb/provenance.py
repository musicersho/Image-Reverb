"""T-43：Git revision／sha256 共用來源（插卡 4/4）。

`run_photo()`（生成時）與 `scripts/t17_blind_test.py`（驗證時）都需要同一組
「這是哪個 revision、輸入檔案有沒有變」的判斷依據；各自實作一次就是地雷 #15
的假綠燈來源之一——範圍或門檻改一邊漏一邊，兩邊看起來都對但語意已經分岔。
兩處都改成呼叫這裡（`t17_blind_test.py` 原本自己的 `_git_rev()` 搬到這裡，
不再各自維護一份）。

`git_revision()` 的 `commit` 一律是**呼叫當下**的 `git rev-parse HEAD` 全長
雜湊，不是任何快取值——`run_photo()` 在成功路徑寫 `analysis.json` 之前呼叫，
記的就是**生成當下**的 revision；`t17_blind_test.py` 在盲測當下另外呼叫一次。
兩次呼叫的結果不保證相同，這正是溯源要抓的事：生成之後改了 HEAD 再驗，必須
被抓到，不能兩邊都讀到「現在」的 HEAD 而變成恆真（Opus 驗證重點紅旗）。
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from . import config

PROJECT_ROOT = config.PROJECT_ROOT


def git_revision(
    cwd: Path = PROJECT_ROOT, scope: tuple[str, ...] = ("src", "data")
) -> dict[str, object]:
    """回傳 `{"commit": <git rev-parse HEAD 全長雜湊>, "dirty": <bool>}`。

    `dirty` 只看 `scope` 內範圍的 `git status --porcelain`（預設 `src`＋`data`，
    沿用 `t17_blind_test.py` 舊版 `_git_rev()` 的範圍）——範圍外的改動
    （例如 `scripts/`、文件）不影響這裡的判定。
    """
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()
    porcelain = subprocess.run(
        ["git", "status", "--porcelain", "--", *scope],
        cwd=cwd, capture_output=True, text=True, check=True,
    ).stdout
    return {"commit": commit, "dirty": bool(porcelain.strip())}


def sha256_file(path: Path) -> str:
    """檔案內容 sha256（bytes 層級，不管檔名／mtime）。"""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
