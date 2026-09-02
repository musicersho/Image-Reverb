## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 29/76（38.2%） |
| 非 proxy 正確率 | 27/63（42.9%） |
| proxy 正確率 | 2/13（15.4%） |


## 表 2：按判定來源分組

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 30 | 1 | 14/29（48.3%） |
| fallback | 22 | 0 | 10/22（45.5%） |
| out_of_domain | 15 | 0 | 5/15（33.3%） |
| 無來源 | 11 | 1 | 0/10（0.0%） |


## 表 3：按角色分組

| 角色 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| floor | 13 | 0 | 5/13（38.5%） |
| ceiling | 13 | 2 | 4/11（36.4%） |
| wall | 52 | 0 | 20/52（38.5%） |


## 表 4：地雷 #18 型 in-set 誤判明細

| 照片 | 面 | AI 判定 | ground truth |
|---|---|---|---|
| bathroom_tiled | floor | carpet | gypsum_board |
| bedroom_ai_generated | north | generic_wall | concrete |
| bedroom_ai_generated | east | generic_wall | concrete |
| bedroom_ai_generated | south | generic_wall | concrete |
| bedroom_ai_generated | west | generic_wall | concrete |
| site_photo_gym | floor | concrete | rubber_flooring |
| site_photo_restaurant | ceiling | curtain_fabric | gypsum_board |
| site_photo_restaurant | north | acoustic_panel | brick |
| site_photo_restaurant | east | acoustic_panel | brick |
| site_photo_restaurant | south | acoustic_panel | brick |
| site_photo_restaurant | west | acoustic_panel | brick |
| RacquetballCourt4 | west | curtain_fabric | glass |
| SteinmanHall | north | acoustic_panel | gypsum_board |
| SteinmanHall | east | acoustic_panel | gypsum_board |
| SteinmanHall | south | curtain_fabric | gypsum_board |


## 表 7'：fallback 門檻（0.4）敏感度分析——按角色分開（PLAN_T44.md §4）


### floor

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 2 | 0 | 2 |
| 0.25 | 2 | 0 | 2 |
| 0.30 | 2 | 0 | 2 |
| 0.35 | 0 | 0 | 0 |
| 0.40 | 0 | 0 | 0 |


| 照片 | 面 | top-1 原始候選 | top-1 信心 | ground truth | 是否正確 |
|---|---|---|---|---|---|
| bedroom_ai_generated | floor | concrete | 0.339 | wood_panel | ✗ |
| SteinmanHall | floor | concrete | 0.331 | gypsum_board | ✗ |

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
| 0.20 | 20 | 1 | 19 |
| 0.25 | 15 | 1 | 14 |
| 0.30 | 13 | 1 | 12 |
| 0.35 | 12 | 0 | 12 |
| 0.40 | 0 | 0 | 0 |


| 照片 | 面 | top-1 原始候選 | top-1 信心 | ground truth | 是否正確 |
|---|---|---|---|---|---|
| stairwell_tiled | north | brick | 0.391 | generic_wall | ✗ |
| stairwell_tiled | east | brick | 0.391 | generic_wall | ✗ |
| stairwell_tiled | south | brick | 0.391 | generic_wall | ✗ |
| stairwell_tiled | west | brick | 0.391 | generic_wall | ✗ |
| arena_ntsu_linkou | north | curtain_fabric | 0.394 | gypsum_board | ✗ |
| arena_ntsu_linkou | east | curtain_fabric | 0.394 | gypsum_board | ✗ |
| arena_ntsu_linkou | south | curtain_fabric | 0.394 | gypsum_board | ✗ |
| arena_ntsu_linkou | west | curtain_fabric | 0.394 | gypsum_board | ✗ |
| CathedralRoom | north | acoustic_panel | 0.281 | concrete | ✗ |
| CathedralRoom | east | glass | 0.296 | concrete | ✗ |
| CathedralRoom | west | acoustic_panel | 0.241 | concrete | ✗ |
| site_photo_department_store | north | curtain_fabric | 0.394 | gypsum_board | ✗ |
| site_photo_department_store | east | curtain_fabric | 0.394 | gypsum_board | ✗ |
| site_photo_department_store | south | curtain_fabric | 0.394 | gypsum_board | ✗ |
| site_photo_department_store | west | curtain_fabric | 0.394 | gypsum_board | ✗ |
| RacquetballCourt4 | north | gypsum_board | 0.310 | gypsum_board | ✓ |
| TunnelToHell | north | acoustic_panel | 0.222 | concrete | ✗ |
| TunnelToHell | east | acoustic_panel | 0.222 | concrete | ✗ |
| TunnelToHell | south | acoustic_panel | 0.222 | marble | ✗ |
| TunnelToHell | west | acoustic_panel | 0.222 | concrete | ✗ |

