# HANDOFF_T44_FIX — 給 Sonnet 的 T-44 第二輪退回修正交接

> 建立者：Opus（驗證視窗，2026-09-07）｜對應退回：commit `4315e96`
> 「docs: T-44 Opus 第二輪複驗退回」
> **這張卡是純文件修正。不必重跑任何一輪、不必動任何程式碼、不必重算任何數字——
> 你要的數字我已經全部實跑核對好，直接抄本檔第五節的附錄。**

---

## 0. 先確認你是誰、範圍在哪

你是 **Sonnet（工兵）**。動工前必讀 [CLAUDE.md](CLAUDE.md)，本檔取代
「去翻 TASKS.md 猜要改什麼」的步驟。

**本輪只准動這 3 個檔**：

| 檔案 | 動哪裡 |
|---|---|
| `output/clip_treatment/REPORT_T44.md` | 只動第五節「同型近失」那一段的**最後兩句** |
| `TASKS.md` | 只動 T-44 卡的「四軸狀態」那一行的**工程軸**＋在「🔧 退回修正紀錄」補第 5 點 |
| `TODO.md` | 只動 T-44 那一條的工程軸文字 |

**⛔ 紅線（違反即再退回）**：
- 不准動 `src/`、`scripts/`、`data/`、`output/clip_treatment/rounds/`（本輪必須零 diff）。
- 不准動 T-44 卡的「狀態」欄裡任何**已存在**的退回理由文字——第一輪（2026-09-02）與
  第二輪（2026-09-07）兩份退回全文都要原封保留（WORKFLOW §7.3 舊 verdict 不覆寫）。
  你只能**在狀態欄最上方新增**一段「第二輪退回修正紀錄」。
- 不准動「四軸狀態」行的**實驗／產品／安全／MVP** 四個欄位（那是 Fable 裁決 T-45-A 的內容）。
- 不准改任何驗收門檻。若你認為門檻本身有錯，停手改走 WORKFLOW §7，去問 Fable。

---

## 1. 一句話現況

第一輪退回的唯一阻擋項（REPORT §7 與表 7' 矛盾）**Opus 已實跑核對、確認修好了**；
但上一輪（commit `98f1ace`）**自己新增的 REPORT §5 段落，末句又跟同一份報告的 §7
wall 表打架**，而且方向是把安全邊界講大約十倍。所以工程軸退回，改一句話就好。

---

## 2. 要改的第一件事（阻擋項）：REPORT_T44.md §5 末兩句

### 問題

檔案：[REPORT_T44.md:185](output/clip_treatment/REPORT_T44.md:185) 起那一段，最後寫：

> 這說明「候選集收窄→softmax 濃縮→信心膨脹」不是 `bathroom_tiled` 的孤例，
> 而是本卡 13 張測試集裡**離門檻最近的那一張先中**：`bathroom_tiled`
> 已經跨過門檻放行，`bedroom_ai_generated.floor` 是下一個最接近的候選。

**為什麼錯**：round17 全部 fallback 面裡，比 `bedroom_ai_generated.floor` 的 0.3394
**更接近** 0.4 門檻的有 **7 面**，最近的 `SteinmanHall.north` 只差 **0.0059**（不是 0.06）。
而這 7 面就明明白白寫在同一份報告 §7 的 wall 表「0.35 → 7 面」那一列。
§5 是「必須誠實揭露的已知殘留風險」章節，把最近距離講成 0.06 是**低報風險**，
這正是第一輪退回的同一種病（WORKFLOW §5.4.1／紅旗 #6：REPORT 摘要不得與程式產出的表矛盾）。

### 怎麼改

**把上面引用的那兩句（從「這說明」到段落結束）整段換成下面這段文字**，
其餘句子（開頭到「…僅差 0.06 就會越過 0.4 門檻改用 clip 判定。」）**一字不動**：

