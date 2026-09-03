# T-44 REPORT — role-aware 材質候選子集（正面結論，已採用）

⚠️ 2026-09-03 裁決 T-45-A：產品採用暫停，`pipeline.py` 預設改回
`role_aware=False`（T-46）；本報告的量測數據與 round17 結論不改。

## 性質聲明（裁決 T-38B-A，寫在最前面）

本卡與 T-38B／T-39 同型：「跑滿預算、誠實報告」＝工程完成（✅ 的充分條件），
「role-aware 沒有改善」原本也會是合法的實驗結論。**本卡的結果是本輪治療系列
（T-38B → T-39 → T-44）第一次拿到正面結論**：對 `round11_remap_baseline`
同時達成 §5 的三個產品採用門檻，`pipeline.py` 已改為 `role_aware=True`。
但正面結論不代表沒有代價——本報告第五節記錄了一個必須誠實揭露的殘留風險
（`bathroom_tiled` 的 gate 從擋變放，材質判定其實是錯的），供 Opus／Fable
判斷是否需要後續處理。

## 一、依據與分區表（工程完成的第一部分）

依 [PLAN_T44.md](PLAN_T44.md) §1，`classify_region_material()` 新增 `role`
參數，`analyse_image()`／`surfaces_from_preprocess()` 新增 `role_aware`
參數（預設 `False`，逐位元等價於 T-44 之前——見
[scripts/test_t44_role_partition.py](../../scripts/test_t44_role_partition.py)
的 role=None 不變量測試）。分區表單一事實來源在
[surfaces.py 的 `ROLE_MATERIAL_CANDIDATES`](../../src/image_reverb/surfaces.py)，
提示詞字串（既有 12 條）全程一字不動。

**最終狀態的分區表**（round17，見下方§三決策鏈）：

| 角色 | 候選子集 | 說明 |
|---|---|---|
| floor | `concrete`／`carpet`／`wood_panel`／`gypsum_board`／`marble`／`audience_seating`（6 種） | round15 首輪設計，round16 曾加回 `generic_wall` 但證偽，round17 撤銷 |
| ceiling | `concrete`／`curtain_fabric`／`generic_wall`／`gypsum_board`（4 種） | round15 首輪設計，全程未調整 |
| wall | 全域 12 種（未收窄，等同不 role-aware） | round16 起還原，round15 首輪的 9 種收窄對 wall 淨負面 |

4 個 OOD 候選（`__vehicle_interior`／`__outdoor_scene`／`__object_closeup`／
`__person`）三個角色全程保留，未被收窄。分區完整性（子集必須涵蓋該角色
ground truth 實際出現的所有材質）與「不新增候選字串」兩項規則的程式化
驗證見 `test_t44_role_partition.py`【1】【5】，`role=None` 逐位元等價見【2】【3】。

## 二、比較基線

`round11_remap_baseline`（T-39 重對映後、候選未動的最終狀態）：
overall **30/76**、floor **4/13**、ceiling **3/11**、wall **23/52**、
非 proxy **30/63**、in-set 誤判 **9**。不是 `round0_baseline`，也不是
已否定的 `round12`～`round14`。

## 三、逐輪發生了什麼（誠實記錄，含機制診斷）

### round15_role_partition —— 首輪分區表：floor／ceiling 有進展，wall 淨負面

依 PLAN_T44.md §1 的最小分區表（每角色只留 ground truth 實際出現過的材質）：

| 指標 | round11 | round15 | 變化 |
|---|---:|---:|---|
| overall | 30/76 | 29/76 | **-1** |
| floor | 4/13 | 5/13 | +1 |
| ceiling | 3/11 | 4/11 | +1 |
| wall | 23/52 | 20/52 | **-3** |
| in-set 誤判 | 9 | 15 | **+6** |

逐面核對：3 面修正（`stairwell_tiled.floor`／`stairwell_tiled.ceiling`／
`CathedralRoom.floor`）、4 面倒退（`bathroom_tiled.floor`、
`SteinmanHall` 三面牆）。三個產品採用門檻只有「floor 上升」達成。

