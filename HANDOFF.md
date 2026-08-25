# 交接文件 — 給下一個視窗

> 最後更新：2026-08-25（Fable 決策視窗）｜對應 commit：見 `git log --oneline -1`
> **新視窗請先讀 [CLAUDE.md](CLAUDE.md) 知道自己的角色，再讀本檔知道現在的狀況。**
>
> 驗證本檔是否過期：看 [DEV_LOG.md](DEV_LOG.md) 最上面一筆是不是 `2026-08-25 (16)`；
> 若已有更新的紀錄，以 DEV_LOG 為準。

---

## 一分鐘進入狀況

**Phase 0 已結案，現在是 Phase 1。**
**T-10 ✅｜T-12 ✅（Opus 驗證通過 2026-08-25）｜T-11 🟡 路線已定案，待執行決策補丁｜T-13 已解除封鎖。**

🔮 **T-11 路線決策已定案（Fable，2026-08-25）**：自動幾何適用範圍明訂「一般室內、
估計最大尺寸 ≤ 10m」（模型量程實證 ~20m 天花板、天花板前就開始壓縮）；
範圍外是正式行為分支——`confidence: low` ＋可操作警示，出口＝手動尺寸（F-09）或環景輸入。
±30% 判準數值一個字都沒改，改的是適用域。換大模型延後至 T-17 驗收後再評估。
**決策全文與理由在 TASKS.md T-11 卡「Fable 路線決策」，SPEC 已升 v0.3。**

🎧 「鐵筒子」缺陷已結案（使用者 2026-08-18 實聽確認），T-12 經 Opus 驗證通過——
約束 A（逐表面材質）的實證閉環完成。

---

## 0. 【現在該做的事】開 Sonnet 視窗執行 T-11 決策補丁（T-13 可並行）

> **模型選 Sonnet**，把下面這段貼進去：

```
執行 TASKS.md 的任務 T-11 的「決策補丁」步驟 7–9（Fable 已於 2026-08-25 定案路線，
決策全文在該卡「Fable 路線決策」一節，先整段讀完再動工）。
範圍僅限步驟 7–9，不要重寫既有實作。完成後執行卡上列的自檢與複測，
最後照 WORKFLOW.md 第 4 節做收工程序（T-11 獨立 commit，不要和別的卡混）。
```

> **可並行**：另開一個 Sonnet 視窗做 T-13（貼標準 Prompt「執行 TASKS.md 的任務 T-13…」）。
> 兩者不動同檔案（補丁動 `config.py`/`geometry.py`，T-13 動 `acoustics.py`）。
> T-13 開工必讀地雷 **#8**（逐頻段 RT60）與 **#14**（Sabine 與實測 IR 低頻差 2 倍，已入卡步驟 4b）。

### 決策補丁在做什麼（一分鐘版）

1. `config.py` 加 `GEOMETRY_SCOPE_MAX_M = 10.0`；`geometry.py` 加量程規則：
   透視照估出任一維 > 10m（環景：單面牆距 > 10m）→ `confidence: low` ＋建議
   `--override-dims` 或環景輸入的警示。與既有三條場景線索規則並存，取最嚴。
2. 重跑 9 張照片＋Steinman，REPORT.md 加「決策後複測」章節，用修訂後判準重評：
   **A'** 範圍內（浴室）≤±30%；**B'** 範圍外（走廊、車內、體育館）全部必須 low
   （走廊目前是 medium，補丁後必須翻成 low）。防濫殺對照：浴室與 Steinman 維持 medium。
3. Opus 驗證重點：走廊翻 low 是靠量程規則、不是 hardcode 場地名；
   `GEOMETRY_ERROR_TOLERANCE`（0.30）與 `CLIP_CONFIDENCE_THRESHOLD`（0.4）未被動過。

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
| T-08 | Phase 0 總結與路線決策 | ✅ **完成（Fable，2026-08-16）** |
| T-10 | 專案骨架與影像前處理（含環景投影） | ✅ **通過**（順序缺陷已修並經 Opus 複驗，2026-08-18） |
| T-11 | 幾何估計（metric depth → 房間尺寸） | 🟡 **路線已定案（Fable 2026-08-25）**，待 Sonnet 執行決策補丁步驟 7–9 |
| T-12 | 材質模組（逐表面材質） | ✅ **通過**（Opus 驗證 2026-08-25，含使用者試聽 ✅） |
| T-13~T-17 | Phase 1 其餘任務（已細化） | ✅ T-13 已解除封鎖，可與 T-11 補丁並行 |

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

## 3. T-08 的三個決策（✅ 已定案，2026-08-16，Fable）

