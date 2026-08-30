# Dev Log

## 2026-08-30 (61)

- ✅ **T-32 Opus 驗證通過**：等效吸音面積入聲學計算與照片管線。全部驗證指令由驗證者在
  乾淨工作區親自重跑，並用 `git worktree` 另建 T-31 版（`8d1c646`）與 HEAD 版兩份獨立
  工作區交叉比對，非採信 Sonnet 自檢轉述。十套測試 exit 0；六條交付 IR MD5 逐條重生
  相同；None 分支拿 T-20／T-21 交付 JSON 重生 `diff` 為空（T-21 零差異、T-20 僅差我自己
  指定的檔名）；`ir_metrics.py`／SPEC／ROADMAP／WORKFLOW／`output/mvp_acceptance/` diff 0 行；
  `ir_synth.py`／`surfaces.py`／`coupled.py` 零 diff。
- **非假實作的實證**：F2 手算與實得誤差 `0.00e+00`；另做**變異測試**——把 Eyring 那行
  改吃 `surfaces_absorption`（模擬「只加 Sabine 不加 Eyring」紅旗），`test_acoustics.py`
  立刻 exit 1、F3 失敗，證實測試對該紅旗有真實診斷力。鐵則 6 逐行核對：`furn` 計算點
  在 gate 區塊之後（`pipeline.py:325-327`），gate 判定所依據的兩軸皆在其之前定案。
- **驗證者補測 Sonnet 未涵蓋的路徑**：`livehouse_riverside_ximen.png` 走完整管線驗證
  cap 端到端（`cap_applied=true`、cap 警告落在 `warnings`、視角說明落在 `notes`）；
  三種壞輸入皆 exit 2 無 crash；極端飽和案例不崩潰（`min(ā, 1-1e-9)` 夾子擋住 `log(0)`）。
- **四項非阻擋事項**（詳見 TASKS.md T-32 卡）：①`livehouse` 加陳設後 RT60 跌到 0.08s、
  跌破 WORKFLOW §5 的 0.1s 下限（該照片本來就被 gate 擋，不在交付路徑上，但是 cap=0.5
  偏鬆的直接證據，T-33 量測要加記兩欄）；②**T-31 遺留必須在 T-33 前補**——卡片指定的
  `data/furnishings.json` source 文件修正未執行，且從未有獨立的 `T-31: 驗證通過` commit
  （T-31 的 ✅ 被夾帶在 T-32 commit 裡，違反 WORKFLOW §4）；③TODO.md 的 T-31 狀態陳舊
  （本次已修）；④`cap_applied` 用「warnings 非空」反推、`total_ratio` 輸出 int `0`（記錄備查）。
- 下一步：補完非阻擋事項②（T-31 的 `data/furnishings.json` 文件修正），再由 Sonnet
  執行 T-33（13 張基準率複測，量測卡；量測期間 `src/` 一行不許改）。

## 2026-08-30 (60)

- ✅ **T-32 Sonnet 執行完成，自檢通過（待 Opus 驗證）**：等效吸音面積入聲學計算與
  照片管線（裁決 T-27-A 執行卡 2/3）。`acoustics.py` 的 `compute_acoustics()`
  加第四參數 `furnishings`（預設 None＝行為與加這參數前逐位元相同）：非 None 時
  逐頻段算 `A_extra[band] = Σ_c ratio_c × S_total × α_c[band]`，**同時**併入
  Sabine 的 `total_absorption` 與 Eyring 的 ā 分子（兩者共用同一個逐頻段變數，
  結構上不可能只加一邊）；`AcousticsResult` 新增 `furnishings` 欄位，`as_dict()`
  只在非 None 時輸出。`pipeline.run_photo()` 在 gate 之後、`compute_acoustics()`
  之前呼叫 `estimate_furnishings(detail)`（新旗標 `--no-furnishings` 可關），
  CLI 印偵測結果、`analysis.json` 新增 `furnishings` 鍵。`run_text`／`run_scene`／
  `ir_synth.py`／`coupled.py`／`surfaces.py` 零改動。
- 十套測試全 exit 0（新增 `test_acoustics.py` F1–F4 共 9 項斷言）；六條交付 IR
  MD5 逐一重生比對逐位元相同；`ir_metrics.py`／`pipeline.py` 的 gate 判定段／
  SPEC／ROADMAP／WORKFLOW／`output/mvp_acceptance/` 均未觸碰；診斷力實測——
  把改動 `git stash` 回 T-31 版本只留新測試，`test_acoustics.py` 對舊
  `compute_acoustics()` 呼叫 `furnishings=` 直接 `TypeError` 崩潰，還原後全部
  重新跑過確認 exit 0。實跑 `bedroom_ai_generated.png`：加陳設後偵測到
  person/bed/curtain/pillow（佔 1kHz 總吸音 87.8%），500/1kHz 代表殘響從
  ~3.7s 降到 ~0.52s，方向與地雷 #22（臥室六面模型測不到床/棉被/窗簾吸音）
  完全吻合；`bathroom_tiled.png`（無陳設）防濫殺對照確認 RT60 完全不變。
  細節見 TASKS.md T-32 卡「交接筆記」。
- 下一步：Opus 驗證 T-32；通過後 Sonnet 接著做 T-33（13 張基準率複測，量測卡）。

## 2026-08-30 (59)

- ✅ **T-31 Sonnet 執行完成，自檢通過（待 Opus 驗證）**：陳設等效吸音資料表＋
  偵測模組（裁決 T-27-A 執行卡 1/3）。新增 `data/furnishings.json`（9 類別，
  α 逐字轉錄裁決指定值，`ade_id` 已用 `SegformerConfig` 的 `id2label` 實測核對
  全部相符）、`src/image_reverb/furnishings.py`（`load_furnishings()` 載入時就擋
  id 相交／頻段不一致／α 越界，`estimate_furnishings(detail)` 從
  `class_ratios` 算逐類別比例＋cap 壓回）、`scripts/test_furnishings.py`
  （【A】【B】【C】三段，含對舊碼會 fail 的診斷力實測）。`surfaces.py` 只加三行
  轉存 `class_ratios` 進 `detail`（`git diff` 逐行核對過，無其他改動）；
  `config.py` 加三個新常數。
- 十套測試全 exit 0；六條交付 IR MD5（T-14×2／T-20×2／T-21×2）逐一重生比對
  逐位元相同；`ir_metrics.py`／`pipeline.py`／SPEC／ROADMAP／WORKFLOW／
  `output/mvp_acceptance/` 均未觸碰；gate 判定規則零改動（端到端跑
  `bathroom_tiled.png --force-low-confidence` 行為與 T-30 時一致）。
  細節見 TASKS.md T-31 卡「交接筆記」。
- 下一步：Opus 驗證 T-31；通過後 Sonnet 接著做 T-32（等效吸音入聲學計算）。

## 2026-08-30 (58)

- 🔮 **Fable 裁決 T-27-A（室內陳設吸音表示）**：採「逐頻段等效吸音面積」——
  `A_extra[band] = Σ ratio_c × S_total × α_c[band]` 直接加進 `compute_acoustics()`
  的 Sabine／Eyring 吸音項，經 `rt60_bands_sabine` 流進 IR 晚期尾巴；
  **不採 occupancy 係數**：單一寬頻旋鈕表達不了窗簾 125Hz α=0.07 vs 1kHz 0.75
  的頻率結構（重犯地雷 #8「平均 α」），且沒有現成物理插入點，每個作用位置都是
  自創規則。資料源＝ADE20K 陳設類別全圖像素佔比（零新模型）；類別 id 與六角色 id
  不相交（T-24 結構性輸入）、rug 排除（已在 floor ids）、玻璃鏡面排除（反射面）。
  全文在 TASKS.md T-27 卡。
- **開 Phase 1.7 材質修正輪四張卡（TASKS.md 檔尾）**：T-31（`furnishings.json`＋
  偵測模組，α 起始值由裁決指定、id 須經 id2label 測試驗證）→ T-32（聲學整合＋
  `--no-furnishings` 旗標，furnishings=None 時輸出逐位元相同）→ T-33（13 張基準率
  複測量測卡，含臥室/浴室分離表——補上裁決 T-28-A 不可能性證明缺的區辨訊號，
  報告交 Fable 複評 gate 規則）→ T-34（gate 訊息規則 2 死路出口＋兩處測試覆蓋，
  收 Opus T-30 兩則後續建議）。共同鐵則沿用 1.6 五條並加第 6 條：gate 判定規則
  零改動、陳設資料不得餵進任何信心軸、scene_cues 段不許動。
- HANDOFF／TODO 同步更新。純文件，未動任何程式碼。
- 下一步：使用者開 Sonnet 視窗貼 WORKFLOW §2.1 Prompt 執行 T-31。

## 2026-08-30 (57)

- ✅ **T-30 Opus 驗證通過**。所有指令由驗證者親自重跑，未採信 Sonnet 宣稱：
  九套測試全 exit 0；T-20／T-21 四條交付 IR 重生後 MD5 逐位元相同
  （`2adbaa75…`／`2dd19b6e…`／`9a94ffdf…`／`a1c21bcc…`），且重生後的
  `output/neighbor_voices/`、`output/stadium_corridor/` 與備份 `diff -rq` 完全一致；
  T-14 兩條由 `test_ir_synth`【6】內建比對。gate 判定條件確認零改動
  （`surfaces.py`／`ir_metrics.py` 不在 commit 內）。
- 實跑 `bathroom_tiled.png` 完整複現自我檢查：exit 3、只點名 `floor`(fallback)、
  未點名 `ceiling`(無來源)與四牆(clip)、無 `--override-dims` 建議、輸出目錄未建立；
  `--override-material floor=marble` 後 exit 0、`materials_confidence=medium`、
  IR 非靜音（48 kHz／5.610 s／RMS 0.008996）。
- 診斷力查核：把新版 `test_output_gate.py` 放進 HEAD~1 的 `git worktree` 實跑，
  **4 項新斷言失敗** → 不是空測試。另寫探針掃四種 (geometry, materials) 組合，
  確認依軸給建議與動態步驟編號（1/2/3、1/2、1）全部正確。
- ⚠️ 兩則後續建議（不影響通過，已寫進 T-30 卡）：①**規則 2 的死路未覆蓋**——
  materials=low 由「六面全同」觸發且無 fallback 面、geometry 非 low 時，
  訊息只剩 `--force-low-confidence`，T-28 的「儀式化 --force」原樣重現；
  這是卡片規格邊界（步驟 1/2 只從 fallback/ood 清單造骨架），非 Sonnet 瑕疵，
  需 Fable 另開卡。②`geometry=low` 的 `--override-dims` 分支無測試覆蓋。
- 下一步：Fable 裁決 T-27（室內陳設吸音，材質修正輪前置）。

## 2026-08-30 (56)

- 🔵 **T-30 完成，待驗證**：gate 出口導引（裁決 T-28-A 執行卡）。只改
  `pipeline.run_photo()` 低信心分支印的訊息，gate 判定條件（`compute_materials_
  confidence()`／`run_photo()` 觸發放行邏輯）逐行未動。新訊息逐面點名
  `fallback`／`out_of_domain` 面（無來源面／clip 面不列，避免誤導——地雷 #23）、
  依軸分開給建議（`geometry=low` 才印 `--override-dims`；`materials=low` 才印
  可直接複製的 `--override-material 面=<材質id>` 指令骨架＋查表提示＋規則 2
  退化警語）、`--force-low-confidence` 文案標明不建議當常規路徑。
- `scripts/test_output_gate.py` 新增案例【D】（materials=low、geometry=medium
  → 斷言 stderr 不含 `--override-dims` 但含 `--override-material`），案例【A】
  加四項 stderr 內容斷言（改用 floor=fallback／ceiling 無來源／四牆 clip 的
  混合 fixture，複現 `bathroom_tiled` 真實分佈）。
- 驗證：九套測試全 exit 0；六條交付 IR MD5 逐一重生比對（T-14 由
  `test_ir_synth.py`【6】內建；T-20 `2adbaa75…`／`2dd19b6e…`、T-21
  `9a94ffdf…`／`a1c21bcc…`手動重生）全部逐位元相同；`ir_metrics.py` diff 空；
  SPEC/ROADMAP/WORKFLOW/`output/mvp_acceptance/` 未觸碰。實跑
  `bathroom_tiled.png`：不帶旗標 exit 3 且訊息只點名 floor，加
  `--override-material floor=marble` 後 exit 0 且 `materials_confidence=medium`。
- 下一步：Opus 驗證 T-30；通過後回 Fable 裁決 T-27（室內陳設吸音）。

## 2026-08-30 (55)

- 📋 **HANDOFF.md 全面更新到現況**（先前停在 (41)，落後 12 筆——上一輪零信用
  複驗點名的過期文件）：「一分鐘進入狀況」重寫（T-17 兩項未達標、13 張照片
  100% 被 gate 擋、裁決 T-28-A 摘要）、進度表補 T-17 實況與 T-23~T-30 十列、
  §5 環境速查補 gate 說明（`--override-dims` 單獨解不了 gate；正規出口是
  `--override-material` 覆寫 fallback/ood 面）、§7 交接流程改為
  「Sonnet 執行 T-30 → Opus 驗證 → Fable 裁決 T-27」、提醒區換成 T-30 紅線
  與地雷 #23/#24。
- 純文件更新，未動任何程式碼。
- 下一步：使用者開 Sonnet 視窗貼 WORKFLOW §2.1 Prompt 執行 T-30。

## 2026-08-30 (54)

- 🔮 **Fable 裁決 T-28-A（gate 擋 13/13）**，裁決前先做零信用複驗：13 張照片
  逐張親自重跑（13/13 exit 3 復現）、六條交付 IR 由 HEAD 重生成 MD5 全數相符、
  九套測試全 exit 0、gate 擋下時零檔案寫出（既有輸出目錄 mtime 未動）。
- **複驗更正了 T-28 卡三處數據**：① materials=low 是 **12/13** 非 13/13
  （DivorceBeach 是 materials=medium，被 geometry=low 擋）；② 「fallback 10／
  ood 5／clip 12 面」單位其實是**照片張數**，真實面數分布（78 面）為
  fallback 32／ood 13／clip 22／**無來源 11**；③ 被擋原因拆解＝僅材質 7 張／
  僅幾何 1 張／雙軸 5 張——**修好材質規則仍有 6/13 被 geometry=low 擋**。
- **裁決內容**：(1) **gate 規則不動**——決定性理由是不可能性證明：臥室（必須
  續擋）與浴室（盲聽答對案例）六面「材質＋來源」逐面完全相同，任何只讀來源的
  規則放浴室必放臥室；區辨訊號（室內陳設）在現有資料裡不存在。(2) **開執行卡
  T-30（gate 出口導引）**：實測 `--override-dims` 單獨走不通（exit 3），唯一
  可行的非 force 出口（覆寫 fallback/ood 面 → medium → exit 0）訊息裡沒提——
  T-30 讓 gate 逐面點名並給可複製指令，規則一行不動、六條 MD5 不變。
  (3) **準確度先行**：T-27／材質輪之後用新基準率複測 13 張再談調規則。
- **新增 HANDOFF 地雷 #23（無來源第四狀態）、#24（透視照 materials high
  結構性不可達——規則 3 要求零 warnings，但透視照必掛共用牆 warning，條件恆假）**。
