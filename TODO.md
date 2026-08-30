# To-Do

> 執行用的任務卡在 [TASKS.md](TASKS.md)，協作規則在 [WORKFLOW.md](WORKFLOW.md)。
> 本檔案只放高層狀態總覽。

## 進行中

- [ ] **Phase 1：MVP（照片 → IR 匯出）** — T-10 ✅ / T-11 ✅ / T-12 ✅ / T-13 ✅ /
      **T-14 ✅**（Opus 驗證 2026-08-28；⚠️ 尺度上限已由 T-22 修正）
- [x] **Phase 1.5：場景描述與複合場景（2026-08-27 使用者需求新增）✅ 全數完成
      （2026-08-28）** — **T-20 ✅**（Opus 驗證 2026-08-28）/ **T-21 ✅**
      （Opus 複驗 2026-08-28，新視窗：v3 對照組由 Opus 自己重建、缺陷原貌重現，
      巨蛋 2k/4k 由 −94%/−93% 收斂到 −13.2%/−17.0%，閉環警示機制接上，
      乾淨 clone 4 檔 MD5 相同，17＋23 項測試全過）/ **T-22 ✅**（Opus 驗證 2026-08-28；
      T-14 引擎尺度自適應：早期窗改依幾何動態計算、40–200m 尺度掃描 2k/4k 誤差
      全部收斂到 ≤25%，4×3×2.5／30×20×12 兩條交付 IR MD5 零回歸，
      新增能量匹配窗縱深防禦警示）
- [x] **Fable 重新規劃（2026-08-30）✅ 完成** — HANDOFF 第 0 節 A~F 六項全數裁決：
      T-15/T-16/T-17 卡改版、新增 T-18（驗收前置）、§7-2 低頻判準事前裁決
      （125/250Hz 改 88–354Hz 聯合帶 <20%，證據鏈見 TASKS.md T-17 卡裁決 B）、
      T-17 達標率依 dims_source 分組、ROADMAP 勾選同步
- [x] **T-15 CLI 整合 ✅ Opus 驗證通過（2026-08-30）** — 三種輸入互斥統一入口；
      乾淨 shell 重跑，MD5 六條零回歸全中（T-14/T-20/T-21）且新 CLI 與獨立腳本
      同輸入逐位元相同；warnings/notes 分流經「所有下修 confidence 的訊息」逐條
      對抗檢查無誤判；互斥 5 種組合、11 種壞輸入全實測；37 個 WAV 全過 check_audio。
      技術債 #1/#2/#5 收斂＋T-20 三條非阻斷建議落地。附 4 項非阻斷建議給 T-16/T-17。
- [x] **T-16 分析視覺化 ✅ Opus 驗證通過（2026-08-30）** — 三種輸入各自的拼版
      `analysis.png`（照片：原圖／分割疊色圖／深度圖／RT60／文字欄／警示；
      文字：preset＋假設值／六面材質表／RT60／警示；複合場景：逐空間 RT60／
      路徑列表／警示）；預設產生、`--no-viz` 可關。乾淨環境重跑 14 次全 `exit 0`；
      攔截 matplotlib figure 逐值比對，**96 根 bar 高度與 JSON 誤差 0**；地雷 #15
      過關（標紅根數 == `within_tolerance=False` 個數，五個輸出全中）；材質覆寫
      實測證實標籤走 `analysis['surfaces']` 非模型重跑結果（無假實作）；
      MD5 零回歸 mono＋stereo 兩條逐位元相同。附 4 項非阻斷建議給 T-17。
- [x] **T-18 驗收前置 ✅ Opus 驗證通過（2026-08-30）** — 新增 `t30_low_combined()`
      （88.4–353.6Hz 低頻聯合帶 T30，純新增、既有函式 diff 刪除行數 0）；
      `test_t30_low_combined.py` 解析構造校驗；`check_audio.py`／`test_segmentation.py`
      退出碼修正。Opus 乾淨環境重跑＋**自建獨立量測實作交叉複驗**（掃 0.3–5.0s 五組，
      誤差 −2.3%～+1.7%）＋裁決 B 混頻機制獨立重現（逐頻段 125Hz +105%）＋
      六條交付 IR MD5 自己重生比對零回歸。附 4 項非阻斷觀察給 T-17。
- [x] **T-17 MVP 驗收 🔵 Opus 已執行（2026-08-30）** — §7-2 完成且**明確未達標**
      （自動幾何組 22%／0-8 場地、手動組 20%／0-5）。**病因已隔離：在材質辨識，
      不在幾何也不在合成引擎**（壁球場同一引擎只換材質即從 −50% 翻成 +13%）。
      新發現三個缺陷（`is_equirect()` 把 2:1 透視照誤判成環景＝地雷 #16、
      `--override-dims` 一律給 `high`＝地雷 #17、戶外無拒絕出口）。
      報告：`output/mvp_acceptance/REPORT.md`
