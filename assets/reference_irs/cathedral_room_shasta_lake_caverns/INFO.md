# Cathedral Room, Shasta Lake Caverns

- **場地類型**：大型石灰岩天然洞窟（觀光洞穴內最大的廳室）
- **官方名稱**：`Cathedral Room Shasta Lake Caverns California`（EchoThief library 分類：`Underground/`）
- **地點**：Shasta Lake Caverns, California, USA
- **網站標註材質**：`Limestone, concrete.`（石灰岩、混凝土）

## 來源

- 場地頁：https://www.echothief.com/cathedral-room-shasta-lake-caverns/
- IR 原始網址：https://www.echothief.com/wp-content/uploads/2012/09/CathedralRoom.wav
- 照片原始網址：https://www.echothief.com/wp-content/uploads/2012/09/CathedralRoom.jpg
- 下載日期：2026-08-16

## IR 檔案

- 檔名：`CathedralRoom.wav`
- 取樣率：44100 Hz
- 長度：1.529 秒
- 聲道數：2（stereo）
- 位元深度：24-bit PCM（`file` 判定）
- RMS：0.048829　峰值：0.999000（非靜音，已做峰值正規化）

驗證指令與輸出：

```
$ python scripts/check_audio.py assets/reference_irs/cathedral_room_shasta_lake_caverns/CathedralRoom.wav
取樣率：44100 Hz
長度：1.529 秒
聲道數：2
RMS：0.048829
峰值：0.999000
```

## 照片

- 檔名：`CathedralRoom.jpg`
- 尺寸：960 x 480，JPEG
- **注意：這是 360° 環景（equirectangular panorama）**，不是一般透視照片。
  若要餵給單張影像的深度／空間估計模型，需先裁切成一般視角，或使用支援環景的模型。

## 授權

EchoThief 網站上**找不到任何明確的授權條款頁**（見本資料夾外的共同說明）。網站唯一的權利聲明是頁尾原文：

> EchoThief Impulse Response Library – copyright 2013-2026 Dr. Chris Warren cwarren@sdsu.edu

場地頁上提供免費下載，原文：

> Download this impulse response (right click and “save as”)

結論：作者明確開放免費下載使用，但**未授予再散布（redistribution）權利**。
本專案僅將檔案作為研究／驗證素材本機使用；若要公開發佈或隨產品散布，必須先寫信向
cwarren@sdsu.edu 取得書面同意。
