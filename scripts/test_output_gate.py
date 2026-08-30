#!/usr/bin/env python3
"""T-26 迴歸測試：低信心／域外輸入的輸出 gate（REPORT §2.6 缺陷 E）。

背景：`pipeline.run_photo()` 舊行為是從幾何直接進聲學→合成→`export_ir()`→wet
preview，完全不檢查 overall confidence——T-17 §7-1 的體育館／車內兩筆防呆規則
都正確判定成 `low` 並附上明確警示，但產品照樣輸出 WAV，使用者盲聽當然配錯。
本卡在合成（T-13/T-14）**之前**加一道 gate：overall confidence 為 `low` 就擋下
（不寫任何 WAV／JSON，exit 3），`--force-low-confidence` 是唯一明確出口。

為了不依賴下載/執行深度模型與 CLIP/分割模型（跑一次要數十秒且非本卡改動範圍），
本測試對 `preprocess.preprocess_image()` 與 `surfaces.surfaces_from_preprocess()`
打樁（stub），改用 `--override-dims` 讓 `estimate_room()` 走手動分支（本來就不跑
模型的既有分支，不是新樁），只控制 `SurfaceMaterials.sources`（真實資料結構）
讓 `compute_materials_confidence()`（T-25 已驗證的真實函式）算出想要的信心等級。
T-13 聲學計算、T-14 IR 合成／匯出、wet preview 全部走**真實程式碼**，只是不下載
影像模型——gate 本身以及 gate 後續的檔案寫出流程都是真實路徑，不是空跑。

本測試分五部分：
  0. CLI 參數接線（subprocess，不跑模型）：`--force-low-confidence` 存在，且
     跟 `--override-dims`/`--override-material` 一樣被限定只能搭配照片輸入
  A. overall=low、不帶旗標 → exit 3，且完全沒有建立輸出目錄（不只是沒有 wav——
     連 `_make_out_dir()` 都不該被呼叫，證明 gate 擋在寫檔**與**合成之前）。
     T-30：另外斷言 stderr 逐面點名觸發面（`floor`=fallback）與 `--override-material`
     字樣，且**不**點名無來源的 `ceiling` 與 clip 來源的四面牆——只有
     fallback/out_of_domain 才觸發 `compute_materials_confidence()` 規則 1，
     列出其他面會誤導使用者以為覆寫它們能解 gate（地雷 #23）。
  B. overall=low、帶 `--force-low-confidence` → exit 0，wav 產生，
     `analysis.json` 有 `forced_low_confidence: true`
  C. overall=medium（沒有觸發 gate）→ exit 0，wav 產生，行為不受影響
  D. materials=low 且 geometry=medium（T-30）→ exit 3，stderr **不**出現
     `--override-dims` 建議（幾何不是 low，這條建議救不了 gate），但仍有
     `--override-material` 建議——驗證建議是依軸分開給的，不是無條件全列
  E.（T-34）六面全同且全 clip、geometry=medium → materials=low 是規則 2
     （退化規則）觸發、非規則 1（沒有 fallback/out_of_domain 面，`low_conf_faces`
     是空的）→ stderr 含規則 2 導引與 `--override-material`、不含 `--override-dims`
     （T-30 沒覆蓋到的死路：舊碼此時只剩 `--force-low-confidence` 一條路）
  F.（T-34）geometry=low、materials=medium → stderr 含 `--override-dims` 建議
     （T-30 驗證者點名的無覆蓋分支：先前所有測試案例的 geometry 都不是 low）
  （C 額外用 `ir_synth.synthesize_ir` 呼叫次數佐證：A 呼叫 0 次、B/C 呼叫 1 次——
  gate 確實擋在合成之前，不是算完才丟棄結果）

跑法：`python scripts/test_output_gate.py`；全部通過 exit 0，任一失敗 exit 1。
會在 `output/` 底下建立／清除 `_test_t26_gate_*` 三個暫存資料夾，不影響任何
既有交付檔案。

診斷力：這支測試在加 gate 前的舊碼上必須 fail（低信心輸入照樣寫出 wav、
exit 0）——自我檢查已用 `git stash` 實測並附輸出。
"""

