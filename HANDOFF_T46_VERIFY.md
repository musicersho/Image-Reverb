# HANDOFF_T46_VERIFY — 給 Opus 的 T-46 v2 修正輪複驗交接

> 建立者：Sonnet（執行視窗，2026-09-09）｜對應結果 commit：`545ec5e`
> 「T-46: 依 criteria v2 修正輪，13/13 三項比對通過 (待驗證)」
> **本檔是複驗的路標，不是複驗本身。你仍須自己重建 B0、自己重跑腳本、自己讀程式碼——
> 本檔只負責告訴你「去哪裡看、對照哪一條、已知會出現的正常差異是什麼」，省你摸索的時間。**

---

## 0. 先確認你是誰、範圍在哪

你是 **Opus（驗證者）**。只審查、不修改程式碼；WORKFLOW.md §5 的驗證標準與本卡「Opus
驗證重點」都適用。你要複驗的門檻是 **[CRITERIA_T46_v2.md](output/role_flag/CRITERIA_T46_v2.md) §5**
（六點清單，逐條列在下面第 3 節），**不是** TASKS.md T-46 卡步驟 4 的 v1 原文（v1 已由 Fable
判 inconclusive、不得改判 PASS，見卡片 §8 變更紀錄）。

若判退回：把理由寫進 TASKS.md T-46 卡「狀態」欄最上方（**不覆寫**既有的 `37e07fe` 退回全文，
只新增一段），四軸工程軸改回「🟠 退回」；**不得**自己動門檻或自己放寬（WORKFLOW §7.1／§7.4）。

---

## 1. 一句話現況

T-46 v1 在 `37e07fe` 因兩個阻擋項被退回（v1 步驟 4 對 geometry／overall／gate 三項字面上不可
執行、腳本 docstring 與自己的輸出矛盾）；Fable 於 2026-09-08 依 WORKFLOW §7 開 criteria v2
（`2be2453`，把基線改成可執行的 B0＝commit `23f2aba` 真實 CLI 結果）；Sonnet 於 2026-09-09
依 v2 §4 逐字重跑（`545ec5e`），13/13 全部斷言通過，四軸「工程：🔵 待審（依 criteria v2）」，
現在交你複驗。

---

## 2. 這輪改了什麼（只改一個檔案＋程式產物，`src/` 零改動）

| 檔案 | 改動 |
|---|---|
| `scripts/t46_role_flag_baseline.py` | 新增 B0 建置（`git worktree` 重建 `23f2aba`＋自證守門＋產出 `BASELINE.md`）；移除 v1 的 `geometry_notes` 降級，改為 A2／A4／A5 硬斷言；快取指紋；`--out-dir` 絕對路徑修正；docstring／訊息重寫 |
| `output/role_flag/{REPORT.md,tables.md}` | 程式重生（覆蓋 v1 版本） |
| `output/role_flag/baseline_23f2aba/BASELINE.md` | 新增（程式產生，B0 的持久證據） |
| `TASKS.md`／`DEV_LOG.md`／`TODO.md`／`HANDOFF.md`／`HANDOFF_PHASE_1.9R.md` | 狀態同步（WORKFLOW §7.9） |
| `output/role_flag/CRITERIA_T46_v2.md` | **未改**（`git log` 只有 Fable 那一筆，見下方指令） |
| `src/` | **零改動**（`git diff --stat -- src/` 空，已驗證） |

---

## 3. 複驗清單（逐條對照 criteria v2 §5）

### §5 第 1 點：criteria commit 早於結果 commit

```bash
git log --oneline -- output/role_flag/CRITERIA_T46_v2.md
```
應該**只有一筆**：`2be2453 criteria: T-46 v2 …`。再確認它在 `git log --oneline -6` 裡排在
`545ec5e`（本輪結果 commit）之前。

### §5 第 2 點：自行重建 B0，`BASELINE.md` 與已 commit 版本比對；worktree HEAD＝`23f2aba` 全長

```bash
source .venv/bin/activate
python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/ --fresh
```
單張 CLI 約 13–34 秒，13 張 B0＋13×2 兩模式＝39 次真實 CLI，全程約 15–20 分鐘。跑完後：

```bash
git diff --stat -- output/role_flag/baseline_23f2aba/BASELINE.md output/role_flag/REPORT.md output/role_flag/tables.md
```

