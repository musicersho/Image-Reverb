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
- **狀態**：✅ **完全通過**（Opus 驗證 + 使用者試聽確認，2026-08-16）
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
  - **🎧 使用者試聽結果（2026-08-16）**：聽 `output/wet_demo.wav` 後回覆
    「殘響的效果還算自然」→ 這張卡的最後一項自我檢查通過，T-02 100% 完成。
    這也是整條鏈路（pyroomacoustics 模擬 → IR → 卷積）第一次由人耳確認可用。
    註：「還算」是可接受而非驚豔，之後 Phase 1 的 IR 合成引擎 v1（T-14）仍應以此為基準線求進步。

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
  - **🔴 後續發現（2026-08-16 試聽對照時）：寬頻 RT60 對頻率選擇性材質是誤導的。**
    以 `small --material carpet` 為例：

    | 頻段 | α | Sabine RT60 |
    |---|---|---|
    | 125 Hz | 0.020 | **4.093 s** |
    | 1 kHz | 0.370 | 0.221 s |
    | 4 kHz | 0.650 | **0.126 s** |

    低頻與高頻的 RT60 差 **32 倍**。把六段 α 平均（0.3067）算出的寬頻 RT60 是 **0.267 s**，
    但實測 T30 是 **4.023 s**——**差 15 倍**，因為殘響尾巴完全由 125 Hz 決定。
    **對 T-13（聲學參數計算）的約束：絕對不能用平均 α 算單一 RT60，必須逐頻段獨立計算。**
    SPEC F-04 已要求「至少 6 個八度頻段」，這裡是實證支持——不是規格潔癖，是不這樣做會錯 15 倍。
  - **🔴🔴 使用者試聽抓到的模型缺陷（2026-08-16）：`--material` 把單一材質套到全部六個面是不現實的。**
    使用者聽 `carpet` 的試聽檔後回覆「感覺很像用手去拍鐵筒子出來的聲音」（marble 與 default 都 OK）。
    追查結果：
    - 頻譜分析證實殘響尾段能量全集中在 **30–135 Hz**，峰值彼此僅差 2.7 dB → 低頻持續共振。
    - 根因：地毯的低頻 α 只有 0.02（多孔吸音材不吃低頻），把它套到六個面等於
      「連天花板和牆壁都鋪地毯」，現實不存在。真實地毯房間的牆與天花板是石膏板，
      而石膏板 125 Hz 的 α = 0.29（板共振吸音體，專吃低頻）。
    - 量化差異（4×3×2.5m，V=30m³，S=59m²）：

      | 頻段 | 全鋪地毯（現況） | 只有地板鋪地毯（現實） | 倍數 |
      |---|---|---|---|
      | 125 Hz | **4.093 s** | 0.348 s | **11.8x** |
      | 1 kHz | 0.221 s | 0.764 s | 0.3x |
      | 4 kHz | 0.126 s | 0.401 s | 0.3x |

      現況模型低頻/高頻 RT60 比是 **32 倍**（病態傾斜）；現實模型約 1 倍（平衡）。
    - **對 T-12（材質模組）的硬性需求：必須能逐表面指定材質**
      （地板／天花板／各面牆分開），不能全域套用單一材質。
      pyroomacoustics 的 ShoeBox 原生支援 per-wall material，技術上沒有障礙。
    - **⚠️ 這件事的意義超出本卡**：RT60 4.023 s 落在 WORKFLOW §5 規定的合理區間（0.1–12 s）、
      α 全部在 0–1、無假實作——**三層自動驗證全部通過，但模型是錯的**。
      這類錯誤只有人耳抓得到。Phase 1 的驗收不能只靠數值範圍檢查。

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
- **狀態**：✅ 完成（Fable，2026-08-16）
- **前置**：T-01 ~ T-07 完成（T-07 可為失敗結案）
- **內容**：Fable 讀所有 REPORT，確認 MVP 路線（維持或修改 SPEC §5 的 A+B 混合決策），
  更新 SPEC/ROADMAP，把 Phase 1 任務卡（T-10 起）補充到可執行的細節
