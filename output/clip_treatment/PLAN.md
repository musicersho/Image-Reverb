# T-38B PLAN — 有界提示詞實驗（round7～round10）

> **本檔在任何一輪 round7～10 執行前寫成並 commit。**（Opus 驗證重點之一：
> 「假設是跑完才補寫的」——本檔 commit 時間必須早於各輪 ROUND.md 的 commit
> 時間，可用 `git log --format='%h %cI %s'` 對照佐證。）

## 0. 依據

比較基線固定為 `round0_baseline`（overall 31/76、floor 4/13、in-set 誤判 9），
不是 T-36 的 52.4%／51.7%（HANDOFF_T38.md 地雷 C）。round0_baseline 的表 4
（`output/clip_treatment/rounds/round0_baseline/tables.md`）列出全部 9 個
in-set 誤判，正是 T-36 REPORT ①②④ 提到的四組混淆：

| 誤判組合（AI 判定 → ground truth） | 出現次數 | 照片／面 |
|---|---:|---|
| generic_wall → concrete | 4 | bedroom_ai_generated 四面牆 |
| acoustic_panel → carpet | 2 | site_photo_department_store floor、site_photo_gym floor |
| curtain_fabric → carpet | 1 | car_interior_suv floor |
| curtain_fabric → gypsum_board | 1 | site_photo_restaurant ceiling |
| curtain_fabric → glass | 1 | RacquetballCourt4 west |

`curtain_fabric` 一個候選就佔了 3 個誤判（跨 floor／ceiling／wall 三種
角色搶答），是單一改動預期影響面最大的候選。

## 1. 預算與變因規則

- 最多 4 個新輪次：round7、round8、round9、round10。round10 是否執行見
  §4 的**事前**條件，不得跑完才決定要不要算數。
- round7～9 **每輪只改一個候選的字串**，且是**累積式**（round8 的提示詞
  = round7 的提示詞再改一個候選；round9 累積 round7＋round8），這樣
  round9 完成時三個假設的**組合效果**已經測到，不必額外開一輪湊組合。
- 全部改動只動 `CLIP_MATERIAL_PROMPTS` 的字串值；不加減候選 id；不動
  `CLIP_OOD_PROMPTS`；不動門檻 0.4；不動 `classify_region_material()`／
  `compute_materials_confidence()`；不夾帶場地／照片特徵（過擬合紅線）。
- 每輪 78 面全量量測（跑 `t38_treatment_eval.py`，不得只挑錯的面調）。

## 2. round7～9 假設（先寫死，不得跑完再改用詞）

### round7 —— 改 `concrete`（父輪次 round0_baseline）

- **鎖定誤判**：generic_wall → concrete（4 面，bedroom_ai_generated）。
- **假設**：目前 `concrete`＝「a smooth poured concrete surface」與
  `generic_wall`＝「a plain smooth plastered wall」都在強調「smooth」，
  對灌漿混凝土牆的視覺特徵（冷灰色調、細微顆粒紋理）描述不夠，導致
  CLIP 在兩者之間更常選到語意較泛用的 generic_wall。改法：把
  `concrete` 的字串換成更強調材質本身視覺特徵（顆粒紋理、冷灰色調、
  可能上漆也可能裸面）的一般性描述，不提「牆」以外的場地細節。
- **新字串（固定，寫死）**：
  `"a poured concrete surface with a subtle grainy texture and a cool grey tone, whether bare or painted"`

### round8 —— 改 `acoustic_panel`（父輪次 round7，累積 round7 的 concrete 改動）

- **鎖定誤判**：acoustic_panel → carpet（2 面，department_store／gym
  的 floor）。
- **假設**：目前 `acoustic_panel`＝「a fibrous acoustic absorption
  panel」只描述材質本身的纖維質感，沒有任何線索排除「軟質地面覆蓋物」
  這個同樣纖維感很重的候選，導致地板的地毯常被判成 acoustic_panel。
  改法：加入「安裝在牆面／天花板上的硬質板材」這個一般性線索（描述
  安裝方式與剛性，非特定場地），與軟質地面覆蓋物做出區隔。
