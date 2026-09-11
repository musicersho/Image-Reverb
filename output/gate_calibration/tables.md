## 表 1（證據①）：13 張照片新基準率（`role_aware=False` vs `True`）

| 照片 | geometry（default） | materials（default） | overall（default） | gate（default） | geometry（role_aware） | materials（role_aware） | overall（role_aware） | gate（role_aware） |
|---|---|---|---|---|---|---|---|---|
| bathroom_tiled | medium | low | low | BLOCK | medium | medium | medium | pass |
| bedroom_ai_generated | medium | low | low | BLOCK | medium | low | low | BLOCK |
| stairwell_tiled | medium | low | low | BLOCK | medium | low | low | BLOCK |
| arena_ntsu_linkou | low | low | low | BLOCK | low | low | low | BLOCK |
| car_interior_suv | low | low | low | BLOCK | low | low | low | BLOCK |
| CathedralRoom | medium | low | low | BLOCK | medium | low | low | BLOCK |
| DivorceBeach | low | medium | low | BLOCK | low | medium | low | BLOCK |
| site_photo_department_store | medium | low | low | BLOCK | low | low | low | BLOCK |
| site_photo_gym | low | low | low | BLOCK | low | low | low | BLOCK |
| site_photo_restaurant | low | low | low | BLOCK | low | low | low | BLOCK |
| RacquetballCourt4 | medium | low | low | BLOCK | medium | low | low | BLOCK |
| SteinmanHall | low | low | low | BLOCK | low | low | low | BLOCK |
| TunnelToHell | low | low | low | BLOCK | low | low | low | BLOCK |


## 表 2（證據②）：`default` 模式被放行（gate=pass）案例逐面 vs ground truth

（本模式下 13 張全數 BLOCK，無 pass 案例）


## 表 2（證據②）：`role_aware` 模式被放行（gate=pass）案例逐面 vs ground truth

| 照片 | 面 | AI 判定 | 來源 | ground truth | 是否正確 |
|---|---|---|---|---|---|
| bathroom_tiled | floor | carpet | clip | gypsum_board | ✗ |
| bathroom_tiled | ceiling | gypsum_board | 無來源 | vinyl_panel | ✗ |
| bathroom_tiled | north | generic_wall | clip | generic_wall | ✓ |
| bathroom_tiled | east | generic_wall | clip | generic_wall | ✓ |
| bathroom_tiled | south | generic_wall | clip | generic_wall | ✓ |
| bathroom_tiled | west | generic_wall | clip | generic_wall | ✓ |


## 表 3（證據③）：已知錯誤案例（鐵則 12）在兩模式的 gate 結果

| 照片 | gate（default） | gate（role_aware） |
|---|---|---|
| bathroom_tiled | BLOCK | pass |
| bedroom_ai_generated | BLOCK | BLOCK |
| site_photo_gym | BLOCK | BLOCK |
| site_photo_restaurant | BLOCK | BLOCK |
| RacquetballCourt4 | BLOCK | BLOCK |


## 表 4（證據④）：`bedroom_ai_generated` 續擋檢查

| 模式 | geometry | materials | overall | gate | floor top-1 機率 |
|---|---|---|---|---|---|
| default | medium | low | low | BLOCK | 0.2436 |
| role_aware | medium | low | low | BLOCK | 0.3394 |


## 表 5（證據⑤）：每面 top-1 機率兩模式位移（67 面全量，按角色排序）