- **交接筆記**：
  - **三個決策（理由與實證都已寫進 SPEC v0.2 與 ROADMAP）**：
    1. **深度路線**：主路線改 **metric depth 模型**（`depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf`，
       與 T-05 用過的 transformers pipeline 同款，遷移成本最低）。已知尺寸參考物（門 ~2.0m）
       **降級為尺度校驗**，不當主路線（T-05 已證 k/disparity 錨定會壞）。手動尺寸覆寫升 P0。
       ⚠️ metric depth 在本專案照片上的精度**尚未驗證**，所以 T-11 內建「評測關卡」：
       先對已知尺寸場地實測誤差，達標才往下接，不達標就停下來回報 Fable。
    2. **材質路線**：**併用**。ADE20K 分割只負責「切出表面的幾何角色」（哪塊是地板/天花板/牆），
       材質標籤一律交給**區域級二階分類器**——v1 用 CLIP zero-shot（transformers 已裝、不用訓練、
       有機率值可做信心 gating）。`floor`/`wall` 的 ADE20K 語意不再採信（T-06 實證）。
       CLIP 不夠好再評估 MINC/DMS 類材質專用模型（記在 SPEC §8 對策欄，不進 Phase 1 範圍）。
    3. **環景**：**做，最小範圍**——T-10 前處理模組加 equirect→多視角透視投影（純幾何運算，無新模型），
       融合只做「多視角結果的簡單統計」。換到的是：SPEC §7 驗收場地 4 個 → 8 個全可用，
       並提前解掉 §8「視野外空間未知」風險的環景部分。
  - **IR 生成路線維持 A+B 混合**：Phase 0 試聽已由人耳確認 pyroomacoustics 這條鏈路可用，不改。
  - 已把 HANDOFF §3 的兩條硬約束寫進任務卡執行步驟：**約束 A（逐表面材質）→ T-12 步驟 2**、
    **約束 B（逐頻段 RT60）→ T-13 步驟 2**，各自的自我檢查也含對應的迴歸數字。
  - 文件更新：SPEC v0.1→v0.2（F-02/F-03/F-04/F-09、§5/§6/§7/§8）、ROADMAP（Phase 0 結案
    含決策紀錄、Phase 1 對應 T-10~T-17、Phase 3 影片輸入定位調整）、本檔 Phase 1 八張卡細化。
  - **給 Sonnet 的執行順序**：T-10 → T-11 與 T-12 可並行（都只依賴 T-10）→ T-13 → T-14 → T-15 → T-16 → T-17。
    T-11 若在評測關卡不達標，會標 🔴 卡關，這是設計內的結果，不是失敗。

---

## Phase 1 — MVP：照片 → IR（T-08 已細化，2026-08-16）

> 執行順序：T-10 → T-11 與 T-12 可並行 → T-13 → T-14 → T-15 → T-16 → T-17。
> **Phase 1 通則（每張卡都適用）**：(1) 改動 IR 生成邏輯後必須產生試聽檔請使用者聽——
> Phase 0 實證「數字合理 ≠ 聽起來對」；(2) 分析結果信心不足時必須輸出明示警示，
> 禁止安靜 fallback；(3) 需要下載新模型時先告知大小並徵求使用者同意。

### T-10 專案骨架與影像前處理
- **狀態**：✅ 通過（Opus 複驗，2026-08-18）— 順序缺陷已確實修正，迴歸測試對舊程式碼實測會失敗
  （有真實診斷力），非環景路徑逐張比對與修正前完全一致。詳見下方「Opus 複驗結果（2026-08-18）」。
  歷程：🟠 退回（2026-08-17，順序反了）→ Sonnet 修正 → ✅ 通過。
  **T-11／T-12 可並行開工。**
- **前置**：T-08
- **對應 SPEC**：§5（架構）、F-01
- **產出**：`src/image_reverb/` 套件（`__init__.py`、`config.py`、`preprocess.py`、`cli.py`）、
  `requirements.txt` 更新
- **執行步驟**：
  1. 建立 `src/image_reverb/` 套件骨架：`config.py`（管線參數集中：投影視角數、FOV、模型 id 等，
     附中文註解）、`cli.py`（入口 `python -m src.image_reverb <photo>`，本卡先只跑前處理並存中間結果）
  2. `preprocess.py` 實作三件事：
     a. **letterbox/UI 黑邊偵測與裁切**——地雷第 4 條：YouTube 截圖的黑邊 disparity 比畫面內容還高，
        會毀掉深度正規化。用邊緣列/欄的亮度變異數偵測純色邊框並裁掉
     b. **環景偵測**：長寬比 ≈ 2:1（容差 ±5%）判定為 equirectangular；不能只看檔名
     c. **equirect → 多視角透視投影**：水平 4 視角（方位角 0/90/180/270°、FOV 90°）＋仰角 ±45° 上下各 1，
        共 6 視角，輸出透視圖清單與各自的方位/仰角 metadata。可用 py360convert（純 numpy 幾何運算）
        或自行實作 spherical→perspective 重投影
  3. HEIC 輸入支援：`pip install pillow-heif`（F-01 要求 JPG/PNG/HEIC），更新 requirements.txt
  4. 一般透視照的行為：判定非環景 → 只做黑邊裁切，原樣通過
- **自我檢查**：
  - 對 corridor 那張 YouTube 截圖跑前處理，輸出圖的左右黑邊已被裁掉（肉眼查 + 邊緣列亮度統計）
  - 對 `assets/reference_irs/steinman_hall/` 的環景照片跑，判定為環景且輸出 6 張透視視角，
    視角圖裡的直線（牆緣、柱子）不彎曲
  - 對 bathroom 照片跑，判定為非環景、僅裁切通過
  - `python -m src.image_reverb assets/photos/<任一張>` 跑得動，中間結果存到 `output/preprocess/`
- **Opus 驗證重點**：投影幾何正確性（equirect 直線在透視圖中應為直線）；環景偵測是看長寬比不是檔名；
  黑邊裁切不會誤砍正常照片的暗色邊緣（拿一張四周偏暗但非黑邊的照片反測）
