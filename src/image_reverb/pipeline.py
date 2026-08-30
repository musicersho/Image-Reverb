"""T-15：CLI 整合 —— 照片／文字／複合場景三條管線的統一入口。

**本模組只是匯流點，不是重寫**（HANDOFF §0 A 已裁決）：三條管線各自的核心邏輯
（T-10~T-14 的照片路徑、T-20 的 `scene_text.py`、T-21 的 `coupled.py`）完全不動，
本模組只負責：(1) 依輸入類型呼叫對應管線、(2) 把各自的合成結果匯整成統一的
`analysis.json` schema、(3) 產生 mono/stereo WAV 與卷積試聽檔。

呼叫既有模組的方式與各自的獨立腳本（`gen_ir_from_text.py`／`gen_ir_coupled.py`）
逐字一致（相同函式、相同預設參數），這是 MD5 零回歸判準能成立的原因——本模組
自己不做任何影響音訊數值的運算。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from PIL import UnidentifiedImageError

from . import config, coupled, ir_synth, scene_text, visualize
from .acoustics import compute_acoustics
from .furnishings import estimate_furnishings
from .geometry import estimate_room, parse_override_dims
from .materials import SURFACE_NAMES, apply_overrides, load_materials
from .surfaces import compute_materials_confidence

PROJECT_ROOT = config.PROJECT_ROOT
OUTPUT_ROOT = PROJECT_ROOT / "output"
DRY_DEFAULT = PROJECT_ROOT / "assets" / "dry" / "clap_synth.wav"
CONVOLVE_SCRIPT = PROJECT_ROOT / "scripts" / "convolve.py"

TIME_BUDGET_S = 60.0  # SPEC §4：目標總耗時，超過不擋驗收，只記錄

# ------------------------------------------------------------
# warnings/notes 分流（技術債 #2，T-15 步驟 3）
#
# 現況：`AcousticsResult.warnings` = `RoomEstimate.notes` + `SurfaceMaterials.warnings`
# 兩者攪在一起寫進 `ir_synth.export_ir()`／`coupled.export_coupled()` 的 JSON（見各自
# 模組 docstring）。逐一改寫這幾個模組的內部資料結構風險太高（牽動 T-11/T-13/T-14/
# T-21 多處呼叫端），所以在這裡用「已知的純解析紀錄樣式」白名單分流：命中白名單
# 的是純粹的「解析器做了什麼」記錄（preset 選擇、顯式尺寸覆寫、材質關鍵字…），
# 其餘一律留在 warnings——不確定時偏向警示，不安靜藏起來（地雷 #15 的分流原則）。
# 白名單字串逐一對應到 geometry.py／scene_text.py／coupled.py 現有的固定文案，
# 若那些模組的文案改了，這裡的白名單要跟著更新。
# ------------------------------------------------------------
_NOTE_MARKERS = (
    "preset '",  # scene_text「文字場景：採用 preset 'x'」／coupled「聲源空間：preset 'x'」
    "場景 JSON 內嵌尺寸/材質",  # coupled inline 空間定義
    "preset 近似說明：",
    "大小修飾詞「",
    "顯式尺寸：",
    "材質關鍵字：",
    "水平 FOV：",
    "進深只涵蓋相機看得到的範圍",
    "尺寸由使用者手動指定",
    "尺度校驗通過：",
    "環景沒有「視野外」問題",
    "沒有足夠大的門，跳過尺度校驗",
    "陳設比例取自",  # T-32：furnishings.notes 的視角平均說明，不是警示
)


# T-25（REPORT §2.5 缺陷 B）：confidence 三軸——幾何 / 材質 / overall。
# overall 取兩者「較低者」，high > medium > low。
_CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}


def _overall_confidence(geometry_confidence: str, materials_confidence: str) -> str:
    """overall confidence = 幾何與材質兩軸取較低者（不會比任一分量更可信）。"""
    if _CONFIDENCE_RANK[materials_confidence] < _CONFIDENCE_RANK[geometry_confidence]:
        return materials_confidence
    return geometry_confidence


def _split_notes_and_warnings(raw: list[str]) -> tuple[list[str], list[str]]:
    notes: list[str] = []
    warnings: list[str] = []
    for item in raw:
        (notes if any(marker in item for marker in _NOTE_MARKERS) else warnings).append(item)
    return notes, warnings


def _elapsed_payload(t0: float) -> dict[str, Any]:
    elapsed = time.time() - t0
    payload: dict[str, Any] = {"elapsed_s": round(elapsed, 2), "time_budget_s": TIME_BUDGET_S}
    if elapsed > TIME_BUDGET_S:
        payload["elapsed_note"] = (
            f"總耗時 {elapsed:.1f}s 超過 SPEC §4 目標 {TIME_BUDGET_S:.0f}s"
            f"（不擋驗收，僅記錄）"
        )
    return payload


def _make_out_dir(name: str) -> Path:
    out_dir = OUTPUT_ROOT / name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _maybe_visualize(analysis: dict[str, Any], out_dir: Path, no_viz: bool) -> None:
    """T-16：預設產生 `analysis.png`，`--no-viz` 可關。只讀 analysis 畫圖，不改它。"""
    if no_viz:
        return
    png_path = visualize.render_analysis_png(analysis, out_dir)
    print(f"🖼️  視覺化：{png_path.name}")


def _write_stereo(out_dir: Path, left: np.ndarray, right: np.ndarray) -> Path:
    path = out_dir / "ir_stereo.wav"
    stereo = np.stack([left, right], axis=-1)
    sf.write(path, stereo, config.IR_SAMPLE_RATE, subtype="PCM_24")
    return path


def _run_wet_preview(dry: Path, ir_wav: Path, out_dir: Path, mix: float) -> Path | None:
    """跑 `scripts/convolve.py` 產生試聽檔（沿用既有腳本，不重寫卷積邏輯）。"""
    wet_path = out_dir / "wet_preview.wav"
    if not dry.exists():
        print(f"⚠️ 找不到乾聲檔 {dry}，略過試聽檔", file=sys.stderr)
        return None
    subprocess.run(
        [
            sys.executable,
            str(CONVOLVE_SCRIPT),
            str(dry),
            str(ir_wav),
            str(wet_path),
            "--mix",
            str(mix),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return wet_path


# ------------------------------------------------------------
# 三種輸入互斥檢查
# ------------------------------------------------------------


def check_mutual_exclusion(photo: str | None, text: str | None, scene: str | None) -> str | None:
    """回傳互斥檢查的錯誤訊息；沒有錯誤回傳 None。"""
    given = [name for name, val in (("photo", photo), ("--text", text), ("--scene", scene)) if val]
    if len(given) >= 2:
        return f"三種輸入互斥（<photo>／--text／--scene 一次只能給一種），收到：{'、'.join(given)}"
    if len(given) == 0:
        return "要指定一種輸入：<photo>｜--text \"場景描述\"｜--scene <場景.json>"
    return None


# ------------------------------------------------------------
# 照片管線：T-10 前處理 → T-11 幾何 → T-12 材質 → T-13 參數 → T-14 IR
# ------------------------------------------------------------


def run_photo(
    photo: str,
    override_dims: str | None = None,
    override_materials: list[str] | None = None,
    no_viz: bool = False,
    force_low_confidence: bool = False,
    furnishings: bool = False,
    no_furnishings: bool = False,
) -> int:
    from .preprocess import preprocess_image
    from .surfaces import surfaces_from_preprocess, _load_segmenter, segment_roles

    t0 = time.time()
    photo_path = Path(photo)
    if photo_path.is_dir():
        print(f"錯誤：{photo_path} 是資料夾，請指定單一圖片檔", file=sys.stderr)
        return 2
    if not photo_path.is_file():
        print(f"錯誤：找不到檔案 {photo_path}", file=sys.stderr)
        return 2

    override = None
    if override_dims is not None:
        try:
            override = parse_override_dims(override_dims)
        except ValueError as e:
            print(f"錯誤：{e}", file=sys.stderr)
            return 2

    try:
        summary = preprocess_image(photo_path)
    except UnidentifiedImageError:
        print(f"錯誤：無法辨識為圖片檔 {photo_path}", file=sys.stderr)
        return 2

    print(f"=== 照片：{photo_path} ===")
    print(f"環景判定：{'是' if summary['is_equirect'] else '否'}")

    try:
        materials_data = load_materials()

        print("--- T-12 逐表面材質辨識 ---")
        surf, detail = surfaces_from_preprocess(summary)
        scene_cues: dict[str, float] = {}
        if not summary["is_equirect"]:
            from PIL import Image

            img = Image.open(summary["cropped"]).convert("RGB")
            _, ratios = segment_roles(img, *_load_segmenter())
            ood = [
                v
                for v in detail["views"].get("single", {}).values()
                if v.get("method") == "out_of_domain"
            ]
            scene_cues = {
                "floor_pixel_ratio": ratios.get(3, 0.0) + ratios.get(28, 0.0),
                "person_pixel_ratio": ratios.get(12, 0.0),
                "out_of_domain": bool(ood),
                "out_of_domain_label": (
                    ood[0]["top3"][0][0].lstrip("_") if ood and ood[0].get("top3") else ""
                ),
            }
        for name, mid in surf.as_dict().items():
            print(f"  {name:<8} → {mid:<16}（來源：{surf.sources.get(name, '-')}）")

        override_specs_used: list[str] = []
        if override_materials:
            apply_overrides(surf, override_materials, materials_data)
            override_specs_used = list(override_materials)
            print(f"  已套用 --override-material：{', '.join(override_specs_used)}")

        # T-25：材質信心要在 surf 最終定案（override 套用完）之後算，
        # 反映實際會拿去合成 IR 的六面材質，不是套 override 之前的猜測。
        materials_confidence = compute_materials_confidence(surf)

        print("--- T-11 幾何估計 ---")
        if override is not None:
            print("（--override-dims 已指定，跳過深度模型）")
        est = estimate_room(summary, override_dims=override, scene_cues=scene_cues or None)
        overall_confidence = _overall_confidence(est.confidence, materials_confidence)
        print(
            f"  房間尺寸：{est.length_m:.2f}×{est.width_m:.2f}×{est.height_m:.2f} m"
            f"（dims_source={est.dims_source}）"
        )
        print(
            f"  confidence：geometry={est.confidence}, materials={materials_confidence}, "
            f"overall={overall_confidence}"
        )

        # T-26（REPORT §2.6 缺陷 E）：overall confidence 為 low 時擋下輸出——
        # 降信心不等於保護使用者，之前 low + 明確警示照樣輸出到底，使用者盲聽當然配錯。
        # 擋在合成（T-13/T-14）之前，不是擋在寫檔之前：不浪費運算，也絕不可能已經
        # 寫出任何 WAV／JSON 才被擋下（紅旗：擋在合成之後＝算了才擋）。
        forced_low_confidence = False
        if overall_confidence == "low":
            if not force_low_confidence:
                print(
                    "錯誤：overall confidence 為 low，已擋下輸出（不會寫出任何 WAV／JSON）。",
                    file=sys.stderr,
                )
                print(
                    f"  原因：geometry={est.confidence}, materials={materials_confidence}"
                    "——幾何和/或材質推測很可能不可信，直接輸出容易讓使用者盲聽配錯空間。",
                    file=sys.stderr,
                )
                # T-30（裁決 T-28-A 執行卡）：只點名 fallback／out_of_domain 的面——
                # 這兩種來源才會觸發 compute_materials_confidence() 規則 1。無來源的面
                # （地雷 #23）不觸發規則 1，列了會誤導使用者以為覆寫它能解 gate。
                low_conf_faces = [
                    name
                    for name in SURFACE_NAMES
                    if surf.sources.get(name) in ("fallback", "out_of_domain")
                ]
                if low_conf_faces:
                    print("  低信心面：", file=sys.stderr)
                    for name in low_conf_faces:
                        print(
                            f"    {name}：目前推測 {getattr(surf, name)}"
                            f"（來源：{surf.sources.get(name)}）",
                            file=sys.stderr,
                        )
                print("  怎麼繼續：", file=sys.stderr)
                step = 1
                if est.confidence == "low":
                    print(
                        f"    {step}) 幾何不可信 → 用 --override-dims 手動指定房間尺寸"
                        "（公尺），例如 4x3x2.5",
                        file=sys.stderr,
                    )
                    step += 1
                if materials_confidence == "low" and low_conf_faces:
                    skeleton = " ".join(
                        f"--override-material {name}=<材質id>" for name in low_conf_faces
                    )
                    print(
                        f"    {step}) 材質不可信 → 人工確認上列面的實際材質後覆寫，"
                        f"例如：python -m src.image_reverb {photo_path} {skeleton}",
                        file=sys.stderr,
                    )
                    print(
                        "       <材質id> 請自行判斷並用 "
                        "`python scripts/gen_ir_manual.py --list-materials` 查表填入"
                        "——這是人工確認的出口，不要用另一層自動猜測取代 CLIP。",
                        file=sys.stderr,
                    )
                    print(
                        "       注意：覆寫後若六面材質變成完全相同，仍會落入退化規則"
                        "（規則 2）判定為 low。",
                        file=sys.stderr,
                    )
                    step += 1
                elif materials_confidence == "low" and not low_conf_faces and surf.is_uniform():
                    # T-34：規則 1（fallback/out_of_domain）沒觸發，materials 仍為 low
                    # 只可能是規則 2（六面全同的退化情況）——這種情況 low_conf_faces
                    # 是空的，之前完全沒有導引，只剩 --force-low-confidence 一條路
                    # （Opus 驗證 T-30 時指出的死路）。
                    skeleton = " ".join(
                        f"--override-material {name}=<材質id>" for name in SURFACE_NAMES
                    )
                    print(
                        f"    {step}) 六面材質被判成完全相同（退化規則）→ 人工確認後用 "
                        "--override-material 至少覆寫一面為實際不同的材質，例如："
                        f"python -m src.image_reverb {photo_path} {skeleton}",
                        file=sys.stderr,
                    )
                    print(
                        "       <材質id> 請自行判斷並用 "
                        "`python scripts/gen_ir_manual.py --list-materials` 查表填入"
                        "——這是人工確認的出口，不要用另一層自動猜測取代 CLIP。",
                        file=sys.stderr,
                    )
                    step += 1
                print(
                    f"    {step}) 仍要照樣輸出 → 加 --force-low-confidence"
                    "（結果會標記 forced_low_confidence=true，不建議當常規路徑）",
                    file=sys.stderr,
                )
                return 3
            forced_low_confidence = True
            print(
                "⚠️  已指定 --force-low-confidence：overall confidence 為 low"
                f"（geometry={est.confidence}, materials={materials_confidence}），"
                "仍強制輸出，結果可信度未知，請自行評估。",
                file=sys.stderr,
            )

        # T-32（裁決 T-27-A 執行卡 2/3）：陳設偵測放在 gate 之後、compute_acoustics()
        # 之前——結構上保證陳設資料不可能影響 gate 判定（Phase 1.7 共同鐵則 6）。
        # T-35（裁決 T-33-A 裁決 A）：偵測維持三態都跑（除非 --no-furnishings），
        # 但只有 --furnishings 才把偵測結果傳給 compute_acoustics()——預設觀測模式
        # 傳 None，讓 compute_acoustics() 的行為與 --no-furnishings 逐位元相同。
        furn = None if no_furnishings else estimate_furnishings(detail)

        print("--- T-13 聲學參數 ---")
        ac = compute_acoustics(
            est, surf, materials_data, furnishings=(furn if furnishings else None)
        )
        print(f"  Sabine 目標 RT60：{[round(v, 2) for v in ac.rt60_bands_sabine]} s")
        if furnishings and ac.furnishings is not None and ac.furnishings["categories"]:
            idx_1k = ac.band_center_freqs_hz.index(1000)
            print("  陳設偵測（等效吸音面積，裁決 T-27-A；已套用 --furnishings）：")
            for name, cat in ac.furnishings["categories"].items():
                print(
                    f"    {name:<10} 佔比 {cat['ratio'] * 100:5.1f}%　"
                    f"A_extra@1kHz {cat['A_by_band'][idx_1k]:.3f} m²"
                )
            print(
                "    佔 1kHz 總吸音比例："
                f"{ac.furnishings['proportion_of_absorption_1khz'] * 100:.1f}%"
            )
        elif not furnishings and not no_furnishings and furn is not None and furn.categories:
            print("  陳設偵測（預設觀測模式，未套用；--furnishings 可啟用）：")
            for name, cat in furn.categories.items():
                print(f"    {name:<10} 佔比 {cat['ratio'] * 100:5.1f}%")

        print("--- T-14 IR 合成 ---")
        mono = ir_synth.synthesize_ir(ac, materials_data)
        left, right, seed_right = ir_synth.synthesize_stereo(ac, materials_data)
    except (ValueError, KeyError, FileNotFoundError) as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 2

    out_dir = _make_out_dir(photo_path.stem)
    mono_wav, mono_json = ir_synth.export_ir(mono, out_dir / "ir_mono")
    stereo_wav = _write_stereo(out_dir, left, right)
    wet_wav = _run_wet_preview(DRY_DEFAULT, mono_wav, out_dir, mix=0.6)

    mono_payload = json.loads(mono_json.read_text(encoding="utf-8"))
    notes, warnings = _split_notes_and_warnings(mono_payload["warnings"])

    # T-35：陳設三態組 analysis.json 的 "furnishings" 鍵。
    #   --no-furnishings → None（現行為，ac.furnishings 本來就是 None）。
    #   --furnishings     → ac.furnishings（現行完整結構）＋ applied=True。
    #   預設（觀測模式）  → 偵測資訊（ratio/total_ratio/cap），不含聲學換算欄位
    #                       （A_by_band／absorption_extra_m2_by_band，地雷 #15 精神），
    #                       applied=False；cap 訊息（若有）走 notes 不走 warnings。
    furnishings_payload: dict[str, Any] | None = None
    if no_furnishings:
        furnishings_payload = None
    elif furnishings:
        if ac.furnishings is not None:
            furnishings_payload = dict(ac.furnishings)
            furnishings_payload["applied"] = True
            detected = "、".join(
                f"{name} {cat['ratio'] * 100:.1f}%"
                for name, cat in ac.furnishings["categories"].items()
            )
            if detected:
                notes.append(
                    f"陳設偵測：{detected}（佔 1kHz 總吸音 "
                    f"{ac.furnishings['proportion_of_absorption_1khz'] * 100:.1f}%）"
                )
    elif furn is not None:
        furnishings_payload = {
            "categories": {
                name: {"ratio": round(cat["ratio"], 5)} for name, cat in furn.categories.items()
            },
            "total_ratio": round(furn.total_ratio, 5),
            "cap_applied": bool(furn.warnings),
            "applied": False,
            "note": (
                "陳設偵測結果未套用聲學計算（預設觀測模式）——T-33 實測套用對 "
                "§7-2 達標率淨效果為負，見 output/material_round/REPORT.md §4.2"
                "（裁決 T-33-A）。加 --furnishings 可啟用套用。"
            ),
        }
        detected = "、".join(
            f"{name} {cat['ratio'] * 100:.1f}%" for name, cat in furn.categories.items()
        )
        if detected:
            notes.append(f"陳設偵測：{detected}（未套用，預設觀測模式，--furnishings 可啟用）")
        # furn.notes（視角平均說明）＋furn.warnings（cap 訊息，若有）都走 notes，
        # 不走 warnings——沒套用的估計值發警報會誤導（地雷 #15 精神）。
        notes.extend(furn.notes + furn.warnings)

    if forced_low_confidence:
        # T-26 步驟 2：帶 --force-low-confidence 越過 gate 時，JSON 要留下明確標記與
        # 一條進 warnings 的說明，不能讓「這筆結果本來會被擋下」的事實只留在 CLI 輸出裡。
        warnings.append(
            "已指定 --force-low-confidence：overall confidence 為 low"
            f"（geometry={est.confidence}, materials={materials_confidence}），"
            "使用者強制輸出，結果可信度未知。"
        )

    analysis: dict[str, Any] = {
        "input_type": "photo",
        "input": str(photo_path),
        "output_dir": str(out_dir),
        "dims_source": est.dims_source,
        "confidence": overall_confidence,
        "geometry_confidence": est.confidence,
        "materials_confidence": materials_confidence,
        "forced_low_confidence": forced_low_confidence,
        "dims_m": {"length": est.length_m, "width": est.width_m, "height": est.height_m},
        "volume_m3": round(est.volume_m3, 2),
        "surfaces": surf.as_dict(),
        "surfaces_sources": surf.sources,
        "override_dims_used": override is not None,
        "override_materials_used": override_specs_used,
        "band_center_freqs_hz": ac.band_center_freqs_hz,
        "rt60_bands_target_sabine": [round(v, 4) for v in ac.rt60_bands_sabine],
        "furnishings": furnishings_payload,
        "closed_loop": mono_payload["closed_loop"],
        "ir_mono": {"path": str(mono_wav)},
        "ir_stereo": {
            "path": str(stereo_wav),
            "note": "簡單 decorrelation：早期反射共用（決定性相同），晚期噪音左右各自不同 seed",
            "seed_left": mono.noise_seed,
            "seed_right": seed_right,
        },
        "wet_preview": {"path": str(wet_wav) if wet_wav else None, "mix": 0.6},
        "notes": notes,
        "warnings": warnings,
        **_elapsed_payload(t0),
    }
    (out_dir / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _maybe_visualize(analysis, out_dir, no_viz)

    print(f"已輸出：{mono_wav.name}、{stereo_wav.name}、analysis.json → {out_dir}")
    if wet_wav:
        print(f"🎧 試聽檔：{wet_wav}（mix=0.6；數字合理 ≠ 聽起來對，請實聽）")
    for w in warnings:
        print(f"  ⚠️ {w}")
    return 0


# ------------------------------------------------------------
# 文字管線：scene_text.parse_scene_text() → T-13 → T-14
# ------------------------------------------------------------


def run_text(text: str, no_viz: bool = False) -> int:
    t0 = time.time()
    try:
        presets = scene_text.load_scene_presets()
        materials_data = load_materials()
        parsed = scene_text.parse_scene_text(text, presets, materials_data)
    except (ValueError, FileNotFoundError) as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 2

    est, surf = parsed.estimate, parsed.surfaces
    print(f"=== 文字場景：{parsed.preset_name_zh}（preset: {parsed.preset_id}） ===")
    print(
        f"尺寸：{est.length_m}×{est.width_m}×{est.height_m} m"
        f"（dims_source={est.dims_source}, confidence={est.confidence}）"
    )

    try:
        ac = compute_acoustics(est, surf, materials_data)
        mono = ir_synth.synthesize_ir(ac, materials_data)
        left, right, seed_right = ir_synth.synthesize_stereo(ac, materials_data)
    except (ValueError, KeyError) as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 2

    out_dir = _make_out_dir(f"text_{parsed.preset_id}")
    mono_wav, mono_json = ir_synth.export_ir(mono, out_dir / "ir_mono")
    stereo_wav = _write_stereo(out_dir, left, right)
    wet_wav = _run_wet_preview(DRY_DEFAULT, mono_wav, out_dir, mix=0.6)

    mono_payload = json.loads(mono_json.read_text(encoding="utf-8"))
    notes, warnings = _split_notes_and_warnings(mono_payload["warnings"])
    notes = list(dict.fromkeys(parsed.parse_notes + notes))

    analysis: dict[str, Any] = {
        "input_type": "text",
        "input": text,
        "output_dir": str(out_dir),
        "preset_id": parsed.preset_id,
        "preset_name_zh": parsed.preset_name_zh,
        "dims_source": est.dims_source,
        "confidence": est.confidence,
        "dims_m": {"length": est.length_m, "width": est.width_m, "height": est.height_m},
        "volume_m3": round(est.volume_m3, 2),
        "surfaces": surf.as_dict(),
        "band_center_freqs_hz": ac.band_center_freqs_hz,
        "rt60_bands_target_sabine": [round(v, 4) for v in ac.rt60_bands_sabine],
        "closed_loop": mono_payload["closed_loop"],
        "ir_mono": {"path": str(mono_wav)},
        "ir_stereo": {
            "path": str(stereo_wav),
            "note": "簡單 decorrelation：早期反射共用（決定性相同），晚期噪音左右各自不同 seed",
            "seed_left": mono.noise_seed,
            "seed_right": seed_right,
        },
        "wet_preview": {"path": str(wet_wav) if wet_wav else None, "mix": 0.6},
        "notes": notes,
        "warnings": warnings,
        **_elapsed_payload(t0),
    }
    (out_dir / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _maybe_visualize(analysis, out_dir, no_viz)

    print(f"已輸出：{mono_wav.name}、{stereo_wav.name}、analysis.json → {out_dir}")
    if wet_wav:
        print(f"🎧 試聽檔：{wet_wav}（mix=0.6；數字合理 ≠ 聽起來對，請實聽）")
    for w in warnings:
        print(f"  ⚠️ {w}")
    return 0


# ------------------------------------------------------------
# 複合場景管線：coupled.synthesize_coupled() → coupled.export_coupled()
# ------------------------------------------------------------


def run_scene(scene_path: str, no_viz: bool = False) -> int:
    t0 = time.time()
    try:
        scene = coupled.load_scene_file(scene_path)
        result = coupled.synthesize_coupled(scene)
    except (ValueError, FileNotFoundError, KeyError) as e:
        print(f"錯誤：{e}", file=sys.stderr)
        return 2

    print(f"=== 複合場景：{result.scene_name}（method: {coupled.METHOD_ID}，工程近似） ===")
    for room in result.rooms_summary:
        print(
            f"  [{room['role']}] {room['name']}：{room['dims_m'][0]}×{room['dims_m'][1]}×"
            f"{room['dims_m'][2]} m，T30 量測 {room['t30_measured_s']} s"
        )

    out_dir = _make_out_dir(result.scene_name)
    mono_wav, scene_json = coupled.export_coupled(result, out_dir / "ir_mono")
    # 複合場景一律全濕（mix 1.0）：聽者與聲源在不同空間，物理上不存在乾聲直達
    wet_wav = _run_wet_preview(DRY_DEFAULT, mono_wav, out_dir, mix=1.0)

    scene_payload = json.loads(scene_json.read_text(encoding="utf-8"))
    notes, warnings = _split_notes_and_warnings(scene_payload["warnings"])
    notes.append(coupled.METHOD_DISCLAIMER)
    if scene.get("description_zh"):
        notes.append(f"場景描述：{scene['description_zh']}")

    rooms_out = []
    for room in result.rooms_summary:
        rooms_out.append(
            {
                "role": room["role"],
                "name": room["name"],
                "dims_source": "scene_json",
                "dims_m": room["dims_m"],
                "surfaces": room["surfaces"],
                "rt60_bands_target_sabine": room["rt60_bands_target_sabine"],
                "t30_measured_s": room["t30_measured_s"],
                "closed_loop": room["closed_loop"],
            }
        )

    analysis: dict[str, Any] = {
        "input_type": "scene",
        "input": str(scene_path),
        "output_dir": str(out_dir),
        "scene_name": result.scene_name,
        "method": coupled.METHOD_ID,
        "method_disclaimer": coupled.METHOD_DISCLAIMER,
        "rooms": rooms_out,
        "paths": result.paths_summary,
        "band_center_freqs_hz": result.band_center_freqs_hz,
        "ir_mono": {"path": str(mono_wav)},
        "ir_stereo": {
            "generated": False,
            "note": "複合場景 v1 只出 mono，stereo 留待後續（不安靜省略）",
        },
        "wet_preview": {"path": str(wet_wav) if wet_wav else None, "mix": 1.0},
        "notes": notes,
        "warnings": warnings,
        **_elapsed_payload(t0),
    }
    (out_dir / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    _maybe_visualize(analysis, out_dir, no_viz)

    print(f"已輸出：{mono_wav.name}（mono，stereo 留待後續）、analysis.json → {out_dir}")
    if wet_wav:
        print(f"🎧 試聽檔：{wet_wav}（全濕 mix=1.0）")
    for w in warnings:
        print(f"  ⚠️ {w}")
    return 0
