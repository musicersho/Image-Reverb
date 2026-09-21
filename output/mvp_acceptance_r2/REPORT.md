# MVP 重新驗收報告（T-17-R2 / SPEC §7）

- **執行者**：Opus（T-17-R2 卡「Opus 主導」；本視窗只跑卡片列出的指令與已驗證的 T-57 工具，未寫、未改任何 repo 腳本）
- **執行日期**：2026-09-21
- **受驗程式版本**：`8ac0b64`（步驟 1 資料集鎖定 commit；與 `0a84f34` 相比只多 `TASKS.md` 2 行＋`DATASET_MANIFEST.json`，`src`／`data`／`scripts` 零 diff）
- **使用者回饋**：2026-09-21 同日（§7-1 作答、§7-3 載入、§7-4 試聽）
- **相關 commit**：步驟 1 `8ac0b64`｜步驟 6 `001c8ed`｜作答鎖定 `d2f3572`｜§7-1 計分紀錄 `a46bac6`｜本 REPORT＝收工 commit

---

## 0. 結論

**`MVP：FAIL（R2）`**——判定式「判準 1～4 全部達成才 PASS」；**判準 2（§7-2 自動組）未達**，其餘三項達成。T-17 首驗 `FAIL` 永久保留。

| 判準 | 門檻 | 結果 | 判定 |
|---|---|---|---|
| 1. §7-1 盲聽配對（held-out） | ≥4/5 | **5/5**（3 題樣本為 forced 產出，照程序 P1 計分） | `達成（held-out＝AI 合成圖・共用開發素材）` |
| 2. §7-2 RT60 對照（in-domain 自動組） | 500Hz–4kHz 逐頻段＋聯合帶皆 <20% | 自動組 **0/0**；coverage **0/1**（唯一 in-domain 場地 `mit_gym` 被 gate 擋下） | **未達** |
| 3. §7-3 外部 convolution reverb 載入 | 可載入 | 使用者回報「可載入」；IR 格式 48 kHz／mono／PCM_24 WAV（`soundfile.info` 驗） | 達成 |
| 4. §7-4 試聽無重大 artifact | 無重大 artifact | 使用者 §7-4 回報未提任何 artifact，只指出殘響長短；§7-1 備註有兩題「輕微／有一點鐵桶子聲」、其一自評「可接受」 | 達成（附記見 §4） |
| 5. 報告項（非門檻） | — | 見 §5：域外 9/9 BLOCK、域外誤放 0；in-domain coverage 場地 0/1、held-out 2/3；錯誤放行率主率 8/10（6N 下界 8/12、上界 10/12） | — |
| 6. 素材可追溯（非判定式項） | — | **T-04 缺項**（退役集 9 張來源網址缺） | 未達（見 §6） |

**一句話**：盲聽能分辨五類空間（5/5），但分辨得出來不等於做得對——同一批樣本的估計尺寸與殘響時間在絕對值上明顯偏大（§1.3），唯一 in-domain 的真實場地被擋下所以 §7-2 自動組沒有任何可計分的 run，而放行的兩張 held-out 六面材質可判的 10 面錯 8 面（§5）。

### 0.1 強制句（裁定 T-17-R2-S §4，逐字）

> §7-1 held-out 五張為 AI 合成圖（GPT Image；使用者 2026-09-20 指定），非真實空間照片；本結果不能外推為『對真實照片有效』，真實照片的 held-out 驗證尚未做過。

> 這五張同時是 T-04 現行開發素材的來源（使用者 2026-09-20 決定一批兩用；其中四張以 `assets/photos/t04_gpt_*.png` 逐位元並存），且在 R2 開跑前已被 Phase 0 冒煙測試（`test_segmentation.py`／`test_depth.py`，只產視覺化與統計）以分割／深度模型處理過；期間未用於任何調參、標註或校準（佐證：`git diff b06f022..HEAD --stat -- src/ data/` 為空——五張圖生成前的最後一個 commit 起，`src/`／`data/` 全目錄零 diff）。所以本批是『未用於調參的合成圖』，不是『模型從未見過的圖』。

### 0.2 核准紀錄（使用者 Prompt 原文三句，逐字）

- 「程序 P1 核准。」（程序 P1；無「P2」字樣）
- 「held-out 已就位。」（Prompt A；無「沿用舊五張（降級）」字樣）
- 「held-out 為 AI 合成圖（路徑 S）。」＝對裁定 T-17-R2-S 條文的核准（依該裁定 §1）。
- held-out 路徑：**路徑 S＝AI 合成圖**（非降級；Prompt B／`--legacy` 依裁定 T-17-R2-S §3 第 6 點不可用、未使用）。
- T-04 缺項：9 張照片來源網址缺、使用者 2026-09-16 決定內部使用不補（全文見 §6）。
- 裁定 T-57-D（錯誤放行率口徑）使用者未行使否決權，照原口徑產表。

### 0.3 步驟 0 前置檢查原始輸出（全部成立才開跑）

