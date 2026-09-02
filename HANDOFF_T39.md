# T-39／T-44 執行交接 — 候選材質集擴充與 role-aware 候選子集（Phase 1.9 治療輪收尾段）

> 本檔由 Fable 於 2026-09-01 依裁決 T-38B-A 建立（裁決全文在
> [TASKS.md](TASKS.md) T-38B 卡尾）；**2026-09-02 由 Opus 於 T-39 驗證通過後
> 更新：T-39 已結案，本檔現在服務的是 T-44**（檔名不改，避免既有連結失效）。
> 同一天起 `HANDOFF_T38.md` 已無作用，可刪。
>
> - **使用者**：讀「§1 白話版」和「§6 你要做的事」即可。
> - **Claude（任一模型）**：先讀 [CLAUDE.md](CLAUDE.md) 知道角色 → 讀本檔
>   → 讀 [TASKS.md](TASKS.md) 的 **T-39／T-44 卡**逐字執行。本檔不取代卡片。
>
> 現況若與本檔衝突，一律以 [DEV_LOG.md](DEV_LOG.md) 最新一筆與 TASKS.md 為準。
> T-44 結案後這份檔可以刪除（HANDOFF_T38.md 在 T-39 結案後即可刪）。

---

## §0 現在的狀態（一句話）

**T-39（候選材質集擴充）已於 2026-09-02 以誠實的否定結論通過 Opus 驗證
——「補選項」這條路在本 13 張資料集上實證關閉（新候選未採用、`surfaces.py`
已還原；materials.json 的 3 筆新材質資料與 ground truth 重對映保留）。
下一步是開 Sonnet 視窗執行 T-44（role-aware 候選子集），這張卡不需要
使用者參與標註。**

Phase 1.9 完整順序（不得跳號）：
**T-37 ✅ → T-40 ✅ → T-41 ✅ → T-38A ✅ → T-38B ✅（否定結論）→
T-39 ✅（否定結論）→ 👉 T-44 → T-42 → T-43 → 回 Fable 收尾複評**

⚠️ **T-44 的比較基線＝`round11_remap_baseline`**（overall 30/76、floor 4/13、
非 proxy 30/63、in-set 誤判 9）。因為 T-39 未採用新候選，這一輪的程式碼與
現行工作樹**逐位元相同**，它就是最終狀態的完整輪。**不得**拿
`round0_baseline`（31/76）或 round12～14 當基線。

---

## §1 白話版：這一階段到底在做什麼

**一句話：AI 認材質認不準。「換個問法」試過了沒用（T-38B），「把缺的
選項補上」也試過了沒用（T-39，2026-09-02 結案）；還剩最後一招——讓
「地板／牆／天花板各自只在合理的選項裡挑」（T-44）。三件事都是實驗，
實驗得到「沒用」的結論也是有價值的答案，不是誰做錯。**

為什麼走到這一步：

- ~~**T-39（補選項）**~~ **✅ 已完成，結論：沒用**。你已經花 10 分鐘確認
  過那 16 個面的真實材質（這份標註**永久保留**，之後每一輪都用它計分）。
  其中 3 個有公開聲學出處的材質補進候選集後，整體正確率反而從 30/76
  掉到 24/76——因為 AI 的選項是「全部一起比」的，多加選項會讓新選項跑去
  搶答別張照片的面。更關鍵的是：其中 2 個新選項要救的那兩個天花板，
  **AI 在更早的「切圖」階段就沒看到天花板**，根本輪不到認材質。
  詳細數字見 §2A。
- 👉 **T-44（分角色選項）＝現在要做的**：前兩輪的失敗有個清楚的型態——
  「牆的材質」跑去搶答地板、「窗簾」跑去搶答天花板、「橡膠地墊」跑去
  搶答球場地板。讓每個角色只在自己合理的選項裡挑，這種錯**從機制上**
  就不可能發生。這張卡**不需要你標註**，交給 Sonnet 跑即可。但要誠實說：臥室那四面牆被判成
  「一般牆面」而不是「混凝土」的問題，這招治不了（兩個都是牆的選項），
  已寫進卡片的預期管理。

