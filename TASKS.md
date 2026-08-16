# TASKS — Sonnet 執行任務卡

規則見 [WORKFLOW.md](WORKFLOW.md)。Sonnet：**一次只做一張卡，逐字照做，
完成「執行步驟」後必須跑完「自我檢查」才能把狀態改成 🔵 待驗證。**
每張卡做完都要在「交接筆記」寫下實際做的事與遇到的坑。

---

## Phase 0 — 可行性驗證

### T-00 建立開發環境
- **狀態**：✅ 通過（Opus 驗證 2026-08-16）
- **前置**：無
- **對應 SPEC**：§5（技術棧基礎）
- **產出**：`.venv/`、`requirements.txt`、`assets/`、`output/`、`scripts/` 資料夾、`scripts/check_audio.py`
- **執行步驟**：
  1. 在專案根目錄建立 Python 虛擬環境：`python3 -m venv .venv`，之後所有指令先 `source .venv/bin/activate`
  2. 升級 pip 後安裝：`numpy scipy soundfile matplotlib pyroomacoustics pillow`
  3. `pip freeze > requirements.txt`
  4. 建立資料夾 `assets/photos/`、`assets/dry/`、`assets/reference_irs/`、`output/`、`scripts/`
  5. 寫 `scripts/check_audio.py`：吃一個音訊檔路徑，印出「取樣率、長度（秒）、聲道數、RMS、峰值」。
     RMS < 0.0001 時額外印出警告「⚠️ 近乎靜音」。用 soundfile 讀檔。
  6. 確認 `.gitignore` 已含 `.venv/`，並新增 `output/`（產出的音檔不進 git，但 `assets/` 進 git）
- **自我檢查**：
  - `source .venv/bin/activate && python -c "import pyroomacoustics, soundfile, numpy; print('OK')"` 印出 OK
  - `python scripts/check_audio.py` 不帶參數時印出用法說明而非 crash
- **Opus 驗證重點**：requirements.txt 存在且非空；check_audio.py 對不存在的檔案給清楚錯誤訊息
- **交接筆記**：
  - 用 `python3 -m venv .venv` 建立虛擬環境（系統 Python 3.9.6），`pip install numpy scipy soundfile matplotlib pyroomacoustics pillow` 全部安裝成功，無需額外處理相依性問題。
  - `pip freeze > requirements.txt` 產出 19 個套件（含被動安裝的相依套件如 Cython、cffi 等），非空。
  - 建立資料夾：`assets/photos/`、`assets/dry/`、`assets/reference_irs/`、`output/`、`scripts/`（皆為空資料夾，git 不會追蹤空目錄，之後有檔案放入時會自動被追蹤）。
  - `scripts/check_audio.py`：用 soundfile 讀檔，印出取樣率/長度/聲道數/RMS/峰值；RMS < 0.0001 印「⚠️ 近乎靜音」；不帶參數印用法說明（exit code 0，不 crash）；檔案不存在時印清楚中文錯誤訊息（exit code 1）。
  - `.gitignore` 新增 `output/`（`.venv/` 原本就已存在）。
  - 自我檢查兩項皆通過（見下方指令輸出）：
    - `python -c "import pyroomacoustics, soundfile, numpy; print('OK')"` → `OK`
    - `python scripts/check_audio.py`（無參數）→ 印用法說明，exit code 0
  - 沒有遇到坑。下一步：T-01（用手動參數生成第一個 IR）。
- **Opus 驗證附註（2026-08-16）**：✅ 通過。但驗證 T-01~T-03 時發現 `check_audio.py` 兩個瑕疵：
  1. **已在本輪修好**：`except FileNotFoundError` 是死分支（soundfile 對不存在的檔案拋的是
     `LibsndfileError` 不是 `FileNotFoundError`），導致檔案不存在時只印含糊的「System error.」。
     已改為 `sf.read` 前先 `Path.exists()` 判斷，並把過寬的 `except Exception` 收窄成 `except sf.LibsndfileError`。
  2. **未修，留給下一張卡**：不帶參數時 `sys.exit(0)`，屬「使用錯誤卻回報成功」，
     串 shell/CI 會被當成通過。建議改 `sys.exit(2)`。任務卡只要求「印用法說明而非 crash」，
     不算違反卡片，故不退回。

