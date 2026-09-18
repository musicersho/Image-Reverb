#!/usr/bin/env python3
"""T-57／T-17-R2 步驟 4：把 R2 的量測結果算成 REPORT.md 要的表格（薄包裝）。

跑法：`python scripts/t17r2_report_tables.py`
（需先跑 `t17r2_dataset_manifest.py`＋`t17r2_rt60_table.py`）
輸出：`output/mvp_acceptance_r2/tables.md`

**五張表**：
1. 完整誤差表（8 場地 ×（6 頻段＋聯合帶）；沿用 T-17 格式，改標 group）。
2. **三組分列，不得合併（裁決 C）**：自動組（`group=="auto"` 且 `in_domain`，
   另印 `coverage = 通過 gate 的 in-domain 場地數 / in-domain 場地數`）／
   forced 組（只列不計達標率）／手動組（照 T-17 口徑，逐 run 標 forced）。
3. 500Hz vs 低頻聯合帶階梯比（同 T-17）。
4. 手動尺寸來源依據（同 T-17 表 4，文字原文從 `t17_report_tables.MANUAL_DIMS_BASIS`
   搬過來，只換 run 名前綴，不重打內容）。
5. **報告項 5**：13 張（5 held-out＋8 場地）逐張 gate 結果／forced／
   `--override-dims` 導引有無／domain／「域外誤放」標記；每張**未 forced 通過**
   的照片列六面材質表（材質 id／來源／GT／正誤，無來源面標「無」、GT 缺或
   `unknown` 標「無法判」不進分子分母，分母固定 6）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from t17_report_tables import AUTO_SOURCES, MANUAL_DIMS_BASIS as T17_MANUAL_DIMS_BASIS  # noqa: E402
from t17r2_rt60_table import parse_gate_log  # noqa: E402
import t17r2_common as common  # noqa: E402

BANDS = ["125", "250", "500", "1000", "2000", "4000"]
CRITERION_KEYS = ["500", "1000", "2000", "4000", "low_combined"]
SURFACE_NAMES = ("floor", "ceiling", "west", "east", "south", "north")

# T-17 表 4 文字原文搬過來，只換 run 名前綴（t17_manual_ → t17r2_manual_），
# 不重打任何字。診斷 run（t17_diag_racquetball_hard）不進 R2（R2 沒有這個病因
# 隔離 run），不搬。
_KEY_REMAP = {
    "t17_manual_department_store": "t17r2_manual_department_store",
    "t17_manual_gym": "t17r2_manual_gym",
    "t17_manual_restaurant": "t17r2_manual_restaurant",
    "t17_manual_racquetball": "t17r2_manual_racquetball",
    "t17_manual_steinman": "t17r2_manual_steinman",
}
MANUAL_DIMS_BASIS_R2 = {new: T17_MANUAL_DIMS_BASIS[old] for old, new in _KEY_REMAP.items()}


def fmt(x, suffix="", width=0):
    if x is None:
        return "—".rjust(width) if width else "—"
    s = f"{x:.3f}{suffix}" if isinstance(x, float) else f"{x}{suffix}"
    return s.rjust(width) if width else s


def pct(x):
    return "—" if x is None else f"{x:+.0f}%"


def mark(err: dict) -> str:
    if err.get("error_pct") is None:
        return "—"
    body = pct(err["error_pct"])
    if err.get("within_tolerance"):
        return f"✅ {body}"
    if err.get("within_range"):
        return f"🟡 {body}"
    return f"❌ {body}"


# ------------------------------------------------------------------
# 表 5：報告項 5 用的逐張 gate／domain／六面材質比對
# ------------------------------------------------------------------

def _load_analysis(output_root: Path, run_stem: str) -> dict | None:
    aj_path = output_root / run_stem / "analysis.json"
    if not aj_path.exists():
        return None
    return json.loads(aj_path.read_text(encoding="utf-8"))


def build_item5(
    *,
    label: str,
    run_stem: str,
    domain: str,
    gt_surfaces: dict | None,
    output_root: Path,
    runs_log_dir: Path,
) -> dict:
    """組出報告項 5 一張照片的逐項判定。`gt_surfaces` 為 None 或缺面 → 該面標「GT 缺」。

    `gate_result`／`domain_leak` 只依 `forced_low_confidence`（`analysis.json`）
    判定，不依賴 `<run>.log` 是否存在：`output/<run>/` 這個目錄存在本身就代表
    「最終有輸出」，唯一的問題只剩「是不是被擋過、靠 force 才輸出的」——這正是
    `forced_low_confidence` 要記的事。`<run>.log`（預設路徑那次的原始輸出）只用
    來補「有沒有印出 --override-dims 導引」這個輔助細節，缺檔不影響判定，
    避免「沒存到 log」把整張表判定弄壞。
    """
    aj = _load_analysis(output_root, run_stem)
    gate = parse_gate_log(runs_log_dir / f"{run_stem}.log")
    item: dict = {
        "label": label,
        "run": run_stem,
        "domain": domain,
        "gate_result": None,
        "forced": None,
        "override_dims_guidance": gate["override_dims_guidance"] if gate else None,
        "domain_leak": False,
        "faces": None,
        "status": "尚未產生" if aj is None else "已產生",
    }
    if aj is None:
        return item

    forced = bool(aj.get("forced_low_confidence", False))
    item["forced"] = forced
    item["gate_result"] = "BLOCK→forced" if forced else "PASS"

    passed_unforced = not forced
    domain_out = domain in ("out", "non_room")
    item["domain_leak"] = bool(domain_out and passed_unforced)

    if passed_unforced:
        surfaces = aj.get("surfaces", {})
        sources = aj.get("surfaces_sources", {})
        faces = {}
        for face in SURFACE_NAMES:
            material_id = surfaces.get(face)
            source = sources.get(face, "無")
            gt_entry = (gt_surfaces or {}).get(face)
            gt_id = gt_entry.get("material_id") if gt_entry else None
            if gt_id is None or gt_id == "unknown":
                verdict = "無法判"
            elif material_id == gt_id:
                verdict = "✅"
            else:
                verdict = "❌"
            faces[face] = {"material_id": material_id, "source": source, "gt": gt_id, "verdict": verdict}
        item["faces"] = faces
    return item


def render_item5_table(items: list[dict]) -> list[str]:
    L = []
    L.append("| 照片 | domain | gate | forced | override-dims 導引 | 域外誤放？ |")
    L.append("|---|---|---|---|---|---|")
    for it in items:
        if it["status"] == "尚未產生":
            L.append(f"| {it['label']} | {it['domain']} | 尚未產生 | — | — | — |")
            continue
        L.append(
            f"| {it['label']} | {it['domain']} | {it['gate_result']} | "
            f"{'是' if it['forced'] else '否'} | "
            f"{'有' if it['override_dims_guidance'] else '無'} | "
            f"{'⚠️ 是' if it['domain_leak'] else '否'} |"
        )
    L.append("")

    L.append("#### 未 forced 通過的照片：六面材質對照 GT\n")
    any_faces = False
    total_wrong = 0
    total_judged = 0
    for it in items:
        if not it["faces"]:
            continue
        any_faces = True
        L.append(f"**{it['label']}**（`{it['run']}`）\n")
        L.append("| 面 | 材質 id | 來源 | GT | 正誤 |")
        L.append("|---|---|---|---|---|")
        for face in SURFACE_NAMES:
            f = it["faces"][face]
            L.append(f"| {face} | {f['material_id']} | {f['source']} | {f['gt'] or '缺'} | {f['verdict']} |")
            if f["verdict"] in ("✅", "❌"):
                total_judged += 1
                if f["verdict"] == "❌":
                    total_wrong += 1
        L.append("")
    if not any_faces:
        L.append("（本次沒有任何照片是「未 forced 通過」——沒有可列的六面表）\n")
    else:
        rate = f"{100.0 * total_wrong / total_judged:.0f}%" if total_judged else "—"
        L.append(
            f"**錯誤放行率彙總**：{total_wrong}/{total_judged}（{rate}）——分母固定 6／張，"
            "GT 缺或 `unknown` 的面標「無法判」不進分子分母。\n"
        )
    return L


def run(
    *,
    repo_root: Path = REPO_ROOT,
    out_dir: Path | None = None,
    heldout_photos_dir: Path | None = None,
    material_gt_path: Path | None = None,
) -> int:
    """全部參數帶預設值＝真實專案路徑，讓 `test_t17r2_tools.py` 可以指到隔離
    git repo 與樁資料重跑同一段邏輯。"""
    out_dir = out_dir if out_dir is not None else (repo_root / "output" / "mvp_acceptance_r2")
    heldout_photos_dir = heldout_photos_dir if heldout_photos_dir is not None else (repo_root / "assets" / "photos_heldout")
    material_gt_path = material_gt_path if material_gt_path is not None else (repo_root / "data" / "material_ground_truth.json")

    src = out_dir / "rt60_table.json"
    manifest_path = out_dir / "DATASET_MANIFEST.json"
    if not src.exists():
        print(f"❌ 找不到 {src}，請先跑 scripts/t17r2_rt60_table.py", file=sys.stderr)
        return 1
    if not manifest_path.exists():
        print(f"❌ 找不到 {manifest_path}，請先跑 scripts/t17r2_dataset_manifest.py", file=sys.stderr)
        return 1

    data = json.loads(src.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_root = repo_root / "output"
    runs_log_dir = out_dir / "runs"

    L: list[str] = []

    # ---------- 表 1：完整誤差表 ----------
    L.append("### 表 1　完整誤差表：8 場地 ×（6 頻段 ＋ 低頻聯合帶）\n")
    L.append(
        "誤差 =（生成 IR 量測 T30 − 真實 IR 量測 T30）/ 真實。"
        "✅ = 誤差 ≤20%；❌ = 超差；🟡 = 對多檔中位數超差但落在該場地多條真實 IR 的區間內。\n"
    )
    head = (
        "| 場地 | 路徑 | dims_source | group | forced | 125Hz | 250Hz | "
        "**500Hz** | **1kHz** | **2kHz** | **4kHz** | **聯合帶** |"
    )
    L.append(head)
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for v in data["venues"]:
        rr = v["real_reference"]
        n = rr["n_files"]
        real_cells = [fmt(rr["bands"][b]["value"]) for b in BANDS] + [fmt(rr["low_combined"]["value"])]
        tag = f"真實 IR（{n} 條中位數）" if n > 1 else "真實 IR"
        L.append(f"| **{v['label']}** | {tag} | — | — | — | " + " | ".join(real_cells) + " |")
        for g in v["generated"]:
            cells = [mark(g["errors"][b]) for b in BANDS] + [mark(g["errors"]["low_combined"])]
            L.append(
                f"| | `{g['run']}` | `{g['dims_source']}` | {g['group']} | "
                f"{'是' if g['forced_low_confidence'] else '否'} | " + " | ".join(cells) + " |"
            )
    L.append("")

    # ---------- 表 2：三組分列（裁決 C：不得合併） ----------
    L.append("### 表 2　達標率 —— 三組分列（裁決 C：不得合併成單一數字）\n")

    all_generated = [(v, g) for v in data["venues"] for g in v["generated"]]

    # 自動組：group=="auto" 且 in_domain
    auto_rows = [(v, g) for v, g in all_generated if g["group"] == "auto" and g["in_domain"]]
    L.append("**自動組**（`group==\"auto\"` 且 in-domain；F-01 產品主張本體）\n")
    L.append("| 場地 | run | 五項判準通過 | 全場地達標？ |")
    L.append("|---|---|---|---|")
    p = t = n_venue_pass = 0
    for v, g in auto_rows:
        ok = sum(1 for k in CRITERION_KEYS if g["errors"][k].get("within_tolerance"))
        tot = sum(1 for k in CRITERION_KEYS if g["errors"][k].get("error_pct") is not None)
        p += ok
        t += tot
        allpass = ok == tot and tot > 0
        n_venue_pass += 1 if allpass else 0
        L.append(f"| {v['label']} | `{g['run']}` | {ok}/{tot} | {'✅' if allpass else '❌'} |")
    if t:
        L.append(f"| **小計** | — | **{p}/{t}**（{100.0 * p / t:.0f}%）| **{n_venue_pass}/{len(auto_rows)} 場地全達標** |")
    else:
        L.append("| **小計** | — | **0/0** | **0/0 場地全達標** |")

    in_domain_venue_keys = {v["key"] for v in manifest.get("venues", []) if v.get("in_domain")}
    n_in_domain = len(in_domain_venue_keys)
    covered_keys = {v["key"] for v, g in auto_rows}
    n_covered = len(covered_keys & in_domain_venue_keys)
    L.append(
        f"**coverage** = 通過 gate 的 in-domain 場地數 / in-domain 場地數 = "
        f"**{n_covered}/{n_in_domain}**\n"
    )

    # forced 組：只列不計達標率
    forced_rows = [(v, g) for v, g in all_generated if g["group"] == "forced"]
    L.append("**forced 組**（被擋後 `--force-low-confidence` 產生，只記錄不計達標率）\n")
    L.append("| 場地 | run | in-domain | 500Hz | 1kHz | 2kHz | 4kHz | 聯合帶 |")
    L.append("|---|---|---|---|---|---|---|---|")
    if forced_rows:
        for v, g in forced_rows:
            cells = [mark(g["errors"][k]) for k in ("500", "1000", "2000", "4000", "low_combined")]
            L.append(f"| {v['label']} | `{g['run']}` | {'是' if g['in_domain'] else '否'} | " + " | ".join(cells) + " |")
    else:
        L.append("| （本次沒有 forced 組資料） | — | — | — | — | — | — | — |")
    L.append("")

    # 手動組：照 T-17 口徑，逐 run 標 forced
    manual_rows = [(v, g) for v, g in all_generated if g["group"] == "manual"]
    L.append("**手動組**（`--override-dims`，F-09 正式出口；照 T-17 另列成績，不混入自動組）\n")
    L.append("| 場地 | run | forced | 五項判準通過 | 全場地達標？ |")
    L.append("|---|---|---|---|---|")
    mp = mt = m_venue_pass = 0
    for v, g in manual_rows:
        ok = sum(1 for k in CRITERION_KEYS if g["errors"][k].get("within_tolerance"))
        tot = sum(1 for k in CRITERION_KEYS if g["errors"][k].get("error_pct") is not None)
        mp += ok
        mt += tot
        allpass = ok == tot and tot > 0
        m_venue_pass += 1 if allpass else 0
        L.append(
            f"| {v['label']} | `{g['run']}` | {'是' if g['forced_low_confidence'] else '否'} | "
            f"{ok}/{tot} | {'✅' if allpass else '❌'} |"
        )
    if mt:
        L.append(f"| **小計** | — | — | **{mp}/{mt}**（{100.0 * mp / mt:.0f}%）| **{m_venue_pass}/{len(manual_rows)} 場地全達標** |")
    else:
        L.append("| **小計** | — | — | **0/0** | **0/0 場地全達標** |")
    L.append("")

    # ---------- 表 3：500Hz vs 聯合帶階梯比 ----------
    L.append("### 表 3　500Hz vs 低頻聯合帶 階梯比\n")
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
        L.append(f"| {v['label']} | {fmt(real_r)} | {'<br>'.join(gens)} | {'⚠️ 是' if risky else '否'} |")
    L.append("")

    # ---------- 表 4：手動尺寸來源依據 ----------
    L.append("### 表 4　手動尺寸（F-09）的來源依據 —— 逐項標明，不得當成場地真值\n")
    L.append("| run | 採用尺寸 | 依據 |")
    L.append("|---|---|---|")
    for v, g in manual_rows:
        d = g["dims_m"]
        basis = MANUAL_DIMS_BASIS_R2.get(g["run"], "**未記錄依據**")
        L.append(f"| `{g['run']}` | {d['length']:.2f}×{d['width']:.2f}×{d['height']:.2f} m | {basis} |")
    L.append("")

    # ---------- 表 5：報告項 5（13 張逐張 gate／domain／六面材質對照） ----------
    L.append("### 表 5　報告項 5 —— 13 張（5 held-out ＋ 8 場地）逐張 gate／domain／六面材質對照\n")
    # legacy（degraded）路徑沒有 ground_truth_heldout.json（舊五張本來就不是
    # held-out，也沒有這份 GT 檔）——一律回傳空 dict，六面表全部標「GT 缺」。
    ground_truth_heldout = (
        {} if manifest.get("degraded") else common.load_ground_truth_heldout(heldout_photos_dir)
    )
    material_gt = (
        json.loads(material_gt_path.read_text(encoding="utf-8")) if material_gt_path.exists() else {"photos": {}}
    )

    items5 = []
    for hp in manifest.get("heldout_photos", []):
        gt_surfaces = ground_truth_heldout.get(hp["stem"], {}).get("surfaces")
        items5.append(
            build_item5(
                label=f"held-out：{hp['category']}",
                run_stem=hp["stem"],
                domain=hp["domain"],
                gt_surfaces=gt_surfaces,
                output_root=output_root,
                runs_log_dir=runs_log_dir,
            )
        )
    for v in manifest.get("venues", []):
        gt_name = common.VENUE_KEY_TO_GT_NAME.get(v["key"])
        gt_surfaces = material_gt.get("photos", {}).get(gt_name) if gt_name else None
        # 自動路徑的 run（`group` 為 auto 或 forced；手動組 `--override-dims`
        # 跳過 gate、不是報告項 5 要看的「gate 有沒有誤放」對象）。
        rv_entry = next((rv for rv in data["venues"] if rv["key"] == v["key"]), None)
        auto_g = next(
            (g for g in (rv_entry or {}).get("generated", []) if g["group"] in ("auto", "forced")),
            None,
        )
        run_stem = auto_g["run"] if auto_g else None
        if run_stem is None:
            items5.append(
                {
                    "label": v["label"], "run": "（尚無自動路徑 run）",
                    "domain": "in" if v.get("in_domain") else "out",
                    "gate_result": None, "forced": None, "override_dims_guidance": None,
                    "domain_leak": False, "faces": None, "status": "尚未產生",
                }
            )
            continue
        items5.append(
            build_item5(
                label=v["label"],
                run_stem=run_stem,
                domain="in" if v.get("in_domain") else "out",
                gt_surfaces=gt_surfaces,
                output_root=output_root,
                runs_log_dir=runs_log_dir,
            )
        )
    L.extend(render_item5_table(items5))

    out = out_dir / "tables.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"已寫入 {out}（{len(L)} 行）")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
