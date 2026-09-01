#!/usr/bin/env python3
"""T-38A 迴歸測試：治療評測 harness 的可重現性機制（`scripts/t38_treatment_eval.py`）。

只測 T-38A 新增/修正的機制本身（誤導訊息修正、原子發布、讀取端跳過邏輯、
指紋彙整、快照差異），不碰任何真實模型或 13 張照片——全部用合成資料與
`tempfile` 臨時目錄，不觸碰 `output/clip_treatment/` 實際輪次。

用法：
    python scripts/test_t38_treatment_eval.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import t38_treatment_eval as t38  # noqa: E402


def die(msg: str) -> None:
    print(f"[錯誤] {msg}", file=sys.stderr)
    sys.exit(1)


def _write_detail(path: Path, *, fingerprint: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"fingerprint": fingerprint, "payload": {}}, ensure_ascii=False),
        encoding="utf-8",
    )


# ------------------------------------------------------------------
# 原子發布：模擬中途當機，summary.json 絕不能出現在半完成的輪次目錄裡。
# ------------------------------------------------------------------

def test_atomic_publish_simulated_crash_leaves_no_valid_round():
    print("[1] 原子發布：模擬 tables.md 寫到一半當機 → summary.json 絕不出現，讀取端正確跳過 ...")
    with tempfile.TemporaryDirectory() as tmp:
        rounds_root = Path(tmp) / "rounds"
        round_dir = rounds_root / "round_crash"

        real_atomic_write = t38._atomic_write_text

        def flaky_write(path, content):
            if path.name == "tables.md":
                tmp_path = path.with_name(path.name + ".tmp")
                tmp_path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path.write_text(content, encoding="utf-8")
                raise RuntimeError("模擬中途當機（寫完暫存檔，rename 前中斷）")
            real_atomic_write(path, content)

        t38._atomic_write_text = flaky_write
        try:
            try:
                t38.publish_round_artifacts(
                    round_dir,
                    tables_text="fake tables",
                    round_md_text="fake round md",
                    snapshot={"a": 1},
                    summary={"overall_correct": 1, "overall_denom": 1},
                )
            except RuntimeError:
                pass
            else:
                die("模擬當機應該讓 publish_round_artifacts 往外丟例外")
        finally:
            t38._atomic_write_text = real_atomic_write

        if (round_dir / "summary.json").exists():
            die("當機後 summary.json 不應該存在")
        if (round_dir / "tables.md").exists():
            die("tables.md 寫到一半當機，正式檔不應該存在（只該留 .tmp）")
        if not (round_dir / "tables.md.tmp").exists():
            die("預期留下 tables.md.tmp 殘檔，但沒有")

        completed, skipped = t38.load_completed_rounds(rounds_root)
        if completed:
            die(f"中止的輪次不該被讀取端納入完整清單，實際：{completed}")
        if not any("round_crash" in s and "無 summary.json" in s for s in skipped):
            die(f"讀取端應明示跳過 round_crash（無 summary.json），實際 skipped={skipped}")
        print(f"    ✓ 中止輪次正確被隔離：summary.json 不存在，讀取端明示跳過（{skipped}）")


def test_atomic_publish_crash_after_partial_success_still_hides_summary():
    print("[2] 原子發布：tables.md／snapshot 已落地，ROUND.md 當機 → summary.json 依然不存在 ...")
    with tempfile.TemporaryDirectory() as tmp:
        rounds_root = Path(tmp) / "rounds"
        round_dir = rounds_root / "round_partial"
        real_atomic_write = t38._atomic_write_text

        def flaky_write(path, content):
            if path.name == "ROUND.md":
                raise RuntimeError("模擬 ROUND.md 當機")
            real_atomic_write(path, content)

        t38._atomic_write_text = flaky_write
        try:
            try:
                t38.publish_round_artifacts(
                    round_dir, tables_text="t", round_md_text="r",
                    snapshot={"x": 1}, summary={"overall_correct": 1, "overall_denom": 1},
                )
            except RuntimeError:
                pass
            else:
                die("ROUND.md 當機應該往外丟例外")
        finally:
            t38._atomic_write_text = real_atomic_write

        if not (round_dir / "tables.md").exists():
            die("tables.md 應該已經落地（順序在 ROUND.md 之前）")
        if (round_dir / "summary.json").exists():
            die("summary.json 不應該存在——它必須在 ROUND.md 之後才落地")
        completed, skipped = t38.load_completed_rounds(rounds_root)
        if completed:
            die("局部完成的輪次不該被視為完整")
        print("    ✓ 即使部分檔案已落地，summary.json 缺席讓讀取端仍正確判定不完整")


def test_publish_round_artifacts_success():
    print("[3] publish_round_artifacts()：正常情況下四個檔案都落地，讀取端視為完整 ...")
    with tempfile.TemporaryDirectory() as tmp:
        rounds_root = Path(tmp) / "rounds"
        round_dir = rounds_root / "round_ok"
        summary = {"overall_correct": 31, "overall_denom": 76}
        t38.publish_round_artifacts(
            round_dir, tables_text="tables content",
            round_md_text="# round\n\n- status: complete\n",
            snapshot={"CLIP_MATERIAL_PROMPTS": {}}, summary=summary,
        )
        for name in ("tables.md", "prompts_snapshot.json", "ROUND.md", "summary.json"):
            if not (round_dir / name).exists():
                die(f"{name} 應該存在")
        completed, skipped = t38.load_completed_rounds(rounds_root)
        if skipped:
            die(f"正常完成的輪次不該被跳過，實際 skipped={skipped}")
        if len(completed) != 1 or completed[0]["label"] != "round_ok":
            die(f"應該讀到 1 個完整輪次 round_ok，實際：{completed}")
        if completed[0]["summary"] != summary:
            die("讀回的 summary 應該與寫入時相同")
        print("    ✓ 四個檔案正確落地，讀取端正確判定完整")


def test_load_completed_rounds_respects_non_complete_status():
    print("[4] load_completed_rounds()：ROUND.md status 非 complete（即使 summary.json 存在）也要跳過 ...")
    with tempfile.TemporaryDirectory() as tmp:
        rounds_root = Path(tmp) / "rounds"
        round_dir = rounds_root / "round_interrupted"
        round_dir.mkdir(parents=True)
        (round_dir / "summary.json").write_text('{"overall_correct": 1}', encoding="utf-8")
        (round_dir / "ROUND.md").write_text("# round\n\n- status: interrupted\n", encoding="utf-8")

        completed, skipped = t38.load_completed_rounds(rounds_root)
        if completed:
            die(f"status=interrupted 的輪次不該被納入完整清單，實際：{completed}")
        if not any("round_interrupted" in s and "interrupted" in s for s in skipped):
            die(f"應該明示跳過 round_interrupted 並附上 status，實際：{skipped}")
        print(f"    ✓ 正確跳過非 complete 的輪次：{skipped}")


# ------------------------------------------------------------------
# 誤導訊息修正：round3/round5 型多張照片漂移不得被印成「預期只有 TunnelToHell」。
# ------------------------------------------------------------------

def test_old_message_logic_was_misleading_new_fixes_it():
    print("[5] 重現舊碼誤導訊息：round3/round5 型多張漂移，舊邏輯仍印「預期只有 TunnelToHell」 ...")

    # 舊碼（T-38A 修正前，見 git 歷史該行）第 216 行附近的邏輯逐字抄錄，
    # 僅用於證明「修正前對這組輸入會誤判」——修正後改用 diff_scope_summary()。
    def old_message(all_diffs: list[str]) -> str:
        return "預期只有 TunnelToHell 三項比對" if len(all_diffs) else "無"

    # round3 型的實際情境（見 output/clip_treatment/rounds/round3/tables.md）：
    # bathroom_tiled／car_interior_suv／SteinmanHall 等多張都有差異，不是只有 TunnelToHell。
    multi_photo_diffs = [
        "bathroom_tiled：surfaces 與 T-33 凍結快取不同（...）",
        "car_interior_suv：surfaces 與 T-33 凍結快取不同（...）",
        "SteinmanHall：surfaces 與 T-33 凍結快取不同（...）",
    ]
    old_result = old_message(multi_photo_diffs)
    if old_result != "預期只有 TunnelToHell 三項比對":
        die("測試前置條件錯誤：舊邏輯應該對這組多照片差異誤判為「預期」，重現失敗")
    print(f"    ✓ 舊碼對多張照片漂移確實誤判：{old_result!r}（bug 重現成立，對舊碼實測 fail）")

    new_result = t38.diff_scope_summary({"bathroom_tiled", "car_interior_suv", "SteinmanHall"})
    if new_result.startswith("符合預期") or "預期只有 TunnelToHell" in new_result:
        die(f"新邏輯不應該把多張照片漂移誤判為符合預期，實際：{new_result}")
    if "bathroom_tiled" not in new_result or "car_interior_suv" not in new_result:
        die(f"新邏輯應該列出實際涉及的照片，實際：{new_result}")
    print(f"    ✓ 新邏輯正確標示非預期範圍：{new_result}")


def test_diff_scope_summary_expected_case():
    print("[6] 只有 TunnelToHell 有差異 → 符合預期 ...")
    result = t38.diff_scope_summary({"TunnelToHell"})
    if not result.startswith("符合預期"):
        die(f"只有 TunnelToHell 差異時應該回報符合預期，實際：{result}")
    print(f"    ✓ {result}")


def test_diff_scope_summary_no_diff():
    print("[7] 無差異 ...")
    result = t38.diff_scope_summary(set())
    if result != "無差異":
        die(f"無差異時應該回報「無差異」，實際：{result}")
    print(f"    ✓ {result}")


# ------------------------------------------------------------------
# 指紋彙整：整輪應該一致，不一致要丟例外；一致時要正確彙整。
# ------------------------------------------------------------------

def test_collect_round_fingerprint_detects_inconsistency():
    print("[8] collect_round_fingerprint()：同輪內指紋不一致（跑到一半換程式碼）應丟例外 ...")
    with tempfile.TemporaryDirectory() as tmp:
        runs_dir = Path(tmp) / "runs"
        gate_items = [{"name": "a"}, {"name": "b"}]
        _write_detail(runs_dir / "a" / "detail.json", fingerprint={
            "photo_sha256": "pa", "code_sha256": {"surfaces.py": "s1"},
            "data_sha256": {}, "segmentation_model_id": "seg", "clip_model_id": "clip",
            "clip_threshold": 0.4, "eval_mode": "treatment:x",
        })
        _write_detail(runs_dir / "b" / "detail.json", fingerprint={
            "photo_sha256": "pb", "code_sha256": {"surfaces.py": "s2-DIFFERENT"},
            "data_sha256": {}, "segmentation_model_id": "seg", "clip_model_id": "clip",
            "clip_threshold": 0.4, "eval_mode": "treatment:x",
        })
        try:
            t38.collect_round_fingerprint(runs_dir, gate_items)
        except ValueError as exc:
            print(f"    ✓ 正確偵測到指紋不一致並丟出例外：{exc}")
        else:
            die("指紋不一致時應該丟出 ValueError，但沒有")


def test_collect_round_fingerprint_success():
    print("[9] collect_round_fingerprint()：一致的指紋 → 正確彙整 shared/per_photo ...")
    with tempfile.TemporaryDirectory() as tmp:
        runs_dir = Path(tmp) / "runs"
        gate_items = [{"name": "a"}, {"name": "b"}]
        shared_fp = {
            "code_sha256": {"surfaces.py": "s1"}, "data_sha256": {},
            "segmentation_model_id": "seg", "clip_model_id": "clip",
            "clip_threshold": 0.4, "eval_mode": "treatment:x",
        }
        _write_detail(runs_dir / "a" / "detail.json", fingerprint={"photo_sha256": "pa", **shared_fp})
        _write_detail(runs_dir / "b" / "detail.json", fingerprint={"photo_sha256": "pb", **shared_fp})
        result = t38.collect_round_fingerprint(runs_dir, gate_items)
        if result["shared"] != shared_fp:
            die(f"shared 指紋應該就是共同部分，實際：{result['shared']}")
        if result["per_photo_sha256"] != {"a": "pa", "b": "pb"}:
            die(f"per_photo_sha256 應該逐張記錄，實際：{result['per_photo_sha256']}")
        print("    ✓ shared/per_photo_sha256 彙整正確")


def test_collect_round_fingerprint_missing_cache_raises():
    print("[10] collect_round_fingerprint()：缺某張照片的 detail.json → 丟例外，不得靜默跳過 ...")
    with tempfile.TemporaryDirectory() as tmp:
        runs_dir = Path(tmp) / "runs"
        gate_items = [{"name": "a"}, {"name": "missing_one"}]
        _write_detail(runs_dir / "a" / "detail.json", fingerprint={
            "photo_sha256": "pa", "code_sha256": {}, "data_sha256": {},
            "segmentation_model_id": "seg", "clip_model_id": "clip",
            "clip_threshold": 0.4, "eval_mode": "treatment:x",
        })
        try:
            t38.collect_round_fingerprint(runs_dir, gate_items)
        except ValueError as exc:
            if "missing_one" not in str(exc):
                die(f"例外訊息應該指出缺哪一張，實際：{exc}")
            print(f"    ✓ 正確丟出例外並指出缺哪張照片：{exc}")
        else:
            die("缺快取檔時應該丟出 ValueError，但沒有")


# ------------------------------------------------------------------
# 快照差異：新增／刪除／改值／無基線。
# ------------------------------------------------------------------

def test_diff_prompt_snapshots():
    print("[11] diff_prompt_snapshots()：新增／刪除／改值／無基線 四種情況 ...")
    baseline = {
        "CLIP_MATERIAL_PROMPTS": {"carpet": "old carpet desc", "glass": "a pane of glass"},
        "CLIP_OOD_PROMPTS": {"__person": "a person"},
    }
    current = {
        "CLIP_MATERIAL_PROMPTS": {"carpet": "new carpet desc", "glass": "a pane of glass", "brick": "a brick wall"},
        "CLIP_OOD_PROMPTS": {},
    }
    diffs = t38.diff_prompt_snapshots(baseline, current)
    joined = "\n".join(diffs)
    if "carpet" not in joined or "old carpet desc" not in joined or "new carpet desc" not in joined:
        die(f"應該列出 carpet 的字串變化，實際：{diffs}")
    if not any("brick" in d and "新增" in d for d in diffs):
        die(f"應該標示 brick 是新增，實際：{diffs}")
    if not any("__person" in d and "刪除" in d for d in diffs):
        die(f"應該標示 __person 被刪除，實際：{diffs}")
    if any(d.startswith("CLIP_MATERIAL_PROMPTS.glass") for d in diffs):
        die(f"glass 沒有變化不應該出現在差異清單，實際：{diffs}")
    print(f"    ✓ 差異清單正確：{diffs}")

    none_result = t38.diff_prompt_snapshots(None, current)
    if none_result != ["（無基線快照可比對）"]:
        die(f"無基線時應該明確回報，實際：{none_result}")
    print("    ✓ 無基線快照時明確回報，不假裝有/無差異")


def test_load_baseline_snapshot_reads_published_file():
    print("[12] load_baseline_snapshot()：讀已發布的 round0_baseline/prompts_snapshot.json ...")
    with tempfile.TemporaryDirectory() as tmp:
        rounds_root = Path(tmp) / "rounds"
        snap = {"CLIP_MATERIAL_PROMPTS": {"carpet": "x"}, "CLIP_OOD_PROMPTS": {}}
        baseline_dir = rounds_root / "round0_baseline"
        baseline_dir.mkdir(parents=True)
        (baseline_dir / "prompts_snapshot.json").write_text(json.dumps(snap), encoding="utf-8")

        loaded = t38.load_baseline_snapshot(rounds_root)
        if loaded != snap:
            die(f"讀回的基線快照應與寫入時相同，實際：{loaded}")
        print("    ✓ 正確讀回基線快照")

        missing = t38.load_baseline_snapshot(rounds_root, baseline_label="round_not_exist")
        if missing is not None:
            die(f"基線目錄不存在時應回傳 None，實際：{missing}")
        print("    ✓ 基線快照不存在時回傳 None，不偽造內容")


def main() -> int:
    test_atomic_publish_simulated_crash_leaves_no_valid_round()
    test_atomic_publish_crash_after_partial_success_still_hides_summary()
    test_publish_round_artifacts_success()
    test_load_completed_rounds_respects_non_complete_status()
    test_old_message_logic_was_misleading_new_fixes_it()
    test_diff_scope_summary_expected_case()
    test_diff_scope_summary_no_diff()
    test_collect_round_fingerprint_detects_inconsistency()
    test_collect_round_fingerprint_success()
    test_collect_round_fingerprint_missing_cache_raises()
    test_diff_prompt_snapshots()
    test_load_baseline_snapshot_reads_published_file()
    print(
        "\n全部通過：誤導訊息已修正（範圍檢查取代非空判斷，對舊碼實測重現過 bug）、"
        "原子發布中途當機不留下看似完整的輪次、讀取端正確跳過無 summary.json／"
        "status 非 complete 的輪次、指紋彙整與快照差異函式行為正確。"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
