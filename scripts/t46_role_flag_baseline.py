#!/usr/bin/env python3
"""T-46 步驟 4（依 criteria v3，`output/role_flag/CRITERIA_T46_v3.md`，
執行者不得改該檔一字；v3 取代 v2 §5.2 與同版 §2.1 自我矛盾的「`BASELINE.md`
逐字相同」，v1／v2 原文與兩輪退回 verdict 全部保留在 v3 附錄 A／B）：13 張
照片基準率變化表（鐵則 8；裁決 T-45-A 執行卡 1/5 收尾）。

背景：T-46 把 `pipeline.run_photo()` 的 `role_aware` 開關從硬編碼 `True`
改回 `config.ROLE_AWARE_MATERIALS_DEFAULT`（`False`），CLI 新增 `--role-aware`
保留 T-44 的研究路徑。本腳本用**真實 CLI**（`python -m src.image_reverb ...`，
含真實幾何模型／分割模型／CLIP，不打樁）對 13 張照片各跑「預設」與
`--role-aware` 兩種模式，並用 `git worktree` 重建 commit `23f2aba`
（role_aware 尚未預設啟用的最後狀態；是 T-44 系列中間 commit、不是 T-44
之前，見 criteria v3 §2.1）的真實 CLI 結果作為基線 B0，程式化驗證
（criteria v3 §2.3／§2.4）：

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
＝🔴 停回 Fable，見 criteria v3 §2.1）；**geometry 欄不作為本卡任何斷言**
（criteria v3 §2.5：`TunnelToHell` 在 `23f2aba` 也是 `geometry=low`，表列
`medium` 是表過期，不是 T-46 的回歸，改表交 T-47／裁決 T-47-A）。

**v3 新增的核心（criteria v3 §2.2）——canonical stable projection**：每份
`analysis.json` 解析後，只移除 `STABLE_PROJECTION_EXCLUDED_PATHS` 這張固定
清單列出的 8 個鍵（耗時／預算／超時說明三個計時欄＋照片與產物五個絕對路徑
欄），`sort_keys` 正規化序列化後取 sha256＝`analysis_stable_sha256`，寫成
`analysis.stable.json`（39 個 run 都有一份）。B0 的 `BASELINE.stable.md`
（13×6 離散欄＋B0 commit＋13 筆 `analysis_stable_sha256`）是 §5.2 的**唯一
硬比對物件**；`BASELINE.md`＝同一段 stable 文字逐字＋provenance 段（主 repo
HEAD／產生時間／環境／原始 `analysis.json` sha256／`elapsed_s`），provenance
段**只記錄、不比對**，不得據此判失敗也不得據此判通過（criteria v3 §2.2.4）。
開跑前守門（§2.6.6）：`CRITERIA_T46_v3.md` 若尚未 commit＝🔴 停、不跑。寫檔
自檢（§2.6.7）：`analysis.stable.json`／`BASELINE.stable.md`／`BASELINE.md`
寫完都重新讀回核對內容與雜湊，任一不符＝🔴 卡關。

**斷言 A1～A7／B1～B2 的程式邏輯本輪一行不動**（v3 只改 B0 的持久化與比對
物件，不改任何實質斷言，見 criteria v3 §4 步驟 2）。

13 張照片清單、`EXPECTED_GATE` 唯讀 import 自 `t36_clip_accuracy.py`，不重打。
round11／round17 的逐面判定明細（`surfaces`／`sources`）唯讀讀取兩輪各自
`runs/<name>/detail.json` 快取（已用真實 `surfaces_from_preprocess()` 算過，
不需要也不應該重新用打樁重算）。

`src/` 全程只讀不寫，只透過 `python -m src.image_reverb` 這個既有 CLI 入口跑
（含 B0 的 `git worktree`），不 import／不打樁任何 `src.image_reverb` 內部函式。

跑法：`python scripts/t46_role_flag_baseline.py --out-dir output/role_flag/v3/ --fresh`
（送審一律加 `--fresh`，含 B0 重建，13 張 B0＋13×2 兩模式＝39 次真實 CLI，
單張約 15–40 秒）。不加 `--fresh` 時走快取：預設模式／`--role-aware` 兩模式的
快取指紋含主 repo HEAD＋`src/image_reverb/{cli,config,pipeline,surfaces,
geometry,preprocess}.py` 內容 sha256＋照片 sha256，指紋不符即視為快取失效、
自動重跑（`scripts/eval_cache.py` 的 `sha256_file` 手法，本檔不重新實作雜湊
邏輯）；B0（`git worktree` 於固定 commit `23f2aba`）的快取指紋只需照片
sha256（該 commit 的程式碼固定不變）。

輸出：`<out_dir>/REPORT.md`、`<out_dir>/tables.md`（表格程式產生，地雷 #15，
不含任何 provenance 值）、`<out_dir>/baseline_23f2aba/{BASELINE.md,
BASELINE.stable.md,runs/<name>/{analysis.json,analysis.stable.json}}`（B0 的
持久證據，`BASELINE.md`／`BASELINE.stable.md` 進 git）、`<out_dir>/runs/
<name>__{default,role_aware}/{analysis.json,analysis.stable.json}`（每個 run
的完整輸出快照）。任一斷言／守門／自檢不成立 exit 非 0，且不寫 REPORT／
tables／BASELINE（半成品比沒有更危險）。
"""

