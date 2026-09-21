# 素材來源與授權（T-04）

> 2026-09-20 後續更新：依使用者指定，大空間由禮堂改為大型演唱會巨蛋，現行檔 `assets/photos/t04_gpt_arena_concert.png`。穹頂／多層看台／滿場觀眾／大型舞台清楚可見；1448×1086 解碼與 SHA-256 檢查通過，禮堂版本已備份。現行九張＝四張沿用＋五張新生成；R2 原禮堂圖不變。 提示詞見 [巨蛋生成紀錄](t04_refresh/ARENA_PROMPT.json)。

> **2026-09-20 現行素材更新**：`assets/photos/` 已改為九張 GPT Image 合成圖（五張沿用 R2 候選、四張本次新生成）。現行來源、逐檔替換、完整提示詞及 SHA-256 見 [T-04 素材更新](t04_refresh/README.md)。下方 §2 舊九張表格與來源缺項是歷史紀錄，原檔已移至本機 `assets/photos_legacy_20260920/`，不再是現行輸入。真實 IR 配對照片保留。新圖不沿用舊 GT，R2 候選未升格為正式 held-out。

本檔記錄 `assets/` 底下所有素材的來源與授權狀態。
**新增任何素材時必須同步更新這裡。**

---

## ⚠️ 授權總則（先讀這段）

本專案目前**沒有任何一項第三方素材取得「再散布」授權**。現況處理方式：

| 類別 | 位置 | 進 git？ | 理由 |
|---|---|---|---|
| 對照 IR 與場地照片 | `assets/reference_irs/` | ❌ 只有 INFO.md 進 | 明確未授予再散布權（見下） |
| 測試照片 | `assets/photos/` | ✅ 進 | 使用者知情後決定納入（見下方註記） |
| 合成乾聲 | `assets/dry/` | ✅ 進 | 本專案自行用 numpy 生成，無第三方權利 |

**若本專案未來要公開發佈或商品化，`assets/photos/` 的第三方影像必須全部移除或改用自行拍攝／取得授權的素材。**
注意 git 歷史是永久的——單純 `git rm` 不會從歷史移除，需要改寫歷史。

---

## 1. `assets/dry/` — 乾聲測試檔

| 檔案 | 來源 | 授權 |
|---|---|---|
| `clap_synth.wav` | 本專案 `scripts/` 用 numpy 合成的 2 秒乾拍手（48kHz） | 專案自有，無限制 |

> 之後若放入真實乾聲（人聲／樂器），請在此註明來源與授權，並優先使用真實檔案（見 T-02 交接筆記）。

---

## 2. `assets/photos/` — 測試照片（9 張）

**全部為第三方影像，僅供本機開發測試，未取得再散布授權。**

### 2.1 YouTube 影片截圖（5 張）

由使用者於 2026-08-16 擷取自 YouTube 播放畫面。**畫面含播放器 UI、字幕與 letterbox 黑邊**
（這對影像模型有實測干擾，見 `output/depth/REPORT.md` §5 與 `output/seg/REPORT.md` §3）。

| 檔案 | 空間類型 | 影片標題（截圖畫面可見） | 出處備註 |
|---|---|---|---|
| `arena_ntsu_linkou.png` | 大型體育館／演唱會 | `[演唱會搶票必看!]林口體育館3樓座位視野導覽(黃藍橙A區)｜NTSU Arena 3F Full Seats View` | YouTube，頻道未記錄 |
| `livehouse_riverside_ximen.png` | 中型 Live House | `天高地厚/兩代吉他手CHRIS、力Q/感動合體/信樂團2026/3/21信念不滅音樂會/西門河岸留言` | YouTube，頻道未記錄 |
| `cgi_cave_lab_sophy.png` | CGI 洞窟實驗室 | `Sophy - This is Where I Begin` | YouTube，畫面右下有「奇瑚文創」浮水印 |
| `cgi_cavern_crowd_sophy.png` | CGI 巨型洞窟 | `Sophy - This is Where I Begin` | 同上 |
| `bedroom_ai_generated.png` | 臥室（住宅尺度） | 標題未擷取到 | **整張為 AI 生成影像**（使用者確認，畫面中人物非真人） |