| 角色 | 照片 | 面 | method（default） | conf（default） | method（role_aware） | conf（role_aware） | 位移 Δ | 距門檻 0.4（default） | 距門檻 0.4（role_aware） |
|---|---|---|---|---|---|---|---|---|---|
| floor | CathedralRoom | floor | fallback | 0.3448 | clip | 0.4970 | +0.1522 | 0.0552 | 0.0970 |
| floor | DivorceBeach | floor | clip | 0.4318 | clip | 0.5803 | +0.1485 | 0.0318 | 0.1803 |
| floor | RacquetballCourt4 | floor | clip | 0.5921 | clip | 0.7400 | +0.1479 | 0.1921 | 0.3400 |
| floor | SteinmanHall | floor | fallback | 0.2105 | fallback | 0.3309 | +0.1204 | 0.1895 | 0.0691 |
| floor | TunnelToHell | floor | out_of_domain | 0.3535 | out_of_domain | 0.6457 | +0.2922 | 0.0465 | 0.2457 |
| floor | bathroom_tiled | floor | fallback | 0.3516 | clip | 0.4044 | +0.0528 | 0.0484 | 0.0044 |
| floor | bedroom_ai_generated | floor | fallback | 0.2436 | fallback | 0.3394 | +0.0958 | 0.1564 | 0.0606 |
| floor | car_interior_suv | floor | clip | 0.5421 | out_of_domain | 0.4692 | -0.0729 | 0.1421 | 0.0692 |
| floor | site_photo_department_store | floor | clip | 0.9356 | out_of_domain | 0.2603 | -0.6753 | 0.5356 | 0.1397 |
| floor | site_photo_gym | floor | clip | 0.5662 | clip | 0.4878 | -0.0784 | 0.1662 | 0.0878 |
| floor | stairwell_tiled | floor | fallback | 0.3133 | clip | 0.4294 | +0.1161 | 0.0867 | 0.0294 |
| ceiling | CathedralRoom | ceiling | out_of_domain | 0.5612 | out_of_domain | 0.7255 | +0.1643 | 0.1612 | 0.3255 |
| ceiling | RacquetballCourt4 | ceiling | out_of_domain | 0.3625 | out_of_domain | 0.5003 | +0.1378 | 0.0375 | 0.1003 |
| ceiling | SteinmanHall | ceiling | clip | 0.6845 | clip | 0.8688 | +0.1843 | 0.2845 | 0.4688 |
| ceiling | TunnelToHell | ceiling | fallback | 0.2419 | out_of_domain | 0.3346 | +0.0927 | 0.1581 | 0.0654 |
| ceiling | arena_ntsu_linkou | ceiling | clip | 0.8299 | clip | 0.8346 | +0.0047 | 0.4299 | 0.4346 |
| ceiling | site_photo_department_store | ceiling | fallback | 0.3840 | clip | 0.5017 | +0.1177 | 0.0160 | 0.1017 |
| ceiling | site_photo_restaurant | ceiling | clip | 0.6606 | clip | 0.8947 | +0.2341 | 0.2606 | 0.4947 |
| ceiling | stairwell_tiled | ceiling | fallback | 0.3051 | clip | 0.4331 | +0.1280 | 0.0949 | 0.0331 |
| wall | CathedralRoom | east | fallback | 0.2776 | fallback | 0.2776 | +0.0000 | 0.1224 | 0.1224 |
| wall | CathedralRoom | north | fallback | 0.2579 | fallback | 0.2579 | +0.0000 | 0.1421 | 0.1421 |
| wall | CathedralRoom | south | out_of_domain | 0.8103 | out_of_domain | 0.8103 | +0.0000 | 0.4103 | 0.4103 |
| wall | CathedralRoom | west | fallback | 0.2258 | fallback | 0.2258 | +0.0000 | 0.1742 | 0.1742 |
| wall | RacquetballCourt4 | east | clip | 0.8965 | clip | 0.8965 | +0.0000 | 0.4965 | 0.4965 |
| wall | RacquetballCourt4 | north | fallback | 0.3079 | fallback | 0.3079 | +0.0000 | 0.0921 | 0.0921 |
| wall | RacquetballCourt4 | south | clip | 0.5421 | clip | 0.5421 | +0.0000 | 0.1421 | 0.1421 |
| wall | RacquetballCourt4 | west | clip | 0.4860 | clip | 0.4860 | +0.0000 | 0.0860 | 0.0860 |
| wall | SteinmanHall | east | fallback | 0.3578 | fallback | 0.3578 | +0.0000 | 0.0422 | 0.0422 |
| wall | SteinmanHall | north | fallback | 0.3941 | fallback | 0.3941 | +0.0000 | 0.0059 | 0.0059 |
| wall | SteinmanHall | south | fallback | 0.3895 | fallback | 0.3895 | +0.0000 | 0.0105 | 0.0105 |
| wall | SteinmanHall | west | clip | 0.7355 | clip | 0.7355 | +0.0000 | 0.3355 | 0.3355 |
| wall | TunnelToHell | east | fallback | 0.2130 | fallback | 0.2130 | +0.0000 | 0.1870 | 0.1870 |
| wall | TunnelToHell | north | fallback | 0.2130 | fallback | 0.2130 | +0.0000 | 0.1870 | 0.1870 |
| wall | TunnelToHell | south | fallback | 0.2130 | fallback | 0.2130 | +0.0000 | 0.1870 | 0.1870 |
| wall | TunnelToHell | west | fallback | 0.2130 | fallback | 0.2130 | +0.0000 | 0.1870 | 0.1870 |
| wall | arena_ntsu_linkou | east | fallback | 0.3153 | fallback | 0.3153 | +0.0000 | 0.0847 | 0.0847 |
| wall | arena_ntsu_linkou | north | fallback | 0.3153 | fallback | 0.3153 | +0.0000 | 0.0847 | 0.0847 |
| wall | arena_ntsu_linkou | south | fallback | 0.3153 | fallback | 0.3153 | +0.0000 | 0.0847 | 0.0847 |
| wall | arena_ntsu_linkou | west | fallback | 0.3153 | fallback | 0.3153 | +0.0000 | 0.0847 | 0.0847 |
| wall | bathroom_tiled | east | clip | 0.7178 | clip | 0.7178 | +0.0000 | 0.3178 | 0.3178 |
| wall | bathroom_tiled | north | clip | 0.7178 | clip | 0.7178 | +0.0000 | 0.3178 | 0.3178 |
| wall | bathroom_tiled | south | clip | 0.7178 | clip | 0.7178 | +0.0000 | 0.3178 | 0.3178 |
| wall | bathroom_tiled | west | clip | 0.7178 | clip | 0.7178 | +0.0000 | 0.3178 | 0.3178 |
| wall | bedroom_ai_generated | east | clip | 0.4791 | clip | 0.4791 | +0.0000 | 0.0791 | 0.0791 |
| wall | bedroom_ai_generated | north | clip | 0.4791 | clip | 0.4791 | +0.0000 | 0.0791 | 0.0791 |
| wall | bedroom_ai_generated | south | clip | 0.4791 | clip | 0.4791 | +0.0000 | 0.0791 | 0.0791 |
| wall | bedroom_ai_generated | west | clip | 0.4791 | clip | 0.4791 | +0.0000 | 0.0791 | 0.0791 |
| wall | car_interior_suv | east | out_of_domain | 0.7354 | out_of_domain | 0.7354 | +0.0000 | 0.3354 | 0.3354 |
| wall | car_interior_suv | north | out_of_domain | 0.7354 | out_of_domain | 0.7354 | +0.0000 | 0.3354 | 0.3354 |
| wall | car_interior_suv | south | out_of_domain | 0.7354 | out_of_domain | 0.7354 | +0.0000 | 0.3354 | 0.3354 |
| wall | car_interior_suv | west | out_of_domain | 0.7354 | out_of_domain | 0.7354 | +0.0000 | 0.3354 | 0.3354 |
| wall | site_photo_department_store | east | fallback | 0.3364 | fallback | 0.3364 | +0.0000 | 0.0636 | 0.0636 |
| wall | site_photo_department_store | north | fallback | 0.3364 | fallback | 0.3364 | +0.0000 | 0.0636 | 0.0636 |
| wall | site_photo_department_store | south | fallback | 0.3364 | fallback | 0.3364 | +0.0000 | 0.0636 | 0.0636 |
| wall | site_photo_department_store | west | fallback | 0.3364 | fallback | 0.3364 | +0.0000 | 0.0636 | 0.0636 |
| wall | site_photo_gym | east | out_of_domain | 0.5244 | out_of_domain | 0.5244 | +0.0000 | 0.1244 | 0.1244 |
| wall | site_photo_gym | north | out_of_domain | 0.5244 | out_of_domain | 0.5244 | +0.0000 | 0.1244 | 0.1244 |
| wall | site_photo_gym | south | out_of_domain | 0.5244 | out_of_domain | 0.5244 | +0.0000 | 0.1244 | 0.1244 |
| wall | site_photo_gym | west | out_of_domain | 0.5244 | out_of_domain | 0.5244 | +0.0000 | 0.1244 | 0.1244 |
| wall | site_photo_restaurant | east | fallback | 0.3471 | fallback | 0.3471 | +0.0000 | 0.0529 | 0.0529 |
| wall | site_photo_restaurant | north | fallback | 0.3471 | fallback | 0.3471 | +0.0000 | 0.0529 | 0.0529 |
| wall | site_photo_restaurant | south | fallback | 0.3471 | fallback | 0.3471 | +0.0000 | 0.0529 | 0.0529 |
| wall | site_photo_restaurant | west | fallback | 0.3471 | fallback | 0.3471 | +0.0000 | 0.0529 | 0.0529 |
| wall | stairwell_tiled | east | fallback | 0.3784 | fallback | 0.3784 | +0.0000 | 0.0216 | 0.0216 |
| wall | stairwell_tiled | north | fallback | 0.3784 | fallback | 0.3784 | +0.0000 | 0.0216 | 0.0216 |
| wall | stairwell_tiled | south | fallback | 0.3784 | fallback | 0.3784 | +0.0000 | 0.0216 | 0.0216 |
| wall | stairwell_tiled | west | fallback | 0.3784 | fallback | 0.3784 | +0.0000 | 0.0216 | 0.0216 |