from __future__ import annotations

import copy
import hashlib
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

import t36_clip_accuracy as t36  # noqa: E402  （唯讀引用：GATE_ITEMS／EXPECTED_GATE）
from t36_analysis import _md_table  # noqa: E402  （唯讀引用，不重新實作表格排版）
from eval_cache import sha256_file  # noqa: E402  （唯讀引用，不重新實作雜湊邏輯）

CRITERIA_PATH = "output/role_flag/CRITERIA_T46_v3.md"
DEFAULT_OUT_DIR = REPO_ROOT / "output" / "role_flag" / "v3"
ROUND11_RUNS = REPO_ROOT / "output" / "clip_treatment" / "rounds" / "round11_remap_baseline" / "runs"
ROUND17_RUNS = REPO_ROOT / "output" / "clip_treatment" / "rounds" / "round17" / "runs"

# criteria v3 §2.1（維持 v2 §2.1 原文）：預設路徑基線 B0＝role_aware 尚未預設
# 啟用的最後狀態（T-44 系列中間 commit，不是 T-44 之前——正確描述見 criteria
# v3 §2.1）。
B0_COMMIT = "23f2aba"

# criteria v3 §2.6.3（維持 v2 §2.5.2 原文）：快取指紋要納入的 src 檔（CLI 實際
# 會載入到的模組）。
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

# criteria v3 §2.2.1：canonical stable projection 排除的固定清單（一個字元都
# 不能偏，執行者不得在這張清單之外多排除任何鍵——發現還有 volatile 欄＝🔴 卡關
# 回 Fable 開 v4，不得自己加，見 criteria v3 §3.3）。逐字採用 criteria v3 給的
# 定義。
STABLE_PROJECTION_EXCLUDED_PATHS = (
    "elapsed_s",         # 本次耗時秒數（pipeline._elapsed_payload）——每次真跑必然不同
    "time_budget_s",     # 同一 payload 的預算常數，隨 elapsed_s 一併排除
    "elapsed_note",      # 超過預算時才出現的說明字串（含耗時數字）
    "input",              # 照片絕對路徑（照片內容已由 photo sha256 硬比對）
    "output_dir",         # 產物目錄絕對路徑（含 worktree 暫存路徑）
    "ir_mono.path",        # 產物絕對路徑
    "ir_stereo.path",      # 產物絕對路徑
    "wet_preview.path",    # 產物絕對路徑
)


def stable_projection(analysis: dict) -> dict:
    """criteria v3 §2.2.1：對 `analysis.json` 解析後的物件，只移除
    `STABLE_PROJECTION_EXCLUDED_PATHS` 這張固定清單（鍵不存在時略過，不報錯；
    不得用「鍵名叫 path 就刪」之類的萬用規則）。逐字採用 criteria v3 給的參考實作。"""
    obj = copy.deepcopy(analysis)
    for dotted in STABLE_PROJECTION_EXCLUDED_PATHS:
        parts = dotted.split(".")
        node = obj
        for p in parts[:-1]:
            node = node.get(p) if isinstance(node, dict) else None
            if node is None:
                break
        if isinstance(node, dict):
            node.pop(parts[-1], None)
    return obj


