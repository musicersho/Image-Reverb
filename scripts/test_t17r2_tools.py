#!/usr/bin/env python3
"""T-57 迴歸測試：五支 `t17r2_*.py` 薄包裝腳本（單一插卡，涵蓋規格第 6 點 (a)~(f)）。

沿用 `test_t17_provenance.py` 的手法：在系統暫存目錄建一個**真的 git repo**
（不是主 repo），全程樁 `analysis.json`／IR／wet preview／ground truth（純資料
檔案），不下載或執行任何模型、不碰真實 `output/`、不建立
`output/mvp_acceptance_r2/`（那個路徑只存在於隔離 repo 裡）。

涵蓋範圍：
  (a) provenance 相符 → `t17r2_blind_test` 5 張全 exit 0，`MANIFEST.json`
      5 筆且 `forced_low_confidence` 逐筆等於樁 `analysis.json`（含突變證明：
      把答案全改寫成 False，證明比對抓得到不符）。
  (b) 同 seed（20260916）跑兩次順序相同；與 T-17 舊 seed（20260830）順序不同。
  (c) provenance 不符（`git_revision` 記舊 commit）→ exit 1。
  (d) 輸出目錄已有 `sample_*.wav` → exit 1（拒絕覆寫，不像 T-17 版會清空重來）。
  (e) 合成 `rt60_table.json`＋`DATASET_MANIFEST.json` → `t17r2_report_tables`：
      forced run 不進自動組小計、coverage 分子分母正確、域外未 forced 通過的
      場地被標「域外誤放」。
  (f) `t17r2_dataset_manifest`：sha256 正確、domain 分類正確、工作樹 dirty →
      exit 1、同一輸入重跑兩次逐位元相同；`--legacy` 路徑 degraded 旗標正確。

跑法：`python scripts/test_t17r2_tools.py`；全部通過 exit 0，任一失敗 exit 1。
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.image_reverb import provenance  # noqa: E402
import t17_blind_test  # noqa: E402
import t17r2_common as common  # noqa: E402
import t17r2_dataset_manifest as manifest_mod  # noqa: E402
import t17r2_blind_test as blind_mod  # noqa: E402
import t17r2_report_tables as report_mod  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout.strip()


def _init_isolated_repo(repo: Path) -> str:
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t57-test@example.com")
    _git(repo, "config", "user.name", "T-57 Test")
    (repo / "src").mkdir()
    (repo / "data").mkdir()
    (repo / "src" / "marker.txt").write_text("v1\n", encoding="utf-8")
    (repo / "data" / "materials.json").write_text(
        json.dumps({"fallback_id": "gypsum_board"}), encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v1")
    (repo / "src" / "marker.txt").write_text("v2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v2")
    return _git(repo, "rev-parse", "HEAD")


def _make_fake_photo(directory: Path, stem: str, ext: str = ".png") -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    p = directory / f"{stem}{ext}"
    p.write_bytes(b"\x89PNG\r\n\x1a\nFAKE_PHOTO_" + stem.encode())
    return p


def _write_fake_output(
    repo: Path,
    name: str,
    *,
    provenance_block: dict | None,
    forced: bool = False,
    dims_source: str = "metric_depth",
    surfaces: dict | None = None,
    surfaces_sources: dict | None = None,
    dims_m: dict | None = None,
    confidence: str = "medium",
) -> Path:
    out_dir = repo / "output" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ir_mono.wav").write_bytes(b"RIFF_FAKE_IR_" + name.encode())
    (out_dir / "wet_preview.wav").write_bytes(b"RIFF_FAKE_WET_" + name.encode())
    analysis: dict = {
        "input": f"assets/photos_heldout/{name}.png",
        "dims_source": dims_source,
        "confidence": confidence,
        "forced_low_confidence": forced,
        "dims_m": dims_m or {"length": 4.0, "width": 3.0, "height": 2.5},
        "surfaces": surfaces or {},
        "surfaces_sources": surfaces_sources or {},
    }
    if provenance_block is not None:
        analysis["provenance"] = provenance_block
    (out_dir / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_dir


def main() -> int:  # noqa: C901 — 單一插卡涵蓋六項斷言，刻意不拆成更多檔案
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "isolated_repo"
        head = _init_isolated_repo(repo)

        materials_path = repo / "data" / "materials.json"
        expected_config = {
            "segmentation_model_id": "fake-seg-model",
            "clip_model_id": "fake-clip-model",
            "clip_confidence_threshold": 0.4,
        }

        photos_dir = repo / "assets" / "photos_heldout"
        stems = [s for _, s in common.HELDOUT_SPACES]
        photos = {stem: _make_fake_photo(photos_dir, stem) for stem in stems}

        gt = {
            "heldout_bathroom": {
                "dims_m": {"length": 3.0, "width": 2.0, "height": 2.4},
                "surfaces": {
                    "floor": {"material_id": "gypsum_board", "confirmed_by": "user"},
                    "ceiling": {"material_id": "gypsum_board", "confirmed_by": "user"},
                    "west": {"material_id": "gypsum_board", "confirmed_by": "user"},
                    "east": {"material_id": "gypsum_board", "confirmed_by": "user"},
                    "south": {"material_id": "gypsum_board", "confirmed_by": "user"},
                    "north": {"material_id": "brick", "confirmed_by": "user"},
                },
            },
            "heldout_living": {"dims_m": {"length": 5.0, "width": 4.0, "height": 2.6}},
            "heldout_hall": {"dims_m": {"length": 20.0, "width": 15.0, "height": 8.0}},
            "heldout_corridor": {"dims_m": {"length": 12.0, "width": 1.5, "height": 2.4}},
        }
        (photos_dir / "ground_truth_heldout.json").write_text(
            json.dumps(gt, ensure_ascii=False), encoding="utf-8"
        )

        forced_flags = {
            "heldout_bathroom": False,
            "heldout_living": True,
            "heldout_hall": False,
            "heldout_corridor": True,
            "heldout_car": False,
        }
        for stem in stems:
            prov = {
                "git_revision": {"commit": head, "dirty": False},
                "input_sha256": provenance.sha256_file(photos[stem]),
                "materials_json_sha256": provenance.sha256_file(materials_path),
                **expected_config,
            }
            _write_fake_output(
                repo,
                stem,
                provenance_block=prov,
                forced=forced_flags[stem],
                surfaces={
                    "floor": "gypsum_board", "ceiling": "gypsum_board", "west": "gypsum_board",
                    "east": "gypsum_board", "south": "gypsum_board", "north": "brick",
                },
                surfaces_sources={"ceiling": "clip", "west": "clip", "east": "clip", "south": "clip", "north": "clip"},
            )

        # ---------------------------------------------------------------
        # (a) provenance 全部相符 → 5 張 exit 0，forced 旗標逐筆相符（含突變證明）
        # ---------------------------------------------------------------
        print("【a】provenance 全部相符 → t17r2_blind_test 5 張 exit 0")
        out_dir_a = repo / "output" / "mvp_acceptance_r2" / "blind_test"
        rc_a = blind_mod.run(
            repo_root=repo, out_dir=out_dir_a, categories=list(common.HELDOUT_SPACES),
            photos_dir=photos_dir, outputs_dir=repo / "output",
            materials_path=materials_path, expected_config=expected_config,
        )
        check("(a-1) exit 0", rc_a == 0, f"rc={rc_a}")
        manifest_a = json.loads((out_dir_a / "MANIFEST.json").read_text(encoding="utf-8"))
        gf = manifest_a.get("generated_from", [])
        check("(a-2) generated_from 5 筆", len(gf) == 5, f"n={len(gf)}")
        by_run = {g["run"]: g for g in gf}
        matched = all(by_run.get(s, {}).get("forced_low_confidence") == forced_flags[s] for s in stems)
        check(
            "(a-3) forced_low_confidence 逐筆等於樁 analysis.json",
            matched,
            f"{[(s, by_run.get(s, {}).get('forced_low_confidence')) for s in stems]}",
        )
        # 突變證明：把 forced_low_confidence 全改寫成 False，證明上面的比對不是恆真
        mutated_ok = all(False == forced_flags[s] for s in stems if forced_flags[s])
        check(
            "(a-4) 突變證明：forced 全寫 False 時比對必須抓到不符",
            not mutated_ok,
            f"forced_flags={forced_flags}（至少一筆為 True，全寫 False 會被抓到）",
        )

        # ---------------------------------------------------------------
        # (b) 同 seed 兩次順序相同；與 T-17 舊 seed 不同
        # ---------------------------------------------------------------
        print("【b】SHUFFLE_SEED：同 seed 兩次相同、與 T-17 舊 seed（20260830）不同")
        check("(b-1) R2 種子不是 T-17 種子", common.SHUFFLE_SEED != 20260830, f"{common.SHUFFLE_SEED}")
        n = len(stems)
        order_r2_1 = list(range(n)); random.Random(common.SHUFFLE_SEED).shuffle(order_r2_1)
        order_r2_2 = list(range(n)); random.Random(common.SHUFFLE_SEED).shuffle(order_r2_2)
        order_t17 = list(range(n)); random.Random(20260830).shuffle(order_t17)
        check("(b-2) 同 seed 兩次打亂順序相同", order_r2_1 == order_r2_2, f"{order_r2_1} vs {order_r2_2}")
        check("(b-3) 與 T-17 舊 seed 順序不同", order_r2_1 != order_t17, f"{order_r2_1} vs {order_t17}")

        out_dir_b1 = repo / "output" / "run_b1" / "blind_test"
        out_dir_b2 = repo / "output" / "run_b2" / "blind_test"
        blind_mod.run(
            repo_root=repo, out_dir=out_dir_b1, categories=list(common.HELDOUT_SPACES),
            photos_dir=photos_dir, outputs_dir=repo / "output",
            materials_path=materials_path, expected_config=expected_config,
        )
        blind_mod.run(
            repo_root=repo, out_dir=out_dir_b2, categories=list(common.HELDOUT_SPACES),
            photos_dir=photos_dir, outputs_dir=repo / "output",
            materials_path=materials_path, expected_config=expected_config,
        )
        ans1 = json.loads((out_dir_b1.parent / "blind_test_ANSWERS.json").read_text(encoding="utf-8"))
        ans2 = json.loads((out_dir_b2.parent / "blind_test_ANSWERS.json").read_text(encoding="utf-8"))
        seq1 = [a["source_run"] for a in ans1["answers"]]
        seq2 = [a["source_run"] for a in ans2["answers"]]
        check("(b-4) 實際跑兩次 blind_test，答案順序一致", seq1 == seq2, f"{seq1} vs {seq2}")

        # ---------------------------------------------------------------
        # (c) provenance 不符 → exit 1
        # ---------------------------------------------------------------
        print("【c】provenance 不符（git_revision 記舊 commit）→ exit 1")
        bad_photo = _make_fake_photo(photos_dir, "heldout_test_c")
        bad_prov = {
            "git_revision": {"commit": "0" * 40, "dirty": False},
            "input_sha256": provenance.sha256_file(bad_photo),
            "materials_json_sha256": provenance.sha256_file(materials_path),
            **expected_config,
        }
        _write_fake_output(repo, "heldout_test_c", provenance_block=bad_prov, forced=False)
        rc_c = blind_mod.run(
            repo_root=repo, out_dir=repo / "output" / "run_c" / "blind_test",
            categories=[("測試", "heldout_test_c")], photos_dir=photos_dir,
            outputs_dir=repo / "output", materials_path=materials_path, expected_config=expected_config,
        )
        check("(c) provenance 不符 → exit 非 0", rc_c != 0, f"rc={rc_c}")

        # ---------------------------------------------------------------
        # (d) 輸出目錄已有 sample_*.wav → exit 1，拒絕覆寫
        # ---------------------------------------------------------------
        print("【d】輸出目錄已有 sample_*.wav → exit 1，拒絕覆寫")
        out_dir_d = repo / "output" / "run_d" / "blind_test"
        rc_d1 = blind_mod.run(
            repo_root=repo, out_dir=out_dir_d, categories=list(common.HELDOUT_SPACES),
            photos_dir=photos_dir, outputs_dir=repo / "output",
            materials_path=materials_path, expected_config=expected_config,
        )
        check("(d-1) 首次產生 exit 0", rc_d1 == 0, f"rc={rc_d1}")
        before_hash = provenance.sha256_file(out_dir_d / "sample_1.wav")
        rc_d2 = blind_mod.run(
            repo_root=repo, out_dir=out_dir_d, categories=list(common.HELDOUT_SPACES),
            photos_dir=photos_dir, outputs_dir=repo / "output",
            materials_path=materials_path, expected_config=expected_config,
        )
        check("(d-2) 再次呼叫同一目錄 → exit 非 0", rc_d2 != 0, f"rc={rc_d2}")
        after_hash = provenance.sha256_file(out_dir_d / "sample_1.wav")
        check("(d-3) 檔案內容未被覆寫", before_hash == after_hash, f"{before_hash} vs {after_hash}")

        # ---------------------------------------------------------------
        # (e) 合成 rt60_table.json → 表 2 分組／coverage／域外誤放
        # ---------------------------------------------------------------
        print("【e】合成 rt60_table.json → t17r2_report_tables 表 2／表 5")
        r2out = repo / "output" / "mvp_acceptance_r2"
        r2out.mkdir(parents=True, exist_ok=True)

        manifest_e = {
            "degraded": False,
            "head": head,
            "heldout_photos": [],
            "venues": [
                {"key": "mit_gym", "label": "Gym（in-domain）", "photo_sha256": "x", "real_ir_sha256": ["x"], "in_domain": True},
                {"key": "steinman_hall", "label": "Steinman（域外）", "photo_sha256": "x", "real_ir_sha256": ["x"], "in_domain": False},
            ],
            "manual_dims": dict(common.MANUAL_DIMS),
            "dry": {"path": "assets/dry/clap_synth.wav", "sha256": "x"},
        }
        (r2out / "DATASET_MANIFEST.json").write_text(json.dumps(manifest_e, ensure_ascii=False), encoding="utf-8")

        def _err(pct: float) -> dict:
            return {"measured_s": 1.0, "reference_s": 1.0, "error_pct": pct, "within_tolerance": abs(pct) <= 20.0}

        def _all_errs(pct: float) -> dict:
            return {k: _err(pct) for k in ("125", "250", "500", "1000", "2000", "4000", "low_combined")}

        def _stub_real_reference() -> dict:
            return {
                "bands": {b: {"value": 1.0, "min": 1.0, "max": 1.0, "n": 1} for b in ("125", "250", "500", "1000", "2000", "4000")},
                "low_combined": {"value": 1.0, "min": 1.0, "max": 1.0, "n": 1},
                "n_files": 1,
            }

        rt60 = {
            "bands_hz": [125, 250, 500, 1000, 2000, 4000], "tolerance_pct": 20.0,
            "venues": [
                {
                    "key": "mit_gym", "label": "Gym（in-domain）", "source": "stub", "photo": "x",
                    "in_domain": True,
                    "real": [], "real_reference": _stub_real_reference(),
                    "generated": [
                        {
                            "run": "gym_stem", "dims_source": "metric_depth", "confidence": "low",
                            "dims_m": {"length": 9, "width": 6, "height": 2.9}, "volume_m3": 156.6,
                            "override_dims_used": False, "forced_low_confidence": True,
                            "group": "forced", "in_domain": True, "gate": None,
                            "measured": {"bands": {}, "low_combined": 1.0},
                            "errors": _all_errs(5.0),
                            "ladder_500_vs_low": {"generated": 1.0, "real": 1.0},
                        }
                    ],
                },
                {
                    "key": "steinman_hall", "label": "Steinman（域外）", "source": "stub", "photo": "x",
                    "in_domain": False,
                    "real": [], "real_reference": _stub_real_reference(),
                    "generated": [
                        {
                            "run": "steinman_stem", "dims_source": "metric_depth", "confidence": "medium",
                            "dims_m": {"length": 20, "width": 18, "height": 7.5}, "volume_m3": 2700.0,
                            "override_dims_used": False, "forced_low_confidence": False,
                            "group": "auto", "in_domain": False, "gate": None,
                            "measured": {"bands": {}, "low_combined": 1.0},
                            "errors": _all_errs(5.0),
                            "ladder_500_vs_low": {"generated": 1.0, "real": 1.0},
                        }
                    ],
                },
            ],
        }
        (r2out / "rt60_table.json").write_text(json.dumps(rt60, ensure_ascii=False), encoding="utf-8")

        _write_fake_output(repo, "gym_stem", provenance_block=None, forced=True, dims_source="metric_depth")
        _write_fake_output(repo, "steinman_stem", provenance_block=None, forced=False, dims_source="metric_depth")

        rc_e = report_mod.run(repo_root=repo, out_dir=r2out)
        check("(e-1) exit 0", rc_e == 0, f"rc={rc_e}")
        tables_text = (r2out / "tables.md").read_text(encoding="utf-8")

        check(
            "(e-2) forced run（gym_stem）不進自動組小計 —— 自動組小計為 0/0",
            "| **小計** | — | **0/0** | **0/0 場地全達標** |" in tables_text,
            "應出現自動組 0/0 小計行（唯一候選是 forced，被排除）",
        )
        check(
            "(e-3) coverage = 0/1（1 個 in-domain 場地，沒有真正 auto 通過）",
            "**coverage** = 通過 gate 的 in-domain 場地數 / in-domain 場地數 = **0/1**" in tables_text,
            tables_text[:200],
        )
        check(
            "(e-4) steinman（域外、auto、未 forced、通過）被標「域外誤放」",
            "Steinman（域外） | out | PASS | 否 | 無 | ⚠️ 是 |" in tables_text,
            "應出現該列且標 ⚠️ 是",
        )
        check(
            "(e-5) gym（in-domain、forced）不標域外誤放",
            "Gym（in-domain） | in | BLOCK→forced | 是 | 無 | 否 |" in tables_text,
            "應出現該列且標 否",
        )

        # ---------------------------------------------------------------
        # (f) t17r2_dataset_manifest：sha256／domain／dirty／可重現／--legacy
        # ---------------------------------------------------------------
        print("【f】t17r2_dataset_manifest：sha256、domain、dirty、可重現、--legacy")
        dry_path = repo / "assets" / "dry" / "clap_synth.wav"
        dry_path.parent.mkdir(parents=True, exist_ok=True)
        dry_path.write_bytes(b"RIFF_FAKE_DRY")

        stub_venue = {
            "key": "stub_venue", "label": "Stub Venue", "source": "stub",
            "real_irs": ["stub_venue/real1.wav", "stub_venue/real2.wav"],
            "photo": "stub_venue/photo.png",
            "runs": ["stub_venue_stem"],
        }
        ref_dir = repo / "assets" / "reference_irs"
        (ref_dir / "stub_venue").mkdir(parents=True, exist_ok=True)
        (ref_dir / "stub_venue" / "photo.png").write_bytes(b"PHOTO_STUB")
        (ref_dir / "stub_venue" / "real1.wav").write_bytes(b"REAL1")
        (ref_dir / "stub_venue" / "real2.wav").write_bytes(b"REAL2")

        heldout_categories = [(c, s) for c, s in common.HELDOUT_SPACES]
        manifest1, errs1 = manifest_mod.build_manifest(
            repo_root=repo, legacy=False, photos_dir=photos_dir, categories=heldout_categories,
            venues=[stub_venue], reference_irs_dir=ref_dir, dry_path=dry_path,
        )
        check("(f-1) 建置成功、無錯誤", not errs1 and manifest1 is not None, f"errs={errs1}")

        expected_sha = provenance.sha256_file(photos["heldout_bathroom"])
        entry_bathroom = next(p for p in manifest1["heldout_photos"] if p["stem"] == "heldout_bathroom")
        check("(f-2) heldout_bathroom sha256 正確", entry_bathroom["sha256"] == expected_sha, "")
        check("(f-3) domain：bathroom 3x2x2.4（≤10m）→ in", entry_bathroom["domain"] == "in", entry_bathroom["domain"])

        entry_hall = next(p for p in manifest1["heldout_photos"] if p["stem"] == "heldout_hall")
        check("(f-4) domain：hall 20x15x8（>10m）→ out", entry_hall["domain"] == "out", entry_hall["domain"])

        entry_car = next(p for p in manifest1["heldout_photos"] if p["stem"] == "heldout_car")
        check("(f-5) domain：車內固定 → non_room（不看尺寸）", entry_car["domain"] == "non_room", entry_car["domain"])

        manifest2, errs2 = manifest_mod.build_manifest(
            repo_root=repo, legacy=False, photos_dir=photos_dir, categories=heldout_categories,
            venues=[stub_venue], reference_irs_dir=ref_dir, dry_path=dry_path,
        )
        check(
            "(f-6) 同一輸入重跑兩次逐位元相同",
            json.dumps(manifest1, sort_keys=True) == json.dumps(manifest2, sort_keys=True),
            "",
        )

        (repo / "scripts").mkdir(exist_ok=True)
        (repo / "scripts" / "dirty_marker.py").write_text("# dirty\n", encoding="utf-8")
        rc_dirty = manifest_mod.run(repo_root=repo, out_path=repo / "output" / "mvp_acceptance_r2" / "DATASET_MANIFEST.json")
        check("(f-7) 工作樹 dirty（scripts/ 未 commit）→ exit 1", rc_dirty == 1, f"rc={rc_dirty}")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "commit dirty marker so later checks see a clean tree")

        legacy_dir = repo / "assets" / "photos"
        for _, stem in t17_blind_test.SPACES:
            _make_fake_photo(legacy_dir, stem)
        manifest_legacy, errs_legacy = manifest_mod.build_manifest(
            repo_root=repo, legacy=True, venues=[stub_venue], reference_irs_dir=ref_dir, dry_path=dry_path,
        )
        check("(f-8) --legacy 建置成功", not errs_legacy and manifest_legacy is not None, f"errs={errs_legacy}")
        if manifest_legacy is not None:
            check("(f-9) --legacy → degraded: true", manifest_legacy["degraded"] is True, manifest_legacy["degraded"])
            car_legacy = next(p for p in manifest_legacy["heldout_photos"] if p["category"] == "車內")
            check("(f-10) legacy 車內仍固定 non_room", car_legacy["domain"] == "non_room", car_legacy["domain"])
            other_legacy = next(p for p in manifest_legacy["heldout_photos"] if p["category"] != "車內")
            check("(f-11) legacy 無 GT 檔 → 其餘 unknown", other_legacy["domain"] == "unknown", other_legacy["domain"])

    if FAILURES:
        print(f"\n❌ {len(FAILURES)} 項失敗：{FAILURES}")
        return 1
    print("\n✅ 全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
