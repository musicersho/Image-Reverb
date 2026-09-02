#!/usr/bin/env python3
"""T-44：role-aware 候選子集 —— 78 面正確率量測驅動程式（分區模式）。

跑法：`python scripts/t44_role_eval.py <round_label> [--fresh] --hypothesis "..." [--parent <round_label>]`
（例如 `round15_role_partition`）。輸出寫到 `output/clip_treatment/rounds/<round_label>/`，
與 T-38/T-39 共用同一個 `rounds/` 目錄與 ROUND.md／summary.json 機制（沿用
T-38A harness，見 `t38_treatment_eval.py` 模組文件）。

**與 `t38_treatment_eval.py` 的差異**：T-38/T-39 的治療只改提示詞字串／候選集
內容，`surfaces_from_preprocess()` 一律用預設的 `role_aware=False`（全域候選集）
呼叫，重用 `t36.run_or_load()` 即可。T-44 需要 `role_aware=True`，`t36.run_or_load()`
不支援這個參數（`t36_clip_accuracy.py` 是唯讀 import 的量測卡，不得為了 T-44
改寫），所以本檔自己實作等價的 `run_or_load_role_aware()`——快取讀寫／指紋／
`_flatten_perspective`／`_flatten_equirect` 全部唯讀重用 `t36`／`eval_cache`
既有函式，只有 `_run()` 內部改呼叫
`surfaces_from_preprocess(prep_summary, role_aware=True)`。

比較基線：`round11_remap_baseline`（重對映後、候選未動的最終狀態，
overall 30/76、floor 4/13、ceiling 3/11、wall 23/52、非 proxy 30/63、
in-set 誤判 9）——不是 `round0_baseline`，也不是已否定的 `round12`～`14`。

ROUND.md／tables.md／summary.json／prompts_snapshot.json 的產生／發布／讀取
全部唯讀 import 自 `t38_treatment_eval`（原子發布、讀取端跳過邏輯、指紋彙整、
字串快照差異——這些機制與 T-44 要不要 role-aware 無關，不重新實作）。額外多
發布一份 `partition_snapshot.json`（`ROLE_MATERIAL_CANDIDATES` 的快照），
供分區表跨輪比對（提示詞字串本輪不動，變動的是分區表）。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from src.image_reverb import preprocess  # noqa: E402
from src.image_reverb import surfaces as surfaces_mod  # noqa: E402

import eval_cache  # noqa: E402  （T-40，唯讀引用）
import t36_clip_accuracy as t36  # noqa: E402  （唯讀引用，不改寫）
import t38_treatment_eval as t38  # noqa: E402  （唯讀引用，重用 harness 機制）
from t36_analysis import (  # noqa: E402  （唯讀引用，不重新實作計分邏輯）
    build_accuracy_tables,
    build_error_type_tables,
    build_ceiling_simulation,
    ROLE_OF_FACE,
    FACES,
    _pct,
    _md_table,
)

TREATMENT_ROOT = REPO_ROOT / "output" / "clip_treatment"
BASELINE_LABEL = "round11_remap_baseline"  # T-44 比較基線（PLAN_T44.md §4）


# ------------------------------------------------------------------
# 等價於 t36.run_or_load()，但 _run() 用 role_aware=True 呼叫
# surfaces_from_preprocess()。快取／指紋／flatten 邏輯唯讀重用 t36／eval_cache。
# ------------------------------------------------------------------

def run_or_load_role_aware(
    item: dict, *, runs_dir: Path, force_fresh: bool, eval_mode: str
) -> dict:
    name = item["name"]
    run_dir = runs_dir / name
    cache_path = run_dir / "detail.json"
    photo_path = REPO_ROOT / item["photo"]

    def _fingerprint() -> dict:
        return eval_cache.compute_fingerprint(
            photo_path=photo_path,
            code_paths=t36.FINGERPRINT_CODE_PATHS,
            data_paths=t36.FINGERPRINT_DATA_PATHS,
            segmentation_model_id=surfaces_mod.config.SEGMENTATION_MODEL_ID,
            clip_model_id=surfaces_mod.config.CLIP_MODEL_ID,
            clip_threshold=t36.THRESHOLD,
            eval_mode=eval_mode,
        )

    def _run() -> dict:
        run_dir.mkdir(parents=True, exist_ok=True)
        prep_summary = preprocess.preprocess_image(photo_path, output_dir=run_dir / "preprocess")
        surfaces_obj, detail = surfaces_mod.surfaces_from_preprocess(prep_summary, role_aware=True)
        is_equirect = bool(prep_summary["is_equirect"])
        faces = t36._flatten_equirect(detail) if is_equirect else t36._flatten_perspective(detail)
        return {
            "is_equirect": is_equirect,
            "surfaces": surfaces_obj.as_dict(),
            "sources": surfaces_obj.sources,
            "warnings": surfaces_obj.warnings,
            "faces": faces,
        }

    payload, was_rerun, reasons = eval_cache.load_or_run(
        cache_path=cache_path,
        fingerprint_fn=_fingerprint,
        run_fn=_run,
        is_frozen=False,
        force_fresh=force_fresh,
    )
    if was_rerun and reasons:
        print(f"  ↻ {name}：快取失效，已重跑（原因：{'; '.join(reasons)}）")
    return payload


# ------------------------------------------------------------------
# 按角色分別做門檻敏感度掃描（PLAN_T44.md §4：不得只跑一份全域敏感度表）
# ------------------------------------------------------------------

def build_threshold_sensitivity_per_role(
    gate_items: list[dict], all_data: dict, gt_photos: dict, ood_prefix: str, current_threshold: float
) -> dict[str, dict]:
    """比照 t36_analysis.build_threshold_sensitivity()，但依 ROLE_OF_FACE 分三組。
    邏輯與該函式完全相同（同一組門檻掃描點），只是先把 fallback 面按角色分桶。
    """
    per_role_records: dict[str, list[dict]] = {"floor": [], "ceiling": [], "wall": []}
    for item in gate_items:
        name = item["name"]
        payload = all_data[name]
        gt_faces = gt_photos[name]
        for face in FACES:
            if payload["sources"].get(face, "無來源") != "fallback":
                continue
            gt_val = gt_faces[face]["material_id"]
            if gt_val == "unknown":
                continue
            detail = payload["faces"].get(face)
            if not detail or not detail.get("top3"):
                continue
            top1_id, top1_conf = detail["top3"][0]
            per_role_records[ROLE_OF_FACE[face]].append({
                "photo": name, "face": face, "top1": top1_id, "top1_conf": top1_conf,
                "gt": gt_val, "top1_correct": top1_id == gt_val,
            })

    result: dict[str, dict] = {}
    for role, records in per_role_records.items():
        sweep = []
        for th in (0.20, 0.25, 0.30, 0.35, current_threshold):
            would_flip = [r for r in records if r["top1_conf"] >= th]
            flip_correct = sum(1 for r in would_flip if r["top1_correct"])
            sweep.append({
                "threshold": th, "would_flip_to_clip": len(would_flip),
                "would_be_correct": flip_correct, "would_be_wrong": len(would_flip) - flip_correct,
            })
        result[role] = {"records": records, "sweep": sweep}
    return result


def build_sensitivity_per_role_text(sensitivity_per_role: dict, current_threshold: float) -> str:
    parts = [f"\n\n## 表 7'：fallback 門檻（{current_threshold}）敏感度分析——按角色分開（PLAN_T44.md §4）\n"]
    for role in ("floor", "ceiling", "wall"):
        s = sensitivity_per_role[role]
        parts.append(f"\n### {role}\n")
        parts.append(_md_table(
            ["候選門檻", "會被放行到 clip 的面數", "放行後答對", "放行後答錯"],
            [[f"{r['threshold']:.2f}", str(r["would_flip_to_clip"]), str(r["would_be_correct"]), str(r["would_be_wrong"])]
             for r in s["sweep"]],
        ))
        if s["records"]:
            parts.append("\n")
            parts.append(_md_table(
                ["照片", "面", "top-1 原始候選", "top-1 信心", "ground truth", "是否正確"],
                [[r["photo"], r["face"], r["top1"], f"{r['top1_conf']:.3f}", r["gt"], "✓" if r["top1_correct"] else "✗"]
                 for r in s["records"]],
            ))
        else:
            parts.append("\n（無可分析的 fallback 面）\n")
    return "\n".join(parts) + "\n"


# ------------------------------------------------------------------
# 分區表快照（唯讀 snapshot，供跨輪比對——本輪的字串不變，變的是分區表）
# ------------------------------------------------------------------

def snapshot_partition() -> dict:
    return {role: list(ids) for role, ids in surfaces_mod.ROLE_MATERIAL_CANDIDATES.items()}


def diff_partition_snapshots(baseline: dict | None, current: dict) -> list[str]:
    if baseline is None:
        return ["（無基線分區表快照可比對）"]
    diffs: list[str] = []
    for role in sorted(set(baseline) | set(current)):
        b, c = baseline.get(role, []), current.get(role, [])
        if b != c:
            added = sorted(set(c) - set(b))
            removed = sorted(set(b) - set(c))
            detail = []
            if added:
                detail.append(f"新增 {added}")
            if removed:
                detail.append(f"移除 {removed}")
            diffs.append(f"{role}：{'；'.join(detail)}")
    return diffs


# ------------------------------------------------------------------
# 每輪主流程
# ------------------------------------------------------------------

def round_summary(accuracy: dict, error_types: dict) -> dict:
    overall = accuracy["overall"]
    denom = overall["total"] - overall["excluded"]
    per_role = accuracy["per_role"]

    def role_pct(role: str) -> tuple[int, int]:
        b = per_role[role]
        return b["correct"], b["total"] - b["excluded"]

    floor_c, floor_d = role_pct("floor")
    ceiling_c, ceiling_d = role_pct("ceiling")
    wall_c, wall_d = role_pct("wall")
    return {
        "overall_correct": overall["correct"], "overall_denom": denom,
        "floor_correct": floor_c, "floor_denom": floor_d,
        "ceiling_correct": ceiling_c, "ceiling_denom": ceiling_d,
        "wall_correct": wall_c, "wall_denom": wall_d,
        "in_set_errors": len(error_types["in_set_errors"]),
        "non_proxy_correct": accuracy["non_proxy_stats"]["correct"],
        "non_proxy_total": accuracy["non_proxy_stats"]["total"],
        "proxy_correct": accuracy["proxy_stats"]["correct"],
        "proxy_total": accuracy["proxy_stats"]["total"],
    }


def build_round_tables_text(accuracy: dict, error_types: dict, sensitivity_per_role: dict | None) -> str:
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

    if sensitivity_per_role is not None:
        parts.append(build_sensitivity_per_role_text(sensitivity_per_role, t36.THRESHOLD))

    return "\n".join(parts) + "\n"


def build_round_md(
    *, round_label: str, parent: str, status: str, hypothesis: str, command: str,
    current_prompts_snapshot: dict, current_partition_snapshot: dict,
    partition_diffs: list[str], summary: dict, per_source: dict, fingerprint: dict,
) -> str:
    lines: list[str] = []
    lines.append(f"# Round `{round_label}` — T-44 role-aware 分區輪紀錄\n")
    lines.append(f"- status: {status}")
    lines.append(f"- 父輪次: {parent}")
    lines.append(f"- 執行指令: `{command}`")
    lines.append(f"- 本輪假設與修改理由: {hypothesis}")
    lines.append("")
    lines.append("## ROLE_MATERIAL_CANDIDATES 分區表快照\n")
    lines.append("```json")
    lines.append(json.dumps(current_partition_snapshot, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append(f"## 相對 round15_role_partition（本卡首輪）的分區表差異\n")
    if partition_diffs:
        lines.extend(f"- {d}" for d in partition_diffs)
    else:
        lines.append("（無差異）")
    lines.append("")
    lines.append("## CLIP_MATERIAL_PROMPTS 字串（本卡不動，附快照供核對）\n")
    lines.append("```json")
    lines.append(json.dumps(current_prompts_snapshot, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    lines.append("## 正確率數字\n")
    lines.append(_md_table(
        ["指標", "數值"],
        [
            ["overall", f"{summary['overall_correct']}/{summary['overall_denom']}"],
            ["floor", f"{summary['floor_correct']}/{summary['floor_denom']}"],
            ["ceiling", f"{summary['ceiling_correct']}/{summary['ceiling_denom']}"],
            ["wall", f"{summary['wall_correct']}/{summary['wall_denom']}"],
            ["in-set 誤判", str(summary["in_set_errors"])],
            ["非 proxy 正確率", f"{summary['non_proxy_correct']}/{summary['non_proxy_total']}"],
            ["proxy 正確率", f"{summary['proxy_correct']}/{summary['proxy_total']}"],
        ],
    ))
    lines.append("")
    lines.append("## 對照比較基線 round11_remap_baseline（overall 30/76、floor 4/13、"
                  "ceiling 3/11、wall 23/52、非 proxy 30/63、in-set 誤判 9）\n")
    lines.append(
        f"overall {summary['overall_correct']}/{summary['overall_denom']} "
        f"（{'上升' if summary['overall_correct'] > 30 else ('持平' if summary['overall_correct'] == 30 else '下降')} "
        f"相對 30）；floor {summary['floor_correct']}/{summary['floor_denom']} "
        f"（{'上升' if summary['floor_correct'] > 4 else ('持平' if summary['floor_correct'] == 4 else '下降')} "
        f"相對 4）；in-set 誤判 {summary['in_set_errors']} "
        f"（{'上升' if summary['in_set_errors'] > 9 else ('持平' if summary['in_set_errors'] == 9 else '下降')} "
        f"相對 9）。"
    )
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
    round_label: str, *, force_fresh: bool, parent: str, hypothesis: str, command: str,
    run_role_sensitivity: bool,
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
    print(f"=== role-aware 模式 round={round_label}：逐面判定明細（跑或讀快取） ===")
    for item in t36.GATE_ITEMS:
        name = item["name"]
        payload = run_or_load_role_aware(
            item, runs_dir=runs_dir, force_fresh=force_fresh,
            eval_mode=f"t44_role_aware:{round_label}",
        )
        all_data[name] = payload
        print(f"✓ {name}（{'equirect' if payload['is_equirect'] else 'perspective'}）")

    accuracy = build_accuracy_tables(t36.GATE_ITEMS, all_data, gt_photos)
    error_types = build_error_type_tables(t36.GATE_ITEMS, all_data, gt_photos, t36.OOD_PREFIX)
    sensitivity_per_role = (
        build_threshold_sensitivity_per_role(t36.GATE_ITEMS, all_data, gt_photos, t36.OOD_PREFIX, t36.THRESHOLD)
        if run_role_sensitivity else None
    )

    tables_text = build_round_tables_text(accuracy, error_types, sensitivity_per_role)
    summary = round_summary(accuracy, error_types)

    current_prompts_snapshot = t38.snapshot_prompts()
    current_partition_snapshot = snapshot_partition()
    # 分區表快照存在專屬的 partition_snapshot.json（t38.load_baseline_snapshot
    # 讀的是 prompts_snapshot.json，格式不同，不能直接借用）。
    first_round_partition = (
        load_partition_snapshot("round15_role_partition")
        if round_label != "round15_role_partition" else None
    )
    partition_diffs = (
        [] if round_label == "round15_role_partition"
        else diff_partition_snapshots(first_round_partition, current_partition_snapshot)
    )

    fingerprint = t38.collect_round_fingerprint(runs_dir, t36.GATE_ITEMS)
    round_md_text = build_round_md(
        round_label=round_label, parent=parent, status="complete", hypothesis=hypothesis,
        command=command, current_prompts_snapshot=current_prompts_snapshot,
        current_partition_snapshot=current_partition_snapshot, partition_diffs=partition_diffs,
        summary=summary, per_source=accuracy["per_source"], fingerprint=fingerprint,
    )

    t38.publish_round_artifacts(
        round_dir, tables_text=tables_text, round_md_text=round_md_text,
        snapshot=current_prompts_snapshot, summary=summary,
    )
    # 額外發布分區表快照（t38 的 publish_round_artifacts 不知道這個新檔案）
    t38._atomic_write_text(
        round_dir / "partition_snapshot.json",
        json.dumps(current_partition_snapshot, ensure_ascii=False, indent=2) + "\n",
    )

    print(
        f"\nround={round_label} 完成：overall {_pct(summary['overall_correct'], summary['overall_denom'])}、"
        f"floor {_pct(summary['floor_correct'], summary['floor_denom'])}、"
        f"ceiling {_pct(summary['ceiling_correct'], summary['ceiling_denom'])}、"
        f"wall {_pct(summary['wall_correct'], summary['wall_denom'])}、"
        f"in-set 誤判 {summary['in_set_errors']} 面。"
    )
    return {
        "accuracy": accuracy, "error_types": error_types, "sensitivity_per_role": sensitivity_per_role,
        "all_data": all_data, "summary": summary,
    }


def load_partition_snapshot(round_label: str) -> dict | None:
    path = TREATMENT_ROOT / "rounds" / round_label / "partition_snapshot.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    argv = sys.argv[1:]
    force_fresh = "--fresh" in argv
    run_sensitivity = "--role-sensitivity" in argv
    hypothesis: str | None = None
    parent: str | None = None
    positional: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--fresh", "--role-sensitivity"):
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
            "用法：python scripts/t44_role_eval.py <round_label> [--fresh] "
            "[--role-sensitivity] --hypothesis \"...\" [--parent <round_label>]"
        )
        return 1
    round_label = positional[0]

    if round_label == "round15_role_partition":
        if hypothesis is None:
            hypothesis = (
                "T-44 首輪：對 round11_remap_baseline 套用 PLAN_T44.md §1 的 role-aware "
                "分區表（floor/ceiling/wall 各自候選子集，OOD 三角色皆保留），"
                "字串與門檻不動"
            )
        if parent is None:
            parent = BASELINE_LABEL
    else:
        if hypothesis is None:
            print("🔴 卡關：非首輪必須用 --hypothesis \"...\" 提供本輪假設與修改理由，不得留空。")
            return 1
        if parent is None:
            parent = "round15_role_partition"

    command = "python scripts/t44_role_eval.py " + " ".join(argv)
    run_round(
        round_label, force_fresh=force_fresh, parent=parent, hypothesis=hypothesis,
        command=command, run_role_sensitivity=run_sensitivity,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