from __future__ import annotations

import contextlib
import io
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config, ir_synth  # noqa: E402
from src.image_reverb import pipeline  # noqa: E402
from src.image_reverb import preprocess as preprocess_mod  # noqa: E402
from src.image_reverb import surfaces as surfaces_mod  # noqa: E402
from src.image_reverb.geometry import RoomEstimate  # noqa: E402
from src.image_reverb.materials import SURFACE_NAMES, SurfaceMaterials  # noqa: E402

PROJECT_ROOT = config.PROJECT_ROOT
OUTPUT_ROOT = PROJECT_ROOT / "output"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


# 六面材質互不相同（跟 T-25 test_confidence_axes.py 的 _DISTINCT 同一套手法），
# 讓「六面全同→low」那條規則不會誤觸發，材質信心完全由 sources 決定。
_DISTINCT = dict(
    floor="carpet", ceiling="gypsum_board", west="brick",
    east="concrete", south="wood_panel", north="glass",
)


def _make_surf(source_for_all: str) -> SurfaceMaterials:
    surf = SurfaceMaterials(**_DISTINCT)
    for name in SURFACE_NAMES:
        surf.sources[name] = source_for_all
    return surf


def _make_uniform_clip_surf() -> SurfaceMaterials:
    """T-34 案例 E：六面全同一種材質、來源全是 'clip'——不觸發規則 1
    （沒有 fallback/out_of_domain），但 `is_uniform()` 為真觸發規則 2。
    """
    surf = SurfaceMaterials(
        floor="concrete", ceiling="concrete", west="concrete",
        east="concrete", south="concrete", north="concrete",
    )
    for name in SURFACE_NAMES:
        surf.sources[name] = "clip"
    return surf


def _make_mixed_surf() -> SurfaceMaterials:
    """T-30：floor=fallback、四面牆=clip、ceiling **不設定來源**（模擬地雷 #23
    的「無來源」狀態——`bathroom_tiled` 的真實分佈：floor fallback、ceiling 無來源、
    四面牆 clip）。用來驗證 gate 訊息只點名 fallback/out_of_domain 的面。
    """
    surf = SurfaceMaterials(**_DISTINCT)
    surf.sources["floor"] = "fallback"
    for name in ("west", "east", "south", "north"):
        surf.sources[name] = "clip"
    return surf


def _fake_estimate_room_medium(summary, override_dims=None, scene_cues=None):
    """T-30 案例 D 用：geometry=medium，不觸發 --override-dims 建議。"""
    return RoomEstimate(
        length_m=4.0, width_m=3.0, height_m=2.5,
        confidence="medium", dims_source="metric_depth",
    )


def _fake_estimate_room_low(summary, override_dims=None, scene_cues=None):
    """T-34 案例 F 用：geometry=low，用來覆蓋先前所有案例都沒測到的
    `--override-dims` 建議分支。"""
    return RoomEstimate(
        length_m=4.0, width_m=3.0, height_m=2.5,
        confidence="low", dims_source="metric_depth",
    )


def _install_stubs(surf: SurfaceMaterials):
    """樁掉 preprocess_image（回傳最小 summary）與 surfaces_from_preprocess
    （直接回傳指定好的 surf），兩者都是 `run_photo()` 裡的區域 import
    （`from .xxx import yyy`），所以在呼叫前把來源模組的屬性換掉即可生效——
    不需要碰 pipeline 模組本身。
    """

    def fake_preprocess_image(path, output_dir=None):
        # is_equirect=True 讓 run_photo() 跳過非環景才會走的
        # segment_roles()/CLIP 場景線索那段（本卡不需要它，也不想連帶下載模型）。
        return {"is_equirect": True}

    def fake_surfaces_from_preprocess(preprocess_summary, threshold=None):
        return surf, {}

    orig_preprocess = preprocess_mod.preprocess_image
    orig_surfaces = surfaces_mod.surfaces_from_preprocess
    preprocess_mod.preprocess_image = fake_preprocess_image
    surfaces_mod.surfaces_from_preprocess = fake_surfaces_from_preprocess
    return orig_preprocess, orig_surfaces


