# T-37 再基線表（程式產出，地雷 #15）

## 表 1：極點列均勻度統計量（步驟 1 量測）

| 照片 | 尺寸 | 長寬比 | 首列 diff | 末列 diff | max(首,末) | 真環景？ |
|---|---|---|---|---|---|---|
| CathedralRoom | 960x480 | 2.0 | 0.2628 | 0.4859 | 0.4859 | 是 |
| DivorceBeach | 4096x2048 | 2.0 | 0.1158 | 0.1636 | 0.1636 | 是 |
| RacquetballCourt4 | 960x480 | 2.0 | 0.3545 | 0.4734 | 0.4734 | 是 |
| SteinmanHall | 4096x2048 | 2.0 | 0.2007 | 0.1724 | 0.2007 | 是 |
| TunnelToHell | 2592x1296 | 2.0 | 4.5149 | 3.1984 | 4.5149 | 否 |

真環景 max(max_diff) = **0.4859**；TunnelToHell = **4.5149**；門檻 `config.EQUIRECT_POLE_DIFF_THRESHOLD = 1.2`（真環景側餘裕 2.47x、TunnelToHell 側餘裕 3.76x）。

## 表 2：13 張三軸 confidence／gate before/after 對照

| 照片 | dims_source (前→後) | geometry (前→後) | materials (前→後) | overall (前→後) | 變動？ |
|---|---|---|---|---|---|
| bathroom_tiled | metric_depth → metric_depth | medium → medium | low → low | low → low | — |
| bedroom_ai_generated | metric_depth → metric_depth | medium → medium | low → low | low → low | — |
| stairwell_tiled | metric_depth → metric_depth | medium → medium | low → low | low → low | — |
| arena_ntsu_linkou | metric_depth → metric_depth | low → low | low → low | low → low | — |
| car_interior_suv | metric_depth → metric_depth | low → low | low → low | low → low | — |
| CathedralRoom | equirect_multiview → equirect_multiview | medium → medium | low → low | low → low | — |
| DivorceBeach | equirect_multiview → equirect_multiview | low → low | medium → medium | low → low | — |
| site_photo_department_store | metric_depth → metric_depth | medium → medium | low → low | low → low | — |
| site_photo_gym | metric_depth → metric_depth | low → low | low → low | low → low | — |
| site_photo_restaurant | metric_depth → metric_depth | low → low | low → low | low → low | — |
| RacquetballCourt4 | equirect_multiview → equirect_multiview | medium → medium | low → low | low → low | — |
| SteinmanHall | equirect_multiview → equirect_multiview | low → low | low → low | low → low | — |
| TunnelToHell | equirect_multiview → metric_depth | medium → low | low → low | low → low | ⚠️ 變動 |

## 表 3：逐面材質判定漂移（預期只有 TunnelToHell 6 面）

| 照片 | 面 | AI 判定 (前→後) | 來源 (前→後) | ground truth | 正確？ (前→後) |
|---|---|---|---|---|---|
| TunnelToHell | floor | gypsum_board → gypsum_board | fallback → out_of_domain | marble | False → False |
| TunnelToHell | ceiling | gypsum_board → gypsum_board | out_of_domain → fallback | concrete | False → False |
| TunnelToHell | north | gypsum_board → gypsum_board | out_of_domain → fallback | concrete | False → False |
| TunnelToHell | east | gypsum_board → gypsum_board | clip → fallback | concrete | False → False |
| TunnelToHell | south | marble → gypsum_board | clip → fallback | marble | True → False |
