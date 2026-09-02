# T-44 PLAN — role-aware 材質候選子集（round11_remap_baseline → round15_role_partition）

> **本檔在 round15 執行前寫成並 commit。**（比照 T-38B PLAN.md／T-39 PLAN_T39.md
> 的做法：本檔 commit 時間必須早於 round15 ROUND.md 的 commit 時間，可用
> `git log --format='%h %cI %s'` 對照佐證。）

## 0. 依據與性質聲明

裁決 T-38B-A 開卡（HANDOFF_T39.md）：round7～10（T-38B）、round12～14（T-39）
的副作用全部是全域候選集**跨角色搶答**型——牆／面板材質搶答地板
（`acoustic_panel`／`curtain_fabric` → 地板應為 `carpet`）、地板材質搶答天花板、
橡膠地墊搶答球場地板。角色候選子集在機制上有字串治療給不了的決定性槓桿：
**不在該角色候選集內的材質不可能被選中**。

**性質聲明（與 T-38B 同型的實驗卡）**：「跑滿預算、誠實報告」＝工程完成
（✅ 的充分條件）；「role-aware 沒有改善」是合法實驗結論，不是工程失敗。

**誠實的預期管理（明文入卡，執行後不得回頭改動去湊結論）**：
- `bedroom_ai_generated` 四面牆的 `generic_wall`→`concrete` 是**牆對牆**混淆
  （兩者都合法存在於 wall 候選子集內），role-aware 對它零槓桿、預期不治。
- `bathroom_tiled.ceiling` 與 `site_photo_gym.ceiling`：ADE20K 分割階段就沒有
  `ceiling` 角色像素（`ratio < config.MIN_SURFACE_AREA_RATIO`），CLIP 從未被
  呼叫——這兩面對本卡**結構性不可達**，不計入預期收益，不為此動分割邏輯。
- `site_photo_gym.floor`（gt=`rubber_flooring`）、`bathroom_tiled.ceiling`
  （gt=`vinyl_panel`，另外也結構性不可達）、`site_photo_gym.ceiling`
  （gt=`metal_roof_deck`，另外也結構性不可達）：這三個材質是 T-39 新增但
  **未採用**進 `CLIP_MATERIAL_PROMPTS` 的候選（見 `surfaces.py` 現行 12 條
  字串），本卡**不新增候選字串**（範圍紅線），這些面在 12-候選宇宙裡無論
  角色怎麼分都**不可能判對**，同樣不計入預期收益。
- `site_photo_restaurant.ceiling`（`curtain_fabric` vs gt `gypsum_board`）與
  `RacquetballCourt4.west`（`curtain_fabric` vs gt `glass`）：**角色內**混淆
  （`curtain_fabric` 在本資料集裡本身就是合法的 ceiling／wall 材質——
  `SteinmanHall.ceiling`／`car_interior_suv.ceiling` 的 gt 正是
  `curtain_fabric`，`SteinmanHall.west` 的 gt 也是 `curtain_fabric`），
  分區規則要求該材質必須留在 ceiling／wall 候選集內（見下方完整性檢查），
  role-aware 對這兩面預期同樣不治。

## 1. 分區表（單一事實來源：`src/image_reverb/surfaces.py` 的
`ROLE_MATERIAL_CANDIDATES` 常數；本節為其設計文件與逐條理由）

依 12 條既有 `CLIP_MATERIAL_PROMPTS` 材質 id，對照
`data/material_ground_truth.json`（T-39 重對映後最終狀態）78 面裡非
`unknown` 的實際材質，程式化統計（非手打，見下方完整性檢查表的產生方式）：

| 角色 | 候選子集（12 條裡的幾條） | 排除的材質 |
|---|---|---|
| floor | `concrete`／`carpet`／`wood_panel`／`gypsum_board`／`marble`／`audience_seating` | `brick`／`glass`／`curtain_fabric`／`acoustic_panel`／`grass_soil`／`generic_wall` |
| ceiling | `concrete`／`curtain_fabric`／`generic_wall`／`gypsum_board` | `brick`／`wood_panel`／`glass`／`marble`／`carpet`／`acoustic_panel`／`audience_seating`／`grass_soil` |
| wall | `concrete`／`brick`／`glass`／`gypsum_board`／`marble`／`curtain_fabric`／`acoustic_panel`／`grass_soil`／`generic_wall` | `wood_panel`／`carpet`／`audience_seating` |