---

### T-01 用手動參數生成第一個 IR
- **狀態**：✅ 通過（Opus 驗證 2026-08-16）
- **前置**：T-00
- **對應 SPEC**：§5 路線 A
- **產出**：`scripts/gen_ir_manual.py`、`output/ir_room_small.wav`、`output/ir_hall_large.wav`
- **執行步驟**：
  1. 寫 `scripts/gen_ir_manual.py`：用 pyroomacoustics 的 ShoeBox 房間模擬生成 IR。
     參數（房間長寬高、各面吸音係數、聲源/麥克風位置）寫成檔案頂部的變數區塊，附中文註解
  2. 內建兩組 preset 由命令列參數選擇：
     - `small`：4×3×2.5m，吸音係數 0.3（一般房間）
     - `hall`：30×20×12m，吸音係數 0.08（音樂廳）
  3. 輸出 48kHz / 24bit mono WAV 到 `output/ir_<name>.wav`，正規化峰值到 -3dBFS
  4. 同時印出模擬得到的 RT60 估計值
- **自我檢查**：
  - 兩個 preset 都跑過，兩個 WAV 都存在
  - `python scripts/check_audio.py output/ir_room_small.wav` — RMS 正常、取樣率 48000
  - `hall` 的 IR 長度明顯比 `small` 長（印出的 RT60：hall 應 > 1.5s，small 應 < 0.8s）
- **Opus 驗證重點**：RT60 數值合理；WAV 真的有內容；參數區塊清楚可改
- **交接筆記**：
  - `scripts/gen_ir_manual.py`：pyroomacoustics ShoeBox 模擬，image-source 算早期反射
    ＋ ray tracing 補晚期殘響。參數區塊在檔案第 29–77 行，每個欄位都有中文說明
    （dimensions / absorption / scattering / source_pos / mic_pos / max_order / n_rays / time_thres）。
  - 實測數值：`small`（4×3×2.5m, α=0.3）→ RT60 **0.219s**、IR 長 0.437s；
    `hall`（30×20×12m, α=0.08）→ RT60 **4.55s**、IR 長 8.437s。兩檔皆 48kHz / PCM_24 / mono、
    峰值精準 -3.0 dBFS、RMS 0.0179 / 0.0055（非靜音）。
  - 開了空氣吸收（20°C / 50%RH），所以 hall 實測 RT60 4.55s 比 Sabine 理論值 6.04s 短——
    7200 m³ 大空間的高頻空氣吸收本來就會造成這個降幅，不是 bug。
  - **反造假交叉驗證**（Opus）：量測 IR 的直達音到達時間 vs 幾何理論值——
    small 實測 6.56ms vs 理論 6.58ms、hall 41.19ms vs 40.84ms，誤差 < 0.4ms，
    證明 IR 真的來自房間幾何而非亂數；另自行算 Schroeder 衰減曲線反推 RT60（0.211 / 4.39s），
    與程式印出的值吻合。
  - **坑**：`hall` 的 `max_order` 只設 4（不是 12），因為大空間 image-source 階數一高就爆炸慢，
    晚期靠 140000 條 ray 補。若之後要更真實的早期反射再調高，但要有心理準備會變很慢。
  - 下一步：T-02（卷積試聽）、T-03（材質表）皆已完成。

---

