#!/usr/bin/env python3
"""T-57／T-17-R2 步驟 1：R2 資料集鎖定 manifest 產生器。

跑法：
    python scripts/t17r2_dataset_manifest.py                 # held-out 路徑
    python scripts/t17r2_dataset_manifest.py --legacy         # 降級：沿用 assets/photos/ 舊五張
    python scripts/t17r2_dataset_manifest.py --dry assets/dry/真實人聲.wav   # 自錄乾聲（與盲測同一個檔）
輸出：`output/mvp_acceptance_r2/DATASET_MANIFEST.json`（`--out` 可換路徑）
`--legacy` 固定使用 `assets/photos/`，**不可**與 `--photos-dir` 併用（CLI 層互斥，exit 2）；
`--photos-dir`／`--dry` 指到 repo 外 → stderr 清楚訊息＋exit 1（manifest 只記 repo 相對路徑）。

**為什麼要有這支腳本**：T-17-R2 是重新驗收，必須先把「這次驗收用的是哪些照片、
哪些真實 IR、哪一版程式碼」凍結下來，之後才能對「盲測產物是不是同一批資料生成的」
做溯源比對（`t17r2_blind_test.py` 用的 provenance 驗證）。內容**不含任何時間戳**——
同一個 HEAD、同一批輸入檔重跑，輸出必須逐位元相同（鐵則的可重現性精神）。

**內容**：
- `head`／`degraded`：目前 `git rev-parse HEAD` 與是否走 `--legacy` 降級路徑。
  開跑前檢查 `git status --porcelain -- src data scripts` 非空 → 直接失敗，
  不寫檔（工作樹不乾淨的當下不該鎖定資料集）。
- `heldout_photos`：五類 held-out（或 legacy 五張）逐筆 stem／path／sha256／
  類別／domain。domain 分類邏輯見 `t17r2_common.classify_domain()`——車內固定
  `non_room`；其餘依 `assets/photos_heldout/ground_truth_heldout.json` 記錄的
  尺寸最大邊是否 ≤10m 分 `in`／`out`；沒有尺寸資料（held-out 尚未填 GT，或
  `--legacy` 路徑本來就沒有這份 GT 檔）→ `unknown`。
- `venues`：8 個 §7-2 對照場地，`in_domain` 旗標**寫死**（只有 `mit_gym`
  true，見 T-17-R2 卡「in-domain 場地事前定義」，結果出來後不得改）。
  逐個場地重用 `t17_rt60_table.VENUES`（唯一事實來源，本檔只 import 不重抄）。
- `manual_dims`：5 組手動尺寸，逐字抄自 `output/mvp_acceptance/tables.md` 表 4，
  寫死在 `t17r2_common.MANUAL_DIMS`。
- `dry`：這次驗收用的乾聲檔的 path＋sha256——預設 `assets/dry/clap_synth.wav`；
  使用者提供自錄乾聲時以 `--dry <wav>` 指定（**必須與 `t17r2_blind_test.py --dry`
  給同一個檔**，DATASET_MANIFEST 鎖定的才是盲測實際用的乾聲；乾聲檔必須在 repo 內）。
  （盲測端另在 `blind_test/MANIFEST.json` 記它自己用的乾聲；兩者是否一致由 T-17-R2
  步驟 3 現場核對，本檔不做交叉比對。）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.image_reverb import provenance  # noqa: E402
import t17_blind_test  # noqa: E402
import t17_rt60_table  # noqa: E402
import t17r2_common as common  # noqa: E402

DIRTY_SCOPE = ("src", "data", "scripts")


def _sha256(path: Path) -> str:
    return provenance.sha256_file(path)


def _repo_relative(path: Path, repo_root: Path) -> str | None:
    """`path` 相對 `repo_root` 的路徑字串；在 repo 外回傳 `None`。

    呼叫端負責把 `None` 變成清楚的錯誤訊息——不得讓 `relative_to()` 的 ValueError
    （或符號連結迴圈的 RuntimeError）洩漏成 Traceback。兩段判斷：
    1. **文字比對**（`os.path.abspath`，不跟隨符號連結）：repo 內的路徑照舊接受、
       記下的相對路徑與修改前逐字相同（repo 內連到外面的符號連結、別名目錄也不改寫）；
       CLI 傳進來的相對路徑（`--photos-dir assets/photos_heldout`）依 cwd 展開。
    2. 文字比對不過才 **resolve** 後再比一次：處理 macOS `/var`↔`/private/var`、
       cwd 是符號連結等「同一個地方、兩種寫法」。兩段都不在 repo 內才算 repo 外。
    `t17r2_blind_test._inside_repo()` 用同一套算法（兩支工具對「在 repo 內」的定義必須一致）。
    """
    try:
        return str(Path(os.path.abspath(path)).relative_to(os.path.abspath(repo_root)))
    except ValueError:
        pass
    try:
        return str(Path(path).resolve().relative_to(Path(repo_root).resolve()))
    except (ValueError, RuntimeError, OSError):
        return None


def build_manifest(
    *,
    repo_root: Path,
    legacy: bool,
    photos_dir: Path | None = None,
    categories: list[tuple[str, str]] | None = None,
    venues: list[dict] | None = None,
    reference_irs_dir: Path | None = None,
    dry_path: Path | None = None,
    manual_dims: dict[str, dict[str, float]] | None = None,
    dirty_scope: tuple[str, ...] = DIRTY_SCOPE,
) -> tuple[dict | None, list[str]]:
    """組出 manifest dict。回傳 `(manifest, errors)`；`errors` 非空時
    `manifest` 一定是 `None`（部分失敗不寫半份檔案）。

    全部參數帶預設值＝真實專案路徑／常數，讓 `test_t17r2_tools.py` 可以指到
    隔離 git repo 與樁資料重跑同一段邏輯（沿用 `t17_blind_test.run()` 的手法）。
    """
    errors: list[str] = []

    # 參數先驗（先於 git／任何檔案存取）：manifest 只記 repo 相對路徑，
    # --photos-dir／--dry 指到 repo 外 → 清楚錯誤，不得 Traceback。
    if legacy:
        photos_dir = (repo_root / "assets" / "photos") if photos_dir is None else photos_dir
    else:
        photos_dir = (repo_root / "assets" / "photos_heldout") if photos_dir is None else photos_dir
    dry_path = (repo_root / "assets" / "dry" / "clap_synth.wav") if dry_path is None else dry_path
    for flag, p in (("--photos-dir", photos_dir), ("--dry", dry_path)):
        if _repo_relative(p, repo_root) is None:
            errors.append(
                f"{flag} 必須位於 repo 內：manifest 只記 repo 相對路徑（收到 {p}；repo＝{repo_root}）"
            )
    if errors:
        return None, errors

    rev = provenance.git_revision(cwd=repo_root, scope=dirty_scope)
    if rev["dirty"]:
        errors.append(
            f"git status --porcelain -- {' '.join(dirty_scope)} 非空："
            "工作樹不乾淨，不得鎖定資料集（先 commit 或還原）"
        )
        return None, errors

    if legacy:
        categories = list(t17_blind_test.SPACES) if categories is None else categories
        ground_truth: dict = {}
    else:
        categories = list(common.HELDOUT_SPACES) if categories is None else categories
        ground_truth = common.load_ground_truth_heldout(photos_dir)

    heldout_photos = []
    for category, stem in categories:
        photo = common.find_photo(photos_dir, stem)
        if photo is None:
            errors.append(f"找不到照片：{photos_dir}/{stem}.<jpg|jpeg|png|heic>")
            continue
        photo_rel = _repo_relative(photo, repo_root)
        if photo_rel is None:
            errors.append(f"照片必須位於 repo 內：manifest 只記 repo 相對路徑（{photo}）")
            continue
        is_car = category == common.CAR_CATEGORY_LABEL
        dims_m = None
        if not legacy:
            dims_m = ground_truth.get(stem, {}).get("dims_m")
        heldout_photos.append(
            {
                "stem": stem,
                "category": category,
                "path": photo_rel,
                "sha256": _sha256(photo),
                "domain": common.classify_domain(is_car=is_car, dims_m=dims_m),
            }
        )

    venues = list(t17_rt60_table.VENUES) if venues is None else venues
    reference_irs_dir = (
        (repo_root / "assets" / "reference_irs") if reference_irs_dir is None else reference_irs_dir
    )
    venue_entries = []
    for v in venues:
        photo_path = reference_irs_dir / v["photo"]
        if not photo_path.exists():
            errors.append(f"找不到場地照片：{photo_path}")
            continue
        real_ir_sha256 = []
        for rel in v["real_irs"]:
            ir_path = reference_irs_dir / rel
            if not ir_path.exists():
                errors.append(f"找不到真實 IR：{ir_path}")
                continue
            real_ir_sha256.append(_sha256(ir_path))
        venue_entries.append(
            {
                "key": v["key"],
                "label": v["label"],
                "photo_sha256": _sha256(photo_path),
                "real_ir_sha256": real_ir_sha256,
                "in_domain": v["key"] in common.IN_DOMAIN_VENUE_KEYS,
            }
        )

    dry_entry = None
    if not dry_path.is_file():
        errors.append(f"找不到乾聲檔（或不是檔案）：{dry_path}")
    else:
        dry_entry = {"path": _repo_relative(dry_path, repo_root), "sha256": _sha256(dry_path)}

    if errors:
        return None, errors

    manifest = {
        "degraded": bool(legacy),
        "head": rev["commit"],
        "heldout_photos": heldout_photos,
        "venues": venue_entries,
        "manual_dims": dict(common.MANUAL_DIMS if manual_dims is None else manual_dims),
        "dry": dry_entry,
    }
    return manifest, []


def run(
    *,
    repo_root: Path = REPO_ROOT,
    legacy: bool = False,
    photos_dir: Path | None = None,
    out_path: Path | None = None,
    dry_path: Path | None = None,
) -> int:
    out_path = (repo_root / "output" / "mvp_acceptance_r2" / "DATASET_MANIFEST.json") if out_path is None else out_path
    manifest, errors = build_manifest(
        repo_root=repo_root, legacy=legacy, photos_dir=photos_dir, dry_path=dry_path
    )
    if errors:
        print("❌ 無法產生 DATASET_MANIFEST.json：", file=sys.stderr)
        for e in errors:
            print(f"   - {e}", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8"
    )
    print(f"✅ 已寫入 {out_path}")
    print(f"   head={manifest['head']}　degraded={manifest['degraded']}")
    print(f"   heldout_photos={len(manifest['heldout_photos'])}　venues={len(manifest['venues'])}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="T-17-R2 資料集鎖定 manifest 產生器")
    parser.add_argument(
        "--photos-dir", default=None, metavar="DIR",
        help="held-out 照片目錄（預設 assets/photos_heldout；必須位於 repo 內；--legacy 固定使用 assets/photos/，不可與本參數併用）",
    )
    parser.add_argument(
        "--legacy", action="store_true",
        help="降級路徑：改用 assets/photos/ 舊五張，manifest 標 degraded: true（固定使用該目錄，不可與 --photos-dir 併用）",
    )
    parser.add_argument(
        "--dry", default=None, metavar="WAV",
        help="自錄乾聲（必須位於 repo 內；預設 assets/dry/clap_synth.wav）——要與 t17r2_blind_test.py --dry 給同一個檔，manifest 鎖定的才是盲測實際用的乾聲",
    )
    parser.add_argument(
        "--out", default=None, metavar="PATH",
        help="輸出路徑（預設 output/mvp_acceptance_r2/DATASET_MANIFEST.json）",
    )
    args = parser.parse_args()
    if args.legacy and args.photos_dir is not None:
        parser.error("--legacy 固定使用 assets/photos/，不可與 --photos-dir 併用")
    photos_dir = Path(args.photos_dir) if args.photos_dir else None
    dry_path = Path(args.dry) if args.dry else None
    out_path = Path(args.out) if args.out else None
    return run(legacy=args.legacy, photos_dir=photos_dir, out_path=out_path, dry_path=dry_path)


if __name__ == "__main__":
    sys.exit(main())
