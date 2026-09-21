# T-70 公開小房間資料集調查表（步驟 1；2026-09-21；Sonnet）

> **範圍聲明**：本表只讀網頁、論文網頁版、資料集說明檔；**沒有下載任何資料集本體**（沒有 IR 音檔、沒有房間照片檔、沒有 zip／tgz）。
> 沒有計算、記錄或轉述任何殘響時間類數值（T-63 r1 程序 P-5）。查不到的欄位一律寫「查不到」，不猜。
> 本檔位於 `assets/reference_rooms_heldout/`——鐵則 18／18-a 自本檔存在起適用於此目錄；目前目錄內只有本檔（文件），沒有任何素材。

## 0. 調查過程的如實揭露（給 Opus 核對）

1. **讀過的來源**（全部只讀）：各資料集官方頁面（BUT Speech@FIT、RWTH IKS、OpenSLR、Stanford Digital Repository、Zenodo、GitHub）、論文網頁版（ar5iv）、BUT 說明檔 `read_me.txt`（14 KB 文字檔＝資料集說明檔，任務卡步驟 1 明列可讀）、BUT 官網頁面上 11 張縮圖（**網頁縮圖，不是資料集內的照片檔**；存在 scratchpad，未進 repo，用來目視判斷官網照片拍了哪類空間）。
2. **用 WebFetch 讀頁面時，每次的提問都明確要求略過殘響時間數值**；`read_me.txt` 另用程式先把含殘響時間關鍵字的行擋掉再顯示。
3. **一次不慎的曝光（已核對未記錄）**：ACE 論文 PDF（Eaton 2015，本機暫存）轉文字後，我用關鍵字過濾列印時，論文表 1 的幾列房間數字（欄位被 PDF 轉文字打散、看不出哪欄是什麼）出現在我的工作畫面。**沒有抄進任何檔案、沒有轉述**；為保守起見，ACE 各房間的尺寸我**不採用**這張表（見 §3 ACE），並在此註記。
4. **另有兩個 PDF 被工具暫存到本機、我沒有讀**：BUT 論文 PDF（工具解析失敗）、ACE 論文 PDF（就是上一點）；存放在 `~/.claude/projects/-Users-musicersho-Image-Reverb/<session>/tool-results/`，不在 repo 內。
5. 尺寸類數值凡出自「摘要模型轉述」的，已再用「要求逐字引用」的第二次提問複核（SoundCam）；BUT 的尺寸表出自官方頁面純文字與 `read_me.txt` 範例，兩者一致。

## 1. 摘要（一表看完）