**機制診斷（不是猜測）**：CLIP 對每個候選的原始 logit 不受候選集大小影響
（各候選字串各自獨立跟裁切圖算相似度），排除候選只會讓「剩下的候選」被
重新正規化——倖存候選之間的相對排序不變，但絕對機率一起被推高。這個機制
對本卡目標型的搶答（跨角色偷渡）是好事，但對 round11 裡「fallback 預設值
剛好等於 ground truth」的**同意偏誤巧合**面（`bathroom_tiled.floor`、
`SteinmanHall` 三面牆）是壞事：排除候選讓原本次高的候選被推過門檻，從
「誠實的不知道」變成「自信的答錯」。這幾個搶答者（`carpet`／`acoustic_panel`／
`curtain_fabric`）依分區完整性鐵則本身就是該角色的合法材質（`carpet` 是
`car_interior_suv.floor`／`site_photo_department_store.floor` 的 gt；
`acoustic_panel` 是 `car_interior_suv.east/west` 的 gt；`curtain_fabric`
是 `SteinmanHall.west` 自己的 gt），**不能被排除**——這是角色內合法材質
互搶，本卡設計的跨角色收窄機制對這型搶答沒有槓桿。

### round16 —— wall 還原：完全命中；floor 加回 generic_wall：證偽

依 §7 決策（完整性鐵則規定的是下限不是上限，多留候選不違規）：
1. **wall 整組還原成全域 12 種**——假設完全證實：`ROLE_MATERIAL_CANDIDATES["wall"]`
   還原後與 `role=None` 的候選字典內容與插入順序逐字相同，softmax 值不受
   影響，wall 角色 52 面逐面核對與 round11 **逐位元相同**。
2. **floor 加回 `generic_wall`**——假設部分證偽：`generic_wall` 不是單純
   「稀釋」`carpet`，而是自己信心夠高**直接接管**成新的錯誤冠軍——
   `bathroom_tiled.floor` 仍錯（`generic_wall` 0.4195，gt=`gypsum_board`），
   且反過來讓 round15 唯一命中的 `stairwell_tiled.floor` 倒退
   （`marble` 0.429→0.2466，`generic_wall` 0.4257 接管，錯）。

| 指標 | round11 | round16 | 變化 |
|---|---:|---:|---|
| overall | 30/76 | 31/76 | +1 |
| floor | 4/13 | 4/13 | 持平（未上升） |
| ceiling | 3/11 | 4/11 | +1 |
| wall | 23/52 | 23/52 | 持平（逐位元＝round11） |
| in-set 誤判 | 9 | 9 | 持平 |

三個產品採用門檻：①overall 上升 ✅；②floor 上升 ❌（持平不算上升）；
③in-set 不上升 ✅。只差 floor 一項。

### round17（最終輪）—— 撤銷 floor 的 generic_wall：三門檻同時達成

依 §8 決策：撤銷 round16 對 floor 的改動（`generic_wall` 從未是任何一面
地板的 ground truth，加回它換來新錯誤冠軍而非稀釋，應撤銷），floor 還原
成 round15 的 6 種候選；wall 保留 round16 的還原（全域 12 種）；ceiling
全程不動。

跑之前先用 round15／round16 的既有快取資料唯讀交叉推算預期值（floor 用
round15 資料、wall 用 round16 資料、ceiling 不變，三角色候選集互相獨立，
可以這樣推算），round17 實測與推算**逐項相符**：

| 指標 | round11 | round17 | 變化 |
|---|---:|---:|---|
| overall | 30/76 | **32/76** | **+2** |
| floor | 4/13 | **5/13** | **+1** |
| ceiling | 3/11 | **4/11** | **+1** |
| wall | 23/52 | **23/52** | 持平（逐位元＝round11） |
| in-set 誤判 | 9 | **8** | **-1** |

三個產品採用門檻**同時達成**：①overall 32>30 ✅；②floor 5>4 ✅；
③in-set 誤判 8<9（不上升，實際下降）✅。

