# T-38 執行交接 — CLIP 提示詞治療（Phase 1.9 治療輪 2/3）

> ⚠️ **本檔已於 2026-09-01 由 Fable 大改版**。第一版（2026-08-31）把 T-38 描述成
> 「使用者只要貼 Prompt 就能完成」的實作卡——這是誤導：T-38 實際是**結果不可
> 事前保證的模型實驗**，且實際執行後六個完整輪次無一達標（詳見 §2）。
> T-38 已拆成 **T-38A（可重現評測與實驗紀錄）→ T-38B（有界提示詞實驗）**，
> 拆卡裁決全文在 [TASKS.md](TASKS.md) T-38 原卡的「Fable 拆卡裁決」節。
>
> - **使用者**：讀「§1 白話版」和「§6 你要做的事」即可。
> - **Claude（任一模型）**：先讀 [CLAUDE.md](CLAUDE.md) 知道角色 → 讀本檔
>   → 讀 [TASKS.md](TASKS.md) 的 **T-38A／T-38B 卡**逐字執行。本檔不取代卡片。
>
> 現況若與本檔衝突，一律以 [DEV_LOG.md](DEV_LOG.md) 最新一筆與 TASKS.md 為準。
> T-39 結案後這份檔可以刪除。

---

## §0 現在的狀態（一句話）

**T-38 已實際跑過 round0～round5 六個完整輪次＋round6 中止，無一輪同時達成
三門檻；Fable 已於 2026-09-01 拆卡改版。下一步是開 Sonnet 視窗執行 T-38A。**

Phase 1.9 完整順序（不得跳號）：
**T-37 ✅ → T-40 ✅ → T-41 ✅ → 👉 T-38A → T-38B → T-39（需使用者參與）→
T-42 → T-43 → 回 Fable 收尾複評**

---

## §1 白話版：這一階段到底在做什麼

**一句話：只改「問 AI 的問法」（提示詞），看能不能讓它認材質認準一點——
但這是實驗，實驗有可能得到「怎麼改都沒用」的結果，那也是有價值的答案。**

現況（T-36 量出來的）：AI 猜六個面的材質，猜對率大約一半，地板最差。
上一個視窗已經試過六輪不同的問法，**沒有一輪比原本好**——最好的一輪只是
打平。這不是誰做錯了什麼：可能「換問法」這條路本身就到頂了，答案要往
「增加材質選項」（T-39）去找。

所以現在分兩步：
- **T-38A**：先把「做實驗的工具」修好——每一輪改了什麼、結果如何，都要留下
  完整可追溯的紀錄（上一輪的六次嘗試沒留下改動內容，現在無法重現，這是
  要修的洞）。
- **T-38B**：在**寫死的預算內**（最多 4 輪）按事先列好的假設再試一次。
  跑滿預算誠實報告就算完成——**就算結論是「提示詞治療無效」，任務也算
  成功完成**，接著由 Fable 決定走 T-39。

⚠️ **重要觀念**：如果 T-38B 的結論是否定的，那是**研究結論**，不是你操作
失敗，也不是執行的 AI 失職。本檔第一版寫「只要貼 Prompt 就能完成」是錯的，
已刪除。

---

## §2 上一個視窗實際發生了什麼（2026-08-31～09-01）

T-38 原卡雖然一直顯示「⬜ 未開始」，但實際已執行六個完整輪次
（數字取自 `output/clip_treatment/rounds/*/summary.json`）：

| 輪次 | overall | floor | in-set 誤判 | 同時達成三門檻？ |
|---|---:|---:|---:|---|
| round0_baseline | 31/76 | 4/13 | 9 | （基線） |
| round1 | 24/76 | 4/13 | 11 | 否 |
| round2 | 24/76 | 3/13 | 16 | 否 |
| round3 | 29/76 | 3/13 | 10 | 否 |
| round4 | 31/76 | 4/13 | 9 | 否（僅持平，不得記為通過） |
| round5 | 24/76 | 3/13 | 12 | 否 |
| round6 | 只完成 6/13 張 | — | — | **interrupted，不納入比較** |

三個必須知道的事實：