- 另修 TODO.md 過期狀態（Phase 1.6 區塊 T-23/T-26 誤標 🔵，實已 ✅）。
- 下一步：Sonnet 執行 T-30；T-27 仍待 Fable 裁決（等效吸音面積 vs occupancy）。

## 2026-08-30 (53)

- ✅ **修正輪第二批全過：T-24 / T-25 / T-26 三張皆 Opus 驗證通過**，
  加上第一批的 T-23，**四張執行卡全部完成**。
- **規劃者獨立複驗（不採信 agent 回報）**：九支測試套件自己重跑全 exit 0；
  六條交付 IR 自己重生比對 **MD5 零回歸**；
  `git diff a98624a HEAD` 對 `ir_metrics.py`／SPEC／ROADMAP／WORKFLOW／
  `output/mvp_acceptance/` **全為空**；gate 實測體育館 exit 3 且
  **輸出目錄完全沒被建立**（證明 gate 在合成之前）；加 `--force-low-confidence`
  → exit 0 且 JSON 有 `forced_low_confidence: true`；臥室 `medium → low`
  且 `ir_mono.wav` MD5 未變；`grep ADE_TRUSTED_MATERIAL src/` = 0 行。
- **🔴 但複驗發現一個規劃者自己的規格錯誤（開 T-28）**：gate 上線後
  **專案裡 13 張照片 100% 被擋**（§7-2 八個場地 8/8＋§7-1 五張 5/5）。
  根因是 T-25 卡片把 `materials_confidence` 定成「六面任一面 fallback → low」，
  而實測六面來源分布是 fallback 10 面／out_of_domain 5 面／clip 12 面——
  CLIP 門檻 0.4 下至少一面 fallback 幾乎必然，這條規則等價於「永遠 low」。
  **T-25 的實作完全照卡片做、驗證者也正確驗了規則邏輯；錯的是卡片規格本身。
  規劃者寫規則時沒有先量基準率——這是規劃錯誤，不是執行或驗證錯誤。**
  T-28 記錄了兩難（擋得對 vs 擋過頭）並明訂「不要用調鬆門檻草草了事」，
  要調必須附實測且**臥室那筆必須仍被擋住**。
- **另開 T-29**：三軸信心只加在 `run_photo()`，`--text` 只有 `confidence`、
  `--scene` 連 `confidence` 都沒有。T-25 驗證者已主動揭露，規劃者實測確認。
  未必是 bug（preset 路徑的信心語義不同），但三條管線 schema 不一致要有意識地決定。
- **REPORT §7 已補**：2026-08-30 後重生 IR 需加 `--force-low-confidence`；
  並聲明本報告數字仍有效（gate 只擋輸出、不改合成邏輯，MD5 全程零回歸）。
- 下一步：T-27（室內陳設吸音）與 T-28（gate 基準率）都需要 Fable 裁決。

## 2026-08-30 (52)

- **T-26 完成，🔵 待驗證**：`pipeline.run_photo()` 加輸出 gate——overall
  confidence 為 `low` 時，在 T-13 聲學計算**之前**就擋下（不只是擋在寫檔前，
  連合成運算都省了），不寫任何 WAV／JSON，印繁中錯誤說明＋兩條可行的下一步，
  `return 3`。唯一明確出口是新 CLI 旗標 `--force-low-confidence`（併入
  `--override-dims`／`--override-material` 那組「僅照片輸入」限制）：帶了就
  照樣輸出，但 `analysis.json` 留下 `forced_low_confidence: true` 與一條
  warnings 說明，CLI 也印顯著警告。`--override-dims` 不會自動解除 gate——
  幾何信心墊高了，材質信心（常見成因：`floor` CLIP 信心不足 fallback）沒有
  連帶被解除，overall 仍取兩者較低者。只動照片管線，`run_text()`/`run_scene()`
  沿用 T-25 已記錄的觀察，維持舊語義不變。
- **執行中發現卡片自我檢查的一個假設過期了**：卡片寫「`bathroom_tiled.png`
  （medium）」，但實測**現行 9 張 `assets/photos/` 全部是 overall=low**
  （單張透視照的通病：四面牆共用同一判定值＋`floor` 常 fallback，T-25 規則①
  幾乎必中）。已如實記錄、用 `git stash` 證明這不是本卡造成的回歸（改動前
  這張照片印出的信心值本來就是 low，只是舊碼沒有讀它），並用
  `--override-dims`＋三個互不相同的 `--override-material` 人工建構出真正的
  `overall=medium` 案例，改動前後 MD5 逐位元相同，佐證 medium 路徑確實
  不受 gate 影響。
- **新增 `scripts/test_output_gate.py`**：樁掉 `preprocess_image()`／
  `surfaces_from_preprocess()`（避免每次都要跑深度/CLIP/分割模型），配合
  `--override-dims` 走既有的手動幾何分支，`compute_materials_confidence()`
  以降的 T-13/T-14/wet preview 全走真實程式碼。四部分：CLI 接線
  （subprocess，非照片輸入帶旗標要報錯）／low 不帶旗標（exit 3、無輸出目錄、
  `synthesize_ir` 呼叫次數 delta=0）／low 帶旗標（exit 0、JSON 標記、
  `synthesize_ir` delta=3）／medium（不受影響、delta 同樣是 3）。`git stash`
  還原到修改前重跑：三項斷言真實失敗（低信心輸入照樣算完、照樣寫出 wav），
  證明非空測試。
- **共同鐵則全過**：九套測試（含 T-23/T-24/T-25 新增的三支）全部 `EXIT=0`；
  六條交付 IR MD5 全部相符；`ir_metrics.py` diff 0 行；SPEC/ROADMAP/WORKFLOW/
  `output/mvp_acceptance/` 零改動；本輪只動 `pipeline.py`／`cli.py` 兩個檔
  ＋新測試檔。
- **⚠️ 已知連帶影響（卡片已預告）**：T-17 §7-2 有數個場地是 `low`
  （DivorceBeach／gym／restaurant／SteinmanHall），之後重跑驗收要加
  `--force-low-confidence`，否則會被擋下。REPORT 補說明留給 T-17 重跑時處理，
  本卡沒有動 REPORT 或 `output/mvp_acceptance/`。
- 下一步：Opus 驗證 T-26 → 通過後 Phase 1.6 四張修正卡全部結案，回頭處理
  TODO.md 的「§7-1＋§7-2 要不要再加一輪」與 T-27（Fable 裁決）。

## 2026-08-30 (51)

- **T-25 完成，🔵 待驗證**：`analysis.json` 的 `confidence` 從「直接等於
  `est.confidence`（只反映幾何）」拆成三軸——新增 `geometry_confidence`
  （＝原本的 `est.confidence`）與 `materials_confidence`（新函式
  `surfaces.compute_materials_confidence()`：任一面來源是 `fallback`/
  `out_of_domain` → low；六面材質全部相同（退化）→ low；六面皆 `clip` 且
  無警示 → high；其餘 → medium），`confidence` 改成 overall＝兩者取較低者
  （`pipeline._overall_confidence()`）。只動 `run_photo()`（照片管線），
  `run_text()`/`run_scene()` 未動——卡片描述的問題（T-17 §7-1 臥室、
  `--override-dims` 一律 high）都是照片管線特有。
- **臥室實測驗證修好了卡片描述的兩個 bug**：①`assets/photos/bedroom_ai_generated.png`
  的 `confidence` 由 `medium`→`low`（地板是 fallback，舊行為看不出來）；
  ②同一張照片加 `--override-dims 4x3x2.5`，geometry 拿到 `high` 但 overall
  正確被材質壓到 `low`（舊行為會整體標成 `high`）。`ir_mono.wav` MD5 兩次都是
  `989b9f354df926fea376ff94c2099526`，跟改動前逐位元相同——metadata 改動沒
  動到音訊。
- **新增 `scripts/test_confidence_axes.py`**（11 項，純資料不下載模型）：
  卡片指定的三個案例＋兩個邊界案例（`_overall_confidence`）、
  `compute_materials_confidence` 四條規則各自的正反案例。`git stash` 還原到
  改動前重跑：`ImportError`（`_overall_confidence` 不存在）`EXIT=1`，證明非
  空測試。
- **共同鐵則全過**：八套測試（含 T-23/T-24 新增的兩支）全部 `EXIT=0`；六條
  交付 IR MD5 全部相符（`chk_bath`/`chk_church`/`coupled_neighbor_voices`/
  `coupled_stadium_corridor` 逐一複驗，T-14 兩條由 `test_ir_synth.py`【6】
  硬編碼比對）；`ir_metrics.py` diff 0 行；SPEC/ROADMAP/WORKFLOW/
  `output/mvp_acceptance/` 零改動；本輪只動 `pipeline.py`／`surfaces.py`
  兩個檔＋新測試檔。
- 下一步：Opus 驗證 T-25 → 通過後接 T-26（低信心／域外輸入的輸出 gate）。
  留了個非本卡範圍的觀察給 T-26：`run_text()`/`run_scene()` 的 `confidence`
  還是舊的純幾何語義，T-26 要用信心 gate 時記得確認它鎖定哪些輸入類型。

## 2026-08-30 (50)

- **T-24 依裁決 T-24-A 重做完成，🔵 待驗證**：`ADE_TRUSTED_MATERIAL` 整張表、
  迴圈裡不可達的 `trusted_hits`/`best_trusted` 計分區塊、依附其上的 note 字串，
  全部從 `src/image_reverb/surfaces.py` 刪除；三處誤導性註解（module docstring、
  常數上方、迴圈內）改寫成描述現況（這段計分在現行架構下不可能觸發，原因是
  角色 id 與可信 id 構造上不相交），順手也清了 `SurfaceObservation.confidence`
  欄位一句同類殘留描述。`classify_region_material` 呼叫與 `material_id` 來源
  邏輯一字未動。`scripts/test_surface_trusted_scope.py` 改寫成移除後的不變量
  測試：斷言 `surfaces` 模組不再有 `ADE_TRUSTED_MATERIAL` 屬性、`analyse_image`
  輸出不再出現「語意可信」字樣的 note。
- **診斷力實測**：`git stash` 只暫存 `surfaces.py`（新測試檔留著）重跑新測試，
  斷言①（`hasattr` 檢查）在舊碼上確實 `EXIT=1`，證明測試有抓到死碼還在的能力；
  還原後 working tree 乾淨。
- **共同鐵則全過**：六套測試（含新的 `test_surface_trusted_scope.py`）全部
  `EXIT=0`；六條交付 IR MD5 重新生成比對全部相符
  （`chk_bath`/`chk_church`/`coupled_neighbor_voices`/`coupled_stadium_corridor`
  四條逐一複驗，T-14 兩條由 `test_ir_synth.py`【6】硬編碼比對）；
  `ir_metrics.py` diff 0 行；SPEC/ROADMAP/WORKFLOW/`output/mvp_acceptance/`
  零改動；本輪只動了 `surfaces.py` 與 `test_surface_trusted_scope.py` 兩個檔。
- **自我檢查的一個誠實例外**：卡片寫「`grep -rn ADE_TRUSTED_MATERIAL src scripts`
  無任何輸出」，`src/` 確實乾淨，但 `scripts/test_surface_trusted_scope.py`
  裡有 8 行——因為新測試本身就是要斷言「這個屬性不存在」，沒辦法在不寫出這個
  識別字的情況下測試它的缺席。已在 TASKS.md T-24 交接筆記把完整 grep 輸出
  逐行列出，讓 Opus 判斷這是合理的例外還是不合格。
- 下一步：Opus 驗證 T-24 → 通過後接 T-25（confidence 拆三軸）。

## 2026-08-30 (49)

- **修正輪 workflow 第一批結果**：T-23 ✅ 通過、T-24 🟠 退回（卡在需要裁決）、
  T-25/T-26 未跑（規劃者設的中斷條件過嚴，見下）。
- **🔬 T-24 揭露的結構性發現（比原診斷更深一層）**：ADE 可信材質分支不是「還沒實作」，
  是**設計上不可達**。ADE20K 每個像素只有一個 label——curtain 像素的 label 就是
  `curtain(18)`，不是 `wall(0)`，所以「在 wall 的 mask 內找 curtain 佔多數」
  永遠不成立。獨立核對：可信 ids `[8,9,12,18,23,27,30,31,147]` 與
  floor/ceiling/wall 三個 id 集合**交集全為 ∅**。
  → **第一輪把計分改成 mask 內是對的修正**，正是它揭露了整個功能不可達；
  先前「看起來有作用」只是因為在數全圖。
- **🔮 裁決 T-24-A（Opus 規劃者）：選 (b) 移除死碼，可信類別搬去 T-27。**
  理由：①不可達是構造性的，不是漏寫；②保留不可達佔位＝再種一個「文件與執行不一致」，
  正是本輪要清的東西（地雷 #19/#21）；③移除零風險（不可達 → 行為不變 → MD5 不變）；
  ④可信類別有價值，但正確位置是「房間裡還有多少額外吸音」＝T-27。
  **這張卡不需要再等 Fable**——本裁決只決定移除死碼，屬維護範圍；
  真正的設計決策（等效吸音面積 vs occupancy）原封不動留在 T-27。
- **📝 規劃者自己的錯誤：workflow 中斷條件設太粗。** 原腳本是「任一卡未通過就停」，
  理由寫「後面的卡依賴它」。實際依賴鏈只有 **T-25 → T-26**；T-24 動的是
  `surfaces.py` 的死碼、與 T-25/T-26 無關，且 T-24 本輪根本沒改任何程式碼，
  不存在衝突。**T-25/T-26 是被我誤擋的，不是真的被阻塞。** 下一輪修正中斷條件。
- **驗證品質記錄（值得保留的做法）**：T-24 的驗證者沒有只讀碼——自己做了 3000 張
  刻意塞滿可信類別的 labelmap fuzz（可信 note 出現次數 = 0），也自己 `git stash`
  還原舊碼驗新測試的診斷力，並且替 Sonnet 說明「停下來是照卡片＋CLAUDE.md 卡關
  規則做的，程序上正確」。
- 下一步：重跑 workflow 做 T-24（新範圍）→ T-25 → T-26。

## 2026-08-30 (48)

- 🔴 **T-24 卡關（修正退回理由這輪）**：拿到 Opus 退回理由 1–4 後先確認
  `surfaces.py`／`test_surface_trusted_scope.py` 自退回 commit `23c289f` 起沒被
  再動過，可以直接對照動工。但理由 1／2 的「重做方向」要求在「(a) 保留程式碼
  並標成不可達佔位」與「(b) 把 `ADE_TRUSTED_MATERIAL` 整段搬去 T-27、真的從
  `analyse_image()` 拿掉」之間二選一，且**加粗寫了兩次**「哪一個都必須先問
  Fable 裁決，不要自己決定刪表」——這是 Opus 規劃時刻意設下的架構裁決關卡，
  不是 Sonnet 能自己選的技術細節：選哪個會直接決定註解怎麼寫（理由 2）、
  新測試要測什麼才有長期診斷力（理由 4）。依 CLAUDE.md 卡關規則，這裡停下、
  沒有改動任何程式碼，把裁決兩個選項與判斷依據整理進 TASKS.md T-24「退回修正
  紀錄」，狀態改 🔴 卡關，請使用者開 Fable 視窗做裁決。