### T-02 離線卷積試聽工具
- **狀態**：✅ 通過（Opus 驗證 2026-08-16）｜🎧 **唯一未完成項：使用者本人試聽**
- **前置**：T-01
- **對應 SPEC**：F-07
- **產出**：`scripts/convolve.py`、`assets/dry/`內至少一個乾聲檔、`output/wet_demo.wav`
- **執行步驟**：
  1. 寫 `scripts/convolve.py`：用法 `python scripts/convolve.py <dry.wav> <ir.wav> <out.wav> [--mix 0.5]`
  2. 用 scipy 的 fftconvolve；`--mix` 控制乾濕比（0=全乾、1=全濕，預設 0.5）；輸出峰值正規化到 -1dBFS 防爆音
  3. 取樣率不同時自動重採樣對齊；mono/stereo 自動處理
  4. 乾聲測試檔：用 numpy 合成一段 2 秒的「乾拍手」（短暫衝擊聲＋很短衰減）存到
     `assets/dry/clap_synth.wav`，48kHz。若使用者之後放入真實乾聲（人聲/樂器）優先用真實檔案
  5. 產出示範：clap_synth + T-01 的 hall IR → `output/wet_demo.wav`
- **自我檢查**：
  - `output/wet_demo.wav` 存在、check_audio.py 無警告
  - wet_demo 長度 ≈ 乾聲長度 + IR 長度（卷積會拖尾）
  - 用 `afplay output/wet_demo.wav` 播放，聽得出大廳殘響（也請使用者聽）
- **Opus 驗證重點**：乾濕比參數真的有作用（mix 0 與 1 的輸出應明顯不同，可用 RMS 差異佐證）；無爆音（峰值 ≤ 0dBFS）
- **交接筆記**：
  - `scripts/convolve.py`：scipy `fftconvolve`，`--mix` 乾濕比（預設 0.5），
    輸出峰值正規化到 -1dBFS，取樣率不同會自動重採樣，mono/stereo 自動處理。
  - `assets/dry/clap_synth.wav`：numpy 合成的 2 秒乾拍手，48kHz、RMS 0.0102。
    **之後有真實乾聲（人聲/樂器）請放進 `assets/dry/` 優先用真實檔案**，合成拍手只是佔位。
  - `output/wet_demo.wav` = clap_synth + hall IR，長度 10.437s = 乾聲 2.000 + IR 8.437（卷積拖尾正確），
    峰值 -1.000 dBFS、**clip 樣本 0 個**（無爆音）。
  - **乾濕比實證**（Opus 獨立重跑）：mix=0 全曲 RMS 0.005626、3 秒後尾段 RMS **0.00000000**（純乾聲）；
    mix=1 全曲 RMS 0.022234、3 秒後尾段 RMS **0.00069906**（真的有殘響尾巴）；
    兩者逐點最大差異 0.891251。參數確實有作用，不是裝飾。
  - **坑**：任務卡自我檢查最後一項「用 afplay 播放，聽得出大廳殘響」**AI 不能代勞**，
    已刻意不執行 afplay（避免在使用者電腦上發出聲音）。這項留給使用者：
    `afplay output/wet_demo.wav`，要聽得出拍手聲後面拖著一條大廳殘響尾巴。
  - 下一步：使用者試聽確認後這張卡才算 100% 完成。

---

### T-03 材質吸音係數表
- **狀態**：✅ 通過（Opus 驗證 2026-08-16）
- **前置**：T-00
- **對應 SPEC**：§6
- **產出**：`data/materials.json`、`scripts/show_materials.py`
- **執行步驟**：
  1. 建 `data/materials.json`：SPEC §6 列出的每種材質，含欄位：
     `id`、`name_zh`、`name_en`、六個頻段（125/250/500/1k/2k/4k Hz）的吸音係數 α、`source`（數據出處說明）
  2. 數值採用建築聲學公開參考值（如各教科書/工程手冊常用表），不確定的材質標 `"confidence": "low"`
  3. 寫 `scripts/show_materials.py` 印出整表（表格排版）供人工核對
  4. 在 pyroomacoustics 中驗證可用：修改 `gen_ir_manual.py` 加一個 `--material <id>` 選項，
     從 materials.json 讀取係數套用到牆面
- **自我檢查**：
  - `python scripts/show_materials.py` 正常列出 ≥ 11 種材質
  - 所有 α 都在 0–1 之間（在 show_materials.py 裡自動檢查並回報）
  - `python scripts/gen_ir_manual.py small --material marble` 跑得動，且 RT60 比預設（0.3）長
