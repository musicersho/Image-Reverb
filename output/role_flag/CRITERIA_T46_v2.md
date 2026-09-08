# CRITERIA_T46_v2 — T-46 步驟 4「13 張基線變化表」驗收門檻第二版

> 依 [WORKFLOW.md](../../WORKFLOW.md) §7 變更控制開立。**本檔是 T-46 步驟 4 的單一事實來源**，
> 取代 TASKS.md T-46 卡步驟 4 的 v1 文字（v1 原文保留在卡片內，不覆寫，§3.4）。
> 執行者（Sonnet）與驗證者（Opus）都以本檔為準；**執行者不得改本檔任何一字**——
> 若發現 v2 仍有錯，寫「🔴 卡關」回 Fable 開 v3，不得自行放寬或降級（§7.1／§7.4）。

## 0. 版本紀錄（§7.1／§7.2／§7.4）

| 欄位 | 內容 |
|---|---|
| `criteria_version` | **v2**（v1＝T-46 卡步驟 4 原文，裁決 T-45-A 開卡 `96e7716`，2026-09-03） |
| `criteria_commit` | 本檔的獨立 commit（`criteria: T-46 v2 …`，2026-09-08）——**必須早於任何依 v2 產生的結果**；執行者重跑前先用 `git log --oneline -- output/role_flag/CRITERIA_T46_v2.md` 核對 |
| `criteria_locked_at` | 2026-09-08 |
| 提案者 | Opus（獨立審查者；退回紀錄 `37e07fe` 阻擋項 1＋驗證紀錄第 9 點，明文提案「以 `23f2aba` 實跑結果為基線」並實證 13/13 可行） |
| 起草者 | Fable（規劃者；**非**本卡執行者、**非**本卡驗證者） |
| 核准者 | 使用者（2026-09-08 指示 Fable 依 §7 開 v2）；Opus 重送審時第一項即核對本檔未被執行者改動（§5「Opus 複驗要點」） |
| `verdict_under_original_criteria` | 工程：**退回**（`37e07fe`）。依 §7.5：v1 步驟 4 對 geometry／overall／gate 三項**不可執行**（基線物件無該欄位），該三項標 **inconclusive（門檻不可執行）**，**不得改為 PASS**；六面材質＋來源 vs round11、`materials_confidence` vs `EXPECTED_GATE` 兩項 Opus 實測成立 |
| `criteria_changed_after_first_result` | **yes**（首跑 `7686462` 2026-09-03，本檔 2026-09-08） |
| `change_record` | 本檔 commit／理由見 §1／核准者見上 |

## 1. 為什麼要改（變更理由）

v1 步驟 4 原文：「預設模式：三軸 confidence／gate／六面材質與 `round11_remap_baseline`
**逐值相同**——任一不同＝🔴 停」。

**事實（Opus 實測，`37e07fe`）**：`output/clip_treatment/rounds/round11_remap_baseline/runs/*/detail.json`
的 `payload` 只有 `is_equirect`／`surfaces`／`sources`／`warnings`／`faces`——那是
`t38_treatment_eval.py` 的純材質評測快取，**沒有 `geometry_confidence`／`materials_confidence`／
`confidence`／gate 任何一欄**。所以 v1 對「三軸 confidence／gate」三項字面上不可能成立，
執行者對不上後把 geometry 降成「notes」、gate 只斷言 2 張，是結果出來後自行放寬（§5.4.1／
§7.1／§7.4 禁止）→ 退回。**根因是門檻寫錯，不是執行者偷懶**；依 §7 由非執行者開新版。

v2 的原則：**每一條斷言都指向一個「真的有該欄位」的基線物件**，且基線本身要能被程式重建。

## 2. v2 門檻（逐條，全部可執行）

### 2.1 基線 B0：預設路徑基線＝commit `23f2aba` 的真實 CLI 實跑結果

