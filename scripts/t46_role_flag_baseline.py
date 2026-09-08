#!/usr/bin/env python3
"""T-46 步驟 4（依 criteria v2，`output/role_flag/CRITERIA_T46_v2.md`，
執行者不得改該檔一字）：13 張照片基準率變化表（鐵則 8；裁決 T-45-A 執行卡 1/5 收尾）。

背景：T-46 把 `pipeline.run_photo()` 的 `role_aware` 開關從硬編碼 `True`
改回 `config.ROLE_AWARE_MATERIALS_DEFAULT`（`False`），CLI 新增 `--role-aware`
保留 T-44 的研究路徑。本腳本用**真實 CLI**（`python -m src.image_reverb ...`，
含真實幾何模型／分割模型／CLIP，不打樁）對 13 張照片各跑「預設」與
`--role-aware` 兩種模式，並用 `git worktree` 重建 commit `23f2aba`
（role_aware 尚未預設啟用的最後狀態；是 T-44 系列中間 commit、不是 T-44
之前，見 criteria v2 §2.1）的真實 CLI 結果作為基線 B0，程式化驗證
（criteria v2 §2.2／§2.3）：

  1. **預設模式（斷言 A1～A7）**：`analysis.json.role_aware == false`；
     `geometry_confidence`／`materials_confidence`／`confidence`（overall）／
     gate（`confidence == "low"` → BLOCK，否則 pass）／六面材質＋來源逐張與
     B0 相同；`bathroom_tiled`／`bedroom_ai_generated` 與鐵則 12 五張已知
     錯誤案例（`KNOWN_ERROR_PHOTOS`）預設全部 BLOCK。
  2. **`--role-aware` 模式（硬性斷言只有 B1／B2）**：`analysis.json.role_aware
     == true`；六面材質＋來源與 `output/clip_treatment/rounds/round17`
     （T-44 最終輪，曾經是 `pipeline.py` 硬編碼的狀態）逐張相同。`B3`
     （`geometry_confidence`／`confidence`／gate）**只報告不斷言**（round17
     同樣沒有 confidence 欄，無可執行基線，交 T-47／T-44-R1）；`B4`（鐵則 12
     五張在此模式的 gate）**只列不判**（`bathroom_tiled` 在此模式 BLOCK→pass
     是 T-44 已記錄的已知錯誤放行，處置屬 T-44-R1）。

`EXPECTED_GATE`（T-28-A／T-36 凍結表）只用於 B0 自證守門（B0 的六面材質＋
來源須等於 round11、`materials_confidence` 須等於其 materials 欄，任一不同
＝🔴 停回 Fable，見 criteria v2 §2.1）；**geometry 欄不作為本卡任何斷言**
（criteria v2 §2.4：`TunnelToHell` 在 `23f2aba` 也是 `geometry=low`，表列
`medium` 是表過期，不是 T-46 的回歸，改表交 T-47／裁決 T-47-A）。

13 張照片清單、`EXPECTED_GATE` 唯讀 import 自 `t36_clip_accuracy.py`，不重打。
round11／round17 的逐面判定明細（`surfaces`／`sources`）唯讀讀取兩輪各自
`runs/<name>/detail.json` 快取（已用真實 `surfaces_from_preprocess()` 算過，
不需要也不應該重新用打樁重算）。

`src/` 全程只讀不寫，只透過 `python -m src.image_reverb` 這個既有 CLI 入口跑
（含 B0 的 `git worktree`），不 import／不打樁任何 `src.image_reverb` 內部函式。

跑法：`python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/ --fresh`
（送審一律加 `--fresh`，含 B0 重建，13 張 B0＋13×2 兩模式＝39 次真實 CLI，
單張約 15–40 秒）。不加 `--fresh` 時走快取：預設模式／`--role-aware` 兩模式的
快取指紋含主 repo HEAD＋`src/image_reverb/{cli,config,pipeline,surfaces,
geometry,preprocess}.py` 內容 sha256＋照片 sha256，指紋不符即視為快取失效、
自動重跑（`scripts/eval_cache.py` 的 `sha256_file` 手法，本檔不重新實作雜湊
邏輯）；B0（`git worktree` 於固定 commit `23f2aba`）的快取指紋只需照片
sha256（該 commit 的程式碼固定不變）。

輸出：`<out_dir>/REPORT.md`、`<out_dir>/tables.md`（表格程式產生，地雷 #15）、
`<out_dir>/baseline_23f2aba/{BASELINE.md,runs/<name>/analysis.json}`
（B0 的持久證據，`BASELINE.md` 進 git）、`<out_dir>/runs/<name>__{default,
role_aware}/`（每個 run 的完整輸出快照）。任一斷言不成立 exit 非 0，且不寫
REPORT／tables／BASELINE.md（半成品比沒有更危險）。
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import t36_clip_accuracy as t36  # noqa: E402  （唯讀引用：GATE_ITEMS／EXPECTED_GATE）
from t36_analysis import _md_table  # noqa: E402  （唯讀引用，不重新實作表格排版）
from eval_cache import sha256_file  # noqa: E402  （唯讀引用，不重新實作雜湊邏輯）

DEFAULT_OUT_DIR = REPO_ROOT / "output" / "role_flag"
ROUND11_RUNS = REPO_ROOT / "output" / "clip_treatment" / "rounds" / "round11_remap_baseline" / "runs"
ROUND17_RUNS = REPO_ROOT / "output" / "clip_treatment" / "rounds" / "round17" / "runs"

# criteria v2 §2.1：預設路徑基線 B0＝role_aware 尚未預設啟用的最後狀態
# （T-44 系列中間 commit，不是 T-44 之前——正確描述見 criteria v2 §2.1）。
B0_COMMIT = "23f2aba"

# criteria v2 §2.5.2：快取指紋要納入的 src 檔（CLI 實際會載入到的模組）。
FINGERPRINT_CODE_PATHS = [
    REPO_ROOT / "src" / "image_reverb" / "cli.py",
    REPO_ROOT / "src" / "image_reverb" / "config.py",
    REPO_ROOT / "src" / "image_reverb" / "pipeline.py",
    REPO_ROOT / "src" / "image_reverb" / "surfaces.py",
    REPO_ROOT / "src" / "image_reverb" / "geometry.py",
    REPO_ROOT / "src" / "image_reverb" / "preprocess.py",
]

# 5 張「已知錯誤案例」照片（鐵則 12）：round17/tables.md 表 4（地雷 #18 型 in-set
# 誤判明細）裡出現的 8 筆誤判分屬這 5 張照片（bedroom_ai_generated 佔 4 面牆），
# 照抄自 output/clip_treatment/rounds/round17/tables.md 表 4，不重新計算。
KNOWN_ERROR_PHOTOS = [
    "bathroom_tiled",
    "bedroom_ai_generated",
    "site_photo_gym",
    "site_photo_restaurant",
    "RacquetballCourt4",
]


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


def _display_path(path: Path) -> str:
    """相對路徑印起來好讀；`--out-dir` 若指到 repo 外的絕對路徑，
    `relative_to()` 會炸 `ValueError`（criteria v2 §2.5.3），退回印絕對路徑。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _git_head(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def _criteria_commit() -> str:
    """criteria v2 §4 步驟 1：核對本檔（CRITERIA_T46_v2.md）的 commit（不得手抄）。"""
    return subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", "output/role_flag/CRITERIA_T46_v2.md"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _code_fingerprint() -> dict:
    return {
        "repo_head": _git_head(REPO_ROOT),
        "code_sha256": {p.name: sha256_file(p) for p in FINGERPRINT_CODE_PATHS},
    }


def run_cli(
    photo: Path,
    name: str,
    mode_tag: str,
    role_aware: bool,
    runs_dir: Path,
    fresh: bool,
    *,
    cwd: Path = REPO_ROOT,
    extra_fingerprint: dict | None = None,
) -> dict:
    """跑一次真實 CLI（`--force-low-confidence` 讓 gate 不擋下輸出，好讀到
    完整 analysis.json；BLOCK／pass 的判定另外從 `confidence` 欄位推回去，
    不依賴 exit code），把 `<cwd>/output/<stem>/` 搬到 `runs_dir/<name>__<mode_tag>/`。

    快取讀寫帶指紋（criteria v2 §2.5.2）：指紋存在 `runs_dir/<name>__<mode_tag>/
    .fingerprint.json`，缺檔或內容不符即視為快取失效、忽略既有輸出重跑。
    """
    dst = runs_dir / f"{name}__{mode_tag}"
    fingerprint = {"photo_sha256": sha256_file(photo)}
    if extra_fingerprint:
        fingerprint.update(extra_fingerprint)
    fp_path = dst / ".fingerprint.json"

    if dst.exists() and not fresh:
        aj = dst / "analysis.json"
        if aj.exists() and fp_path.exists() and json.loads(fp_path.read_text(encoding="utf-8")) == fingerprint:
            print(f"  ⏭️  快取命中（指紋相符）：{_display_path(dst)}")
            return json.loads(aj.read_text(encoding="utf-8"))
        print(f"  ↻ {name} ({mode_tag})：快取指紋不符或缺檔，重跑")

    cmd = [sys.executable, "-m", "src.image_reverb", str(photo), "--force-low-confidence", "--no-viz"]
    if role_aware:
        cmd.append("--role-aware")

    t0 = time.time()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    elapsed = time.time() - t0

    stem = photo.stem
    src_out = cwd / "output" / stem
    if proc.returncode != 0 or not src_out.exists():
        raise RuntimeError(
            f"{name} ({mode_tag}) 失敗：exit={proc.returncode}\n"
            f"cmd={' '.join(cmd)}（cwd={cwd}）\n"
            f"--- stdout（末 40 行）---\n" + "\n".join(proc.stdout.splitlines()[-40:]) + "\n"
            f"--- stderr（末 40 行）---\n" + "\n".join(proc.stderr.splitlines()[-40:])
        )

    if dst.exists():
        shutil.rmtree(dst)
    runs_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src_out), str(dst))
    fp_path.write_text(json.dumps(fingerprint, ensure_ascii=False, indent=2), encoding="utf-8")
    aj = json.loads((dst / "analysis.json").read_text(encoding="utf-8"))
    print(f"  ✅ {name} ({mode_tag}) {elapsed:.1f}s → {_display_path(dst)}")
    return aj