**(a)＋`b06f022` 零 diff＋(d) 兩段 diff**（zsh 下路徑逐字寫在指令列）：
```
### 0(a)
porcelain_exit=0 lines=       0
0a84f3406419591c7fae3024687a621bcf7c465c
274
c1b3f63 T-56: 驗證通過（工程）
875697e T-57: 驗證通過（工程）（含修正輪 T-57-F1）
0a84f34 T-60: 驗證通過（工程）
a65fc32 T-62: 驗證通過（工程）
--- T-58 recent
875697e T-57: 驗證通過（工程）（含修正輪 T-57-F1）
b06f022 T-58: 驗證通過（工程）（含修正輪 T-58-F1／T-58-F2）
1d5ca73 T-58-F2: 完成第二修正輪（待驗證）
## main...origin/main
### b06f022
exit=0
### 0(d)-1
 src/image_reverb/geometry.py | 15 ++++++++++++---
 1 file changed, 12 insertions(+), 3 deletions(-)
### 0(d)-2
exit=0
### a65fc32..HEAD
 DEV_LOG.md                                      |  15 +
 HANDOFF.md                                      |  25 +
 TASKS.md                                        | 576 +++++++++++++++++++++++-
 TODO.md                                         |   3 +
 assets/SOURCES.md                               |  16 +-
 assets/photos_heldout/ground_truth_heldout.json | 241 ++++++++++
 assets/photos_heldout/heldout_bathroom.png      | Bin 0 -> 2170166 bytes
 assets/photos_heldout/heldout_car.png           | Bin 0 -> 2342677 bytes
 assets/photos_heldout/heldout_corridor.png      | Bin 0 -> 2149625 bytes
 assets/photos_heldout/heldout_hall.png          | Bin 0 -> 1943157 bytes
 assets/photos_heldout/heldout_living.png        | Bin 0 -> 2324171 bytes
 assets/t17r2_synthetic_candidates/README.md     |   3 +
 12 files changed, 872 insertions(+), 7 deletions(-)
```
讀法：porcelain 0 行；`c1b3f63`（T-56）、`875697e`（T-57 含 T-57-F1）、`0a84f34`（T-60）、`a65fc32`（T-62）各一行；T-58 已由 `b06f022` 結案、無進行中的 commit。
`git diff b06f022..HEAD --stat -- src/ data/` 為空。(d) 第一段非空（`geometry.py | 15`，T-54）、第二段 `80dd527..HEAD` 為空＝「A 由 T-55 於 T-54 之後重量（`80dd527`）、B 由 T-56 重量（`c1b3f63`），其後量測路徑零 diff」。

**(c) 尺寸／長寬比／sha256 同一性**（PIL 只讀尺寸、未 save）：
```
### 0(c) listing
total 21376
drwxr-xr-x   8 musicersho  staff      256 Sep 21 10:09 .
drwxr-xr-x  11 musicersho  staff      352 Sep 21 09:52 ..
-rw-r--r--   1 musicersho  staff     7491 Sep 21 10:09 ground_truth_heldout.json
-rw-r--r--   1 musicersho  staff  2170166 Sep 20 15:05 heldout_bathroom.png
-rw-r--r--   1 musicersho  staff  2342677 Sep 20 15:06 heldout_car.png
-rw-r--r--   1 musicersho  staff  2149625 Sep 20 15:07 heldout_corridor.png
-rw-r--r--   1 musicersho  staff  1943157 Sep 20 15:06 heldout_hall.png
-rw-r--r--   1 musicersho  staff  2324171 Sep 20 15:05 heldout_living.png
### size/aspect/sha vs manifest
manifest keys: <class 'list'>
manifest entries: {'heldout_bathroom.png': '9697b659d104f71643f5083b166445a7381db147f52f4607412395bf8dec3a05', 'heldout_living.png': '0a731b514a7645143d26cc460e531aea2bc29a767c17b3cd402b3d8e30dd8a07', 'heldout_hall.png': 'eb4f1d09b86c9c6b7658662820a7d419a0f4b243c4746353aae09f94c59adc59', 'heldout_corridor.png': '7a9f2b8595b6102d5c52bc0738923dd8a24192233565c7e3dd64bbf654d7044d', 'heldout_car.png': '7b345e6692bc0ca866c9516fe734dd9789f1b95b937345ac2de20bb7a08b457f'}
heldout_bathroom.png 1448 1086 ratio=1.3333 2:1±5%=False maxside>=1280=True 9697b659d104f71643f5083b166445a7381db147f52f4607412395bf8dec3a05 manifest_match=True
heldout_car.png 1448 1086 ratio=1.3333 2:1±5%=False maxside>=1280=True 7b345e6692bc0ca866c9516fe734dd9789f1b95b937345ac2de20bb7a08b457f manifest_match=True
heldout_corridor.png 1448 1086 ratio=1.3333 2:1±5%=False maxside>=1280=True 7a9f2b8595b6102d5c52bc0738923dd8a24192233565c7e3dd64bbf654d7044d manifest_match=True
heldout_hall.png 1448 1086 ratio=1.3333 2:1±5%=False maxside>=1280=True eb4f1d09b86c9c6b7658662820a7d419a0f4b243c4746353aae09f94c59adc59 manifest_match=True
heldout_living.png 1448 1086 ratio=1.3333 2:1±5%=False maxside>=1280=True 0a731b514a7645143d26cc460e531aea2bc29a767c17b3cd402b3d8e30dd8a07 manifest_match=True
ALL_OK True
```
**(c) 純度檢查＋`find` 目錄檢查**（grep 範圍＝`output/.archive/`、`data/` 全目錄、`output/**/*.md`＋`output/**/MANIFEST.json`）：
```
### purity grep
9697b659d104 archive=       0 data=       0 output_md_manifest=       0
0a731b514a76 archive=       0 data=       0 output_md_manifest=       0
eb4f1d09b86c archive=       0 data=       0 output_md_manifest=       0
7a9f2b8595b6 archive=       0 data=       0 output_md_manifest=       0
7b345e6692bc archive=       0 data=       0 output_md_manifest=       0
output/.archive
     442
### find dirs
find_exit=0 (empty above = pass)
### mvp_acceptance_r2 exists?
ls: output/mvp_acceptance_r2: No such file or directory
### exposure
-rw-r--r--   1 musicersho  staff     9892 Sep 21 09:43 depth_stats.json
-rw-r--r--   1 musicersho  staff  1043959 Sep 21 09:43 t04_gpt_arena_concert_depth.png
-rw-r--r--   1 musicersho  staff   688955 Sep 21 09:43 t04_gpt_bathroom_depth.png
-rw-r--r--   1 musicersho  staff   785031 Sep 21 09:43 t04_gpt_car_depth.png
-rw-r--r--   1 musicersho  staff   886864 Sep 21 09:43 t04_gpt_cave_lab_depth.png
-rw-r--r--   1 musicersho  staff   890685 Sep 21 09:43 t04_gpt_cavern_crowd_depth.png
-rw-r--r--   1 musicersho  staff   653981 Sep 21 09:43 t04_gpt_corridor_depth.png
-rw-r--r--   1 musicersho  staff   779651 Sep 21 09:43 t04_gpt_livehouse_depth.png
-rw-r--r--   1 musicersho  staff   767772 Sep 21 09:43 t04_gpt_living_depth.png
-rw-r--r--   1 musicersho  staff   676113 Sep 21 09:43 t04_gpt_stairwell_depth.png
-rw-r--r--   1 musicersho  staff    10520 Sep 21 09:45 stats.json
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_arena_concert_labelmap.npy
-rw-r--r--   1 musicersho  staff  5453357 Sep 21 09:45 t04_gpt_arena_concert_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_bathroom_labelmap.npy
-rw-r--r--   1 musicersho  staff  3854256 Sep 21 09:45 t04_gpt_bathroom_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_car_labelmap.npy
-rw-r--r--   1 musicersho  staff  4183304 Sep 21 09:45 t04_gpt_car_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_cave_lab_labelmap.npy
-rw-r--r--   1 musicersho  staff  4766623 Sep 21 09:45 t04_gpt_cave_lab_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_cavern_crowd_labelmap.npy
-rw-r--r--   1 musicersho  staff  4974210 Sep 21 09:45 t04_gpt_cavern_crowd_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_corridor_labelmap.npy
-rw-r--r--   1 musicersho  staff  3806063 Sep 21 09:45 t04_gpt_corridor_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 20 16:16 t04_gpt_hall_labelmap.npy
-rw-r--r--   1 musicersho  staff  3455868 Sep 20 16:16 t04_gpt_hall_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_livehouse_labelmap.npy
-rw-r--r--   1 musicersho  staff  4455578 Sep 21 09:45 t04_gpt_livehouse_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_living_labelmap.npy
-rw-r--r--   1 musicersho  staff  4133100 Sep 21 09:45 t04_gpt_living_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_stairwell_labelmap.npy
-rw-r--r--   1 musicersho  staff  3940623 Sep 21 09:45 t04_gpt_stairwell_seg.png
      31
output/seg/stats.json:18
output/depth/depth_stats.json:9
```
另：`ground_truth_heldout.json` 五 stem×六面、schema 符合 T-57 交接筆記第 1 點；GT 用到的材質 id 全部存在於 `data/materials.json`；`assets/SOURCES.md` §4 五列齊全。

