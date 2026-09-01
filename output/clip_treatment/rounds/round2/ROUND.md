# Round `round2` — T-38 治療輪紀錄（歷史補寫，T-38A 步驟 4）

> 本檔由 T-38A 補寫，不是當輪執行當下產生的即時紀錄——round2 是「上一個視窗」
> 在 T-38A 的原子發布／ROUND.md 機制存在之前跑的，補寫時只能依現存證據
> （`summary.json`／`tables.md`／`runs/*/detail.json` 的指紋）誠實記錄，
> **凡是已遺失的內容一律明寫「不可恢復」，不得猜測或倒填**（Fable 拆卡裁決第 4 點）。

- status: complete
- 父輪次: round1（推定——逐輪覆寫的線性紀錄推定，非精確 lineage 證據）
- 執行指令: `python scripts/t38_treatment_eval.py round2`（重建的慣例格式，非逐字保留的原始指令列）
- 本輪假設與修改理由: **不可恢復**。上一個視窗逐輪覆寫 `src/image_reverb/surfaces.py`
  且從未 commit，本輪實際改了哪個材質候選的提示詞字串、動機是什麼，已隨後續輪次
  的覆寫遺失，只留檔案內容 sha256（見下方指紋表）。不得猜測或倒填。

## CLIP_MATERIAL_PROMPTS / CLIP_OOD_PROMPTS 快照

**不可恢復**——`surfaces.py` 在本輪之後被下一輪覆寫，且從未進版控，逐字提示詞
內容已遺失，只剩檔案內容 sha256（見下方指紋表 `code_sha256.surfaces.py`）。

## 相對 round0_baseline 的字串差異

**不可恢復**（原因同上）。可確定的是：本輪 `surfaces.py` 的 sha256
（`876e875ee7700758911e8adc786a19d6c9d58eb79e65a8c6cb0bbcffbe2569a1`）與
round0_baseline（`c87d90c9cc23f4bcbc15c32b7955f3066881da9b91565d15fd413eaf0c7f6511`）
不同，代表提示詞確實被改過，但改了哪個候選、改成什麼字串，無法重建。

## 正確率數字（來自 `summary.json`，程式產出非手打）

| 指標 | 數值 |
|---|---|
| overall | 24/76 |
| floor | 3/13 |
| in-set 誤判 | 16 |
| clip 來源正確率 | 7/23 |
| 非 proxy 正確率 | 23/60 |
| proxy 正確率 | 1/16 |

相對 round0_baseline（31/76、4/13、9）：overall 下降、floor 下降、in-set 誤判大幅
上升——本輪三項門檻皆未達成。

## 與 T-33 凍結快取的差異範圍評估

非預期範圍：11 張照片有差異（CathedralRoom, DivorceBeach, RacquetballCourt4,
SteinmanHall, TunnelToHell, bathroom_tiled, bedroom_ai_generated, car_interior_suv,
site_photo_department_store, site_photo_restaurant, stairwell_tiled），其中 10 張非
TunnelToHell，多半是本輪提示詞造成的漂移（`diff_scope_summary()` 對本輪差異集合的
實際輸出，見同目錄 `tables.md` 最後一節的完整差異清單）。

## 指紋（沿用 `eval_cache.py` 六類指紋，來自 `runs/*/detail.json` 既有快取，本次補寫不重跑）

| 項目 | 值 |
|---|---|
| code_sha256 | {"preprocess.py": "f3d1d2f820087f603ff5cde90c6a4905ec87513fd3d846440c2f79ee7f6b8352", "surfaces.py": "876e875ee7700758911e8adc786a19d6c9d58eb79e65a8c6cb0bbcffbe2569a1", "config.py": "c1e09da90283cb20b3a1c672f0b3150c6f6c280d6d83adeeb218b6413fc176c4"} |
| data_sha256 | {"materials.json": "8afb86e4a44cbb85fc274b1f9369aa598c816a8f1bb60a0f612e5007cd48127f", "material_ground_truth.json": "a4116632e61d90ebcb8cd985fca889762dc57a5c9ad1873b2095f03a70c8b20c"} |
| segmentation_model_id | nvidia/segformer-b4-finetuned-ade-512-512 |
| clip_model_id | openai/clip-vit-base-patch32 |
| clip_threshold | 0.4 |
| eval_mode | treatment:round2 |

（`photo_sha256` 逐張與 round0_baseline 相同，13 張來源圖片本輪未變，僅
`surfaces.py` 改變——見 `runs/<name>/detail.json` 的 `fingerprint.photo_sha256`。）

詳細逐面判定與 in-set 誤判明細見同目錄既有的 `tables.md`（本卡未改動其內容）。
