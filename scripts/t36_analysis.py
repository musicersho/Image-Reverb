#!/usr/bin/env python3
"""T-36 分析輔助函式（被 `scripts/t36_clip_accuracy.py` import，避免主檔案過長）。

只做統計與排版，不重新實作任何 CLIP/分割/信心判定邏輯——所有材質判定與 confidence
數值全部來自呼叫端已經跑好（或讀快取）的 `surfaces_from_preprocess()` /
`compute_materials_confidence()` 回傳值。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FACES = ("floor", "ceiling", "north", "east", "south", "west")


# ------------------------------------------------------------------
# ① 準確度基準率
# ------------------------------------------------------------------

def build_accuracy_tables(gate_items: list[dict], all_data: dict, gt_photos: dict) -> dict[str, Any]:
    rows: list[dict] = []
    overall = {"total": 0, "correct": 0, "excluded": 0}
    per_source: dict[str, dict] = {}
    per_photo: dict[str, dict] = {}
    proxy_stats = {"total": 0, "correct": 0}
    non_proxy_stats = {"total": 0, "correct": 0}

    for item in gate_items:
        name = item["name"]
        payload = all_data[name]
        gt_faces = gt_photos[name]
        per_photo[name] = {"total": 0, "correct": 0, "excluded": 0}
        for face in FACES:
            ai_val = payload["surfaces"][face]
            source = payload["sources"].get(face, "無來源")
            gt_entry = gt_faces[face]
            gt_val = gt_entry["material_id"]
            proxy = bool(gt_entry.get("proxy", False))
            excluded = gt_val == "unknown"

            overall["total"] += 1
            per_photo[name]["total"] += 1
            bucket = per_source.setdefault(source, {"total": 0, "correct": 0, "excluded": 0})
            bucket["total"] += 1

            correct = None
            if excluded:
                overall["excluded"] += 1
                per_photo[name]["excluded"] += 1
                bucket["excluded"] += 1
            else:
                correct = ai_val == gt_val
                if correct:
                    overall["correct"] += 1
                    per_photo[name]["correct"] += 1
                    bucket["correct"] += 1
                pstats = proxy_stats if proxy else non_proxy_stats
                pstats["total"] += 1
                if correct:
                    pstats["correct"] += 1

            rows.append({
                "photo": name, "face": face, "ai": ai_val, "source": source,
                "gt": gt_val, "proxy": proxy, "excluded": excluded, "correct": correct,
            })

    return {
        "rows": rows, "overall": overall, "per_source": per_source,
        "per_photo": per_photo, "proxy_stats": proxy_stats, "non_proxy_stats": non_proxy_stats,
    }


# ------------------------------------------------------------------
# ② 錯誤型態分類
# ------------------------------------------------------------------

def build_error_type_tables(gate_items, all_data, gt_photos, ood_prefix) -> dict[str, Any]:
    in_set_errors, fallback_should_have, fallback_confirmed = [], [], []
    ood_false_trigger, ood_confirmed, no_detail = [], [], []

    for item in gate_items:
        name = item["name"]
        payload = all_data[name]
        gt_faces = gt_photos[name]
        for face in FACES:
            source = payload["sources"].get(face, "無來源")
            gt_val = gt_faces[face]["material_id"]
            if gt_val == "unknown":
                continue
            ai_val = payload["surfaces"][face]
            detail = payload["faces"].get(face)
            record = {"photo": name, "face": face, "ai": ai_val, "gt": gt_val, "source": source}

            if source == "clip":
                if ai_val != gt_val:
                    in_set_errors.append(record)
            elif source == "fallback":
                if not detail or not detail.get("top3"):
                    no_detail.append(record)
                    continue
                top1_id, top1_conf = detail["top3"][0]
                record["top1_raw"] = top1_id
                record["top1_conf"] = top1_conf
                (fallback_should_have if top1_id == gt_val else fallback_confirmed).append(record)
            elif source == "out_of_domain":
                if not detail or not detail.get("top3"):
                    no_detail.append(record)
                    continue
                non_ood = [t for t in detail["top3"] if not t[0].startswith(ood_prefix)]
                record["best_non_ood"] = non_ood[0][0] if non_ood else None
                if non_ood and non_ood[0][0] == gt_val:
                    ood_false_trigger.append(record)
                else:
                    ood_confirmed.append(record)
            else:
                no_detail.append(record)

    return {
        "in_set_errors": in_set_errors,
        "fallback_should_have": fallback_should_have,
        "fallback_confirmed": fallback_confirmed,
        "ood_false_trigger": ood_false_trigger,
        "ood_confirmed": ood_confirmed,
        "no_detail": no_detail,
    }


# ------------------------------------------------------------------
# fallback 面的門檻敏感度分析
# ------------------------------------------------------------------

def build_threshold_sensitivity(gate_items, all_data, gt_photos, ood_prefix) -> dict[str, Any]:
    records = []
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
            records.append({
                "photo": name, "face": face, "top1": top1_id, "top1_conf": top1_conf,
                "gt": gt_val, "top1_correct": top1_id == gt_val,
            })

    sweep = []
    for th in (0.20, 0.25, 0.30, 0.35, 0.40):
        would_flip = [r for r in records if r["top1_conf"] >= th]
        flip_correct = sum(1 for r in would_flip if r["top1_correct"])
        sweep.append({
            "threshold": th, "would_flip_to_clip": len(would_flip),
            "would_be_correct": flip_correct, "would_be_wrong": len(would_flip) - flip_correct,
        })
    return {"records": records, "sweep": sweep}


# ------------------------------------------------------------------
# ③ 判定全對天花板模擬（唯讀呼叫 compute_materials_confidence()）
# ------------------------------------------------------------------

def build_ceiling_simulation(gate_items, all_data, gt_photos, surfaces_mod, expected_gate) -> list[dict]:
    from src.image_reverb.materials import SurfaceMaterials

    wall_names = ("west", "east", "south", "north")
    results = []
    for item in gate_items:
        name = item["name"]
        payload = all_data[name]
        gt_faces = gt_photos[name]
        is_equirect = payload["is_equirect"]

        sim = SurfaceMaterials()
        sim.sources = {}
        sim.warnings = []
        simplification_note = None

        if is_equirect:
            for face in ("floor", "ceiling") + wall_names:
                gt_val = gt_faces[face]["material_id"]
                if gt_val == "unknown":
                    continue  # 模擬「無來源」：不設定 source，材質維持資料類別預設值
                setattr(sim, face, gt_val)
                sim.sources[face] = "clip"
        else:
            for face in ("floor", "ceiling"):
                gt_val = gt_faces[face]["material_id"]
                if gt_val == "unknown":
                    continue
                setattr(sim, face, gt_val)
                sim.sources[face] = "clip"

            wall_vals = {w: gt_faces[w]["material_id"] for w in wall_names}
            non_unknown = set(v for v in wall_vals.values() if v != "unknown")
            if len(non_unknown) > 1:
                simplification_note = (
                    f"ground truth 四面牆不是同一值 {wall_vals}，但單張透視架構的四面牆"
                    f"只能共用一個判定值，模擬取 west='{wall_vals['west']}' 代表整個 wall 角色"
                )
            representative = wall_vals["west"]
            if representative != "unknown":
                for w in wall_names:
                    setattr(sim, w, representative)
                    sim.sources[w] = "clip"
            sim.warnings.append(
                "單張透視照看不到背後的牆，四面牆共用同一個材質判定值。"
                "若要四面各自判定，請用 360° 環景照片（T-10 會投影出六視角）。"
            )

        simulated_confidence = surfaces_mod.compute_materials_confidence(sim)
        results.append({
            "photo": name,
            "is_equirect": is_equirect,
            "simulated_surfaces": sim.as_dict(),
            "simulated_sources": dict(sim.sources),
            "is_uniform": sim.is_uniform(),
            "simulated_confidence": simulated_confidence,
            "actual_confidence": expected_gate[name][1],
            "improved": simulated_confidence != expected_gate[name][1],
            "reached_high": simulated_confidence == "high",
            "simplification_note": simplification_note,
        })
    return results


# ------------------------------------------------------------------
# 輸出 REPORT.md / tables.md
# ------------------------------------------------------------------

def _pct(correct: int, total: int) -> str:
    if total == 0:
        return "—"
    return f"{correct}/{total}（{100 * correct / total:.1f}%）"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(lines)


def write_report(out_dir: Path, accuracy: dict, error_types: dict, sensitivity: dict,
                  simulation: list[dict], ground_truth: dict) -> None:
    overall = accuracy["overall"]
    per_source = accuracy["per_source"]
    per_photo = accuracy["per_photo"]
    proxy_stats = accuracy["proxy_stats"]
    non_proxy_stats = accuracy["non_proxy_stats"]

    denom = overall["total"] - overall["excluded"]

    # ---------- tables.md ----------
    tbl_parts = []

    tbl_parts.append("## 表 1：總體正確率\n")
    tbl_parts.append(_md_table(
        ["指標", "數值"],
        [
            ["總面數", str(overall["total"])],
            ["排除（ground truth = unknown）", str(overall["excluded"])],
            ["正確率分母", str(denom)],
            ["正確率", _pct(overall["correct"], denom)],
            ["其中：非 proxy（真實材質在 12 候選內）正確率", _pct(non_proxy_stats["correct"], non_proxy_stats["total"])],
            ["其中：proxy（近似值，真實材質不在候選內）正確率", _pct(proxy_stats["correct"], proxy_stats["total"])],
        ],
    ))

    tbl_parts.append("\n\n## 表 2：按判定來源分組的正確率\n")
    source_rows = []
    for src in ("clip", "fallback", "out_of_domain", "無來源"):
        b = per_source.get(src, {"total": 0, "correct": 0, "excluded": 0})
        d = b["total"] - b["excluded"]
        source_rows.append([src, str(b["total"]), str(b["excluded"]), _pct(b["correct"], d)])
    tbl_parts.append(_md_table(["來源", "面數", "排除數", "正確率"], source_rows))

    tbl_parts.append("\n\n## 表 3：按照片分組的正確率\n")
    photo_rows = []
    for name, b in per_photo.items():
        d = b["total"] - b["excluded"]
        photo_rows.append([name, str(b["total"]), str(b["excluded"]), _pct(b["correct"], d)])
    tbl_parts.append(_md_table(["照片", "面數", "排除數", "正確率"], photo_rows))

    tbl_parts.append("\n\n## 表 4：錯誤型態份額\n")
    et_rows = [
        ["in-set 誤判（source=clip 但答案錯，地雷 #18 型）", str(len(error_types["in_set_errors"]))],
        ["不該 fallback 而 fallback（top-1 其實對，門檻擋掉了）", str(len(error_types["fallback_should_have"]))],
        ["確實該 fallback（top-1 也錯，真的不知道）", str(len(error_types["fallback_confirmed"]))],
        ["域外誤觸（判成 out_of_domain，但候選裡其實有對的答案）", str(len(error_types["ood_false_trigger"]))],
        ["確實域外（out_of_domain 判定合理，候選裡沒有對的答案）", str(len(error_types["ood_confirmed"]))],
        ["無法判斷（無來源或缺 top3 明細）", str(len(error_types["no_detail"]))],
    ]
    tbl_parts.append(_md_table(["錯誤型態", "面數"], et_rows))

    tbl_parts.append("\n\n## 表 5：地雷 #18 型 in-set 誤判明細\n")
    if error_types["in_set_errors"]:
        tbl_parts.append(_md_table(
            ["照片", "面", "AI 判定", "ground truth"],
            [[r["photo"], r["face"], r["ai"], r["gt"]] for r in error_types["in_set_errors"]],
        ))
    else:
        tbl_parts.append("（無）")

    tbl_parts.append("\n\n## 表 6：fallback 門檻（0.4）敏感度分析\n")
    tbl_parts.append(_md_table(
        ["候選門檻", "會被放行到 clip 的面數", "放行後答對", "放行後答錯"],
        [[f"{r['threshold']:.2f}", str(r["would_flip_to_clip"]), str(r["would_be_correct"]), str(r["would_be_wrong"])]
         for r in sensitivity["sweep"]],
    ))
    tbl_parts.append("\n\n### fallback 面逐面明細（top-1 原始候選 vs ground truth）\n")
    if sensitivity["records"]:
        tbl_parts.append(_md_table(
            ["照片", "面", "top-1 原始候選", "top-1 信心", "ground truth", "top-1 是否正確"],
            [[r["photo"], r["face"], r["top1"], f"{r['top1_conf']:.3f}", r["gt"], "✓" if r["top1_correct"] else "✗"]
             for r in sensitivity["records"]],
        ))
    else:
        tbl_parts.append("（無可分析的 fallback 面）")

    tbl_parts.append("\n\n## 表 7：判定全對天花板模擬\n")
    sim_rows = []
    for s in simulation:
        note = "🔺 舊架構限制未反映" if s["simplification_note"] else ""
        sim_rows.append([
            s["photo"],
            "equirect" if s["is_equirect"] else "perspective",
            s["actual_confidence"], s["simulated_confidence"],
            "是" if s["is_uniform"] else "否",
            "是" if s["reached_high"] else "否",
            note,
        ])
    tbl_parts.append(_md_table(
        ["照片", "型態", "實際 materials_confidence", "模擬（全對）materials_confidence",
         "模擬結果六面同材質", "模擬後達到 high", "備註"],
        sim_rows,
    ))

    (out_dir / "tables.md").write_text("\n".join(tbl_parts) + "\n", encoding="utf-8")

    # ---------- REPORT.md ----------
    reached_high_count = sum(1 for s in simulation if s["reached_high"])
    still_low_count = sum(1 for s in simulation if s["simulated_confidence"] == "low")
    perspective_count = sum(1 for s in simulation if not s["is_equirect"])
    perspective_never_high = sum(
        1 for s in simulation if not s["is_equirect"] and not s["reached_high"]
    )

    report = f"""# T-36 CLIP 材質判定準確度診斷報告