**逐面完整清單**（78 面裡有變動的 10 面，其餘 68 面逐位元不變）：

| 照片 | 面 | ground truth | round11 | round17 | 對錯變化 |
|---|---|---|---|---|---|
| bathroom_tiled | floor | gypsum_board | gypsum_board（fallback） | carpet（clip） | **倒退** |
| stairwell_tiled | floor | marble | gypsum_board（fallback） | marble（clip） | **修正** |
| stairwell_tiled | ceiling | generic_wall | gypsum_board（fallback） | generic_wall（clip） | **修正** |
| arena_ntsu_linkou | ceiling | unknown（排除） | audience_seating（clip） | curtain_fabric（clip） | 不計分 |
| car_interior_suv | floor | carpet | curtain_fabric（clip） | gypsum_board（out_of_domain） | 持平（皆錯，換答案） |
| CathedralRoom | floor | concrete（proxy） | gypsum_board（fallback） | concrete（clip） | **修正** |
| site_photo_department_store | floor | carpet | acoustic_panel（clip） | gypsum_board（out_of_domain） | 持平（皆錯，換答案） |
| site_photo_department_store | ceiling | gypsum_board | gypsum_board（fallback） | gypsum_board（clip） | 持平（皆對，來源變誠實） |
| site_photo_gym | floor | rubber_flooring（結構性不可達，見下） | acoustic_panel（clip） | concrete（clip） | 持平（皆錯，換答案） |
| TunnelToHell | ceiling | concrete | gypsum_board（fallback） | gypsum_board（out_of_domain） | 持平（皆錯，換答案） |

淨變化＝3 修正 − 1 倒退 ＝ +2，與 overall 30→32 完全對帳。

## 四、誠實的預期管理兌現情況（對照 PLAN §0／§6 事前寫死的假設）

- ✅ `bedroom_ai_generated` 四面牆的牆對牆混淆——依 PLAN §0 明文預期不治，
  round17 逐位元核對 `bedroom_ai_generated` 全部 6 面與 round11 完全相同
  （見第五節共同鐵則 7），**確實未治，符合預期，不是本卡失敗依據**。
- ✅ `bathroom_tiled.ceiling`／`site_photo_gym.ceiling`（分割階段沒有
  ceiling 角色像素，CLIP 從未被呼叫）——結構性不可達，round17 的
  `detail.json` 對這兩面依然完全沒有 `ceiling` 鍵，未計入預期收益，
  也沒有動分割邏輯。
- ✅ `site_photo_gym.floor`（gt=`rubber_flooring`，T-39 未採用的候選，
  12-候選宇宙內結構性判不到）——round17 仍錯（換成 `concrete`），符合
  「不計入預期收益」的預先聲明。
- 🟡 PLAN §6 預測的兩個「最強機會」（`car_interior_suv.floor`／
  `site_photo_department_store.floor` 的 `carpet`）**沒有兌現**——兩者都
  沒有翻正，而是從「clip 自信答錯」變成「out_of_domain」（仍錯，只是換了
  形式）。PLAN 當時就承認這兩個方向「不確定，需要真跑」，如實記錄：
  預測方向對了一半（候選被排除後確實不再是原搶答者贏），但沒猜中誰會贏。
- 🟡 PLAN §6 預測的風險面（`bathroom_tiled.floor`／`SteinmanHall.floor`）
  ——`bathroom_tiled.floor` 命中（真的倒退了），`SteinmanHall.floor`
  沒有倒退（fallback 各輪都維持 gypsum_board=gt）；但**round15 額外
  發現了一個 PLAN 沒預測到的同型風險**：`SteinmanHall` 的三面**牆**
  （不是 PLAN 猜的 floor）也是同一種「fallback 巧合答對被拆穿」——
  這面不在 PLAN 事前列表裡，是跑完才發現的，如實記錄，round16 已用
  wall 整組還原解決。