### 距門檻 <0.05 的面清單（按角色分）


**floor**

| 照片 | 面 | conf（default） | conf（role_aware） | 距門檻（default） | 距門檻（role_aware） |
|---|---|---|---|---|---|
| bathroom_tiled | floor | 0.3516 | 0.4044 | 0.0484 | 0.0044 |
| stairwell_tiled | floor | 0.3133 | 0.4294 | 0.0867 | 0.0294 |
| DivorceBeach | floor | 0.4318 | 0.5803 | 0.0318 | 0.1803 |
| TunnelToHell | floor | 0.3535 | 0.6457 | 0.0465 | 0.2457 |

**ceiling**

| 照片 | 面 | conf（default） | conf（role_aware） | 距門檻（default） | 距門檻（role_aware） |
|---|---|---|---|---|---|
| stairwell_tiled | ceiling | 0.3051 | 0.4331 | 0.0949 | 0.0331 |
| site_photo_department_store | ceiling | 0.3840 | 0.5017 | 0.0160 | 0.1017 |
| RacquetballCourt4 | ceiling | 0.3625 | 0.5003 | 0.0375 | 0.1003 |

**wall**

| 照片 | 面 | conf（default） | conf（role_aware） | 距門檻（default） | 距門檻（role_aware） |
|---|---|---|---|---|---|
| stairwell_tiled | north | 0.3784 | 0.3784 | 0.0216 | 0.0216 |
| stairwell_tiled | east | 0.3784 | 0.3784 | 0.0216 | 0.0216 |
| stairwell_tiled | south | 0.3784 | 0.3784 | 0.0216 | 0.0216 |
| stairwell_tiled | west | 0.3784 | 0.3784 | 0.0216 | 0.0216 |
| SteinmanHall | north | 0.3941 | 0.3941 | 0.0059 | 0.0059 |
| SteinmanHall | east | 0.3578 | 0.3578 | 0.0422 | 0.0422 |
| SteinmanHall | south | 0.3895 | 0.3895 | 0.0105 | 0.0105 |


