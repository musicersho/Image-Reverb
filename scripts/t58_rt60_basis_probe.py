#!/usr/bin/env python3
"""T-58 調查卡：Sabine 目標 vs 幾何聲學（pra）參考 vs 產品合成路徑——只量不改。

**本卡不改任何程式、不下任何產品決定**（見 TASKS.md T-58 卡）。目的：把
Sabine／Eyring（公式）、pra ISM+ray tracing（幾何聲學參考）、`ir_synth`（產品路徑）
三者在同一批房間上的差距量清楚，供 R2 之後決定 `config.IR_RT60_BASIS` 的證據。

**唯讀輸入**（不重生、不重跑 CLI）：
- `output/material_r3/runs/{per_wall,control_gypsum,control_carpet}_seed100{1..10}.wav`
  （T-56 首跑的 30 條 IR，4×3×2.5m 三條件）
- `output/t17_manual_{gym,restaurant,department_store,racquetball,steinman}/
  {analysis.json,ir_mono.wav}`（T-17 手動組 5 場地，讀既有尺寸／材質／產品 IR）
- `output/mvp_acceptance/rt60_table.json`（讀 `real_reference`，不重量真實 IR）

**本卡新產出**（唯一允許的輸出路徑）：`output/rt60_basis_probe/{REPORT.md,tables.md,
runs/}`（`runs/` 底下另存 pra 參考房間新模擬的 IR＋Part A/B 的中間量測結果快取，
`DATASET_MANIFEST.json` 依 T-58 卡步驟 0 直接放在 `output/rt60_basis_probe/` 下）。

子指令：
    python scripts/t58_rt60_basis_probe.py manifest   # 步驟 0：只產 manifest
    python scripts/t58_rt60_basis_probe.py partA      # Part A：三條件 4×3×2.5m
    python scripts/t58_rt60_basis_probe.py partB      # Part B：T-17 手動組 5 場地
    python scripts/t58_rt60_basis_probe.py report     # 讀 partA/partB 快取產 REPORT/tables
    python scripts/t58_rt60_basis_probe.py all        # 依序跑完上面四步
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pyroomacoustics as pra
import soundfile as sf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.image_reverb import acoustics, ir_metrics, ir_synth  # noqa: E402
from src.image_reverb.geometry import RoomEstimate  # noqa: E402
from src.image_reverb.materials import (  # noqa: E402
    SURFACE_NAMES,
    SurfaceMaterials,
    load_materials,
)
from gen_ir_manual import PRESETS, build_room  # noqa: E402  （T-58-F1 R4：import 白名單新增 PRESETS，唯讀常數，供取 small preset 位置；build_material 未用到，見交接筆記）

OUTPUT_DIR = PROJECT_ROOT / "output" / "rt60_basis_probe"
RUNS_DIR = OUTPUT_DIR / "runs"
MANIFEST_PATH = OUTPUT_DIR / "DATASET_MANIFEST.json"
REPORT_PATH = OUTPUT_DIR / "REPORT.md"
TABLES_PATH = OUTPUT_DIR / "tables.md"
PART_A_CACHE = RUNS_DIR / "part_a_measurements.json"
PART_B_CACHE = RUNS_DIR / "part_b_measurements.json"

MATERIAL_R3_RUNS = PROJECT_ROOT / "output" / "material_r3" / "runs"
RT60_TABLE_PATH = PROJECT_ROOT / "output" / "mvp_acceptance" / "rt60_table.json"

BAND_FREQS = [125, 250, 500, 1000, 2000, 4000]
CRITERIA_BAND_FREQS = [500, 1000, 2000, 4000]  # 判準頻段（不含聯合帶，聯合帶另計）

# --- Part A：三條件，4×3×2.5m（與 T-56／T-48 同房間、同 preset）---
ROOM_DIMS_A = (4.0, 3.0, 2.5)
CONDITIONS_A: dict[str, dict[str, str]] = {
    "per_wall": {
        "floor": "carpet",
        "ceiling": "gypsum_board",
        "west": "gypsum_board",
        "east": "gypsum_board",
        "south": "gypsum_board",
        "north": "gypsum_board",
    },
    "control_gypsum": {name: "gypsum_board" for name in SURFACE_NAMES},
    "control_carpet": {name: "carpet" for name in SURFACE_NAMES},
}
SEEDS_A = list(range(1001, 1011))

# --- Part B：T-17 手動組 5 場地（venue key → output/t17_manual_<manual_key>/）---
VENUE_KEY_TO_MANUAL_KEY: dict[str, str] = {
    "mit_department_store": "department_store",
    "mit_gym": "gym",
    "mit_restaurant": "restaurant",
    "racquetball_court_4": "racquetball",
    "steinman_hall": "steinman",
}
MIT_VENUE_KEYS = {"mit_department_store", "mit_gym", "mit_restaurant"}
SEEDS_B = [1001, 1002, 1003, 1004, 1005]
IR_SCATTERING = 0.1


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_head() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT)
        .decode()
        .strip()
    )


def read_wav_mono(path: Path) -> tuple[np.ndarray, int]:
    data, fs = sf.read(path, dtype="float64", always_2d=False)
    if data.ndim > 1:
        data = data[:, 0]
    return np.asarray(data, dtype=np.float64), int(fs)


def measure_bands_and_combined(ir: np.ndarray, fs: int) -> tuple[list[float], float]:
    bands = [float(v) for v in ir_metrics.band_t30(ir, fs, BAND_FREQS)]
    combined = float(ir_metrics.t30_low_combined(ir, fs))
    return bands, combined


def median_over_runs(
    band_runs: list[list[float]], combined_runs: list[float]
) -> tuple[list[float], float]:
    arr = np.array(band_runs, dtype=np.float64)
    band_medians = [float(v) for v in np.median(arr, axis=0)]
    combined_median = float(np.median(np.array(combined_runs, dtype=np.float64)))
    return band_medians, combined_median


def combined_approx_from_bands(band_freqs: list[int], band_values: list[float]) -> float:
    """聯合帶（88.4–353.6Hz）沒有 Sabine/Eyring 公式對應，取 125/250Hz 兩帶平均近似
    （T-58 卡步驟 1 明文的近似規則，REPORT §2 會註明）。"""
    i125 = band_freqs.index(125)
    i250 = band_freqs.index(250)
    return (band_values[i125] + band_values[i250]) / 2.0


def normalize_peak(ir: np.ndarray, target_dbfs: float = -3.0) -> np.ndarray:
    peak = float(np.max(np.abs(ir)))
    if peak <= 0.0:
        raise ValueError("IR 全零，正規化失敗")
    return ir * (10.0 ** (target_dbfs / 20.0) / peak)


# ------------------------------------------------------------
# 步驟 0：manifest
# ------------------------------------------------------------


def build_manifest() -> dict[str, Any]:
    wav_entries = []
    for cond in CONDITIONS_A:
        for seed in SEEDS_A:
            p = MATERIAL_R3_RUNS / f"{cond}_seed{seed}.wav"
            wav_entries.append(
                {
                    "condition": cond,
                    "seed": seed,
                    "path": str(p.relative_to(PROJECT_ROOT)),
                    "sha256": sha256_file(p),
                }
            )

    t17_entries = []
    for venue_key in sorted(VENUE_KEY_TO_MANUAL_KEY):
        manual_key = VENUE_KEY_TO_MANUAL_KEY[venue_key]
        site_dir = PROJECT_ROOT / "output" / f"t17_manual_{manual_key}"
        analysis_p = site_dir / "analysis.json"
        ir_p = site_dir / "ir_mono.wav"
        t17_entries.append(
            {
                "venue_key": venue_key,
                "manual_key": manual_key,
                "analysis_json_path": str(analysis_p.relative_to(PROJECT_ROOT)),
                "analysis_json_sha256": sha256_file(analysis_p),
                "ir_mono_wav_path": str(ir_p.relative_to(PROJECT_ROOT)),
                "ir_mono_wav_sha256": sha256_file(ir_p),
            }
        )

    return {
        "task": "T-58",
        "git_head_at_manifest_time": git_head(),
        "material_r3_wav_count": len(wav_entries),
        "material_r3_wavs": wav_entries,
        "t17_manual_sites": t17_entries,
        "mvp_acceptance_rt60_table": {
            "path": str(RT60_TABLE_PATH.relative_to(PROJECT_ROOT)),
            "sha256": sha256_file(RT60_TABLE_PATH),
        },
    }


def cmd_manifest() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"已寫入 {MANIFEST_PATH}")
    print(f"sha256（填入 T-58 §8 dataset_manifest_sha256）：{sha256_file(MANIFEST_PATH)}")


# ------------------------------------------------------------
# Part A
# ------------------------------------------------------------


def run_part_a() -> dict[str, Any]:
    materials_data = load_materials()
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    for cond_name, surf_kwargs in CONDITIONS_A.items():
        surfaces = SurfaceMaterials(**surf_kwargs)
        surfaces.validate(materials_data)
        estimate = RoomEstimate(
            length_m=ROOM_DIMS_A[0],
            width_m=ROOM_DIMS_A[1],
            height_m=ROOM_DIMS_A[2],
            confidence="high",
            dims_source="manual",
        )
        ac = acoustics.compute_acoustics(estimate, surfaces, materials_data)
        band_freqs = list(ac.band_center_freqs_hz)
        sabine_bands = list(ac.rt60_bands_sabine)
        eyring_bands = list(ac.rt60_bands_eyring)
        sabine_combined = combined_approx_from_bands(band_freqs, sabine_bands)
        eyring_combined = combined_approx_from_bands(band_freqs, eyring_bands)

        band_runs, combined_runs = [], []
        for seed in SEEDS_A:
            wav_path = MATERIAL_R3_RUNS / f"{cond_name}_seed{seed}.wav"
            ir, fs = read_wav_mono(wav_path)
            bands, combined = measure_bands_and_combined(ir, fs)
            band_runs.append(bands)
            combined_runs.append(combined)
        pra_band_median, pra_combined_median = median_over_runs(band_runs, combined_runs)

        product = ir_synth.synthesize_ir(ac, materials_data)
        out_wav = RUNS_DIR / f"product_{cond_name}.wav"
        sf.write(out_wav, product.ir, product.sample_rate, subtype="PCM_24")
        product_ir, product_fs = read_wav_mono(out_wav)
        product_bands, product_combined = measure_bands_and_combined(product_ir, product_fs)

        results[cond_name] = {
            "band_freqs": band_freqs,
            "sabine_bands": sabine_bands,
            "eyring_bands": eyring_bands,
            "sabine_combined_approx": sabine_combined,
            "eyring_combined_approx": eyring_combined,
            "pra_band_median": pra_band_median,
            "pra_combined_median": pra_combined_median,
            "pra_band_runs": band_runs,
            "pra_combined_runs": combined_runs,
            "product_bands": product_bands,
            "product_combined": product_combined,
            "product_wav": str(out_wav.relative_to(PROJECT_ROOT)),
        }

    return results


def cmd_part_a() -> None:
    results = run_part_a()
    PART_A_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PART_A_CACHE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Part A 完成，已寫入快取 {PART_A_CACHE}")


# ------------------------------------------------------------
# Part B
# ------------------------------------------------------------


def run_part_b() -> dict[str, Any]:
    materials_data = load_materials()
    rt60_table = json.loads(RT60_TABLE_PATH.read_text(encoding="utf-8"))
    venues_by_key = {v["key"]: v for v in rt60_table["venues"]}
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}

    for venue_key, manual_key in VENUE_KEY_TO_MANUAL_KEY.items():
        site_dir = PROJECT_ROOT / "output" / f"t17_manual_{manual_key}"
        analysis = json.loads((site_dir / "analysis.json").read_text(encoding="utf-8"))
        dims = analysis["dims_m"]
        length_m, width_m, height_m = dims["length"], dims["width"], dims["height"]
        surfaces_dict = analysis["surfaces"]
        surfaces = SurfaceMaterials(**{name: surfaces_dict[name] for name in SURFACE_NAMES})
        surfaces.validate(materials_data)

        estimate = RoomEstimate(
            length_m=length_m,
            width_m=width_m,
            height_m=height_m,
            confidence="high",
            dims_source="manual",
        )
        ac = acoustics.compute_acoustics(estimate, surfaces, materials_data)
        band_freqs = list(ac.band_center_freqs_hz)

        # Sabine：直接沿用 analysis.json 既有記錄值（不重算，避免與生成當下的管線
        # 產生細微不一致）；Eyring：analysis.json 沒存，用同一組 dims/surfaces 重算。
        sabine_bands = [float(v) for v in analysis["rt60_bands_target_sabine"]]
        eyring_bands = list(ac.rt60_bands_eyring)
        sabine_combined = combined_approx_from_bands(band_freqs, sabine_bands)
        eyring_combined = combined_approx_from_bands(band_freqs, eyring_bands)

        max_dim = max(length_m, width_m, height_m)
        if max_dim <= 10.0:
            max_order, n_rays = 12, 20000
        else:
            max_order, n_rays = 4, 140000
        time_thres = max(2.0, 2.0 * max(sabine_bands))

        source, mic = ir_synth._source_mic_positions(length_m, width_m, height_m)
        material = ir_synth.build_pra_materials(surfaces, materials_data, scattering=IR_SCATTERING)
        preset = {
            "dimensions": [length_m, width_m, height_m],
            "scattering": IR_SCATTERING,
            "source_pos": source,
            "mic_pos": mic,
            "max_order": max_order,
            "n_rays": n_rays,
            "time_thres": time_thres,
        }

        band_runs, combined_runs = [], []
        for seed in SEEDS_B:
            pra.random.seed(seed)
            pra.libroom.set_rng_seed(seed)
            room = build_room(preset, material, time_thres)
            ir = np.asarray(room.rir[0][0], dtype=np.float64)
            ir = normalize_peak(ir)
            out_wav = RUNS_DIR / f"pra_{manual_key}_seed{seed}.wav"
            sf.write(out_wav, ir, acoustics.config.IR_SAMPLE_RATE, subtype="PCM_24")
            bands, combined = measure_bands_and_combined(ir, acoustics.config.IR_SAMPLE_RATE)
            band_runs.append(bands)
            combined_runs.append(combined)
        pra_band_median, pra_combined_median = median_over_runs(band_runs, combined_runs)

        product_ir, product_fs = read_wav_mono(site_dir / "ir_mono.wav")
        product_bands, product_combined = measure_bands_and_combined(product_ir, product_fs)

        real_ref = venues_by_key[venue_key]["real_reference"]
        real_bands = [float(real_ref["bands"][str(f)]["value"]) for f in band_freqs]
        real_combined = float(real_ref["low_combined"]["value"])

        results[venue_key] = {
            "manual_key": manual_key,
            "dims_m": [length_m, width_m, height_m],
            "band_freqs": band_freqs,
            "real_bands": real_bands,
            "real_combined": real_combined,
            "sabine_bands": sabine_bands,
            "sabine_combined_approx": sabine_combined,
            "eyring_bands": eyring_bands,
            "eyring_combined_approx": eyring_combined,
            "pra_band_median": pra_band_median,
            "pra_combined_median": pra_combined_median,
            "pra_band_runs": band_runs,
            "pra_combined_runs": combined_runs,
            "product_bands": product_bands,
            "product_combined": product_combined,
            "existing_closed_loop": analysis.get("closed_loop"),
            "preset": {"max_order": max_order, "n_rays": n_rays, "time_thres": time_thres},
        }

    return results


def cmd_part_b() -> None:
    results = run_part_b()
    PART_B_CACHE.parent.mkdir(parents=True, exist_ok=True)
    PART_B_CACHE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Part B 完成，已寫入快取 {PART_B_CACHE}")


# ------------------------------------------------------------
# 表格與 REPORT
# ------------------------------------------------------------


def _fmt(v: float) -> str:
    return f"{v:.4f}"


def _pct(v: float) -> str:
    return f"{v * 100.0:+.1f}%"


def build_table_a(part_a: dict[str, Any]) -> str:
    lines = [
        "## 表 A：Part A 三條件（4×3×2.5m）× 頻段 × {sabine, eyring, pra_median, product}",
        "",
        "| 條件 | 頻段 | sabine | eyring | pra_median(10次) | product | (sabine−pra)/pra | (eyring−pra)/pra | (product−sabine)/sabine |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for cond, r in part_a.items():
        band_freqs = r["band_freqs"]
        rows = list(zip(band_freqs, r["sabine_bands"], r["eyring_bands"], r["pra_band_median"], r["product_bands"]))
        rows.append(("聯合帶(88.4-353.6Hz，近似)", r["sabine_combined_approx"], r["eyring_combined_approx"], r["pra_combined_median"], r["product_combined"]))
        for freq, sabine, eyring, pra_med, product in rows:
            dev_sabine = (sabine - pra_med) / pra_med
            dev_eyring = (eyring - pra_med) / pra_med
            dev_product = (product - sabine) / sabine
            lines.append(
                f"| {cond} | {freq} | {_fmt(sabine)} | {_fmt(eyring)} | {_fmt(pra_med)} | {_fmt(product)} "
                f"| {_pct(dev_sabine)} | {_pct(dev_eyring)} | {_pct(dev_product)} |"
            )
    lines.append("")
    lines.append("### 表 A-1：Part A 10 次量測穩定度（pra 參考，聯合帶）")
    lines.append("")
    lines.append("| 條件 | 10 次值 (s) | median | min | max | (max−min)/median |")
    lines.append("|---|---|---|---|---|---|")
    for cond, r in part_a.items():
        vals = r["pra_combined_runs"]
        median = r["pra_combined_median"]
        vmin, vmax = min(vals), max(vals)
        spread = (vmax - vmin) / median if median else float("nan")
        vals_str = ", ".join(f"{v:.4f}" for v in vals)
        lines.append(f"| {cond} | {vals_str} | {_fmt(median)} | {_fmt(vmin)} | {_fmt(vmax)} | {spread*100:.1f}% |")
    lines.append("")
    return "\n".join(lines)


def build_table_b(part_b: dict[str, Any]) -> str:
    lines = [
        "## 表 B：Part B（T-17 手動組 5 場地）× 頻段 × {real, sabine, eyring, pra_median, product}＋誤差",
        "",
        "| 場地 | 頻段 | real | sabine | eyring | pra_median(5次) | product | (sabine−real)/real | (eyring−real)/real | (pra−real)/real | (product−real)/real |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for venue_key, r in part_b.items():
        band_freqs = r["band_freqs"]
        rows = list(
            zip(band_freqs, r["real_bands"], r["sabine_bands"], r["eyring_bands"], r["pra_band_median"], r["product_bands"])
        )
        rows.append(
            (
                "聯合帶(近似)",
                r["real_combined"],
                r["sabine_combined_approx"],
                r["eyring_combined_approx"],
                r["pra_combined_median"],
                r["product_combined"],
            )
        )
        for freq, real, sabine, eyring, pra_med, product in rows:
            e_sabine = (sabine - real) / real
            e_eyring = (eyring - real) / real
            e_pra = (pra_med - real) / real
            e_product = (product - real) / real
            lines.append(
                f"| {venue_key} | {freq} | {_fmt(real)} | {_fmt(sabine)} | {_fmt(eyring)} | {_fmt(pra_med)} | {_fmt(product)} "
                f"| {_pct(e_sabine)} | {_pct(e_eyring)} | {_pct(e_pra)} | {_pct(e_product)} |"
            )
    lines.append("")
    return "\n".join(lines)


def _criteria_abs_errors(part_b: dict[str, Any], basis: str, venue_keys: list[str]) -> list[float]:
    """判準頻段（500/1k/2k/4k＋聯合帶）誤差絕對值，跨指定場地攤平成一個 list。"""
    errs: list[float] = []
    for venue_key in venue_keys:
        r = part_b[venue_key]
        band_freqs = r["band_freqs"]
        if basis == "sabine":
            band_vals, combined_val = r["sabine_bands"], r["sabine_combined_approx"]
        elif basis == "eyring":
            band_vals, combined_val = r["eyring_bands"], r["eyring_combined_approx"]
        elif basis == "pra_median":
            band_vals, combined_val = r["pra_band_median"], r["pra_combined_median"]
        elif basis == "product":
            band_vals, combined_val = r["product_bands"], r["product_combined"]
        else:
            raise ValueError(basis)
        real_bands, real_combined = r["real_bands"], r["real_combined"]
        for freq in CRITERIA_BAND_FREQS:
            idx = band_freqs.index(freq)
            errs.append(abs((band_vals[idx] - real_bands[idx]) / real_bands[idx]))
        errs.append(abs((combined_val - real_combined) / real_combined))
    return errs


def build_table_c(part_b: dict[str, Any]) -> tuple[str, dict[str, float], dict[str, float]]:
    all_venues = list(part_b.keys())
    mit_venues = [k for k in all_venues if k in MIT_VENUE_KEYS]
    bases = ["sabine", "eyring", "pra_median", "product"]

    all_medians = {b: float(np.median(_criteria_abs_errors(part_b, b, all_venues))) for b in bases}
    mit_medians = {b: float(np.median(_criteria_abs_errors(part_b, b, mit_venues))) for b in bases}

    lines = [
        "## 表 C：判準頻段（500/1k/2k/4k＋聯合帶近似）誤差絕對值中位數，按基準彙總",
        "",
        "| 基準 | 5 場地中位數（n=25） | MIT 3 場地中位數（n=15，🟡 弱證據，樣本小） |",
        "|---|---|---|",
    ]
    for b in bases:
        lines.append(f"| {b} | {_fmt(all_medians[b])} | {_fmt(mit_medians[b])} |")
    lines.append("")
    return "\n".join(lines), all_medians, mit_medians


def evaluate_hypotheses(
    part_a: dict[str, Any], part_b: dict[str, Any], table_c_all: dict[str, float], table_c_mit: dict[str, float]
) -> tuple[str, dict[str, Any]]:
    lines = ["## §1 假設 H1～H4 逐條判定", ""]
    verdicts: dict[str, Any] = {}

    # H1
    dev = {}
    for cond, r in part_a.items():
        dev[cond] = (r["sabine_combined_approx"] - r["pra_combined_median"]) / r["pra_combined_median"]
    per_wall_dev = dev["per_wall"]
    uniform_devs = {c: dev[c] for c in ("control_gypsum", "control_carpet")}
    h1_positive = per_wall_dev > 0
    h1_smaller_uniform = all(abs(uniform_devs[c]) < abs(per_wall_dev) for c in uniform_devs)
    h1_support = h1_positive and h1_smaller_uniform
    lines.append(
        f"- **H1**：{'支持' if h1_support else '不支持'}——per-wall 偏差 {_pct(per_wall_dev)}"
        f"（{'為正' if h1_positive else '為負或零'}）；六面 gypsum 偏差 {_pct(uniform_devs['control_gypsum'])}、"
        f"六面 carpet 偏差 {_pct(uniform_devs['control_carpet'])}（絕對值"
        f"{'皆小於' if h1_smaller_uniform else '未皆小於'} per-wall 絕對值 {abs(per_wall_dev)*100:.1f}%）。"
    )
    verdicts["h1"] = {
        "support": h1_support,
        "dev": dev,
        "all_negative": all(v < 0 for v in dev.values()),
    }

    # H2
    eyring_dev_per_wall = (
        part_a["per_wall"]["eyring_combined_approx"] - part_a["per_wall"]["pra_combined_median"]
    ) / part_a["per_wall"]["pra_combined_median"]
    same_sign = (eyring_dev_per_wall > 0) == (per_wall_dev > 0) and abs(eyring_dev_per_wall) > 1e-6
    lines.append(
        f"- **H2**：{'支持' if same_sign else '不支持'}——per-wall 的 Eyring 相對 pra 偏差 "
        f"{_pct(eyring_dev_per_wall)}，與 Sabine 偏差 {_pct(per_wall_dev)} "
        f"{'同號（Eyring 未消除非均勻偏差）' if same_sign else '不同號或近零（Eyring 有消除偏差的跡象）'}。"
    )
    verdicts["h2"] = {"support": same_sign, "eyring_dev_per_wall": eyring_dev_per_wall}

    # H3（T-58-F1 R2：MIT 括號比較的是「與 5 場地判定是否同向」，不是「MIT 子集本身是否支持」；
    # H3 判定本身仍只由 5 場地 h3_all_support 決定）
    h3_all_support = table_c_all["pra_median"] < table_c_all["sabine"]
    h3_mit_support = table_c_mit["pra_median"] < table_c_mit["sabine"]
    h3_dir_consistent = h3_all_support == h3_mit_support
    lines.append(
        f"- **H3**：{'支持' if h3_all_support else '不支持'}——5 場地判準頻段誤差絕對值中位數："
        f"pra_median={_fmt(table_c_all['pra_median'])} vs sabine={_fmt(table_c_all['sabine'])}"
        f"（{'下降' if h3_all_support else '未下降'}）。MIT 3 場地子集（🟡 弱證據，樣本小）："
        f"pra_median={_fmt(table_c_mit['pra_median'])} vs sabine={_fmt(table_c_mit['sabine'])}"
        f"（{'下降' if h3_mit_support else '未下降'}；與 5 場地{'方向一致' if h3_dir_consistent else '方向不一致'}）。"
    )
    verdicts["h3"] = {
        "all_support": h3_all_support,
        "mit_support": h3_mit_support,
        "dir_consistent": h3_dir_consistent,
    }

    # H4（T-58-F1 R3：多數＝嚴格大於半數，對齊卡片條文；另加僅供參考的三條件合併計數）
    tol = 0.20
    h4_lines = []
    all_majority = True
    per_cond_counts: dict[str, dict[str, Any]] = {}
    for cond, r in part_a.items():
        band_freqs = r["band_freqs"]
        devs = [(prod - sab) / sab for prod, sab in zip(r["product_bands"], r["sabine_bands"])]
        within = [abs(d) <= tol for d in devs]
        majority = sum(within) > len(within) / 2
        all_majority = all_majority and majority
        idx_max = max(range(len(devs)), key=lambda i: abs(devs[i]))
        per_cond_counts[cond] = {
            "within": sum(within),
            "total": len(within),
            "max_dev_band": band_freqs[idx_max],
            "max_dev_pct": devs[idx_max],
        }
        h4_lines.append(f"{cond}：{sum(within)}/{len(within)} 頻段在 ±20% 內")
    merged_n = sum(v["within"] for v in per_cond_counts.values())
    merged_total = sum(v["total"] for v in per_cond_counts.values())
    if merged_n > merged_total / 2:
        merged_label = "＞半數"
    elif merged_n == merged_total / 2:
        merged_label = "＝半數"
    else:
        merged_label = "＜半數"

    # Part B 佐證（既有 closed_loop，本卡未重量）
    b_within_counts = []
    for venue_key, r in part_b.items():
        cl = r.get("existing_closed_loop")
        if cl:
            n_within = sum(1 for b in cl["bands"] if b["within_tolerance"])
            b_within_counts.append(f"{venue_key} {n_within}/{len(cl['bands'])}")
    lines.append(
        f"- **H4**：{'支持' if all_majority else '不支持'}——Part A 產品路徑 vs 自身 Sabine 目標，"
        f"多數頻段（＞半數；6 帶需 ≥4 帶）在 ±20% 內：{'；'.join(h4_lines)}。"
        f"三條件合併 {merged_n}/{merged_total}（{merged_label}；僅供參考，不是判定式）。"
        f"Part B 佐證（沿用 T-17 各場地既有 `analysis.json.closed_loop`；本卡**未**重量）："
        f"{'；'.join(b_within_counts) if b_within_counts else '無'}。"
    )
    verdicts["h4"] = {
        "support": all_majority,
        "per_cond_counts": per_cond_counts,
        "merged": (merged_n, merged_total, merged_label),
    }

    return "\n".join(lines) + "\n", verdicts


def _part_a_position_diff() -> dict[str, Any]:
    """T-58-F1 R4：Part A pra 參考（`gen_ir_manual.PRESETS["small"]`）與產品
    `ir_synth._source_mic_positions(*ROOM_DIMS_A)` 的座標差（cm，程式算，不手打）。"""
    preset_source = [float(v) for v in PRESETS["small"]["source_pos"]]
    preset_mic = [float(v) for v in PRESETS["small"]["mic_pos"]]
    raw_source, raw_mic = ir_synth._source_mic_positions(*ROOM_DIMS_A)
    product_source = [float(v) for v in raw_source]
    product_mic = [float(v) for v in raw_mic]

    axis_names = ["x", "y", "z"]
    diffs = [
        ("聲源", axis_names[i], abs(preset_source[i] - product_source[i]) * 100.0) for i in range(3)
    ] + [
        ("麥克風", axis_names[i], abs(preset_mic[i] - product_mic[i]) * 100.0) for i in range(3)
    ]
    max_point, max_axis, max_cm = max(diffs, key=lambda t: t[2])

    return {
        "preset_source": preset_source,
        "preset_mic": preset_mic,
        "product_source": product_source,
        "product_mic": product_mic,
        "max_diff_cm": max_cm,
        "max_diff_label": f"{max_point} {max_axis}",
    }


def _pra_credibility_lines(part_b: dict[str, Any]) -> tuple[list[str], str]:
    """T-58-F1 R5 §3(b)：Part B 每場地 pra 參考可信度逐行＋`max_order=4` 彙總句
    （程式從 part_b 逐場地算出，不手打）。"""
    per_venue: dict[str, dict[str, Any]] = {}
    for venue_key, r in part_b.items():
        band_freqs = r["band_freqs"]
        errs = []
        for freq in CRITERIA_BAND_FREQS:
            idx = band_freqs.index(freq)
            errs.append((r["pra_band_median"][idx] - r["real_bands"][idx]) / r["real_bands"][idx])
        errs.append((r["pra_combined_median"] - r["real_combined"]) / r["real_combined"])
        all_pos = all(e > 0 for e in errs)
        all_neg = all(e < 0 for e in errs)
        sign_label = "全為正" if all_pos else ("全為負" if all_neg else "有正有負")
        per_venue[venue_key] = {"preset": r["preset"], "errs": errs, "all_pos": all_pos, "sign_label": sign_label}

    lines = []
    for venue_key, info in per_venue.items():
        p = info["preset"]
        lines.append(
            f"  - {venue_key}：preset（max_order={p['max_order']}／n_rays={p['n_rays']}），"
            f"判準頻段 (pra−real)/real 範圍 {_pct(min(info['errs']))}～{_pct(max(info['errs']))}，{info['sign_label']}"
        )

    mo4 = {k: v for k, v in per_venue.items() if v["preset"]["max_order"] == 4}
    mo4_all_pos = {k: v for k, v in mo4.items() if v["all_pos"]}
    if mo4_all_pos:
        combined_errs = [e for v in mo4_all_pos.values() for e in v["errs"]]
        summary = (
            f"`max_order=4` 的場地共 {len(mo4)} 個，其中 {len(mo4_all_pos)} 個五格全為正，"
            f"範圍 {_pct(min(combined_errs))}～{_pct(max(combined_errs))}。"
        )
    else:
        summary = f"`max_order=4` 的場地共 {len(mo4)} 個，沒有場地五格全為正。"

    return lines, summary


def _build_section_3(
    part_b: dict[str, Any],
    table_c_all: dict[str, float],
    verdicts: dict[str, Any],
    pos_diff: dict[str, Any],
) -> str:
    """T-58-F1 R5：§3 全段重寫——只列選項與證據，不下決定；不對未成立的假設寫『若…成立』。"""
    lines = ["## §3 給 Fable 的決策輸入（只列選項與證據，不下決定）", ""]

    # (a) 基準比較
    sabine_v = table_c_all["sabine"]
    eyring_v = table_c_all["eyring"]
    pra_v = table_c_all["pra_median"]
    not_support_change = sabine_v <= eyring_v and sabine_v <= pra_v
    op_eyring = "≤" if sabine_v <= eyring_v else ">"
    op_pra = "≤" if sabine_v <= pra_v else ">"
    lines.append(
        f"- **(a) 基準比較**：5 場地判準頻段誤差絕對值中位數 sabine={_fmt(sabine_v)}、"
        f"eyring={_fmt(eyring_v)}、pra_median={_fmt(pra_v)}（MIT 子集見表 C）。"
        f"現有證據{'不支持' if not_support_change else '支持'}把 `IR_RT60_BASIS` 由 sabine 換成 "
        f"eyring 或 pra 量測值（sabine {op_eyring} eyring 且 sabine {op_pra} pra_median）。"
        "此為證據陳述，不是產品決定；決定歸 Fable，T-17-R2 之後。"
    )

    # (b) pra 參考本身的可信度
    venue_lines, mo4_summary = _pra_credibility_lines(part_b)
    lines.append("- **(b) pra 參考本身的可信度**（逐場地，程式產生）：")
    lines.extend(venue_lines)
    lines.append(f"  {mo4_summary}")

    # (c) H1／H2 的實際意涵
    if not verdicts["h1"]["support"] and verdicts["h1"]["all_negative"]:
        dev = verdicts["h1"]["dev"]
        text_c = (
            f"三條件 Sabine 相對 pra 的聯合帶偏差全為負（per_wall {_pct(dev['per_wall'])}、"
            f"control_gypsum {_pct(dev['control_gypsum'])}、control_carpet {_pct(dev['control_carpet'])}）——"
            "「Sabine 在非均勻房間相對幾何聲學參考偏長」未獲支持；H2 的「同號」只表示 Eyring 與 Sabine "
            "同向偏短，在 H1 前提不成立下不具原假設的含意。"
        )
    else:
        text_c = (
            f"本輪 H1：{'支持' if verdicts['h1']['support'] else '不支持'}、"
            f"H2：{'支持' if verdicts['h2']['support'] else '不支持'}，不符合上述已知分支，"
            "含意需另行檢視 §1 的逐值敘述，此處不重複展開。"
        )
    lines.append(f"- **(c) H1／H2 的實際意涵**：{text_c}")

    # (d) H4 的實際意涵
    if not verdicts["h4"]["support"]:
        cond_parts = []
        for cond, info in verdicts["h4"]["per_cond_counts"].items():
            cond_parts.append(
                f"{cond} {info['within']}/{info['total']}（最大偏差頻段 {info['max_dev_band']}Hz "
                f"{_pct(info['max_dev_pct'])}）"
            )
        b_parts = []
        for venue_key, r in part_b.items():
            cl = r.get("existing_closed_loop")
            if not cl:
                continue
            n_within = sum(1 for b in cl["bands"] if b["within_tolerance"])
            total = len(cl["bands"])
            exceed = [b for b in cl["bands"] if not b["within_tolerance"]]
            if exceed:
                detail = "、".join(f"{b['freq_hz']}Hz {b['error_pct']:+.1f}%" for b in exceed)
                b_parts.append(f"{venue_key} {n_within}/{total}（超差：{detail}）")
            else:
                b_parts.append(f"{venue_key} {n_within}/{total}")
        text_d = (
            f"逐條件：{'；'.join(cond_parts)}。Part B 既有 `closed_loop`：{'；'.join(b_parts)}。"
            "已知機制＝T-14 裁決／T-17 裁決 B 記錄的『陡峭頻段階梯下的鄰帶耦合』；"
            "control_carpet 是極端案例，且六面地毯是地雷 #9 明列的不現實模型；"
            "本卡**未**重新驗證機制歸因（保留號 T-59）。對決策的含意：『產品 T30≈Sabine 目標』"
            "不是無條件成立，產品對真實 IR 的誤差除了材質誤差與 Sabine 偏差，還可能含這一項。"
        )
    else:
        text_d = (
            "本輪 H4 支持，產品路徑忠實反映 Sabine 目標；對決策的含意：現有「T-17 生成側誤差為正」的"
            "觀察，病因更可能是「Sabine 對真實房間本身的偏差」而非「產品合成環節額外引入誤差」。"
        )
    lines.append(f"- **(d) H4 的實際意涵**：{text_d}")

    lines.append("")
    return "\n".join(lines)


def build_report(part_a: dict[str, Any], part_b: dict[str, Any]) -> str:
    table_c_md, table_c_all, table_c_mit = build_table_c(part_b)
    h_section, verdicts = evaluate_hypotheses(part_a, part_b, table_c_all, table_c_mit)
    pos_diff = _part_a_position_diff()

    sorted_bases = sorted(table_c_all.items(), key=lambda kv: kv[1])
    sorted_bases_str = "、".join(f"{name} {_fmt(val)}" for name, val in sorted_bases)
    result_sentence = (
        "**結果**：H1 " + ("支持" if verdicts["h1"]["support"] else "不支持")
        + "｜H2 " + ("支持" if verdicts["h2"]["support"] else "不支持")
        + "｜H3 " + ("支持" if verdicts["h3"]["all_support"] else "不支持")
        + "｜H4 " + ("支持" if verdicts["h4"]["support"] else "不支持")
        + f"；表 C 5 場地判準頻段誤差絕對值中位數四個基準由小到大：{sorted_bases_str}。"
    )

    section_3 = _build_section_3(part_b, table_c_all, verdicts, pos_diff)

    lines = [
        "# T-58 REPORT：Sabine vs Eyring vs 幾何聲學（pra）參考 vs 產品合成路徑",
        "",
        "## §0 摘要",
        "",
        "本卡只量不改、不下產品決定（歸 Fable，R2 之後）。Part A 在合成的 4×3×2.5m 三條件房間"
        "（沿用 T-56 首跑的 30 條 pra IR，未重生）比較 Sabine／Eyring 公式值與 pra 幾何聲學量測值、"
        "以及產品 `ir_synth` 合成 IR 的 T30；Part B 在 T-17 手動組 5 個真實場地上，額外加入真實 IR"
        "（`output/mvp_acceptance/rt60_table.json` 的 `real_reference`）當比較基準。事前登記的假設"
        "H1～H4 判定見 §1，數字全部引用下方表 A／B／C（表格程式產出，見 `tables.md`）。",
        "",
        result_sentence,
        "",
        h_section,
        "## §2 限制",
        "",
        "- 聯合帶（88.4–353.6Hz）沒有 Sabine/Eyring 公式對應，本卡取 125Hz／250Hz 兩帶公式值"
        "**平均**近似（不是量測 IR 的聯合帶濾波，只用於 Sabine/Eyring 欄；pra_median／product／real"
        "欄的聯合帶仍是 `ir_metrics.t30_low_combined()` 對整條 IR 的真實量測，兩種計算方式不可直接"
        "當同一件事比較細節，只看方向與量級）。",
        "- pra 的 image-source + ray tracing 本身是一個模型，不是真值；Part A 沿用 T-56 首跑（已鎖定，"
        "不可重跑），Part B 為本卡新模擬（seed 1001–1005，5 次取中位數），兩者都可能與更精細的聲學"
        "模型有落差。",
        "- MIT 三場地（`mit_gym`／`mit_restaurant`／`mit_department_store`）在 Part B 判準頻段比較中"
        "另外用區間中位數列出，樣本只有 3 場地、15 個誤差值，弱證據，標 🟡（沿用 T-17 慣例）。",
        "- Part B 手動尺寸與材質判定是 Opus 於 T-17 執行時的人工估計（見各 `t17_manual_*/analysis.json`"
        "`notes`／`warnings`），不是實測值。",
        "- Part B 的「產品」欄是 T-17 HEAD 時生成的既有 `ir_mono.wav`（未重生），與 Part A 的「產品」欄"
        "（本卡用當前 HEAD 的 `ir_synth.synthesize_ir()` 重新合成）不是同一次生成，兩者不可跨 Part 直接"
        "比較生成環境。",
        f"- **R4**：Part A 的 pra 參考（T-56 首跑、已鎖定不可重生）位置＝聲源 {pos_diff['preset_source']}／"
        f"麥克風 {pos_diff['preset_mic']}（`gen_ir_manual.PRESETS[\"small\"]`），與產品 "
        f"`ir_synth._source_mic_positions(4,3,2.5)`＝聲源 {[round(v, 2) for v in pos_diff['product_source']]}／"
        f"麥克風 {[round(v, 2) for v in pos_diff['product_mic']]} 不同（各軸最大差 {pos_diff['max_diff_cm']:.1f} cm，"
        f"{pos_diff['max_diff_label']}）；Part B 的 pra 房間用的就是 `_source_mic_positions`（一致）；"
        "本卡**未量化**此差異對 T30 的影響（T30 是晚期衰減斜率，預期影響小；但未驗證）。",
        "",
        section_3,
        "## §4 可重跑指令",
        "",
        "```bash",
        "source .venv/bin/activate",
        "python scripts/t58_rt60_basis_probe.py manifest",
        "python scripts/t58_rt60_basis_probe.py partA",
        "python scripts/t58_rt60_basis_probe.py partB",
        "python scripts/t58_rt60_basis_probe.py report",
        "```",
        "",
    ]
    return "\n".join(lines)


def cmd_report() -> None:
    part_a = json.loads(PART_A_CACHE.read_text(encoding="utf-8"))
    part_b = json.loads(PART_B_CACHE.read_text(encoding="utf-8"))

    table_a_md = build_table_a(part_a)
    table_b_md = build_table_b(part_b)
    table_c_md, _, _ = build_table_c(part_b)

    TABLES_PATH.write_text(table_a_md + "\n" + table_b_md + "\n" + table_c_md, encoding="utf-8")
    REPORT_PATH.write_text(build_report(part_a, part_b), encoding="utf-8")
    print(f"已寫入 {REPORT_PATH}")
    print(f"已寫入 {TABLES_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cmd", choices=["manifest", "partA", "partB", "report", "all"])
    args = parser.parse_args()

    if args.cmd == "manifest":
        cmd_manifest()
    elif args.cmd == "partA":
        cmd_part_a()
    elif args.cmd == "partB":
        cmd_part_b()
    elif args.cmd == "report":
        cmd_report()
    elif args.cmd == "all":
        cmd_manifest()
        cmd_part_a()
        cmd_part_b()
        cmd_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
