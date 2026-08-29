# Roadmap

規格詳見 [SPEC.md](SPEC.md)，相關研究調查見 [RESEARCH.md](RESEARCH.md)。

## Phase 0 — 研究與可行性驗證 ✅（2026-08-16 完成，T-08 結案）

目標：確認「照片 → 可聽的 IR」整條路走得通，選定 MVP 的 IR 生成路線。

- [ ] ~~跑通 Image2Reverb baseline~~ ⏸️ 暫緩（T-07 選做，使用者未授權下載；不擋 Phase 1）
- [x] 測試單目深度估計 → **🔴 否定性結論**：相對深度不能估房間體積（`output/depth/REPORT.md` §7）
- [x] 測試語意分割 → **🔴 否定性結論**：ADE20K 的 `floor`/`wall` 材質語意不可信、車內無對應類別（`output/seg/REPORT.md`）
- [x] 建立材質 → 各頻段吸音係數對照表（12 種材質，`data/materials.json`）
- [x] 用 pyroomacoustics 手動參數生成 IR + 卷積試聽 → **使用者人耳確認整條鏈路可用**（T-02）
- [x] 建立「同場地照片 vs 真實 IR」評測集 → OpenAIR 已停站，改用 EchoThief + MIT Reverb Survey（8 場地）
- [ ] 細讀 AV-RIR 與 Differentiable Room Acoustic Rendering（2025）→ 移到 Phase 1 期間補
- [x] **決策點（T-08，2026-08-16 定案）**：
  1. IR 生成維持 **A+B 混合**（image-source 早期 + shaped-noise 晚期）——Phase 0 試聽已驗證此路線可聽
  2. 深度改 **metric depth 模型**（Depth-Anything-V2-Metric-Indoor），參考物尺度降為校驗用，手動覆寫升 P0
  3. 材質改 **兩階段**：分割管幾何角色、CLIP zero-shot 二階分類器管材質標籤，逐表面指定
  4. **環景支援納入 Phase 1 前處理**（equirect→多視角透視投影），解鎖 8 個驗收場地並提前處理視野外風險

## Phase 1 — MVP：照片 → IR 匯出（SPEC F-01 ~ F-09）← 現在

目標：CLI 工具，輸入照片、輸出可用的 IR (WAV)。任務卡 T-10~T-17 見 [TASKS.md](TASKS.md)。

- [x] T-10 專案骨架 + 影像前處理（letterbox 裁切、環景偵測與投影、HEIC 支援）✅ 通過（Opus 複驗 2026-08-18）
- [x] T-11 幾何估計模組（metric depth → 房間尺寸/體積，內建已知場地評測關卡、手動覆寫）✅ 通過（Opus 驗證 2026-08-27）
      — 🔮 **評測關卡卡關後 Fable 定案（2026-08-25）**：模型量程實證 ~20m 天花板，
      自動幾何適用範圍明訂 ≤10m；範圍外強制 low confidence ＋警示，出口為手動尺寸（F-09）
      或環景輸入；換 Metric-Indoor-Large 延後至 T-17 驗收後再評估（若屆時產品體驗不可接受）。
      補丁已執行（2026-08-26）；Steinman 對照組卡關經 Fable 裁決結案（2026-08-27）：
      **環景解「視野外」、不解「量程」**，單面牆距超標的環景場地正確地標 low。
      詳見 TASKS.md T-11 卡「Fable 路線決策」「Fable 裁決」、SPEC v0.3.1
- [x] T-12 材質模組（表面分割 + 二階材質分類 → **逐表面**吸音係數；「鐵筒子」缺陷已修並經人耳確認）✅ 通過（Opus 驗證 2026-08-25）
- [x] T-13 聲學參數計算（Sabine/Eyring → **逐頻段** RT60、pre-delay）✅ 通過（Opus 驗證 2026-08-27）
- [x] T-14 IR 合成引擎 v1（image-source 早期反射 + 分頻段 shaped-noise 晚期殘響）✅ 通過（Opus 驗證 2026-08-28；尺度上限由 T-22 解除）
- [ ] T-15 CLI 整合（**照片／文字／複合場景三種輸入互斥** → IR WAV + 分析報告 JSON，
      含手動覆寫、warnings/notes 分流、技術債收斂、交付 IR MD5 零回歸判準）
      — 🔮 卡片已於 2026-08-30 由 Fable 依 Phase 1.5 後實況改版