- 同時在 TASKS.md 承認並更正理由 3：上一輪交接筆記「可信類別只影響 note，
  不影響 material_id」的前半句不成立（角色 id 與可信 id 集合不相交，這段
  計分連 note 都不會被觸發），並記錄上一輪測試註解其實已經寫到關鍵線索
  （windowpane id=8 不在任何角色 id 集合裡）卻沒推廣成通用結論、也沒回報矛盾。
- 共同鐵則 1–5 本輪未重跑（沒有動過程式碼，Opus 上一輪的複驗結果仍有效）；
  六條交付 IR MD5 與 `ir_metrics.py` 因此也維持不變。本輪只 commit 文件
  （`docs: T-24 卡關紀錄`），不 push。

## 2026-08-30 (47)

- 🔵 **T-24 完成（Phase 1.6 四張卡第二張）：ADE 可信材質分支計分錯誤與死碼**
  （REPORT §2.6 缺陷 D）。`surfaces.py` 的 `trusted_hits` 曾用 `segment_roles()`
  回傳的**全圖** `ratios` 去跟每個角色比對，完全沒被角色 mask 限制——windowpane
  全在畫面上半時，`floor`／`ceiling`（在下半、跟 windowpane 零重疊）的 note 卻
  雙雙宣稱「40% 屬語意可信類別」。改成用 `labelmap[mask]` 只算該角色 mask 內的
  比例，門檻同步從 `ratio * 0.5`（混用兩種分母、邏輯不對稱）改成 `0.5`
  （`role_ratios` 已是角色內部比例，對稱比較才對）。
- 同時清掉誤導性註解：module docstring 與 `ADE_TRUSTED_MATERIAL` 上方兩處
  「這些不必問 CLIP」改成描述現況（可信類別只影響 note，不影響 `material_id`，
  直接映射待 T-27 設計）；`SurfaceObservation.method` 欄位註解移除從未被指派的
  `"ade_trusted"`，只留實際會出現的 `"clip"` / `"fallback"` / `"out_of_domain"`。
  **`material_id` 的來源邏輯（`classify_region_material()` 那條路徑）完全沒動。**
- 新增 `scripts/test_surface_trusted_scope.py`：合成 labelmap（可信類別集中上半、
  floor/ceiling 在下半且零重疊），樁掉 segmenter／CLIP，斷言 floor/ceiling 的
  note 不再誤宣稱擁有可信類別。**診斷力已實測**：`git stash` 還原舊碼後跑同一支
  測試 exit 1（floor/ceiling note 都宣稱「50.0% 屬語意可信類別」），確認不是
  空測試，`git stash pop` 還原乾淨。
- **鐵則全過**：五套既有測試 exit 0；六條交付 IR 的 MD5 全部不變（浴室/大教堂/
  neighbor_voices/stadium_corridor，逐一重跑複驗，T-14 兩條由
  `test_ir_synth.py`【6】硬編碼比對過）；`ir_metrics.py` 的 `git diff` 為 0 行；
  未動 SPEC/ROADMAP/WORKFLOW/output/mvp_acceptance。
- 下一步：Opus 驗證 T-24 → 通過後接 T-25（confidence 拆幾何／材質／overall 三軸，
  前置依賴本卡）。

## 2026-08-30 (46)

- 🔵 **T-23 完成（Phase 1.6 四張卡第一張）：fallback 材質單一事實來源**
  （REPORT §2.6 缺陷 F／地雷 #21）。`data/materials.json` 的 `fallback_id` 由
  `"generic_wall"` 改成 `"gypsum_board"`（Opus 裁決：這是現行實際行為，改文件不改值）；
  `config.py` 的 `DEFAULT_WALL_MATERIAL` 改成**從 materials.json 動態讀取**，不再是
  寫死字面值；`config.py:103`、`surfaces.py` docstring 的 `generic_wall` 說法一併改成
  `gypsum_board`。**只改文件與讀取方式，`classify_region_material()` 三個 return 出口
  的邏輯完全沒動。**
- 新增 `scripts/test_material_fallback.py`：斷言 config 常數與 JSON 值一致、id 存在於
  材質表、現行值確實是 `gypsum_board`。**診斷力已實測**：暫時把 fallback_id 改回
  `generic_wall`，新測試 exit 1（❌ fallback_id == 'gypsum_board'：實際值
  'generic_wall'），確認不是空測試，跑完用 `git checkout` 還原乾淨。
- **鐵則全過**：五套既有測試 exit 0；六條交付 IR 的 MD5 全部不變（浴室/大教堂/
  neighbor_voices/stadium_corridor）；`ir_metrics.py` 的 `git diff` 為 0 行；
  未動 SPEC/ROADMAP/WORKFLOW/output/mvp_acceptance。
- 下一步：Opus 驗證 T-23 → 通過後接 T-24（ADE 可信材質分支計分修正，鐵則要求
  T-23→T-24→T-25→T-26 依序做，避免 `surfaces.py`/`pipeline.py` 併行衝突）。

## 2026-08-30 (45)

- **收到外部 bug 診斷，Opus 逐條查證後確認五條全部屬實**（未採信轉述，讀碼＋執行期重現）：
  - **🔴 缺陷 D：ADE20K 語意可信材質分支是 dead behavior**。註解兩處寫「不必問 CLIP」，
    程式每次都問；`best_trusted` 只拿去串 note 字串；`"ade_trusted"` 全專案只存在於
    記錄 method 可能值的註解裡，**從未被指派**。執行期重現：windowpane 佔 40% 時，
    三個角色 `material_id` 全是 CLIP 的 concrete。
    **附帶發現（比原診斷更嚴重）**：`trusted_hits` 用全圖 ratios、未被角色 mask 限制，
    重現中 windowpane 全在畫面上半，floor/ceiling 的 note 卻都宣稱 40% 屬可信類別
    → **補個 if 就啟用會引入新錯誤**。→ 地雷 #19
  - **🔴 缺陷 E：pipeline 已判定不可信仍無條件輸出 WAV**（`pipeline.py:225-239` 無 gate）
    → 地雷 #20。與本報告 §1.2 從產品面記錄的是同一問題的兩個視角。
  - **🟠 缺陷 F：fallback 材質四處說法不一致**（materials.json `generic_wall`
    vs config 實際 `gypsum_board` vs 兩處註解）→ 地雷 #21。
  - **🟠 缺陷 G（我自己的交付物）：`t17_blind_test.py` 只檢查檔案存在**，
    等於允許拿舊產物驗收新程式。**已當場修好並實測護欄會觸發**（情境 A 照片比產物新
    → exit 1；情境 B 記錄來源對不上 → exit 1；情境 C 正常 → exit 0，
    五個盲聽檔 MD5 未變）。新增 `blind_test/MANIFEST.json`（git revision＋sha256）。
- **📝 據實更正本報告的過度延伸**：首版在 §0 與 §6 把 §7-1 概括成「與 §7-2 撞出同一個
  病因（材質）」。**這個概括不精確**——§1.2 的逐案歸因本身是對的（幾何／域外／材質各一），
  但摘要層把三個不同根因壓成一個。**修正輪若只打材質，sample_1／sample_2 不會被修好。**
- **📝 據實更正 §1.3 的標註錯誤**：首版把 `generic_wall` 標成 fallback。
  查 `surfaces_sources` 後確認臥室四面牆是 `clip` 不是 `fallback`，`generic_wall`
  是 CLIP 的正常候選（提示詞 "a plain smooth plastered wall"）。
  **會標錯正是因為缺陷 F**——資料檔與註解都說 fallback 是 generic_wall。
  連帶更正 sample_4 的歸因：牆判得沒錯，錯在**床/窗簾/地毯在六面模型裡無處可放**
  ——模型結構限制，不是辨識準確度問題（地雷 #22）。
- **未動 `src/`**：缺陷 D/E/F 屬引擎程式，是 Fable 修正輪的裁決範圍，
  本卡只查證與記錄，`git diff -- src/` 為空。
- 下一步：交 Fable 裁決修正輪範圍（**只打材質不足以修好 §7-1 的兩題**）。

## 2026-08-30 (44)

- 🔵 **T-17 四項驗收標準全部有結果**（使用者回饋已補進 REPORT）：
  **§7-1 未達標 2/5、§7-2 未達標、§7-3 ✅ 通過、§7-4 已執行並記錄。**
- **🔬 §7-1 的價值不在分數，在錯誤結構——管線把空間大小做反了**：
  體育館（實際 ~150m 跨距）估成 **30.8 m³**、1kHz T30 **0.324s** → 使用者聽成車內；
  臥室做成 **3.558s** → 聽成教堂；SUV 車內估成 **332 m³**。
  逐案量測後確認**使用者的耳朵每一題都正確描述了聲音，錯的是管線**。
  §7-1（耳朵）與 §7-2（量測）是兩條獨立證據鏈，**撞出同一個病因：材質**。
- **🔴 最危險的是臥室**：唯一沒被攔下來的（`medium`、無空間/材質警示），
  六面全是 `generic_wall`×4＋`gypsum_board`×2（1kHz α 0.03–0.04），
  真實臥室有床/地毯/窗簾（α 0.37–0.72）。
- **🔴 新產品層議題**：體育館與車內的防呆規則**都正確作動了**（`low`＋明確警示），
  產品照樣輸出聽起來是別的空間的 IR → **降信心不等於保護使用者**。
  `confidence: low` 該不該升級成「拒絕輸出／強制手動尺寸」，交 Fable。
- **§7-4 聽感與量測互相印證**：無「鐵筒子」artifact（地雷 #9 修正仍有效）；
  壁球場材質判錯 vs 改對「有差異」→ 耳朵獨立佐證 §2.4 病因診斷；
  聽感說改對版還應再少 1–1.5 秒，量測 2kHz +1.42s／4kHz +0.71s／1kHz +2.16s
  ——**同方向同量級**，證實系統性偏長不是量測假象。
- **誠實限制寫進 REPORT §5**：§7-1 只有 n=5、一位聽者、聽一次，2/5 與隨機期望 1.0
  的差距**統計上不顯著**，分數不能單獨下結論；fallback 材質的 α 表雖然清楚，
  但跨場地相關性**去掉一個點 r 就從 −0.57 翻成 +0.90**，不足以當證據。
- 下一步：📷 補照片來源網址（裁決 E 結案前置）；交 Fable 裁決是否加修正輪
  （**建議打材質**）與 `confidence: low` 的產品行為。

## 2026-08-30 (43)

- 🔵 **T-17 MVP 驗收執行完畢（Opus 主導）**，產出
  `output/mvp_acceptance/REPORT.md`。§7-2 已完成且**明確未達標**；
  §7-1／§7-3／§7-4 素材備妥但需使用者操作，尚無結果。依裁決 E（照片來源網址未補齊）
  狀態最高停在 🔵。
- **§7-2 分組達標率（裁決 C，未合併）**：自動幾何組 **9/40（22%）、0/8 場地全達標**；
  手動尺寸組 **5/25（20%）、0/5**。唯一接近的是 `SteinmanHall`（500Hz–4kHz 四頻段全過，
  只差聯合帶 +30%）。
- **🔬 病因隔離——問題在材質，不在幾何也不在引擎**：必測反例壁球場，同一支引擎只換輸入，
  自動 −50% → 換官方標準尺寸 **−61%（更差）** → 只把材質改對 **+13%（125Hz −3.3%）**。
  CLIP 把壁球場的牆判成 `curtain_fabric` 且**未觸發任何警示**（正常 `clip` 結果），
  直接印證地雷 #13。→ 已補進 HANDOFF **地雷 #18**。
- **裁決 B 事後檢驗（誠實回報）**：聯合帶通過 4/13、逐頻段 125Hz 4/13、250Hz 4/13
  ——**三者一樣**。裁決 B 修好了量測，但被量測的東西本來就錯。殘留風險逐場地檢查：
  階梯比 0.669–1.259，**沒有場地接近觸發區** → 自陳的殘留風險未發生。
- **🐛 新缺陷三個**：A（🔴）`is_equirect()` 只看長寬比，把 2592×1296 的一般透視照
  誤判成環景還給 `medium`（EXIF＋目視＋SOURCES 三重佐證）→ **地雷 #16**，
  本專案第六次「安靜地輸出看似合理的錯誤結果」；B（🟠）`--override-dims` 一律 `high`
  但材質是猜的 → **地雷 #17**；C（🟡）戶外場地無拒絕出口（`divorce_beach` +676%）。
- **合規與可重跑**：`git diff -- src/image_reverb/ir_metrics.py` 為空（`src/` 一行未動）；
  聯合帶參數全場地共用未調整；立體聲真實 IR 逐聲道量測不做聲道相加；
  新增三支腳本（量測／統計／盲聽素材），**重跑產物逐位元一致**（md5 實測），
  REPORT 數字無一手打。
- 下一步：使用者做 §7-1 盲聽、§7-3 載入 plugin、§7-4 試聽、補照片來源網址；
  之後交 Fable 裁決是否加修正輪（**建議打材質不要打幾何**）。

## 2026-08-30 (42)

- ✅ **T-18 Opus 驗證通過**（乾淨環境 `git clone` 到暫存目錄重跑，非沿用工作區）。
  四支腳本退出碼實測：`test_t30_low_combined.py` 0、`check_audio.py` 無參數 **2**、
  `test_segmentation.py` 全失敗 **1**／路徑不存在 2、三套件（ir_synth 23 項／
  scene_text／coupled）全 0 且 `❌` 次數為 0。
- **紅旗逐條排除**：①「偷改既有量測程式」→ `git diff -U0` 只有 `@@ -127,0 +128,39 @@`，
  **刪除行數 0**，純檔尾追加；②「循環論證」→ 真值取自解析包絡 `10^(-3t/T60)`，
  且 Opus **另建一套獨立量測實作**（FIR + filtfilt，與受測的 Butterworth/sosfiltfilt
  設計不同）交叉比對，掃 0.3–5.0s 五組受測誤差 +1.7%/−0.2%/−2.3%/+1.6%/+0.5%，
  兩套實作互相印證；③「退出碼修正波及成功路徑」→ 兩處都只在失敗分支內，成功路徑實測仍 0。
- **裁決 B 的機制被獨立證實，不是採信轉述**：Opus 自建對照——兩個八度同速衰減時
  聯合帶 +0.0%/−0.6% 而逐頻段 125Hz 已 +3.9%/+4.7%；異速時（125 帶 0.40s、250 帶 1.20s）
  逐頻段 125Hz 量到 **0.8195s（+105%）**，與 T-14 裁決記載的 +105% 混頻偏差
  數量級方向完全吻合。聯合帶落在兩帶之間，符合「共享邊緣內部化」的設計意圖。
- **MD5 零回歸由 Opus 自己重生比對**（不採信「沒動合成路徑」的推論）：T-20 兩條另存
  新檔重生、T-21 兩條先記舊值再重生覆寫、T-14 兩條由測試硬編碼比對——**六條逐位元相同**。
- 附 4 項非阻斷觀察給 T-17（測試訊號與受測函式同一濾波器設計故測不到帶外洩漏、
  地毯房那項本就非硬判準、354/500Hz 共享邊緣殘留風險未排除故 REPORT 階梯比欄不可省、
  超短 IR 錯誤訊息是 scipy 英文原文）。
- 下一步：**T-17 MVP 驗收**（低頻判準工具已就緒並通過驗證）。

## 2026-08-30 (41)