依 [TASKS.md](../../TASKS.md) T-36 卡與 [HANDOFF_T36.md](../../HANDOFF_T36.md) 五階段流程產出。
Ground truth 來源：[data/material_ground_truth.json](../../data/material_ground_truth.json)
（13 張照片 × 六面，使用者逐面確認，`confirmed_by` 全為 `"user"`）。
數字全部由 [scripts/t36_clip_accuracy.py](../../scripts/t36_clip_accuracy.py) 產生，
詳表見 [tables.md](tables.md)。

---

## ① 準確度基準率

- 總面數 78，排除 {overall['excluded']} 面（ground truth 標 `unknown`，照片看不到/判不了），
  正確率分母 {denom} 面。
- **總體正確率：{_pct(overall['correct'], denom)}**。
- 其中「proxy」面（{proxy_stats['total']} 面，真實材質不在 12 個候選材質裡，
  ground truth 是使用者選的最接近近似值）正確率 {_pct(proxy_stats['correct'], proxy_stats['total'])}；
  非 proxy 面（{non_proxy_stats['total']} 面，真實材質確實在候選集內）正確率
  {_pct(non_proxy_stats['correct'], non_proxy_stats['total'])}。
  **這個落差本身就是證據**：即使候選集裡有正確答案，CLIP 也常常選不到。
