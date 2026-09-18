#!/usr/bin/env python3
"""T-57／T-17-R2 步驟 4：R2 生成 IR vs 真實 IR 逐頻段 RT60 對照表（薄包裝）。

跑法：`python scripts/t17r2_rt60_table.py`
輸出：`output/mvp_acceptance_r2/rt60_table.json`

**量測管線與 T-17 完全相同**：本檔只 import `t17_rt60_table.py` 的
`measure_file()`／`real_reference()`／`error_vs_reference()`／`ratio()`／
`BANDS`／`VENUES`，不重新實作任何量測邏輯——8 場地清單就是同一份
`t17_rt60_table.VENUES`，不重抄一份（避免場地清單漂移）。

**R2 加的三個分組欄位（每筆 `generated` 加）**：
- `forced_low_confidence`：原文抄 `analysis.json`。
- `group`：`"auto"`（`dims_source` 屬於 `t17_report_tables.AUTO_SOURCES` 且
  未 forced）／`"forced"`（同上但 forced）／`"manual"`（`dims_source=="manual"`，
  forced 與否另看 `forced_low_confidence` 欄，不算獨立第四組）。
- `in_domain`：讀 `output/mvp_acceptance_r2/DATASET_MANIFEST.json` 對應場地的
  `in_domain` 旗標（T-17-R2 卡「in-domain 場地事前定義」，寫死只有 mit_gym
  true）——本檔不重新判斷，只搬過來，避免兩處各自維護同一個判斷。

**run 清單（與 T-17 不同，R2 只認兩種 run，不像 T-17 那樣把「自動候選」與
「手動候選」混在同一個 `runs` 清單裡逐個嘗試）**：
- 自動 run：`output/<VENUES[i]["runs"][0]>/`（該場地的照片 stem，唯一一個）。
- 手動 run（只有 5 個場地有）：`output/t17r2_manual_<key>/`
  （`key` 見 `t17r2_common.VENUE_KEY_TO_MANUAL_KEY`）。
缺 run 印「尚未產生」跳過（T-17 同手法），不當成錯誤。

**gate 欄位**：解析 `output/mvp_acceptance_r2/runs/<run>.log`（每個 run 的
stdout＋stderr，格式沿用 `t48_geometry_material_r2._run_cli()` 的既有慣例：
`stdout + "\\n--- stderr ---\\n" + stderr`）——這一份**一律是「預設路徑」（不帶
`--force-low-confidence`）那次**的 log，用來讀「預設路徑本身有沒有被 gate 擋下」
與「有沒有印出 `--override-dims` 導引」，跟這個 run 最終量測用的 IR 是不是
forced 產生的是兩回事（那個看 `forced_low_confidence`）。log 不存在 → `gate`
欄位為 `None`（尚未產生 default log，例如域外場地一開始就沒有嘗試預設路徑）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from t17_rt60_table import VENUES, measure_file, real_reference, error_vs_reference, ratio, BANDS  # noqa: E402
from t17_report_tables import AUTO_SOURCES  # noqa: E402
import t17r2_common as common  # noqa: E402

BLOCKED_MARKER = "已擋下輸出"
OVERRIDE_DIMS_MARKER = "--override-dims"


def parse_gate_log(log_path: Path) -> dict | None:
    """解析一份 `<run>.log`（預設路徑那次）。找不到檔案回傳 `None`。"""
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    blocked = BLOCKED_MARKER in text
    return {
        "default_exit": 3 if blocked else 0,
        "blocked": blocked,
        "override_dims_guidance": OVERRIDE_DIMS_MARKER in text,
    }


def classify_group(dims_source: str | None, forced_low_confidence: bool) -> str | None:
    if dims_source == "manual":
        return "manual"
    if dims_source in AUTO_SOURCES:
        return "forced" if forced_low_confidence else "auto"
    return None


def run(
    *,
    repo_root: Path = REPO_ROOT,
    out_root: Path | None = None,
    venues: list[dict] | None = None,
    manifest_path: Path | None = None,
) -> int:
    out_root = out_root if out_root is not None else (repo_root / "output" / "mvp_acceptance_r2")
    venues = list(VENUES) if venues is None else venues
    manifest_path = manifest_path if manifest_path is not None else (out_root / "DATASET_MANIFEST.json")

    in_domain_by_key: dict[str, bool] = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for v in manifest.get("venues", []):
            in_domain_by_key[v["key"]] = bool(v.get("in_domain"))

    ref_root = repo_root / "assets" / "reference_irs"
    output_root = repo_root / "output"
    runs_log_dir = out_root / "runs"
    result: dict = {"bands_hz": BANDS, "tolerance_pct": 20.0, "venues": []}

    for v in venues:
        print(f"=== {v['label']}")
        entry = {k: v[k] for k in ("key", "label", "source", "photo")}
        entry["in_domain"] = in_domain_by_key.get(v["key"], False)

        entry["real"] = []
        for rel in v["real_irs"]:
            p = ref_root / rel
            if not p.exists():
                print(f"  ❌ 找不到真實 IR：{p}", file=sys.stderr)
                return 1
            m = measure_file(p)
            entry["real"].append(m)

        entry["real_reference"] = {
            "bands": {
                str(f): real_reference([r["bands"] for r in entry["real"]], str(f)) for f in BANDS
            },
            "low_combined": real_reference(entry["real"], "low_combined"),
            "n_files": len(entry["real"]),
        }

        run_names = [v["runs"][0]]
        manual_key = common.VENUE_KEY_TO_MANUAL_KEY.get(v["key"])
        if manual_key:
            run_names.append(f"t17r2_manual_{manual_key}")

        entry["generated"] = []
        for run_name in run_names:
            run_dir = output_root / run_name
            ir_path = run_dir / "ir_mono.wav"
            aj_path = run_dir / "analysis.json"
            if not ir_path.exists() or not aj_path.exists():
                print(f"  ⏭️  尚未產生：output/{run_name}/（跳過）")
                continue
            aj = json.loads(aj_path.read_text(encoding="utf-8"))
            m = measure_file(ir_path)
            forced = bool(aj.get("forced_low_confidence", False))
            g = {
                "run": run_name,
                "dims_source": aj.get("dims_source"),
                "confidence": aj.get("confidence"),
                "dims_m": aj.get("dims_m"),
                "volume_m3": aj.get("volume_m3"),
                "override_dims_used": aj.get("override_dims_used"),
                "forced_low_confidence": forced,
                "group": classify_group(aj.get("dims_source"), forced),
                "in_domain": entry["in_domain"],
                "gate": parse_gate_log(runs_log_dir / f"{run_name}.log"),
                "measured": {"bands": m["bands"], "low_combined": m["low_combined"]},
                "errors": {},
            }
            for f in BANDS:
                g["errors"][str(f)] = error_vs_reference(
                    m["bands"][str(f)], entry["real_reference"]["bands"][str(f)]
                )
            g["errors"]["low_combined"] = error_vs_reference(
                m["low_combined"], entry["real_reference"]["low_combined"]
            )
            g["ladder_500_vs_low"] = {
                "generated": ratio(m["bands"]["500"], m["low_combined"]),
                "real": ratio(
                    entry["real_reference"]["bands"]["500"]["value"],
                    entry["real_reference"]["low_combined"]["value"],
                ),
            }
            print(
                f"  生成 {run_name:34s} dims_source={g['dims_source']} group={g['group']} "
                f"forced={forced} conf={g['confidence']} 聯合帶={m['low_combined']}"
            )
            entry["generated"].append(g)

        result["venues"].append(entry)

    out_path = out_root / "rt60_table.json"
    out_root.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已寫入 {out_path}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