- **定義**：對 `scripts/t36_clip_accuracy.py` 的 `GATE_ITEMS` 13 張照片，在 commit `23f2aba`
  的程式碼上各跑一次真實 CLI `python -m src.image_reverb <photo> --force-low-confidence --no-viz`，
  取每張的 `analysis.json`。
- **`23f2aba` 的正確描述（照 Opus 核對，避免下一位再對不上）**：commit 訊息「T-44 2/N：role-aware
  介面改動」，是 **T-44 系列中間的 commit、不是 T-44 之前**；但當時 `pipeline.py` 的呼叫點是
  `surfaces_from_preprocess(summary, role_aware=False)`（且該函式預設值也是 `False`），所以
  **預設照片路徑的行為＝role-aware 尚未預設啟用的最後狀態**。真正把預設改成 `True` 的是後來的
  `5520b83`。v2 文字一律寫「`23f2aba`（role_aware 尚未預設啟用的最後狀態）」，**不要寫 pre-T-44**。
- **為什麼不用 `eebf71a`（`5520b83` 的父 commit）**：`git diff 23f2aba eebf71a -- src/` 只有
  `surfaces.py` 的 `ROLE_MATERIAL_CANDIDATES` 分區表（僅 `role_aware=True` 路徑會讀到）＋註解，
  預設路徑等價；固定用 `23f2aba` 是因為 Opus 已在該 commit 實證 13/13 全欄位相同，沿用其證據。
- **產生方式（必須由程式產生，不得手抄 Opus 的數字）**：
  1. `git worktree add <暫存目錄> 23f2aba`，用主 repo 同一個 `.venv`，`cwd` 設在 worktree 內跑 CLI；
  2. **照片路徑一律用主 repo 的絕對路徑**（13 張裡 8 張在 `assets/reference_irs/**` 被 `.gitignore`
     排除，worktree 內不存在）；
  3. 每張把 worktree 的 `output/<stem>/analysis.json` 複製到
     `output/role_flag/baseline_23f2aba/runs/<name>/analysis.json`；
  4. 跑完 `git worktree remove` 清掉暫存目錄，不得殘留。
- **產物**：
  - `output/role_flag/baseline_23f2aba/runs/<name>/analysis.json`（13 份；`output/**` 不進 git，
    屬本機重建物）；
  - `output/role_flag/baseline_23f2aba/BASELINE.md`（**程式產生、進 git**，是 B0 的持久證據）：
    表列 13 張的 `geometry_confidence`／`materials_confidence`／`confidence`／gate／六面 `surfaces`／
    `surfaces_sources`；末段 manifest：worktree `git rev-parse HEAD`（**必須等於 `23f2aba` 全長雜湊**，
    不等＝🔴 停）、每張照片 sha256、每份 `analysis.json` sha256、產生當下主 repo HEAD、產生時間。
- **B0 自證守門（基線本身要對，否則不能拿來比）**：B0 的六面 `surfaces`＋`surfaces_sources` 必須與
  `round11_remap_baseline/runs/<name>/detail.json` 的 `payload.surfaces`／`payload.sources` 逐值相同，
  且 B0 的 `materials_confidence` 必須與 `EXPECTED_GATE[name][1]`（T-28-A／T-36 凍結表 materials 欄）
  逐值相同。**任一不同＝🔴 停、回 Fable**（代表基線或凍結物有問題，不得改 v2 硬過）。

### 2.2 斷言 A：預設模式（13 張，每一條都是硬性；任一不成立 → exit 非 0 且不寫 REPORT／tables）

