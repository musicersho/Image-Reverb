#!/usr/bin/env python3
"""T-57 迴歸測試：五支 `t17r2_*.py` 薄包裝腳本（單一插卡，涵蓋規格第 6 點 (a)~(f)）。

沿用 `test_t17_provenance.py` 的手法：在系統暫存目錄建一個**真的 git repo**
（不是主 repo），全程樁 `analysis.json`／IR／wet preview／ground truth（純資料
檔案），不下載或執行任何模型、不碰真實 `output/`、不建立
`output/mvp_acceptance_r2/`（那個路徑只存在於隔離 repo 裡）。

涵蓋範圍：
  (a) provenance 相符 → `t17r2_blind_test` 5 張全 exit 0，`MANIFEST.json`
      5 筆且 `forced_low_confidence` 逐筆等於樁 `analysis.json`。
  (b) 同 seed（20260916）跑兩次順序相同；與 T-17 舊 seed（20260830）順序不同。
  (c) provenance 不符（`git_revision` 記舊 commit）→ exit 1。
  (d) 輸出目錄已有 `sample_*.wav` → exit 1（拒絕覆寫，不像 T-17 版會清空重來）。
  (e) 合成 `rt60_table.json`＋`DATASET_MANIFEST.json` → `t17r2_report_tables`：
      forced run 不進自動組小計、coverage 分子分母正確、域外未 forced 通過的
      場地被標「域外誤放」。
  (f) `t17r2_dataset_manifest`：sha256 正確、domain 分類正確、工作樹 dirty →
      exit 1、同一輸入重跑兩次逐位元相同；`--legacy` 路徑 degraded 旗標正確。
  T-57-F1 修正輪追加（新斷言用 `guarded()` 包：功能缺失時記 ❌，不讓整支測試崩潰）：
  (g) R3：`t17r2_blind_test.main()` 把 `--photos-dir` 接進 `run(photos_dir=…)`。
  (h) R4：`t17r2_rt60_table.run()` 缺 `DATASET_MANIFEST.json`／缺場地 key → exit 1，
      不寫 `rt60_table.json`；manifest 齊全時 `in_domain`／`gate` 欄位正確搬運。
  (i) R5：`parse_gate_log()` 只認末行 `exit=<整數>`，缺→`None`；表 5 印「預設路徑
      exit」欄，未記錄／⚠️ 不一致標記正確。
  (j) R6：`t17r2_dataset_manifest` 的 `--dry` 接線（`run(dry_path=…)`、`main()`）。
  (k) 裁定 T-57-D：`tables.md` 錯誤放行率彙總（N／6N／可判／無法判／主率／上下界）
      與測試端獨立重算相同；無來源面在分母內；可判＝0、N＝0 不印 0%；不含「分母固定 6」。
  (l) 小問題：`--legacy` 與 `--photos-dir` CLI 互斥（exit 2）；`--photos-dir`／`--dry`
      在 repo 外 → exit 1＋清楚訊息、無例外；相對路徑（repo 內）可用。

跑法：`python scripts/test_t17r2_tools.py`；全部通過 exit 0，任一失敗 exit 1。
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.image_reverb import provenance  # noqa: E402
import t17_blind_test  # noqa: E402
import t17r2_common as common  # noqa: E402
import t17r2_dataset_manifest as manifest_mod  # noqa: E402
import t17r2_blind_test as blind_mod  # noqa: E402
import t17r2_rt60_table as rt60_mod  # noqa: E402
import t17r2_report_tables as report_mod  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def guarded(name: str, fn) -> None:
    """`fn()` 回傳 `(ok, detail)`。被測功能缺失（拋例外、`SystemExit`）時記成 ❌，
    不讓整支測試崩潰——這樣舊碼上跑新斷言時，每一條都看得到自己的 ❌。
    只接 `Exception`／`SystemExit`；斷言本身的判定不吞。"""
    try:
        ok, detail = fn()
    except (Exception, SystemExit) as exc:  # noqa: BLE001
        ok, detail = False, f"例外：{type(exc).__name__}: {exc}"
    check(name, ok, detail)


def _quiet():
    """把被測函式的 stdout／stderr 收進 StringIO（回傳 `(context, err_buf)`），測試輸出保持乾淨。"""
    err = io.StringIO()
    stack = contextlib.ExitStack()
    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
    stack.enter_context(contextlib.redirect_stderr(err))
    return stack, err


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
        # (a) provenance 全部相符 → 5 張 exit 0，forced 旗標逐筆相符
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

        # ---------------------------------------------------------------
        # (g) R3：t17r2_blind_test.main() 把 --photos-dir 接進 run()
        # ---------------------------------------------------------------
        print("【g】R3：t17r2_blind_test.main() 把 --photos-dir 接進 run(photos_dir=…)")

        def _blind_main_kwargs(argv_tail: list[str]) -> dict:
            quiet, _ = _quiet()
            with quiet, mock.patch.object(blind_mod, "run", return_value=0) as fake_run, \
                    mock.patch.object(sys, "argv", ["t17r2_blind_test.py", *argv_tail]):
                blind_mod.main()
            return dict(fake_run.call_args.kwargs)

        def _g1():
            kw = _blind_main_kwargs(["--photos-dir", "some/dir"])
            return kw.get("photos_dir") == Path("some/dir"), f"photos_dir={kw.get('photos_dir')!r}"

        def _g2():
            kw = _blind_main_kwargs([])
            return ("photos_dir" in kw and kw["photos_dir"] is None), f"kwargs={kw}"

        guarded("(g-1) --photos-dir some/dir → run() 收到 photos_dir == Path('some/dir')", _g1)
        guarded("(g-2) 未給 --photos-dir → run() 收到 photos_dir=None", _g2)

        # ---------------------------------------------------------------
        # (h) R4：t17r2_rt60_table.run() 缺 manifest／缺場地 key → exit 1，不寫表
        # ---------------------------------------------------------------
        print("【h】R4：t17r2_rt60_table.run() 缺 manifest／缺場地 key → exit 1，不寫 rt60_table.json")
        venue_h = {
            "key": "stub_venue_h", "label": "Stub Venue H", "source": "stub",
            "real_irs": ["stub_h/real.wav"], "photo": "stub_h/photo.png", "runs": ["stub_h_stem"],
        }
        venue_h2 = {  # 第二個場地：與第一個 in_domain 相反，才分得出「照 manifest」與「寫死」
            "key": "stub_venue_h2", "label": "Stub Venue H2", "source": "stub",
            "real_irs": ["stub_h/real.wav"], "photo": "stub_h/photo.png", "runs": ["stub_h2_stem"],
        }
        (repo / "assets" / "reference_irs" / "stub_h").mkdir(parents=True, exist_ok=True)
        (repo / "assets" / "reference_irs" / "stub_h" / "real.wav").write_bytes(b"REAL_STUB_H")
        band_keys = ("125", "250", "500", "1000", "2000", "4000")

        def _fake_measure(path):
            # 量測本身（ir_metrics）不是本測試的對象：換成固定值，只驗 run() 的流程與欄位搬運。
            return {
                "file": str(path), "sample_rate": 48000, "channels": 1, "duration_s": 1.0,
                "bands": {b: 1.0 for b in band_keys}, "low_combined": 1.0, "per_channel": [],
            }

        def _run_rt60(out_root: Path, venues: list[dict] | None = None) -> tuple[int, str]:
            quiet, err = _quiet()
            with quiet, mock.patch.object(rt60_mod, "measure_file", side_effect=_fake_measure):
                rc = rt60_mod.run(repo_root=repo, out_root=out_root, venues=venues or [venue_h])
            return rc, err.getvalue()

        def _h1():
            out = repo / "output" / "run_h1"
            rc, err = _run_rt60(out)
            wrote = (out / "rt60_table.json").exists()
            said = "找不到" in err and "DATASET_MANIFEST" in err and "請先跑 scripts/t17r2_dataset_manifest.py" in err
            return (rc == 1 and not wrote and said), \
                f"rc={rc}, rt60_table.json 已寫出={wrote}, 訊息含「找不到…DATASET_MANIFEST…請先跑 scripts/t17r2_dataset_manifest.py」={said}, stderr={err.strip()!r}"

        def _h2():
            out = repo / "output" / "run_h2"
            out.mkdir(parents=True, exist_ok=True)
            (out / "DATASET_MANIFEST.json").write_text(
                json.dumps({"venues": [{"key": "some_other_venue", "in_domain": True}]}), encoding="utf-8"
            )
            rc, err = _run_rt60(out)
            wrote = (out / "rt60_table.json").exists()
            return (rc == 1 and not wrote and "stub_venue_h" in err), \
                f"rc={rc}, rt60_table.json 已寫出={wrote}, stderr={err.strip()!r}"

        def _h3():
            out = repo / "output" / "run_h3"
            (out / "runs").mkdir(parents=True, exist_ok=True)
            (out / "DATASET_MANIFEST.json").write_text(
                json.dumps({"venues": [
                    {"key": "stub_venue_h", "in_domain": True},
                    {"key": "stub_venue_h2", "in_domain": False},
                ]}), encoding="utf-8"
            )
            _write_fake_output(repo, "stub_h_stem", provenance_block=None, forced=True, dims_source="metric_depth")
            _write_fake_output(repo, "stub_h2_stem", provenance_block=None, forced=False, dims_source="metric_depth")
            (out / "runs" / "stub_h_stem.log").write_text(
                f"stdout…\n❌ {rt60_mod.BLOCKED_MARKER}\n\nexit=3\n", encoding="utf-8"
            )
            (out / "runs" / "stub_h_stem.forced.log").write_text("forced 重跑\n\nexit=0\n", encoding="utf-8")
            rc, err = _run_rt60(out, venues=[venue_h, venue_h2])
            table = json.loads((out / "rt60_table.json").read_text(encoding="utf-8"))
            v, v2 = table["venues"]
            g = v["generated"][0]
            g2 = v2["generated"][0]
            ok = (
                rc == 0 and v["in_domain"] is True and g["in_domain"] is True and g["group"] == "forced"
                and g["gate"]["default_exit"] == 3 and g["gate"]["exit_marker_consistent"] is True
                and v2["in_domain"] is False and g2["in_domain"] is False and g2["group"] == "auto" and g2["gate"] is None
            )
            return ok, (
                f"rc={rc}；場地1 in_domain={v['in_domain']} group={g['group']} gate={g['gate']}；"
                f"場地2 in_domain={v2['in_domain']} group={g2['group']} gate={g2['gate']}"
            )

        guarded("(h-1) 無 DATASET_MANIFEST.json → exit 1、不寫 rt60_table.json、stderr＝「找不到 …DATASET_MANIFEST.json，請先跑 scripts/t17r2_dataset_manifest.py」", _h1)
        guarded("(h-2) manifest 缺該場地 key → exit 1、列出缺的 key、不寫 rt60_table.json", _h2)
        def _h4():
            out = repo / "output" / "run_h4"
            out.mkdir(parents=True, exist_ok=True)
            (out / "DATASET_MANIFEST.json").write_text(
                json.dumps({"venues": [{"key": "stub_venue_h"}]}), encoding="utf-8"  # 有 key、缺 in_domain 欄位
            )
            rc, err = _run_rt60(out)
            wrote = (out / "rt60_table.json").exists()
            return (rc == 1 and not wrote and "stub_venue_h" in err and "in_domain" in err), \
                f"rc={rc}, rt60_table.json 已寫出={wrote}, stderr={err.strip()!r}"

        def _h5():
            results = []
            for tag, text in (("bad_json", "{not json"), ("empty", ""), ("list", "[]"), ("venues_null", '{"venues": null}')):
                out = repo / "output" / f"run_h5_{tag}"
                out.mkdir(parents=True, exist_ok=True)
                (out / "DATASET_MANIFEST.json").write_text(text, encoding="utf-8")
                rc, err = _run_rt60(out)  # 例外會被 guarded 記成 ❌（＝裸 Traceback 的等價物）
                results.append((tag, rc, (out / "rt60_table.json").exists(), "DATASET_MANIFEST" in err))
            ok = all(rc == 1 and not wrote and named for _t, rc, wrote, named in results)
            return ok, f"(情境, rc, 已寫表, stderr 含 DATASET_MANIFEST)＝{results}"

        guarded("(h-3) manifest 齊全 → exit 0；兩場地 in_domain 各照 manifest（True／False）；gate 讀 <run>.log（不讀 .forced.log）", _h3)
        guarded("(h-4) manifest 有場地 key 但缺 in_domain 欄位 → exit 1（不得靜默當 False）、不寫表", _h4)
        guarded("(h-5) manifest 壞 JSON／空檔／非 dict／venues 為 null → exit 1、訊息提到 DATASET_MANIFEST、不寫表、無例外", _h5)

        # ---------------------------------------------------------------
        # (i) R5：parse_gate_log() 只認 log 末行 exit=<整數>；表 5 印「預設路徑 exit」
        # ---------------------------------------------------------------
        print("【i】R5：parse_gate_log() 回報真實結束碼（log 末行 exit=<整數>）；表 5 印「預設路徑 exit」")
        logs_i = repo / "output" / "run_i" / "runs"
        logs_i.mkdir(parents=True, exist_ok=True)
        marker = rt60_mod.BLOCKED_MARKER
        stub_logs = {
            "gate_i": f"stdout…\n❌ {marker}：geometry=low\n\n--- stderr ---\n…\n\nexit=3\n",
            "gate_ii": "stdout…\n--- stderr ---\nTraceback (most recent call last):\n  File \"x.py\", line 1\nValueError: boom\n\nexit=1\n",
            "gate_iii": "stdout…\n已產生輸出\n--- stderr ---\n（無）\n",
            "gate_iv": f"stdout…\n❌ {marker}：material=low\n\nexit=0\n",
        }
        for stem, text in stub_logs.items():
            (logs_i / f"{stem}.log").write_text(text, encoding="utf-8")
            # 每個 run 旁邊都放一份 .forced.log（exit=0）：表 5 若誤讀它，「3／1／未記錄」會變成「0」
            (logs_i / f"{stem}.forced.log").write_text("forced 重跑\n\nexit=0\n", encoding="utf-8")
            _write_fake_output(repo, stem, provenance_block=None, forced=False, dims_source="metric_depth")

        def _i1():
            g = rt60_mod.parse_gate_log(logs_i / "gate_i.log")
            return (g["default_exit"] == 3 and g["blocked"] is True and g["exit_marker_consistent"] is True), f"{g}"

        def _i2():
            g = rt60_mod.parse_gate_log(logs_i / "gate_ii.log")
            return (g["default_exit"] == 1 and g["blocked"] is False), f"{g}"

        def _i3():
            g = rt60_mod.parse_gate_log(logs_i / "gate_iii.log")
            return (g["default_exit"] is None and g["exit_marker_consistent"] is None), f"{g}"

        def _i4():
            g = rt60_mod.parse_gate_log(logs_i / "gate_iv.log")
            return (g["default_exit"] == 0 and g["blocked"] is True and g["exit_marker_consistent"] is False), f"{g}"

        def _i5():
            (logs_i / "only_forced.forced.log").write_text("forced 重跑\n\nexit=0\n", encoding="utf-8")
            missing = rt60_mod.parse_gate_log(logs_i / "no_such_run.log")
            forced_only = rt60_mod.parse_gate_log(logs_i / "only_forced.log")
            return (missing is None and forced_only is None), f"不存在→{missing}；只有 .forced.log→{forced_only}"

        def _i6():
            (logs_i / "mid.log").write_text("exit=0\n之後還有輸出\n", encoding="utf-8")
            (logs_i / "two.log").write_text("exit=0\nTraceback…\n\nexit=1\n", encoding="utf-8")
            mid = rt60_mod.parse_gate_log(logs_i / "mid.log")
            two = rt60_mod.parse_gate_log(logs_i / "two.log")
            return (mid["default_exit"] is None and two["default_exit"] == 1), \
                f"中間的 exit= 不算→{mid['default_exit']}；兩行 exit= 取末行→{two['default_exit']}"

        guarded("(i-1) 擋下標記＋末行 exit=3 → default_exit 3、blocked True、consistent True", _i1)
        guarded("(i-2) Traceback＋末行 exit=1 → default_exit 1（不是 0）、blocked False", _i2)
        guarded("(i-3) 無 exit 行 → default_exit None、consistent None", _i3)
        guarded("(i-4) 擋下標記＋末行 exit=0 → consistent False", _i4)
        guarded("(i-5) log 不存在→None；只有 <run>.forced.log 也→None（不讀 forced log）", _i5)
        guarded("(i-6) 只認最後一個非空行的 exit=（中間的不算、多行取末行）", _i6)

        def _item5_lines() -> list[str]:
            items = [
                report_mod.build_item5(
                    label=stem, run_stem=stem, domain="in", gt_surfaces=None,
                    output_root=repo / "output", runs_log_dir=logs_i,
                )
                for stem in stub_logs
            ]
            return report_mod.render_item5_table(items)

        def _last_cell(lines: list[str], stem: str) -> str:
            row = next(ln for ln in lines if ln.startswith(f"| {stem} |"))
            return [c.strip() for c in row.strip().strip("|").split("|")][-1]

        def _i7():
            lines = _item5_lines()
            return ("預設路徑 exit" in lines[0]), lines[0]

        def _i8():
            lines = _item5_lines()
            cells = {stem: _last_cell(lines, stem) for stem in stub_logs}
            ok = (
                cells["gate_i"] == "3" and cells["gate_ii"] == "1" and cells["gate_iii"] == "未記錄"
                and cells["gate_iv"].startswith("0") and "⚠️" in cells["gate_iv"]
                and all("⚠️" not in cells[s] for s in ("gate_i", "gate_ii", "gate_iii"))
            )
            return ok, f"{cells}"

        def _i9():
            cases = {  # log 全文 → 預期 default_exit（None＝格式不符／缺；只認最後一個非空行的 ^exit=(-?\d+)$，半形數字）
                "exit=3junk\n": None,
                "exit=-1\n": -1,
                "exit=3\n\n  \n\n": 3,      # 檔尾多個空行／空白行：仍取最後一個「非空」行
                "Traceback…\r\nexit=3\r\n": 3,  # CRLF
                "exit=３\n": None,              # 全形數字
                "EXIT=3\n": None,
                "exit=3 \n": None,              # 行尾空白
                "exit=3\x0b\n": None,          # \x0b：str.splitlines() 會斷行，這裡不該被讀成 3
                "process exit=3\n": None,
            }
            got = {}
            for i, (text, want) in enumerate(cases.items()):
                pth = logs_i / f"strict_{i}.log"
                pth.write_bytes(text.encode("utf-8"))
                got[text] = (rt60_mod.parse_gate_log(pth)["default_exit"], want)
            bad = {k: v for k, v in got.items() if v[0] != v[1]}
            return not bad, f"{len(cases)} 種變體；(實得, 預期) 不符：{bad}"

        def _i10():
            pth = logs_i / "guidance_only.log"
            pth.write_text("請改用 --override-dims 4x3x2.5\n（沒有 exit 行）\n", encoding="utf-8")
            g = rt60_mod.parse_gate_log(pth)
            return (g["override_dims_guidance"] is True and g["default_exit"] is None and g["blocked"] is False), f"{g}"

        def _i11():
            # gate_result／domain_leak 只依 analysis.json 的 forced_low_confidence，不受 <run>.log 影響
            (logs_i / "indep_unforced.log").write_text(f"❌ {marker}\n\nexit=3\n", encoding="utf-8")  # log 說被擋，但最終輸出未 forced
            (logs_i / "indep_forced.log").write_text("正常\n\nexit=0\n", encoding="utf-8")             # log 說沒擋，但最終輸出是 forced
            _write_fake_output(repo, "indep_unforced", provenance_block=None, forced=False)
            _write_fake_output(repo, "indep_forced", provenance_block=None, forced=True)
            a = report_mod.build_item5(label="a", run_stem="indep_unforced", domain="out", gt_surfaces=None,
                                       output_root=repo / "output", runs_log_dir=logs_i)
            b = report_mod.build_item5(label="b", run_stem="indep_forced", domain="out", gt_surfaces=None,
                                       output_root=repo / "output", runs_log_dir=logs_i)
            ok = (a["gate_result"] == "PASS" and a["domain_leak"] is True
                  and b["gate_result"] == "BLOCK→forced" and b["domain_leak"] is False)
            return ok, f"未 forced（log 說被擋）→{a['gate_result']}／域外誤放={a['domain_leak']}；forced（log 說沒擋）→{b['gate_result']}／域外誤放={b['domain_leak']}"

        guarded("(i-7) 表 5 表頭有「預設路徑 exit」欄", _i7)
        guarded("(i-8) 表 5：exit=3→「3」、exit=1→「1」、無 exit 行→「未記錄」、不一致→「0 ⚠️…」（每個 run 旁另有 exit=0 的 .forced.log，不得被讀到）", _i8)
        guarded("(i-9) 嚴格度：exit=3junk／全形數字／EXIT=3／行尾空白／\\x0b／process exit=3→None；exit=-1→-1；檔尾空行、CRLF→照取", _i9)
        guarded("(i-10) 末行不是 exit= 時：override_dims_guidance 仍照 log 內容、default_exit＝None", _i10)
        guarded("(i-11) gate_result／域外誤放只依 forced_low_confidence（log 說被擋／沒擋都不改變判定）", _i11)

        # ---------------------------------------------------------------
        # (j) R6：t17r2_dataset_manifest 的 --dry 接線
        # ---------------------------------------------------------------
        print("【j】R6：t17r2_dataset_manifest 的 --dry 接線（run(dry_path=…)、main()）")
        second_dry = repo / "assets" / "dry" / "my_voice.wav"
        second_dry.write_bytes(b"RIFF_FAKE_SECOND_DRY")

        def _manifest_run(**kwargs) -> tuple[int, str]:
            # run() 沒有 venues 參數：把 t17_rt60_table.VENUES 暫換成樁場地（真實 8 場地的檔案不在隔離 repo）。
            quiet, err = _quiet()
            with quiet, mock.patch.object(manifest_mod.t17_rt60_table, "VENUES", [stub_venue]):
                rc = manifest_mod.run(repo_root=repo, **kwargs)
            return rc, err.getvalue()

        def _j1():
            out = repo / "output" / "run_j1" / "DATASET_MANIFEST.json"
            rc, err = _manifest_run(photos_dir=photos_dir, out_path=out, dry_path=second_dry)
            m = json.loads(out.read_text(encoding="utf-8"))
            ok = (
                rc == 0 and m["dry"]["path"] == "assets/dry/my_voice.wav"
                and m["dry"]["sha256"] == provenance.sha256_file(second_dry)
            )
            return ok, f"rc={rc}, dry={m['dry']}"

        def _j2():
            out = repo / "output" / "run_j2" / "DATASET_MANIFEST.json"
            rc, err = _manifest_run(photos_dir=photos_dir, out_path=out)
            m = json.loads(out.read_text(encoding="utf-8"))
            ok = (
                rc == 0 and m["dry"]["path"] == "assets/dry/clap_synth.wav"
                and m["dry"]["sha256"] == provenance.sha256_file(dry_path)
            )
            return ok, f"rc={rc}, dry={m['dry']}"

        def _manifest_main_kwargs(argv_tail: list[str]) -> dict:
            quiet, _ = _quiet()
            with quiet, mock.patch.object(manifest_mod, "run", return_value=0) as fake_run, \
                    mock.patch.object(sys, "argv", ["t17r2_dataset_manifest.py", *argv_tail]):
                manifest_mod.main()
            return dict(fake_run.call_args.kwargs)

        def _j3():
            kw = _manifest_main_kwargs(["--dry", "some/voice.wav"])
            return kw.get("dry_path") == Path("some/voice.wav"), f"dry_path={kw.get('dry_path')!r}"

        def _j4():
            kw = _manifest_main_kwargs([])
            return ("dry_path" in kw and kw["dry_path"] is None), f"kwargs={kw}"

        guarded("(j-1) run(dry_path=第二個乾聲) → manifest dry.path／dry.sha256 等於該檔", _j1)
        guarded("(j-2) 未給 dry_path → manifest dry 仍是 assets/dry/clap_synth.wav（原行為不變）", _j2)
        guarded("(j-3) main() --dry some/voice.wav → run() 收到 dry_path == Path('some/voice.wav')", _j3)
        guarded("(j-4) main() 未給 --dry → run() 收到 dry_path=None", _j4)

        # ---------------------------------------------------------------
        # (k) 裁定 T-57-D：tables.md 錯誤放行率彙總＝測試端從輸入獨立重算
        # ---------------------------------------------------------------
        print("【k】裁定 T-57-D：tables.md 錯誤放行率彙總（N／6N／可判／無法判／主率／上下界）")
        surf_names = ("floor", "ceiling", "west", "east", "south", "north")
        gyp = "gypsum_board"

        def _k_run(tag: str, spec: dict, gt: dict | None, *, forced: bool = False, logs: dict | None = None) -> str:
            """建樁（output/<stem>/analysis.json、held-out GT、manifest、rt60 表）→ report_mod.run → 回傳 tables.md。
            spec[stem][face] = (材質 id, 來源或 None)；gt[stem][face] = GT 材質 id 或 {"material_id":…, "proxy": True}
            （缺面＝GT 缺）；logs[stem] = 該 run 的預設路徑 log 全文（放在 <out>/runs/<stem>.log）。"""
            out = repo / "output" / f"run_k_{tag}"
            out.mkdir(parents=True, exist_ok=True)
            gt_dir = repo / "assets" / f"photos_heldout_k_{tag}"
            gt_dir.mkdir(parents=True, exist_ok=True)
            hp = []
            for stem, faces in spec.items():
                _write_fake_output(
                    repo, stem, provenance_block=None, forced=forced, dims_source="metric_depth",
                    surfaces={f: m for f, (m, _s) in faces.items()},
                    surfaces_sources={f: s for f, (_m, s) in faces.items() if s is not None},
                )
                hp.append({"stem": stem, "category": f"k-{stem}", "path": f"assets/x/{stem}.png", "sha256": "x", "domain": "in"})
            if gt is not None:
                (gt_dir / "ground_truth_heldout.json").write_text(
                    json.dumps(
                        {s: {"surfaces": {
                            f: (m if isinstance(m, dict) else {"material_id": m, "confirmed_by": "user"})
                            for f, m in g.items()}}
                         for s, g in gt.items()},
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
            (out / "DATASET_MANIFEST.json").write_text(
                json.dumps({"degraded": False, "head": head, "heldout_photos": hp, "venues": [],
                            "manual_dims": {}, "dry": {"path": "x", "sha256": "x"}}, ensure_ascii=False),
                encoding="utf-8",
            )
            (out / "rt60_table.json").write_text(
                json.dumps({"bands_hz": [125, 250, 500, 1000, 2000, 4000], "tolerance_pct": 20.0, "venues": []}),
                encoding="utf-8",
            )
            for stem, text in (logs or {}).items():
                (out / "runs").mkdir(parents=True, exist_ok=True)
                (out / "runs" / f"{stem}.log").write_text(text, encoding="utf-8")
            quiet, _ = _quiet()
            with quiet:
                rc = report_mod.run(repo_root=repo, out_dir=out, heldout_photos_dir=gt_dir)
            assert rc == 0, f"report_mod.run rc={rc}"
            return (out / "tables.md").read_text(encoding="utf-8")

        def _k_expected(spec: dict, gt: dict | None) -> dict:
            """測試端獨立重算（不呼叫被測程式的任何函式）：逐面比對材質與 GT。"""
            per = {}
            for stem, faces in spec.items():
                right = wrong = unjudged = 0
                for face in surf_names:
                    ref = (gt or {}).get(stem, {}).get(face)
                    if isinstance(ref, dict):  # GT proxy: true 的面照判（裁定 T-57-D §3.2）
                        ref = ref["material_id"]
                    if ref is None or ref == "unknown":
                        unjudged += 1
                    elif faces[face][0] == ref:
                        right += 1
                    else:
                        wrong += 1
                per[stem] = (right, wrong, unjudged)
            return per

        def _k_summary(text: str) -> str:
            lines = [ln for ln in text.splitlines() if ln.startswith("**錯誤放行率彙總**")]
            assert len(lines) == 1, f"彙總行應恰 1 行，實得 {len(lines)}"
            return lines[0]

        # 情境 A：2 張未 forced 通過、共 12 面＝7 ✅＋3 ❌＋2 無法判（其中 k_a2 的 west 是「無來源」面且被判 ❌）
        spec_a = {
            "k_a1": {
                "floor": (gyp, "clip"), "ceiling": (gyp, "clip"), "west": (gyp, "clip"),
                "east": ("carpet", "clip"), "south": ("wood_panel", "clip"), "north": ("brick", "clip"),
            },
            "k_a2": {
                "floor": (gyp, "clip"), "ceiling": (gyp, "clip"), "west": ("carpet", None),
                "east": ("carpet", "clip"), "south": (gyp, "clip"), "north": ("wood_panel", "clip"),
            },
        }
        gt_a = {
            "k_a1": {"floor": gyp, "ceiling": gyp, "west": gyp, "east": gyp, "south": "unknown",
                     "north": {"material_id": "brick", "proxy": True}},  # proxy 面照判（這面材質相符→✅）
            "k_a2": {"floor": gyp, "ceiling": gyp, "west": gyp, "east": gyp, "south": gyp},  # north：GT 缺
        }
        k_cache: dict[str, str] = {}
        logs_a = {"k_a1": "stdout…\n\nexit=1\n"}  # k_a2 沒有 log → 表 5「預設路徑 exit」印「未記錄」

        def _k_tables(tag: str, spec: dict, gt: dict | None, *, forced: bool = False, logs: dict | None = None) -> str:
            # 只在斷言內才真的產表：被測程式拋例外時，記在該條斷言的 ❌ 上，不讓整支測試崩潰。
            if tag not in k_cache:
                k_cache[tag] = _k_run(tag, spec, gt, forced=forced, logs=logs)
            return k_cache[tag]

        per_a = _k_expected(spec_a, gt_a)
        n_a = len(per_a)
        right_a = sum(v[0] for v in per_a.values())
        wrong_a = sum(v[1] for v in per_a.values())
        unjudged_a = sum(v[2] for v in per_a.values())
        judged_a = right_a + wrong_a
        total_a = 6 * n_a

        def _pct(x: int, y: int) -> str:
            return f"{round(100.0 * x / y)}%"

        def _k1():
            line = _k_summary(_k_tables("a", spec_a, gt_a, logs=logs_a))
            want = [
                f"N＝{n_a}", f"6N＝{total_a}", f"可判面數 {judged_a}", f"無法判面數 {unjudged_a}",
                f"{wrong_a}/{judged_a}（{_pct(wrong_a, judged_a)}）",
                f"{wrong_a}/{total_a}（{_pct(wrong_a, total_a)}）",
                f"{wrong_a + unjudged_a}/{total_a}（{_pct(wrong_a + unjudged_a, total_a)}）",
            ]
            hard = [
                "N＝2", "6N＝12", "可判面數 10", "無法判面數 2", "3/10（30%）", "3/12（25%）", "5/12（42%）",
            ]
            missing = [w for w in want + hard if w not in line]
            # 標籤↔數值綁定：以「；」切段，每個比率段必須「以該數值結尾」（子字串包含抓不到主率／下界／上界互換）
            segs = {seg.split("（")[0]: seg for seg in line.split("；")[1:]}
            bound = {
                "主率": f"＝{wrong_a}/{judged_a}（{_pct(wrong_a, judged_a)}）",
                "下界": f"＝{wrong_a}/{total_a}（{_pct(wrong_a, total_a)}）",
                "上界": f"＝{wrong_a + unjudged_a}/{total_a}（{_pct(wrong_a + unjudged_a, total_a)}）",
            }
            hard_bound = {"主率": "＝3/10（30%）", "下界": "＝3/12（25%）", "上界": "＝5/12（42%）"}
            mismatched = [k for k in ("主率", "下界", "上界") if not (segs.get(k, "").endswith(bound[k]) and segs.get(k, "").endswith(hard_bound[k]))]
            return (not missing and not mismatched and (n_a, right_a, wrong_a, unjudged_a) == (2, 7, 3, 2)), \
                f"獨立重算 N/✅/❌/無法判={(n_a, right_a, wrong_a, unjudged_a)}；彙總行缺：{missing}；標籤↔數值不符：{mismatched}；{line}"

        def _k2():
            return "分母固定 6" not in _k_tables("a", spec_a, gt_a, logs=logs_a), "tables.md 全文不得再出現「分母固定 6」"

        def _k3():
            want = [
                f"❌ {per_a[s][1]}／可判 {per_a[s][0] + per_a[s][1]}／無法判 {per_a[s][2]}（共 6）"
                for s in ("k_a1", "k_a2")
            ]
            tables_a = _k_tables("a", spec_a, gt_a, logs=logs_a)
            missing = [w for w in want if w not in tables_a]
            return not missing, f"逐張計數行：{want}；缺：{missing}"

        def _k4():
            row = f"| west | carpet | 無 | {gyp} | ❌ |"
            in_table = row in _k_tables("a", spec_a, gt_a, logs=logs_a)
            # k_a2 的 ❌ 數（2）包含這個無來源面：證明它在分母（可判 5）與分子內
            return in_table and per_a["k_a2"] == (3, 2, 1), f"無來源面照列、照判：{row!r} 在表中={in_table}；k_a2(✅/❌/無法判)={per_a['k_a2']}"

        def _k5():
            line = _k_summary(_k_tables("a", spec_a, gt_a, logs=logs_a))
            return "—（無可判面）" not in line, line

        guarded("(k-1) 彙總行：N／6N／可判／無法判／主率／下界／上界＝測試端獨立重算（2／12／10／2／3/10=30%／3/12=25%／5/12=42%）", _k1)
        guarded("(k-2) tables.md 不含「分母固定 6」", _k2)
        guarded("(k-3) 每張照片六面表下有「❌ x／可判 y／無法判 z（共 6）」", _k3)
        guarded("(k-4) 無來源面被判 ❌ 仍照列、算進分子與可判面數", _k4)
        def _k8():
            text = _k_tables("a", spec_a, gt_a, logs=logs_a)
            cells = {}
            for stem in ("k_a1", "k_a2"):
                row = next(ln for ln in text.splitlines() if ln.startswith(f"| held-out：k-{stem} |"))
                cells[stem] = [c.strip() for c in row.strip().strip("|").split("|")][-1]
            return (cells == {"k_a1": "1", "k_a2": "未記錄"}), f"report_tables.run() 端到端：表 5「預設路徑 exit」欄＝{cells}"

        guarded("(k-5) 可判面數 > 0 時不印「—（無可判面）」", _k5)
        guarded("(k-8) report_tables.run() 端到端：runs/<run>.log 末行 exit=1→表 5 印「1」；沒有 log→「未記錄」", _k8)

        # 情境 B：可判面數＝0（GT 檔缺）→ 主率印「—（無可判面）」，彙總行不得含「0%」
        spec_b = {"k_b1": {f: (gyp, "clip") for f in surf_names}}

        def _k6():
            line = _k_summary(_k_tables("b", spec_b, None))
            want = ["N＝1", "6N＝6", "可判面數 0", "無法判面數 6", "—（無可判面）"]
            missing = [w for w in want if w not in line]
            segs = {seg.split("（")[0]: seg for seg in line.split("；")[1:]}
            main_ok = segs.get("主率", "").endswith("＝—（無可判面）")
            return (not missing and main_ok and "0%" not in line), \
                f"缺：{missing}；「主率」段以「＝—（無可判面）」結尾={main_ok}；含「0%」={'0%' in line}；{line}"

        guarded("(k-6) 可判＝0 → 含「—（無可判面）」、N／6N／無法判正確、彙總行不含「0%」", _k6)

        # 情境 C：N＝0（唯一一張是 forced，沒有任何未 forced 通過）→「錯誤放行率不適用（0 張放行）」
        spec_c = {"k_c1": {f: (gyp, "clip") for f in surf_names}}

        def _k7():
            tables_c = _k_tables("c", spec_c, None, forced=True)
            hits = [ln for ln in tables_c.splitlines() if "錯誤放行率不適用（0 張放行）" in ln]
            return (len(hits) == 1 and "0%" not in hits[0]), f"命中行={hits}"

        guarded("(k-7) N＝0 → 含「錯誤放行率不適用（0 張放行）」、該行不含「0%」", _k7)

        # 共用樁：一個「溯源對得上『現在』HEAD」的 run（(f-7) 之後隔離 repo 又多了一個 commit，最初的 head 已過期）
        def _fresh_case(stem: str) -> Path:
            photo = _make_fake_photo(photos_dir, stem)
            prov = {
                "git_revision": {"commit": _git(repo, "rev-parse", "HEAD"), "dirty": False},
                "input_sha256": provenance.sha256_file(photo),
                "materials_json_sha256": provenance.sha256_file(materials_path),
                **expected_config,
            }
            return _write_fake_output(repo, stem, provenance_block=prov)

        # ---------------------------------------------------------------
        # (l) 小問題：--legacy／--photos-dir 互斥；repo 外路徑；相對路徑
        # ---------------------------------------------------------------
        print("【l】小問題：--legacy 與 --photos-dir 互斥（exit 2）；repo 外路徑 → exit 1＋清楚訊息；repo 內相對路徑可用")
        scripts_dir = Path(__file__).resolve().parent

        def _mutex(script: str):
            def _fn():
                proc = subprocess.run(
                    [sys.executable, str(scripts_dir / script), "--legacy", "--photos-dir", "no_such_dir"],
                    capture_output=True, text=True, timeout=300,
                )
                tail = proc.stderr.strip().splitlines()[-1:] or [""]
                return (proc.returncode == 2 and "不可" in proc.stderr), f"returncode={proc.returncode}；stderr 末行={tail[0]!r}"
            return _fn

        guarded("(l-1) t17r2_dataset_manifest.py --legacy --photos-dir x → exit 2、stderr 含「不可」", _mutex("t17r2_dataset_manifest.py"))
        guarded("(l-2) t17r2_blind_test.py --legacy --photos-dir x → exit 2、stderr 含「不可」", _mutex("t17r2_blind_test.py"))

        outside_dir = Path(tmp) / "outside_photos"  # 隔離 repo 之外
        for stem in stems:
            _make_fake_photo(outside_dir, stem)
        outside_dry = Path(tmp) / "outside_dry.wav"
        outside_dry.write_bytes(b"RIFF_OUTSIDE_DRY")
        outside_msg = "必須位於 repo 內：manifest 只記 repo 相對路徑"

        def _l3():
            out = repo / "output" / "run_l3" / "DATASET_MANIFEST.json"
            rc, err = _manifest_run(photos_dir=outside_dir, out_path=out)
            return (rc == 1 and outside_msg in err and "repo" in err and not out.exists()), \
                f"rc={rc}；已寫出={out.exists()}；stderr={err.strip()!r}"

        def _l4():
            out = repo / "output" / "run_l4" / "DATASET_MANIFEST.json"
            rc, err = _manifest_run(photos_dir=photos_dir, dry_path=outside_dry, out_path=out)
            return (rc == 1 and outside_msg in err and "--dry" in err and not out.exists()), \
                f"rc={rc}；已寫出={out.exists()}；stderr={err.strip()!r}"

        def _l5():
            out_dir_l5 = repo / "output" / "run_l5" / "blind_test"
            quiet, err = _quiet()
            with quiet:
                rc = blind_mod.run(
                    repo_root=repo, out_dir=out_dir_l5, categories=list(common.HELDOUT_SPACES),
                    photos_dir=outside_dir, outputs_dir=repo / "output",
                    materials_path=materials_path, expected_config=expected_config,
                )
            wrote = out_dir_l5.exists() and any(out_dir_l5.glob("sample_*.wav"))
            return (rc == 1 and outside_msg in err.getvalue() and not wrote), \
                f"rc={rc}；已產生樣本={wrote}；stderr={err.getvalue().strip()!r}"

        def _l6():
            out = repo / "output" / "run_l6" / "DATASET_MANIFEST.json"
            cwd0 = os.getcwd()
            try:
                os.chdir(repo)
                rc, err = _manifest_run(
                    photos_dir=Path("assets/photos_heldout"), dry_path=Path("assets/dry/my_voice.wav"), out_path=out
                )
            finally:
                os.chdir(cwd0)
            m = json.loads(out.read_text(encoding="utf-8"))
            ok = (
                rc == 0 and len(m["heldout_photos"]) == 5
                and all(p["path"].startswith("assets/photos_heldout/") for p in m["heldout_photos"])
                and m["dry"]["path"] == "assets/dry/my_voice.wav"
            )
            return ok, f"rc={rc}；stderr={err.strip()!r}；paths={[p['path'] for p in m['heldout_photos']][:2]}…"

        def _cli_outside(script: str, extra: list[str]):
            # CLI 層（真的跑腳本）：--photos-dir／--dry 在 repo 外 → exit 1、清楚訊息、沒有 Traceback。
            # 路徑檢查先於任何讀寫，所以對真實 repo 跑也不會產生檔案；仍核對真實 output/mvp_acceptance_r2 有無變化。
            def _fn():
                real_r2 = scripts_dir.parent / "output" / "mvp_acceptance_r2"
                existed_before = real_r2.exists()
                proc = subprocess.run(
                    [sys.executable, str(scripts_dir / script), *extra],
                    capture_output=True, text=True, timeout=300,
                )
                ok = (
                    proc.returncode == 1 and outside_msg in proc.stderr and "Traceback" not in proc.stderr
                    and real_r2.exists() == existed_before
                )
                tail = proc.stderr.strip().splitlines()[-1:] or [""]
                return ok, f"returncode={proc.returncode}；Traceback={'Traceback' in proc.stderr}；stderr 末行={tail[0][:120]!r}"
            return _fn

        guarded("(l-3) manifest --photos-dir 在 repo 外 → exit 1、訊息含「必須位於 repo 內…」、無例外、不寫檔", _l3)
        guarded("(l-4) manifest --dry 在 repo 外 → exit 1、訊息含「必須位於 repo 內…」與「--dry」、無例外、不寫檔", _l4)
        guarded("(l-5) blind_test --photos-dir 在 repo 外 → exit 1、訊息含「必須位於 repo 內…」、不產生樣本", _l5)
        guarded("(l-6) manifest 的 --photos-dir／--dry 給 repo 內相對路徑 → exit 0、記 repo 相對路徑", _l6)
        guarded(
            "(l-7) CLI：t17r2_dataset_manifest.py --photos-dir <repo 外> → exit 1、訊息清楚、無 Traceback",
            _cli_outside("t17r2_dataset_manifest.py", ["--photos-dir", str(outside_dir)]),
        )
        guarded(
            "(l-8) CLI：t17r2_dataset_manifest.py --dry <repo 外> → exit 1、訊息清楚、無 Traceback",
            _cli_outside("t17r2_dataset_manifest.py", ["--dry", str(outside_dry)]),
        )
        guarded(
            "(l-9) CLI：t17r2_blind_test.py --photos-dir <repo 外> → exit 1、訊息清楚、無 Traceback",
            _cli_outside("t17r2_blind_test.py", ["--photos-dir", str(outside_dir)]),
        )

        def _l10():
            # run() 層保留 --legacy 與 --photos-dir 並存（隔離 repo 測試需要）；只有 CLI 層互斥
            custom = repo / "assets" / "photos_legacy_custom"
            for _, legacy_stem in t17_blind_test.SPACES:
                _make_fake_photo(custom, legacy_stem)
            m, errs = manifest_mod.build_manifest(
                repo_root=repo, legacy=True, photos_dir=custom, venues=[stub_venue],
                reference_irs_dir=repo / "assets" / "reference_irs", dry_path=dry_path,
            )
            _fresh_case("legacy_case")
            quiet, err = _quiet()
            with quiet:
                rc = blind_mod.run(
                    repo_root=repo, out_dir=repo / "output" / "run_l10" / "blind_test", legacy=True,
                    categories=[("測試", "legacy_case")], photos_dir=photos_dir, outputs_dir=repo / "output",
                    materials_path=materials_path, expected_config=expected_config,
                )
            prefixes = [p["path"] for p in (m or {}).get("heldout_photos", [])]
            ok = (
                not errs and m is not None and m["degraded"] is True and len(prefixes) == 5
                and all(x.startswith("assets/photos_legacy_custom/") for x in prefixes) and rc == 0
            )
            return ok, f"manifest(legacy=True, photos_dir=自訂目錄)：errs={errs}、路徑={prefixes[:1]}…；blind_test.run(legacy=True, photos_dir=…) rc={rc}"

        def _l11():
            # blind_test 的「在 repo 內」檢查不得擋死相對路徑（R2 真實流程：--photos-dir assets/photos_heldout）
            _fresh_case("rel_case")
            out_dir_l11 = repo / "output" / "run_l11" / "blind_test"
            quiet, err = _quiet()
            cwd0 = os.getcwd()
            try:
                os.chdir(repo)
                with quiet:
                    rc = blind_mod.run(
                        repo_root=repo, out_dir=out_dir_l11, categories=[("測試", "rel_case")],
                        photos_dir=Path("assets/photos_heldout"), outputs_dir=repo / "output",
                        materials_path=materials_path, expected_config=expected_config,
                    )
            finally:
                os.chdir(cwd0)
            return (rc == 0 and (out_dir_l11 / "sample_1.wav").exists()), f"rc={rc}；stderr={err.getvalue().strip()!r}"

        def _l12():
            out = repo / "output" / "run_l12" / "DATASET_MANIFEST.json"
            rc, err = _manifest_run(photos_dir=photos_dir, dry_path=repo / "assets" / "dry", out_path=out)  # repo 內的「目錄」
            return (rc == 1 and "乾聲" in err and not out.exists()), f"rc={rc}；已寫出={out.exists()}；stderr={err.strip()!r}"

        def _l13():
            # 兩支工具對「在 repo 內」的定義必須一致（含符號連結、迴圈、.. 逃逸、相對路徑），且都不得丟例外
            outside_file = Path(tmp) / "outside_target.png"
            outside_file.write_bytes(b"x")
            inside = repo / "assets" / "consistency"
            inside.mkdir(parents=True, exist_ok=True)
            (inside / "plain.png").write_bytes(b"x")
            os.symlink(outside_file, inside / "link_to_outside.png")  # repo 內的符號連結，目標在 repo 外
            os.symlink(inside / "loop_a", inside / "loop_b")  # repo 內的符號連結迴圈
            os.symlink(inside / "loop_b", inside / "loop_a")
            outside_loop = Path(tmp) / "outside_loop"
            os.symlink(outside_loop, outside_loop)  # repo 外的符號連結迴圈（自己指自己）
            cases = {
                "repo 內一般檔": (inside / "plain.png", True),
                "repo 內連到 repo 外的符號連結（文字上在 repo 內；舊碼接受）": (inside / "link_to_outside.png", True),
                "repo 內符號連結迴圈": (inside / "loop_a", True),
                "repo 本身": (repo, True),
                "相對路徑（cwd＝repo）": (Path("assets/consistency/plain.png"), True),
                "repo 外一般檔": (outside_file, False),
                "repo 外符號連結迴圈": (outside_loop, False),
                "含 .. 逃出 repo": (repo / "assets" / ".." / ".." / "outside_target.png", False),
            }
            rows: dict = {}
            cwd0 = os.getcwd()
            try:
                os.chdir(repo)
                for name, (pth, want) in cases.items():
                    rows[name] = (manifest_mod._repo_relative(pth, repo) is not None, blind_mod._inside_repo(pth, repo), want)
            finally:
                os.chdir(cwd0)
            bad = {k: v for k, v in rows.items() if not (v[0] == v[1] == v[2])}
            return not bad, f"{len(cases)} 種路徑；(manifest, blind_test, 預期) 不一致或不符：{bad}"

        guarded("(l-10) run() 層 legacy=True 與自訂 photos_dir 並存（manifest、blind_test 都是；只有 CLI 互斥）", _l10)
        guarded("(l-11) blind_test.run() 給 repo 內相對 photos_dir（cwd＝repo）→ exit 0（不得被「repo 內」檢查擋死）", _l11)
        guarded("(l-12) manifest --dry 指到 repo 內的「目錄」→ exit 1、訊息清楚、不寫檔、無例外", _l12)
        guarded("(l-13) manifest 與 blind_test 對「在 repo 內」判定一致（符號連結／迴圈／.. 逃逸／相對路徑），且都不丟例外", _l13)

        # ---------------------------------------------------------------
        # (m) 不得回歸：T-57 已實測成立的行為，修正輪不得退步（T-57-F1「不得回歸」清單中原本沒有測試的項目）
        # ---------------------------------------------------------------
        print("【m】不得回歸：樣本＝來源 wet_preview 逐位元複製；--dry（44.1k）重採樣至 48k；manifest 兩次寫檔逐位元相同且無時間戳")

        def _m1():
            answers = json.loads((out_dir_a.parent / "blind_test_ANSWERS.json").read_text(encoding="utf-8"))["answers"]
            bad = [
                a["sample"] for a in answers
                if (out_dir_a / f"{a['sample']}.wav").read_bytes()
                != (repo / "output" / a["source_run"] / "wet_preview.wav").read_bytes()
            ]
            return (len(answers) == 5 and not bad), f"未給 --dry：{len(answers)} 個 sample_N.wav 與各自來源 wet_preview.wav 逐位元相同；不符={bad}"

        def _m2():
            import numpy as np
            import soundfile as sf

            stem = "dry_case"
            out = _fresh_case(stem)
            t = np.arange(24000) / 48000.0
            noise = np.random.default_rng(0).standard_normal(24000)
            sf.write(str(out / "ir_mono.wav"), 0.3 * noise * np.exp(-6.9 * t / 0.4), 48000, subtype="PCM_24")
            dry = repo / "assets" / "dry" / "dry_441.wav"
            dry.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(dry), 0.3 * np.sin(2 * np.pi * 440 * np.arange(13230) / 44100), 44100, subtype="PCM_24")
            out_dir = repo / "output" / "run_m2" / "blind_test"
            quiet, err = _quiet()
            with quiet:
                rc = blind_mod.run(
                    repo_root=repo, out_dir=out_dir, categories=[("測試", stem)], photos_dir=photos_dir,
                    outputs_dir=repo / "output", materials_path=materials_path,
                    expected_config=expected_config, dry_path=dry,
                )
            data, sr = sf.read(str(out_dir / "sample_1.wav"))
            recorded = json.loads((out_dir / "MANIFEST.json").read_text(encoding="utf-8"))["dry"]["sha256"]
            ok = rc == 0 and sr == 48000 and len(data) > 24000 and float(np.abs(data).max()) > 0.0 and recorded == provenance.sha256_file(dry)
            return ok, f"rc={rc}；sample_1.wav 取樣率={sr}、{len(data)} 取樣點、峰值={float(np.abs(data).max()):.3f}；MANIFEST dry.sha256 相符={recorded == provenance.sha256_file(dry)}；stderr={err.getvalue().strip()!r}"

        def _m3():
            import re

            a = repo / "output" / "run_m3a" / "DATASET_MANIFEST.json"
            b = repo / "output" / "run_m3b" / "DATASET_MANIFEST.json"
            rc1, _ = _manifest_run(photos_dir=photos_dir, out_path=a)
            rc2, _ = _manifest_run(photos_dir=photos_dir, out_path=b)
            same = a.read_bytes() == b.read_bytes()
            has_ts = re.search(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}", a.read_text(encoding="utf-8")) is not None
            return (rc1 == 0 and rc2 == 0 and same and not has_ts), f"rc={rc1},{rc2}；經 run() 寫檔兩次逐位元相同={same}；含時間戳樣式={has_ts}"

        guarded("(m-1) 未給 --dry：5 個 sample_N.wav 與來源 wet_preview.wav 逐位元相同", _m1)
        guarded("(m-2) --dry（44.1k 乾聲）可跑，樣本重採樣至 48k、非靜音、MANIFEST 記該乾聲 sha256", _m2)
        guarded("(m-3) manifest 經 run() 寫檔兩次逐位元相同、無時間戳", _m3)
        check("(m-4) SHUFFLE_SEED 仍是 20260916", common.SHUFFLE_SEED == 20260916, f"{common.SHUFFLE_SEED}")

    if FAILURES:
        print(f"\n❌ {len(FAILURES)} 項失敗：{FAILURES}")
        return 1
    print("\n✅ 全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
