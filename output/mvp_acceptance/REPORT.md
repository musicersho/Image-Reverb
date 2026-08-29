# MVP 驗收報告（T-17 / SPEC §7）

- **執行者**：Opus（T-17 卡明列「Opus 主導」）
- **執行日期**：2026-08-30
- **程式版本**：`git 61c448d`（T-18 驗證通過後的 main，`ir_metrics.py` 未再改動）
- **卡片狀態上限**：🔵 —— 依 **Fable 裁決 E**，照片來源網址未補齊前不得結案；
  且 §7-1／§7-3／§7-4 三項需要使用者本人操作，目前**尚未取得回饋**。

---

## 0. 結論摘要

| SPEC §7 標準 | 判準 | 結果 |
|---|---|---|
| §7-1 盲聽配對 | ≥ 4/5 | ⏳ **待使用者作答**（素材已備妥，見 §1） |
| §7-2 RT60 對照 | 500Hz–4kHz 逐頻段 ＋ 低頻聯合帶皆 <20% | ❌ **未達標**（自動組 0/8 場地、手動組 0/5 場地全達標） |
| §7-3 外部相容性 | 可載入任一 convolution reverb | ⏳ **待使用者操作**（格式已驗證，見 §3） |
| §7-4 人耳試聽 | 記錄聽感與 artifact | ⏳ **待使用者試聽**（9 個 wet 檔已備妥，見 §4） |

**一句話結論**：§7-2 明確未達標，且**病因已被隔離出來——不在幾何、也不在 IR 合成引擎，
而在材質辨識（CLIP）**。決定性證據是必測反例壁球場：自動路徑 −50%、換成官方標準尺寸
反而更差（−61%），但**只要把材質改對，同一支引擎立刻從 −50% 翻成 +13%（低頻聯合帶）**。
詳見 §2.4。

---

## 1. §7-1 盲聽配對 —— ⏳ 待使用者作答

**素材已備妥**：`output/mvp_acceptance/blind_test/`

| 檔案 | 內容 |
|---|---|
| `sample_1.wav` … `sample_5.wav` | 加了殘響的試聽檔（乾聲 ⊗ 生成 IR，mix=0.6） |
| `sample_N_IR.wav` | 對應的原始 IR（§7-3 載入 plugin 時用這個） |
| `作答表.md` | 請在此填答 |
| `../blind_test_ANSWERS.json` | 答案鍵，**作答完成前請不要打開** |

**盲性如何保證**（`scripts/t17_blind_test.py`，可重跑複驗）：

1. 檔名只有 `sample_N`，不含空間名、不含來源照片檔名。
2. 順序由**固定種子 20260830** 打亂——照原順序改名等於沒打亂，`sample_1` 會永遠是浴室。
3. 五個檔的 mtime 全部對齊成同一時間戳，避免用「檔案建立時間 = 生成順序」反推答案。

五個檔案皆已確認**非靜音**（RMS 0.0283–0.0357，遠高於 WORKFLOW §5 的 0.0001 門檻）。

> ⚠️ **已知限制**：乾聲目前只有 `assets/dry/clap_synth.wav`（numpy 合成拍手）。
> 真實說話乾聲是 HANDOFF §4「等使用者的事」的待補項。用拍手做空間類型配對比用人聲**難**，
> 因此本項分數會偏**保守**（低估），不會偏樂觀——這個方向的偏差對驗收是安全的。

---

## 2. §7-2 RT60 對照 —— ❌ 未達標

### 2.1 量測方法（裁決 B 執行要求）

| 要求 | 落實方式 |
|---|---|
| 生成 IR 與真實 IR 用**同一支未經修改**的量測管線 | 兩邊都走 `src/image_reverb/ir_metrics.py` 的 `band_t30()` 與 `t30_low_combined()`。`scripts/t17_rt60_table.py` 不重新實作任何量測邏輯 |
| `ir_metrics.py` 既有程式 T-17 期間 git diff 為空 | ✅ `git diff -- src/image_reverb/ir_metrics.py` **輸出為空**（本次驗收未動 `src/` 任何一行） |
| 聯合帶參數 88.4–353.6Hz 固定，不得逐場地調整 | ✅ 寫死在 `ir_metrics._LOW_COMBINED_*`，本報告全部場地共用同一組 |

**立體聲真實 IR 的處理**：EchoThief 五場地是 stereo。**不做聲道相加**——兩聲道相加會在高頻
產生梳狀濾波，污染 2k/4k 的量測。改為逐聲道各量一次 T30 取平均，逐聲道值保留在
`rt60_table.json` 的 `per_channel` 欄可供審查。