⚠️ **重要觀念（與 T-38B／T-39 相同）**：這張卡跑滿預算、誠實報告就算完成；
「分了角色沒有改善」是合法的研究結論，不是誰做錯。

---

## §2 上一個視窗實際發生了什麼（2026-09-01，T-38B）

依 `output/clip_treatment/PLAN.md`（先寫後跑，commit `ca029ee` 早於全部
輪次）跑滿 4 輪預算，累積式單改一個候選字串：

| 輪次 | 累積改動 | overall | floor | in-set 誤判 | 三門檻同時通過？ |
|---|---|---:|---:|---:|---|
| round0_baseline | （基線） | 31/76 | 4/13 | 9 | — |
| round7 | 改 `concrete` | 30/76 | 3/13 | 9 | 否 |
| round8 | ＋改 `acoustic_panel` | 24/76 | 3/13 | 18 | 否 |
| round9 | ＋改 `curtain_fabric` | 20/76 | 3/13 | 23 | 否 |
| round10 | ＋再改 `concrete` 第二版 | 23/76 | 3/13 | 26 | 否 |

- **無一輪達成產品採用三門檻，且逐輪劣化**；最終不採用任何改動，
  `surfaces.py` 已逐字還原 baseline（sha256 `c87d90c9…`；Opus 用全新
  無快取的 13 張重跑重現 31/76、4/13、9，表 1～4 與基線逐行相同）。
  `git diff -- src/ data/` 為空。
- **實證關掉的路線**：兩種風格完全不同的 `concrete` 寫法（round7 冗長
  描述句、round10 簡短 caption 句）都動不了 bedroom 四面
  generic_wall→concrete；且全域 12 候選共用 softmax，改任一字串必然在
  未鎖定照片製造副作用（round7 弄壞 DivorceBeach floor、round8 讓
  acoustic_panel 在 gym／restaurant 暴走、round10 讓 concrete 三處誤搶）。
- **方法論限制已入 REPORT §四**：78 面既是調參集也是驗收集、無 held-out。
- Opus 驗證紀錄的非阻擋觀察（不必回頭改，但要知道）：round10 選目標時有
  一組同分未載明（規則落點仍正確）；REPORT §round8 的「新增 9 面」是
  淨增值（實際新出現 10 面、另 1 面退出 in-set）；§round9 敘事把 round8
  就發生的翻轉算在 round9；`prompts_snapshot.json`／`summary.json`／
  `runs/` 依 `.gitignore` 不進版控，全新 clone 只能靠各 ROUND.md 內嵌的
  json 區塊回溯。

---

## §2A 上一個視窗實際發生了什麼（2026-09-02，T-39 ✅ 否定結論）

依 `output/clip_treatment/PLAN_T39.md`（先寫後跑，commit `103674c` 14:53
早於全部輪次產物）跑滿預算：

| 輪次 | 候選集 | overall | floor | 非 proxy | in-set 誤判 |
|---|---|---:|---:|---:|---:|
| **round11_remap_baseline**（重對映後、候選未動）**＝T-44 的基線** | 原 12 | **30/76** | **4/13** | **30/63** | **9** |
| round12_expanded（＋3 新候選） | 15 | 28/76 | 4/13 | 28/63 | 10 |
| round13（調 `metal_roof_deck`） | 15 | 29/76 | 4/13 | 29/63 | 9 |
| round14（調 `vinyl_panel`，最終輪） | 15 | 24/76 | 4/13 | 24/63 | 12 |

- **16 個 proxy 面已由使用者逐面重對映**（`confirmed_by: "user"`，
  日期 2026-09-02）：3 面查到公開出處 → 改標新候選並 `proxy: false`
  （`bathroom_tiled.ceiling`→`vinyl_panel`、`site_photo_gym.floor`→
  `rubber_flooring`、`site_photo_gym.ceiling`→`metal_roof_deck`）；
  其餘 13 面查無公開逐頻段出處，**維持原候選並逐面記錄理由**，proxy 面
  16 → 13。**這份重對映保留不回滾，T-44 直接沿用，不得再動。**