**曝光範圍紀錄（裁定 T-17-R2-S §4 最後一點；只列不刪）**——`ls -la output/seg/ output/depth/ | grep -E 't04_gpt|stats\.json'` 與 `grep -c t04_gpt output/seg/stats.json output/depth/depth_stats.json`（步驟 0、全套測試執行**前**）：
```
-rw-r--r--   1 musicersho  staff     9892 Sep 21 09:43 depth_stats.json
-rw-r--r--   1 musicersho  staff  1043959 Sep 21 09:43 t04_gpt_arena_concert_depth.png
-rw-r--r--   1 musicersho  staff   688955 Sep 21 09:43 t04_gpt_bathroom_depth.png
-rw-r--r--   1 musicersho  staff   785031 Sep 21 09:43 t04_gpt_car_depth.png
-rw-r--r--   1 musicersho  staff   886864 Sep 21 09:43 t04_gpt_cave_lab_depth.png
-rw-r--r--   1 musicersho  staff   890685 Sep 21 09:43 t04_gpt_cavern_crowd_depth.png
-rw-r--r--   1 musicersho  staff   653981 Sep 21 09:43 t04_gpt_corridor_depth.png
-rw-r--r--   1 musicersho  staff   779651 Sep 21 09:43 t04_gpt_livehouse_depth.png
-rw-r--r--   1 musicersho  staff   767772 Sep 21 09:43 t04_gpt_living_depth.png
-rw-r--r--   1 musicersho  staff   676113 Sep 21 09:43 t04_gpt_stairwell_depth.png
-rw-r--r--   1 musicersho  staff    10520 Sep 21 09:45 stats.json
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_arena_concert_labelmap.npy
-rw-r--r--   1 musicersho  staff  5453357 Sep 21 09:45 t04_gpt_arena_concert_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_bathroom_labelmap.npy
-rw-r--r--   1 musicersho  staff  3854256 Sep 21 09:45 t04_gpt_bathroom_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_car_labelmap.npy
-rw-r--r--   1 musicersho  staff  4183304 Sep 21 09:45 t04_gpt_car_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_cave_lab_labelmap.npy
-rw-r--r--   1 musicersho  staff  4766623 Sep 21 09:45 t04_gpt_cave_lab_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_cavern_crowd_labelmap.npy
-rw-r--r--   1 musicersho  staff  4974210 Sep 21 09:45 t04_gpt_cavern_crowd_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_corridor_labelmap.npy
-rw-r--r--   1 musicersho  staff  3806063 Sep 21 09:45 t04_gpt_corridor_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 20 16:16 t04_gpt_hall_labelmap.npy
-rw-r--r--   1 musicersho  staff  3455868 Sep 20 16:16 t04_gpt_hall_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_livehouse_labelmap.npy
-rw-r--r--   1 musicersho  staff  4455578 Sep 21 09:45 t04_gpt_livehouse_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_living_labelmap.npy
-rw-r--r--   1 musicersho  staff  4133100 Sep 21 09:45 t04_gpt_living_seg.png
-rw-r--r--   1 musicersho  staff  1572656 Sep 21 09:45 t04_gpt_stairwell_labelmap.npy
-rw-r--r--   1 musicersho  staff  3940623 Sep 21 09:45 t04_gpt_stairwell_seg.png
      31
output/seg/stats.json:18
output/depth/depth_stats.json:9
```
揭露：① T-62 驗證時的全套測試讓此清單由 23 行增為 31 行，`t04_gpt_corridor`、`t04_gpt_living`（held-out 逐位元複本）首度產生深度圖（T-62 卡 Opus 驗證紀錄）；
② 本卡步驟 0(e) 的全套測試（禁用令例外 ③；本卡唯一一次）重新處理了同一組共用圖，檔名清單前後逐行相同（31 行）、`output/` 頂層與目錄清單不變，只有時間戳更新；
③ 步驟 2 依本卡執行步驟以 CLI 處理五張 held-out（例外 ①），產生 `output/heldout_*/`。以上皆涵蓋於 §0.1 第二句。

