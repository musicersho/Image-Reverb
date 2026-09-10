# CRITERIA_T46_v3 — T-46 步驟 4「13 張基線變化表」驗收門檻第三版

> 依 [WORKFLOW.md](../../WORKFLOW.md) §7 變更控制開立。**本檔是 T-46 步驟 4 的單一事實來源**，
> 取代 [CRITERIA_T46_v2.md](CRITERIA_T46_v2.md)（v2 檔案**原樣保留、不得再改**，全文逐字複製於本檔附錄 B；
> v1 原文＝TASKS.md T-46 卡步驟 4，逐字複製於附錄 A）。
> 執行者（Sonnet）與驗證者（Opus）都以本檔為準；**執行者不得改本檔任何一字**——
> 若發現 v3 仍有錯，寫「🔴 卡關」回 Fable 開 v4，不得自行放寬或降級（§7.1／§7.4）。

## 0. 版本紀錄（§7.1／§7.2／§7.4／§8）

| 欄位 | 內容 |
|---|---|
| `criteria_version` | **v3**（v1＝T-46 卡步驟 4 原文，`96e7716`，2026-09-03；v2＝`2be2453`，2026-09-08） |
| `criteria_commit` | 本檔的獨立 commit（`criteria: T-46 v3 …`，2026-09-10；**只含本檔一個檔案**）——**必須早於任何依 v3 產生的結果**；執行者重跑前先用 `git log --oneline -- output/role_flag/CRITERIA_T46_v3.md` 核對（腳本也會自動核對，見 §2.6.6） |
| `criteria_locked_at` | 2026-09-10 |
| 提案者 | **Opus**（獨立審查者；第二輪複驗 `6efa6ba`，TASKS.md T-46 卡「Opus 驗證紀錄（第二輪）」第 8 點：提案 canonical stable projection＋`analysis_stable_sha256`＋三個資訊欄降為只記錄不比對，並以 10 張 B0 逐葉比對實證唯一差異為 `.elapsed_s`） |
| 起草者 | **Fable**（規劃者；**非**本卡執行者、**非**本卡驗證者；2026-09-10）。起草時另加入一項 Opus 提案未涵蓋的排除欄（五個絕對路徑欄，理由見 §1.2） |
| 核准者 | **使用者**（2026-09-10 指示 Fable「正式建立 CRITERIA_T46_v3.md，單獨 criteria commit，早於任何 v3 結果」，並逐條指定 §1.3 六項要求）；Opus 重送審時第一項即核對本檔未被執行者改動（§5.1） |
| `verdict_under_original_criteria`（v1） | 工程：**🟠 退回**（`37e07fe`，2026-09-03）。步驟 4 對 geometry／overall／gate 三項**不可執行**（round11 基線物件無該欄位）→ 該三項 **inconclusive**；**永久保留，不得改為 PASS**。原文見附錄 A |
| `verdict_under_v2` | 工程：**🟠 退回**（`6efa6ba`，2026-09-10）。13 項實質斷言 Opus 全部獨立重跑成立；退回唯一原因＝v2 §5.2「`BASELINE.md` 逐字相同」與同版 §2.1（該檔須含產生時間／產生當下主 repo HEAD／每份 `analysis.json` 原始 sha256）互相矛盾 → 依 §7.5 標 **inconclusive（門檻不可執行）**；**永久保留，不得改為 PASS**。原文見附錄 B |
| `verdict_under_current_criteria`（v3） | **尚無**——必須由 Sonnet 依本檔 §4 `--fresh` 重跑產生**新的結果 commit**，再由 Opus 依 §5 複驗後填寫（§6） |
| `criteria_changed_after_first_result` | **yes**（首跑 `7686462` 2026-09-03；v2 `2be2453` 2026-09-08；v3 本檔 2026-09-10） |
| `change_record` | 本檔 commit／理由見 §1／提案 Opus（`6efa6ba`）、起草 Fable、核准 使用者（2026-09-10 指示） |

## 1. 為什麼要改（變更理由）

### 1.1 v2 的自我矛盾（Opus `6efa6ba` 實證）

v2 §5.2 要求「自行重建 B0（`--fresh`）→ `BASELINE.md` 與已 commit 版本**逐字相同**」，
但同版 §2.1 又要求 `BASELINE.md` 的 manifest 必須包含：

1. 「產生時主 repo 的 `git rev-parse HEAD`」——每次重跑時主 repo 已前進，必然不同；
2. 「產生時間（UTC）」——必然不同；
3. 「每份 `analysis.json` sha256」——[`src/image_reverb/pipeline.py:89`](../../src/image_reverb/pipeline.py)
   的 `_elapsed_payload()` 把本次耗時 `elapsed_s` 寫進 `analysis.json`，整份 JSON 的 sha256 每次真跑必然不同。

