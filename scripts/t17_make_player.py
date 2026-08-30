#!/usr/bin/env python3
"""T-17：產生「一頁點開就能聽」的本機播放頁（§7-1 盲聽 / §7-3 / §7-4 試聽）。

跑法：`python scripts/t17_make_player.py`（跑完會印出開啟指令）
輸出：`output/mvp_acceptance/播放頁.html` ＋ `output/mvp_acceptance/_play/`（16-bit 播放副本）

**為什麼要另外做 16-bit 副本**：管線輸出的是 48kHz **24-bit** PCM WAV，而
`<audio>` 對 24-bit WAV 的支援**因瀏覽器而異**——Chromium 實測可以播（已驗證），
Safari 則不保證（本機無法驗證）。16-bit PCM WAV 是所有瀏覽器都吃的格式，
所以播放頁一律走 `_play/` 底下的 16-bit 副本，避免使用者遇到放不出來的情況。
**原始 24-bit 檔一個都沒動**——§7-3 要載進 convolution reverb 的仍然是原檔。
24→16 bit 對「聽空間類型／聽 artifact」聽不出差別（動態範圍 96dB 遠超需求）。

**盲性**：本頁的 §7-1 區塊與其 HTML 原始碼**都不含任何答案**——
連檔名對應表都不寫進去（view source 也看不到）。答案只在
`blind_test_ANSWERS.json`，作答完再打開。
"""

from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parent.parent
BASE = REPO_ROOT / "output" / "mvp_acceptance"
PLAY = BASE / "_play"

BLIND_N = 5

# §7-4：九個試聽檔。`pair` 標記的兩個是 REPORT §2.4 病因診斷的 A/B 對照組。
LISTEN = [
    ("racquetball_court_4__wet.wav", "壁球場（材質判錯）", "低頻聯合帶 −50%", "pair"),
    (
        "DIAG_racquetball_correct_dims_and_hard_materials__wet.wav",
        "壁球場（材質改對）",
        "低頻聯合帶 +13%、125Hz −3.3%",
        "pair",
    ),
    ("steinman_hall__wet.wav", "Steinman Hall 音樂廳", "全場最佳：500Hz–4kHz 四頻段全過", ""),
    ("tunnel_to_hell__wet.wav", "地下混凝土隧道", "聯合帶 +0.2%，但 1kHz +144%", ""),
    ("cathedral_room__wet.wav", "石灰岩洞窟", "聯合帶 +186%（過長）", ""),
    ("mit_department_store__wet.wav", "百貨賣場", "聯合帶 +121%", ""),
    ("mit_gym__wet.wav", "健身房", "聯合帶 −20%（低頻剛好壓線過）", ""),
    ("mit_restaurant__wet.wav", "餐廳", "聯合帶 −4%（低頻最準的一筆）", ""),
    ("divorce_beach__wet.wav", "戶外沙灘", "聯合帶 +676%——全表最大誤差，戶外無出口", ""),
]

SPACE_OPTIONS = ["浴室", "客廳臥室", "教堂大空間", "走廊樓梯間", "車內"]


def to16(src: Path, dst: Path) -> None:
    """轉 16-bit PCM 播放副本（取樣率、聲道、長度全部不變，只降位元深度）。"""
    data, fs = sf.read(str(src), always_2d=True)
    dst.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(dst), data, fs, subtype="PCM_16")


def audio_block(rel: str) -> str:
    return (
        f'<audio controls preload="none" src="{html.escape(rel)}">'
        f"你的瀏覽器放不出這個檔，請直接用 Finder 開 <code>{html.escape(rel)}</code>。</audio>"
    )


