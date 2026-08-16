# Restaurant（MIT Reverb Survey）

- **場地類型**：餐廳用餐區（室內，白色磚牆、木桌、皮革卡座、木樑與硬質天花板）
- **官方名稱**：資料集內標記為 `Restaurant`
- **地點**：美國麻州 Cambridge / Boston 一帶。論文 Figure 1D 的圖說把同型照片描述為
  「one of the survey sites, a restaurant in Cambridge, Massachusetts」
- **網站標註材質**：**無**。MIT 這份資料集只提供空間類型名稱，沒有材質標註。

## ⚠️ 照片與 IR 的對應關係（必讀）

**MIT 沒有公開「IR 檔案 ↔ 照片」的對應表。** 本資料夾的照片是 MIT 論文網站上
「量測器材架設在各survey地點」的示意照之一，圖說原文：

> The measurement apparatus in a range of survey locations (from left): Gym, supermarket, forest, restaurant, department store.

照片確定是**這次 survey 的餐廳現場**（畫面右側是量測用喇叭航空箱，左側是麥克風），
但資料集內名為 `Restaurant` 的 IR 有 4 個（另有 2 個 `FastFoodRestaurant`），
**無法確認照片對應的是哪一個**。本資料夾把 4 個 `Restaurant` IR 全部放進來，
**不做任何猜測性的一對一配對**。

補充：論文 Figure 1 的 D 圖是餐廳照片、E 圖是「An IR measured in the room shown in (D)」，
所以 MIT 手上確實有成對資料，但**公開檔案裡沒有標出是哪一個 wav**。

→ 用途定位：可作「同類空間的照片 + 同類空間的真實 IR」參考素材，
**不可**當成嚴格的 photo→IR ground-truth pair 來評分模型。

## 來源

- 資料集頁：https://mcdermottlab.mit.edu/Reverb/IR_Survey.html
- IR 原始網址：https://mcdermottlab.mit.edu/Reverb/IRMAudio/Audio.zip （整包 271 個 IR，11,660,005 bytes ≈ 11.1 MiB）
- 照片原始網址：https://mcdermottlab.mit.edu/Reverb/Figs/Summary/Survey/Restaurant.png
- 照片出處頁：https://mcdermottlab.mit.edu/Reverb/ReverbSummary.html
- 下載日期：2026-08-16

## IR 檔案

四個檔案皆為 32000 Hz / mono / 24-bit PCM，已做峰值正規化（峰值 0.9999）。

| 檔名 | 長度 | RMS | 峰值 |
|------|------|-----|------|
| `h093_Restaurant_2txts.wav` | 0.527 秒 | 0.012265 | 0.999900 |
| `h114_Restaurant_txts.wav` | 0.306 秒 | 0.013528 | 0.999900 |
| `h130_Restaurant_1txs.wav` | 0.787 秒 | 0.012807 | 0.999900 |
| `h164_Restaurant_1txts.wav` | 0.290 秒 | 0.012308 | 0.999900 |

註：`h114_Restaurant_txts` 與 `h130_Restaurant_1txs` 的檔名是 MIT 原始拼字（漏數字／少一個 t），
**不要改檔名**，保持與上游一致才好追溯。

檔名規則（官網原文）：

> All IRs are named with the following convention (Index)_(Descriptive name of space)_(No of texts received from participants in this space)

驗證指令與輸出：

```
$ python scripts/check_audio.py assets/reference_irs/mit_restaurant/h093_Restaurant_2txts.wav
取樣率：32000 Hz
長度：0.527 秒
聲道數：1
RMS：0.012265
峰值：0.999900
```

## 照片

- 檔名：`site_photo_restaurant.png`
- 尺寸：1920 x 1080，PNG 8-bit RGB（2,727,133 bytes）
- 一般透視照片（非環景），適合直接餵給深度／語意分割模型
- **這張的取景較窄**（貼近卡座拍攝、右側被喇叭箱擋掉近半個畫面），
  對深度估計而言可用資訊比 gym / department store 那兩張少，做 T-05 時可預期表現較差

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