1. **round1～round5 的提示詞字串已遺失**（逐輪覆寫、未 commit，只剩
   `surfaces.py` 的 sha256）。**不可恢復就標不可恢復，不得猜測倒填**
   ——T-38A 會補寫誠實的 ROUND.md。
2. **工作樹有未提交成果，不得清除**：`src/image_reverb/surfaces.py`
   （一行 carpet 提示詞改動＝round6 快照，sha256 相符）、
   `scripts/t38_treatment_eval.py`（評測 harness，T-38A 收編）、
   `output/clip_treatment/rounds/`（六輪證據）。**在 T-38A 依步驟記錄之前，
   禁止 reset／checkout／clean／刪除。**
3. **卡關根因不是 T-41**（SegFormer 去重維持 ✅）：是 T-38 原卡把「產品
   成效門檻」誤寫成「工程完成條件」，又沒有迭代預算與紀錄機制。
   診斷全文：`/Users/musicersho/Documents/Codex/2026-08-30/
   users-musicersho-image-reverb/outputs/T41_transition_block_diagnosis.md`。

---

## §3 三個一定會踩到的地雷（仍然有效）

### 💣 地雷 A：預設指令從此永遠 hard fail（T-40 的刻意設計）

```bash
python scripts/t36_clip_accuracy.py
```

這行一定 exit 1（`output/clip_accuracy/` 是 T-36 凍結基線）。治療評測一律用
`scripts/t38_treatment_eval.py <round_label>`，輸出寫 `output/clip_treatment/`。
子目錄也算凍結，別想繞。

### 💣 地雷 B：T-33 凍結快取交叉守門

`t36_clip_accuracy.py` 的守門在預設模式必 exit 1（TunnelToHell 在 T-37 後
本來就與 T-33 凍結快取不同——正當修正，非錯誤）。治療模式
（`t38_treatment_eval.py`）已改成產差異清單不卡關；**預設模式行為一個字都
不能弱化**。⚠️ T-38A 要修它的差異訊息：現行只要有差異就印「預期只有
TunnelToHell」，即使多張照片大量漂移也印同一句——必須改成真正檢查差異
照片集合。

### 💣 地雷 C：驗收基線＝round0_baseline，不是 T-36 的數字

T-36 的 52.4%／51.7% 在現行碼已過期。**T-38B 的比較基線一律是
round0_baseline：overall 31/76、floor 4/13、in-set 誤判 9**（已用 T-37 修正後
的現行碼實際量出，非推算）。

---

## §4 範圍紅線（超出就是退回）

- **T-38A** 只動：`scripts/t38_treatment_eval.py`（收編＋修正）、
  `output/clip_treatment/rounds/*/ROUND.md`、新測試。`src/` 最終零 diff
  （步驟內的 `surfaces.py` 還原必須在 round6 diff 記錄 commit 之後）。
- **T-38B** 只動：`surfaces.py` 的 `CLIP_MATERIAL_PROMPTS`／`CLIP_OOD_PROMPTS`
  **字串值**。❌ 不加減候選 id（T-39）；❌ 門檻 0.4；❌
  `classify_region_material()`／`compute_materials_confidence()` 邏輯；❌
  `data/material_ground_truth.json`；❌ role-aware prompts（要開須 Fable 新裁決）。
- ❌ 兩張卡都不許動：`SPEC.md`／`ROADMAP.md`／`WORKFLOW.md`／
  `output/mvp_acceptance/`／`output/material_round/`／`output/clip_accuracy/`。
- ⚠️ **過擬合紅線**：提示詞必須是材質的一般性描述，不得夾帶特定場地／照片
  特徵。78 面既是調參集也是驗收集、無 held-out——誠實寫進 REPORT。

## §5 驗收怎麼算（拆卡後的新口徑）

**工程完成**（決定卡片 ✅ 與否）：
- T-38A：harness 修正到位、七份 ROUND.md 誠實補齊、測試全綠。
- T-38B：假設先寫（PLAN.md）、預算內（最多 4 輪＝round7～round10）每輪
  78 面全量量測＋ROUND.md、報告誠實。**跑滿預算無改善也是 ✅。**

