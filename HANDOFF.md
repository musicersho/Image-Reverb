# 交接文件 — 給下一個視窗

> 最後更新：2026-09-02（Opus 驗證視窗：**T-39 ✅ 通過（否定結論成立）**——
> 16 個 proxy 面已由使用者逐面重對映（proxy 16→13），3 個有公開出處的新
> 候選 `vinyl_panel`／`rubber_flooring`／`metal_roof_deck` 加入後跑滿預算
> （round12～round14）未同時達成三個產品採用門檻且最終輪最差（24/76），
> 「補選項」這條路在本 13 張資料集上實證關閉。`surfaces.py` 已還原成 12
> 條候選（與 T-39 前逐位元相同）；`materials.json` 的 3 筆新材質資料與
> ground truth 重對映**保留不回滾**。關鍵發現：兩個新候選的目標面在
> ADE20K 分割階段就沒被偵測到，CLIP 從未被呼叫＝結構性不可達。
> 下一步：開 Sonnet 視窗執行 **T-44（role-aware 候選子集，不需使用者參與
> 標註）**，交接文件見 [HANDOFF_T39.md](HANDOFF_T39.md)）
> **新視窗請先讀 [CLAUDE.md](CLAUDE.md) 知道自己的角色，再讀本檔知道現在的狀況。**
>
> 驗證本檔是否過期：看 [DEV_LOG.md](DEV_LOG.md) 最上面一筆是不是 `2026-09-02 (89)`；
> 若已有更新的紀錄，以 DEV_LOG 為準。

---

## 一分鐘進入狀況

**Phase 0 ✅；Phase 1 工程卡全數通過（T-10~T-16、T-18、T-22）；Phase 1.5 ✅；
Phase 1.6 修正輪（T-23~T-26）✅ 四張全過（2026-08-30）。**
**但 T-17 MVP 驗收已執行且兩項未達標：§7-1 盲聽 2/5（要 ≥4/5）、§7-2 RT60
自動組 0/8、手動組 0/5。病因已隔離——主導是材質辨識（CLIP），不是幾何、
不是合成引擎**（決定性證據：壁球場只把材質改對，誤差 −50% → +13%；
報告全文在 `output/mvp_acceptance/REPORT.md`）。

⚠️ **目前產品狀態要誠實知道**：T-26 的輸出 gate 上線後，**專案 13 張真實照片
100% 被擋**（exit 3、不寫任何檔；Fable 2026-08-30 零信用複驗逐張重跑證實）。
這與 T-17 量測一致（自動路徑目前不可信），已由 **Fable 裁決 T-28-A** 定調：
**gate 規則不動、修出口（T-30）、材質準確度先行**（全文見 TASKS.md T-28 卡尾）。
文字（`--text`）與複合場景（`--scene`）兩條管線不受 gate 影響，端到端可用。

🎯 **現在該做的：開 Sonnet 視窗執行 T-44（role-aware 材質候選子集）**
——T-38B（改字串）與 T-39（補選項）兩條治療路線都已跑滿預算、以誠實的
否定結論通過 Opus 驗證，`surfaces.py` 兩次都還原成 12 條 baseline 候選。
T-44 是裁決 T-38B-A 的第二條出口，也是 Phase 1.9 治療輪的最後一張治療卡：
讓 `classify_region_material()` 吃 `role` 參數，**地板／牆／天花板各自
只在合理的候選子集裡挑**——T-38B 的 round7～10 與 T-39 的 round12～14
副作用**全部是跨角色搶答型**（地板材質搶天花板、面板材質搶牆），
「不在該角色候選集內的材質不可能被選中」是字串治療給不了的機制性槓桿。
⚠️ 誠實的預期管理已明文入卡：bedroom 四面牆的 generic_wall→concrete 是
**牆對牆**混淆，role-aware 對它零槓桿、預期不治，不得拿它當本卡失敗依據。
**T-44 的比較基線是 `round11_remap_baseline`（30/76、floor 4/13、
非 proxy 30/63、in-set 誤判 9），不是 round0_baseline、也不是 round12～14。**
📄 **本階段專屬交接文件 [HANDOFF_T39.md](HANDOFF_T39.md)（動工前必讀，
已於 2026-09-02 更新為服務 T-44：§0 現況、§2A T-39 實績與對 T-44 的三項
證據輸入、§3 地雷、§4 範圍紅線、§5 驗收、§6 可直接複製的開工／驗證
Prompt）**。`HANDOFF_T38.md` 已隨 T-39 結案失效，可刪。
⚠️ **T-38 已於 2026-09-01 由 Fable 拆卡改版**：原卡實際已跑六個完整輪次
（round0 基線 31/76、最佳 round4 僅持平、round6 中止 6/13 張）無一達標；
拆成 **T-38A**（先把實驗紀錄機制修好——round1～round5 的提示詞字串已遺失
只剩 hash，標「不可恢復」不得倒填）→ **T-38B**（有界實驗：假設先寫、最多
4 輪、跑滿誠實報告＝完成；「沒有提示詞能改善」是合法研究結論，不是工程
失敗也不是使用者操作失敗）。產品採用門檻不變（overall↑＋floor↑＋in-set
不升，對 round0 基線）；無候選達標則保留 baseline 交 Fable 裁決進 T-39 或
另開 role-aware 卡（`classify_region_material()` 無 role 參數，floor 目標
用全域字串不保證可達——介面限制已明文入卡）。拆卡裁決全文在 TASKS.md
T-38 卡。
📄 T-38A／T-38B 階段的專屬交接文件 [HANDOFF_T38.md](HANDOFF_T38.md) 已完成
歷史任務（T-39 結案後可刪）；**T-39／T-44 階段改讀
[HANDOFF_T39.md](HANDOFF_T39.md)**。
⚠️ 2026-08-31 Fable 已依外部掃描報告在
Phase 1.9 插入**產物可信度修正輪 T-40～T-43**（評測快取指紋／SegFormer
去重／gate 交易式輸出／T-17 產物溯源——五項缺陷全部對碼核實屬實），完整
順序更新為（2026-09-01 裁決 T-38B-A 後）
**T-37 ✅ → T-40 ✅ → T-41 ✅ → T-38A ✅ → T-38B ✅（否定結論）→ T-39 →
T-44 → T-42 → T-43 → 收尾複評**；
**任何新的正式盲聽必須在 T-42＋T-43 之後**（現存盲測素材是 `d958b3c` 產的，
舊 2/5 不能宣稱屬於現行碼）。卡片與插卡裁決全文在 TASKS.md 檔尾 Phase 1.9 節。
⚠️ **T-40 的一個重要副作用**：`python scripts/t36_clip_accuracy.py`
不帶參數執行**從此永遠 hard fail**（因為 13 份既有 `detail.json` 是無
`fingerprint` 欄的舊格式，且規則規定既有凍結檔一個 bit 都不許補寫）——
這是刻意設計，不是程式壞了；往後任何治療評測（T-38／T-39）一律要加
`--out-dir <新目錄>`。詳見 TASKS.md T-40 卡「交接筆記」。

🔮 **裁決 T-36-A 一句話（2026-08-31，全文在 TASKS.md T-36 卡尾）**：
**gate 規則就地定案——規則 1／2／3 與地雷 #23／#24 全部維持原樣、議題關閉**
（終止條款觸發：12/13 low 未動；獨立實證：CLIP 真判定 52.4%＝丟銅板、fallback
32 面裡 29 面 top-1 也錯、調低門檻放行的多數是錯的；規則 3 語義定調「high＝
六面皆獨立觀測且模型自信，只有環景拿得到」）；出口導引（T-30/T-34）即為 gate
長期形態；未來任何調整＝新裁決，必附四樣證據（新基準率／放行清單／T-17 已知
錯誤佔比／臥室續擋）。**開 Phase 1.9 CLIP 治療輪**（基準率會動是本輪目的，
但 gate 規則本體與門檻 0.4 零改動；新增「臥室紅旗」與「基線變化表」鐵則）。
**陳設換算公式修正輪不開**（T-38/T-39 會動 S×α、地基又要動；重啟評估點寫死
在 Phase 1.9 收尾複評）。

Phase 1.7 三張執行卡（T-31／T-32／T-33）已全部 ✅ 通過；T-33 量出陳設機制
淨效果為負（自動組 22%→10%、手動組 20%→12%，Steinman Hall 4/5→1/5），
Fable 已於 2026-08-31 作出**裁決 T-33-A**（全文在 TASKS.md T-33 卡尾）並開
**Phase 1.8 輪**（T-33 文件修正／T-34／T-35／T-36 四步全數 ✅ 結案）。

🔮 **裁決 T-33-A 一句話**：陳設機制改**預設觀測模式**（偵測照跑、進
`analysis.json` 標 `applied: false`，聲學不套用；`--furnishings` 才套用
——執行卡 T-35）；**開 CLIP 準確度輪、診斷先行**（執行卡 T-36：13 張×六面
ground truth 由使用者逐面確認＋準確度量測＋「判定全對時 materials 軸天花板」
模擬）；**gate 規則本體零改動但依據全文改寫**——裁決 T-28-A 裁決一的
「不可能性證明」作廢（區辨訊號已存在，只是 Steinman 證明它目前不合格），
複評錨定在 **T-36 交回時就地定案、不得再展延**（硬性終止條款）。
T-34 範圍與文案零調整，照原卡執行。