**(e) 全套測試（`ls scripts/test_*.py`＝22 支，不帶引數、各一次）**：
```
scripts/test_acoustics.py EXIT=0
scripts/test_confidence_axes.py EXIT=0
scripts/test_coupled.py EXIT=0
scripts/test_depth.py EXIT=0
scripts/test_eval_cache.py EXIT=0
scripts/test_furnishings.py EXIT=0
scripts/test_geometry_scope.py EXIT=0
scripts/test_ir_synth.py EXIT=0
scripts/test_material_fallback.py EXIT=0
scripts/test_output_gate.py EXIT=0
scripts/test_pipeline_dedup.py EXIT=0
scripts/test_preprocess.py EXIT=0
scripts/test_scene_text.py EXIT=0
scripts/test_segmentation.py EXIT=0
scripts/test_surface_trusted_scope.py EXIT=0
scripts/test_t17_provenance.py EXIT=0
scripts/test_t17r2_tools.py EXIT=0
scripts/test_t30_low_combined.py EXIT=0
scripts/test_t38_treatment_eval.py EXIT=0
scripts/test_t39_materials_invariant.py EXIT=0
scripts/test_t44_role_partition.py EXIT=0
scripts/test_t46_role_flag.py EXIT=0
```
**(e) 六條交付 IR MD5**：T-14 兩條由 `test_ir_synth.py` 內建比對（log：`small_surf_carpet … f3a763bed13cf4d6f49dbacddee6313f`、`hall … f24353b5dbecf0f6073ca65a7be44ad3` 皆「與 T-14 交付版相同」）；T-20／T-21 四條以 `pipeline.OUTPUT_ROOT` 導到 scratchpad 經 `cli.main()` 重生，`md5 -q`：
```
text_bathroom 2adbaa75eb698772a8c9aa693179ec47
text_church 2dd19b6e6d351d713887636fe45cd67e
neighbor_voices 9a94ffdf5d8295aee7889729c39c9cd8
stadium_corridor a1c21bcc3fd9aa3480df203a89c8cd05
```
與歷史紀錄完整 32 碼逐字相同。

**(f)** `output/mvp_acceptance/` 41 檔 sha256 清單，清單本身 sha256＝`9c514e87884f929f6fefc6bba09ad2cf9fd292d2348858c395598423da1c08ce`；收工比對結果見 §7。

### 0.4 資料集鎖定與樣本出處（步驟 1～3）

- 步驟 1：`python scripts/t17r2_dataset_manifest.py` → `DATASET_MANIFEST.json` sha256 `501eb6a7ec1f48febd8f51530d7c92cc232f74d16ca6d5395ca2a436ec705bd2`（manifest 內 head `0a84f34`、degraded false、domain in／in／out／in／non_room、in_domain 僅 `mit_gym`、乾聲 `assets/dry/clap_synth.wav`）；commit `8ac0b64`（10:32:23 +0800），早於任何樣本。
- 步驟 2（10:33:13～10:42:58 +0800，HEAD `8ac0b64`）：指令樣板逐字（`python -m src.image_reverb <參數…> --no-viz > "$LOG" 2>&1; printf '\nexit=%d\n' $? >> "$LOG"`），結束碼 3 者另存 `.forced.log`：
```
heldout_bathroom default exit=0
heldout_living default exit=0
heldout_hall default exit=3
heldout_hall forced exit=0
heldout_corridor default exit=3
heldout_corridor forced exit=0
heldout_car default exit=3
heldout_car forced exit=0
CathedralRoom default exit=3
CathedralRoom forced exit=0
DivorceBeach default exit=3
DivorceBeach forced exit=0
site_photo_department_store default exit=3
site_photo_department_store forced exit=0
site_photo_gym default exit=3
site_photo_gym forced exit=0
site_photo_restaurant default exit=3
site_photo_restaurant forced exit=0
RacquetballCourt4 default exit=3
RacquetballCourt4 forced exit=0
SteinmanHall default exit=3
SteinmanHall forced exit=0
TunnelToHell default exit=3
TunnelToHell forced exit=0
t17r2_manual_department_store default exit=3
t17r2_manual_department_store forced exit=0
t17r2_manual_gym default exit=3
t17r2_manual_gym forced exit=0
t17r2_manual_restaurant default exit=3
t17r2_manual_restaurant forced exit=0
t17r2_manual_racquetball default exit=3
t17r2_manual_racquetball forced exit=0
t17r2_manual_steinman default exit=3
t17r2_manual_steinman forced exit=0
```
- 步驟 3：`t17r2_blind_test.py` exit 0；核對（為免洩題，打包當下只比集合、不印對應）：
```
blind top keys: ['degraded', 'dry', 'generated_from', 'packaging_git_revision', 'shuffle_seed']
photo_sha256 count 5 set equal (sorted, 不印對應關係): True
dry.sha256 equal: True 9d89ddae83d1e4f4
Traceback (most recent call last):
  File "<stdin>", line 17, in <module>
TypeError: unhashable type: 'dict'
packaging_git_revision: {'commit': '8ac0b643b387603458b9b26e005d1f60775f6f42', 'dirty': False} shuffle_seed: 20260916 degraded: False
list 5
entry keys: ['confidence', 'dims_source', 'forced_low_confidence', 'ir_sha256', 'photo_sha256', 'run', 'source_provenance', 'wet_sha256']
prov keys: ['cli_params', 'clip_confidence_threshold', 'clip_model_id', 'generated_at', 'git_revision', 'input_sha256', 'materials_json_sha256', 'segmentation_model_id']
git_revision distinct: {'{"commit": "8ac0b643b387603458b9b26e005d1f60775f6f42", "dirty": false}'}
generated_at sorted: ['2026-09-21T02:33:27Z', '2026-09-21T02:33:40Z', '2026-09-21T02:34:06Z', '2026-09-21T02:34:33Z', '2026-09-21T02:35:00Z']
forced (sorted, 無序): ['False', 'False', 'True', 'True', 'True']
```
（第一次核對的 python 一行式在印 `git_revision` 時因欄位是 dict 而 `TypeError`——是 Opus 臨時核對碼的錯誤，不是工具錯誤；第二段改正後重印。）五筆 `generated_at`（02:33:27Z～02:35:00Z）晚於步驟 1 commit（02:32:23Z）、早於步驟 6 commit（`001c8ed` 02:43:46Z）；步驟 2～3 之間無 commit；步驟 6 之後未重生任何樣本。