def _restore_stubs(orig_preprocess, orig_surfaces) -> None:
    preprocess_mod.preprocess_image = orig_preprocess
    surfaces_mod.surfaces_from_preprocess = orig_surfaces


def _check_cli_wiring() -> None:
    print("【0】CLI 參數接線（subprocess，不跑模型——在 check_mutual_exclusion 之後、"
          "任何管線呼叫之前就會回傳）")
    proc = subprocess.run(
        [sys.executable, "-m", "src.image_reverb", "--text", "測試", "--force-low-confidence"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    check(
        "--force-low-confidence 搭配 --text 用（非照片輸入）→ exit 2",
        proc.returncode == 2,
        f"returncode={proc.returncode}",
    )
    check(
        "錯誤訊息有點名 --force-low-confidence",
        "--force-low-confidence" in proc.stderr,
        f"stderr={proc.stderr.strip()!r}",
    )


def main() -> int:
    _check_cli_wiring()

    call_count = {"n": 0}
    real_synthesize_ir = ir_synth.synthesize_ir

    def counting_synthesize_ir(*args, **kwargs):
        call_count["n"] += 1
        return real_synthesize_ir(*args, **kwargs)

    with tempfile.TemporaryDirectory() as tmp:
        # 三個案例各用獨立的假照片路徑（stem 決定輸出資料夾名稱），內容不重要
        # ——preprocess_image 已被樁掉，從不會真的去讀取這個檔案的畫素。
        low_photo = Path(tmp) / "_test_t26_gate_low.png"
        low_forced_photo = Path(tmp) / "_test_t26_gate_low_forced.png"
        medium_photo = Path(tmp) / "_test_t26_gate_medium.png"
        mixed_geom_photo = Path(tmp) / "_test_t30_gate_mixed_geom.png"
        uniform_photo = Path(tmp) / "_test_t34_gate_uniform.png"
        low_geom_photo = Path(tmp) / "_test_t34_gate_low_geom.png"
        for p in (
            low_photo, low_forced_photo, medium_photo, mixed_geom_photo,
            uniform_photo, low_geom_photo,
        ):
            p.write_bytes(b"")

        out_dirs = [
            OUTPUT_ROOT / p.stem
            for p in (
                low_photo, low_forced_photo, medium_photo, mixed_geom_photo,
                uniform_photo, low_geom_photo,
            )
        ]
        for d in out_dirs:
            if d.exists():
                shutil.rmtree(d)

        ir_synth.synthesize_ir = counting_synthesize_ir
        try:
            # --- 案例 A：overall=low，不帶旗標 -----------------------------
            print("【A】overall=low，不帶 --force-low-confidence")
            low_surf = _make_surf("fallback")  # 任一面 fallback → materials_confidence=low
            mixed_surf = _make_mixed_surf()  # T-30：floor fallback／ceiling 無來源／四牆 clip
            orig = _install_stubs(mixed_surf)
            n_before = call_count["n"]
            stderr_buf_a = io.StringIO()
            try:
                with contextlib.redirect_stderr(stderr_buf_a):
                    rc = pipeline.run_photo(
                        str(low_photo), override_dims="4x3x2.5", no_viz=True
                    )
            finally:
                _restore_stubs(*orig)
            stderr_a = stderr_buf_a.getvalue()

            check("exit code == 3", rc == 3, f"rc={rc}")
            check(
                "stderr 點名觸發面 floor（fallback）＋目前材質 id",
                "floor" in stderr_a and "fallback" in stderr_a and "carpet" in stderr_a,
                f"stderr={stderr_a!r}",
            )
            check(
                "stderr 出現 --override-material 覆寫骨架",
                "--override-material floor=" in stderr_a,
                f"stderr={stderr_a!r}",
            )
            check(
                "stderr 不點名無來源的 ceiling（地雷 #23：不觸發規則 1，列了會誤導）",
                "ceiling" not in stderr_a,
                f"stderr={stderr_a!r}",
            )
            check(
                "stderr 不點名 clip 來源的四面牆（只列 fallback/out_of_domain）",
                not any(w in stderr_a for w in ("west", "east", "south", "north")),
                f"stderr={stderr_a!r}",
            )
            out_dir_a = OUTPUT_ROOT / low_photo.stem
            check(
                "完全沒有建立輸出目錄（gate 擋在 _make_out_dir() 之前）",
                not out_dir_a.exists(),
                f"exists={out_dir_a.exists()}",
            )
            check(
                "synthesize_ir 完全沒被呼叫（gate 擋在合成之前，不是合成完才丟棄）",
                call_count["n"] - n_before == 0,
                f"delta={call_count['n'] - n_before}",
            )

            # --- 案例 B：overall=low，帶 --force-low-confidence -------------
            print("【B】overall=low，帶 --force-low-confidence")
            orig = _install_stubs(low_surf)
            n_before = call_count["n"]
            try:
                rc = pipeline.run_photo(
                    str(low_forced_photo),
                    override_dims="4x3x2.5",
                    no_viz=True,
                    force_low_confidence=True,
                )
            finally:
                _restore_stubs(*orig)

            check("exit code == 0", rc == 0, f"rc={rc}")
            out_dir_b = OUTPUT_ROOT / low_forced_photo.stem
            wav_b = out_dir_b / "ir_mono.wav"
            check("ir_mono.wav 有產生", wav_b.exists(), f"path={wav_b}")
            check(
                "synthesize_ir 有被呼叫（mono 1 次 + stereo 2 次 = 3 次）",
                call_count["n"] - n_before == 3,
                f"delta={call_count['n'] - n_before}",
            )
            analysis_b = _read_json(out_dir_b / "analysis.json")
            check(
                "analysis.json: confidence == 'low'",
                analysis_b.get("confidence") == "low",
                f"confidence={analysis_b.get('confidence')!r}",
            )
            check(
                "analysis.json: forced_low_confidence == true",
                analysis_b.get("forced_low_confidence") is True,
                f"forced_low_confidence={analysis_b.get('forced_low_confidence')!r}",
            )
            check(
                "analysis.json 的 warnings 有留下 force 說明",
                any("force-low-confidence" in w for w in analysis_b.get("warnings", [])),
                f"warnings={analysis_b.get('warnings')!r}",
            )

            # --- 案例 C：overall=medium，不受 gate 影響 ----------------------
            print("【C】overall=medium（六面材質互不相同、來源 'manual'，"
                  "不觸發 fallback/退化規則）")
            medium_surf = _make_surf("manual")
            orig = _install_stubs(medium_surf)
            n_before = call_count["n"]
            try:
                rc = pipeline.run_photo(
                    str(medium_photo), override_dims="4x3x2.5", no_viz=True
                )
            finally:
                _restore_stubs(*orig)

            check("exit code == 0", rc == 0, f"rc={rc}")
            out_dir_c = OUTPUT_ROOT / medium_photo.stem
            wav_c = out_dir_c / "ir_mono.wav"
            check("ir_mono.wav 有產生", wav_c.exists(), f"path={wav_c}")
            check(
                "synthesize_ir 有被呼叫（medium 不受 gate 影響，一樣是 3 次）",
                call_count["n"] - n_before == 3,
                f"delta={call_count['n'] - n_before}",
            )
            analysis_c = _read_json(out_dir_c / "analysis.json")
            check(
                "analysis.json: confidence == 'medium'",
                analysis_c.get("confidence") == "medium",
                f"confidence={analysis_c.get('confidence')!r}",
            )
            check(
                "analysis.json: forced_low_confidence == false（旗標沒給、也不需要）",
                analysis_c.get("forced_low_confidence") is False,
                f"forced_low_confidence={analysis_c.get('forced_low_confidence')!r}",
            )

            # --- 案例 D（T-30）：materials=low 且 geometry=medium ----------------
            print("【D】materials=low 且 geometry=medium → stderr 不出現 --override-dims 建議")
            mixed_surf_d = _make_mixed_surf()
            orig_stubs_d = _install_stubs(mixed_surf_d)
            orig_estimate_room = pipeline.estimate_room
            pipeline.estimate_room = _fake_estimate_room_medium
            stderr_buf_d = io.StringIO()
            try:
                with contextlib.redirect_stderr(stderr_buf_d):
                    rc = pipeline.run_photo(str(mixed_geom_photo), no_viz=True)
            finally:
                _restore_stubs(*orig_stubs_d)
                pipeline.estimate_room = orig_estimate_room
            stderr_d = stderr_buf_d.getvalue()

            check(
                "exit code == 3（materials=low → overall=low，即使 geometry=medium）",
                rc == 3,
                f"rc={rc}",
            )
            check(
                "stderr 不出現 --override-dims 建議（geometry=medium，不是 low）",
                "--override-dims" not in stderr_d,
                f"stderr={stderr_d!r}",
            )
            check(
                "stderr 仍有 --override-material 建議（materials=low 才是觸發原因）",
                "--override-material floor=" in stderr_d,
                f"stderr={stderr_d!r}",
            )

            # --- 案例 E（T-34）：六面全同且全 clip → 規則 2 死路 -----------------
            print("【E】materials=low 由規則 2（六面全同）觸發、geometry=medium "
                  "→ stderr 含規則 2 導引與 --override-material、不含 --override-dims")
            uniform_surf = _make_uniform_clip_surf()
            orig_stubs_e = _install_stubs(uniform_surf)
            orig_estimate_room_e = pipeline.estimate_room
            pipeline.estimate_room = _fake_estimate_room_medium
            stderr_buf_e = io.StringIO()
            try:
                with contextlib.redirect_stderr(stderr_buf_e):
                    rc = pipeline.run_photo(str(uniform_photo), no_viz=True)
            finally:
                _restore_stubs(*orig_stubs_e)
                pipeline.estimate_room = orig_estimate_room_e
            stderr_e = stderr_buf_e.getvalue()

            check(
                "exit code == 3（materials=low 由規則 2 觸發）",
                rc == 3,
                f"rc={rc}",
            )
            check(
                "stderr 含規則 2 導引文字",
                "六面材質被判成完全相同" in stderr_e,
                f"stderr={stderr_e!r}",
            )
            check(
                "stderr 含 --override-material 骨架",
                "--override-material floor=" in stderr_e,
                f"stderr={stderr_e!r}",
            )
            check(
                "stderr 不含 --override-dims（geometry=medium，不是 low）",
                "--override-dims" not in stderr_e,
                f"stderr={stderr_e!r}",
            )

            # --- 案例 F（T-34）：geometry=low → --override-dims 建議 ------------
            print("【F】geometry=low、materials=medium → stderr 含 --override-dims 建議")
            medium_surf_f = _make_surf("manual")
            orig_stubs_f = _install_stubs(medium_surf_f)
            orig_estimate_room_f = pipeline.estimate_room
            pipeline.estimate_room = _fake_estimate_room_low
            stderr_buf_f = io.StringIO()
            try:
                with contextlib.redirect_stderr(stderr_buf_f):
                    rc = pipeline.run_photo(str(low_geom_photo), no_viz=True)
            finally:
                _restore_stubs(*orig_stubs_f)
                pipeline.estimate_room = orig_estimate_room_f
            stderr_f = stderr_buf_f.getvalue()

            check(
                "exit code == 3（geometry=low → overall=low）",
                rc == 3,
                f"rc={rc}",
            )
            check(
                "stderr 含 --override-dims 建議（geometry=low 才是觸發原因）",
                "--override-dims" in stderr_f,
                f"stderr={stderr_f!r}",
            )
            check(
                "stderr 不含 --override-material（materials 不是 low，不該被建議）",
                "--override-material" not in stderr_f,
                f"stderr={stderr_f!r}",
            )
        finally:
            ir_synth.synthesize_ir = real_synthesize_ir
            for d in out_dirs:
                if d.exists():
                    shutil.rmtree(d)

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-26 低信心輸出 gate 測試全部通過")
    return 0


def _read_json(path: Path) -> dict:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    sys.exit(main())
