# T-38B REPORT — 有界提示詞實驗（round7～round10）

## 性質聲明

**本卡是模型實驗，結果不可事前保證。** 「跑滿預算、誠實產出報告」＝工程任務
完成（✅ 的充分條件）；**本輪結論是「目前 12 候選、無 role 參數的介面下，
單改 `CLIP_MATERIAL_PROMPTS` 字串治不好這幾組混淆」，這是合法的實驗否定
結論，不是執行失敗、不是工程沒做完。**

假設設計見 [PLAN.md](PLAN.md)（在任何一輪執行前寫成並 commit，
`git log --format='%h %cI %s'` 可查 PLAN.md 的 commit（`ca029ee`，
2026-09-01T14:36:35+08:00）早於全部四輪 ROUND.md 的產生時間）。

## 一、四輪跑完的數字（對照 round0_baseline）

比較基線固定為 `round0_baseline`：overall 31/76、floor 4/13、in-set 誤判 9
（HANDOFF_T38.md 地雷 C；不是 T-36 的 52.4%／51.7%）。

| 輪次 | 累積改動 | overall | floor | in-set 誤判 | 三門檻同時通過？ |
|---|---|---:|---:|---:|---|
| round0_baseline | （無，基線） | 31/76（40.8%） | 4/13（30.8%） | 9 | （基線） |
| round7 | 改 `concrete` | 30/76（39.5%） | 3/13（23.1%） | 9 | 否（overall／floor 皆下降） |
| round8 | ＋改 `acoustic_panel` | 24/76（31.6%） | 3/13（23.1%） | 18 | 否（三項全劣化） |
| round9 | ＋改 `curtain_fabric` | 20/76（26.3%） | 3/13（23.1%） | 23 | 否（三項全劣化） |
| round10 | ＋再改 `concrete`（第二版） | 23/76（30.3%） | 3/13（23.1%） | 26 | 否（三項全劣化） |

**四輪無一同時滿足「overall 上升＋floor 上升＋in-set 誤判不上升」三個產品
採用門檻**（PLAN.md §5，繼承原 T-38 裁決），且一輪比一輪差——round10（用完
4 輪預算的最後一輪）in-set 誤判 26 面，比基線的 9 面還多將近三倍。

上表數字經由實際呼叫 `load_completed_rounds()`（非手動挑檔案）重新核對，
輸出 `completed=[round0_baseline, round1, round10, round2, round3, round4,
round5, round7, round8, round9]`（含 T-38A 歷史七輪，字典序排列非時間序）、
`skipped=['round6：無 summary.json（不完整或中止的輪次），跳過']`，
逐輪數字與本表相符（回應 T-38A 非阻擋觀察第 2 點）。

## 二、逐輪發生了什麼（誠實記錄，含未預期的副作用）

### round7 —— 改 `concrete`：完全沒修到目標，還製造了一個新副作用

- **目標**：generic_wall→concrete（4 面，bedroom_ai_generated）。
- **結果**：表 4 的 9 個 in-set 誤判**逐項與 round0_baseline 完全相同**——
  bedroom 四面牆一面都沒被改判成 concrete。假設「加強顆粒紋理／冷灰色調
  描述能讓 concrete 贏過 generic_wall」不成立：CLIP 的判斷沒有因為這句更
  精確的英文描述而改變 bedroom 那四張圖的贏家。
- **副作用**：floor 正確率反而從 4/13 掉到 3/13——`DivorceBeach` 的 floor
  從 `concrete`（正確判定，來源 clip）掉成 `gypsum_board`（來源
  out_of_domain），連帶讓該面的 `materials_confidence` 軸從 `medium`
  掉到 `low`（用本次 surfaces/sources 唯讀重算
  `compute_materials_confidence()` 得到 low，見 round7/tables.md 差異區）。
  即使改動只鎖定「讓 concrete 更容易贏」，實際效果卻是**在原本判對的
  地方讓 concrete 更難贏**——CLIP zero-shot 對這句英文的整體排序反應和
  直覺預期不同方向。

### round8 —— 改 `acoustic_panel`：目標沒修到，且大範圍劣化

- **目標**：acoustic_panel→carpet（2 面，department_store／gym 的
  floor）。
- **結果**：這 2 面誤判**原封不動**；但新字串（加入「安裝在牆面／
  天花板、非地面覆蓋物」的描述）讓 `acoustic_panel` 在其他多張照片的
  **牆面／天花板**大量搶答成功——`site_photo_gym` 四面牆＋天花板、
  `site_photo_restaurant` 四面牆＋天花板全部被判成 acoustic_panel，
  `SteinmanHall` 天花板也是。in-set 誤判從 9 面暴增到 18 面（全部新增
  的 9 面都是這個候選造成的）。