```markdown
這說明「候選集收窄→softmax 濃縮→信心膨脹」不是 `bathroom_tiled` 的孤例。
**但這句話必須限定範圍才誠實**：在**候選集實際被收窄**的角色（floor／ceiling）裡，
round17 只剩 2 個 fallback 面可比（`bedroom_ai_generated.floor` 0.3394、
`SteinmanHall.floor` 0.3309），`bathroom_tiled` 已跨過門檻放行，
`bedroom_ai_generated.floor` 確實是這個範圍內下一個最接近門檻的候選。
**不能推論成「全測試集裡最接近門檻的一面」**——依本報告第七節的 wall 表
（0.35 → 7 面），wall 側有 7 面比它更接近 0.4，最近的 `SteinmanHall.north`
只差 **0.0059**（0.3941），其次 `SteinmanHall.south` 0.3895、`stairwell_tiled`
四面各 0.3784、`SteinmanHall.east` 0.3578。這 7 面**不是本卡造成的**：wall 的候選集
在 round16 已完全還原成與全域相同的 12 條，實測 `round11_remap_baseline` 與 round17
的 48 個 wall 面 face 物件**逐位元完全相同**，屬本卡之前就存在的既有風險。
兩件事要分開講：本卡新增的膨脹風險集中在 floor／ceiling；而整個系統離 gate 門檻
最近的一面其實只有 0.0059 的餘裕，這是 T-47 gate 校準複審應該一併看的既有議題。
```

---

## 3. 要改的第二件事（次要）：TASKS.md 卡內兩個狀態欄打架

### 問題

T-44 卡的「狀態」欄現在是 🟠 退回，但下方 [TASKS.md:6612](TASKS.md:6612) 的
「四軸狀態」那行**工程軸**仍寫：

> 工程：**待複驗**（🟠 退回中：REPORT §7 敏感度摘要與表 7' 矛盾，純文件；由 **T-46** 修並複驗）

兩個問題：
1. 依 WORKFLOW §7.9，**TASKS.md 四軸才是單一事實來源**，`TODO.md`／`HANDOFF.md` 都要跟它同步。
   上一輪只改了「狀態」欄就去同步 TODO，同步錯了對象。
2. 「由 **T-46** 修並複驗」與事實不符：§7 的修正實際落在 commit `1121293`
   （2026-09-03 13:45，**早於** T-46 的工作 commit `7686462`），而 T-46 本身在
   `37e07fe` 仍是 🟠 退回，沒有修也沒有複驗這一項。

### 怎麼改

把「四軸狀態」那行**只有工程軸那一段**（到第一個 `｜` 為止）換成：

```
  工程：**待審**（第一輪阻擋項「REPORT §7 敏感度摘要與表 7' 矛盾」已於 `1121293`
  修正並經 Opus 2026-09-07 逐位元複核確認；第二輪退回的 §5 措辭已於本輪修正，
  待第三輪複驗。歷史沿革：原記「由 T-46 修並複驗」與事實不符，T-46 未處理此項且自身仍 🟠 退回）｜
```

**`｜` 後面的實驗／產品／安全／MVP 四段一個字都不要動。**

---

## 4. 要改的第三件事：同步 TODO.md ＋ 補修正紀錄

1. **TODO.md**：把 T-44 那一條的工程軸從 `🟠 **退回**（Opus 第二輪複驗…）`
   改成 `🔵 待驗證（第二輪退回已修：§5 措辭限定範圍＋補記 wall 側最近面；四軸／TODO 一致性已修）`，
   `｜實驗相對正向｜產品 🧪 **暫停採用**` 之後的內容不動。
2. **TASKS.md** 的「🔧 退回修正紀錄」段落**補第 5 點**，如實寫：本輪改了 §5 哪兩句、
   四軸工程軸怎麼改、TODO 怎麼同步，並註明 `src/`／`scripts/`／`data/`／`rounds/` 零 diff。
   **不要刪改既有的第 1～4 點。**

---

## 5. 附錄：Opus 已實跑核對的數據（直接用，不用重算）

### 5.1 round17 全部 fallback 面，依 top-1 信心排序（距 0.4 門檻由近至遠）

| 面 | top-1 | 信心 | 距門檻 | 角色候選集是否收窄 | round11 是否相同 |
|---|---|---|---|---|---|
| `SteinmanHall.north` | audience_seating | 0.3941 | 0.0059 | ❌ 未收窄 | ✅ 逐位元相同 |
| `SteinmanHall.south` | curtain_fabric | 0.3895 | 0.0105 | ❌ 未收窄 | ✅ 逐位元相同 |
| `stairwell_tiled.{n,e,s,w}` | brick | 0.3784 | 0.0216 | ❌ 未收窄 | ✅ 逐位元相同 |
| `SteinmanHall.east` | acoustic_panel | 0.3578 | 0.0422 | ❌ 未收窄 | ✅ 逐位元相同 |
| `site_photo_restaurant.west` | acoustic_panel | 0.3471 | 0.0529 | ❌ 未收窄 | ✅ 逐位元相同 |
| **`bedroom_ai_generated.floor`** | **concrete** | **0.3394** | **0.0606** | **✅ 已收窄** | **❌ 有變（0.2436→0.3394）** |
| `SteinmanHall.floor` | concrete | 0.3309 | 0.0691 | ✅ 已收窄 | ❌ 有變 |

