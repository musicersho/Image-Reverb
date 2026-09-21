#!/usr/bin/env python3
"""T-62：退役集（舊 9 張 T-04 照片）的取圖輔助。

背景：Codex `ba1fcdb` 把 `assets/photos/` 的舊 9 張搬到本機 `assets/photos_legacy_20260920/`
（git 忽略；`14fc4ac` 的 git 歷史仍有），`assets/photos/` 改放 `t04_gpt_*.png`。
使用者 2026-09-20 決定維持新配置、改程式去適應（T-04 卡裁定 T-04-R）。
本模組讓仍需歷史原檔的測試，能在 `assets/photos/<舊檔名>` 缺檔時改由退役集備份目錄取圖。

純函式、無副作用、不 import `src`、不寫任何檔。所有函式在呼叫當下才讀模組全域
`LEGACY_PHOTOS_DIR`／`MANIFEST_PATH`（不綁成預設參數），讓測試可以 monkeypatch。
"""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEGACY_PHOTOS_DIR = REPO_ROOT / "assets" / "photos_legacy_20260920"
LEGACY_SOURCE_COMMIT = "14fc4ac"
MANIFEST_PATH = REPO_ROOT / "assets" / "t04_refresh" / "ASSET_MANIFEST.json"

_PHOTOS_REL_DIR = Path("assets") / "photos"


def resolve_photo(rel_path: str | Path) -> Path:
    """回傳測試該讀的照片路徑。

    - `REPO_ROOT / rel_path` 存在 → 回它。
    - 不存在、且上層目錄是 `assets/photos` → 回 `LEGACY_PHOTOS_DIR / <檔名>`
      （不論存在與否，存在性由呼叫端檢查）。
    - 其他路徑原樣回 `REPO_ROOT / rel_path`。
    """
    rel = Path(rel_path)
    direct = REPO_ROOT / rel
    if direct.exists():
        return direct
    if rel.parent == _PHOTOS_REL_DIR:
        return LEGACY_PHOTOS_DIR / rel.name
    return direct


def restore_hint(filename: str) -> str:
    """缺退役備份時，從 git 歷史還原該檔的指令。"""
    return (
        f"git show {LEGACY_SOURCE_COMMIT}:assets/photos/{filename} "
        f"> assets/photos_legacy_20260920/{filename}"
    )


def expected_sha256(filename: str) -> str | None:
    """從 ASSET_MANIFEST.json 的 images[] 取舊檔 `old_file == filename` 的 `old_sha256`。

    manifest 不存在、讀不了或找不到 → None。
    """
    try:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    for image in manifest.get("images", []):
        if image.get("old_file") == filename:
            return image.get("old_sha256")
    return None
