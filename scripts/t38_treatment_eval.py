#!/usr/bin/env python3
"""T-38：CLIP 提示詞治療 —— 78 面正確率量測驅動程式（治療模式）。

跑法：`python scripts/t38_treatment_eval.py <round_label> [--fresh] --hypothesis "..." [--parent <round_label>]`
（例如 `round0_baseline`／`round7`）。輸出寫到
`output/clip_treatment/rounds/<round_label>/`，一律是非凍結目錄
（`output/clip_accuracy/` 的 T-36 凍結基線本腳本完全不寫）。

**治療模式與 `t36_clip_accuracy.py` 的唯一差異**：與 T-33 凍結快取
（`output/material_round/runs/<name>__no_furn/analysis.json`）的交叉守門，
在這裡改成「產差異清單、繼續往下跑」，而不是 `sys.exit(1)`——因為 T-37 已
正當修正 `TunnelToHell`，它的 surfaces/sources 與 T-33 凍結快取本來就不再
相同（見 HANDOFF_T38.md 地雷 B）。`t36_clip_accuracy.py` 本身的預設模式行為
**完全不動**（不 import 這支腳本改寫它，只唯讀 import 它的模組級常數與函式）。

本腳本只唯讀 import：
- `t36_clip_accuracy` 的 `GATE_ITEMS`／`EXPECTED_GATE`／`run_or_load`／
  `OOD_PREFIX`／`THRESHOLD`／`MATERIAL_ROUND_RUNS`／`GROUND_TRUTH_PATH`
  （13 張清單與量測驅動邏輯，不重打、不重新實作）
- `t36_analysis` 的 `build_accuracy_tables`／`build_error_type_tables`／
  `build_threshold_sensitivity`／`build_ceiling_simulation`（材質計分邏輯，
  不重新實作）
- `src.image_reverb.surfaces` / `materials`（唯讀呼叫
  `compute_materials_confidence()`，規則零改動）

`src/`、`data/`（含 `material_ground_truth.json`）本腳本全程只讀不寫。
每一輪的完整表格與逐面判定快取都留在 `runs/`，可回溯每一輪動了什麼提示詞
之後正確率如何變化（卡片要求：允許迭代，但每輪都要在完整 78 面上量測）。

**T-38A 新增（工程卡：可重現評測 harness＋輪次紀錄）**：
1. `diff_scope_summary()`：修正舊版「只要有差異就印預期只有 TunnelToHell」
   的誤導訊息——真正檢查差異涉及的照片集合。
2. `publish_round_artifacts()`：原子發布（先寫暫存檔，全部完成才 rename 落地，
   `summary.json` 最後才落地，讀取端只認它存在與否當完整性判準）。
3. `build_round_md()` 等：每輪自動產生會進版控的 `ROUND.md`（快照／差異／
   父輪次／假設／指令／指紋／數字／status），供 T-38B 後續輪次使用。
4. `load_completed_rounds()`：讀取端跳過無 `summary.json` 或 status 非
   complete 的輪次，不得靜默納入比較。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from src.image_reverb import surfaces as surfaces_mod  # noqa: E402
from src.image_reverb import materials as materials_mod  # noqa: E402

import t36_clip_accuracy as t36  # noqa: E402  （唯讀引用，不改寫）
from t36_analysis import (  # noqa: E402  （唯讀引用，不重新實作計分邏輯）
    build_accuracy_tables,
    build_error_type_tables,
    build_threshold_sensitivity,
    build_ceiling_simulation,
    _pct,
    _md_table,
    FACES,
)

TREATMENT_ROOT = REPO_ROOT / "output" / "clip_treatment"
BASELINE_LABEL = "round0_baseline"


def cross_check_treatment(name: str, payload: dict) -> list[str]:
    """比照 `t36_clip_accuracy.cross_check_against_frozen_baseline()`，但回傳
    差異描述清單而非 `sys.exit(1)`——治療模式的守門不卡關，只記錄。"""
    diffs: list[str] = []
    frozen_path = t36.MATERIAL_ROUND_RUNS / f"{name}__no_furn" / "analysis.json"
    if not frozen_path.exists():
        diffs.append(f"{name}：找不到 T-33 凍結快取 {frozen_path}，無法比對。")
        return diffs
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))

    if payload["surfaces"] != frozen["surfaces"]:
        diffs.append(
            f"{name}：surfaces 與 T-33 凍結快取不同（凍結={frozen['surfaces']}，"
            f"本次={payload['surfaces']}）"
        )
    if payload["sources"] != frozen.get("surfaces_sources", {}):
        diffs.append(
            f"{name}：sources 與 T-33 凍結快取不同（凍結={frozen.get('surfaces_sources')}，"
            f"本次={payload['sources']}）"
        )
    expected_geo, expected_mat = t36.EXPECTED_GATE[name]
    if frozen["geometry_confidence"] != expected_geo or frozen["materials_confidence"] != expected_mat:
        diffs.append(
            f"{name}：T-33 凍結快取三軸與裁決 T-28-A 基線不符"
            f"（geometry={frozen['geometry_confidence']}, materials={frozen['materials_confidence']}，"
            f"基線={expected_geo}/{expected_mat}）"
        )

    surf_obj = materials_mod.SurfaceMaterials(**payload["surfaces"])
    surf_obj.sources = dict(payload["sources"])
    surf_obj.warnings = list(payload["warnings"])
    recomputed = surfaces_mod.compute_materials_confidence(surf_obj)
    if recomputed != expected_mat:
        diffs.append(
            f"{name}：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() "
            f"得到 {recomputed}，與 T-28-A 基線 {expected_mat} 不同"
        )
    return diffs


def diff_scope_summary(diff_photo_names: set[str]) -> str:
    """T-38A 步驟 1 修正（地雷：舊版只要 `all_diffs` 非空就印同一句「預期只有
    TunnelToHell 三項比對」，round3／round5 明明有多張照片大量漂移也印同一句）。

    真正檢查差異涉及的照片集合：只有 TunnelToHell 一張有差異才符合
    HANDOFF_T38.md 地雷 B 記載的預期（T-37 修正後 TunnelToHell 走透視路徑，
    與 T-33 凍結快取本來就不同）；出現任何其他照片都必須明確列出，不能被
    「預期只有 TunnelToHell」這句蓋過去。
    """
    if not diff_photo_names:
        return "無差異"
    if diff_photo_names == {"TunnelToHell"}:
        return "符合預期（僅 TunnelToHell，T-37 修正後與 T-33 凍結快取本來就不同，見 HANDOFF_T38.md 地雷 B）"
    unexpected = sorted(diff_photo_names - {"TunnelToHell"})
    return (
        f"非預期範圍：{len(diff_photo_names)} 張照片有差異"
        f"（{', '.join(sorted(diff_photo_names))}），其中 {len(unexpected)} 張非 TunnelToHell"
        f"（{', '.join(unexpected)}），多半是本輪提示詞造成的漂移"
    )


def round_summary(accuracy: dict, error_types: dict) -> dict:
    """壓縮成一輪的關鍵數字，供輪次軌跡表使用（不重算，直接讀 build_accuracy_tables 的結果）。"""
    overall = accuracy["overall"]
    denom = overall["total"] - overall["excluded"]
    per_role = accuracy["per_role"]
    clip_bucket = accuracy["per_source"].get("clip", {"total": 0, "correct": 0, "excluded": 0})
    clip_denom = clip_bucket["total"] - clip_bucket["excluded"]

    def role_pct(role: str) -> tuple[int, int]:
        b = per_role[role]
        return b["correct"], b["total"] - b["excluded"]

    floor_c, floor_d = role_pct("floor")
    return {
        "overall_correct": overall["correct"],
        "overall_denom": denom,
        "floor_correct": floor_c,
        "floor_denom": floor_d,
        "clip_correct": clip_bucket["correct"],
        "clip_denom": clip_denom,
        "in_set_errors": len(error_types["in_set_errors"]),
        "non_proxy_correct": accuracy["non_proxy_stats"]["correct"],
        "non_proxy_total": accuracy["non_proxy_stats"]["total"],
        "proxy_correct": accuracy["proxy_stats"]["correct"],
        "proxy_total": accuracy["proxy_stats"]["total"],
    }


def build_round_tables_text(accuracy: dict, error_types: dict, diffs: list[str], scope_msg: str) -> str:
    """一輪的詳表（不含③④——那兩節每輪數字相同，只在最終報告列一次）。"""
    parts = []
    overall = accuracy["overall"]
    denom = overall["total"] - overall["excluded"]

    parts.append("## 表 1：總體正確率\n")
    parts.append(_md_table(
        ["指標", "數值"],
        [
            ["總面數", str(overall["total"])],
            ["排除（ground truth = unknown）", str(overall["excluded"])],
            ["正確率分母", str(denom)],
            ["正確率", _pct(overall["correct"], denom)],
            ["非 proxy 正確率", _pct(accuracy["non_proxy_stats"]["correct"], accuracy["non_proxy_stats"]["total"])],
            ["proxy 正確率", _pct(accuracy["proxy_stats"]["correct"], accuracy["proxy_stats"]["total"])],
        ],
    ))

    parts.append("\n\n## 表 2：按判定來源分組\n")
    source_rows = []
    for src in ("clip", "fallback", "out_of_domain", "無來源"):
        b = accuracy["per_source"].get(src, {"total": 0, "correct": 0, "excluded": 0})
        d = b["total"] - b["excluded"]
        source_rows.append([src, str(b["total"]), str(b["excluded"]), _pct(b["correct"], d)])
    parts.append(_md_table(["來源", "面數", "排除數", "正確率"], source_rows))

    parts.append("\n\n## 表 3：按角色分組\n")
    role_rows = []
    for role in ("floor", "ceiling", "wall"):
        b = accuracy["per_role"][role]
        d = b["total"] - b["excluded"]
        role_rows.append([role, str(b["total"]), str(b["excluded"]), _pct(b["correct"], d)])
    parts.append(_md_table(["角色", "面數", "排除數", "正確率"], role_rows))

    parts.append("\n\n## 表 4：地雷 #18 型 in-set 誤判明細\n")
    if error_types["in_set_errors"]:
        parts.append(_md_table(
            ["照片", "面", "AI 判定", "ground truth"],
            [[r["photo"], r["face"], r["ai"], r["gt"]] for r in error_types["in_set_errors"]],
        ))
    else:
        parts.append("（無）")

    parts.append("\n\n## 與 T-33 凍結快取的差異（治療模式，僅記錄不卡關；見 HANDOFF_T38.md 地雷 B）\n")
    parts.append(f"**範圍評估**：{scope_msg}\n")
    parts.append("\n".join(f"- {d}" for d in diffs) if diffs else "（無差異）")

    return "\n".join(parts) + "\n"


# ------------------------------------------------------------------
# T-38A 步驟 2：原子發布——先寫暫存檔，全部完成才 rename 落地。
# `summary.json` 最後才落地：讀取端只認它「存在」當這輪完整的判準
# （見 load_completed_rounds()）。任何一步中途失敗，之前已落地的檔案不回滾，
# 但 summary.json 保證不存在，讀取端仍會正確判定這輪不完整、不納入比較。
# ------------------------------------------------------------------

def _atomic_write_text(path: Path, content: str) -> None:
    tmp_path = path.with_name(path.name + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def publish_round_artifacts(
    round_dir: Path,
    *,
    tables_text: str,
    round_md_text: str,
    snapshot: dict,
    summary: dict,
) -> None:
    round_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(round_dir / "tables.md", tables_text)
    _atomic_write_text(
        round_dir / "prompts_snapshot.json",
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
    )
    _atomic_write_text(round_dir / "ROUND.md", round_md_text)
    # summary.json 必須最後落地——見上方模組註解。
    _atomic_write_text(
        round_dir / "summary.json",
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
    )


# ------------------------------------------------------------------
# T-38A 步驟 2：讀取端跳過邏輯——無 summary.json 或 status 非 complete 一律跳過。
# ------------------------------------------------------------------

def _extract_round_md_status(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip().lstrip("-").strip()
        if stripped.lower().startswith("status:"):
            return stripped.split(":", 1)[1].strip().strip("`").strip()
    return None


def load_completed_rounds(rounds_root: Path) -> tuple[list[dict], list[str]]:
    """掃 `rounds_root` 底下所有輪次目錄，回傳 `(完整輪次清單, 被跳過的說明清單)`。

    完整的判準：`summary.json` 存在；若同目錄有 `ROUND.md` 且能解析出
    `status` 欄，該欄必須是 `complete`，否則即使 `summary.json` 意外存在
    也不採信。只留 `.tmp` 殘檔（中途失敗的產物）不會被當成 `summary.json`
    存在——`Path.exists()` 只認完整檔名，`.tmp` 後綴不匹配。
    """
    completed: list[dict] = []
    skipped: list[str] = []
    if not rounds_root.exists():
        return completed, skipped
    for round_dir in sorted(p for p in rounds_root.iterdir() if p.is_dir()):
        label = round_dir.name
        summary_path = round_dir / "summary.json"
        if not summary_path.exists():
            skipped.append(f"{label}：無 summary.json（不完整或中止的輪次），跳過")
            continue
        round_md_path = round_dir / "ROUND.md"
        status = None
        if round_md_path.exists():
            status = _extract_round_md_status(round_md_path.read_text(encoding="utf-8"))
        if status is not None and status != "complete":
            skipped.append(f"{label}：ROUND.md status={status}（非 complete），跳過")
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        completed.append({"label": label, "summary": summary, "status": status or "complete"})
    return completed, skipped


# ------------------------------------------------------------------
# T-38A 步驟 3：每輪自動生成會進版控的 ROUND.md。
# ------------------------------------------------------------------

def snapshot_prompts() -> dict:
    """讀目前記憶體中 `surfaces` 模組的提示詞字典（即本次執行當下的提示詞）。"""
    return {
        "CLIP_MATERIAL_PROMPTS": dict(surfaces_mod.CLIP_MATERIAL_PROMPTS),
        "CLIP_OOD_PROMPTS": dict(surfaces_mod.CLIP_OOD_PROMPTS),
    }


def diff_prompt_snapshots(baseline: dict | None, current: dict) -> list[str]:
    """回傳 `current` 相對 `baseline` 的逐鍵字串差異（人類可讀）。
    `baseline` 為 None（例如 round0_baseline 自己還沒發布過快照）時，
    回傳明確的「無基線快照可比對」，不得假裝有差異或無差異。
    """
    if baseline is None:
        return ["（無基線快照可比對）"]
    diffs: list[str] = []
    for group in ("CLIP_MATERIAL_PROMPTS", "CLIP_OOD_PROMPTS"):
        base_group = baseline.get(group, {})
        cur_group = current.get(group, {})
        for key in sorted(set(base_group) | set(cur_group)):
            b = base_group.get(key)
            c = cur_group.get(key)
            if b == c:
                continue
            if key not in base_group:
                diffs.append(f"{group}.{key}：新增（\"{c}\"）")
            elif key not in cur_group:
                diffs.append(f"{group}.{key}：刪除（原「{b}」）")
            else:
                diffs.append(f"{group}.{key}：「{b}」→「{c}」")
    return diffs


def load_baseline_snapshot(rounds_root: Path, baseline_label: str = BASELINE_LABEL) -> dict | None:
    path = rounds_root / baseline_label / "prompts_snapshot.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def collect_round_fingerprint(runs_dir: Path, gate_items: list[dict]) -> dict:
    """從各張照片的 `detail.json` 快取讀出指紋，彙整成一輪的指紋紀錄。
    `code_sha256`／`data_sha256`／模型 id／門檻／`eval_mode` 理論上整輪應該
    一致（同一次執行、同一份 `surfaces.py`），只有 `photo_sha256` 逐張不同
    ——不一致代表跑到一半換了程式碼，直接丟例外讓呼叫端知道，不得靜默吞掉。
    """
    shared: dict | None = None
    per_photo: dict[str, str] = {}
    for item in gate_items:
        name = item["name"]
        cache_path = runs_dir / name / "detail.json"
        if not cache_path.exists():
            raise ValueError(f"{name}：找不到 {cache_path}，無法收集指紋。")
        entry = json.loads(cache_path.read_text(encoding="utf-8"))
        fp = entry.get("fingerprint")
        if fp is None:
            raise ValueError(f"{name}：快取無 fingerprint 欄位，無法收集指紋。")
        per_photo[name] = fp["photo_sha256"]
        current_shared = {k: v for k, v in fp.items() if k != "photo_sha256"}
        if shared is None:
            shared = current_shared
        elif shared != current_shared:
            raise ValueError(
                f"{name}：本輪內指紋不一致（code/data/model/threshold/eval_mode 應整輪相同）："
                f"{shared} != {current_shared}"
            )
    return {"shared": shared or {}, "per_photo_sha256": per_photo}


def build_round_md(
    *,
    round_label: str,
    parent: str,
    status: str,
    hypothesis: str,
    command: str,
    current_snapshot: dict,
    prompt_diffs: list[str],
    summary: dict,
    per_source: dict,
    fingerprint: dict,
) -> str:
    lines: list[str] = []
    lines.append(f"# Round `{round_label}` — T-38 治療輪紀錄\n")
    lines.append(f"- status: {status}")
    lines.append(f"- 父輪次: {parent}")
    lines.append(f"- 執行指令: `{command}`")
    lines.append(f"- 本輪假設與修改理由: {hypothesis}")
    lines.append("")
    lines.append("## CLIP_MATERIAL_PROMPTS / CLIP_OOD_PROMPTS 快照\n")
    lines.append("```json")
    lines.append(json.dumps(current_snapshot, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append(f"## 相對 {BASELINE_LABEL} 的字串差異\n")
    if prompt_diffs:
        lines.extend(f"- {d}" for d in prompt_diffs)
    else:
        lines.append("（無差異）")
    lines.append("")
    lines.append("## 正確率數字\n")
    lines.append(_md_table(
        ["指標", "數值"],
        [
            ["overall", f"{summary['overall_correct']}/{summary['overall_denom']}"],
            ["floor", f"{summary['floor_correct']}/{summary['floor_denom']}"],
            ["in-set 誤判", str(summary["in_set_errors"])],
            ["clip 來源正確率", f"{summary['clip_correct']}/{summary['clip_denom']}"],
            ["非 proxy 正確率", f"{summary['non_proxy_correct']}/{summary['non_proxy_total']}"],
            ["proxy 正確率", f"{summary['proxy_correct']}/{summary['proxy_total']}"],
        ],
    ))
    lines.append("")
    lines.append("## 按判定來源分組\n")
    source_rows = []
    for src in ("clip", "fallback", "out_of_domain", "無來源"):
        b = per_source.get(src, {"total": 0, "correct": 0, "excluded": 0})
        d = b["total"] - b["excluded"]
        source_rows.append([src, str(b["total"]), str(b["excluded"]), _pct(b["correct"], d)])
    lines.append(_md_table(["來源", "面數", "排除數", "正確率"], source_rows))
    lines.append("")
    lines.append("## 指紋（沿用 `eval_cache.py` 六類指紋）\n")
    shared = fingerprint.get("shared", {})
    lines.append(_md_table(
        ["項目", "值"],
        [
            ["code_sha256", json.dumps(shared.get("code_sha256", {}), ensure_ascii=False)],
            ["data_sha256", json.dumps(shared.get("data_sha256", {}), ensure_ascii=False)],
            ["segmentation_model_id", str(shared.get("segmentation_model_id"))],
            ["clip_model_id", str(shared.get("clip_model_id"))],
            ["clip_threshold", str(shared.get("clip_threshold"))],
            ["eval_mode", str(shared.get("eval_mode"))],
        ],
    ))
    lines.append("")
    lines.append("### 逐張照片 photo_sha256\n")
    per_photo = fingerprint.get("per_photo_sha256", {})
    lines.append(_md_table(["照片", "sha256"], [[k, v] for k, v in sorted(per_photo.items())]))
    lines.append("")
    lines.append("詳細逐面判定與 in-set 誤判明細見同目錄 `tables.md`。")
    return "\n".join(lines) + "\n"


def run_round(
    round_label: str,
    *,
    force_fresh: bool,
    parent: str,
    hypothesis: str,
    command: str,
) -> dict:
    if not hypothesis or not hypothesis.strip():
        print("🔴 卡關：本輪假設與修改理由（--hypothesis）不得留空。")
        sys.exit(1)

    round_dir = TREATMENT_ROOT / "rounds" / round_label
    runs_dir = round_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    if not t36.GROUND_TRUTH_PATH.exists():
        print(f"🔴 卡關：找不到 {t36.GROUND_TRUTH_PATH}")
        sys.exit(1)
    ground_truth = json.loads(t36.GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    gt_photos = ground_truth["photos"]

    all_data: dict[str, dict] = {}
    all_diffs: list[str] = []
    diff_photo_names: set[str] = set()
    print(f"=== 治療模式 round={round_label}：逐面判定明細（跑或讀快取） ===")
    for item in t36.GATE_ITEMS:
        name = item["name"]
        payload = t36.run_or_load(
            item, runs_dir=runs_dir, is_frozen=False, force_fresh=force_fresh,
            eval_mode=f"treatment:{round_label}",
        )
        diffs = cross_check_treatment(name, payload)
        if diffs:
            diff_photo_names.add(name)
        all_diffs.extend(diffs)
        all_data[name] = payload
        print(f"✓ {name}（{'equirect' if payload['is_equirect'] else 'perspective'}）")

    accuracy = build_accuracy_tables(t36.GATE_ITEMS, all_data, gt_photos)
    error_types = build_error_type_tables(t36.GATE_ITEMS, all_data, gt_photos, t36.OOD_PREFIX)
    sensitivity = build_threshold_sensitivity(t36.GATE_ITEMS, all_data, gt_photos, t36.OOD_PREFIX, t36.THRESHOLD)
    simulation = build_ceiling_simulation(t36.GATE_ITEMS, all_data, gt_photos, surfaces_mod, t36.EXPECTED_GATE)

    scope_msg = diff_scope_summary(diff_photo_names)
    tables_text = build_round_tables_text(accuracy, error_types, all_diffs, scope_msg)
    summary = round_summary(accuracy, error_types)

    current_snapshot = snapshot_prompts()
    baseline_snapshot = load_baseline_snapshot(TREATMENT_ROOT / "rounds") if round_label != BASELINE_LABEL else None
    prompt_diffs = (
        [] if round_label == BASELINE_LABEL else diff_prompt_snapshots(baseline_snapshot, current_snapshot)
    )
    fingerprint = collect_round_fingerprint(runs_dir, t36.GATE_ITEMS)
    round_md_text = build_round_md(
        round_label=round_label,
        parent=parent,
        status="complete",
        hypothesis=hypothesis,
        command=command,
        current_snapshot=current_snapshot,
        prompt_diffs=prompt_diffs,
        summary=summary,
        per_source=accuracy["per_source"],
        fingerprint=fingerprint,
    )

    publish_round_artifacts(
        round_dir,
        tables_text=tables_text,
        round_md_text=round_md_text,
        snapshot=current_snapshot,
        summary=summary,
    )

    print(
        f"\nround={round_label} 完成：整體 {_pct(summary['overall_correct'], summary['overall_denom'])}、"
        f"floor {_pct(summary['floor_correct'], summary['floor_denom'])}、"
        f"in-set 誤判 {summary['in_set_errors']} 面、"
        f"T-33 凍結快取差異 {len(all_diffs)} 項（{scope_msg}）。"
    )
    return {
        "accuracy": accuracy, "error_types": error_types, "sensitivity": sensitivity,
        "simulation": simulation, "diffs": all_diffs, "all_data": all_data, "summary": summary,
    }


def main() -> int:
    argv = sys.argv[1:]
    force_fresh = "--fresh" in argv
    hypothesis: str | None = None
    parent: str | None = None
    positional: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--fresh":
            i += 1
        elif arg == "--hypothesis":
            if i + 1 >= len(argv):
                print("🔴 卡關：--hypothesis 需要接一段文字。")
                return 1
            hypothesis = argv[i + 1]
            i += 2
        elif arg == "--parent":
            if i + 1 >= len(argv):
                print("🔴 卡關：--parent 需要接一個輪次標籤。")
                return 1
            parent = argv[i + 1]
            i += 2
        else:
            positional.append(arg)
            i += 1

    if not positional:
        print(
            "用法：python scripts/t38_treatment_eval.py <round_label> [--fresh] "
            "--hypothesis \"...\" [--parent <round_label>]"
        )
        return 1
    round_label = positional[0]

    if round_label == BASELINE_LABEL:
        if hypothesis is None:
            hypothesis = "基線量測，未修改任何提示詞（round0_baseline 本身即基線，無假設）"
        if parent is None:
            parent = "（無——本輪即基線）"
    else:
        if hypothesis is None:
            print("🔴 卡關：非基線輪次必須用 --hypothesis \"...\" 提供本輪假設與修改理由，不得留空。")
            return 1
        if parent is None:
            parent = BASELINE_LABEL

    command = "python scripts/t38_treatment_eval.py " + " ".join(argv)
    run_round(round_label, force_fresh=force_fresh, parent=parent, hypothesis=hypothesis, command=command)
    return 0


if __name__ == "__main__":
    sys.exit(main())
