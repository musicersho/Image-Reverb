# HANDOFF_PHASE_1.9R — Phase 1.9-R 階段交接（從 T-46 到 T-17-R2）

> 建立者：Opus（驗證視窗，2026-09-07）｜基準：DEV_LOG `2026-09-07 (95)`、commit `a6a2dc5`
> **2026-09-08 Fable 更新**：卡點 A 已解決（criteria v2＝`2be2453`，[CRITERIA_T46_v2.md](output/role_flag/CRITERIA_T46_v2.md)）；
> §7 排程問題已裁決（裁決 T-48-S：T-48 可與 T-42／T-43 平行）。T-44 另於 2026-09-08 被 Opus 第三輪退回（見 DEV_LOG (97)）。
> **2026-09-08 Sonnet 更新**：§4 第 2 線（T-46 v2 修正輪）已完成——依 v2 §4 逐字執行、`--fresh`
> 全新跑（39 次真實 CLI），B0 自證守門／A1～A7／B1～B2/表 1 三項比對全數 13/13 通過，19 支測試
> exit 0、六條 IR MD5 全中、`src/` 零 diff。四軸「工程：🔵 待審（依 criteria v2）」，**下一步是
> Opus 複驗（依 v2 §5），不是再跑一次**。細節見 TASKS.md T-46 卡「交接筆記（v2 修正輪）」、
> DEV_LOG `2026-09-08 (99)`。下面 §1 表格與 §2～§4 提到「Sonnet 修正輪」處視為已完成，等 Opus
> 複驗結果更新前，T-42／T-47／T-48／T-44-R1 仍暫掛在「等 Opus 確認 T-46 ✅」。
> **2026-09-10 Opus 更新（本檔最新一筆，優先於上面兩筆）**：T-46 v2 首次複驗 **🟠 退回**——
> 13 項實質斷言我全部獨立重跑成立（`--fresh` 39 次真實 CLI、19 支測試 EXIT=0、`tables.md`
> 逐字相同、五紅旗全不成立），**退回的唯一原因是 criteria v2 §5.2「`BASELINE.md` 逐字相同」
> 與同版 §2.1（要求該檔含產生時間／產生當下主 repo HEAD／每份 `analysis.json` sha256）
> 互相矛盾、字面不可執行**（依 WORKFLOW §7.5 標 inconclusive，不得改判 PASS）。
> **卡點回到 Fable：要開 criteria v3**（提案見 TASKS.md T-46 卡「Opus 驗證紀錄（第二輪）」
> 第 8 點）。`HANDOFF_T46_VERIFY.md` 的「建議判法」三項豁免**不是有效門檻**，不得據此放行。
> T-42／T-47／T-48／T-44-R1 仍全數掛在「等 T-46 ✅」。
> 適用範圍：**T-45 之後、回 Fable 收尾之前的全部 7 張卡**。
> 單卡層級的交接另見：[HANDOFF_T44_FIX.md](HANDOFF_T44_FIX.md)（T-44 第二輪退回修正）、
> [HANDOFF_T46_VERIFY.md](HANDOFF_T46_VERIFY.md)（T-46 v2 修正輪複驗交接，Sonnet 2026-09-09
> 建立，結果 commit `545ec5e`；含複驗清單、已核對資料、`analysis.json sha256` 不逐字相同的
> 已知限制說明）。
>
> ⚠️ **本檔取代 [HANDOFF.md](HANDOFF.md)「接下來的固定順序」那一段**——該段寫
> 「T-46 🔵 待審已完成」是**過期的**，T-46 在 `37e07fe` 已被退回。

---

## 1. 一頁看懂：現在每張卡真的在哪