**截尾檢查**：每一筆都記錄 Schroeder 曲線最低點。13 條真實 IR 的曲線最低點落在
**−90dB 至 −inf**，−5→−35dB 的擬合區完全在資料內，**無截尾偏差**。

### 2.2 完整誤差表與分組達標率

完整表格（8 場地 ×（6 頻段＋聯合帶）、分組達標率、階梯比、手動尺寸依據）由
`scripts/t17_report_tables.py` 產生，見 **[tables.md](tables.md)**。以下摘錄關鍵結果。

**分組達標率（裁決 C：不得合併成單一數字）**

| 組別 | 五項硬判準通過 | 全達標場地 |
|---|---|---|
| **自動幾何**（`metric_depth` / `equirect_multiview`，F-01 產品主張本體） | **9/40（22%）** | **0/8** |
| **手動尺寸**（`manual`，F-09 正式出口） | **5/25（20%）** | **0/5** |

> **對自動路徑的單獨結論（裁決 C 要求）**：F-01 所主張的「照片 → 自動幾何 → IR」這條路徑，
> 在 8 個有真實 IR 對照的場地上**沒有任何一個場地通過 §7-2**，五項硬判準的整體通過率
> 只有 22%。**自動路徑目前不具備 SPEC §7-2 意義下的準確度。**
>
> 手動尺寸組（20%）**並沒有比自動組好**——這是本次驗收最重要的訊號之一：
> 把幾何換成（近似）正確的值幾乎沒有改善結果，代表**誤差的主導來源不是幾何**。

**逐 run 摘要**

| run | dims_source | conf | 500Hz–4kHz 通過 | 聯合帶 | 125Hz | 250Hz |
|---|---|---|---|---|---|---|
| `CathedralRoom` | equirect_multiview | medium | 0/4 | ❌ +186% | +45% | +191% |
| `DivorceBeach` | equirect_multiview | low | 0/4 | ❌ +676% | +373% | +651% |
| `site_photo_department_store` | metric_depth | medium | 1/4 | ❌ +121% | +77% | +113% |
| `t17_manual_department_store` | manual | high | 1/4 | ❌ +162% | +126% | +154% |
| `site_photo_gym` | metric_depth | low | 0/4 | ✅ −20% | −18% | −17% |
| `t17_manual_gym` | manual | high | 0/4 | ✅ −17% | −14% | −13% |
| `site_photo_restaurant` | metric_depth | low | 1/4 | ✅ −4% | −17% | −3% |
| `t17_manual_restaurant` | manual | high | 0/4 | ❌ +80% | +54% | +98% |
| `RacquetballCourt4` | equirect_multiview | medium | 0/4 | ❌ −50% | −68% | −46% |
| `t17_manual_racquetball` | manual | high | 0/4 | ❌ −61% | −76% | −52% |
| **`SteinmanHall`** | equirect_multiview | low | **4/4** | ❌ +30% | +17% | +47% |
| `t17_manual_steinman` | manual | high | 3/4 | ❌ +38% | +24% | +55% |
| `TunnelToHell` | equirect_multiview | medium | 0/4 | ✅ +0.2% | −40% | +2% |

**唯一接近達標的是 `SteinmanHall`**：500Hz–4kHz **四個頻段全部通過**（+16%／+6%／−3%／+9%），
只差低頻聯合帶 +30% 一項。這是 8 個場地中唯一一個「產品主張的自動路徑幾乎做對了」的案例。

### 2.3 裁決 B 的事後檢驗 —— 誠實回報：本資料集上聯合帶沒有改變低頻達標率

裁決 B 把低頻判準從逐頻段 125/250Hz 換成聯合帶，理由是逐頻段低頻是**不可信的量測**
（T-18 已由 Opus 獨立重現該混頻機制：異速鄰帶會讓 125Hz 量到 +105%）。
機制本身確實成立。但在本次 8 場地的實測上：

| 判準 | 13 個 run 中通過數 |
|---|---|
| 低頻聯合帶 | **4/13** |
| 逐頻段 125Hz | 4/13 |
| 逐頻段 250Hz | 4/13 |

**三者完全一樣。** 解讀：本資料集上，低頻誤差的主導來源是**模型預測本身就錯**
（誤差量級 +45% ～ +676%），遠大於裁決 B 要消除的量測混頻偏差（量級 ~+100%）。
換句話說——**裁決 B 是對的但不夠用：它修好了量測，可是被量測的東西本來就是錯的。**
這不是推翻裁決 B（量測正確性本身有獨立價值），而是說它不是 §7-2 未達標的原因。

