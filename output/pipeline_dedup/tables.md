# T-41 基線變化表（程式產出，地雷 #15）

## 表 1：13 張三軸 confidence／gate／六面材質／dims_m／volume_m3 before/after

| 照片 | dims_source | geometry | materials | overall | dims_m/volume_m3 | surfaces/sources | 變動？ |
|---|---|---|---|---|---|---|---|
| bathroom_tiled | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| bedroom_ai_generated | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| stairwell_tiled | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| arena_ntsu_linkou | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| car_interior_suv | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| CathedralRoom | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| DivorceBeach | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| site_photo_department_store | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| site_photo_gym | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| site_photo_restaurant | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| RacquetballCourt4 | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| SteinmanHall | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |
| TunnelToHell | 同 | 同 | 同 | 同 | 同 / 同 | 同 / 同 | — |

## 表 2：scene_cues 四鍵新舊路 bit-identical（9 張透視照，陷阱 1 直證）

| 照片 | floor_pixel_ratio | person_pixel_ratio | out_of_domain | out_of_domain_label | 不同？ |
|---|---|---|---|---|---|
| bathroom_tiled | 同 | 同 | 同 | 同 | — |
| bedroom_ai_generated | 同 | 同 | 同 | 同 | — |
| stairwell_tiled | 同 | 同 | 同 | 同 | — |
| arena_ntsu_linkou | 同 | 同 | 同 | 同 | — |
| car_interior_suv | 同 | 同 | 同 | 同 | — |
| site_photo_department_store | 同 | 同 | 同 | 同 | — |
| site_photo_gym | 同 | 同 | 同 | 同 | — |
| site_photo_restaurant | 同 | 同 | 同 | 同 | — |
| TunnelToHell | 同 | 同 | 同 | 同 | — |

## 表 3：單張耗時對照（`analysis.json` 的 `elapsed_s`，地雷 #15：非手打）

重跑指令：`/Users/musicersho/Image Reverb/.venv/bin/python -m src.image_reverb /Users/musicersho/Image Reverb/assets/reference_irs/tunnel_to_hell/TunnelToHell.jpg --force-low-confidence --no-furnishings --no-viz`（對每張照片的 `<photo>` 部分替換）

| 照片 | 型態 | before elapsed_s | after elapsed_s | 差 |
|---|---|---|---|---|
| bathroom_tiled | 透視 | 17.27 | 13.46 | -3.81s |
| bedroom_ai_generated | 透視 | 22.54 | 21.95 | -0.59s |
| stairwell_tiled | 透視 | 17.21 | 13.32 | -3.89s |
| arena_ntsu_linkou | 透視 | 28.89 | 17.32 | -11.57s |
| car_interior_suv | 透視 | 19.2 | 12.9 | -6.30s |
| CathedralRoom | 環景 | 31.11 | 25.72 | -5.39s |
| DivorceBeach | 環景 | 26.01 | 26.51 | +0.50s |
| site_photo_department_store | 透視 | 17.17 | 13.03 | -4.14s |
| site_photo_gym | 透視 | 17.3 | 12.83 | -4.47s |
| site_photo_restaurant | 透視 | 17.59 | 13.05 | -4.54s |
| RacquetballCourt4 | 環景 | 26.37 | 27.49 | +1.12s |
| SteinmanHall | 環景 | 29.57 | 28.97 | -0.60s |
| TunnelToHell | 透視 | 21.25 | 14.99 | -6.26s |
