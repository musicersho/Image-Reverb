# Department Store（MIT Reverb Survey）

- **場地類型**：百貨／服飾賣場（大面積低天花板室內空間，磨石／水泥地、大量布料衣物吸音、金屬層架、圓柱）
- **官方名稱**：資料集內標記為 `DepartmentStore`
- **地點**：美國麻州 Cambridge / Boston 一帶（MIT Reverb Survey 的測量範圍，未公布精確地址）
- **網站標註材質**：**無**。MIT 這份資料集只提供空間類型名稱，沒有材質標註。

## ⚠️ 照片與 IR 的對應關係（必讀）

**MIT 沒有公開「IR 檔案 ↔ 照片」的對應表。** 本資料夾的照片是 MIT 論文網站上
「量測器材架設在各survey地點」的示意照之一，圖說原文：

> The measurement apparatus in a range of survey locations (from left): Gym, supermarket, forest, restaurant, department store.

本資料夾是三個 MIT 資料夾中對應關係**最強**的一個：整份資料集裡
`DepartmentStore` 只有 `h160` 這**唯一一個** IR，照片又明確標為 department store，
因此兩者對應的可能性很高。**但 MIT 從未聲明這件事**，也不能排除照片拍的賣場
其 IR 根本沒被收進資料集、或被歸類成 `h132_ToyStore` / `h112_Bookstore` 等其他名稱。

→ 用途定位：可作「高度可能同場地」的參考素材，
**不可**在未加註記的情況下當成嚴格的 photo→IR ground-truth pair 來評分模型。

## 來源

- 資料集頁：https://mcdermottlab.mit.edu/Reverb/IR_Survey.html
- IR 原始網址：https://mcdermottlab.mit.edu/Reverb/IRMAudio/Audio.zip （整包 271 個 IR，11,660,005 bytes ≈ 11.1 MiB）
- 照片原始網址：https://mcdermottlab.mit.edu/Reverb/Figs/Summary/Survey/Store.png
- 照片出處頁：https://mcdermottlab.mit.edu/Reverb/ReverbSummary.html
- 下載日期：2026-08-16

## IR 檔案

- 檔名：`h160_DepartmentStore_1txts.wav`
- 取樣率：32000 Hz
- 長度：0.654 秒
- 聲道數：1（mono）
- 位元深度：24-bit PCM（`file` 判定）
- RMS：0.011449　峰值：0.999900（非靜音，已做峰值正規化）

檔名規則（官網原文）：

> All IRs are named with the following convention (Index)_(Descriptive name of space)_(No of texts received from participants in this space)

`1txts` = 只有 1 則簡訊回報在這個空間，與聲學特性無關。

驗證指令與輸出：

```
$ python scripts/check_audio.py assets/reference_irs/mit_department_store/h160_DepartmentStore_1txts.wav
取樣率：32000 Hz
長度：0.654 秒
聲道數：1
RMS：0.011449
峰值：0.999900
```

觀察：0.654 秒對這麼大的室內空間算短，符合「滿場衣物 + 低天花板 = 高吸音」的直覺，
是個對本專案很有價值的反例（大空間 ≠ 長殘響），可用來檢驗幾何導向的估計是否會高估 RT60。

## 照片

- 檔名：`site_photo_department_store.png`
- 尺寸：1920 x 1080，PNG 8-bit RGB（2,953,363 bytes）
- 一般透視照片（非環景），適合直接餵給深度／語意分割模型
- 畫面中央有量測器材（喇叭航空箱、背包、麥克風腳架），
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
