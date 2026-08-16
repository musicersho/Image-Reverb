#!/usr/bin/env python3
"""T-03：列印材質吸音係數表（對應 SPEC §6），供人工核對。

資料來源：data/materials.json
本檔同時提供 load_materials() / get_material() / alpha_list() 給其他腳本共用
（例如 gen_ir_manual.py 的 --material 選項）。

用法：
    python scripts/show_materials.py
"""

import json
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MATERIALS_PATH = PROJECT_ROOT / "data" / "materials.json"


# ============================================================
# 資料讀取
# ============================================================


def load_materials(path=MATERIALS_PATH):
    """讀取 materials.json，回傳整份 dict。找不到檔案就直接拋錯，不做靜默 fallback。"""
    if not path.exists():
        raise FileNotFoundError(f"找不到材質表：{path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def get_material(material_id, data=None):
    """依 id 取出單一材質；找不到就拋 KeyError 並列出所有可用 id。"""
    if data is None:
        data = load_materials()
    for mat in data["materials"]:
        if mat["id"] == material_id:
            return mat
    available = ", ".join(m["id"] for m in data["materials"])
    raise KeyError(f"材質表裡沒有 id='{material_id}'。可用的 id：{available}")


def alpha_list(material, band_freqs):
    """把材質的 alpha dict 依頻段順序轉成 list[float]。缺頻段就拋錯。"""
    alphas = []
    for freq in band_freqs:
        key = str(freq)
        if key not in material["alpha"]:
            raise KeyError(f"材質 '{material['id']}' 缺少 {key} Hz 的吸音係數")
        alphas.append(float(material["alpha"][key]))
    return alphas


# ============================================================
# 表格排版（處理中日韓全形字寬度）
# ============================================================


def display_width(text):
    """算字串在等寬終端機上佔的欄位數（全形字算 2 欄）。"""
    width = 0
    for ch in text:
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


def pad(text, width, align="left"):
    """依顯示寬度補空白，讓中英文混排的表格能對齊。"""
    fill = max(0, width - display_width(text))
    if align == "right":
        return " " * fill + text
    return text + " " * fill


def format_freq_label(freq):
    """1000 → 1k、4000 → 4k，其餘照原樣。"""
    if freq >= 1000 and freq % 1000 == 0:
        return f"{freq // 1000}k"
    return str(freq)


# ============================================================
# 檢查
# ============================================================


def check_alphas(data):
    """檢查每個材質的每個頻段 α 是否都落在 0–1 之間，回傳問題清單。"""
    band_freqs = data["band_center_freqs_hz"]
    problems = []
    for mat in data["materials"]:
        for freq in band_freqs:
            key = str(freq)
            if key not in mat["alpha"]:
                problems.append(f"{mat['id']}：缺少 {key} Hz 的係數")
                continue
            value = mat["alpha"][key]
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                problems.append(f"{mat['id']} @ {key} Hz：α 不是數字（{value!r}）")
            elif not (0.0 <= float(value) <= 1.0):
                problems.append(f"{mat['id']} @ {key} Hz：α = {value}，超出 0–1 範圍")
    return problems


def check_required_fields(data):
    """檢查必要欄位是否齊全（id / name_zh / name_en / source）。"""
    required = ("id", "name_zh", "name_en", "source")
    problems = []
    for idx, mat in enumerate(data["materials"]):
        for field in required:
            if not mat.get(field):
                problems.append(f"第 {idx + 1} 筆材質缺少或空白的欄位：{field}")
    return problems


# ============================================================
# 主流程
# ============================================================


def main():
    try:
        data = load_materials()
    except FileNotFoundError as e:
        # 只處理「材質表不存在」這一種狀況，並印出真正的原因
        print(f"❌ 錯誤：{e}")
        print("   請確認 data/materials.json 存在（T-03 的材質表），或先切換回專案根目錄再執行。")
        sys.exit(1)

    band_freqs = data["band_center_freqs_hz"]
    materials = data["materials"]

    # --- 欄寬計算 ---
    id_w = max(display_width("id"), max(display_width(m["id"]) for m in materials))
    zh_w = max(display_width("材質"), max(display_width(m["name_zh"]) for m in materials))
    en_w = max(display_width("name_en"), max(display_width(m["name_en"]) for m in materials))
    conf_w = max(
        display_width("信心"),
        max(display_width(str(m.get("confidence", "-"))) for m in materials),
    )
    band_w = 6  # 每個頻段欄位固定寬度（顯示如 0.014）

    print(f"=== 材質吸音係數表（SPEC §6）｜資料版本 {data.get('version', '?')} ===")
    print(f"來源檔：{MATERIALS_PATH}")
    print(f"頻段（Hz）：{' / '.join(str(f) for f in band_freqs)}")
    print()

    # --- 表頭 ---
    header = (
        pad("id", id_w)
        + "  "
        + pad("材質", zh_w)
        + "  "
        + "".join(pad(format_freq_label(f), band_w, "right") for f in band_freqs)
        + "  "
        + pad("信心", conf_w)
    )
    print(header)
    print("-" * display_width(header))

    # --- 每一列 ---
    for mat in materials:
        row = (
            pad(mat["id"], id_w)
            + "  "
            + pad(mat["name_zh"], zh_w)
            + "  "
            + "".join(
                pad(f"{float(mat['alpha'][str(f)]):.3f}", band_w, "right") for f in band_freqs
            )
            + "  "
            + pad(str(mat.get("confidence", "-")), conf_w)
        )
        print(row)

    print("-" * display_width(header))
    print(f"共 {len(materials)} 種材質")
    print()

    # --- 英文名對照（給對建築聲學表格的人核對用）---
    print("=== 英文名對照 ===")
    for mat in materials:
        print(f"  {pad(mat['id'], id_w)}  {pad(mat['name_en'], en_w)}")
    print()

    # --- 數據出處 ---
    print("=== 數據出處（source）===")
    for mat in materials:
        print(f"[{mat['id']}] {mat['name_zh']}（信心：{mat.get('confidence', '-')}）")
        print(f"  {mat['source']}")
        print()

    # --- 自動檢查 ---
    print("=== 自動檢查 ===")
    field_problems = check_required_fields(data)
    alpha_problems = check_alphas(data)

    if field_problems:
        print(f"✗ 必要欄位檢查：{len(field_problems)} 個問題")
        for p in field_problems:
            print(f"    - {p}")
    else:
        print("✓ 必要欄位檢查：所有材質都有 id / name_zh / name_en / source")

    total_alphas = len(materials) * len(band_freqs)
    if alpha_problems:
        print(f"✗ α 範圍檢查：{len(alpha_problems)} 個問題（共檢查 {total_alphas} 個數值）")
        for p in alpha_problems:
            print(f"    - {p}")
    else:
        print(f"✓ α 範圍檢查：{total_alphas} 個數值全部落在 0–1 之間")

    count_ok = len(materials) >= 11
    if count_ok:
        print(f"✓ 材質數量檢查：{len(materials)} 種（≥ 11 種，符合 SPEC §6 初版涵蓋範圍）")
    else:
        print(f"✗ 材質數量檢查：只有 {len(materials)} 種，未達 SPEC §6 要求的 11 種")

    low_conf = [m["id"] for m in materials if m.get("confidence") == "low"]
    if low_conf:
        print(f"ℹ 標為 low confidence（不確定，用前請注意）：{', '.join(low_conf)}")

    if field_problems or alpha_problems or not count_ok:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
