## 表 1：13 張照片基準率變化（預設 vs --role-aware）

| 照片 | geometry（預設） | geometry（--role-aware） | materials（預設） | overall（預設） | gate（預設） | materials（--role-aware） | overall（--role-aware） | gate（--role-aware） | 與 round11 相符 | 與 round17 相符 |
|---|---|---|---|---|---|---|---|---|---|---|
| bathroom_tiled | medium | medium | low | low | BLOCK | medium | medium | pass | ✅ | ✅ |
| bedroom_ai_generated | medium | medium | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| stairwell_tiled | medium | medium | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| arena_ntsu_linkou | low | low | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| car_interior_suv | low | low | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| CathedralRoom | medium | medium | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| DivorceBeach | low | low | medium | low | BLOCK | medium | low | BLOCK | ✅ | ✅ |
| site_photo_department_store | medium | low | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| site_photo_gym | low | low | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| site_photo_restaurant | low | low | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| RacquetballCourt4 | medium | medium | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| SteinmanHall | low | low | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |
| TunnelToHell | low | low | low | low | BLOCK | low | low | BLOCK | ✅ | ✅ |

## 表 2：已知錯誤案例清單（鐵則 12）在兩模式的 gate 結果

| 照片 | gate（預設） | gate（--role-aware） |
|---|---|---|
| bathroom_tiled | BLOCK | pass |
| bedroom_ai_generated | BLOCK | BLOCK |
| site_photo_gym | BLOCK | BLOCK |
| site_photo_restaurant | BLOCK | BLOCK |
| RacquetballCourt4 | BLOCK | BLOCK |

## 表 3：geometry_confidence 觀察到的落差（不影響本卡結論，供 T-47 參考）

- site_photo_department_store：geometry_confidence 在兩模式間不同（default=medium, role_aware=low）
- TunnelToHell：預設模式 geometry_confidence=low 與 EXPECTED_GATE（T-28-A／T-36 凍結表）medium 不同