→ **floor／ceiling（真正被收窄的角色）在 round17 只有最後那 2 個 fallback 面**，
所以「bedroom 是最接近的」限定在這個範圍內成立。
→ **48 個 wall 面 round11 vs round17 face 物件全部逐位元相同（0 個差異）**，已程式化驗證。

### 5.2 §7 與表 7' 的核對結果（第一輪阻擋項，已確認正確，不要再改）

- floor：0.20／0.25／0.30 三檔各放行 2 面、0 對 2 錯；0.35 起 0 面 —— ✅ 與表 7' 相同。
- `bedroom_ai_generated.floor` top-1 `concrete` 0.3394（報告寫 0.339）、次高
  `wood_panel` 0.2202（報告寫 0.220）＝ground truth —— ✅ `data/material_ground_truth.json` 確認。
- `SteinmanHall.floor` top-1 `concrete` 0.3309（報告寫 0.331）、gt `gypsum_board` —— ✅ 確認。
- wall 五檔 27(1/26)／22(1/21)／20(1/19)／7(0/7)／0 —— ✅ 與表 7' 逐格相同，
  且用表 7' 的 27 筆逐面信心自行重算門檻計數全部吻合。

**這一節已經是對的，本輪不要動它。**

### 5.3 交接筆記那段用詞（上一輪改的）也是對的，不要動

`compute_materials_confidence()`（[surfaces.py:412](src/image_reverb/surfaces.py:412)）
只讀 `sources`／`warnings`／六面材質 id，**不讀數值信心**，規則 1（floor 為 fallback）
先命中，所以 bedroom 兩輪 gate 同為 `low`——「gate 與 round11 相同」有機制層級的根據。

---

## 6. 自我檢查（收工前逐條實跑，把輸出貼進 DEV_LOG）

```bash
git diff --stat -- src/ scripts/ data/ output/clip_treatment/rounds/
```
↑ **必須完全沒有輸出**（零 diff）。

```bash
git status --porcelain
```
↑ 只該看到 `TASKS.md`／`TODO.md`／`DEV_LOG.md`／`REPORT_T44.md`（`AGENTS.md` 是未追蹤的既有檔，不要動它）。

```bash
source .venv/bin/activate && for f in scripts/test_*.py; do echo "=== $f ==="; python3 "$f" > /dev/null 2>&1; echo "EXIT=$?"; done
```
↑ 19 支必須全部 `EXIT=0`（會跑約 2–3 分鐘）。

```bash
grep -n "離門檻最近的那一張先中\|下一個最接近的候選" output/clip_treatment/REPORT_T44.md
```
↑ **必須完全沒有輸出**（舊的錯誤措辭已清掉）。

```bash
grep -n "由 \*\*T-46\*\* 修並複驗" TASKS.md
```
↑ **必須完全沒有輸出**（四軸工程軸的錯誤歸屬已修）。

再自己確認一次：兩份退回全文（2026-09-02 第一輪、2026-09-07 第二輪）都還在、一字未刪。

---

## 7. 收工程序（WORKFLOW §4）

1. TASKS.md：四軸工程軸 → **待審**；補「🔧 退回修正紀錄」第 5 點。
2. DEV_LOG.md：最上方加第 96 筆，寫清楚改了哪兩句、為什麼、實跑檢查的輸出。
3. TODO.md：同步（跟著**四軸**走，不是跟著「狀態」欄走）。
4. Commit：`T-44: 修正第二輪退回（REPORT §5 措辭限定範圍＋四軸一致性）(待驗證)`
5. `git push`

---

## 8. 給第三輪 Opus 複驗的重點（讓下一位驗證者省事）

- REPORT §5 末段是否已限定到 floor／ceiling，且有點名 wall 側最近面 0.3941／0.0059。
- 新措辭是否反過來又誇大成「wall 那 7 面是本卡造成的」——**不是**，48 面兩輪逐位元相同。
- 兩份退回全文是否原封保留；四軸／TODO／HANDOFF 是否三者一致（§7.9）。
- `src/`／`scripts/`／`data/`／`rounds/` 零 diff；19 支測試 EXIT=0。
- §7 與交接筆記那兩處**已於第二輪確認正確**，不必重驗，但要確認沒有被誤改。
