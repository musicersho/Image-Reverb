## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 29/76（38.2%） |
| 非 proxy 正確率 | 29/63（46.0%） |
| proxy 正確率 | 0/13（0.0%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 19 | 1 | 9/18（50.0%） |
| fallback | 38 | 0 | 16/38（42.1%） |
| out_of_domain | 10 | 0 | 4/10（40.0%） |
| 無來源 | 11 | 1 | 0/10（0.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 4/13（30.8%） |
| ceiling | 13 | 2 | 3/11（27.3%） |
| wall | 52 | 0 | 22/52（42.3%） |


## 表 4：地雷 #18 型 in-set 誤判明細

| 照片 | 面 | AI 判定 | ground truth |
|---|---|---|---|
| bedroom_ai_generated | north | generic_wall | concrete |
| bedroom_ai_generated | east | generic_wall | concrete |
| bedroom_ai_generated | south | generic_wall | concrete |
| bedroom_ai_generated | west | generic_wall | concrete |
| car_interior_suv | floor | rubber_flooring | carpet |
| site_photo_department_store | floor | acoustic_panel | carpet |
| site_photo_restaurant | ceiling | curtain_fabric | gypsum_board |
| RacquetballCourt4 | south | vinyl_panel | glass |
| TunnelToHell | floor | rubber_flooring | marble |


## 與 T-33 凍結快取的差異（治療模式，僅記錄不卡關；見 HANDOFF_T38.md 地雷 B）

**範圍評估**：非預期範圍：4 張照片有差異（RacquetballCourt4, TunnelToHell, car_interior_suv, site_photo_gym），其中 3 張非 TunnelToHell（RacquetballCourt4, car_interior_suv, site_photo_gym），多半是本輪提示詞造成的漂移

- car_interior_suv：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'curtain_fabric', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'rubber_flooring', 'ceiling': 'gypsum_board'}）
- site_photo_gym：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'rubber_flooring', 'ceiling': 'gypsum_board'}）
- RacquetballCourt4：surfaces 與 T-33 凍結快取不同（凍結={'west': 'curtain_fabric', 'east': 'gypsum_board', 'south': 'glass', 'north': 'gypsum_board', 'floor': 'wood_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'vinyl_panel', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- RacquetballCourt4：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'clip', 'south': 'clip', 'west': 'clip', 'ceiling': 'out_of_domain', 'floor': 'clip'}，本次={'north': 'fallback', 'east': 'clip', 'south': 'clip', 'west': 'fallback', 'ceiling': 'fallback', 'floor': 'fallback'}）
- TunnelToHell：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'marble', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'rubber_flooring', 'ceiling': 'gypsum_board'}）
- TunnelToHell：sources 與 T-33 凍結快取不同（凍結={'north': 'out_of_domain', 'east': 'clip', 'south': 'clip', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'floor': 'clip', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
