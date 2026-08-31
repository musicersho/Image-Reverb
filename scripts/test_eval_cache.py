#!/usr/bin/env python3
"""T-40 迴歸測試：評測快取指紋與自動失效（`scripts/eval_cache.py`）。

用合成小圖＋樁 runner（不跑任何真實模型），逐項擾動六類指紋，驗證每一項都會
觸發快取失效；並驗證舊格式（無指紋欄）、凍結目錄 hard fail、非凍結目錄自動
重跑、以及「凍結目錄絕不被覆寫」等行為。全部用 `tempfile` 臨時目錄，不觸碰
`output/clip_accuracy/` 實際凍結基線。

用法：
    python scripts/test_eval_cache.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import eval_cache  # noqa: E402


def die(msg: str) -> None:
    print(f"[錯誤] {msg}", file=sys.stderr)
    sys.exit(1)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class Runner:
    """樁 runner：記錄被呼叫次數，回傳固定 payload。"""

    def __init__(self, tag: str = "v1"):
        self.calls = 0
        self.tag = tag

    def __call__(self) -> dict:
        self.calls += 1
        return {"result": self.tag, "call_no": self.calls}


def make_baseline_inputs(root: Path) -> dict:
    """建一組基準輸入檔（合成小圖＋假 code/data 檔），回傳指紋所需的所有路徑與參數。"""
    photo = root / "photo.png"
    _write(photo, "fake-photo-bytes-v1")

    code1 = root / "preprocess.py"
    code2 = root / "surfaces.py"
    code3 = root / "config.py"
    _write(code1, "code1-v1")
    _write(code2, "code2-v1")
    _write(code3, "config-v1")

    data1 = root / "materials.json"
    data2 = root / "ground_truth.json"
    _write(data1, '{"materials": "v1"}')
    _write(data2, '{"gt": "v1"}')

    return {
        "photo_path": photo,
        "code_paths": [code1, code2, code3],
        "data_paths": [data1, data2],
        "segmentation_model_id": "seg-model-v1",
        "clip_model_id": "clip-model-v1",
        "clip_threshold": 0.4,
        "eval_mode": "default",
    }


def test_first_run_writes_cache_with_fingerprint():
    print("[1/9] 快取不存在 → 執行 run_fn 並寫入含 fingerprint 的快取 ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        runner = Runner()

        payload, was_rerun, reasons = eval_cache.load_or_run(
            cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=runner, is_frozen=False,
        )
        if runner.calls != 1:
            die(f"run_fn 應被呼叫 1 次，實際 {runner.calls} 次")
        if not was_rerun:
            die("快取不存在時 was_rerun 應為 True")
        if payload["call_no"] != 1:
            die("payload 應為 run_fn 的回傳值")
        if not cache_path.exists():
            die("應該寫出快取檔")
        on_disk = json.loads(cache_path.read_text(encoding="utf-8"))
        if "fingerprint" not in on_disk or "payload" not in on_disk:
            die(f"快取檔格式錯誤，缺 fingerprint 或 payload 欄位：{on_disk.keys()}")
        if on_disk["fingerprint"] != fingerprint:
            die("寫入的 fingerprint 與計算值不符")
        print("    ✓ 首次執行呼叫 run_fn，快取寫入 fingerprint+payload")


def test_cache_hit_skips_rerun():
    print("[2/9] 指紋相符 → 讀快取，不重跑 run_fn ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        runner = Runner()
        eval_cache.load_or_run(cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=runner, is_frozen=False)

        runner2 = Runner(tag="should-not-run")
        payload, was_rerun, reasons = eval_cache.load_or_run(
            cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=runner2, is_frozen=False,
        )
        if runner2.calls != 0:
            die(f"指紋相符時不應呼叫 run_fn，實際呼叫 {runner2.calls} 次")
        if was_rerun:
            die("指紋相符時 was_rerun 應為 False")
        if reasons:
            die(f"指紋相符時 reasons 應為空，實際 {reasons}")
        if payload["call_no"] != 1:
            die("快取命中應回傳第一次執行的 payload（call_no=1）")
        print("    ✓ 快取命中，run_fn 未被呼叫")


# ------------------------------------------------------------------
# 逐項擾動六類指紋 → 每一項都必須觸發失效（非凍結目錄：自動重跑）
# ------------------------------------------------------------------

def _assert_mutation_triggers_rerun(mutate_fn, label: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        eval_cache.load_or_run(cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=Runner("v1"), is_frozen=False)

        mutated_inputs = mutate_fn(root, dict(inputs))
        mutated_fingerprint = eval_cache.compute_fingerprint(**mutated_inputs)
        runner2 = Runner("v2")
        payload, was_rerun, reasons = eval_cache.load_or_run(
            cache_path=cache_path, fingerprint_fn=lambda: mutated_fingerprint, run_fn=runner2, is_frozen=False,
        )
        if runner2.calls != 1:
            die(f"{label}：擾動後應觸發重跑，實際呼叫 run_fn {runner2.calls} 次")
        if not was_rerun or not reasons:
            die(f"{label}：擾動後 was_rerun/reasons 應非空，實際 was_rerun={was_rerun} reasons={reasons}")
        print(f"    ✓ {label} 擾動觸發失效重跑（原因：{reasons}）")


def test_mutation_photo():
    print("[3/9] 逐項擾動 1/6：來源圖片 bytes 改變 ...")
    def mutate(root, inputs):
        _write(inputs["photo_path"], "fake-photo-bytes-v2-CHANGED")
        return inputs
    _assert_mutation_triggers_rerun(mutate, "來源圖片 sha256")


def test_mutation_code():
    print("[4/9] 逐項擾動 2/6：src 三檔任一內容改變（模擬 dirty 工作樹） ...")
    def mutate(root, inputs):
        _write(inputs["code_paths"][2], "config-v2-CHANGED")
        return inputs
    _assert_mutation_triggers_rerun(mutate, "code_sha256（config.py）")


def test_mutation_data():
    print("[5/9] 逐項擾動 3/6：materials.json／ground_truth.json 任一內容改變 ...")
    def mutate(root, inputs):
        _write(inputs["data_paths"][0], '{"materials": "v2-CHANGED"}')
        return inputs
    _assert_mutation_triggers_rerun(mutate, "data_sha256（materials.json）")


def test_mutation_model_ids():
    print("[6/9] 逐項擾動 4/6：模型 id（SegFormer／CLIP）改變 ...")
    def mutate(root, inputs):
        inputs["segmentation_model_id"] = "seg-model-v2-CHANGED"
        return inputs
    _assert_mutation_triggers_rerun(mutate, "segmentation_model_id")

    def mutate2(root, inputs):
        inputs["clip_model_id"] = "clip-model-v2-CHANGED"
        return inputs
    _assert_mutation_triggers_rerun(mutate2, "clip_model_id")


def test_mutation_threshold():
    print("[7/9] 逐項擾動 5/6：CLIP 門檻改變 ...")
    def mutate(root, inputs):
        inputs["clip_threshold"] = 0.5
        return inputs
    _assert_mutation_triggers_rerun(mutate, "clip_threshold")


def test_mutation_eval_mode():
    print("[8/9] 逐項擾動 6/6：評測模式改變（預設／治療） ...")
    def mutate(root, inputs):
        inputs["eval_mode"] = "treatment"
        return inputs
    _assert_mutation_triggers_rerun(mutate, "eval_mode")


# ------------------------------------------------------------------
# 舊格式（無指紋欄）視同不符
# ------------------------------------------------------------------

def test_legacy_cache_without_fingerprint_treated_as_mismatch():
    print("[9/9-a] 舊格式快取（無 fingerprint 欄，T-36 原始格式）視同指紋不符 ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        # 舊格式：直接存 payload，沒有 fingerprint 欄位包裝
        cache_path.write_text(json.dumps({"legacy_field": "old-value"}), encoding="utf-8")

        runner = Runner("v2")
        payload, was_rerun, reasons = eval_cache.load_or_run(
            cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=runner, is_frozen=False,
        )
        if runner.calls != 1:
            die("舊格式快取應被視為指紋不符，非凍結目錄應自動重跑")
        if not was_rerun or "舊格式" not in " ".join(reasons):
            die(f"舊格式快取的失效原因應提及「舊格式」，實際 reasons={reasons}")
        print(f"    ✓ 舊格式快取自動重跑（原因：{reasons}）")


# ------------------------------------------------------------------
# 凍結目錄：hard fail，絕不覆寫
# ------------------------------------------------------------------

def test_frozen_dir_matching_fingerprint_is_cache_hit():
    print("[9/9-b] 凍結目錄＋指紋相符 → 正常讀快取，不 hard fail ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        eval_cache.load_or_run(cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=Runner("v1"), is_frozen=True)

        runner2 = Runner("should-not-run")
        payload, was_rerun, reasons = eval_cache.load_or_run(
            cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=runner2, is_frozen=True,
        )
        if runner2.calls != 0 or was_rerun:
            die("凍結目錄指紋相符時應正常讀快取，不應重跑")
        print("    ✓ 凍結目錄指紋相符時正常讀快取")


def test_frozen_dir_mismatch_hard_fails_without_overwriting():
    print("[9/9-c] 凍結目錄＋指紋不符 → FrozenBaselineError，且快取檔案不被覆寫 ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        eval_cache.load_or_run(cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=Runner("v1"), is_frozen=True)
        before_bytes = cache_path.read_bytes()

        mutated_inputs = dict(inputs)
        _write(mutated_inputs["code_paths"][2], "config-v2-CHANGED")
        mutated_fingerprint = eval_cache.compute_fingerprint(**mutated_inputs)

        runner2 = Runner("should-not-run")
        try:
            eval_cache.load_or_run(
                cache_path=cache_path, fingerprint_fn=lambda: mutated_fingerprint, run_fn=runner2, is_frozen=True,
            )
        except eval_cache.FrozenBaselineError as exc:
            if runner2.calls != 0:
                die(f"hard fail 前不應呼叫 run_fn，實際呼叫 {runner2.calls} 次")
            after_bytes = cache_path.read_bytes()
            if before_bytes != after_bytes:
                die("凍結目錄的快取檔案在 hard fail 後被改變了——鐵則 4 破功！")
            print(f"    ✓ 正確丟出 FrozenBaselineError：{exc}")
        else:
            die("凍結目錄指紋不符時應丟出 FrozenBaselineError，但沒有")


def test_legacy_cache_in_frozen_dir_hard_fails():
    print("[9/9-d] 凍結目錄＋舊格式快取（無 fingerprint 欄）→ hard fail（P2 情境的直接重現） ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"surfaces": "legacy-no-fingerprint"}), encoding="utf-8")
        before_bytes = cache_path.read_bytes()

        runner = Runner("should-not-run")
        try:
            eval_cache.load_or_run(
                cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=runner, is_frozen=True,
            )
        except eval_cache.FrozenBaselineError:
            if runner.calls != 0:
                die("hard fail 前不應呼叫 run_fn")
            if cache_path.read_bytes() != before_bytes:
                die("凍結目錄的舊格式快取檔案被改變了")
            print("    ✓ 舊格式快取在凍結目錄下正確 hard fail，未被覆寫")
        else:
            die("舊格式快取在凍結目錄下應該 hard fail，但沒有")


def test_legacy_cache_mismatch_never_calls_fingerprint_fn():
    print("[9/9-f] 舊格式快取的「指紋不符」判定不需要呼叫 fingerprint_fn"
          "（來源圖片可能已不在本機，例如乾淨 clone 缺 assets/reference_irs/） ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cache_path = root / "runs" / "item1" / "detail.json"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps({"surfaces": "legacy-no-fingerprint"}), encoding="utf-8")
        before_bytes = cache_path.read_bytes()

        def _fingerprint_fn_should_not_be_called():
            die("fingerprint_fn 不該被呼叫——舊格式快取一看 fingerprint 欄位缺席就能判定不符，"
                "不需要讀取來源圖片")

        try:
            eval_cache.load_or_run(
                cache_path=cache_path,
                fingerprint_fn=_fingerprint_fn_should_not_be_called,
                run_fn=Runner("should-not-run"),
                is_frozen=True,
            )
        except eval_cache.FrozenBaselineError:
            if cache_path.read_bytes() != before_bytes:
                die("舊格式快取檔案被改變了")
            print("    ✓ hard fail 前完全沒呼叫 fingerprint_fn（惰性成立）")
        else:
            die("舊格式快取在凍結目錄下應該 hard fail，但沒有")


def test_frozen_dir_rejects_force_fresh():
    print("[9/9-e] 凍結目錄＋--fresh 強制重跑 → 一律拒絕（不得覆寫凍結基線） ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        inputs = make_baseline_inputs(root)
        fingerprint = eval_cache.compute_fingerprint(**inputs)
        cache_path = root / "runs" / "item1" / "detail.json"
        eval_cache.load_or_run(cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=Runner("v1"), is_frozen=True)
        before_bytes = cache_path.read_bytes()

        runner2 = Runner("should-not-run")
        try:
            eval_cache.load_or_run(
                cache_path=cache_path, fingerprint_fn=lambda: fingerprint, run_fn=runner2,
                is_frozen=True, force_fresh=True,
            )
        except eval_cache.FrozenBaselineError:
            if runner2.calls != 0:
                die("--fresh 在凍結目錄應直接拒絕，不應呼叫 run_fn")
            if cache_path.read_bytes() != before_bytes:
                die("凍結目錄快取檔案被 --fresh 改變了")
            print("    ✓ 凍結目錄拒絕 --fresh，快取未被覆寫")
        else:
            die("凍結目錄 + --fresh 應該 FrozenBaselineError，但沒有")


# ------------------------------------------------------------------
# FREEZE_MANIFEST：產生與驗證
# ------------------------------------------------------------------

def test_freeze_manifest_round_trip():
    print("[額外] FREEZE_MANIFEST 產生與驗證往返一致 ...")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "frozen_dir"
        _write(root / "REPORT.md", "report content")
        _write(root / "runs" / "item1" / "detail.json", '{"a": 1}')
        _write(root / "runs" / "item2" / "detail.json", '{"b": 2}')

        manifest_text = eval_cache.build_freeze_manifest_text(root, "python scripts/t40_freeze_manifest.py")
        problems = eval_cache.verify_freeze_manifest(root, manifest_text)
        if problems:
            die(f"剛產生的 manifest 立刻驗證應該全部相符，實際不符：{problems}")
        print("    ✓ 產生後立即驗證：全部相符")

        # 竄改一個既有檔案，驗證應該抓到 hash 不符
        _write(root / "runs" / "item1" / "detail.json", '{"a": 999-TAMPERED}')
        problems2 = eval_cache.verify_freeze_manifest(root, manifest_text)
        if not problems2:
            die("竄改既有檔案後 verify_freeze_manifest 應該回報不符，但沒有")
        print(f"    ✓ 竄改後正確偵測到不符：{problems2}")

        # 新增一個 manifest 沒記錄的檔案，驗證應該抓到「多出未記錄的檔案」
        _write(root / "runs" / "item3" / "detail.json", '{"c": 3}')
        problems3 = eval_cache.verify_freeze_manifest(root, manifest_text)
        extra_flagged = any("多出" in p for p in problems3)
        if not extra_flagged:
            die(f"新增未記錄檔案後應偵測到「多出」，實際 problems={problems3}")
        print(f"    ✓ 新增未記錄檔案正確偵測：{[p for p in problems3 if '多出' in p]}")


def main() -> int:
    test_first_run_writes_cache_with_fingerprint()
    test_cache_hit_skips_rerun()
    test_mutation_photo()
    test_mutation_code()
    test_mutation_data()
    test_mutation_model_ids()
    test_mutation_threshold()
    test_mutation_eval_mode()
    test_legacy_cache_without_fingerprint_treated_as_mismatch()
    test_frozen_dir_matching_fingerprint_is_cache_hit()
    test_frozen_dir_mismatch_hard_fails_without_overwriting()
    test_legacy_cache_in_frozen_dir_hard_fails()
    test_legacy_cache_mismatch_never_calls_fingerprint_fn()
    test_frozen_dir_rejects_force_fresh()
    test_freeze_manifest_round_trip()
    print("\n全部通過：六類指紋逐項擾動皆觸發失效、舊格式視同不符、凍結目錄"
          "hard fail 且絕不覆寫、非凍結目錄自動重跑、FREEZE_MANIFEST 產生/驗證往返一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
