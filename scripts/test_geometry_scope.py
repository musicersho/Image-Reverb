#!/usr/bin/env python3
"""T-54 迴歸測試：量程規則 v2（環景分支加三維檢查，裁決 T-48-F 第 1 點）。

背景：`apply_scope_confidence()` 的 `equirect_multiview` 分支舊碼只比對
「單面牆距是否 > GEOMETRY_SCOPE_MAX_M」。T-48 實測 RacquetballCourt4
（實際 12.19m）估出 16.10×9.39×5.55m，六面牆距皆 ≤10m，卻因為只看單面
牆距而判為 confidence: medium——三維相加後已明顯超出已驗證量程，是預設
路徑的域外安全缺口（Opus V5 情境：覆寫兩面材質後仍 exit 0 輸出 IR）。

量程規則 v2（見 output/geometry_scope/CRITERIA_GEOMETRY_SCOPE_v2.md rule G2）：
環景分支**保留**單面牆距檢查、**另加**與 `metric_depth` 分支同式的三維
（`length_m`／`width_m`／`height_m`）任一超過門檻檢查；`GEOMETRY_SCOPE_MAX_M`
不動、不新增常數；`metric_depth`／`manual`／未知 `dims_source` 三個分支不變。

本測試純函式測試、不載模型，直接組 `RoomEstimate` 呼叫
`apply_scope_confidence()`：
  (a) equirect、六個 wall_distances_m 皆 ≤10、但三維（16.1/9.4/5.6）超標
      → confidence 由 medium 降為 low，notes 含「超出已驗證量程」與
      「length_m=16.1m」（新行為，對舊碼必須 fail）
  (b) equirect、牆距皆 ≤10 且三維皆 ≤10 → confidence 不變、notes 不增
  (c) equirect、單面牆距 12.2 >10（三維皆 ≤10）→ low（現行行為回歸）
  (d) metric_depth、任一維 >10 → low；三維皆 ≤10 → 不變（現行行為回歸）
  (e) manual → 不變、notes 不增

跑法：`python scripts/test_geometry_scope.py`；全部通過 exit 0，
任一失敗 exit 1。

診斷力：(a) 在舊碼（只比單面牆距）上必須 fail——自我檢查已用
`git worktree` 對照 §8 前四欄 commit 實測並附輸出。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb.geometry import RoomEstimate, apply_scope_confidence  # noqa: E402

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'✅' if ok else '❌'} {name}：{detail}")
    if not ok:
        FAILURES.append(name)


def _equirect_estimate(
    wall_distances_m: dict[str, float],
    length_m: float,
    width_m: float,
    height_m: float,
) -> RoomEstimate:
    return RoomEstimate(
        length_m=length_m,
        width_m=width_m,
        height_m=height_m,
        confidence="medium",
        dims_source="equirect_multiview",
        notes=[],
        depth_stats={"wall_distances_m": wall_distances_m},
    )


def case_a() -> None:
    print("【(a)】equirect：六面牆距皆 ≤10m，但三維相加後超標（16.1/9.4/5.6）")
    est = _equirect_estimate(
        wall_distances_m={
            "north": 9.8, "south": 6.3, "east": 4.5,
            "west": 4.9, "ceiling": 5.6, "floor": 2.3,
        },
        length_m=16.1, width_m=9.4, height_m=5.6,
    )
    result = apply_scope_confidence(est)
    check("confidence 降為 low", result.confidence == "low", f"confidence={result.confidence!r}")
    notes_joined = " ".join(result.notes)
    check(
        "notes 含「超出已驗證量程」",
        "超出已驗證量程" in notes_joined,
        f"notes={result.notes!r}",
    )
    check(
        "notes 含 length_m=16.1m",
        "length_m=16.1m" in notes_joined,
        f"notes={result.notes!r}",
    )


def case_b() -> None:
    print("【(b)】equirect：牆距皆 ≤10 且三維皆 ≤10 → 不變")
    est = _equirect_estimate(
        wall_distances_m={
            "north": 9.8, "south": 6.3, "east": 4.5,
            "west": 4.9, "ceiling": 5.6, "floor": 2.3,
        },
        length_m=9.9, width_m=8.0, height_m=3.0,
    )
    result = apply_scope_confidence(est)
    check("confidence 不變（medium）", result.confidence == "medium", f"confidence={result.confidence!r}")
    check("notes 不增（空清單）", result.notes == [], f"notes={result.notes!r}")


def case_c() -> None:
    print("【(c)】equirect：單面牆距 12.2 >10（三維皆 ≤10）→ low（現行行為回歸）")
    est = _equirect_estimate(
        wall_distances_m={
            "north": 12.2, "south": 6.3, "east": 4.5,
            "west": 4.9, "ceiling": 5.6, "floor": 2.3,
        },
        length_m=9.9, width_m=8.0, height_m=3.0,
    )
    result = apply_scope_confidence(est)
    check("confidence 降為 low", result.confidence == "low", f"confidence={result.confidence!r}")
    notes_joined = " ".join(result.notes)
    check(
        "notes 含「超出已驗證量程」",
        "超出已驗證量程" in notes_joined,
        f"notes={result.notes!r}",
    )


def case_d() -> None:
    print("【(d)】metric_depth：任一維 >10 → low；三維皆 ≤10 → 不變（現行行為回歸）")
    est_over = RoomEstimate(
        length_m=12.0, width_m=8.0, height_m=3.0,
        confidence="medium", dims_source="metric_depth",
        notes=[], depth_stats={},
    )
    result_over = apply_scope_confidence(est_over)
    check(
        "confidence 降為 low（length_m=12.0 超標）",
        result_over.confidence == "low",
        f"confidence={result_over.confidence!r}",
    )

    est_ok = RoomEstimate(
        length_m=9.9, width_m=8.0, height_m=3.0,
        confidence="medium", dims_source="metric_depth",
        notes=[], depth_stats={},
    )
    result_ok = apply_scope_confidence(est_ok)
    check("confidence 不變（medium）", result_ok.confidence == "medium", f"confidence={result_ok.confidence!r}")
    check("notes 不增（空清單）", result_ok.notes == [], f"notes={result_ok.notes!r}")


def case_e() -> None:
    print("【(e)】manual → 不變、notes 不增")
    est = RoomEstimate(
        length_m=99.0, width_m=99.0, height_m=99.0,
        confidence="high", dims_source="manual",
        notes=[], depth_stats={},
    )
    result = apply_scope_confidence(est)
    check("confidence 不變（high）", result.confidence == "high", f"confidence={result.confidence!r}")
    check("notes 不增（空清單）", result.notes == [], f"notes={result.notes!r}")


def main() -> int:
    case_a()
    case_b()
    case_c()
    case_d()
    case_e()

    print()
    if FAILURES:
        print(f"❌ {len(FAILURES)} 項失敗：{'、'.join(FAILURES)}")
        return 1
    print("✅ T-54 量程規則 v2 測試全部通過")
    return 0


if __name__ == "__main__":
    sys.exit(main())
