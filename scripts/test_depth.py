#!/usr/bin/env python3
"""T-05 深度估計模型測試

用 Depth-Anything-V2-Small-hf 對 assets/photos/ 的每張照片做單目深度估計，
輸出「原圖 + 深度圖」並排視覺化 PNG，以及深度統計數值。

注意：Depth Anything V2 (relative) 輸出的是 *inverse depth / disparity*，
數值越大代表越近，而且沒有絕對單位（不是公尺）。本腳本所有統計都以原始
disparity 值呈現，不做任何假裝成公尺的換算。

用法：
    python scripts/test_depth.py
    python scripts/test_depth.py --photos-dir assets/photos --out-dir output/depth
    python scripts/test_depth.py --npy-dir /tmp/depth_npy      # 另存原始深度陣列供後續分析
"""

import argparse
import json
import os
import sys
import time

MODEL_ID = "depth-anything/Depth-Anything-V2-Small-hf"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def die(msg, code=1):
    print(f"[錯誤] {msg}", file=sys.stderr)
    sys.exit(code)


def collect_images(photos_dir):
    """列出資料夾中的圖片檔；資料夾不存在或沒圖片時給清楚訊息而非 traceback。"""
    if not os.path.exists(photos_dir):
        die(f"找不到資料夾：{photos_dir}\n     請確認路徑，或用 --photos-dir 指定正確位置。")
    if not os.path.isdir(photos_dir):
        die(f"{photos_dir} 不是資料夾（看起來是一個檔案）。")

    names = sorted(os.listdir(photos_dir))
    images, skipped = [], []
    for n in names:
        p = os.path.join(photos_dir, n)
        if not os.path.isfile(p):
            continue
        if n.startswith("."):
            continue
        if os.path.splitext(n)[1].lower() in IMAGE_EXTS:
            images.append(p)
        else:
            skipped.append(n)

    if skipped:
        print(f"[略過] 非圖片檔 {len(skipped)} 個：{', '.join(skipped)}")
    if not images:
        die(f"{photos_dir} 裡沒有任何支援的圖片檔"
            f"（支援副檔名：{', '.join(sorted(IMAGE_EXTS))}）。")
    return images


def load_image(path):
    from PIL import Image, UnidentifiedImageError
    try:
        return Image.open(path).convert("RGB")
    except UnidentifiedImageError:
        print(f"[略過] {os.path.basename(path)} 無法解析為圖片（可能損毀或副檔名不符）。")
        return None
    except OSError as e:
        print(f"[略過] {os.path.basename(path)} 讀取失敗：{e}")
        return None


def pick_device(requested):
    import torch
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def build_pipeline(device):
    try:
        from transformers import pipeline
    except ImportError:
        die("找不到 transformers 套件。請先 `source .venv/bin/activate` 再執行。")
    try:
        return pipeline("depth-estimation", model=MODEL_ID, device=device)
    except Exception as e:
        die(f"載入模型 {MODEL_ID} 失敗：{type(e).__name__}: {e}\n"
            f"     若是網路問題，請確認模型已下載到 ~/.cache/huggingface/hub。")


def depth_stats(arr):
    """arr 是 disparity（越大越近），單位為模型內部任意尺度。"""
    import numpy as np
    a = arr.astype(np.float64)
    a = a[np.isfinite(a)]
    q = np.percentile(a, [1, 5, 25, 50, 75, 95, 99])
    p1, p5, p25, p50, p75, p95, p99 = (float(v) for v in q)
    # p99/p1 常常爆掉：天空/窗外/消失點會讓 p1 逼近 0 甚至負值，比值就沒有意義。
    # 因此另外提供較穩健的 p95/p5。
    dyn = float(p99 / p1) if p1 > 0.05 else None
    return {
        "min": float(a.min()), "max": float(a.max()),
        "median": p50, "mean": float(a.mean()), "std": float(a.std()),
        "p1": p1, "p5": p5, "p25": p25, "p75": p75, "p95": p95, "p99": p99,
        "dyn_range_p99_over_p1": dyn,
        "dyn_range_p95_over_p5": float(p95 / p5) if p5 > 0.05 else None,
        "frac_nonpositive": float((a <= 0).mean()),
        "frac_below_10pct_of_max": float((a < 0.10 * a.max()).mean()),
        "frac_above_50pct_of_max": float((a > 0.50 * a.max()).mean()),
    }