**Phase 1.8 執行順序：T-33 文件修正 → T-34 → T-35 → T-36 → 回 Fable**
（gate 定案＋治療卡規劃＋評估陳設公式修正輪）。
**本輪明確不做**：陳設公式修正（座位類打折／地板面積換算）、gate 規則調整、T-29。
**紅線不變：gate 判定規則一行不動、六條交付 IR MD5 不變、陳設資料不得餵進
任何信心軸（觀測模式下也一樣）。**

⚠️ **排隊中**：T-29（三條管線 `analysis.json` schema 不一致：三軸信心只在照片管線，
`--text` 只有 `confidence`、`--scene` 連 `confidence` 都沒有；未裁決）。

🔮 **裁決 T-27-A 一句話**：室內陳設用**逐頻段等效吸音面積**表示——
`A_extra[band] = Σ ratio_c × S_total × α_c[band]` 直接加進 `compute_acoustics()`
的 Sabine／Eyring 吸音項，經 `rt60_bands_sabine` 流進 IR 晚期尾巴；**不採
occupancy 係數**（單一寬頻旋鈕表達不了窗簾 125Hz α=0.07 vs 1kHz 0.75 的頻率
結構＝重犯地雷 #8，且沒有現成物理插入點）。資料源＝ADE20K 陳設類別全圖像素
佔比（零新模型），類別 id 與六角色 id 不相交、rug 排除（已在 floor ids）、
玻璃鏡面排除（反射面）。全文見 TASKS.md T-27 卡。

🔮 **裁決 T-28-A 一句話**：臥室（gate 必須擋的案例）與浴室（盲聽答對案例）的
六面「材質＋來源」**逐面完全相同**，任何只讀來源的放寬規則放浴室必放臥室
→ 調門檻做不到；出口是人工確認材質（T-30 ✅），長期解是準確度（T-27／材質輪），
材質輪後用新基準率複測 13 張再談規則。**裁決時已更正 T-28 卡三處數據**
（materials=low 是 12/13 非 13/13；面數分布實為 fallback 32／ood 13／clip 22／
無來源 11；修好材質規則仍有 6/13 被 geometry=low 擋）。臥室 vs 浴室的區辨訊號
（室內陳設）當時不存在——T-31/T-32 正是把它做出來。
⚠️ **其中「不可能性證明」與「材質輪後用新基準率複測」兩句已由裁決 T-33-A 更新**
（前者作廢換新依據、後者承認是規劃錯誤並重新錨定到 T-36），見上方 T-33-A 一句話。

🎧 **使用者試聽紀錄**：T-02 ✅｜T-12 ✅（鐵筒子已解）｜T-14 ✅｜T-20 ✅｜
T-21 ✅（四輪迭代）｜T-17 §7-4 ✅ 已執行（無鐵筒子 artifact；聽感「殘響普遍
過長」，與 §7-2 量測多數場地高估同方向）。人耳回饋全文記在 TASKS.md 各卡。

⚠️ **本專案頭號失敗型態「安靜地輸出看似合理的錯誤結果」已出現六次**
（地雷 #2 洞二、#9、#12、#13、#15、#16）。凡是輸出裡同時有目標值與量測值，
必須有程式在比對；新增 zero-shot 分類必讀地雷 #13；動信心規則必讀地雷 #23/#24。

---

## 0. 【已處理】Fable 規劃結果（2026-08-30）— 六項裁決摘要

原第 0 節的 A~F 六件待裁決事項已全數處理完畢。摘要如下，細節看括號內的出處：

- **A（T-15 卡與實際需求對不上）→ 已改版**：三種輸入（照片/`--text`/`--scene`）互斥
  已落實進「產出/執行步驟/自我檢查」三欄；`dims_source` 三種輸入都必須標；
  複合場景 wet 預覽一律 mix 1.0；新增「交付 IR MD5 零回歸」硬判準（T-22 手法，
  六條交付 IR bit-identical → 免試聽關卡）。（TASKS.md T-15 卡 🔮 2026-08-30）
- **B（§7-2 低頻判準，最重要）→ 已事前裁決**：500Hz–4kHz 逐頻段 <20% **不變**；
  125/250Hz 的**門檻**改為「88–354Hz 低頻聯合帶 T30 誤差 <20%」——逐頻段數字照列、
  超差照警示，只是不當門檻。**數字不放寬，換掉的是已被三次實測證實不可信的量測
  對象**（低頻八度帶 T30；機制＝177Hz 共享邊緣的鄰帶耦合，聯合帶把它內部化）。
  殘留風險（354Hz 上緣）已誠實寫進卡片供 Opus 對抗檢查；`ir_metrics.py` 既有程式
  在 T-17 期間 diff 必須為空。（證據鏈全文：TASKS.md T-17 卡 🔮 裁決 B）
- **C（量程落差呈現）→ 分組統計**：T-17 達標率依 `dims_source` 分兩組
  （metric_depth vs manual），不得合併——自動路徑才是 F-01 產品主張。
  Metric-Indoor-Large 維持延後，分組統計就是它的決策輸入。（T-17 卡裁決 C）
- **D（技術債）→ 分流**：#1（材質 dict 重複實作）、#2（warnings/notes 分流）、
  #5（零/負尺寸、量程規則預設放行）併進 T-15；#4（退出碼）與聯合帶量測工具開
  **新卡 T-18（驗收前置，不依賴 T-15/T-16，T-17 前必過 Opus 驗證）**；
  #3（匹配窗門檻 3dB 薄餘裕）維持文件化不動碼——無失效案例支撐的門檻調整是投機。
- **E（等使用者）→ 照片來源網址列為 T-17 結案前置**（量測可先跑，REPORT 結案前
  必須補齊，否則狀態最高停 🔵）；乾聲/小房間環景/T-07 不擋任何卡。
- **F（ROADMAP 勾選）→ 已同步**：Phase 1 的 T-10~T-14、Phase 1.5 全節（含補列 T-22）
  勾選補齊，過期註記清除，新增 T-18 一行。

---

### 給後續視窗的背景重點（原「給 Fable 的背景重點」，仍然有效）

1. **人耳驗收不是形式**：T-21 走了四輪，每輪都是使用者聽出來、程式數字沒抓到的問題
   （太亮 → 混入乾聲 40%；鐵桶感 → 場景空間選錯；尾巴太長 → 巨蛋沒算滿場觀眾吸音；
   低頻共振 → 石膏板 TL 低頻凸）。**T-15/T-16 只要動到 IR 生成路徑就要排試聽關卡。**
2. **「安靜地輸出看似合理的錯誤結果」已出現五次**，是本專案的體質問題不是偶發。
   規劃 T-15 的 `analysis.json` 與 T-16 的視覺化時，請把「哪裡會有目標值與量測值並列、
   誰負責比對它們」當成明確的設計項，不要留給執行者自由發揮。
3. **T-15 是三條管線的匯流點**：照片（T-10~T-14）、文字（T-20 `scene_text.py`）、
   複合場景（T-21 `coupled.py`）。後兩者已各自有可用的獨立腳本
   （`gen_ir_from_text.py`、`gen_ir_coupled.py`），T-15 只是統一入口——
   **範圍要框住，別讓它變成重寫**。
4. **零回歸是可以硬性驗證的**：T-22 用「交付版 IR 的 MD5 必須 bit-identical」當判準，
   實際擋住了改動擴散。T-15 整合時建議沿用同一手法（三條管線的既有交付檔 MD5 不得變）。

## 1. 目前進度