**4 個 OOD 候選**（`__vehicle_interior`／`__outdoor_scene`／`__object_closeup`／
`__person`）**三個角色都保留**，不分掉、不排除（設計 4）。

### 排除理由（逐條，分區完整性鐵則要求）

排除的共同理由：**該材質在（T-39 重對映後）78 面 ground truth 裡，從未在
該角色出現過**——用下面的程式化統計核對，不是猜測：

```
floor  reachable(12條內) = {audience_seating, carpet, concrete, gypsum_board, marble, wood_panel}
       unreachable(不在12條，T-39未採用) = {rubber_flooring}   ← site_photo_gym.floor，結構性不可達
ceiling reachable = {concrete, curtain_fabric, generic_wall, gypsum_board}
        unreachable = {metal_roof_deck, vinyl_panel}            ← 兩面結構性不可達（見 §0）
wall   reachable = {acoustic_panel, brick, concrete, curtain_fabric,
                     generic_wall, glass, grass_soil, gypsum_board, marble}
       unreachable = {}（無）
```

（產生方式：對 `data/material_ground_truth.json` 逐面依 `floor`/`ceiling`/
`north|east|south|west→wall` 分類，material_id≠`unknown` 就收進該角色集合，
再對照 `CLIP_MATERIAL_PROMPTS.keys()` 分 reachable/unreachable。跑法附錄於
`scripts/test_t44_role_partition.py` 的完整性測試，Opus 可重跑核對。）

- **floor 排除 `generic_wall`／`brick`／`glass`／`curtain_fabric`／
  `acoustic_panel`／`grass_soil`**：這 6 種材質在 13 張照片、78 面裡從未是
  任何一面地板的 ground truth——它們是牆／面板／簾幕類材質。且其中
  `curtain_fabric`（`car_interior_suv.floor`，round11 信心 0.542）與
  `acoustic_panel`（`site_photo_department_store.floor` 0.936、
  `site_photo_gym.floor` 0.566）正是 round11_remap_baseline 表 4 記錄的
  「地板被非地板材質搶答」in-set 誤判實例，是本卡要治的病灶本身。
- **ceiling 排除 `brick`／`wood_panel`／`glass`／`marble`／`carpet`／
  `acoustic_panel`／`audience_seating`／`grass_soil`**：這 8 種材質從未是
  任何一面天花板的 ground truth。
- **wall 排除 `wood_panel`／`carpet`／`audience_seating`**：這 3 種是
  「地板專屬」材質（六面裡從未出現在任何一面牆的 ground truth），wall
  候選集因此保留 12 條裡的 9 條，改動幅度本來就最小——**預期 wall 角色
  本卡效益有限**，主戰場在 floor／ceiling（誠實記在此處，不是跑完才說）。

### 完整性檢查（鐵則：不得排除該角色 ground truth 實際出現過的材質）

上表「候選子集」欄與「reachable」集合逐一核對相等（`assert` 見
`scripts/test_t44_role_partition.py`）：floor 6 種、ceiling 4 種、wall 9 種，
與 reachable 統計**完全相符，無遺漏**。三個 `unreachable` 材質（`rubber_flooring`／
`metal_roof_deck`／`vinyl_panel`）依範圍紅線不新增候選字串，其對應面已在
§0 列為「不計入預期收益」，不是被分區表排除，是从来就不在 12-候選宇宙內。

## 2. 介面設計

- `classify_region_material()` 新增 `role: str | None = None` 參數（放在
  既有參數最後，關鍵字參數）。`role=None`（預設）→ 候選集＝
  `{**CLIP_MATERIAL_PROMPTS, **CLIP_OOD_PROMPTS}`，與改動前**逐位元相同的
  程式路徑**（同一個 dict-merge 表達式，非僅結果相同）。`role` 給定時
  →候選集＝`{material: CLIP_MATERIAL_PROMPTS[m] for m in
  ROLE_MATERIAL_CANDIDATES[role]}` ＋ `CLIP_OOD_PROMPTS`。
- `analyse_image()` 新增 `role_aware: bool = False` 參數（預設向後相容）。
  `role_aware=False` 時，對 `classify_region_material()` 的呼叫**維持原本
  5 個位置參數、不帶 `role`**（不是傳 `role=None` 才等價，是連這個關鍵字都
  不出現在呼叫式裡，字面上與改動前 100% 相同一行程式碼）；`role_aware=True`
  時才多帶 `role=role`（用迴圈變數，剛好就是 `"floor"`／`"ceiling"`／`"wall"`）。