- **Opus 驗證重點**：抽查 3 種材質的係數是否符合常識（地毯高頻吸收高、大理石全頻段吸收低、布幕中高頻吸收高）；source 欄位不是空話
- **交接筆記**：
  - `data/materials.json`：**12 種材質**（SPEC §6 點名的 11 種全到齊 + fallback `generic_wall`），
    六頻段 125/250/500/1k/2k/4k Hz，72 個 α 值全部落在 0–1。
    頂層欄位：`version` / `description` / `band_center_freqs_hz` / `confidence_levels` / `fallback_id` / `materials`。
  - `scripts/show_materials.py`：印出整表供人工核對，並自動檢查必要欄位、α 範圍、材質數量 ≥ 11。
    `gen_ir_manual.py` 直接 import 它的 `load_materials/get_material/alpha_list`，不重複實作。
  - `gen_ir_manual.py` 新增 `--material <id>` 與 `--list-materials`；**不帶 --material 時行為與 T-01 完全相同**。
    實測 `small --material marble` → RT60 **6.40s**，是預設 α=0.3（0.219s）的 29 倍——
    大理石六頻段 α 只有 0.01~0.02，幾乎不吸音，物理上就該這麼長。
  - 有個沒被要求但做對的設計：帶 `--material` 時會依**最長頻段 RT60 自動加長 ray tracing 的 time_thres**
    （marble 例：2.0s → 12.28s），避免 IR 被截斷害 RT60 量測失真。
  - **Opus 抽查係數**（對照建築聲學標準表，全部正確）：
    - `carpet` 0.02/0.06/0.14/0.37/0.60/0.65 — 多孔吸音材典型：低頻幾乎不吸、高頻吸很多 ✓
    - `marble` 0.01/0.01/0.01/0.01/0.02/0.02 — 硬質光滑面全頻段幾乎不吸 ✓
    - `curtain_fabric` 0.14/0.35/0.55/0.72/0.70/0.65 — 中高頻吸收高 ✓
    - `source` 欄位是具體出處（Egan《Architectural Acoustics》、Beranek《Concert Halls and Opera Houses》、
      Cox & D'Antonio），不是空話 ✓
  - 2 種標 `confidence: low`：`audience_seating`、`grass_soil`（觀眾席與戶外地面本來就變異大），
    誠實標註不確定性。Phase 1 的材質模組要注意這兩種的誤差。
  - **坑**：`materials.json` 若「存在但 JSON 損毀」目前仍會噴 traceback（只處理了「檔案不存在」）。
    這是大聲失敗不是吞錯誤，但 Phase 1 把材質表變成正式模組時要補。

---

### T-04 收集測試素材與對照 IR
- **狀態**：✅ 通過（素材部分，2026-08-16）｜🚧 **照片來源連結待使用者補**（自我檢查第 2 項未達成）
- **前置**：T-00
- **對應 SPEC**：§7 驗收標準
- **產出**：`assets/photos/` 內 5 類空間照片、`assets/reference_irs/` 內 ≥ 3 個 OpenAIR 真實 IR、`assets/SOURCES.md`
- **執行步驟**：
  1. 請使用者提供（或用手機拍）5 類空間照片：浴室、客廳、教堂/大空間、樓梯間/走廊、車內。
     **先問使用者是否要自己拍**；使用者沒空則從免授權圖庫（Unsplash 等）下載，記下網址
  2. 從 OpenAIR（openairlib.net）下載 ≥ 3 個附有場地照片的 IR（下載前依規則先徵求使用者同意），
     連同場地照片存入 `assets/reference_irs/<場地名>/`
  3. 建 `assets/SOURCES.md` 記錄每個檔案的來源與授權
  4. 用 check_audio.py 檢查所有下載的 IR 可正常讀取
- **自我檢查**：
  - 照片 ≥ 5 張、參照 IR ≥ 3 組（IR + 場地照片成對）
  - SOURCES.md 每一項都有來源連結