| 卡 | 內容 | 狀態 |
|---|---|---|
| T-00 | 開發環境（`.venv`、`check_audio.py`） | ✅ 通過 |
| T-01 | 手動參數生成 IR（`gen_ir_manual.py`） | ✅ 通過 |
| T-02 | 離線卷積試聽（`convolve.py`） | ✅ **完全通過**（使用者試聽確認殘響自然） |
| T-03 | 材質吸音係數表（12 種材質） | ✅ 通過 |
| T-04 | 測試素材與對照 IR（9 照片 + 8 組 IR） | ✅ 通過｜🚧 照片來源網址待補 |
| T-05 | 深度估計測試（Depth Anything V2） | ✅ 通過｜🔴 產出否定性結論 |
| T-06 | 語意分割測試（SegFormer ADE20K） | ✅ 通過｜🔴 產出否定性結論 |
| T-07 | Image2Reverb baseline（選做） | ⏸️ 暫緩，使用者未授權下載 |
| T-08 | Phase 0 總結與路線決策 | ✅ **完成（Fable，2026-08-16）** |
| T-10 | 專案骨架與影像前處理（含環景投影） | ✅ **通過**（順序缺陷已修並經 Opus 複驗，2026-08-18） |
| T-11 | 幾何估計（metric depth → 房間尺寸） | ✅ **通過**（Opus 驗證 2026-08-27；量程規則經對抗測試確認非 hardcode） |
| T-12 | 材質模組（逐表面材質） | ✅ **通過**（Opus 驗證 2026-08-25，含使用者試聽 ✅） |
| T-13 | 聲學參數計算（逐頻段 RT60 + pre-delay） | ✅ **通過**（Opus 驗證 2026-08-27） |
| T-14 | IR 合成引擎 v1（早期 image-source + 晚期 shaped-noise） | ✅ **通過**（Opus 驗證 2026-08-28）｜尺度上限已由 T-22 解除 |
| T-20 | 文字場景描述 → IR（13 preset＋解析器，F-16） | ✅ **通過**（Opus 驗證 2026-08-28）｜`stadium_dome` preset 受惠於 T-22，程式未改 |
| T-21 | 複合場景引擎 v1（路徑串接＋TL 表，F-17） | ✅ **通過**（Opus 複驗 2026-08-28，退回→修正→v4 重聽→複驗；人耳共四輪） |
| T-22 | T-14 引擎尺度自適應（早期窗/匹配窗隨尺寸調整） | ✅ **通過**（Opus 驗證 2026-08-28；驗證到 200m 級，小/中房間 bit-identical 零回歸） |
| T-15 | CLI 整合（照片／文字／複合場景 → IR + 報告） | ✅ **通過**（Opus 驗證 2026-08-30） |
| T-16 | 分析視覺化（三種輸入各有拼版） | ✅ **通過**（Opus 驗證 2026-08-30） |
| T-18 | 驗收前置（聯合帶量測工具＋退出碼技術債） | ✅ **通過**（Opus 驗證 2026-08-30） |
| T-17 | MVP 驗收（SPEC §7 四項） | ⚠️ **已執行，2 項未達標**（§7-1 盲聽 2/5、§7-2 自動組 0/8；§7-3/§7-4 通過；報告 `output/mvp_acceptance/REPORT.md`）｜🚧 照片來源網址仍為結案前置 |
| T-23 | fallback 材質單一事實來源 | ✅ **通過**（Opus 驗證 2026-08-30） |
| T-24 | ADE 可信材質死碼清理（裁決 T-24-A） | ✅ **通過**（Opus 驗證 2026-08-30，第三輪） |
| T-25 | confidence 拆三軸（幾何／材質／overall） | ✅ **通過**（Opus 驗證 2026-08-30） |
| T-26 | 低信心輸出 gate（low → exit 3 不出檔） | ✅ **通過**（Opus 驗證 2026-08-30）｜⚠️ 連帶：13 張真實照片 100% 被擋 → 裁決 T-28-A |
| T-28 | gate 基準率（13/13 被擋的兩難） | 🔮 **已裁決 T-28-A**（Fable 2026-08-30：規則不動、修出口、準確度先行；含三處數據更正） |
| T-30 | gate 出口導引（裁決 T-28-A 執行卡） | ✅ **通過**（Opus 驗證 2026-08-30；附兩則後續建議 → 已開 T-34） |
| T-27 | 室內陳設吸音表示 | 🔮 **已裁決 T-27-A**（Fable 2026-08-30：逐頻段等效吸音面積，不採 occupancy；執行卡 T-31~T-33） |
| T-31 | 陳設等效吸音：資料表＋偵測模組 | ✅ **通過**（Opus 驗證 2026-08-30） |
| T-32 | 等效吸音面積入聲學計算與照片管線 | ✅ **通過**（Opus 驗證 2026-08-30） |
| T-33 | 材質輪基準率複測（量測卡） | ✅ **通過**（Opus 驗證 2026-08-31；量測結論：陳設機制淨效果為負）｜文件修正已補（2026-08-31） |
| — | 🔮 裁決 T-33-A（T-33 複評＋Phase 1.8 規劃） | ✅ **已裁決**（Fable 2026-08-31：陳設改觀測模式、開 CLIP 診斷輪、gate 依據改寫；全文 TASKS.md T-33 卡尾） |
| T-34 | gate 訊息補洞（規則 2 死路＋測試覆蓋） | ✅ **通過**（Opus 驗證 2026-08-31；gate 判定條件零改動，只補訊息與測試；附兩則文件修正建議） |
| T-35 | 陳設改預設觀測模式（裁決 T-33-A 裁決 A） | ✅ **通過**（Opus 驗證，2026-08-31） |
| T-36 | CLIP 材質判定準確度診斷（量測卡，需使用者標註） | ✅ **通過**（Opus 複驗 2026-08-31）；裁決 T-36-A 已下，開 Phase 1.9 治療輪 |
| T-37 | 地雷 #16 修正：`is_equirect()` 加極點列均勻度檢查 | ✅ **通過**（Opus 驗證，2026-08-31；`output/equirect_fix/REPORT.md`） |
| T-40 | 評測快取指紋與自動失效（插卡 1/4） | ✅ **通過**（Opus 複驗，2026-08-31；退回修正輪已驗收） |
| T-41 | 透視照 SegFormer 重複載入去重（插卡 2/4） | ✅ **通過**（Opus 驗證，2026-08-31；`pipeline.py` `+2 -5`） |
| T-29 | 三管線 analysis.json schema 一致性 | ⬜ 未裁決（不進 Phase 1.8） |

逐卡的詳細交接筆記在 [TASKS.md](TASKS.md) 每張卡的「交接筆記」欄，本檔不重複。

---

## 2. 這一輪推翻了什麼（最重要的部分）

Phase 0 的實測結果**否定了 SPEC 原本假設的兩個關鍵環節**。以下是證據，不是推測。

### 🔴 洞一：單張相對深度圖不能估房間體積

出處：[`output/depth/REPORT.md`](output/depth/REPORT.md) §7

- Depth Anything V2 輸出的是**每張圖各自正規化的相對 disparity**，不是距離。
- 實測 9 張照片，深度動態範圍與實際空間大小**沒有單調關係**：

  | 空間 | 實際進深 | 核心 p95/p5 |
  |---|---|---|
  | SUV 車內 | ~2 m | **91.5x** |
  | 浴室 | ~3 m | 5.5x |
  | 飯店長廊 | ~30 m | 12.7x |
  | 體育館 | ~150 m | **11.7x** |

  車內比體育館小好幾個數量級，深度範圍卻大 8 倍。
- 就算給絕對錨點用 `距離 = k/disparity` 換算也會壞：
  走廊消失點（disparity=0）推出 **3,747,829 公尺**；浴室實際 2.5–3.5 m，推得 5.50 m（**高估 60–120%**）。
- **後果**：Sabine 公式 RT60 ∝ V，體積誤差以平方/立方級放大到 RT60
  → **SPEC F-02 的「±30% 誤差目標」照現行路線做不到。**

### 🔴 洞二：ADE20K 分不出地毯，也認不得車內

出處：[`output/seg/REPORT.md`](output/seg/REPORT.md) §2.3、§2.9、§4

- **地毯**：飯店走廊滿鋪地毯，只有 **29.6%** 判成 `rug`、**70.4%** 判成 `floor`。
  換算吸音係數：`0.296×0.65 + 0.704×0.02 = 0.207`，正確值應是 `0.65`
  → **高頻吸音只剩 32%**。REPORT 結論：「`floor` 這個類別在本專案裡是不可信的」。
- **車內**：ADE20K 沒有任何車輛內裝類別。車頂內襯、窗外樹林（92.4%）、
  連車外橘色烤漆（100%）**全部判成 `wall`**。
- **最麻煩的性質**：模型對失敗**毫無自覺**，一律輸出高置信度結果——
  「會安靜地輸出看似合理的錯誤結果」。

### 💡 一個意外的機會：360° 環景

8 個對照場地的照片有 5 張是 equirectangular 環景（見 [`assets/SOURCES.md`](assets/SOURCES.md) §3.4）。

- **壞消息**：透視模型不能直接吃 → SPEC §7 驗收第 2 條目前只有 4 個場地可用。
- **好消息**：環景**沒有「視野外」**。SPEC §8 的已知風險「照片視野外的空間（背後的牆）未知」
  原本要靠 Phase 3 的影片輸入（F-20）才能解，用環景可以提早處理。

---

## 3. T-08 的三個決策（✅ 已定案，2026-08-16，Fable）

1. **深度路線 → metric depth 模型**（Depth-Anything-V2-Metric-Indoor，與 T-05 同款 pipeline）。
   參考物（門 ~2.0m）降級為尺度校驗；手動尺寸覆寫升 P0。
   ⚠️ metric 模型在本專案照片上的精度未驗證 → **T-11 內建評測關卡**：先對已知尺寸場地實測，
   一般室內誤差 ≤±30% 才往下走，不達標就 🔴 卡關回報 Fable（設計內的結果，不是失敗）。
2. **材質路線 → 併用**：ADE20K 分割只管「切出表面的幾何角色」，材質標籤交給
   **CLIP zero-shot 二階分類器**（信心 gating + fallback 警示）；`floor`/`wall` 語意不採信。
3. **環景 → 做，最小範圍**：equirect→6 視角透視投影，放 T-10 前處理（純幾何運算、無新模型）。
   換到驗收場地 4 個 → 8 個全可用，並提前解掉 SPEC §8「視野外」風險。

