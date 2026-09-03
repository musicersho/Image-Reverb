#!/usr/bin/env python3
"""T-46 介面測試：`role_aware` feature flag 接線（裁決 T-45-A 執行卡 1/5）。

背景：T-44（round17）把 `pipeline.run_photo()` 對 `surfaces_from_preprocess()`
的唯一呼叫點寫死成 `role_aware=True`。裁決 T-45-A（2026-09-03）認定 T-44 的
產品採用門檻只有相對改善、未含絕對安全下限（`bathroom_tiled` 已知錯誤放行），
產品採用暫停，`role_aware` 改回預設 `False`，研究路徑保留在 CLI `--role-aware`
旗標（`config.ROLE_AWARE_MATERIALS_DEFAULT` 是單一事實來源）。

本測試只驗證接線本身（會不會被改回硬編碼 True），不重跑 T-44/round17 的材質
準確度量測——那些數字已經在 `output/clip_treatment/REPORT_T44.md` 與
`test_t44_role_partition.py`（分區表、`role=None` 不變量）驗證過，不是本卡
範圍。

分四部分：
  0. CLI 參數接線（subprocess，不跑模型）：`--role-aware` 存在，且跟其他
     照片限定旗標一樣被 `check_mutual_exclusion` 之後的檢查擋下（非照片輸入
     搭配使用 → exit 2）。
  A. 不傳 `role_aware`（預設路徑）→ `surfaces_from_preprocess()` 實際收到的
     kwargs 是 `role_aware=False`（即 `config.ROLE_AWARE_MATERIALS_DEFAULT`）。
  B. 明確傳 `role_aware=True` → `surfaces_from_preprocess()` 收到
     `role_aware=True`（旗標路徑沒壞）。
  C. `analysis.json` 的 `"role_aware"` 欄位與呼叫時傳入的值逐值相符
     （A/B 兩種模式各跑一次，overall confidence 給 medium 以免被 T-26 gate
     擋下、無法產生檔案可讀）。

診斷力（自我檢查要求）：對 git worktree 的 HEAD 舊碼（5520b83 之後、本卡之前，
`surfaces_from_preprocess(summary, role_aware=True)` 是寫死的）實測，本測試
案例 A 必須 fail（舊碼預設路徑錄到 `role_aware=True`，不是 `False`）。

跑法：`python scripts/test_t46_role_flag.py`；全部通過 exit 0，任一失敗 exit 1。
會在 `output/` 底下建立／清除 `_test_t46_role_flag_*` 兩個暫存資料夾，不影響
任何既有交付檔案。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb import config  # noqa: E402
from src.image_reverb import pipeline  # noqa: E402
from src.image_reverb import preprocess as preprocess_mod  # noqa: E402
from src.image_reverb import surfaces as surfaces_mod  # noqa: E402
from src.image_reverb.materials import SURFACE_NAMES, SurfaceMaterials  # noqa: E402

PROJECT_ROOT = config.PROJECT_ROOT
OUTPUT_ROOT = PROJECT_ROOT / "output"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


# 六面材質互不相同、來源全是 'manual'（與 test_output_gate.py 案例 C 同一手法）：
# 不觸發 fallback/退化規則，materials_confidence 落在 medium，不會被 T-26 gate 擋下。
_DISTINCT = dict(
    floor="carpet", ceiling="gypsum_board", west="brick",
    east="concrete", south="wood_panel", north="glass",
)


def _make_medium_surf() -> SurfaceMaterials:
    surf = SurfaceMaterials(**_DISTINCT)
    for name in SURFACE_NAMES:
        surf.sources[name] = "manual"
    return surf


def _install_stubs(surf: SurfaceMaterials, recorded_kwargs: dict):
    """樁掉 preprocess_image（回傳最小 summary）與 surfaces_from_preprocess
    （直接回傳指定好的 surf，並把收到的 kwargs 錄進 recorded_kwargs），兩者都是
    `run_photo()` 裡的區域 import，換掉來源模組的屬性即可生效。
    """

    def fake_preprocess_image(path, output_dir=None):
        # is_equirect=True 跳過非環景才會走的 CLIP 場景線索那段，不連帶下載模型。
        return {"is_equirect": True}

    def fake_surfaces_from_preprocess(preprocess_summary, threshold=None, role_aware=False):
        recorded_kwargs["role_aware"] = role_aware
        return surf, {}

    orig_preprocess = preprocess_mod.preprocess_image
    orig_surfaces = surfaces_mod.surfaces_from_preprocess
    preprocess_mod.preprocess_image = fake_preprocess_image
    surfaces_mod.surfaces_from_preprocess = fake_surfaces_from_preprocess
    return orig_preprocess, orig_surfaces


def _restore_stubs(orig_preprocess, orig_surfaces) -> None:
    preprocess_mod.preprocess_image = orig_preprocess
    surfaces_mod.surfaces_from_preprocess = orig_surfaces


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _check_cli_wiring() -> None:
    print("【0】CLI 參數接線（subprocess，不跑模型）")
    proc = subprocess.run(
        [sys.executable, "-m", "src.image_reverb", "--text", "測試", "--role-aware"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    check(
        "--role-aware 搭配 --text 用（非照片輸入）→ exit 2",
        proc.returncode == 2,
        f"returncode={proc.returncode}",
    )
    check(
        "錯誤訊息有點名 --role-aware",
        "--role-aware" in proc.stderr,
        f"stderr={proc.stderr.strip()!r}",
    )

    proc_help = subprocess.run(
        [sys.executable, "-m", "src.image_reverb", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    check(
        "--help 有列出 --role-aware 且標明實驗性／產品採用暫停",
        "--role-aware" in proc_help.stdout and "裁決 T-45-A" in proc_help.stdout,
        f"stdout={proc_help.stdout!r}",
    )


def main() -> int:
    _check_cli_wiring()

    with tempfile.TemporaryDirectory() as tmp:
        default_photo = Path(tmp) / "_test_t46_role_flag_default.png"
        role_aware_photo = Path(tmp) / "_test_t46_role_flag_on.png"
        for p in (default_photo, role_aware_photo):
            p.write_bytes(b"")

        out_dirs = [OUTPUT_ROOT / p.stem for p in (default_photo, role_aware_photo)]
        for d in out_dirs:
            if d.exists():
                shutil.rmtree(d)

        try:
            # --- 案例 A：不傳 role_aware（預設路徑） -------------------------
            print("【A】run_photo() 不傳 role_aware → 預設值")
            surf = _make_medium_surf()
            recorded: dict = {}
            orig = _install_stubs(surf, recorded)
            try:
                rc = pipeline.run_photo(str(default_photo), override_dims="4x3x2.5", no_viz=True)
            finally:
                _restore_stubs(*orig)

            check("exit code == 0（medium 不受 gate 影響）", rc == 0, f"rc={rc}")
            check(
                "surfaces_from_preprocess() 實際收到 role_aware=False",
                recorded.get("role_aware") is False,
                f"recorded={recorded!r}",
            )
            check(
                "config.ROLE_AWARE_MATERIALS_DEFAULT 本身也是 False（單一事實來源）",
                config.ROLE_AWARE_MATERIALS_DEFAULT is False,
                f"ROLE_AWARE_MATERIALS_DEFAULT={config.ROLE_AWARE_MATERIALS_DEFAULT!r}",
            )
            analysis_a = _read_json(OUTPUT_ROOT / default_photo.stem / "analysis.json")
            check(
                "analysis.json: role_aware == false",
                analysis_a.get("role_aware") is False,
                f"role_aware={analysis_a.get('role_aware')!r}",
            )

            # --- 案例 B：明確傳 role_aware=True ------------------------------
            print("【B】run_photo(role_aware=True) → 旗標路徑沒壞")
            recorded_b: dict = {}
            orig = _install_stubs(surf, recorded_b)
            try:
                rc = pipeline.run_photo(
                    str(role_aware_photo), override_dims="4x3x2.5", no_viz=True, role_aware=True
                )
            finally:
                _restore_stubs(*orig)

            check("exit code == 0", rc == 0, f"rc={rc}")
            check(
                "surfaces_from_preprocess() 實際收到 role_aware=True",
                recorded_b.get("role_aware") is True,
                f"recorded={recorded_b!r}",
            )
            analysis_b = _read_json(OUTPUT_ROOT / role_aware_photo.stem / "analysis.json")
            check(
                "analysis.json: role_aware == true",
                analysis_b.get("role_aware") is True,
                f"role_aware={analysis_b.get('role_aware')!r}",
            )
        finally:
            for d in out_dirs:
                if d.exists():
                    shutil.rmtree(d)

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-46 role_aware feature flag 接線測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
