# To-Do

> 執行用的任務卡在 [TASKS.md](TASKS.md)，協作規則在 [WORKFLOW.md](WORKFLOW.md)。
> 本檔案只放高層狀態總覽。

## 進行中

- [ ] **Phase 1：MVP（照片 → IR 匯出）** — T-10 順序缺陷已修（Sonnet，2026-08-18），
      🔵 待 Opus 重新驗證。通過後才能開 T-11／T-12

## ✅ T-08 決策結果（2026-08-16，Fable）

- [x] **深度路線**：改用 **metric depth 模型**（Depth-Anything-V2-Metric-Indoor）；
      參考物尺度降為校驗用；手動尺寸覆寫升 P0；T-11 內建評測關卡（不達標即停）
- [x] **材質路線**：**併用**——ADE20K 分割只管幾何角色，材質標籤交給 CLIP zero-shot
      二階分類器＋信心 gating；`floor`/`wall` 語意不再採信
- [x] **環景**：**做，最小範圍**——equirect→多視角透視投影進 T-10 前處理，
      驗收場地 4 個 → 8 個全可用，順便提前解掉「視野外」風險
- [x] 兩條硬約束已寫進任務卡：**逐表面材質 → T-12 步驟 2**、**逐頻段 RT60 → T-13 步驟 2**
- [x] IR 生成路線維持 A+B 混合（人耳已確認鏈路可用）；SPEC 升 v0.2、ROADMAP 同步更新

## 等使用者（AI 推不動）

- [ ] 📷 補上 `assets/photos/` 9 張照片的來源網址（T-04 自我檢查第 2 項，目前不符合）
- [ ] 📷 補一張**真實的教堂／空場硬質大空間**照片（目前所有大空間樣本都被人群主導，
      無法驗證長殘響情境）
- [ ] ❓ T-07 Image2Reverb baseline 要不要做？（限時 2h、2021 舊專案、失敗是可接受結果）

## 待處理

- [ ] **T-10 等 Opus 重新驗證順序缺陷修正**（已改 `preprocess_image()` 判環景/裁切順序，
      已加 `scripts/test_preprocess.py` 迴歸測試，見 TASKS.md 交接筆記）
- [ ] T-11 幾何估計模組 ｜ T-12 材質模組（T-10 驗證通過後可並行）
- [ ] T-13 → T-14 → T-15 → T-16 → T-17（依序）
- [ ] T-07（選做）Image2Reverb baseline
- [ ] 小修：錯誤處理一致性 — `check_audio.py` 無參數時應 `exit 2` 而非 0；
      `test_segmentation.py` 全部圖片失敗時應 exit 1 而非 0（`test_depth.py` 已正確）

## 已完成

- [x] **T-08 Phase 0 總結與路線決策（Fable）✅ 完成** — 三決策定案、SPEC v0.2、
      ROADMAP 更新、Phase 1 八張卡細化（含 A/B 兩條硬約束入卡）
- [x] T-06 語意分割測試（SegFormer ADE20K，9 張，42 類→材質對照表）✅ 驗證通過
- [x] T-05 深度估計測試（Depth Anything V2，9 張）✅ 驗證通過 — 產出關鍵負面結論
- [x] T-04 測試素材與對照 IR（9 張照片 + 8 組真實 IR）✅ 通過（照片來源連結待補）
- [x] T-03 材質吸音係數表（12 種材質 + `--material` 選項）✅ 驗證通過
- [x] T-02 離線卷積試聽工具（`convolve.py` + `wet_demo.wav`）✅ **完全通過**（使用者試聽確認殘響自然）
- [x] T-01 用手動參數生成第一個 IR（small / hall 兩組 preset）✅ 驗證通過
- [x] T-00 建立開發環境 ✅ 驗證通過
- [x] 建立專案基礎文件（README, ROADMAP, TODO, DEV_LOG, .gitignore）
- [x] 確立專案願景：照片/影片 → AI 空間與材質分析 → IR 生成 → Convolution Reverb
- [x] SPEC v0.1、RESEARCH 調查、ROADMAP Phase 0–3
- [x] 建立多視窗協作系統（CLAUDE.md / WORKFLOW.md / TASKS.md）
