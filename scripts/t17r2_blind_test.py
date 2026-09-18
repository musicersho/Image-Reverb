#!/usr/bin/env python3
"""T-57／T-17-R2 步驟 3：R2 盲聽配對測試素材產生器（薄包裝，沿用 `t17_blind_test.py`）。

跑法：
    python scripts/t17r2_blind_test.py                 # held-out 五張
    python scripts/t17r2_blind_test.py --legacy         # 降級：舊五張（T-17 用過）
    python scripts/t17r2_blind_test.py --dry assets/dry/真實人聲.wav   # 可選：換乾聲
輸出：`output/mvp_acceptance_r2/blind_test/`（5 組試聽檔＋作答表＋MANIFEST）、
      `output/mvp_acceptance_r2/blind_test_ANSWERS.json`。

**與 `t17_blind_test.py` 的差異（僅此三點，其餘邏輯——溯源驗證、打亂手法、
mtime 對齊——原封不動重用該檔的 `verify_source_provenance()`）**：
1. `SHUFFLE_SEED` 換一個新種子（`t17r2_common.SHUFFLE_SEED = 20260916`；
   T-17 用的是 20260830），確保這次的打亂順序與 T-17 不同。
2. **輸出目錄已有 `sample_*.wav` → exit 1 拒絕覆寫**。T-17 版本每次重跑都
   `shutil.rmtree()` 清空重來；R2 是正式驗收（首跑即最終，`t18r2` 卡的中途
   commit 之後不得重生任何樣本），拿掉「靜默覆寫」這條路，逼問題在
   commit 之前就被發現，不是事後才發現「其實跑了兩次」。
3. 可選 `--dry <wav>`：給了就用 `scripts/convolve.py` 的 `convolve_signals()`／
   `normalize_peak()` 把 `ir_mono.wav` 與這個乾聲卷積成新的試聽檔（純濕聲，
   不做乾濕混音——`--mix` 是 `convolve.py` CLI 才有的選項，這裡不用）；
   沒給就跟 T-17 一樣直接複製既有 `wet_preview.wav`（pipeline 內建用
   `assets/dry/clap_synth.wav`、mix=0.6 生成，逐位元複製，不重新卷積）。
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import soundfile as sf  # noqa: E402

from src.image_reverb import provenance  # noqa: E402
import convolve  # noqa: E402
import t17_blind_test  # noqa: E402
import t17r2_common as common  # noqa: E402


def run(
    *,
    repo_root: Path = REPO_ROOT,
    out_dir: Path | None = None,
    legacy: bool = False,
    categories: list[tuple[str, str]] | None = None,
    photos_dir: Path | None = None,
    outputs_dir: Path | None = None,
    materials_path: Path | None = None,
    expected_config: dict[str, object] | None = None,
    dry_path: Path | None = None,
) -> int:
    """主流程。全部參數帶預設值＝真實專案路徑，讓 `test_t17r2_tools.py` 可以指到
    隔離 git repo 重跑同一段邏輯（沿用 `test_t17_provenance.py` 的手法）。
    """
    out_dir = out_dir if out_dir is not None else (repo_root / "output" / "mvp_acceptance_r2" / "blind_test")
    categories = categories if categories is not None else (
        list(t17_blind_test.SPACES) if legacy else list(common.HELDOUT_SPACES)
    )
    photos_dir = photos_dir or (common.LEGACY_PHOTOS_DIR if legacy else common.HELDOUT_PHOTOS_DIR)
    outputs_dir = outputs_dir or (repo_root / "output")
    materials_path = materials_path or (repo_root / "data" / "materials.json")
    expected_config = (
        expected_config if expected_config is not None else t17_blind_test._expected_model_config()
    )

    if out_dir.exists() and any(out_dir.glob("sample_*.wav")):
        print(
            f"❌ 輸出目錄已有 sample_*.wav，拒絕覆寫（首跑即最終，沒有 --force）：{out_dir}",
            file=sys.stderr,
        )
        return 1

    if dry_path is not None and not Path(dry_path).exists():
        print(f"❌ 找不到 --dry 指定的乾聲檔：{dry_path}", file=sys.stderr)
        return 1

    items = []
    stale: list[str] = []
    for space_type, run_name in categories:
        wet = outputs_dir / run_name / "wet_preview.wav"
        ir = outputs_dir / run_name / "ir_mono.wav"
        aj = outputs_dir / run_name / "analysis.json"
        photo = common.find_photo(photos_dir, run_name)
        if photo is None or not wet.exists() or not ir.exists() or not aj.exists():
            print(
                f"❌ 缺少 output/{run_name}/ 或找不到照片 {photos_dir}/{run_name}.*"
                f"（請先跑 `python -m src.image_reverb {photos_dir}/{run_name}.<ext>`）",
                file=sys.stderr,
            )
            return 1

        meta = json.loads(aj.read_text(encoding="utf-8"))
        prov_errs = t17_blind_test.verify_source_provenance(
            meta, photo, materials_path, repo_root, expected_config
        )
        for e in prov_errs:
            stale.append(f"{run_name}：{e}")

        items.append(
            {
                "space_type": space_type,
                "run": run_name,
                "photo": photo,
                "wet": wet,
                "ir": ir,
                "photo_sha256": provenance.sha256_file(photo),
                "ir_sha256": provenance.sha256_file(ir),
                "dims_source": meta.get("dims_source"),
                "confidence": meta.get("confidence"),
                "forced_low_confidence": meta.get("forced_low_confidence", False),
                "source_provenance": meta.get("provenance"),
            }
        )

    if stale:
        print("❌ 溯源驗證失敗（可能拿舊產物驗收新程式，或環境已變更）：", file=sys.stderr)
        for m in stale:
            print(f"   - {m}", file=sys.stderr)
        return 1

    import random

    order = list(range(len(items)))
    random.Random(common.SHUFFLE_SEED).shuffle(order)

    out_dir.mkdir(parents=True, exist_ok=True)

    dry_signal = None
    dry_sr = None
    if dry_path is not None:
        dry_signal, dry_sr = convolve.load_audio(str(dry_path))

    def _rel_or_str(p: Path) -> str:
        try:
            return str(p.resolve().relative_to(repo_root))
        except ValueError:
            return str(p)

    answers = []
    for slot, idx in enumerate(order, start=1):
        it = items[idx]
        dst_wet = out_dir / f"sample_{slot}.wav"
        dst_ir = out_dir / f"sample_{slot}_IR.wav"
        shutil.copyfile(it["ir"], dst_ir)
        if dry_signal is not None:
            ir_signal, ir_sr = convolve.load_audio(str(it["ir"]))
            target_sr = max(dry_sr, ir_sr)
            d = convolve.resample_to(dry_signal, dry_sr, target_sr)
            i = convolve.resample_to(ir_signal, ir_sr, target_sr)
            d, i, _ = convolve.match_channels(d, i)
            wet_signal = convolve.normalize_peak(convolve.convolve_signals(d, i))
            sf.write(str(dst_wet), wet_signal, target_sr, subtype="PCM_24")
        else:
            shutil.copyfile(it["wet"], dst_wet)
        it["wet_sha256"] = provenance.sha256_file(dst_wet)

        answers.append(
            {
                "sample": f"sample_{slot}",
                "correct_space_type": it["space_type"],
                "source_run": it["run"],
                "source_photo": _rel_or_str(it["photo"]),
            }
        )

    for p in sorted(out_dir.iterdir()):
        os.utime(p, (1000000000, 1000000000))

    packaging_rev = provenance.git_revision(cwd=repo_root)
    dry_manifest_entry = None
    if dry_path is not None:
        dry_manifest_entry = {
            "path": _rel_or_str(Path(dry_path)),
            "sha256": provenance.sha256_file(dry_path),
        }
    else:
        default_dry = repo_root / "assets" / "dry" / "clap_synth.wav"
        if default_dry.exists():
            dry_manifest_entry = {
                "path": _rel_or_str(default_dry),
                "sha256": provenance.sha256_file(default_dry),
                "note": "未給 --dry：沿用既有 wet_preview.wav（pipeline 內建以此乾聲、mix=0.6 生成，本次未重新卷積）",
            }

    manifest = {
        "packaging_git_revision": packaging_rev,
        "shuffle_seed": common.SHUFFLE_SEED,
        "degraded": bool(legacy),
        "dry": dry_manifest_entry,
        "generated_from": [
            {
                k: it[k]
                for k in (
                    "run",
                    "photo_sha256",
                    "ir_sha256",
                    "wet_sha256",
                    "dims_source",
                    "confidence",
                    "forced_low_confidence",
                    "source_provenance",
                )
            }
            for it in items
        ],
    }
    (out_dir / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    key_path = out_dir.parent / "blind_test_ANSWERS.json"
    key_path.write_text(
        json.dumps(
            {"shuffle_seed": common.SHUFFLE_SEED, "answers": answers},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    sheet = out_dir / "作答表.md"
    sheet.write_text(
        "# T-17-R2 §7-1 盲聽配對作答表\n\n"
        "請依序聽 `sample_1.wav` ～ `sample_5.wav`，在下表填入你認為的空間類型。"
        "**作答完成前請不要打開 `../blind_test_ANSWERS.json`。**\n\n"
        "可選的空間類型（5 選 1，每個只會用到一次）：\n"
        "浴室 ／ 客廳臥室 ／ 教堂大空間 ／ 走廊樓梯間 ／ 車內\n\n"
        "| 檔案 | 你聽到的空間類型 | 備註（聽感、有沒有鐵筒子味）|\n"
        "|---|---|---|\n"
        + "".join(f"| `sample_{i}.wav` | | |\n" for i in range(1, len(items) + 1))
        + "\n`sample_N_IR.wav` 是對應的原始 IR（不含乾聲），§7-3 要載入 convolution reverb 測試時用這個。\n",
        encoding="utf-8",
    )

    print(f"✅ 盲聽素材：{out_dir}/（{len(items)} 組，檔名不洩露答案）")
    print(f"   作答表：{sheet}")
    print(f"   答案鍵：{key_path}（作答前請勿打開）")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="T-17-R2 §7-1 盲聽配對測試素材產生器")
    parser.add_argument("--legacy", action="store_true", help="降級：改用 assets/photos/ 舊五張")
    parser.add_argument("--dry", default=None, metavar="WAV", help="可選：用這個乾聲重新卷積試聽檔")
    args = parser.parse_args()
    dry_path = Path(args.dry) if args.dry else None
    return run(legacy=args.legacy, dry_path=dry_path)


if __name__ == "__main__":
    sys.exit(main())
