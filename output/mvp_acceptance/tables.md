### 表 1　完整誤差表：8 場地 ×（6 頻段 ＋ 低頻聯合帶）

誤差 =（生成 IR 量測 T30 − 真實 IR 量測 T30）/ 真實。✅ = 誤差 ≤20%；❌ = 超差；🟡 = 對多檔中位數超差但落在該場地多條真實 IR 的區間內（MIT 三場地無公開 photo↔IR 配對，判準較弱，見 §限制）。

**判準（裁決 B）**：門檻只看 500Hz–4kHz ＋ 低頻聯合帶；125/250Hz 照列、超差照警示，但不當門檻。

| 場地 | 路徑 | dims_source | conf | 125Hz | 250Hz | **500Hz** | **1kHz** | **2kHz** | **4kHz** | **聯合帶** |
|---|---|---|---|---|---|---|---|---|---|---|
| **Cathedral Room, Shasta Lake Caverns（石灰岩洞窟）** | 真實 IR | — | — | 1.353 | 1.143 | 1.071 | 1.014 | 0.971 | 0.793 | 1.165 |
| | 生成`CathedralRoom` | `equirect_multiview` | medium | ❌ +45% | ❌ +191% | ❌ +263% | ❌ +354% | ❌ +224% | ❌ +166% | ❌ +186% |
| **Divorce Beach（戶外沙灘岩礁）** | 真實 IR | — | — | 0.766 | 0.753 | 0.812 | 0.731 | 0.648 | 1.026 | 0.719 |
| | 生成`DivorceBeach` | `equirect_multiview` | low | ❌ +373% | ❌ +651% | ❌ +751% | ❌ +959% | ❌ +701% | ❌ +252% | ❌ +676% |
| **Department Store（MIT，百貨賣場）** | 真實 IR | — | — | 0.464 | 0.541 | 0.683 | 0.843 | 0.729 | 0.591 | 0.506 |
| | 生成`site_photo_department_store` | `metric_depth` | medium | ❌ +77% | ❌ +113% | ❌ +26% | ❌ -25% | ❌ -29% | ✅ -12% | ❌ +121% |
| | 生成`t17_manual_department_store` | `manual` | high | ❌ +126% | ❌ +154% | ❌ +56% | ❌ -29% | ❌ -36% | ✅ -18% | ❌ +162% |
| **Gym（MIT，健身房／重訓室）** | 真實 IR（3 條中位數） | — | — | 0.842 | 1.158 | 1.239 | 0.903 | 0.770 | 0.587 | 1.163 |
| | 生成`site_photo_gym` | `metric_depth` | low | ✅ -18% | ✅ -17% | 🟡 -43% | 🟡 -43% | 🟡 -44% | 🟡 -27% | ✅ -20% |
| | 生成`t17_manual_gym` | `manual` | high | ✅ -14% | ✅ -13% | 🟡 -48% | 🟡 -39% | 🟡 -47% | 🟡 -32% | ✅ -17% |
| **Restaurant（MIT，餐廳用餐區）** | 真實 IR（4 條中位數） | — | — | 0.475 | 0.495 | 0.365 | 0.290 | 0.279 | 0.288 | 0.494 |
| | 生成`site_photo_restaurant` | `metric_depth` | low | ✅ -17% | ✅ -3% | 🟡 +26% | 🟡 +23% | 🟡 +20% | ✅ +10% | ✅ -4% |
| | 生成`t17_manual_restaurant` | `manual` | high | ❌ +54% | ❌ +98% | ❌ +113% | ❌ +118% | 🟡 +104% | ❌ +104% | ❌ +80% |
| **Racquetball Court 4（壁球場，必測反例）** | 真實 IR | — | — | 3.078 | 2.664 | 3.049 | 2.926 | 3.009 | 2.755 | 2.755 |
| | 生成`RacquetballCourt4` | `equirect_multiview` | medium | ❌ -68% | ❌ -46% | ❌ -50% | ❌ -41% | ❌ -46% | ❌ -47% | ❌ -50% |
| | 生成`t17_manual_racquetball` | `manual` | high | ❌ -76% | ❌ -52% | ❌ -60% | ❌ -52% | ❌ -56% | ❌ -55% | ❌ -61% |
| | 🔬診斷`t17_diag_racquetball_hard` | `manual` | high | ✅ -3% | ❌ +26% | ❌ +28% | ❌ +74% | ❌ +47% | ❌ +26% | ✅ +13% |
| **Steinman Hall（音樂廳）** | 真實 IR | — | — | 1.247 | 1.099 | 1.049 | 1.003 | 0.961 | 0.851 | 1.196 |
| | 生成`SteinmanHall` | `equirect_multiview` | low | ✅ +17% | ❌ +47% | ✅ +16% | ✅ +6% | ✅ -3% | ✅ +9% | ❌ +30% |
| | 生成`t17_manual_steinman` | `manual` | high | ❌ +24% | ❌ +55% | ❌ +26% | ✅ +15% | ✅ +7% | ✅ +17% | ❌ +38% |
| **Tunnel to Hell（要塞地下混凝土隧道）** | 真實 IR | — | — | 2.956 | 2.463 | 2.083 | 1.512 | 1.209 | 0.855 | 2.564 |
| | 生成`TunnelToHell` | `equirect_multiview` | medium | ❌ -40% | ✅ +2% | ❌ +54% | ❌ +144% | ❌ +95% | ❌ +100% | ✅ +0% |
| | 🔬診斷`t17_diag_tunnel_perspective` | `metric_depth` | low | ✅ +7% | ❌ +124% | ❌ +215% | ❌ +396% | ❌ +342% | ❌ +293% | ❌ +114% |

