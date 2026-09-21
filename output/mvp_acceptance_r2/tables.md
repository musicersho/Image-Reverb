### 表 1　完整誤差表：8 場地 ×（6 頻段 ＋ 低頻聯合帶）

誤差 =（生成 IR 量測 T30 − 真實 IR 量測 T30）/ 真實。✅ = 誤差 ≤20%；❌ = 超差；🟡 = 對多檔中位數超差但落在該場地多條真實 IR 的區間內。

| 場地 | 路徑 | dims_source | group | forced | 125Hz | 250Hz | **500Hz** | **1kHz** | **2kHz** | **4kHz** | **聯合帶** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Cathedral Room, Shasta Lake Caverns（石灰岩洞窟）** | 真實 IR | — | — | — | 1.353 | 1.143 | 1.071 | 1.014 | 0.971 | 0.793 | 1.165 |
| | `CathedralRoom` | `equirect_multiview` | forced | 是 | ❌ +45% | ❌ +191% | ❌ +263% | ❌ +354% | ❌ +224% | ❌ +166% | ❌ +186% |
| **Divorce Beach（戶外沙灘岩礁）** | 真實 IR | — | — | — | 0.766 | 0.753 | 0.812 | 0.731 | 0.648 | 1.026 | 0.719 |
| | `DivorceBeach` | `equirect_multiview` | forced | 是 | ❌ +373% | ❌ +651% | ❌ +751% | ❌ +959% | ❌ +701% | ❌ +252% | ❌ +676% |
| **Department Store（MIT，百貨賣場）** | 真實 IR | — | — | — | 0.464 | 0.541 | 0.683 | 0.843 | 0.729 | 0.591 | 0.506 |
| | `site_photo_department_store` | `metric_depth` | forced | 是 | ❌ +77% | ❌ +113% | ❌ +26% | ❌ -25% | ❌ -29% | ✅ -12% | ❌ +121% |
| | `t17r2_manual_department_store` | `manual` | manual | 是 | ❌ +126% | ❌ +154% | ❌ +56% | ❌ -29% | ❌ -36% | ✅ -18% | ❌ +162% |
| **Gym（MIT，健身房／重訓室）** | 真實 IR（3 條中位數） | — | — | — | 0.842 | 1.158 | 1.239 | 0.903 | 0.770 | 0.587 | 1.163 |
| | `site_photo_gym` | `metric_depth` | forced | 是 | ✅ -18% | ✅ -17% | 🟡 -43% | 🟡 -43% | 🟡 -44% | 🟡 -27% | ✅ -20% |
| | `t17r2_manual_gym` | `manual` | manual | 是 | ✅ -14% | ✅ -13% | 🟡 -48% | 🟡 -39% | 🟡 -47% | 🟡 -32% | ✅ -17% |
| **Restaurant（MIT，餐廳用餐區）** | 真實 IR（4 條中位數） | — | — | — | 0.475 | 0.495 | 0.365 | 0.290 | 0.279 | 0.288 | 0.494 |
| | `site_photo_restaurant` | `metric_depth` | forced | 是 | ✅ -17% | ✅ -3% | 🟡 +26% | 🟡 +23% | 🟡 +20% | ✅ +10% | ✅ -4% |
| | `t17r2_manual_restaurant` | `manual` | manual | 是 | ❌ +54% | ❌ +98% | ❌ +113% | ❌ +118% | 🟡 +104% | ❌ +104% | ❌ +80% |
| **Racquetball Court 4（壁球場，必測反例）** | 真實 IR | — | — | — | 3.078 | 2.664 | 3.049 | 2.926 | 3.009 | 2.755 | 2.755 |
| | `RacquetballCourt4` | `equirect_multiview` | forced | 是 | ❌ -68% | ❌ -46% | ❌ -50% | ❌ -41% | ❌ -46% | ❌ -47% | ❌ -50% |
| | `t17r2_manual_racquetball` | `manual` | manual | 是 | ❌ -76% | ❌ -52% | ❌ -60% | ❌ -52% | ❌ -56% | ❌ -55% | ❌ -61% |
| **Steinman Hall（音樂廳）** | 真實 IR | — | — | — | 1.247 | 1.099 | 1.049 | 1.003 | 0.961 | 0.851 | 1.196 |
| | `SteinmanHall` | `equirect_multiview` | forced | 是 | ✅ +17% | ❌ +47% | ✅ +16% | ✅ +6% | ✅ -3% | ✅ +9% | ❌ +30% |
| | `t17r2_manual_steinman` | `manual` | manual | 是 | ❌ +24% | ❌ +55% | ❌ +26% | ✅ +15% | ✅ +7% | ✅ +17% | ❌ +38% |
| **Tunnel to Hell（要塞地下混凝土隧道）** | 真實 IR | — | — | — | 2.956 | 2.463 | 2.083 | 1.512 | 1.209 | 0.855 | 2.564 |
| | `TunnelToHell` | `metric_depth` | forced | 是 | ✅ +4% | ❌ +121% | ❌ +212% | ❌ +393% | ❌ +349% | ❌ +291% | ❌ +108% |