def core_stats(arr, x=(0.05, 0.95), y=(0.08, 0.85)):
    """裁掉上下 UI/黑邊與左右黑邊後的統計，用來看『真實畫面內容』的深度分佈。"""
    import numpy as np
    h, w = arr.shape
    core = arr[int(y[0] * h):int(y[1] * h), int(x[0] * w):int(x[1] * w)]
    p5, p50, p95 = (float(v) for v in np.percentile(core, [5, 50, 95]))
    return {"crop_x": list(x), "crop_y": list(y), "p5": p5, "median": p50, "p95": p95,
            "p95_over_p5": float(p95 / p5) if p5 > 0.05 else None}


def visualize(img, depth_arr, stats, title, out_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    h, w = depth_arr.shape
    aspect = h / w
    fig_w = 14
    fig, axes = plt.subplots(1, 2, figsize=(fig_w, fig_w / 2 * aspect + 1.6))

    axes[0].imshow(img)
    axes[0].set_title("原圖 / original", fontsize=11)
    axes[0].axis("off")

    im = axes[1].imshow(depth_arr, cmap="inferno")
    axes[1].set_title("深度圖 (inverse depth：亮=近, 暗=遠)", fontsize=11)
    axes[1].axis("off")
    cb = fig.colorbar(im, ax=axes[1], fraction=0.046, pad=0.02)
    cb.set_label("disparity (relative, no unit)", fontsize=9)

    dyn = stats["dyn_range_p99_over_p1"]
    dyn_s = f"{dyn:.1f}x" if dyn is not None else "n/a (p1<=0.05)"
    sub = ("min={min:.2f}  max={max:.2f}  median={median:.2f}  "
           "mean={mean:.2f}  std={std:.2f}\n"
           "p1={p1:.2f}  p25={p25:.2f}  p75={p75:.2f}  p99={p99:.2f}  "
           "p99/p1=").format(**stats) + dyn_s + f"  p95/p5={stats['p95']/max(stats['p5'],1e-6):.1f}x"
    fig.suptitle(title, fontsize=13)
    fig.text(0.5, 0.015, sub, ha="center", fontsize=10, family="monospace")
    fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(out_path, dpi=110)
    plt.close(fig)


def run_probe(args):
    """--probe 模式：對單一張圖列出指定矩形區域的 disparity 統計（REPORT 的數字來源）。"""
    import numpy as np
    path = args.probe_image
    if not os.path.isfile(path):
        die(f"--probe-image 指定的檔案不存在：{path}")
    img = load_image(path)
    if img is None:
        die(f"{path} 無法讀取為圖片。")
    pipe = build_pipeline(pick_device(args.device))
    out = pipe(img)
    arr = out["predicted_depth"]
    if hasattr(arr, "detach"):
        arr = arr.detach().to("cpu").float().numpy()
    arr = np.squeeze(np.asarray(arr))
    h, w = arr.shape
    print(f"# {os.path.basename(path)}  depth shape={h}x{w}  "
          f"(座標為 0~1 比例：label:x0,x1,y0,y1)")
    for spec in args.probe:
        try:
            label, nums = spec.split(":", 1)
            x0, x1, y0, y1 = (float(v) for v in nums.split(","))
        except ValueError:
            die(f"--probe 格式錯誤：{spec!r}，應為 label:x0,x1,y0,y1（0~1 比例）")
        s = arr[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]
        if s.size == 0:
            print(f"  {label:28s} (空區域，請檢查座標)")
            continue
        print(f"  {label:28s} mean={s.mean():7.3f} median={np.median(s):7.3f} "
              f"min={s.min():7.3f} max={s.max():7.3f}")


def main():
    ap = argparse.ArgumentParser(description="T-05 深度估計模型測試")
    ap.add_argument("--photos-dir", default="assets/photos")
    ap.add_argument("--out-dir", default="output/depth")
    ap.add_argument("--npy-dir", default=None,
                    help="若指定，另存每張圖的原始 disparity 陣列 .npy（供後續分析）")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    ap.add_argument("--probe-image", default=None,
                    help="單張圖 ROI 探測模式：指定圖片路徑")
    ap.add_argument("--probe", action="append", default=[],
                    metavar="LABEL:x0,x1,y0,y1",
                    help="搭配 --probe-image，指定要量測的矩形（0~1 比例），可重複")
    args = ap.parse_args()

    if args.probe_image:
        if not args.probe:
            die("--probe-image 需要至少一個 --probe LABEL:x0,x1,y0,y1")
        run_probe(args)
        return
    if args.probe:
        die("--probe 需要搭配 --probe-image 使用。")

    # 中文字型（macOS 內建），避免圖上出現豆腐字
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = [
        "Heiti TC", "PingFang HK", "Arial Unicode MS", "DejaVu Sans"]
    matplotlib.rcParams["axes.unicode_minus"] = False

    import numpy as np

    images = collect_images(args.photos_dir)
    os.makedirs(args.out_dir, exist_ok=True)
    if args.npy_dir:
        os.makedirs(args.npy_dir, exist_ok=True)

    device = pick_device(args.device)
    print(f"[資訊] 模型 {MODEL_ID}，device={device}，共 {len(images)} 張圖")
    pipe = build_pipeline(device)

    results = []
    for i, path in enumerate(images, 1):
        name = os.path.basename(path)
        img = load_image(path)
        if img is None:
            continue
        t0 = time.time()
        try:
            out = pipe(img)
        except Exception as e:
            print(f"[略過] {name} 推論失敗：{type(e).__name__}: {e}")
            continue
        dt = time.time() - t0

        arr = out["predicted_depth"]
        if hasattr(arr, "detach"):
            arr = arr.detach().to("cpu").float().numpy()
        arr = np.squeeze(np.asarray(arr))

        st = depth_stats(arr)
        st["core"] = core_stats(arr)
        stem = os.path.splitext(name)[0]
        vis_path = os.path.join(args.out_dir, f"{stem}_depth.png")
        visualize(img, arr, st, f"{name}   ({img.size[0]}x{img.size[1]})", vis_path)

        if args.npy_dir:
            np.save(os.path.join(args.npy_dir, f"{stem}.npy"), arr.astype(np.float32))

        st.update({"file": name, "size": list(img.size),
                   "depth_shape": list(arr.shape), "infer_sec": round(dt, 2)})
        results.append(st)
        d = st["dyn_range_p99_over_p1"]
        print(f"[{i}/{len(images)}] {name}  {dt:.2f}s  "
              f"min={st['min']:.2f} max={st['max']:.2f} median={st['median']:.2f} "
              f"p99/p1={f'{d:.1f}x' if d is not None else 'n/a'} "
              f"core_p95/p5={st['core']['p95_over_p5']:.1f}x  -> {vis_path}")

    if not results:
        die("沒有任何圖片成功處理。")

    json_path = os.path.join(args.out_dir, "depth_stats.json")
    with open(json_path, "w") as f:
        json.dump({"model": MODEL_ID, "device": device,
                   "note": "predicted_depth 為 inverse depth (disparity)，越大越近，無絕對單位",
                   "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\n[完成] {len(results)} 張，統計寫入 {json_path}")


if __name__ == "__main__":
    main()