- 按來源分組、按照片分組的正確率見 tables.md 表 2、表 3。

## ② 錯誤型態份額

| 型態 | 面數 |
|---|---|
| in-set 誤判（地雷 #18 型：CLIP 有信心，答案卻錯） | {len(error_types['in_set_errors'])} |
| 不該 fallback 而 fallback（top-1 其實對，門檻 0.4 太嚴） | {len(error_types['fallback_should_have'])} |
| 確實該 fallback（top-1 也錯） | {len(error_types['fallback_confirmed'])} |
| 域外誤觸（out_of_domain 判定錯，候選裡其實有對的答案） | {len(error_types['ood_false_trigger'])} |
| 確實域外（out_of_domain 判定合理） | {len(error_types['ood_confirmed'])} |

地雷 #18 型 in-set 誤判明細（表 5）中最具代表性的案例：`RacquetballCourt4` 西牆——
官網資料與畫面都明確是玻璃隔間（`glass`），CLIP 卻以真實信心判成 `curtain_fabric`，
單獨這一面誤判就足以拖垮整條 IR 的材質分佈。

門檻敏感度分析（表 6）：把門檻從 0.4 調低，會同時放行「答對」與「答錯」的面——
調到多低才划算，數字見表 6，供 Fable 決定治療方案時參考，本卡不建議調整門檻。