- 🔵 **T-18 驗收前置完成（Sonnet 自檢通過，待 Opus 驗證）**：`ir_metrics.py`
  純新增 `t30_low_combined()`（88.4–353.6Hz 低頻聯合帶 T30，取代 T-17 §7-2
  已裁決要換掉的低頻八度帶逐頻段量測），既有函式 `git diff` 零改動。
  新增獨立測試 `scripts/test_t30_low_combined.py`：解析構造已知 RT60（0.5s/2.5s，
  非循環論證）誤差 -4.1%/+2.9%（判準 ≤10%）；地毯房參考量測 0.9823s，落在
  合理區間內且接近 125Hz/250Hz 錨點。
- **退出碼技術債收斂（地雷 #10）**：`check_audio.py` 無參數 exit 0→2；
  `test_segmentation.py` 全部圖片失敗 exit 0→1（與 `test_depth.py` 一致），
  兩者皆實測驗證（自建假圖片檔觸發失敗路徑），非改完沒測。
- **六條交付 IR MD5 零回歸逐一重跑複驗**（非只信任「本卡沒動合成路徑」的推論）：
  T-14 兩條（`test_ir_synth.py`【6】）、T-20 兩條（`gen_ir_from_text.py`
  「浴室」／「大教堂」）、T-21 兩條（`gen_ir_coupled.py` neighbor_voices／
  stadium_corridor）**六條全數與 TASKS.md 記錄的 MD5 逐位元相同**。
  `test_ir_synth.py`／`test_scene_text.py`／`test_coupled.py` 三套件全過。
- 下一步：Opus 驗證 T-18；通過後進 T-17（低頻判準已由本卡工具落實 T-17 卡裁決 B）。

## 2026-08-30 (40)

- ✅ **T-16 Opus 驗證通過**（乾淨環境重跑，先 `rm -rf` 掉輸出目錄再跑，不是沿用
  Sonnet 留下的檔案）。9 張照片＋環景 SteinmanHall＋2 文字＋2 場景共 14 次全 `exit 0`、
  `analysis.png` 全產出；音訊非靜音（RMS 0.0058/0.0141/0.0490）；4 支測試腳本全過；
  不存在的檔案／非圖片皆為清楚中文訊息、無 traceback。
- **「數字取自 JSON」用程式驗，不是目測**：攔截 matplotlib figure，把每根 bar 的
  `get_height()` 與每個 Text artist 抓出來對 `analysis.json`。五個輸出共 **96 根 bar，
  高度與 JSON `closed_loop.bands[]` 的 target/measured 最大誤差 0**（完全相等，非近似）；
  bar 數字標籤全部等於 JSON 四捨五入 2 位；`warnings` 逐條原文出現在 PNG。
  Sonnet 自檢宣稱的「<1e-6／<0.001 誤差」實測其實是 0——它比對的是頂層
  `rt60_bands_target_sabine`，而繪圖實際吃的是 `closed_loop.bands[]`，後者無捨入落差。
- **地雷 #15 專項**：超差頻段標紅的 measured bar 根數 == JSON `within_tolerance=False`
  個數，五個輸出全數相符（1/1、4/4、1/1、2/2、1/1），沒有「並排呈現卻藏掉超差」；
  `notes` 未混進紅字區塊（程式檢出）。
- **「無假實作」決定性測試**：`bathroom_tiled` 加 `--override-material floor=carpet
  --override-material walls=wood_panel`，CLIP 重跑結果是 `generic_wall`/`gypsum_board`，
  PNG 卻正確顯示覆寫後的「地毯 α=0.37」「木板 α=0.09」——證實文字標籤走
  `analysis['surfaces']`，不是那次為了畫圖重跑的分割結果。環景 SteinmanHall 的 wall
  標籤顯示 `north` 的 gypsum_board（非 `west` 的 curtain_fabric），視角對應正確。
- **MD5 零回歸獨立複驗**：`stairwell_tiled` 預設 vs `--no-viz`，`ir_mono.wav`
  `7953acc1…`、`ir_stereo.wav` `ac058b49…` **兩條**皆逐位元相同（Sonnet 只驗了 mono）。
  範圍：`git diff 4ca2ed5..70c709c` 對 SPEC/ROADMAP/WORKFLOW/`data/`/`assets/`
  與 T-10~T-14、T-20、T-21 的 8 個模組全部為空。
- **附 4 項非阻斷建議**給 T-17／未來收斂：① `_photo_pixel_panels()` 的
  `wall_face = "west"` hardcode——實測 `--override-material east=marble` 時 PNG 仍顯示
  west 的材質，被覆寫的面圖上看不到（非數字錯，是單面覆寫時資訊不完整）；
  ② `_maybe_visualize()` 沒 try/except，畫圖若失敗會在音訊已產出後吐 traceback；
  ③ RT60 圖標題在並排 measured 時仍寫「（Sabine 目標）」；④ 文字拼版大片留白＋
  「六面材質表」標題與內文首行重複。
- 下一步：T-18（驗收前置，可提前插）→ T-17。

## 2026-08-30 (39)

- 🔵 **T-16 分析視覺化完成（Sonnet 自檢通過，待 Opus 驗證）**：新增
  `src/image_reverb/visualize.py`，三種輸入各自的拼版 `analysis.png`（照片：
  原圖／表面分割疊色圖／深度圖／六頻段 RT60／尺寸體積 pre-delay confidence
  文字欄／警示紅字；文字：preset＋全部假設值／六面材質表／RT60／警示；
  複合場景：逐空間 RT60 摘要／路徑列表／警示），預設產生、`--no-viz` 可關。
  `pipeline.py`/`cli.py` 只加路由層（三個 `run_*()` 各加 `no_viz` 參數＋
  `_maybe_visualize()`），**沒有動任何既有數值路徑一行**。
- **PNG 上的數字全部直接讀 `analysis.json`（RT60 用 `closed_loop.bands[]`，
  target/measured/within_tolerance 同一筆，不會兩邊對不上）**，唯一重跑模型
  的地方是分割疊色圖／深度圖的像素資料（`analysis.json` 不存 labelmap／深度
  陣列，做法與既有 `scene_cues` 重跑 `segment_roles()` 同模式）；材質文字標籤
  仍是查 `analysis['surfaces']`，不是從這次重跑的分割結果反推。
- **自我檢查全過**：9 張照片＋2 個文字場景＋2 個複合場景共 13 次全 `exit 0`
  且都產出 `analysis.png`；另外用非測試集環景照（SteinmanHall）驗證環景分支
  （主視角＋「已展開 6 視角」字樣、wall 標籤正確對到 `north` 面）。RT60 數值
  逐值比對（程式比對非目測）：photo/text 11 個輸出誤差 <1e-6，scene 5 個房間
  誤差 <0.001（純屬 `coupled.py` 既有三位/四位小數四捨五入差異，非本卡引入）。
  MD5 零回歸：`stairwell_tiled` 同輸入 with/without `--no-viz` 的 `ir_mono.wav`
  逐位元相同；`test_ir_synth.py`（23 項）/`test_scene_text.py`/`test_coupled.py`/
  `test_preprocess.py` 全過。`git status --short` 只有 3 個檔案變動。
- 過程中確認一個**既有、非本卡引入**的行為：`output/<name>/` 同名覆寫不會清掉
  上次殘留檔案（T-15 Opus 非阻斷建議②同一個坑），先跑預設模式再對同目錄跑
  `--no-viz` 會看到舊的 `analysis.png` 還在——不是 `--no-viz` 沒生效。
- 下一步：Opus 驗證 T-16；通過後依序 T-18（可提前插）→ T-17。

## 2026-08-30 (38)

- ✅ **T-15 Opus 驗證通過**（乾淨 shell 重跑，不是讀 Sonnet 的宣稱）。三面紅旗逐一查過：
  (1) 沒有為了統一 schema 動到引擎數值路徑——**MD5 六條零回歸全中**（T-14 ×2、
  T-20 ×2、T-21 ×2），且新 CLI 對同一輸入與獨立腳本產物**逐位元相同**（4/4）；
  驗證方式是先把 `output/` 既有產物整批移到暫存區當基準再全部重跑，避免拿舊檔對舊檔。
  (2) warnings/notes 分流沒有把真警示分錯欄——把 `geometry.py`/`scene_text.py`
  **所有會下修 confidence 的訊息**逐條對照白名單 `_NOTE_MARKERS`，無一命中，全部留在
  `warnings`（洞窟低信心 preset、clamp 比例、地板可見度、人群佔比、CLIP 域外、超量程）。
  (3) 互斥檢查不是只驗 happy path——兩兩組合、三種全給、一種都不給共 5 種全實測。
- 其他實測：9 張照片＋額外 JPG 全 `exit 0`（耗時 15–19s）；37 個輸出 WAV 全過
  `check_audio.py`（48kHz／`PCM_24`／非靜音／無爆音）；`ir_stereo` 左聲道與 `ir_mono`
  `np.array_equal` 為 True、右聲道不同、左右峰值相同；覆寫真的生效到 IR（同一張照片
  無覆寫／`--override-dims`／再加 `--override-material` 三個不同 MD5）；11 種壞輸入
  全部清楚中文錯誤到 stderr＋`exit 2`；5 支測試腳本全過。
- **Opus 非阻斷建議 4 項（留給 T-16/T-17，已寫進 T-15 卡）**：① `--override-material`
  之後舊的 CLIP fallback 警示沒被移除（與 T-20 建議②同型，本卡只修了 scene_text 那半）；
  ② `output/<檔名>/` 同名會安靜覆寫，前後對照需區分目錄；③ `analysis.json` schema
  尚未真正統一（`surfaces_sources`/`override_*` 只有照片路徑有），T-16 讀 JSON 前宜補齊；
  ④ `_run_wet_preview()` 用 `check=True` 但沒接 `CalledProcessError`（目前不可達）。
- 據實更正交接筆記一處：兩張 CGI 洞窟只有 `cgi_cavern_crowd_sophy` 是 `confidence: low`，
  `cgi_cave_lab_sophy` 實測是 `medium`。
- 下一步：T-16 → T-18（可提前插）→ T-17。

## 2026-08-30 (37)

- 🔵 **T-15 CLI 整合完成（Sonnet 自檢通過，待 Opus 驗證）**：`python -m src.image_reverb`
  改成三種輸入（`<photo>`／`--text`／`--scene`）互斥的統一入口，輸出到
  `output/<name>/`：`ir_mono.wav`＋`ir_stereo.wav`（簡單 decorrelation；複合場景
  v1 只出 mono）＋`analysis.json`（統一 schema，warnings/notes 已分流）＋
  `wet_preview.wav`。新增 `src/image_reverb/pipeline.py` 當路由層，**三條管線的
  核心邏輯（T-10~T-14、`scene_text.py`、`coupled.py`）完全沒重寫**，只是呼叫既有
  函式後統一輸出格式。
- **MD5 零回歸逐一實測通過**：T-14 兩條（`test_ir_synth.py`【6】）、T-20 兩條
  （`text_bathroom`/`text_church`）、T-21 兩條（`neighbor_voices`/
  `stadium_corridor`）全部逐位元不變；新 CLI 與既有獨立腳本同輸入也逐位元相同
  → 依卡片判準本卡免試聽關卡。
- 併收三項技術債：#1（`gen_ir_manual.py` 重複的 per-wall 材質建構函式收斂進
  `ir_synth.build_pra_materials()`）、#2（warnings/notes 分流，`neighbor_voices`
  實測「preset 'bedroom'」進 notes、+114.4% 誤差留 warnings）、#5（T-13 入口零/
  負尺寸硬擋、`geometry.apply_scope_confidence()` 補上「不認得的 dims_source
  預設降 low」而不是預設放行）。另落地 T-20 Opus 三條非阻斷建議（cabin/cabinet
  詞邊界比對、顯式尺寸覆寫移除失效 note、錯誤訊息改印 stderr）。
- 9 張測試照片全數跑通不 crash（車內/CGI 洞窟正確降 `confidence: low` 並帶
  可操作警示）；`--override-dims`/新增的 `--override-material` 都驗證生效。
- ⚠️ **過程中發現、非本卡引入**：`gen_ir_manual.py --materials` 這條路徑因為用了
  pyroomacoustics 的 ray tracing（內部亂數沒固定種子），本來就不是 run-to-run
  bit-identical，與本卡收斂材質建構函式無關（純數值上驗證過等價）。
- ⚠️ **移除了 `--geometry`/`--materials-detect` 舊除錯旗標**（bare `<photo>` 現在
  直接跑完整管線）——HANDOFF.md §5 指令速查那行已過期，待下個 Fable 視窗更新。
- 下一步：Opus 驗證 T-15；通過後依序 T-16 → T-18（可提前插）→ T-17。

## 2026-08-30 (36)

- 🔮 **Fable 規劃視窗：HANDOFF 第 0 節 A~F 六項全數裁決完畢，Phase 1 尾段卡片改版。**
- **A（T-15 改版）**：三種輸入（照片/`--text`/`--scene`）互斥已落實進「產出/執行步驟/
  自我檢查」三欄，不再只是卡片下方補註；併入技術債 #1（材質 dict 重複實作收斂）、
  #2（warnings/notes 分流）、#5（零/負尺寸與量程規則預設放行防呆）與 T-20 Opus
  三條非阻斷建議；新增「交付 IR MD5 零回歸」硬判準（T-22 手法）——MD5 全不變則
  本卡免試聽關卡。
- **B（§7-2 低頻判準，最重要）**：**事前裁決**——500Hz–4kHz 逐頻段 <20% 不變；
  125/250Hz 門檻改為「88–354Hz 低頻聯合帶 T30 誤差 <20%」，逐頻段數字照列、
  超差照警示，只是不當門檻。理由：低頻八度帶 T30 已三次實測證實不可信
  （地雷 #14 +115%、T-14 裁決成分單獨 0.411s≈目標但八度量測 +105%、T-21 複驗
  +27.5%~+158.6%），機制是 177Hz 共享邊緣的鄰帶耦合；聯合帶把該邊緣內部化。
  **數字不放寬（維持 20%），換掉的是不可信的量測對象**。殘留風險（354Hz 上緣）
  已誠實寫進卡片供 Opus 對抗檢查。證據鏈全文見 TASKS.md T-17 卡裁決 B。
- **C（尺度落差呈現）**：T-17 達標率依 `dims_source` 分兩組統計（metric_depth vs
  manual），不得合併——自動路徑才是 F-01 產品主張。Metric-Indoor-Large 維持延後，
  分組統計就是它的決策輸入。
- **D（技術債）**：#1/#2/#5 併入 T-15；#4（退出碼）與新的聯合帶量測工具開新卡
  **T-18（驗收前置，不依賴 T-15/T-16，T-17 前必過）**；#3（匹配窗門檻 3dB 薄餘裕）
  裁決維持文件化不動碼——無失效案例支撐的門檻調整是投機。
- **E（等使用者）**：照片來源網址列為 **T-17 結案前置**（量測可先跑，結案前必補）；
  乾聲/小房間環景/T-07 不擋。
- **F（ROADMAP）**：Phase 1 的 T-10~T-14 與 Phase 1.5 全節勾選補齊、過期註記清除、
  新增 T-22 一行與 T-18 一行。
- **下一步：開 Sonnet 視窗執行 T-15**（標準 Prompt 見 WORKFLOW §2.1）。T-18 可在
  T-15/T-16 之間任何時點插入，T-17 前必須通過驗證。

