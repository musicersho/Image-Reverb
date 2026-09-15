# T-56 T-12 v2-b 量測方法 v3 — seed 鎖定＋10 次中位數

> 產生日期：2026-09-15T09:25:33.764021+00:00　git_head：`3b3a723d5621b23201965882b89fa8e868fe6d19`　git status --porcelain -- src data scripts：(空)

判準 v3（事前鎖定，見 `output/material_r3/CRITERIA_T12_v3.md`，commit `4a0b23e`，單一事實來源；使用者 2026-09-15 刪除草案內「方法有效性守門」條款，本報表不套用任何守門邏輯，10 次的 min／max／(max−min)/median 只記錄不改判定）：門檻數字與 v2 不變——|median(per-wall) − median(gypsum)| / median(gypsum) ≤ 20% 且 median(carpet) ≥ 3 × median(per-wall)。10 個 seed（1001–1010）事前鎖定，首跑即定案，禁止重跑（本檔為首跑結果）。

## 0. 結論

- **v2-b（判準 v3，唯一計入 verdict 的子判準）**：**FAIL**——median(per-wall)=0.9255s，median(六面 gypsum)=1.1824s，差異 -21.7%（≤±20%：FAIL）；median(六面 carpet)=3.9010s，倍數 4.22×（≥3×：PASS）
- **v2-a（公式層，同義反覆，裁決 T-48-F F4，不計入 verdict）**：PASS——Sabine 125Hz 0.3480s，目標 0.348s ±20%，誤差 +0.0%（非鑑別性，只記錄，不構成材質模組正確性證據）

- **v1 字面條件（只記錄不當門檻）**：未達——per-wall 125Hz 八度 T30（10 次中位數）0.7465s，字面目標 0.35s ±20%，誤差 +113.3%（裁決 B 已證八度量測受鄰帶耦合污染，此數字不當作判準，僅照量照列）


## 1. 逐條件統計（10 次 t30_low_combined()，中位數判定，無守門）

| 條件 | 指令 | 10 次值 (s) | median | min | max | (max−min)/median |
|---|---|---|---|---|---|---|
| per-wall：floor=carpet／其餘 gypsum_board（4×3×2.5m） | `python scripts/gen_ir_manual.py small --materials floor=carpet,walls=gypsum_board --seed <seed>` | 0.9822, 0.8448, 0.9306, 0.9199, 0.9203, 0.8858, 0.9718, 0.9466, 0.9394, 0.9190 | 0.9255 | 0.8448 | 0.9822 | 14.9% |
| 對照組：六面 gypsum_board（4×3×2.5m） | `python scripts/gen_ir_manual.py small --materials floor=gypsum_board --seed <seed>` | 1.1923, 1.1595, 1.2191, 1.1725, 1.2070, 1.1599, 1.1454, 1.2799, 1.1720, 1.2310 | 1.1824 | 1.1454 | 1.2799 | 11.4% |
| 對照組：六面 carpet（4×3×2.5m，舊六面同材質模式） | `python scripts/gen_ir_manual.py small --material carpet --seed <seed>` | 3.9725, 3.9082, 3.8943, 3.9031, 3.8727, 4.0998, 3.8586, 3.7551, 3.8989, 3.9602 | 3.9010 | 3.7551 | 4.0998 | 8.8% |

## 2. 30 條 IR 的 sha256（程式列出，供追溯；WAV 存於 `output/material_r3/runs/`，不進版控）