| 卡 | 工程 | 實驗 | 產品 | MVP | 卡在誰身上 |
|---|---|---|---|---|---|
| T-45 審查制度修正 | ✅ 已執行 | — | — | — | 結案 |
| **T-46** 收尾修正（§7＋feature flag） | 🟠 **退回（Opus 第二輪複驗 2026-09-10：實質斷言 13/13 成立，門檻 v2 §5.2 自我矛盾、不可執行）** | 不適用 | 🧪 flag | 不適用 | ~~Fable（門檻 v2）~~ ~~Sonnet（修正輪）~~ ~~Opus（複驗）~~ **Fable（開 criteria v3）** |
| **T-44** role-aware | 🟠 **退回**（第二輪） | 🟢 相對正向 | 🧪 暫停採用 | FAIL | **Sonnet**（見 HANDOFF_T44_FIX.md） |
| T-42 gate 交易式輸出 | ⬜ 未開始 | — | — | — | 等 T-46 ✅ |
| T-43 產物溯源 provenance | ⬜ 未開始 | — | — | — | 等 T-42 ✅ |
| T-47 gate 校準複審量測 | ⬜ 未開始 | 待量測 | 待裁決 T-47-A | 不適用 | 等 T-46／T-42／T-43 ✅ |
| T-48 T-11／T-12 判準 v2 重驗 | ⬜ 未開始 | 待量測 | 不適用 | 不適用 | 等 T-46 ✅（裁決 T-48-S：**不必等 T-42／T-43**） |
| T-44-R1 安全門檻重驗 | ⬜ 未開始 | 待驗證 | 待升級判定 | 不適用 | **使用者 ×2** ＋ 裁決 T-47-A |
| T-17-R2 MVP 重新驗收 | ⬜ 未開始 | 不適用 | 不適用 | **待重驗** | 上面全部 |
| T-04 素材來源 | 未結案 | — | — | — | **使用者**（9 張照片網址） |

**專案總狀態：MVP FAIL**（T-17 首驗 2026-08-30，永久保留）。
13 張真實照片目前 100% 被 gate 擋下；`--text`／`--scene` 兩條管線不受影響、端到端可用。

---

## 2. 關鍵路徑：**T-46 是全域瓶頸**

```
                        ┌─ T-44 修正輪（Sonnet）─→ Opus 第三輪複驗 ─┐
                        │   ※ 不擋任何下游，可平行做              │
（現在）────────────────┤                                          ├──→ 收尾
                        │                                          │
                        └─ ★ T-46 ★ ──┬─→ T-42 ─→ T-43 ─→ T-47 ─→ 裁決 T-47-A ─┐
                           （Fable 先  │                                          ├─→ T-44-R1 ─→ T-17-R2
                            開門檻 v2）└─→ T-48（可與 T-42/T-43 平行）───────────┘
```

**要點三句話**：
1. **T-46 沒過，下面 6 張卡一張都不能開。** T-42／T-48 的前置都是「T-46 ✅（工程）」。
2. **T-44 修正輪不擋任何人**——裁決 T-45-A 已把 T-42 的前置從「T-44 ✅」改成「T-46 ✅」。
   所以 T-44 修正輪與 T-46 門檻 v2 **可以同時進行**（兩人／兩視窗，檔案不相交）。
3. **T-48 只需要 T-46**，可與 T-42→T-43 平行跑，是唯一能縮短鏈條的地方（見 §6 待確認事項）。

---

## 3. 三個卡點（不解決就前進不了）

### 🔮 卡點 A（最急）：Fable 要開 **T-46 門檻 v2**，這件事不能由執行者自己做

> ✅ **已解決（Fable 2026-09-08，commit `2be2453`）**：採**選項 1**，全文在
> [output/role_flag/CRITERIA_T46_v2.md](output/role_flag/CRITERIA_T46_v2.md)。基線 B0＝`23f2aba`
> （寫法照下方 ⚠️ 警告：「role_aware 尚未預設啟用的最後狀態」，不寫 pre-T-44），由程式在 worktree 重建並產出
> `BASELINE.md`；預設模式 A1～A7 硬斷言；`--role-aware` 只斷言材質＋來源 vs round17；`EXPECTED_GATE` geometry 欄
> 明文排除、交 T-47。卡點 C 的 docstring 修正已併入 v2 §2.5 第 4 條。**下一步：Sonnet 依 v2 §4 執行修正輪。**
> 以下為原始問題描述，保留供追溯。