def canonical_stable_bytes(analysis: dict) -> bytes:
    """criteria v3 §2.2.1：正規化序列化（一個字元都不能偏）。"""
    projected = stable_projection(analysis)
    return (json.dumps(projected, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


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
    `relative_to()` 會炸 `ValueError`（criteria v3 §2.6.3，維持 v2 §2.5.3），
    退回印絕對路徑。"""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _git_head(cwd: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=cwd, capture_output=True, text=True, check=True
    ).stdout.strip()


def _criteria_commit() -> str:
    """criteria v3 §2.6.6／§4 步驟 1：核對本檔（CRITERIA_T46_v3.md）的 commit
    （不得手抄）。空字串代表本檔尚未 commit。"""
    return subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", CRITERIA_PATH],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()


def _startup_gate() -> None:
    """criteria v3 §2.6.6：開跑前守門。`CRITERIA_T46_v3.md` 若尚未 commit
    （`git log -1 -- 該檔` 為空）＝🔴 停、不跑，不得改用手抄值頂替。"""
    commit = _criteria_commit()
    if not commit:
        raise SystemExit(
            f"🔴 卡關：{CRITERIA_PATH} 尚未 commit（git log -1 -- 該檔為空），"
            "依 criteria v3 §2.6.6 不得開跑。"
        )
    print(f"[守門] {CRITERIA_PATH} 已於 commit {commit} 存在，允許開跑。")


def _environment_string() -> str:
    """criteria v3 §2.2.3 provenance 段：platform／python／torch 版本
    （torch import 失敗寫 n/a，不當斷言用，只記錄）。"""
    try:
        import torch  # noqa: PLC0415

        torch_version = torch.__version__
    except Exception:
        torch_version = "n/a"
    return f"{platform.platform()}；python {sys.version.split()[0]}；torch {torch_version}"


def _code_fingerprint() -> dict:
    return {
        "repo_head": _git_head(REPO_ROOT),
        "code_sha256": {p.name: sha256_file(p) for p in FINGERPRINT_CODE_PATHS},
    }


def write_stable_analysis(dst: Path, analysis: dict) -> str:
    """criteria v3 §2.2.1：把 `analysis.json` 的 canonical stable projection
    寫成 `analysis.stable.json`，放在 `analysis.json` 旁邊。自檢（§2.6.7）：
    寫檔後重新讀回、重算 sha256，須等於寫入時算出的 `analysis_stable_sha256`，
    不符＝🔴 卡關（半成品比沒有更危險）。回傳 `analysis_stable_sha256`。"""
    canonical_bytes = canonical_stable_bytes(analysis)
    analysis_stable_sha256 = hashlib.sha256(canonical_bytes).hexdigest()
    stable_path = dst / "analysis.stable.json"
    stable_path.write_bytes(canonical_bytes)
    reread_sha256 = hashlib.sha256(stable_path.read_bytes()).hexdigest()
    if reread_sha256 != analysis_stable_sha256:
        raise RuntimeError(
            f"🔴 卡關：{stable_path} 自檢失敗，寫入後重讀 sha256 不符"
            f"（寫入時 {analysis_stable_sha256}，重讀 {reread_sha256}）"
        )
    return analysis_stable_sha256


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
    不依賴 exit code），把 `<cwd>/output/<stem>/` 搬到 `runs_dir/<name>__<mode_tag>/`，
    並在旁邊寫一份 `analysis.stable.json`（criteria v3 §2.2.1，含自檢）。

    快取讀寫帶指紋（criteria v3 §2.6.3，維持 v2 §2.5.2）：指紋存在 `runs_dir/
    <name>__<mode_tag>/.fingerprint.json`，缺檔或內容不符即視為快取失效、
    忽略既有輸出重跑。
    """
    dst = runs_dir / f"{name}__{mode_tag}"
    fingerprint = {"photo_sha256": sha256_file(photo)}
    if extra_fingerprint:
        fingerprint.update(extra_fingerprint)
    fp_path = dst / ".fingerprint.json"

    if dst.exists() and not fresh:
        aj_path = dst / "analysis.json"
        if aj_path.exists() and fp_path.exists() and json.loads(fp_path.read_text(encoding="utf-8")) == fingerprint:
            print(f"  ⏭️  快取命中（指紋相符）：{_display_path(dst)}")
            cached = json.loads(aj_path.read_text(encoding="utf-8"))
            write_stable_analysis(dst, cached)
            return cached
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
    write_stable_analysis(dst, aj)
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
    `build_baseline_b0` 可以跳過建 `git worktree`（純加速，不影響斷言邏輯；
    此路徑不重建 `BASELINE.md`／`BASELINE.stable.md`，與 v2 行為一致——送審
    一律 `--fresh`，本路徑不用於送審）。"""
    dst = runs_dir / f"{name}__b0"
    aj = dst / "analysis.json"
    fp_path = dst / ".fingerprint.json"
    if not (aj.exists() and fp_path.exists()):
        return None
    if json.loads(fp_path.read_text(encoding="utf-8")) != {"photo_sha256": sha256_file(photo)}:
        return None
    return json.loads(aj.read_text(encoding="utf-8"))


def _b0_gate_failures(analyses: dict[str, dict]) -> list[str]:
    """B0 自證守門（criteria v3 §2.1，維持 v2 §2.1）：六面材質＋來源須＝round11；
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


def build_baseline_b0(out_dir: Path, fresh: bool) -> tuple[dict[str, dict], list[str], str | None]:
    """criteria v3 §2.1：在 `git worktree` 重建 `B0_COMMIT` 的真實 CLI 結果，
    回傳 `({name: analysis.json}, 守門不符清單, baseline_stable_sha256)`。
    守門不符非空時，呼叫端須視為 🔴 停，不得繼續往下跑或改寬鬆；
    `baseline_stable_sha256` 只在守門通過且走過真實 worktree 重建時才有值。"""
    baseline_dir = out_dir / f"baseline_{B0_COMMIT}"
    runs_dir = baseline_dir / "runs"

    if not fresh:
        cached = {
            item["name"]: _b0_run_cached(runs_dir, item["name"], REPO_ROOT / item["photo"])
            for item in t36.GATE_ITEMS
        }
        if all(cached.values()):
            print(f"[B0] 全部 13 張快取命中（指紋相符），略過 git worktree 重建")
            return cached, _b0_gate_failures(cached), None

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
            photo = REPO_ROOT / item["photo"]  # criteria v3 §2.1：照片一律用主 repo 絕對路徑
            print(f"[B0 {name}]")
            analyses[name] = run_cli(
                photo, name, "b0", role_aware=False,
                runs_dir=runs_dir, fresh=fresh, cwd=worktree_dir,
            )
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(worktree_dir)], cwd=REPO_ROOT, check=False)
        shutil.rmtree(worktree_dir, ignore_errors=True)

    gate_failures = _b0_gate_failures(analyses)
    baseline_stable_sha256 = None
    if not gate_failures:
        photo_hashes = {item["name"]: sha256_file(REPO_ROOT / item["photo"]) for item in t36.GATE_ITEMS}
        stable_shas = {
            name: sha256_file(runs_dir / f"{name}__b0" / "analysis.stable.json") for name in analyses
        }
        raw_json_paths = {name: runs_dir / f"{name}__b0" / "analysis.json" for name in analyses}
        baseline_stable_sha256 = write_baseline_files(
            baseline_dir,
            analyses,
            worktree_head=expected_b0_head,
            stable_shas=stable_shas,
            photo_hashes=photo_hashes,
            raw_json_paths=raw_json_paths,
        )

    return analyses, gate_failures, baseline_stable_sha256