def main() -> int:
    if PLAY.exists():
        shutil.rmtree(PLAY)
    PLAY.mkdir(parents=True)

    made = 0
    for i in range(1, BLIND_N + 1):
        to16(BASE / "blind_test" / f"sample_{i}.wav", PLAY / f"sample_{i}.wav")
        made += 1
    to16(BASE / "blind_test" / "sample_3_IR.wav", PLAY / "sample_3_IR.wav")
    made += 1
    for fn, *_ in LISTEN:
        to16(BASE / "listening" / fn, PLAY / fn)
        made += 1

    # ---------- §7-1 盲聽（原始碼不含任何答案）----------
    blind_rows = []
    for i in range(1, BLIND_N + 1):
        opts = "".join(f'<option value="{o}">{o}</option>' for o in SPACE_OPTIONS)
        blind_rows.append(
            f"""<div class="card">
  <div class="cardhead"><span class="slot">sample_{i}</span></div>
  {audio_block(f"_play/sample_{i}.wav")}
  <div class="ans">
    <label>你聽到的空間：
      <select data-slot="{i}"><option value="">— 請選 —</option>{opts}</select>
    </label>
    <label class="note">備註：<input type="text" data-note="{i}"
      placeholder="聽感、有沒有『拍鐵筒子』的 artifact…"></label>
  </div>
</div>"""
        )

    listen_rows = []
    for fn, title, note, kind in LISTEN:
        cls = " pair" if kind == "pair" else ""
        listen_rows.append(
            f"""<div class="card{cls}">
  <div class="cardhead"><strong>{html.escape(title)}</strong>
    <span class="meta">{html.escape(note)}</span></div>
  {audio_block("_play/" + fn)}
</div>"""
        )

    doc = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>T-17 驗收試聽</title>
<style>
  :root {{
    --bg:#fbfaf8; --fg:#1c1a17; --muted:#6b6560; --line:#e2ddd6;
    --card:#ffffff; --accent:#9a5b2c; --warn:#8a4b1f; --pairbg:#fdf4ea;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg:#17161a; --fg:#ece8e3; --muted:#9c948c; --line:#332f36;
      --card:#201e24; --accent:#d9955c; --warn:#e0a26a; --pairbg:#2a2119;
    }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
    font:16px/1.65 -apple-system,"PingFang TC","Helvetica Neue",sans-serif; }}
  .wrap {{ max-width:820px; margin:0 auto; padding:32px 20px 80px; }}
  h1 {{ font-size:1.5rem; margin:0 0 4px; letter-spacing:-.01em; }}
  .sub {{ color:var(--muted); font-size:.9rem; margin-bottom:32px; }}
  h2 {{ font-size:1.1rem; margin:40px 0 6px; padding-top:20px;
    border-top:1px solid var(--line); }}
  h2 .tag {{ font-size:.75rem; color:var(--accent); font-weight:600;
    letter-spacing:.06em; display:block; margin-bottom:2px; }}
  p.lead {{ color:var(--muted); font-size:.92rem; margin:0 0 18px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:14px 16px; margin-bottom:12px; }}
  .card.pair {{ background:var(--pairbg); border-color:var(--accent); }}
  .cardhead {{ display:flex; flex-wrap:wrap; gap:10px; align-items:baseline;
    margin-bottom:10px; }}
  .slot {{ font:600 .95rem/1 ui-monospace,SFMono-Regular,Menlo,monospace;
    color:var(--accent); }}
  .meta {{ color:var(--muted); font-size:.83rem; }}
  audio {{ width:100%; height:36px; }}
  .ans {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:12px;
    padding-top:12px; border-top:1px dashed var(--line); font-size:.9rem; }}
  .ans label {{ display:flex; align-items:center; gap:6px; }}
  .ans .note {{ flex:1 1 260px; }}
  select, input[type=text] {{ font:inherit; font-size:.88rem; padding:5px 8px;
    border:1px solid var(--line); border-radius:6px;
    background:var(--bg); color:var(--fg); }}
  input[type=text] {{ width:100%; }}
  .callout {{ border-left:3px solid var(--warn); background:var(--pairbg);
    padding:12px 16px; border-radius:0 8px 8px 0; margin:16px 0;
    font-size:.9rem; }}
  button {{ font:inherit; font-weight:600; padding:9px 18px; border-radius:8px;
    border:1px solid var(--accent); background:var(--accent); color:#fff;
    cursor:pointer; }}
  button:hover {{ opacity:.88; }}
  textarea {{ width:100%; min-height:130px; margin-top:12px; font:13px/1.55
    ui-monospace,SFMono-Regular,Menlo,monospace; padding:12px;
    border:1px solid var(--line); border-radius:8px;
    background:var(--card); color:var(--fg); }}
  code {{ font:.86em ui-monospace,SFMono-Regular,Menlo,monospace;
    background:var(--pairbg); padding:1px 5px; border-radius:4px; }}
  .foot {{ color:var(--muted); font-size:.82rem; margin-top:40px;
    padding-top:16px; border-top:1px solid var(--line); }}