def load_frozen_faces(round_runs_dir: Path, name: str) -> dict:
    """讀 round11/round17 快取的 `payload.surfaces`／`payload.sources`（唯讀，
    T-44/T-38/T-39 evaluation harness 已用真實 `surfaces_from_preprocess()`
    算過，本腳本不重算）。"""
    path = round_runs_dir / name / "detail.json"
    if not path.exists():
        raise RuntimeError(f"🔴 卡關：找不到快取 {path}（round11/round17 產物是否被移動？）")
    data = json.loads(path.read_text(encoding="utf-8"))
    payload = data["payload"]
    return {"surfaces": payload["surfaces"], "sources": payload["sources"]}


def gate_of(analysis: dict) -> str:
    return "BLOCK" if analysis["confidence"] == "low" else "pass"


def _b0_run_cached(runs_dir: Path, name: str, photo: Path) -> dict | None:
    """B0 的程式碼固定在 `B0_COMMIT`，快取指紋只需照片 sha256。全部命中時
    `build_baseline_b0` 可以跳過建 `git worktree`（純加速，不影響斷言邏輯）。"""
    dst = runs_dir / f"{name}__b0"
    aj = dst / "analysis.json"
    fp_path = dst / ".fingerprint.json"
    if not (aj.exists() and fp_path.exists()):
        return None
    if json.loads(fp_path.read_text(encoding="utf-8")) != {"photo_sha256": sha256_file(photo)}:
        return None
    return json.loads(aj.read_text(encoding="utf-8"))