- [x] **§7-1／§7-3／§7-4 使用者回饋已完成（2026-08-30）** — §7-1 **2/5 未達標**
      （體育館聽成車內、臥室聽成教堂＝**管線把大小做反了**，使用者的耳朵每題都對）；
      §7-3 **✅ 通過**（可載入、有殘響）；§7-4 **無鐵筒子 artifact**，壁球場材質
      判錯 vs 改對「有差異」→ 耳朵獨立佐證病因診斷，聽感說還應再少 1–1.5 秒
      （與量測 +0.71~+2.16s 同方向同量級）
- [ ] **📷 補齊 9 張照片來源網址**（`assets/SOURCES.md` §2）——裁決 E 的結案前置，
      補齊前 T-17 狀態不得改 ✅
- [x] **外部 bug 診斷五條已查證屬實（2026-08-30）** — ADE 可信材質分支是 dead behavior
      （且計分用全圖比例，補個 if 就啟用會引入新錯誤）、pipeline 無輸出 gate、
      fallback 四處說法不一致、我自己的 `t17_blind_test.py` 可接受舊產物（**已修並實測**）。
      → HANDOFF 地雷 #19–#22、REPORT §2.6
- [x] **Phase 1.6 修正輪（T-23→T-24→T-25→T-26 依序，Opus 2026-08-30 規劃）✅ 四張全過**：
      **T-23 ✅ 通過**——fallback 材質單一事實來源，`materials.json`
      的 `fallback_id` 改成 `gypsum_board`（現行實際行為）、`config.py` 改成動態讀取、
      新增 `test_material_fallback.py`。
      **T-24 ✅ 通過（Opus 驗證，第三輪）**——`ADE_TRUSTED_MATERIAL`
      整張表與不可達的計分區塊已從 `surfaces.py` 刪除，三處誤導性註解改寫成
      描述現況，`test_surface_trusted_scope.py` 改成斷言「屬性不存在＋note 不再
      提語意可信」的不變量測試；七套測試全過、六條 MD5 零回歸。
      **T-25 ✅ 通過**——`analysis.json` 的 `confidence` 拆成
      `geometry_confidence`／`materials_confidence`／`confidence`(overall＝取
      較低者) 三軸，只動照片管線 `run_photo()`；臥室實測 confidence 由
      medium→low（材質是 fallback，舊行為看不出來）、`--override-dims` 不再
      整體誤標 high；`ir_mono.wav` MD5 改動前後相同。新增
      `test_confidence_axes.py`（11 項）。
      **T-26 ✅ 通過**——`run_photo()` 在 T-13 聲學計算之前加
      gate：overall confidence 為 `low` 就擋下（不寫任何 WAV／JSON，exit 3），
      新旗標 `--force-low-confidence` 是唯一出口（帶了照樣輸出，JSON 標記
      `forced_low_confidence: true`）；`--override-dims` 不會自動解除 gate。
      實測發現現行 9 張 `assets/photos/` 全部 overall=low（素材庫現實限制，
      非本卡回歸），已用 override 組合人工建構真正的 medium 案例佐證該路徑
      MD5 不受影響。新增 `test_output_gate.py`。
- [x] **T-23 fallback 單一事實來源 ✅ 通過**（Opus 驗證，六條 MD5 全數不變）
- [x] **T-24 ADE 可信材質分支清理 ✅ 通過**（Opus 驗證第三輪，六條 MD5 全數不變）
- [x] **T-25 confidence 拆三軸 ✅ 通過**（Opus 驗證，六條 MD5 全數不變）
- [x] **修正輪四張卡全部完成 ✅**（T-23/T-24/T-25/T-26 皆 Opus 驗證通過；
      規劃者另做獨立複驗：九支測試套件全 exit 0、六條交付 IR MD5 零回歸、
      gate 實測體育館 exit 3 且輸出目錄完全沒被建立、臥室 medium→low 且 IR MD5 未變）
      - T-24 依裁決 T-24-A 移除不可達死碼：可信類別 id 與角色 id **交集為 ∅**，
        在 ADE20K 一像素一 label 的前提下**永遠不可達**，非漏寫；清單搬去 T-27
