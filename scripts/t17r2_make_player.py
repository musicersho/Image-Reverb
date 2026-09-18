#!/usr/bin/env python3
"""T-57／T-17-R2 步驟 5：R2 版「一頁點開就能聽」的播放頁（薄包裝）。

跑法：`python scripts/t17r2_make_player.py`（需先跑過
`t17r2_dataset_manifest.py`／`t17r2_blind_test.py`／`t17r2_rt60_table.py`）
輸出：`output/mvp_acceptance_r2/播放頁.html`＋`output/mvp_acceptance_r2/_play/`

**沿用 `t17_make_player.py` 的 `to16()`／`audio_block()`**，不重新實作 16-bit
轉檔或播放器 HTML 片段——那兩個函式跟「這頁要列哪些檔案」無關，是純工具函式。

**§7-4 清單怎麼決定**（R2 特有）：gate 擋下的照片，預設路徑那次**不會**留下
`output/<run>/`（pipeline 擋在合成之前，暫存產物直接清除）——所以每個 run 最終
只會有一份 `output/<run>/wet_preview.wav`，來自「預設路徑通過」或「被擋後
`--force-low-confidence` 重跑」兩者之一，不會同時存在両份。本頁直接用這一份，
`forced_low_confidence`（讀 `analysis.json`）決定要不要標「forced」，不必另外
判斷「自動 run 存在則用自動，否則用 forced」的分支邏輯——分支已經由「有沒有
這個目錄」自然決定了。
"""

from __future__ import annotations

import html
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from t17_make_player import to16, audio_block  # noqa: E402
from t17_rt60_table import VENUES  # noqa: E402
import t17r2_common as common  # noqa: E402

BLIND_N = 5
SPACE_OPTIONS = ["浴室", "客廳臥室", "教堂大空間", "走廊樓梯間", "車內"]


def _forced_tag(analysis_path: Path) -> str:
    import json

    if not analysis_path.exists():
        return "尚未產生"
    aj = json.loads(analysis_path.read_text(encoding="utf-8"))
    return "forced" if aj.get("forced_low_confidence") else "自動路徑通過"


def run(
    *,
    repo_root: Path = REPO_ROOT,
    out_dir: Path | None = None,
    output_root: Path | None = None,
    manifest_path: Path | None = None,
) -> int:
    out_dir = out_dir if out_dir is not None else (repo_root / "output" / "mvp_acceptance_r2")
    output_root = output_root if output_root is not None else (repo_root / "output")
    manifest_path = manifest_path if manifest_path is not None else (out_dir / "DATASET_MANIFEST.json")
    play_dir = out_dir / "_play"

    import json

    if not manifest_path.exists():
        print(f"❌ 找不到 {manifest_path}，請先跑 scripts/t17r2_dataset_manifest.py", file=sys.stderr)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if play_dir.exists():
        shutil.rmtree(play_dir)
    play_dir.mkdir(parents=True)

    made = 0
    blind_dir = out_dir / "blind_test"
    for i in range(1, BLIND_N + 1):
        src = blind_dir / f"sample_{i}.wav"
        if not src.exists():
            print(f"❌ 找不到 {src}，請先跑 scripts/t17r2_blind_test.py", file=sys.stderr)
            return 1
        to16(src, play_dir / f"sample_{i}.wav")
        made += 1
    ir_sample = blind_dir / "sample_3_IR.wav"
    if ir_sample.exists():
        to16(ir_sample, play_dir / "sample_3_IR.wav")
        made += 1

    listen_rows_data: list[tuple[str, str, str]] = []  # (播放檔相對 _play 路徑, 標題, 標記)
    for hp in manifest.get("heldout_photos", []):
        wet = output_root / hp["stem"] / "wet_preview.wav"
        tag = _forced_tag(output_root / hp["stem"] / "analysis.json")
        fn = f"heldout__{hp['stem']}__wet.wav"
        if wet.exists():
            to16(wet, play_dir / fn)
            made += 1
            listen_rows_data.append((fn, f"held-out：{hp['category']}", tag))
        else:
            listen_rows_data.append((None, f"held-out：{hp['category']}", "尚未產生"))

    for v in VENUES:
        stem = v["runs"][0]
        wet = output_root / stem / "wet_preview.wav"
        tag = _forced_tag(output_root / stem / "analysis.json")
        fn = f"venue__{v['key']}__wet.wav"
        if wet.exists():
            to16(wet, play_dir / fn)
            made += 1
            listen_rows_data.append((fn, v["label"], tag))
        else:
            listen_rows_data.append((None, v["label"], "尚未產生"))

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
    <label class="note">備註：<input type="text" data-note="{i}" placeholder="聽感、有沒有『拍鐵筒子』的 artifact…"></label>
  </div>
</div>"""
        )

    listen_rows = []
    for fn, title, tag in listen_rows_data:
        if fn is None:
            listen_rows.append(
                f"""<div class="card"><div class="cardhead"><strong>{html.escape(title)}</strong>
    <span class="meta">{html.escape(tag)}</span></div></div>"""
            )
            continue
        listen_rows.append(
            f"""<div class="card{' pair' if tag == 'forced' else ''}">
  <div class="cardhead"><strong>{html.escape(title)}</strong>
    <span class="meta">{html.escape(tag)}</span></div>
  {audio_block("_play/" + fn)}
</div>"""
        )

    ir_block = ""
    if ir_sample.exists():
        ir_block = f"""