### 表 2　達標率 —— 三組分列（裁決 C：不得合併成單一數字）

**自動組**（`group=="auto"` 且 in-domain；F-01 產品主張本體）

| 場地 | run | 五項判準通過 | 全場地達標？ |
|---|---|---|---|
| **小計** | — | **0/0** | **0/0 場地全達標** |
**coverage** = 通過 gate 的 in-domain 場地數 / in-domain 場地數 = **0/1**

**forced 組**（被擋後 `--force-low-confidence` 產生，只記錄不計達標率）

| 場地 | run | in-domain | 500Hz | 1kHz | 2kHz | 4kHz | 聯合帶 |
|---|---|---|---|---|---|---|---|
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | `CathedralRoom` | 否 | ❌ +263% | ❌ +354% | ❌ +224% | ❌ +166% | ❌ +186% |
| Divorce Beach（戶外沙灘岩礁） | `DivorceBeach` | 否 | ❌ +751% | ❌ +959% | ❌ +701% | ❌ +252% | ❌ +676% |
| Department Store（MIT，百貨賣場） | `site_photo_department_store` | 否 | ❌ +26% | ❌ -25% | ❌ -29% | ✅ -12% | ❌ +121% |
| Gym（MIT，健身房／重訓室） | `site_photo_gym` | 是 | 🟡 -43% | 🟡 -43% | 🟡 -44% | 🟡 -27% | ✅ -20% |
| Restaurant（MIT，餐廳用餐區） | `site_photo_restaurant` | 否 | 🟡 +26% | 🟡 +23% | 🟡 +20% | ✅ +10% | ✅ -4% |
| Racquetball Court 4（壁球場，必測反例） | `RacquetballCourt4` | 否 | ❌ -50% | ❌ -41% | ❌ -46% | ❌ -47% | ❌ -50% |
| Steinman Hall（音樂廳） | `SteinmanHall` | 否 | ✅ +16% | ✅ +6% | ✅ -3% | ✅ +9% | ❌ +30% |
| Tunnel to Hell（要塞地下混凝土隧道） | `TunnelToHell` | 否 | ❌ +212% | ❌ +393% | ❌ +349% | ❌ +291% | ❌ +108% |

**手動組**（`--override-dims`，F-09 正式出口；照 T-17 另列成績，不混入自動組）

| 場地 | run | forced | 五項判準通過 | 全場地達標？ |
|---|---|---|---|---|
| Department Store（MIT，百貨賣場） | `t17r2_manual_department_store` | 是 | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `t17r2_manual_gym` | 是 | 1/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `t17r2_manual_restaurant` | 是 | 0/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `t17r2_manual_racquetball` | 是 | 0/5 | ❌ |
| Steinman Hall（音樂廳） | `t17r2_manual_steinman` | 是 | 3/5 | ❌ |
| **小計** | — | — | **5/25**（20%）| **0/5 場地全達標** |

### 表 3　500Hz vs 低頻聯合帶 階梯比

| 場地 | 真實 IR 階梯比 | 生成 IR 階梯比（各 run） | 觸發殘留風險？ |
|---|---|---|---|
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | 0.920 | `CathedralRoom` 1.166 | 否 |
| Divorce Beach（戶外沙灘岩礁） | 1.130 | `DivorceBeach` 1.239 | 否 |
| Department Store（MIT，百貨賣場） | 1.351 | `site_photo_department_store` 0.768<br>`t17r2_manual_department_store` 0.805 | 否 |
| Gym（MIT，健身房／重訓室） | 1.065 | `site_photo_gym` 0.753<br>`t17r2_manual_gym` 0.669 | 否 |
| Restaurant（MIT，餐廳用餐區） | 0.739 | `site_photo_restaurant` 0.965<br>`t17r2_manual_restaurant` 0.873 | 否 |
| Racquetball Court 4（壁球場，必測反例） | 1.106 | `RacquetballCourt4` 1.097<br>`t17r2_manual_racquetball` 1.144 | 否 |
| Steinman Hall（音樂廳） | 0.877 | `SteinmanHall` 0.784<br>`t17r2_manual_steinman` 0.803 | 否 |
| Tunnel to Hell（要塞地下混凝土隧道） | 0.812 | `TunnelToHell` 1.223 | 否 |