**問題**：T-46 卡片步驟 4 寫死的驗收斷言**字面上不可能成立**——它要求
「預設模式：**三軸 confidence／gate**／六面材質與 `round11_remap_baseline` 逐值相同」，
但 Opus 實測 `round11_remap_baseline/runs/*/detail.json` 的 `payload` 只有
`is_equirect`／`surfaces`／`sources`／`warnings`／`faces`，**根本沒有 confidence 或 gate 欄位**。

上一輪 Sonnet 發現對不上後，把 `geometry_confidence` 降級成「notes」不再攔停、
gate 只斷言 2 張（其餘 11 張不比對）——這是**結果出來後自己放寬門檻**，
違反 WORKFLOW §5.4.1／§7.1／§7.4，所以退回。**根因是門檻有錯，不是執行者偷懶。**

**Fable 要做的**（WORKFLOW §7：新 `criteria_version` ＋ **獨立** commit
`criteria: T-46 v2 …` ＋ 理由 ＋ 核准者，且 commit 必須早於重跑結果）：

- **選項 1（前一位 Opus 已實證可行，建議）**：把 geometry／overall／gate 的基線改成
  **「以 commit `23f2aba` 的實跑結果為基線」**——前一位 Opus 已實測 13 張全欄位逐值相同、
  單張約 15–40 秒。
  ⚠️ **`23f2aba` 的正確描述**（我實際核對過，避免 Fable 誤會）：它的 commit 訊息是
  「T-44 2/N：role-aware 介面改動」，**是 T-44 系列中間的 commit、不是 T-44 之前**；
  但當時 `pipeline.py:207` 仍是 `surfaces_from_preprocess(summary, role_aware=False)`
  （`surfaces_from_preprocess` 的預設值也是 `False`），所以**預設照片路徑的行為等同
  role-aware 啟用前**。真正把預設打開成 `True` 的是後來的 `5520b83`。
  ——用它當基線在語義上成立，但 criteria v2 的文字要寫清楚是「role_aware 尚未預設啟用的
  最後狀態」，不要只寫「pre-T-44」，否則下一位又會對不上。
- **選項 2**：明文把 geometry 軸**排除**在 T-46 範圍外，只保留「六面材質＋來源 vs round11」
  與「`materials_confidence` vs `EXPECTED_GATE`」，並說明為什麼這樣就夠。

**順帶要 Fable 一起看的**：`EXPECTED_GATE`（T-28-A／T-36 凍結表）的 geometry 欄位
疑似部分過期（`TunnelToHell` 實測 low、表列 medium，T-37 equirect 修正後未更新）。

### 👤 卡點 B：等使用者三件事

| # | 要什麼 | 擋住誰 | 說明 |
|---|---|---|---|
| B1 | 核准 **T-44-R1 的絕對品質下限**（`CRITERIA_T44R1.md`，A／B 兩選項，Fable 建議 B） | T-44-R1 | 必須**單獨 commit** `criteria: T-44-R1 v2 …` 且早於任何量測（§7.2） |
| B2 | 提供 **≥5 張 held-out 照片**＋逐面材質確認 | T-44-R1、T-17-R2 §7-1 | 必須**未曾用於 T-36～T-44 任何調參**；進 `data/material_ground_truth_heldout.json` |
| B3 | 補 **9 張照片的來源網址**（T-04 自檢第 2 項） | T-17-R2（或明確決定「維持未結案」） | 不補就要在 R2 REPORT 標明缺項 |

B1／B2 現在就可以請使用者處理，不必等 T-46——**這是目前唯一能提前並行的使用者工項**。

### ⚙️ 卡點 C：T-46 的第二個阻擋項（Sonnet 做，不需等 Fable）

`scripts/t46_role_flag_baseline.py` 的 docstring 宣稱的事程式沒做，還被自己的輸出打臉：
1. docstring 說驗了「三軸 confidence」——程式對 geometry 一個斷言都沒有；
2. docstring 說「geometry 完全不受 `role_aware` 影響」——同一支腳本產出的 `tables.md` 表 3
   第一行就是 `site_photo_department_store: default=medium, role_aware=low`，直接反證；
