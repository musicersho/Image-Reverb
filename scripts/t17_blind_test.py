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

**產物來源查核（T-43：改為溯源驗證，取代 T-17 診斷 P2 的存在性／mtime 查核）**：
P2 舊版只檢查 `analysis.json` 記錄的來源照片是否就是本次要用的那張、比對產物與
照片的 mtime 先後——外部掃描指出這**擋不住**「v1 碼產的 IR 拿去驗收 v2 碼」，
因為 mtime 只反映檔案系統時間，不反映「用哪個 revision 的程式產生」。現在改為
主證據：來源 `analysis.json` 必須有 `provenance`（`src/image_reverb/pipeline.py`
在生成當下寫入），且 (a) `git_revision.commit` 與盲測當下主 repo HEAD 相同、
雙方皆非 dirty（範圍 `src`＋`data`）、(b) `input_sha256` 與 `assets/photos/` 實檔
一致、(c) 模型 id／CLIP 門檻／`materials.json` hash 與當前 `config` 一致——任一
不符，或缺 `provenance`（T-43 之前的舊產物）→ exit 非 0，指示重生。原本的 mtime
檢查降級為輔助警示，不再是判定通過與否的主證據。

`MANIFEST.json` 分開記錄兩種 revision，不混用同一個鍵名：`packaging_git_revision`
＝打包（跑本腳本）當下的 HEAD；每筆 sample 的 `source_provenance`＝來源
`analysis.json` 的 `provenance` 區塊原文逐項複製（生成當下的 revision）。

**已知限制（REPORT 必須寫）**：乾聲目前只有 `assets/dry/clap_synth.wav`（numpy 合成
拍手）。真實說話乾聲是 HANDOFF §4「等使用者的事」的待補項；用拍手做空間類型配對
比用人聲難，這會讓 §7-1 的分數偏保守（低估），不會偏樂觀。
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.image_reverb import config  # noqa: E402
from src.image_reverb import provenance  # noqa: E402

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


def _expected_model_config() -> dict[str, object]:
    """T-43：溯源驗證要比對的「當下」模型／門檻設定——單一事實來源是
    `config` 模組（Opus 驗證重點紅旗：不得手打常數）。"""
    return {
        "segmentation_model_id": config.SEGMENTATION_MODEL_ID,
        "clip_model_id": config.CLIP_MODEL_ID,
        "clip_confidence_threshold": config.CLIP_CONFIDENCE_THRESHOLD,
    }


def verify_source_provenance(
    analysis: dict,
    photo: Path,
    materials_path: Path,
    repo_root: Path,
    expected_config: dict[str, object],
) -> list[str]:
    """T-43 溯源驗證核心：回傳不符項清單（空清單＝全部相符，可放行）。

    抽成獨立函式，讓 `test_t17_provenance.py` 可以在隔離 git repo 內重跑同一段
    判斷邏輯（不必真的跑模型、不必動到 `output/mvp_acceptance/`）。
    """
    prov = analysis.get("provenance")
    if not prov:
        return ["缺少 provenance（T-43 之前的舊產物，無法溯源，必須重生）"]

    errs: list[str] = []

    current_rev = provenance.git_revision(cwd=repo_root)
    source_rev = prov.get("git_revision") or {}
    if source_rev.get("commit") != current_rev["commit"]:
        errs.append(
            f"git_revision 不符：來源產物生成於 {source_rev.get('commit')!r}，"
            f"盲測當下主 repo HEAD 是 {current_rev['commit']!r}"
            "（拿舊碼產物驗收新碼，或反過來，必須重生）"
        )
    if current_rev["dirty"]:
        errs.append("盲測當下主 repo（src／data）為 dirty，不可信，必須先 commit 或還原")
    if source_rev.get("dirty"):
        errs.append("來源產物生成時主 repo（src／data）為 dirty，不可信，必須重生")

    if photo.exists():
        actual_photo_hash = provenance.sha256_file(photo)
        if prov.get("input_sha256") != actual_photo_hash:
            errs.append(
                f"input_sha256 不符：analysis.json 記 {prov.get('input_sha256')!r}，"
                f"實際照片檔 sha256 是 {actual_photo_hash!r}（來源照片已被替換，必須重生）"
            )
    else:
        errs.append(f"找不到來源照片 {photo}")

    if materials_path.exists():
        actual_materials_hash = provenance.sha256_file(materials_path)
        if prov.get("materials_json_sha256") != actual_materials_hash:
            errs.append(
                f"materials_json_sha256 不符：analysis.json 記 "
                f"{prov.get('materials_json_sha256')!r}，實際 {materials_path.name} "
                f"是 {actual_materials_hash!r}（材質資料表已變更，必須重生）"
            )
    else:
        errs.append(f"找不到 {materials_path}")

    for key, expected in expected_config.items():
        if prov.get(key) != expected:
            errs.append(
                f"{key} 不符：analysis.json 記 {prov.get(key)!r}，"
                f"當前 config 是 {expected!r}（模型／門檻設定已變更，必須重生）"
            )

    return errs


