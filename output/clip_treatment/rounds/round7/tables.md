## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 30/76（39.5%） |
| 非 proxy 正確率 | 29/60（48.3%） |
| proxy 正確率 | 1/16（6.2%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 19 | 1 | 9/18（50.0%） |
| fallback | 34 | 0 | 15/34（44.1%） |
| out_of_domain | 14 | 0 | 5/14（35.7%） |
| 無來源 | 11 | 1 | 1/10（10.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 3/13（23.1%） |
| ceiling | 13 | 2 | 4/11（36.4%） |
| wall | 52 | 0 | 23/52（44.2%） |


## 表 4：地雷 #18 型 in-set 誤判明細

| 照片 | 面 | AI 判定 | ground truth |
|---|---|---|---|
| bedroom_ai_generated | north | generic_wall | concrete |
| bedroom_ai_generated | east | generic_wall | concrete |
| bedroom_ai_generated | south | generic_wall | concrete |
| bedroom_ai_generated | west | generic_wall | concrete |
| car_interior_suv | floor | curtain_fabric | carpet |
| site_photo_department_store | floor | acoustic_panel | carpet |
| site_photo_gym | floor | acoustic_panel | carpet |
| site_photo_restaurant | ceiling | curtain_fabric | gypsum_board |
| RacquetballCourt4 | west | curtain_fabric | glass |


## 與 T-33 凍結快取的差異（治療模式，僅記錄不卡關；見 HANDOFF_T38.md 地雷 B）

**範圍評估**：非預期範圍：3 張照片有差異（CathedralRoom, DivorceBeach, TunnelToHell），其中 2 張非 TunnelToHell（CathedralRoom, DivorceBeach），多半是本輪提示詞造成的漂移

- CathedralRoom：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'out_of_domain'}）
- DivorceBeach：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'concrete', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- DivorceBeach：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip'}，本次={'floor': 'out_of_domain'}）
- DivorceBeach：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() 得到 low，與 T-28-A 基線 medium 不同
- TunnelToHell：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'marble', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- TunnelToHell：sources 與 T-33 凍結快取不同（凍結={'north': 'out_of_domain', 'east': 'clip', 'south': 'clip', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'floor': 'out_of_domain', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
