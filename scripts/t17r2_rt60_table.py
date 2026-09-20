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
  **manifest 不存在、無法解析，或某場地 key（或它的 `in_domain` 布林欄位）不在其中
  → 直接 exit 1（不寫 `rt60_table.json`）**：不得靜默當成 `in_domain=False`——那會讓
  `mit_gym` 無聲掉出自動組、coverage 變 0/1（T-57-F1 R4）。

**run 清單（與 T-17 不同，R2 只認兩種 run，不像 T-17 那樣把「自動候選」與
「手動候選」混在同一個 `runs` 清單裡逐個嘗試）**：
- 自動 run：`output/<VENUES[i]["runs"][0]>/`（該場地的照片 stem，唯一一個）。
- 手動 run（只有 5 個場地有）：`output/t17r2_manual_<key>/`
  （`key` 見 `t17r2_common.VENUE_KEY_TO_MANUAL_KEY`）。
缺 run 印「尚未產生」跳過（T-17 同手法），不當成錯誤。

**gate 欄位**：解析 `output/mvp_acceptance_r2/runs/<run>.log`（每個 run 的
stdout＋stderr）——這一份**一律是「預設路徑」（不帶 `--force-low-confidence`）
那次**的 log，用來讀「預設路徑本身有沒有被 gate 擋下」與「有沒有印出
`--override-dims` 導引」，跟這個 run 最終量測用的 IR 是不是 forced 產生的是
兩回事（那個看 `forced_low_confidence`）。**只讀 `<run>.log`，不讀
`<run>.forced.log`**（forced 重跑另存、只留稽核）。log 不存在 → `gate` 欄位為
`None`（尚未產生 default log，例如域外場地一開始就沒有嘗試預設路徑）。

**`default_exit`＝CLI 真實結束碼（T-17-R2 步驟 2(e)，Fable 裁定選項 (i)）**：
log 的**最後一個非空行**必須是 `exit=<整數>`（指令樣板見該步驟），本檔以
`^exit=(-?\\d+)$` 解析它；該行不存在或格式不符 → `default_exit: None`，表 5 印
「未記錄」（看得見的缺口）——**不得**再用字串推測填 0 或 3。`blocked`＝log 含
「已擋下輸出」標記（語義就是「標記有無」，與結束碼是兩件事）；
`exit_marker_consistent`＝`(default_exit == 3) == blocked`（`default_exit` 為
`None` 時為 `None`），不一致代表 log 被手改或 CLI 行為與標記脫鉤。
"""

from __future__ import annotations

import json
import re
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
# re.ASCII：只認半形 0-9（否則全形「３」之類的 Unicode 數字也會被 \d 吃進去）
EXIT_LINE_RE = re.compile(r"^exit=(-?\d+)$", re.ASCII)


def parse_gate_log(log_path: Path) -> dict | None:
    """解析一份 `<run>.log`（預設路徑那次）。找不到檔案回傳 `None`。

    `default_exit` 只認最後一個非空行的 `exit=<整數>`；缺／格式不符 → `None`
    （不用字串推測）。只讀傳進來的這一份，呼叫端不得把 `<run>.forced.log` 傳進來。
    """
    if not log_path.exists():
        return None
    text = log_path.read_text(encoding="utf-8", errors="replace")
    blocked = BLOCKED_MARKER in text
    # 只依 "\n" 分行（read_text 的 universal newlines 已把 CRLF／CR 統一成 "\n"）：
    # str.splitlines() 還會在 \x0b／\x0c／\x85／\u2028 等字元斷行，'exit=3\x0b' 會被誤讀成 3
    non_empty = [ln for ln in text.split("\n") if ln.strip()]
    m = EXIT_LINE_RE.match(non_empty[-1]) if non_empty else None
    default_exit = int(m.group(1)) if m else None
    return {
        "default_exit": default_exit,
        "blocked": blocked,
        "exit_marker_consistent": None if default_exit is None else (default_exit == 3) == blocked,
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

    # manifest 缺檔或缺場地 key 一律 exit 1、不寫表：靜默當成 in_domain=False 會讓
    # mit_gym 無聲掉出自動組（步驟順序錯時 coverage 變 0/1）。比照 t17r2_report_tables.py。
    if not manifest_path.exists():
        print(f"❌ 找不到 {manifest_path}，請先跑 scripts/t17r2_dataset_manifest.py", file=sys.stderr)
        return 1
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_venues = manifest["venues"]
        if not isinstance(manifest_venues, list):
            raise TypeError("venues 不是清單")
        # 只收「有 key 且 in_domain 是布林」的條目；缺欄位的場地一律當成缺項（不得靜默當 False）
        in_domain_by_key: dict[str, bool] = {
            v["key"]: v["in_domain"]
            for v in manifest_venues
            if isinstance(v, dict) and "key" in v and isinstance(v.get("in_domain"), bool)
        }
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(
            f"❌ {manifest_path} 無法解析（{type(exc).__name__}: {exc}）；"
            "請重跑 scripts/t17r2_dataset_manifest.py",
            file=sys.stderr,
        )
        return 1
    missing_keys = [v["key"] for v in venues if v["key"] not in in_domain_by_key]
    if missing_keys:
        print(
            f"❌ {manifest_path} 沒有這些場地 key（或該場地缺 in_domain 欄位）：{', '.join(missing_keys)}"
            "（不得靜默當成 in_domain=False；請重跑 scripts/t17r2_dataset_manifest.py）",
            file=sys.stderr,
        )
        return 1

    ref_root = repo_root / "assets" / "reference_irs"
    output_root = repo_root / "output"
    runs_log_dir = out_root / "runs"
    result: dict = {"bands_hz": BANDS, "tolerance_pct": 20.0, "venues": []}

    for v in venues:
        print(f"=== {v['label']}")
        entry = {k: v[k] for k in ("key", "label", "source", "photo")}
        entry["in_domain"] = in_domain_by_key[v["key"]]

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
