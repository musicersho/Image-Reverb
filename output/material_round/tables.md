# T-33 材質輪基準率複測 — 程式產生表格

本檔全部數字由 `scripts/t33_material_round_tables.py` 產生，無一手打（地雷 #15）。

## 表 1　13 張照片 gate 基準率複測（三軸 confidence 對照裁決 T-28-A）

| 照片 | geometry | materials | overall | 與基準相符 | 陳設類別 | total_ratio | cap_applied | RT60 最小頻段跌破 0.1s？ |
|---|---|---|---|---|---|---|---|---|
| `bathroom_tiled` | medium | low | low | ✅ | （無） | 0.0% | 否 | 否 |
| `bedroom_ai_generated` | medium | low | low | ✅ | person 3.2%、bed 21.2%、curtain 9.0%、pillow 0.5% | 33.9% | 否 | 否 |
| `stairwell_tiled` | medium | low | low | ✅ | （無） | 0.0% | 否 | 否 |
| `arena_ntsu_linkou` | low | low | low | ✅ | person 9.4% | 9.4% | 否 | 否 |
| `car_interior_suv` | low | low | low | ✅ | seat 45.6% | 45.6% | 否 | 否 |
| `CathedralRoom` | medium | low | low | ✅ | （無） | 0.0% | 否 | 否 |
| `DivorceBeach` | low | medium | low | ✅ | （無） | 0.0% | 否 | 否 |
| `site_photo_department_store` | medium | low | low | ✅ | （無） | 0.0% | 否 | 否 |
| `site_photo_gym` | low | low | low | ✅ | （無） | 0.0% | 否 | 否 |
| `site_photo_restaurant` | low | low | low | ✅ | seat 20.2% | 20.2% | 否 | 否 |
| `RacquetballCourt4` | medium | low | low | ✅ | （無） | 0.0% | 否 | 否 |
| `SteinmanHall` | low | low | low | ✅ | seat 32.8%、curtain 6.1% | 38.8% | 否 | 否 |
| `TunnelToHell` | medium | low | low | ✅ | （無） | 0.0% | 否 | 否 |

## 表　達標率 — 自動幾何（8 場地）

| 場地 | run | 陳設 | 500Hz | 1kHz | 2kHz | 4kHz | 聯合帶 | 通過數 | 全達標 |
|---|---|---|---|---|---|---|---|---|---|
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | `CathedralRoom` | 預設（含陳設） | ❌ +263% | ❌ +354% | ❌ +224% | ❌ +166% | ❌ +186% | 0/5 | ❌ |
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | `CathedralRoom` | `--no-furnishings` | ❌ +263% | ❌ +354% | ❌ +224% | ❌ +166% | ❌ +186% | 0/5 | ❌ |
| Divorce Beach（戶外沙灘岩礁） | `DivorceBeach` | 預設（含陳設） | ❌ +751% | ❌ +959% | ❌ +701% | ❌ +252% | ❌ +676% | 0/5 | ❌ |
| Divorce Beach（戶外沙灘岩礁） | `DivorceBeach` | `--no-furnishings` | ❌ +751% | ❌ +959% | ❌ +701% | ❌ +252% | ❌ +676% | 0/5 | ❌ |
| Department Store（MIT，百貨賣場） | `site_photo_department_store` | 預設（含陳設） | ❌ +26% | ❌ -25% | ❌ -29% | ✅ -12% | ❌ +121% | 1/5 | ❌ |
| Department Store（MIT，百貨賣場） | `site_photo_department_store` | `--no-furnishings` | ❌ +26% | ❌ -25% | ❌ -29% | ✅ -12% | ❌ +121% | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `site_photo_gym` | 預設（含陳設） | 🟡 -43% | 🟡 -43% | 🟡 -44% | 🟡 -27% | ✅ -20% | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `site_photo_gym` | `--no-furnishings` | 🟡 -43% | 🟡 -43% | 🟡 -44% | 🟡 -27% | ✅ -20% | 1/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `site_photo_restaurant` | 預設（含陳設） | ❌ -31% | ❌ -28% | 🟡 -28% | 🟡 -32% | ❌ -41% | 0/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `site_photo_restaurant` | `--no-furnishings` | 🟡 +26% | 🟡 +23% | 🟡 +20% | ✅ +10% | ✅ -4% | 2/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `RacquetballCourt4` | 預設（含陳設） | ❌ -50% | ❌ -41% | ❌ -46% | ❌ -47% | ❌ -50% | 0/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `RacquetballCourt4` | `--no-furnishings` | ❌ -50% | ❌ -41% | ❌ -46% | ❌ -47% | ❌ -50% | 0/5 | ❌ |
| Steinman Hall（音樂廳） | `SteinmanHall` | 預設（含陳設） | ❌ -29% | ❌ -44% | ❌ -43% | ❌ -32% | ✅ -13% | 1/5 | ❌ |
| Steinman Hall（音樂廳） | `SteinmanHall` | `--no-furnishings` | ✅ +16% | ✅ +6% | ✅ -3% | ✅ +9% | ❌ +30% | 4/5 | ❌ |
| Tunnel to Hell（要塞地下混凝土隧道） | `TunnelToHell` | 預設（含陳設） | ❌ +54% | ❌ +144% | ❌ +95% | ❌ +100% | ✅ +0% | 1/5 | ❌ |
| Tunnel to Hell（要塞地下混凝土隧道） | `TunnelToHell` | `--no-furnishings` | ❌ +54% | ❌ +144% | ❌ +95% | ❌ +100% | ✅ +0% | 1/5 | ❌ |