| 資料集 | 房間數 | 授權 | 下載方式／大小 | 有官方尺寸的 ≤10 m 房間 | 官方房間照片 | 全向麥克風 IR | 本次結論 |
|---|---|---|---|---|---|---|---|
| **SoundCam**（Stanford／Adobe，NeurIPS 2023；Sonnet 補提名） | 3（聲學實驗室＝`Treated Room`、住家客廳、會議室） | MIT（Stanford PURL 頁面） | Stanford PURL `xq364hd5023`；大小查不到；有一個只含 Treated Room 的 Google Drive 小樣本 | 2（實驗室、會議室）；客廳無尺寸 | 論文有房間實拍圖（見 §4） | 10 支 Dayton Audio EMM6（型號有寫；「全向」一詞論文原句沒寫，見 §4 註） | **2 個房間五條件可由官方文件確認**（待 Opus 複核） |
| **BUT ReverbDB**（Brno 理工，官網頁列 9 房） | 9 | CC BY 4.0 | 官網單一 tgz `BUT_ReverbDB_rel_19_06_RIR-Only.tgz`，**9,308,593,693 位元組（約 9.3 GB；官網寫 8.7 GB，是 GiB 換算）**；HEAD 顯示支援 Range，但 tgz 為 gzip 串流，**沒辦法只取某幾個房間** | 4（L207、L212、R112、C236）；其餘 5 個 >10 m | 官方說明檔：每個房間目錄有 `*.jpg` 房間照片（用字為 usually）；官網頁另有 11 張**未標註**縮圖 | 論文寫全部為全向 | **4 個房間：尺寸／麥克風／授權已確認；照片要下載後才能確認** |
| **Aachen AIR v1.4** | 5（官網頁列會議室、講堂、樓梯間、走廊、Aula Carolina；論文另有錄音室、辦公室） | 官網：「壓縮檔內含 MIT 授權檔」；OpenSLR 頁：「下載內未載明」——**兩處不一致** | 官網 zip 175 MB | 網頁沒有尺寸（Aula Carolina 只寫地面積）；尺寸在論文表，未取得 | 官網頁有 5 房間照片（會議室、講堂、樓梯間、走廊、Aula） | **不符**：主體是假人頭雙耳（BRIR）；「無假人頭」子集的麥克風型式查不到 | **0 個**（尺寸查不到＋麥克風型式不符） |
| **ACE Challenge corpus** | 7（Imperial College 電機系） | CC BY-ND 4.0 | **需註冊／IEEE DataPort 訂閱才能下載**；官方註冊網址目前解析失敗（`acecorpus.ee.ic.ac.uk` 無此主機） | 房間尺寸在「註冊後才能取得的文件」；論文網頁版查不到乾淨的尺寸 | 查不到 | 有（單麥克風、DPA 4060 等）；型式細節查不到 | **0 個**（需註冊＝依卡片卡關規則停；我不能替使用者建立帳號） |
| **dEchorate** | **1 個實體房間**、11 種牆面吸音配置 | 資料 CC BY 4.0（Zenodo）；程式碼 MIT（GitHub） | Zenodo 單一檔 `dechorate.hdf5`，**83.9 GB，無法只下載部分**；另有 SOFA 版（大小查不到） | 1（約 6×6×2.4 m）；牆面材質隨配置改變 | 論文 Fig. 2 一張整體照（實驗室全景；不含各配置） | 30 支 AKG CK32（型號有寫；型式未查證） | **不建議**：見 §3 dEchorate |
| **OpenAIR**（York；Sonnet 補提名） | 查不到 | 頁面說「多數 CC」 | **兩個官方網址都顯示「帳號已停權」**，內容無法查證 | 查不到 | 查不到 | 查不到 | **0 個**（網站目前無法存取） |

## 2. 「五條件全符合的房間清單」（本卡步驟 1 的最終列表）

五條件＝T-63 r1 V2-2(a)：(i) 官方文件化尺寸最大維 ≤10 m；(ii) 非 `domain_out_non_room`；(iii) 官方附 ≥1 張可當 `--suggest` 輸入的該房間照片；(iv) 官方量測的全向麥克風 IR；(v) 授權允許本專案內部非商業使用。

### A. 官方文件已可確認、不必先下載（共 **2** 個，待 Opus 對原文複核）

| # | 資料集／房間 | (i) 尺寸（出處） | (ii) | (iii) 照片（出處） | (iv) | (v) |
|---|---|---|---|---|---|---|
| A1 | SoundCam／Treated Room（聲學實驗室） | 約 4.9×5.1 m、高 2.7 m（論文原句「The Treated Room is rectangular, approximately 4.9×5.1 meters and 2.7 meters in height.」） | 房間 ✔ | 論文 Fig. 4（空房實拍）、Fig. 5（掛布幔隔板配置實拍） | ✔（型號 Dayton Audio EMM6，10 支；**「全向」待 Opus 核**，見 §4 註） | ✔ MIT |
| A2 | SoundCam／Conference Room（會議室） | 約 6.7×3.3 m、高 2.7 m（論文原句「The Conference Room is rectangular, approximately 6.7×3.3 meters and 2.7 meters in height.」） | 房間 ✔ | 論文 Fig. 8（房間實拍） | ✔（同上） | ✔ MIT |

### B. 條件式符合：只差 (iii) 照片要下載後才能確認（共 **4** 個）

