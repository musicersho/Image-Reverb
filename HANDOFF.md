# 交接文件 — 給下一個視窗

> 最後更新：2026-08-16（Opus 視窗）｜對應 commit：`a9d2ee7` 之後
> **新視窗請先讀 [CLAUDE.md](CLAUDE.md) 知道自己的角色，再讀本檔知道現在的狀況。**

---

## 一分鐘進入狀況

Phase 0（可行性驗證）**實質完成**。T-00~T-06 全部做完並通過驗證，只剩 T-07（選做、暫緩）
與 T-08（Fable 的路線決策）。

**Phase 0 的結論不是「可以做」，而是「原訂路線有兩個洞，要先補」。**
這是好事——Phase 0 的目的就是在投入 MVP 之前把不可行的路徑砍掉。

**下一步：換 Fable 做 T-08。** 三個必須決策的問題在本檔第 3 節。

---

## 1. 目前進度

| 卡 | 內容 | 狀態 |
|---|---|---|
| T-00 | 開發環境（`.venv`、`check_audio.py`） | ✅ 通過 |
| T-01 | 手動參數生成 IR（`gen_ir_manual.py`） | ✅ 通過 |
| T-02 | 離線卷積試聽（`convolve.py`） | ✅ **完全通過**（使用者試聽確認殘響自然） |
| T-03 | 材質吸音係數表（12 種材質） | ✅ 通過 |
| T-04 | 測試素材與對照 IR（9 照片 + 8 組 IR） | ✅ 通過｜🚧 照片來源網址待補 |
| T-05 | 深度估計測試（Depth Anything V2） | ✅ 通過｜🔴 產出否定性結論 |
| T-06 | 語意分割測試（SegFormer ADE20K） | ✅ 通過｜🔴 產出否定性結論 |
| T-07 | Image2Reverb baseline（選做） | ⏸️ 暫緩，使用者未授權下載 |
| T-08 | Phase 0 總結與路線決策 | ⬜ **下一步，Fable 做** |
| T-10~T-17 | Phase 1 MVP 框架 | ⬜ 等 T-08 細化 |

逐卡的詳細交接筆記在 [TASKS.md](TASKS.md) 每張卡的「交接筆記」欄，本檔不重複。

---

## 2. 這一輪推翻了什麼（最重要的部分）

Phase 0 的實測結果**否定了 SPEC 原本假設的兩個關鍵環節**。以下是證據，不是推測。

### 🔴 洞一：單張相對深度圖不能估房間體積

出處：[`output/depth/REPORT.md`](output/depth/REPORT.md) §7

- Depth Anything V2 輸出的是**每張圖各自正規化的相對 disparity**，不是距離。
- 實測 9 張照片，深度動態範圍與實際空間大小**沒有單調關係**：

  | 空間 | 實際進深 | 核心 p95/p5 |
  |---|---|---|
  | SUV 車內 | ~2 m | **91.5x** |
  | 浴室 | ~3 m | 5.5x |
  | 飯店長廊 | ~30 m | 12.7x |
  | 體育館 | ~150 m | **11.7x** |

  車內比體育館小好幾個數量級，深度範圍卻大 8 倍。
- 就算給絕對錨點用 `距離 = k/disparity` 換算也會壞：
  走廊消失點（disparity=0）推出 **3,747,829 公尺**；浴室實際 2.5–3.5 m，推得 5.50 m（**高估 60–120%**）。
- **後果**：Sabine 公式 RT60 ∝ V，體積誤差以平方/立方級放大到 RT60
  → **SPEC F-02 的「±30% 誤差目標」照現行路線做不到。**

### 🔴 洞二：ADE20K 分不出地毯，也認不得車內

出處：[`output/seg/REPORT.md`](output/seg/REPORT.md) §2.3、§2.9、§4

- **地毯**：飯店走廊滿鋪地毯，只有 **29.6%** 判成 `rug`、**70.4%** 判成 `floor`。
  換算吸音係數：`0.296×0.65 + 0.704×0.02 = 0.207`，正確值應是 `0.65`
  → **高頻吸音只剩 32%**。REPORT 結論：「`floor` 這個類別在本專案裡是不可信的」。
- **車內**：ADE20K 沒有任何車輛內裝類別。車頂內襯、窗外樹林（92.4%）、
  連車外橘色烤漆（100%）**全部判成 `wall`**。
- **最麻煩的性質**：模型對失敗**毫無自覺**，一律輸出高置信度結果——
  「會安靜地輸出看似合理的錯誤結果」。

### 💡 一個意外的機會：360° 環景

8 個對照場地的照片有 5 張是 equirectangular 環景（見 [`assets/SOURCES.md`](assets/SOURCES.md) §3.4）。

- **壞消息**：透視模型不能直接吃 → SPEC §7 驗收第 2 條目前只有 4 個場地可用。
- **好消息**：環景**沒有「視野外」**。SPEC §8 的已知風險「照片視野外的空間（背後的牆）未知」
  原本要靠 Phase 3 的影片輸入（F-20）才能解，用環景可以提早處理。

---

## 3. T-08 必須決策的三件事（Fable 的工作）

1. **深度路線**：改用 metric depth 模型（Depth-Anything-V2-Metric / UniDepth / Metric3D），
   還是保留相對深度但靠已知尺寸參考物（門 ~2.0 m、人 ~1.7 m）錨定 + 近距離限縮？
   這決定 SPEC F-02 的 ±30% 目標能不能達成，也可能要改 SPEC。
2. **材質路線**：ADE20K 的 `floor`/`wall` 不可信。要在分割後加「紋理／顏色二階分類器」，
   還是換材質專用模型（DMS、MINC 之類）？或兩者併用？