| 條件 | seed | sha256 |
|---|---|---|
| per_wall | 1001 | `886e5a75e4f6bd3ff421c1af02ff95829bab3b070431e12fffe0ee60a245f48c` |
| per_wall | 1002 | `43563e08a58c3616702df4df0775c7b2c8c260dc1e436aaa7ee30fedb38ef411` |
| per_wall | 1003 | `c3b8611ef60e03a8299782a318f5f5af7be37c0150aca00297ae07328292d0da` |
| per_wall | 1004 | `48fa370cdc18d479aa679f3cda56990a3dfe52bcfd24330e8566f9661019d701` |
| per_wall | 1005 | `bb6348ebbe672111172f1d60dc52261f25fff495f58bfc14db7fa855a5d38e3c` |
| per_wall | 1006 | `a4f71517cf282f588a5a0e9725700cde4403d8ae9d4811c620625ceda7fc8b9a` |
| per_wall | 1007 | `39767bf031819aacb42ec19a629be6cbbd6b125425ef858d4a350bc5533e1a6b` |
| per_wall | 1008 | `9cf66e3493e81ba8c733b08bdf47b8f8bfff7bc9dcdeee3dbd589631811b45ed` |
| per_wall | 1009 | `75c1123fee94c990d7ffb0b4d7622a87d5fd2b6908fae829be6392bb4a385f9d` |
| per_wall | 1010 | `cbdc332d53006d47729dc3145592030ccc395ed632dab6325cd743f5a5f53676` |
| control_gypsum | 1001 | `7111504cf39c00a22f7b191a16c315f193ceb0b22276a51b9fa566020bebd910` |
| control_gypsum | 1002 | `411ef4e48b1bf81eeb736630a1d54b13704903b41b0d94023f5e2bdfca447644` |
| control_gypsum | 1003 | `5fc4b44bda69d596d8dda861f8eae71bf782112c5901ff6640bcfb7ea82f876a` |
| control_gypsum | 1004 | `f4466804b27404916f75d0a4bdabeadc63813d679252004a12def71f33678413` |
| control_gypsum | 1005 | `0bb5de7716e475d17e6d3c4c4d705bb96f38a02687d9a69a6aaf7fc8643d19db` |
| control_gypsum | 1006 | `b5f9ebd32f7fbf64672b9147367a26b4774c13fe7c75b67eab597a296c859e7a` |
| control_gypsum | 1007 | `f70bed7c652892b7072252ab6042562210985eb5168371e857211af4aed339f1` |
| control_gypsum | 1008 | `1f9e7ef54c5abc5749452ce5dc95884e9d81f187255744fb7cc301d598dfd515` |
| control_gypsum | 1009 | `b6f53ce06132584fc6b9268f01c05ad13a2a087bb2dd31efe9112550ed74fa68` |
| control_gypsum | 1010 | `dd64d05a6b6a0ee3046b998baeafff3059dd14af678dbc44cb8d0fcadcf09f07` |
| control_carpet | 1001 | `5b06df6052ee2992690dacd0692f83ed4fbc7df7ea8e9805676fb478d415f98f` |
| control_carpet | 1002 | `e4fe4133b19c07fd177a17f67021d40ee91d07bf5f5b2ef789d6b4440022514f` |
| control_carpet | 1003 | `8622a0ede245089f79ff57228a994945793bf9ac8ac58899fa0554df6283bed9` |
| control_carpet | 1004 | `182267582935a36866f6ed2def31e2b88fdc04e5882c2d549fcc70f6d0e3e817` |
| control_carpet | 1005 | `8253ac23e6dc81138124a8eaa6a48fd752f8ba52815a40569857bf56d8b7b7c8` |
| control_carpet | 1006 | `d162bfc8093985f97af4cf5cd9d525372b5f446a7db6db10625e624ae112976e` |
| control_carpet | 1007 | `ce5beba3eb5909336319467cf52cb3f0fa66f26e7346d3d717285da17dafb7af` |
| control_carpet | 1008 | `74900dad5b078ebda89d184cc29db58e0aee509e05863dc34cbdb59d5792502e` |
| control_carpet | 1009 | `a9b9a267880517068e616ab6f8d6b23ccb618917ba89281bb6eb0d11c308eaef` |
| control_carpet | 1010 | `e22c46b236745eef66e3382fb82be19042cecf642727b990d2acf07789815868` |

## 3. 方法

1. `scripts/gen_ir_manual.py`（新增 `--seed N`，未給時逐位元不變，見腳本 docstring）依上表指令對三條件各跑 10 次（seed 分別為 1001–1010，事前鎖定），每次呼叫 `pra.random.seed(N)`＋`pra.libroom.set_rng_seed(N)`，輸出立即搬到 `output/material_r3/runs/<條件>_seed<seed>.wav`（紅線：不得重用 `output/` 舊 IR、不得重用 `output/material_r2/`）。
2. v2-b／v1：讀 `src/image_reverb/ir_metrics.py` 既有函式——`t30_low_combined()`（T-18，88.4–353.6Hz 聯合帶）與 `band_t30(ir, fs, [125])`（單一 125Hz 八度，v1 字面條件用）——對每條 IR 直接量測，10 次取中位數；不重新實作任何頻段濾波／Schroeder 積分邏輯。
3. v2-a：Sabine 125Hz 數字讀自其中一次 per-wall 執行的 stdout（公式值只取決於吸音係數，與 ray tracing 隨機種子無關，量一次即可）。
4. `ir_metrics.py`、`src/`、`data/`、`output/material_r2/` 全程零 diff／零改動。
5. **首跑即定案，禁止重跑**（CRITERIA_T12_v3.md `first_run_is_final: yes`）；本報表是本卡唯一一次 30 條 IR 生成的結果。