3. `mismatches` 訊息把兩個不同基線寫成同一個。

→ **改 docstring 與訊息，使其只宣稱程式真的驗過的事。** 這一項與卡點 A 無關，可先做。

---

## 4. 現在該做什麼（依序）

**可以立刻平行開三條線：**

| 線 | 角色 | 做什麼 | 開工 Prompt |
|---|---|---|---|
| 1 | **Sonnet** | T-44 第二輪退回修正 | 「執行 TASKS.md 的 T-44 修正輪。先讀 CLAUDE.md，再**逐字照做 [HANDOFF_T44_FIX.md](HANDOFF_T44_FIX.md)**，最後照 WORKFLOW §4 收工（狀態寫四軸）。」 |
| 2 | ~~Fable~~ → **Sonnet** | ~~開 T-46 門檻 v2~~ **已開（`2be2453`）→ T-46 修正輪** | 「執行 TASKS.md 的 T-46 修正輪。先讀 CLAUDE.md、T-46 卡的 Opus 退回全文與『🔮 門檻 v2』段，再**逐字照做 [output/role_flag/CRITERIA_T46_v2.md](output/role_flag/CRITERIA_T46_v2.md) §4**（不得改該檔一字），最後照 WORKFLOW §4 收工（狀態寫四軸）。」 |
| 3 | **使用者** | B1 核准絕對下限、B2 準備 held-out 照片 | 見 §3 卡點 B |

**T-46 門檻 v2 落地後**：Sonnet 依 v2 重跑 `t46_role_flag_baseline.py` ＋ 修 docstring →
Opus 複驗 → T-46 ✅ → 才輪到 T-42。

---

## 5. 全階段共同紅線（每張卡都適用，違反即退回）

沿用 Phase 1.9 共同鐵則 1～8（測試全 exit 0／六條交付 IR MD5 全中／`ir_metrics.py` 零 diff／
凍結目錄不動／新測試對舊碼要有診斷力／gate 規則零改動／臥室紅旗／基線變化表由程式產出），
外加 Phase 1.9-R 的 9～12：

9. **狀態一律四軸**（WORKFLOW §3），收工與驗證都不得只寫 `✅ 通過`。
10. **變更控制**（§7）：結果出來後不得改同版門檻；改標準＝新版號＋獨立 `criteria:` commit
    ＋理由＋核准者，原 verdict 保留。**不得自改自批。**
11. **舊結果唯讀**：`output/mvp_acceptance/`、T-44 round15～17、`output/clip_accuracy/`、
    `output/material_round/` 一個 bit 不改；重驗一律寫新目錄
    （`mvp_acceptance_r2/`、`gate_calibration/`、`geometry_r2/`、`material_r2/`、`rounds/r1_*/`）。
12. **已知錯誤案例清單**（安全 guard 基準）：`bathroom_tiled`、`bedroom_ai_generated`、
    `RacquetballCourt4`、`arena_ntsu_linkou`、`site_photo_gym`、`car_interior_suv`。
    任何卡讓其中任一張由 BLOCK 變 pass，都必須逐例證明材質／幾何正確，否則 🔴 停。

**另外兩個踩過的坑**：
- `python scripts/t36_clip_accuracy.py` 不帶參數**從此永遠 hard fail**（T-40 指紋，13 份舊
  `detail.json` 無 `fingerprint` 欄且不許補寫）——這是刻意設計。治療評測一律加 `--out-dir <新目錄>`。
- 任何新的正式盲聽必須在 T-42＋T-43 之後（現存盲測素材是 `d958b3c` 產的，
  舊 2/5 不能宣稱屬於現行碼）。

---

## 6. 已知的文件不一致（下一位動手前要知道，別被誤導）