- `surfaces_from_preprocess()` 新增 `role_aware: bool = False` 參數，
  原樣往下傳給兩個分支（equirect／單張透視）內的 `analyse_image()` 呼叫。
- `pipeline.py`（`run_photo()`）呼叫端明確寫
  `surfaces_from_preprocess(summary, role_aware=False)`（本卡執行時先寫死
  `False`，讓呼叫端可見這個開關存在；若最終達成 §5 產品採用門檻，改成
  `True` 並 commit；未達成則保持 `False`，即全域 baseline 行為——不動這一行
  以外的任何邏輯）。
- **`classify_region_material()`／`analyse_image()`／`surfaces_from_preprocess()`
  三者新參數皆為關鍵字參數、皆預設向後相容值**，`role=None` invariant test
  見 §3。

## 3. `role=None` 逐位元等價 invariant test（工程完成充分條件之一）

`scripts/test_t44_role_partition.py` 新增：
1. **完整性檢查**（§1）：對 `data/material_ground_truth.json` 程式化統計
   每個角色的 reachable 材質集合，`assert` 與 `ROLE_MATERIAL_CANDIDATES`
   逐一相等。
2. **role=None 逐位元等價**：樁掉 CLIP 模型呼叫（不下載真模型），固定回傳
   一個可觀察的假 softmax 輸出，分別呼叫
   `classify_region_material(..., role=None)` 與（修改前的呼叫方式，即不帶
   `role` 參數）比對候選集字典**逐鍵逐值相同**（不只是最終材質 id 相同，
   是餵給 CLIP 的候選提示詞字典完全一致）。
3. **`analyse_image(role_aware=False)`**：樁掉 `classify_region_material`，
   斷言呼叫時的 `args`／`kwargs` 裡**沒有 `role` 這個鍵**（證明呼叫式字面
   上跟改動前相同，不是傳了 `role=None` 才「碰巧」等價）。
4. **OOD 候選三角色皆保留**：對 floor／ceiling／wall 三個角色分別呼叫
   `classify_region_material(..., role=<角色>)`（樁掉 CLIP），檢查候選字典
   包含全部 4 個 `CLIP_OOD_PROMPTS` 鍵。
5. **既有 12 條 `CLIP_MATERIAL_PROMPTS` 字串逐位元不變**（比照
   `test_t39_materials_invariant.py` 的寫死比對手法）。

**對舊碼（T-44 之前）必然 fail**：舊碼的 `classify_region_material()` 沒有
`role` 參數，測試【2】【4】呼叫時會直接 `TypeError`；`analyse_image()` 沒有
`role_aware` 參數，測試【3】會 `TypeError`。

## 4. 實驗設計

- **比較基線**：`round11_remap_baseline`（overall 30/76、floor 4/13、
  ceiling 3/11、wall 23/52、非 proxy 30/63、in-set 誤判 9）——**不是**
  `round0_baseline`（31/76，重對映前量尺）、**不是** `round12`～`round14`
  （T-39 未採用，量尺與 round11 相同但屬於已否定的分支）。
- **輪次標籤**延續 `output/clip_treatment/rounds/` 既有全域序號（round0～14
  已用），本卡從 **`round15_role_partition`** 開始。
- **首輪**（round15）：`role_aware=True`，套用 §1 分區表，門檻沿用 0.4
  不動，既有 12 條字串不動。
- **調整輪**（最多 2 輪：round16／round17）：**只准調整分區表**（哪個材質
  屬於哪個角色），**不准調字串**（範圍紅線）。跑滿即停，不得為了達標超
  預算加輪次。
- **門檻敏感度**：最終輪之後，對 floor／wall／ceiling **三個角色分別**
  重跑一次表 7 型的敏感度掃描（沿用 `t36_analysis` 的 sweep 邏輯，門檻本身
  不動，只是把 fallback 面依角色分組分別統計）——不得只跑一份全域敏感度
  表（Opus 驗證重點紅旗）。

## 5. 產品採用門檻（對 `round11_remap_baseline`，繼承卡片原文）

最終輪（round15，或 round16／round17 若有調整，取最後一輪）**必須同時**
滿足：① overall 上升；② floor 上升；③ in-set 誤判不上升。

