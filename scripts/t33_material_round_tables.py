#!/usr/bin/env python3
"""T-33：材質輪基準率複測（裁決 T-27-A 執行卡 3/3；量測卡）。

跑法：`python scripts/t33_material_round_tables.py`（可重跑；已產生的 run 會被快取，
加 `--fresh` 強制全部重跑）。

**這是量測卡的量測驅動程式**：只呼叫 CLI（`python -m src.image_reverb ...`）與既有的
`src/image_reverb/ir_metrics.py`（透過 import `scripts/t17_rt60_table.py` 重用其
`measure_file()`／`real_reference()`／`error_vs_reference()`／`ratio()`，不重新實作
量測或比對邏輯——`t33` 只加「陳設 A/B 兩組」這個新維度）。`src/` 全程只讀不寫。

輸出（`output/material_round/`，**不觸碰 `output/mvp_acceptance/`**——鐵則 4）：
  - `runs/<name>__with_furn/`、`runs/<name>__no_furn/`：每個 run 的完整輸出快照
    （從 `output/<photo_stem>/` 搬移過來，避免同 stem 的 A/B 兩次呼叫互相覆蓋）
  - `data.json`：全部原始量測數字（表格與 REPORT 的唯一數字來源）
  - `tables.md`：程式產生的表格（地雷 #15：不手打表格）
  - `listen_bedroom_with_furnishings.wav` / `listen_bedroom_without_furnishings.wav`

**13 張照片基準率複測**（步驟 1）：8 個 §7-2 對照場地照片 + 5 個 §7-1 盲聽照片，
预設幾何（不覆寫尺寸）＋ `--force-low-confidence --no-viz`，量測 geometry/materials
confidence **必須與裁決 T-28-A 複驗的基準完全相同**（`EXPECTED_GATE` 表）——
不同就是動到 gate，腳本直接 `sys.exit(1)`，不寫 `data.json`／`tables.md`。

**達標率 before/after**（步驟 2）：8 個對照場地（自動幾何）與 5 個 F-09 手動 run
（`--override-dims`，尺寸依據見 `output/mvp_acceptance/tables.md` 表 4）各自重跑兩組
（預設陳設 vs `--no-furnishings`），對照真實 IR（自行從 `assets/reference_irs/` 量測，
不讀快取的 `output/mvp_acceptance/rt60_table.json`，避免任何對 mvp_acceptance 產物的
隱性依賴）。判準與 T-17 §7-2 相同：500Hz/1kHz/2kHz/4kHz 各頻段 + 88.4–353.6Hz 低頻
聯合帶，五項各自 <20% 誤差算通過。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from src.image_reverb import ir_metrics  # noqa: E402
import t17_rt60_table as t17  # noqa: E402  （重用 measure_file/real_reference/error_vs_reference/ratio）

BANDS = t17.BANDS
OUT_DIR = REPO_ROOT / "output" / "material_round"
RUNS_DIR = OUT_DIR / "runs"
REF_ROOT = REPO_ROOT / "assets" / "reference_irs"
DRY = REPO_ROOT / "assets" / "dry" / "clap_synth.wav"
CONVOLVE = REPO_ROOT / "scripts" / "convolve.py"

# ------------------------------------------------------------------
# 13 張照片（8 對照場地 + 5 盲聽），裁決 T-28-A 複驗基準（TASKS.md T-28 卡「三處更正」）
# ------------------------------------------------------------------
EXPECTED_GATE = {
    # name: (expected_geometry_confidence, expected_materials_confidence)
    "bathroom_tiled": ("medium", "low"),
    "bedroom_ai_generated": ("medium", "low"),
    "stairwell_tiled": ("medium", "low"),
    "arena_ntsu_linkou": ("low", "low"),
    "car_interior_suv": ("low", "low"),
    "CathedralRoom": ("medium", "low"),
    "DivorceBeach": ("low", "medium"),
    "site_photo_department_store": ("medium", "low"),
    "site_photo_gym": ("low", "low"),
    "site_photo_restaurant": ("low", "low"),
    "RacquetballCourt4": ("medium", "low"),
    "SteinmanHall": ("low", "low"),
    "TunnelToHell": ("medium", "low"),
}

GATE_ITEMS = [
    {"name": "bathroom_tiled", "photo": "assets/photos/bathroom_tiled.png", "venue_key": None},
    {"name": "bedroom_ai_generated", "photo": "assets/photos/bedroom_ai_generated.png", "venue_key": None},
    {"name": "stairwell_tiled", "photo": "assets/photos/stairwell_tiled.png", "venue_key": None},
    {"name": "arena_ntsu_linkou", "photo": "assets/photos/arena_ntsu_linkou.png", "venue_key": None},
    {"name": "car_interior_suv", "photo": "assets/photos/car_interior_suv.png", "venue_key": None},
    {
        "name": "CathedralRoom",
        "photo": "assets/reference_irs/cathedral_room_shasta_lake_caverns/CathedralRoom.jpg",
        "venue_key": "cathedral_room_shasta_lake_caverns",
    },
    {
        "name": "DivorceBeach",
        "photo": "assets/reference_irs/divorce_beach/DivorceBeach.jpg",
        "venue_key": "divorce_beach",
    },
    {
        "name": "site_photo_department_store",
        "photo": "assets/reference_irs/mit_department_store/site_photo_department_store.png",
        "venue_key": "mit_department_store",
    },
    {
        "name": "site_photo_gym",
        "photo": "assets/reference_irs/mit_gym/site_photo_gym.png",
        "venue_key": "mit_gym",
    },
    {
        "name": "site_photo_restaurant",
        "photo": "assets/reference_irs/mit_restaurant/site_photo_restaurant.png",
        "venue_key": "mit_restaurant",
    },
    {
        "name": "RacquetballCourt4",
        "photo": "assets/reference_irs/racquetball_court_4/RacquetballCourt4.jpg",
        "venue_key": "racquetball_court_4",
    },
    {
        "name": "SteinmanHall",
        "photo": "assets/reference_irs/steinman_hall/SteinmanHall.jpg",
        "venue_key": "steinman_hall",
    },
    {
        "name": "TunnelToHell",
        "photo": "assets/reference_irs/tunnel_to_hell/TunnelToHell.jpg",
        "venue_key": "tunnel_to_hell",
    },
]

# 8 個對照場地：自動組用哪個 GATE_ITEMS 條目（venue_key 非 None 的 8 筆，順序固定）
AUTO_VENUE_ORDER = [
    "cathedral_room_shasta_lake_caverns",
    "divorce_beach",
    "mit_department_store",
    "mit_gym",
    "mit_restaurant",
    "racquetball_court_4",
    "steinman_hall",
    "tunnel_to_hell",
]

# 5 個 F-09 手動 run：尺寸依據見 output/mvp_acceptance/tables.md 表 4（不變動、原樣沿用）
MANUAL_ITEMS = [
    {
        "name": "t17_manual_department_store",
        "photo": "assets/reference_irs/mit_department_store/site_photo_department_store.png",
        "override_dims": "35.00x25.00x3.20",
        "venue_key": "mit_department_store",
    },
    {
        "name": "t17_manual_gym",
        "photo": "assets/reference_irs/mit_gym/site_photo_gym.png",
        "override_dims": "9.00x6.00x2.90",
        "venue_key": "mit_gym",
    },
    {
        "name": "t17_manual_restaurant",
        "photo": "assets/reference_irs/mit_restaurant/site_photo_restaurant.png",
        "override_dims": "14.00x9.00x3.20",
        "venue_key": "mit_restaurant",
    },
    {
        "name": "t17_manual_racquetball",
        "photo": "assets/reference_irs/racquetball_court_4/RacquetballCourt4.jpg",
        "override_dims": "12.19x6.10x6.10",
        "venue_key": "racquetball_court_4",
    },
    {
        "name": "t17_manual_steinman",
        "photo": "assets/reference_irs/steinman_hall/SteinmanHall.jpg",
        "override_dims": "20.00x18.00x7.50",
        "venue_key": "steinman_hall",
    },
]

# 8 個場地的真實 IR 檔（與 t17_rt60_table.py VENUES 的 real_irs 逐字相同，僅節錄本卡需要的 8 個）
REAL_IRS = {
    "cathedral_room_shasta_lake_caverns": [
        "cathedral_room_shasta_lake_caverns/CathedralRoom.wav",
    ],
    "divorce_beach": ["divorce_beach/DivorceBeach.wav"],
    "mit_department_store": [
        "mit_department_store/h160_DepartmentStore_1txts.wav",
    ],
    "mit_gym": [
        "mit_gym/h026_Gym_8txts.wav",
        "mit_gym/h052_Gym_WeightRoom_3txts.wav",
        "mit_gym/h120_Gym_WeightRoom_1txts.wav",
    ],
    "mit_restaurant": [
        "mit_restaurant/h093_Restaurant_2txts.wav",
        "mit_restaurant/h114_Restaurant_txts.wav",
        "mit_restaurant/h130_Restaurant_1txs.wav",
        "mit_restaurant/h164_Restaurant_1txts.wav",
    ],
    "racquetball_court_4": ["racquetball_court_4/RacquetballCourt4.wav"],
    "steinman_hall": ["steinman_hall/SteinmanHall.wav"],
    "tunnel_to_hell": ["tunnel_to_hell/TunnelToHell.wav"],
}

VENUE_LABELS = {
    "cathedral_room_shasta_lake_caverns": "Cathedral Room, Shasta Lake Caverns（石灰岩洞窟）",
    "divorce_beach": "Divorce Beach（戶外沙灘岩礁）",
    "mit_department_store": "Department Store（MIT，百貨賣場）",
    "mit_gym": "Gym（MIT，健身房／重訓室）",
    "mit_restaurant": "Restaurant（MIT，餐廳用餐區）",
    "racquetball_court_4": "Racquetball Court 4（壁球場，必測反例）",
    "steinman_hall": "Steinman Hall（音樂廳）",
    "tunnel_to_hell": "Tunnel to Hell（要塞地下混凝土隧道）",
}


def run_cli(photo: Path, run_name: str, furn_tag: str, override_dims: str | None, fresh: bool) -> dict:
    """跑一次 CLI，把 output/<stem>/ 搬到 runs/<run_name>__<furn_tag>/，回傳 analysis.json。"""
    dst = RUNS_DIR / f"{run_name}__{furn_tag}"
    if dst.exists() and not fresh:
        aj = dst / "analysis.json"
        if aj.exists():
            print(f"  ⏭️  快取命中：{dst.relative_to(REPO_ROOT)}")
            return {
                "exit_code": 0,
                "analysis": json.loads(aj.read_text(encoding="utf-8")),
                "out_dir": str(dst.relative_to(REPO_ROOT)),
            }

    cmd = [sys.executable, "-m", "src.image_reverb", str(photo), "--force-low-confidence", "--no-viz"]
    if override_dims:
        cmd += ["--override-dims", override_dims]
    if furn_tag == "no_furn":
        cmd.append("--no-furnishings")

    t0 = time.time()
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - t0

    stem = photo.stem
    src_out = REPO_ROOT / "output" / stem
    if proc.returncode != 0 or not src_out.exists():
        raise RuntimeError(
            f"{run_name} ({furn_tag}) 失敗：exit={proc.returncode}\n"
            f"cmd={' '.join(cmd)}\n"
            f"--- stdout（末 40 行）---\n" + "\n".join(proc.stdout.splitlines()[-40:]) + "\n"
            f"--- stderr（末 40 行）---\n" + "\n".join(proc.stderr.splitlines()[-40:])
        )

    if dst.exists():
        shutil.rmtree(dst)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_out), str(dst))
    aj = json.loads((dst / "analysis.json").read_text(encoding="utf-8"))
    print(f"  ✅ {run_name} ({furn_tag}) {elapsed:.1f}s → {dst.relative_to(REPO_ROOT)}")
    return {"exit_code": 0, "analysis": aj, "out_dir": str(dst.relative_to(REPO_ROOT))}


def measure_real_side(venue_key: str) -> dict:
    """自行量測真實 IR（不讀 output/mvp_acceptance/ 的任何快取），回傳 real_reference 結構。"""
    files = [measure_file_real(REF_ROOT / rel) for rel in REAL_IRS[venue_key]]
    return {
        "bands": {str(f): t17.real_reference([m["bands"] for m in files], str(f)) for f in BANDS},
        "low_combined": t17.real_reference(files, "low_combined"),
        "n_files": len(files),
    }


def measure_file_real(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"找不到真實 IR：{path}")
    return t17.measure_file(path)


DECAY_THRESHOLDS_DB = (-20, -30, -40, -45)


def audible_decay_times(path: Path) -> dict:
    """§6.1 使用者試聽查核方法：20ms 非重疊窗逐窗 RMS 包絡線，門檻相對整段訊號的
    絕對值峰值（取樣，非包絡線峰值）取樣，對每個門檻取「最後一個超過門檻之窗」的
    起始時間。輸入必須是卷積後的試聽檔，不是 ir_mono.wav。"""
    x, sr = sf.read(str(path))
    x = x.mean(axis=1) if x.ndim > 1 else x
    w = int(0.020 * sr)
    n = len(x) // w
    env = np.array([np.sqrt(np.mean(x[i * w:(i + 1) * w] ** 2)) for i in range(n)])
    ref = np.abs(x).max()
    return {
        str(th): float(np.where(env > ref * 10 ** (th / 20))[0][-1] * w / sr)
        for th in DECAY_THRESHOLDS_DB
    }


def main() -> int:
    fresh = "--fresh" in sys.argv
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    data: dict = {"generated_at_note": "見 git log；本檔不含時間戳（Workflow 腳本規則）"}

    # ---------------- 步驟 1：13 張照片基準率複測（gate baseline） ----------------
    print("=== 步驟 1：13 張照片基準率複測（predetermined geometry，--force-low-confidence） ===")
    gate_rows = []
    mismatches = []
    for item in GATE_ITEMS:
        name = item["name"]
        photo = REPO_ROOT / item["photo"]
        print(f"[{name}]")
        r_furn = run_cli(photo, name, "with_furn", None, fresh)
        r_nofurn = run_cli(photo, name, "no_furn", None, fresh)

        a_furn = r_furn["analysis"]
        a_nofurn = r_nofurn["analysis"]
        geo = a_furn["geometry_confidence"]
        mat = a_furn["materials_confidence"]
        expected = EXPECTED_GATE[name]
        if (geo, mat) != expected:
            mismatches.append(
                f"{name}: 實測 (geometry={geo}, materials={mat}) != 基準 {expected}"
            )
        # 鐵則 6 交叉檢查：furnishings 不得影響 gate 兩軸
        if (a_nofurn["geometry_confidence"], a_nofurn["materials_confidence"]) != (geo, mat):
            mismatches.append(
                f"{name}: --no-furnishings 版本 confidence 軸與預設版不同"
                f"（with_furn=({geo},{mat})，no_furn=({a_nofurn['geometry_confidence']},"
                f"{a_nofurn['materials_confidence']})）——furnishings 疑似影響了 gate！"
            )

        furn = a_furn.get("furnishings")
        rt60_min = min(a_furn["rt60_bands_target_sabine"]) if furn else None
        gate_rows.append(
            {
                "name": name,
                "geometry_confidence": geo,
                "materials_confidence": mat,
                "overall_confidence": a_furn["confidence"],
                "expected": list(expected),
                "match_expected": (geo, mat) == expected,
                "furnishings_categories": (
                    {
                        k: {"ratio": v["ratio"], "A_by_band_1khz": v["A_by_band"][BANDS.index(1000)]}
                        for k, v in furn["categories"].items()
                    }
                    if furn
                    else {}
                ),
                "total_ratio": furn["total_ratio"] if furn else 0.0,
                "cap_applied": furn["cap_applied"] if furn else False,
                "proportion_of_absorption_1khz": furn["proportion_of_absorption_1khz"] if furn else 0.0,
                "rt60_bands_with_furn": a_furn["rt60_bands_target_sabine"],
                "rt60_bands_no_furn": a_nofurn["rt60_bands_target_sabine"],
                "rt60_min_with_furn": rt60_min,
                "rt60_below_0_1s": bool(rt60_min is not None and rt60_min < 0.1),
            }
        )

    if mismatches:
        print("\n🔴 gate 基準率與裁決 T-28-A 複驗不符，立即停：", file=sys.stderr)
        for m in mismatches:
            print(f"  - {m}", file=sys.stderr)
        return 1

    print("✅ 13 張照片的三軸 confidence 與裁決 T-28-A 複驗基準完全相同（含 --no-furnishings 交叉檢查）。")
    data["gate_baseline"] = gate_rows

    # ---------------- 步驟 2：8 對照場地（自動） + 5 手動 run，兩組 ----------------
    print("\n=== 步驟 2：8 對照場地（自動幾何）+ 5 F-09 手動 run，各兩組（預設陳設 vs --no-furnishings） ===")

    gate_by_name = {g["name"]: g for g in GATE_ITEMS}
    auto_results = []
    for venue_key in AUTO_VENUE_ORDER:
        item = next(g for g in GATE_ITEMS if g["venue_key"] == venue_key)
        name = item["name"]
        real_ref = measure_real_side(venue_key)
        for tag in ("with_furn", "no_furn"):
            run_dir = RUNS_DIR / f"{name}__{tag}"
            ir_path = run_dir / "ir_mono.wav"
            m = t17.measure_file(ir_path)
            errors = {
                str(f): t17.error_vs_reference(m["bands"][str(f)], real_ref["bands"][str(f)]) for f in BANDS
            }
            errors["low_combined"] = t17.error_vs_reference(m["low_combined"], real_ref["low_combined"])
            passed = sum(
                1
                for k in ("500", "1000", "2000", "4000", "low_combined")
                if errors[k].get("within_tolerance")
            )
            auto_results.append(
                {
                    "venue_key": venue_key,
                    "label": VENUE_LABELS[venue_key],
                    "run": name,
                    "furn_tag": tag,
                    "measured": {"bands": m["bands"], "low_combined": m["low_combined"]},
                    "real_reference": real_ref,
                    "errors": errors,
                    "passed_of_5": passed,
                    "all_pass": passed == 5,
                    "ladder_500_vs_low": t17.ratio(m["bands"]["500"], m["low_combined"]),
                }
            )
            print(f"  {name:34s} [{tag}] 通過 {passed}/5")

    manual_results = []
    for item in MANUAL_ITEMS:
        name = item["name"]
        photo = REPO_ROOT / item["photo"]
        print(f"[{name}]")
        run_cli(photo, name, "with_furn", item["override_dims"], fresh)
        run_cli(photo, name, "no_furn", item["override_dims"], fresh)
        real_ref = measure_real_side(item["venue_key"])
        for tag in ("with_furn", "no_furn"):
            run_dir = RUNS_DIR / f"{name}__{tag}"
            ir_path = run_dir / "ir_mono.wav"
            aj = json.loads((run_dir / "analysis.json").read_text(encoding="utf-8"))
            m = t17.measure_file(ir_path)
            errors = {
                str(f): t17.error_vs_reference(m["bands"][str(f)], real_ref["bands"][str(f)]) for f in BANDS
            }
            errors["low_combined"] = t17.error_vs_reference(m["low_combined"], real_ref["low_combined"])
            passed = sum(
                1
                for k in ("500", "1000", "2000", "4000", "low_combined")
                if errors[k].get("within_tolerance")
            )
            manual_results.append(
                {
                    "venue_key": item["venue_key"],
                    "label": VENUE_LABELS[item["venue_key"]],
                    "run": name,
                    "furn_tag": tag,
                    "override_dims": item["override_dims"],
                    "geometry_confidence": aj["geometry_confidence"],
                    "materials_confidence": aj["materials_confidence"],
                    "measured": {"bands": m["bands"], "low_combined": m["low_combined"]},
                    "real_reference": real_ref,
                    "errors": errors,
                    "passed_of_5": passed,
                    "all_pass": passed == 5,
                    "ladder_500_vs_low": t17.ratio(m["bands"]["500"], m["low_combined"]),
                }
            )
            print(f"  {name:34s} [{tag}] 通過 {passed}/5")

    data["auto_group"] = auto_results
    data["manual_group"] = manual_results

    # ---------------- 步驟 3：臥室 vs 浴室 分離表 ----------------
    bedroom = next(g for g in gate_rows if g["name"] == "bedroom_ai_generated")
    bathroom = next(g for g in gate_rows if g["name"] == "bathroom_tiled")
    data["bedroom_vs_bathroom"] = {"bedroom": bedroom, "bathroom": bathroom}

    # ---------------- 步驟 4：試聽檔（臥室 with/without furnishings） ----------------
    print("\n=== 步驟 4：臥室試聽檔（with/without furnishings） ===")
    for tag, out_name in (
        ("with_furn", "listen_bedroom_with_furnishings.wav"),
        ("no_furn", "listen_bedroom_without_furnishings.wav"),
    ):
        ir_path = RUNS_DIR / f"bedroom_ai_generated__{tag}" / "ir_mono.wav"
        out_path = OUT_DIR / out_name
        subprocess.run(
            [sys.executable, str(CONVOLVE), str(DRY), str(ir_path), str(out_path), "--mix", "0.6"],
            cwd=REPO_ROOT,
            check=True,
        )
        print(f"  🎧 {out_path.relative_to(REPO_ROOT)}")

    # ---------------- 步驟 4b：可聽門檻衰減時間（§6.1 試聽查核，補程式來源） ----------------
    print("\n=== 步驟 4b：可聽門檻衰減時間（20ms 窗、相對峰值取樣） ===")
    audible_decay = {}
    for tag, out_name in (
        ("with_furn", "listen_bedroom_with_furnishings.wav"),
        ("no_furn", "listen_bedroom_without_furnishings.wav"),
    ):
        times = audible_decay_times(OUT_DIR / out_name)
        audible_decay[tag] = times
        print(f"  {out_name}: {times}")
    data["audible_decay_bedroom"] = audible_decay

    # ---------------- 寫檔 ----------------
    (OUT_DIR / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已寫入 {(OUT_DIR / 'data.json').relative_to(REPO_ROOT)}")

    write_tables_md(data)
    print(f"已寫入 {(OUT_DIR / 'tables.md').relative_to(REPO_ROOT)}")
    return 0


def write_tables_md(data: dict) -> None:
    lines = []
    lines.append("# T-33 材質輪基準率複測 — 程式產生表格\n")
    lines.append("本檔全部數字由 `scripts/t33_material_round_tables.py` 產生，無一手打（地雷 #15）。\n")

    lines.append("## 表 1　13 張照片 gate 基準率複測（三軸 confidence 對照裁決 T-28-A）\n")
    lines.append("| 照片 | geometry | materials | overall | 與基準相符 | 陳設類別 | total_ratio | cap_applied | RT60 最小頻段跌破 0.1s？ |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for g in data["gate_baseline"]:
        cats = "、".join(
            f"{k} {v['ratio']*100:.1f}%" for k, v in g["furnishings_categories"].items()
        ) or "（無）"
        lines.append(
            f"| `{g['name']}` | {g['geometry_confidence']} | {g['materials_confidence']} | "
            f"{g['overall_confidence']} | {'✅' if g['match_expected'] else '🔴'} | {cats} | "
            f"{g['total_ratio']*100:.1f}% | {'是' if g['cap_applied'] else '否'} | "
            f"{'⚠️ 是' if g['rt60_below_0_1s'] else '否'} |"
        )

    for group_key, group_title in (("auto_group", "自動幾何（8 場地）"), ("manual_group", "手動尺寸 F-09（5 場地）")):
        lines.append(f"\n## 表　達標率 — {group_title}\n")
        lines.append("| 場地 | run | 陳設 | 500Hz | 1kHz | 2kHz | 4kHz | 聯合帶 | 通過數 | 全達標 |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in data[group_key]:
            e = r["errors"]

            def cell(k):
                v = e[k]
                if v.get("error_pct") is None:
                    return "—"
                mark = "✅" if v["within_tolerance"] else ("🟡" if v.get("within_range") else "❌")
                return f"{mark} {v['error_pct']:+.0f}%"

            furn_label = "預設（含陳設）" if r["furn_tag"] == "with_furn" else "`--no-furnishings`"
            lines.append(
                f"| {r['label']} | `{r['run']}` | {furn_label} | {cell('500')} | {cell('1000')} | "
                f"{cell('2000')} | {cell('4000')} | {cell('low_combined')} | "
                f"{r['passed_of_5']}/5 | {'✅' if r['all_pass'] else '❌'} |"
            )
        n_runs = len(data[group_key])
        total_passed = sum(r["passed_of_5"] for r in data[group_key])
        all_pass_venues = sum(1 for r in data[group_key] if r["all_pass"])
        lines.append(
            f"\n**小計（{group_title}，含兩組陳設設定合計）**：{total_passed}/{n_runs*5}"
            f"（{total_passed/(n_runs*5)*100:.0f}%）；全達標 run 數 {all_pass_venues}/{n_runs}"
        )
        # 分開列預設 vs no-furnishings 兩組小計，裁決 C 精神延伸（本卡是陳設 A/B，不是 dims_source 分組）
        for tag, tag_label in (("with_furn", "預設（含陳設）"), ("no_furn", "`--no-furnishings`")):
            rows = [r for r in data[group_key] if r["furn_tag"] == tag]
            p = sum(r["passed_of_5"] for r in rows)
            n = len(rows)
            ap = sum(1 for r in rows if r["all_pass"])
            lines.append(f"  - {tag_label}：{p}/{n*5}（{p/(n*5)*100:.0f}%）；全達標 {ap}/{n}")

    lines.append("\n## 表　臥室 vs 浴室 分離表（裁決 T-28-A 不可能性證明的區辨訊號）\n")
    lines.append("| | 臥室 `bedroom_ai_generated` | 浴室 `bathroom_tiled` |")
    lines.append("|---|---|---|")
    bd = data["bedroom_vs_bathroom"]["bedroom"]
    bt = data["bedroom_vs_bathroom"]["bathroom"]
    lines.append(f"| geometry | {bd['geometry_confidence']} | {bt['geometry_confidence']} |")
    lines.append(f"| materials | {bd['materials_confidence']} | {bt['materials_confidence']} |")
    bd_cats = "、".join(f"{k} {v['ratio']*100:.1f}%" for k, v in bd["furnishings_categories"].items()) or "（無）"
    bt_cats = "、".join(f"{k} {v['ratio']*100:.1f}%" for k, v in bt["furnishings_categories"].items()) or "（無）"
    lines.append(f"| 陳設類別＋佔比 | {bd_cats} | {bt_cats} |")
    lines.append(f"| total_ratio | {bd['total_ratio']*100:.1f}% | {bt['total_ratio']*100:.1f}% |")
    lines.append(
        f"| 佔 1kHz 總吸音比例 | {bd['proportion_of_absorption_1khz']*100:.1f}% | "
        f"{bt['proportion_of_absorption_1khz']*100:.1f}% |"
    )
    lines.append(
        f"| rt60_bands_target_sabine（含陳設） | {bd['rt60_bands_with_furn']} | {bt['rt60_bands_with_furn']} |"
    )
    lines.append(
        f"| rt60_bands_target_sabine（`--no-furnishings`） | {bd['rt60_bands_no_furn']} | "
        f"{bt['rt60_bands_no_furn']} |"
    )

    lines.append("\n## 表　臥室試聽檔可聽門檻衰減時間（§6.1 使用者試聽查核）\n")
    lines.append(
        "計算方法：20ms 非重疊窗逐窗 RMS 包絡線；門檻相對整段訊號的絕對值峰值"
        "（取樣，非包絡線峰值）；對每個門檻取「最後一個超過門檻之窗」的**起始時間**。"
        "輸入是卷積後的試聽檔（`assets/dry/clap_synth.wav` mix=0.6），不是 `ir_mono.wav`。\n"
    )
    lines.append("| 門檻 | 有陳設 (`listen_bedroom_with_furnishings.wav`) | 無陳設 (`listen_bedroom_without_furnishings.wav`) | 差距 |")
    lines.append("|---|---|---|---|")
    ad = data["audible_decay_bedroom"]
    for th in DECAY_THRESHOLDS_DB:
        w_t = ad["with_furn"][str(th)]
        nf_t = ad["no_furn"][str(th)]
        lines.append(f"| −{abs(th)}dB | {w_t:.2f}s | {nf_t:.2f}s | {nf_t - w_t:.2f}s |")

    (OUT_DIR / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