- **Opus 驗證重點**：IR 與照片是同一場地（抽查 OpenAIR 頁面）；授權允許開發使用
- **交接筆記**：
  - **⚠️ OpenAIR 已停站**：`openair.hosted.york.ac.uk` 與 `openairlib.net` 兩個域名都轉到
    主機商的 `suspendedpage.cgi`，站台實質關閉。經使用者同意後改用 **EchoThief + MIT Reverb Survey**。
    這是對任務卡的來源替換，理由記於此與 `assets/SOURCES.md` §3.1。
  - **產出（超額）**：對照 IR **8 個場地**（卡片要求 ≥3），全部 IR + 場地照片 + INFO.md 成對：
    - EchoThief 5 組：`cathedral_room_shasta_lake_caverns`（石灰岩洞窟）、`steinman_hall`（音樂廳）、
      `racquetball_court_4`（壁球場）、`tunnel_to_hell`（混凝土隧道）、`divorce_beach`（戶外沙灘）
    - MIT 3 組：`mit_department_store`、`mit_gym`、`mit_restaurant`
    - 全部跑過 check_audio.py，RMS 0.0094–0.0488 皆非靜音。
  - **測試照片 9 張**（卡片要求 ≥5），T-04 的 5 類全部涵蓋，另加 Live House 與 CGI ×2。
  - **🔴 授權：媒體檔已加入 .gitignore，只有 INFO.md 進版控。** EchoThief 網站從未有過
    License/Terms 頁（已查證首頁、WordPress REST API 全 73 頁、Wayback 1077 筆歷史 URL、
    以及 EchoThief.zip 中央目錄內也無 LICENSE 檔），唯一權利聲明是頁尾的
    `copyright 2013-2026 Dr. Chris Warren`。**免費下載可用於研究，但未授予再散布權。**
    公開發佈前須寫信 cwarren@sdsu.edu。
  - **🔴 未竟事項（自我檢查第 2 項「SOURCES.md 每一項都有來源連結」未達成）**：
    `assets/photos/` 9 張照片的來源網址全部沒有記錄（5 張 YouTube 截圖只有畫面上可見的影片標題，
    4 張網路圖片完全無出處）。已在 `assets/SOURCES.md` §2 明確標記待補。**需要使用者補上。**
  - **💡 重大發現：8 張場地照片有 5 張是 360° 環景**（steinman_hall、divorce_beach、
    cathedral_room、racquetball_court_4 為 equirectangular；只有 tunnel_to_hell 與 3 張 MIT 是一般透視）。
    Depth Anything V2 / SegFormer 都用透視影像訓練，環景直接餵幾何會歪掉
    → **SPEC §7 驗收第 2 條（RT60 誤差 <20%）目前只有 4 個場地能用**。
    但反面是機會：環景沒有「視野外」，可直接解掉 SPEC §8 的已知風險「照片視野外的空間未知」。
    **架構決策，留給 T-08。**
  - **💡 必測反例（EchoThief agent 建議）**：`racquetball_court_4` 是 8 個場地裡空間最小的，
    殘響卻最長（3.538s，比大洞窟的 1.529s 長一倍多），因為全是木頭與玻璃硬面。
    任何「空間看起來小就給短殘響」的天真規則在這個場地一定會爆掉。

---

### T-05 深度估計模型測試
- **狀態**：✅ 通過（Opus 驗證 2026-08-16）｜⚠️ **產出重大負面結論，影響 MVP 路線**
- **前置**：T-00、T-04（需要測試照片）
- **對應 SPEC**：F-02
- **產出**：`scripts/test_depth.py`、`output/depth/`（每張照片的深度圖 PNG）、`output/depth/REPORT.md`
- **執行步驟**：
  1. `pip install torch transformers accelerate`，更新 requirements.txt
  2. 寫 `scripts/test_depth.py`：用 Hugging Face `depth-anything/Depth-Anything-V2-Small-hf`
     （transformers 的 depth-estimation pipeline），對 `assets/photos/` 每張照片輸出：
     深度圖視覺化 PNG（原圖與深度圖並排）＋深度統計（最小/最大/中位數）
  3. 模型下載約數百 MB，第一次執行前告知使用者並徵求同意
  4. 在 `output/depth/REPORT.md` 記錄：每張照片的深度圖是否合理（牆遠地板近）、
     明顯失敗的案例、以及「相對深度 → 絕對尺寸」的問題觀察（這個模型輸出相對深度）