## 五、⚠️ 已知殘留風險（必須誠實揭露，供 Opus／Fable 判斷是否需後續處理）

**`bathroom_tiled` 的 overall gate 從 BLOCK 變成 pass**（`materials_confidence`
`low`→`medium`），但 floor 的實際判定是**錯的**（`carpet`，gt=`gypsum_board`）。

機制：round11 裡 `bathroom_tiled.floor` 是 `fallback`（CLIP top-1 機率不足
門檻，誠實承認不知道，材質預設值剛好等於 ground truth，`compute_materials_
confidence()` 規則 1 命中「任一面 fallback → low」，`_overall_confidence()`
取幾何 medium 與材質 low 的較低者 → `low` → **擋下輸出**）。round17 裡同一面
變成 `clip`（真的判出一個答案，只是判錯了），不再觸發規則 1，六面也未全同
（規則 2 不命中），落入規則 4「其餘情況 → medium」，`_overall_confidence()`
變成 `medium`／`medium` → `medium` → **放行輸出**。

**13 張裡只有這一張出現這個型態**（見下方共同鐵則 8 全表）；`bedroom_ai_
generated`（共同鐵則 7 明文點名的紅旗案例）在 round17 逐位元核對後與
round11 完全相同，**未觸發**「從擋變放」（詳見下節），依卡片明文規則本卡
**未違反任何一條寫死的紅線**。但 `bathroom_tiled` 這個新出現的型態與
`bedroom` 紅旗背後的精神完全一樣——**材質判定的信心分數變高，但判定本身
沒有變準**，這正是本卡機制本身（候選集收窄→softmax 濃縮→更容易越過信心
門檻）在「fallback 預設值剛好答對」這類面上的必然副作用，不是實作疏漏。

**本卡的立場**：三個產品採用門檻是卡片明文寫死、PLAN 跑之前就承諾的驗收
標準，round17 三項都達成，依卡片規則本卡判定為**採用**；但這個殘留風險
不應該被本報告的正面結論蓋過去，**明確建議 Fable 收尾複評時考慮是否要
開一張新卡**（例如：`compute_materials_confidence()` 規則 4 的 `medium`
是否該區分「多面 clip 但候選集被收窄過」與「多面 clip 且候選集未收窄」，
或者乾脆的做法是把這類新增風險交給未來的 MINC/DMS 材質模型卡一併處理）。
本卡範圍紅線禁止動 `compute_materials_confidence()`／gate（共同鐵則 6），
所以本卡**不**在這裡動手修，只誠實記錄。

## 六、共同鐵則自我檢查

1. **測試套件全部 exit 0**：全部 18 支 `scripts/test_*.py`（含新增的
   `test_t44_role_partition.py`）逐支執行，全部 EXIT=0。
2. **六條交付 IR MD5 逐條比對**：T-14 兩條經 `test_ir_synth.py`【6】全過；
   T-20 兩條（`text_bathroom`／`text_church`）重新生成比對
   `2adbaa75eb698772a8c9aa693179ec47`／`2dd19b6e6d351d713887636fe45cd67e`，
   逐位元相符；T-21 兩條（`neighbor_voices`／`stadium_corridor`）重新生成
   比對 `9a94ffdf5d8295aee7889729c39c9cd8`／`a1c21bcc3fd9aa3480df203a89c8cd05`，
   逐位元相符。全部在 role_aware=True 採用**之後**重新生成驗證（文字／
   複合管線不經 CLIP，理論上不受影響，實測也確實不變）。
3. **`ir_metrics.py` 零 diff**：`git diff 63c536c HEAD -- src/image_reverb/ir_metrics.py`
   輸出 0 行。
4. **不許動的檔案／目錄**：`SPEC.md`／`ROADMAP.md`／`WORKFLOW.md`／
   `output/mvp_acceptance/`／`output/material_round/`／`output/clip_accuracy/`
   逐項核對 `git diff --stat` 為空。
