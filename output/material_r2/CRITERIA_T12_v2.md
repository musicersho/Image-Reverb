# T-12 判準 v2（複製自 TASKS.md T-48 卡 §8，供追溯；內容不得與本卡不同）

criteria_version: v2（裁決 T-45-A 於 T-48 卡事前鎖定：v2-a 公式層 Sabine 125Hz＝0.348s ±20%；
v2-b IR 實測層改量 T-18 聯合帶 T30，判準見 T-48 卡）

B 部分——T-12 判準 v2 量測：
1. 用 `scripts/gen_ir_manual.py` 重生三條 IR：per-wall（4×3×2.5m，floor=carpet／其餘
   gypsum_board）、對照組六面 gypsum_board、對照組六面 carpet（與 T-12 交接筆記同設定）；
2. v2-a（公式層）：`compute_acoustics()`／Sabine 125Hz 對 per-wall 房間＝0.348s ±20%
   （重跑確認，預期達成）；
3. v2-b（IR 實測層，聯合帶）：用 T-18 `t30_low_combined()`（88.4–353.6Hz）量三條 IR。
   判準：per-wall IR 的聯合帶 T30 與六面 gypsum 對照組差異 ≤ ±20%，且六面 carpet 對照組
   的聯合帶 T30 ≥ per-wall 的 3 倍；
4. 原 v1 字面條件（125Hz 八度 T30 ≈0.35s ±20%）照量照列，預期仍未達（裁決 B 已證八度
   量測受鄰帶耦合污染），只記錄不當門檻；
5. `output/material_r2/REPORT.md`（程式產表）＋`CRITERIA_T12_v2.md`（本檔）。
