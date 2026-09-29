# assets/reference_rooms_heldout/ — T-70 公開小房間 IR 資料集

本目錄封存 T-63 MVP 判準 v2（輔助路徑）V2-2(a) 的公開資料集房間候選（SoundCam、BUT ReverbDB）。
資料集本體（IR、照片、官方說明檔）依 `.gitignore` 不進 git；只有本檔、`SURVEY.md`、`rooms.json`、
`ASSET_MANIFEST.json` 與各房間的 `materials_official.txt`（白名單抽取結果，見下）進版控。

## 鐵則 18／18-a（自 TASKS.md Phase 1.10 逐字複製；核准版＝r5，`criteria: T-63 v2` 寫入 2026-09-23）

> ⚠️ 以下條文引用 TASKS.md 的鐵則 18／18-a。鐵則 18-a 現行有效版本＝**r5**（`criteria: T-63 v2` 已寫入、
> 已生效；後續 v2.1／v2.2 只修改 (1) 的一個子字串與另一行，範圍不變，皆已生效）。**唯一授權＝T-17-R3 受驗
> run，尚未開卡**；本卡（T-70）3a／3b 全程只用鐵則 18 原文「只准」的操作，不需要、也不構成 18-a 的授權。

### 鐵則 18（原文）

> 18. **held-out 從出生就實體隔離**（R2「一批兩用」的教訓）：`assets/photos_real_heldout/` 內的檔，自 T-64
> 就位起到 T-17-R3 收工＋複驗、Fable 寫解除紀錄為止，任何視窗不得以任何模型或分析／評測腳本處理，**沒有
> 例外三項**——全套 `scripts/test_*.py` 不得掃到該目錄（T-64 自我檢查要證明）；
> 只准算 sha256、讀尺寸／EXIF、人眼看圖。不得複製到其他目錄、不得一批兩用。

### 鐵則 18-a（r5；`criteria: T-63 v2` 寫入，2026-09-23；條文＝T-63 卡 R5-2c 逐字，只刪修訂標籤與共同行首縮排）

> 18-a（r5）. **鐵則 18 的適用範圍與 R3 授權條款**：
>
> (1) **範圍**：鐵則 18 同樣適用 `assets/photos_synth_heldout/`（T-64 路徑 S）與
> `assets/reference_rooms_heldout/`（T-70）——自各卡就位起生效。後者「只准」的清單另含：`soundfile.info`
> 讀音檔格式；`.npy` 依 V2-2(d)④ 只讀 `.shape`／`.dtype`；T-70 r2-3b 的欄位白名單抽取（只顯示白名單欄
> 位，用於尺寸、材質文字、`SpeakerVisibility`）。三者都不讀樣本、不算任何聲學量。 另含：對官方說明檔與
> 四個授權房間目錄內全部 `*.txt` 的關鍵字**計數**（`grep -ci`，只輸出數字、不輸出任何行；限
> V2-2(d)②(甲)(B) 列出的七個關鍵字）；白名單抽取依 T-70 r2-3b(1) 含 r3-1 的黑名單補充（吸音係數類欄位永
> 不顯示）與 r4-1 的略過行規則。兩者同樣不讀樣本、不算任何聲學量、不顯示任何殘響類文字。 另含：PIL
> `Image.open` 只讀 `.mode`／`.size`（不呼叫 `load()`、不解碼像素、不 `save`、不 `show`、不轉存任何格
> 式），用於 V2-2(a)(iii)①(A)(二) 與 ②；開啟失敗即記入 `images_excluded`，不得為此安裝或註冊額外解碼
> 器。此項同樣不讀樣本、不算任何聲學量。（v2.1 生效後字樣＝「用於 V2-2(a)(iii)①(A)(二) 與 ②」——本行已
> 對齊，見 TASKS.md「18-a（v2.1 生效）」）
>
> (2) **唯一授權＝T-17-R3 受驗 run**，且須在 T-63 `criteria:` commit 之後、由 T-17-R3 卡的步驟明列才可執
> 行；每個封存檔、每支程式**各一次**，輸出一律寫新目錄 `output/mvp_acceptance_r3/` 之下、**四個互不重疊
> 的子目錄**：① `python -m src.image_reverb <封存照片> --suggest --out-params
> output/mvp_acceptance_r3/params_suggested/<代號>.json`；② 同一張照片的全自動路徑報告項 run
> （V2-D），輸出 `output/mvp_acceptance_r3/auto_runs/<代號>/`——**封存照片只跑預設路徑一次、不跑
> `--force-low-confidence`**，v1 口徑中要靠 forced 那次才算得出的部分在 REPORT 記「未跑（18-a）」；非封
> 存照片（V2-D 所列的 8 場地）不受 18-a 限制，照 R2 做法預設＋forced 各一次（V2-D 的「各跑一次」對非封
> 存照片＝預設＋forced 一組）；③ 對 `assets/reference_rooms_heldout/` 的參考 IR 跑 V2-2(e) 參考值可算性
> 檢查、V2-2(d) 參考值計算與 V2-2(k) 品質揭露（R3 工具卡的腳本；**只能在參數鎖定 commit 之後**，程序
> P-5），輸出 `output/mvp_acceptance_r3/reference_metrics/`；定義 RR 的紀錄寫
> `output/mvp_acceptance_r3/run_evidence/`，它不是 ①②③ 的輸出目錄（RR-1）；
>
> ④**獨立複驗**：T-17-R3 的獨立複驗者可以對 ③ 在 scratchpad **重算一次**，結果必須與 R3 commit 的數值
> 逐位元相同（不同＝複驗不通過，不得擇一採用）——複驗者須在 `pip freeze | shasum -a 256` 與 R3
> `run_evidence/env_freeze.sha256` 相同、且 `python -VV` 與 `env_python.txt` 逐字相同的環境執行（不同 →
> 先對齊環境，不得以環境差異為由放寬），「逐位元相同」指 R3 commit 內 JSON 的數值字串逐字相同；④ 的輸
> 出目標位置＝複驗者事先宣告的單一 scratchpad 子目錄，重跑次數與 ③ 分開計（定義 RR 的 RR-1、RR-5）；①
> 與 ② 只核對輸出檔的 sha256 與 provenance，**不重跑**。`--params` 不讀照片，不在此限。除 ①②③④ 外的任
> 何模型、腳本、測試、視覺化都不得碰封存檔。
>
> (3) **重跑**：①②③④ 的重跑條件＝SPEC §7 程序 P 的「定義 RR」五條，全文適用、不另立定義；不符任何一
> 條 → 不得重跑。SPEC §7-v2 估計式「不符合時的處置」(甲) 在讀取任何輸入之前結束的事前自檢，不是
> ①②③④ 的執行、不計入「各一次」、也不是重跑。
>
> (4) **解除**：T-17-R3 收工＋獨立複驗通過後由 Fable 寫解除紀錄；解除前其他卡（含 T-59／T-68／T-69）一
> 律不得使用封存檔。
>
> (5) 任何 README 或卡片在 18-a 經核准寫入前引用其文字，須標「草案；T-63 r(n) 核准前從嚴＝沒有任何授
> 權」。