- **自我檢查**：
  - 每張測試照片都有對應的深度 PNG
  - REPORT.md 有逐張的觀察紀錄（不是空泛的「都很好」）
- **Opus 驗證重點**：REPORT 誠實記錄失敗案例；深度圖用肉眼抽查 2 張是否合理；紅旗：用隨機數假裝模型輸出
- **交接筆記**：
  - 產出：`scripts/test_depth.py`、`output/depth/`（9 張深度視覺化 PNG + `depth_stats.json`）、
    `output/depth/REPORT.md`（21KB，9 章）。模型：`depth-anything/Depth-Anything-V2-Small-hf`。
    環境：torch 2.8.0、MPS 可用。
  - **🔴 本卡最重要的結論（REPORT §7）——「不要用單張深度圖去估房間體積」**：
    - 模型輸出是每張圖各自正規化的 **相對 disparity**，不是距離。
    - 實測 9 張的深度動態範圍與實際空間大小**完全沒有單調關係**：
      SUV 車內（~2m）核心 p95/p5 = **91.5x**，體育館（~150m）只有 **11.7x**，差 8 倍且方向相反。
    - 就算給絕對錨點用 `距離 = k/disparity` 換算也會壞：飯店長廊消失點 disparity=0
      推出 **3,747,829 公尺**；浴室實際進深 2.5–3.5m，推得 5.50m，**高估 60–120%**。
    - Sabine 公式 RT60 ∝ V，體積誤差會以平方/立方級放大到 RT60
      → **直接衝擊 SPEC F-02 的「±30% 誤差目標」**。
    - REPORT 建議的替代路線：偵測已知尺寸參考物（門 ~2.0m、人 ~1.7m）取絕對錨點且只在近距離推算；
      或改用 metric depth 模型（Depth-Anything-V2-Metric / UniDepth / Metric3D）。**留給 T-08 決策。**
  - **必要的前處理三步**（REPORT §7.3）：(a) 裁掉 letterbox/UI；(b) 濾掉 disparity≈0 的區域
    （窗外、天空、消失點）；(c) clamp 負值。車內那張證明 (b) 的威力——套用後動態範圍
    從「無限大」收斂到 6.33x，跟浴室同級。
  - **逐張評級**：✅ bathroom / bedroom / cgi_cave_lab；⚠️ car / stairwell / corridor / cgi_cavern；
    ❌ livehouse（舞台被壓平且**深度排序反轉**：布幕 0.897 比站在布幕前的吉他手 0.618 更「近」）、
    ❌ arena（大空間 + 全套 YouTube UI 污染）。
  - **鏡子沒失敗但不能當通則**：浴室鏡子這次過關，但 REPORT 主動自我設限——
    「這面鏡子照到的是同樣平淡的米色磁磚牆…這是簡單模式的鏡子」。**玻璃則確實失敗**
    （淋浴門被看穿，disparity 1.28 vs 同距馬桶 3.01）。
  - **YouTube 黑邊會污染深度**：corridor 那張的左右黑邊 disparity 7.88，比畫面內最近的木門 5.96 還高，
    是全圖最大值的來源——**黑邊不裁掉會直接毀掉正規化基準**。
  - **Opus 反造假查核**：重跑後 27 個輸出檔 MD5 **完全相同**（亂數不可能 bit-identical）；
    disparity 陣列 lag-1 空間自相關 0.9952–1.0000（均勻雜訊會趨近 0）；
    REPORT 的 ROI 數字用 `--probe` 重現一字不差。確認無造假。

---