- [x] **🔮 T-28 已裁決（Fable 裁決 T-28-A，2026-08-30，零信用複驗後）**：
      裁決前 Fable 親自重跑 13 張，**更正原卡三處數據**（materials=low 是 12/13
      非 13/13——DivorceBeach 是被 geometry 擋的；「fallback 10／ood 5／clip 12 面」
      單位其實是照片張數，真實面數分布為 fallback 32／ood 13／clip 22／無來源 11；
      修好材質規則仍有 6/13 被 geometry=low 擋）。裁決：**規則不動**（實測不可能性
      證明：臥室與浴室六面「材質＋來源」逐面相同，任何來源規則放浴室必放臥室，
      而臥室必須擋）；**修出口開 T-30**（gate 擋下時逐面點名 fallback/ood 面＋
      給可複製的 `--override-material` 指令——實測這是唯一可行的非 force 出口，
      現有訊息卻只提走不通的 `--override-dims`）；**準確度先行**（材質輪後用新
      基準率複測再談調規則）。另記 HANDOFF 地雷 #23/#24（無來源第四狀態；
      透視照 materials high 結構性不可達）。全文見 TASKS.md T-28 卡尾。
- [x] **🔮 T-27 已裁決（Fable 裁決 T-27-A，2026-08-30）**：採「逐頻段等效吸音面積」
      （Sabine A 的加項，經 `rt60_bands_sabine` 流進 IR 晚期尾巴），不採 occupancy
      係數（寬頻單一旋鈕＝重犯地雷 #8，且無現成物理插入點）。資料源＝ADE20K 陳設
      類別全圖像素佔比，類別 id 與六角色 id 不相交、rug／玻璃鏡面排除。
      全文見 TASKS.md T-27 卡。
- [ ] **Phase 1.7 材質修正輪（Fable 規劃 2026-08-30，卡片在 TASKS.md 檔尾）**：
      **T-31 ✅ 通過**（Opus 驗證 2026-08-30；陳設資料表＋偵測模組。卡片指定的
      `data/furnishings.json` source 文件修正已於 2026-08-30 補完並以獨立的
      `T-31: 驗證通過` commit 提交——curtain.source 描述改為中量級 14 oz/yd² 天鵝絨，
      curtain／seat 兩筆的精確書目點名退回卡片原本要求的通用寫法，α 數值不變，
      十套測試 exit 0）→ **T-32 ✅ 通過**
      （Opus 驗證 2026-08-30；`compute_acoustics()` 加 `furnishings` 參數＋
      `--no-furnishings` 旗標，furnishings=None 時逐位元不變。驗證者在乾淨工作區
      重跑十套測試 exit 0、六條交付 IR MD5 零回歸、None 分支交付 JSON 重生 diff 為空、
      gate 判定零改動；另以變異測試證實「只加 Sabine 不加 Eyring」會被 F3 抓到。
      ⚠️ 帶給 T-33 的輸入：`livehouse_riverside_ximen.png` 加陳設後 RT60 跌到 0.08s，
      跌破 WORKFLOW §5 的 0.1s 合理性下限——cap=0.5 偏鬆的證據，量測時要一併記錄）→
      T-33 ⬜（13 張基準率複測量測卡，通過後回 Fable 複評 gate 規則與 cap 值）→
      T-34 ⬜（gate 訊息規則 2 死路出口＋測試補洞）。共同紅線：gate 判定規則
      零改動、六條交付 IR MD5 不變、陳設資料不得餵進信心軸。
- [x] **T-30 gate 出口導引 ✅ 通過（Opus 驗證 2026-08-30）**：
      只改 `pipeline.run_photo()` gate 觸發後印的訊息——逐面點名 fallback/ood
      面（無來源面／clip 面不列）、依軸分開給建議（geometry=low 才印
      `--override-dims`；materials=low 才印可直接複製的 `--override-material`
      指令骨架）、`--force-low-confidence` 文案標明不建議當常規路徑。
      gate 判定條件（`compute_materials_confidence()`／`run_photo()` 觸發放行
      邏輯）逐行未動；九套測試全 exit 0；六條交付 IR MD5 逐一重生比對逐位元
      相同；實跑 `bathroom_tiled.png` 驗證訊息內容與 gate 解除路徑皆符合預期。
      新增 `test_output_gate.py` 案例【D】。卡片見 TASKS.md T-30。
      **Opus 驗證通過**（九套測試／四條 MD5／`bathroom_tiled` 自我檢查全部親跑複現，
      新斷言在 HEAD~1 worktree 上實測 4 項失敗＝有診斷力）。附兩則後續建議：
      ①「規則 2 退化（六面全同、無 fallback 面）＋geometry 非 low」時訊息仍只剩
      `--force-low-confidence`，死路未被本卡覆蓋——屬卡片規格邊界，需 Fable 另開卡；
      ② `geometry=low` 印 `--override-dims` 的分支無測試覆蓋（【A】是 high、【D】是 medium），
      建議補正向案例。下一步：Fable 裁決 T-27（室內陳設吸音）。
