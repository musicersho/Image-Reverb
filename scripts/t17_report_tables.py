#!/usr/bin/env python3
"""T-17 §7-2：把 `rt60_table.json` 算成 REPORT.md 要的表格與分組達標率。

跑法：`python scripts/t17_report_tables.py`（需先跑 `scripts/t17_rt60_table.py`）
輸出：`output/mvp_acceptance/tables.md`（REPORT.md 直接引用，數字不手打）

**為什麼分兩支腳本**：量測（慢，要讀 IR、跑濾波）與統計（快，純算術）分開，
改統計呈現時不必重跑量測；也讓「量測管線未被統計邏輯汙染」這件事在檔案層級就成立。

**分組規則（裁決 C）**：達標率依 `dims_source` 分組統計，
`metric_depth` / `equirect_multiview`（自動幾何，F-01 產品主張本體）與
`manual`（F-09 正式出口）**不得合併成單一數字**。本腳本在資料結構層級就分開算，
沒有「全部合併」的輸出路徑。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "output" / "mvp_acceptance"
BANDS = ["125", "250", "500", "1000", "2000", "4000"]
# §7-2 硬判準頻段（裁決 B）：500Hz–4kHz 逐頻段 ＋ 低頻聯合帶。
# 125/250Hz 照樣全表列出、超差照樣警示，但不當門檻。
CRITERION_KEYS = ["500", "1000", "2000", "4000", "low_combined"]
AUTO_SOURCES = {"metric_depth", "equirect_multiview"}

# 手動尺寸的來源依據（F-09）。**唯一有公開標準的是壁球場**；其餘為 Opus 依照片
# 估計，REPORT 必須逐項標明，不得讓讀者誤以為是查得到的場地真值。
MANUAL_DIMS_BASIS = {
    "t17_manual_racquetball": (
        "**公開標準**：國際壁球場規格 40×20×20 ft = 12.19×6.10×6.10 m（唯一有權威來源者）"
    ),
    "t17_manual_steinman": "Opus 由環景數座位排數／排距推估（~300 席演講廳含舞台）：20×18×7.5 m",
    "t17_manual_department_store": "Opus 由照片估：吊頂日光燈格柵推天花 ~3.2m，樓板取中型賣場 35×25 m",
    "t17_manual_gym": "Opus 由照片估：門高 2.03m 為基準推天花 ~2.9m，小型健身工作室 9×6 m",
    "t17_manual_restaurant": "Opus 由照片估：**照片只拍到卡座，室內尺寸不可見**，取一般用餐區 14×9×3.2 m",
    "t17_diag_racquetball_hard": (
        "同上公開標準尺寸，**額外用 `--override-material` 把六面改成正確硬質**"
        "（floor=wood_panel、其餘 concrete）——病因隔離用的診斷 run，不計入達標率"
    ),
}

DIAG_RUNS = {"t17_diag_racquetball_hard", "t17_diag_tunnel_perspective"}


def fmt(x, suffix="", width=0):
    if x is None:
        return "—".rjust(width) if width else "—"
    s = f"{x:.3f}{suffix}" if isinstance(x, float) else f"{x}{suffix}"
    return s.rjust(width) if width else s


def pct(x):
    return "—" if x is None else f"{x:+.0f}%"


def mark(err: dict) -> str:
    """達標標記。真實側是區間時（MIT 多檔）用 `~` 標明判準較弱。"""
    if err.get("error_pct") is None:
        return "—"
    body = pct(err["error_pct"])
    if err.get("within_tolerance"):
        return f"✅ {body}"
    if err.get("within_range"):
        return f"🟡 {body}"  # 落在多檔區間內，但對中位數超差——弱命中
    return f"❌ {body}"


def main() -> int:
    src = OUT_DIR / "rt60_table.json"
    if not src.exists():
        print(f"❌ 找不到 {src}，請先跑 scripts/t17_rt60_table.py", file=sys.stderr)
        return 1
    data = json.loads(src.read_text(encoding="utf-8"))
    L: list[str] = []

    # ---------- 表 1：完整誤差表（8 場地 × (6 頻段 + 聯合帶)）----------
    L.append("### 表 1　完整誤差表：8 場地 ×（6 頻段 ＋ 低頻聯合帶）\n")
    L.append(
        "誤差 =（生成 IR 量測 T30 − 真實 IR 量測 T30）/ 真實。"
        "✅ = 誤差 ≤20%；❌ = 超差；🟡 = 對多檔中位數超差但落在該場地多條真實 IR 的區間內"
        "（MIT 三場地無公開 photo↔IR 配對，判準較弱，見 §限制）。\n"
    )
    L.append(
        "**判準（裁決 B）**：門檻只看 500Hz–4kHz ＋ 低頻聯合帶；"
        "125/250Hz 照列、超差照警示，但不當門檻。\n"
    )
    head = (
        "| 場地 | 路徑 | dims_source | conf | 125Hz | 250Hz | "
        "**500Hz** | **1kHz** | **2kHz** | **4kHz** | **聯合帶** |"
    )
    L.append(head)
    L.append("|---|---|---|---|---|---|---|---|---|---|---|")

    for v in data["venues"]:
        rr = v["real_reference"]
        n = rr["n_files"]
        real_cells = [fmt(rr["bands"][b]["value"]) for b in BANDS] + [
            fmt(rr["low_combined"]["value"])
        ]
        tag = f"真實 IR（{n} 條中位數）" if n > 1 else "真實 IR"
        L.append(f"| **{v['label']}** | {tag} | — | — | " + " | ".join(real_cells) + " |")
        for g in v["generated"]:
            note = "🔬診斷" if g["run"] in DIAG_RUNS else "生成"
            cells = [mark(g["errors"][b]) for b in BANDS] + [mark(g["errors"]["low_combined"])]
            L.append(
                f"| | {note}`{g['run']}` | `{g['dims_source']}` | {g['confidence']} | "
                + " | ".join(cells)
                + " |"
            )
    L.append("")

    # ---------- 表 2：分組達標率（裁決 C，不得合併）----------
    L.append("### 表 2　達標率 —— 依 `dims_source` 分組（裁決 C：不得合併成單一數字）\n")

    def group_stats(pred):
        n_band_pass = n_band = 0
        venue_rows = []
        for v in data["venues"]:
            for g in v["generated"]:
                if g["run"] in DIAG_RUNS or not pred(g):
                    continue
                ok = sum(1 for k in CRITERION_KEYS if g["errors"][k].get("within_tolerance"))
                tot = sum(1 for k in CRITERION_KEYS if g["errors"][k].get("error_pct") is not None)
                n_band_pass += ok
                n_band += tot
                venue_rows.append((v["label"], g, ok, tot))
        return n_band_pass, n_band, venue_rows

    for gname, pred in (
        ("自動幾何 `metric_depth` / `equirect_multiview`（F-01 產品主張本體）",
         lambda g: g["dims_source"] in AUTO_SOURCES),
        ("手動尺寸 `manual`（F-09 正式出口）", lambda g: g["dims_source"] == "manual"),
    ):
        p, t, rows = group_stats(pred)
        L.append(f"**{gname}**\n")
        L.append("| 場地 | run | 五項判準通過 | 全場地達標？ |")
        L.append("|---|---|---|---|")
        n_venue_pass = 0
        for label, g, ok, tot in rows:
            allpass = ok == tot and tot > 0
            n_venue_pass += 1 if allpass else 0
            L.append(f"| {label} | `{g['run']}` | {ok}/{tot} | {'✅' if allpass else '❌'} |")
        L.append(
            f"| **小計** | — | **{p}/{t}**"
            f"（{100.0 * p / t:.0f}%）| **{n_venue_pass}/{len(rows)} 場地全達標** |"
        )
        L.append("")

    # ---------- 表 3：500Hz vs 聯合帶階梯比（裁決 B 殘留風險檢查點）----------
    L.append("### 表 3　500Hz vs 低頻聯合帶 階梯比（裁決 B 要求的殘留風險檢查）\n")
    L.append(
        "裁決 B 自陳：聯合帶上緣 354Hz 與 500Hz 帶仍共享邊緣，"
        "**若某場地 500Hz T30 比聯合帶慢 2 倍以上，聯合帶量測仍可能被拉長**。"
        "比值 = T30(500Hz) / T30(聯合帶)；|比值| ≥ 2 或 ≤ 0.5 時該場地的聯合帶數字需打折看待。\n"
    )
    L.append("| 場地 | 真實 IR 階梯比 | 生成 IR 階梯比（各 run） | 觸發殘留風險？ |")
    L.append("|---|---|---|---|")
    for v in data["venues"]:
        real_r = None
        gens = []
        for g in v["generated"]:
            real_r = g["ladder_500_vs_low"]["real"]
            gens.append(f"`{g['run']}` {fmt(g['ladder_500_vs_low']['generated'])}")
        vals = [real_r] + [g["ladder_500_vs_low"]["generated"] for g in v["generated"]]
        risky = any(x is not None and (x >= 2.0 or x <= 0.5) for x in vals)
        L.append(
            f"| {v['label']} | {fmt(real_r)} | {'<br>'.join(gens)} | "
            f"{'⚠️ 是' if risky else '否'} |"
        )
    L.append("")

    # ---------- 表 4：手動尺寸來源依據 ----------
    L.append("### 表 4　手動尺寸（F-09）的來源依據 —— 逐項標明，不得當成場地真值\n")
    L.append("| run | 採用尺寸 | 依據 |")
    L.append("|---|---|---|")
    for v in data["venues"]:
        for g in v["generated"]:
            if g["dims_source"] != "manual":
                continue
            d = g["dims_m"]
            basis = MANUAL_DIMS_BASIS.get(g["run"], "**未記錄依據**")
            L.append(
                f"| `{g['run']}` | {d['length']:.2f}×{d['width']:.2f}×{d['height']:.2f} m | {basis} |"
            )
    L.append("")

    out = OUT_DIR / "tables.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"已寫入 {out.relative_to(REPO_ROOT)}（{len(L)} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