def _b0_row(name: str, a: dict) -> list[str]:
    return [
        name,
        a["geometry_confidence"],
        a["materials_confidence"],
        a["confidence"],
        gate_of(a),
        json.dumps(a["surfaces"], ensure_ascii=False),
        json.dumps(a["surfaces_sources"], ensure_ascii=False),
    ]


def build_baseline_stable_text(
    analyses: dict[str, dict], *, worktree_head: str, stable_shas: dict[str, str], photo_hashes: dict[str, str]
) -> str:
    """criteria v3 §2.2.2：`BASELINE.stable.md` 全文——固定四塊，順序固定，
    不得含時間／主 repo HEAD／原始 sha256／環境資訊或任何會隨重跑改變的字串。
    這是 §5.2 的唯一硬比對物件。"""
    rows = [_b0_row(item["name"], analyses[item["name"]]) for item in t36.GATE_ITEMS]
    table_s1 = _md_table(
        ["照片", "geometry_confidence", "materials_confidence", "overall confidence", "gate", "surfaces", "surfaces_sources"],
        rows,
    )
    manifest_rows = [[name, photo_hashes[name], stable_shas[name]] for name in sorted(photo_hashes)]
    table_s2 = _md_table(["照片", "photo sha256", "analysis_stable_sha256"], manifest_rows)

    return (
        "# BASELINE.stable.md — T-46 criteria v3 基線 B0 穩定投影（程式產生，勿手改；§5.2 硬比對物件）\n\n"
        f"{table_s1}\n\n"
        f"- B0 commit（worktree git rev-parse HEAD）：{worktree_head}\n\n"
        f"{table_s2}\n"
    )


