# Racquetball Court #4

- **場地類型**：室內壁球／回力球場，小型硬牆房間（木地板 + 白牆 + 玻璃背牆，幾乎無吸音）
- **官方名稱**：`Racquetball Court UC San Diego California`（EchoThief library 分類：`Recreation/`）
- **地點**：University of California, San Diego, California, USA
- **網站標註材質**：`Wood, glass.`（木材、玻璃）

## 來源

- 場地頁：https://www.echothief.com/racquetball-court-4/
- IR 原始網址：https://www.echothief.com/wp-content/uploads/2012/09/RacquetballCourt4.wav
- 照片原始網址：https://www.echothief.com/wp-content/uploads/2012/09/RacquetballCourt4.jpg
- 下載日期：2026-08-16

## IR 檔案

- 檔名：`RacquetballCourt4.wav`
- 取樣率：44100 Hz
- 長度：3.538 秒（本批 5 個場地中最長，小房間但幾乎全反射面）
- 聲道數：2（stereo）
- 位元深度：16-bit PCM
- RMS：0.028243　峰值：0.980774（非靜音）

驗證指令與輸出：

```
$ python scripts/check_audio.py assets/reference_irs/racquetball_court_4/RacquetballCourt4.wav
取樣率：44100 Hz
長度：3.538 秒
聲道數：2
RMS：0.028243
峰值：0.980774
```

## 照片

- 檔名：`RacquetballCourt4.jpg`
- 尺寸：960 x 480，JPEG
- **注意：這是 360° 環景（equirectangular panorama）**，不是一般透視照片。

這個場地對本專案特別有價值：**小空間但殘響很長**，可以用來檢驗「照片看起來小 → 就給短殘響」
這種天真規則會失敗（材質吸音係數才是關鍵）。

## 授權

EchoThief 網站上**找不到任何明確的授權條款頁**。網站唯一的權利聲明是頁尾原文：

> EchoThief Impulse Response Library – copyright 2013-2026 Dr. Chris Warren cwarren@sdsu.edu

此場地頁的下載連結原文（用的是方括號版本）：

> Download this impulse response [right click and “save as”]

結論：免費下載可用，但**未授予再散布權利**。公開發佈或隨產品散布前需寫信向 cwarren@sdsu.edu 取得同意。