| 位置 | 問題 | 怎麼處理 |
|---|---|---|
| `HANDOFF.md`「接下來的固定順序」 | 寫「T-46 🔵 待審已完成」——**過期**，T-46 已退回 | 已在該檔頂部與「一分鐘進入狀況」標註；以本檔 §2 為準 |
| `TASKS.md` T-42 卡「前置」 | 卡內同時有「前置：T-44 ✅」與上方裁決更新「前置改為 T-46 ✅」 | **以裁決 T-45-A 那行為準**（T-46 ✅）；原文保留不覆寫（§3.4） |
| `TASKS.md` T-44 卡「四軸狀態」工程軸 | 仍寫「由 **T-46** 修並複驗」，與事實不符 | 修法已寫進 HANDOFF_T44_FIX.md §3 |
| `EXPECTED_GATE` 凍結表 geometry 欄 | 疑似部分過期（`TunnelToHell` 實測 low、表列 medium） | **已裁決**（criteria v2 §2.4）：不作 T-46 斷言，表不動；T-47 量測後由裁決 T-47-A 決定是否更新 |

## 7. 待 Fable 確認的一個排程問題（Opus 提出，不自行決定）

> ✅ **已裁決（裁決 T-48-S，Fable 2026-09-08，寫進 TASKS.md T-48 卡與 T-42 卡）**：**不適用，T-48 可與 T-42／T-43 平行**。
> 理由：T-47 量的正是 gate 輸出行為（T-42 會改），T-48 量的是幾何值／Sabine／IR T30（T-42／T-43 紅線不碰）。
> 條件：T-48 自帶溯源（HEAD＋乾淨工作樹＋照片與 IR sha256，T-43 之後不回頭補章）；T-42 不得改 `--override-dims`
> 導引語意、不得動幾何／聲學／合成模組；T-17-R2 前用 `git diff <T-48 result_commit>..HEAD --stat` 對量測路徑程式化判定要不要重跑。

**T-48 可不可以在 T-42／T-43 之前跑？** T-48 卡的前置只寫「T-46 ✅」，
但 T-47 的前置明確要求 T-42／T-43 ✅，理由是「量測產物要走交易式輸出與 provenance」。
同一個理由看起來也適用於 T-48 的 `output/geometry_r2/` 產物，卡片卻沒寫。

- 若 Fable 認為適用 → T-48 也要排在 T-43 之後，鏈條無法縮短。
- 若 Fable 認為不適用（T-48 是唯讀量測、`src/` 零改動）→ T-48 可與 T-42／T-43 平行，
  是目前唯一能縮短關鍵路徑的地方。

**請 Fable 明文裁決並寫進 T-48 卡，不要讓執行者自己判斷**（那會變成另一次自改自批）。

---

## 8. 各卡開工前必讀（避免重複踩雷）

| 卡 | 動工前先讀 | 一句話重點 |
|---|---|---|
| T-46 | T-46 卡 Opus 退回全文＋Fable 的 criteria v2 | 只准動範圍清單那 7 個檔；表 7' 數字一個都不准改 |
| T-42 | T-42 卡「問題」三個洞 | gate 訊息「不會寫出任何檔」目前**不實**（`meta.json` 先被寫出去了） |
| T-43 | T-43 卡＋`blind_test/MANIFEST.json` | 現存 MANIFEST 記 `d958b3c` 是誠實的歷史標記，**不得回頭改寫** |
| T-47 | 裁決 T-36-A（重開 gate 議題需四樣證據） | `src/` 零 diff、只量不改；產出交 Fable 下裁決 T-47-A |
| T-48 | T-48 卡（判準 v2 已事前鎖定） | **只量不改**，量到什麼寫什麼；未達＝如實記 FAIL，不得再改 v2 |
| T-44-R1 | `CRITERIA_T44R1.md`（待使用者核准） | 是**驗證**不是調參；`ROLE_MATERIAL_CANDIDATES` 凍結，一輪跑完即結案 |
| T-17-R2 | T-17 首驗 REPORT＋SPEC §7 | 只有 §7-1～§7-4 全達成才可寫 `MVP：PASS`；首驗 FAIL 永久保留 |
