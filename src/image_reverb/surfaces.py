"""T-12：表面辨識 —— 兩階段（ADE20K 分割取幾何角色 → CLIP zero-shot 判材質）。

**為什麼要兩階段**（T-06 實證，見 `output/seg/REPORT.md` §2.3、§4）：
ADE20K 的 `floor`／`wall` 類別語意在本專案**不可信**——滿鋪地毯的飯店走廊只有
29.6% 的像素被判成 `rug`，70.4% 判成 `floor`；換算吸音係數是 0.207，正確值應是 0.65，
高頻吸音只剩 32%。而且模型對失敗毫無自覺，一律輸出高信心結果。

所以分工是：
  第一階段 ADE20K → **只回答「這塊像素是地板／天花板／牆」這個幾何角色**
  第二階段 CLIP  → **回答「這塊表面是什麼材質」**（候選標籤＝materials.json 的 12 種材質）

曾經有一段「語意可信類別」（mirror、windowpane、curtain 等 REPORT §4 的 🟢 級）
計分邏輯，想在角色 mask 內統計這些類別佔比、額外加註提示。已依裁決 T-24-A 移除：
ADE20K 每個像素只有一個 label，可信類別的 id（windowpane/curtain/sofa 等）
與六個幾何角色（floor/ceiling/wall）的 id **在構造上互不相交**，
所以「這個角色 mask 內有多少像素屬於可信類別」在任何輸入下都恆為零——
這不是還沒做，是問法本身就問不到東西，留著只會誤導讀者以為它有作用。
這些類別真正該問的問題是「這個房間裡還有多少額外吸音」，屬於 T-27 的設計範圍
（家具／織品的等效吸音面積或 occupancy 表示），不是本模組的面材質判定
（REPORT §2.6 缺陷 D，裁決 T-24-A）。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from . import config
from .materials import SURFACE_NAMES, SurfaceMaterials, load_materials

# ------------------------------------------------------------
# 第一階段：ADE20K 類別 → 幾何角色（只取角色，不取材質語意）
# ------------------------------------------------------------
# ADE20K class id（nvidia/segformer-b4-finetuned-ade-512-512 的 id2label）
ADE_FLOOR_IDS = {3: "floor", 28: "rug", 13: "earth", 46: "sand", 53: "path", 6: "road"}
ADE_CEILING_IDS = {5: "ceiling"}
ADE_WALL_IDS = {0: "wall", 1: "building", 25: "house"}

# 曾有一張「語意可信類別」（mirror/windowpane/curtain 等）id → 材質的映射表，
# 已依裁決 T-24-A 移除——這些 id 與上面三個角色 id 集合互不相交，在角色 mask 內
# 恆量不到任何像素，是不可達死碼。清單與結構性理由已搬到 T-27（見 module docstring）。

# 封閉空間不該出現的類別 → 觸發「模型在猜」全圖警示（T-06 防呆規則）
ADE_OUTDOOR_IDS = {2: "sky"}

# 門（T-11 的尺度校驗要用，這裡順手一起輸出，避免兩張卡各跑一次分割）
ADE_DOOR_IDS = {14: "door", 58: "screen door"}

# ------------------------------------------------------------
# 第二階段：CLIP zero-shot 的候選標籤
# 每個材質給一句英文描述（zero-shot 對描述句比對單詞敏感）
# ------------------------------------------------------------
CLIP_MATERIAL_PROMPTS = {
    "concrete": "a smooth poured concrete surface",
    "brick": "a bare unglazed brick surface",
    "wood_panel": "a wooden panel or wood plank surface",
    "gypsum_board": "a painted plasterboard drywall surface",
    "glass": "a pane of clear glass or a window",
    "marble": "a polished marble or ceramic tile surface",
    "carpet": "a thick carpet or textile floor covering",
    "curtain_fabric": "a heavy fabric curtain or drape",
    "acoustic_panel": "a fibrous acoustic absorption panel",
    "audience_seating": "rows of upholstered seats with an audience",
    "grass_soil": "natural grass or bare soil ground",
    "generic_wall": "a plain smooth plastered wall",
}
# T-39（裁決 T-38B-A 開卡，output/clip_treatment/PLAN_T39.md／REPORT_T39.md）
# 試過新增 vinyl_panel／rubber_flooring／metal_roof_deck 三個候選（round12～14），
# 對 round11_remap_baseline 未同時滿足產品採用門檻（overall 24/76 < 30/76、
# 非 proxy 正確率 24/63 < 30/63，round14 最終輪），已還原、不採用。
# `data/materials.json` 仍保留這三種材質的資料（有出處，供 --override-material
# 手動指定使用），只是這裡不把它們排進 CLIP 候選集。

# T-44（裁決 T-38B-A 執行卡，output/clip_treatment/PLAN_T44.md）：
# role-aware 候選子集——每個幾何角色只在自己的候選子集裡挑，不共用全域 12 條。
# 單一事實來源：下面這個表；PLAN_T44.md §1 是它的設計文件與逐條排除理由，
# 不要各自維護一份。子集內容＝該角色在 data/material_ground_truth.json
# （T-39 重對映後）實際出現過的材質，排除的材質從未是該角色的 ground truth
# （完整性檢查見 scripts/test_t44_role_partition.py）。
# 提示詞字串本身不動——這裡只決定「哪些候選參賽」，不動「怎麼描述」。
ROLE_MATERIAL_CANDIDATES: dict[str, list[str]] = {
    # round17（PLAN_T44.md §8）：round16 加回 generic_wall 的假設證偽——它沒有
    # 只「稀釋」carpet，而是自己信心夠高直接接管成新的錯誤冠軍
    # （bathroom_tiled.floor 仍錯，且反過來讓 round15 唯一命中的
    # stairwell_tiled.floor 倒退）。generic_wall 從未是任何一面地板的 ground
    # truth，撤銷這個候選，floor 還原成 round15 的 6 種（round16 唯一改動的
    # 撤銷，其餘維持不動）。
    "floor": ["concrete", "carpet", "wood_panel", "gypsum_board", "marble", "audience_seating"],
    "ceiling": ["concrete", "curtain_fabric", "generic_wall", "gypsum_board"],
    # round16（PLAN_T44.md §7）：round15 首輪實測 wall 角色零修正、三倒退
    # （SteinmanHall 三面牆被 acoustic_panel／curtain_fabric 搶答，兩者依
    # 完整性鐵則本來就不能排除，本卡對 wall 找不到合法的正面槓桿）。還原成
    # 全域 12 種候選（等同 wall 角色暫不 role-aware），不影響 floor／ceiling。
    "wall": [
        "concrete", "brick", "wood_panel", "gypsum_board", "glass", "marble",
        "carpet", "curtain_fabric", "acoustic_panel", "audience_seating",
        "grass_soil", "generic_wall",
    ],
}

# 「以上皆非」的域外候選（out-of-domain）。
#
# 為什麼需要這個：CLIP 的 softmax 是在**封閉候選集**上做的，機率永遠加總為 1，
# 所以它無法表達「這根本不是建築表面」——只會把機率分給最像的那個材質。
# 實測（2026-08-18）：車內照片在只有 12 個材質候選時，floor 判成 curtain_fabric
# 信心 0.760、wall 判成 acoustic_panel 信心 0.489，**兩者都在 0.4 門檻之上，
# 完全不會觸發警示**——正是 HANDOFF §2 洞二「模型對失敗毫無自覺」的重演。
# 單純調高門檻無效：要擋住車內的 0.760 得把門檻設到 0.8，那會連
# corridor 天花板（0.599）這種判對的案例一起擋掉，模組就沒用了。
#
# 加入域外候選後，softmax 才有地方可以「投給以上皆非」。
# top-1 落在這裡 → fallback ＋ 明確警示，不假裝量到了材質。
CLIP_OOD_PROMPTS = {
    "__vehicle_interior": "the inside of a car or vehicle cabin",
    "__outdoor_scene": "an outdoor landscape with sky and trees",
    "__object_closeup": "a close-up photograph of a small object",
    "__person": "a photograph of a person's face or body",
}
OOD_PREFIX = "__"

# equirect 的六視角 → ShoeBox 六個面。用得上 T-10 投影出來的方位資訊：
# 方位角 0/90/180/270 對到四面牆，仰角 ±45 對到天花板/地板。
VIEW_TO_SURFACE = {
    "az000_el00": "north",
    "az090_el00": "east",
    "az180_el00": "south",
    "az270_el00": "west",
    "el+45": "ceiling",
    "el-45": "floor",
}


@dataclass
class SurfaceObservation:
    """一個幾何角色區域的觀測結果。"""

    role: str                  # "floor" / "ceiling" / "wall"
    pixel_ratio: float         # 佔整張圖的像素比例
    material_id: str           # 二階分類的結果（或 fallback）
    confidence: float          # CLIP top-1 機率（fallback / out_of_domain 記該次 top-1）
    method: str                # "clip" / "fallback" / "out_of_domain"
    top3: list[tuple[str, float]] = field(default_factory=list)
    note: str = ""


def _load_segmenter():
    """載入 ADE20K 分割模型（沿用 T-06 的模型）。"""
    from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor

    processor = SegformerImageProcessor.from_pretrained(config.SEGMENTATION_MODEL_ID)
    model = SegformerForSemanticSegmentation.from_pretrained(config.SEGMENTATION_MODEL_ID)
    model.eval()
    return processor, model


def _load_clip():
    """載入 CLIP zero-shot 分類模型。"""
    from transformers import CLIPModel, CLIPProcessor

    processor = CLIPProcessor.from_pretrained(config.CLIP_MODEL_ID)
    model = CLIPModel.from_pretrained(config.CLIP_MODEL_ID)
    model.eval()
    return processor, model


def segment_roles(img: Image.Image, processor, model) -> tuple[np.ndarray, dict[int, float]]:
    """跑 ADE20K 分割，回傳 (labelmap, {class_id: 像素比例})。"""
    import torch
    import torch.nn.functional as F

    inputs = processor(images=img, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    # 上採樣回原圖大小再取 argmax（先 argmax 再放大會產生鋸齒假邊界）
    logits = F.interpolate(logits, size=img.size[::-1], mode="bilinear", align_corners=False)
    labelmap = logits.argmax(dim=1)[0].cpu().numpy().astype(np.int32)

    total = labelmap.size
    ids, counts = np.unique(labelmap, return_counts=True)
    ratios = {int(i): float(c) / total for i, c in zip(ids, counts)}
    return labelmap, ratios


def classify_region_material(
    img: Image.Image,
    mask: np.ndarray,
    clip_processor,
    clip_model,
    threshold: float = config.CLIP_CONFIDENCE_THRESHOLD,
    role: str | None = None,
) -> tuple[str, float, list[tuple[str, float]], str]:
    """對一個表面區域跑 CLIP zero-shot，回傳 (材質 id, 信心, top3, 方法)。

    信心 gating：top-1 機率低於 threshold → fallback `config.DEFAULT_WALL_MATERIAL`
    （現行值 `gypsum_board`，單一事實來源是 data/materials.json 的 fallback_id，
    見 T-23），呼叫端要把警示寫進輸出 JSON（不能安靜地當成量到的結果）。

    `role`（T-44）：`None`（預設，向後相容）＝候選集為全域 12 種材質，與
    T-44 之前逐位元相同；給 `"floor"`／`"ceiling"`／`"wall"` 時，候選集收窄成
    `ROLE_MATERIAL_CANDIDATES[role]`（單一事實來源），域外候選
    `CLIP_OOD_PROMPTS` 三個角色都保留，不收窄。
    """
    import torch

    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return config.DEFAULT_WALL_MATERIAL, 0.0, [], "fallback"

    # 取遮罩的 bounding box 裁切，並把遮罩外的像素塗成中性灰，
    # 避免 CLIP 看到隔壁表面的內容（例如判牆面時被地板干擾）
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    arr = np.asarray(img.convert("RGB")).copy()
    arr[~mask] = 128
    crop = Image.fromarray(arr[y0:y1, x0:x1])

    # 候選集＝材質 ＋ 域外選項，讓 softmax 有辦法表達「以上皆非」。
    # role=None：全域 12 種（T-44 之前唯一行為，逐位元相同的路徑）。
    # role=給定角色：只有該角色的候選子集（T-44，ROLE_MATERIAL_CANDIDATES）。
    if role is None:
        material_prompts = CLIP_MATERIAL_PROMPTS
    else:
        material_prompts = {mid: CLIP_MATERIAL_PROMPTS[mid] for mid in ROLE_MATERIAL_CANDIDATES[role]}
    all_prompts = {**material_prompts, **CLIP_OOD_PROMPTS}
    ids = list(all_prompts.keys())
    prompts = [all_prompts[i] for i in ids]
    inputs = clip_processor(text=prompts, images=crop, return_tensors="pt", padding=True)
    with torch.no_grad():
        out = clip_model(**inputs)
    probs = out.logits_per_image.softmax(dim=1)[0].cpu().numpy()

    order = np.argsort(probs)[::-1]
    top3 = [(ids[i], float(probs[i])) for i in order[:3]]
    best_id, best_p = top3[0]

    # top-1 落在域外候選 → 模型認不出這是建築表面，不能給材質數字
    if best_id.startswith(OOD_PREFIX):
        return config.DEFAULT_WALL_MATERIAL, best_p, top3, "out_of_domain"

    if best_p < threshold:
        return config.DEFAULT_WALL_MATERIAL, best_p, top3, "fallback"
    return best_id, best_p, top3, "clip"


def analyse_image(
    img: Image.Image,
    seg=None,
    clip=None,
    threshold: float = config.CLIP_CONFIDENCE_THRESHOLD,
    role_aware: bool = False,
) -> dict[str, Any]:
    """對單張透視圖跑兩階段辨識，回傳各幾何角色的觀測結果與警示。

    `role_aware`（T-44，預設 `False`＝向後相容）：`False` 時對
    `classify_region_material()` 的呼叫**字面上**與 T-44 之前相同（不帶
    `role` 關鍵字），不是傳 `role=None` 才達成等價；`True` 時才多帶
    `role=role`（迴圈變數，即 `"floor"`／`"ceiling"`／`"wall"`）。
    """
    seg_processor, seg_model = seg if seg is not None else _load_segmenter()
    clip_processor, clip_model = clip if clip is not None else _load_clip()

    labelmap, ratios = segment_roles(img, seg_processor, seg_model)
    warnings: list[str] = []

    # T-06 防呆規則：封閉空間出現 sky → 模型在猜
    for cid, name in ADE_OUTDOOR_IDS.items():
        r = ratios.get(cid, 0.0)
        if r > 0.01:
            warnings.append(
                f"分割結果有 {r*100:.1f}% 的像素被判成 '{name}'（室外類別）。"
                f"若這是室內空間，代表模型在猜，整張圖的材質判定都要打折看待（T-06 防呆規則）。"
            )

    observations: dict[str, SurfaceObservation] = {}
    role_ids = {"floor": ADE_FLOOR_IDS, "ceiling": ADE_CEILING_IDS, "wall": ADE_WALL_IDS}

    for role, id_map in role_ids.items():
        mask = np.isin(labelmap, list(id_map.keys()))
        ratio = float(mask.mean())
        if ratio < config.MIN_SURFACE_AREA_RATIO:
            # 區域太小就不判，免得拿一小撮雜點決定整面牆的材質
            continue

        if role_aware:
            mid, conf, top3, method = classify_region_material(
                img, mask, clip_processor, clip_model, threshold, role=role
            )
        else:
            mid, conf, top3, method = classify_region_material(
                img, mask, clip_processor, clip_model, threshold
            )
        note = ""
        if method == "out_of_domain":
            ood_name = top3[0][0].lstrip(OOD_PREFIX)
            note = (
                f"CLIP 認為這塊區域最像「{ood_name}」（機率 {conf:.2f}）而非任何建築材質——"
                f"模型認不出這是建築表面，改用 fallback '{config.DEFAULT_WALL_MATERIAL}'。"
                f"這個空間的材質判定不可信，請人工用 --materials 覆寫。"
            )
            warnings.append(f"{role}：{note}")
        elif method == "fallback":
            note = (
                f"CLIP top-1 機率 {conf:.2f} 低於門檻 {threshold}，"
                f"改用 fallback '{config.DEFAULT_WALL_MATERIAL}'"
            )
            warnings.append(f"{role}：{note}")

        observations[role] = SurfaceObservation(
            role=role, pixel_ratio=ratio, material_id=mid,
            confidence=conf, method=method, top3=top3, note=note,
        )

    door_ratio = sum(ratios.get(cid, 0.0) for cid in ADE_DOOR_IDS)

    return {
        "observations": observations,
        "warnings": warnings,
        "class_ratios": ratios,
        "door_pixel_ratio": door_ratio,
        "labelmap": labelmap,
    }


def surfaces_from_preprocess(
    preprocess_summary: dict[str, Any],
    threshold: float = config.CLIP_CONFIDENCE_THRESHOLD,
    role_aware: bool = False,
) -> tuple[SurfaceMaterials, dict[str, Any]]:
    """吃 T-10 `preprocess_image()` 的輸出，產生逐表面材質（約束 A）。

    - **環景**：T-10 已投影出六視角，方位資訊剛好對應 ShoeBox 六個面
      （az000→north、az090→east、az180→south、az270→west、el+45→ceiling、el-45→floor），
      所以四面牆可以**各自**判材質，不必共用一個值。
    - **一般透視照**：一張照片看不到背後的牆，四面牆只能共用同一個判定值；
      這件事會如實寫進 `sources` 與 `warnings`，不假裝有四面獨立資訊。

    `role_aware`（T-44，預設 `False`＝向後相容）：原樣往下傳給 `analyse_image()`。
    """
    data = load_materials()
    seg = _load_segmenter()
    clip = _load_clip()

    surfaces = SurfaceMaterials()
    detail: dict[str, Any] = {"mode": None, "views": {}, "warnings": [], "class_ratios": {}}

    if preprocess_summary.get("is_equirect"):
        detail["mode"] = "equirect_6views"
        for view_name, view_meta in preprocess_summary["views"].items():
            surface = VIEW_TO_SURFACE.get(view_name)
            if surface is None:
                continue
            img = Image.open(view_meta["path"]).convert("RGB")
            res = analyse_image(img, seg, clip, threshold, role_aware=role_aware)
            detail["warnings"].extend(f"[{view_name}] {w}" for w in res["warnings"])
            detail["class_ratios"][view_name] = res["class_ratios"]

            # 這個視角對應的面，優先採用同角色的觀測；沒有就退回牆面觀測
            role = "floor" if surface == "floor" else ("ceiling" if surface == "ceiling" else "wall")
            obs = res["observations"].get(role) or res["observations"].get("wall")
            if obs is None:
                detail["warnings"].append(
                    f"[{view_name}] 沒有偵測到足夠大的 {role} 區域，{surface} 面保持預設材質"
                )
                continue
            surfaces.set_surface(surface, obs.material_id, source=obs.method)
            detail["views"][view_name] = {
                "surface": surface, "role": obs.role, "material_id": obs.material_id,
                "confidence": round(obs.confidence, 4), "method": obs.method,
                "pixel_ratio": round(obs.pixel_ratio, 4),
                "top3": [(m, round(p, 4)) for m, p in obs.top3],
                "note": obs.note,
            }
    else:
        detail["mode"] = "single_perspective"
        img = Image.open(preprocess_summary["cropped"]).convert("RGB")
        res = analyse_image(img, seg, clip, threshold, role_aware=role_aware)
        detail["warnings"].extend(res["warnings"])
        detail["class_ratios"]["single"] = res["class_ratios"]

        for role, obs in res["observations"].items():
            if role == "wall":
                surfaces.set_walls(obs.material_id, source=obs.method)
            else:
                surfaces.set_surface(role, obs.material_id, source=obs.method)
            detail["views"].setdefault("single", {})[role] = {
                "material_id": obs.material_id, "confidence": round(obs.confidence, 4),
                "method": obs.method, "pixel_ratio": round(obs.pixel_ratio, 4),
                "top3": [(m, round(p, 4)) for m, p in obs.top3], "note": obs.note,
            }
        if "wall" in res["observations"]:
            detail["warnings"].append(
                "單張透視照看不到背後的牆，四面牆共用同一個材質判定值。"
                "若要四面各自判定，請用 360° 環景照片（T-10 會投影出六視角）。"
            )
        detail["door_pixel_ratio"] = res["door_pixel_ratio"]

    surfaces.warnings.extend(detail["warnings"])
    surfaces.validate(data)

    if surfaces.is_uniform():
        surfaces.warnings.append(
            "六個面被判成同一種材質——這是約束 A 要避免的退化情況，請人工檢查／用 --materials 覆寫。"
        )

    return surfaces, detail


def compute_materials_confidence(surfaces: SurfaceMaterials) -> str:
    """依六面材質的來源與是否退化，判定「材質」這一軸的信心（T-25，REPORT §2.5 缺陷 B）。

    這是跟 `RoomEstimate.confidence`（幾何信心）**分開**的一軸——舊行為把
    分析輸出的 `confidence` 直接設成幾何信心，材質是不是用猜的完全沒有訊號透出去，
    T-17 §7-1 的臥室因此被標成 `medium`，但地板其實是 fallback（沒判到）。

    規則（🔮 Opus 裁決 T-25，順序不可調換，由上而下第一個命中的就是結果）：
      1. 六面中**任一面**的 `sources[name]` 是 `"fallback"` 或 `"out_of_domain"`
         → `low`（CLIP 對這面沒把握，或這根本不是建築表面，是用猜的）
      2. 六面材質**全部相同**（`is_uniform()`，約束 A 要避免的退化情況）→ `low`
      3. 六面皆 `"clip"`（每一面都是模型自己判出來的）**且**沒有任何
         `surfaces.warnings` → `high`
      4. 其餘情況 → `medium`

    只讀 `sources` / `warnings` / 六面材質 id，不碰任何聲學數值——本卡「只動
    metadata，不得改變任何 IR 內容」。
    """
    face_sources = [surfaces.sources.get(name, "") for name in SURFACE_NAMES]
    if any(s in ("fallback", "out_of_domain") for s in face_sources):
        return "low"
    if surfaces.is_uniform():
        return "low"
    if all(s == "clip" for s in face_sources) and not surfaces.warnings:
        return "high"
    return "medium"


def save_detail(detail: dict[str, Any], surfaces: SurfaceMaterials, out_path: str | Path) -> Path:
    """把辨識明細與逐表面結果存成 JSON（含 warnings，不隱藏低信心）。"""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "surfaces": surfaces.as_dict(),
        "sources": surfaces.sources,
        "warnings": surfaces.warnings,
        "detail": {k: v for k, v in detail.items() if k != "labelmap"},
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