- **交接筆記**：
  - 新增 `src/image_reverb/`：`__init__.py`、`config.py`（黑邊門檻、環景長寬比、六視角參數集中於此）、
    `preprocess.py`（三件事都實作：黑邊裁切、環景偵測、equirect→6 視角投影）、`cli.py`、`__main__.py`；
    根目錄加 `src/__init__.py` 讓 `python -m src.image_reverb <photo>` 可執行。
  - 黑邊裁切用 **p90-p10（去除離群值後的亮度分佈範圍）而非「夠不夠暗」判定純色邊框**：
    純色邊框 p90-p10 會趨近 0，不管邊框是黑是白都抓得到；反之畫面偏暗但有紋理的正常內容
    p90-p10 明顯偏高、不會被誤裁。已用 `assets/photos/cgi_cave_lab_sophy.png`（邊緣暗但有紋理）
    反測，僅裁到 1px（安全誤差），沒有被錯誤大量裁切。加了 `BORDER_MAX_CROP_RATIO`（單邊上限 45%）
    防止極端情況把照片裁光。
  - corridor 那張黑邊其實左右是黑色（各裁掉 50px/30px），底部另外還有一條 6px 的**白色**細邊
    （字幕條殘留），同一套 p90-p10 邏輯一併抓到並裁掉，肉眼確認乾淨。
  - equirect 投影直接用 `py360convert.e2p`（純 numpy 球面幾何重投影，非 AI 模型），比自行重寫穩妥；
    已把 `py360convert`、`pillow_heif` 加進 `requirements.txt`（版本鎖定 1.0.4 / 1.1.1）。
  - 六視角用 `SteinmanHall.jpg`（4096×2048，長寬比剛好 2.0）跑出，肉眼檢查 az000（正面舞台）與
    el+45（往上看的天花板網格/樑）直線都沒有彎曲。
  - HEIC 支援靠 `pillow_heif.register_heif_opener()`，已驗證 `.heic` 有進 `Image.registered_extensions()`；
    專案裡目前沒有 .heic 測試檔，沒有拿真檔案跑過，之後若使用者提供 HEIC 照片要再驗一次。
  - 錯誤處理：CLI 對「檔案不存在」與「檔案存在但不是圖片」都會印清楚中文錯誤訊息＋非 0 exit code，
    不會丟原始 traceback（原本非圖片輸入會噴 `UnidentifiedImageError` 的完整 traceback，已補 try/except）。
  - `output/preprocess/` 已在 `.gitignore` 的 `output/**` 規則下自動排除，不用額外處理。
  - 下一步：T-11（幾何估計）與 T-12（材質模組）可並行，兩者都要先呼叫這裡的
    `preprocess.preprocess_image()`（環景會拿到 6 張透視圖清單，非環景拿到裁切後單張圖）。

- **Opus 驗證結果（2026-08-17）：🟠 退回，一個必修缺陷**

  **🔴 缺陷：先裁黑邊、再判環景 —— 順序反了**

  `preprocess_image()` 目前是 `detect_and_crop_border()` → `is_equirect()`。
  但 **equirectangular 影像的第一列就是「天頂那一個點」被拉伸成整列**，
  依定義完全均勻；天底同理。於是黑邊偵測會把極點當成純色邊框吃掉。

  實證（合成有紋理、只有極點均勻的 equirect，模擬 CGI／平坦天花板／陰天）：

  | 均勻極點列數 | 裁上/下 | 裁後長寬比 | is_equirect | 後果 |
  |---|---|---|---|---|
  | 0 | 0 / 0 | 1.998 | True | ✅ 正常 |
  | 3 | 3 / 3 | 2.010 | True | ⚠️ 仍判為環景，但垂直視角被靜默壓縮 |
  | 10 | 10 / 10 | 2.038 | True | ⚠️ 同上 |
  | **≥25** | 25 / 25 | 2.101 | **False** | ❌ **環景路徑整個被跳過，360 圖被當一般照片送進 T-11** |

  - 裁掉 3 列就讓赤道在 768px 透視圖中偏移 **3.8px**——`e2p` 假設影像垂直涵蓋完整 180°，
    裁過之後這個假設就不成立，但程式不會有任何警示。
  - 裁掉 ≥25 列（總高 1024 時）長寬比就超出 ±5% 容差 → **環景判定翻成 False**，
    整條 T-08 決策三的環景路徑被跳過，而且**完全靜默**。
  - **這正是本專案已經被燒過兩次的失敗類型**（HANDOFF §2 洞二、地雷第 9 條：
    「會安靜地輸出看似合理的錯誤結果」）。

  **為什麼這次沒被自檢抓到**：唯一能測的真實環景 `SteinmanHall.jpg`
  第 0 列 spread = **3.0**，門檻是 `spread < 3.0`——**餘裕剛好是 0.0，純屬僥倖**。
  門檻只要設 3.1、或圖片壓縮再乾淨一點，就會裁下去。
  更要緊的是：8 個對照場地有 5 張是環景，但照片沒進 git（授權未允許再散布），
  **5 張裡只有 1 張測得到，另外 4 張完全沒驗證過**。

  **修法（給下一個 Sonnet 視窗）**：
  1. `is_equirect()` 改成對**原圖**判斷，不是裁切後的圖
  2. 判定為環景 → **完全跳過黑邊裁切**（equirect 是完整球面渲染，本來就不會有 letterbox）
  3. 若日後真要對環景做任何裁切，必須同步記錄裁掉的垂直角度並傳給投影函式，
     否則 `e2p` 的「垂直涵蓋 180°」假設會被破壞
  4. 迴歸自檢：合成一張極點均勻的 equirect（上下各 30 列純色），
     修好後應仍判為環景、且 6 視角照常輸出

  **✅ 已驗證通過的部分（這些不用重做）**
  - **投影幾何正確**：用「gnomonic 投影中大圓必為直線」量化檢驗——
    赤道最大偏離 **2.81px**、經線 **1.42px**（768px 影像，屬於線寬/抗鋸齒等級誤差）
  - **環景判定確實看長寬比不看檔名**（讀碼＋行為雙重確認）
  - **反測無誤裁**：9 張照片逐一測，暗邊照片（cgi_cave/cgi_cavern）只裁掉 1 列（0.06%），
    只有 corridor 這張真有 letterbox 的裁掉 6.72%
  - **corridor 黑邊裁乾淨**：裁後最外圈 spread 56–123，無殘留純色邊
  - **HEIC 實測可用**：Opus 另外產生真實 `.heic` 檔跑過 CLI，成功
    （Sonnet 原本只確認 opener 有註冊、沒跑過真檔案，此項缺口已由驗證補上）
  - **錯誤處理**：檔案不存在 / 非圖片 / 缺參數 / 傳目錄，四種都是清楚中文訊息＋正確 exit code，
    無 traceback 外洩
  - **乾淨重跑成功**、宣稱產出全部存在、模組邊界清楚、無假實作、無 hardcode
  - **範圍乾淨**：沒動到 SPEC/ROADMAP/WORKFLOW，沒動到其他任務的 `scripts/`

  **小瑕疵（不阻擋，順手修即可）**
  - `project_equirect_to_perspectives(views=config.PERSPECTIVE_VIEWS)` 用可變物件當預設參數
    （目前沒被改動所以無害，但是壞味道）
  - 輸出檔名 `view_el+45.png` 含 `+`，在 shell glob／URL 情境容易出事，建議改 `el_up45`
  - 傳目錄當輸入時訊息是「找不到檔案」，語意不精確（路徑其實存在），建議分開處理
  （以上三項本輪未動，範圍只限修順序缺陷，仍待之後順手處理）