（本 README 於 3b 撰寫時，18-a 已核准生效，不再需要標「草案」。）

## 目錄結構

```
reference_rooms_heldout/
├── SURVEY.md                 T-70 步驟 1～2 調查表
├── rooms.json                五條件逐房間結果（included／blocked_pending_fable／excluded 三桶）
├── ASSET_MANIFEST.json       全部檔案 sha256／位元組數；reference_irs（v3b 起）
├── README.md                 本檔
├── _download/                三個下載整包（tgz／tar.gz；.gitignore 忽略；3b 經 Opus 驗證通過前不刪）
├── BUT_ReverbDB/<房間>/       官方目錄原樣解出（四房：L207/L212/Hotel_SkalskyDvur_Room112/C236）
│   └── materials_official.txt   白名單抽取的材質欄位（原檔 env_meta.txt 不進 git、不得整檔顯示）
└── SoundCam/<房間>/           ConferenceRoom／TreatedRoom；官方目錄在其下一層
    ├── <房間>_preprocessed/   官方解壓目錄（Conference 全解；Treated 只解 Empty/）
    └── paper_figs/            自論文 PDF 抽取的內嵌原生影像（僅 Fig.4／Fig.8；Fig.5 不授權使用）
```

**官方目錄 ↔ 本地房間目錄對照**（T-70 r6-5(i)）：BUT 四房的本地 `<房間>/` 就是官方 tgz 根目錄下的房間
目錄，同一層。SoundCam 的官方目錄在本地房間目錄**下一層**：`SoundCam/ConferenceRoom/` 下的
`ConferenceRoom_preprocessed/` 才是官方解壓根；`paper_figs/` 是 T-70 另加的、不屬官方資料集。

**manifest 路徑根換算**（T-70 r6-5(ii)）：`ASSET_MANIFEST.json` 的路徑以 `assets/reference_rooms_heldout/`
為根；`rooms.json` 的 `suggest_photo`／候選照片路徑以**該房間本地目錄**為根（去掉共同前綴
`<資料集>/<房間>/` 即可換算）。

## 授權與引用（見 `assets/SOURCES.md` 新增段；本卡新增）

- **SoundCam**：Wang, Clarke, Wang, Gao, Wu, *SoundCam: A Dataset for Finding Humans Using Room
  Acoustics*, NeurIPS 2023 Datasets & Benchmarks; arXiv:2311.03517。授權：MIT（Stanford PURL 頁面聲
  明）。
- **BUT ReverbDB**：Szöke et al., *Building and evaluation of a real room impulse response dataset*,
  IEEE JSTSP 2019；授權：CC BY 4.0（官網頁面聲明；`read_me.txt` 檔頭 Apache 2.0 只是說明檔／腳本本身的
  版權聲明，不是資料授權）。

僅供本專案內部非商業使用；再散布前須依上列授權條款處理。