## 2026-08-28 (35)

- ✅ **Opus 複驗 T-21 通過**（新開視窗，不是修正輪那個上下文自己審自己）。
- **關鍵驗證手法：v3 對照組由 Opus 自己重建**——把 repo clone 出去 checkout 到
  `0d7bae6`（T-22 之前的引擎）重生兩個示範場景，得到的 v3 MD5 與卡片表格逐項吻合，
  且該版 JSON 的巨蛋 2k/4k 量測就是 0.173/0.184s（−94%/−93%）、warnings 全空——
  **退回理由 1、3 的缺陷原貌獨立重現**，卡片自述不是編的。
- v4 同一空間收斂到 2.575s（−13.2%）／2.224s（−17.0%），六頻段全在 ±20% 內。
- 乾淨 clone 重跑 4 個交付檔 MD5 全部相同；`test_coupled.py` 17 項、
  `test_ir_synth.py` 23 項全過；容差 0.20 未放寬、`ir_metrics.py` 一個字沒動。
- 已知混頻偏差（走廊 +158.6% 等）確認在 v3 就存在且靜默，現在浮出來是誠實回報。
- 非阻斷觀察：JSON `warnings` 仍把解析 note 與真警示混在同一欄，建議 T-15 時拆兩欄。
- **下一步：Phase 1.5 全數完成（T-20/T-21/T-22 皆 ✅），回頭接 Phase 1 的 T-15/T-16/T-17。
  建議開 Fable 視窗重新規劃接續順序。**

## 2026-08-28 (34)

- 🎧 **使用者第四輪重聽 v4：「聽起來沒問題」→ T-21 狀態改 🔵 待驗證。**
- 這輪重聽不是形式：v3 的「確認OK」是對**巨蛋高頻晚期殘響幾乎不存在**的那條 IR 給的，
  修好後頻譜確實變了（4kHz 感知傾斜 −32.6 → −27.6dB、複合 IR 4kHz T30 1.325 → 2.252s），
  舊結論不能沿用。使用者對改變後的聲音重新確認，v3 的聽感結論才正式被取代。
- T-21 的人耳驗收至此共四輪（v1 退回 → v2 退回 → v3 OK → 修引擎後 v4 OK），
  是 SPEC §7-4 流程目前最完整的案例。
- **下一步：開新 Opus 視窗複驗 T-21**（T-22 已 ✅）。複驗要換視窗——本輪修正是由
  驗證 T-22 的那個 Opus 視窗接手做的，別讓同一個上下文自己審自己。

## 2026-08-28 (33)

- 🔧 **T-21 修正輪程式與文件完成，狀態 🟡 進行中——卡在「請使用者重聽 v4」這一步。**
- **修正清單第 1 項（閉環比對警示）已完成，但實作位置與卡片字面不同**：卡片寫在
  `export_coupled()`，實際上該函式手上只有加總後的複合 IR 與已四捨五入的摘要數字，
  拿不到任何單一空間自己的 IR，無法「直接複用 `closed_loop_report()`」。改放在
  `synthesize_coupled()` 的 `build_room_ir()`（唯一同時握有空間 IR 與目標 RT60 的地方），
  報告存進 `rooms[].closed_loop`，超差訊息加 `[空間角色／名稱]` 前綴進 warnings。
  **保證比卡片字面更強**：JSON 與 CLI 兩邊都出現，且不經 export 直接用函式庫的
  下游（T-15/T-17）也不會再安靜。容差 0.20，與 T-14 `export_ir()` 同值。
- **已知混頻偏差照樣浮出來（誠實回報，不是修掉）**：臥室 125Hz +27.5%/+34.8%、
  家用小走廊 +114.4%/+51.7%、巨蛋場景的聽者走廊 +158.6%/+37.0%（這條在 v3 也存在、
  也一樣靜默，修正後才浮出來）。判準維持 ±20% 未放寬。
- **v4 重生，MD5 差異來源完全可解釋**：`neighbor_voices` 的 IR 與試聽檔 MD5
  **與 v3 完全相同**（三個空間都在安全尺度、走 T-22 max 左支）；`stadium_corridor`
  兩個檔 MD5 改變——聲源空間正是 160×130×45 的巨蛋，**這個差異就是本次修正的目的**。
- **巨蛋 −94% 消失**：聲源空間 2kHz 0.173→**2.575s**、4kHz 0.184→**2.224s**，
  `closed_loop.all_within_tolerance: true`。複合 IR 125Hz T30 5.07→**5.05s**
  （尾巴沒有退回 12.9s 級），高頻 2k 2.045→2.657s、4k 1.325→2.252s。
  感知傾斜 4kHz 由 −32.6 變 **−27.6dB**（仍然很悶，亮了約 5dB＝高頻晚期殘響回來了）。
- 測試：`test_coupled.py` 既有 14 項全過、判準未放寬，新增【5b】3 項；
  `test_ir_synth.py` 23 項維持全過。
- 順手做掉 Opus 驗證 T-22 留下的 5 條非阻斷文件建議（docstring 說法統一、
  `export_ir()` 誤植更正、測項計數 10+13=23、防禦門檻 3dB 薄餘裕寫進 config 註解、
  合成耗時補記）。
- **下一步：請使用者重聽 `output/listen_coupled_stadium_corridor.wav` 與
  `output/listen_coupled_neighbor_voices.wav`** → 確認後改 🔵 待驗證 → Opus 複驗 T-21。

## 2026-08-28 (32)

- ✅ **Opus 驗證 T-22 通過**（T-14 引擎尺度自適應）。完整逐項紀錄寫進 TASKS.md
  T-22 卡「✅ Opus 驗證紀錄」。
- **核心判斷點裁定**：Sonnet 自標的偏離點——早期窗用「絕對到達時間」而非「比直達音
  晚多久」的差值——**成立、不算偏離**。卡片背景欄自己寫的「巨蛋要 262ms」就是絕對
  尺度的數字（實測直達 266.0ms、絕對一階反射 290.6ms、差值僅 24.6ms）；照差值讀，
  卡片「房間大到最短一階反射比 90ms 還晚到」的立卡前提會自相矛盾。
- **關鍵：兩項硬判準都由 Opus 獨立複現，不是採信 Sonnet 的自填數字**。用
  `git worktree` 拉出修正前 commit 的引擎重算，兩條 T-14 交付 IR 的陣列 MD5 與
  測試檔寫死的常數完全相同（證明常數非事後回填）；同一支修正前引擎也重現了
  −74.9%／−94.2% 崩壞，修正後**六個頻段全部**收斂（最差 1kHz −21.5%）。
- 另獨立驗證：早期窗與自寫的鏡像法暴力解在 13 組任意尺寸上小數位全等（確為幾何
  推導、連續、無特例分支）；防禦警示只在兩個歷史崩壞案例觸發、四個健康尺寸靜默
  （有鑑別力）；`ir_metrics.py` 自 T-14 起零改動、既有判準一條未放寬；
  巨蛋交接前後 RMS 跳變僅 +0.38dB、晚期 crest 11.8dB；T-20/T-21 等旁支測試無附帶損傷。
- 留下 5 條非阻斷文件修正建議（docstring 說法不一致、`export_ir()` 誤植、
  測項計數 10+13=23 而非 11+11、防禦門檻餘裕僅 3dB 應記為已知限制、補記合成耗時
  0.35s／階數 6），併入 T-21 修正輪順手改即可。
- 下一步：**T-21 修正輪**（`export_coupled()` 補閉環警示、更正交接筆記錯誤斷言、
  用修正後引擎重生 v4 試聽檔）→ 使用者重聽 v4 → Opus 複驗 T-21。

## 2026-08-28 (31)

- ✅ **Sonnet 完成 T-22（T-14 引擎尺度自適應），狀態 🔵 待驗證。**
  `config.IR_EARLY_MS` 改名為下限值 `IR_EARLY_MIN_MS`（仍 90ms）；早期窗長改在
  `ir_synth.simulate_early_ir()` 執行期依幾何動態計算：
  `max(IR_EARLY_MIN_MS, 最短一階反射到達時間 + IR_ENERGY_MATCH_MS)`
  （鏡像法對六面各算一條一階反射路徑長取最短，非查表/hardcode）。
- **關鍵設計決定：用「絕對到達時間」而非「比直達音晚多久」的差值**。
  一開始用差值做（160×130×45 只差 24.6ms），窗長仍卡在 90ms 下限、−94% 沒解——
  問題根因不只是「窗不夠晚才開始」，是大房間反射本來就稀疏（離散回聲串），
  固定 90ms 換算出的窗剛好落在兩簇回聲之間的空隙（實測 40–70ms 窗 broadband
  RMS 只有 2–6e-6，比 20–40ms 那簇反射低 40 倍以上）。改用絕對到達時間會把
  窗大幅後推、同時讓 `_required_max_order()` 算出更高階數涵蓋更多累積反射，
  匹配窗因此量到有代表性的位準——這才是真正解掉 −94% 的機制，不是單純的
  時間平移。
- **新增縱深防禦**：`config.IR_MATCH_WINDOW_RMS_FLOOR_DB`（−60dB）——合成時量
  能量匹配窗 broadband RMS 相對直達音峰值，低於門檻就輸出明確警示「能量匹配窗
  內幾乎無反射能量，晚期殘響位準不可信」。人工把窗強制退回固定 90ms 重跑巨蛋
  尺寸，警示真的會觸發（測試【8】）。
- **零回歸（硬證據）**：4×3×2.5（地毯房）與 30×20×12（hall）——T-14 交付版的
  兩條示範 IR——`synthesize_ir()` 回傳陣列 MD5 與修正前 bit-identical
  （`f3a763be...` / `f24353b5...`），且與 `output/ir_synth/T14_*.wav` 檔案 MD5
  交叉核對一致。兩者的「反射到達時間 + 30ms」都 < 90ms，走 max() 左支。
- **尺度掃描收斂**（同材質＝巨蛋 `audience_seating` 六面＋`generic_wall` 天花板，
  只變尺寸，2k/4k 對 Sabine 目標誤差）：40×30×15 +0.5%、80×60×25 −9.4%、
  120×100×35 −12.3%、160×130×45 −17.5%（修正前 −94%）、
  200×160×55（=T-20 `stadium_dome` preset 尺寸）−18.4%——全部 ≤25% 目標內，
  無一觸發能量匹配窗警示。`python scripts/gen_ir_from_text.py "巨蛋"` 閉環 JSON
  六頻段 `all_within_tolerance: true`，高頻晚期殘響不再消失。
- `scripts/test_ir_synth.py` 既有項目全過、判準未放寬；新增【6】零回歸、
  【7】尺度掃描（10 項）、【8】防禦性警示觸發。
  （計數更正 2026-08-28：既有 **10 項**＋新增 **13 項**＝**23 項**全過；
  本筆原寫的「既有 11 項…全部 21 項」是誤植，判準未增未減。）
- 更新 T-14 卡「⚠️ 後續發現的適用尺度上限」附註：改為「已由 T-22 修正，驗證尺度
  至 200m 級」＋修正前後對比表。
- 下一步：**Opus 驗證 T-22** → 通過後接 T-21 修正輪（`export_coupled()` 補閉環
  警示、更正交接筆記錯誤斷言、重生 v4 試聽檔）→ 使用者重聽 v4 → Opus 複驗 T-21。

## 2026-08-28 (30)

- 🔮 **Fable 裁決 T-21 修正清單第 2 項：選 (a) 修 T-14 引擎，開新卡 T-22
  （早期窗／能量匹配窗尺度自適應）；示範場景維持真實巨蛋尺寸 160×130×45。**
  決定性理由：(1) 巨蛋→通道是 F-17 的原始需求場景，選 (b) 等於把招牌案例做成假的；
  (2) **缺陷不侷限 T-21**——T-20 已通過驗證的 preset 庫裡 `stadium_dome` 是
  200×160×55，比示範場景更深入失效區，(b) 得連它一起縮水或留著已知會壞的 preset；
  (3) T-17 §7-2 對照場地含 ~150m 級場館，引擎在驗收時遲早面對這個尺度；
  (4) (b) 仍須實作警示機制才能消除靜默錯誤（文件擋不住 T-15 之後的
  `--override-dims`），近半工作量卻什麼都沒修好；(5) 修法局部——早期窗改
  `max(90ms, 最短一階反射到達＋匹配窗長)`，小/中房間走 max 左支行為完全不變，
  可用「交付 IR bit-identical」硬性驗證零回歸。
- **T-22 卡已寫入 TASKS.md**：尺度自適應窗（幾何解析、非查表）＋防禦性
  「匹配窗無能量」警示（縱深防禦，−60dB 門檻進 config）＋尺度掃描迴歸
  （40→200m 五級，含 stadium_dome 尺寸，2k/4k 誤差 ≤25%）；
  既有 11 項迴歸判準不得放寬、小/中房 IR bit-identical 為 Opus 紅旗。
- **T-21 修正輪安排**：修正清單第 1（export_coupled 補閉環警示）、3（更正
  「尺寸無關」錯誤斷言）項**不併入 T-22**——跨卡改檔違反範圍紀律（本卡 Opus 才對
  `e1cfa8f` 記過一筆），且兩項不依賴引擎改動；已寫成 T-21 卡的修正輪步驟，
  前置 T-22。執行順序：**T-22 → T-21 修正輪 → 重生 v4 試聽檔 →
  使用者一次重聽（兩卡合併一輪，避免聽兩次）→ Opus 依序複驗 T-22、T-21**。
  重聽是硬性關卡：使用者先前的 v3「確認OK」是對高頻晚期殘響缺失的 IR 給的，不能沿用。
- 補記本輪 Opus 驗證結果（2026-08-27~28 視窗，commit 98fcd5f／d9a18b2／67b05e8）：
  **T-14 ✅、T-20 ✅、T-21 🟠 退回**（巨蛋場景 2k/4k −94% 靜默錯誤）。
  驗證全文在各任務卡的「Opus 驗證紀錄」。
- 下一步：**Sonnet 執行 T-22**（TASKS.md 有完整卡片）。

## 2026-08-27 (29)

- 🎧 **T-21 第三輪試聽通過（v3，使用者「確認OK」）。** 三輪人耳迭代收斂：
  v1 退回（乾聲混入/場景平衡）→ v2 部分退回（巨蛋尾太長/低頻共振）→ v3 通過
  （滿場巨蛋 12.9→5.1s、eq_db 壓共振與加悶）。
- 現況：**T-14 / T-20 / T-21 三張卡的使用者試聽全部 ✅，全部 🔵 只剩 Opus 驗證。**
- 下一步：開 Opus 視窗依序驗證 **T-14 → T-20 → T-21**（先驗地基），
  全過後回 T-15（CLI 整合，含 `--text` / `--scene` 入口）。

## 2026-08-27 (28)

- 🎧 **第二輪試聽：T-20 兩檔「沒有問題」→ 試聽通過 ✅；T-21 兩檔部分退回 → v3。**
  回饋：巨蛋「尾巴拉太長——演唱會場內人很多會吸收回音」；隔壁「差不多，但音色可以
  再悶一些、低頻有一個共振的聲音可以減少」。
- **巨蛋滿場化（物理修正）**：空場 preset 四面裸混凝土 125Hz RT60 13.7s；場景改 inline
  「滿場」版（160×130×45、環繞看台＋地面全 audience_seating）→ 5.2s，合成 T30
  12.9→5.07s。