- **三個產品採用門檻未同時滿足（①overall ③非 proxy 皆下降）→ 新候選不採用**：
  `CLIP_MATERIAL_PROMPTS` 已還原成 12 條（與 T-39 開工前逐位元相同，只多
  一段註解）；`data/materials.json` 的 3 筆新材質資料**保留**（有出處，
  供 `--override-material` 手動指定，且不在候選集就不影響自動判定）。
- 🔑 **對 T-44 最重要的一項發現（結構性，寫進 T-44 的 PLAN 當證據輸入）**：
  `bathroom_tiled.ceiling` 與 `site_photo_gym.ceiling` 在四輪的
  `runs/*/detail.json` 裡 `sources`／`faces` **完全沒有 `ceiling` 鍵**——
  ADE20K 分割階段就沒偵測到 ceiling 角色像素（`ratio <
  config.MIN_SURFACE_AREA_RATIO`），**CLIP 從未被呼叫**。也就是說這兩個
  面的收益端在本 13 張資料集裡**結構性不可達**，任何 CLIP 層的改動
  （含 T-44 的 role-aware）都碰不到。**T-44 不得把這兩面算進自己的預期
  收益，也不得為了碰它們去動分割邏輯（範圍紅線）。**
- **新增候選製造的副作用，正是 T-44 要治的型態**：`SteinmanHall.ceiling`
  被 `metal_roof_deck` 搶答（round13 改字串後壓下來了）、
  `RacquetballCourt4.south` 被 `vinyl_panel` 搶走 `glass`、
  `RacquetballCourt4.floor` 被 `rubber_flooring` 拉到門檻下掉 fallback、
  round14 更讓 `vinyl_panel` 在百貨四面牆與 `RacquetballCourt4.north`
  暴走（29→24 的落差正好是這 5 面正確→錯誤）。**全部都是跨角色搶答**
  ——地板材質搶天花板、面板材質搶牆——這就是 role-aware 候選子集的
  機制性槓桿所在。
- Opus 驗證的非阻擋觀察（知道就好，不必回頭改）：REPORT_T39.md §三 把
  `CathedralRoom.west` 誤述為「原正確 concrete」（實為錯→錯）；§六 標題
  有個簡體字「门檻」；門檻敏感度只對最終狀態（round11 候選集）重跑，
  未附擴充集對照表（T-44 若要拿擴充集當證據，資料都在 `runs/` 可唯讀
  重算）；`car_interior_suv.west`／`.east` 的 proxy 標記不一致（已如實
  記在 ground truth 備註，留給 Fable 收尾複評）。

---

## §3 一定會踩到的地雷

### 💣 T-38B 交接筆記的四個坑（原文出處：TASKS.md T-38B 卡）

1. **`gen_ir_coupled.py` 不支援 `-o`／`--out`**（只有 `scene`／
   `--no-listen`／`--list-types`），輸出固定寫
   `output/ir_synth/` + 依場景檔名。驗證交付 IR MD5 時直接對固定路徑跑、
   跑完 md5 比對，**不要加 `-o`**。
2. **`gen_ir_from_text.py` 加 `-o <非預設目錄>` 會讓試聽檔路徑組錯**：
   腳本內部另組 `output/listen_<主檔名>` 試聽路徑，`-o` 指到 `/tmp/...`
   之類會使 `convolve.py` 寫檔失敗、腳本**非零 exit**——但**主 IR 檔本身
   仍正確產生、MD5 不受影響**。驗 MD5 看重生成的 wav 內容，不要只看
   exit code。
3. **全域 12 候選＋無 role 參數的架構下，改任何一個候選（字串或集合）
   幾乎必然在未鎖定的其他照片製造副作用**——這不是 bug，是介面設計的
   直接後果。T-39 加新候選同樣適用；每輪的「與 T-33 凍結快取差異」段落
   （`diff_scope_summary()`）會自動列出，**別漏看**。這也正是 T-44
   存在的理由。
