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

- [ ] T-10 專案骨架 + 影像前處理（letterbox 裁切、環景偵測與投影、HEIC 支援）
- [ ] T-11 幾何估計模組（metric depth → 房間尺寸/體積，內建已知場地評測關卡、手動覆寫）
- [ ] T-12 材質模組（表面分割 + 二階材質分類 → **逐表面**吸音係數；修好「鐵筒子」缺陷後重試聽）
- [ ] T-13 聲學參數計算（Sabine/Eyring → **逐頻段** RT60、pre-delay）
- [ ] T-14 IR 合成引擎 v1（image-source 早期反射 + 分頻段 shaped-noise 晚期殘響）
- [ ] T-15 CLI 整合（照片 → IR WAV + 分析報告 JSON，含手動覆寫參數）
- [ ] T-16 分析視覺化（材質疊圖、深度圖、RT60 頻段圖、警示標示）
- [ ] T-17 **驗收**：SPEC §7 四項標準（含人耳試聽環節，Opus 主導）

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
