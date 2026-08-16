# Gym（MIT Reverb Survey）

- **場地類型**：健身房／重訓室（室內，橡膠地墊、石膏板牆、鏡面玻璃、少量吸音）
- **官方名稱**：資料集內標記為 `Gym` / `Gym_WeightRoom`
- **地點**：美國麻州 Cambridge / Boston 一帶（MIT Reverb Survey 的測量範圍，未公布精確地址）
- **網站標註材質**：**無**。MIT 這份資料集只提供空間類型名稱，沒有材質標註。

## ⚠️ 照片與 IR 的對應關係（必讀）

**MIT 沒有公開「IR 檔案 ↔ 照片」的對應表。** 本資料夾的照片是 MIT 論文網站上
「量測器材架設在各survey地點」的示意照之一，圖說原文：

> The measurement apparatus in a range of survey locations (from left): Gym, supermarket, forest, restaurant, department store.

照片確定是**這次 survey 的健身房現場**（可以看到量測用的喇叭航空箱與麥克風腳架），
但資料集內共有 3 個 Gym 類 IR，**無法確認照片對應的是哪一個**。
本資料夾把 3 個 Gym IR 全部放進來，**不做任何猜測性的一對一配對**。

→ 用途定位：可作「同類空間的照片 + 同類空間的真實 IR」參考素材，
**不可**當成嚴格的 photo→IR ground-truth pair 來評分模型。

## 來源

- 資料集頁：https://mcdermottlab.mit.edu/Reverb/IR_Survey.html
- IR 原始網址：https://mcdermottlab.mit.edu/Reverb/IRMAudio/Audio.zip （整包 271 個 IR，11,660,005 bytes ≈ 11.1 MiB）
- 照片原始網址：https://mcdermottlab.mit.edu/Reverb/Figs/Summary/Survey/Gym.png
- 照片出處頁：https://mcdermottlab.mit.edu/Reverb/ReverbSummary.html
- 下載日期：2026-08-16

## IR 檔案

三個檔案皆為 32000 Hz / mono / 24-bit PCM，已做峰值正規化（峰值 0.9999）。

| 檔名 | 長度 | RMS | 峰值 |
|------|------|-----|------|
| `h026_Gym_8txts.wav` | 1.776 秒 | 0.009412 | 0.999900 |
| `h052_Gym_WeightRoom_3txts.wav` | 1.368 秒 | 0.014111 | 0.999900 |
| `h120_Gym_WeightRoom_1txts.wav` | 0.433 秒 | 0.013637 | 0.999900 |

檔名規則（官網原文）：

> All IRs are named with the following convention (Index)_(Descriptive name of space)_(No of texts received from participants in this space)

即 `h026_Gym_8txts` = 第 26 號 IR、空間描述 Gym、有 8 則簡訊回報在這個空間。
`Nhits`/`Ntxts` 只代表受試者待在此類空間的頻率，**與聲學特性無關**。

驗證指令與輸出：

```
$ python scripts/check_audio.py assets/reference_irs/mit_gym/h026_Gym_8txts.wav
取樣率：32000 Hz
長度：1.776 秒
聲道數：1
RMS：0.009412
峰值：0.999900
```

## 照片

- 檔名：`site_photo_gym.png`
- 尺寸：1920 x 1080，PNG 8-bit RGB（2,930,284 bytes）
- 一般透視照片（非環景），適合直接餵給深度／語意分割模型
- 畫面中央有量測器材（喇叭航空箱、背包、麥克風腳架、假人頭），
  做 T-05/T-06 測試時要注意這些前景物件會被模型當成一般物體

## 授權

MIT McDermott Lab 的 Reverb Survey 頁面與 lab 的 Downloads 頁面
**都沒有任何授權條款、使用條件或引用要求的文字**（2026-08-16 逐字檢查過整頁 HTML）。
唯一的權利相關資訊是資料集所屬論文：

> Traer J, McDermott JH (2016). Statistics of natural reverberation enable perceptual
> separation of sound and space. *Proceedings of the National Academy of Sciences*,
> 113(48). DOI: 10.1073/pnas.1612524113

下載頁面原文只有一句：

> Download all 271 IRs (zip of audio files)

結論：**無明示授權 = 未授予再散布權利**。學術慣例是使用時引用上面那篇 PNAS 論文。
本專案僅將檔案作為研究／驗證素材本機使用；若要公開發佈或隨產品散布，
必須先寫信給 Josh McDermott（jhm@mit.edu）取得書面同意。