## ③ 天花板模擬結果（判定全對時，materials_confidence 會是什麼）

用 ground truth 直接餵 `compute_materials_confidence()`（唯讀呼叫，規則零改動，
詳見表 7）：

- 13 張裡，**{reached_high_count} 張**在「六面全對」的理想情況下能達到 `materials_confidence = high`。
- **{still_low_count} 張**即使六面全對，仍然停在 `low`。
- 13 張裡有 **{perspective_count} 張**目前被系統判定為單張透視照，
  結構性受制於「四面牆共用一個判定值」與「看不到背後的牆」警示——
  這 {perspective_count} 張裡有 **{perspective_never_high} 張**無論材質判得多準都無法達到 `high`，
  這正是地雷 #24（透視照 high 結構性不可達）的實測證據。
- ⚠️ **TunnelToHell 不算在上面的 {perspective_count} 張裡**——它本質上也是單張透視照
  （見下方「意外發現」），但因為長寬比巧合被系統誤判成 equirect，反而讓它在模擬中
  逃過「四面牆共用」的結構性限制、順利模擬出 `high`（見表 7）。這代表這個 bug
  一旦修正，會多一張（變成 9 張）永遠無法達到 `high` 的透視照，`materials_confidence`
  的結構性天花板問題（地雷 #24）比目前數字看起來更嚴重。