def _b0_gate_failures(analyses: dict[str, dict]) -> list[str]:
    """B0 自證守門（criteria v2 §2.1）：六面材質＋來源須＝round11；
    materials_confidence 須＝EXPECTED_GATE materials 欄。"""
    gate_failures: list[str] = []
    for item in t36.GATE_ITEMS:
        name = item["name"]
        a = analyses[name]
        frozen = load_frozen_faces(ROUND11_RUNS, name)
        _, expected_mat = t36.EXPECTED_GATE[name]
        if a["surfaces"] != frozen["surfaces"]:
            gate_failures.append(f"{name}：B0 surfaces 與 round11_remap_baseline 不一致")
        if a["surfaces_sources"] != frozen["sources"]:
            gate_failures.append(f"{name}：B0 surfaces_sources 與 round11_remap_baseline 不一致")
        if a["materials_confidence"] != expected_mat:
            gate_failures.append(
                f"{name}：B0 materials_confidence={a['materials_confidence']} != EXPECTED_GATE materials 欄 {expected_mat}"
            )
    return gate_failures


def build_baseline_b0(out_dir: Path, fresh: bool) -> tuple[dict[str, dict], list[str]]:
    """criteria v2 §2.1：在 `git worktree` 重建 `B0_COMMIT` 的真實 CLI 結果，
    回傳 `({name: analysis.json}, 守門不符清單)`。守門不符非空時，呼叫端須
    視為 🔴 停，不得繼續往下跑或改寬鬆。"""
    baseline_dir = out_dir / f"baseline_{B0_COMMIT}"
    runs_dir = baseline_dir / "runs"

    if not fresh:
        cached = {
            item["name"]: _b0_run_cached(runs_dir, item["name"], REPO_ROOT / item["photo"])
            for item in t36.GATE_ITEMS
        }
        if all(cached.values()):
            print(f"[B0] 全部 13 張快取命中（指紋相符），略過 git worktree 重建")
            return cached, _b0_gate_failures(cached)

    worktree_dir = REPO_ROOT / f".worktree_t46_b0_{B0_COMMIT}"

    if worktree_dir.exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree_dir)], cwd=REPO_ROOT, check=False)
        shutil.rmtree(worktree_dir, ignore_errors=True)

    print(f"[B0] git worktree add {_display_path(worktree_dir)} {B0_COMMIT}")
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_dir), B0_COMMIT],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    )
    try:
        worktree_head = _git_head(worktree_dir)
        expected_b0_head = subprocess.run(
            ["git", "rev-parse", B0_COMMIT], cwd=REPO_ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        if worktree_head != expected_b0_head:
            raise RuntimeError(
                f"🔴 卡關：worktree HEAD（{worktree_head}）≠ {B0_COMMIT} 全長雜湊（{expected_b0_head}）"
            )

        analyses: dict[str, dict] = {}
        for item in t36.GATE_ITEMS:
            name = item["name"]
            photo = REPO_ROOT / item["photo"]  # criteria v2 §2.1：照片一律用主 repo 絕對路徑
            print(f"[B0 {name}]")
            analyses[name] = run_cli(
                photo, name, "b0", role_aware=False,
                runs_dir=runs_dir, fresh=fresh, cwd=worktree_dir,
            )
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree_dir)], cwd=REPO_ROOT, check=False)
        shutil.rmtree(worktree_dir, ignore_errors=True)

    gate_failures = _b0_gate_failures(analyses)
    if not gate_failures:
        write_baseline_md(baseline_dir, analyses, worktree_head=expected_b0_head)

    return analyses, gate_failures