| # | 資料集／房間 | (i) 尺寸（官網頁表＋`read_me.txt`） | (ii) | (iii) | (iv) | (v) |
|---|---|---|---|---|---|---|
| B1 | BUT／L207（辦公室） | 4.6×6.9×3.1 m（說明檔範例：4.585×6.903×3.144） | ✔ | 說明檔宣稱每個房間目錄有 `*.jpg` 房間照片；**逐房間是否確實有、是否看得到牆／地板／天花板＝待下載確認** | ✔（論文：全向） | ✔ CC BY 4.0 |
| B2 | BUT／L212（辦公室） | 7.5×4.6×3.1 m | ✔ | 同 B1 | ✔ | ✔ |
| B3 | BUT／R112（旅館房間） | 4.4×2.8×2.6 m，**帶星號＝官方註明「非方塊形（例如 L 形）」**；`read_me` 說 L 形房間會拆成兩個方塊各記尺寸 | ✔ | 同 B1（官網頁縮圖中目視可見旅館臥室與浴室，**未經官方標註，不採信**） | ✔ | ✔ |
| B4 | BUT／C236（會議室） | 7.0×4.1×3.6 m | ✔ | 同 B1 | ✔ | ✔ |

### C. 不符合或無法確認（不入清單）

| 資料集／房間 | 不符條件 | 說明 |
|---|---|---|
| SoundCam／Living Room（客廳） | (i) | 論文原句：「The Living Room is in a real household with an open layout, i.e., the room does not have specific walls delineating it from parts of the rest of the house.」——無尺寸、且無獨立牆面。資料集附「textured 3D scans」，若能量出尺寸也是**我方量測**、不是「官方文件化」，故不算。 |
| BUT／Q301（辦公室，10.7×6.9×2.6 m） | (i) | 最大維 10.7 m >10 m |
| BUT／L227（樓梯間，6.2×2.6×14.2 m）、CR2（28.2×11.1×3.3 m）、E112（11.5×20.1×4.8 m，非方塊形）、D105（17.2×22.8×6.9 m，非方塊形） | (i)（L227、CR2、E112、D105 皆 >10 m）；L227 另有 (ii) 疑慮 | — |
| AIR 全部房間 | (i) 查不到；(iv) 不符 | 見 §3 AIR |
| ACE 全部房間 | 需註冊（卡關規則）；(iii) 查不到 | 見 §3 ACE |
| dEchorate | 見 §3 dEchorate | 一個房間、材質隨配置改變 |

### D. 結論數字

- **官方文件即可確認五條件全符合：2 個（SoundCam 實驗室、會議室）。**
- **加上 BUT 4 個「照片待確認」：最多 6 個。**
- 加上既有 `mit_gym`（U2）：**名單目前確定至少 3 個（`mit_gym`＋A1＋A2），最多 7 個。**
- 所以**不是「少於 2 個」**，「判準 2 一定樣本不足」的預告**暫不成立**；但很脆弱：只確認得了 SoundCam 的兩個時，名單剛好 3 個＝V2-2(f) 的下限，V2-2(e) 第二段（參考值可算性檢查）若再刷掉任何一個，就掉回「樣本不足」。

## 3. 逐資料集細節

### SoundCam（補提名 1）
- 出處：Wang, Clarke, Wang, Gao, Wu，NeurIPS 2023 Datasets & Benchmarks；arXiv 2311.03517；Stanford Digital Repository `https://purl.stanford.edu/xq364hd5023`（發表日 2023-08-22）；專案頁 `https://sites.google.com/view/soundcam`；程式碼 `https://github.com/maswang32/soundcam`。
- 授權：Stanford PURL 頁面「This work is licensed under an MIT License」。（GitHub README 與專案頁沒寫授權，以 PURL 為準。）
- 內容：3 個房間各約 1,000 組 10 聲道 RIR（有人在不同位置）＋空房間錄音；另有深度影像、關節位置、`3Dscans.tar.gz`（房間的貼圖 3D 掃描）。論文明說**不釋出人物 RGB 影像**（為保護受試者），只釋出深度圖與關節位置。
- 下載：`./download.sh` 或 PURL；大小**查不到**；另有 `TreatedRoomSmallSet`（Google Drive，只含 Treated Room 的小樣本）。
- 給名單的注意事項（交 Fable／Opus）：①**「有人在場」的 IR 與「空房」的 IR 混在同一資料集**，V2-2(d) 字面寫「全部官方全向 IR」——應限定空房；②Treated Room 有兩種配置（空房、掛布幔隔板），照片與 IR 的對應要在 T-70 步驟 3 註明；③論文中的房間實拍圖是論文插圖，**資料集本體內是否另附房間 RGB 照片＝查不到**（只確定有 3D 掃描）——卡片卡關規則允許「論文／官方網站的房間照片算官方」，故仍記為符合 (iii)，但**需要在 `rooms.json` 記出處為論文 Fig. 4／5／8**，且**從論文取圖＝下載論文插圖，屬步驟 3**。