- **順序缺陷修正（Sonnet，2026-08-18）**：只動 `preprocess_image()` 一處，其餘（`is_equirect()`
  本身的長寬比邏輯、`detect_and_crop_border()` 的 p90-p10 判定、投影函式）未改動。
  - 把原本的 `裁黑邊 → is_equirect(裁後圖)` 改成 `is_equirect(原圖) → 環景則跳過裁切／非環景才裁`。
    `is_equirect()` 函式簽章本身沒變（本來就吃 `img` 參數），只是呼叫方改傳原圖而非裁切後的圖。
  - 判定為環景時，`border_crop` 欄位仍保留與非環景相同的欄位結構（`crop_*_px` 全填 0、
    多一個 `skipped_equirect: true`），維持 CLI 輸出格式與 `meta.json` schema 相容，不用改 CLI 程式碼。
  - 新增 `scripts/test_preprocess.py`：合成兩張圖做迴歸測試——
    (a) 1024×512 equirect（長寬比精確 2:1），上 30 列／下 30 列各填純色模擬天頂/天底極點，
        中間隨機紋理；驗證 `is_equirect` 仍為 True、`border_crop` 的 `crop_*_px` 全為 0、
        天頂/天底像素與原圖逐 pixel 相同（`np.array_equal`）、6 視角正常輸出。
    (b) 800×450 非環景照片、左右各 60px 純黑 letterbox；驗證 `is_equirect` 為 False、
        左右仍被正常裁掉（回歸防呆：確保這次改動沒有連帶弄壞非環景的黑邊裁切路徑）。
    跑法：`python scripts/test_preprocess.py`（純合成資料，不依賴 git 沒有的環景照片，
    任何 clone 都能重跑，彌補「5 張環景照片只有 1 張測得到」的驗證缺口）。
  - 對真實 `SteinmanHall.jpg` 重跑 `python -m src.image_reverb`，確認 `border_crop` 四邊
    皆為 0px（先前版本因餘裕剛好 0.0 而僥倖沒裁到，現在是「保證不裁」而非「運氣好沒裁」），
    6 視角照常輸出。對 `corridor_hotel_carpet.png`（非環景 letterbox）與 `bathroom_tiled.png`
    （一般照片）重跑，裁切結果與退回前完全一致（左50/右30/上0/下6 px、0px），確認非環景路徑未受影響。
  - 未動：SPEC/ROADMAP/WORKFLOW、其他任務的 `scripts/`、`config.py` 任何數值門檻。
  - 下一步：請 Opus 依 WORKFLOW.md §5 重新驗證這一處修正（含跑 `scripts/test_preprocess.py`），
    通過後 T-11／T-12 即可並行開工。
  - ⚠️ 上面「1024×1024」原本寫錯（實際是 1024×512），已由 Opus 複驗時更正。