### 表 4　手動尺寸（F-09）的來源依據 —— 逐項標明，不得當成場地真值

| run | 採用尺寸 | 依據 |
|---|---|---|
| `t17r2_manual_department_store` | 35.00×25.00×3.20 m | Opus 由照片估：吊頂日光燈格柵推天花 ~3.2m，樓板取中型賣場 35×25 m |
| `t17r2_manual_gym` | 9.00×6.00×2.90 m | Opus 由照片估：門高 2.03m 為基準推天花 ~2.9m，小型健身工作室 9×6 m |
| `t17r2_manual_restaurant` | 14.00×9.00×3.20 m | Opus 由照片估：**照片只拍到卡座，室內尺寸不可見**，取一般用餐區 14×9×3.2 m |
| `t17r2_manual_racquetball` | 12.19×6.10×6.10 m | **公開標準**：國際壁球場規格 40×20×20 ft = 12.19×6.10×6.10 m（唯一有權威來源者） |
| `t17r2_manual_steinman` | 20.00×18.00×7.50 m | Opus 由環景數座位排數／排距推估（~300 席演講廳含舞台）：20×18×7.5 m |

### 表 5　報告項 5 —— 13 張（5 held-out ＋ 8 場地）逐張 gate／domain／六面材質對照

| 照片 | domain | gate | forced | override-dims 導引 | 域外誤放？ | 預設路徑 exit |
|---|---|---|---|---|---|---|
| held-out：浴室 | in | PASS | 否 | 無 | 否 | 0 |
| held-out：客廳／臥室（住宅尺度） | in | PASS | 否 | 無 | 否 | 0 |
| held-out：教堂／大空間 | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| held-out：走廊／樓梯間 | in | BLOCK→forced | 是 | 有 | 否 | 3 |
| held-out：車內 | non_room | BLOCK→forced | 是 | 有 | 否 | 3 |
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Divorce Beach（戶外沙灘岩礁） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Department Store（MIT，百貨賣場） | out | BLOCK→forced | 是 | 無 | 否 | 3 |
| Gym（MIT，健身房／重訓室） | in | BLOCK→forced | 是 | 有 | 否 | 3 |
| Restaurant（MIT，餐廳用餐區） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Racquetball Court 4（壁球場，必測反例） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Steinman Hall（音樂廳） | out | BLOCK→forced | 是 | 有 | 否 | 3 |
| Tunnel to Hell（要塞地下混凝土隧道） | out | BLOCK→forced | 是 | 有 | 否 | 3 |

#### 未 forced 通過的照片：六面材質對照 GT

**held-out：浴室**（`heldout_bathroom`）

| 面 | 材質 id | 來源 | GT | 正誤 |
|---|---|---|---|---|
| floor | carpet | clip | marble | ❌ |
| ceiling | generic_wall | clip | gypsum_board | ❌ |
| west | generic_wall | clip | marble | ❌ |
| east | generic_wall | clip | marble | ❌ |
| south | generic_wall | clip | unknown | 無法判 |
| north | generic_wall | clip | marble | ❌ |

❌ 5／可判 5／無法判 1（共 6）

**held-out：客廳／臥室（住宅尺度）**（`heldout_living`）

| 面 | 材質 id | 來源 | GT | 正誤 |
|---|---|---|---|---|
| floor | carpet | clip | wood_panel | ❌ |
| ceiling | generic_wall | clip | gypsum_board | ❌ |
| west | gypsum_board | clip | gypsum_board | ✅ |
| east | gypsum_board | clip | gypsum_board | ✅ |
| south | gypsum_board | clip | unknown | 無法判 |
| north | gypsum_board | clip | curtain_fabric | ❌ |

❌ 3／可判 5／無法判 1（共 6）

**錯誤放行率彙總**：被放行照片數 N＝2／總面數 6N＝12／可判面數 10／無法判面數 2／❌ 8；主率（❌÷可判面數）＝8/10（80%）；下界（❌÷6N，無法判全當對）＝8/12（67%）；上界（（❌＋無法判）÷6N，無法判全當錯）＝10/12（83%）

