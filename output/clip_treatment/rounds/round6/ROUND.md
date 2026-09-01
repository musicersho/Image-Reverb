# Round `round6` — T-38 治療輪紀錄（歷史補寫，T-38A 步驟 4）

> 本檔由 T-38A 補寫。round6 是「上一個視窗」在原子發布／ROUND.md 機制存在之前
> 跑到一半中止的輪次，**本輪與 round1～round5 不同：它的提示詞快照可以完整重建**
> ——中止當下，`src/image_reverb/surfaces.py` 的那一行未提交改動一直留在工作樹
> 沒被下一輪覆寫（因為沒有下一輪），sha256 與本輪快取記錄的
> `code_sha256.surfaces.py` 完全相符，是本案六輪覆寫紀錄裡**唯一一輪**留下逐字
> 提示詞證據的輪次。以下內容原文記錄自 T-38A 動工當下、尚未還原 `surfaces.py`
> 前抓到的 `git diff`。

- status: **interrupted**（**不納入任何比較**，含產品採用門檻評估與軌跡表——
  Fable 拆卡裁決第 5 點：round6 標 interrupted，不納入比較）
- 父輪次: round5（推定——逐輪覆寫的線性紀錄推定，非精確 lineage 證據）
- 執行指令: `python scripts/t38_treatment_eval.py round6`（重建的慣例格式，非逐字保留的原始指令列）
- 本輪假設與修改理由: 未留下紀錄（中止於執行中，機制存在之前沒有假設欄位可寫）。
  可確定的修改內容見下方「本輪唯一倖存的提示詞證據」——只改了 `carpet` 一個候選的
  描述句，方向像是想讓 CLIP 更強調「纖維紋理」而非泛用的「地毯或織品地板覆蓋物」。

## 完成度（6/13 張；1 張啟動但未跑完；6 張未啟動）

| 狀態 | 照片 |
|---|---|
| ✅ 已完成（有 `detail.json`） | CathedralRoom, arena_ntsu_linkou, bathroom_tiled, bedroom_ai_generated, car_interior_suv, stairwell_tiled |
| 🟡 已啟動未完成（只有 `preprocess/`，無 `detail.json`） | DivorceBeach |
| ⬜ 未啟動（`runs/` 底下無此照片目錄） | site_photo_department_store, site_photo_gym, site_photo_restaurant, RacquetballCourt4, SteinmanHall, TunnelToHell |

因此**沒有 78 面全量的 `summary.json`／正確率數字**——本輪不曾算出 overall／floor／
in-set 誤判，任何宣稱這些數字的紀錄都是杜撰，本檔不列。

## 本輪唯一倖存的提示詞證據：`surfaces.py` 未提交 diff（原文記錄）

以下是 T-38A 開工當下、尚未執行任何還原動作前，`git diff src/image_reverb/surfaces.py`
的**逐字原文**（sha256 與本輪 6 張已完成照片的 `fingerprint.code_sha256.surfaces.py`
——`c89382baa9994a911817c372b945dcc4b1c76bae3defef9e92e763d225c305d8`——完全相符，
確認這正是 round6 執行當下實際使用的提示詞）：

```diff
--- a/src/image_reverb/surfaces.py
+++ b/src/image_reverb/surfaces.py
@@ -62,7 +62,7 @@ CLIP_MATERIAL_PROMPTS = {
     "gypsum_board": "a painted plasterboard drywall surface",
     "glass": "a pane of clear glass or a window",
     "marble": "a polished marble or ceramic tile surface",
-    "carpet": "a thick carpet or textile floor covering",
+    "carpet": "a thick pile carpet with fiber texture",
     "curtain_fabric": "a heavy fabric curtain or drape",
     "acoustic_panel": "a fibrous acoustic absorption panel",
     "audience_seating": "rows of upholstered seats with an audience",
```

即完整的 `CLIP_MATERIAL_PROMPTS` 快照（`CLIP_OOD_PROMPTS` 未變）：