| # | 斷言 | 比對對象 |
|---|---|---|
| A1 | `analysis.json.role_aware == false` | 常數 |
| A2 | `geometry_confidence` 逐張相同 | **B0** |
| A3 | `materials_confidence` 逐張相同 | **B0**（經 2.1 守門，同時等於 `EXPECTED_GATE` materials 欄） |
| A4 | `confidence`（overall）逐張相同 | **B0** |
| A5 | gate 逐張相同 | **B0**。gate 定義固定為：`confidence == "low"` → `BLOCK`，否則 `pass`（與 `--force-low-confidence` 下真實 exit code 的等價性，由自我檢查「`bathroom_tiled` 不加 force 實跑 exit 3」抽驗） |
| A6 | 六面 `surfaces` ＋ `surfaces_sources` 逐張相同 | **B0**（經 2.1 守門，同時等於 round11） |
| A7 | `bathroom_tiled` 與 `bedroom_ai_generated` 的預設 gate ＝ `BLOCK`；鐵則 12 五張已知錯誤案例（`KNOWN_ERROR_PHOTOS`）預設 gate 全部 `BLOCK` | 常數（A5 已涵蓋，但這是本卡的目標，須顯式斷言並在表 2 列出） |

### 2.3 斷言 B：`--role-aware` 模式（13 張）

| # | 斷言 | 比對對象 |
|---|---|---|
| B1 | `analysis.json.role_aware == true` | 常數 |
| B2 | 六面 `surfaces` ＋ `surfaces_sources` 逐張相同 | `round17/runs/<name>/detail.json` 的 `payload.surfaces`／`payload.sources`（T-44 最終輪；旗標路徑沒壞） |
| B3 | `geometry_confidence`／`confidence`／gate **只報告、不斷言** | 無可執行基線（round17 同樣沒有 confidence 欄；`5520b83` 實跑基線屬 T-47／T-44-R1 範圍，本卡不建） |
| B4 | 鐵則 12 五張在 `--role-aware` 模式的 gate **只列不判**（表 2） | `bathroom_tiled` 在旗標路徑 BLOCK→pass 是 T-44 已記錄的已知錯誤放行，處置屬 T-44-R1，本卡不重判 |

### 2.4 `EXPECTED_GATE` 的 geometry 欄：**不作為 T-46 斷言**（明文排除）

- 理由：Opus 在 `23f2aba` 實測 `TunnelToHell` 也是 `geometry=low`，表列 `medium` 是**表過期**
  （T-37 equirect 修正後未更新），不是 T-46 的回歸；該表由 `t33`／`t36`／`t37`／`t38` 多支腳本共用，
  改表＝改凍結基準，須 T-47 量測後由裁決 T-47-A 決定，本卡不動。
- 本卡腳本仍以「表 3：geometry 觀察」**資訊性**列出：(a) B0 vs `EXPECTED_GATE` geometry 欄的差異；
  (b) 預設 vs `--role-aware` 的 `geometry_confidence` 差異（`scene_cues` 側通道）。REPORT 明寫「交 T-47」。

### 2.5 產物與可重現要求（送審前必須全部成立）

1. **送審結果一律 `--fresh` 從零跑**（含 B0 重建），REPORT 檔頭記：主 repo HEAD、B0 commit（`23f2aba` 全長）、
   `criteria_version: v2`、本檔 commit、`--fresh`。
2. **快取要帶指紋**：`run_cli()` 的快取命中條件不得只看目錄存在——至少納入主 repo HEAD＋
   `src/image_reverb/{cli,config,pipeline,surfaces,geometry,preprocess}.py` 內容 sha256＋照片 sha256
   （可直接用 `scripts/eval_cache.py` 的 `sha256_file`／`compute_fingerprint` 手法），指紋不符＝不得命中、
   必須重跑。（Opus 非阻擋建議 ①；v2 升為要求，因 v2 比的是「改 `src/` 前後」，舊快取會讓斷言失真。）
3. `--out-dir` 給 repo 外絕對路徑不得炸 `ValueError`（Opus 非阻擋建議 ②；印相對路徑時用 try/except 退回絕對路徑即可）。
4. **docstring 與 `mismatches` 訊息只宣稱程式真的斷言的事**（退回阻擋項 2）：不得再出現「三軸 confidence／gate 與 round11
   逐值相同」、「geometry 完全不受 `role_aware` 影響」；訊息裡每個「!= 〈基線〉」都要寫對是哪個基線（B0／round11／round17／`EXPECTED_GATE`）。