</style></head><body><div class="wrap">

<h1>T-17 MVP 驗收 · 試聽頁</h1>
<div class="sub">點播放鍵就能聽。播放器走的是 16-bit 副本（各家瀏覽器對 24-bit WAV
的支援不一致，16-bit 才是穩的）；§7-3 要載進 plugin 的仍然是原始 24-bit 檔。</div>

<h2><span class="tag">SPEC §7-1</span>盲聽配對　目標 ≥ 4/5</h2>
<p class="lead">五個空間類型各一個，順序已打亂。聽完在下面選你認為的空間類型，
選完按最下面的按鈕產生回報文字貼給我。</p>
<div class="callout"><strong>作答完成前，請不要打開
<code>blind_test_ANSWERS.json</code>。</strong>這一頁（含 HTML 原始碼）不含任何答案。</div>
{"".join(blind_rows)}
<button id="gen">產生回報文字</button>
<textarea id="out" placeholder="按上面的按鈕，這裡會出現可以直接貼給我的文字…"></textarea>

<h2><span class="tag">SPEC §7-3</span>外部相容性　載入 convolution reverb</h2>
<p class="lead">把下面這個檔案拖進 Logic 的 Space Designer（或任一 convolution reverb），
確認 ① 能載入不報錯 ② 有殘響效果 ③ 長度看起來正常。</p>
<div class="card">
  <div class="cardhead"><span class="slot">sample_3_IR.wav</span>
    <span class="meta">48kHz / 24-bit PCM / 5.60s —— 最長的一條，最容易聽出問題</span></div>
  <p class="lead" style="margin:0 0 10px">要載進 plugin 的原始檔在這裡（Finder 路徑）：<br>
    <code>output/mvp_acceptance/blind_test/sample_3_IR.wav</code></p>
  {audio_block("_play/sample_3_IR.wav")}
  <p class="lead" style="margin:8px 0 0">↑ 這個播放器是 16-bit 預覽，
    只是讓你先確認它不是靜音。</p>
</div>

<h2><span class="tag">SPEC §7-4</span>人耳試聽　八個對照場地 ＋ 一個診斷組</h2>
<div class="callout"><strong>最有資訊量的是前兩個（橘色框）。</strong>
兩者是<strong>同一支合成引擎、同一組尺寸</strong>，差別只在材質判定。
如果第二個明顯比第一個更像壁球場，你就用耳朵獨立確認了報告 §2.4 的病因診斷
——問題出在材質辨識，不在幾何、也不在合成引擎。</div>
<p class="lead">聽的時候請特別注意有沒有 HANDOFF 地雷 #9 那種「像用手拍鐵筒子」的 artifact。</p>
{"".join(listen_rows)}

<div class="foot">由 <code>scripts/t17_make_player.py</code> 產生。
原始 24-bit 檔一個都沒動；<code>_play/</code> 是可重新產生的播放副本。<br>
完整結果見 <code>output/mvp_acceptance/REPORT.md</code>。</div>

</div>
<script>
document.getElementById('gen').addEventListener('click', function () {{
  var lines = ['§7-1 盲聽作答：'];
  for (var i = 1; i <= {BLIND_N}; i++) {{
    var sel = document.querySelector('select[data-slot="' + i + '"]');
    var note = document.querySelector('input[data-note="' + i + '"]');
    var v = sel.value || '(未作答)';
    var n = note.value.trim();
    lines.push('  sample_' + i + ' → ' + v + (n ? '　備註：' + n : ''));
  }}
  lines.push('');
  lines.push('§7-3 載入 convolution reverb：（可以載入嗎？有殘響嗎？）');
  lines.push('§7-4 試聽（壁球場那組有沒有明顯差別？有沒有鐵筒子 artifact？）：');
  var out = document.getElementById('out');
  out.value = lines.join('\\n');
  out.focus(); out.select();
}});
</script>
</body></html>
"""

    page = BASE / "播放頁.html"
    page.write_text(doc, encoding="utf-8")
    print(f"✅ 播放副本 {made} 個 → {PLAY.relative_to(REPO_ROOT)}/（16-bit，原始 24-bit 檔未動）")
    print(f"✅ 播放頁 → {page.relative_to(REPO_ROOT)}")
    print(f"\n開啟：\n  open '{page}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