### T-44 第四輪 9 面信心上升交叉檢查（程式化核對，非手打）

- ✅ CathedralRoom.ceiling：T-44 第四輪記錄 0.5612→0.7255（上升）；本卡本次重測 0.5612→0.7255（上升，與歷史記錄數值逐位元相同）
- ✅ DivorceBeach.floor：T-44 第四輪記錄 0.4318→0.5803（上升）；本卡本次重測 0.4318→0.5803（上升，與歷史記錄數值逐位元相同）
- ✅ RacquetballCourt4.ceiling：T-44 第四輪記錄 0.3625→0.5003（上升）；本卡本次重測 0.3625→0.5003（上升，與歷史記錄數值逐位元相同）
- ✅ RacquetballCourt4.floor：T-44 第四輪記錄 0.5921→0.7400（上升）；本卡本次重測 0.5921→0.7400（上升，與歷史記錄數值逐位元相同）
- ✅ SteinmanHall.ceiling：T-44 第四輪記錄 0.6845→0.8688（上升）；本卡本次重測 0.6845→0.8688（上升，與歷史記錄數值逐位元相同）
- ✅ SteinmanHall.floor：T-44 第四輪記錄 0.2105→0.3309（上升）；本卡本次重測 0.2105→0.3309（上升，與歷史記錄數值逐位元相同）
- ✅ TunnelToHell.floor：T-44 第四輪記錄 0.3535→0.6457（上升）；本卡本次重測 0.3535→0.6457（上升，與歷史記錄數值逐位元相同）
- ✅ bedroom_ai_generated.floor：T-44 第四輪記錄 0.2436→0.3394（上升）；本卡本次重測 0.2436→0.3394（上升，與歷史記錄數值逐位元相同）
- ✅ site_photo_restaurant.ceiling：T-44 第四輪記錄 0.6606→0.8947（上升）；本卡本次重測 0.6606→0.8947（上升，與歷史記錄數值逐位元相同）


