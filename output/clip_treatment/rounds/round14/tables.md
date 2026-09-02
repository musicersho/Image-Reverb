## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 24/76（31.6%） |
| 非 proxy 正確率 | 24/63（38.1%） |
| proxy 正確率 | 0/13（0.0%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 22 | 1 | 9/21（42.9%） |
| fallback | 38 | 0 | 14/38（36.8%） |
| out_of_domain | 7 | 0 | 1/7（14.3%） |
| 無來源 | 11 | 1 | 0/10（0.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 4/13（30.8%） |
| ceiling | 13 | 2 | 3/11（27.3%） |
| wall | 52 | 0 | 17/52（32.7%） |


## 表 4：地雷 #18 型 in-set 誤判明細

| 照片 | 面 | AI 判定 | ground truth |
|---|---|---|---|
| car_interior_suv | floor | rubber_flooring | carpet |
| CathedralRoom | west | vinyl_panel | concrete |
| site_photo_department_store | floor | acoustic_panel | carpet |
| site_photo_department_store | north | vinyl_panel | gypsum_board |
| site_photo_department_store | east | vinyl_panel | gypsum_board |
| site_photo_department_store | south | vinyl_panel | gypsum_board |
| site_photo_department_store | west | vinyl_panel | gypsum_board |
| site_photo_restaurant | ceiling | curtain_fabric | gypsum_board |
| RacquetballCourt4 | north | vinyl_panel | gypsum_board |
| RacquetballCourt4 | south | vinyl_panel | glass |
| RacquetballCourt4 | west | vinyl_panel | glass |
| TunnelToHell | floor | rubber_flooring | marble |


## 與 T-33 凍結快取的差異（治療模式，僅記錄不卡關；見 HANDOFF_T38.md 地雷 B）

**範圍評估**：非預期範圍：7 張照片有差異（CathedralRoom, RacquetballCourt4, TunnelToHell, bedroom_ai_generated, car_interior_suv, site_photo_department_store, site_photo_gym），其中 6 張非 TunnelToHell（CathedralRoom, RacquetballCourt4, bedroom_ai_generated, car_interior_suv, site_photo_department_store, site_photo_gym），多半是本輪提示詞造成的漂移

- bedroom_ai_generated：surfaces 與 T-33 凍結快取不同（凍結={'west': 'generic_wall', 'east': 'generic_wall', 'south': 'generic_wall', 'north': 'generic_wall', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- bedroom_ai_generated：sources 與 T-33 凍結快取不同（凍結={'floor': 'fallback', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}，本次={'floor': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
- car_interior_suv：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'curtain_fabric', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'rubber_flooring', 'ceiling': 'gypsum_board'}）
- CathedralRoom：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'vinyl_panel', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- CathedralRoom：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'clip', 'ceiling': 'out_of_domain', 'floor': 'fallback'}）
- site_photo_department_store：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'vinyl_panel', 'east': 'vinyl_panel', 'south': 'vinyl_panel', 'north': 'vinyl_panel', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}）
- site_photo_department_store：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}，本次={'floor': 'clip', 'ceiling': 'fallback', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}）
- site_photo_gym：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'rubber_flooring', 'ceiling': 'gypsum_board'}）
- site_photo_gym：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip', 'west': 'out_of_domain', 'east': 'out_of_domain', 'south': 'out_of_domain', 'north': 'out_of_domain'}，本次={'floor': 'clip', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
- RacquetballCourt4：surfaces 與 T-33 凍結快取不同（凍結={'west': 'curtain_fabric', 'east': 'gypsum_board', 'south': 'glass', 'north': 'gypsum_board', 'floor': 'wood_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'vinyl_panel', 'east': 'gypsum_board', 'south': 'vinyl_panel', 'north': 'vinyl_panel', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- RacquetballCourt4：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'clip', 'south': 'clip', 'west': 'clip', 'ceiling': 'out_of_domain', 'floor': 'clip'}，本次={'north': 'clip', 'east': 'clip', 'south': 'clip', 'west': 'clip', 'ceiling': 'out_of_domain', 'floor': 'fallback'}）
- TunnelToHell：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'marble', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'rubber_flooring', 'ceiling': 'gypsum_board'}）
- TunnelToHell：sources 與 T-33 凍結快取不同（凍結={'north': 'out_of_domain', 'east': 'clip', 'south': 'clip', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'floor': 'clip', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