- [ ] **T-29**：三軸信心只加在 `run_photo()`，`--text` 只有 `confidence`、
      `--scene` 連 `confidence` 都沒有；三條管線 schema 不一致要有意識地決定
- [ ] **← 之後（Fable）**：§7-1＋§7-2 皆未達標，要不要再加一輪。
      ⚠️ **範圍要先定清楚：只打材質不足以修好 §7-1 的 sample_1（幾何量程）與
      sample_2（域外輸入）**——這是本報告首版概括過頭、現已更正的地方。
      **T-17 數據建議打材質、不要打幾何**（手動組 20% 沒有比自動組 22% 好，
      不支持優先換 Metric-Indoor-Large；且 §7-1 與 §7-2 兩條獨立證據鏈都指到材質）。
      另有新議題：**`confidence: low` 要不要升級成「拒絕輸出／強制手動尺寸」**
      ——體育館與車內的防呆都正確作動了，產品仍輸出聽起來是別的空間的 IR，
      降信心不等於保護使用者

## ✅ T-11 路線決策結果（2026-08-25，Fable）

- [x] **b 為主幹**：自動幾何適用範圍明訂「一般室內、估計最大尺寸 ≤ 10m」
      （模型量程實證 ~20m 天花板、天花板前就開始壓縮；門檻進 `config.GEOMETRY_SCOPE_MAX_M`）
- [x] **c 為正式出口**：範圍外 → `confidence: low` ＋可操作警示，手動尺寸（F-09）承接
- [x] **d 保留**：環景仍是大空間的建議輸入（量程規則獨立：單面牆距 >10m 才降 low）
- [x] **a 延後**：換 Metric-Indoor-Large 留待 T-17 驗收後再評估
- [x] **e 拒絕**：±30% 判準與所有門檻一個字都沒改，改的是適用域
- [x] SPEC 升 v0.3、ROADMAP 更新、T-11 卡加補丁步驟 7–9、T-13 卡解除封鎖＋地雷 #14 入卡
- [x] **（補充裁決 2026-08-27）Steinman 翻 low 屬規則正確行為**：原「單面牆距未超標」是
      總長÷2 粗估錯誤；規則不改，對照組語句修正。環景解「視野外」不解「量程」。SPEC 升 v0.3.1

## ✅ T-08 決策結果（2026-08-16，Fable）

- [x] **深度路線**：改用 **metric depth 模型**（Depth-Anything-V2-Metric-Indoor）；
      參考物尺度降為校驗用；手動尺寸覆寫升 P0；T-11 內建評測關卡（不達標即停）
- [x] **材質路線**：**併用**——ADE20K 分割只管幾何角色，材質標籤交給 CLIP zero-shot
      二階分類器＋信心 gating；`floor`/`wall` 語意不再採信
- [x] **環景**：**做，最小範圍**——equirect→多視角透視投影進 T-10 前處理，
      驗收場地 4 個 → 8 個全可用，順便提前解掉「視野外」風險
- [x] 兩條硬約束已寫進任務卡：**逐表面材質 → T-12 步驟 2**、**逐頻段 RT60 → T-13 步驟 2**
- [x] IR 生成路線維持 A+B 混合（人耳已確認鏈路可用）；SPEC 升 v0.2、ROADMAP 同步更新

## 等使用者（AI 推不動）

- [x] 🎧 ~~試聽 T-14 的 3 個檔案~~ **✅ 已完成（2026-08-27）：「目前聽起來 OK」**
- [x] 🎧 ~~試聽 T-20 的 2 個檔案~~ **✅ 通過（2026-08-27 第二輪）：「沒有問題」**
- [x] 🎧 ~~第三輪試聽 T-21 的 2 個檔案（v3）~~ **✅ 通過（2026-08-27）：「確認OK」**
- [x] 🎧 ~~第四輪重聽 T-21 的 2 個檔案（v4，修引擎後）~~ **✅ 通過（2026-08-28）：「聽起來沒問題」**（v3 的 OK 是對高頻晚期殘響
      缺失的 IR 給的，不能沿用——這輪重聽是必要的）
- [ ] 🎤 （建議）提供一段**真實說話聲乾聲**放 `assets/dry/`——隔壁人聲情境用拍手
      示範不出「講話聲」的感覺，有真實乾聲後重跑 `gen_ir_coupled.py` 更有感