### BUT ReverbDB
- 出處：`https://speech.fit.vut.cz/software/but-speech-fit-reverb-database`；引用：Szöke et al., IEEE JSTSP 2019（`https://ieeexplore.ieee.org/document/8717722`、arXiv 1811.06795）。
- 授權：CC BY 4.0（官網頁面）。`read_me.txt` 檔頭的 Apache 2.0 是套在說明檔／腳本上的版權聲明，不是資料授權。
- 下載：`http://merlin.fit.vutbr.cz/ReverbDB/BUT_ReverbDB_rel_19_06_RIR-Only.tgz`（9,308,593,693 位元組，HEAD 實測）；說明檔 `http://merlin.fit.vutbr.cz/ReverbDB/read_me.txt`。
- **檔案格式（說明檔明寫）：WAV、PCM 16-bit、單聲道、16 kHz**（每檔副檔名 `.vNN.wav`）。**本專案既有參考 IR 是 48 kHz 系統**；判準最高頻段 4 kHz 在 16 kHz 取樣下奈奎斯特 8 kHz 以內，理論上可用，但 `ir_metrics.py` 對 16 kHz 檔的行為未驗證——這是 V2-2(e) 第二段（可算性檢查）該回答的事，本卡不判。
- 每房間：31 支麥克風；說明檔範例顯示 `env_meta.txt`（官方房間資訊：尺寸、體積、類型、牆／地／天花板材質、家具佔比）與 `*.jpg`（房間照片）。**只有下載後才能逐房間確認 `*.jpg` 是否存在**。
- **參考 IR 挑選的注意事項**（交 Fable／Opus）：說明檔的麥克風欄位有 `SpeakerVisibility`＝`visible`／`non-visible`／`partly boxed`／`fully boxed`（麥克風放在抽屜、垃圾桶、架子裡）；論文也說有「hidden placements」。V2-2(d)「全部官方全向 IR」字面會把**藏在抽屜裡的麥克風**也算進參考值。
- 說明檔「已知瑕疵」：`Hotel_SkalskyDvur_ConferenceRoom2`（CR2，>10 m，不入名單）的量測位置不可信。
- 官網頁 11 張縮圖（**未標註**，我目視所見；不採信、僅供參考）：旅館房間浴室與臥床（img1、img3）、辦公室（img4、img9、img10）、大會議廳（img6）、階梯教室（img7、img8）、樓梯間（img11）、量測工具特寫（img2）、喇叭架設（img5）。

### Aachen AIR v1.4
- 出處：`https://www.iks.rwth-aachen.de/en/research/tools-downloads/databases/aachen-impulse-response-database/`；鏡像 `https://www.openslr.org/20/`；引用：Jeub, Schäfer, Vary，DSP 2009。
- 授權：IKS 官網說壓縮檔內含 MIT 授權檔；OpenSLR 頁寫「下載內未載明」——**不一致，需下載後看授權檔才能定**。
- 下載：`air_database_release_1_4.zip`，175 MB。
- 麥克風：**假人頭雙耳（BRIR）**為主；另有假人嘴到手機模型的雙聲道 IR；官網寫「錄音有無假人頭皆做過」，但「無假人頭」時的麥克風型式**查不到**。
- 官網頁有照片的房間：會議室、講堂、樓梯間、走廊、Aula Carolina；辦公室、錄音室頁面沒有照片。
- 尺寸：官網頁**沒有**（只寫 Aula Carolina 地面積 570 m²，遠超 10 m）；尺寸若有，只可能在論文（付費牆後）或壓縮檔內的說明檔；本次沒有取得論文（同類論文的房間表常與殘響時間同表，為守 P-5 我沒有去繞付費牆）。→ (i) 查不到、(iv) 不符 → **不入清單**。