1. **深度路線 → metric depth 模型**（Depth-Anything-V2-Metric-Indoor，與 T-05 同款 pipeline）。
   參考物（門 ~2.0m）降級為尺度校驗；手動尺寸覆寫升 P0。
   ⚠️ metric 模型在本專案照片上的精度未驗證 → **T-11 內建評測關卡**：先對已知尺寸場地實測，
   一般室內誤差 ≤±30% 才往下走，不達標就 🔴 卡關回報 Fable（設計內的結果，不是失敗）。
2. **材質路線 → 併用**：ADE20K 分割只管「切出表面的幾何角色」，材質標籤交給
   **CLIP zero-shot 二階分類器**（信心 gating + fallback 警示）；`floor`/`wall` 語意不採信。
3. **環景 → 做，最小範圍**：equirect→6 視角透視投影，放 T-10 前處理（純幾何運算、無新模型）。
   換到驗收場地 4 個 → 8 個全可用，並提前解掉 SPEC §8「視野外」風險。

IR 生成路線維持 A+B 混合不變（人耳已確認鏈路可用）。SPEC 已升 v0.2。

### ⚠️ 另有兩條「已定案、不需決策，但 T-08 細化任務卡時必須寫進去」的約束

這兩條是 Phase 0 實測出來的硬性結論，不是選項：

| # | 約束 | 影響的卡 | 實證 |
|---|---|---|---|
| A | **材質必須逐表面指定**（地板／天花板／各面牆分開），不可全域套單一材質 ✅ **已在 T-12 實作並經人耳確認（2026-08-18）** | T-12 | 全鋪地毯 vs 只有地板鋪地毯，低頻 RT60 差 **11.8 倍**（4.093s vs 0.348s）；舊版使用者試聽形容「像用手拍鐵筒子」，修好後實聽確認「沒問題」 |
| B | **RT60 必須逐頻段獨立計算**，不可用平均 α 算單一寬頻值 | T-13 | 地毯房間 125Hz RT60 = 4.093s、4kHz = 0.126s（差 32 倍）；平均 α 算出 0.267s，實測 T30 是 4.023s（**差 15 倍**） |

細節見本檔第 6 節地雷第 8、9 條，以及 [TASKS.md](TASKS.md) T-03 卡的交接筆記。

✅ **T-08 已把 A、B 兩條寫進任務卡執行步驟**：A → T-12 步驟 2（含 0.35s vs 4.09s 迴歸自檢
與使用者複聽關卡）、B → T-13 步驟 2（含「程式裡不得存在 mean(α)→RT60 路徑」的 Opus 紅旗）。

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
| `python scripts/test_preprocess.py` | T-10 前處理迴歸測試（合成資料，任何 clone 可跑） |
| `python scripts/gen_ir_manual.py small --materials floor=carpet,walls=gypsum_board` | **T-12 逐表面材質**生成 IR |
| `python -m src.image_reverb <photo> --geometry --materials-detect` | T-11 幾何＋T-12 材質完整分析 |
| `python -m src.image_reverb <photo> --override-dims 4x3x2.5` | 手動指定房間尺寸（F-09，不跑深度模型） |

環境：Python 3.9.6 / torch 2.8.0（MPS 可用）/ pyroomacoustics 0.10.1 / numpy 2.0.2。

### 產生材質試聽對照組（要請使用者用耳朵驗收時用）

`output/` 不進 git，所以這些檔案在新視窗／新 clone 都要重新產生：

```bash
python scripts/gen_ir_manual.py small                      # 預設 α=0.3
python scripts/gen_ir_manual.py small --material marble
python scripts/gen_ir_manual.py small --material carpet
for m in ir_room_small:default ir_room_small_marble:marble ir_room_small_carpet:carpet; do
  python scripts/convolve.py assets/dry/clap_synth.wav "output/${m%%:*}.wav" \
    "output/listen_${m##*:}.wav" --mix 0.6
done
```

聽感基準（2026-08-16 使用者實聽）：`marble` ✅ 自然、`default` ✅ 自然、
**`carpet` ❌「像用手拍鐵筒子」** ← 這是地雷第 9 條的模型缺陷。

**T-12 修好後的對照組（2026-08-18 產生，等使用者試聽）：**

```bash
python scripts/gen_ir_manual.py small --materials floor=carpet,walls=gypsum_board,ceiling=gypsum_board
python scripts/gen_ir_manual.py small --material carpet          # 舊的鐵筒子版（會印警告）
python scripts/convolve.py assets/dry/clap_synth.wav output/ir_room_small_surf_carpet.wav \
  output/listen_T12_surf_carpet.wav --mix 0.6
python scripts/convolve.py assets/dry/clap_synth.wav output/ir_room_small_carpet.wav \
  output/listen_T12_uniform_carpet.wav --mix 0.6
```