- **解讀**：新描述句雖然語意上更貼近「牆面／天花板」，但視覺上與很多
  平面、略帶紋理的表面（包含磁磚、水泥、石膏板）過度相似，CLIP 的
  softmax 排序把它推成到處都贏的強勢候選——這正是 HANDOFF §2 洞二型
  的「模型對失敗毫無自覺」的翻版：字面上更精確不代表視覺嵌入更精確。

### round9 —— 改 `curtain_fabric`：目標沒修到（其中兩組被別的問題取代），整體持續崩壞

- **目標**：curtain_fabric→carpet／gypsum_board／glass（3 面）。
- **結果**：`car_interior_suv` floor 與 `site_photo_restaurant` ceiling
  不再判成 curtain_fabric，但**兩者都變成 acoustic_panel**（round8 已經
  壞掉的候選接手），依然是 in-set 誤判，只是換了個錯誤的候選；
  `RacquetballCourt4` west 的 curtain_fabric→glass **原封不動**。整體
  overall 掉到 20/76，in-set 誤判累積到 23 面（round8 的 18 面全部
  留著，`car_interior_suv` floor 的誤判候選只是從 curtain_fabric 換成
  acoustic_panel，沒有淨減少）。
- **解讀**：三輪累積下來已經很清楚——round8 造成的 acoustic_panel
  過度搶答，蓋過了 round9 想測的 curtain_fabric 效果，兩個假設互相
  污染，這也是「單變因」設計在**累積式**執行下的已知代價（PLAN.md 已
  預先聲明是累積式，此為誠實記錄之現象，非事後才發現的設計缺陷）。

### round10 —— 再改 `concrete`（PLAN.md §4 事前規則選中）：仍未修到目標，且是四輪最差的一輪

- **選擇依據**：round9 未同時滿足三門檻，依 PLAN.md §4 的**事前**規則，
  從 round0_baseline 表 4 五組原始誤判中選出「round9 跑完後仍未修正、
  出現次數最多」的一組＝generic_wall→concrete（4 面，round7～9 全程
  未變）；依規則改動的候選＝ground truth 該有的 `concrete`。
- **新假設**：round7 的冗長描述句無效，改用 CLIP 常見的簡短 caption
  式寫法（`"a photo of a X"`）測試是否更貼近訓練分布。
- **結果**：bedroom 四面牆**依然一面都沒有被改判成 concrete**——兩種
  完全不同風格的英文描述（詳細描述句、簡短 caption 句）對這四張圖的
  CLIP 排序都沒有效果，這強化了下面第三節「介面限制」的判斷：問題
  可能根本不在字串怎麼寫。同時，這句更泛用的 `"a photo of a concrete
  ... surface"` 又在別的地方搶答（`RacquetballCourt4` north、
  `SteinmanHall` floor、`TunnelToHell` south 都新誤判成 concrete），
  in-set 誤判來到四輪最高的 26 面。

## 三、為什麼「換句話說」這條路可能已經到頂——介面限制（裁決第 3 點，明文承認）

`classify_region_material()` 沒有 `role` 參數，floor／wall／ceiling 共用
同一套全域 12 候選 prompts 與 softmax。這意味著：

- 改一個候選的字串，影響的不是「這個候選在某個角色上的表現」，而是
  「這個候選在**所有**78 面、三種角色上的相對排名」——round7／round8／
  round10 的副作用（在未鎖定的照片上製造新誤判）都是這個全域效應的
  直接後果，不是個案的巧合。
- generic_wall→concrete（bedroom）這組誤判，經過兩次完全不同寫法的
  `concrete` 改動（round7 詳細描述、round10 簡短 caption）都沒有讓
  CLIP 在這四張圖上把贏家從 generic_wall 換成 concrete。合理推測是
  bedroom_ai_generated 這幾面牆的視覺特徵本身就更接近「平滑牆面」而非
  「有顆粒感的混凝土」（AI 生成圖的算繪風格可能本來就偏光滑），純文字
  提示詞治療對這種視覺層級的落差沒有槓桿點。
- 這是**介面限制**造成「floor／某些候選必然改善」在此架構下**不保證
  可達**，不是本卡執行不力（T-38B 卡片與 HANDOFF_T38.md §3 已明文
  承認這點）。

## 四、過擬合紅線（誠實揭露）