def run(
    *,
    repo_root: Path = REPO_ROOT,
    out_dir: Path = OUT_DIR,
    spaces: list[tuple[str, str]] | None = None,
    photos_dir: Path | None = None,
    outputs_dir: Path | None = None,
    materials_path: Path | None = None,
    expected_config: dict[str, object] | None = None,
) -> int:
    """主流程。抽成函式（帶預設值＝真實專案路徑）讓
    `test_t17_provenance.py` 可以指到隔離 git repo 重跑同一段溯源驗證邏輯；
    `main()` 只是套上真實路徑的薄殼。"""
    spaces = spaces if spaces is not None else SPACES
    photos_dir = photos_dir or (repo_root / "assets" / "photos")
    outputs_dir = outputs_dir or (repo_root / "output")
    materials_path = materials_path or (repo_root / "data" / "materials.json")
    expected_config = expected_config if expected_config is not None else _expected_model_config()

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    items = []
    stale: list[str] = []
    for space_type, run_name in spaces:
        wet = outputs_dir / run_name / "wet_preview.wav"
        ir = outputs_dir / run_name / "ir_mono.wav"
        aj = outputs_dir / run_name / "analysis.json"
        photo = photos_dir / f"{run_name}.png"
        if not wet.exists() or not ir.exists() or not aj.exists():
            print(f"❌ 缺少 output/{run_name}/（請先跑 `python -m src.image_reverb "
                  f"assets/photos/{run_name}.png`）", file=sys.stderr)
            return 1

        meta = json.loads(aj.read_text(encoding="utf-8"))

        # T-43：溯源驗證取代單純的存在性／mtime 檢查——主證據是 provenance。
        prov_errs = verify_source_provenance(meta, photo, materials_path, repo_root, expected_config)
        for e in prov_errs:
            stale.append(f"{run_name}：{e}")

        # 既有 mtime 檢查降級為輔助警示（T-43：不再是主證據，只協助人眼發現
        # 「忘記重跑」這類明顯狀況；判定通過與否一律看上面的 provenance）。
        if photo.exists() and aj.stat().st_mtime < photo.stat().st_mtime:
            print(
                f"⚠️ {run_name}：analysis.json 比來源照片舊（輔助警示，不影響通過判定，"
                "主證據見 provenance）",
                file=sys.stderr,
            )

        items.append({
            "space_type": space_type, "run": run_name, "wet": wet, "ir": ir,
            "photo_sha256": _sha256(photo) if photo.exists() else None,
            "ir_sha256": _sha256(ir), "wet_sha256": _sha256(wet),
            "dims_source": meta.get("dims_source"),
            "confidence": meta.get("confidence"),
            "source_provenance": meta.get("provenance"),
        })

    if stale:
        print("❌ 溯源驗證失敗（可能拿舊產物驗收新程式，或環境已變更）：", file=sys.stderr)
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
        dst_wet = out_dir / f"sample_{slot}.wav"
        dst_ir = out_dir / f"sample_{slot}_IR.wav"
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
    for p in sorted(out_dir.iterdir()):
        os.utime(p, (1000000000, 1000000000))

    packaging_rev = provenance.git_revision(cwd=repo_root)
    (out_dir / "MANIFEST.json").write_text(
        json.dumps({
            "packaging_git_revision": packaging_rev,
            "shuffle_seed": SHUFFLE_SEED,
            "generated_from": [
                {
                    **{k: it[k] for k in ("run", "photo_sha256", "ir_sha256",
                                           "wet_sha256", "dims_source", "confidence")},
                    "source_provenance": it["source_provenance"],
                }
                for it in items
            ],
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    key_path = out_dir.parent / "blind_test_ANSWERS.json"
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

    sheet = out_dir / "作答表.md"
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

    print(f"\n✅ 盲聽素材：{out_dir.relative_to(repo_root)}/（5 組，檔名不洩露答案）")
    print(f"   作答表：{sheet.relative_to(repo_root)}")
    print(f"   答案鍵：{key_path.relative_to(repo_root)}（作答前請勿打開）")
    return 0


def main() -> int:
    return run()


if __name__ == "__main__":
    sys.exit(main())