def build_provenance_text(
    baseline_stable_sha256: str, analyses: dict[str, dict], raw_json_paths: dict[str, Path]
) -> str:
    """criteria v3 §2.2.3 P 段：只記錄、不比對；不同重跑本來就會不同，
    不得據此判失敗、也不得據此判通過。"""
    rows = []
    for name in sorted(analyses):
        a = analyses[name]
        rows.append([name, sha256_file(raw_json_paths[name]), str(a.get("elapsed_s"))])
    table_p1 = _md_table(["照片", "analysis.json sha256（原始，含 elapsed_s）", "elapsed_s"], rows)

    return (
        f"- baseline_stable_sha256：`{baseline_stable_sha256}`\n"
        f"- 產生時主 repo 的 git rev-parse HEAD：`{_git_head(REPO_ROOT)}`\n"
        f"- 產生時間（UTC）：{datetime.now(timezone.utc).isoformat()}\n"
        f"- 環境：{_environment_string()}\n"
        f"- criteria_commit（git log -1 -- {CRITERIA_PATH}）：`{_criteria_commit()}`\n\n"
        f"{table_p1}\n"
    )


_S_MARKER = "## S. Stable projection（§5.2 硬比對範圍；與 BASELINE.stable.md 逐字相同）\n"
_P_MARKER = "## P. Provenance（只記錄、不比對；不同重跑本來就會不同，不得據此判失敗、也不得據此判通過）\n"


def write_baseline_files(
    baseline_dir: Path,
    analyses: dict[str, dict],
    *,
    worktree_head: str,
    stable_shas: dict[str, str],
    photo_hashes: dict[str, str],
    raw_json_paths: dict[str, Path],
) -> str:
    """criteria v3 §2.2.2／§2.2.3：程式產生 `BASELINE.stable.md`（§5.2 硬比對
    物件）與 `BASELINE.md`（stable 段逐字＋provenance 段）。自檢（§2.6.7）：
    兩檔寫完都重新讀回核對內容／雜湊，任一不符＝🔴 卡關。回傳
    `baseline_stable_sha256`。"""
    stable_text = build_baseline_stable_text(
        analyses, worktree_head=worktree_head, stable_shas=stable_shas, photo_hashes=photo_hashes
    )
    stable_bytes = stable_text.encode("utf-8")

    baseline_dir.mkdir(parents=True, exist_ok=True)
    stable_path = baseline_dir / "BASELINE.stable.md"
    stable_path.write_bytes(stable_bytes)
    if stable_path.read_bytes() != stable_bytes:
        raise RuntimeError(f"🔴 卡關：{stable_path} 自檢失敗，寫入後重讀內容不符")
    baseline_stable_sha256 = hashlib.sha256(stable_bytes).hexdigest()

    provenance_text = build_provenance_text(baseline_stable_sha256, analyses, raw_json_paths)

    intro = (
        f"B0 定義（criteria v3 §2.1）：commit `{B0_COMMIT}`"
        "（role_aware 尚未預設啟用的最後狀態；是 T-44 系列中間 commit，不是 T-44 之前）"
        "的真實 CLI 實跑結果。下方「S. Stable projection」段是 §5.2 的唯一硬比對物件"
        "（canonical stable projection，排除 8 個 volatile 鍵後 sort_keys 正規化）；"
        "「P. Provenance」段只記錄、不比對，不同重跑本來就會不同，不得據此判失敗、也不得據此判通過。\n"
    )

    full_text = (
        "# BASELINE.md — T-46 criteria v3 基線 B0（程式產生，勿手改）\n"
        f"{intro}\n"
        f"{_S_MARKER}"
        f"{stable_text}"
        f"{_P_MARKER}"
        f"{provenance_text}"
    )
    baseline_path = baseline_dir / "BASELINE.md"
    baseline_path.write_text(full_text, encoding="utf-8")

    reread_full = baseline_path.read_text(encoding="utf-8")
    s_start = reread_full.index(_S_MARKER) + len(_S_MARKER)
    p_start = reread_full.index(_P_MARKER)
    s_section = reread_full[s_start:p_start]
    if s_section.encode("utf-8") != stable_bytes:
        raise RuntimeError("🔴 卡關：BASELINE.md 的 S 段與 BASELINE.stable.md 不逐字相同（自檢失敗）")

    return baseline_stable_sha256