### ACE Challenge corpus
- 出處：Imperial College；`https://www.imperial.ac.uk/a-z-research/speech-audio-processing/projects/ace-challenge/`；IEEE DataPort `https://ieee-dataport.org/documents/ace-challenge-2015`。
- 授權：CC BY-ND 4.0（禁止散布衍生作品；本專案內部分析用途大致可行，但需 Opus／使用者判讀）。
- 取得：需註冊（官方頁）／IEEE DataPort 訂閱；官方註冊網址目前解析失敗。**依卡片卡關規則「需註冊 → 停，問使用者」；建立帳號屬我不能做的事**，故不進一步。
- 內容：7 個房間（Office 1、Office 2、Meeting Room 1／2、Lecture Room 1／2、Building Lobby）；官方說明「房間尺寸與麥克風／聲源大略位置在語料文件中」——**文件在註冊牆之後**；照片**查不到**。
- → **不入清單**（可在使用者願意註冊並自行下載說明檔後重評，但 CC BY-ND、無照片，優先度低）。

### dEchorate
- 出處：Zenodo `10.5281/zenodo.4626590`（單檔 `dechorate.hdf5`，83.9 GB）、GitHub `Chutlhu/dEchorate`、Di Carlo et al.，EURASIP JASM 2021（arXiv 2104.13168）。
- 授權：Zenodo CC BY 4.0；GitHub 程式 MIT。
- 內容：**一個** 6×6×2.4 m 的長方體房間（Bar-Ilan 大學聲學實驗室），以可翻面牆板（一面反射、一面吸音）組成 11 種吸音配置；30 支 AKG CK32、多個聲源；論文 Fig. 2 有一張實驗室整體照。
- 不建議：①一個房間而非 11 個（各配置只是牆面材質不同）；②**「使用者只看照片確認材質」做不到**——照片只有一張整體照，看不出各配置每面牆是反射還是吸音；③83.9 GB 單檔無法只下載部分（占空間遠超需要）。若 Fable 要用，必須先裁定「選哪一種配置、材質怎麼定」。

### OpenAIR（補提名 2）
- `https://www.openair.hosted.york.ac.uk/` 與 `https://openairlib.net/` 兩個網址**都顯示「This Account has been suspended」**，無法查證任何內容。搜尋結果只說「多數內容為 Creative Commons，各項內容底下註明」。**不入清單**；網站恢復後可重評（單一地點頁面通常附照片與尺寸，但我無法在此確認）。

### 只在彙整清單看到、未進一步調查
SRIRACHA（單一盒形房間，約 265 萬個單聲道 RIR）、FLAIR、HOMULA-RIR、MP-RIR、MIRACLE 等都是「單一房間、以陣列量測」的資料集，清單沒有房間照片／尺寸的資訊；**未查證、不入表**。補提名額度用了 2 個（SoundCam、OpenAIR）。

## 4. 註記

- **SoundCam 的「全向」**：論文原句只寫「We place 10 Dayton Audio EMM6 microphones at different positions along the periphery.」；摘要模型轉述時加了「omnidirectional」，我用第二次逐字提問確認**原句沒有這個字**。EMM6 是量測用麥克風（Sonnet 的記憶為全向電容式，**未查證**）。Opus 驗證時請對廠商規格頁核實。
- **尺寸的精確度**：SoundCam 的兩個尺寸都是「approximately」；BUT 官網表為 1 位小數，`env_meta.txt` 有 3 位小數（只看得到 L207 的範例）。V2-2(a)(i) 只需要「最大維 ≤10 m」，都不受影響。
- **BUT 的 R112 為非方塊形**：SPEC 的房間模型是盒形，L 形房間套進去本身就是誤差來源；是否仍納入名單是 Fable 的裁決題，我不代為排除（V2-2(a) 五條件沒有「盒形」這一條，且卡片規定符合者全數入名單、不得挑選）。
- **T-63 卡 F-4 的風險預告狀態**：**未成立**（符合房間 ≥2），但見 §2-D 的脆弱性說明。

## 5. 下一步（步驟 2 停點）

使用者回覆「可以下載〈哪些〉」之前，**不得**下載任何東西（步驟 3 的前置另需 T-63 r1 經 Opus 審過）。可選的授權範圍見 TASKS.md T-70 卡交接筆記與本次的白話摘要。