**同一份鎖定門檻內互相矛盾＝字面不可執行**，Opus 依 §7.5 標 inconclusive，並拒絕採納執行者事後在
`HANDOFF_T46_VERIFY.md` 自行提出的三項豁免（§7.1／§7.4 自改自批、§5 紅旗 7）。**這是門檻寫錯，不是執行者做錯**；
依 §7 由非執行者（Fable）開新版，經使用者核准。

Opus 的實證（不採信交接筆記、自行重跑 39 次真實 CLI 後）：13 張表格、worktree HEAD、13 張照片 sha256、
`tables.md` 整份**全部逐字相同**；執行者殘留的 10 份 B0 `analysis.json` 與 Opus 重建版逐葉攤平比對（90–108 個葉節點／張），
**唯一差異都是 `.elapsed_s`**，其餘含連續浮點值（`dims_m`、`closed_loop.t30_measured_s` 等）逐位元相同。

### 1.2 Fable 起草時另發現的一項（Opus 提案未涵蓋）

Opus 提案的穩定雜湊只排除 `elapsed_s`／`time_budget_s`／`elapsed_note` 三欄。Fable 靜態掃描 39 份
`analysis.json`（13 張 B0＋13×2 兩模式）的全部葉節點後，另有**五個絕對路徑欄**：
`input`、`output_dir`、`ir_mono.path`、`ir_stereo.path`、`wet_preview.path`
（值形如 `/Users/musicersho/Image Reverb/.worktree_t46_b0_23f2aba/output/...`）。
這五欄在**同一台機器**上重跑相同（所以 Opus 的 10 張同機比對看不到差異），但換機器、換使用者名稱、
搬 repo 目錄就必然不同——若不排除，v3 會在第一次跨環境複驗時再度變成「門檻不可執行」。
v3 一併排除（§2.2.1），**照片內容本身仍由「照片 sha256」硬比對**，排除 `input` 路徑不損失任何證據力。

### 1.3 使用者核准的六項要求（2026-09-10，本檔逐條落實）

| # | 要求 | 落實在 |
|---|---|---|
| 1 | 保留 v1、v2 原文與 verdict | §0 表、附錄 A、附錄 B |
| 2 | 定義可重現的 canonical stable projection／hash，明確排除 `elapsed_s`、產生時間等 volatile 欄位 | §2.2 |
| 3 | geometry／materials／overall／gate／surfaces／sources、B0 commit、照片 hash 仍是硬斷言 | §2.2.4 表「硬」列、§2.3 |
| 4 | 當下主 repo HEAD、執行時間、原始 JSON SHA 只作 provenance，不要求不同重跑逐字相同 | §2.2.3、§2.2.4 表「provenance」列、§2.7 |
| 5 | 舊結果不得補判 PASS，必須由 Sonnet 依 v3 `--fresh` 重跑 | §6 |
| 6 | 不修改 `src/`、不修改既有 v2 結果 | §3.2、§3.3 |

## 2. v3 門檻（逐條，全部可執行）

### 2.1 基線 B0（維持 v2 §2.1，僅產物路徑改到 v3 目錄）

- **定義不變**：對 `scripts/t36_clip_accuracy.py` 的 `GATE_ITEMS` 13 張照片，在 commit `23f2aba`
  （**role_aware 尚未預設啟用的最後狀態**；是 T-44 系列中間 commit、不是 T-44 之前；全長
  `23f2abada92aa9d46b1da0ac1ba2a7f1dc178872`）的程式碼上各跑一次真實 CLI
  `python -m src.image_reverb <photo> --force-low-confidence --no-viz`，取每張的 `analysis.json`。
- **產生方式不變**（v2 §2.1 的 1～4）：`git worktree add --detach <暫存目錄> 23f2aba`、共用主 repo `.venv`、
  `cwd` 在 worktree 內跑；照片一律用主 repo 絕對路徑；每張的 `analysis.json` 搬到
  `output/role_flag/v3/baseline_23f2aba/runs/<name>__b0/`；跑完 `git worktree remove` 清掉，不得殘留。
- **worktree HEAD 守門不變**：`git rev-parse HEAD`（worktree）必須等於 `23f2aba` 全長，不等＝🔴 停。
- **B0 自證守門不變**：B0 的六面 `surfaces`＋`surfaces_sources` 必須與
  `output/clip_treatment/rounds/round11_remap_baseline/runs/<name>/detail.json` 的 `payload.surfaces`／`payload.sources`
  逐值相同，且 B0 的 `materials_confidence` 必須與 `EXPECTED_GATE[name][1]` 逐值相同。任一不同＝🔴 停、回 Fable。
- **產物**（全部程式產生，地雷 #15）：
  - `output/role_flag/v3/baseline_23f2aba/runs/<name>__b0/{analysis.json, analysis.stable.json}`（13 組；不進 git）；
  - `output/role_flag/v3/baseline_23f2aba/BASELINE.stable.md`（**進 git；§5.2 的硬比對物件**，定義見 §2.2.2）；
  - `output/role_flag/v3/baseline_23f2aba/BASELINE.md`（**進 git；人讀全文＝stable 段逐字＋provenance 段**，定義見 §2.2.3）。