**小計（自動幾何（8 場地），含兩組陳設設定合計）**：13/80（16%）；全達標 run 數 0/16
  - 預設（含陳設）：4/40（10%）；全達標 0/8
  - `--no-furnishings`：9/40（22%）；全達標 0/8

## 表　達標率 — 手動尺寸 F-09（5 場地）

| 場地 | run | 陳設 | 500Hz | 1kHz | 2kHz | 4kHz | 聯合帶 | 通過數 | 全達標 |
|---|---|---|---|---|---|---|---|---|---|
| Department Store（MIT，百貨賣場） | `t17_manual_department_store` | 預設（含陳設） | ❌ +56% | ❌ -29% | ❌ -36% | ✅ -18% | ❌ +162% | 1/5 | ❌ |
| Department Store（MIT，百貨賣場） | `t17_manual_department_store` | `--no-furnishings` | ❌ +56% | ❌ -29% | ❌ -36% | ✅ -18% | ❌ +162% | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `t17_manual_gym` | 預設（含陳設） | 🟡 -48% | 🟡 -39% | 🟡 -47% | 🟡 -32% | ✅ -17% | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `t17_manual_gym` | `--no-furnishings` | 🟡 -48% | 🟡 -39% | 🟡 -47% | 🟡 -32% | ✅ -17% | 1/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `t17_manual_restaurant` | 預設（含陳設） | 🟡 +43% | 🟡 +42% | 🟡 +44% | 🟡 +42% | ❌ +32% | 0/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `t17_manual_restaurant` | `--no-furnishings` | ❌ +113% | ❌ +118% | 🟡 +104% | ❌ +104% | ❌ +80% | 0/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `t17_manual_racquetball` | 預設（含陳設） | ❌ -60% | ❌ -52% | ❌ -56% | ❌ -55% | ❌ -61% | 0/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `t17_manual_racquetball` | `--no-furnishings` | ❌ -60% | ❌ -52% | ❌ -56% | ❌ -55% | ❌ -61% | 0/5 | ❌ |
| Steinman Hall（音樂廳） | `t17_manual_steinman` | 預設（含陳設） | ❌ -27% | ❌ -40% | ❌ -40% | ❌ -28% | ✅ -10% | 1/5 | ❌ |
| Steinman Hall（音樂廳） | `t17_manual_steinman` | `--no-furnishings` | ❌ +26% | ✅ +15% | ✅ +7% | ✅ +17% | ❌ +38% | 3/5 | ❌ |

**小計（手動尺寸 F-09（5 場地），含兩組陳設設定合計）**：8/50（16%）；全達標 run 數 0/10
  - 預設（含陳設）：3/25（12%）；全達標 0/5
  - `--no-furnishings`：5/25（20%）；全達標 0/5

## 表　臥室 vs 浴室 分離表（裁決 T-28-A 不可能性證明的區辨訊號）

| | 臥室 `bedroom_ai_generated` | 浴室 `bathroom_tiled` |
|---|---|---|
| geometry | medium | medium |
| materials | low | low |
| 陳設類別＋佔比 | person 3.2%、bed 21.2%、curtain 9.0%、pillow 0.5% | （無） |
| total_ratio | 33.9% | 0.0% |
| 佔 1kHz 總吸音比例 | 87.8% | 0.0% |
| rt60_bands_target_sabine（含陳設） | [0.6334, 0.6686, 0.5703, 0.4682, 0.4253, 0.408] | [1.0786, 2.5522, 3.5093, 3.0478, 2.0199, 1.4811] |
| rt60_bands_target_sabine（`--no-furnishings`） | [1.016, 2.5562, 3.8388, 3.5526, 2.285, 1.6554] | [1.0786, 2.5522, 3.5093, 3.0478, 2.0199, 1.4811] |