- **新增 path `eq_db` 調音參數**（coupled.py，誠實標注為場景調音非物理推導、寫進
  輸出 JSON 可追溯；迴歸+2 項共 14 項全過）。根因：石膏板 TL 低頻透射比中頻多 23dB
  → 125Hz 凸＝「共振聲」。隔間牆＋門路徑套 [-8,0,-2,-6,-10,-14]：最終頻譜相對 125Hz
  （扣頻寬基準）500 -9.1／1k -15.6／4k -25.9 dB，T30 0.59/1.01/0.61s。
  過程發現中頻近半能量來自門-走廊路徑——多路徑調音要看逐路徑頻段貢獻。
- 下一步：使用者第三輪試聽 coupled 兩檔（v3）→ Opus 依序驗證 T-14 → T-20 → T-21。

## 2026-08-27 (27)

- 🎧🔴 **T-21 第一輪使用者試聽退回（第四次「數字合理、耳朵抓到問題」），已修正重生 v2。**
  回饋：stadium_corridor「太亮、沒有被阻隔的聽感，穿水泥牆應幾乎只剩低頻」；
  neighbor_voices「像在鐵桶中而不是在隔壁，Reverb 應該蠻小」。
- 三個真因與修法：(1) **試聽檔混入 40% 乾聲**（--mix 0.6 從房間殘響照抄）——複合場景
  聽到的每一分聲音都穿過阻隔，**必須全濕 mix 1.0**（已改 gen_ir_coupled.py）；
  (2) 通道口洩漏路徑蓋過穿牆聲——混凝土 TL 在 125Hz 就 -36dB，任何近平坦的洩漏路徑
  都會贏，巨蛋場景改封閉走廊純穿牆單路徑；(3) 空間選錯——聲源房「空房間」(1.33s)
  改有家具臥室(0.56s)、中繼 20m 機構走廊(2.5s) 改 4m 家用小走廊 inline。
- 修正後量測：stadium 4kHz 相對 125Hz **-32.6dB**（感知基準修正後；修前 -10dB）；
  neighbor T30 **1.05/2.40/1.19 → 0.59/1.01/0.59s**。迴歸測試維持全過。
- 通則入 T-21 卡：複合場景 wet 預覽一律 mix=1.0；量悶亮要扣 +3dB/oct 頻寬基準；
  場景空間選「含家具」等效吸音版本。
- 下一步：使用者第二輪試聽 4 檔（coupled ×2 為 v2、text ×2 未回饋）→ Opus 依序驗證
  T-14 → T-20 → T-21。

## 2026-08-27 (26)

- 🔵 **T-20（文字場景→IR）與 T-21（複合場景引擎 v1）完成（Fable 執行），皆待 Opus 驗證
  ＋使用者試聽。** T-20：13 個 preset＋關鍵字/顯式參數解析（`scene_text.py`），
  迴歸 13 項全過；T-21：8 種構造 TL 表＋路徑串接引擎（`coupled.py`，支援 `tl_times`
  與 `via_room`），迴歸 12 項全過（牆 vs 開口高/低頻比差 20.7dB、線性疊加誤差 3.9e-16、
  延遲 50ms 實測 50.0ms、bit-identical）。
- **T-20 執行中修了一個 preset 物理錯誤**：浴室六面全磁磚 Sabine mid 算出 3.65s
  （真實 ~0.5-1s）——浴簾/毛巾/門才是主要吸音體，一面牆改 curtain_fabric 後 0.46s。
  原則入卡：preset 要把家具吸音近似進表面選擇。13 preset 的 RT60 掃描：
  浴室 0.46｜一般房間 1.33｜臥室 0.56｜客廳 0.64｜走廊 2.48｜樓梯間 4.85｜教室 0.49｜
  辦公室 0.41｜音樂廳 1.53｜教堂 8.06｜體育館 7.68｜巨蛋 7.78｜洞窟 7.36（mid, 秒）。
- **示範場景**（使用者兩個實際案例）：`stadium_corridor`（巨蛋演唱會→通道走廊，
  開口+穿牆兩路徑，IR 21s）、`neighbor_voices`（隔壁講話，隔間牆/窗-戶外-窗/
  門-走廊-門三路徑，IR 6.3s）。輸出 JSON 皆標 `method: path_cascade_v1`＋近似聲明。
- 待使用者試聽 4 個檔：`listen_text_bathroom`／`listen_text_church`／
  `listen_coupled_stadium_corridor`／`listen_coupled_neighbor_voices`。
- 下一步：使用者試聽 → Opus 驗證順序 **T-14 → T-20 → T-21**（T-20/T-21 建立在
  T-14 引擎上，先驗地基）。之後回 T-15（CLI 整合，含 `--text`/`--scene` 入口）。

## 2026-08-27 (25)

- 🔮 **Fable 規劃 Phase 1.5（使用者需求新增）：F-16 文字場景輸入、F-17 複合場景。**
  SPEC 升 v0.4（§3.3 新表＋§8 兩條風險）、ROADMAP 插入 Phase 1.5、TASKS 新增
  T-20/T-21 卡、T-15 卡補註（CLI 屆時收進 `--text` 與 `--scene` 入口）。
- 三個架構決策：(1) 文字場景 v1＝preset 庫＋關鍵字比對＋顯式參數抽取，**不接外部
  LLM API**（隱私原則；本機 LLM 留待 Phase 3）；認不得就報錯列清單，不安靜猜。
  (2) 複合場景 v1＝**路徑串接近似**（聲源空間 IR ⊗ 傳輸濾波 ⊗ 中繼 ⊗ 聽者空間 IR，
  多路徑加總）——遊戲音訊 portal 系統的成熟做法；輸出必標 `method: "path_cascade_v1"`
  ＋近似聲明，不包裝成精確模擬。(3) `data/transmission.json` 傳輸損失表比照
  materials.json 規格（六頻段＋出處＋信心）。
- 兩卡都不動照片管線與 T-14 引擎；排在 T-15 前，讓 CLI 一次統一三種輸入。
  ⚠️ 依賴鏈風險已標注：T-14 仍 🔵 待 Opus 驗證，若被退回則 T-20/T-21 需複測。
- 下一步：本視窗依使用者指示接續執行 T-20、T-21。

## 2026-08-27 (24)

- 🎧 **使用者試聽 T-14 三個檔案，回饋「目前聽起來 OK」**（small 地毯房無鐵筒子聲、
  hall 新引擎、hall T-01 對照無明顯劣化）。T-14 卡步驟 5 的必要通過條件達成，
  自我檢查全部 ✅。這是繼 T-02、T-12 之後第三次人耳確認。
- T-14 狀態維持 🔵 待驗證。**下一步：開 Opus 視窗驗證 T-14（Prompt 在 HANDOFF §7）。**

## 2026-08-27 (23)

- 🔵 **T-14 IR 合成引擎 v1 完成（Fable 依使用者指示直接執行），待 Opus 驗證＋使用者試聽。**
  新增 `src/image_reverb/ir_synth.py`（image-source 早期 + 六頻段 shaped-noise 晚期，
  逐表面材質、能量匹配 crossfade、固定 seed 可重現）、`ir_metrics.py`（獨立 T30 量測，
  不 import 合成端）、`scripts/test_ir_synth.py`（11 項閉環迴歸全過）、`gen_t14_listen.py`。
- 🔮 **執行中裁決：閉環驗收「對 Sabine 目標 <20%」物理上不可達，改兩層閉環。**
  實測地毯房 125Hz 量測 +105%，逐成分分解證明引擎沒錯（125 成分單獨量 0.411s≈目標
  0.348s），偏差是八度頻帶量測的混頻：250Hz 頻段（目標大 2.5 倍）與量測頻帶共享 177Hz
  邊緣、以 -8dB 耦合主導尾段；加陡濾波器（3→8 階）無效（截止點永遠 -3dB）。
  **pra 全模擬 ground truth 自己也 +115%**（T-12 實測 0.748s vs Sabine 0.348s）。
  改後：機制閉環（平坦目標）≤20% 全頻段（實測 ≤10.8%）＋實例閉環對 T-12 文件化
  物理錨點 0.748s ≤20%（實測 +1.1%）。T-17 驗收不受影響（量測 vs 量測本來就同類）。
  完整證據在 TASKS.md T-14 卡。
- 其他實作發現：pra RIR 開頭有 air absorption 濾波慢速漂移，直達音起點改幾何解析不用
  波形門檻；pra ray tracing 非決定性（125Hz T30 ±20%），不能拿單次隨機模擬當硬判準；
  大空間早期反射稀疏，能量匹配窗從 10ms 加到 30ms 才穩（hall 交接 -27.2→-26.3dB 平滑）。
- 試聽檔已產生：`listen_T14_small_carpet` / `listen_T14_hall` / `listen_T14_hall_T01baseline`
  （T-01 對照）。**下一步：使用者實聽 → 開 Opus 視窗驗證 T-14。**

## 2026-08-27 (22)

- 🔮 **Fable 確認 T-14 開工，任務卡依上游三卡實際產出調整（純文件，未動程式）。**
  三個定案：(1) 輸入介面＝T-13 的 `AcousticsResult` 單一物件（卡片原文的 `rt60_bands`
  欄位不存在，實際是 sabine/eyring 兩組並列）；(2) **晚期目標值用 `rt60_bands_sabine`**
  （進 `config.IR_RT60_BASIS` 可切換）——理由：專案全部迴歸錨點都是 Sabine 值，且地雷 #14
  實證 α 高時實測 IR 比 Sabine 更長，Eyring 更短只會把落差拉更大；(3) 聲源/麥克風位置
  沿用 `config.PREDELAY_*_POS_FRAC`，合成 IR 的直達音時間才與 T-13 的 predelay_ms 一致。
- 地雷 #14 的正面處理寫死在步驟 4：閉環量測 T30 與目標並列輸出 JSON
  （`rt60_bands_target`/`rt60_bands_measured`），對外殘響數字以量測值為準；並納入
  T-13 Opus 建議 2（T30 超出 0.1–12s 區間要警示）與 T-12 Opus 附註 2（`SURFACE_NAMES`
  加 assert）。新增 Opus 紅旗：不得為了閉環過關把量測窗調到只量晚期尾巴。
- 產出清單明確拆成 `ir_synth.py`（合成）與 `ir_metrics.py`（獨立量測）兩個模組，
  外加 `scripts/test_ir_synth.py` 閉環迴歸測試——量測與合成分離是卡上既有的 Opus 紅旗，
  拆檔讓這條界線在檔案層級就看得見。
- 下一步：執行 T-14（本視窗依使用者指示接續執行），完成後開 Opus 視窗驗證。

## 2026-08-27 (21)

- ✅ **T-11 Opus 驗證通過。Phase 1 前三卡（T-11/T-12/T-13）全部過驗證，T-14 可開工。**
- **決定性檢查是「把門檻改掉看規則會不會跟著變」**：光看 `grep` 沒有場地名只能算間接證據，
  所以在測試腳本裡把 `config.GEOMETRY_SCOPE_MAX_M` 改成 30.0 再餵同一組走廊估值
  （12.79/14.76/14.69）→ **confidence 變回 medium**；改 5.0 → 維持 low。
  若程式裡藏著「走廊→low」的 hardcode，門檻改 30 不可能翻回 medium。紅旗排除。
- **環景「單面牆距 vs 相加總長」也做了獨立對抗測試**（裁決理由 3 的實作是否到位）：
  餵四面各 9.9m（相加 19.8m）→ 維持 medium；單面 10.1m（相加僅 15.4m）→ 翻 low。
  確認規則看的是單面，偏心大廳不會安靜通過。
- **全部 10 個場地實際重跑，數字與 REPORT §8.2 逐位吻合**：浴室 3.721m（+24.0%）medium、
  走廊 12.785 low、車內 7.218 low（域外）、體育館 3.333 low（地板 0.0%）、
  Steinman low（觸發值 12.2/10.4/11.1m）；防濫殺對照組 4/4 全 medium。
  三個門檻查**全 git 歷史**每個 commit 都沒變過；補丁 diff 刪除行數 0（純新增）。
- ⚠️ **驗證時踩到一個陷阱，記下來給後續視窗**：REPORT §7 的重跑指令最後一條是
  `--override-dims`，它和 `--geometry` **寫同一個 `geometry.json` 路徑**，所以照著 §7
  跑完，浴室的佐證檔會停在 `manual`/`high`——初次讀檔一度看不到 +24%/medium 的證據。
  重跑即重現，不是造假，但建議 §7 調換順序或手動結果另存檔名（已記入 T-11 卡建議 1）。
- **四個不阻擋的建議記在 T-11 卡**：override 覆蓋 JSON（同上）；量程規則是「預設放行」——
  實測 `dims_source="metric_depth_v2"` 的 50×50×50m 會**靜默維持 medium**，目前無實際
  缺口但將來新增來源會踩本專案吃過三次虧的靜默失效；docstring 未寫明 manual 豁免；
  環景仍無「範圍內維持 medium」的對照素材。
- 現況：**T-10 ✅／T-11 ✅／T-12 ✅／T-13 ✅**。下一步：回 Fable 視窗確認 **T-14（IR 合成引擎）** 開工。

## 2026-08-27 (20)

- ✅ **T-13 Opus 驗證通過。** 三項決定性檢查：(1) **約束 B 做數值對抗**——算出 HANDOFF
  地雷 #8 點名的禁忌值（全 carpet 平均 α=0.30667 → 寬頻 0.2669s），掃過輸出全部 16 個
  數值欄位無一接近；`grep` 除 `mean` 外另掃 `np.mean`/`statistics`/`sum()/len()`，
  全檔唯一的除以 len 在 `rt60_mid()`，平均的是 RT60 結果值而非 α（卡上明文允許）。
- (2) **空氣吸收開/關比較（卡上指定、Sonnet 自檢未涵蓋，驗證者補測）**：自寫關閉對照組重算，
  大空間 30×20×12 的 4kHz **5.367→3.470s（−35.3%）**、125Hz 僅 −0.4%；小房間 4kHz 僅 −8.5%。
  大空間>小空間、高頻>低頻，兩個方向都與物理一致。附帶發現該大空間 1kHz 關掉是 12.075s
  （超出合理區間）、開啟後 9.288s——空氣吸收項是把大空間拉回合理範圍的關鍵。
- (3) **獨立手算逐位比對**：驗證者不看被驗程式自行推 Sabine/Eyring 公式手算 floor=carpet 組，
  **12 個數字與模組輸出小數第 5 位完全一致**。過程中 `marble 4×3×2.5` 與 `carpet 8×6×5`
  的 125Hz 都是 8.023s，形似快取——追查確認是巧合（marble α 恰為 carpet 一半、尺寸恰為
  2 倍放大，分子分母同步放大 8 倍），其餘五頻段數字全不同，快取與 hardcode 均排除。
- 反造假：`config.py` 純新增，**T-11 保護的 `GEOMETRY_ERROR_TOLERANCE`(0.30) 與
  `CLIP_CONFIDENCE_THRESHOLD`(0.4) 一字未動**；未動 `cli.py`／`geometry.py`，無跨任務污染。