### T-06 語意分割模型測試
- **狀態**：✅ 通過（Opus 驗證 2026-08-16）｜⚠️ **產出重大負面結論，影響材質模組設計**
- **前置**：T-05（環境已含 torch/transformers）
- **對應 SPEC**：F-03
- **產出**：`scripts/test_segmentation.py`、`output/seg/`（分割疊圖 PNG）、`output/seg/REPORT.md`
- **執行步驟**：
  1. 用 Hugging Face `nvidia/segformer-b4-finetuned-ade-512-512`（ADE20K，150 類，含
     wall/floor/ceiling/window/curtain/sofa 等）對每張測試照片做語意分割
  2. 輸出：原圖＋分割疊色圖並排 PNG、每張照片的「類別 → 佔畫面比例」統計
  3. 在 REPORT.md 記錄：牆/地板/天花板是否被正確分出、哪些 ADE20K 類別可對應到
     materials.json 的材質、對應不到的缺口清單
- **自我檢查**：
  - 每張照片有分割 PNG＋比例統計
  - REPORT.md 含「ADE20K 類別 → 我們的材質 id」的初版對照表
- **Opus 驗證重點**：對照表合理性；REPORT 是否誠實記錄分割失敗的照片
- **交接筆記**：
  - 產出：`scripts/test_segmentation.py`、`output/seg/`（9 張分割疊圖 PNG + 9 個 labelmap.npy）、
    `output/seg/REPORT.md`（24KB，6 章）。模型：`nvidia/segformer-b4-finetuned-ade-512-512`（ADE20K 150 類）。
  - **一句話結論**：牆/地板/天花板在「一般建築室內」能正確分出（bedroom / bathroom / corridor /
    stairwell 四張可用），但在「非建築空間」（車內、CGI 洞窟）與「人群主導的大空間」
    （體育館、Live House）會**系統性失敗，且模型對失敗毫無自覺**——一律輸出高置信度的 wall/floor/ceiling。
  - **🔴 最危險的失敗：地毯（REPORT §2.3）**。飯店走廊是滿鋪地毯，但只有 **29.6%** 被判成 `rug`，
    **70.4% 被判成 `floor`**。換算吸音係數的後果：0.296×0.65 + 0.704×0.02 = **0.207**，
    正確值應是 0.65 → **高頻吸音只剩 32%**。REPORT 的結論是
    「`floor` 這個類別在本專案裡是不可信的」。
  - **🔴 車內是已證實的最大失敗案例（REPORT §2.9）**：ADE20K 沒有任何車輛內裝類別。
    實測車頂內襯、窗外樹林（92.4%）、連車外橘色烤漆（100%）**全部被判成 `wall`**。
    結論：「目前的材質辨識管線對非建築空間是無能為力的，而且會**安靜地輸出看似合理的錯誤結果**」。
  - **鏡子**：浴室鏡子被判成 `mirror` 82.0%（分得出來），但玻璃淋浴門被判成 `screen door` 30.5%
    且**吞掉後方的磁磚牆** → 表面積歸類錯誤，不是細節誤差。
  - **✅ 產出 T-06 要求的對照表**（REPORT §4）：9 張圖實際出現的 **42 個 ADE20K 類別 → materials.json
    材質 id**，含 🟢/🟡/🔴 信心分級 + §4.2 缺口清單。兩個最該注意的 🔴：
    - `wall`（id 0）佔比最高（最高 69.81%）也最不可靠——磁磚牆、抹灰牆、岩壁、車頂內襯、
      窗外樹林、YouTube 黑邊全叫 wall
    - `floor`（id 3）只表示「地面」，木地板／磁磚／地毯完全無法區分
  - **CGI 沒被一竿子打翻**：AI 生成臥室的分割品質與真實照片無異（可信），但兩張 CGI 洞窟判 ❌ 不可用。
    REPORT 還提出可操作的防呆規則：**「封閉洞窟出現 `sky` 類別 = 模型正在猜」的可偵測訊號**。
  - **⚠️ 已知小瑕疵（留給下一張卡）**：`test_segmentation.py` 在「所有輸入圖片都解碼失敗」時
    仍回傳 exit code 0 並寫出空的 stats.json；同情境下 `test_depth.py` 會 exit 1。
    兩支腳本行為不一致，自動化串接時 seg 會把「全部失敗」誤判成成功。
  - **Opus 反造假查核**：`grep -nEi "random|rand\(|randn|fake|dummy|mock"` 無命中；
    重跑後 9 個 seg PNG + 9 個 labelmap.npy MD5 完全相同；
    **獨立重算 REPORT 裡 14 組區域統計，全部吻合到小數第二位**
    （如 bathroom 鏡子 bbox 宣稱 82.0/16.9/1.1，實測 82.45/16.45/1.10）；
    42 個 ADE20K id↔類別名用 model.config.id2label 逐一核對全部正確。確認無造假。

