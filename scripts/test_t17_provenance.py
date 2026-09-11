#!/usr/bin/env python3
"""T-43 迴歸測試：`t17_blind_test.py` 溯源驗證（插卡 4/4，修 bug 類）。

外部掃描 P1 指出 `t17_blind_test.py:140-149` 舊版寫進 MANIFEST 的 `_git_rev()`
是**執行盲測複製腳本當下**的 HEAD，不是**產生來源 IR 當下**的 HEAD——舊產物
被蓋上新 HEAD 的章，「v1 碼產的 IR 拿去驗收 v2 碼」偵測不出來。T-43 把
`run_photo()` 改成在生成當下寫 `provenance.git_revision`，`t17_blind_test.py`
改成溯源驗證：來源 revision 與盲測當下 HEAD 不符就 fail。

本測試在系統暫存目錄建一個**真的 git repo**（不是主 repo，不動任何既有檔案）
重現外部報告的情境，全程樁 `analysis.json`／IR／wet preview（純資料檔案），
不下載或執行任何模型：

  A（舊產物冒充新 HEAD 必須 fail）：`analysis.json` 的
     `provenance.git_revision.commit` 記錄隔離 repo 的第一個 commit（v1），但
     repo 目前 HEAD 已經是第二個 commit（v2，模擬「生成之後又 commit 了新程式」）。
     呼叫 `t17_blind_test.run()` 指到這個隔離 repo，斷言 (a) 回傳非 0、
     (b) stderr 訊息點名 `git_revision 不符`。
  B（provenance 齊全且相符）：另一次 `analysis.json` 的
     `provenance.git_revision.commit` 改成當下 HEAD（v2）、`input_sha256`／
     `materials_json_sha256`／模型 id／門檻全部與隔離 repo 的實際檔案／
     `expected_config` 相符。斷言 (a) 回傳 0、(b) `MANIFEST.json` 的
     `generated_from[0].source_provenance` 與來源 `analysis.json` 的
     `provenance` 逐項相同、(c) `packaging_git_revision.commit` 等於當下 HEAD、
     (d) 兩個鍵名不混用（頂層沒有裸的 `git_revision`／`source_provenance`）。
  C（附帶，缺 provenance 同樣 fail）：`analysis.json` 完全沒有 `provenance`
     鍵（T-43 之前的舊產物）→ 斷言 (a) 回傳非 0、(b) stderr 點名缺少 provenance。

跑法：`python scripts/test_t17_provenance.py`；全部通過 exit 0，任一失敗 exit 1。
只在 `tempfile.TemporaryDirectory()` 內建立隔離 git repo，結束後自動清除，
不影響本 repo 任何既有檔案。
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.image_reverb import provenance  # noqa: E402
import t17_blind_test as t17  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _init_isolated_repo(repo: Path) -> None:
    repo.mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t43-test@example.com")
    _git(repo, "config", "user.name", "T-43 Test")
    (repo / "src").mkdir()
    (repo / "data").mkdir()
    (repo / "src" / "marker.txt").write_text("v1\n", encoding="utf-8")
    (repo / "data" / "materials.json").write_text(
        json.dumps({"fallback_id": "gypsum_board"}), encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v1")


def _make_fake_photo(repo: Path, name: str) -> Path:
    photos_dir = repo / "assets" / "photos"
    photos_dir.mkdir(parents=True, exist_ok=True)
    photo = photos_dir / f"{name}.png"
    photo.write_bytes(b"\x89PNG\r\n\x1a\nFAKE_PHOTO_BYTES_FOR_T43_TEST")
    return photo


def _write_fake_output(repo: Path, name: str, provenance_block: dict | None) -> Path:
    out_dir = repo / "output" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ir_mono.wav").write_bytes(b"RIFF_FAKE_IR_BYTES")
    (out_dir / "wet_preview.wav").write_bytes(b"RIFF_FAKE_WET_BYTES")
    analysis: dict = {
        "input": f"assets/photos/{name}.png",
        "dims_source": "metric_depth",
        "confidence": "medium",
    }
    if provenance_block is not None:
        analysis["provenance"] = provenance_block
    (out_dir / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out_dir


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "isolated_repo"
        _init_isolated_repo(repo)
        v1_commit = _git(repo, "rev-parse", "HEAD")

        # 模擬「生成之後又 commit 了新程式」：v2 commit，HEAD 往前移動。
        (repo / "src" / "marker.txt").write_text("v2\n", encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "v2")
        v2_commit = _git(repo, "rev-parse", "HEAD")
        check(
            "隔離 repo 兩個 commit 確實不同（v1 != v2）",
            v1_commit != v2_commit,
            f"v1={v1_commit} v2={v2_commit}",
        )

        photo = _make_fake_photo(repo, "testroom")
        materials_path = repo / "data" / "materials.json"
        expected_config = {
            "segmentation_model_id": "fake-seg-model",
            "clip_model_id": "fake-clip-model",
            "clip_confidence_threshold": 0.4,
        }

        # --- 案例 A：v1 產物＋v2 HEAD → 必須 fail，訊息點名 git_revision 不符 --
        print("【A】v1 產物（provenance 記 v1 commit）＋v2 HEAD → 必須 fail")
        prov_v1 = {
            "git_revision": {"commit": v1_commit, "dirty": False},
            "input_sha256": provenance.sha256_file(photo),
            "materials_json_sha256": provenance.sha256_file(materials_path),
            **expected_config,
        }
        _write_fake_output(repo, "testroom", prov_v1)
        stderr_a = io.StringIO()
        with contextlib.redirect_stderr(stderr_a):
            rc_a = t17.run(
                repo_root=repo,
                out_dir=repo / "output" / "_blind_test_a",
                spaces=[("測試空間", "testroom")],
                photos_dir=repo / "assets" / "photos",
                outputs_dir=repo / "output",
                materials_path=materials_path,
                expected_config=expected_config,
            )
        stderr_a_text = stderr_a.getvalue()
        check("(a) exit 非 0（舊產物驗收新程式必須擋下）", rc_a != 0, f"rc={rc_a}")
        check(
            "(b) stderr 點名 git_revision 不符",
            "git_revision 不符" in stderr_a_text,
            f"stderr={stderr_a_text!r}",
        )

        # --- 案例 B：provenance 齊全且相符 → 必須 exit 0，MANIFEST 正確 -------
        print("【B】provenance 齊全且相符（記錄當下 HEAD＝v2）→ 必須 exit 0")
        prov_v2 = {
            "git_revision": {"commit": v2_commit, "dirty": False},
            "input_sha256": provenance.sha256_file(photo),
            "materials_json_sha256": provenance.sha256_file(materials_path),
            **expected_config,
        }
        _write_fake_output(repo, "testroom", prov_v2)
        out_dir_b = repo / "output" / "_blind_test_b"
        stderr_b = io.StringIO()
        with contextlib.redirect_stderr(stderr_b):
            rc_b = t17.run(
                repo_root=repo,
                out_dir=out_dir_b,
                spaces=[("測試空間", "testroom")],
                photos_dir=repo / "assets" / "photos",
                outputs_dir=repo / "output",
                materials_path=materials_path,
                expected_config=expected_config,
            )
        check(
            "(a) exit 0（provenance 齊全且相符）",
            rc_b == 0,
            f"rc={rc_b}\nstderr={stderr_b.getvalue()!r}",
        )

        manifest = json.loads((out_dir_b / "MANIFEST.json").read_text(encoding="utf-8"))
        source_prov = manifest.get("generated_from", [{}])[0].get("source_provenance")
        check(
            "(b) MANIFEST.generated_from[0].source_provenance 與來源 analysis.json.provenance 逐項相同",
            source_prov == prov_v2,
            f"source_provenance={source_prov!r}",
        )
        check(
            "(c) MANIFEST.packaging_git_revision.commit 為當下 HEAD（v2）",
            manifest.get("packaging_git_revision", {}).get("commit") == v2_commit,
            f"packaging_git_revision={manifest.get('packaging_git_revision')!r}",
        )
        check(
            "(d) packaging_git_revision 與 source_provenance 未混用同一鍵名（頂層無裸 git_revision）",
            "git_revision" not in manifest and "source_provenance" not in manifest,
            f"top-level keys={list(manifest.keys())!r}",
        )

        # --- 案例 C（附帶）：缺 provenance（舊產物）同樣 fail ------------------
        print("【C】缺 provenance（T-43 之前的舊產物）→ 必須 fail")
        _write_fake_output(repo, "testroom", None)
        stderr_c = io.StringIO()
        with contextlib.redirect_stderr(stderr_c):
            rc_c = t17.run(
                repo_root=repo,
                out_dir=repo / "output" / "_blind_test_c",
                spaces=[("測試空間", "testroom")],
                photos_dir=repo / "assets" / "photos",
                outputs_dir=repo / "output",
                materials_path=materials_path,
                expected_config=expected_config,
            )
        stderr_c_text = stderr_c.getvalue()
        check("(a) exit 非 0（缺 provenance 的舊產物必須擋下）", rc_c != 0, f"rc={rc_c}")
        check(
            "(b) stderr 點名缺少 provenance",
            "缺少 provenance" in stderr_c_text,
            f"stderr={stderr_c_text!r}",
        )

    if FAILURES:
        print(f"\n❌ {len(FAILURES)} 項失敗：{FAILURES}")
        return 1
    print("\n✅ 全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