- [ ] T-16 分析視覺化（材質疊圖、深度圖、RT60 頻段圖、警示標示；文字/複合場景另有拼版）
- [ ] T-18 驗收前置（低頻聯合帶量測工具＋退出碼技術債；不依賴 T-15/T-16，T-17 前必過）
- [ ] T-17 **驗收**：SPEC §7 四項標準（含人耳試聽環節，Opus 主導）
      — 🔮 **§7-2 低頻判準已事前裁決（2026-08-30，Fable）**：500Hz–4kHz 逐頻段 <20% 不變；
      125/250Hz 門檻改為 88–354Hz 聯合帶 T30 <20%（逐頻段數字照列、超差照警示，只是不當門檻）。
      理由與證據鏈見 TASKS.md T-17 卡裁決 B。達標率依 dims_source 分組統計（裁決 C）；
      照片來源網址為結案前置（裁決 E）

## Phase 1.5 — 場景描述輸入與複合場景（SPEC F-16 ~ F-17）✅（2026-08-28 全數結案）

目標：不用照片也能產 IR（文字描述），並支援「聲源與聽者在不同空間」的複合場景。
兩者都掛在既有中間表示之上，照片管線不改。任務卡 T-20/T-21/T-22 見 [TASKS.md](TASKS.md)。

- [x] T-20 文字場景描述 → IR（13 種 preset + 關鍵字/參數解析；認不得就報錯列清單）
      ✅ 通過（Opus 驗證 2026-08-28；使用者試聽「沒有問題」）
- [x] T-21 複合場景引擎 v1（路徑串接 + `data/transmission.json` 傳輸損失表；
      示範場景＝巨蛋→走廊、隔壁人聲三路徑）✅ 通過（Opus 複驗 2026-08-28；
      人耳共四輪：v1 退回 → v2 退回 → v3 OK → 修引擎後 v4 OK）
- [x] T-22 T-14 引擎尺度自適應（計畫外新增：T-21 退回時定位到引擎固定 90ms 早期窗
      在 80–120m 跨臨界尺度失效且全程無警示——巨蛋 2k/4k −94%；改為依幾何動態計算，
      驗證至 200m 級、小/中房間 bit-identical 零回歸）✅ 通過（Opus 驗證 2026-08-28）

## Phase 2 — 即時效果器（SPEC F-10 ~ F-15）

目標：可在 DAW 中使用的 AU/VST3 plugin（macOS 優先）。

- [ ] JUCE 專案架構、partitioned convolution 零延遲引擎
- [ ] 參數組：Wet/Dry、Gain、Pre-delay、Size、Damping、EQ
- [ ] Python 管線整合方案定案（ONNX/CoreML 內嵌 vs local service）
- [ ] Plugin 內照片載入 UI 與分析視覺化
- [ ] IR 庫瀏覽器（內建 preset + 使用者生成）
- [ ] Stereo IR（decorrelation）
- [ ] AU / VST3 打包與 DAW 相容性測試

## Phase 3 — 進階功能（SPEC F-20 ~ F-23）

- [ ] 影片輸入：多幀融合（參考 AV-RIR）。環景輸入已在 Phase 1 解掉「視野外」的一部分，
      影片輸入的價值改為：一般透視照的視野外補全、鏡頭移動時的動態空間
- [ ] Positioner：空間內移動音源（動態早期反射）
- [ ] 神經 IR 生成路線：以聲學參數為條件的生成模型（RESEARCH §2）取代 shaped-noise
- [ ] 空間類型 preset IR 庫（音樂廳、教堂、浴室、車內…）
- [ ] Windows 支援

## 長期願景

- [ ] 即時影片串流 → 動態空間模擬
- [ ] 使用者社群 IR 分享
- [ ] 行動裝置版本（拍照即得該空間 Reverb）
