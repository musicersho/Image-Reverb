#!/usr/bin/env python3
"""T-10 前處理迴歸測試 —— 地雷第 11 條：equirect 極點均勻列不能被黑邊裁切吃掉。
T-37 新增：地雷 #16（`is_equirect()` 純長寬比誤判 2:1 透視照為環景）迴歸測試。

前兩支（極點列存活／letterbox 非環景）不依賴外部素材，全部合成圖片，可在任何
clone 上重跑；T-37 新增的合成案例同樣不依賴外部素材。TunnelToHell／4 張真環景
的資產測試需要 `assets/reference_irs/`（不在 git 裡），若素材不存在會清楚印出
略過訊息並繼續（不是靜默通過，也不會讓沒有素材的乾淨 clone 失敗）。

用法：
    python scripts/test_preprocess.py
"""

import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.image_reverb.preprocess import is_equirect, load_image, preprocess_image  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent


def die(msg, code=1):
    print(f"[錯誤] {msg}", file=sys.stderr)
    sys.exit(code)


def make_synthetic_equirect(width=1024, height=512, pole_rows=30, seed=0):
    """模擬 equirect：上下各 pole_rows 列純色（天頂/天底），中間隨機紋理。"""
    rng = np.random.default_rng(seed)
    body = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    body[:pole_rows, :, :] = 40  # 天頂：均勻深灰
    body[height - pole_rows :, :, :] = 220  # 天底：均勻淺灰
    return Image.fromarray(body)


def make_synthetic_letterbox_photo(width=800, height=450, bar_px=60, seed=1):
    """模擬非環景照片（長寬比遠離 2:1）左右有純黑 letterbox。"""
    rng = np.random.default_rng(seed)
    img = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    img[:, :bar_px, :] = 0
    img[:, width - bar_px :, :] = 0
    return Image.fromarray(img)


def test_equirect_poles_survive():
    """核心迴歸案例：極點均勻列不應被裁掉，環景判定不應被裁切動搖。"""
    print("[1/2] 合成極點均勻的 equirect 影像 ...")
    img = make_synthetic_equirect()
    top_rows_before = np.asarray(img)[:30].copy()
    bottom_rows_before = np.asarray(img)[-30:].copy()

    with tempfile.TemporaryDirectory() as tmp:
        photo_path = Path(tmp) / "synthetic_equirect.png"
        img.save(photo_path)
        out_dir = Path(tmp) / "out"

        summary = preprocess_image(photo_path, output_dir=out_dir)

        if not summary["is_equirect"]:
            die("極點均勻的合成 equirect 被誤判為非環景（黑邊裁切吃掉極點的地雷第 11 條回歸了）")
        print("    ✓ 判定為環景")

        b = summary["border_crop"]
        if (b["crop_top_px"], b["crop_bottom_px"], b["crop_left_px"], b["crop_right_px"]) != (0, 0, 0, 0):
            die(f"環景不應被裁黑邊，但 border_crop 顯示有裁切：{b}")
        print("    ✓ 黑邊裁切已完全跳過（crop_*_px 全為 0）")

        cropped_path = Path(summary["cropped_equirect"])
        cropped = np.asarray(Image.open(cropped_path))
        if cropped.shape[:2] != (512, 1024):
            die(f"裁切後尺寸應與原圖相同 (512, 1024)，實際 {cropped.shape[:2]}")
        if not np.array_equal(cropped[:30], top_rows_before):
            die("天頂（前 30 列）像素在前處理後被改動，極點被裁到了")
        if not np.array_equal(cropped[-30:], bottom_rows_before):
            die("天底（後 30 列）像素在前處理後被改動，極點被裁到了")
        print("    ✓ 天頂/天底像素完整保留，未被誤裁")

        views = summary.get("views", {})
        if len(views) != 6:
            die(f"應輸出 6 個透視視角，實際 {len(views)}")
        for name, v in views.items():
            if not Path(v["path"]).is_file():
                die(f"視角 {name} 的輸出檔不存在：{v['path']}")
        print("    ✓ 6 個透視視角皆已輸出")