實測差異：125Hz T30 **3.952s → 0.748s**、低頻/高頻比 **48.8 倍 → 1.27 倍**。

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
9. **✅ 已修並經人耳確認（2026-08-18）｜`gen_ir_manual.py --material` 把單一材質套到全部六個面，是不現實的模型。**
   保留全文因為這是「數值驗證抓不到、只有耳朵抓得到」的經典案例。
   修法：T-12 的 `--materials` 逐表面介面（`floor=carpet,walls=gypsum_board`）；
   舊的 `--material` 保留但會印警告。實測 125Hz T30 3.952s→0.748s、低/高頻比 48.8→1.27 倍，
   **使用者 2026-08-18 實聽確認「沒問題」**。
   使用者試聽 carpet 版本後說「像用手拍鐵筒子」——追查證實殘響能量全集中在 30–135 Hz。
   根因：地毯低頻 α 只有 0.02，套到六面等於連天花板牆壁都鋪地毯；真實房間的牆是石膏板，
   125 Hz 的 α = 0.29（板共振吸音體專吃低頻）。量化：低頻 RT60 差 **11.8 倍**
   （4.093 s vs 0.348 s），低頻/高頻比從現實的 ~1 倍變成 **32 倍**。
   **→ T-12（材質模組）必須支援逐表面指定材質**（pyroomacoustics ShoeBox 原生支援 per-wall material）。
10. **小瑕疵待修**（不影響現有功能）：
   - `check_audio.py` 不帶參數時 `exit 0`，應為 `exit 2`
   - `test_segmentation.py` 在所有圖片都失敗時 `exit 0`，應為 `exit 1`（`test_depth.py` 已正確）
11. **✅ 已修（2026-08-18）｜equirect 前處理順序：要先判環景，再決定要不要裁黑邊——順序反了會裁到極點。**
   保留全文是因為這個「靜默失敗」的推理過程本身有價值，不是還沒修。
   修正內容：`is_equirect()` 改吃原圖、判定為環景就完全跳過裁切；
   迴歸測試 `scripts/test_preprocess.py`（對舊碼實測會 exit 1，有真實診斷力）。
   ⚠️ **殘留限制（既有，非本次引入）**：帶 letterbox 外框的 equirect（長寬比因外框超出 ±5%）
   仍會被靜默當成一般照片處理——實測舊碼新碼行為一致。真實 360 檔案通常沒有外框，風險低，
   但建議日後補：非環景裁切後若長寬比落回 2:1 容差內就印警告。
   equirect 影像的第一列就是「天頂那一個點」被拉伸成整列，依定義完全均勻；天底同理。
   若先跑黑邊偵測（用「純色邊框」判定）再判斷長寬比，均勻的極點列會被誤判成黑邊裁掉：
   合成實測裁 3 列 → 赤道在 768px 透視圖中偏移 3.8px；裁 ≥25 列 → 長寬比超出 ±5% 容差
   → **`is_equirect()` 直接翻成 False，整條環景路徑被靜默跳過**，360 圖被當一般照片處理。
   T-10 第一版就是這樣被 Opus 驗證退回的（2026-08-17）；唯一測得到的真實環景
   `SteinmanHall.jpg` 逃過裁切的餘裕剛好是 0.0（spread=3.0，門檻是 `<3.0`），純屬僥倖。
   **→ 判環景要用原圖判斷，且判定為環景就要整個跳過黑邊裁切**（equirect 是完整球面渲染，
   本來就不會有 letterbox）。這也是「安靜地輸出看似合理的錯誤結果」這一類（同地雷 #2 洞二、#9）。
   細節見 [TASKS.md](TASKS.md) T-10 卡「Opus 驗證結果」。

12. **🔴 metric depth 模型有量程上限，超出就安靜地給錯數字。**
   `Depth-Anything-V2-Metric-Indoor-Small` 在 9 張照片上的**最大預測距離全部落在 3.6–19.7 m**，
   從沒超過 ~20m。體育館實際 ~150m，模型全圖最遠只說 3.61m（誤差 −98%）——
   **任何公式都無法從 3.61m 推出 150m**，這不是參數調校問題。
   更要緊的是：**體育館那筆的深度統計完全正常**（clamp 比例 0、百分位平順、離上限很遠），
   只看深度輸出**無法發現它錯了 98%**。這是本專案第三次遇到「安靜地輸出看似合理的錯誤結果」
   （前兩次是地雷 #2 洞二、#9）。
   → 能發現的訊號在**分割**，不在深度：地板可見度 0.0%（vs 浴室 6.8%）、人群佔比、
   以及 T-12 的 CLIP 域外判定。已實作成 `geometry.apply_scene_cue_confidence()` 三條規則。