- **新字串（固定，寫死）**：
  `"a rigid fibrous acoustic foam or felt panel mounted on a wall or ceiling, not a floor covering"`

### round9 —— 改 `curtain_fabric`（父輪次 round8，累積 round7＋round8）

- **鎖定誤判**：curtain_fabric → carpet（1，car_interior_suv floor）、
  curtain_fabric → gypsum_board（1，restaurant ceiling）、
  curtain_fabric → glass（1，RacquetballCourt4 west）——同一個候選在
  三種角色（floor／ceiling／wall）都搶答成功，是本輪錯誤率最高的
  單一候選。
- **假設**：目前 `curtain_fabric`＝「a heavy fabric curtain or drape」
  只講材質類別，沒有描述外形（垂直懸掛、摺痕），導致地板紋理、天花板
  平面、玻璃反光都可能被誤判成布料垂墜的視覺特徵相符。改法：加入
  「垂直懸掛、有明顯摺痕」的外形描述，收窄它能匹配的視覺範圍。
- **新字串（固定，寫死）**：
  `"a heavy fabric curtain or drape hanging vertically in visible folds over a window or wall"`

## 3. 每輪的驗收讀法

每輪跑完後，對照 `round0_baseline` 讀三個數字（overall／floor／in-set
誤判）與表 4 的誤判清單是否真的把該輪鎖定的那幾面修正、有沒有製造新的
誤判（副作用）。這是**觀察記錄**，不是本卡的產品採用門檻判定——
產品採用門檻在 round9（或 round10，若執行）跑完後對 round0_baseline
做**最終**判定（§5）。

## 4. round10 是否執行——事前規則（不是跑完才決定）

**條件**：round9 完成後，若 round9 對 round0_baseline **同時**滿足
overall 上升＋floor 上升＋in-set 誤判不上升三個門檻 → **不跑 round10**，
直接進入 §5 收尾（round9 已經是達標候選，不需要用完預算）。

**否則**（round9 未同時滿足三門檻）→ 跑 round10，規則：
- 父輪次＝round9（累積），仍只改一個字串。
- 目標從 round0_baseline 表 4 的五組誤判中選：取 round9 跑完後
  **仍未修正、或本輪新製造**的誤判裡，出現次數最多的那一組
  （同分時取字典序在前的候選）；只能是 §0 表格裡本來就列出的組合
  之一，不得挑表外的新配對（避免過擬合到臨時觀察到的個案）。
- 修改的候選＝該誤判組合裡「ground truth 該有」但沒被選中的那個候選
  （例如仍是 generic_wall→concrete 沒修正，就再改 `concrete`；
  若是 curtain_fabric→glass 沒修正，就改 `glass`），寫法比照 round7～9：
  一般性材質視覺特徵描述，不夾帶場地特徵。
- 執行前把「本輪實際鎖定哪一組、為什麼」寫進 round10 的 `--hypothesis`
  參數與 ROUND.md，讓 Opus 可以對照本節規則檢查是不是照規則選的，不是
  臨時换目標。

## 5. 產品採用門檻（繼承原 T-38，不變）

以 round0_baseline 為基準（overall 31/76、floor 4/13、in-set 誤判 9）：
round9（若不跑 round10）或 round10（若有跑）**必須同時**：
1. overall 上升；2. floor 上升；3. in-set 誤判不上升。
持平（round4 型）不算通過。三者不能同時滿足 → 不採用任何提示詞改動，
`surfaces.py` 還原成 round0_baseline 字串（零 diff），REPORT.md 寫明
「提示詞治療輪否定結果」，交 Fable 收尾裁決。

若同時滿足 → 採用該輪（round9 或 round10）的 `CLIP_MATERIAL_PROMPTS`
字串作為 `surfaces.py` 正式內容並 commit，跑基線變化表（共同鐵則 8）＋
臥室紅旗檢查（共同鐵則 7）。
