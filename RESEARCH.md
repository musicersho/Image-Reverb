# Research — 相關研究與開源專案調查

日期：2026-08-16。結論先講：**「照片 → IR」已有學術開源實作（Image2Reverb 等），
但沒有任何專案做到產品級（GUI、即時卷積、可調參數、材質視覺化）。**
我們的機會在於：用新一代視覺模型提升分析品質＋做成真正可用的工具。

## 1. 最直接相關：影像 → IR

| 專案 | 年份 | 方法 | 對我們的價值 |
|------|------|------|--------------|
| [Image2Reverb](https://github.com/mdkberry/image2reverb)（[論文](https://arxiv.org/abs/2103.14201)，ICCV 2021，MIT Media Lab） | 2021 | Conditional GAN，單張照片端到端生成 IR，附 `run_single_image.py` | **Phase 0 首要目標**：跑通它，聽它的輸出品質，作為 baseline |
| [AV-RIR](https://arxiv.org/pdf/2312.00834)（CVPR 2024） | 2024 | 影音多模態（畫面＋殘響語音）估計 IR | 對應我們的影片輸入構想；比 Image2Reverb 準 |
| Visual Acoustic Matching（CVPR 2022, Meta） | 2022 | 讓音訊「聽起來像在目標影像的空間」，不顯式輸出 IR | 端到端路線參考；但我們需要顯式 IR 才能做 plugin |
| [MMAudioReverbs](https://arxiv.org/pdf/2605.00431) | 2026 | 影片引導的去殘響與 IR 估計 | 最新工作，追蹤其結果與資料集 |

## 2. IR 生成（非影像條件）

| 專案 | 方法 | 對我們的價值 |
|------|------|--------------|
| [roomfuser](https://github.com/egrinstein/roomfuser) | Diffusion model 生成 RIR | 路線 C（神經生成）的技術參考 |
| [RIR Generation Conditioned on Acoustic Parameters](https://arxiv.org/html/2507.12136)（2025） | 以聲學參數為條件生成 IR | **與我們架構高度契合**：我們的視覺管線輸出參數 → 這類模型生成 IR，可取代 shaped-noise 合成 |
| [NeuralReverberator](https://github.com/csteinmetz1/NeuralReverberator) | Spectral autoencoder 合成 reverb | 早期神經合成參考 |
| [Speech2RIR](https://github.com/anton-jeran/Speech2RIR) | 從殘響語音反推 IR | 另一輸入模態；未來可與影像融合（同 AV-RIR 思路） |
| MESH2IR | 3D mesh → IR 神經生成 | 若走「深度→3D 重建」路線，這是幾何→IR 的橋 |

## 3. 幾何聲學模擬工具（路線 A 的積木）

| 工具 | 說明 |
|------|------|
| pyroomacoustics | Python，image-source + ray tracing，MVP 早期反射生成首選 |
| [rir-generator](https://github.com/audiolabs/rir-generator) | Python/C，經典 image method |
| [ImageMethodReverb.jl](https://github.com/nantonel/ImageMethodReverb.jl) | Julia，randomized image method |
| [Acoustic Volume Rendering](https://arxiv.org/pdf/2411.06307)、NeRAF (ICLR 2025) | 神經聲場（NeRF 式）；研究前沿，暫不採用 |
| [Differentiable Room Acoustic Rendering with Multi-View Vision Priors](https://arxiv.org/pdf/2504.21847)（2025） | 多視角影像先驗＋可微分聲學渲染，與我們「幾何＋材質→模擬」路線最接近，需細讀 |

## 4. 資料集（訓練與評測）

| 資料集 | 內容 | 用途 |
|--------|------|------|
| [Real Acoustic Fields (RAF)](https://github.com/facebookresearch/real-acoustic-fields)（Meta） | 多視角影像＋密集真實 IR＋6DoF pose | 訓練/評測影像→IR 的黃金配對資料 |
| [room-impulse-responses 清單](https://github.com/Graphi07/room-impulse-responses) | 公開 RIR 資料集總整理 | 找評測基準 |
| OpenAIR | 真實場地 IR＋場地照片 | **驗收標準用**：同場地「照片→生成 IR」vs 真實 IR 對比 |
| Image2Reverb 資料集 | 論文隨附的影像-IR 配對 | baseline 訓練資料 |

## 5. 視覺分析模型（我們管線的前端）

- 深度估計：Depth Anything V2 / Metric3D（需要**絕對尺度**深度，或用物件尺度校正）
- 分割：SAM 系列＋材質分類；或語意分割（ADE20K 類別含牆/地板/天花板/窗簾等）
- 材質辨識：材質分割研究（如 Materialistic、DMS dataset）→ 對應吸音係數表
- 空間類型分類：場景分類（Places365 類）作為聲學先驗（教堂 vs 臥室的 RT60 統計）

## 6. 定位分析：我們 vs 現有專案

現有專案的共同缺口（= 我們的差異化）：

1. **全是研究代碼**：無 GUI、無即時卷積、無使用者可調參數、環境安裝困難
2. **模型過時**：Image2Reverb 是 2021 GAN；2026 年的深度估計/分割/生成模型已大幅進步
3. **黑箱不可控**：端到端模型無法讓使用者修正「這面牆其實是玻璃」；
   我們的「顯式參數層」（幾何＋材質＋RT60 → IR）天生可解釋、可微調
4. **沒有產品整合**：沒人做成 plugin 或把 IR 匯出流程做好

## 7. 待研究問題（Open Questions）

- [ ] Image2Reverb 實際輸出品質如何？（跑通後盲聽評估）
- [ ] 單張照片的絕對尺度問題：用類別先驗＋已知物件校正能達到多少精度？
- [ ] 顯式參數路線（A+B）vs 端到端神經路線（C）的品質天花板比較
- [ ] Python 分析管線如何與 C++ plugin 整合？（ONNX/CoreML 內嵌 vs local service）
- [ ] Stereo IR 的合成策略：decorrelation 的最佳做法