78 面既是本輪的調參集，也是驗收集，**無 held-out**。round7～10 的假設
設計雖然依據 round0_baseline 的錯誤表（一般性材質視覺特徵，未夾帶
特定場地／照片細節），但因為同一批 78 面同時拿來看效果、同時拿來算
分數，即使某一輪真的讓分數變好，也不能排除是「湊巧改善了這 78 面」而非
「材質辨識能力真的變好」。本輪最終結論是全面劣化，不存在「表面改善、
實際過擬合」的風險，但這個方法論限制仍如實記錄，供 T-39 或後續路線
參考。

## 五、最終決定

**無候選達標。`src/image_reverb/surfaces.py` 已還原成
`CLIP_MATERIAL_PROMPTS` 的 round0_baseline 字串（`concrete`／
`curtain_fabric`／`acoustic_panel` 三個候選逐字改回原句），
`git diff -- src/ data/` 為空，等同零 diff。**

依 PLAN.md §5：不採用 round7～10 任何一輪的提示詞改動；`surfaces.py`
保留 baseline；本 REPORT 即誠實記錄「提示詞治療輪否定結果」；交 Fable
收尾裁決是否進 T-39（擴充候選材質集）或另開 role-aware 設計卡
（HANDOFF_T38.md §8 選項 A／B）。

## 六、共同鐵則自我檢查

- **共同鐵則 1**：`scripts/test_*.py` 16 支全部 EXIT=0（`test_preprocess`／
  `test_segmentation`／`test_pipeline_dedup` 三支慢測試已包含在內，逐支
  單獨執行，非略過）。
- **共同鐵則 2（六條交付 IR MD5，逐條比對）**：
  - `gen_ir_from_text.py "浴室"` → `2adbaa75eb698772a8c9aa693179ec47`
  - `gen_ir_from_text.py "大教堂"` → `2dd19b6e6d351d713887636fe45cd67e`
  - `gen_ir_coupled.py assets/scenes/neighbor_voices.json` →
    `9a94ffdf5d8295aee7889729c39c9cd8`
  - `gen_ir_coupled.py assets/scenes/stadium_corridor.json` →
    `a1c21bcc3fd9aa3480df203a89c8cd05`
  - T-14 兩條由 `test_ir_synth.py`（隨鐵則 1 通過）硬編碼比對，本輪未
    另外重生成。
  - 四條自行重新生成，逐位元與已知值相符；另跑
    `check_audio.py output/ir_synth/coupled_neighbor_voices.wav`：
    RMS 0.049047、峰值 0.707946，非靜音。
- **共同鐵則 3**：`git diff -- src/image_reverb/ir_metrics.py` 為空
  （本卡從未動過此檔）。
- **共同鐵則 4**：`git diff --stat -- SPEC.md ROADMAP.md WORKFLOW.md
  output/mvp_acceptance/ output/material_round/ output/clip_accuracy/`
  輸出為空，四份文件與三個凍結目錄皆未觸碰。
- **共同鐵則 6（gate 判定規則零改動）**：`classify_region_material()`／
  `compute_materials_confidence()` 全程未修改一行；`git diff --stat --
  src/` 最終為空（round7～10 期間曾暫時修改 `CLIP_MATERIAL_PROMPTS` 三個
  字串值，收尾已逐字還原，過程紀錄見各輪 ROUND.md，最終 diff 為零）。
- **共同鐵則 7（臥室紅旗）**：`surfaces.py` 最終與 round0_baseline 逐字
  相同 → bedroom_ai_generated 的三軸與 gate 結果與 round0_baseline
  完全相同（無程式碼改動即無從產生任何 gate 變化），未發生擋變放。
- **共同鐵則 8（基線變化表）準用 T-40 補充細則**：本卡最終 `src/`／
  `data/` 零改動（過程雖動過，收尾已還原），依 T-38B 卡片明文
  「無候選達標：`surfaces.py` 零 diff（＝baseline），鐵則 8 準用 T-40
  補充細則」，以「`git diff src/ data/` 為空＋六條交付 IR MD5 逐條比對」
  代替 13 張全量重跑——上述共同鐵則 2／4／6 已完成這兩項。
- **範圍紅線**：全程只動過 `CLIP_MATERIAL_PROMPTS` 三個候選（`concrete`／
  `acoustic_panel`／`curtain_fabric`）的字串值；未加減候選 id；門檻 0.4
  全程未動；`data/material_ground_truth.json` 全程只讀未寫（`git diff
  -- data/` 為空）；`classify_region_material()`／
  `compute_materials_confidence()` 邏輯行零改動；`CLIP_OOD_PROMPTS`
  全程未動；未夾帶場地／照片特徵（round7～10 全部字串皆為一般性材質
  視覺描述，見 §四過擬合紅線討論）。
