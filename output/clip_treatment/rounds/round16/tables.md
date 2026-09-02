## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 31/76（40.8%） |
| 非 proxy 正確率 | 30/63（47.6%） |
| proxy 正確率 | 1/13（7.7%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 23 | 1 | 13/22（59.1%） |
| fallback | 29 | 0 | 13/29（44.8%） |
| out_of_domain | 15 | 0 | 5/15（33.3%） |
| 無來源 | 11 | 1 | 0/10（0.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 4/13（30.8%） |
| ceiling | 13 | 2 | 4/11（36.4%） |
| wall | 52 | 0 | 23/52（44.2%） |


## 表 4：地雷 #18 型 in-set 誤判明細

| 照片 | 面 | AI 判定 | ground truth |
|---|---|---|---|
| bathroom_tiled | floor | generic_wall | gypsum_board |
| bedroom_ai_generated | north | generic_wall | concrete |
| bedroom_ai_generated | east | generic_wall | concrete |
| bedroom_ai_generated | south | generic_wall | concrete |
| bedroom_ai_generated | west | generic_wall | concrete |
| stairwell_tiled | floor | generic_wall | marble |
| site_photo_gym | floor | concrete | rubber_flooring |
| site_photo_restaurant | ceiling | curtain_fabric | gypsum_board |
| RacquetballCourt4 | west | curtain_fabric | glass |


## 表 7'：fallback 門檻（0.4）敏感度分析——按角色分開（PLAN_T44.md §4）


### floor

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 2 | 0 | 2 |
| 0.25 | 2 | 0 | 2 |
| 0.30 | 1 | 0 | 1 |
| 0.35 | 0 | 0 | 0 |
| 0.40 | 0 | 0 | 0 |


| 照片 | 面 | top-1 原始候選 | top-1 信心 | ground truth | 是否正確 |
|---|---|---|---|---|---|
| bedroom_ai_generated | floor | generic_wall | 0.333 | wood_panel | ✗ |
| SteinmanHall | floor | concrete | 0.282 | gypsum_board | ✗ |

### ceiling

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 0 | 0 | 0 |
| 0.25 | 0 | 0 | 0 |
| 0.30 | 0 | 0 | 0 |
| 0.35 | 0 | 0 | 0 |
| 0.40 | 0 | 0 | 0 |

（無可分析的 fallback 面）


### wall

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 27 | 1 | 26 |
| 0.25 | 22 | 1 | 21 |
| 0.30 | 20 | 1 | 19 |
| 0.35 | 7 | 0 | 7 |
| 0.40 | 0 | 0 | 0 |


| 照片 | 面 | top-1 原始候選 | top-1 信心 | ground truth | 是否正確 |
|---|---|---|---|---|---|
| stairwell_tiled | north | brick | 0.378 | generic_wall | ✗ |
| stairwell_tiled | east | brick | 0.378 | generic_wall | ✗ |
| stairwell_tiled | south | brick | 0.378 | generic_wall | ✗ |
| stairwell_tiled | west | brick | 0.378 | generic_wall | ✗ |
| arena_ntsu_linkou | north | curtain_fabric | 0.315 | gypsum_board | ✗ |
| arena_ntsu_linkou | east | curtain_fabric | 0.315 | gypsum_board | ✗ |
| arena_ntsu_linkou | south | curtain_fabric | 0.315 | gypsum_board | ✗ |
| arena_ntsu_linkou | west | curtain_fabric | 0.315 | gypsum_board | ✗ |
| CathedralRoom | north | acoustic_panel | 0.258 | concrete | ✗ |
| CathedralRoom | east | glass | 0.278 | concrete | ✗ |
| CathedralRoom | west | acoustic_panel | 0.226 | concrete | ✗ |
| site_photo_department_store | north | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_department_store | east | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_department_store | south | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_department_store | west | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_restaurant | north | acoustic_panel | 0.347 | brick | ✗ |
| site_photo_restaurant | east | acoustic_panel | 0.347 | brick | ✗ |
| site_photo_restaurant | south | acoustic_panel | 0.347 | brick | ✗ |
| site_photo_restaurant | west | acoustic_panel | 0.347 | brick | ✗ |
| RacquetballCourt4 | north | gypsum_board | 0.308 | gypsum_board | ✓ |
| SteinmanHall | north | audience_seating | 0.394 | gypsum_board | ✗ |
| SteinmanHall | east | acoustic_panel | 0.358 | gypsum_board | ✗ |
| SteinmanHall | south | curtain_fabric | 0.390 | gypsum_board | ✗ |
| TunnelToHell | north | acoustic_panel | 0.213 | concrete | ✗ |
| TunnelToHell | east | acoustic_panel | 0.213 | concrete | ✗ |
| TunnelToHell | south | acoustic_panel | 0.213 | marble | ✗ |
| TunnelToHell | west | acoustic_panel | 0.213 | concrete | ✗ |