```json
{
  "CLIP_MATERIAL_PROMPTS": {
    "concrete": "a smooth poured concrete surface",
    "brick": "a bare unglazed brick surface",
    "wood_panel": "a wooden panel or wood plank surface",
    "gypsum_board": "a painted plasterboard drywall surface",
    "glass": "a pane of clear glass or a window",
    "marble": "a polished marble or ceramic tile surface",
    "carpet": "a thick pile carpet with fiber texture",
    "curtain_fabric": "a heavy fabric curtain or drape",
    "acoustic_panel": "a fibrous acoustic absorption panel",
    "audience_seating": "rows of upholstered seats with an audience",
    "grass_soil": "natural grass or bare soil ground",
    "generic_wall": "a plain smooth plastered wall"
  },
  "CLIP_OOD_PROMPTS": {
    "__vehicle_interior": "the inside of a car or vehicle cabin",
    "__outdoor_scene": "an outdoor landscape with sky and trees",
    "__object_closeup": "a close-up photograph of a small object",
    "__person": "a photograph of a person's face or body"
  }
}
```

## 相對 round0_baseline 的字串差異

只有一處：`CLIP_MATERIAL_PROMPTS.carpet`：「a thick carpet or textile floor covering」
→「a thick pile carpet with fiber texture」。其餘 11 個材質候選與全部 4 個
out-of-domain 候選逐字相同。

## 指紋（沿用 `eval_cache.py` 六類指紋，僅 6 張已完成照片有紀錄；本次補寫不重跑）

| 項目 | 值 |
|---|---|
| code_sha256 | {"preprocess.py": "f3d1d2f820087f603ff5cde90c6a4905ec87513fd3d846440c2f79ee7f6b8352", "surfaces.py": "c89382baa9994a911817c372b945dcc4b1c76bae3defef9e92e763d225c305d8", "config.py": "c1e09da90283cb20b3a1c672f0b3150c6f6c280d6d83adeeb218b6413fc176c4"} |
| data_sha256 | {"materials.json": "8afb86e4a44cbb85fc274b1f9369aa598c816a8f1bb60a0f612e5007cd48127f", "material_ground_truth.json": "a4116632e61d90ebcb8cd985fca889762dc57a5c9ad1873b2095f03a70c8b20c"} |
| segmentation_model_id | nvidia/segformer-b4-finetuned-ade-512-512 |
| clip_model_id | openai/clip-vit-base-patch32 |
| clip_threshold | 0.4 |
| eval_mode | treatment:round6 |

`photo_sha256`（6 張已完成的照片，與 round0_baseline 相同來源圖片）：

| 照片 | sha256 |
|---|---|
| CathedralRoom | d4dcaed7c3b590546aa26e006930b1dfc1050e509cca20e4d806a050773c9d48 |
| arena_ntsu_linkou | 2b72af99bbaf6ae791b4c462af1da4808a4fded5f4cb39f9a3f1eb89df0a9b10 |
| bathroom_tiled | 1f7ced1531d50ff9ed839315ad85063d6bfc6a699cbd63467481b56a44e35d73 |
| bedroom_ai_generated | b108578269b96adcdcabac65641c766ff1a7e3e5243707a2ce5014858434bde5 |
| car_interior_suv | 7dd1c6b2a154fea934e0ecc4790d18de46276be52f291d6a6eb873cf06ca0cc5 |
| stairwell_tiled | 40859d6e815202a700b237625e33e177ec6f3193cd5e409231ef0c0385b370fa |

## 後續處置（T-38A 步驟 4 規定的順序，不得顛倒）

本檔（含上方 diff 原文）落地並完成 commit 之後，`surfaces.py` 才被還原到 HEAD
基線（`git checkout HEAD -- src/image_reverb/surfaces.py`）——這是本案唯一允許的
還原動作。還原後 `carpet` 提示詞回到 round0_baseline 的
「a thick carpet or textile floor covering」，`src/` 對 HEAD 零 diff。