3. **環景處理**：要不要做「環景 → 多視角透視投影 → 融合」？做了可順便解掉 SPEC §8 的風險，
   但增加 Phase 1 範圍。

決策完成後，T-08 要把 Phase 1 的 T-10~T-17 補到可執行的細節（目前只有標題）。

---

## 4. 等使用者的事（AI 推不動）

- 📷 **補 9 張照片的來源網址** — `assets/SOURCES.md` §2 已標好待補位置。
  T-04 自我檢查第 2 項「SOURCES.md 每一項都有來源連結」目前**不符合**。
- 📷 **補一張真實的教堂／空場硬質大空間** — 現有大空間樣本全被人群主導（人是強吸音體），
  無法驗證長殘響情境。
- ❓ **T-07 要不要做** — Image2Reverb baseline，限時 2 小時，失敗是可接受結果。需授權 clone/下載。

---

## 5. 環境速查

```bash
cd "/Users/musicersho/Image Reverb"
source .venv/bin/activate          # 跑任何 python 前都要先做這件事
```

| 指令 | 用途 |
|---|---|
| `python scripts/check_audio.py <檔>` | 印取樣率/長度/聲道/RMS/峰值，RMS<0.0001 警告靜音 |
| `python scripts/gen_ir_manual.py small\|hall [--material <id>]` | 生成 IR（48kHz/24bit/mono，-3dBFS） |
| `python scripts/gen_ir_manual.py --list-materials` | 列出 12 種材質 id |
| `python scripts/show_materials.py` | 印材質吸音係數表 + 自動檢查 |
| `python scripts/convolve.py <dry> <ir> <out> [--mix 0.5]` | 離線卷積，輸出 -1dBFS |
| `python scripts/test_depth.py` | 深度估計批次處理 `assets/photos/` |
| `python scripts/test_segmentation.py` | 語意分割批次處理 `assets/photos/` |

環境：Python 3.9.6 / torch 2.8.0（MPS 可用）/ pyroomacoustics 0.10.1 / numpy 2.0.2。

---

## 6. 坑與地雷（避免下個視窗重踩）

1. **OpenAIR 已停站**，別再試。`openair.hosted.york.ac.uk` 與 `openairlib.net` 兩個域名
   都轉到主機商的 `suspendedpage.cgi`。已改用 EchoThief + MIT Reverb Survey。
2. **`assets/reference_irs/` 的 .wav/.jpg 不在 git 裡**（授權未允許再散布，只有 INFO.md 進版控）。
   全新 clone 需照各 `INFO.md` 的網址自行重新下載。
3. **`output/` 只有 `*.md` 進 git**。深度圖/分割圖 PNG、labelmap.npy、IR wav 都不在版控裡，
   全新 clone 需重跑腳本產生。
4. **YouTube 截圖的黑邊會毀掉深度正規化**。走廊那張的左右黑邊 disparity 7.88，
   比畫面內最近的木門 5.96 還高，是全圖最大值來源。**做任何深度處理前要先裁掉 letterbox/UI。**
5. **環景照片不能直接餵透視模型**（見第 2 節）。
6. **`racquetball_court_4` 是必測反例**：8 個場地裡空間最小，殘響卻最長（3.538 s，
   比大洞窟的 1.529 s 長一倍多），因為全是木頭與玻璃硬面。
   任何「空間看起來小就給短殘響」的天真規則在這裡一定爆掉。
7. **玻璃會被深度模型看穿**（淋浴門 disparity 1.28 vs 同距離馬桶 3.01）。
   鏡子這次沒失敗，但 REPORT 主動註明「這是簡單模式的鏡子」，不能當通則。
8. **🔴 絕對不能用「平均 α」算單一寬頻 RT60。** 以地毯房間為例，125 Hz 的 RT60 是 4.093 s、
   4 kHz 只有 0.126 s（差 32 倍）；六段 α 平均後算出的寬頻 RT60 是 0.267 s，
   但實測 T30 是 **4.023 s——差 15 倍**，因為殘響尾巴完全由低頻決定。
   **T-13（聲學參數計算）必須逐頻段獨立算 RT60。** 這是實證，不是規格潔癖。
9. **小瑕疵待修**（不影響現有功能）：
   - `check_audio.py` 不帶參數時 `exit 0`，應為 `exit 2`
   - `test_segmentation.py` 在所有圖片都失敗時 `exit 0`，應為 `exit 1`（`test_depth.py` 已正確）

### 給用 workflow 跑多 agent 的視窗

若你禁止 subagent 執行 git 與修改 TASKS/DEV_LOG/TODO（建議這樣做，避免並行衝突與造假），
**驗證者會回報「收工程序沒做、沒 commit」**——那是它不知道你的設計，屬誤判，
主控端自己核對後補做收工程序即可。本輪兩次都出現這個假陽性。

---

## 7. 標準交接流程

```
【結束舊視窗】
  貼：「執行 WORKFLOW.md 第 4 節收工程序」

【開新視窗 — 做 T-08】（模型選 Fable）
  貼 WORKFLOW.md §2.3 的規劃 Prompt，狀況描述用本檔第 2、3 節

【開新視窗 — 做 Phase 1 任務】（模型選 Sonnet）
  貼：「執行 TASKS.md 的任務 T-XX。先讀 CLAUDE.md 和該任務卡的全部內容再動工，
      完成後執行任務卡裡的自我檢查，最後照 WORKFLOW.md 第 4 節做收工程序。」

【每 1–3 個任務後】（模型選 Opus）
  貼 WORKFLOW.md §2.2 的驗證 Prompt
```