IR 生成路線維持 A+B 混合不變（人耳已確認鏈路可用）。SPEC 已升 v0.2。

### ⚠️ 另有兩條「已定案、不需決策，但 T-08 細化任務卡時必須寫進去」的約束

這兩條是 Phase 0 實測出來的硬性結論，不是選項：

| # | 約束 | 影響的卡 | 實證 |
|---|---|---|---|
| A | **材質必須逐表面指定**（地板／天花板／各面牆分開），不可全域套單一材質 ✅ **已在 T-12 實作並經人耳確認（2026-08-18）** | T-12 | 全鋪地毯 vs 只有地板鋪地毯，低頻 RT60 差 **11.8 倍**（4.093s vs 0.348s）；舊版使用者試聽形容「像用手拍鐵筒子」，修好後實聽確認「沒問題」 |
| B | **RT60 必須逐頻段獨立計算**，不可用平均 α 算單一寬頻值 | T-13 | 地毯房間 125Hz RT60 = 4.093s、4kHz = 0.126s（差 32 倍）；平均 α 算出 0.267s，實測 T30 是 4.023s（**差 15 倍**） |

細節見本檔第 6 節地雷第 8、9 條，以及 [TASKS.md](TASKS.md) T-03 卡的交接筆記。

✅ **T-08 已把 A、B 兩條寫進任務卡執行步驟**：A → T-12 步驟 2（含 0.35s vs 4.09s 迴歸自檢
與使用者複聽關卡）、B → T-13 步驟 2（含「程式裡不得存在 mean(α)→RT60 路徑」的 Opus 紅旗）。

---

## 4. 等使用者的事（AI 推不動）

- 📷 **補 9 張照片的來源網址** — `assets/SOURCES.md` §2 已標好待補位置。
  T-04 自我檢查第 2 項「SOURCES.md 每一項都有來源連結」目前**不符合**。
- 📷 **補一張真實的教堂／空場硬質大空間** — 現有大空間樣本全被人群主導（人是強吸音體），
  無法驗證長殘響情境。
- 📷 **（新，2026-08-27 裁決衍生）補一張「小房間的 360° 環景」** — 目前唯一測得到的環景
  Steinman 實測單面牆距超標（依裁決正確地標 low），所以環景路徑**沒有任何一個
  「範圍內維持 medium」的防濫殺對照案例**。一張普通房間的 equirect 照片就能補上這個缺口；
  沒有的話留待 T-17 用真實 IR 間接檢驗。
- 🎤 **（新，2026-08-28）補一段真實說話聲乾聲** 放 `assets/dry/` — `neighbor_voices`
  複合場景的情境是「隔壁有人在講話」，但目前乾聲只有合成拍手，示範不出講話聲的感覺。
  有真實乾聲後重跑 `python scripts/gen_ir_coupled.py assets/scenes/neighbor_voices.json` 即可。
- ❓ **T-07 要不要做** — Image2Reverb baseline，限時 2 小時，失敗是可接受結果。需授權 clone/下載。

---

## 5. 環境速查

```bash
cd "/Users/musicersho/Image Reverb"
source .venv/bin/activate          # 跑任何 python 前都要先做這件事
```

| 指令 | 用途 |
|---|---|
| `python scripts/check_audio.py <檔>` | 印取樣率/長度/聲道/RMS/峰值，RMS<0.0001 警告靜音 |
| `python scripts/gen_ir_manual.py small\|hall [--material <id>]` | 生成 IR（48kHz/24bit/mono，-3dBFS） |
| `python scripts/gen_ir_manual.py --list-materials` | 列出 12 種材質 id |
| `python scripts/show_materials.py` | 印材質吸音係數表 + 自動檢查 |
| `python scripts/convolve.py <dry> <ir> <out> [--mix 0.5]` | 離線卷積，輸出 -1dBFS |
| `python scripts/test_depth.py` | 深度估計批次處理 `assets/photos/` |
| `python scripts/test_segmentation.py` | 語意分割批次處理 `assets/photos/` |
| `python scripts/test_preprocess.py` | T-10 前處理迴歸測試（合成資料，任何 clone 可跑） |
| `python scripts/gen_ir_manual.py small --materials floor=carpet,walls=gypsum_board` | **T-12 逐表面材質**生成 IR |
| `python -m src.image_reverb <photo> --geometry --materials-detect` | T-11 幾何＋T-12 材質完整分析 |
| `python -m src.image_reverb <photo> --override-dims 4x3x2.5` | 手動指定房間尺寸（F-09，不跑深度模型） |

⚠️ **2026-08-30 起照片管線有輸出 gate（T-26）**：overall confidence 為 `low`
→ exit 3、不寫任何檔——**目前 13 張真實照片全部如此**。要照樣輸出加
`--force-low-confidence`（產物會標記 `forced_low_confidence: true`）；
正規出口是把 `fallback`／`out_of_domain` 的面用 `--override-material 面=材質id`
覆寫（materials 會變 medium，實測 exit 0；T-30 會把這條路印進 gate 錯誤訊息）。
注意 `--override-dims` **單獨用解不了 gate**（只救幾何軸）。

環境：Python 3.9.6 / torch 2.8.0（MPS 可用）/ pyroomacoustics 0.10.1 / numpy 2.0.2。

### 產生材質試聽對照組（要請使用者用耳朵驗收時用）

`output/` 不進 git，所以這些檔案在新視窗／新 clone 都要重新產生：

```bash
python scripts/gen_ir_manual.py small                      # 預設 α=0.3
python scripts/gen_ir_manual.py small --material marble
python scripts/gen_ir_manual.py small --material carpet
for m in ir_room_small:default ir_room_small_marble:marble ir_room_small_carpet:carpet; do
  python scripts/convolve.py assets/dry/clap_synth.wav "output/${m%%:*}.wav" \
    "output/listen_${m##*:}.wav" --mix 0.6
done
```

聽感基準（2026-08-16 使用者實聽）：`marble` ✅ 自然、`default` ✅ 自然、
**`carpet` ❌「像用手拍鐵筒子」** ← 這是地雷第 9 條的模型缺陷。

**T-12 修好後的對照組（2026-08-18 產生，等使用者試聽）：**

```bash
python scripts/gen_ir_manual.py small --materials floor=carpet,walls=gypsum_board,ceiling=gypsum_board
python scripts/gen_ir_manual.py small --material carpet          # 舊的鐵筒子版（會印警告）
python scripts/convolve.py assets/dry/clap_synth.wav output/ir_room_small_surf_carpet.wav \
  output/listen_T12_surf_carpet.wav --mix 0.6
python scripts/convolve.py assets/dry/clap_synth.wav output/ir_room_small_carpet.wav \
  output/listen_T12_uniform_carpet.wav --mix 0.6
```

實測差異：125Hz T30 **3.952s → 0.748s**、低頻/高頻比 **48.8 倍 → 1.27 倍**。

---

## 6. 坑與地雷（避免下個視窗重踩）

1. **OpenAIR 已停站**，別再試。`openair.hosted.york.ac.uk` 與 `openairlib.net` 兩個域名
   都轉到主機商的 `suspendedpage.cgi`。已改用 EchoThief + MIT Reverb Survey。
2. **`assets/reference_irs/` 的 .wav/.jpg 不在 git 裡**（授權未允許再散布，只有 INFO.md 進版控）。
   全新 clone 需照各 `INFO.md` 的網址自行重新下載。
3. **`output/` 只有 `*.md` 進 git**。深度圖/分割圖 PNG、labelmap.npy、IR wav 都不在版控裡，
   全新 clone 需重跑腳本產生。
4. **YouTube 截圖的黑邊會毀掉深度正規化**。走廊那張的左右黑邊 disparity 7.88，
   比畫面內最近的木門 5.96 還高，是全圖最大值來源。**做任何深度處理前要先裁掉 letterbox/UI。**
5. **環景照片不能直接餵透視模型**（見第 2 節）。
6. **`racquetball_court_4` 是必測反例**：8 個場地裡空間最小，殘響卻最長（3.538 s，
   比大洞窟的 1.529 s 長一倍多），因為全是木頭與玻璃硬面。
   任何「空間看起來小就給短殘響」的天真規則在這裡一定爆掉。
7. **玻璃會被深度模型看穿**（淋浴門 disparity 1.28 vs 同距離馬桶 3.01）。
   鏡子這次沒失敗，但 REPORT 主動註明「這是簡單模式的鏡子」，不能當通則。
8. **🔴 絕對不能用「平均 α」算單一寬頻 RT60。** 以地毯房間為例，125 Hz 的 RT60 是 4.093 s、
   4 kHz 只有 0.126 s（差 32 倍）；六段 α 平均後算出的寬頻 RT60 是 0.267 s，
   但實測 T30 是 **4.023 s——差 15 倍**，因為殘響尾巴完全由低頻決定。
   **T-13（聲學參數計算）必須逐頻段獨立算 RT60。** 這是實證，不是規格潔癖。