> ❗ **待補**：以上 5 項的 YouTube 網址與頻道名稱尚未記錄。
> 任務卡 T-04 的自我檢查要求「SOURCES.md 每一項都有來源連結」，**這一節目前不符合**。
> 請使用者補上網址，或改用可自由授權的替代素材。

### 2.2 網路圖片（4 張）

由使用者於 2026-08-16 提供，補齊 T-04 要求但當時缺少的空間類別。

| 檔案 | 空間類型 | 出處 |
|---|---|---|
| `bathroom_tiled.png` | 磁磚浴室 | **未記錄**（研判為網路圖庫或建材商型錄照片） |
| `car_interior_suv.png` | SUV 車內後座 | **未記錄**（研判為車廠新聞稿／媒體試駕照片） |
| `stairwell_tiled.png` | 磁磚樓梯間 | **未記錄** |
| `corridor_hotel_carpet.png` | 飯店走廊 | **未記錄**；實測發現此圖有左右 letterbox 黑邊，可能同為影片截圖 |

> ❗ **待補**：以上 4 項來源網址與授權皆未記錄，同樣不符合 T-04 自我檢查要求。

> 📌 **2026-09-16 使用者決定**：不補來源網址——本專案非商業發行作品、僅供內部使用。依 T-04 裁決 E 第二路徑「明確維持未結案」處理；
> T-17-R2 REPORT 第 6 項須標明此缺項。§2.1／§2.2 的「待補」原文保留（不改寫歷史）。

> 📌 **2026-09-20 使用者決定（T-04 卡裁定 T-04-R，v2）**：照片重新提供——上列 9 張自此為**退役集**：v1 自檢「來源連結」**未達**的紀錄永久保留（§2.1／§2.2 原文不改），不再等補網址。
> 檔案已由 Codex（`ba1fcdb`）移到本機 `assets/photos_legacy_20260920/`（git 忽略；git 歷史 `14fc4ac` 仍有，**不得刪除備份**），只供內部回歸與重現歷史結果，不得對外發佈。
> T-04 的**現行交付集**＝`assets/t04_refresh/ASSET_MANIFEST.json` 所列 `assets/photos/t04_gpt_*.png`；其中四張與 §4 的 T-17-R2 held-out 逐位元相同（**共用圖禁用令**見裁定 T-04-R §2 第 4 點）。

### 2.3 覆蓋率對照（T-04 要求的 5 類）

| T-04 要求 | 對應檔案 | 狀態 |
|---|---|---|
| 浴室 | `bathroom_tiled.png` | ✅ |
| 客廳（居住空間） | `bedroom_ai_generated.png` | ✅（以臥室代替） |
| 教堂／大空間 | `arena_ntsu_linkou.png` | ✅（以體育館代替） |
| 樓梯間／走廊 | `stairwell_tiled.png`、`corridor_hotel_carpet.png` | ✅（兩張） |
| 車內 | `car_interior_suv.png` | ✅ |
| —（額外） | `livehouse_riverside_ximen.png`、`cgi_*` ×2 | ➕ |

> ⚠️ **已知缺口**：沒有任何一張是**真實的教堂／長殘響硬質大空間**
> （體育館那張有滿場觀眾，吸音特性與空場的教堂完全不同）。
> 這是 `output/seg/REPORT.md` §0 主動指出的素材缺口，Phase 1 驗收前應補。

---

## 3. `assets/reference_irs/` — 真實對照 IR + 場地照片（8 場地）

**媒體檔（.wav/.jpg）已加入 `.gitignore`，只有 INFO.md 進版控。**
每個場地資料夾的 `INFO.md` 內有完整的原始網址、檔案規格與授權分析，
照著網址即可自行重新下載。