def test_non_equirect_letterbox_still_cropped():
    """反例：非環景照片的黑邊裁切邏輯不能被這次改動連帶破壞。"""
    print("[2/2] 合成非環景 letterbox 照片 ...")
    img = make_synthetic_letterbox_photo()

    with tempfile.TemporaryDirectory() as tmp:
        photo_path = Path(tmp) / "synthetic_letterbox.png"
        img.save(photo_path)
        out_dir = Path(tmp) / "out"

        summary = preprocess_image(photo_path, output_dir=out_dir)

        if summary["is_equirect"]:
            die("長寬比遠離 2:1 的照片不應被判為環景")
        print("    ✓ 判定為非環景")

        b = summary["border_crop"]
        if b["crop_left_px"] < 55 or b["crop_right_px"] < 55:
            die(f"非環景的黑邊裁切應正常運作，但左右裁切量異常偏小：{b}")
        print(f"    ✓ 黑邊裁切正常運作（左{b['crop_left_px']}px 右{b['crop_right_px']}px）")


def make_synthetic_2to1_nonuniform_poles(width=1024, height=512, seed=2):
    """模擬地雷 #16 的核心案例：長寬比剛好 2:1，但首/尾列不是天頂/天底、
    是正常場景內容（隨機紋理，相鄰像素差異大）——不應被判為環景。"""
    rng = np.random.default_rng(seed)
    body = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    return Image.fromarray(body)


def make_synthetic_uniform_pole_equirect(width=1024, height=512, pole_rows=1, seed=3):
    """模擬極點列均勻的合成 equirect：只有首/尾各一列是均勻純色（天頂/天底），
    中間隨機紋理，長寬比 2:1。"""
    rng = np.random.default_rng(seed)
    body = rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)
    body[:pole_rows, :, :] = 90
    body[height - pole_rows :, :, :] = 200
    return Image.fromarray(body)


def test_is_equirect_synthetic_pole_uniformity():
    """地雷 #16 迴歸案例（合成，不依賴資產）：2:1 但極點列不均勻 → False；
    極點列均勻的合成 equirect → True。對舊碼（純長寬比判定）必定 fail——
    舊碼會把兩者都判為 True，因為兩者長寬比都是 2:1。"""
    print("[3/4] 合成「2:1 但極點列不均勻」影像（地雷 #16 核心案例）...")
    nonuniform = make_synthetic_2to1_nonuniform_poles()
    if is_equirect(nonuniform):
        die("長寬比 2:1 但極點列不均勻的合成影像被誤判為環景（地雷 #16 回歸了）")
    print("    ✓ 正確判為非環景")

    print("[4/4] 合成極點列均勻的 equirect（首尾各一列純色）...")
    uniform = make_synthetic_uniform_pole_equirect()
    if not is_equirect(uniform):
        die("極點列均勻的合成 equirect 被誤判為非環景")
    print("    ✓ 正確判為環景")


def test_is_equirect_real_assets():
    """地雷 #16 的真實案例：TunnelToHell.jpg（2592×1296，長寬比巧合 2.000 的
    一般透視照）必須判為 False；4 張真環景（CathedralRoom／DivorceBeach／
    RacquetballCourt4／SteinmanHall）必須全部判為 True。依賴
    `assets/reference_irs/`（不在 git 裡），素材不存在時清楚印出略過訊息。"""
    cases = [
        ("TunnelToHell", "assets/reference_irs/tunnel_to_hell/TunnelToHell.jpg", False),
        ("CathedralRoom", "assets/reference_irs/cathedral_room_shasta_lake_caverns/CathedralRoom.jpg", True),
        ("DivorceBeach", "assets/reference_irs/divorce_beach/DivorceBeach.jpg", True),
        ("RacquetballCourt4", "assets/reference_irs/racquetball_court_4/RacquetballCourt4.jpg", True),
        ("SteinmanHall", "assets/reference_irs/steinman_hall/SteinmanHall.jpg", True),
    ]
    missing = [name for name, rel, _ in cases if not (REPO_ROOT / rel).is_file()]
    if missing:
        print(f"[資產測試] 略過（{', '.join(missing)} 不存在——素材未進版控，"
              "全新 clone 需照 assets/SOURCES.md 重新下載）。")
        return

    print("[資產測試] 5 張真實照片的 is_equirect() 判定 ...")
    for name, rel, expected in cases:
        img = load_image(REPO_ROOT / rel)
        actual = is_equirect(img)
        if actual != expected:
            die(f"{name} 判定為 {actual}，預期 {expected}（地雷 #16 回歸了）")
        print(f"    ✓ {name} → {actual}")


def main():
    test_equirect_poles_survive()
    test_non_equirect_letterbox_still_cropped()
    test_is_equirect_synthetic_pole_uniformity()
    test_is_equirect_real_assets()
    print("\n全部通過：equirect 極點不再被誤裁，非環景黑邊裁切行為未被破壞，"
          "地雷 #16（2:1 透視照誤判環景）已修正。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