- **Opus 複驗結果（2026-08-18）：✅ 通過**

  **決定性的一項：迴歸測試對舊程式碼實測會失敗。**
  把 `5c643fd` 的舊 `preprocess.py` 複製到暫存目錄、配上新的測試腳本執行——
  `exit 1`，錯誤訊息正是「極點均勻的合成 equirect 被誤判為非環景」。
  對新程式碼則 `exit 0` 全過。**這證明測試有真實診斷力，不是只會亮綠燈的裝飾**
  （這一項若沒驗，整個修正的可信度就是零）。

  | 檢查項 | 方法 | 結果 |
  |---|---|---|
  | 缺陷是否真的修好 | 舊碼跑新測試 / 新碼跑新測試 | ✅ 舊碼 exit 1、新碼 exit 0 |
  | 真實環景不再靠僥倖 | `SteinmanHall.jpg` 重跑，讀 `meta.json` | ✅ 四邊 0px、`skipped_equirect: true`、6 視角 |
  | 非環景路徑沒被連帶弄壞 | corridor／bathroom／cgi_cave 新舊碼逐張比對 | ✅ 三張裁切量**完全一致**（50/30/0/6、0、上1） |
  | 六視角是真的內容 | 亮度 std + 兩兩 `array_equal` | ✅ std 43–61、無重複視角、非空白 |
  | 是否偷放寬門檻蒙混過關 | `git diff` 看 `config.py` | ✅ **完全未變動**，不是靠改容差過關 |
  | 旁路 | grep 全專案呼叫點 | ✅ `detect_and_crop_border` 只剩非環景分支一個呼叫點 |
  | 錯誤處理 | 不存在檔／非圖片／缺參數／傳目錄 | ✅ 四種都清楚中文訊息＋exit 2，無 traceback |
  | 範圍 | `git show --stat` | ✅ 只動 `preprocess.py` ＋新增測試腳本＋三份文件；未動 SPEC/ROADMAP/WORKFLOW |

  **複驗時另外發現的既有限制（不是這次造成的，不阻擋）**：
  **帶 letterbox 外框的 equirect 會被靜默當成一般照片。** 實測合成一張真 equirect
  外加左右各 40px 黑框（長寬比 2.156，超出 ±5%）→ `is_equirect` 判 False、不產生視角、
  而且黑邊裁切還順手吃掉了 30 列極點。
  **但拿舊程式碼跑同一張圖，結果一模一樣（也是 False）**——所以這是既有限制，
  不是這次修正引入的迴歸，不構成退回理由。
  只是它屬於本專案已被燒過三次的「安靜地輸出看似合理的錯誤結果」那一類，建議日後補強：
  非環景裁切完後，若裁後長寬比落進 2:1 容差內就印警告（提示「這可能是被裱框的環景圖」）。
  已入 HANDOFF 地雷第 11 條。

  **仍未處理的三個小瑕疵**（Sonnet 已明確聲明本輪範圍只限順序缺陷，合理）：
  可變物件當預設參數、`view_el+45.png` 檔名含 `+`、傳目錄時訊息說「找不到檔案」。

### T-11 幾何估計模組（metric depth → 房間尺寸/體積）
- **狀態**：⬜ 未開始
- **前置**：T-10
- **對應 SPEC**：F-02、F-09（尺寸覆寫）
- **產出**：`src/image_reverb/geometry.py`、`output/geometry/REPORT.md`（評測報告）
- **執行步驟**：
  1. 模型換成 **metric depth**：`depth-anything/Depth-Anything-V2-Metric-Indoor-Small-hf`
     （transformers depth-estimation pipeline，與 T-05 同款用法，但輸出是**公尺**）。
     下載前告知使用者大小並徵求同意。**禁止退回相對深度模型**（T-05 已否定該路線）
  2. 輸入一律先過 T-10 前處理（裁黑邊；環景則對各視角分別估深度）。
     沿用 T-05 REPORT §7.3 的防呆：濾掉極遠區域（窗外/天空/消失點）、clamp 異常值
  3. 從 metric 深度估 ShoeBox 尺寸（MVP 簡化為長方體）：以深度 robust 統計（p5/p50/p95）
     ＋假設相機水平 FOV（EXIF 有就用，沒有預設 60°）推進深/寬/高；環景用多視角深度合併估四壁距離
  4. **尺度校驗**（不是主路線）：若分割結果中有 door 類別，用門高 ~2.0m 反推尺度並與 metric 深度比對，
     偏差 > 50% 時在輸出標 `confidence: low` 警示
  5. **評測關卡（本卡的通過條件）**：對已知尺寸的照片實測並寫進 `output/geometry/REPORT.md`：
     浴室（實際進深 2.5–3.5m）、飯店走廊（~30m）、車內（~2m）、體育館（~150m）。判準：
     一般室內（浴室、走廊近端）尺寸誤差 ≤ ±30%；車內與超大空間**允許數字不準，
     但必須輸出 `confidence: low`**，不得給出自信的錯誤數字。
     達不到 → 狀態改 🔴 卡關，把誤差表寫進 REPORT，回報 Fable 重新決策（這是設計內的結果）
  6. 手動覆寫：CLI 參數 `--override-dims 長x寬x高`（公尺），覆寫後下游一律用覆寫值，
     且輸出 JSON 標記 `dims_source: "manual"`