### 3.1 來源變更說明（重要）

T-04 任務卡原本指定 **OpenAIR**（openairlib.net）。實際執行時發現：

```
https://www.openair.hosted.york.ac.uk/  → 轉到 suspendedpage.cgi
https://openairlib.net/                 → 轉到 suspendedpage.cgi
```

**兩個域名都已被主機商停權，站台實質關閉。** 經使用者同意後改用下列兩個替代來源。

### 3.2 EchoThief（5 場地）

- 網站：https://www.echothief.com/
- 作者：Dr. Chris Warren（San Diego State University）
- **授權**：網站**從未有過** License / Terms / FAQ 頁面（已查證首頁、WordPress REST API 全 73 頁、
  Wayback Machine 1077 筆歷史 URL、以及 EchoThief.zip 的中央目錄——壓縮檔內也無任何 LICENSE 檔）。
  唯一權利聲明為頁尾原文：

  > EchoThief Impulse Response Library – copyright 2013-2026 Dr. Chris Warren cwarren@sdsu.edu

  **結論：免費下載可用於本機研究，但未授予再散布權利。**
  公開發佈前須寫信至 cwarren@sdsu.edu 取得書面同意。

| 資料夾 | 空間 | 官網標註材質 | IR 長度 |
|---|---|---|---|
| `cathedral_room_shasta_lake_caverns` | 大型石灰岩天然洞窟 | Limestone, concrete. | 1.529 s |
| `steinman_hall` | 音樂廳（軟座椅、地毯） | Plaster, wood, upholstery, carpet. | 1.189 s |
| `racquetball_court_4` | 小型壁球場（全硬面） | Wood, glass. | 3.538 s |
| `tunnel_to_hell` | 要塞地下混凝土隧道 | Painted concrete. | 1.832 s |
| `divorce_beach` | 戶外沙灘岩礁 | Sand, sandstone, tears. | 0.979 s |

全部 44100 Hz / 立體聲 / 非靜音。

### 3.3 MIT Reverb Survey（3 場地）

- 網站：https://mcdermottlab.mit.edu/Reverb/IR_Survey.html
- 授權與引用要求詳見各場地 `INFO.md`
- 全部 32000 Hz / 單聲道

| 資料夾 | 空間 | IR 長度 |
|---|---|---|
| `mit_department_store` | 百貨公司 | 0.654 s |
| `mit_gym` | 體育館 | 1.368 s |
| `mit_restaurant` | 餐廳 | 0.306 s |

### 3.4 ⚠️ 場地照片有 5 張是 360° 環景（影響 Phase 1 架構）

| 場地 | 照片尺寸 | 型態 | 可直接餵給深度／分割模型？ |
|---|---|---|---|
| `steinman_hall` | 4096×2048 | 360° 環景 | ❌ |
| `divorce_beach` | 4096×2048 | 360° 環景 | ❌ |
| `cathedral_room_shasta_lake_caverns` | 960×480 | 360° 環景 | ❌ |
| `racquetball_court_4` | 960×480 | 360° 環景 | ❌ |
| `tunnel_to_hell` | 2592×1296 | 一般透視（iPhone 4） | ✅ |
| `mit_department_store` | 1920×1080 | 一般透視 | ✅ |
| `mit_gym` | 1920×1080 | 一般透視 | ✅ |
| `mit_restaurant` | 1920×1080 | 一般透視 | ✅ |

Depth Anything V2 與 SegFormer 都是用一般透視影像訓練，
等距長方投影（equirectangular）直接餵進去幾何會嚴重歪掉。

**影響**：SPEC §7 驗收標準第 2 條需要「拿場地照片跑管線 → 生成 IR → 與真實 IR 比 RT60」，
**8 個場地裡只有 4 個的照片能直接用**。