### 2.2 Canonical stable projection（本版新增的核心）

#### 2.2.1 `analysis.stable.json`：每份 `analysis.json` 的穩定投影

**定義**：對 `analysis.json` 解析後的物件，**只**移除下列 8 個以點分隔路徑指定的鍵（鍵不存在時略過，不報錯；
**不得**用「鍵名叫 path 就刪」之類的萬用規則，只准用這張固定清單）：

```text
STABLE_PROJECTION_EXCLUDED_PATHS = (
    "elapsed_s",         # 本次耗時秒數（pipeline._elapsed_payload）——每次真跑必然不同
    "time_budget_s",     # 同一 payload 的預算常數，隨 elapsed_s 一併排除
    "elapsed_note",      # 超過預算時才出現的說明字串（含耗時數字）
    "input",             # 照片絕對路徑（照片內容已由 photo sha256 硬比對）
    "output_dir",        # 產物目錄絕對路徑（含 worktree 暫存路徑）
    "ir_mono.path",      # 產物絕對路徑
    "ir_stereo.path",    # 產物絕對路徑
    "wet_preview.path",  # 產物絕對路徑
)
```

**正規化序列化（一個字元都不能偏）**：

```python
canonical_bytes = (json.dumps(projected, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
analysis_stable_sha256 = hashlib.sha256(canonical_bytes).hexdigest()
```

- `analysis.stable.json` 的檔案內容**必須恰好是** `canonical_bytes`（寫檔後重新讀回取 sha256 必須等於
  `analysis_stable_sha256`，腳本自檢，§2.6.7）。
- 每個 run（13 張 B0＋13×2 兩模式＝39 個 run 目錄）都要寫一份 `analysis.stable.json` 放在 `analysis.json` 旁邊，
  讓任何人都能用 `diff`／`shasum -a 256` 直接核對，不需要重跑腳本。
- **Fable 起草時已用 13 張 B0 實檔驗證此定義**：投影內不含任何絕對路徑或耗時字串；改 `elapsed_s` 或打亂鍵序雜湊不變；
  改任一 `surfaces` 值雜湊即變。參考實作如下，執行者可逐字採用（放進 `t46_role_flag_baseline.py`，不另開腳本）：

```python
def stable_projection(analysis: dict) -> dict:
    obj = copy.deepcopy(analysis)
    for dotted in STABLE_PROJECTION_EXCLUDED_PATHS:
        parts = dotted.split(".")
        node = obj
        for p in parts[:-1]:
            node = node.get(p) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, dict):
            node.pop(parts[-1], None)
    return obj
```

- **明文不斷言的事**：B0 與預設模式（HEAD）的 `analysis_stable_sha256` **不要求相等**（HEAD 的 `analysis.json` 多了
  `role_aware` 欄，且 `warnings` 文字可能不同）；兩模式之間的等價性仍只由 §2.3 A2～A6 的離散欄位斷言負責。
  `analysis_stable_sha256` 的用途是「**同一 commit、不同次重跑之間**」的整份穩定比對（§2.7）。

#### 2.2.2 `BASELINE.stable.md`：B0 的 canonical stable projection（§5.2 硬比對物件）

程式產生，內容**只有**下列四塊，順序固定，**不得**含時間、主 repo HEAD、原始 `analysis.json` sha256、
環境資訊或任何會隨重跑改變的字串：

1. 一行標題：`# BASELINE.stable.md — T-46 criteria v3 基線 B0 穩定投影（程式產生，勿手改；§5.2 硬比對物件）`
2. **表 S1**（13 列，順序＝`GATE_ITEMS` 順序，欄位與 v2 相同）：
   `照片｜geometry_confidence｜materials_confidence｜overall confidence｜gate｜surfaces｜surfaces_sources`
   （`surfaces`／`surfaces_sources` 以 `json.dumps(..., ensure_ascii=False)` 原鍵序輸出，與 v2 相同）
3. 一行（腳本從 worktree 實際讀出，不得手抄；不等於 `git rev-parse 23f2aba` ＝🔴 停）：
   ```text
   - B0 commit（worktree git rev-parse HEAD）：23f2abada92aa9d46b1da0ac1ba2a7f1dc178872
   ```
4. **表 S2 manifest-stable**（13 列，照片名排序）：`照片｜photo sha256｜analysis_stable_sha256`

**`baseline_stable_sha256`** ＝ `BASELINE.stable.md` 檔案 bytes 的 sha256（腳本計算，寫進 §2.2.3 的 provenance 段與 REPORT 檔頭）。

#### 2.2.3 `BASELINE.md`：人讀全文＝stable 段＋provenance 段

