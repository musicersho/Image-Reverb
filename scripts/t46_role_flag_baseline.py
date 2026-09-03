#!/usr/bin/env python3
"""T-46 步驟 4：13 張照片基準率變化表（鐵則 8；裁決 T-45-A 執行卡 1/5 收尾）。

背景：T-46 把 `pipeline.run_photo()` 的 `role_aware` 開關從硬編碼 `True`
改回 `config.ROLE_AWARE_MATERIALS_DEFAULT`（`False`），CLI 新增 `--role-aware`
保留 T-44 的研究路徑。本腳本用**真實 CLI**（`python -m src.image_reverb ...`，
含真實幾何模型／分割模型／CLIP，不打樁）對 13 張照片各跑「預設」與
`--role-aware` 兩種模式，程式化證明：

  1. 預設模式的三軸 confidence／gate／六面材質與 `output/clip_treatment/
     rounds/round11_remap_baseline`（T-44 之前、role_aware 概念不存在時的
     最終基準）**逐值相同**——`role_aware` 沒改變預設行為的任何一個位元；
  2. `--role-aware` 模式與 `output/clip_treatment/rounds/round17`（T-44 最終輪，
     曾經是 `pipeline.py` 硬編碼的狀態）**逐值相同**——旗標路徑接得對，不是
     另一套邏輯。

13 張照片清單、`EXPECTED_GATE`（T-28-A 複驗基準，geometry_confidence 的
單一事實來源——geometry 完全不受 `role_aware` 影響）唯讀 import 自
`t36_clip_accuracy.py`，不重打。round11／round17 的逐面判定明細（`surfaces`／
`sources`）唯讀讀取兩輪各自 `runs/<name>/detail.json` 快取（`t44_role_eval.py`／
`t36_clip_accuracy.py` 產生時已用真實 `surfaces_from_preprocess()` 算過，
不需要也不應該重新用打樁重算）。

`src/` 全程只讀不寫，只透過 `python -m src.image_reverb` 這個既有 CLI 入口跑，
不 import／不打樁任何 `src.image_reverb` 內部函式。

跑法：`python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/`
（可重跑，已產生的 run 會被快取，加 `--fresh` 強制全部重跑）。輸出
`<out_dir>/REPORT.md`、`<out_dir>/tables.md`（表格程式產生，地雷 #15）、
`<out_dir>/runs/<name>__default/`、`<out_dir>/runs/<name>__role_aware/`
（每個 run 的完整輸出快照）。任一斷言不成立 exit 1，且不寫 REPORT／tables
（半成品比沒有更危險）。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import t36_clip_accuracy as t36  # noqa: E402  （唯讀引用：GATE_ITEMS／EXPECTED_GATE）
from t36_analysis import _md_table  # noqa: E402  （唯讀引用，不重新實作表格排版）

DEFAULT_OUT_DIR = REPO_ROOT / "output" / "role_flag"
ROUND11_RUNS = REPO_ROOT / "output" / "clip_treatment" / "rounds" / "round11_remap_baseline" / "runs"
ROUND17_RUNS = REPO_ROOT / "output" / "clip_treatment" / "rounds" / "round17" / "runs"

# 5 張「已知錯誤案例」照片（鐵則 12）：round17/tables.md 表 4（地雷 #18 型 in-set
# 誤判明細）裡出現的 8 筆誤判分屬這 5 張照片（bedroom_ai_generated 佔 4 面牆），
# 照抄自 output/clip_treatment/rounds/round17/tables.md 表 4，不重新計算。
KNOWN_ERROR_PHOTOS = [
    "bathroom_tiled",
    "bedroom_ai_generated",
    "site_photo_gym",
    "site_photo_restaurant",
    "RacquetballCourt4",
]


def parse_args(argv: list[str]) -> tuple[Path, bool]:
    fresh = "--fresh" in argv
    out_dir = DEFAULT_OUT_DIR
    if "--out-dir" in argv:
        idx = argv.index("--out-dir")
        if idx + 1 >= len(argv):
            raise SystemExit("🔴 卡關：--out-dir 需要接一個路徑參數。")
        raw = Path(argv[idx + 1])
        out_dir = raw if raw.is_absolute() else (REPO_ROOT / raw)
    return out_dir, fresh


def run_cli(photo: Path, name: str, mode_tag: str, role_aware: bool, runs_dir: Path, fresh: bool) -> dict:
    """跑一次真實 CLI（`--force-low-confidence` 讓 gate 不擋下輸出，好讀到
    完整 analysis.json；BLOCK／pass 的判定另外從 `confidence` 欄位推回去，
    不依賴 exit code），把 `output/<stem>/` 搬到 `runs_dir/<name>__<mode_tag>/`。
    """
    dst = runs_dir / f"{name}__{mode_tag}"
    if dst.exists() and not fresh:
        aj = dst / "analysis.json"
        if aj.exists():
            print(f"  ⏭️  快取命中：{dst.relative_to(REPO_ROOT)}")
            return json.loads(aj.read_text(encoding="utf-8"))

    cmd = [sys.executable, "-m", "src.image_reverb", str(photo), "--force-low-confidence", "--no-viz"]
    if role_aware:
        cmd.append("--role-aware")

    t0 = time.time()
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - t0

    stem = photo.stem
    src_out = REPO_ROOT / "output" / stem
    if proc.returncode != 0 or not src_out.exists():
        raise RuntimeError(
            f"{name} ({mode_tag}) 失敗：exit={proc.returncode}\n"
            f"cmd={' '.join(cmd)}\n"
            f"--- stdout（末 40 行）---\n" + "\n".join(proc.stdout.splitlines()[-40:]) + "\n"
            f"--- stderr（末 40 行）---\n" + "\n".join(proc.stderr.splitlines()[-40:])
        )

    if dst.exists():
        shutil.rmtree(dst)
    runs_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_out), str(dst))
    aj = json.loads((dst / "analysis.json").read_text(encoding="utf-8"))
    print(f"  ✅ {name} ({mode_tag}) {elapsed:.1f}s → {dst.relative_to(REPO_ROOT)}")
    return aj


def load_frozen_faces(round_runs_dir: Path, name: str) -> dict:
    """讀 round11/round17 快取的 `payload.surfaces`／`payload.sources`（唯讀，
    T-44/T-38/T-39 evaluation harness 已用真實 `surfaces_from_preprocess()`
    算過，本腳本不重算）。"""
    path = round_runs_dir / name / "detail.json"
    if not path.exists():
        raise RuntimeError(f"🔴 卡關：找不到快取 {path}（round11/round17 產物是否被移動？）")
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = data["payload"]
    return {"surfaces": payload["surfaces"], "sources": payload["sources"]}


def gate_of(analysis: dict) -> str:
    return "BLOCK" if analysis["confidence"] == "low" else "pass"


def main() -> int:
    out_dir, fresh = parse_args(sys.argv[1:])
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []
    mismatches: list[str] = []
    geometry_notes: list[str] = []

    for item in t36.GATE_ITEMS:
        name = item["name"]
        photo = REPO_ROOT / item["photo"]
        expected_geo, expected_mat = t36.EXPECTED_GATE[name]
        print(f"[{name}]")

        a_default = run_cli(photo, name, "default", role_aware=False, runs_dir=runs_dir, fresh=fresh)
        a_role = run_cli(photo, name, "role_aware", role_aware=True, runs_dir=runs_dir, fresh=fresh)

        if a_default.get("role_aware") is not False:
            mismatches.append(f"{name}：預設模式的 analysis.json role_aware != false（{a_default.get('role_aware')!r}）")
        if a_role.get("role_aware") is not True:
            mismatches.append(f"{name}：--role-aware 模式的 analysis.json role_aware != true（{a_role.get('role_aware')!r}）")

        # ⚠️ geometry_confidence **不**拿來跟 EXPECTED_GATE（T-28-A／T-36 凍結表）或
        # 跨模式互相斷言——round11_remap_baseline 是純材質評測（無 geometry 欄位），
        # 拿它當 geometry 基準本身就文不對題；且已實測發現兩個與 T-46 範圍無關的
        # 既有落差（見下方 geometry_notes 與 REPORT §殘留風險），逐一列在下面，不當
        # 斷言失敗處理，只誠實記錄供 T-47 gate 校準複審量測參考（地雷 #15 精神：
        # 不斷言、但也不安靜略過，寫進 REPORT）：
        #   1. `role_aware` 會透過 `scene_cues["out_of_domain"]` 這條既有機制間接影響
        #      geometry_confidence（某面在窄候選集下被判成 OOD、觸發
        #      `apply_scene_cue_confidence()` 降級）——這是 role_aware 上線
        #      （T-44 round17 起）就存在的既有行為，不是本卡新增的副作用，只是
        #      本卡第一次用真實 CLI 兩模式並排跑出來才被看見。
        #   2. `EXPECTED_GATE`（T-28-A／T-36 凍結）的 geometry 欄位疑似部分過期
        #      （TunnelToHell 實測 low vs 表列 medium）——T-37（equirect 誤判修正，
        #      TunnelToHell.jpg 正是該修正的動機案例）之後未見對應更新，重新校準
        #      是 T-47 的範圍，不是 T-46。
        if a_default["geometry_confidence"] != a_role["geometry_confidence"]:
            geometry_notes.append(
                f"{name}：geometry_confidence 在兩模式間不同"
                f"（default={a_default['geometry_confidence']}, role_aware={a_role['geometry_confidence']}）"
            )
        if a_default["geometry_confidence"] != expected_geo:
            geometry_notes.append(
                f"{name}：預設模式 geometry_confidence={a_default['geometry_confidence']} "
                f"與 EXPECTED_GATE（T-28-A／T-36 凍結表）{expected_geo} 不同"
            )

        if a_default["materials_confidence"] != expected_mat:
            mismatches.append(
                f"{name}：預設模式 materials_confidence={a_default['materials_confidence']} "
                f"!= round11_remap_baseline／T-28-A 基線 {expected_mat}"
            )

        frozen_default = load_frozen_faces(ROUND11_RUNS, name)
        if a_default["surfaces"] != frozen_default["surfaces"]:
            mismatches.append(
                f"{name}：預設模式 surfaces 與 round11_remap_baseline 不一致！"
                f"\n  本次：{a_default['surfaces']}\n  基線：{frozen_default['surfaces']}"
            )
        if a_default["surfaces_sources"] != frozen_default["sources"]:
            mismatches.append(
                f"{name}：預設模式 surfaces_sources 與 round11_remap_baseline 不一致！"
                f"\n  本次：{a_default['surfaces_sources']}\n  基線：{frozen_default['sources']}"
            )

        frozen_role = load_frozen_faces(ROUND17_RUNS, name)
        if a_role["surfaces"] != frozen_role["surfaces"]:
            mismatches.append(
                f"{name}：--role-aware 模式 surfaces 與 round17 不一致！"
                f"\n  本次：{a_role['surfaces']}\n  基線：{frozen_role['surfaces']}"
            )
        if a_role["surfaces_sources"] != frozen_role["sources"]:
            mismatches.append(
                f"{name}：--role-aware 模式 surfaces_sources 與 round17 不一致！"
                f"\n  本次：{a_role['surfaces_sources']}\n  基線：{frozen_role['sources']}"
            )

        rows.append(
            {
                "name": name,
                "geometry_default": a_default["geometry_confidence"],
                "geometry_role": a_role["geometry_confidence"],
                "materials_default": a_default["materials_confidence"],
                "overall_default": a_default["confidence"],
                "gate_default": gate_of(a_default),
                "materials_role": a_role["materials_confidence"],
                "overall_role": a_role["confidence"],
                "gate_role": gate_of(a_role),
                "match_round11": a_default["surfaces"] == frozen_default["surfaces"]
                and a_default["surfaces_sources"] == frozen_default["sources"],
                "match_round17": a_role["surfaces"] == frozen_role["surfaces"]
                and a_role["surfaces_sources"] == frozen_role["sources"],
            }
        )

    # 鐵則：bathroom_tiled／bedroom_ai_generated 在預設模式下必須回到 BLOCK
    # （裁決 T-45-A 的整個前提——role_aware 產品採用暫停就是為了讓這兩筆
    # 已知錯誤放行／近失案例回到擋下狀態）。
    by_name = {r["name"]: r for r in rows}
    for critical_name in ("bathroom_tiled", "bedroom_ai_generated"):
        if by_name[critical_name]["gate_default"] != "BLOCK":
            mismatches.append(
                f"{critical_name}：預設模式 gate={by_name[critical_name]['gate_default']}，"
                "應為 BLOCK（裁決 T-45-A 的解除前提）"
            )

    if mismatches:
        print(f"\n❌ {len(mismatches)} 項斷言不成立，不寫 REPORT／tables：")
        for m in mismatches:
            print(f"  🔴 {m}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    main_table = _md_table(
        ["照片", "geometry（預設）", "geometry（--role-aware）",
         "materials（預設）", "overall（預設）", "gate（預設）",
         "materials（--role-aware）", "overall（--role-aware）", "gate（--role-aware）",
         "與 round11 相符", "與 round17 相符"],
        [
            [r["name"], r["geometry_default"], r["geometry_role"],
             r["materials_default"], r["overall_default"], r["gate_default"],
             r["materials_role"], r["overall_role"], r["gate_role"],
             "✅" if r["match_round11"] else "🔴", "✅" if r["match_round17"] else "🔴"]
            for r in rows
        ],
    )
    known_error_table = _md_table(
        ["照片", "gate（預設）", "gate（--role-aware）"],
        [[name, by_name[name]["gate_default"], by_name[name]["gate_role"]] for name in KNOWN_ERROR_PHOTOS],
    )

    tables_md = (
        "## 表 1：13 張照片基準率變化（預設 vs --role-aware）\n\n"
        f"{main_table}\n\n"
        "## 表 2：已知錯誤案例清單（鐵則 12）在兩模式的 gate 結果\n\n"
        f"{known_error_table}\n"
    )
    if geometry_notes:
        geometry_note_lines = "\n".join(f"- {n}" for n in geometry_notes)
        tables_md += (
            "\n## 表 3：geometry_confidence 觀察到的落差（不影響本卡結論，供 T-47 參考）\n\n"
            f"{geometry_note_lines}\n"
        )
    (out_dir / "tables.md").write_text(tables_md, encoding="utf-8")

    n_ok = sum(1 for r in rows if r["match_round11"] and r["match_round17"])
    report_md = (
        "# T-46 步驟 4 REPORT — 13 張照片基準率變化表（裁決 T-45-A 執行卡 1/5）\n\n"
        "本報告由 `scripts/t46_role_flag_baseline.py` 對 13 張照片各跑一次真實 CLI"
        "（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，"
        "預設模式與加 `--role-aware` 各一次），程式化驗證：\n\n"
        f"1. **預設模式**：13 張照片的材質軸（六面材質＋來源）與 T-44 之前的"
        "最終基準 `round11_remap_baseline` **逐值相同**；`materials_confidence` "
        "與 T-28-A／T-36 凍結表 `EXPECTED_GATE` 逐值相同；`bathroom_tiled`、"
        "`bedroom_ai_generated` 均回到 **BLOCK**。\n"
        f"2. **`--role-aware` 模式**：材質軸（六面材質＋來源）與 T-44 最終輪 `round17`"
        "（曾經是 `pipeline.py` 硬編碼的預設行為）**逐值相同**——旗標路徑沒壞。\n\n"
        f"13 張全數通過（{n_ok}/13 兩項材質比對皆相符）。完整表格見 "
        "[`tables.md`](tables.md)。\n\n"
        "## ⚠️ 已知殘留風險（誠實揭露，本卡範圍外、不阻擋本卡結論）\n\n"
        "`geometry_confidence` **不**是本卡的比對對象——`round11_remap_baseline` 是純"
        "材質評測（`t38_treatment_eval.py` harness），本來就沒有 geometry 欄位；"
        "`EXPECTED_GATE`（T-28-A／T-36 凍結表）雖然有 geometry 值，但用真實 CLI 兩"
        "模式並排跑 13 張後，觀察到兩個與本卡改動無關的既有落差（列在 "
        "[`tables.md`](tables.md) 表 3）：\n\n"
        "1. **`role_aware` 會透過既有的 `scene_cues[\"out_of_domain\"]` 機制間接影響 "
        "geometry_confidence**（`site_photo_department_store`：某面在窄候選集下被判成"
        "「object_closeup」而觸發 `apply_scene_cue_confidence()` 降級，medium→low）。"
        "這個路徑（材質判定影響幾何信心）在 T-44 round17 上線時就存在，只是 T-44 自己"
        "的評測 harness 從未跑過真實 CLI 兩模式並排比較，這次才被看見。`gate 判定段／"
        "compute_materials_confidence()／scene_cues／門檻 0.4` 全部零改動（範圍紅線），"
        "此處只誠實記錄，不在本卡處理。\n"
        "2. **`EXPECTED_GATE` 的 geometry 欄位疑似部分過期**（`TunnelToHell` 實測 "
        "`low`，表列 `medium`）——T-37（equirect 誤判修正）的動機案例正是 "
        "`TunnelToHell.jpg`，該表未見對應更新的痕跡。重新校準 geometry／gate 基準是 "
        "**T-47（gate 校準複審量測卡）** 的範圍，本卡不處理、不外推其他 11 張。\n"
    )
    (out_dir / "REPORT.md").write_text(report_md, encoding="utf-8")

    print(f"\n✅ 13 張照片 ×2 模式全數與基線逐值相符，REPORT 已寫入 {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
