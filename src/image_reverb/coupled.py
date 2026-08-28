"""T-21：複合場景引擎 v1 —— 路徑串接近似（F-17）。

聲源與聽者在**不同空間**時的 IR：

    IR_總 = [ Σ各路徑 delay( gain · TL濾波( 聲源空間IR ⊗ 中繼空間IR(可選) ) ) ] ⊗ 聽者空間IR

例：巨蛋演唱會 → 通道走廊聽（敞開通道口＋混凝土牆兩條路徑）；
隔壁講話聲 → 我的房間（隔間牆／窗-戶外-窗／門-走廊-門三條路徑混合）。

**這是工程近似（遊戲音訊 portal 系統的做法），不是完整耦合房間模擬**：
忽略房間間的能量回饋、繞射細節與傳輸面的精確位置；路徑間相對音量由場景作者的
`gain_db` 設定。輸出 JSON 一律標 `method: "path_cascade_v1"` ＋近似聲明（SPEC §8）。

各空間 IR 由 T-14 引擎生成（逐表面材質、固定 seed 逐空間遞增——決定性保留、
且避免兩個空間共用同一段 noise 造成相關染色）。傳輸損失查 `data/transmission.json`
（六頻段 TL＋出處＋信心，比照 materials.json 規格）。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve, sosfilt

from . import config, ir_metrics, ir_synth
from .acoustics import AcousticsResult, compute_acoustics
from .geometry import RoomEstimate
from .materials import SurfaceMaterials, load_materials
from .scene_text import load_scene_presets

TRANSMISSION_PATH = config.PROJECT_ROOT / "data" / "transmission.json"

METHOD_ID = "path_cascade_v1"
METHOD_DISCLAIMER = (
    "路徑串接近似：各路徑＝聲源空間IR ⊗ 傳輸濾波（六頻段TL）⊗ 中繼空間IR(可選)，"
    "加總後 ⊗ 聽者空間IR。忽略耦合房間能量回饋、繞射細節與傳輸面精確位置；"
    "路徑間相對音量是場景設定值（gain_db），非物理推導。不是完整耦合房間模擬（SPEC §8）。"
)


def load_transmission(path: str | Path | None = None) -> dict[str, Any]:
    path = Path(path) if path is not None else TRANSMISSION_PATH
    if not path.exists():
        raise FileNotFoundError(f"找不到傳輸損失表：{path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"傳輸損失表 {path} 不是合法的 JSON（第 {e.lineno} 行：{e.msg}）。"
        ) from e
    for key in ("paths", "band_center_freqs_hz"):
        if key not in data:
            raise ValueError(f"傳輸損失表 {path} 缺少必要欄位 '{key}'。")
    return data


def get_transmission(path_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    if data is None:
        data = load_transmission()
    for entry in data["paths"]:
        if entry["id"] == path_type:
            return entry
    available = ", ".join(e["id"] for e in data["paths"])
    raise ValueError(f"傳輸損失表裡沒有路徑類型 '{path_type}'。可用：{available}")


def resolve_room(
    room_spec: dict[str, Any],
    presets_data: dict[str, Any],
    materials_data: dict[str, Any],
    label: str,
) -> tuple[RoomEstimate, SurfaceMaterials, str]:
    """場景 JSON 的空間定義 → (RoomEstimate, SurfaceMaterials, 顯示名稱)。

    兩種寫法：`{"preset": "corridor"}` 引用 T-20 的 preset，
    或 inline `{"dims_m": [長,寬,高], "surfaces": {六面材質}}`。
    """
    if not isinstance(room_spec, dict):
        raise ValueError(f"{label} 必須是物件（{{'preset': id}} 或 {{'dims_m':…, 'surfaces':…}}）")

    if "preset" in room_spec:
        pid = room_spec["preset"]
        preset = next((p for p in presets_data["presets"] if p["id"] == pid), None)
        if preset is None:
            available = ", ".join(p["id"] for p in presets_data["presets"])
            raise ValueError(f"{label} 引用了不存在的 preset '{pid}'。可用：{available}")
        dims = [float(v) for v in preset["dims_m"]]
        surfaces = SurfaceMaterials(**dict(preset["surfaces"]))
        for name in surfaces.as_dict():
            surfaces.sources[name] = f"scene_preset:{pid}"
        name = preset["name_zh"]
        confidence = preset["confidence"]
        notes = [f"{label}：preset '{pid}'（{name}）"]
    elif "dims_m" in room_spec and "surfaces" in room_spec:
        dims = [float(v) for v in room_spec["dims_m"]]
        surfaces = SurfaceMaterials(**dict(room_spec["surfaces"]))
        for sname in surfaces.as_dict():
            surfaces.sources[sname] = "scene_json"
        name = room_spec.get("name_zh", label)
        confidence = "medium"
        notes = [f"{label}：場景 JSON 內嵌尺寸/材質"]
    else:
        raise ValueError(
            f"{label} 要嘛給 {{'preset': id}}，要嘛給 {{'dims_m': [長,寬,高], 'surfaces': {{…}}}}"
        )

    if any(d <= 0 for d in dims):
        raise ValueError(f"{label} 的尺寸 {dims} 含零或負值")
    surfaces.validate(materials_data)
    estimate = RoomEstimate(
        length_m=dims[0], width_m=dims[1], height_m=dims[2],
        confidence=confidence, dims_source="scene_json", notes=notes,
    )
    return estimate, surfaces, name


def apply_transmission_filter(
    signal: np.ndarray,
    tl_db: list[float],
    band_freqs: list[int],
    fs: int,
    times: int = 1,
    eq_db: list[float] | None = None,
) -> np.ndarray:
    """六頻段濾波套 TL 衰減（`times`=穿過幾次，如窗-戶外-窗是玻璃 ×2）。

    `eq_db`：場景作者的**調音參數**（每頻段 dB，正=增益、負=衰減），疊加在 TL 之上。
    這是聽感 voicing 不是物理推導——TL 表是實驗室值，實際牆的面積/輻射效率/縫隙
    沒有建模，留這個誠實的旋鈕給場景作者對齊人耳（會完整寫進輸出 JSON，可追溯）。
    濾波器組沿用 T-14 引擎的（最低段低通/最高段高通，頻譜無空洞）。
    """
    sos_list = ir_synth.synthesis_filterbank_sos(band_freqs, fs)
    if eq_db is None:
        eq_db = [0.0] * len(band_freqs)
    out = np.zeros_like(signal)
    for sos, tl, eq in zip(sos_list, tl_db, eq_db):
        gain = 10.0 ** ((-(tl * times) + eq) / 20.0)
        out += gain * sosfilt(sos, signal)
    return out


@dataclass
class CoupledResult:
    ir: np.ndarray
    sample_rate: int
    scene_name: str
    band_center_freqs_hz: list[int]
    rooms_summary: list[dict[str, Any]]
    paths_summary: list[dict[str, Any]]
    warnings: list[str] = field(default_factory=list)


def synthesize_coupled(
    scene: dict[str, Any],
    presets_data: dict[str, Any] | None = None,
    materials_data: dict[str, Any] | None = None,
    transmission_data: dict[str, Any] | None = None,
    seed_base: int | None = None,
    normalize: bool = True,
) -> CoupledResult:
    """主入口：複合場景 JSON → 合成 IR。"""
    if presets_data is None:
        presets_data = load_scene_presets()
    if materials_data is None:
        materials_data = load_materials()
    if transmission_data is None:
        transmission_data = load_transmission()
    if seed_base is None:
        seed_base = config.IR_NOISE_SEED
    fs = config.IR_SAMPLE_RATE

    for key in ("source_room", "listener_room", "paths"):
        if key not in scene:
            raise ValueError(f"場景 JSON 缺少必要欄位 '{key}'")
    if not scene["paths"]:
        raise ValueError("場景 JSON 的 paths 不能是空清單（至少要一條傳輸路徑）")

    warnings: list[str] = []
    rooms_summary: list[dict[str, Any]] = []

    def build_room_ir(spec: dict[str, Any], label: str, seed: int) -> tuple[np.ndarray, AcousticsResult, str]:
        est, surf, name = resolve_room(spec, presets_data, materials_data, label)
        ac = compute_acoustics(est, surf, materials_data)
        result = ir_synth.synthesize_ir(ac, materials_data, seed=seed)
        warnings.extend(result.warnings)
        measured = ir_metrics.band_t30(result.ir, fs, ac.band_center_freqs_hz)
        rooms_summary.append({
            "role": label,
            "name": name,
            "dims_m": [est.length_m, est.width_m, est.height_m],
            "surfaces": surf.as_dict(),
            "rt60_bands_target_sabine": [round(v, 3) for v in ac.rt60_bands_sabine],
            "t30_measured_s": [round(float(v), 3) for v in measured],
            "noise_seed": seed,
        })
        return result.ir, ac, name

    src_ir, src_ac, src_name = build_room_ir(scene["source_room"], "聲源空間", seed_base + 1)
    lst_ir, lst_ac, lst_name = build_room_ir(scene["listener_room"], "聽者空間", seed_base)
    band_freqs = list(src_ac.band_center_freqs_hz)

    # --- 各路徑：聲源IR ⊗ 中繼IR(可選) → TL 濾波 → gain/delay ---
    paths_summary: list[dict[str, Any]] = []
    path_signals: list[np.ndarray] = []
    for i, p in enumerate(scene["paths"]):
        entry = get_transmission(p["type"], transmission_data)
        times = int(p.get("tl_times", 1))
        gain_db = float(p.get("gain_db", 0.0))
        delay_ms = float(p.get("extra_delay_ms", 0.0))
        if times < 1 or delay_ms < 0:
            raise ValueError(f"路徑 {i}（{p['type']}）的 tl_times/extra_delay_ms 不合法")
        eq_db = p.get("eq_db")
        if eq_db is not None:
            if len(eq_db) != len(entry["tl_db"]):
                raise ValueError(
                    f"路徑 {i}（{p['type']}）的 eq_db 要有 {len(entry['tl_db'])} 個頻段值，"
                    f"收到 {len(eq_db)} 個"
                )
            eq_db = [float(v) for v in eq_db]

        sig = src_ir
        via_name = None
        if p.get("via_room"):
            via_ir, _, via_name = build_room_ir(p["via_room"], f"路徑{i}中繼空間", seed_base + 2 + i)
            sig = fftconvolve(sig, via_ir)

        sig = apply_transmission_filter(sig, entry["tl_db"], band_freqs, fs, times=times, eq_db=eq_db)
        sig = sig * 10.0 ** (gain_db / 20.0)
        n_delay = int(round(delay_ms / 1000.0 * fs))
        if n_delay:
            sig = np.concatenate([np.zeros(n_delay), sig])
        path_signals.append(sig)
        paths_summary.append({
            "index": i,
            "type": entry["id"],
            "name_zh": entry.get("name_zh", entry["id"]),
            "note_zh": p.get("note_zh", ""),
            "tl_db_per_band": entry["tl_db"],
            "tl_times": times,
            "eq_db": eq_db,
            "gain_db": gain_db,
            "extra_delay_ms": delay_ms,
            "via_room": via_name,
            "tl_confidence": entry.get("confidence", "-"),
        })

    n_max = max(len(s) for s in path_signals)
    summed = np.zeros(n_max)
    for s in path_signals:
        summed[: len(s)] += s

    # 聽者空間對「全部到達聲」生效 → 加總後只卷積一次（線性系統，等價且省算）
    combined = fftconvolve(summed, lst_ir)

    if normalize:
        peak = float(np.max(np.abs(combined)))
        if peak <= 0.0:
            raise ValueError("複合場景 IR 全零，合成失敗")
        combined = combined * 10.0 ** (config.IR_TARGET_PEAK_DBFS / 20.0) / peak

    return CoupledResult(
        ir=combined,
        sample_rate=fs,
        scene_name=scene.get("name", "coupled_scene"),
        band_center_freqs_hz=band_freqs,
        rooms_summary=rooms_summary,
        paths_summary=paths_summary,
        warnings=warnings,
    )


def export_coupled(result: CoupledResult, out_stem: str | Path) -> tuple[Path, Path]:
    """輸出 `<stem>.wav` 與 `<stem>.json`（method 標記＋近似聲明＋全部參數可追溯）。"""
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    wav_path = out_stem.with_suffix(".wav")
    json_path = out_stem.with_suffix(".json")

    sf.write(wav_path, result.ir, result.sample_rate, subtype="PCM_24")

    measured = ir_metrics.band_t30(result.ir, result.sample_rate, result.band_center_freqs_hz)
    plaus_warnings = [
        f"{f} Hz 合成結果 T30 {float(m):.3f}s 超出合理區間 "
        f"{config.RT60_PLAUSIBLE_MIN_S}–{config.RT60_PLAUSIBLE_MAX_S}s（WORKFLOW §5）"
        for f, m in zip(result.band_center_freqs_hz, measured)
        if not (config.RT60_PLAUSIBLE_MIN_S <= float(m) <= config.RT60_PLAUSIBLE_MAX_S)
    ]

    payload = {
        "scene_name": result.scene_name,
        "method": METHOD_ID,
        "method_disclaimer": METHOD_DISCLAIMER,
        "ir_file": wav_path.name,
        "sample_rate": result.sample_rate,
        "length_s": round(len(result.ir) / result.sample_rate, 3),
        "band_center_freqs_hz": result.band_center_freqs_hz,
        "t30_measured_s": [round(float(v), 3) for v in measured],
        "rooms": result.rooms_summary,
        "paths": result.paths_summary,
        "warnings": list(dict.fromkeys(list(result.warnings) + plaus_warnings)),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return wav_path, json_path


def load_scene_file(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到場景檔：{path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"場景檔 {path} 不是合法的 JSON（第 {e.lineno} 行：{e.msg}）") from e