程式產生，結構固定為兩段，**stable 段的文字必須與 `BASELINE.stable.md` 檔案內容逐字相同**（程式用同一個字串
寫兩處，不得各寫一份）：

```text
# BASELINE.md — T-46 criteria v3 基線 B0（程式產生，勿手改）
<一段固定說明：B0 定義、哪一段是硬比對、哪一段是 provenance>

## S. Stable projection（§5.2 硬比對範圍；與 BASELINE.stable.md 逐字相同）
<BASELINE.stable.md 的完整內容，逐字>

## P. Provenance（只記錄、不比對；不同重跑本來就會不同，不得據此判失敗、也不得據此判通過）
- baseline_stable_sha256：<上方 S 段＝BASELINE.stable.md 的 sha256>
- 產生時主 repo 的 git rev-parse HEAD：<…>
- 產生時間（UTC）：<…>
- 環境：<platform.platform()>；python <sys.version.split()[0]>；torch <torch.__version__，import 失敗寫 n/a>
- criteria_commit（git log -1 -- output/role_flag/CRITERIA_T46_v3.md）：<…>
<表 P1（13 列，照片名排序）：照片｜analysis.json sha256（原始，含 elapsed_s）｜elapsed_s>
```

#### 2.2.4 硬斷言 vs provenance 的正式分類（本版的單一對照表）

| 類別 | 項目 | 比對方式 | 不同時的處置 |
|---|---|---|---|
| **硬** | 表 S1 的 13×6 個離散欄（geometry／materials／overall／gate／六面 surfaces／六面 surfaces_sources） | 逐字 | 見 §2.7 |
| **硬** | B0 commit＝`23f2aba` 全長（worktree HEAD） | 逐字 | 🔴 停 |
| **硬** | 13 張照片 sha256 | 逐字 | 🔴 停（照片被動） |
| **硬** | 13 筆 `analysis_stable_sha256`（表 S2） | 逐字 | 見 §2.7（分層判定） |
| **硬** | `BASELINE.stable.md` 整份 | `git diff` 為空 | 見 §2.7 |
| **硬** | `tables.md` 整份 | `git diff` 為空 | 退回（產物不可重現） |
| **硬** | REPORT 檔頭四個常數欄：`criteria_version=v3`、`criteria_commit`＝本檔 commit 全長、B0 全長、跑法＝`--fresh` | 值正確 | 退回 |
| **provenance** | 產生時主 repo HEAD、產生時間（UTC）、環境字串 | **不比對** | 驗證者只記錄「本輪為何值」，**不得據此判失敗或通過** |
| **provenance** | 13 筆原始 `analysis.json` sha256（含 `elapsed_s`）、13 筆 `elapsed_s` | **不比對** | 同上 |
| **provenance** | `baseline_stable_sha256` | 不單獨比對（它是 S 段的函數，S 段逐字相同時必然相同） | — |

### 2.3 斷言 A：預設模式（13 張；維持 v2 §2.2 原文，逐條硬性；任一不成立 → exit 非 0 且不寫 REPORT／tables／BASELINE）

| # | 斷言 | 比對對象 |
|---|---|---|
| A1 | `analysis.json.role_aware == false` | 常數 |
| A2 | `geometry_confidence` 逐張相同 | **B0** |
| A3 | `materials_confidence` 逐張相同 | **B0**（經 §2.1 守門，同時等於 `EXPECTED_GATE` materials 欄） |
| A4 | `confidence`（overall）逐張相同 | **B0** |
| A5 | gate 逐張相同（gate 定義固定：`confidence == "low"` → `BLOCK`，否則 `pass`；等價性由自我檢查「`bathroom_tiled` 不加 force 實跑 exit 3」抽驗） | **B0** |
| A6 | 六面 `surfaces`＋`surfaces_sources` 逐張相同 | **B0**（經 §2.1 守門，同時等於 round11） |
| A7 | `bathroom_tiled` 與 `bedroom_ai_generated` 預設 gate＝`BLOCK`；鐵則 12 五張 `KNOWN_ERROR_PHOTOS` 預設 gate 全部 `BLOCK` | 常數（顯式斷言並列於表 2） |

### 2.4 斷言 B：`--role-aware` 模式（13 張；維持 v2 §2.3 原文）

| # | 斷言 | 比對對象 |
|---|---|---|
| B1 | `analysis.json.role_aware == true` | 常數 |
| B2 | 六面 `surfaces`＋`surfaces_sources` 逐張相同 | `round17/runs/<name>/detail.json` 的 `payload.surfaces`／`payload.sources` |
| B3 | `geometry_confidence`／`confidence`／gate **只報告、不斷言** | 無可執行基線（交 T-47／T-44-R1） |
| B4 | 鐵則 12 五張在 `--role-aware` 模式的 gate **只列不判**（表 2） | `bathroom_tiled` 旗標路徑 BLOCK→pass 是 T-44 已記錄的已知錯誤放行，處置屬 T-44-R1 |