**殘留風險檢查（裁決 B 自陳，逐場地列出）**：聯合帶上緣 354Hz 與 500Hz 帶共享邊緣，
若某場地 500Hz T30 比聯合帶慢 2 倍以上，聯合帶量測可能被拉長。
實測 8 場地的 `T30(500Hz)/T30(聯合帶)` 階梯比落在 **0.669 – 1.259**，
**沒有任何一個場地接近 ≥2 或 ≤0.5 的觸發區**（完整逐場地表見 tables.md 表 3）。
→ **裁決 B 自陳的殘留風險在本資料集上沒有發生。**

### 2.4 🔬 病因隔離：問題在材質辨識，不在幾何、不在 IR 合成引擎

必測反例 `racquetball_court_4`（最小空間、最長殘響）**被做成短殘響 → 依卡片規定直接記為未達標項**。
但更重要的是它讓病因被隔離出來。三個 run 用**同一支合成引擎**，只換輸入：

| run | 尺寸 | 材質 | 125Hz | 500Hz | 1kHz | 聯合帶 |
|---|---|---|---|---|---|---|
| `RacquetballCourt4`（自動） | 16.10×9.39×5.55（估錯） | CLIP：west=**curtain_fabric**、south=glass、floor=wood_panel | −68% | −50% | −41% | **−50%** |
| `t17_manual_racquetball`（F-09） | **12.19×6.10×6.10（官方標準尺寸）** | 同上（CLIP 未變） | −76% | −60% | −52% | **−61%** |
| `t17_diag_racquetball_hard`（診斷） | 同上官方標準尺寸 | **人工改對**：floor=wood_panel、其餘五面 concrete | **−3%** | +28% | +74% | **+13%** |

**推論鏈**：

1. 把幾何從「估錯的 16.1×9.4×5.6」換成「官方標準 12.19×6.10×6.10」，結果**不但沒好，還更差**
   （−50% → −61%）。→ **幾何不是主因。**
2. 幾何不動、只把材質改對，同一支引擎立刻從 −50% 變成 **+13%**（低頻聯合帶），
   125Hz 誤差 −3.3%。→ **材質就是主因。**
3. 具體的錯誤是 CLIP 把壁球場的一面牆判成 `curtain_fabric`（厚窗簾布）。壁球場裡不存在窗簾；
   而 `curtain_fabric` 是資料表中吸音最強的材質之一，一面就足以把 3 秒殘響吃成 1.4 秒。

這**直接印證 HANDOFF 地雷 #13**（「CLIP zero-shot 的 top-1 機率不能單獨當信心指標」）：
該筆判定並未觸發任何警示——`surfaces_sources` 顯示它是正常的 `clip` 結果，不是 fallback、
不是 out_of_domain。**模型高高興興地給了一個會毀掉整條 IR 的答案。**

> 診斷 run 剩下的 +28%～+74%（500Hz–2kHz 偏長）是另一個獨立議題：混凝土 α 極低、
> Sabine 在小而硬的空間高估、且引擎未建模空氣吸收。這一項**沒有被本次驗收隔離**，
> 留給 Fable 決定是否進修正輪。

### 2.5 🐛 新發現的缺陷（本次驗收發現，先前未記錄）

#### 缺陷 A（🔴 高）：`is_equirect()` 只看長寬比，把 2:1 的一般透視照誤判成 360° 環景

`TunnelToHell.jpg` 是 **2592×1296 = 正好 2.000** 的一般透視照片
（`SOURCES.md` 與 `INFO.md` 都明載「一般透視（iPhone 4）」、「✅ 可直接餵給深度／分割模型」）。
決定性佐證：**EXIF 記錄原始影像高度為 1936**（iPhone 4 的 4:3 感光元件），
`Software=Adobe Photoshop CS5` —— 這是一張被裁成 2:1 的透視照，不是球面全景。
目視也確認是單點透視消失點的隧道照。

`preprocess.is_equirect()` 的實作是：

```python
def is_equirect(img, aspect_ratio=2.0, tolerance=0.05) -> bool:
    """只看長寬比是否 ≈ 2:1（容差 ±5%），不看檔名。"""
    w, h = img.size
    return abs(w / h - aspect_ratio) <= aspect_ratio * tolerance
```

→ 這張照片被**靜默地**送進環景路徑，做了 6 次球面重投影。輸出：

