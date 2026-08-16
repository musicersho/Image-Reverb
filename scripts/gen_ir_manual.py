#!/usr/bin/env python3
"""T-01：用手動參數生成第一個 IR（SPEC §5 路線 A：幾何聲學模擬）。

用 pyroomacoustics 的 ShoeBox（長方體房間）模擬，
以 image-source method 算早期反射、ray tracing 補晚期殘響，
輸出 48kHz / 24bit mono WAV 到 output/ir_<name>.wav。

用法：
    python scripts/gen_ir_manual.py small
    python scripts/gen_ir_manual.py hall

T-03 新增：--material <id> 可從 data/materials.json 讀取分頻段吸音係數套到六個牆面，
    python scripts/gen_ir_manual.py small --material marble
    python scripts/gen_ir_manual.py --list-materials
不帶 --material 時，行為與 T-01 完全相同（用 preset 裡的單一 α、輸出同一個檔名）。
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pyroomacoustics as pra
import soundfile as sf

# 共用材質表讀取工具（同一個 scripts/ 目錄）
from show_materials import alpha_list, get_material, load_materials

# ============================================================
# 參數區塊 — 想調整 IR 就改這裡
# ============================================================

SAMPLE_RATE = 48000  # 取樣率 (Hz)
SUBTYPE = "PCM_24"  # WAV 位元深度：24bit
TARGET_PEAK_DBFS = -3.0  # 正規化的目標峰值 (dBFS)

# 空氣吸收（高頻隨距離衰減，大空間影響明顯）
AIR_ABSORPTION = True
TEMPERATURE = 20.0  # 室溫 (攝氏)
HUMIDITY = 50.0  # 相對濕度 (%)

# 每個 preset 的欄位說明：
#   dimensions      房間長×寬×高 (公尺)
#   absorption      各面統一的吸音係數 α（0=全反射硬牆，1=全吸收）
#   scattering      表面擴散係數（ray tracing 需要，值越大反射越散）
#   source_pos      聲源位置 (x, y, z)，單位公尺
#   mic_pos         麥克風位置 (x, y, z)，單位公尺
#   max_order       image-source 的最高反射階數（負責早期反射細節）
#   n_rays          ray tracing 發射的射線數（負責晚期殘響密度）
#   time_thres      ray tracing 追蹤的最長時間 (秒)，要 > 預期 RT60
#   output_name     輸出檔名 output/ir_<output_name>.wav
PRESETS = {
    # 一般房間：4×3×2.5m，吸音係數 0.3
    "small": {
        "dimensions": [4.0, 3.0, 2.5],
        "absorption": 0.3,
        "scattering": 0.1,
        "source_pos": [1.0, 1.0, 1.5],
        "mic_pos": [3.0, 2.0, 1.2],
        "max_order": 12,
        "n_rays": 20000,
        "time_thres": 2.0,
        "output_name": "room_small",
    },
    # 音樂廳：30×20×12m，吸音係數 0.08
    "hall": {
        "dimensions": [30.0, 20.0, 12.0],
        "absorption": 0.08,
        "scattering": 0.1,
        "source_pos": [8.0, 10.0, 2.0],
        "mic_pos": [22.0, 10.0, 1.5],
        "max_order": 4,
        "n_rays": 140000,
        "time_thres": 12.0,
        "output_name": "hall_large",
    },
}

# 專案路徑
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"

# ============================================================


def sabine_rt60(dimensions, absorption):
    """用 Sabine 公式算理論 RT60，當作模擬結果的對照參考值。"""
    lx, ly, lz = dimensions
    volume = lx * ly * lz
    surface = 2.0 * (lx * ly + lx * lz + ly * lz)
    return 0.161 * volume / (surface * absorption)


def build_material(preset, material_entry=None, band_freqs=None):
    """建立 pyroomacoustics 的 Material。

    material_entry 是 None（沒帶 --material）時，維持 T-01 的行為：
    用 preset 裡的單一 α，全頻段一致。
    有帶 --material 時，改用材質表的六頻段係數。
    """
    if material_entry is None:
        energy_absorption = preset["absorption"]
    else:
        energy_absorption = {
            "description": material_entry["name_en"],
            "coeffs": alpha_list(material_entry, band_freqs),
            "center_freqs": list(band_freqs),
        }

    return pra.Material(
        energy_absorption=energy_absorption,
        scattering=preset["scattering"],
    )


def build_room(preset, material, time_thres):
    """依 preset 建立 ShoeBox 房間，放好聲源與麥克風，跑模擬。"""
    room = pra.ShoeBox(
        preset["dimensions"],
        fs=SAMPLE_RATE,
        materials=material,
        max_order=preset["max_order"],
        # 這裡先不開 ray tracing，改由下面的 set_ray_tracing() 開啟並帶入我們自己的參數，
        # 避免建構時先用預設值自動推算射線數而印出無關的警告
        ray_tracing=False,
        air_absorption=AIR_ABSORPTION,
        temperature=TEMPERATURE,
        humidity=HUMIDITY,
    )
    # ray tracing 參數：射線數越多晚期殘響越平滑，time_thres 要涵蓋整段衰減
    room.set_ray_tracing(
        n_rays=preset["n_rays"],
        receiver_radius=0.5,
        energy_thres=1e-7,
        time_thres=time_thres,
    )

    room.add_source(preset["source_pos"])
    room.add_microphone(preset["mic_pos"])

    room.compute_rir()
    return room


def normalize_peak(signal, target_dbfs):
    """把訊號峰值正規化到指定 dBFS。"""
    peak = float(np.max(np.abs(signal)))
    if peak <= 0.0:
        raise ValueError("IR 全為零，模擬失敗（峰值 = 0）")
    target_linear = 10.0 ** (target_dbfs / 20.0)
    return signal * (target_linear / peak)


def main():
    parser = argparse.ArgumentParser(description="用手動參數生成 IR（pyroomacoustics ShoeBox）")
    parser.add_argument(
        "preset",
        nargs="?",
        choices=sorted(PRESETS.keys()),
        help="要生成的 preset：small（一般房間）或 hall（音樂廳）",
    )
    parser.add_argument(
        "--material",
        default=None,
        metavar="ID",
        help="從 data/materials.json 取材質，把該材質的六頻段吸音係數套到全部牆面"
        "（不指定時沿用 preset 內建的單一 α）",
    )
    parser.add_argument(
        "--list-materials",
        action="store_true",
        help="列出材質表裡可用的 id 後結束",
    )
    args = parser.parse_args()

    if args.list_materials:
        try:
            data = load_materials()
        except FileNotFoundError as e:
            print(f"❌ 錯誤：{e}")
            print("   請確認 data/materials.json 存在（T-03 的材質表）。")
            sys.exit(1)
        print("data/materials.json 可用的材質 id：")
        for mat in data["materials"]:
            print(f"  {mat['id']:<18} {mat['name_zh']}")
        return 0

    if args.preset is None:
        parser.error("要指定 preset（small 或 hall），或用 --list-materials 查材質表")

    preset = PRESETS[args.preset]
    dims = preset["dimensions"]

    # --- 決定吸音係數：預設沿用 preset 的單一 α，有 --material 才改用材質表 ---
    material_entry = None
    band_freqs = None
    if args.material is not None:
        try:
            data = load_materials()
        except FileNotFoundError as e:
            print(f"❌ 錯誤：{e}")
            print("   請確認 data/materials.json 存在（T-03 的材質表）。")
            sys.exit(1)
        band_freqs = data["band_center_freqs_hz"]
        try:
            material_entry = get_material(args.material, data)
        except KeyError as e:
            # e.args[0] 就是 get_material 寫好的中文訊息（已含可用 id 清單）
            print(f"❌ 錯誤：{e.args[0]}")
            print("   （可用 python scripts/gen_ir_manual.py --list-materials 查看完整清單）")
            sys.exit(1)

    print(f"=== preset：{args.preset} ===")
    print(f"房間尺寸：{dims[0]}×{dims[1]}×{dims[2]} m（體積 {dims[0]*dims[1]*dims[2]:.1f} m³）")

    if material_entry is None:
        print(f"吸音係數 α：{preset['absorption']}（各面相同）")
        sabine = sabine_rt60(dims, preset["absorption"])
        longest_band_rt60 = sabine
    else:
        alphas = alpha_list(material_entry, band_freqs)
        print(f"材質：{material_entry['id']} — {material_entry['name_zh']}"
              f"（信心：{material_entry.get('confidence', '-')}）")
        print("吸音係數 α（各面相同）與各頻段 Sabine 理論 RT60：")
        band_rt60s = []
        for freq, alpha in zip(band_freqs, alphas):
            band_rt60 = sabine_rt60(dims, alpha)
            band_rt60s.append(band_rt60)
            print(f"    {freq:>5} Hz　α = {alpha:.3f}　→ RT60 ≈ {band_rt60:.3f} 秒")
        # 寬頻的殘響尾巴由「最不吸音的頻段」主導，這個值才是判斷 IR 要多長的依據
        longest_band_rt60 = max(band_rt60s)
        sabine = sabine_rt60(dims, float(np.mean(alphas)))
        print(f"平均 α = {np.mean(alphas):.4f}　→ 寬頻 Sabine RT60 ≈ {sabine:.3f} 秒")
        print(f"最長頻段 RT60 ≈ {longest_band_rt60:.3f} 秒（殘響尾巴由這個頻段決定）")

    print(f"聲源位置：{preset['source_pos']}　麥克風位置：{preset['mic_pos']}")
    print(f"image-source 最高階數：{preset['max_order']}　ray tracing 射線數：{preset['n_rays']}")

    if material_entry is None:
        print(f"Sabine 理論 RT60（參考值）：{sabine:.3f} 秒")

    # ray tracing 的追蹤時間必須涵蓋整段衰減，否則 IR 會被截斷、RT60 量測失真。
    # 不帶 --material 時完全沿用 preset 的值（維持 T-01 行為）；
    # 帶了材質才依「最長頻段 RT60」自動加長。
    time_thres = preset["time_thres"]
    if material_entry is not None:
        needed = longest_band_rt60 * 1.5
        if needed > time_thres:
            time_thres = float(needed)
            print(f"（依最長頻段 RT60，ray tracing 追蹤時間自動由 {preset['time_thres']} 秒"
                  f"加長到 {time_thres:.2f} 秒，避免 IR 被截斷）")

    print("模擬中，請稍候…")

    material = build_material(preset, material_entry, band_freqs)
    room = build_room(preset, material, time_thres)

    ir = np.asarray(room.rir[0][0], dtype=np.float64)
    print(f"模擬完成，IR 長度：{len(ir)} 取樣點（{len(ir)/SAMPLE_RATE:.3f} 秒）")

    # 用模擬出來的 IR 量測 RT60（T30 外推：量測 -5dB → -35dB 的衰減斜率再換算到 60dB）
    rt60_t30 = float(room.measure_rt60(decay_db=30)[0, 0])
    print(f"模擬 RT60 估計值（T30 外推）：{rt60_t30:.3f} 秒")

    ir_normalized = normalize_peak(ir, TARGET_PEAK_DBFS)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # 不帶 --material 時檔名照 T-01 舊樣；帶了材質才加後綴，避免蓋掉預設版本
    if material_entry is None:
        out_name = preset["output_name"]
    else:
        out_name = f"{preset['output_name']}_{material_entry['id']}"
    out_path = OUTPUT_DIR / f"ir_{out_name}.wav"
    sf.write(out_path, ir_normalized, SAMPLE_RATE, subtype=SUBTYPE)

    print(f"已輸出：{out_path}（{SAMPLE_RATE} Hz / 24bit / mono，峰值正規化到 {TARGET_PEAK_DBFS} dBFS）")


if __name__ == "__main__":
    sys.exit(main())