### 2.5 `EXPECTED_GATE` 的 geometry 欄：**不作為 T-46 斷言**（維持 v2 §2.4 原文）

只以「表 3：geometry 觀察」資訊性列出 (a) B0 vs `EXPECTED_GATE` geometry 欄差異、(b) 預設 vs `--role-aware` 的
`geometry_confidence` 差異；REPORT 明寫「交 T-47」。表 3 **恰為兩條**資訊性描述（`site_photo_department_store`
兩模式不同、`TunnelToHell` vs `EXPECTED_GATE` 不同）是 v2 兩輪實測的已知狀態；多出或少掉任何一條都要在 REPORT 說明。

### 2.6 產物與可重現要求（送審前必須全部成立）

1. **送審結果一律 `--fresh` 從零跑**（含 B0 重建），跑法固定：
   `python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/v3/ --fresh`。
2. **v3 產物一律寫在 `output/role_flag/v3/`**（新目錄；腳本 `DEFAULT_OUT_DIR` 同步改為此路徑）。
   進 git 的只有：`v3/REPORT.md`、`v3/tables.md`、`v3/baseline_23f2aba/BASELINE.md`、`v3/baseline_23f2aba/BASELINE.stable.md`
   （`.gitignore` 已允許 `output/**/*.md`）。**v2 的 `output/role_flag/{REPORT.md,tables.md,baseline_23f2aba/BASELINE.md}`
   原樣保留、不得改動**（它們是 v2 verdict 的證據；本機 `output/role_flag/runs/`、`baseline_23f2aba/runs/` 不進 git，可留可清）。
3. **快取指紋維持 v2 §2.5.2**（主 repo HEAD＋六個 `src` 檔 sha256＋照片 sha256；B0 只需照片 sha256）；
   `--out-dir` 絕對路徑不得炸（v2 §2.5.3）；docstring／`mismatches` 訊息只宣稱程式真的斷言的事（v2 §2.5.4），
   且全文把「criteria v2」改成「criteria v3」、不得再出現「`BASELINE.md` 逐字相同」這種未限定的話——
   正確寫法是「`BASELINE.stable.md` 逐字相同；`BASELINE.md` provenance 段只記錄不比對」。
4. **REPORT.md 檔頭表格**分兩區：硬（`criteria_version: v3`、`criteria_commit` 全長、B0 全長、跑法 `--fresh`、
   `baseline_stable_sha256`）與 provenance（主 repo HEAD、產生時間 UTC、環境）。REPORT 其餘正文與 v2 相同要求
   （表 1 三欄「與 B0／與 round11／與 round17 相符」、表 2、表 3、殘留風險段）。
5. **`tables.md` 不得含任何 provenance 值**（v2 已如此，Opus 實證整份逐字相同；v3 明文要求維持）。
6. **腳本開跑前守門**：`git log -1 --format=%H -- output/role_flag/CRITERIA_T46_v3.md` 為空（本檔尚未 commit）＝🔴 停、不跑；
   REPORT 檔頭的 `criteria_commit` 由此指令讀出，不得手抄。
7. **腳本自檢**：寫完每份 `analysis.stable.json` 後重新讀回、重算 sha256，必須等於寫入 manifest 的值；
   寫完 `BASELINE.stable.md` 與 `BASELINE.md` 後，讀回 `BASELINE.md` 的 S 段必須與 `BASELINE.stable.md` bytes 逐字相同。任一不成立＝exit 非 0。
8. **單元測試**：在 `scripts/test_t46_role_flag.py` 加一個案例，對 `stable_projection()`＋正規化序列化斷言四件事：
   (a) 8 個排除鍵全部不在投影內；(b) 兩個只差 `elapsed_s`／`input` 的物件雜湊相等；(c) 只差 `surfaces.floor` 的物件雜湊不等；
   (d) 鍵序打亂後雜湊相等。全部 `scripts/test_*.py` 仍須 exit 0。
9. `git worktree list` 只剩主 repo；`git diff -- src/` 為空；`git diff -- output/role_flag/CRITERIA_T46_v2.md output/role_flag/CRITERIA_T46_v3.md output/role_flag/REPORT.md output/role_flag/tables.md output/role_flag/baseline_23f2aba/BASELINE.md scripts/t36_clip_accuracy.py output/clip_treatment/rounds/round17/tables.md` 全空。

### 2.7 §5.2 的分層判定表（每一種結果都有唯一處置，驗證者照表填、不得自創第四種）

Opus 依 §5.2 `--fresh` 重建後，對 `BASELINE.stable.md` 做 `git diff`，結果落入且只落入下列一列：