---

## 1. §7-1 盲聽配對 —— `達成（held-out＝AI 合成圖・共用開發素材）`

> §7-1 held-out 五張為 AI 合成圖（GPT Image；使用者 2026-09-20 指定），非真實空間照片；本結果不能外推為『對真實照片有效』，真實照片的 held-out 驗證尚未做過。

> 這五張同時是 T-04 現行開發素材的來源（使用者 2026-09-20 決定一批兩用；其中四張以 `assets/photos/t04_gpt_*.png` 逐位元並存），且在 R2 開跑前已被 Phase 0 冒煙測試（`test_segmentation.py`／`test_depth.py`，只產視覺化與統計）以分割／深度模型處理過；期間未用於任何調參、標註或校準（佐證：`git diff b06f022..HEAD --stat -- src/ data/` 為空——五張圖生成前的最後一個 commit 起，`src/`／`data/` 全目錄零 diff）。所以本批是『未用於調參的合成圖』，不是『模型從未見過的圖』。

### 1.1 作答與對答

作答原文先由 Opus 逐字轉入 `blind_test/作答表.md` 並 commit 鎖定（`d2f3572`，檔案 sha256 `68faaa1ff69893652d6c5cf8eeda36159423c298142c51460cb390ae01d5613a`），之後才打開 `blind_test_ANSWERS.json`。

| 樣本 | 使用者作答 | 正解（source_run） | 樣本是否 forced | 正誤 | 使用者備註（原文） |
|---|---|---|---|---|---|
| sample_1 | 客廳臥室 | 客廳／臥室（`heldout_living`） | 否 | ✅ | 微微的鐵桶子聲，但可接受 |
| sample_2 | 教堂大空間 | 教堂／大空間（`heldout_hall`） | 是 | ✅ | — |
| sample_3 | 車內 | 車內（`heldout_car`） | 是 | ✅ | 尾巴有點長，實際空間沒那麼大 |
| sample_4 | 走廊樓梯間 | 走廊／樓梯間（`heldout_corridor`） | 是 | ✅ | 尾巴有點長，實際空間沒那麼大 |
| sample_5 | 浴室 | 浴室（`heldout_bathroom`） | 否 | ✅ | 有一點鐵桶子聲 |

**5/5**。答案鍵獨立複核：五個 `sample_N.wav`／`sample_N_IR.wav` 的 sha256 分別等於 `blind_test/MANIFEST.json` 對應 run 的 `wet_sha256`／`ir_sha256`，且 `sample_N_IR.wav` 與 `output/<source_run>/ir_mono.wav` 逐位元相同。
乾聲為合成拍手（無自錄乾聲）；`SHUFFLE_SEED = 20260916`；五筆 provenance 皆 `8ac0b64`、dirty false。五張中 **3 張被 gate 擋下後 forced 產樣**（hall／corridor／car），依程序 P1 照算。

### 1.2 這個 5/5 能說明什麼、不能說明什麼

- **能**：管線對這五張合成圖產出的 IR，在「五選一、每類只用一次」的配對下，彼此的**相對**差異足以讓一位聽者全部配對正確。T-17 首驗的「空間大小聽反」（2/5）這次沒有重演。
- **不能**：① 外推到真實照片（§0.1 第一句）；② 說明「模型沒見過這些圖」（§0.1 第二句）；③ 說明絕對殘響正確——見 §1.3；
  ④ 單一聽者、五題、每類用一次的配對設計可用刪去法（做對 4 題第 5 題必對），5/5 與 4/5 的資訊量差距小；⑤ 3/5 樣本是 forced 產出，即 gate 認為不可信、產品預設路徑不會交給使用者的輸出。

### 1.3 🔬 絕對值：估計尺寸與目標殘響明顯偏大（和使用者備註一致）

`output/heldout_*/analysis.json` 原值（`dims_source=metric_depth`；`rt60_bands_target_sabine` 依序 125／250／500／1k／2k／4k Hz，秒）：

| run | 估計尺寸 L×W×H（m） | confidence | 500Hz 目標 | 1kHz 目標 |
|---|---|---|---|---|
| `heldout_bathroom` | 5.64×6.51×4.88 | medium（放行） | 3.33 s（125Hz 10.22 s） | 1.52 s |
| `heldout_living` | 8.40×9.69×7.27 | medium（放行） | 3.45 s | 2.10 s |
| `heldout_hall` | 18.51×21.37×16.03 | low（forced） | 6.14 s | 7.98 s |
| `heldout_corridor` | 10.12×11.69×8.77 | low（forced） | 9.06 s | 7.35 s |
| `heldout_car` | 9.16×10.58×7.93 | low（forced） | 4.55 s | 5.30 s |