- 四個不阻擋的建議記在 T-13 卡：零/負尺寸會安靜回傳 rt60 全 0 且 confidence 仍 high
  （上游目前擋得住，屬潛在缺口，但正是本專案吃過三次虧的「安靜的合理錯誤」型態，建議 T-15 補防呆）；
  模組不自我檢查 RT60 合理區間；面積計算與 `gen_ir_manual.py` 邏輯重複有分歧風險；
  `dims_source` 實際值與卡上文字不同但**判斷正確**（上游透傳不重新命名）。
- 現況：**T-13 ✅、T-11 🔵 待驗證**。下一步：T-11 開 Opus 視窗驗證，過後回 Fable 確認 T-14 開工。
- ⚠️ **並行視窗提交衝突（第二次，記錄備查）**：本輪寫進 TASKS.md 的 T-13 驗證結果，
  被同時作業的 Fable 視窗以 `git add`/`commit -a` 掃進 `bca6b61`（docs: T-11 Fable 裁決）。
  **內容正確且已在版控裡，只是歸在錯的 commit 訊息底下**；未改寫歷史（會干擾另一個視窗）。
  T-12 驗證時已發生過一次（`fc688cd` 混兩張卡）。**建議並行開視窗時，提交一律指名檔案
  （`git add <明確檔名>`），不要用 `git add -A`／`git commit -a`。**

## 2026-08-27 (19)

- 🔮 **Fable 裁決 T-11 Steinman 卡關：接受 (a)，Steinman 翻 low 是規則該有的行為。**
  量程實證逐視角適用（每個環景視角就是餵給同一模型的透視圖），單面牆距 12.2m 無法與
  「被壓縮的 30m」區分；維持 medium 等於在無 ground truth 下宣稱它可信。
- **規則一個字不改，修的是對照組驗收語句**：原句「單面牆距未超標」是總長÷2 的粗估，
  與 2026-08-18 就存在的六視角實測數據（12.2/10.4/5.25/11.1m，三面超標）矛盾。
  拒絕改配對軸長（偏心大廳會安靜通過＝設計性引入第四次「安靜的合理錯誤」）、
  拒絕環景另訂門檻（無實證、為過而發明）。防濫殺對照組改為
  浴室＋樓梯間＋AI 臥室＋洞穴實驗室（複測全部 medium ✅）。
- 明確化產品語義：**環景解「視野外」、不解「量程」**；環景超標場地 T-17 驗收同走
  手動尺寸。SPEC 升 v0.3.1（§7-2 措辭涵蓋環景超標場地）。新增待使用者事項：
  補一張小房間 360 照片當環景防濫殺對照（否則留待 T-17 間接檢驗）。
- 依裁決後判準補丁自檢全數通過 → **T-11 改 🔵 待 Opus 驗證**；T-13 也已 🔵 待驗證
  （並行視窗，da394ab）。下一步：兩卡各開 Opus 視窗驗證，都過後回 Fable 確認 T-14 開工。
  本裁決為純文件更新，未動程式碼。

## 2026-08-26 (18)

- 🔵 **T-13 聲學參數計算完成（Sonnet），待 Opus 驗證。** 新增 `src/image_reverb/acoustics.py`：
  吃 T-11 的 `RoomEstimate` ＋ T-12 的 `SurfaceMaterials` → 逐頻段 Sabine/Eyring RT60、
  pre-delay。約束 B（逐頻段獨立算，禁止平均 α）落地：`grep -n "mean"` 零命中；
  地雷第 14 條落地：`rt60_source: "formula"` ＋ `rt60_disclaimer` 明講公式值不等於實測。
- 空氣吸收（Sabine 4mV 修正）直接查 `pyroomacoustics.Physics` 內建表（20°C/50%RH），
  與 T-01/T-14 模擬用同一份資料源，避免公式與模擬互相矛盾。
- 新增 `scripts/test_acoustics.py` 純公式回歸測試：task 卡步驟 5a/5b 六個數字全部
  ±10% 內通過（125/1k/4kHz，全 carpet 與 floor=carpet+石膏板兩組）；Eyring 高 α 較短、
  低 α 趨近 Sabine；換房間尺寸數字會變（非 hardcode）。未動 `cli.py`（CLI 整合是 T-15）。
- 下一步：Opus 驗證 T-13。T-11 決策補丁仍卡在步驟 9（Steinman 對照組），與本卡無關、
  可獨立驗證。

## 2026-08-26 (17)

- 🔴 **T-11 決策補丁執行（Sonnet）——步驟 7–8 完成，步驟 9 自檢卡關。**
  `config.py` 加 `GEOMETRY_SCOPE_MAX_M = 10.0`；`geometry.py` 加
  `apply_scope_confidence()`（透視照任一維、環景單面牆距 >10m → confidence 降 low），
  與既有三條場景線索規則並存取最嚴。`GEOMETRY_ERROR_TOLERANCE`／`CLIP_CONFIDENCE_THRESHOLD`
  未動。重跑全部 9 張照片＋Steinman：**A' 通過（浴室 +24%）、B' 通過（走廊/車內/體育館
  全部翻/維持 low，走廊靠量程規則非 hardcode）**。
- ⚠️ **對照組防濫殺卡關**：浴室維持 medium ✅，但 **Steinman 翻成 low**（決策文字寫
  「單面牆距未超標」用的是總長÷2 粗估，實際六視角原始牆距 12.2/10.4/5.25/11.1m，
  三個超過 10m，相機明顯偏心）。未調整規則讓它通過——如實記錄。細節在
  `output/geometry/REPORT.md` §8.4、TASKS.md T-11 卡交接筆記。
- 下一步：待 Fable 決定 (a) 接受 Steinman low 或 (b) 調整環景量程判定基準，
  才能把 T-11 狀態改回 🔵 待 Opus 驗證。T-13（可並行）不受影響。

## 2026-08-25 (16)

- 🔮 **Fable 定案 T-11 路線：b 為主幹＋c 為正式出口＋d 保留；a 延後；e 拒絕。**
  自動幾何適用範圍明訂「一般室內、估計最大尺寸 ≤ 10m」；範圍外不是失敗而是正式行為分支
  （`confidence: low` ＋可操作警示，出口＝手動尺寸 F-09 或環景輸入）。
- **10m 的理由**：模型量程天花板實證 ~20m，且天花板前就開始壓縮（走廊 30m→估 12.8m），
  估值 >10m 無法區分「真的 10–20m」與「被壓縮的 30m+」；±30% 判準只在 3m 級有 ground truth。
  取天花板一半，進 `config.GEOMETRY_SCOPE_MAX_M` 可調。環景規則獨立（單面牆距 >10m 才降 low，
  因對牆相加上限 ~40m）。
- **a（換 Large 模型）現在不做**：需授權 1.3GB、天花板由訓練資料決定、即使摸到 30m 也到不了
  150m，投資報酬不明——延後至 T-17 驗收後再評估。**e（放寬判準）拒絕**：
  `GEOMETRY_ERROR_TOLERANCE` 維持 0.30，本決策改適用域不改門檻，且代價是顯性警示＋手動出口。
- 文件更新：SPEC v0.3（F-02 適用範圍、§7-2 範圍外場地用手動尺寸驗收、§8 風險表）、
  ROADMAP T-11 條目、TASKS.md T-11 卡（決策全文＋補丁步驟 7–9，狀態 🔴→🟡）、
  T-13 卡（解除封鎖、schema 加 `dims_source`、地雷 #14 入卡為步驟 4b）。
- 下一步：**Sonnet 執行 T-11 決策補丁（步驟 7–9）**，與 **T-13 可並行**（不動同檔案）。
  補丁重點：走廊必須靠量程規則翻成 low（不得 hardcode 場地名）、浴室與 Steinman 不得被濫殺。

## 2026-08-25 (15)

- ✅ **T-12 Opus 驗證通過。** 決定性檢查：(1) 直接讀 `pra.ShoeBox` 房間物件內部，
  六面牆各自持有正確 α（floor 0.02 vs 牆 0.29 @125Hz），per-wall 不是只有 print；
  (2) Opus 獨立實作頻段 T30 量測，全 carpet 低/高頻比 **49.0 倍** vs 逐表面 **1.1 倍**，
  鐵筒子頻譜特徵確實消失；(3) corridor carpet 信心 0.9632 重跑可重現，非 hardcode。
- 三個不阻擋附註記在 T-12 卡：fc688cd 混了兩張卡一個 commit（下不為例）；
  交接筆記「wall_names 實際取得」與程式不符（實為 hardcode tuple，已驗證一致無害）；
  步驟 6a 量測值 0.748s vs Sabine 0.35s 的落差**已明確交 T-13，不得再往後傳**。
- 現況：T-12 ✅。瓶頸仍是 **T-11 等 Fable 決策**（metric depth 量程問題）。

## 2026-08-18 (14)

- 🎧 **使用者試聽通過：「鐵筒子」缺陷正式結案。** 使用者實聽 `listen_T12_surf_carpet`
  （逐表面修復版）與 `listen_T12_uniform_carpet`（舊版）後回覆「沒問題」。
  T-12 卡步驟 6b 的必要通過條件達成，**自檢項目全數完成**，狀態 → 🔵 待 Opus 驗證。
- 這是本專案**第二次由人耳確認成果**（第一次是 T-02）。意義在於：
  2026-08-16 使用者對舊版 carpet 的評語是「感覺很像用手去拍鐵筒子出來的聲音」，
  當時那個錯誤**通過了 WORKFLOW §5 的全部三層數值檢查**，只有耳朵抓得到；
  這一輪的量化改善（125Hz T30 3.952s→0.748s、低/高頻比 48.8→1.27 倍）
  **與聽感一致** —— 約束 A（逐表面材質）的實證閉環完成。
- 下一步：開 **Fable 視窗決策 T-11 路線**（HANDOFF §0 有可直接貼的 Prompt）。
  T-12 可另開 Opus 視窗驗證，兩者互不阻擋。

## 2026-08-18 (13)

- **T-12 材質模組完成待驗證；T-11 幾何模組完成但評測關卡 🔴 卡關。**
  使用者授權下載兩個模型（metric depth 99MB、CLIP 605MB），SegFormer 用本機既有快取。
- **T-12 的核心成果：「鐵筒子」缺陷確實修好。** 逐表面 floor=carpet＋石膏板牆：
  125Hz Sabine RT60 **0.348s**（全 carpet 是 4.093s，差 **11.8 倍**）；
  實測 IR 的 125Hz T30 由 **3.952s → 0.748s**，低頻/高頻比由 **48.8 倍 → 1.27 倍**。
  試聽檔已產生並送出，**等使用者耳朵確認**（卡片明訂 AI 不能代勞）。
- **T-12 修正了 T-06 的地毯缺陷**：corridor 地板判成 `carpet` **信心 0.963**
  （T-06 只有 29.6% 判成 rug，換算 α 從 0.207 修正回 0.65）。兩階段分工有效。
- 🔴 **T-12 實作中發現卡片的信心 gating 規則不足**：只用「top-1 < 0.4」擋不住車內——
  車內 floor 判成 curtain_fabric **信心 0.760**、wall 判成 acoustic_panel 0.489，
  兩者都在門檻上，完全不觸發警示。根因：CLIP softmax 在封閉候選集上永遠加總為 1，
  **無法表達「以上皆非」**；調高門檻無效（要 0.8，會連判對的案例一起擋掉）。
  → 加入 4 個域外候選讓 softmax 有地方投「以上皆非」，車內改判 `__vehicle_interior` 0.735 ＋明確警示。
- 🔴 **T-11 評測關卡未通過（判準 A）**：走廊 **−57%**（估 12.79m vs ~30m）。
  浴室 +24% ✅ 在 ±30% 內；車內、體育館都正確標 `confidence: low` ✅（判準 B 通過）。
  **根因是模型量程**：9 張照片最大預測距離全部落在 3.6–19.7m，`Metric-Indoor-Small` 到不了 30m。
  體育館實際 ~150m，模型全圖最遠只說 **3.61m**（−98%）。
  已先排除「用錯模型/單位」：metric 與相對版輸出確實不同、浴室 p50=2.94m 對照實際合理。
- 🔴 **本輪最重要的教訓（第三次遇到同一類失敗）**：體育館錯 98%，但深度統計**完全正常**
  （clamp 比例 0、百分位平順、離上限很遠）——**只看深度輸出無法發現它錯了**。
  能發現的訊號在分割：地板可見度 0.0%（vs 浴室 6.8%）。已實作三條有實測依據的信心規則，
  其中「T-12 判定域外」是跨模組訊號，且**只有它抓得到車內**。已驗證不濫殺對照組。
- ⚠️ **交給 T-13 的發現**：Sabine 理論與實測 IR 的頻段 T30 在 125Hz 差 2 倍以上
  （逐表面 0.348 vs 0.748；六面 gypsum 0.282 vs 0.772），但 500Hz 幾乎完全吻合（1.638 vs 1.634）。
  用六面均勻對照組確認**與 per-wall 改動無關**，是 α 高時模擬與 Sabine 的系統性偏差。
  T-13 若只輸出 Sabine 數字會與實際聽到的差 2 倍——又是「數字合理但東西是錯的」。
- **沒有放寬任何判準**：`GEOMETRY_ERROR_TOLERANCE` 仍 0.30、`CLIP_CONFIDENCE_THRESHOLD` 仍 0.4。
- 向下相容確認：T-01（不帶材質參數）行為與檔名照舊、T-03 `--material` 保留但印警告、
  T-10 迴歸測試仍通過。
- 下一步：**T-13 先不要開工**（RT60 ∝ 體積，尺寸來源未定案會白做）。
  請 Fable 依 `output/geometry/REPORT.md` §6 的 5 個方向決策 T-11 路線。

## 2026-08-18 (12)

- **T-10 Opus 複驗：✅ 通過。順序缺陷確實修好，T-11／T-12 解鎖。**
- **決定性的一項驗證：把舊 `preprocess.py`（`5c643fd`）複製到暫存目錄配上新測試腳本跑，
  結果 exit 1、錯誤訊息正是「極點均勻的合成 equirect 被誤判為非環景」；新程式碼 exit 0 全過。**
  這證明 `scripts/test_preprocess.py` 有真實診斷力，不是只會亮綠燈的裝飾——
  沒驗這一項的話，整個修正的可信度是零。
- 反造假檢查：`git diff` 確認 `config.py` 的容差/門檻**完全未變動**，不是靠放寬標準過關；
  grep 確認 `detect_and_crop_border` 只剩非環景分支一個呼叫點，沒有旁路。
- 非環景路徑新舊碼逐張比對：corridor（50/30/0/6）、bathroom（0）、cgi_cave（上 1）
  **裁切量完全一致**，確認這次改動沒有連帶弄壞既有行為。六視角亮度 std 43–61、兩兩不重複、非空白。
- **複驗另外發現一項既有限制（非本次引入，不阻擋）**：帶 letterbox 外框的 equirect
  （外框讓長寬比 2.156 超出 ±5%）會被靜默當一般照片處理；**拿舊碼跑同一張圖結果一模一樣**，
  所以是既有限制不是迴歸。已入 HANDOFF 地雷第 11 條，建議日後補「裁切後長寬比落回 2:1 就印警告」。
- 順手更正 TASKS.md 一處文件錯誤：合成測試圖寫成「1024×1024（長寬比精確 2:1）」自相矛盾，
  實際是 1024×512。
- 下一步：T-11（幾何估計，含 metric depth 評測關卡）與 T-12（材質模組）可並行。

## 2026-08-18 (11)