| 情形 | 表 S1（13×6 離散欄）| 表 S2 `analysis_stable_sha256` | 判定 |
|---|---|---|---|
| ① | 逐字相同 | 13/13 相同 | **§5.2 成立** |
| ② | 逐字相同 | 任一不同 | **inconclusive（環境差異待查）**：不得 PASS、不得記執行者過失。驗證者必須附上該張兩份 `analysis.stable.json` 的逐葉 diff（用 `diff` 即可）＋兩邊 provenance 段的環境字串，回 Fable 判斷是浮點／模型版本差異還是真回歸 |
| ③ | 任一欄不同 | （不論） | **inconclusive（B0 不可重現）**：同一 commit `23f2aba` 兩次重建結果不同＝管線非決定性，屬 Fable 層級問題（可能需開 v4 或另開卡），不得記執行者過失，亦不得 PASS |
| ④ | B0 commit 或任一 photo sha256 不同 | （不論） | 🔴 停：基線物件或照片被動，回 Fable |

情形 ①～④ 之外（例如 `BASELINE.stable.md` 多了一行時間戳），屬**執行者違反 §2.2.2** → 退回。

## 3. 範圍與紅線

### 3.1 v1／v2 保留不動的部分

步驟 1（REPORT §7 修正，`1121293`）、步驟 2（feature flag）、步驟 3（介面測試＋舊碼 fail 實測）、步驟 5、
自我檢查、四個紅旗：**全部維持 v1 原文**（附錄 A）。v2 §2.1～§2.4 的實質斷言 A1～A7／B1～B4／`EXPECTED_GATE`
排除：**全部維持**（§2.3～§2.5 逐字抄錄）。Opus 兩輪已實測通過的項目，重送審時是否重驗由 Opus 依 §5 決定。

### 3.2 允許改動的檔案（本修正輪只准動這些）

- `scripts/t46_role_flag_baseline.py`（加 stable projection／`BASELINE.stable.md`／provenance 段／守門／自檢；改 v3 路徑與文字）；
- `scripts/test_t46_role_flag.py`（加 §2.6.8 的一個案例）；
- `output/role_flag/v3/**`（全部程式產生）；
- 狀態文件：TASKS.md T-46 卡（只追加交接筆記與四軸）、DEV_LOG.md、TODO.md、HANDOFF.md、HANDOFF_PHASE_1.9R.md。

### 3.3 紅線（任一觸犯＝退回）

- 改 `src/` 任何一字（`elapsed_s` 留在 `analysis.json` 是合理設計，處理方式是**比對時投影排除**，不是刪欄位）；
- 改本檔或 `CRITERIA_T46_v2.md` 任何一字；
- 改 v2 已 commit 的三份產物（`output/role_flag/{REPORT.md,tables.md,baseline_23f2aba/BASELINE.md}`）；
- 手打或手改任何 `v3/**` 產物；用舊快取送審；`EXPECTED_GATE` 或表 7' 被動；
- 在 `STABLE_PROJECTION_EXCLUDED_PATHS` 之外多排除任何鍵（發現還有 volatile 欄＝🔴 卡關回 Fable 開 v4，不得自己加）。

## 4. 執行者順序（Sonnet，逐字照做）

1. 讀本檔全文＋T-46 卡兩輪退回全文；`git log --oneline -- output/role_flag/CRITERIA_T46_v3.md` 確認本檔已有一筆
   `criteria: T-46 v3 …` commit 且早於你的任何 run；`git log --oneline -- output/role_flag/CRITERIA_T46_v2.md` 仍只有 `2be2453`。
2. 改 `scripts/t46_role_flag_baseline.py`：加 `STABLE_PROJECTION_EXCLUDED_PATHS`＋`stable_projection()`（§2.2.1，可逐字採用）、
   每個 run 寫 `analysis.stable.json`、`BASELINE.stable.md`（§2.2.2）、`BASELINE.md` 兩段式（§2.2.3）、REPORT 檔頭兩區（§2.6.4）、
   開跑守門（§2.6.6）、自檢（§2.6.7）、`DEFAULT_OUT_DIR`＝`output/role_flag/v3/`、docstring／訊息 v2→v3（§2.6.3）。
   **斷言 A1～A7／B1～B2 的程式邏輯一行不動**。
3. 改 `scripts/test_t46_role_flag.py`：加 §2.6.8 案例。
4. `python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/v3/ --fresh`（13 張 B0＋13×2＝39 次真實 CLI，約 15–20 分鐘）。
   任一斷言／守門／自檢不成立 → 不得改本檔、不得改斷言，寫 🔴 卡關＋原因。
5. 全部 `scripts/test_*.py` exit 0；六條交付 IR MD5；§2.6.9 的 `git diff`／`git worktree list` 全部乾淨。
6. 收工：四軸「工程：🔵 待審（依 criteria v3）」；交接筆記寫 `criteria_version: v3`＋本檔 commit＋結果 commit＋
   `baseline_stable_sha256`；結果 commit 格式 `T-46: 依 criteria v3 …(待驗證)`，**不得與本檔同一 commit**；
   HANDOFF／TODO／DEV_LOG 同步（§7.9）。