- **自我檢查**：
  - bathroom 估出的進深誤差 ≤ ±30%（對照實際 2.5–3.5m）
  - 車內照片的輸出含 `confidence: low`，而非自信的錯誤數字
  - `--override-dims 4x3x2.5` 後，輸出 JSON 的尺寸就是 4×3×2.5 且標 `manual`
  - `output/geometry/REPORT.md` 有逐場地誤差表（不是空泛的「都很好」）
- **Opus 驗證重點**：REPORT 誤差表誠實、沒有只挑好看的照片；確認程式真的在用 metric 模型的公尺輸出
  （紅旗：又拿相對深度自己正規化）；評測關卡判準沒有被改寬鬆
- **交接筆記**：

### T-12 材質模組（表面分割 + 二階材質分類 → 逐表面吸音係數）
- **狀態**：⬜ 未開始
- **前置**：T-10（可與 T-11 並行）
- **對應 SPEC**：F-03、§6、F-09（材質覆寫）
- **產出**：`src/image_reverb/materials.py`（材質表模組）、`src/image_reverb/surfaces.py`
  （分割＋二階分類）、`gen_ir_manual.py` 逐表面支援、重生的試聽對照組
- **執行步驟**：
  1. 把 `data/materials.json` 的讀取模組化成 `src/image_reverb/materials.py`
     （沿用 T-03 的 load/get/alpha 介面），補上「JSON 存在但損毀」的清楚錯誤訊息（T-03 交接筆記的坑）
  2. **【約束 A——Phase 0 實證的硬性需求】定義逐表面材質資料結構**：
     `SurfaceMaterials`＝floor / ceiling / 四面牆（north/south/east/west）**六個面各自**的材質 id
     與六頻段 α。**禁止全域套用單一材質**——Phase 0 實測全鋪地毯 vs 只有地板鋪地毯，
     低頻 RT60 差 **11.8 倍**（4.093s vs 0.348s），使用者試聽形容「像用手拍鐵筒子」。
     傳入 pyroomacoustics 時用 ShoeBox 原生的 per-wall `pra.Material` dict（技術上無障礙）
  3. 改 `scripts/gen_ir_manual.py`：`--material <id>` 之外新增逐表面介面
     `--materials floor=carpet,ceiling=gypsum_board,walls=gypsum_board`（材質 id 以
     `--list-materials` 實際輸出為準）。未指定的面預設石膏板類牆面材質，**不是**複製地板材質。
     保留舊的 `--material`（全六面同材質）但執行時印警告「⚠️ 單一材質套六面是不現實的模型（T-03）」
  4. `surfaces.py` 兩階段辨識：
     a. SegFormer ADE20K 分割（沿用 T-06 的模型與腳本邏輯）→ 只取**幾何角色**：
        哪些像素屬於地板/天花板/牆面/大面積物件
     b. 對每個表面區域 crop 後跑 **CLIP zero-shot 分類**（transformers 的
        zero-shot-image-classification pipeline，候選標籤＝materials.json 的 12 種材質的英文描述）。
        ADE20K 的 `floor`/`wall` **類別語意不採信**（T-06 實證：滿鋪地毯 70.4% 判成 floor）。
        語意可信的類別（mirror、window、curtain 等 output/seg/REPORT.md §4 的 🟢 級）可直接映射。
        CLIP 模型下載前徵求使用者同意
  5. 信心 gating：二階分類 top-1 機率低於閾值（config 可調，預設 0.4）→ fallback `generic_wall`
     並在輸出 JSON 記 `warnings`；封閉空間出現 `sky` 類別 → 加「模型在猜」全圖警示（T-06 防呆規則）
  6. **驗證「鐵筒子」缺陷已修復**：用逐表面材質重生地毯房間 IR
     （floor=carpet、其餘=石膏板，4×3×2.5m）：
     a. 量測 125Hz 頻段 RT60 應 ≈ 0.35s（±20%），不再是全 carpet 的 4.09s
     b. 重跑 HANDOFF §5 的試聽對照組（marble / default / carpet 逐表面版），
        **請使用者試聽確認鐵筒子聲消失**（這是本卡的必要通過條件，AI 不能代勞）
- **自我檢查**：
  - 逐表面 API：floor=carpet＋其餘石膏板的 125Hz RT60 ≈ 0.35s；全 carpet 仍 ≈ 4.09s——
    兩者明顯不同，證明 per-wall 真的生效
  - 對 corridor（滿鋪地毯走廊）跑兩階段管線，地板區域被二階分類器判成 carpet
    （修正 T-06 的 29.6% 問題）；若判錯，誠實記錄在交接筆記，不改判準
  - 車內照片輸出帶警示（低信心 fallback），而非安靜輸出 wall
  - 試聽對照組已重生並請使用者聽過，回饋記錄在交接筆記
- **Opus 驗證重點**：per-wall 材質真的逐面傳進 pyroomacoustics（紅旗：先把六面 α 平均再套用——
  這等於繞過約束 A）；CLIP 分類是真的跑模型而非 hardcode 對照；信心 gating 有警示輸出
- **交接筆記**：