### 表 2　達標率 —— 依 `dims_source` 分組（裁決 C：不得合併成單一數字）

**自動幾何 `metric_depth` / `equirect_multiview`（F-01 產品主張本體）**

| 場地 | run | 五項判準通過 | 全場地達標？ |
|---|---|---|---|
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | `CathedralRoom` | 0/5 | ❌ |
| Divorce Beach（戶外沙灘岩礁） | `DivorceBeach` | 0/5 | ❌ |
| Department Store（MIT，百貨賣場） | `site_photo_department_store` | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `site_photo_gym` | 1/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `site_photo_restaurant` | 2/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `RacquetballCourt4` | 0/5 | ❌ |
| Steinman Hall（音樂廳） | `SteinmanHall` | 4/5 | ❌ |
| Tunnel to Hell（要塞地下混凝土隧道） | `TunnelToHell` | 1/5 | ❌ |
| **小計** | — | **9/40**（22%）| **0/8 場地全達標** |

**手動尺寸 `manual`（F-09 正式出口）**

| 場地 | run | 五項判準通過 | 全場地達標？ |
|---|---|---|---|
| Department Store（MIT，百貨賣場） | `t17_manual_department_store` | 1/5 | ❌ |
| Gym（MIT，健身房／重訓室） | `t17_manual_gym` | 1/5 | ❌ |
| Restaurant（MIT，餐廳用餐區） | `t17_manual_restaurant` | 0/5 | ❌ |
| Racquetball Court 4（壁球場，必測反例） | `t17_manual_racquetball` | 0/5 | ❌ |
| Steinman Hall（音樂廳） | `t17_manual_steinman` | 3/5 | ❌ |
| **小計** | — | **5/25**（20%）| **0/5 場地全達標** |

### 表 3　500Hz vs 低頻聯合帶 階梯比（裁決 B 要求的殘留風險檢查）

裁決 B 自陳：聯合帶上緣 354Hz 與 500Hz 帶仍共享邊緣，**若某場地 500Hz T30 比聯合帶慢 2 倍以上，聯合帶量測仍可能被拉長**。比值 = T30(500Hz) / T30(聯合帶)；|比值| ≥ 2 或 ≤ 0.5 時該場地的聯合帶數字需打折看待。

| 場地 | 真實 IR 階梯比 | 生成 IR 階梯比（各 run） | 觸發殘留風險？ |
|---|---|---|---|
| Cathedral Room, Shasta Lake Caverns（石灰岩洞窟） | 0.920 | `CathedralRoom` 1.166 | 否 |
| Divorce Beach（戶外沙灘岩礁） | 1.130 | `DivorceBeach` 1.239 | 否 |
| Department Store（MIT，百貨賣場） | 1.351 | `site_photo_department_store` 0.768<br>`t17_manual_department_store` 0.805 | 否 |
| Gym（MIT，健身房／重訓室） | 1.065 | `site_photo_gym` 0.753<br>`t17_manual_gym` 0.669 | 否 |
| Restaurant（MIT，餐廳用餐區） | 0.739 | `site_photo_restaurant` 0.965<br>`t17_manual_restaurant` 0.873 | 否 |
| Racquetball Court 4（壁球場，必測反例） | 1.106 | `RacquetballCourt4` 1.097<br>`t17_manual_racquetball` 1.144<br>`t17_diag_racquetball_hard` 1.259 | 否 |
| Steinman Hall（音樂廳） | 0.877 | `SteinmanHall` 0.784<br>`t17_manual_steinman` 0.803 | 否 |
| Tunnel to Hell（要塞地下混凝土隧道） | 0.812 | `TunnelToHell` 1.251<br>`t17_diag_tunnel_perspective` 1.196 | 否 |

### 表 4　手動尺寸（F-09）的來源依據 —— 逐項標明，不得當成場地真值

| run | 採用尺寸 | 依據 |
|---|---|---|
| `t17_manual_department_store` | 35.00×25.00×3.20 m | Opus 由照片估：吊頂日光燈格柵推天花 ~3.2m，樓板取中型賣場 35×25 m |
| `t17_manual_gym` | 9.00×6.00×2.90 m | Opus 由照片估：門高 2.03m 為基準推天花 ~2.9m，小型健身工作室 9×6 m |
| `t17_manual_restaurant` | 14.00×9.00×3.20 m | Opus 由照片估：**照片只拍到卡座，室內尺寸不可見**，取一般用餐區 14×9×3.2 m |
| `t17_manual_racquetball` | 12.19×6.10×6.10 m | **公開標準**：國際壁球場規格 40×20×20 ft = 12.19×6.10×6.10 m（唯一有權威來源者） |
| `t17_diag_racquetball_hard` | 12.19×6.10×6.10 m | 同上公開標準尺寸，**額外用 `--override-material` 把六面改成正確硬質**（floor=wood_panel、其餘 concrete）——病因隔離用的診斷 run，不計入達標率 |
| `t17_manual_steinman` | 20.00×18.00×7.50 m | Opus 由環景數座位排數／排距推估（~300 席演講廳含舞台）：20×18×7.5 m |

