## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 30/76（39.5%） |
| 非 proxy 正確率 | 30/63（47.6%） |
| proxy 正確率 | 0/13（0.0%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 20 | 1 | 10/19（52.6%） |
| fallback | 35 | 0 | 15/35（42.9%） |
| out_of_domain | 12 | 0 | 5/12（41.7%） |
| 無來源 | 11 | 1 | 0/10（0.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 4/13（30.8%） |
| ceiling | 13 | 2 | 3/11（27.3%） |
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
| site_photo_gym | floor | acoustic_panel | rubber_flooring |
| site_photo_restaurant | ceiling | curtain_fabric | gypsum_board |
| RacquetballCourt4 | west | curtain_fabric | glass |


## 與 T-33 凍結快取的差異（治療模式，僅記錄不卡關；見 HANDOFF_T38.md 地雷 B）

**範圍評估**：符合預期（僅 TunnelToHell，T-37 修正後與 T-33 凍結快取本來就不同，見 HANDOFF_T38.md 地雷 B）

- TunnelToHell：surfaces 與 T-33 凍結快取不同（凍結={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'marble', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}，本次={'west': 'gypsum_board', 'east': 'gypsum_board', 'south': 'gypsum_board', 'north': 'gypsum_board', 'floor': 'gypsum_board', 'ceiling': 'gypsum_board'}）
- TunnelToHell：sources 與 T-33 凍結快取不同（凍結={'north': 'out_of_domain', 'east': 'clip', 'south': 'clip', 'west': 'fallback', 'ceiling': 'out_of_domain', 'floor': 'fallback'}，本次={'floor': 'out_of_domain', 'ceiling': 'fallback', 'west': 'fallback', 'east': 'fallback', 'south': 'fallback', 'north': 'fallback'}）
