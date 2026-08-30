#!/usr/bin/env python3
"""T-17 §7-1：盲聽配對測試素材產生器。

跑法：`python scripts/t17_blind_test.py`
輸出：`output/mvp_acceptance/blind_test/` 底下 5 個**檔名不洩露答案**的試聽檔，
      ＋ `blind_test_ANSWERS.json`（答案鍵，使用者作答**前**不要打開）。

**盲聽的「盲」是這支腳本的唯一職責**，所以做了三件事：
1. 檔名只有 `sample_1.wav`…`sample_5.wav`，不含空間名、不含來源照片檔名。
2. 順序由**固定種子**打亂（種子寫死在原始碼，可重跑複驗），不是照原順序改名——
   照原順序改名等於沒打亂，`sample_1` 永遠是浴室。
3. 檔案的 mtime 全部對齊，避免用「檔案建立時間 = 生成順序」反推答案。

**產物來源查核（T-17 診斷 P2 修正）**：舊版只檢查 `wet_preview.wav` 存在就複製，
等於允許「拿舊產物驗收新程式」。現在會核對 `analysis.json` 記錄的來源照片是否就是
本次要用的那張、比對產物與照片的 mtime 先後，並把 git revision（含 `src/`、`data/`
是否 dirty）與三個檔的 sha256 寫進 `blind_test/MANIFEST.json`。

**已知限制（REPORT 必須寫）**：乾聲目前只有 `assets/dry/clap_synth.wav`（numpy 合成
拍手）。真實說話乾聲是 HANDOFF §4「等使用者的事」的待補項；用拍手做空間類型配對
比用人聲難，這會讓 §7-1 的分數偏保守（低估），不會偏樂觀。
"""

from __future__ import annotations

import hashlib
import json
import random
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "output" / "mvp_acceptance" / "blind_test"

SHUFFLE_SEED = 20260830  # 寫死＝可重跑複驗；改這個數字會得到不同的打亂順序

# SPEC §7-1 指定的 5 類代表性空間 → 本專案的測試照片
SPACES = [
    ("浴室", "bathroom_tiled"),
    ("客廳／臥室（住宅尺度）", "bedroom_ai_generated"),
    ("教堂／大空間", "arena_ntsu_linkou"),
    ("走廊／樓梯間", "stairwell_tiled"),
    ("車內", "car_interior_suv"),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_rev() -> str:
    """記錄產生素材時的 git revision，讓「舊產物驗收新程式」事後查得出來。"""
    try:
        rev = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip() or "unknown"
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--", "src", "data"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        return rev + ("+dirty(src/data)" if dirty else "")
    except Exception:
        return "unknown"


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    items = []
    stale: list[str] = []
    for space_type, run in SPACES:
        wet = REPO_ROOT / "output" / run / "wet_preview.wav"
        ir = REPO_ROOT / "output" / run / "ir_mono.wav"
        aj = REPO_ROOT / "output" / run / "analysis.json"
        photo = REPO_ROOT / "assets" / "photos" / f"{run}.png"
        if not wet.exists() or not ir.exists() or not aj.exists():
            print(f"❌ 缺少 output/{run}/（請先跑 `python -m src.image_reverb "
                  f"assets/photos/{run}.png`）", file=sys.stderr)
            return 1

        # 產物來源查核（T-17 診斷 P2）：只檢查存在性會讓舊產物被拿去驗收新程式
        meta = json.loads(aj.read_text(encoding="utf-8"))
        if Path(meta.get("input", "")).name != photo.name:
            stale.append(
                f"{run}：analysis.json 記錄來源是 "
                f"{Path(meta.get('input','')).name}，不是 {photo.name}"
            )
        if not photo.exists():
            stale.append(f"{run}：找不到來源照片 {photo}")
        elif aj.stat().st_mtime < photo.stat().st_mtime:
            stale.append(f"{run}：analysis.json 比來源照片舊，產物過期")

        items.append({
            "space_type": space_type, "run": run, "wet": wet, "ir": ir,
            "photo_sha256": _sha256(photo) if photo.exists() else None,
            "ir_sha256": _sha256(ir), "wet_sha256": _sha256(wet),
            "dims_source": meta.get("dims_source"),
            "confidence": meta.get("confidence"),
        })

    if stale:
        print("❌ 產物來源查核失敗（可能拿舊產物驗收新程式）：", file=sys.stderr)
        for m in stale:
            print(f"   - {m}", file=sys.stderr)
        print("   請先重跑 `python -m src.image_reverb assets/photos/<name>.png`",
              file=sys.stderr)
        return 1

    order = list(range(len(items)))
    random.Random(SHUFFLE_SEED).shuffle(order)

    answers = []
    for slot, idx in enumerate(order, start=1):
        it = items[idx]
        dst_wet = OUT_DIR / f"sample_{slot}.wav"
        dst_ir = OUT_DIR / f"sample_{slot}_IR.wav"
        shutil.copyfile(it["wet"], dst_wet)
        shutil.copyfile(it["ir"], dst_ir)
        answers.append(
            {
                "sample": f"sample_{slot}",
                "correct_space_type": it["space_type"],
                "source_run": it["run"],
                "source_photo": f"assets/photos/{it['run']}.png",
            }
        )
        print(f"  sample_{slot}.wav  ←  （答案已寫入 ANSWERS 檔，此處不印）")

    # mtime 對齊：避免用檔案時間反推生成順序
    for p in sorted(OUT_DIR.iterdir()):
        import os

        os.utime(p, (1000000000, 1000000000))

    (OUT_DIR / "MANIFEST.json").write_text(
        json.dumps({
            "git_revision": _git_rev(),
            "shuffle_seed": SHUFFLE_SEED,
            "generated_from": [
                {k: it[k] for k in ("run", "photo_sha256", "ir_sha256",
                                    "wet_sha256", "dims_source", "confidence")}
                for it in items
            ],
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    key_path = OUT_DIR.parent / "blind_test_ANSWERS.json"
    key_path.write_text(
        json.dumps(
            {
                "shuffle_seed": SHUFFLE_SEED,
                "dry_signal": "assets/dry/clap_synth.wav（合成拍手；真實人聲乾聲待補）",
                "answers": answers,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    sheet = OUT_DIR / "作答表.md"
    sheet.write_text(
        "# §7-1 盲聽配對作答表\n\n"
        "請依序聽 `sample_1.wav` ～ `sample_5.wav`（已經是加了殘響的試聽檔），\n"
        "在下表填入你認為的空間類型。**作答完成前請不要打開 "
        "`../blind_test_ANSWERS.json`。**\n\n"
        "可選的空間類型（5 選 1，每個只會用到一次）：\n"
        "浴室 ／ 客廳臥室 ／ 教堂大空間 ／ 走廊樓梯間 ／ 車內\n\n"
        "| 檔案 | 你聽到的空間類型 | 備註（聽感、有沒有鐵筒子味）|\n"
        "|---|---|---|\n"
        + "".join(f"| `sample_{i}.wav` | | |\n" for i in range(1, len(items) + 1))
        + "\n`sample_N_IR.wav` 是對應的原始 IR（不含乾聲），"
        "§7-3 要載入 convolution reverb 測試時用這個。\n",
        encoding="utf-8",
    )

    print(f"\n✅ 盲聽素材：{OUT_DIR.relative_to(REPO_ROOT)}/（5 組，檔名不洩露答案）")
    print(f"   作答表：{sheet.relative_to(REPO_ROOT)}")
    print(f"   答案鍵：{key_path.relative_to(REPO_ROOT)}（作答前請勿打開）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