## 5. Opus 複驗要點（四軸輸出；只審不改碼）

1. **門檻未被動**：`git log -- output/role_flag/CRITERIA_T46_v3.md` 只有 Fable 的一筆 `criteria:` commit（只含本檔），
   且早於結果 commit；`CRITERIA_T46_v2.md` 仍只有 `2be2453`；v2 三份產物零 diff（§3.3）。
2. **自行 `--fresh` 重建**（跑法同 §2.6.1）→ `git diff -- output/role_flag/v3/baseline_23f2aba/BASELINE.stable.md output/role_flag/v3/tables.md`
   **為空**；`BASELINE.md`／`REPORT.md` 的 diff **只能**落在 provenance 段／provenance 區（逐行列出並確認每一行都是 §2.2.4 表列的 provenance 項）。
   結果依 §2.7 分層判定表填**且只填一列**。
3. **投影可獨立重算**：不用腳本，對 13 份 B0 `analysis.json` 用 §2.2.1 的定義自行重算 `analysis_stable_sha256`，
   須與 `analysis.stable.json` 的檔案 sha256、表 S2 三者一致（13/13）。
4. 13×（A1～A7）、13×（B1～B2）、B4 表 2 全部成立；表 3 只列不判（§2.5）。
5. docstring／訊息與程式實際斷言一致；不得殘留「`BASELINE.md` 逐字相同」的未限定宣稱（§2.6.3）。
6. §2.6.8 單元測試存在且 19 支 `test_*.py` exit 0；六條 IR MD5；`bathroom_tiled` 不加 force 實跑 exit 3。
7. 紅旗：§3.3 全部；另加「驗證者自己用 provenance 差異判失敗或判通過」（兩個方向都是紅旗，§2.2.4）。
8. 通過後：T-46 四軸工程改「✅ 已驗證（依 criteria v3）」；T-44 工程軸已於 `6c405a1`（第四輪）獨立驗證通過，
   **不因本卡改寫**（v2 §5.6「以較晚一筆為準、互不覆寫」）；T-42／T-47／T-48／T-44-R1 的「前置 T-46 ✅」自此滿足。
   結案後 `HANDOFF_T46_VERIFY.md` 可刪（其三項豁免自 `6efa6ba` 起即非有效門檻）。

## 6. 舊結果的處置（§7.3／§7.5；使用者要求 5）

- v1 結果（`7686462`）與 v2 結果（`545ec5e`）的 verdict **永久保留**（§0 表），**不得依 v3 補判 PASS**——
  即使 Opus `6efa6ba` 已實證 v2 結果的 13 項實質斷言全部成立，也**不得**把 `545ec5e` 的產物拿來「依 v3 重新核對一次」當作通過：
  v3 要求的 `analysis.stable.json`／`BASELINE.stable.md`／守門／自檢在 `545ec5e` 的腳本裡不存在，
  且使用者明確指示「必須由 Sonnet 依 v3 `--fresh` 重跑」。
- v3 的第一個有效結果＝Sonnet 依 §4 產生的**新結果 commit**；`verdict_under_current_criteria` 只能由 Opus 在該 commit 之後填寫。

---

## 附錄 A：v1 原文（TASKS.md T-46 卡步驟 4，`96e7716`，逐字）與 v1 verdict

### A.1 v1 步驟 4 原文

```markdown
  4. **13 張基線變化表（鐵則 8，程式產出）**：`scripts/t46_role_flag_baseline.py` 用
     `--out-dir output/role_flag/` 跑 13 張 ×2 模式（預設／`--role-aware`），輸出
     `output/role_flag/REPORT.md`＋`tables.md`：
     - 預設模式：三軸 confidence／gate／六面材質與 `round11_remap_baseline` **逐值相同**
       （`bathroom_tiled` 回 BLOCK、`bedroom_ai_generated` BLOCK）——任一不同＝🔴 停；
     - `--role-aware` 模式：與 round17 逐值相同（旗標路徑沒壞）；
     - 表尾由程式列「已知錯誤案例清單」（鐵則 12）五張在兩模式的 gate 結果。
     腳本任一斷言不成立 exit 非 0。
```

### A.2 v1 verdict（Opus，`37e07fe`，2026-09-03；commit message 逐字）