9. **✅ 已修並經人耳確認（2026-08-18）｜`gen_ir_manual.py --material` 把單一材質套到全部六個面，是不現實的模型。**
   保留全文因為這是「數值驗證抓不到、只有耳朵抓得到」的經典案例。
   修法：T-12 的 `--materials` 逐表面介面（`floor=carpet,walls=gypsum_board`）；
   舊的 `--material` 保留但會印警告。實測 125Hz T30 3.952s→0.748s、低/高頻比 48.8→1.27 倍，
   **使用者 2026-08-18 實聽確認「沒問題」**。
   使用者試聽 carpet 版本後說「像用手拍鐵筒子」——追查證實殘響能量全集中在 30–135 Hz。
   根因：地毯低頻 α 只有 0.02，套到六面等於連天花板牆壁都鋪地毯；真實房間的牆是石膏板，
   125 Hz 的 α = 0.29（板共振吸音體專吃低頻）。量化：低頻 RT60 差 **11.8 倍**
   （4.093 s vs 0.348 s），低頻/高頻比從現實的 ~1 倍變成 **32 倍**。
   **→ T-12（材質模組）必須支援逐表面指定材質**（pyroomacoustics ShoeBox 原生支援 per-wall material）。
10. **小瑕疵待修**（不影響現有功能）：
   - `check_audio.py` 不帶參數時 `exit 0`，應為 `exit 2`
   - `test_segmentation.py` 在所有圖片都失敗時 `exit 0`，應為 `exit 1`（`test_depth.py` 已正確）
11. **✅ 已修（2026-08-18）｜equirect 前處理順序：要先判環景，再決定要不要裁黑邊——順序反了會裁到極點。**
   保留全文是因為這個「靜默失敗」的推理過程本身有價值，不是還沒修。
   修正內容：`is_equirect()` 改吃原圖、判定為環景就完全跳過裁切；
   迴歸測試 `scripts/test_preprocess.py`（對舊碼實測會 exit 1，有真實診斷力）。
   ⚠️ **殘留限制（既有，非本次引入）**：帶 letterbox 外框的 equirect（長寬比因外框超出 ±5%）
   仍會被靜默當成一般照片處理——實測舊碼新碼行為一致。真實 360 檔案通常沒有外框，風險低，
   但建議日後補：非環景裁切後若長寬比落回 2:1 容差內就印警告。
   equirect 影像的第一列就是「天頂那一個點」被拉伸成整列，依定義完全均勻；天底同理。
   若先跑黑邊偵測（用「純色邊框」判定）再判斷長寬比，均勻的極點列會被誤判成黑邊裁掉：
   合成實測裁 3 列 → 赤道在 768px 透視圖中偏移 3.8px；裁 ≥25 列 → 長寬比超出 ±5% 容差
   → **`is_equirect()` 直接翻成 False，整條環景路徑被靜默跳過**，360 圖被當一般照片處理。
   T-10 第一版就是這樣被 Opus 驗證退回的（2026-08-17）；唯一測得到的真實環景
   `SteinmanHall.jpg` 逃過裁切的餘裕剛好是 0.0（spread=3.0，門檻是 `<3.0`），純屬僥倖。
   **→ 判環景要用原圖判斷，且判定為環景就要整個跳過黑邊裁切**（equirect 是完整球面渲染，
   本來就不會有 letterbox）。這也是「安靜地輸出看似合理的錯誤結果」這一類（同地雷 #2 洞二、#9）。
   細節見 [TASKS.md](TASKS.md) T-10 卡「Opus 驗證結果」。

12. **🔴 metric depth 模型有量程上限，超出就安靜地給錯數字。**
   `Depth-Anything-V2-Metric-Indoor-Small` 在 9 張照片上的**最大預測距離全部落在 3.6–19.7 m**，
   從沒超過 ~20m。體育館實際 ~150m，模型全圖最遠只說 3.61m（誤差 −98%）——
   **任何公式都無法從 3.61m 推出 150m**，這不是參數調校問題。
   更要緊的是：**體育館那筆的深度統計完全正常**（clamp 比例 0、百分位平順、離上限很遠），
   只看深度輸出**無法發現它錯了 98%**。這是本專案第三次遇到「安靜地輸出看似合理的錯誤結果」
   （前兩次是地雷 #2 洞二、#9）。
   → 能發現的訊號在**分割**，不在深度：地板可見度 0.0%（vs 浴室 6.8%）、人群佔比、
   以及 T-12 的 CLIP 域外判定。已實作成 `geometry.apply_scene_cue_confidence()` 三條規則。
13. **🔴 CLIP zero-shot 的 top-1 機率不能單獨當信心指標。**
   softmax 在**封閉候選集**上永遠加總為 1，所以模型無法表達「以上皆非」——
   實測 SUV 車內的地板被判成 `curtain_fabric` **信心 0.760**、牆判成 `acoustic_panel` 0.489，
   **兩者都在 0.4 門檻之上，完全不觸發任何警示**。
   調高門檻無效：要 0.8 才擋得住車內，但那會連 corridor 天花板（0.599，判對的）一起擋掉。
   → 解法是在候選集**加入域外選項**（`__vehicle_interior`、`__outdoor_scene` 等），
   讓 softmax 有地方投「以上皆非」。修正後車內判為 `__vehicle_interior` 0.735 ＋明確警示。
   **任何未來要加 zero-shot 分類的地方都要記得這件事。**
14. **⚠️ Sabine 公式與實測 IR 在低頻差 2 倍以上（T-13 必讀）。**
   實測：逐表面 floor=carpet 的 125Hz，Sabine 算 0.348s、**實際量測 IR 是 0.748s**；
   六面全 gypsum 的 125Hz，Sabine 0.282s、實測 **0.772s**。
   但 500Hz 幾乎完全吻合（1.638 vs 1.634），全 carpet 的 125Hz 也吻合（4.093 vs 3.952）。
   用「六面均勻」當對照組確認**與逐表面改動無關**，是 α 高（0.29）時模擬 IR 與 Sabine
   的系統性偏差（小房間低頻非擴散場）。
   → **T-13 若只輸出 Sabine 數字，會與使用者實際聽到的差 2 倍以上**，
   又是「數字合理但東西是錯的」。建議以量測 IR 為準，或兩者並列。

15. **🔴 並列了「目標值」與「量測值」卻沒有程式在比對它們 = 靜默錯誤的溫床。**
   T-21 第一版的 `export_coupled()` 把 `rt60_bands_target_sabine` 與 `t30_measured_s`
   兩排數字**並列寫進 JSON 給人看，但從不比對**。結果巨蛋聲源空間 2kHz 目標 2.966s、
   量測 0.173s（**−94%**）就這樣安靜地過關，`warnings` 欄只有兩條其實是 note 的解析紀錄。
   同一份 JSON 裡連 neighbor_voices 已知的混頻偏差（+27.5%/+114.4%）也一併靜默。
   對照組：T-14 的 `export_ir()` 有跑 `ir_metrics.closed_loop_report()`，同樣的錯誤在
   T-14 就會被攔下來——**差別只在有沒有人寫那一行比對**。
   修正後（T-21 修正輪）比對放在唯一握有單一空間 IR 的地方，超差一律進 `warnings`
   並加 `[空間角色／名稱]` 前綴，JSON 與 CLI 兩邊都出現。
   → **通則：輸出裡凡是同時有目標值與量測值，就必須有程式在比對，不能只是並列給人看。**
   這是本專案「安靜地輸出看似合理的錯誤結果」的第五次（前四次：地雷 #2 洞二、#9、#12、#13）。

16. **🔴 `is_equirect()` 只看長寬比，2:1 的一般透視照會被誤判成 360° 環景（T-17 驗收發現）。**
   `assets/reference_irs/tunnel_to_hell/TunnelToHell.jpg` 是 **2592×1296 = 正好 2.000**
   的一般透視隧道照（`SOURCES.md`／`INFO.md` 都標「一般透視（iPhone 4）✅ 可直接餵模型」）。
   三重佐證它不是環景：① EXIF `ImageLength=1936`（iPhone 4 的 4:3 原始高度）＋
   `Software=Adobe Photoshop CS5` → 是被裁成 2:1 的透視照；② 目視是單點透視消失點；
   ③ SOURCES.md 早就這樣分類。
   但 `preprocess.is_equirect()` 的實作只有一行判斷：
   ```python
   return abs(w / h - 2.0) <= 2.0 * 0.05    # 只看長寬比，不看內容
   ```
   → 這張照片被**靜默地**送進環景路徑做 6 次球面重投影，輸出
   10.48×2.48×6.67m 並拿到**沒有依據的 `confidence: medium`**；
   裁成 2400×1296 破壞 2:1 後走正確的透視路徑，反而誠實標了 `low`。
   **兩條路徑的幾何都錯，但誤判那條錯得比較「有自信」。**
   這是本專案「安靜地輸出看似合理的錯誤結果」的**第六次**
   （前五次：地雷 #2 洞二、#9、#12、#13、#15）。
   ⚠️ 注意這與**地雷 #11 是反方向**——#11 記的是「帶 letterbox 外框的 equirect 被當成
   一般照片」（漏判），這條是「一般照片被當成 equirect」（誤判），先前沒被記錄過。
   ⚠️ **2026-08-31 更新：已開修正卡 T-37（裁決 T-36-A 裁決二）**，主修法＝本條記載的
   極點列均勻度檢查（EXIF/XMP 降為正向輔助）。T-36 天花板模擬另補了量化證據：
   這個 bug 修好後，永遠到不了 materials high 的透視照從 8 張變 9 張。
   → **建議修法**：長寬比之外再加一個極點列均勻度檢查。equirect 的第一／最後一列依定義
   是天頂／天底被拉伸成整列、**完全均勻**，透視照不會——地雷 #11 已經記錄了這個性質，
   只是當時用在反方向。詳見 `output/mvp_acceptance/REPORT.md` §2.5 缺陷 A。