**⚠️ 重要澄清（本檔最重要的一段，請先讀完再判斷「不逐字相同」是不是問題）**：

`output/role_flag/baseline_23f2aba/BASELINE.md` 裡有兩個欄位**每次重跑本來就會變**，
不是錯誤，不是快取指紋失效，不是重建出錯：
- 「產生時主 repo 的 `git rev-parse HEAD`」：你重跑時主 repo HEAD 已經是 `545ec5e`（或更晚），
  不會是我這輪產生時的 `c8f6be9`——這是預期行為，該欄位記的是「產生當下」，不是固定值。
- 「產生時間（UTC）」：每次重跑都不同，同樣預期。

**除了這兩個欄位，`BASELINE.md` 的其餘內容（13 張表格：geometry_confidence／
materials_confidence／overall confidence／gate／surfaces／surfaces_sources；manifest 裡的
worktree HEAD、每張照片 sha256）必須逐字相同。**

還有一個我自己實測發現、必須先講清楚的**已知限制**：manifest 裡「每份 `analysis.json` sha256」
**這一欄不會逐字相同，即使結果完全正確**。原因：我在同一份 commit（未改動）上把同一張照片
（`CathedralRoom`，真實 CLI、非樁）**連續真跑兩次**互相比對，逐欄位 diff 後只有一個欄位不同：

```
.elapsed_s => 27.79 != 25.58
```

`analysis.json` 裡帶一個 `elapsed_s`（本次真跑耗時，浮點秒數），每次真跑的機器排程/負載都不同，
這個數字必然每次不同，連帶讓整份 JSON 的 sha256 每次都不同——**其餘所有欄位（含連續浮點值
`dims_m`、`closed_loop.t30_measured_s` 等）逐位元完全相同**，我已經用兩次獨立真跑證實過。
criteria v2 的 A2～A6 斷言比對的是 `geometry_confidence`／`materials_confidence`／`confidence`／
gate／`surfaces`／`surfaces_sources` 這幾個離散欄位（腳本裡直接讀 dict key 比對，不是比對整份
JSON 或其 sha256），完全不受 `elapsed_s` 波動影響——**這是我自己也在收工前才發現的限制，
不是本卡的漏洞，是 `analysis.json` 本身設計上就含一個計時欄位**。

**建議判法**：worktree HEAD＝`23f2abada92aa9d46b1da0ac1ba2a7f1dc178872`（`23f2aba` 全長）
逐字核對；13 張表格逐值核對；「每張照片 sha256」逐字核對（照片內容不變，這欄必然相同）；
「每份 analysis.json sha256」**因上述已知限制，不逐字比對，改為直接讀該 json 裡的
`geometry_confidence`／`materials_confidence`／`confidence`／`surfaces`／`surfaces_sources`
幾個欄位是否與 `BASELINE.md` 表格內容相符**（這才是斷言實際依賴的內容）。

### §5 第 3 點：13×（A1～A7）、13×（B1～B2）、B4 表 2 全部成立；表 3 只列不判

腳本本身會自動斷言並在任一項不成立時 exit 非 0、不寫任何產物——`--fresh` 重跑後看到
`output/role_flag/REPORT.md` 存在且 exit 0，即代表全部 13×A1～A7、13×B1～B2 成立。
逐條核對表 1（`output/role_flag/tables.md`）：

- 「與 B0 相符」「與 round11 相符」「與 round17 相符」三欄應全部 `✅`（13/13）；
- `bathroom_tiled`／`bedroom_ai_generated` 的「gate（預設）」欄應為 `BLOCK`；
- 表 2（鐵則 12 五張已知錯誤案例）：預設模式全部 `BLOCK`；`--role-aware` 模式只有
  `bathroom_tiled` 是 `pass`（B4「只列不判」——這正是 T-44 已記錄的已知錯誤放行，
  存在於旗標路徑，處置屬 T-44-R1，本卡不判定）。
- 表 3（geometry 觀察）應只有兩條資訊性描述（`site_photo_department_store` 兩模式不同、
  `TunnelToHell` vs `EXPECTED_GATE` 不同），**不應該有任何斷言失敗訊息混進來**。