車內估成 9×11×8 m、浴室 500Hz 目標 3.3 秒，對一般轎車車廂與家用浴室都不合理（這裡只用常識判斷，**未**以 GT 的 `dims_m` 設計值計算誤差——裁定 T-17-R2-S 禁止把它當真實尺寸引用）。
使用者對 sample_3／4 的備註「尾巴有點長，實際空間沒那麼大」與 §7-4「殘響尾巴都偏長」是同一個訊號。**配對 5/5 靠的是五張之間的相對排序，不是每一張都做對。**
觀察（未深究、交 Fable）：五張 held-out 與四個 `metric_depth` 場地（百貨、健身房、餐廳、隧道）的寬／長比**全部**是 1.1547（＝2/√3，與預設 60° FOV 一致），五張 held-out 的高／長比也全部是 0.866（＝√3/2）——表示在這批圖上單張透視照只估出一個尺度，房間形狀是固定比例。

---

## 2. §7-2 RT60 對照 —— **未達**

`git diff -- src/image_reverb/ir_metrics.py` 為空（步驟 4 當下實跑）。以下表格全部由 `scripts/t17r2_report_tables.py` 產出（`tables.md`，地雷 #15：數字不手打），此處原文照錄表 2；完整誤差表 1、階梯比表 3、手動尺寸依據表 4 見 `tables.md`。

### 表 2　達標率 —— 三組分列（裁決 C：不得合併成單一數字）

**自動組**（`group=="auto"` 且 in-domain；F-01 產品主張本體）

| 場地 | run | 五項判準通過 | 全場地達標？ |
|---|---|---|---|
| **小計** | — | **0/0** | **0/0 場地全達標** |
**coverage** = 通過 gate 的 in-domain 場地數 / in-domain 場地數 = **0/1**

**forced 組**（被擋後 `--force-low-confidence` 產生，只記錄不計達標率）

| 場地 | run | in-domain | 500Hz | 1kHz | 2kHz | 4kHz | 聯合帶 |
|---|---|---|---|---|---|---|---|
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | `CathedralRoom` | 否 | ❌ +263% | ❌ +354% | ❌ +224% | ❌ +166% | ❌ +186% |
| Divorce Beach（戶外沙灘岩礁） | `DivorceBeach` | 否 | ❌ +751% | ❌ +959% | ❌ +701% | ❌ +252% | ❌ +676% |
| Department Store（MIT，百貨賣場） | `site_photo_department_store` | 否 | ❌ +26% | ❌ -25% | ❌ -29% | ✅ -12% | ❌ +121% |
| Gym（MIT，健身房／重訓室） | `site_photo_gym` | 是 | 🟡 -43% | 🟡 -43% | 🟡 -44% | 🟡 -27% | ✅ -20% |
| Restaurant（MIT，餐廳用餐區） | `site_photo_restaurant` | 否 | 🟡 +26% | 🟡 +23% | 🟡 +20% | ✅ +10% | ✅ -4% |
| Racquetball Court 4（壁球場，必測反例） | `RacquetballCourt4` | 否 | ❌ -50% | ❌ -41% | ❌ -46% | ❌ -47% | ❌ -50% |
| Steinman Hall（音樂廳） | `SteinmanHall` | 否 | ✅ +16% | ✅ +6% | ✅ -3% | ✅ +9% | ❌ +30% |
| Tunnel to Hell（要塞地下混凝土隧道） | `TunnelToHell` | 否 | ❌ +212% | ❌ +393% | ❌ +349% | ❌ +291% | ❌ +108% |

**手動組**（`--override-dims`，F-09 正式出口；照 T-17 另列成績，不混入自動組）

| 場地 | run | forced | 五項判準通過 | 全場地達標？ |
|---|---|---|---|---|
| Department Store（MIT，百貨賣場） | `t17r2_manual_department_store` | 是 | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `t17r2_manual_gym` | 是 | 1/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `t17r2_manual_restaurant` | 是 | 0/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `t17r2_manual_racquetball` | 是 | 0/5 | ❌ |
| Steinman Hall（音樂廳） | `t17r2_manual_steinman` | 是 | 3/5 | ❌ |
| **小計** | — | — | **5/25**（20%）| **0/5 場地全達標** |

- **自動組 0/0、coverage 0/1** → 判準 2 沒有任何一個 in-domain 場地可計分 → **未達**。這與 Fable 2026-09-15／16 的事前預告一致（`output/gate_calibration_v3/tables.md` 表 1 即顯示 `site_photo_gym` BLOCK）。in-domain 名單＝`mit_gym` 一個，與事前定義相同、未改動。
- **forced 組只記錄、不計達標率**（裁決 C；本表沒有任何 forced 列進自動組）。僅供參考：`mit_gym` forced 在 500Hz–4kHz 皆 🟡（對 3 條真實 IR 中位數超差、但落在多條真實 IR 區間內）、聯合帶 ✅ −20%。
- **手動組 5/25 項（20%）、0/5 場地全達標**；5 個手動 run 全部是 exit 3 → forced（手動尺寸之下材質仍被判 low）。T-17 首驗手動組為 0/5 場地，本次同為 0/5。

---

## 3. §7-3 外部相容性 —— 達成

- 使用者回報原文（2026-09-21）：「§7-3：可載入」。
- Opus 事前驗格式（`soundfile.info`）：`sample_1..5_IR.wav` 皆 48000 Hz、1 聲道、PCM_24、WAV，長度 4.42～12.87 s。
- 限制：使用者未註明載入的外掛名稱與所用的是哪一條 IR；T-17 首驗已記錄同類外掛可載入，本項判定只依本次回報。

---

## 4. §7-4 人耳試聽 —— 達成（無重大 artifact；殘響長短另記）

held-out 五列全為 AI 合成圖。

播放頁 `播放頁.html`（`t17r2_make_player.py` 產出）：8 場地 wet（全部為 forced 產出者——8 場地自動路徑皆被擋）＋5 張 held-out wet（浴室、客廳未 forced；大空間、走廊、車內 forced），頁面逐檔標示 forced 與否；另附盲測樣本。