三者未同時滿足 → **不採用**，`pipeline.py` 的 `run_photo()` 維持
`surfaces_from_preprocess(summary, role_aware=False)`（即全域 baseline
行為），`ROLE_MATERIAL_CANDIDATES`／`role` 介面**保留但不啟用**（供未來
參考或 Fable 收尾複評決定後續），REPORT.md 誠實記錄。

三者同時滿足 → 改 `pipeline.py` 呼叫端為 `role_aware=True` 並 commit，
跑基線變化表（共同鐵則 8）＋臥室紅旗檢查（共同鐵則 7）。

## 6. 依 round11 快取資料的量化預期（跑之前先寫死的假設，不是跑完才編）

以下數字全部讀自 `output/clip_treatment/rounds/round11_remap_baseline/runs/*/detail.json`
既有快取（真實跑過的結果，非猜測），用來說明分區表**為什麼有機會、也有
風險**——round15 跑完後要對照這裡逐項核對，不得事後改寫本節。

**floor 角色的機會（top-1 目前被排除材質壓過、gt 在候選集內）**：
- `site_photo_department_store.floor`：目前 `acoustic_panel` 0.9356 壓過一切
  （`curtain_fabric` 0.0178），排除後底層地板候選（含 gt `carpet`）第一次有
  機會競爭 top-1——**最強的正向假設**。
- `car_interior_suv.floor`：目前 `curtain_fabric` 0.5421 壓過一切，gt=`carpet`
  甚至不在 top3（機率 <0.115），排除 `curtain_fabric` 後有機會浮現，但也可能
  被 OOD（`__vehicle_interior`）搶去——**方向不確定，需要真跑**。
- `bedroom_ai_generated.floor`（fallback，top3 `generic_wall` 0.2436／
  `concrete` 0.1659／`wood_panel` 0.1076，gt=`wood_panel`）、
  `stairwell_tiled.floor`（fallback，`generic_wall` 0.3133／`marble` 0.1815，
  gt=`marble`）、`CathedralRoom.floor`（fallback，`concrete` 0.3448 本來就
  最高但被 `__object_closeup`／`acoustic_panel` 拖到門檻下，gt=`concrete`，
  proxy）：排除 `generic_wall`／`acoustic_panel` 後，gt 材質的機率有機會被
  推過 0.4 門檻轉為 `clip`。

**floor 角色的風險（目前靠 fallback 預設值「巧合答對」，排除候選後可能被
真判定推翻而答錯——地雷 #15 型同意偏誤的反向風險）**：
- `bathroom_tiled.floor`：fallback→`gypsum_board`（＝gt，巧合），但 top3
  第二名 `carpet` 0.1968 排除 `generic_wall`（0.3516，第一名）後可能被推過
  門檻，`carpet`≠gt→**可能從答對變答錯**。
- `SteinmanHall.floor`：fallback→`gypsum_board`（＝gt，巧合），排除
  `acoustic_panel`（0.2105，第一名）後，第二名 `concrete` 0.1856 可能被推
  過門檻，`concrete`≠gt→**可能從答對變答錯**。

這兩個風險必須在 ROUND.md 逐面核對，若真的發生（可預期發生 0～2 面）要如
實記錄為「role-aware 拆穿了 fallback 預設值的同意偏誤，不是分區表退步」，
不得隱藏或美化。

**ceiling 角色的機會**：`stairwell_tiled.ceiling`（fallback，`acoustic_panel`
0.3051 排除後，gt=`generic_wall` 0.2031 有機會轉正）——目前最有機會的
ceiling 修正案例。`site_photo_department_store.ceiling`（fallback，
`gypsum_board` 0.384 本來就是自己最高但差一點點沒過門檻，排除小額候選後
機率上升機會很大）、`RacquetballCourt4.ceiling`（out_of_domain 但
fallback 值本來就＝gt，排除 `acoustic_panel` 0.2 對其影響方向不明但下檔
有限）：這兩面已經是答對，主要是觀察會不會維持答對。

**wall 角色**：候選子集改動最小（12 條留 9 條），且既有 9 個 in-set 誤判裡
2 個是角色內混淆（`RacquetballCourt4.west`／`bedroom` 四面），本卡對 wall
的預期效益本來就有限，不是本卡重點戰場。

**加總的誠實預期**：非常粗略地說，floor／ceiling 合計有 2～6 面「有機會」
修正、也有 0～2 面「有風險」被拆穿同意偏誤而倒扣，wall 幾乎不動——
**overall 淨變化方向在跑之前無法確定，這正是需要真跑一輪的原因，不是可以
用試算表算出來的**。