### T-13 聲學參數計算（Sabine/Eyring → 逐頻段 RT60、pre-delay）
- **狀態**：⬜ 未開始
- **前置**：T-11、T-12
- **對應 SPEC**：F-04
- **產出**：`src/image_reverb/acoustics.py`
- **執行步驟**：
  1. 輸入：房間尺寸（T-11 或手動覆寫）＋逐表面六頻段 α（T-12）。
     輸出 JSON schema：`dims`、`volume`、`surfaces`（逐表面材質）、`rt60_bands`（六值）、
     `predelay_ms`、`confidence` / `warnings`（從上游透傳）
  2. **【約束 B——Phase 0 實證的硬性結論】RT60 必須逐頻段獨立計算**：
     對 125/250/500/1k/2k/4k Hz 六頻段，各自用該頻段的 Σ Sᵢ·αᵢ(band) 算 Sabine 與 Eyring。
     **禁止把六段 α 平均後算單一寬頻 RT60**——Phase 0 實測地毯房間 125Hz RT60=4.093s、
     4kHz=0.126s（差 32 倍）；平均 α 算出 0.267s，實測 T30 卻是 4.023s，**差 15 倍**，
     因為殘響尾巴完全由低頻決定。程式裡不得存在「mean(α) → RT60」的計算路徑。
     若要給單一代表值（顯示用），必須從頻段結果取（如 500Hz/1kHz 平均）並命名為 `rt60_mid`，
     不可由平均 α 重算
  3. 大空間加空氣吸收項（Sabine 的 4mV 修正，20°C/50%RH，m 隨頻段變化）——
     T-01 已證實 hall 級空間高頻空氣吸收顯著（4.55s vs 理論 6.04s）
  4. pre-delay：由房間尺寸與聲源/麥克風假設位置（config 預設）算直達距離 → ms
  5. **迴歸自檢（數字直接對照 T-03 卡的實測表）**：
     a. 全 carpet 六面（4×3×2.5m）：125Hz ≈ 4.09s、1kHz ≈ 0.22s、4kHz ≈ 0.126s
     b. floor=carpet＋其餘石膏板：125Hz ≈ 0.348s、1kHz ≈ 0.764s、4kHz ≈ 0.401s
     c. 誤差各 ±10% 內（同公式同輸入，理應幾乎一致）
- **自我檢查**：
  - 輸出 JSON 的 `rt60_bands` 恆為 6 個值；不存在由平均 α 算出的欄位
  - 迴歸自檢 a、b 兩組六個數字全部落在 ±10%
  - `grep -n "mean" src/image_reverb/acoustics.py` 逐一人工確認沒有 α 平均進 RT60 公式的路徑
  - Eyring 與 Sabine 在高 α（>0.3）時的差異有呈現（Eyring 較短），低 α 時兩者趨近
- **Opus 驗證重點**：**約束 B 的紅旗＝程式裡任何「先平均 α 再算 RT60」的路徑**（包括藏在
  「顯示用摘要值」裡的）；空氣吸收對大空間高頻確實有效果（開/關比較）；迴歸數字不是 hardcode
  （改輸入尺寸後數字要跟著變）
- **交接筆記**：

### T-14 IR 合成引擎 v1（image-source 早期 + shaped-noise 晚期）
- **狀態**：⬜ 未開始
- **前置**：T-13
- **對應 SPEC**：F-05、§5 路線 A+B
- **產出**：`src/image_reverb/ir_synth.py`、試聽檔一組
- **執行步驟**：
  1. 早期反射（路線 A）：pyroomacoustics ShoeBox image-source，**用 T-12 的逐表面材質**
     （不是單一 α），取前 ~80–100ms
  2. 晚期殘響（路線 B）：六頻段 shaped-noise——白噪音過八度頻段濾波器組（Butterworth），
     每頻段按 T-13 的 `rt60_bands[band]` 做指數衰減，疊加後與早期反射在交接點做能量匹配的 crossfade
  3. 輸出 48kHz/24bit mono WAV、峰值 -3dBFS；IR 長度 ≥ max(rt60_bands) × 1.2（避免截尾，T-03 的坑）
  4. **閉環驗證**：對合成出的 IR 獨立量測各頻段 T30（Schroeder 積分，量測程式碼與合成程式碼分離），
     與輸入的 `rt60_bands` 比對，各頻段誤差 < 20%（SPEC §4 非功能需求）
  5. 產生試聽檔：clap＋（若 `assets/dry/` 有真實人聲/樂器則優先）對 small 房間（逐表面地毯版）
     與 hall 兩組，`convolve.py --mix 0.6`，**請使用者試聽**，以 T-02 的「還算自然」為基準線求進步
- **自我檢查**：
  - 逐表面地毯房 IR 的量測 T30：125Hz 對目標誤差 < 20%，且無鐵筒子聽感
  - hall 的 IR 與 T-01 純 image-source 版本試聽對照，不得明顯劣化
  - IR 尾端無突然截斷（最後 10% 樣本 RMS 顯著低於整體）
  - 使用者至少試聽一次並記錄回饋
- **Opus 驗證重點**：晚期不是未 shaping 的白噪音直接貼上（頻譜應隨時間高頻先衰減）；
  T30 量測程式與合成程式是獨立實作（紅旗：量測函式直接回傳輸入值）；crossfade 點無能量跳變
- **交接筆記**：

