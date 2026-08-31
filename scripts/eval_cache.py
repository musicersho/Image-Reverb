#!/usr/bin/env python3
"""T-40：評測快取指紋與自動失效（插卡 1/4；純 harness 模組，零 `src/`／`data/` 改動）。

純函式模組，供評測 harness（`t36_clip_accuracy.py` 等）共用，本檔本身只讀取
檔案內容算 hash，不寫入任何 `src/` 或 `data/` 底下的檔案。

背景（外部掃描 P2，已對碼核實）：舊版 `run_or_load()` 只要 `detail.json`
存在且未加 `--fresh` 就直接讀快取，快取內沒有任何指紋（無 code hash、無
提示詞/門檻/模型 id、無來源圖片 hash）——改了分類程式之後用預設指令重跑，
報告看似成功卻完全沒量到新碼，只靠操作者記得 `--fresh`。這是「安靜地輸出
看似合理的錯誤結果」的新亞型：量測結果可能根本不是本次程式產的。

本模組提供三件事：
1. `compute_fingerprint()`：算出一份快取的指紋（六類，缺一不可）。
2. `diff_fingerprint()`：比對兩份指紋，回傳不符項目清單（人類可讀）。
3. `load_or_run()`：load-or-run 快取邏輯，依「是否指向凍結目錄」分兩態：
   - 非凍結目錄：指紋不符（含舊格式無指紋欄）→ 自動重跑，回傳不符原因；
   - 凍結目錄：指紋不符 → 丟 `FrozenBaselineError`（hard fail，呼叫端
     負責印訊息並以非 0 結束）——絕不允許自動重跑覆寫凍結基線；
     即使呼叫端要求 `force_fresh`，凍結目錄一樣拒絕（唯一允許寫入凍結
     目錄的例外是 FREEZE_MANIFEST.md，見下）。

另外提供 FREEZE_MANIFEST 相關函式（鐵則 4 的唯一允許例外：純新增一個
manifest 檔，凍結目錄既有檔案一個 bit 都不許變）：
4. `list_frozen_files()` / `build_freeze_manifest_text()` / `verify_freeze_manifest()`
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

FREEZE_MANIFEST_NAME = "FREEZE_MANIFEST.md"


class FrozenBaselineError(RuntimeError):
    """指向凍結基線目錄但指紋不符（或要求強制重跑）——hard fail，不得自動重跑覆寫。"""


# ------------------------------------------------------------------
# 指紋計算與比對
# ------------------------------------------------------------------

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def compute_fingerprint(
    *,
    photo_path: Path,
    code_paths: list[Path],
    data_paths: list[Path],
    segmentation_model_id: str,
    clip_model_id: str,
    clip_threshold: float,
    eval_mode: str = "default",
) -> dict[str, Any]:
    """算出一份快取的指紋字典。六類指紋（卡片列的 1–6 項）缺一不可：
    1. 來源圖片 sha256；2. `code_paths` 逐檔內容 hash；3. `data_paths` 逐檔
    內容 hash；4. 模型 id；5. CLIP 門檻；6. 評測模式。
    """
    return {
        "photo_sha256": sha256_file(photo_path),
        "code_sha256": {p.name: sha256_file(p) for p in code_paths},
        "data_sha256": {p.name: sha256_file(p) for p in data_paths},
        "segmentation_model_id": segmentation_model_id,
        "clip_model_id": clip_model_id,
        "clip_threshold": clip_threshold,
        "eval_mode": eval_mode,
    }


def diff_fingerprint(cached: dict | None, current: dict) -> list[str]:
    """回傳指紋不符的項目清單（人類可讀字串）；全部相符則回傳空 list。
    `cached` 為 None（快取內完全沒有 fingerprint 欄位＝舊格式）視為全部不符。
    """
    if cached is None:
        return ["快取內無 fingerprint 欄位（舊格式，視為指紋全部不符）"]

    mismatches: list[str] = []
    for key in (
        "photo_sha256",
        "segmentation_model_id",
        "clip_model_id",
        "clip_threshold",
        "eval_mode",
    ):
        if cached.get(key) != current.get(key):
            mismatches.append(f"{key}: {cached.get(key)!r} → {current.get(key)!r}")

    for group in ("code_sha256", "data_sha256"):
        cached_group = cached.get(group) or {}
        current_group = current.get(group) or {}
        names = sorted(set(cached_group) | set(current_group))
        for name in names:
            before = cached_group.get(name)
            after = current_group.get(name)
            if before != after:
                mismatches.append(f"{group}.{name}: {before!r} → {after!r}")

    return mismatches


def load_or_run(
    *,
    cache_path: Path,
    fingerprint_fn: Callable[[], dict[str, Any]],
    run_fn: Callable[[], dict[str, Any]],
    is_frozen: bool,
    force_fresh: bool = False,
) -> tuple[dict[str, Any], bool, list[str]]:
    """讀快取或執行 `run_fn()`，回傳 `(payload, was_rerun, mismatch_reasons)`。

    `fingerprint_fn` 是**惰性**的：只有真的需要比對指紋內容時才呼叫（見下）。
    這樣快取是「舊格式（完全沒有 fingerprint 欄位）」時，判定「指紋不符」
    不需要真的算出當前指紋——來源圖片可能已不在本機（例如乾淨 clone 缺
    `assets/reference_irs/`），凍結目錄的 hard-fail 判定不該因此連帶失敗。

    - 目標是凍結目錄且要求 `force_fresh`：直接 `FrozenBaselineError`（凍結
      目錄不允許任何形式的強制重跑，包含手動 `--fresh`）。
    - 快取不存在：
        - 非凍結目錄，或 `force_fresh`（非凍結目錄）：執行 `run_fn()`；
        - 凍結目錄：`FrozenBaselineError`（凍結目錄不存在快取也不可自動
          產生新內容——不得有「快取不存在就默默重跑並寫進凍結基線」的
          第三態）。
    - 快取存在且指紋相符：直接回傳快取內容，`was_rerun=False`。
    - 快取存在但指紋不符：
        - 非凍結目錄 → 自動重跑（`was_rerun=True`），`mismatch_reasons` 非空；
        - 凍結目錄 → `FrozenBaselineError`（絕不自動重跑覆寫凍結基線）。
    """
    if is_frozen and force_fresh:
        raise FrozenBaselineError(
            f"{cache_path} 屬於凍結基線目錄，不可用 --fresh 強制重跑。"
            "治療評測請用 --out-dir 指到新目錄。"
        )

    reasons: list[str] = []
    if cache_path.exists() and not force_fresh:
        cached_entry = json.loads(cache_path.read_text(encoding="utf-8"))
        cached_fingerprint = cached_entry.get("fingerprint")
        if cached_fingerprint is None:
            reasons = ["快取內無 fingerprint 欄位（舊格式，視為指紋全部不符）"]
        else:
            reasons = diff_fingerprint(cached_fingerprint, fingerprint_fn())
        if not reasons:
            return cached_entry["payload"], False, []
        if is_frozen:
            raise FrozenBaselineError(
                f"{cache_path} 指紋不符，但這是凍結基線目錄，不可自動重跑覆寫。"
                f"不符項目：{reasons}。治療評測請用 --out-dir 指到新目錄。"
            )
    elif is_frozen:
        raise FrozenBaselineError(
            f"{cache_path} 屬於凍結基線目錄，快取不存在，不可自動重跑產生新內容。"
            "治療評測請用 --out-dir 指到新目錄。"
        )
    else:
        reasons = ["快取不存在" if not force_fresh else "使用者要求 --fresh 強制重跑"]

    fingerprint = fingerprint_fn()
    payload = run_fn()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps({"fingerprint": fingerprint, "payload": payload}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload, True, reasons


# ------------------------------------------------------------------
# FREEZE_MANIFEST：凍結基線可追溯化（鐵則 4 唯一允許例外）
# ------------------------------------------------------------------

def list_frozen_files(root: Path) -> list[Path]:
    """列出 `root` 底下所有既有檔案（排除 FREEZE_MANIFEST.md 本身），
    依相對路徑排序，回傳絕對路徑清單。"""
    files = [
        p for p in root.rglob("*")
        if p.is_file() and p.name != FREEZE_MANIFEST_NAME
    ]
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def build_freeze_manifest_text(root: Path, command: str) -> str:
    """產出 FREEZE_MANIFEST.md 內容：`root` 下所有既有檔案的 sha256 清單
    ＋產生指令原文。純讀取，不寫入任何檔案（由呼叫端決定是否寫檔）。"""
    files = list_frozen_files(root)
    lines = [
        f"# {root.name} 凍結基線 FREEZE_MANIFEST（T-40 產出，鐵則 4 唯一允許例外）\n",
        "本檔案以外，本目錄下所有既有檔案自本檔產生起一個 bit 都不許變。",
        f"若要重新驗證，逐檔重算 sha256 並與下表比對——不符即代表凍結基線被覆寫過。\n",
        f"產生指令：`{command}`\n",
        "| 相對路徑 | sha256 |",
        "|---|---|",
    ]
    for path in files:
        rel = path.relative_to(root).as_posix()
        lines.append(f"| {rel} | {sha256_file(path)} |")
    lines.append(f"\n共 {len(files)} 個檔案。\n")
    return "\n".join(lines) + "\n"


def verify_freeze_manifest(root: Path, manifest_text: str) -> list[str]:
    """比對 `manifest_text`（FREEZE_MANIFEST.md 的內容）與 `root` 底下實際
    檔案的 sha256，回傳不符項目清單（缺檔／多檔／hash 不符）；全部相符則
    回傳空 list。"""
    recorded: dict[str, str] = {}
    for line in manifest_text.splitlines():
        line = line.strip()
        if not line.startswith("| ") or line.startswith("| 相對路徑"):
            continue
        parts = [c.strip() for c in line.strip("|").split("|")]
        if len(parts) != 2 or len(parts[1]) != 64:
            continue
        recorded[parts[0]] = parts[1]

    actual_files = list_frozen_files(root)
    actual = {p.relative_to(root).as_posix(): sha256_file(p) for p in actual_files}

    problems: list[str] = []
    for rel, expected_hash in recorded.items():
        actual_hash = actual.get(rel)
        if actual_hash is None:
            problems.append(f"缺檔：{rel}（manifest 有記錄，實際不存在）")
        elif actual_hash != expected_hash:
            problems.append(f"hash 不符：{rel}（manifest={expected_hash}，實際={actual_hash}）")
    for rel in actual:
        if rel not in recorded:
            problems.append(f"多出未記錄的檔案：{rel}")
    return problems
