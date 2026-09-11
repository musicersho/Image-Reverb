#!/usr/bin/env python3
"""T-47：gate 校準複審量測（裁決 T-45-A 執行卡 2/5；量測卡，`src/` 零改動）。

跑法：`python scripts/t47_gate_calibration.py --out-dir output/gate_calibration/ --fresh`
（送審一律加 `--fresh`；13 張照片 ×2 模式，`role_aware=False`／`True` 各一次真實
CLI＋一次逐面判定明細，共 52 次真實模型推論，單張約 15–40 秒，總計約 20–30 分鐘）。

**為什麼**（卡片全文）：T-26 gate、裁決 T-28-A、裁決 T-36-A 的 BLOCK／pass 校準全
建立在「固定門檻 0.4＋全域 12 候選 softmax」；T-44 candidate 子集收窄後 softmax
濃縮，`bathroom_tiled` 越過門檻被放行且判錯、`bedroom.floor` 近失。裁決 T-36-A
規定重開 gate 議題需四樣證據——本卡就是產出那四樣證據（兩種模式各一份），交
Fable 下裁決 T-47-A。

**量測機制（兩條獨立真實資料來源，互相交叉驗證）**：
1. **真實 CLI**（`python -m src.image_reverb <photo> --force-low-confidence
   --no-viz [--role-aware]`）：拿 geometry_confidence／materials_confidence／
   overall confidence／gate／`surfaces`／`surfaces_sources`／`provenance`——這是
   使用者實際會看到的行為，且滿足前置「量測產物要走交易式輸出與 provenance」
   （T-42／T-43 落地後 `run_photo()` 的既有行為，本卡未改動任何一行）。
2. **逐面判定明細 harness**（唯讀重用 `t36_clip_accuracy.run_or_load()` /
   `t44_role_eval.run_or_load_role_aware()` / `eval_cache.py`，不重新實作）：
   CLI 的 `analysis.json` 不含逐面 top3／top-1 機率，證據②③⑤⑥需要這份明細，
   只能靠直接呼叫 `surfaces_from_preprocess()` 取得（與 CLI 呼叫同一段程式碼，
   同一張照片＋同一個 role_aware 值，理論上 `surfaces`／`surfaces_sources`
   必須逐位元相同——本卡對每一組跑完都程式化互相核對，不符即 🔴 卡關，不寫
   REPORT）。

**四樣證據（兩種模式 `role_aware=False`／`True` 各一份，13 張全量）**：
  ① 新基準率（13 張三軸 confidence＋gate）
  ② 被放行案例清單（每張 pass 的照片逐面材質 vs ground truth 正誤）
  ③ 其中 T-17 已知錯誤輸出佔比（已知錯誤清單＝鐵則 12）
  ④ 臥室續擋
  外加卡片明列的兩項延伸量測：
  ⑤ 信心膨脹量化（每面 top-1 機率兩模式位移、與 0.4 的距離、<0.05 清單，按角色分）
  ⑥ 門檻敏感度（表 7' 型，按角色、按模式各一張）
  ⑦ 兩種唯讀模擬（不改碼，只算不採用）：
     (a) 門檻隨候選數 n 調整（等效於全域 16 候選 softmax 的機率門檻）對 gate 的影響；
     (b) `compute_materials_confidence()` 規則 4 若加「候選集收窄的 clip 面不得
         直接 medium」對 gate 的影響。

⑤ 的交叉檢查：T-44 第四輪複驗紀錄（TASKS.md T-44 卡「⚠️ 帶到 T-44-R1 的殘留
精確度問題」段）點名 9 個 round11→round17 信心上升面，本卡的量測必須把這 9 面
當作膨脹幅度的量測輸入——程式化斷言這 9 個 (照片, 面) 必須出現在本卡算出的
信心位移表裡且方向一致（上升），不得只在文字裡點名 bedroom 而漏掉其餘 8 面。

**紅線**：`src/` 零 diff（含 gate 與門檻）；不得用舊快取（T-40 指紋，寫新目錄，
預設 `output/gate_calibration/`，是全新目錄，不重用任何 T-36／T-44／T-46 的舊
`runs/`）；不得只跑一種模式；REPORT 數字全由程式產生，不手打；⑦ 只計算不採用，
`compute_materials_confidence()`／`classify_region_material()`／gate 判定段／
門檻 0.4／`ROLE_MATERIAL_CANDIDATES` 全部只唯讀 import，一行不改。
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from src.image_reverb import surfaces as surfaces_mod  # noqa: E402  （唯讀引用）
from src.image_reverb import config  # noqa: E402  （唯讀引用）
from src.image_reverb.materials import SurfaceMaterials, SURFACE_NAMES  # noqa: E402  （唯讀引用）
from src.image_reverb.pipeline import _overall_confidence  # noqa: E402  （唯讀引用，gate rank 單一事實來源）

import eval_cache  # noqa: E402  （T-40，唯讀引用）
import t36_clip_accuracy as t36  # noqa: E402  （唯讀引用：GATE_ITEMS／EXPECTED_GATE／run_or_load）
import t44_role_eval as t44role  # noqa: E402  （唯讀引用：run_or_load_role_aware／build_threshold_sensitivity_per_role）
from t36_analysis import (  # noqa: E402  （唯讀引用，不重新實作計分邏輯）
    FACES,
    ROLE_OF_FACE,
    ROLE_ORDER,
    _md_table,
    _pct,
    build_accuracy_tables,
    build_error_type_tables,
)

DEFAULT_OUT_DIR = REPO_ROOT / "output" / "gate_calibration"
MODES = ("default", "role_aware")  # role_aware False / True

# 5 張「已知錯誤案例」照片（鐵則 12）：照抄自
# output/clip_treatment/rounds/round17/tables.md 表 4（地雷 #18 型 in-set 誤判明細），
# 與 scripts/t46_role_flag_baseline.py 的 KNOWN_ERROR_PHOTOS 同一份清單，不重新計算。
KNOWN_ERROR_PHOTOS = [
    "bathroom_tiled",
    "bedroom_ai_generated",
    "site_photo_gym",
    "site_photo_restaurant",
    "RacquetballCourt4",
]

# T-44 第四輪複驗紀錄（TASKS.md T-44 卡「⚠️ 帶到 T-44-R1 的殘留精確度問題」段）
# 點名的 9 個 round11→round17 信心上升面，逐字照抄（(photo, face, round11_conf,
# round17_conf)），供本卡 ⑤ 的交叉檢查斷言——本卡必須在自己算出的信心位移表裡
# 找到這 9 面且方向一致（上升），只用來核對，不當作本卡的量測輸入來源。
T44_ROUND4_NINE_FACES = [
    ("CathedralRoom", "ceiling", 0.5612, 0.7255),
    ("DivorceBeach", "floor", 0.4318, 0.5803),
    ("RacquetballCourt4", "ceiling", 0.3625, 0.5003),
    ("RacquetballCourt4", "floor", 0.5921, 0.7400),
    ("SteinmanHall", "ceiling", 0.6845, 0.8688),
    ("SteinmanHall", "floor", 0.2105, 0.3309),
    ("TunnelToHell", "floor", 0.3535, 0.6457),
    ("bedroom_ai_generated", "floor", 0.2436, 0.3394),
    ("site_photo_restaurant", "ceiling", 0.6606, 0.8947),
]

NEAR_THRESHOLD_BAND = 0.05  # 「距門檻 <0.05」的定義（卡片原文）

# 快取指紋要納入的 src 檔（CLI 實際會載入到的模組；比照 t46_role_flag_baseline.py）
FINGERPRINT_CODE_PATHS = [
    REPO_ROOT / "src" / "image_reverb" / "cli.py",
    REPO_ROOT / "src" / "image_reverb" / "config.py",
    REPO_ROOT / "src" / "image_reverb" / "pipeline.py",
    REPO_ROOT / "src" / "image_reverb" / "surfaces.py",
    REPO_ROOT / "src" / "image_reverb" / "geometry.py",
    REPO_ROOT / "src" / "image_reverb" / "preprocess.py",
]


# ------------------------------------------------------------------
# 共用小工具
# ------------------------------------------------------------------

def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _git_head(cwd: Path = REPO_ROOT) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def _porcelain(paths: list[str]) -> str:
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", *paths],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout
    return out if out.strip() else "（空，工作區乾淨）"


def _environment_string() -> str:
    try:
        import torch  # noqa: PLC0415

        torch_version = torch.__version__
    except Exception:
        torch_version = "n/a"
    return f"{platform.platform()}；python {sys.version.split()[0]}；torch {torch_version}"


def _code_fingerprint() -> dict:
    return {
        "repo_head": _git_head(),
        "code_sha256": {p.name: eval_cache.sha256_file(p) for p in FINGERPRINT_CODE_PATHS},
    }


def gate_of(analysis: dict) -> str:
    return "BLOCK" if analysis["confidence"] == "low" else "pass"


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


# ------------------------------------------------------------------
# 資料來源 1：真實 CLI（geometry／overall／gate／provenance 的單一事實來源）
# ------------------------------------------------------------------

def run_cli(
    photo: Path, name: str, mode_tag: str, role_aware: bool, runs_dir: Path, fresh: bool, code_fp: dict
) -> dict:
    dst = runs_dir / f"{name}__{mode_tag}"
    fingerprint = {"photo_sha256": eval_cache.sha256_file(photo), **code_fp}
    fp_path = dst / ".fingerprint.json"

    if dst.exists() and not fresh:
        aj_path = dst / "analysis.json"
        if aj_path.exists() and fp_path.exists() and json.loads(fp_path.read_text(encoding="utf-8")) == fingerprint:
            print(f"  ⏭️  [CLI] 快取命中：{_display_path(dst)}")
            return json.loads(aj_path.read_text(encoding="utf-8"))
        print(f"  ↻ [CLI] {name} ({mode_tag})：快取指紋不符或缺檔，重跑")

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
            f"{name} ({mode_tag}) [CLI] 失敗：exit={proc.returncode}\n"
            f"cmd={' '.join(cmd)}\n"
            f"--- stdout（末 40 行）---\n" + "\n".join(proc.stdout.splitlines()[-40:]) + "\n"
            f"--- stderr（末 40 行）---\n" + "\n".join(proc.stderr.splitlines()[-40:])
        )

    if dst.exists():
        shutil.rmtree(dst)
    runs_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_out), str(dst))
    fp_path.write_text(json.dumps(fingerprint, ensure_ascii=False, indent=2), encoding="utf-8")
    aj = json.loads((dst / "analysis.json").read_text(encoding="utf-8"))
    print(f"  ✅ [CLI] {name} ({mode_tag}) {elapsed:.1f}s")
    return aj


# ------------------------------------------------------------------
# 資料來源 2：逐面判定明細（唯讀重用 t36／t44 的 harness，不重新實作）
# ------------------------------------------------------------------

def get_detail(item: dict, role_aware: bool, runs_dir: Path, fresh: bool) -> dict:
    if role_aware:
        return t44role.run_or_load_role_aware(
            item, runs_dir=runs_dir, force_fresh=fresh, eval_mode="t47_gate_calibration:role_aware"
        )
    return t36.run_or_load(
        item, runs_dir=runs_dir, is_frozen=False, force_fresh=fresh, eval_mode="t47_gate_calibration:default"
    )


# ------------------------------------------------------------------
# ⑤ 候選數 n（讀 ROLE_MATERIAL_CANDIDATES／CLIP_OOD_PROMPTS 現行內容，不手打）
# ------------------------------------------------------------------

N_OOD = len(surfaces_mod.CLIP_OOD_PROMPTS)
N_GLOBAL = len(surfaces_mod.CLIP_MATERIAL_PROMPTS) + N_OOD  # 16


def candidate_count(role: str, role_aware: bool) -> int:
    if not role_aware:
        return N_GLOBAL
    return len(surfaces_mod.ROLE_MATERIAL_CANDIDATES[role]) + N_OOD


# ------------------------------------------------------------------
# ⑦(a) 唯讀模擬：門檻隨候選數 n 調整（等效於全域 16 候選 softmax 的機率門檻）
# ------------------------------------------------------------------

def effective_threshold(n: int) -> float:
    """把門檻依候選數縮放，維持「相對全域 16 候選 baseline（1/16）的倍率」不變：
    `threshold(n) = min(0.99, THRESHOLD * N_GLOBAL / n)`。n=N_GLOBAL 時＝原門檻
    （identity，wall 角色候選集未收窄，n 恆為 16，本模擬對 wall 是 no-op）。
    只是一種「等效門檻」的計算方式，不是唯一合理公式——供 Fable 參考，只算不採用。
    """
    return min(0.99, config.CLIP_CONFIDENCE_THRESHOLD * N_GLOBAL / n)


def simulate_method(face_detail: dict | None, threshold: float) -> str | None:
    """比照 `surfaces.classify_region_material()` 的判定順序（唯讀重讀 top3，
    不重跑 CLIP）：top-1 落在域外候選 → out_of_domain；top-1 機率 < threshold →
    fallback；否則 clip。"""
    if not face_detail or not face_detail.get("top3"):
        return None
    top1_id, _top1_conf = face_detail["top3"][0]
    if str(top1_id).startswith(surfaces_mod.OOD_PREFIX):
        return "out_of_domain"
    if face_detail["top3"][0][1] < threshold:
        return "fallback"
    return "clip"


def build_surface_from_sim(payload: dict, method_sim: dict[str, str]) -> SurfaceMaterials:
    """依模擬後的 method（clip/fallback/out_of_domain）重建一份 `SurfaceMaterials`：
    clip → 沿用該面 top-1 候選 id；fallback／out_of_domain → `config.DEFAULT_WALL_MATERIAL`
    （與 `classify_region_material()` 的 fallback 值同一個常數，唯讀讀取，不手打）。"""
    kwargs: dict[str, str] = {}
    sources: dict[str, str] = {}
    for name in SURFACE_NAMES:
        detail = payload["faces"].get(name)
        m = method_sim.get(name)
        if m is None or detail is None:
            continue
        top1_id = detail["top3"][0][0] if detail.get("top3") else None
        kwargs[name] = top1_id if m == "clip" else config.DEFAULT_WALL_MATERIAL
        sources[name] = m
    surf = SurfaceMaterials(**kwargs) if kwargs else SurfaceMaterials()
    surf.sources = sources
    surf.warnings = list(payload.get("warnings", []))
    return surf


def run_threshold_n_simulation(all_data: dict[str, dict], role_aware: bool, geometry_by_photo: dict[str, str]) -> list[dict]:
    rows = []
    for item in t36.GATE_ITEMS:
        name = item["name"]
        payload = all_data[name]
        method_sim: dict[str, str] = {}
        flips: list[str] = []
        for face in SURFACE_NAMES:
            detail = payload["faces"].get(face)
            if detail is None:
                continue
            real_method = payload["sources"].get(face)
            role = ROLE_OF_FACE[face]
            eff_th = effective_threshold(candidate_count(role, role_aware))
            sim_method = simulate_method(detail, eff_th)
            method_sim[face] = sim_method or real_method
            if sim_method and sim_method != real_method:
                flips.append(f"{face}（{real_method}→{sim_method}，eff_threshold={eff_th:.3f}）")

        surf_sim = build_surface_from_sim(payload, method_sim)
        # 唯讀呼叫現行 compute_materials_confidence()（規則 1～4 零改動），不重新
        # 實作評分邏輯——只有餵進去的 surf_sim（method 依模擬門檻重算）是模擬的。
        materials_sim = surfaces_mod.compute_materials_confidence(surf_sim)
        gate_sim = _overall_confidence(geometry_by_photo[name], materials_sim)
        rows.append({
            "photo": name, "flips": flips,
            "materials_sim": materials_sim, "gate_sim": gate_sim,
        })
    return rows


# ------------------------------------------------------------------
# ⑦(b) 唯讀模擬：compute_materials_confidence() 規則 4 加「候選集收窄的 clip 面
#      不得直接 medium」
# ------------------------------------------------------------------

def simulate_narrow_clip_downgrade(
    payload: dict, role_aware: bool, narrowed_roles: tuple[str, ...] = ("floor", "ceiling")
) -> str:
    surf = SurfaceMaterials(**payload["surfaces"])
    surf.sources = dict(payload["sources"])
    surf.warnings = list(payload.get("warnings", []))
    base = surfaces_mod.compute_materials_confidence(surf)  # 唯讀呼叫，規則 1～4 現行邏輯零改動
    if base != "medium" or not role_aware:
        return base  # 只有規則 4（catch-all→medium）的結果會被本模擬觸及
    for name in SURFACE_NAMES:
        if payload["sources"].get(name) == "clip" and ROLE_OF_FACE[name] in narrowed_roles:
            return "low（模擬：候選集收窄的 clip 面不得直接 medium）"
    return base


# ------------------------------------------------------------------
# 主流程
# ------------------------------------------------------------------

def main() -> int:
    argv = sys.argv[1:]
    out_dir, fresh = parse_args(argv)
    cli_runs_dir = out_dir / "cli_runs"
    detail_runs_dir = out_dir / "detail_runs"

    if not t36.GROUND_TRUTH_PATH.exists():
        print(f"🔴 卡關：找不到 {t36.GROUND_TRUTH_PATH}")
        return 1
    ground_truth = json.loads(t36.GROUND_TRUTH_PATH.read_text(encoding="utf-8"))
    gt_photos = ground_truth["photos"]

    code_fp = _code_fingerprint()

    cli_data: dict[str, dict[str, dict]] = {"default": {}, "role_aware": {}}
    detail_data: dict[str, dict[str, dict]] = {"default": {}, "role_aware": {}}
    mismatches: list[str] = []

    print(f"=== 兩模式 ×{len(t36.GATE_ITEMS)} 張：真實 CLI ＋ 逐面判定明細（跑或讀快取） ===")
    for item in t36.GATE_ITEMS:
        name = item["name"]
        photo = REPO_ROOT / item["photo"]
        print(f"[{name}]")
        for mode, role_aware in (("default", False), ("role_aware", True)):
            cli_a = run_cli(photo, name, mode, role_aware, cli_runs_dir, fresh, code_fp)
            detail = get_detail(item, role_aware, detail_runs_dir / mode, fresh)
            cli_data[mode][name] = cli_a
            detail_data[mode][name] = detail

            if cli_a.get("role_aware") is not role_aware:
                mismatches.append(f"{name}/{mode}：analysis.json.role_aware={cli_a.get('role_aware')!r}，應為 {role_aware!r}")
            if cli_a["surfaces"] != detail["surfaces"]:
                mismatches.append(f"{name}/{mode}：CLI surfaces != harness surfaces（兩條資料來源不一致）")
            if cli_a["surfaces_sources"] != detail["sources"]:
                mismatches.append(f"{name}/{mode}：CLI surfaces_sources != harness sources（兩條資料來源不一致）")

    if mismatches:
        print(f"\n❌ {len(mismatches)} 項交叉核對不成立，不寫 REPORT：")
        for m in mismatches:
            print(f"  🔴 {m}")
        return 1
    print("\n✅ 兩條資料來源（真實 CLI／harness）26 組 surfaces＋sources 逐位元相符。\n")

    # ---------------- ①新基準率 ----------------
    baseline_rows = []
    geometry_by_photo: dict[str, dict[str, str]] = {"default": {}, "role_aware": {}}
    gate_by_photo: dict[str, dict[str, str]] = {"default": {}, "role_aware": {}}
    for item in t36.GATE_ITEMS:
        name = item["name"]
        row = {"name": name}
        for mode in MODES:
            a = cli_data[mode][name]
            row[f"geometry_{mode}"] = a["geometry_confidence"]
            row[f"materials_{mode}"] = a["materials_confidence"]
            row[f"overall_{mode}"] = a["confidence"]
            row[f"gate_{mode}"] = gate_of(a)
            geometry_by_photo[mode][name] = a["geometry_confidence"]
            gate_by_photo[mode][name] = gate_of(a)
        baseline_rows.append(row)

    # ---------------- ②被放行案例清單（逐面 vs ground truth） ----------------
    pass_case_rows: dict[str, list[list[str]]] = {"default": [], "role_aware": []}
    accuracy_by_mode: dict[str, dict] = {}
    error_types_by_mode: dict[str, dict] = {}
    for mode in MODES:
        accuracy = build_accuracy_tables(t36.GATE_ITEMS, detail_data[mode], gt_photos)
        error_types = build_error_type_tables(t36.GATE_ITEMS, detail_data[mode], gt_photos, t36.OOD_PREFIX)
        accuracy_by_mode[mode] = accuracy
        error_types_by_mode[mode] = error_types
        for r in accuracy["rows"]:
            if gate_by_photo[mode][r["photo"]] != "pass":
                continue
            pass_case_rows[mode].append([
                r["photo"], r["face"], r["ai"], r["source"], r["gt"],
                "—" if r["excluded"] else ("✓" if r["correct"] else "✗"),
            ])

    # ---------------- ③已知錯誤案例在 pass 案例裡的佔比 ----------------
    known_error_gate: dict[str, dict[str, str]] = {"default": {}, "role_aware": {}}
    for mode in MODES:
        for name in KNOWN_ERROR_PHOTOS:
            known_error_gate[mode][name] = gate_by_photo[mode][name]

    in_set_error_in_pass: dict[str, int] = {}
    scored_faces_in_pass: dict[str, int] = {}
    for mode in MODES:
        pass_names = {name for name in gate_by_photo[mode] if gate_by_photo[mode][name] == "pass"}
        in_set_errors = error_types_by_mode[mode]["in_set_errors"]
        in_set_error_in_pass[mode] = sum(1 for r in in_set_errors if r["photo"] in pass_names)
        scored_faces_in_pass[mode] = sum(
            1 for r in accuracy_by_mode[mode]["rows"]
            if r["photo"] in pass_names and not r["excluded"]
        )

    # ---------------- ④臥室續擋 ----------------
    bedroom_rows = []
    for mode in MODES:
        a = cli_data[mode]["bedroom_ai_generated"]
        floor_detail = detail_data[mode]["bedroom_ai_generated"]["faces"].get("floor")
        floor_conf = floor_detail["top3"][0][1] if floor_detail and floor_detail.get("top3") else None
        bedroom_rows.append([
            mode, a["geometry_confidence"], a["materials_confidence"], a["confidence"],
            gate_of(a), f"{floor_conf:.4f}" if floor_conf is not None else "n/a",
        ])

    # ---------------- ⑤信心膨脹量化 ----------------
    shift_rows = []
    nine_face_hits: dict[tuple[str, str], dict] = {}
    for item in t36.GATE_ITEMS:
        name = item["name"]
        for face in FACES:
            d_default = detail_data["default"][name]["faces"].get(face)
            d_role = detail_data["role_aware"][name]["faces"].get(face)
            if not d_default or not d_default.get("top3") or not d_role or not d_role.get("top3"):
                continue
            c_default = d_default["top3"][0][1]
            c_role = d_role["top3"][0][1]
            delta = c_role - c_default
            role = ROLE_OF_FACE[face]
            row = {
                "photo": name, "face": face, "role": role,
                "method_default": d_default.get("method"), "conf_default": c_default,
                "method_role": d_role.get("method"), "conf_role": c_role,
                "delta": delta,
                "dist_default": abs(c_default - config.CLIP_CONFIDENCE_THRESHOLD),
                "dist_role": abs(c_role - config.CLIP_CONFIDENCE_THRESHOLD),
            }
            shift_rows.append(row)
            key = (name, face)
            if key in {(p, f) for p, f, *_ in T44_ROUND4_NINE_FACES}:
                nine_face_hits[key] = row

    near_threshold_rows = [
        r for r in shift_rows if r["dist_default"] < NEAR_THRESHOLD_BAND or r["dist_role"] < NEAR_THRESHOLD_BAND
    ]

    nine_face_check_lines = []
    all_nine_present = True
    for photo, face, hist_default, hist_role in T44_ROUND4_NINE_FACES:
        key = (photo, face)
        row = nine_face_hits.get(key)
        if row is None:
            all_nine_present = False
            nine_face_check_lines.append(f"🔴 {photo}.{face}：本卡資料裡找不到這一面（缺 top3 明細）")
            continue
        direction_ok = row["delta"] > 0
        if not direction_ok:
            all_nine_present = False
        exact_match = (
            abs(row["conf_default"] - hist_default) < 1e-6 and abs(row["conf_role"] - hist_role) < 1e-6
        )
        nine_face_check_lines.append(
            f"{'✅' if direction_ok else '🔴'} {photo}.{face}：T-44 第四輪記錄 {hist_default:.4f}→{hist_role:.4f}"
            f"（上升）；本卡本次重測 {row['conf_default']:.4f}→{row['conf_role']:.4f}"
            f"（{'上升' if direction_ok else '未上升，異常'}，"
            f"{'與歷史記錄數值逐位元相同' if exact_match else '數值與歷史記錄不同（模型/環境差異，方向仍需一致）'}）"
        )
    n_nine_faces = len(T44_ROUND4_NINE_FACES)
    n_nine_faces_ok = sum(1 for line in nine_face_check_lines if line.startswith("✅"))
    if not all_nine_present:
        print(f"\n❌ T-44 第四輪 {n_nine_faces} 面信心上升交叉檢查未全部通過，不寫 REPORT：")
        for line in nine_face_check_lines:
            print(f"  {line}")
        return 1
    print(
        f"\n✅ T-44 第四輪信心上升交叉檢查全部通過"
        f"（{n_nine_faces_ok}/{n_nine_faces} 在本卡量測資料中出現且方向一致）。\n"
    )

    # ---------------- ⑥門檻敏感度（按角色、按模式） ----------------
    sensitivity_by_mode = {
        mode: t44role.build_threshold_sensitivity_per_role(
            t36.GATE_ITEMS, detail_data[mode], gt_photos, t36.OOD_PREFIX, t36.THRESHOLD
        )
        for mode in MODES
    }

    # ---------------- ⑦(a)(b) 唯讀模擬 ----------------
    sim_a_rows = {
        mode: run_threshold_n_simulation(detail_data[mode], mode == "role_aware", geometry_by_photo[mode])
        for mode in MODES
    }
    sim_b_rows = {
        mode: [
            {
                "photo": name,
                "materials_real": cli_data[mode][name]["materials_confidence"],
                "materials_sim": simulate_narrow_clip_downgrade(detail_data[mode][name], mode == "role_aware"),
            }
            for name in detail_data[mode]
        ]
        for mode in MODES
    }

    # ---------------- 寫 tables.md / REPORT.md ----------------
    out_dir.mkdir(parents=True, exist_ok=True)
    tables_md = build_tables_md(
        baseline_rows=baseline_rows, pass_case_rows=pass_case_rows,
        known_error_gate=known_error_gate, bedroom_rows=bedroom_rows,
        shift_rows=shift_rows, near_threshold_rows=near_threshold_rows,
        nine_face_check_lines=nine_face_check_lines, sensitivity_by_mode=sensitivity_by_mode,
        sim_a_rows=sim_a_rows, sim_b_rows=sim_b_rows, n_photos=len(t36.GATE_ITEMS),
    )
    (out_dir / "tables.md").write_text(tables_md, encoding="utf-8")

    report_md = build_report_md(
        out_dir=out_dir, fresh=fresh, code_fp=code_fp,
        accuracy_by_mode=accuracy_by_mode, error_types_by_mode=error_types_by_mode,
        in_set_error_in_pass=in_set_error_in_pass, scored_faces_in_pass=scored_faces_in_pass,
        pass_case_rows=pass_case_rows, known_error_gate=known_error_gate,
        n_nine_faces=n_nine_faces, n_nine_faces_ok=n_nine_faces_ok,
        n_photos=len(t36.GATE_ITEMS),
    )
    (out_dir / "REPORT.md").write_text(report_md, encoding="utf-8")

    print(f"✅ 完成。REPORT：{out_dir / 'REPORT.md'}；表格：{out_dir / 'tables.md'}")
    return 0


def build_tables_md(
    *, baseline_rows, pass_case_rows, known_error_gate, bedroom_rows, shift_rows,
    near_threshold_rows, nine_face_check_lines, sensitivity_by_mode, sim_a_rows, sim_b_rows,
    n_photos,
) -> str:
    parts = []

    parts.append(f"## 表 1（證據①）：{n_photos} 張照片新基準率（`role_aware=False` vs `True`）\n")
    parts.append(_md_table(
        ["照片", "geometry（default）", "materials（default）", "overall（default）", "gate（default）",
         "geometry（role_aware）", "materials（role_aware）", "overall（role_aware）", "gate（role_aware）"],
        [[r["name"], r["geometry_default"], r["materials_default"], r["overall_default"], r["gate_default"],
          r["geometry_role_aware"], r["materials_role_aware"], r["overall_role_aware"], r["gate_role_aware"]]
         for r in baseline_rows],
    ))

    for mode in MODES:
        parts.append(f"\n\n## 表 2（證據②）：`{mode}` 模式被放行（gate=pass）案例逐面 vs ground truth\n")
        if pass_case_rows[mode]:
            parts.append(_md_table(
                ["照片", "面", "AI 判定", "來源", "ground truth", "是否正確"], pass_case_rows[mode],
            ))
        else:
            parts.append(f"（本模式下 {n_photos} 張全數 BLOCK，無 pass 案例）")

    parts.append("\n\n## 表 3（證據③）：已知錯誤案例（鐵則 12）在兩模式的 gate 結果\n")
    parts.append(_md_table(
        ["照片", "gate（default）", "gate（role_aware）"],
        [[name, known_error_gate["default"][name], known_error_gate["role_aware"][name]] for name in KNOWN_ERROR_PHOTOS],
    ))

    parts.append("\n\n## 表 4（證據④）：`bedroom_ai_generated` 續擋檢查\n")
    parts.append(_md_table(
        ["模式", "geometry", "materials", "overall", "gate", "floor top-1 機率"], bedroom_rows,
    ))

    parts.append(f"\n\n## 表 5（證據⑤）：每面 top-1 機率兩模式位移（{len(shift_rows)} 面全量，按角色排序）\n")
    sorted_shift = sorted(shift_rows, key=lambda r: (ROLE_ORDER.index(r["role"]), r["photo"], r["face"]))
    parts.append(_md_table(
        ["角色", "照片", "面", "method（default）", "conf（default）", "method（role_aware）",
         "conf（role_aware）", "位移 Δ", "距門檻 0.4（default）", "距門檻 0.4（role_aware）"],
        [[r["role"], r["photo"], r["face"], r["method_default"], f"{r['conf_default']:.4f}",
          r["method_role"], f"{r['conf_role']:.4f}", f"{r['delta']:+.4f}",
          f"{r['dist_default']:.4f}", f"{r['dist_role']:.4f}"] for r in sorted_shift],
    ))

    parts.append(f"\n\n### 距門檻 <{NEAR_THRESHOLD_BAND} 的面清單（按角色分）\n")
    for role in ROLE_ORDER:
        role_rows = [r for r in near_threshold_rows if r["role"] == role]
        parts.append(f"\n**{role}**\n")
        if role_rows:
            parts.append(_md_table(
                ["照片", "面", "conf（default）", "conf（role_aware）", "距門檻（default）", "距門檻（role_aware）"],
                [[r["photo"], r["face"], f"{r['conf_default']:.4f}", f"{r['conf_role']:.4f}",
                  f"{r['dist_default']:.4f}", f"{r['dist_role']:.4f}"] for r in role_rows],
            ))
        else:
            parts.append("（無）")

    parts.append("\n\n### T-44 第四輪 9 面信心上升交叉檢查（程式化核對，非手打）\n")
    parts.append("\n".join(f"- {line}" for line in nine_face_check_lines))

    for mode in MODES:
        parts.append(f"\n\n## 表 6（證據⑥）：`{mode}` 模式 fallback 門檻（{config.CLIP_CONFIDENCE_THRESHOLD}）敏感度分析——按角色分開\n")
        for role in ROLE_ORDER:
            s = sensitivity_by_mode[mode][role]
            parts.append(f"\n### {role}\n")
            parts.append(_md_table(
                ["候選門檻", "會被放行到 clip 的面數", "放行後答對", "放行後答錯"],
                [[f"{r['threshold']:.2f}", str(r["would_flip_to_clip"]), str(r["would_be_correct"]), str(r["would_be_wrong"])]
                 for r in s["sweep"]],
            ))

    parts.append(
        "\n\n## 表 7（證據⑦a，唯讀模擬，只算不採用）：門檻依候選數 n 調整"
        f"（`threshold(n)=min(0.99, {config.CLIP_CONFIDENCE_THRESHOLD}×{N_GLOBAL}/n)`）對 gate 的影響\n\n"
        "⚠️ 已知近似：`materials_sim` 是唯讀呼叫現行 `compute_materials_confidence()` 算出（規則 "
        "1～4 零改動），但餵進去的 `warnings` 沿用**該面實際那次真跑**留下的警示文字，未依模擬後的 "
        "method 重新產生——如果某面實際是 fallback／out_of_domain（有警示字串）而本模擬把它翻成 "
        "clip，規則 3「全 clip 且無 warnings→high」仍可能因為殘留的警示字串而判不到 `high`（偏保守，"
        "不影響 `low` 的判定，`low`／`gate` 才是本卡的量測重點）。\n"
    )
    for mode in MODES:
        parts.append(f"\n### `{mode}` 模式\n")
        rows = sim_a_rows[mode]
        parts.append(_md_table(
            ["照片", "會翻轉的面（method 變化＋等效門檻）", "模擬 materials", "模擬 gate"],
            [[r["photo"], "；".join(r["flips"]) if r["flips"] else "（無）", r["materials_sim"], r["gate_sim"]] for r in rows],
        ))

    parts.append(
        "\n\n## 表 8（證據⑦b，唯讀模擬，只算不採用）："
        "`compute_materials_confidence()` 規則 4 加「候選集收窄的 clip 面不得直接 medium」對 gate 的影響\n"
    )
    for mode in MODES:
        parts.append(f"\n### `{mode}` 模式\n")
        rows = sim_b_rows[mode]
        parts.append(_md_table(
            ["照片", "實際 materials_confidence", "模擬 materials_confidence"],
            [[r["photo"], r["materials_real"], r["materials_sim"]] for r in rows],
        ))

    return "\n".join(parts) + "\n"


def build_report_md(
    *, out_dir, fresh, code_fp, accuracy_by_mode, error_types_by_mode,
    in_set_error_in_pass, scored_faces_in_pass, pass_case_rows, known_error_gate,
    n_nine_faces, n_nine_faces_ok, n_photos,
) -> str:
    hard_table = _md_table(
        ["硬（欄位）", "值"],
        [
            ["跑法", "`--fresh`（零快取，全新目錄）" if fresh else "非 `--fresh`（含快取結果，送審請重跑 `--fresh`）"],
            ["out_dir", _display_path(out_dir)],
            ["照片張數（`t36.GATE_ITEMS`）", str(n_photos)],
        ],
    )
    porcelain_value = _porcelain(["src", "scripts", "data"])
    porcelain_clean = porcelain_value.startswith("（空")
    provenance_table = _md_table(
        ["provenance（只記錄，不比對）", "值"],
        [
            ["主 repo HEAD（產生本報告時）", f"`{_git_head()}`"],
            ["git status --porcelain -- src scripts data", "見下方"],
            ["產生時間（UTC）", datetime.now(timezone.utc).isoformat()],
            ["環境", _environment_string()],
            ["code_fingerprint.repo_head（跑 CLI 當下）", f"`{code_fp['repo_head']}`"],
        ],
    )
    porcelain_block = (
        f"`git status --porcelain -- src scripts data`：\n```\n{porcelain_value}\n```\n"
        if not porcelain_clean
        else f"`git status --porcelain -- src scripts data`：{porcelain_value}\n"
    )
    if not porcelain_clean:
        porcelain_block += (
            "\n⚠️ 執行者本次跑的當下工作區有未 commit 變更，不因此視為斷言失敗；"
            "Opus 複驗那次應為空（同 T-42／T-43／T-49 既有慣例）。\n"
        )

    known_error_pass_default = sum(1 for g in known_error_gate["default"].values() if g == "pass")
    known_error_pass_role = sum(1 for g in known_error_gate["role_aware"].values() if g == "pass")

    lines = []
    lines.append("# T-47 REPORT — gate 校準複審量測（裁決 T-45-A 執行卡 2/5）\n")
    lines.append("## 硬（欄位）\n\n" + hard_table + "\n")
    lines.append("## Provenance（只記錄、不比對）\n\n" + provenance_table + "\n\n" + porcelain_block + "\n")
    lines.append(
        f"本報告由 `scripts/t47_gate_calibration.py` 對 {n_photos} 張照片各跑一次真實 CLI"
        "（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，"
        "預設模式與加 `--role-aware` 各一次）＋一次逐面判定明細 harness（唯讀重用 "
        "`t36_clip_accuracy.py`／`t44_role_eval.py`／`eval_cache.py`），兩條資料來源的 "
        "`surfaces`／`surfaces_sources` 已程式化核對逐位元相符。詳表見 [tables.md](tables.md)。\n\n"
    )
    lines.append("## 四樣證據摘要\n\n")
    lines.append(
        f"① **新基準率**：見 tables.md 表 1（{n_photos} 張×2 模式的三軸 confidence＋gate）。\n\n"
        f"② **被放行案例清單**：`default` 模式 {len(pass_case_rows['default'])} 面來自 pass 案例、"
        f"`role_aware` 模式 {len(pass_case_rows['role_aware'])} 面來自 pass 案例，逐面 vs ground truth "
        "見 tables.md 表 2。\n\n"
        f"③ **T-17 已知錯誤（鐵則 12）輸出佔比**：5 張已知錯誤案例中，`default` 模式 "
        f"{known_error_pass_default}/5 張為 pass、`role_aware` 模式 {known_error_pass_role}/5 張為 pass"
        "（見 tables.md 表 3）；pass 案例裡的 in-set 誤判面數／pass 案例總評分面數："
        f"`default` {in_set_error_in_pass['default']}/{scored_faces_in_pass['default'] or 0}、"
        f"`role_aware` {in_set_error_in_pass['role_aware']}/{scored_faces_in_pass['role_aware'] or 0}。\n\n"
        f"④ **臥室續擋**：`bedroom_ai_generated` 在 `default`／`role_aware` 兩模式 gate 皆為 "
        f"`{known_error_gate['default']['bedroom_ai_generated']}`／`{known_error_gate['role_aware']['bedroom_ai_generated']}`"
        "（見 tables.md 表 4，含 floor 面 top-1 機率與 0.4 門檻的距離）。\n\n"
    )
    lines.append(
        "## 延伸量測（卡片明列）\n\n"
        "⑤ 每面 top-1 機率兩模式位移、與 0.4 門檻的距離、<0.05 清單按角色分——見 tables.md 表 5，"
        f"含 T-44 第四輪記錄的 {n_nine_faces} 面信心上升交叉檢查"
        f"（程式化核對，{n_nine_faces_ok}/{n_nine_faces} 通過）。\n\n"
        "⑥ 門檻敏感度（表 7' 型）按角色、按模式各一張——見 tables.md 表 6。\n\n"
        "⑦ 兩種唯讀模擬（只算不採用，`compute_materials_confidence()`／gate 判定段／門檻 0.4 零改動）：\n"
        "  (a) 門檻依候選數 n 調整（等效全域 16 候選 softmax 的機率門檻）對 gate 的影響——見 tables.md 表 7；\n"
        "  (b) `compute_materials_confidence()` 規則 4 加「候選集收窄的 clip 面不得直接 medium」對 gate 的影響"
        "——見 tables.md 表 8。\n\n"
    )
    lines.append(
        "## ⚠️ 本卡不下結論（範圍紅線）\n\n"
        "本卡只產出四樣證據與兩項延伸量測供 Fable 下裁決 T-47-A，**不對「該不該調整門檻／候選集"
        "分區表」下任何建議或結論**；⑦ 的兩個模擬公式僅供參考，未經採用，`src/` 全程零改動。\n"
    )
    return "".join(lines)


if __name__ == "__main__":
    sys.exit(main())