## 表 6（證據⑥）：`default` 模式 fallback 門檻（0.4）敏感度分析——按角色分開


### floor

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 5 | 1 | 4 |
| 0.25 | 3 | 1 | 2 |
| 0.30 | 3 | 1 | 2 |
| 0.35 | 1 | 0 | 1 |
| 0.40 | 0 | 0 | 0 |

### ceiling

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 3 | 1 | 2 |
| 0.25 | 2 | 1 | 1 |
| 0.30 | 2 | 1 | 1 |
| 0.35 | 1 | 1 | 0 |
| 0.40 | 0 | 0 | 0 |

### wall

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 27 | 1 | 26 |
| 0.25 | 22 | 1 | 21 |
| 0.30 | 20 | 1 | 19 |
| 0.35 | 7 | 0 | 7 |
| 0.40 | 0 | 0 | 0 |


## 表 6（證據⑥）：`role_aware` 模式 fallback 門檻（0.4）敏感度分析——按角色分開


### floor

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 2 | 0 | 2 |
| 0.25 | 2 | 0 | 2 |
| 0.30 | 2 | 0 | 2 |
| 0.35 | 0 | 0 | 0 |
| 0.40 | 0 | 0 | 0 |

### ceiling

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 0 | 0 | 0 |
| 0.25 | 0 | 0 | 0 |
| 0.30 | 0 | 0 | 0 |
| 0.35 | 0 | 0 | 0 |
| 0.40 | 0 | 0 | 0 |

### wall

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 27 | 1 | 26 |
| 0.25 | 22 | 1 | 21 |
| 0.30 | 20 | 1 | 19 |
| 0.35 | 7 | 0 | 7 |
| 0.40 | 0 | 0 | 0 |


## 表 7（證據⑦a，唯讀模擬，只算不採用）：門檻依候選數 n 調整（`threshold(n)=min(0.99, 0.4×16/n)`）對 gate 的影響