4. **累積式輪次會互相污染**：T-38B 的 round9 目標有 2/3 被 round8 已壞掉
   的 acoustic_panel 頂替，效果無法歸因。T-39 的 round13／round14 若做
   調整輪，每輪的父輪次與單一變因要在 ROUND.md 寫清楚，歸因敘事不得把
   前一輪的翻轉算到本輪頭上（T-38B 的 §round9 就犯過這個記述錯，Opus
   記為非阻擋觀察）。

### 💣 沿用自 HANDOFF_T38 的三個坑（仍然有效）

5. **`python scripts/t36_clip_accuracy.py` 不帶參數從此永遠 hard fail**
   （T-40 刻意設計，`output/clip_accuracy/` 是凍結基線）。治療評測一律用
   `scripts/t38_treatment_eval.py <round_label>`，輸出寫
   `output/clip_treatment/`。
6. **T-33 凍結快取交叉守門**：`t38_treatment_eval.py` 對差異只列清單
   不卡關；`t36_clip_accuracy.py` 預設模式行為一個字都不能弱化。
7. **比較基線會換**：T-38B 之前是 round0_baseline（31/76、4/13、9）。
   ⚠️ **T-39 重對映 ground truth 之後，比較基線換成
   `round11_remap_baseline`**（重對映後、候選未動的全量重跑）——
   round12 以後**不得**再拿 round0_baseline 直接比（量尺不同）。
   round11 的數字預期比 31/76 低，那是量尺變誠實，不是退步。

### 💣 T-39／T-44 專屬的新坑

8. **ground truth 檔 sha 一改，`eval_cache` 指紋全量失效**：重對映後每輪
   都是 13 張真跑（不像 T-38B 基線可 cache hit），一輪要載入模型跑完
   13 張，時間成本高是**預期行為**，不得為省時間繞過指紋機制。
9. **重對映必須有使用者逐面確認紀錄**（`confirmed_by`），Opus 會查；
   AI 不得代替使用者確認。新材質 α 必須有建築聲學公開出處，查不到出處的
   材質**不加**（記錄原因），不得自創數字。
10. **手寫 ROUND.md 的 status 要用純文字**（`- status: complete`，不要
    粗體）——`_extract_round_md_status()` 是字面比對，粗體會被保守地誤跳過。
11. **全新 clone 沒有 `runs/` 快取與 `prompts_snapshot.json`**：字串差異
    比對會明示降級成「（無基線快照可比對）」；基線快照原文在
    `round0_baseline/ROUND.md` 的 json 區塊裡。

---

## §4 範圍紅線（超出就是退回）

- **T-39** 只動：`data/materials.json`（新增材質，**既有 12 種 α 逐位元
  不變**＋invariant test）、`surfaces.py` 提示詞字典**新增條目**（既有
  12 條字串一字不動——T-38B 已實證改它們有害無益）、
  `data/material_ground_truth.json` 的 16 個 proxy 面重對映（限使用者
  確認過的）、`output/clip_treatment/` 下的 PLAN／ROUND／REPORT。
  ❌ role-aware（那是 T-44）；❌ 門檻 0.4；❌
  `classify_region_material()`／`compute_materials_confidence()` 邏輯；
  ❌ 為達標回頭改重對映結果。
- **T-44** 只動：`classify_region_material()` 介面（加 `role` 參數，
  `role=None` 與現行逐位元等價）、候選分區表（單一事實來源）、
  `pipeline.py` 呼叫端傳 role、新測試與量測產物。❌ 提示詞字串（一字
  不動）；❌ per-role 字串變體；❌ `compute_materials_confidence()`／
  gate／scene_cues／門檻 0.4；❌ ground truth。
- 兩張卡都不許動：`SPEC.md`／`ROADMAP.md`／`WORKFLOW.md`／
  `output/mvp_acceptance/`／`output/material_round/`／`output/clip_accuracy/`；
  `ir_metrics.py` 零 diff；六條交付 IR MD5 逐條比對（鐵則 2）。