5. REPORT／tables／BASELINE.md 全部程式產生（地雷 #15）；表 1 每張至少含：兩模式的 geometry／materials／overall／gate、
   「與 B0 相符」「與 round11 相符」「與 round17 相符」三欄；表 2 鐵則 12 五張兩模式 gate；表 3 geometry 觀察。

## 3. v1 保留不動的部分

- 步驟 1（REPORT §7 修正，`1121293`）、步驟 2（feature flag）、步驟 3（介面測試＋舊碼 fail 實測）、步驟 5、
  自我檢查、四個紅旗：**全部維持 v1 原文**。Opus `37e07fe` 已實測通過的項目退回後不必重做；重送審時是否
  重驗，由 Opus 依 §5 決定。
- **範圍清單新增允許**：`output/role_flag/baseline_23f2aba/BASELINE.md`（新，程式產生）、
  `scripts/t46_role_flag_baseline.py`（B0 建置寫在同一支腳本，例如 `--build-baseline` 子步驟；**不另開新腳本**，
  避免範圍外溢）。本檔唯讀。其餘範圍清單不變。
- `src/`：本修正輪**零改動**（feature flag 已在 `7686462` 落地並經 Opus 實測）。若 B0 建置需要任何 `src/` 改動
  ＝🔴 卡關回 Fable。

## 4. 執行者順序（Sonnet 修正輪，逐字照做）

1. 讀本檔＋T-46 卡退回全文；`git log --oneline -- output/role_flag/CRITERIA_T46_v2.md` 核對本檔 commit 存在且早於你的任何 run。
2. 修 §2.5 的 2／3／4（快取指紋、絕對路徑、docstring／訊息）。
3. 在 `t46_role_flag_baseline.py` 加 B0 建置（§2.1 產生方式 1～4）＋守門＋ `BASELINE.md` 產出。
4. 把 v1 的 `geometry_notes` 降級邏輯**移除**，改為 §2.2 A2／A4／A5 硬斷言；表 3 只留 §2.4 的資訊性觀察。
5. `python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/ --fresh` 從零跑（13 張 B0＋13×2 兩模式＝39 次 CLI，
   單張約 15–40 秒）。任一斷言不成立 → 不得改本檔、不得改腳本斷言，寫 🔴 卡關＋原因。
6. 全部 `scripts/test_*.py` exit 0；六條交付 IR MD5；`git diff -- src/` 為空；`git status` 無殘留 worktree。
7. 收工：四軸「工程：待審（依 criteria v2）」，交接筆記寫 `criteria_version: v2`＋本檔 commit＋結果 commit；
   HANDOFF／TODO 同步（§7.9）。

## 5. Opus 複驗要點（四軸輸出；只審不改碼）

1. `git log -- output/role_flag/CRITERIA_T46_v2.md` 只有 Fable 的那一筆 `criteria:` commit，且早於結果 commit（§7.2）。
2. 自行重建 B0（`--fresh`）→ `BASELINE.md` 與已 commit 版本**逐字相同**；manifest 內 worktree HEAD ＝ `23f2aba` 全長。
3. 13×（A1～A7）、13×（B1～B2）、B4 表 2 全部成立；表 3 只列不判。
4. docstring／訊息與程式實際斷言一致（阻擋項 2 解除）。
5. 紅旗：改了本檔；改了 `src/`；用舊快取（指紋不符仍命中）；BASELINE.md 手打；`EXPECTED_GATE` 被改；表 7' 數字被動。
6. 通過後 T-44 四軸依卡片原文改「工程：已驗證（經 T-46 複驗）」（若 T-44 修正輪屆時已由 Opus 另行通過，則以較晚的那一筆為準，兩邊互不覆寫）。