**但反過來是個機會**：SPEC §8 列的已知風險有一條「照片視野外的空間（背後的牆）未知」，
360° 環景根本沒有視野外——若 Phase 1 做「環景 → 多視角透視投影 → 融合」，
這條風險可以比 SPEC 原訂的「靠影片輸入 F-20 解決」更早被處理。
**此為架構決策，留給 T-08（Fable）。**

---

## 4. `assets/photos_heldout/` — T-17-R2 held-out 五類照片（等使用者提供；Opus 於 T-17-R2 步驟 1 填表）

用途：T-17-R2 §7-1 盲聽的 held-out 素材（未曾用於任何調參／標註／校準）。拍攝規格見 TASKS.md T-17-R2 卡「🔮 Fable 落地」§1。
逐面材質與大約尺寸由使用者於對話中確認，Opus 抄進 `assets/photos_heldout/ground_truth_heldout.json`（`confirmed_by: user`）。

| 檔案 | 類別 | 來源 | 授權 | 拍攝日 | 大約尺寸（L×W×H m，使用者估） |
|---|---|---|---|---|---|
| `heldout_bathroom.png` | 浴室 | AI 生成：GPT Image（Codex 內建 image_gen），依使用者要求，2026-09-20；提示詞 assets/t17r2_synthetic_candidates/PROMPTS.json；sha256 assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json | 無第三方影像輸入（純文字提示）；使用者委託生成；僅供專案內部使用 | （生成日）2026-09-20 | 2.4×1.8×2.5（設計值，非實測） |
| `heldout_living.png` | 居住空間 | AI 生成：GPT Image（Codex 內建 image_gen），依使用者要求，2026-09-20；提示詞 assets/t17r2_synthetic_candidates/PROMPTS.json；sha256 assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json | 無第三方影像輸入（純文字提示）；使用者委託生成；僅供專案內部使用 | （生成日）2026-09-20 | 5×4×2.7（設計值，非實測） |
| `heldout_hall.png` | 教堂／大空間 | AI 生成：GPT Image（Codex 內建 image_gen），依使用者要求，2026-09-20；提示詞 assets/t17r2_synthetic_candidates/PROMPTS.json；sha256 assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json | 無第三方影像輸入（純文字提示）；使用者委託生成；僅供專案內部使用 | （生成日）2026-09-20 | 24×16×8（設計值，非實測） |
| `heldout_corridor.png` | 樓梯間／走廊 | AI 生成：GPT Image（Codex 內建 image_gen），依使用者要求，2026-09-20；提示詞 assets/t17r2_synthetic_candidates/PROMPTS.json；sha256 assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json | 無第三方影像輸入（純文字提示）；使用者委託生成；僅供專案內部使用 | （生成日）2026-09-20 | 8×1.8×2.6（設計值，非實測） |
| `heldout_car.png` | 車內 | AI 生成：GPT Image（Codex 內建 image_gen），依使用者要求，2026-09-20；提示詞 assets/t17r2_synthetic_candidates/PROMPTS.json；sha256 assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json | 無第三方影像輸入（純文字提示）；使用者委託生成；僅供專案內部使用 | （生成日）2026-09-20 | 2.6×1.5×1.2（設計值，非實測） |

> 📌 **2026-09-20（T-17-R2 卡裁定 T-17-R2-S）**：本節素材改走「**路徑 S＝AI 合成圖**」——使用者指定採用 §6 的五張 GPT Image 合成圖；解析度下限改為長邊 ≥1280px（五張皆 1448×1086）。
> 上表由 **T-60** 就位時填寫（不是 T-17-R2 步驟 1）；「來源」欄依 T-04 卡裁定 T-04-R §2 第 3 點填 AI 生成圖的五項紀錄，「拍攝日」填生成日，「大約尺寸」填裁定寫死的設計值（僅供域內／域外分類，非實測）。
> 已揭露事項：五張同時是 T-04 現行開發素材的來源，且在 R2 前被分割／深度冒煙測試處理過；未用於調參／標註／校準。