| | 尺寸 | dims_source | confidence |
|---|---|---|---|
| 誤判走環景路徑（**產品實際行為**） | 10.48×2.48×6.67 | equirect_multiview | **medium** |
| 裁成 2400×1296 破壞 2:1 後走透視路徑（診斷） | 15.61×18.03×9.82 | metric_depth | low |

**兩個都錯**（真實是隧道，寬度約 3m 而非 2.48m 或 18.03m），但誤判那條路徑拿到了
**沒有依據的 `medium`**，而正確路徑至少誠實標了 `low`。

這是本專案「安靜地輸出看似合理的錯誤結果」的**第六次**
（前五次：地雷 #2 洞二、#9、#12、#13、#15）。
HANDOFF 地雷 #11 記錄的殘留限制是**反方向**的（帶外框的 equirect 被當成一般照片），
**這個正向誤判先前沒有被記錄過。**

#### 缺陷 B（🟠 中）：`--override-dims` 一律給 `confidence: high`，但材質仍是猜的

五個 `manual` run 全部回報 `confidence: high`，然而它們的**材質完全沒被驗證**——
且肉眼可見是錯的：

| run | CLIP 判定的地板 | 實際 |
|---|---|---|
| `t17_manual_department_store` | `acoustic_panel` | 賣場磨石／水泥地 |
| `t17_manual_gym` | `acoustic_panel` | 橡膠地墊 |
| `t17_manual_racquetball` | west 牆 = `curtain_fabric` | 硬質牆（§2.4 已證這一項毀掉整條 IR） |

`confidence` 只反映幾何來源，**卻是使用者唯一看得到的信任訊號**。
手動輸入尺寸後拿到 `high`，會讓使用者以為整份分析都可信。
建議（不在本卡範圍，交 Fable）：`confidence` 拆成 `geometry_confidence` 與
`materials_confidence`，或在 manual 路徑下以材質信心為準取 min()。

#### 缺陷 C（🟡 低）：戶外場地無結構性出口

`divorce_beach` 是戶外沙灘（SPEC 未排除此類輸入）。ShoeBox 房間模型在物理上無法表示開放空間，
結果是全表最大誤差（聯合帶 **+676%**、1kHz **+959%**）。管線有標 `confidence: low`，
但**沒有任何一條警示說「這看起來是戶外，本模型不適用」**——分割結果其實有 sky 類別可用
（T-06 防呆規則已經在偵測 sky，只是用途是打折材質信心，不是拒絕輸出）。

---

## 3. §7-3 外部相容性 —— ⏳ 待使用者操作

**格式已由 Opus 驗證**（`soundfile.info` ＋ `file`）：

```
output/bathroom_tiled/ir_mono.wav    48000Hz 1ch PCM_24 WAV
output/bathroom_tiled/ir_stereo.wav  48000Hz 2ch PCM_24 WAV
file → RIFF (little-endian) data, WAVE audio, Microsoft PCM, 24 bit, mono 48000 Hz
```

48kHz / 24-bit PCM / RIFF WAV 是 Space Designer、Altiverb 等 convolution reverb 的標準輸入格式，
**格式層面沒有已知障礙**。但 SPEC §7-3 要求的是「可直接載入並正常使用」——
這件事**只有使用者實際載入才算數**，Opus 無法代為驗證。

**請使用者做**：把 `output/mvp_acceptance/blind_test/sample_3_IR.wav`（最長的那條，
最容易聽出問題）載入 Logic 的 Space Designer 或任一 convolution reverb，確認：
① 能載入不報錯　② 有殘響效果　③ 長度看起來正常。

---

## 4. §7-4 人耳試聽 —— ⏳ 待使用者試聽

**素材已備妥**：`output/mvp_acceptance/listening/`（9 個 wet 檔，mix=0.6）

| 檔案 | 對應 |
|---|---|
| `cathedral_room__wet.wav` … `tunnel_to_hell__wet.wav` | 8 個對照場地的自動路徑輸出 |
| `DIAG_racquetball_correct_dims_and_hard_materials__wet.wav` | §2.4 的診斷 run |

**特別請使用者比較這一組**（這是本次驗收最有資訊量的一對）：

- `racquetball_court_4__wet.wav`（材質判錯，−50%）
- `DIAG_racquetball_correct_dims_and_hard_materials__wet.wav`（材質改對，+13%）

如果第二個明顯比第一個「更像壁球場」，就用耳朵獨立確認了 §2.4 的病因診斷。
**請一併記錄有沒有 HANDOFF 地雷 #9 那種「拍鐵筒子」的 artifact。**