- 迭代預算寫死：T-39 為 round12 後最多 2 輪調整（round13／round14）；
  T-44 為分區首跑 1 輪＋最多 2 輪調整。跑滿即停。

## §5 驗收怎麼算（工程完成與產品採用分離——T-38 拆卡教訓，兩張卡通用）

**工程完成**（決定卡片 ✅ 與否）：
- T-39：α 有出處＋12 種既有 α invariant test＋重對映有使用者確認紀錄＋
  PLAN 先寫先 commit＋兩段式基線（round11_remap_baseline →
  round12_expanded）＋預算內輪次＋門檻敏感度重跑＋誠實 REPORT。
- T-44：介面改動＋`role=None` 等價 invariant test＋分區表（逐條理由＋
  完整性檢查：不排除該角色 ground truth 實際出現的材質）＋預算內輪次＋
  三角色門檻敏感度＋誠實 REPORT。
- **兩張卡：跑滿預算、結論否定，也是 ✅。**

**產品採用**（決定改動要不要留在 `surfaces.py`／pipeline）：
- T-39：對 `round11_remap_baseline`——overall 上升＋floor 不下降＋原 62
  個非 proxy 面正確數不下降。未達→新增候選條目還原、materials.json 資料
  保留、重對映保留不回滾。
- T-44：對 T-39 收尾基線——overall 上升＋floor 上升＋in-set 誤判不上升。
  未達→pipeline 維持 `role=None`（＝全域 baseline 行為）。

**共同鐵則照舊**：`scripts/test_*.py` 全 exit 0；六條交付 IR MD5 不變；
`ir_metrics.py` 零 diff；臥室紅旗（bedroom 從擋變放 → 🔴 停）；T-44 動
`src/` 判定路徑，鐵則 8 照原文重跑 13 張產基線變化表。

---

## §6 你（使用者）要做的事

依 [WORKFLOW.md](WORKFLOW.md)，一次一張卡。**T-39 已結案，現在輪到 T-44
（這張卡不需要你逐面標註）。**

1. 開 **Sonnet** 視窗，貼：

```
執行 TASKS.md 的任務 T-44。先讀 CLAUDE.md、HANDOFF_T39.md（§0／§2A／§3／§4／§5）和該任務卡的全部內容再動工。

務必遵守的五件事：
1. 比較基線是 round11_remap_baseline（overall 30/76、floor 4/13、非 proxy 30/63、in-set 誤判 9），不是 round0_baseline、也不是 round12～14。
2. 提示詞字串一字不動（12 條既有字串），本卡只動「哪些候選參賽」，不做 per-role 字串變體。
3. 分區完整性鐵則：每個角色的候選子集必須涵蓋該角色在（T-39 重對映後）ground truth 實際出現的所有材質；每一條「某角色排除某材質」都要在 PLAN 寫理由。4 個 OOD 候選每個角色都要保留。
4. role=None 必須與改動前逐位元等價，要有 invariant test 證明。
5. PLAN.md（含分區表與假設）先寫死、單獨 commit，才准跑第一輪；分區首跑 1 輪＋最多 2 輪調整（只准調分區表），跑滿即停。門檻敏感度要對 floor／wall／ceiling 三個角色分別重跑。

已知的結構性事實（寫進 PLAN，不要重新發現）：bathroom_tiled.ceiling 與 site_photo_gym.ceiling 在分割階段就沒有 ceiling 角色像素，CLIP 從未被呼叫，這兩面對本卡結構性不可達，不得計入預期收益，也不得為此動分割邏輯。bedroom_ai_generated 四面牆的 generic_wall→concrete 是牆對牆混淆，role-aware 預期不治，不得拿它當本卡失敗依據。

完成後執行任務卡裡的「自我檢查」，最後照 WORKFLOW.md 第 4 節做收工程序。
```

2. Sonnet 回報 🔵 待驗證後，開 **Opus** 視窗貼：

