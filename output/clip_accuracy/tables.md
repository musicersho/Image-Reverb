## 表 1：總體正確率

| 指標 | 數值 |
|---|---|
| 總面數 | 78 |
| 排除（ground truth = unknown） | 2 |
| 正確率分母 | 76 |
| 正確率 | 32/76（42.1%） |
| 其中：非 proxy（真實材質在 12 候選內）正確率 | 31/60（51.7%） |
| 其中：proxy（近似值，真實材質不在候選內）正確率 | 1/16（6.2%） |


## 表 2：按判定來源分組的正確率

| 來源 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| clip | 22 | 1 | 11/21（52.4%） |
| fallback | 32 | 0 | 15/32（46.9%） |
| out_of_domain | 13 | 0 | 5/13（38.5%） |
| 無來源 | 11 | 1 | 1/10（10.0%） |


## 表 3：按照片分組的正確率

| 照片 | 面數 | 排除數 | 正確率 |
|---|---|---|---|
| bathroom_tiled | 6 | 0 | 6/6（100.0%） |
| bedroom_ai_generated | 6 | 0 | 0/6（0.0%） |
| stairwell_tiled | 6 | 0 | 0/6（0.0%） |
| arena_ntsu_linkou | 6 | 1 | 4/5（80.0%） |
| car_interior_suv | 6 | 0 | 0/6（0.0%） |
| CathedralRoom | 6 | 0 | 0/6（0.0%） |
| DivorceBeach | 6 | 1 | 1/5（20.0%） |
| site_photo_department_store | 6 | 0 | 5/6（83.3%） |
| site_photo_gym | 6 | 0 | 4/6（66.7%） |
| site_photo_restaurant | 6 | 0 | 0/6（0.0%） |
| RacquetballCourt4 | 6 | 0 | 5/6（83.3%） |
| SteinmanHall | 6 | 0 | 6/6（100.0%） |
| TunnelToHell | 6 | 0 | 1/6（16.7%） |


## 表 4：錯誤型態份額

| 錯誤型態 | 面數 |
|---|---|
| in-set 誤判（source=clip 但答案錯，地雷 #18 型） | 10 |
| 不該 fallback 而 fallback（top-1 其實對，門檻擋掉了） | 3 |
| 確實該 fallback（top-1 也錯，真的不知道） | 29 |
| 域外誤觸（判成 out_of_domain，但候選裡其實有對的答案） | 2 |
| 確實域外（out_of_domain 判定合理，候選裡沒有對的答案） | 11 |
| 無法判斷（無來源或缺 top3 明細） | 10 |


## 表 5：地雷 #18 型 in-set 誤判明細

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
| TunnelToHell | east | gypsum_board | concrete |


## 表 6：fallback 門檻（0.4）敏感度分析

| 候選門檻 | 會被放行到 clip 的面數 | 放行後答對 | 放行後答錯 |
|---|---|---|---|
| 0.20 | 32 | 3 | 29 |
| 0.25 | 29 | 3 | 26 |
| 0.30 | 26 | 3 | 23 |
| 0.35 | 9 | 1 | 8 |
| 0.40 | 0 | 0 | 0 |


### fallback 面逐面明細（top-1 原始候選 vs ground truth）

| 照片 | 面 | top-1 原始候選 | top-1 信心 | ground truth | top-1 是否正確 |
|---|---|---|---|---|---|
| bathroom_tiled | floor | generic_wall | 0.352 | gypsum_board | ✗ |
| bedroom_ai_generated | floor | generic_wall | 0.244 | wood_panel | ✗ |
| stairwell_tiled | floor | generic_wall | 0.313 | marble | ✗ |
| stairwell_tiled | ceiling | acoustic_panel | 0.305 | generic_wall | ✗ |
| stairwell_tiled | north | brick | 0.378 | generic_wall | ✗ |
| stairwell_tiled | east | brick | 0.378 | generic_wall | ✗ |
| stairwell_tiled | south | brick | 0.378 | generic_wall | ✗ |
| stairwell_tiled | west | brick | 0.378 | generic_wall | ✗ |
| arena_ntsu_linkou | north | curtain_fabric | 0.315 | gypsum_board | ✗ |
| arena_ntsu_linkou | east | curtain_fabric | 0.315 | gypsum_board | ✗ |
| arena_ntsu_linkou | south | curtain_fabric | 0.315 | gypsum_board | ✗ |
| arena_ntsu_linkou | west | curtain_fabric | 0.315 | gypsum_board | ✗ |
| CathedralRoom | floor | concrete | 0.345 | concrete | ✓ |
| CathedralRoom | north | acoustic_panel | 0.258 | concrete | ✗ |
| CathedralRoom | east | glass | 0.278 | concrete | ✗ |
| CathedralRoom | west | acoustic_panel | 0.226 | concrete | ✗ |
| site_photo_department_store | ceiling | gypsum_board | 0.384 | gypsum_board | ✓ |
| site_photo_department_store | north | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_department_store | east | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_department_store | south | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_department_store | west | curtain_fabric | 0.336 | gypsum_board | ✗ |
| site_photo_restaurant | north | acoustic_panel | 0.347 | brick | ✗ |
| site_photo_restaurant | east | acoustic_panel | 0.347 | brick | ✗ |
| site_photo_restaurant | south | acoustic_panel | 0.347 | brick | ✗ |
| site_photo_restaurant | west | acoustic_panel | 0.347 | brick | ✗ |
| RacquetballCourt4 | north | gypsum_board | 0.308 | gypsum_board | ✓ |
| SteinmanHall | floor | acoustic_panel | 0.210 | gypsum_board | ✗ |
| SteinmanHall | north | audience_seating | 0.394 | gypsum_board | ✗ |
| SteinmanHall | east | acoustic_panel | 0.358 | gypsum_board | ✗ |
| SteinmanHall | south | curtain_fabric | 0.390 | gypsum_board | ✗ |
| TunnelToHell | floor | acoustic_panel | 0.302 | marble | ✗ |
| TunnelToHell | west | gypsum_board | 0.273 | concrete | ✗ |


## 表 7：判定全對天花板模擬

| 照片 | 型態 | 實際 materials_confidence | 模擬（全對）materials_confidence | 模擬結果六面同材質 | 模擬後達到 high | 備註 |
|---|---|---|---|---|---|---|
| bathroom_tiled | perspective | low | medium | 否 | 否 |  |
| bedroom_ai_generated | perspective | low | medium | 否 | 否 |  |
| stairwell_tiled | perspective | low | medium | 否 | 否 |  |
| arena_ntsu_linkou | perspective | low | medium | 否 | 否 |  |
| car_interior_suv | perspective | low | medium | 否 | 否 | 🔺 舊架構限制未反映 |
| CathedralRoom | equirect | low | low | 是 | 否 |  |
| DivorceBeach | equirect | medium | medium | 否 | 否 |  |
| site_photo_department_store | perspective | low | medium | 否 | 否 |  |
| site_photo_gym | perspective | low | medium | 否 | 否 |  |
| site_photo_restaurant | perspective | low | medium | 否 | 否 |  |
| RacquetballCourt4 | equirect | low | high | 否 | 是 |  |
| SteinmanHall | equirect | low | high | 否 | 是 |  |
| TunnelToHell | equirect | low | high | 否 | 是 |  |