**使用者回報原文（2026-09-21）**：
> §7-4：除了以下幾個之外，殘響尾巴都偏長。Department Store（MIT，百貨賣場）／Gym（MIT，健身房／重訓室）／Racquetball Court 4（壁球場，必測反例）／Steinman Hall（音樂廳）
> 額外補充：但 Steinman Hall（音樂廳）的殘響則是太短；Divorce Beach（戶外沙灘岩礁） 在戶外基本上應該聽不到什麼殘響，除非是山谷
（「／」為原訊息換行處。）

**判定理由**：判準 4 問的是「重大 artifact」（T-17 首驗口徑：如地雷 #9「鐵筒子」那類合成瑕疵），殘響長短是準確度問題、歸判準 2。§7-4 回報沒有提到任何 artifact；§7-1 備註有兩題輕微鐵桶子聲（sample_1 客廳「微微的…但可接受」、sample_5 浴室「有一點」），使用者自己的措辭都是輕微等級，**不判為重大**。
這是單一聽者的主觀判斷；地雷 #9 型的低頻集中聲響在兩個未 forced 的 held-out 上被聽到，建議 Fable 在 R2 後複查（`heldout_bathroom` 目標 125Hz 10.22 s 遠大於中高頻，是可疑來源，未驗證）。

**聽感與量測對照（量測數字取 `tables.md` 表 1，forced run）**：

| 場地 | 使用者聽感 | 生成 vs 真實 IR（500Hz／1kHz／聯合帶） | 一致？ |
|---|---|---|---|
| Cathedral Room | 偏長 | +263%／+354%／+186% | ✅ |
| Divorce Beach | 偏長；戶外應幾乎無殘響 | +751%／+959%／+676% | ✅（真實 IR 本身 T30 仍約 0.7 s，是岩礁反射） |
| Tunnel to Hell | 偏長 | +212%／+393%／+108% | ✅ |
| Restaurant | 偏長 | +26%／+23%／−4% | 大致（中頻偏長約兩成） |
| Department Store | 不偏長 | +26%／−25%／+121% | 部分（中高頻偏短、低頻偏長） |
| Gym | 不偏長 | −43%／−43%／−20% | ✅（偏短） |
| Racquetball Court 4 | 不偏長 | −50%／−41%／−50% | ✅（偏短） |
| Steinman Hall | 太短 | +16%／+6%／+30% | ❌ 量測上接近真實 IR（1kHz 真實 1.00 s）；聽者對音樂廳的預期可能比這個實測廳長，單一聽者，不下結論 |
| held-out 五張 | 偏長 | 無真實 IR 可比；目標值見 §1.3 | ✅（與 §1.3 一致） |

---

## 5. 報告項 5（不是門檻）—— coverage／錯誤放行率／域外處理／手動出口

held-out 五列全為 AI 合成圖。

以下原文照錄 `tables.md` 表 5（程式產出，錯誤放行率口徑＝裁定 T-57-D）：

### 表 5　報告項 5 —— 13 張（5 held-out ＋ 8 場地）逐張 gate／domain／六面材質對照

| 照片 | domain | gate | forced | override-dims 導引 | 域外誤放？ | 預設路徑 exit |
|---|---|---|---|---|---|---|
| held-out：浴室 | in | PASS | 否 | 無 | 否 | 0 |
| held-out：客廳／臥室（住宅尺度） | in | PASS | 否 | 無 | 否 | 0 |
| held-out：教堂／大空間 | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| held-out：走廊／樓梯間 | in | BLOCK→forced | 是 | 有 | 否 | 3 |
| held-out：車內 | non_room | BLOCK→forced | 是 | 有 | 否 | 3 |
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Divorce Beach（戶外沙灘岩礁） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Department Store（MIT，百貨賣場） | out | BLOCK→forced | 是 | 無 | 否 | 3 |
| Gym（MIT，健身房／重訓室） | in | BLOCK→forced | 是 | 有 | 否 | 3 |
| Restaurant（MIT，餐廳用餐區） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Racquetball Court 4（壁球場，必測反例） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Steinman Hall（音樂廳） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Tunnel to Hell（要塞地下混凝土隧道） | out | BLOCK→forced | 是 | 有 | 否 | 3 |

#### 未 forced 通過的照片：六面材質對照 GT

**held-out：浴室**（`heldout_bathroom`）

| 面 | 材質 id | 來源 | GT | 正誤 |
|---|---|---|---|---|
| floor | carpet | clip | marble | ❌ |
| ceiling | generic_wall | clip | gypsum_board | ❌ |
| west | generic_wall | clip | marble | ❌ |
| east | generic_wall | clip | marble | ❌ |
| south | generic_wall | clip | unknown | 無法判 |
| north | generic_wall | clip | marble | ❌ |

❌ 5／可判 5／無法判 1（共 6）

**held-out：客廳／臥室（住宅尺度）**（`heldout_living`）

| 面 | 材質 id | 來源 | GT | 正誤 |
|---|---|---|---|---|
| floor | carpet | clip | wood_panel | ❌ |
| ceiling | generic_wall | clip | gypsum_board | ❌ |
| west | gypsum_board | clip | gypsum_board | ✅ |
| east | gypsum_board | clip | gypsum_board | ✅ |
| south | gypsum_board | clip | unknown | 無法判 |
| north | gypsum_board | clip | curtain_fabric | ❌ |

❌ 3／可判 5／無法判 1（共 6）

**錯誤放行率彙總**：被放行照片數 N＝2／總面數 6N＝12／可判面數 10／無法判面數 2／❌ 8；主率（❌÷可判面數）＝8/10（80%）；下界（❌÷6N，無法判全當對）＝8/12（67%）；上界（（❌＋無法判）÷6N，無法判全當錯）＝10/12（83%）