若跑出 `mismatches` 非空、exit 非 0：仔細看訊息裡「!= 〈基線〉」點名的是 B0／round11／round17／
`EXPECTED_GATE` 哪一個，回頭查對應 `runs/<name>__b0`／`round11_remap_baseline`／`round17` 的
`detail.json`／`analysis.json`，不要假設是我這輪的錯——但也不要因為卡關就放寬任何一項。

### §5 第 4 點：docstring／訊息與程式實際斷言一致（阻擋項 2 解除）

```bash
grep -n "三軸 confidence／gate.*逐值相同\|geometry 完全不受" scripts/t46_role_flag_baseline.py
```
**必須完全沒有輸出**（v1 那兩句誇大宣稱已清除）。再讀一次
[scripts/t46_role_flag_baseline.py](scripts/t46_role_flag_baseline.py) 的 docstring（開頭到第
54 行）與 `mismatches.append(...)` 那些行，確認每個「!=」都寫明是對 B0／round11／round17／
`EXPECTED_GATE` 哪一個基線（不再像 v1 把兩個不同基線寫成同一個）。

### §5 第 5 點：五個紅旗

| 紅旗 | 怎麼查 | 預期結果 |
|---|---|---|
| 改了 `CRITERIA_T46_v2.md` 本檔 | `git log --oneline -- output/role_flag/CRITERIA_T46_v2.md` | 只有 `2be2453` 一筆 |
| 改了 `src/` | `git diff --stat -- src/` | 空（我已驗證，你要自己再查一次） |
| 用舊快取（指紋不符仍命中） | 你自己 `--fresh` 重跑，`--fresh` 會強制忽略所有快取，天然排除這個紅旗 | 全部真跑，log 裡每張都印 `✅ ... (default)` / `(role_aware)` / `(b0)`，不應出現「快取命中」字樣 |
| `BASELINE.md` 手打 | 檔頭寫「程式產生，勿手改」；你重跑後與已 commit 版本比對（除上述兩個已知會變的欄位＋analysis.json sha256 那欄外）逐字相同，即代表確實是程式產的 | 相同 |
| `EXPECTED_GATE` 被改 | `git diff -- scripts/t36_clip_accuracy.py` | 空（本卡未列在範圍清單內，不該有 diff） |
| 表 7' 數字被動 | `git diff -- output/clip_treatment/rounds/round17/tables.md` | 空 |

### §5 第 6 點：通過後的連動

通過後：
1. T-46 四軸工程改「已驗證」（依 WORKFLOW §3.2，只有你能把工程軸改成「已驗證」）；
2. T-44 四軸依 T-46 卡片原文改「工程：已驗證（經 T-46 複驗）」——**除非** T-44 修正輪
   （另一視窗，`HANDOFF_T44_FIX.md`）屆時已由你另行複驗通過，那就以較晚的那一筆為準，
   兩邊互不覆寫（見 T-46 卡「Opus 驗證紀錄」第 11 點的既有約定）；
3. 依 HANDOFF_PHASE_1.9R.md §2，T-46 ✅ 後 T-42／T-48 前置滿足，可以開下一張卡。

---

## 4. 附錄：我已實跑核對的資料（複驗仍要自己重建 B0，這裡只是省你查找時間）

### 4.1 結果 commit 與雜湊

| 項目 | 值 |
|---|---|
| 結果 commit | `545ec5e` |
| criteria commit（`2be2453`）全長 | `2be24530766e14951bd4562f6c5f87d33555bd63` |
| B0 commit（`23f2aba`）全長 | `23f2abada92aa9d46b1da0ac1ba2a7f1dc178872` |
| 我產生 `BASELINE.md` 時的主 repo HEAD | `c8f6be9b60fbb7030a27687436c4dd5fbe97c495` |

### 4.2 六條交付 IR MD5（本輪 `src/` 零改動，理論上不會變，我已重生比對過）