13. **🔴 CLIP zero-shot 的 top-1 機率不能單獨當信心指標。**
   softmax 在**封閉候選集**上永遠加總為 1，所以模型無法表達「以上皆非」——
   實測 SUV 車內的地板被判成 `curtain_fabric` **信心 0.760**、牆判成 `acoustic_panel` 0.489，
   **兩者都在 0.4 門檻之上，完全不觸發任何警示**。
   調高門檻無效：要 0.8 才擋得住車內，但那會連 corridor 天花板（0.599，判對的）一起擋掉。
   → 解法是在候選集**加入域外選項**（`__vehicle_interior`、`__outdoor_scene` 等），
   讓 softmax 有地方投「以上皆非」。修正後車內判為 `__vehicle_interior` 0.735 ＋明確警示。
   **任何未來要加 zero-shot 分類的地方都要記得這件事。**
14. **⚠️ Sabine 公式與實測 IR 在低頻差 2 倍以上（T-13 必讀）。**
   實測：逐表面 floor=carpet 的 125Hz，Sabine 算 0.348s、**實際量測 IR 是 0.748s**；
   六面全 gypsum 的 125Hz，Sabine 0.282s、實測 **0.772s**。
   但 500Hz 幾乎完全吻合（1.638 vs 1.634），全 carpet 的 125Hz 也吻合（4.093 vs 3.952）。
   用「六面均勻」當對照組確認**與逐表面改動無關**，是 α 高（0.29）時模擬 IR 與 Sabine
   的系統性偏差（小房間低頻非擴散場）。
   → **T-13 若只輸出 Sabine 數字，會與使用者實際聽到的差 2 倍以上**，
   又是「數字合理但東西是錯的」。建議以量測 IR 為準，或兩者並列。

### ⚠️ 數值驗證抓不到的錯誤

地雷第 9 條是這一輪最值得記住的教訓：那個錯誤的 RT60（4.023 s）**通過了 WORKFLOW §5 的全部三層檢查**
——落在合理區間 0.1–12 s、α 全在 0–1、無假實作、無 hardcode。
但模型本身是錯的，而且錯得離譜（低頻差 11.8 倍）。**是使用者的耳朵抓到的。**

**Phase 1 的驗收不能只靠數值範圍檢查。** 每次改動 IR 生成邏輯後，
都應該產生試聽檔請使用者實際聽過（`convolve.py` 跑一下就有）。
數字合理 ≠ 聽起來對。

### 給用 workflow 跑多 agent 的視窗

若你禁止 subagent 執行 git 與修改 TASKS/DEV_LOG/TODO（建議這樣做，避免並行衝突與造假），
**驗證者會回報「收工程序沒做、沒 commit」**——那是它不知道你的設計，屬誤判，
主控端自己核對後補做收工程序即可。本輪兩次都出現這個假陽性。

---

## 7. 標準交接流程

```
【結束舊視窗】
  貼：「執行 WORKFLOW.md 第 4 節收工程序」

【現在該做的 — T-11 決策補丁】（模型選 Sonnet）
  貼本檔第 0 節那段 Prompt（已針對補丁範圍寫好，可直接複製）

【可平行做 — T-13 聲學參數】（模型選 Sonnet，另開視窗）
  貼：「執行 TASKS.md 的任務 T-13。先讀 CLAUDE.md 和該任務卡的全部內容再動工，
      完成後執行任務卡裡的自我檢查，最後照 WORKFLOW.md 第 4 節做收工程序。」

【補丁／T-13 完成後 — 驗證】（模型選 Opus）
  貼：「你是驗證者，只審查不修改程式碼。請依 WORKFLOW.md 第 5 節的驗證標準，
      審查任務 T-XX 的成果：讀 TASKS.md 的該任務卡、讀相關程式碼、實際執行驗證指令。
      最後輸出：「✅ 通過」或「❌ 退回」＋具體理由。」
```

### ⚠️ 給下一個 Sonnet 視窗的提醒

- **T-11 補丁範圍僅限步驟 7–9**，不要重寫既有實作；T-11 獨立 commit，不要和別的卡混。
- T-13 開工時必讀地雷 **#8**（逐頻段算 RT60）與 **#14**（Sabine 與實測 IR 在低頻差 2 倍以上，
  已入卡為步驟 4b）。
- 新增 zero-shot 分類的地方必讀地雷 **#13**（softmax 無法表達「以上皆非」）。