17. **⚠️ `--override-dims` 一律回報 `confidence: high`，但材質仍然是猜的（T-17 驗收發現）。**
   `confidence` 只反映**幾何來源**，卻是使用者唯一看得到的信任訊號。T-17 的五個 manual run
   全部 `high`，但材質肉眼可見是錯的（賣場地板判成 `acoustic_panel`、健身房地板
   `acoustic_panel`、壁球場一面牆 `curtain_fabric`——最後這個單獨毀掉整條 IR，見地雷 #18）。
   → 建議 `confidence` 拆成 `geometry_confidence` / `materials_confidence`，
   或 manual 路徑下取兩者 min()。

18. **🔴 材質誤判是目前 RT60 誤差的主導來源——不是幾何，也不是合成引擎（T-17 實證）。**
   必測反例壁球場，**同一支引擎只換輸入**：
   | run | 尺寸 | 材質 | 聯合帶誤差 |
   |---|---|---|---|
   | 自動 | 16.10×9.39×5.55（估錯） | CLIP：west=`curtain_fabric` | **−50%** |
   | F-09 手動 | **12.19×6.10×6.10（官方標準）** | 同上未變 | **−61%（更差）** |
   | 診斷 | 同上官方標準 | **改對**（floor=wood_panel、其餘 concrete） | **+13%**（125Hz −3.3%） |
   把幾何換成正確值**不但沒好還更差**；只把材質改對就從 −50% 翻成 +13%。
   壁球場裡不存在窗簾，而 `curtain_fabric` 是表中吸音最強的材質之一，一面就足以把
   3 秒殘響吃成 1.4 秒。且該筆 `surfaces_sources` 是正常的 `clip`，**不是 fallback、
   不是 out_of_domain、沒有觸發任何警示**——地雷 #13 加的域外選項救不到
   「在候選集內被判錯」這一類。
   → **任何要改善 RT60 準確度的提案，先問它打的是不是材質。**
     T-17 數據**不支持**優先做「換 Metric-Indoor-Large 深度模型」：
     手動組（近似正確幾何）達標率 20%，並沒有比自動組 22% 好。

19. **🔴 `surfaces.py` 的 ADE20K「語意可信材質」分支是 dead behavior（T-17 診斷確認）。**
   `ADE_TRUSTED_MATERIAL`（`surfaces.py:37-48`）的註解寫「這些不必問 CLIP」、
   迴圈註解（`:238`）再寫一次「有就直接映射，不必問 CLIP」——**但程式每次都問 CLIP**：
   `:244` 無條件呼叫 `classify_region_material()`，`best_trusted` 只被拿去串
   `:262-265` 的 `note` 字串，`:268` 的 `material_id=mid` 永遠是 CLIP 結果。
   全專案 grep：`"ade_trusted"` **只出現在 `:115` 記錄 method 可能值的註解，從未被指派**。
   **執行期重現**（樁掉 seg 與 CLIP，CLIP 固定回 concrete）：windowpane 佔 40% 時，
   floor/ceiling/wall 三個角色的 `material_id` **全部是 concrete**。
   ⚠️ **不要只補一個 `if` 就啟用**：`:239` 的 `trusted_hits` 用的是 `segment_roles()`
   回傳的**全圖** `ratios`（`:154` = `count/total_pixels`），**沒有被角色 mask 限制**。
   上述重現裡 windowpane 全在畫面上半，floor 與 ceiling 的 note 卻都宣稱
   「40% 屬語意可信類別」。**現在的計分方式本身是錯的**，啟用等於引入新錯誤。
   → 家具／人群應該當作等效吸音面積或 occupancy 處理，不是把整面牆改成 `audience_seating`。

20. **🔴 pipeline 已判定不可信仍無條件輸出 WAV（T-17 §7-1 實證後果）。**
   `geometry.py:187-207` 會把體育館降 `low`、把車內標成「不能用 ShoeBox 描述」，
   但 `pipeline.py:225-239` **沒有任何一行檢查 `est.confidence` 或域外狀態**，
   直接聲學→合成→`export_ir()`→wet preview，`:281` 還回傳成功。
   T-17 盲聽的實際後果：體育館（估成 30.8 m³）被聽成車內、車內（估成 332 m³）
   被聽成客廳——**兩筆的防呆規則都正確作動了，產品照樣出貨**。
   → **降信心不等於保護使用者。** 警示只是 JSON 欄位，不是產品防護。

21. **🟠 fallback 材質沒有單一事實來源，四處說法不一致（T-17 診斷確認）。**
   | 位置 | 說法 |
   |---|---|
   | `data/materials.json:10` | `"fallback_id": "generic_wall"` |
   | `config.py:95` | `DEFAULT_WALL_MATERIAL = "gypsum_board"` ← **實際執行值** |
   | `config.py:103` 註解 | 「fallback generic_wall」 |
   | `surfaces.py:167` docstring | 「fallback `generic_wall`」 |
   `classify_region_material()` 三個 fallback 出口全回傳 `config.DEFAULT_WALL_MATERIAL`
   ＝ **`gypsum_board`**。⚠️ 這已經害過人：T-17 REPORT §1.3 首版把 `generic_wall`
   標成 fallback，就是被資料檔與註解誤導。**改的時候要加 invariant test。**
   附帶：`generic_wall` 其實是 CLIP 的正常候選（提示詞 "a plain smooth plastered wall"），
   看到它不代表分類失敗——要看 `surfaces_sources` 才知道是 `clip` 還是 `fallback`。

22. **🟠 ShoeBox 六面模型表達不了室內陳設（T-17 §7-1 sample_4）。**
   臥室被做成 3.56 秒殘響、盲聽被聽成教堂。但四面牆的 CLIP 判定是 `generic_wall`
   且 `source: clip`——**視覺上判得沒錯**，一面臥室牆確實是「plain smooth plastered wall」。
   錯在**床、棉被、窗簾、地毯（α 0.37–0.72）在六面模型裡無處可放**。
   → 這是**模型結構限制，不是辨識準確度問題**，換更好的材質分類器救不到。
   與地雷 #18（CLIP 把壁球場的牆判成 curtain_fabric）是**不同的病因**，不要混為一談。

23. **🟠 材質來源有第四種狀態「無來源」，文件與規則都沒寫（裁決 T-28-A 複驗發現）。**
   角色沒被觀測到時（例：透視照的天花板沒判到），該面保持預設材質但
   `surfaces.sources` **沒有這個面的條目**（CLI 印 `-`）。實測 13 張 78 面裡佔
   **11 面**。對 `compute_materials_confidence()` 的效果：**不觸發規則 1**
   （不逼 low——所以它不是過 gate 的障礙，T-30 的覆寫建議不要把它列進去），
   但**永久阻斷規則 3**（六面全 clip 才能 high）。任何要動信心規則的人必須
   先知道這個狀態存在。
   ⚠️ **2026-08-31 更新：語義已依裁決 T-36-A 定案（維持現狀，議題關閉）**——
   不觸發規則 1、阻斷規則 3、不升格為觸發 low（T-36 模型 A/B 對照實測 13 張
   零差異；升格只會把 DivorceBeach 也擋成 13/13，攔不到任何已知錯誤輸出）。
   無來源面預設值命中率 1/10 屬治療輪／角色觀測覆蓋率議題，不是 gate 議題。

24. **🔴 透視照的 `materials_confidence == "high"` 結構性不可達（裁決 T-28-A 複驗發現）。**
   規則 3 要求「六面皆 clip **且**零 warnings」，但透視照只要判到牆就必然被
   `surfaces_from_preprocess()` 掛上「單張透視照看不到背後的牆，四面牆共用同一個
   材質判定值」的 warning——條件恆假。加上 #23（天花板常無來源），透視照的材質軸
   **永遠 ≤ medium**。這是與 T-28（「任一面 fallback → low」等價永遠 low）**同型的
   「沒量過基準率就寫規則」**：一條從不變化的訊號等於沒有訊號。已裁決材質修正輪
   時一併檢討規則 3，屆時要先量新基準率再定規則。
   ⚠️ 2026-08-31 更新：檢討時點已由裁決 T-33-A 錨定在 T-36（CLIP 診斷）交回時
   就地定案，T-36 的「判定全對天花板模擬」就是為此準備的證據。
   ✅ **2026-08-31 已定案（裁決 T-36-A 裁決一，議題關閉）**：規則 3 維持不動，
   語義正式定調——**high 是「六面皆獨立觀測且模型自信」的等級，本來就只有
   環景輸入拿得到**；透視照 ≤ medium 是誠實的天花板，不是缺陷。「從不變化
   的訊號等於沒有訊號」的批評已有答案：訊號在**輸入型態之間**變化（T-36
   模擬：環景 3 張可達 high、透視 0 張），它告訴使用者「要 high 就拍環景」。