| 檔案 | MD5 |
|---|---|
| `chk_bath.wav`（T-20，`gen_ir_from_text.py "浴室" -o chk_bath`） | `2adbaa75eb698772a8c9aa693179ec47` |
| `chk_church.wav`（T-20，`gen_ir_from_text.py "大教堂" -o chk_church`） | `2dd19b6e6d351d713887636fe45cd67e` |
| `coupled_neighbor_voices.wav`（T-21，`gen_ir_coupled.py assets/scenes/neighbor_voices.json`） | `9a94ffdf5d8295aee7889729c39c9cd8` |
| `coupled_stadium_corridor.wav`（T-21，`gen_ir_coupled.py assets/scenes/stadium_corridor.json`） | `a1c21bcc3fd9aa3480df203a89c8cd05` |
| T-14 兩條（`small_surf_carpet`／`hall`） | 由 `test_ir_synth.py`【6】內建斷言，隨測試套件一起過（`f3a763be…`／`f24353b5…`） |

### 4.3 19 支 `scripts/test_*.py`

我已逐支實跑，全部 `EXIT=0`（含 `test_t46_role_flag.py`）。你複驗時請自己重跑一次：

```bash
source .venv/bin/activate
for f in scripts/test_*.py; do echo "=== $f ==="; python3 "$f" > /dev/null 2>&1; echo "EXIT=$?"; done
```

### 4.4 表 1／表 2 摘要（完整表格在 `output/role_flag/tables.md`，這裡只列你最該盯的幾張）

| 照片 | gate（預設） | gate（--role-aware） | 備註 |
|---|---|---|---|
| `bathroom_tiled` | `BLOCK` | `pass` | 鐵則 12＋T-45-A 焦點案例；`--role-aware` 的 `pass` 是 T-44 已記錄的已知錯誤放行，本卡不判 |
| `bedroom_ai_generated` | `BLOCK` | `BLOCK` | — |
| `site_photo_gym`／`site_photo_restaurant`／`RacquetballCourt4` | `BLOCK` | `BLOCK` | 鐵則 12 其餘三張 |

13 張三項比對（與 B0／round11／round17）**13/13 全 `✅`**（無任何 `🔴`）。

---

## 5. 自我檢查總覽（收工前你應該已經跑過這一整批）

```bash
# 1. criteria commit 唯一且在前
git log --oneline -- output/role_flag/CRITERIA_T46_v2.md

# 2. 自行重建 B0（15-20 分鐘）
source .venv/bin/activate
python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/ --fresh

# 3. 對照已 commit 版本（除「主 repo HEAD」「產生時間」「analysis.json sha256」三個已知會變的欄位外，應逐字相同）
git diff -- output/role_flag/baseline_23f2aba/BASELINE.md output/role_flag/REPORT.md output/role_flag/tables.md

# 4. docstring／訊息沒有誇大宣稱
grep -n "三軸 confidence／gate.*逐值相同\|geometry 完全不受" scripts/t46_role_flag_baseline.py

# 5. 五個紅旗
git diff --stat -- src/ scripts/t36_clip_accuracy.py output/clip_treatment/rounds/round17/tables.md

# 6. 完整測試套件
for f in scripts/test_*.py; do echo "=== $f ==="; python3 "$f" > /dev/null 2>&1; echo "EXIT=$?"; done

# 7. 沒有殘留 worktree
git worktree list
```

`git worktree list` 應該只剩主 repo（`--fresh` 重跑會自己建立又自己清掉暫存 worktree；
若中途被你手動中斷，可能留下 `.worktree_t46_b0_23f2aba/`，記得 `git worktree remove --force` 清掉）。

---

## 6. 給下一位（若你判通過，寫進 TASKS.md 的內容建議）

- T-46「四軸狀態」工程軸：`✅ 已驗證（Opus 複驗，2026-XX-XX，依 criteria v2；commit 見複驗紀錄）`。
- 在「Opus 驗證紀錄」新增一段（比照現有 2026-09-03 那段格式），寫明：criteria commit 早於結果
  commit 已核對、B0 重建與已 commit 版本比對結果（含上述「analysis.json sha256 不逐字比對」
  的判法說明，供再下一位不會誤會）、13×A1～A7／13×B1～B2／B4 逐項成立、五個紅旗皆不成立、
  六條 IR MD5 與 19 支測試自己重跑結果。
- T-44 四軸工程軸依上方「§3 第 6 點」處理。
- 同步 HANDOFF.md／HANDOFF_PHASE_1.9R.md／TODO.md（WORKFLOW §7.9）。
- 本檔（`HANDOFF_T46_VERIFY.md`）複驗完成、結案後可以刪除。
