"""T-14：IR 合成引擎 v1 —— image-source 早期反射 + 六頻段 shaped-noise 晚期殘響。

SPEC §5 路線 A+B 混合：
- 早期（路線 A）：pyroomacoustics ShoeBox image-source，**逐表面材質**（約束 A，
  per-wall `pra.Material`，整條路徑不存在跨面平均 α），取直達音後 ~90ms。
- 晚期（路線 B）：白噪音過八度頻段濾波器組（Butterworth），每頻段按 T-13 的目標
  RT60 做指數衰減（-60dB @ RT60），逐頻段與早期反射做能量匹配後 raised-cosine 交接。

**晚期目標值用哪一組**：`config.IR_RT60_BASIS`（預設 "sabine"，Fable 2026-08-27 定案，
理由見 TASKS.md T-14 卡——專案全部迴歸錨點都是 Sabine 值，且地雷 #14 實證 α 高時
實測 IR 比 Sabine 長，Eyring 更短只會把落差拉更大）。

**地雷 #14 的正面處理**：合成後用 `ir_metrics.py`（獨立實作，與本檔分離）對整條 IR
量測各頻段 T30，量測值與目標值並列寫進 JSON——對外宣稱的殘響時間以量測 T30 為準，
呼應 T-13 的 `rt60_disclaimer`。本檔只負責合成，量測邏輯一行都不在這裡。

聲源/麥克風位置沿用 `config.PREDELAY_SOURCE_POS_FRAC`/`_MIC_POS_FRAC`——與 T-13 算
predelay_ms 是同一組假設，合成 IR 的直達音時間才會與 JSON 裡的 predelay_ms 對得上。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pyroomacoustics as pra
import soundfile as sf
from scipy.signal import butter, sosfilt

from . import config
from .acoustics import AcousticsResult
from .materials import SURFACE_NAMES, SurfaceMaterials, get_material, load_materials
from . import ir_metrics


# ------------------------------------------------------------
# 早期反射（路線 A）：pyroomacoustics image-source，逐表面材質
# ------------------------------------------------------------


def build_pra_materials(
    surfaces: SurfaceMaterials, materials_data: dict[str, Any]
) -> dict[str, pra.Material]:
    """把 SurfaceMaterials 轉成 ShoeBox 的 per-wall dict，六面各自帶六頻段係數。

    與 `scripts/gen_ir_manual.py:build_surface_material_dict()` 邏輯相同（T-13 Opus
    建議 3 已記錄這類重複的分歧風險；等 T-15 整合時再收斂成單一實作）。
    整條路徑不存在任何跨面平均（約束 A 的 Opus 紅旗）。
    """
    band_freqs, alpha_table = surfaces.alpha_table(materials_data)
    materials = {}
    for name in SURFACE_NAMES:
        materials[name] = pra.Material(
            energy_absorption={
                "description": f"{name}: {getattr(surfaces, name)}",
                "coeffs": alpha_table[name],
                "center_freqs": list(band_freqs),
            },
            scattering=config.IR_SCATTERING,
        )
    return materials


def _source_mic_positions(
    length_m: float, width_m: float, height_m: float
) -> tuple[list[float], list[float]]:
    """聲源/麥克風位置：config 的固定比例（與 T-13 predelay 同一組假設）。"""
    sl, sw, sh = config.PREDELAY_SOURCE_POS_FRAC
    ml, mw, mh = config.PREDELAY_MIC_POS_FRAC
    source = [sl * length_m, sw * width_m, sh * height_m]
    mic = [ml * length_m, mw * width_m, mh * height_m]
    return source, mic


def _required_max_order(
    dims: list[float], covered_time_s: float, sound_speed: float
) -> int:
    """涵蓋 covered_time_s 內全部反射所需的 image-source 階數（有上限防爆炸）。"""
    travel_m = sound_speed * covered_time_s
    order = int(math.ceil(travel_m / min(dims))) + 1
    return min(order, config.IR_MAX_IMAGE_ORDER)


def simulate_early_ir(
    acoustics: AcousticsResult,
    surfaces: SurfaceMaterials,
    materials_data: dict[str, Any],
) -> tuple[np.ndarray, float]:
    """跑 image-source（不開 ray tracing——晚期由 shaped-noise 負責）。

    回傳 (原始 RIR, 直達音起點秒數)。直達音起點用幾何解析算
    （直達距離/音速 + pra 小數延遲濾波器的固定偏移），不用波形門檻偵測——
    實測 RIR 開頭有 air absorption 濾波造成的慢速漂移，門檻偵測會抓錯。
    """
    dims = [acoustics.length_m, acoustics.width_m, acoustics.height_m]
    source, mic = _source_mic_positions(*dims)

    physics = pra.Physics(
        temperature=config.AIR_TEMPERATURE_C, humidity=config.AIR_HUMIDITY_PCT
    )
    direct_s = math.dist(source, mic) / physics.get_sound_speed()
    max_order = _required_max_order(
        dims, direct_s + config.IR_EARLY_MS / 1000.0, physics.get_sound_speed()
    )

    room = pra.ShoeBox(
        dims,
        fs=config.IR_SAMPLE_RATE,
        materials=build_pra_materials(surfaces, materials_data),
        max_order=max_order,
        ray_tracing=False,
        air_absorption=True,
        temperature=config.AIR_TEMPERATURE_C,
        humidity=config.AIR_HUMIDITY_PCT,
    )

    # T-12 Opus 附註 2：SURFACE_NAMES 是 hardcode tuple，pra 升版改牆名會靜默失效。
    # 在真的把材質餵進去之後，對 room 內部實際牆名做一次 assert，讓失效變成大聲失敗。
    actual_wall_names = {wall.name for wall in room.walls}
    assert actual_wall_names == set(SURFACE_NAMES), (
        f"pyroomacoustics 的牆面名稱 {sorted(actual_wall_names)} 與 SURFACE_NAMES "
        f"{sorted(SURFACE_NAMES)} 不一致——pra 版本可能變了，per-wall 材質對應已失效"
    )

    room.add_source(source)
    room.add_microphone(mic)
    room.compute_rir()

    # pra 的 RIR 對齊：直達音落在「幾何傳播時間 + 小數延遲濾波器半長」處
    # （已實測驗證：4×3×2.5 房間幾何值 315.2 樣本 + 40 = 355，與波形一致）
    onset_s = direct_s + (pra.constants.get("frac_delay_length") // 2) / config.IR_SAMPLE_RATE
    return np.asarray(room.rir[0][0], dtype=np.float64), onset_s


# ------------------------------------------------------------
# 晚期殘響（路線 B）：六頻段 shaped-noise
# ------------------------------------------------------------


def synthesis_filterbank_sos(band_freqs: list[int], fs: int) -> list[np.ndarray]:
    """合成用濾波器組：中間頻段帶通，最低頻段補成低通、最高頻段補成高通。

    邊緣頻段外擴是為了讓六段加總後涵蓋整個頻譜（不留 <88Hz 與 >5.6kHz 的能量空洞），
    外擴區沿用相鄰頻段的 RT60——v1 的簡化，記錄於 TASKS.md 交接筆記。
    """
    nyq = fs / 2.0
    sos_list = []
    for i, freq in enumerate(band_freqs):
        lo = freq / math.sqrt(2.0)
        hi = min(freq * math.sqrt(2.0), nyq * 0.98)
        if i == 0:
            sos = butter(4, hi / nyq, btype="lowpass", output="sos")
        elif i == len(band_freqs) - 1:
            sos = butter(4, lo / nyq, btype="highpass", output="sos")
        else:
            sos = butter(3, [lo / nyq, hi / nyq], btype="bandpass", output="sos")
        sos_list.append(sos)
    return sos_list


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x**2))) if len(x) else 0.0


# ------------------------------------------------------------
# 主流程
# ------------------------------------------------------------


@dataclass
class IRSynthesisResult:
    """合成結果：IR 波形＋重現這條 IR 所需的全部參數（量測結果由 export 階段補）。"""

    ir: np.ndarray
    sample_rate: int
    band_center_freqs_hz: list[int]
    rt60_bands_target: list[float]
    rt60_basis: str
    early_ms: float
    crossfade_ms: float
    noise_seed: int
    onset_s: float  # 直達音實際起點（含 pra 小數延遲濾波器的固定偏移）
    acoustics: AcousticsResult
    warnings: list[str] = field(default_factory=list)


def _select_rt60_target(acoustics: AcousticsResult, basis: str) -> list[float]:
    if basis == "sabine":
        return list(acoustics.rt60_bands_sabine)
    if basis == "eyring":
        return list(acoustics.rt60_bands_eyring)
    raise ValueError(f"IR_RT60_BASIS 只能是 'sabine' 或 'eyring'，收到 '{basis}'")


def synthesize_ir(
    acoustics: AcousticsResult,
    materials_data: dict[str, Any] | None = None,
    seed: int | None = None,
) -> IRSynthesisResult:
    """主入口：T-13 的 `AcousticsResult` → 完整 IR（早期 image-source + 晚期 shaped-noise）。

    逐表面材質從 `acoustics.surfaces`（{面: 材質id}）重建——不收任何單一 α 參數
    （約束 A：那是退化成全域材質的入口）。
    """
    if materials_data is None:
        materials_data = load_materials()
    if seed is None:
        seed = config.IR_NOISE_SEED
    fs = config.IR_SAMPLE_RATE

    basis = config.IR_RT60_BASIS
    rt60_target = _select_rt60_target(acoustics, basis)
    band_freqs = list(acoustics.band_center_freqs_hz)

    warnings = list(acoustics.warnings)
    for freq, rt60 in zip(band_freqs, rt60_target):
        if not (config.RT60_PLAUSIBLE_MIN_S <= rt60 <= config.RT60_PLAUSIBLE_MAX_S):
            warnings.append(
                f"目標 RT60（{basis}）在 {freq} Hz 為 {rt60:.3f}s，超出合理區間 "
                f"{config.RT60_PLAUSIBLE_MIN_S}–{config.RT60_PLAUSIBLE_MAX_S}s"
                f"（WORKFLOW §5），輸入參數可疑"
            )

    # 逐表面材質重建（材質 id 先驗一遍，早失敗）
    surfaces = SurfaceMaterials(
        **{name: acoustics.surfaces[name] for name in SURFACE_NAMES}
    )
    surfaces.validate(materials_data)

    # --- 路線 A：早期反射 ---
    early_full, onset_s = simulate_early_ir(acoustics, surfaces, materials_data)
    if float(np.max(np.abs(early_full))) <= 0.0:
        raise ValueError("image-source 模擬輸出全零，早期反射合成失敗")
    onset_idx = int(round(onset_s * fs))

    n_early_end = onset_idx + int(round(fs * config.IR_EARLY_MS / 1000.0))
    n_xf = int(round(fs * config.IR_CROSSFADE_MS / 1000.0))
    n_match = int(round(fs * config.IR_ENERGY_MATCH_MS / 1000.0))
    n_fade_start = n_early_end - n_xf
    match_window = slice(n_fade_start - n_match, n_fade_start)

    max_rt60 = max(rt60_target)
    n_total = n_early_end + int(round(fs * max_rt60 * config.IR_TAIL_LENGTH_FACTOR))

    early = np.zeros(n_total)
    n_copy = min(len(early_full), n_early_end)
    early[:n_copy] = early_full[:n_copy]

    # --- 路線 B：六頻段 shaped-noise ---
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n_total)
    t = np.arange(n_total, dtype=np.float64) / fs
    t_ref = n_fade_start / fs  # 衰減包絡以 crossfade 起點為基準（env(t_ref)=1）

    sos_list = synthesis_filterbank_sos(band_freqs, fs)
    late = np.zeros(n_total)
    for i, (freq, rt60) in enumerate(zip(band_freqs, rt60_target)):
        band_noise = sosfilt(sos_list[i], noise)
        envelope = np.power(10.0, -3.0 * (t - t_ref) / rt60)
        shaped = band_noise * envelope

        # 逐頻段能量匹配：晚期在交接點的位準要接上早期在同視窗的位準（無能量跳變）
        early_band = sosfilt(sos_list[i], early)
        a_early = _rms(early_band[match_window])
        a_late = _rms(shaped[match_window])
        if a_early <= 0.0 or a_late <= 0.0:
            warnings.append(
                f"{freq} Hz 頻段在交接視窗能量為 0（early={a_early:.2e}, "
                f"late={a_late:.2e}），該頻段晚期殘響被略過"
            )
            continue
        late += (a_early / a_late) * shaped

    # --- 交接：raised-cosine crossfade（早期淡出、晚期淡入，同一窗互補）---
    fade_in = 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, n_xf)))
    early[n_fade_start:n_early_end] *= 1.0 - fade_in
    early[n_early_end:] = 0.0
    late[:n_fade_start] = 0.0
    late[n_fade_start:n_early_end] *= fade_in

    ir = early + late

    # 峰值正規化 -3dBFS（與 T-01 輸出規格一致）
    peak = float(np.max(np.abs(ir)))
    if peak <= 0.0:
        raise ValueError("合成 IR 全零，正規化失敗")
    ir *= 10.0 ** (config.IR_TARGET_PEAK_DBFS / 20.0) / peak

    return IRSynthesisResult(
        ir=ir,
        sample_rate=fs,
        band_center_freqs_hz=band_freqs,
        rt60_bands_target=rt60_target,
        rt60_basis=basis,
        early_ms=config.IR_EARLY_MS,
        crossfade_ms=config.IR_CROSSFADE_MS,
        noise_seed=seed,
        onset_s=onset_s,
        acoustics=acoustics,
        warnings=warnings,
    )


def export_ir(result: IRSynthesisResult, out_stem: str | Path) -> tuple[Path, Path]:
    """輸出 `<stem>.wav`（48kHz/24bit mono）與 `<stem>.json`（閉環驗證報告）。

    JSON 裡 `rt60_bands_target` 與 `t30_measured_s` 並列（地雷 #14 的正面處理）：
    量測由 `ir_metrics.py` 獨立執行，對外宣稱的殘響時間以量測 T30 為準。
    """
    out_stem = Path(out_stem)
    out_stem.parent.mkdir(parents=True, exist_ok=True)
    wav_path = out_stem.with_suffix(".wav")
    json_path = out_stem.with_suffix(".json")

    sf.write(wav_path, result.ir, result.sample_rate, subtype="PCM_24")

    report = ir_metrics.closed_loop_report(
        result.ir,
        result.sample_rate,
        result.band_center_freqs_hz,
        result.rt60_bands_target,
        tolerance=0.20,
        plausible_min_s=config.RT60_PLAUSIBLE_MIN_S,
        plausible_max_s=config.RT60_PLAUSIBLE_MAX_S,
    )

    acoustics_dict = result.acoustics.as_dict()
    payload = {
        "ir_file": wav_path.name,
        "sample_rate": result.sample_rate,
        "length_samples": int(len(result.ir)),
        "length_s": round(len(result.ir) / result.sample_rate, 3),
        "rt60_basis": result.rt60_basis,
        "early_ms": result.early_ms,
        "crossfade_ms": result.crossfade_ms,
        "noise_seed": result.noise_seed,
        "onset_s": round(result.onset_s, 5),
        "predelay_ms_from_acoustics": acoustics_dict["predelay_ms"],
        "dims": acoustics_dict["dims"],
        "dims_source": acoustics_dict["dims_source"],
        "surfaces": acoustics_dict["surfaces"],
        "confidence": acoustics_dict["confidence"],
        "closed_loop": report,
        "rt60_note": (
            "rt60_target 是公式值（T-13），t30_measured_s 是對合成 IR 的獨立量測；"
            "對外宣稱的殘響時間以量測值為準（地雷 #14）。"
        ),
        "warnings": list(result.warnings) + list(report["warnings"]),
    }
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return wav_path, json_path