**產品採用**（決定提示詞改動要不要進 `surfaces.py`，事前門檻不變）：
1. overall 必須上升；2. floor 必須上升；3. in-set 誤判不得上升
（皆對 round0_baseline）。持平不算通過。無候選達標→保留 baseline、
不採用任何改動，交 Fable 收尾裁決（進 T-39 擴候選，或另開 role-aware 設計卡）。

**共同鐵則照舊**：15 支 `scripts/test_*.py` 全 exit 0；六條交付 IR MD5 不變；
`ir_metrics.py` 零 diff；臥室紅旗（bedroom 從擋變放 → 🔴 停）。

⚠️ **floor 門檻的誠實註記**：`classify_region_material()` 沒有 role 參數，
floor／wall／ceiling 共用同一套全域 prompts 與 softmax——「floor 必須改善」
在只改全域字串的前提下**不保證可達**。做不到不是執行失敗，是介面限制，
由 Fable 收尾裁決後續路線。

---

## §6 你（使用者）要做的事

依 [WORKFLOW.md](WORKFLOW.md)，一次一張卡：

1. 開 **Sonnet** 視窗，貼：

```
執行 TASKS.md 的任務 T-38A。先讀 CLAUDE.md、HANDOFF_T38.md 和該任務卡的全部內容再動工。注意：工作樹裡未提交的 surfaces.py、t38_treatment_eval.py 與 output/clip_treatment/ 是上一輪的實驗證據，是本卡的輸入，動工前不得 reset、checkout、clean 或刪除；surfaces.py 的還原只能照任務卡步驟 4 的順序做。完成後執行任務卡裡的「自我檢查」，最後照 WORKFLOW.md 第 4 節做收工程序。
```

2. Sonnet 回報 🔵 待驗證後，開 **Opus** 視窗貼 WORKFLOW.md §2.2 驗證 Prompt
   （T-XX 換成 T-38A）。
3. T-38A ✅ 後，同樣流程執行 T-38B。
4. **T-38B 不管結論是正面還是否定，只要按規矩跑完都是完成**；結論出來後
   開 **Fable** 視窗做收尾裁決（要不要採用／進 T-39／開 role-aware 卡）。

⚠️ T-39 才需要你本人參與（16 個 proxy 面重對映，估 10 分鐘級）。

---

## §7 卡關怎麼辦

- **Sonnet 同一件事連續 3 次嘗試失敗**（指工程步驟做不出來，例如測試寫不出、
  harness 改不動）→ 停，在 TASKS.md 該卡狀態寫 `🔴 卡關`＋原因，只 commit
  文件，請使用者開 Fable 視窗。
- **T-38B 正確率調不上去** → **這不是卡關**。照 ROUND.md 記錄、跑滿預算、
  誠實寫否定結論，狀態標 🔵 待驗證交 Opus。絕對不許為了達標而改 ground
  truth、改驗收口徑、超出預算加輪次、或只挑錯的面調提示詞。
- **13 張三軸 confidence 非預期漂移** → 紅旗，🔴 停（共同鐵則 8）。
- **臥室從擋變放** → 🔴 停，回 Fable（共同鐵則 7）。

---

## §8 T-38B 之後（給下下個視窗）

- **T-39**（候選材質集擴充，需使用者參與）：新增材質要有建築聲學公開出處，
  不得自創 α；既有 12 種材質 α 逐位元不變；地雷 #13 → 門檻敏感度分析重跑。
  T-38B 否定結論同樣解鎖 T-39（涵蓋率天花板正是往這裡走的理由）。
- **T-42**／**T-43**：任何新的正式盲聽必須等這兩張 ✅ 之後（現存盲測素材是
  `d958b3c` 產的，舊 2/5 不能宣稱屬於現行碼）。T-39 等使用者期間 T-42 可
  提前（檔案範圍不相交），提前要在交接筆記註明。
- **收尾複評**：回 Fable，一併評估陳設換算公式修正輪與 role-aware 路線。

---

## §9 一分鐘查證本檔是否過期

```bash
git log --oneline -3 && head -5 DEV_LOG.md
```

本檔改版於 2026-09-01（Fable 拆卡）。若 DEV_LOG.md 已有更新的紀錄，
以 DEV_LOG.md 與 TASKS.md 為準。