5. **新測試診斷力**：`test_t44_role_partition.py` 對 T-44 之前的舊碼實測
   `AttributeError: module ... has no attribute 'ROLE_MATERIAL_CANDIDATES'`
   （`git stash` 還原後實跑，見開工時的驗證紀錄），fail 明確。
6. **gate／`compute_materials_confidence()`／scene_cues／門檻 0.4 零改動**（
   共同鐵則 6 的 T-44 限定例外只涵蓋 `classify_region_material()` 介面與
   候選集選取）：`git diff 63c536c HEAD -- src/image_reverb/config.py` 為空；
   `compute_materials_confidence()` 函式本體逐行核對與改動前相同（第五節
   已記錄它的**行為**因為輸入資料變了而不同，但**規則邏輯一行沒動**——
   這正是第五節殘留風險的性質：不是規則變寬鬆，是資料分佈的自然結果）。
7. **臥室紅旗**：`bedroom_ai_generated` 逐位元核對——round17 的 `surfaces`／
   `sources` 與 round11 **完全相同**（`{'west': 'generic_wall', 'east':
   'generic_wall', 'south': 'generic_wall', 'north': 'generic_wall', 'floor':
   'gypsum_board', 'ceiling': 'gypsum_board'}`），`materials_confidence`
   round11=`low`、round17=`low`，overall gate 兩輪皆 `low`（BLOCK），
   **未從擋變放**。（機制：floor 用 round15/17 的 floor 候選集，round11
   即已是 fallback，此配置未變；ceiling 結構性不可達不受影響；wall 用
   round16 起還原的全域 12 種，逐位元＝round11——三個角色的候選集變動
   沒有一項touch到 bedroom 任何一面的判定路徑。）
8. **13 張基線變化表**（本卡動 `src/`，依鐵則原文全量產表）：

   | 照片 | geometry | materials（round11） | materials（round17） | overall（round11） | overall（round17） | surfaces 有變動 |
   |---|---|---|---|---|---|---|
   | bathroom_tiled | medium | low | **medium** | low | **medium** | 是（見第五節） |
   | bedroom_ai_generated | medium | low | low | low | low | 否 |
   | stairwell_tiled | medium | low | low | low | low | 是（2 面修正） |
   | arena_ntsu_linkou | low | low | low | low | low | 是（1 面，unknown 排除） |
   | car_interior_suv | low | low | low | low | low | 是（1 面，皆錯換答案） |
   | CathedralRoom | medium | low | low | low | low | 是（1 面修正） |
   | DivorceBeach | low | medium | medium | low | low | 否 |
   | site_photo_department_store | medium | low | low | low | low | 是（2 面，1 皆錯換答案/1 皆對來源變） |
   | site_photo_gym | low | low | low | low | low | 是（1 面，皆錯換答案） |
   | site_photo_restaurant | low | low | low | low | low | 否 |
   | RacquetballCourt4 | medium | low | low | low | low | 否 |
   | SteinmanHall | low | low | low | low | low | 否（wall 已還原＝round11） |
   | TunnelToHell | medium | low | low | low | low | 是（1 面，皆錯換答案） |

   **漂移逐張有原因**（見上表與第三節逐輪記錄）；除 `bathroom_tiled`
   （第五節已誠實記錄的殘留風險）外，其餘 12 張的 gate 決策（BLOCK/pass）
   全部與 round11 相同，即使 `surfaces` 內容有變動。

## 七、門檻敏感度分析（表 7' 型，對 floor／wall／ceiling 三個角色分別重跑）

依 PLAN §4，最終輪（round17）跑了 `--role-sensitivity`，完整表見
[`rounds/round17/tables.md`](rounds/round17/tables.md) 表 7'。摘要：

