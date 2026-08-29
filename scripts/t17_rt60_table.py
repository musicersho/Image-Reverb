#!/usr/bin/env python3
"""T-17 §7-2：生成 IR vs 真實 IR 的逐頻段 RT60 對照表（量測驅動程式）。

跑法：`python scripts/t17_rt60_table.py`
輸出：`output/mvp_acceptance/rt60_table.json`（REPORT.md 的數字全部由此檔產生）

**為什麼要有這支腳本**：REPORT.md 的每一個數字都必須可被第三方重跑複驗。
把量測寫成一次性 shell 操作，等於交出一份沒人能重算的表——那正是 WORKFLOW §5
紅旗 1（「說測試通過但沒有實際執行的輸出」）的溫床。

**量測管線（裁決 B 執行要求 1）**：生成 IR 與真實 IR 走**同一支未經修改的**
`src/image_reverb/ir_metrics.py`：
  - 逐頻段 T30 → `ir_metrics.band_t30()`（125/250/500/1k/2k/4k）
  - 低頻聯合帶 T30 → `ir_metrics.t30_low_combined()`（88.4–353.6Hz 固定值，
    **不得逐場地調整**，裁決 B 執行要求 2）
本腳本不重新實作任何量測邏輯，只負責讀檔、聲道處理、組表。

**立體聲真實 IR 的處理**：EchoThief 五場地是 stereo。**不做聲道相加**——兩聲道
相加會在高頻產生梳狀濾波，污染 2k/4k 頻段的量測。改為逐聲道各量一次 T30，
取兩聲道平均，並記錄兩聲道差值供審查（`per_channel` 欄）。

**截尾偵測**：Schroeder 曲線若沒衰減到 -35dB，`t30_from_curve()` 會直接報錯；
但曲線「剛好」掃到 -35dB 的情況會給出被截尾壓短的 T30 而不報錯。因此每一筆都
記錄曲線最低點 `curve_min_db` 與擬合區樣本數，讓 REPORT 能標出可疑值。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.image_reverb import ir_metrics  # noqa: E402

BANDS = [125, 250, 500, 1000, 2000, 4000]
OUT_DIR = REPO_ROOT / "output" / "mvp_acceptance"

# 8 個對照場地：真實 IR 檔案 ← → 本專案生成 IR 的輸出目錄
# `real_irs` 給多個檔案者＝MIT 未公開 photo↔IR 對應，不做猜測性一對一配對，
# 全部量測後以「範圍」呈現（見各 INFO.md 的「⚠️ 照片與 IR 的對應關係」）。
VENUES = [
    {
        "key": "cathedral_room_shasta_lake_caverns",
        "label": "Cathedral Room, Shasta Lake Caverns（石灰岩洞窟）",
        "source": "EchoThief",
        "real_irs": ["cathedral_room_shasta_lake_caverns/CathedralRoom.wav"],
        "photo": "cathedral_room_shasta_lake_caverns/CathedralRoom.jpg",
        "runs": ["CathedralRoom"],
    },
    {
        "key": "divorce_beach",
        "label": "Divorce Beach（戶外沙灘岩礁）",
        "source": "EchoThief",
        "real_irs": ["divorce_beach/DivorceBeach.wav"],
        "photo": "divorce_beach/DivorceBeach.jpg",
        "runs": ["DivorceBeach"],
    },
    {
        "key": "mit_department_store",
        "label": "Department Store（MIT，百貨賣場）",
        "source": "MIT Reverb Survey",
        "real_irs": ["mit_department_store/h160_DepartmentStore_1txts.wav"],
        "photo": "mit_department_store/site_photo_department_store.png",
        "runs": ["site_photo_department_store", "t17_manual_department_store"],
    },
    {
        "key": "mit_gym",
        "label": "Gym（MIT，健身房／重訓室）",
        "source": "MIT Reverb Survey",
        "real_irs": [
            "mit_gym/h026_Gym_8txts.wav",
            "mit_gym/h052_Gym_WeightRoom_3txts.wav",
            "mit_gym/h120_Gym_WeightRoom_1txts.wav",
        ],
        "photo": "mit_gym/site_photo_gym.png",
        "runs": ["site_photo_gym", "t17_manual_gym"],
    },
    {
        "key": "mit_restaurant",
        "label": "Restaurant（MIT，餐廳用餐區）",
        "source": "MIT Reverb Survey",
        "real_irs": [
            "mit_restaurant/h093_Restaurant_2txts.wav",
            "mit_restaurant/h114_Restaurant_txts.wav",
            "mit_restaurant/h130_Restaurant_1txs.wav",
            "mit_restaurant/h164_Restaurant_1txts.wav",
        ],
        "photo": "mit_restaurant/site_photo_restaurant.png",
        "runs": ["site_photo_restaurant", "t17_manual_restaurant"],
    },
    {
        "key": "racquetball_court_4",
        "label": "Racquetball Court 4（壁球場，必測反例）",
        "source": "EchoThief",
        "real_irs": ["racquetball_court_4/RacquetballCourt4.wav"],
        "photo": "racquetball_court_4/RacquetballCourt4.jpg",
        "runs": [
            "RacquetballCourt4",
            "t17_manual_racquetball",
            "t17_diag_racquetball_hard",
        ],
    },
    {
        "key": "steinman_hall",
        "label": "Steinman Hall（音樂廳）",
        "source": "EchoThief",
        "real_irs": ["steinman_hall/SteinmanHall.wav"],
        "photo": "steinman_hall/SteinmanHall.jpg",
        "runs": ["SteinmanHall", "t17_manual_steinman"],
    },
    {
        "key": "tunnel_to_hell",
        "label": "Tunnel to Hell（要塞地下混凝土隧道）",
        "source": "EchoThief",
        "real_irs": ["tunnel_to_hell/TunnelToHell.wav"],
        "photo": "tunnel_to_hell/TunnelToHell.jpg",
        "runs": ["TunnelToHell", "t17_diag_tunnel_perspective"],
    },
]


def measure_one_channel(x: np.ndarray, fs: int) -> dict:
    """對單聲道訊號量六頻段 T30 ＋ 低頻聯合帶 T30，並記錄截尾診斷。"""
    out: dict = {"bands": {}, "low_combined": None, "diagnostics": {}}

    try:
        vals = ir_metrics.band_t30(x, fs, BANDS)
        out["bands"] = {str(f): round(float(v), 4) for f, v in zip(BANDS, vals)}
    except Exception as e:  # 逐頻段個別重跑，讓能量測的頻段不被一個壞頻段拖垮
        out["bands"] = {}
        for f in BANDS:
            try:
                out["bands"][str(f)] = round(float(ir_metrics.band_t30(x, fs, [f])[0]), 4)
            except Exception as e2:
                out["bands"][str(f)] = None
                out["diagnostics"][f"band_{f}_error"] = str(e2)[:160]
        out["diagnostics"]["band_t30_bulk_error"] = str(e)[:160]

    try:
        out["low_combined"] = round(float(ir_metrics.t30_low_combined(x, fs)), 4)
    except Exception as e:
        out["diagnostics"]["low_combined_error"] = str(e)[:160]

    # 截尾診斷：曲線最低點沒有明顯低於 -35dB，代表擬合區貼在檔尾，T30 會被壓短
    from scipy.signal import sosfiltfilt

    for f in BANDS:
        try:
            sos = ir_metrics._bandpass_sos(float(f), fs)
            curve = ir_metrics.schroeder_curve_db(sosfiltfilt(sos, np.asarray(x, dtype=np.float64)))
            out["diagnostics"][f"curve_min_db_{f}"] = round(float(curve[-2]), 1)
        except Exception:
            pass
    return out


def measure_file(path: Path) -> dict:
    """讀檔 → 逐聲道量測 → 回傳平均值與逐聲道明細。"""
    data, fs = sf.read(str(path), always_2d=True)
    n_ch = data.shape[1]
    per_channel = [measure_one_channel(data[:, c], fs) for c in range(n_ch)]

    def avg(getter):
        vals = [getter(pc) for pc in per_channel]
        vals = [v for v in vals if v is not None]
        return round(float(np.mean(vals)), 4) if vals else None

    return {
        "file": str(path.relative_to(REPO_ROOT)),
        "sample_rate": int(fs),
        "channels": n_ch,
        "duration_s": round(len(data) / fs, 4),
        "bands": {str(f): avg(lambda pc, f=f: pc["bands"].get(str(f))) for f in BANDS},
        "low_combined": avg(lambda pc: pc["low_combined"]),
        "per_channel": per_channel,
    }


def real_reference(real_list: list[dict], key: str) -> dict:
    """真實 IR 的參考值。

    單一檔案 → 該值即參考值。多檔案（MIT 未公開 photo↔IR 對應）→ **不挑一個當
    ground truth**，回傳 min/max 區間與中位數；誤差以「是否落在區間內」判定，
    並在 REPORT 標明這是弱於單一配對的證據。
    """
    vals = [r[key] for r in real_list if r.get(key) is not None]
    if not vals:
        return {"value": None, "min": None, "max": None, "n": 0}
    return {
        "value": round(float(np.median(vals)), 4),
        "min": round(float(min(vals)), 4),
        "max": round(float(max(vals)), 4),
        "n": len(vals),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ref_root = REPO_ROOT / "assets" / "reference_irs"
    out_root = REPO_ROOT / "output"
    result: dict = {"bands_hz": BANDS, "tolerance_pct": 20.0, "venues": []}

    for v in VENUES:
        print(f"=== {v['label']}")
        entry = {k: v[k] for k in ("key", "label", "source", "photo")}

        entry["real"] = []
        for rel in v["real_irs"]:
            p = ref_root / rel
            if not p.exists():
                print(f"  ❌ 找不到真實 IR：{p}", file=sys.stderr)
                return 1
            m = measure_file(p)
            print(
                f"  真實 {p.name:38s} fs={m['sample_rate']} ch={m['channels']} "
                f"低頻聯合帶={m['low_combined']}"
            )
            entry["real"].append(m)

        # 真實側參考值（多檔＝區間）
        entry["real_reference"] = {
            "bands": {
                str(f): real_reference([r["bands"] for r in entry["real"]], str(f)) for f in BANDS
            },
            "low_combined": real_reference(entry["real"], "low_combined"),
            "n_files": len(entry["real"]),
        }

        # 生成側：逐個 run 量測 + 對真實側算誤差
        entry["generated"] = []
        for run in v.get("runs", []):
            run_dir = out_root / run
            ir_path = run_dir / "ir_mono.wav"
            aj_path = run_dir / "analysis.json"
            if not ir_path.exists() or not aj_path.exists():
                print(f"  ⏭️  尚未產生：output/{run}/（跳過）")
                continue
            aj = json.loads(aj_path.read_text(encoding="utf-8"))
            m = measure_file(ir_path)
            g = {
                "run": run,
                "dims_source": aj.get("dims_source"),
                "confidence": aj.get("confidence"),
                "dims_m": aj.get("dims_m"),
                "volume_m3": aj.get("volume_m3"),
                "override_dims_used": aj.get("override_dims_used"),
                "measured": {"bands": m["bands"], "low_combined": m["low_combined"]},
                "errors": {},
            }
            for f in BANDS:
                g["errors"][str(f)] = error_vs_reference(
                    m["bands"][str(f)], entry["real_reference"]["bands"][str(f)]
                )
            g["errors"]["low_combined"] = error_vs_reference(
                m["low_combined"], entry["real_reference"]["low_combined"]
            )
            # 裁決 B 殘留風險檢查點：500Hz vs 聯合帶的階梯比（生成側與真實側各一）
            g["ladder_500_vs_low"] = {
                "generated": ratio(m["bands"]["500"], m["low_combined"]),
                "real": ratio(
                    entry["real_reference"]["bands"]["500"]["value"],
                    entry["real_reference"]["low_combined"]["value"],
                ),
            }
            print(
                f"  生成 {run:34s} dims_source={g['dims_source']} "
                f"conf={g['confidence']} 聯合帶={m['low_combined']}"
            )
            entry["generated"].append(g)

        result["venues"].append(entry)

    out_path = OUT_DIR / "rt60_table.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n已寫入 {out_path.relative_to(REPO_ROOT)}")
    return 0


def ratio(a, b):
    if a is None or b is None or b == 0:
        return None
    return round(float(a) / float(b), 3)


def error_vs_reference(measured, ref: dict) -> dict:
    """誤差 = (生成 − 真實) / 真實。

    真實側是區間時（MIT 多檔），額外給 `within_range`：生成值落在 min–max 內即算
    命中——這是**弱於**單一配對的判準，REPORT 必須標明，不得與單一配對場地混算。
    """
    if measured is None or ref.get("value") is None:
        return {"error_pct": None, "within_tolerance": None, "within_range": None}
    err = (measured - ref["value"]) / ref["value"]
    out = {
        "measured_s": round(float(measured), 4),
        "reference_s": ref["value"],
        "error_pct": round(err * 100.0, 1),
        "within_tolerance": bool(abs(err) <= 0.20),
    }
    if ref.get("n", 1) > 1:
        out["within_range"] = bool(ref["min"] <= measured <= ref["max"])
        out["reference_range"] = [ref["min"], ref["max"]]
    return out


if __name__ == "__main__":
    sys.exit(main())