> 📌 **2026-09-21（T-60）**：五張已就位於 `assets/photos_heldout/heldout_{bathroom,living,hall,corridor,car}.png`（自 `assets/t17r2_synthetic_candidates/` 以 `mv` 搬入；搬移前後 sha256 皆等於 `assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json`）。
> 逐面材質與設計尺寸＝`assets/photos_heldout/ground_truth_heldout.json`（`confirmed_by: user`；使用者 2026-09-21 逐張看圖確認，原話記於 TASKS.md T-60 卡交接筆記）；上表「大約尺寸」欄的數字是設計值、僅用於域內／域外分類，非實測。
> 解析度：五張皆 1448×1086、4:3，長邊 1448 ≥ 1280（裁定 T-17-R2-S 的下限）。
> 共用圖：`heldout_bathroom`／`heldout_living`／`heldout_corridor`／`heldout_car` 四張與 `assets/photos/t04_gpt_{bathroom,living,corridor,car}.png` 逐位元相同；`heldout_hall` 的複本在 `assets/photos_legacy_20260920/t04_gpt_hall.png`（本機、git 忽略）。共用圖禁用令（T-04 卡裁定 T-04-R §2 第 4 點）適用，解除前不得處理這些圖。
> T-04 v2「來源連結」五項（裁定 T-04-R §2 第 3 點）對應：① 生成工具名稱＝上表「來源」欄「GPT Image（Codex 內建 image_gen）」；② 生成日＝「拍攝日」欄 2026-09-20；③ 依誰的要求生成＝「來源」欄「依使用者要求」；④ 完整提示詞檔的 repo 內路徑＝「來源」欄 `assets/t17r2_synthetic_candidates/PROMPTS.json`；⑤ 逐張 sha256 清單的 repo 內路徑＝「來源」欄 `assets/t17r2_synthetic_candidates/ASSET_MANIFEST.json`。

---

## 5. 待辦

- [ ] 補上 `assets/photos/` 全部 9 張的來源網址（T-04 自我檢查要求，目前不符合）
- [ ] 補一張**真實的教堂／長殘響硬質大空間**照片（目前素材缺口）
- [ ] 若要公開發佈：處理 `assets/photos/` 第三方影像的授權，或全部替換

> 📌 **2026-09-20 補**：第一項與第三項改由「替換素材」處理（T-04 卡裁定 T-04-R），不再等補網址。第一項**永不勾**（舊 9 張＝v1 未達（來源缺）／v2 退役，依 WORKFLOW §7.6 永久列示）；第三項待 T-04 依 v2 經 Opus 驗證通過時，另起新行註記現況。
> 第二項**仍缺**——現行素材全為 AI 合成圖，沒有任何真實的長殘響大空間照片。

## 6. T-17-R2 合成候選圖（2026-09-20；非正式 held-out）

五張由本次內建 GPT Image 生成，見 `assets/t17r2_synthetic_candidates/README.md`、`PROMPTS.json` 與 `ASSET_MANIFEST.json`。無外部來源照片；尺寸設計不是實測真值。原檔皆 1448×1086，未達任務卡 1920px 下限，§4 的正式素材缺口仍保留。PNG 僅本機留存，本輪只提交來源與需求文件。

> 📌 **2026-09-20 補（同日稍後；上段原文保留）**：使用者下達標準變更後，解析度下限改為長邊 ≥1280px（T-17-R2 卡裁定 T-17-R2-S），五張 1448×1086 自此**合格**，並由使用者指定為 T-17-R2 正式 held-out（路徑 S）。
> 上段「未達 1920px 下限」「PNG 僅本機留存」是舊門檻下的如實紀錄；五張將由 **T-60** `mv` 到 `assets/photos_heldout/` 並進版控，來源紀錄填入 §4。