### T-15 CLI 整合（照片 → IR WAV + 分析報告 JSON）
- **狀態**：⬜ 未開始
- **前置**：T-14
- **對應 SPEC**：F-01、F-06、F-07、F-09
- **產出**：完整命令 `python -m src.image_reverb <photo> -o output/<name>/`
- **執行步驟**：
  1. 串起全鏈：T-10 前處理 → T-11 幾何 → T-12 材質 → T-13 參數 → T-14 IR
  2. 輸出到 `output/<name>/`：`ir_mono.wav`（48kHz/24bit）、`ir_stereo.wav`
     （簡單 decorrelation：晚期 noise 用兩個不同 seed 生成左右聲道，早期共用）、
     `analysis.json`（T-13 schema＋各階段 warnings 彙整）、`wet_preview.wav`（自動用 clap 卷積）
  3. 手動覆寫參數透傳：`--override-dims 長x寬x高`、`--override-material floor=carpet`
     （可多次指定不同表面）。RT60 直接覆寫不做（SPEC 列 P1）
  4. 錯誤處理：非圖片/壞檔 → 清楚中文錯誤訊息、exit code ≠ 0；
     low confidence → stderr 印警示但仍完成輸出（警示同時進 analysis.json）
  5. 印出總耗時，對照 SPEC §4 目標 ≤ 60 秒（超過不擋驗收，但要記錄）
- **自我檢查**：
  - 9 張測試照片全部跑完不 crash（車內、CGI 洞窟允許 low-confidence fallback，但必須有輸出與警示）
  - 所有輸出 WAV 過 `check_audio.py`：48kHz、非靜音、無爆音
  - `analysis.json` 的數值與各模組單獨執行的結果一致（抽 1 張人工比對）
  - 給壞輸入（文字檔改名 .jpg）→ 清楚錯誤、exit ≠ 0
- **Opus 驗證重點**：乾淨環境（新 shell、只靠 requirements.txt）end-to-end 重跑成功；
  JSON 與中間模組輸出一致；覆寫參數真的生效到 IR（覆寫前後 IR 應不同）
- **交接筆記**：

### T-16 分析視覺化（材質疊圖 + 參數報告）
- **狀態**：⬜ 未開始
- **前置**：T-15
- **對應 SPEC**：F-08
- **產出**：`src/image_reverb/visualize.py`、每張照片的 `output/<name>/analysis.png`
- **執行步驟**：
  1. matplotlib 拼版單張 PNG：原圖（前處理後）｜表面分割疊色圖（標二階分類的材質名與 α@1kHz）｜
     深度圖｜六頻段 RT60 長條圖｜文字欄（尺寸/體積/pre-delay/confidence）
  2. 有 warnings 的照片，PNG 上顯著標示警示文字（如車內的 low-confidence）
  3. 環景照片：顯示投影後的主視角並註明「環景已展開為 N 視角」
  4. 掛進 CLI：預設產生，`--no-viz` 可關
- **自我檢查**：
  - 9 張照片各有 analysis.png，圖上材質標籤與 analysis.json 一致
  - 車內那張 PNG 上看得到警示字樣
  - RT60 長條圖的六個值與 JSON 的 `rt60_bands` 一致
- **Opus 驗證重點**：視覺化的數字直接取自 JSON，不是另外重算（紅旗：兩邊數字不一致）
- **交接筆記**：

### T-17 MVP 驗收（SPEC §7 四項標準，Opus 主導）
- **狀態**：⬜ 未開始
- **前置**：T-16
- **對應 SPEC**：§7
- **產出**：`output/mvp_acceptance/REPORT.md`
- **執行步驟**：
  1. **§7-1 盲聽配對**：5 類空間照片（浴室、客廳/臥室、大空間、走廊/樓梯間、車內）各生成 IR 與 wet 檔，
     檔名打亂後請使用者盲聽配對空間類型，目標 ≥ 4/5
  2. **§7-2 RT60 對照**：8 個對照場地（環景經 T-10 投影，全部可用）跑完整管線，
     量測生成 IR 的各頻段 RT60 vs 真實 IR 的 T30，目標各頻段誤差 < 20%。
     逐場地逐頻段列誤差表，**不得只挑會過的場地**。必測反例 `racquetball_court_4`
     （最小空間、最長殘響 3.538s）：若被做成短殘響，直接記為未達標項
  3. **§7-3 外部相容性**：匯出 WAV 請使用者載入任一 convolution reverb（如 Logic 的 Space Designer）
     確認可正常使用
  4. **§7-4 人耳試聽**：每個場地的 wet 檔請使用者聽，記錄鐵筒子類 artifact 與整體聽感
  5. 彙整成 REPORT.md：達標/未達標逐項列，未達標項寫明量化差距與可能原因，交 Fable 決定
     是否加 Phase 1.5 修正輪
- **自我檢查**：REPORT.md 四項標準都有結果（含未達標的誠實記錄）；使用者的盲聽與試聽回饋已記錄
- **Opus 驗證重點**：誤差表完整涵蓋 8 場地 × 6 頻段；盲聽流程真的是盲的（檔名不洩露答案）；
  失敗案例的記錄足以讓 Fable 判斷下一步
- **交接筆記**：