**摘要（三個數字一起引，依裁定 T-57-D §3 第 6 點）**：錯誤放行率主率 **8/10（80%）**、6N 下界 **8/12（67%）**、上界 **10/12（83%）**；N＝2、6N＝12、可判 10、無法判 2（兩張的 `south` 面 GT 皆 `unknown`）。

1. **in-domain coverage**：8 場地 **0/1**（`mit_gym` 被擋）；held-out in-domain（浴室、客廳、走廊）**2/3**；合計 2/4。
2. **錯誤放行**：放行的兩張都是 held-out，且材質嚴重錯誤——`heldout_bathroom` 可判 5 面全錯（地板 GT `marble` 判成 `carpet`、三面 GT `marble` 的牆判成 `generic_wall`、天花 GT `gypsum_board` 判成 `generic_wall`），`heldout_living` 可判 5 面錯 3（地板 GT `wood_panel` 判成 `carpet`、天花 GT `gypsum_board` 判成 `generic_wall`、north GT `curtain_fabric` 判成 `gypsum_board`）。兩張都以 `confidence: medium` 放行，估計尺寸也偏大（§1.3）。**gate 擋下的是「看起來不確定」的，不是「錯的」**——這正是本報告項要揭露的安全假象的反面：放行的也不可靠。
3. **域外輸入全部 BLOCK**：域外／非房間共 9 張（held-out hall、car＋7 個域外場地）**9/9 BLOCK、域外誤放 0**。
   **出口訊息可操作**：9/9 都給出可執行的指令（覆寫材質的完整命令、`--force-low-confidence`），其中 8 張含 `--override-dims` 導引；
   **例外**：`site_photo_department_store`（域外，T-17 表 4 估 35×25 m）被估成 6.04×6.97×3.92 m、geometry＝**medium**，出口訊息只提材質覆寫、**沒有幾何出口**——照著導引改材質，可能以錯誤幾何放行（與裁決 T-48-F 的 V5 同型；本卡不加跑驗證）。
4. **手動出口成績另列**：見 §2 手動組（5/25 項、0/5 場地）；5 個手動 run 都還需要 forced 才有輸出。

---

## 6. 素材來源與授權（判準 6）—— 未達（T-04 缺項）

- **強制句（T-04 缺項）**：9 張照片來源網址缺、使用者 2026-09-16 決定內部使用不補。
- **強制句（裁定 T-17-R2-S §5，逐字）**：使用者 2026-09-20 決定以替換素材處理 T-04（裁定 T-04-R）：舊 9 張退役（來源缺永久保留）、現行素材改為 GPT Image 合成圖；R2 受驗的 gate 仍是以退役集校準的。held-out 五張的來源紀錄見 assets/SOURCES.md §4。
- held-out 五張：AI 生成（GPT Image，Codex 內建 image_gen），依使用者要求，2026-09-20；提示詞 `assets/t17r2_synthetic_candidates/PROMPTS.json`；sha256 `assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json`；GT `assets/photos_heldout/ground_truth_heldout.json`（使用者 2026-09-21 看圖確認，原話在 TASKS.md T-60 卡）。
- 8 組對照 IR 與照片：`assets/SOURCES.md` §1（OpenAIR／MIT IR Survey，既有紀錄不變）。
- 共用圖禁用令（T-04 卡裁定 T-04-R §2 第 4 點）仍有效，解除條件＝本卡收工 push＋步驟 11 獨立複驗通過（或使用者明示略過），由 Fable 寫解除紀錄。

---

## 7. 可重跑複驗

```bash
git checkout 8ac0b64   # 受驗版本（樣本產生時的 HEAD）
source .venv/bin/activate
python scripts/t17r2_dataset_manifest.py --out <scratchpad>/DATASET_MANIFEST.json   # 應與 501eb6a7… 逐位元相同
# 步驟 2：逐字照 TASKS.md T-17-R2「🔮 Fable 落地」§4 步驟 2(e) 指令樣板；本次實際指令檔保存在本機 output/mvp_acceptance_r2/step0_evidence/step2_run.sh
python scripts/t17r2_blind_test.py
python scripts/t17r2_rt60_table.py && python scripts/t17r2_report_tables.py
python scripts/t17r2_make_player.py
```
⚠️ 共用圖禁用令解除前，重現只能由步驟 11 的獨立複驗者進行，且輸出一律導到 scratchpad（不得寫 `output/`／`data/`）。
手動組照片須先複製到 scratchpad 改名為 `t17r2_manual_<key>.<ext>`（`--override-dims` 依表 4：35x25x3.2／9x6x2.9／14x9x3.2／12.19x6.1x6.1／20x18x7.5）。
步驟 0～5 的原始終端輸出保存在本機 `output/mvp_acceptance_r2/step0_evidence/`（git 忽略；不刪）。

**收工不變量**：見本卡收工段（TASKS.md T-17-R2 交接筆記）——`output/mvp_acceptance/` 快照比對、`output/.archive` 條目數、本輪新建目錄清單。

---

## 8. 給 Fable 的輸入（R2 收尾複評用；非本卡判定）

1. 判準 2 的瓶頸仍是 gate 對唯一 in-domain 場地的 BLOCK（材質 `out_of_domain`＋geometry low），不是量測方法。
2. 放行≠正確：兩張被放行的 held-out 材質可判面錯 8/10、尺寸偏大；gate 的 `medium` 無法區分「確定地錯」。
3. 單張透視照的尺寸估計在合成圖上系統性偏大，且形狀比例固定（寬／長＝1.1547；§1.3）；殘響系統性偏長與 T-17 首驗的訊號一致，聽感再次獨立佐證。
4. 百貨賣場 geometry=medium 的域外誤估使出口訊息缺幾何導引（§5 第 3 點）。
5. 兩個未 forced 的 held-out 有輕微鐵桶子聲（§4），建議複查低頻集中。
6. 工具小瑕疵：`t17r2_report_tables.py` 印「116 行」但檔案 132 行（`len(L)` 計字串段數），不影響表內容。