<h2><span class="tag">SPEC §7-3</span>外部相容性　載入 convolution reverb</h2>
<p class="lead">把下面這個檔案拖進 Logic 的 Space Designer（或任一 convolution reverb），
確認 ① 能載入不報錯 ② 有殘響效果 ③ 長度看起來正常。</p>
<div class="card">
  <div class="cardhead"><span class="slot">sample_3_IR.wav</span></div>
  <p class="lead" style="margin:0 0 10px">要載進 plugin 的原始檔在這裡（Finder 路徑）：<br>
    <code>output/mvp_acceptance_r2/blind_test/sample_3_IR.wav</code></p>
  {audio_block("_play/sample_3_IR.wav")}
</div>
"""

    doc = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>T-17-R2 驗收試聽</title>
<style>
  :root {{ --bg:#fbfaf8; --fg:#1c1a17; --muted:#6b6560; --line:#e2ddd6;
    --card:#ffffff; --accent:#9a5b2c; --warn:#8a4b1f; --pairbg:#fdf4ea; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#17161a; --fg:#ece8e3; --muted:#9c948c; --line:#332f36;
      --card:#201e24; --accent:#d9955c; --warn:#e0a26a; --pairbg:#2a2119; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg);
    font:16px/1.65 -apple-system,"PingFang TC","Helvetica Neue",sans-serif; }}
  .wrap {{ max-width:820px; margin:0 auto; padding:32px 20px 80px; }}
  h1 {{ font-size:1.5rem; margin:0 0 4px; }}
  .sub {{ color:var(--muted); font-size:.9rem; margin-bottom:32px; }}
  h2 {{ font-size:1.1rem; margin:40px 0 6px; padding-top:20px; border-top:1px solid var(--line); }}
  h2 .tag {{ font-size:.75rem; color:var(--accent); font-weight:600; letter-spacing:.06em; display:block; }}
  p.lead {{ color:var(--muted); font-size:.92rem; margin:0 0 18px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:14px 16px; margin-bottom:12px; }}
  .card.pair {{ background:var(--pairbg); border-color:var(--accent); }}
  .cardhead {{ display:flex; flex-wrap:wrap; gap:10px; align-items:baseline; margin-bottom:10px; }}
  .slot {{ font:600 .95rem/1 ui-monospace,SFMono-Regular,Menlo,monospace; color:var(--accent); }}
  .meta {{ color:var(--muted); font-size:.83rem; }}
  audio {{ width:100%; height:36px; }}
  .ans {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:12px; padding-top:12px;
    border-top:1px dashed var(--line); font-size:.9rem; }}
  .ans label {{ display:flex; align-items:center; gap:6px; }}
  .ans .note {{ flex:1 1 260px; }}
  select, input[type=text] {{ font:inherit; font-size:.88rem; padding:5px 8px; border:1px solid var(--line);
    border-radius:6px; background:var(--bg); color:var(--fg); }}
  input[type=text] {{ width:100%; }}
  .callout {{ border-left:3px solid var(--warn); background:var(--pairbg); padding:12px 16px;
    border-radius:0 8px 8px 0; margin:16px 0; font-size:.9rem; }}
  button {{ font:inherit; font-weight:600; padding:9px 18px; border-radius:8px; border:1px solid var(--accent);
    background:var(--accent); color:#fff; cursor:pointer; }}
  textarea {{ width:100%; min-height:130px; margin-top:12px; font:13px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace;
    padding:12px; border:1px solid var(--line); border-radius:8px; background:var(--card); color:var(--fg); }}
  code {{ font:.86em ui-monospace,SFMono-Regular,Menlo,monospace; background:var(--pairbg); padding:1px 5px; border-radius:4px; }}
  .foot {{ color:var(--muted); font-size:.82rem; margin-top:40px; padding-top:16px; border-top:1px solid var(--line); }}
</style></head><body><div class="wrap">

<h1>T-17-R2 MVP 重新驗收 · 試聽頁</h1>
<div class="sub">播放器走 16-bit 副本；§7-3 要載進 plugin 的仍然是原始 24-bit 檔。</div>

<h2><span class="tag">SPEC §7-1</span>盲聽配對　目標 ≥ 4/5</h2>
<p class="lead">五個空間類型各一個，順序已打亂。聽完在下面選你認為的空間類型。</p>
<div class="callout"><strong>作答完成前，請不要打開
<code>blind_test_ANSWERS.json</code>。</strong>這一頁（含 HTML 原始碼）不含任何答案。</div>
{"".join(blind_rows)}
<button id="gen">產生回報文字</button>
<textarea id="out" placeholder="按上面的按鈕，這裡會出現可以直接貼給我的文字…"></textarea>
{ir_block}
<h2><span class="tag">SPEC §7-4</span>人耳試聽　5 張 held-out ＋ 8 個對照場地</h2>
<p class="lead">每張標明是「自動路徑通過」還是「forced（被 gate 擋下、強制輸出）」。</p>
{"".join(listen_rows)}

<div class="foot">由 <code>scripts/t17r2_make_player.py</code> 產生。
完整結果見 <code>output/mvp_acceptance_r2/REPORT.md</code>。</div>

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
  var out = document.getElementById('out');
  out.value = lines.join('\\n');
  out.focus(); out.select();
}});
</script>
</body></html>
"""

    page = out_dir / "播放頁.html"
    page.write_text(doc, encoding="utf-8")
    print(f"✅ 播放副本 {made} 個 → {play_dir}/")
    print(f"✅ 播放頁 → {page}")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