- **T-10 順序缺陷已修，待重新驗證。** `preprocess_image()` 原本 `裁黑邊 → is_equirect(裁後圖)`，
  改成 `is_equirect(原圖) → 環景則整段跳過黑邊裁切／非環景才裁`。equirect 判定的 `is_equirect()`
  函式本身沒改，只是呼叫方不再把裁切後的圖餵進去。環景時 `border_crop` 欄位保留與非環景一致的
  結構（`crop_*_px` 全 0，多一個 `skipped_equirect: true`），CLI 與 `meta.json` 不用跟著改。
- 新增 `scripts/test_preprocess.py`：合成極點均勻的 equirect（上下各 30 列純色模擬天頂/天底）
  做迴歸測試，驗證裁切完全跳過、極點像素逐 pixel 不變、6 視角照常輸出；另外合成一張非環景
  letterbox 照片驗證黑邊裁切沒被連帶弄壞。純合成資料、不依賴 git 裡沒有的環景照片，
  彌補上一輪「5 張環景照只有 1 張測得到」的驗證缺口，任何 clone 都能重跑。
- 重跑真實 `SteinmanHall.jpg`：`border_crop` 四邊確認皆 0px（上一版是餘裕剛好 0.0 的僥倖，
  這次是保證不裁）。重跑 corridor／bathroom：裁切結果與退回前完全一致，非環景路徑未受影響。
- 範圍乾淨：只動 `src/image_reverb/preprocess.py` 一個函式＋新增一支測試腳本，
  未動 SPEC/ROADMAP/WORKFLOW、`config.py` 任何門檻、其他任務的檔案。
- 下一步：Opus 依 WORKFLOW.md §5 重新驗證這一處（含跑 `scripts/test_preprocess.py`），
  通過後 T-11／T-12 並行開工。

## 2026-08-17 (10)

- **T-10 Opus 驗證：🟠 退回，一個必修缺陷（前處理順序反了）。**
  `preprocess_image()` 先裁黑邊再判環景，但 **equirect 的第一列就是天頂那一點被拉伸成整列、
  依定義完全均勻**，於是極點被當純色邊框吃掉。合成實測：裁 3 列 → 赤道在 768px 透視圖偏移 3.8px；
  **裁 ≥25 列 → 長寬比超出 ±5% → 環景判定翻成 False → 整條環景路徑被靜默跳過**，
  360 圖會被當一般照片送進 T-11。
- **沒被自檢抓到的原因**：唯一測得到的真實環景 `SteinmanHall.jpg` 第 0 列 spread = 3.0，
  門檻是 `< 3.0`，**餘裕剛好 0.0，純屬僥倖**。且 8 個對照場地的 5 張環景照沒進 git，
  **只有 1 張測得到，另外 4 張完全沒驗證**。
  → 又是「安靜地輸出看似合理的錯誤結果」這一類（同 HANDOFF §2 洞二、地雷第 9 條）。
- 修法：`is_equirect()` 改對原圖判斷；判定為環景就完全跳過黑邊裁切（equirect 本來就沒有 letterbox）。
- **驗證通過的部分**：投影幾何用「gnomonic 中大圓必為直線」量化確認（赤道偏離 2.81px、
  經線 1.42px／768px，屬線寬等級）；9 張照片反測無誤裁（暗邊照片只裁 1 列）；
  corridor 黑邊裁乾淨；錯誤處理四種情境都正確；範圍乾淨無越界。
- **驗證期間補上一項 Sonnet 沒測的**：實際產生真實 `.heic` 檔跑過 CLI，F-01 的 HEIC 支援確認可用。
- 下一步：Sonnet 修這一處順序問題（含極點均勻的合成迴歸測試），修完重新驗證。

## 2026-08-17 (9)

- **T-10 完成自檢，待 Opus 驗證**：新增 `src/image_reverb/` 套件（`config.py`/`preprocess.py`/`cli.py`/
  `__main__.py`），`python -m src.image_reverb <photo>` 可跑。三件事都實作：黑邊/letterbox 裁切、
  環景（equirect）偵測、equirect→6 視角透視投影（`py360convert.e2p`）。
- 黑邊裁切改用 **p90-p10 亮度分佈範圍**判定純色邊框（不是「夠不夠暗」），同時抓到 corridor 的
  黑色左右邊與白色底部細邊；用洞穴暗邊照片反測未誤裁（僅 1px 安全誤差）。
- corridor（YouTube 截圖，非環景）→ 左右黑邊裁掉；Steinman Hall（4096×2048，環景）→ 判定正確、
  6 視角肉眼確認直線不彎曲；bathroom（一般照片）→ 僅原樣通過，無誤裁。
- requirements.txt 新增 `py360convert==1.0.4`、`pillow_heif==1.1.1`（HEIC 支援）。
- 補上一個 WORKFLOW §5 第三層要求的錯誤處理漏洞：非圖片輸入原本會噴完整 traceback，
  已改成清楚中文錯誤訊息＋exit code 2。
- 下一步：T-11（幾何估計）與 T-12（材質模組）可並行進行，兩者前置皆為 T-10。

## 2026-08-16 (8)

- **T-08 完成（Fable）：Phase 0 結案，三個路線決策定案。**
  1. 深度：改 metric depth 模型（Depth-Anything-V2-Metric-Indoor），參考物降為尺度校驗，
     手動覆寫升 P0；T-11 內建評測關卡——metric 模型精度未驗證，先對已知尺寸場地實測，
     不達標即 🔴 卡關回報，不硬走。
  2. 材質：併用——ADE20K 只管幾何角色分割，材質標籤交 CLIP zero-shot 二階分類器
     （信心 gating + fallback 警示）；`floor`/`wall` 語意不再採信。
  3. 環景：做最小範圍（equirect→6 視角透視投影，進 T-10 前處理），驗收場地 4→8 個，
     提前解掉 SPEC §8 視野外風險。
- IR 生成維持 A+B 混合（人耳已確認鏈路可用）。SPEC v0.1→v0.2
  （F-02/F-03/F-04/F-09 修訂、§5 加前處理層、§7 加人耳試聽驗收、§8 加「模型安靜失敗」風險）。
- Phase 1 八張卡（T-10~T-17）細化到可執行：**約束 A（逐表面材質）寫進 T-12 步驟 2、
  約束 B（逐頻段 RT60）寫進 T-13 步驟 2**，各含迴歸數字自檢（0.348s/4.093s 那組）
  與 Opus 紅旗（先平均再套用＝繞過約束）。T-12 含「鐵筒子」修復的使用者複聽關卡。
- 下一步：Sonnet 執行 T-10。T-11 與 T-12 之後可並行。

## 2026-08-16 (7)

- **T-02 100% 完成**：使用者試聽 `output/wet_demo.wav` 後回覆「殘響的效果還算自然」，
  最後一項自我檢查（人耳試聽）通過。這是整條鏈路 pyroomacoustics 模擬 → IR → 卷積
  第一次由人耳確認可用。註記「還算」是可接受而非驚豔，T-14 應以此為基準線求進步。
- 新增 HANDOFF.md 交接文件，CLAUDE.md 加上指標。T-07 狀態改為「暫緩—使用者未授權下載」。
- **🔴 產生材質試聽對照組時發現：寬頻 RT60 對頻率選擇性材質是誤導的。**
  以 `small --material carpet` 為例，125 Hz 的 RT60 是 4.093 s、4 kHz 只有 0.126 s（差 32 倍）；
  把六段 α 平均（0.3067）算出的寬頻 RT60 是 0.267 s，但實測 T30 是 4.023 s——**差 15 倍**，
  因為殘響尾巴完全由低頻決定。**T-13 必須逐頻段獨立算 RT60，不能用平均 α。**
  已記入 TASKS.md T-03 卡、HANDOFF.md 地雷第 8 條、TODO.md。
- **🔴🔴 使用者試聽材質對照組，抓到數值驗證抓不到的模型缺陷。**
  使用者聽 carpet 版本後回覆「感覺很像用手去拍鐵筒子出來的聲音」（marble 與 default 都 OK）。
  頻譜分析證實殘響能量全集中在 30–135 Hz（峰值僅差 2.7 dB，低頻持續共振）。
  根因：`--material` 把單一材質套到全部六個面，等於「連天花板牆壁都鋪地毯」；
  地毯低頻 α 只有 0.02，而真實房間的牆是石膏板（125 Hz α = 0.29，板共振吸音體專吃低頻）。
  量化：低頻 RT60 差 **11.8 倍**（4.093 s vs 0.348 s），低頻/高頻比從現實的約 1 倍變成 **32 倍**。
  → **T-12 必須支援逐表面指定材質**（ShoeBox 原生支援 per-wall material）。
  **這個錯誤通過了 WORKFLOW §5 全部三層檢查**（RT60 在 0.1–12s 內、α 在 0–1、無假實作），
  只有人耳抓得到 → **Phase 1 驗收必須加入試聽環節，數字合理 ≠ 聽起來對。**

## 2026-08-16 (6)

- T-04／T-05／T-06 完成（多 agent workflow，含跨任務總稽核）。Phase 0 只剩 T-07（選做）與 T-08。
- **T-04 來源變更**：OpenAIR 兩個域名都被主機商停權（轉 `suspendedpage.cgi`），站台實質關閉。
  經使用者同意改用 EchoThief（5 場地）+ MIT Reverb Survey（3 場地），共 8 組 IR + 場地照片，
  超過卡片要求的 3 組。測試照片 9 張，T-04 的 5 類全涵蓋。
- **授權處理**：EchoThief 查證後確認「免費下載但未授予再散布權」（網站從未有 License 頁，
  連 zip 中央目錄都沒有 LICENSE 檔）。已把 `assets/reference_irs/` 的媒體檔加入 .gitignore，
  只讓 INFO.md 進版控。另修正 .gitignore 讓 `output/**/*.md` 例外進版控——
  兩份 REPORT 是本輪最有價值的資產，原本會被 `output/` 規則整個吃掉。
- **🔴 T-05 產出否定性結論**：單張相對深度圖**不能**用來估房間體積。實測深度動態範圍與空間大小
  無單調關係（車內 91.5x > 體育館 11.7x）；給絕對錨點後走廊消失點推出 374 萬公尺、
  浴室高估 60–120%。因 RT60 ∝ V，這直接衝擊 SPEC F-02 的 ±30% 目標。
  建議改用 metric depth 模型或已知尺寸參考物錨定 → **T-08 架構決策**。
- **🔴 T-06 產出否定性結論**：滿鋪地毯只有 29.6% 被判成 `rug`、70.4% 判成 `floor`，
  換算後高頻吸音只剩正確值的 32%；車內場景 ADE20K 完全無對應類別（連車外烤漆都判成 wall），
  且模型會「安靜地輸出看似合理的錯誤結果」。已產出 42 類 → 材質 id 對照表含信心分級。
- **💡 新發現**：8 張場地照片有 5 張是 360° 環景，透視模型不能直接吃
  → SPEC §7 驗收第 2 條目前只有 4 個場地可用；但環景沒有「視野外」，
  反而可提早解掉 SPEC §8 的已知風險。留給 T-08。
- 補上 `assets/SOURCES.md`（T-04 明列產出）。**未竟**：9 張照片的來源網址仍待使用者提供。

## 2026-08-16 (5)

- 用多 agent workflow 一口氣跑完 T-01／T-02／T-03，每張卡配獨立驗證者依 WORKFLOW §5 三層標準
  親自執行指令審查。三張卡都 **0 修正輪直接通過**，另加一輪跨任務總稽核。
- T-01：`gen_ir_manual.py`，small RT60 0.219s／hall 4.55s，48kHz/24bit/mono、峰值 -3dBFS。
  反造假交叉驗證：直達音到達時間 vs 幾何理論值誤差 < 0.4ms，確認 IR 真的來自房間模擬。
- T-02：`convolve.py` + 合成乾拍手 + `wet_demo.wav`（10.437s，無爆音）。乾濕比實證有效
  （mix=0 尾段 RMS 0.0、mix=1 為 0.00069906）。
- T-03：`materials.json` 12 種材質、72 個 α 全在 0–1，係數對照建築聲學標準表抽查正確，
  `--material` 選項可用（marble RT60 6.40s，是預設的 29 倍）。
- 總稽核抓到 4 個錯誤處理缺陷（壞輸入吐 traceback），另開一輪修正 + 複驗，PASS。
  順帶修掉 T-00 `check_audio.py` 的死分支 bug（`except FileNotFoundError` 永遠抓不到，
  因為 soundfile 拋的是 `LibsndfileError`），並把過寬的 `except Exception` 收窄。
- T-00 驗證通過。**Phase 0 卡在 T-04**：需要使用者提供照片、並同意下載 OpenAIR IR 與 AI 模型。

## 2026-08-16 (4)

- T-00 完成（Sonnet 執行，狀態改為 🔵 待驗證，待 Opus 審查）。
- 建立 `.venv/` 虛擬環境，安裝 numpy/scipy/soundfile/matplotlib/pyroomacoustics/pillow，
  `pip freeze > requirements.txt`（19 個套件）。
- 建立 `assets/photos/`、`assets/dry/`、`assets/reference_irs/`、`output/`、`scripts/` 資料夾。
- 新增 `scripts/check_audio.py`：印出音訊檔取樣率/長度/聲道數/RMS/峰值，近乎靜音會警告，
  無參數印用法說明，檔案不存在給清楚錯誤訊息。
- `.gitignore` 新增 `output/`。自我檢查兩項皆通過。

## 2026-08-16 (3)

- 建立多視窗協作系統：Fable 規劃 / Opus 驗證 / Sonnet 執行。
- 新增 CLAUDE.md（每個視窗自動載入的角色說明與規則入口）。
- 新增 WORKFLOW.md（三種標準 Prompt、收工程序、Commit 時機、三層驗證標準與造假紅旗）。
- 新增 TASKS.md（Phase 0 任務卡 T-00~T-08 可無腦執行；Phase 1 框架 T-10~T-17 待 T-08 細化）。
- TODO.md 改為高層總覽，執行細節移至 TASKS.md。

## 2026-08-16 (2)

- 調查 GitHub 上的類似專案，結論：「照片→IR」有學術實作（Image2Reverb ICCV 2021、
  AV-RIR CVPR 2024 等）但無產品級工具 → 整理為 RESEARCH.md。
- 撰寫 SPEC.md v0.1：功能需求（F-01~F-23）、非功能需求、系統架構、
  材質吸音係數表規劃、驗收標準、風險。
- 更新 ROADMAP：各 Phase 對應 SPEC 功能編號，Phase 0 加入具體研究項目與決策點。
- 暫定 MVP IR 生成路線：image-source 早期反射 + shaped-noise 晚期殘響（A+B 混合）。

## 2026-08-16

- 確立專案願景：做一個空間模擬 Reverb 效果器（對標 Altiverb 8），但 IR 不靠實地錄製，
  而是由 AI 從照片/影片分析空間幾何與材質後自動生成。
- 研讀 Altiverb 8 手冊，確認其核心為 convolution reverb（IR 卷積）。
- 更新 README（系統架構、三條 IR 生成路線）、ROADMAP（Phase 0–3）、TODO。
- 決策：MVP 先做「照片 → IR (WAV) 匯出」，用現有 convolution reverb 驗證品質，
  之後再做 JUCE plugin。

## 2026-08-05

- 建立專案 repo 並初始化基礎文件（README, ROADMAP, TODO, DEV_LOG, .gitignore）。
