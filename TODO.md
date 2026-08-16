# To-Do

> 執行用的任務卡在 [TASKS.md](TASKS.md)，協作規則在 [WORKFLOW.md](WORKFLOW.md)。
> 本檔案只放高層狀態總覽。

## 進行中

- [ ] Phase 0：可行性驗證 — T-00~T-03 全部驗證通過，**卡在 T-04 等使用者決定**

## 等使用者（AI 推不動）

- [ ] 🎧 試聽 `afplay output/wet_demo.wav`，確認聽得出大廳殘響（T-02 最後一項自我檢查）
- [ ] 📷 T-04 照片：5 類空間自己拍，還是授權從免授權圖庫下載？
- [ ] ⬇️ T-04 授權從 OpenAIR 下載 ≥ 3 組「IR + 場地照片」
- [ ] ⬇️ T-05/T-06 授權下載 AI 模型（Depth Anything V2、SegFormer，各數百 MB）

## 待處理

- [ ] T-04 ~ T-07（見 TASKS.md，全部前置於 T-04）
- [ ] T-08 Phase 0 總結與路線決策（Fable）
- [ ] 小修：`check_audio.py` 不帶參數時應 `sys.exit(2)` 而非 0（見 T-00 卡驗證附註）

## 已完成

- [x] T-03 材質吸音係數表（12 種材質 + `--material` 選項）✅ 驗證通過
- [x] T-02 離線卷積試聽工具（`convolve.py` + `wet_demo.wav`）✅ 驗證通過（待人耳確認）
- [x] T-01 用手動參數生成第一個 IR（small / hall 兩組 preset）✅ 驗證通過
- [x] T-00 建立開發環境 ✅ 驗證通過
- [x] 建立專案基礎文件（README, ROADMAP, TODO, DEV_LOG, .gitignore）
- [x] 確立專案願景：照片/影片 → AI 空間與材質分析 → IR 生成 → Convolution Reverb
- [x] SPEC v0.1、RESEARCH 調查、ROADMAP Phase 0–3
- [x] 建立多視窗協作系統（CLAUDE.md / WORKFLOW.md / TASKS.md）