```text
docs: T-46 Opus 驗證退回（步驟 4 驗收斷言結果後放寬未走 §7＋腳本 docstring 與自產表格矛盾）

四軸：工程 退回｜實驗 不適用｜產品 🧪 feature flag（建議維持，不回滾 src/）｜MVP 不適用。

程式本體與數值結論全部實測成立：19 支測試 EXIT=0；新測試對舊碼 5520b83（worktree）
實測正確 fail；git diff 只有 cli/config/pipeline 三檔 +35/-3，surfaces.py／
compute_materials_confidence／scene_cues／門檻 0.4 零改動；表 7' 未被動；REPORT §7
三段與表 7' 逐值相符、括號 0 未閉合；bathroom_tiled 真實 CLI 預設 exit 3、
--role-aware exit 0＋experimental；六條交付 IR MD5 全中（T-21 兩條由 Opus 重生比對）；
FREEZE_MANIFEST 零 diff；腳本換新 out-dir 從零重跑 26 次真實 CLI，產出與已 commit 版逐字相同。

兩個阻擋項：
1. 步驟 4 寫死的「預設模式三軸 confidence／gate／六面材質 vs round11 逐值相同，
   任一不同＝🔴 停」被結果後降級成只記錄不攔停（geometry 軸零斷言、gate 只驗 2/13 張），
   未走 WORKFLOW §7 變更控制。根因是門檻本身有事實錯誤——round11_remap_baseline 的
   detail.json 只有 surfaces/sources/warnings/faces，沒有 confidence／gate 欄位，
   該句字面不可能成立 → 交 Fable 開 T-46 門檻 v2（獨立 commit）後重跑重送審。
2. t46_role_flag_baseline.py 的 docstring 宣稱「三軸……逐值相同」與「geometry 完全不受
   role_aware 影響」，被同一支腳本產出的 tables.md 表 3 反證（§5.4.1 產物／報告一致性、
   紅旗 6，正是本卡被開出來修的同型缺陷）。

Opus 旁證（供 §7 v2 使用，不當本卡已達標）：另開 worktree 到 pre-T-44 的 23f2aba，
13 張照片真實 CLI 與 HEAD 預設模式比對 geometry/materials/overall/surfaces/sources
→ 13/13 全欄位逐值相同；並證實 EXPECTED_GATE 的 TunnelToHell geometry 欄位確實過期
（舊碼也是 low），department_store 的 medium→low 只發生在 --role-aware 路徑。

T-44 維持「工程：待複驗」；T-42 前置未達成，尚不可開。
```

## 附錄 B：v2 全文（`output/role_flag/CRITERIA_T46_v2.md`，`2be2453`，逐字）與 v2 verdict

### B.1 v2 verdict（Opus，`6efa6ba`，2026-09-10；commit message 逐字）

```text
docs: T-46 Opus 第二輪複驗退回（criteria v2 §5.2 與同版 §2.1 自我矛盾、字面不可執行）

依 CRITERIA_T46_v2.md §5 六點複驗結果 commit 545ec5e，四軸判定：
工程：🟠 退回｜實驗：不適用｜產品：🧪 feature flag｜MVP：不適用（沿用 T-17 FAIL）

實質斷言全部獨立重跑成立（不採信交接筆記）：
- --fresh 39 次真實 CLI（13 張 B0＋13×2 兩模式）exit 0，約 19 分鐘
- B0 自證守門 13/13；A1～A7、B1～B2 13/13；表 1 三欄 13/13 全 ✅
- tables.md 與已 commit 版本整份逐字相同；表 3 恰兩條資訊性描述
- 19 支 test_*.py EXIT=0；四條手動 IR MD5 全中；五個紅旗全不成立
- bathroom_tiled 不加 --force-low-confidence 實跑 exit 3（BLOCK）

退回的唯一原因＝門檻自我矛盾，不是執行者做錯：
v2 §5.2 要求 BASELINE.md 與已 commit 版本「逐字相同」，但同版 §2.1 又要求該檔
內含「產生時間」「產生當下主 repo HEAD」「每份 analysis.json sha256」，三者每次
真跑必然不同（pipeline.py:89 _elapsed_payload 寫入 elapsed_s）。依 WORKFLOW §7.5
標 inconclusive（門檻不可執行），不得改判 PASS；HANDOFF_T46_VERIFY.md 事後由執行者
本人提出的三項豁免不予採納（§7.1／§7.4 自改自批、§5 紅旗 7）。
實證：執行者殘留的 10 份 B0 analysis.json 與本輪重建逐欄位攤平比對，90–108 個葉節點
中唯一差異都是 .elapsed_s。

處置：提案交 Fable 開 criteria v3（canonical stable projection＋analysis_stable_sha256
＋三個資訊欄降為只記錄不比對），提案全文見 TASKS.md T-46 卡驗證紀錄第 8 點。
v1／v2 舊 verdict 全部保留不覆寫。T-44 四軸不因本卡變動。

備註：本輪部分 T-46 文字被另一視窗的 6c405a1（T-44 驗證通過）併入，非本視窗刻意混卡。
```

### B.2 v2 全文（逐字；以下至檔尾為 `CRITERIA_T46_v2.md` 在 `2be2453` 的完整內容，置於 markdown 圍欄內）

```markdown
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
```
