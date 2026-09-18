#!/usr/bin/env python3
"""T-57／T-17-R2 步驟 1：R2 資料集鎖定 manifest 產生器。

跑法：
    python scripts/t17r2_dataset_manifest.py                 # held-out 路徑
    python scripts/t17r2_dataset_manifest.py --legacy         # 降級：沿用 assets/photos/ 舊五張
輸出：`output/mvp_acceptance_r2/DATASET_MANIFEST.json`（`--out` 可換路徑）

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
- `dry`：目前預設乾聲檔（`assets/dry/clap_synth.wav`）的 path＋sha256——鎖住
  「這次驗收用的乾聲版本」，不是鎖定使用者屆時 `--dry` 選哪一個檔案
  （那個選擇記在 `t17r2_blind_test.py` 產出的 `blind_test/MANIFEST.json`）。
"""

from __future__ import annotations

import argparse
import json
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

    rev = provenance.git_revision(cwd=repo_root, scope=dirty_scope)
    if rev["dirty"]:
        errors.append(
            f"git status --porcelain -- {' '.join(dirty_scope)} 非空："
            "工作樹不乾淨，不得鎖定資料集（先 commit 或還原）"
        )
        return None, errors

    if legacy:
        photos_dir = (repo_root / "assets" / "photos") if photos_dir is None else photos_dir
        categories = list(t17_blind_test.SPACES) if categories is None else categories
        ground_truth: dict = {}
    else:
        photos_dir = (repo_root / "assets" / "photos_heldout") if photos_dir is None else photos_dir
        categories = list(common.HELDOUT_SPACES) if categories is None else categories
        ground_truth = common.load_ground_truth_heldout(photos_dir)

    heldout_photos = []
    for category, stem in categories:
        photo = common.find_photo(photos_dir, stem)
        if photo is None:
            errors.append(f"找不到照片：{photos_dir}/{stem}.<jpg|jpeg|png|heic>")
            continue
        is_car = category == common.CAR_CATEGORY_LABEL
        dims_m = None
        if not legacy:
            dims_m = ground_truth.get(stem, {}).get("dims_m")
        heldout_photos.append(
            {
                "stem": stem,
                "category": category,
                "path": str(photo.relative_to(repo_root)),
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

    dry_path = (repo_root / "assets" / "dry" / "clap_synth.wav") if dry_path is None else dry_path
    dry_entry = None
    if not dry_path.exists():
        errors.append(f"找不到乾聲檔：{dry_path}")
    else:
        dry_entry = {"path": str(dry_path.relative_to(repo_root)), "sha256": _sha256(dry_path)}

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
) -> int:
    out_path = (repo_root / "output" / "mvp_acceptance_r2" / "DATASET_MANIFEST.json") if out_path is None else out_path
    manifest, errors = build_manifest(repo_root=repo_root, legacy=legacy, photos_dir=photos_dir)
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
        help="held-out 照片目錄（預設 assets/photos_heldout；--legacy 時忽略此參數）",
    )
    parser.add_argument(
        "--legacy", action="store_true",
        help="降級路徑：改用 assets/photos/ 舊五張，manifest 標 degraded: true",
    )
    parser.add_argument(
        "--out", default=None, metavar="PATH",
        help="輸出路徑（預設 output/mvp_acceptance_r2/DATASET_MANIFEST.json）",
    )
    args = parser.parse_args()
    photos_dir = Path(args.photos_dir) if args.photos_dir else None
    out_path = Path(args.out) if args.out else None
    return run(legacy=args.legacy, photos_dir=photos_dir, out_path=out_path)


if __name__ == "__main__":
    sys.exit(main())