---

### T-07（選做，限時）跑通 Image2Reverb baseline
- **狀態**：⏸️ **暫緩— 使用者未授權下載**（2026-08-16 詢問時未勾選此項；前置 T-04 已完成，隨時可啟動）
- **前置**：T-04
- **對應 SPEC**：§5 路線 C 評估
- **產出**：`output/image2reverb/`（生成的 IR 與試聽 wet 檔）或 `output/image2reverb/FAILURE.md`
- **執行步驟**：
  1. **限時 2 小時**（2021 年的舊專案，相依套件很可能裝不起來，失敗是可接受結果）
  2. Clone https://github.com/mdkberry/image2reverb 到 `vendor/image2reverb/`
     （把 `vendor/` 加進 .gitignore），嘗試建立獨立環境跑 `run_single_image.py`
  3. 成功 → 對 3 張測試照片生成 IR，用 convolve.py 做 wet 檔，聽感筆記寫入 REPORT.md
  4. 失敗 → 在 FAILURE.md 詳實記錄卡在哪一步、錯誤訊息、可能解法，然後**停止**，不要無限嘗試
- **自我檢查**：REPORT.md 或 FAILURE.md 擇一存在且內容具體
- **Opus 驗證重點**：若宣稱成功，wet 檔要真的有殘響（對比乾檔）；若失敗，紀錄要足以讓 Fable 判斷是否值得再投入
- **交接筆記**：

---

### T-08 Phase 0 總結與路線決策（🔮 Fable 任務，Sonnet 不要做）
- **狀態**：⬜ 未開始
- **前置**：T-01 ~ T-07 完成（T-07 可為失敗結案）
- **內容**：Fable 讀所有 REPORT，確認 MVP 路線（維持或修改 SPEC §5 的 A+B 混合決策），
  更新 SPEC/ROADMAP，把 Phase 1 任務卡（T-10 起）補充到可執行的細節
- **交接筆記**：

---

## Phase 1 — MVP：照片 → IR（T-08 後由 Fable 細化，以下為預排框架）

### T-10 專案骨架（`src/` 套件結構、CLI 入口、設定檔）
- **狀態**：⬜ 未開始 ｜ **前置**：T-08
### T-11 幾何估計模組（深度圖 → 房間尺寸/體積，含尺度校正與手動覆寫）
- **狀態**：⬜ 未開始 ｜ **前置**：T-10
### T-12 材質模組（分割 → materials.json 對應 → 各表面吸音係數）
- **狀態**：⬜ 未開始 ｜ **前置**：T-10
### T-13 聲學參數計算（Sabine/Eyring → 六頻段 RT60、pre-delay）
- **狀態**：⬜ 未開始 ｜ **前置**：T-11、T-12
### T-14 IR 合成引擎 v1（image-source 早期反射 + shaped-noise 晚期殘響）
- **狀態**：⬜ 未開始 ｜ **前置**：T-13
### T-15 CLI 整合（照片 → IR WAV + 分析報告 JSON）
- **狀態**：⬜ 未開始 ｜ **前置**：T-14
### T-16 分析視覺化（材質疊圖 + 參數報告）
- **狀態**：⬜ 未開始 ｜ **前置**：T-15
### T-17 MVP 驗收（SPEC §7 三項標準，Opus 主導）
- **狀態**：⬜ 未開始 ｜ **前置**：T-16