```
你是驗證者，只審查不修改程式碼。請依 WORKFLOW.md 第 5 節的驗證標準，審查任務 T-44 的成果：讀 TASKS.md 的該任務卡（含「設計」「範圍紅線」「Opus 驗證重點」）、讀 output/clip_treatment/ 下 T-44 的 PLAN 與 REPORT、讀相關程式碼（surfaces.py、pipeline.py、分區表檔案、新測試），實際執行驗證指令。特別注意卡片點名的紅旗：分區表有沒有排除該角色 ground truth 實際出現的材質而無理由（＝偷壓天花板）、有沒有角色缺 OOD 候選、既有 12 條提示詞字串有無 diff（字串變體偷渡）、role=None 是否與改動前逐位元等價、門檻敏感度有沒有分三個角色跑、有沒有超出輪次預算、有沒有誤拿 round0_baseline／round12～14 當基線（正解是 round11_remap_baseline）、compute_materials_confidence()／gate 有沒有任何 diff、否定結論有沒有被誤標成失敗或卡關。最後輸出：「✅ 通過」或「❌ 退回」＋具體理由清單。若退回，把理由寫進 TASKS.md 該任務卡的「狀態」欄，改成 🟠 退回。
```

3. **不管結論正面或否定，按規矩跑完都是完成**（T-38B 與 T-39 都是否定
   結論、都記 ✅）。
4. T-44 ✅ 後，依固定順序做 **T-42 → T-43**（貼 WORKFLOW.md §2.1 的標準
   開工 Prompt 即可，這兩張不需要本檔的特別叮嚀），再開 **Fable** 視窗做
   Phase 1.9 收尾複評（清單見 §8）。
5. T-44 結案後，`HANDOFF_T39.md`（本檔）可以刪除。

---

## §7 卡關怎麼辦

- **Sonnet 同一工程步驟連續 3 次嘗試失敗** → 停，在 TASKS.md 該卡狀態寫
  `🔴 卡關`＋原因，只 commit 文件，請使用者開 Fable 視窗。
- **正確率上不去／加了候選反而更差／分區沒有改善** → **這不是卡關**。
  照 ROUND.md 記錄、跑滿預算、誠實寫否定結論，狀態標 🔵 待驗證交 Opus。
  絕對不許為了達標改 ground truth、改驗收口徑、超預算加輪次、或動既有
  字串。
- **分區表某一格拿不定主意** → 依「分區完整性鐵則」從寬（該角色 ground
  truth 出現過的材質一律留在子集內），把猶豫寫進 PLAN 的理由欄，不是卡關。
- **T-44 因故停滯** → 依裁決 T-38B-A 延伸的例外條款，停滯期間可提前執行
  T-42（檔案範圍不相交），提前要在交接筆記註明；T-43 仍須排在 T-42 之後。
  （T-39 的「等使用者重對映」例外已不適用——T-39 已結案。）
- **13 張三軸 confidence 非預期漂移** → 紅旗，🔴 停（共同鐵則 8）。
- **臥室從擋變放** → 🔴 停，回 Fable（共同鐵則 7）。

---

## §8 T-44 之後（給下下個視窗）

- **T-42**（gate 交易式輸出與舊產物 archive 隔離）→ **T-43**（analysis.json
  生成指紋＋t17_blind_test 溯源）：**任何新的正式盲聽必須在這兩張 ✅ 之後**
  （現存盲測素材是 `d958b3c` 產的，舊 2/5 不能宣稱屬於現行碼）。
- **Phase 1.9 收尾複評（回 Fable）**：治療效果總結（對照理論上限 7/13）、
  要不要開 MINC/DMS 材質專用模型卡、**陳設換算公式修正輪的重啟評估點在
  這裡**（裁決 T-38B-A 已裁定不插隊）、T-17 複驗時機。

---

## §9 一分鐘查證本檔是否過期

```bash
git log --oneline -3 && head -5 DEV_LOG.md
```

本檔建立於 2026-09-01（Fable 裁決 T-38B-A），2026-09-02 於 T-39 驗證通過後
更新為服務 T-44。若 DEV_LOG.md 最上面一筆已晚於 `2026-09-02 (89)`，
以 DEV_LOG.md 與 TASKS.md 為準。