25. **🟠 單一 RT60/T30 數字會高估兩個版本的「聽起來差多少」（T-33 §6.1 實證）。**
   臥室 with/without 陳設兩檔 RT60 差 2.6 秒，使用者實聽只差「頂多 0.5 秒」——
   查核確認**使用者沒聽錯**：差距主要落在 −45dB 以下的深尾（接近或低於一般播放
   環境的背景噪音），可聽門檻（−30~−45dB）衰減時間差只有 0.3–0.8 秒。RT60 量測
   本身沒錯（管線與 T-17 逐位元一致），錯的是拿它當感知差距的代理。
   → **凡是要調「聽感強度」類的參數（陳設效果、damping 等），必須用可聽門檻
   衰減時間與 RT60 並列交叉檢查**——已寫死進裁決 T-33-A 裁決 A 的終止條件。

26. **🔴 `ratio × S_total` 像素佔比換算公式的準確度依鏡頭情境南轅北轍（T-33 §4.2）。**
   同一條公式：臥室（近景、少量大型物件——床 21.2%）方向正確；Steinman Hall
   （遠景、大量重複小物件——排排座椅 32.8%）**系統性高估**（座椅只佔地板一部分、
   不佔牆與天花板，但公式把像素佔比直接當成佔六面總表面積的比例），把 T-17
   唯一接近達標的場地從 4/5 拖到 1/5，四個頻段全部翻成方向相反的不通過。
   目前**沒有任何機制區分兩種情境**（cap=0.5 擋不住這型）；Restaurant 自動組
   −4%→−41% vs 手動組 +80%→+32% 的反向結果另證明效果與 S_total 誤差**疊乘**。
   → 陳設機制已因此改預設觀測模式（裁決 T-33-A）；任何要重新啟用套用的提案，
   必須先解這個失效模式（文獻方向：座位區以地板面積換算，Beranek 觀眾席法），
   並過裁決 A 寫死的終止條件。

### ⚠️ 數值驗證抓不到的錯誤

地雷第 9 條是這一輪最值得記住的教訓：那個錯誤的 RT60（4.023 s）**通過了 WORKFLOW §5 的全部三層檢查**
——落在合理區間 0.1–12 s、α 全在 0–1、無假實作、無 hardcode。
但模型本身是錯的，而且錯得離譜（低頻差 11.8 倍）。**是使用者的耳朵抓到的。**

**Phase 1 的驗收不能只靠數值範圍檢查。** 每次改動 IR 生成邏輯後，
都應該產生試聽檔請使用者實際聽過（`convolve.py` 跑一下就有）。
數字合理 ≠ 聽起來對。

### 給用 workflow 跑多 agent 的視窗

若你禁止 subagent 執行 git 與修改 TASKS/DEV_LOG/TODO（建議這樣做，避免並行衝突與造假），
**驗證者會回報「收工程序沒做、沒 commit」**——那是它不知道你的設計，屬誤判，
主控端自己核對後補做收工程序即可。本輪兩次都出現這個假陽性。

---

## 7. 標準交接流程

