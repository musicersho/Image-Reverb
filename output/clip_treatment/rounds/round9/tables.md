## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 20/76（26.3%） |
| 非 proxy 正確率 | 19/60（31.7%） |
| proxy 正確率 | 1/16（6.2%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 33 | 1 | 9/32（28.1%） |
| fallback | 19 | 0 | 9/19（47.4%） |
| out_of_domain | 15 | 0 | 1/15（6.7%） |
| 無來源 | 11 | 1 | 1/10（10.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 3/13（23.1%） |
| ceiling | 13 | 2 | 3/11（27.3%） |
| wall | 52 | 0 | 14/52（26.9%） |


## 表 4：地雷 #18 型 in-set 誤判明細

| 照片 | 面 | AI 判定 | ground truth |
|---|---|---|---|
| bedroom_ai_generated | north | generic_wall | concrete |
| bedroom_ai_generated | east | generic_wall | concrete |
| bedroom_ai_generated | south | generic_wall | concrete |
| bedroom_ai_generated | west | generic_wall | concrete |
| car_interior_suv | floor | acoustic_panel | carpet |
| site_photo_department_store | floor | acoustic_panel | carpet |
| site_photo_department_store | north | curtain_fabric | gypsum_board |
| site_photo_department_store | east | curtain_fabric | gypsum_board |
| site_photo_department_store | south | curtain_fabric | gypsum_board |
| site_photo_department_store | west | curtain_fabric | gypsum_board |
| site_photo_gym | floor | acoustic_panel | carpet |
| site_photo_gym | north | acoustic_panel | gypsum_board |
| site_photo_gym | east | acoustic_panel | gypsum_board |
| site_photo_gym | south | acoustic_panel | gypsum_board |
| site_photo_gym | west | acoustic_panel | gypsum_board |
| site_photo_restaurant | ceiling | acoustic_panel | gypsum_board |
| site_photo_restaurant | north | acoustic_panel | brick |
| site_photo_restaurant | east | acoustic_panel | brick |
| site_photo_restaurant | south | acoustic_panel | brick |
| site_photo_restaurant | west | acoustic_panel | brick |
| RacquetballCourt4 | west | curtain_fabric | glass |
| SteinmanHall | ceiling | acoustic_panel | curtain_fabric |
| SteinmanHall | north | audience_seating | gypsum_board |


## 與 T-33 凍結快取的差異（治療模式，僅記錄不卡關；見 HANDOFF_T38.md 地雷 B）

**範圍評估**：非預期範圍：8 張照片有差異（CathedralRoom, DivorceBeach, SteinmanHall, TunnelToHell, car_interior_suv, site_photo_department_store, site_photo_gym, site_photo_restaurant），其中 7 張非 TunnelToHell（CathedralRoom, DivorceBeach, SteinmanHall, car_interior_suv, site_photo_department_store, site_photo_gym, site_photo_restaurant），多半是本輪提示詞造成的漂移

- car_interior_suv：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'curtain_fabric', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}）
- CathedralRoom：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'north': 'fallback', 'east': 'fallback', 'south': 'out_of_domain', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'out_of_domain'}）
- DivorceBeach：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'concrete', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- DivorceBeach：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip'}，本次={'floor': 'out_of_domain'}）
- DivorceBeach：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() 得到 low，與 T-28-A 基線 medium 不同
- site_photo_department_store：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'curtain_fabric', 'east': 'curtain_fabric', 'south': 'curtain_fabric', 'north': 'curtain_fabric', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}）
- site_photo_department_store：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}，本次={'floor': 'clip', 'ceiling': 'clip', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}）
- site_photo_department_store：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() 得到 medium，與 T-28-A 基線 low 不同
- site_photo_gym：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}，本次={'west': 'acoustic_panel', 'east': 'acoustic_panel', 'south': 'acoustic_panel', 'north': 'acoustic_panel', 'floor': 'acoustic_panel', 'ceiling': 'gypsum_board'}）
- site_photo_gym：sources 與 T-33 凍結快取不同（凍結={'floor': 'clip', 'west': 'out_of_domain', 'east': 'out_of_domain', 'south': 'out_of_domain', 'north': 'out_of_domain'}，本次={'floor': 'clip', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}）
- site_photo_gym：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() 得到 medium，與 T-28-A 基線 low 不同
- site_photo_restaurant：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'curtain_fabric'}，本次={'west': 'acoustic_panel', 'east': 'acoustic_panel', 'south': 'acoustic_panel', 'north': 'acoustic_panel', 'floor': 'gypsum_board', 'ceiling': 'acoustic_panel'}）
- site_photo_restaurant：sources 與 T-33 凍結快取不同（凍結={'ceiling': 'clip', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}，本次={'ceiling': 'clip', 'west': 'clip', 'east': 'clip', 'south': 'clip', 'north': 'clip'}）
- site_photo_restaurant：用本次 surfaces/sources 唯讀重算 compute_materials_confidence() 得到 medium，與 T-28-A 基線 low 不同
- SteinmanHall：surfaces 與 T-33 凍結快取不同（凍結={'west': 'curtain_fabric', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'curtain_fabric'}，本次={'west': 'curtain_fabric', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'audience_seating', 'floor': 'gypsum_board', 'ceiling': 'acoustic_panel'}）
- SteinmanHall：sources 與 T-33 凍結快取不同（凍結={'north': 'fallback', 'east': 'fallback', 'south': 'fallback', 'west': 'clip', 'ceiling': 'clip', 'floor': 'fallback'}，本次={'north': 'clip', 'east': 'fallback', 'south': 'fallback', 'west': 'clip', 'ceiling': 'clip', 'floor': 'fallback'}）
- TunnelToHell：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'marble', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- TunnelToHell：sources 與 T-33 凍結快取不同（凍結={'north': 'out_of_domain', 'east': 'clip', 'south': 'clip', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'floor': 'out_of_domain', 'ceiling': 'out_of_domain', 'west': 'out_of_domain', 'east': 'out_of_domain', 'south': 'out_of_domain', 'north': 'out_of_domain'}）