- **floor**（round17 候選集：6 材質＋4 OOD）：僅 2 個 fallback 面可分析
  （`bedroom_ai_generated.floor`、`SteinmanHall.floor`）。門檻 0.20／0.25／0.30
  三檔皆會放行這 2 面，**放行後答對 0、答錯 2**；門檻 0.35 起才變回 0 面放行。
  即：**調低到 0.30 會多放行 2 面且兩面皆答錯**，現行門檻 0.4 對 floor 是安全
  邊界，但 0.30 不是「零影響」的調降空間。
  逐面明細：`bedroom_ai_generated.floor` top-1 是 `concrete` 0.339，
  `wood_panel` 0.220 是次高候選、也是 ground truth；`SteinmanHall.floor`
  top-1 是 `concrete` 0.331，ground truth 是 `gypsum_board`。
- **ceiling**（4 材質＋4 OOD）：round17 已無 fallback 面可分析（原本
  `stairwell_tiled.ceiling` 在 round15 就已轉正），五檔候選門檻皆 0 面放行。
- **wall**（全域 12 材質＋4 OOD，等同未收窄）：`ROLE_MATERIAL_CANDIDATES["wall"]`
  已還原成與 `CLIP_MATERIAL_PROMPTS` 完全相同的 12 條、相同插入順序（見第三節
  round16 記錄），`classify_region_material()` 對 wall 角色送進 CLIP 的候選
  字典因此與 `role=None` 逐字相同——這是程式碼層級的保證（同一份候選字典
  餵給同一個模型必然算出同一組 softmax 值），round17 表 7' 量出的敏感度就是
  「role-aware 之前」的真實敏感度，未被本卡以任何方式扭曲：

  | 候選門檻 | 放行面數 | 放行後答對 | 放行後答錯 |
  |---|---|---|---|
  | 0.20 | 27 | 1 | 26 |
  | 0.25 | 22 | 1 | 21 |
  | 0.30 | 20 | 1 | 19 |
  | 0.35 | **7** | **0** | **7** |
  | 0.40（現行） | 0 | 0 | 0 |

  即：**調低到 0.35 會放行 7 面且 0 面答對**；完整 27 面逐面明細見
  [`rounds/round17/tables.md`](rounds/round17/tables.md) 表 7'。

三個角色分別重跑，未只跑一份全域敏感度表（Opus 驗證重點）。

## 八、Opus 驗證重點對照

- 分區表排除 ground truth 實際出現材質而無理由？**否**——`test_t44_
  role_partition.py`【1】程式化驗證涵蓋（⊇）關係，PLAN_T44.md §1 逐條
  排除理由，round16/round17 的追加候選（`wall` 全還原、`floor` 曾加回
  又撤銷）皆有實測證據與理由。
- 任一角色缺 OOD 候選？**否**——`test_t44_role_partition.py`【4】三角色
  逐一驗證含全部 4 個 OOD。
- 既有 12 條字串 diff？**否**——`test_t44_role_partition.py`【5】逐位元
  比對，`git diff 63c536c HEAD -- src/image_reverb/surfaces.py` 只在
  `ROLE_MATERIAL_CANDIDATES` 與 `classify_region_material`/`analyse_image`/
  `surfaces_from_preprocess` 的介面段落，`CLIP_MATERIAL_PROMPTS` 字典本身
  無 diff。
- `role=None` 與改動前逐位元等價？**是**——`test_t44_role_partition.py`
  【2】【3】。
- 門檻敏感度只跑全域一份？**否**——見第七節，floor/wall/ceiling 三份。
- 超出輪次預算？**否**——首輪（round15）＋2 輪調整（round16／round17）＝
  PLAN §4 上限，round17 後即停。
- 誤拿 `round0_baseline`／`round12`～`14` 當基線？**否**——全程以
  `round11_remap_baseline`（30/76、4/13）為準。
- `compute_materials_confidence()`／gate 有 diff？**否**——第六節鐵則 6。
- **本報告額外主動揭露的一項**：`bathroom_tiled` 的 overall gate 因材質
  confidence 提升而從 BLOCK 變 pass，但材質判定本身是錯的（第五節）——
  請 Opus 特別確認這是否構成「存在任何指紋不符仍印成功的旁路」同型風險，
  或本卡對三個明文門檻的判定已足夠、留給 Fable 收尾複評後續處理。