def write_baseline_md(baseline_dir: Path, analyses: dict[str, dict], *, worktree_head: str) -> None:
    """criteria v2 §2.1：程式產生 `BASELINE.md`，含 13 張表格＋manifest
    （worktree HEAD、每張照片與 analysis.json 的 sha256、主 repo HEAD、產生時間）。"""
    rows = []
    photo_hashes: dict[str, str] = {}
    json_hashes: dict[str, str] = {}
    for item in t36.GATE_ITEMS:
        name = item["name"]
        a = analyses[name]
        rows.append([
            name, a["geometry_confidence"], a["materials_confidence"],
            a["confidence"], gate_of(a),
            json.dumps(a["surfaces"], ensure_ascii=False),
            json.dumps(a["surfaces_sources"], ensure_ascii=False),
        ])
        photo_hashes[name] = sha256_file(REPO_ROOT / item["photo"])
        json_hashes[name] = sha256_file(baseline_dir / "runs" / f"{name}__b0" / "analysis.json")

    table = _md_table(
        ["照片", "geometry_confidence", "materials_confidence", "overall confidence", "gate", "surfaces", "surfaces_sources"],
        rows,
    )
    manifest_rows = [[name, photo_hashes[name], json_hashes[name]] for name in sorted(photo_hashes)]
    manifest_table = _md_table(["照片", "photo sha256", "analysis.json sha256"], manifest_rows)

    text = (
        "# BASELINE.md — T-46 criteria v2 基線 B0（程式產生，勿手改）\n\n"
        f"B0 定義（criteria v2 §2.1）：commit `{B0_COMMIT}`"
        "（role_aware 尚未預設啟用的最後狀態；是 T-44 系列中間 commit，不是 T-44 之前）"
        "的真實 CLI 實跑結果。\n\n"
        "## 表：13 張照片的 B0 結果\n\n"
        f"{table}\n\n"
        "## Manifest\n\n"
        f"- worktree `git rev-parse HEAD`：`{worktree_head}`（須等於 `{B0_COMMIT}` 全長雜湊，本檔產生時已驗證相符）\n"
        f"- 產生時主 repo 的 `git rev-parse HEAD`：`{_git_head(REPO_ROOT)}`\n"
        f"- 產生時間（UTC）：{datetime.now(timezone.utc).isoformat()}\n\n"
        f"{manifest_table}\n"
    )
    baseline_dir.mkdir(parents=True, exist_ok=True)
    (baseline_dir / "BASELINE.md").write_text(text, encoding="utf-8")