```
【結束舊視窗】
  貼：「執行 WORKFLOW.md 第 4 節收工程序」

【已完成 — T-34 ✅ 通過】（Sonnet 執行 + Opus 驗證，2026-08-31）
  gate 訊息補洞：規則 2（六面全同退化規則）觸發且無 fallback/out_of_domain 面時，
  補印專屬導引＋六面 `--override-material` 骨架（先前只剩 `--force-low-confidence`
  一條路）；新增 geometry=low 分支的測試覆蓋。gate 判定條件零改動。
  Opus 驗證通過：十套測試 EXIT=0、六條交付 IR MD5 驗證者重生比對全相符、
  `surfaces.py` 零 diff、`pipeline.py` 純新增 21 行零刪除、真實輸入複現 exit 3
  且不留輸出目錄；【E】對舊碼實測 fail、【F】以突變測試證明非空測試。
  附兩則文件修正建議（TODO 措辭已就地修正；共同鐵則 5 措辭請 Fable 後續調整）。
  詳見 TASKS.md T-34 卡「Opus 驗證紀錄」。

【已完成 — T-35 ✅ 通過】（Sonnet 執行、Opus 驗證，2026-08-31）
  陳設改預設觀測模式（裁決 T-33-A 裁決 A 執行卡）：`cli.py` 新增 `--furnishings`
  旗標（與 `--no-furnishings` 互斥）；`pipeline.run_photo()` 改三態——預設偵測
  照跑但不套用（`compute_acoustics(..., furnishings=None)`，與 `--no-furnishings`
  逐位元等價）、`--furnishings` 套用（現行舊行為）、`--no-furnishings` 完全不
  偵測。`analysis.json` 的 `furnishings` 鍵三態對應三種 dict，觀測模式不含
  聲學換算欄位。gate 判定段一行未動（改動全在 gate 之後）；`acoustics.py`／
  `surfaces.py`／`furnishings.py` 零改動。
  自我檢查：十套測試 EXIT=0；六條交付 IR MD5 全部逐位元相同（T-14 自動驗證＋
  T-20/T-21 手動重生比對）；新測試【D】對 `git stash` 出的舊碼實測 fail；
  bedroom_ai_generated 三態實跑核對 T-33 記錄的兩組 RT60 數字逐位元相同；
  bathroom_tiled 三態防濫殺對照聲學全同。詳見 TASKS.md T-35 卡「交接筆記」。
  Opus 驗證通過（2026-08-31，全部指令驗證者自己重跑）：十套測試 EXIT=0、六條
  交付 IR MD5 重生比對全相符、`acoustics.py`／`surfaces.py`／`furnishings.py`／
  `ir_metrics.py` 零 diff、gate 段零改動；**最關鍵的一項**——bedroom 預設模式與
  `--no-furnishings` 的 `ir_mono.wav` MD5 逐位元相同（`989b9f35…`，比卡片要求的
  RT60 相同更嚴格），`--furnishings` 為 `0cdeb64c…`＝T-33 預設組；bathroom_tiled
  三態 MD5 全同；未套用時陳設訊息全走 notes 不走 warnings；【D】對舊碼實測 fail
  （驗證者用 `git worktree` 開舊碼重現）。詳見 TASKS.md T-35 卡「Opus 驗證紀錄」。
  ⚠️ 驗證者附一則**交 T-36 帶走的提醒**：`scripts/t33_material_round_tables.py`
  的「套用組」靠舊預設，本卡之後那一組會跑成觀測模式並在讀 `A_by_band` 時
  `KeyError`；T-33 已結案不影響驗收，但 T-36 若沿用該腳本樣式，套用組要顯式加
  `--furnishings`。

【已完成 — T-36 ✅ 通過（Opus 複驗 2026-08-31）＋裁決 T-36-A 已下（Fable，2026-08-31）】
  T-36：13 張×78 面 ground truth（使用者逐面確認，47 面人工覆寫）＋CLIP 準確度
  量測（真判定 11/21＝52.4%、非 proxy 51.7%、proxy 6.2%、floor 角色最差 30.8%）
  ＋天花板模擬（判定全對仍只有 3 張能 high、8 張透視結構性不可達＝地雷 #24
  實證、CathedralRoom 全對仍因規則 2 停 low）。中間退回一輪（按角色正確率／
  地雷 #16 誤述／無來源模擬敘述），修正後複驗通過。
  裁決 T-36-A：gate 規則就地定案（全部維持原樣、議題關閉）＋開 Phase 1.9
  CLIP 治療輪＋陳設公式修正輪不開。全文見 TASKS.md T-36 卡尾。

【已完成 — T-36 文件修正 ✅（Sonnet，2026-08-31）】
  照 TASKS.md Phase 1.9 節「T-36 文件修正」執行 T-36 複驗開出的 6 項非退回
  事項（詳細執行紀錄見 TASKS.md T-36 卡尾），十三套測試與六條 IR MD5 全綠、
  `src/` 零改動。

【已完成 — T-37 ✅ 通過】（Sonnet 執行，Opus 驗證，2026-08-31）
  地雷 #16 修正：`preprocess.is_equirect()` 加極點列均勻度檢查（長寬比 2:1±5%
  AND 灰階首/尾列相鄰像素絕對差均值 < `config.EQUIRECT_POLE_DIFF_THRESHOLD`
  = 1.2；門檻由 `scripts/t37_rebaseline.py` 程式量測，4 張真環景 max 0.4859、
  TunnelToHell 4.5149，兩側餘裕 2.47x／3.76x）。TunnelToHell.jpg 修正後正確
  判為 False（改走透視路徑，`geometry_confidence` medium→low，未比原本更
  自信）；4 張真環景維持 True；其餘 12 張三軸 confidence／gate 與 72 面材質
  判定逐值不變。Opus 驗證通過（詳見 TASKS.md T-37 卡「Opus 驗證紀錄」）。

【已完成 — T-40 🔵 待驗證】（Sonnet 執行，2026-08-31）
  評測快取指紋與自動失效（插卡 1/4）：新增 `scripts/eval_cache.py`（純函式
  模組——`compute_fingerprint()`／`diff_fingerprint()`／`load_or_run()`／
  `FrozenBaselineError`／FREEZE_MANIFEST 產生與驗證），接上
  `scripts/t36_clip_accuracy.py`（新增 `--out-dir`）。六類指紋（來源圖片／
  三個 `src` 檔／兩個 `data` 檔／模型 id／CLIP 門檻／評測模式）任一改變即
  觸發失效；指向非凍結目錄自動重跑，指向 `output/clip_accuracy/`（T-36
  凍結基線）一律 hard fail，絕不自動重跑覆寫。新增
  `output/clip_accuracy/FREEZE_MANIFEST.md`（71 個既有檔案 sha256 清單，
  鐵則 4 唯一允許例外）。指紋計算改惰性（`fingerprint_fn`）以避免舊格式
  快取的 hard fail 判定意外要求讀取可能不存在的來源圖片。
  舊碼最小重現（`git worktree` 開 T-37 後的舊碼＋竄改一張照片的快取內容）
  證實：舊碼 exit 0 印成功但報告數字被污染；新碼同情境 hard fail 並點名
  「快取內無 fingerprint 欄位」。零 `src/`／`data/` 改動；六條交付 IR MD5
  逐位元相同；14 支測試（含新增 `test_eval_cache.py`）全 exit 0。
  ⚠️ 副作用：`t36_clip_accuracy.py` 不帶參數執行從此永遠 hard fail（13 份
  既有快取是舊格式且不許被補寫）——刻意設計，往後治療評測要用 `--out-dir`。
  詳見 TASKS.md T-40 卡「交接筆記」。

【現在該做的 — 開 Opus 視窗驗證 T-40】（模型選 Opus）
  依 WORKFLOW.md 第 5 節驗證標準審查 T-40。重點：六類指紋是否真的逐項擾動
  都觸發失效（`test_eval_cache.py` 少一類＝退回）；FREEZE_MANIFEST 與凍結
  基線既有檔案 hash 是否逐項相符；是否存在任何「指紋不符仍印成功」的路徑
  （含 `--fresh` 以外的旁路）；`src/`／`data/` 是否零 diff；舊碼最小重現是否
  真的附了實測輸出（可用 `git worktree` 重現驗證者自己再跑一次）。通過後開
  Sonnet 視窗執行 T-41。

【已完成 — T-40 ✅、T-41 ✅ 皆通過（Opus，2026-08-31）】
  T-41：透視照 SegFormer 去重（pipeline.py +2 -5），13 張基線全 25 鍵零漂移、
  六條交付 IR MD5 未變。詳見 TASKS.md T-41 卡。

【已處理 — T-38 拆卡改版（Fable，2026-09-01）】
  T-38 實際已跑 round0～round5 六個完整輪次＋round6 中止（6/13 張、無
  summary、標 interrupted 不納入比較），無一輪同時達成三門檻（基線 31/76、
  最佳 round4 僅持平）；round1～round5 提示詞字串已遺失只剩 hash（標
  「不可恢復」，不得倒填）。根因＝原卡把模型實驗寫成必達工程卡。拆成
  T-38A（可重現評測與實驗紀錄）→ T-38B（有界實驗，最多 4 輪，否定結果
  是合法結論）。T-41 維持 ✅ 不退回。⚠️ 工作樹未提交的 surfaces.py／
  t38_treatment_eval.py／output/clip_treatment/ 是實驗證據，T-38A 依步驟
  記錄前不得清除。裁決全文見 TASKS.md T-38 卡。

【已完成 — T-38B ✅ 通過（Opus 驗證 2026-09-01）＋裁決 T-38B-A 已下（Fable，2026-09-01）】
  T-38B：四輪預算跑滿（round7 改 concrete → round8 加 acoustic_panel →
  round9 加 curtain_fabric → round10 依 PLAN §4 規則再改 concrete），對
  round0_baseline（31/76、4/13、9）無一輪同時達成三門檻且逐輪劣化
  （in-set 誤判 9→9→18→23→26）；不採用任何改動，`surfaces.py` 還原
  baseline（Opus 全新無快取 13 張重跑證實與基線逐行相同）。否定結論＝
  合法研究結論＝✅。
  裁決 T-38B-A：兩條出口都要，順序 **T-39（擴候選）→ T-44（role-aware
  候選子集，新卡）**；兩卡驗收改為工程完成／產品採用分離＋預算寫死＋
  否定結論算通過；T-39 比較基線換成 round11_remap_baseline（兩段式基線）；
  鐵則 6 對 T-44 開限定例外（只准動 classify_region_material() 介面與
  候選集選取）；陳設公式修正輪不插隊。全文見 TASKS.md T-38B 卡尾。

【現在該做的 — 開 Sonnet 視窗執行 T-39】（需使用者 10 分鐘級參與）
  貼 HANDOFF_T39.md §6 的 T-39 Prompt。
  之後依序 T-39 → T-44（role-aware 候選子集）→ T-42（gate 交易式輸出與
  舊產物 archive 隔離）→ T-43（analysis.json 生成指紋＋t17_blind_test
  溯源驗證）。插卡裁決與各卡全文見 TASKS.md。

【Phase 1.9 跑完後 — 回 Fable 收尾複評】（模型選 Fable）
  帶 T-37/T-38A/T-38B/T-39/T-44 的 REPORT 與基線變化表＋插卡輪 T-40～T-43
  的 REPORT，一次議決：治療效果總結（對照理論上限 7/13）、要不要開
  MINC/DMS 模型卡、要不要開陳設公式修正輪（裁決 T-36-A 裁決三的重啟
  評估點；裁決 T-38B-A 確認不插隊、在此評估）、T-17 複驗時機
  （硬性前置：任何新的正式盲聽必須在 T-42＋T-43 ✅ 之後）。
```

### ⚠️ 給下一個視窗的提醒

- **Phase 1.7／1.8／1.9 全輪紅線（共同鐵則 6，三輪相同）**：gate 判定規則
  （`compute_materials_confidence()` 與 `run_photo()` 的觸發／放行條件）與
  scene_cues 段**一行都不許動**；陳設資料不得餵進任何信心軸——觀測模式下也一樣，
  偵測結果只進報告欄位。**gate 規則已於 2026-08-31 依裁決 T-36-A 就地定案
  （維持原樣、議題關閉）**；未來任何調整＝新的 Fable 裁決，必附四樣證據
  （新基準率實測／被放行案例清單／其中 T-17 已知錯誤輸出佔比／臥室續擋驗證）。
  Opus 驗證用六條交付 IR MD5＋`test_output_gate.py` 既有案例抓偷改。
  ⚠️ Phase 1.9 差異：13 張 materials 軸基準率**允許因治療而動**（這是本輪
  目的），但要有程式生成的基線變化表；CLIP fallback 門檻 0.4 也不許動。
- **T-31 的 `ade_id` 不可直接信任**（規劃者憑文件寫的）：`test_furnishings.py`【C】
  用 segmenter 的 id2label 實測驗證，抓到不符就修 json 的 id，不是改測試。
- **全圖像素比例在陳設偵測是語義正確的用法**（陳設是獨立區域）——與地雷 #19
  的錯誤（拿全圖比例替單一角色計分）不同型，不要「順手修正」。
- **文字／複合管線不啟用陳設**：`compute_acoustics()` 的 furnishings 預設 None，
  None 時 `as_dict()` 輸出必須與現行逐位元相同——這就是六條 MD5 不變的機制。
- **重生照片 IR 要知道 gate**（REPORT §7 已註記）：2026-08-30 後重跑要加
  `--force-low-confidence`，或依第 5 節用 `--override-material` 走正規出口。
- **任何再調 gate 門檻的提案**：T-33 的新基準率已出來（見
  `output/material_round/REPORT.md`）——**13/13 gate 基準率與裁決 T-28-A 複驗
  完全沒變**（架構上必然，鐵則 6），materials_confidence 12/13 low 一個都沒改善，
  所以現在也還沒有實證支持調鬆門檻；臥室那筆必須仍被擋住。
- **T-33 的意外發現（已裁決處理，T-35 已落地）**：陳設等效吸音對 §7-2 式達標率
  是**淨負面**（自動組 22%→10%、手動組 20%→12%，根因見地雷 #26）。裁決 T-33-A
  定案改**預設觀測模式**，T-35（🔵 待驗證）已把程式改成三態：預設＝偵測照跑但
  不套用（聲學數字與 `--no-furnishings` 逐位元相同＝T-17/T-33 `--no-furnishings`
  基準）；`--furnishings`＝套用（＝舊預設行為＝T-33 預設組數字）；重跑照片 IR
  比對數字時要知道自己指定的是哪一態。
- 新增 zero-shot 分類的地方必讀地雷 **#13**（softmax 無法表達「以上皆非」）；
  任何「目標 vs 量測」並列的輸出必讀地雷 **#15**；動信心規則必讀地雷 **#23／#24**。