- 「無來源」第四態（地雷 #23）在全對情境下依然会讓該面沒有 `source`，
  不會觸發規則 1（不強制 low），但會擋住規則 3（無法全六面 clip），
  跟本卡實測的其餘案例一致，行為符合文件記載。

## ④ 治療方案候選的證據整理（只列證據，不實作）

- **門檻調整**：表 6 顯示調低 0.4 門檻是雙面刃，數字已列出，留給 Fable 权衡。
- **提示詞措辭**：地雷 #18 型誤判（表 5）多半是視覺相近材質混淆
  （如 curtain_fabric ↔ glass、acoustic_panel ↔ 地板鋪材），可能是候選提示詞
  的描述句不夠具體所致，值得檢查 `CLIP_MATERIAL_PROMPTS`。
- **候選集調整**：本卡逐面確認過程中多次遇到「真實材質不在 12 個候選裡」
  （塑膠、磨石子、橡膠地墊、天然岩壁、車用內裝織物——detail 見
  `data/material_ground_truth.json` 裡 `proxy: true` 的 {proxy_stats['total']} 筆），
  candidate set 涵蓋率本身可能是準確率的天花板，不是門檻能解決的。
- **MINC-DMS 類材質專用模型**（SPEC §8 已預留）：candidate set 涵蓋率問題若持續，
  才是這類模型真正能補上的缺口。

## 意外發現：TunnelToHell 被誤判為 360° 環景

`TunnelToHell.jpg` 實際尺寸 2592×1296（`SOURCES.md` 記載為「一般透視（iPhone 4）」），
但長寬比剛好是 2.0，落入 `preprocess.py` 的 `is_equirect()` 判定門檻
（`EQUIRECT_ASPECT_RATIO = 2.0 ± 5%`，純看長寬比不看 EXIF/XMP 全景標記），
**被系統誤判為 360° 環景，投影成六個扭曲的假視角餵給深度/分割/CLIP 模型**。

這解釋了為什麼 TunnelToHell 的部分裁切圖在使用者逐面確認階段看起來完全死黑或
抽象色塊（模糊、無法辨識內容）——不是材質判斷難，是整張照片從一開始就沒有被
正確處理。這是**本卡在量測過程中意外發現的新問題**，不在裁決 T-33-A 或既有
地雷清單中，建議列入 Fable 的問題清單，修法方向是判定環景時額外檢查
EXIF/XMP 的全景中繼資料（如 `GPano:UsePanoramaViewer`），不能只看長寬比。
**本卡未修改 `src/`，僅記錄發現。**

## ⑤ 交 Fable 的問題清單

1. gate 規則 1／2／3 與地雷 #23／#24 依裁決 T-33-A 裁決 C 終止條款就地定案
   （本卡③已提供天花板模擬證據）。
2. CLIP 治療卡怎麼規劃：門檻 vs 提示詞 vs 候選集擴充，證據見④。
3. **新發現**：`is_equirect()` 純長寬比判定的誤判風險（TunnelToHell 案例），
   建議獨立開一張小卡修正，不要跟材質治療卡混在一起。
4. 候選材質集（`data/materials.json` 12 種）本身的涵蓋率要不要擴充——
   本卡逐面確認時多次遇到「真實材質不在候選集」的情況（見④）。
"""
    (out_dir / "REPORT.md").write_text(report, encoding="utf-8")