def main() -> int:
    _startup_gate()

    out_dir, fresh = parse_args(sys.argv[1:])
    runs_dir = out_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    print("=== 建置基線 B0（criteria v3 §2.1）===")
    b0_analyses, b0_gate_failures, baseline_stable_sha256 = build_baseline_b0(out_dir, fresh)
    if b0_gate_failures:
        print(f"\n❌ B0 自證守門不成立（{len(b0_gate_failures)} 項），不得往下跑、不寫任何產物：")
        for f in b0_gate_failures:
            print(f"  🔴 {f}")
        return 1

    code_fp = _code_fingerprint()
    rows: list[dict] = []
    mismatches: list[str] = []
    geometry_notes: list[str] = []

    print("\n=== 預設／--role-aware 兩模式（criteria v3 §2.3／§2.4）===")
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

        # criteria v3 §2.6.4 表 1 要求的第三欄「與 round11 相符」（B0 已於 §2.1
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

        # --- 表 3：geometry 觀察，只報告不斷言（criteria v3 §2.5；B3 同精神）---
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

    # criteria v3 §2.6.5：tables.md 不得含任何 provenance 值（維持 v2 已如此的作法）。
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
            "\n## 表 3：geometry_confidence 觀察（只報告不斷言，criteria v3 §2.5；供 T-47 參考）\n\n"
            f"{geometry_note_lines}\n"
        )
    (out_dir / "tables.md").write_text(tables_md, encoding="utf-8")

    n_ok = sum(1 for r in rows if r["match_b0"] and r["match_round11"] and r["match_round17"])

    # criteria v3 §2.6.4：REPORT.md 檔頭分兩區——硬（比對用）與 provenance（只記錄不比對）。
    hard_table = _md_table(
        ["硬（欄位，§5.2／§2.7 比對用）", "值"],
        [
            ["criteria_version", "v3"],
            ["criteria_commit（本檔 commit，全長）", f"`{_criteria_commit()}`"],
            ["B0 commit（全長）", f"`{B0_COMMIT}` → `{subprocess.run(['git', 'rev-parse', B0_COMMIT], cwd=REPO_ROOT, capture_output=True, text=True, check=True).stdout.strip()}`"],
            ["跑法", "`--fresh`（含 B0 重建，零快取）" if fresh else "非 `--fresh`（含快取結果，送審請重跑 `--fresh`）"],
            ["baseline_stable_sha256", f"`{baseline_stable_sha256}`"],
        ],
    )
    provenance_table = _md_table(
        ["provenance（欄位，只記錄不比對）", "值"],
        [
            ["主 repo HEAD（產生本報告時）", f"`{_git_head(REPO_ROOT)}`"],
            ["產生時間（UTC）", datetime.now(timezone.utc).isoformat()],
            ["環境", _environment_string()],
        ],
    )
    report_md = (
        "# T-46 步驟 4 REPORT — 13 張照片基準率變化表（裁決 T-45-A 執行卡 1/5；criteria v3）\n\n"
        "## 硬（比對用，§2.7 分層判定依據）\n\n"
        f"{hard_table}\n\n"
        "## Provenance（只記錄、不比對；不同重跑本來就會不同，不得據此判失敗、也不得據此判通過）\n\n"
        f"{provenance_table}\n\n"
        "本報告由 `scripts/t46_role_flag_baseline.py` 依 "
        "[`CRITERIA_T46_v3.md`](../CRITERIA_T46_v3.md) 對 13 張照片各跑一次真實 CLI"
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
        f"B0 的持久證據見 [`baseline_{B0_COMMIT}/BASELINE.stable.md`](baseline_{B0_COMMIT}/BASELINE.stable.md)"
        f"（§5.2 硬比對物件）與 [`baseline_{B0_COMMIT}/BASELINE.md`](baseline_{B0_COMMIT}/BASELINE.md)"
        "（stable 段逐字＋provenance 段，provenance 段只記錄不比對）。\n\n"
        "## ⚠️ 已知殘留風險（誠實揭露，本卡範圍外、不阻擋本卡結論；criteria v3 §2.5）\n\n"
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
