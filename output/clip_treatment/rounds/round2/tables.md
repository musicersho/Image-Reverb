## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 24/76（31.6%） |
| 非 proxy 正確率 | 23/60（38.3%） |
| proxy 正確率 | 1/16（6.2%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 24 | 1 | 7/23（30.4%） |
| fallback | 28 | 0 | 11/28（39.3%） |
| out_of_domain | 15 | 0 | 5/15（33.3%） |
| 無來源 | 11 | 1 | 1/10（10.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 3/13（23.1%） |
| ceiling | 13 | 2 | 4/11（36.4%） |
| wall | 52 | 0 | 17/52（32.7%） |


## 表 4：地雷 #18 型 in-set 誤判明細

| 照片 | 面 | AI 判定 | ground truth |
|---|---|---|---|
| bedroom_ai_generated | floor | concrete | wood_panel |
| stairwell_tiled | ceiling | acoustic_panel | generic_wall |
| stairwell_tiled | north | brick | generic_wall |
| stairwell_tiled | east | brick | generic_wall |
| stairwell_tiled | south | brick | generic_wall |
| stairwell_tiled | west | brick | generic_wall |
| site_photo_department_store | floor | acoustic_panel | carpet |
| site_photo_gym | floor | acoustic_panel | carpet |
| site_photo_restaurant | ceiling | acoustic_panel | gypsum_board |
| site_photo_restaurant | north | acoustic_panel | brick |
| site_photo_restaurant | east | acoustic_panel | brick |
| site_photo_restaurant | south | acoustic_panel | brick |
| site_photo_restaurant | west | acoustic_panel | brick |
| RacquetballCourt4 | north | glass | gypsum_board |
| SteinmanHall | north | audience_seating | gypsum_board |
| SteinmanHall | east | acoustic_panel | gypsum_board |


## 與 T-33 凍結快取的差異（治療模式，僅記錄不卡關；見 HANDOFF_T38.md 地雷 B）

- bathroom_tiled：surfaces 與 T-33 凍結快取不同（凍結={'west': 'generic_wall', 'east': 'generic_wall', 'south': 'generic_wall', 'north': 'generic_wall', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- bathroom_tiled：sources 與 T-33 凍結快取不同（凍結={'floor': 'fallback', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}，本次={'floor': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
- bedroom_ai_generated：surfaces 與 T-33 凍結快取不同（凍結={'west': 'generic_wall', 'east': 'generic_wall', 'south': 'generic_wall', 'north': 'generic_wall', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'concrete', 'ceiling': 'gypsum_board'}）
- bedroom_ai_generated：sources 與 T-33 凍結快取不同（凍結={'floor': 'fallback', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}，本次={'floor': 'clip', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
- stairwell_tiled：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'brick', 'east': 'brick', 'south': 'brick', 'north': 'brick', 'floor': 'gypsum_board', 'ceiling': 'acoustic_panel'}）
- stairwell_tiled：sources 與 T-33 凍結快取不同（凍結={'floor': 'fallback', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}，本次={'floor': 'fallback', 'ceiling': 'clip', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}）
- car_interior_suv：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'curtain_fabric', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- car_interior_suv：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip', 'west': 'out_of_domain', 'east': 'out_of_domain', 'south': 'out_of_domain', 'north': 'out_of_domain'}，本次={'floor': 'out_of_domain', 'west': 'out_of_domain', 'east': 'out_of_domain', 'south': 'out_of_domain', 'north': 'out_of_domain'}）
- CathedralRoom：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'out_of_domain'}）
- DivorceBeach：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'concrete', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- DivorceBeach：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip'}，本次={'floor': 'out_of_domain'}）
- DivorceBeach：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() 得到 low，與 T-28-A 基線 medium 不同
- site_photo_department_store：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}，本次={'floor': 'clip', 'ceiling': 'clip', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
- site_photo_restaurant：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'curtain_fabric'}，本次={'west': 'acoustic_panel', 'east': 'acoustic_panel', 'south': 'acoustic_panel', 'north': 'acoustic_panel', 'floor': 'gypsum_board', 'ceiling': 'acoustic_panel'}）
- site_photo_restaurant：sources 與 T-33 凍結快取不同（凍結={'ceiling': 'clip', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}，本次={'ceiling': 'clip', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}）
- site_photo_restaurant：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() 得到 medium，與 T-28-A 基線 low 不同
- RacquetballCourt4：surfaces 與 T-33 凍結快取不同（凍結={'west': 'curtain_fabric', 'east': 'gypsum_board', 'south': 'glass', 'north': 'gypsum_board', 'floor': 'wood_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'glass', 'east': 'gypsum_board', 'south': 'glass', 'north': 'glass', 'floor': 'wood_panel', 'ceiling': 'gypsum_board'}）
- RacquetballCourt4：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'clip', 'south': 'clip', 'west': 'clip', 'ceiling': 'out_of_domain', 'floor': 'clip'}，本次={'north': 'clip', 'east': 'clip', 'south': 'clip', 'west': 'clip', 'ceiling': 'out_of_domain', 'floor': 'clip'}）
- SteinmanHall：surfaces 與 T-33 凍結快取不同（凍結={'west': 'curtain_fabric', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'curtain_fabric'}，本次={'west': 'curtain_fabric', 'east': 'acoustic_panel', 'south': 'gypsum_board', 'north': 'audience_seating', 'floor': 'gypsum_board', 'ceiling': 'curtain_fabric'}）
- SteinmanHall：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'fallback', 'south': 'fallback', 'west': 'clip', 'ceiling': 'clip', 'floor': 'fallback'}，本次={'north': 'clip', 'east': 'clip', 'south': 'fallback', 'west': 'clip', 'ceiling': 'clip', 'floor': 'fallback'}）
- TunnelToHell：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'marble', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- TunnelToHell：sources 與 T-33 凍結快取不同（凍結={'north': 'out_of_domain', 'east': 'clip', 'south': 'clip', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'floor': 'out_of_domain', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