⚠️ 已知近似：`materials_sim` 是唯讀呼叫現行 `compute_materials_confidence()` 算出（規則 1～4 零改動），但餵進去的 `warnings` 沿用**該面實際那次真跑**留下的警示文字，未依模擬後的 method 重新產生——如果某面實際是 fallback／out_of_domain（有警示字串）而本模擬把它翻成 clip，規則 3「全 clip 且無 warnings→high」仍可能因為殘留的警示字串而判不到 `high`（偏保守，不影響 `low` 的判定，`low`／`gate` 才是本卡的量測重點）。


### `default` 模式

| 照片 | 會翻轉的面（method 變化＋等效門檻） | 模擬 materials | 模擬 gate |
|---|---|---|---|
| bathroom_tiled | （無） | low | low |
| bedroom_ai_generated | （無） | low | low |
| stairwell_tiled | （無） | low | low |
| arena_ntsu_linkou | （無） | low | low |
| car_interior_suv | （無） | low | low |
| CathedralRoom | （無） | low | low |
| DivorceBeach | （無） | medium | low |
| site_photo_department_store | （無） | low | low |
| site_photo_gym | （無） | low | low |
| site_photo_restaurant | （無） | low | low |
| RacquetballCourt4 | （無） | low | low |
| SteinmanHall | （無） | low | low |
| TunnelToHell | （無） | low | low |

### `role_aware` 模式

| 照片 | 會翻轉的面（method 變化＋等效門檻） | 模擬 materials | 模擬 gate |
|---|---|---|---|
| bathroom_tiled | floor（clip→fallback，eff_threshold=0.640） | low | low |
| bedroom_ai_generated | （無） | low | low |
| stairwell_tiled | floor（clip→fallback，eff_threshold=0.640）；ceiling（clip→fallback，eff_threshold=0.800） | low | low |
| arena_ntsu_linkou | （無） | low | low |
| car_interior_suv | （無） | low | low |
| CathedralRoom | floor（clip→fallback，eff_threshold=0.640） | low | low |
| DivorceBeach | floor（clip→fallback，eff_threshold=0.640） | low | low |
| site_photo_department_store | ceiling（clip→fallback，eff_threshold=0.800） | low | low |
| site_photo_gym | floor（clip→fallback，eff_threshold=0.640） | low | low |
| site_photo_restaurant | （無） | low | low |
| RacquetballCourt4 | （無） | low | low |
| SteinmanHall | （無） | low | low |
| TunnelToHell | （無） | low | low |


## 表 8（證據⑦b，唯讀模擬，只算不採用）：`compute_materials_confidence()` 規則 4 加「候選集收窄的 clip 面不得直接 medium」對 gate 的影響


### `default` 模式

| 照片 | 實際 materials_confidence | 模擬 materials_confidence |
|---|---|---|
| bathroom_tiled | low | low |
| bedroom_ai_generated | low | low |
| stairwell_tiled | low | low |
| arena_ntsu_linkou | low | low |
| car_interior_suv | low | low |
| CathedralRoom | low | low |
| DivorceBeach | medium | medium |
| site_photo_department_store | low | low |
| site_photo_gym | low | low |
| site_photo_restaurant | low | low |
| RacquetballCourt4 | low | low |
| SteinmanHall | low | low |
| TunnelToHell | low | low |

### `role_aware` 模式

| 照片 | 實際 materials_confidence | 模擬 materials_confidence |
|---|---|---|
| bathroom_tiled | medium | low（模擬：候選集收窄的 clip 面不得直接 medium） |
| bedroom_ai_generated | low | low |
| stairwell_tiled | low | low |
| arena_ntsu_linkou | low | low |
| car_interior_suv | low | low |
| CathedralRoom | low | low |
| DivorceBeach | medium | low（模擬：候選集收窄的 clip 面不得直接 medium） |
| site_photo_department_store | low | low |
| site_photo_gym | low | low |
| site_photo_restaurant | low | low |
| RacquetballCourt4 | low | low |
| SteinmanHall | low | low |
| TunnelToHell | low | low |