> SPEC §7-4 的原文是「數字合理 ≠ 聽起來對」。反過來在本次也成立：
> **數字明確不合理時，也要用耳朵確認它到底錯得多離譜**——`divorce_beach` 的 +676%
> 應該會非常明顯。

---

## 5. 素材與方法的限制（誠實聲明）

這些限制**削弱**本報告的證據力，必須與結論一起讀：

1. **MIT 三場地不是嚴格的 photo↔IR 配對。** 各 `INFO.md` 原文明載
   「**不可**當成嚴格的 photo→IR ground-truth pair 來評分模型」——MIT 從未公開對應表。
   gym 有 3 條 IR（聯合帶 0.438 / 1.163 / 1.469 s，**相差 3.4 倍**）、restaurant 有 4 條
   （0.361 – 0.603 s）。本報告的處理是**不挑一條當真值**，取中位數為參考值並在表中標
   `🟡` 表示「對中位數超差但落在該場地多條 IR 的區間內」的弱命中。
   → **這 3 個場地的達標／未達標判定證據力弱於另外 5 個。**
2. **手動尺寸只有一個有權威來源。** `t17_manual_racquetball` 用的是國際壁球場公開標準
   （40×20×20 ft）；其餘四個是 **Opus 依照片估的**，逐項依據列在 tables.md 表 4。
   尤其 `t17_manual_restaurant` —— **那張照片只拍到一個卡座，室內尺寸根本不可見**，
   該筆數字幾乎是純猜測。→ **手動組 20% 的達標率不應被當成「給定正確幾何後的真實表現」**，
   它只是「給定 Opus 估的幾何後的表現」。
3. **EchoThief 的 IR 經過峰值正規化且可能經過修剪**，尾段若被處理過會讓真實側 T30 偏短。
   本報告未能獨立驗證這件事。
4. **§7-1／§7-3／§7-4 三項全部依賴使用者**，Opus 只能備妥素材。本報告在這三項上
   **沒有結果，只有待辦**——不得被讀成「已通過」。
5. **📷 照片來源網址仍未補齊**（`assets/SOURCES.md` §2，9 張全部）。依 **Fable 裁決 E**，
   這是結案前置：**本卡狀態最高停在 🔵**，不得改 ✅。

---

## 6. 給 Fable 的決策輸入

**已經有數據支撐的判斷：**

1. **修正輪應該打材質，不是打幾何。** §2.4 是決定性的：同一支引擎，只換材質就從 −50%
   翻到 +13%。而把幾何換成官方標準尺寸**反而更差**。目前 `T-11 換 Metric-Indoor-Large`
   的提案（ROADMAP 延後至 T-17 後評估）——**本次數據不支持優先做它**：
   手動組（近似正確幾何）達標率 20%，並沒有比自動組 22% 好。
2. **CLIP zero-shot 的域外處理還不夠。** 地雷 #13 加的 `__vehicle_interior` 之類選項救了車內，
   但壁球場那面牆是**在候選集內被判錯**（判成 curtain_fabric），域外選項救不到這種錯。
   需要的是另一個層次的對策（材質專用模型？空間類型先驗約束候選集？）。
3. **`is_equirect()` 必須修**（缺陷 A）。這是可以立刻修掉的靜默失敗：長寬比之外再加一個
   極點列均勻度檢查（equirect 的第一／最後一列依定義完全均勻，透視照不會）——
   HANDOFF 地雷 #11 已經記錄了這個性質，只是當時用在反方向。
4. **`confidence` 語義需要拆**（缺陷 B）：目前它只講幾何，卻是使用者唯一的信任訊號。

**需要 Fable 裁決的：**

- §7-2 未達標 → 加修正輪？還是接受現況、把 §7-2 的目標往後移到材質模組升級之後？
- 是否要為戶外／非矩形空間加「拒絕輸出」的出口（缺陷 C），還是列為 SPEC 適用範圍外？
- 診斷 run 剩下的 500Hz–2kHz +28%～+74% 偏長（§2.4 末），要不要單獨開卡追？

---

## 7. 可重跑複驗

本報告的每一個數字都由下列指令產生，無一手打：

```bash
source .venv/bin/activate
python scripts/t17_rt60_table.py      # 量測 → output/mvp_acceptance/rt60_table.json
python scripts/t17_report_tables.py   # 統計 → output/mvp_acceptance/tables.md
python scripts/t17_blind_test.py      # §7-1 盲聽素材（固定種子，可重現同一組打亂）
```

生成側 IR 的重跑指令逐一列在 `rt60_table.json` 的 `run` 欄；`manual` 組的
`--override-dims` 參數列在 tables.md 表 4。
