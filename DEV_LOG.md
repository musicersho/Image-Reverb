# Dev Log

## 2026-08-16 (5)

- 用多 agent workflow 一口氣跑完 T-01／T-02／T-03，每張卡配獨立驗證者依 WORKFLOW §5 三層標準
  親自執行指令審查。三張卡都 **0 修正輪直接通過**，另加一輪跨任務總稽核。
- T-01：`gen_ir_manual.py`，small RT60 0.219s／hall 4.55s，48kHz/24bit/mono、峰值 -3dBFS。
  反造假交叉驗證：直達音到達時間 vs 幾何理論值誤差 < 0.4ms，確認 IR 真的來自房間模擬。
- T-02：`convolve.py` + 合成乾拍手 + `wet_demo.wav`（10.437s，無爆音）。乾濕比實證有效
  （mix=0 尾段 RMS 0.0、mix=1 為 0.00069906）。
- T-03：`materials.json` 12 種材質、72 個 α 全在 0–1，係數對照建築聲學標準表抽查正確，
  `--material` 選項可用（marble RT60 6.40s，是預設的 29 倍）。
- 總稽核抓到 4 個錯誤處理缺陷（壞輸入吐 traceback），另開一輪修正 + 複驗，PASS。
  順帶修掉 T-00 `check_audio.py` 的死分支 bug（`except FileNotFoundError` 永遠抓不到，
  因為 soundfile 拋的是 `LibsndfileError`），並把過寬的 `except Exception` 收窄。
- T-00 驗證通過。**Phase 0 卡在 T-04**：需要使用者提供照片、並同意下載 OpenAIR IR 與 AI 模型。

## 2026-08-16 (4)

- T-00 完成（Sonnet 執行，狀態改為 🔵 待驗證，待 Opus 審查）。
- 建立 `.venv/` 虛擬環境，安裝 numpy/scipy/soundfile/matplotlib/pyroomacoustics/pillow，
  `pip freeze > requirements.txt`（19 個套件）。
- 建立 `assets/photos/`、`assets/dry/`、`assets/reference_irs/`、`output/`、`scripts/` 資料夾。
- 新增 `scripts/check_audio.py`：印出音訊檔取樣率/長度/聲道數/RMS/峰值，近乎靜音會警告，
  無參數印用法說明，檔案不存在給清楚錯誤訊息。
- `.gitignore` 新增 `output/`。自我檢查兩項皆通過。

## 2026-08-16 (3)

- 建立多視窗協作系統：Fable 規劃 / Opus 驗證 / Sonnet 執行。
- 新增 CLAUDE.md（每個視窗自動載入的角色說明與規則入口）。
- 新增 WORKFLOW.md（三種標準 Prompt、收工程序、Commit 時機、三層驗證標準與造假紅旗）。
- 新增 TASKS.md（Phase 0 任務卡 T-00~T-08 可無腦執行；Phase 1 框架 T-10~T-17 待 T-08 細化）。
- TODO.md 改為高層總覽，執行細節移至 TASKS.md。

## 2026-08-16 (2)

- 調查 GitHub 上的類似專案，結論：「照片→IR」有學術實作（Image2Reverb ICCV 2021、
  AV-RIR CVPR 2024 等）但無產品級工具 → 整理為 RESEARCH.md。
- 撰寫 SPEC.md v0.1：功能需求（F-01~F-23）、非功能需求、系統架構、
  材質吸音係數表規劃、驗收標準、風險。
- 更新 ROADMAP：各 Phase 對應 SPEC 功能編號，Phase 0 加入具體研究項目與決策點。
- 暫定 MVP IR 生成路線：image-source 早期反射 + shaped-noise 晚期殘響（A+B 混合）。

## 2026-08-16

- 確立專案願景：做一個空間模擬 Reverb 效果器（對標 Altiverb 8），但 IR 不靠實地錄製，
  而是由 AI 從照片/影片分析空間幾何與材質後自動生成。
- 研讀 Altiverb 8 手冊，確認其核心為 convolution reverb（IR 卷積）。
- 更新 README（系統架構、三條 IR 生成路線）、ROADMAP（Phase 0–3）、TODO。
- 決策：MVP 先做「照片 → IR (WAV) 匯出」，用現有 convolution reverb 驗證品質，
  之後再做 JUCE plugin。

## 2026-08-05

- 建立專案 repo 並初始化基礎文件（README, ROADMAP, TODO, DEV_LOG, .gitignore）。