def main() -> int:
    out_dir, fresh = parse_args(sys.argv[1:])
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    print("=== 建置基線 B0（criteria v2 §2.1）===")
    b0_analyses, b0_gate_failures = build_baseline_b0(out_dir, fresh)
    if b0_gate_failures:
        print(f"\n❌ B0 自證守門不成立（{len(b0_gate_failures)} 項），不得往下跑、不寫任何產物：")
        for f in b0_gate_failures:
            print(f"  🔴 {f}")
        return 1

    code_fp = _code_fingerprint()
    rows: list[dict] = []
    mismatches: list[str] = []
    geometry_notes: list[str] = []

    print("\n=== 預設／--role-aware 兩模式（criteria v2 §2.2／§2.3）===")
    for item in t36.GATE_ITEMS:
        name = item["name"]
        photo = REPO_ROOT / item["photo"]
        b0 = b0_analyses[name]
        expected_geo, _ = t36.EXPECTED_GATE[name]
        print(f"[{name}]")

        a_default = run_cli(
            photo, name, "default", role_aware=False, runs_dir=runs_dir, fresh=fresh,
            extra_fingerprint=code_fp,
        )
        a_role = run_cli(
            photo, name, "role_aware", role_aware=True, runs_dir=runs_dir, fresh=fresh,
            extra_fingerprint=code_fp,
        )

        # --- 斷言 A1～A6（predefault vs B0）---
        if a_default.get("role_aware") is not False:
            mismatches.append(f"{name}：A1 預設模式 analysis.json.role_aware != false（{a_default.get('role_aware')!r}）")
        if a_default["geometry_confidence"] != b0["geometry_confidence"]:
            mismatches.append(
                f"{name}：A2 geometry_confidence={a_default['geometry_confidence']} != B0（{B0_COMMIT}）{b0['geometry_confidence']}"
            )
        if a_default["materials_confidence"] != b0["materials_confidence"]:
            mismatches.append(
                f"{name}：A3 materials_confidence={a_default['materials_confidence']} != B0（{B0_COMMIT}）{b0['materials_confidence']}"
            )
        if a_default["confidence"] != b0["confidence"]:
            mismatches.append(
                f"{name}：A4 overall confidence={a_default['confidence']} != B0（{B0_COMMIT}）{b0['confidence']}"
            )
        if gate_of(a_default) != gate_of(b0):
            mismatches.append(
                f"{name}：A5 gate={gate_of(a_default)} != B0（{B0_COMMIT}）{gate_of(b0)}"
            )
        if a_default["surfaces"] != b0["surfaces"]:
            mismatches.append(
                f"{name}：A6 預設模式 surfaces != B0（{B0_COMMIT}）"
                f"\n  本次：{a_default['surfaces']}\n  B0：{b0['surfaces']}"
            )
        if a_default["surfaces_sources"] != b0["surfaces_sources"]:
            mismatches.append(
                f"{name}：A6 預設模式 surfaces_sources != B0（{B0_COMMIT}）"
                f"\n  本次：{a_default['surfaces_sources']}\n  B0：{b0['surfaces_sources']}"
            )

        # criteria v2 §2.5.5 表 1 要求的第三欄「與 round11 相符」（B0 已於 §2.1
        # 自證守門對過 round11，這裡對預設模式結果直接複查一次，資訊性顯示）。
        frozen_round11 = load_frozen_faces(ROUND11_RUNS, name)
        match_round11 = (
            a_default["surfaces"] == frozen_round11["surfaces"]
            and a_default["surfaces_sources"] == frozen_round11["sources"]
        )

        # --- 斷言 B1～B2（--role-aware vs round17）---
        if a_role.get("role_aware") is not True:
            mismatches.append(f"{name}：B1 --role-aware 模式 analysis.json.role_aware != true（{a_role.get('role_aware')!r}）")
        frozen_role = load_frozen_faces(ROUND17_RUNS, name)
        if a_role["surfaces"] != frozen_role["surfaces"]:
            mismatches.append(
                f"{name}：B2 --role-aware 模式 surfaces != round17"
                f"\n  本次：{a_role['surfaces']}\n  round17：{frozen_role['surfaces']}"
            )
        if a_role["surfaces_sources"] != frozen_role["sources"]:
            mismatches.append(
                f"{name}：B2 --role-aware 模式 surfaces_sources != round17"
                f"\n  本次：{a_role['surfaces_sources']}\n  round17：{frozen_role['sources']}"
            )

        # --- 表 3：geometry 觀察，只報告不斷言（criteria v2 §2.4；B3 同精神）---
        if a_default["geometry_confidence"] != a_role["geometry_confidence"]:
            geometry_notes.append(
                f"{name}：geometry_confidence 在兩模式間不同"
                f"（default={a_default['geometry_confidence']}, role_aware={a_role['geometry_confidence']}）"
            )
        if a_default["geometry_confidence"] != expected_geo:
            geometry_notes.append(
                f"{name}：預設模式 geometry_confidence={a_default['geometry_confidence']} "
                f"與 EXPECTED_GATE（T-28-A／T-36 凍結表）{expected_geo} 不同（B0 於 {B0_COMMIT} 亦同，非本卡回歸）"
            )

        rows.append(
            {
                "name": name,
                "geometry_default": a_default["geometry_confidence"],
                "geometry_role": a_role["geometry_confidence"],
                "materials_default": a_default["materials_confidence"],
                "overall_default": a_default["confidence"],
                "gate_default": gate_of(a_default),
                "materials_role": a_role["materials_confidence"],
                "overall_role": a_role["confidence"],
                "gate_role": gate_of(a_role),
                "match_b0": (
                    a_default["geometry_confidence"] == b0["geometry_confidence"]
                    and a_default["materials_confidence"] == b0["materials_confidence"]
                    and a_default["confidence"] == b0["confidence"]
                    and gate_of(a_default) == gate_of(b0)
                    and a_default["surfaces"] == b0["surfaces"]
                    and a_default["surfaces_sources"] == b0["surfaces_sources"]
                ),
                "match_round11": match_round11,
                "match_round17": a_role["surfaces"] == frozen_role["surfaces"]
                and a_role["surfaces_sources"] == frozen_role["sources"],
            }
        )

    # 斷言 A7：bathroom_tiled／bedroom_ai_generated 與鐵則 12 五張已知錯誤案例
    # 在預設模式下必須全部 BLOCK（裁決 T-45-A 的整個前提）。
    by_name = {r["name"]: r for r in rows}
    for critical_name in {"bathroom_tiled", "bedroom_ai_generated"} | set(KNOWN_ERROR_PHOTOS):
        if by_name[critical_name]["gate_default"] != "BLOCK":
            mismatches.append(
                f"{critical_name}：A7 預設模式 gate={by_name[critical_name]['gate_default']}，"
                "應為 BLOCK（鐵則 12／裁決 T-45-A 的解除前提）"
            )

    if mismatches:
        print(f"\n❌ {len(mismatches)} 項斷言不成立，不寫 REPORT／tables：")
        for m in mismatches:
            print(f"  🔴 {m}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    main_table = _md_table(
        ["照片", "geometry（預設）", "geometry（--role-aware）",
         "materials（預設）", "overall（預設）", "gate（預設）",
         "materials（--role-aware）", "overall（--role-aware）", "gate（--role-aware）",
         "與 B0 相符", "與 round11 相符", "與 round17 相符"],
        [
            [r["name"], r["geometry_default"], r["geometry_role"],
             r["materials_default"], r["overall_default"], r["gate_default"],
             r["materials_role"], r["overall_role"], r["gate_role"],
             "✅" if r["match_b0"] else "🔴", "✅" if r["match_round11"] else "🔴",
             "✅" if r["match_round17"] else "🔴"]
            for r in rows
        ],
    )
    known_error_table = _md_table(
        ["照片", "gate（預設）", "gate（--role-aware，只列不判）"],
        [[name, by_name[name]["gate_default"], by_name[name]["gate_role"]] for name in KNOWN_ERROR_PHOTOS],
    )

    tables_md = (
        "## 表 1：13 張照片基準率變化（預設 vs --role-aware，vs 基線 B0＝"
        f"commit `{B0_COMMIT}`）\n\n"
        f"{main_table}\n\n"
        "## 表 2：已知錯誤案例清單（鐵則 12）在兩模式的 gate 結果\n\n"
        f"{known_error_table}\n"
    )
    if geometry_notes:
        geometry_note_lines = "\n".join(f"- {n}" for n in geometry_notes)
        tables_md += (
            "\n## 表 3：geometry_confidence 觀察（只報告不斷言，criteria v2 §2.4；供 T-47 參考）\n\n"
            f"{geometry_note_lines}\n"
        )
    (out_dir / "tables.md").write_text(tables_md, encoding="utf-8")

    n_ok = sum(1 for r in rows if r["match_b0"] and r["match_round11"] and r["match_round17"])
    header_table = _md_table(
        ["欄位", "值"],
        [
            ["主 repo HEAD（產生本報告時）", f"`{_git_head(REPO_ROOT)}`"],
            ["B0 commit（全長）", f"`{B0_COMMIT}` → `{subprocess.run(['git', 'rev-parse', B0_COMMIT], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()}`"],
            ["criteria_version", "v2"],
            ["criteria_commit（本檔 commit）", f"`{_criteria_commit()}`"],
            ["跑法", "`--fresh`（含 B0 重建，零快取）" if fresh else "非 `--fresh`（含快取結果，送審請重跑 `--fresh`）"],
        ],
    )
    report_md = (
        "# T-46 步驟 4 REPORT — 13 張照片基準率變化表（裁決 T-45-A 執行卡 1/5；criteria v2）\n\n"
        f"{header_table}\n\n"
        "本報告由 `scripts/t46_role_flag_baseline.py` 依 "
        "[`CRITERIA_T46_v2.md`](CRITERIA_T46_v2.md) 對 13 張照片各跑一次真實 CLI"
        "（`python -m src.image_reverb <photo> --force-low-confidence --no-viz`，"
        "預設模式與加 `--role-aware` 各一次），並在 `git worktree` 重建基線 B0"
        f"（commit `{B0_COMMIT}`：role_aware 尚未預設啟用的最後狀態）之真實 CLI 結果，"
        "程式化驗證：\n\n"
        "1. **預設模式（斷言 A1～A7）**：`role_aware==false`；geometry／materials／overall "
        "confidence、gate、六面材質＋來源逐張與基線 B0 **逐值相同**；`bathroom_tiled`、"
        "`bedroom_ai_generated` 與鐵則 12 五張已知錯誤案例均回到 **BLOCK**。\n"
        "2. **`--role-aware` 模式（斷言 B1～B2）**：`role_aware==true`；六面材質＋來源與 "
        f"T-44 最終輪 `round17`（曾經是 `pipeline.py` 硬編碼的預設行為）**逐值相同**——旗標路徑沒壞。"
        "geometry／overall confidence／gate 只報告不斷言（無可執行基線，交 T-47）。\n\n"
        f"13 張全數通過（{n_ok}/13 三項比對皆相符：與 B0、與 round11、與 round17）。完整表格見 [`tables.md`](tables.md)、"
        f"B0 的持久證據見 [`baseline_{B0_COMMIT}/BASELINE.md`](baseline_{B0_COMMIT}/BASELINE.md)。\n\n"
        "## ⚠️ 已知殘留風險（誠實揭露，本卡範圍外、不阻擋本卡結論；criteria v2 §2.4）\n\n"
        "`EXPECTED_GATE`（T-28-A／T-36 凍結表）的 geometry 欄**不作為本卡斷言**——B0 於 "
        f"commit `{B0_COMMIT}` 實測 `TunnelToHell.geometry_confidence=low`，表列 `medium`，"
        "是表本身過期（T-37 equirect 修正後未更新），不是本卡回歸，交 T-47／裁決 T-47-A。"
        "另外用真實 CLI 兩模式並排跑 13 張後，觀察到 `role_aware` 會透過既有的 "
        "`scene_cues[\"out_of_domain\"]` 機制間接影響 `geometry_confidence`"
        "（`site_photo_department_store`：某面在窄候選集下被判成「object_closeup」而觸發 "
        "`apply_scene_cue_confidence()` 降級，medium→low）——這個路徑在 T-44 round17 上線時"
        "就存在，只是這次用真實 CLI 兩模式並排比較才被看見。`gate 判定段／"
        "compute_materials_confidence()／scene_cues／門檻 0.4` 全部零改動（範圍紅線），"
        "此處只誠實記錄，不在本卡處理。完整清單見 [`tables.md`](tables.md) 表 3。\n"
    )
    (out_dir / "REPORT.md").write_text(report_md, encoding="utf-8")

    print(f"\n✅ 13 張照片 ×2 模式全數與基線 B0／round17 逐值相符，REPORT 已寫入 {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