- [ ] 📷 補上 `assets/photos/` 9 張照片的來源網址（T-04 自我檢查第 2 項，目前不符合）
- [ ] 📷 補一張**真實的教堂／空場硬質大空間**照片（目前所有大空間樣本都被人群主導，
      無法驗證長殘響情境）
- [ ] ❓ T-07 Image2Reverb baseline 要不要做？（限時 2h、2021 舊專案、失敗是可接受結果）
- [ ] 📷 **（新）補一張小房間的 360° 環景照片** — 環景路徑目前沒有「範圍內維持 medium」
      的防濫殺對照案例（唯一的 Steinman 實測超標）；沒有就留待 T-17 間接檢驗

## 待處理

- [ ] 小修（T-11 Opus 驗證建議，不阻擋）：`--override-dims` 與 `--geometry` 寫同一個
      `geometry.json`，後跑的會蓋掉先跑的（REPORT §7 照順序跑完，佐證檔會停在 manual 版）
      → §7 調換順序或手動結果另存檔名；docstring 補一句 manual 路徑豁免量程規則
      （**量程規則預設放行的部分已於 2026-08-30 併進 T-15 步驟 5**）
- [ ] 小修（T-10 殘留，不阻擋）：非環景裁切後若長寬比落回 2:1 容差內就印警告
      （防「帶外框的環景圖被靜默當一般照片」）；`view_el+45.png` 檔名去掉 `+`；
      可變物件當預設參數；傳目錄時的錯誤訊息語意
- [ ] **T-15 → T-16 → T-17（依序）；T-18 不依賴 T-15/T-16 可隨時插入，T-17 前必過**
      （2026-08-30 Fable 重排）
- [ ] T-07（選做）Image2Reverb baseline
- [x] ~~小修：錯誤處理一致性（check_audio exit 2、test_segmentation exit 1）~~
      **已於 2026-08-30 開卡收斂 → T-18 步驟 3/4**

## 已完成

- [x] **T-13 聲學參數計算（Sabine/Eyring 逐頻段 RT60 + pre-delay）✅ Opus 驗證通過（2026-08-27）**
      — 約束 B 經數值對抗確認（禁忌值 0.267s 不存在於任何輸出欄位）；空氣吸收開/關實測
      大空間 4kHz −35.3%、小空間 −8.5%；12 個頻段數字經驗證者獨立手算逐位一致
- [x] **T-12 材質模組（逐表面材質 + 兩階段辨識）✅ Opus 驗證通過（2026-08-25）**
      — per-wall 實測進 pra 內部、獨立 T30 量測證實鐵筒子特徵消失（49.0→1.1 倍）
- [x] 🎧 **「鐵筒子」缺陷結案（2026-08-18 使用者實聽確認）** — 逐表面材質修復，
      125Hz T30 3.95s→0.75s、低/高頻比 48.8→1.27 倍，聽感與數據一致
- [x] **T-10 專案骨架與影像前處理（含 equirect→6 視角投影）✅ 通過**
      — 曾因前處理順序反了被退回，修正後經 Opus 複驗（迴歸測試對舊碼實測會失敗）
- [x] **T-08 Phase 0 總結與路線決策（Fable）✅ 完成** — 三決策定案、SPEC v0.2、
      ROADMAP 更新、Phase 1 八張卡細化（含 A/B 兩條硬約束入卡）
- [x] T-06 語意分割測試（SegFormer ADE20K，9 張，42 類→材質對照表）✅ 驗證通過
- [x] T-05 深度估計測試（Depth Anything V2，9 張）✅ 驗證通過 — 產出關鍵負面結論
- [x] T-04 測試素材與對照 IR（9 張照片 + 8 組真實 IR）✅ 通過（照片來源連結待補）
- [x] T-03 材質吸音係數表（12 種材質 + `--material` 選項）✅ 驗證通過
- [x] T-02 離線卷積試聽工具（`convolve.py` + `wet_demo.wav`）✅ **完全通過**（使用者試聽確認殘響自然）
- [x] T-01 用手動參數生成第一個 IR（small / hall 兩組 preset）✅ 驗證通過
- [x] T-00 建立開發環境 ✅ 驗證通過
- [x] 建立專案基礎文件（README, ROADMAP, TODO, DEV_LOG, .gitignore）
- [x] 確立專案願景：照片/影片 → AI 空間與材質分析 → IR 生成 → Convolution Reverb
- [x] SPEC v0.1、RESEARCH 調查、ROADMAP Phase 0–3
- [x] 建立多視窗協作系統（CLAUDE.md / WORKFLOW.md / TASKS.md）
