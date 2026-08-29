#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""T-06 語意分割模型測試

用 nvidia/segformer-b4-finetuned-ade-512-512（ADE20K，150 類）對測試照片做語意分割，
輸出：
  1. 原圖 ＋ 分割疊色圖 並排 PNG（含 top 類別圖例）
  2. 每張照片的「類別 → 佔畫面比例」統計（印在終端 + 寫入 stats.json）

用法：
    python scripts/test_segmentation.py                      # 處理 assets/photos/ 全部圖片
    python scripts/test_segmentation.py <圖片或資料夾> ...    # 指定來源
    python scripts/test_segmentation.py --outdir output/seg  # 指定輸出資料夾
    python scripts/test_segmentation.py --device cpu|mps     # 指定運算裝置
    python scripts/test_segmentation.py --top 15             # 統計列出前 N 類

本腳本只做「觀察與記錄」，不修改任何既有檔案。
"""

import argparse
import json
import os
import sys

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
DEFAULT_MODEL = "nvidia/segformer-b4-finetuned-ade-512-512"
DEFAULT_PHOTO_DIR = "assets/photos"
DEFAULT_OUTDIR = "output/seg"


# ---------------------------------------------------------------- 輸入蒐集

def collect_images(paths):
    """把使用者給的路徑（檔案或資料夾）展開成圖片檔清單。

    回傳 (images, problems)：problems 是給使用者看的清楚錯誤訊息清單。
    """
    images, problems = [], []
    for raw in paths:
        p = os.path.abspath(os.path.expanduser(raw))
        if not os.path.exists(p):
            problems.append("找不到路徑：%s" % raw)
            continue
        if os.path.isdir(p):
            names = sorted(os.listdir(p))
            found = [
                os.path.join(p, n) for n in names
                if os.path.splitext(n)[1].lower() in IMAGE_EXTS
                and os.path.isfile(os.path.join(p, n))
            ]
            if not found:
                problems.append(
                    "資料夾內沒有支援的圖片檔（支援 %s）：%s"
                    % (", ".join(sorted(IMAGE_EXTS)), raw)
                )
            images.extend(found)
        else:
            ext = os.path.splitext(p)[1].lower()
            if ext not in IMAGE_EXTS:
                problems.append(
                    "不是支援的圖片格式（副檔名 '%s'，支援 %s）：%s"
                    % (ext or "無", ", ".join(sorted(IMAGE_EXTS)), raw)
                )
                continue
            images.append(p)
    # 去重但保留順序
    seen, uniq = set(), []
    for p in images:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq, problems


# ---------------------------------------------------------------- 調色盤

def build_palette(n):
    """為 n 個類別產生固定、彼此區別度高的 RGB 調色盤（不依賴亂數種子）。"""
    import colorsys
    palette = []
    for i in range(n):
        # 用 golden-ratio 跳號讓相鄰類別顏色差異大
        h = (i * 0.6180339887) % 1.0
        s = 0.55 + 0.35 * ((i // 3) % 2)
        v = 0.55 + 0.35 * ((i // 2) % 2)
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        palette.append((int(r * 255), int(g * 255), int(b * 255)))
    return palette


# ---------------------------------------------------------------- 主流程

def main():
    ap = argparse.ArgumentParser(
        description="T-06：ADE20K 語意分割測試（SegFormer-B4）"
    )
    ap.add_argument("paths", nargs="*", default=None,
                    help="圖片檔或資料夾（預設 %s）" % DEFAULT_PHOTO_DIR)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR, help="輸出資料夾")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="HuggingFace 模型 id")
    ap.add_argument("--device", default="auto", choices=["auto", "cpu", "mps", "cuda"])
    ap.add_argument("--top", type=int, default=12, help="統計/圖例列出前 N 類")
    ap.add_argument("--min-pct", type=float, default=0.1,
                    help="統計時忽略佔比小於此百分比的類別")
    args = ap.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_paths = args.paths if args.paths else [os.path.join(repo_root, DEFAULT_PHOTO_DIR)]

    images, problems = collect_images(src_paths)
    for msg in problems:
        print("[錯誤] %s" % msg, file=sys.stderr)
    if not images:
        print("[錯誤] 沒有任何可處理的圖片，結束。", file=sys.stderr)
        return 2

    # 延後 import：先把路徑錯誤講清楚，再花時間載入重量級套件
    try:
        import numpy as np
        import torch
        from PIL import Image, ImageDraw
        from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor
    except ImportError as e:
        print("[錯誤] 缺少必要套件（%s）。請先 source .venv/bin/activate。" % e,
              file=sys.stderr)
        return 3

    if args.device == "auto":
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
    else:
        device = args.device
    print("[資訊] 裝置：%s" % device)

    print("[資訊] 載入模型 %s ..." % args.model)
    try:
        processor = SegformerImageProcessor.from_pretrained(args.model)
        model = SegformerForSemanticSegmentation.from_pretrained(args.model)
    except Exception as e:
        print("[錯誤] 模型載入失敗：%s" % e, file=sys.stderr)
        return 4
    model.eval().to(device)

    id2label = model.config.id2label
    n_cls = len(id2label)
    palette = build_palette(n_cls)
    print("[資訊] 類別數：%d" % n_cls)

    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    all_stats = {}
    for path in images:
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            print("[錯誤] 無法讀取圖片 %s：%s" % (path, e), file=sys.stderr)
            continue
        W, H = img.size
        print("\n=== %s (%dx%d) ===" % (name, W, H))

        inputs = processor(images=img, return_tensors="pt").to(device)
        with torch.no_grad():
            logits = model(**inputs).logits            # (1, 150, h/4, w/4)
        # 上採樣回原圖尺寸再取 argmax
        up = torch.nn.functional.interpolate(
            logits.float().cpu(), size=(H, W), mode="bilinear", align_corners=False
        )
        seg = up.argmax(dim=1)[0].numpy().astype(np.int32)

        # ---- 類別佔比統計
        ids, counts = np.unique(seg, return_counts=True)
        total = float(seg.size)
        rows = sorted(
            [(int(i), id2label[int(i)], 100.0 * c / total) for i, c in zip(ids, counts)],
            key=lambda r: -r[2],
        )
        kept = [r for r in rows if r[2] >= args.min_pct]
        print("  類別數（>=%.2f%%）：%d / 出現總類別 %d"
              % (args.min_pct, len(kept), len(rows)))
        for cid, lbl, pct in kept[:args.top]:
            print("    %6.2f%%  [%3d] %s" % (pct, cid, lbl))
        tail = sum(r[2] for r in rows[args.top:])
        if tail > 0:
            print("    %6.2f%%  (其餘 %d 類)" % (tail, len(rows) - args.top))

        all_stats[name] = {
            "file": os.path.relpath(path, repo_root),
            "size": [W, H],
            "num_classes_present": len(rows),
            "classes": [
                {"id": cid, "label": lbl, "pct": round(pct, 3)} for cid, lbl, pct in rows
            ],
        }

        # ---- 疊色圖
        lut = np.array(palette, dtype=np.uint8)        # (150, 3)
        color = lut[seg]                               # (H, W, 3)
        color_img = Image.fromarray(color)
        overlay = Image.blend(img, color_img, 0.55)

        # ---- 並排：左原圖、右疊色圖，下方圖例
        legend_rows = kept[:args.top]
        legend_h = 22 * len(legend_rows) + 16
        canvas = Image.new("RGB", (W * 2 + 12, H + legend_h), (18, 18, 18))
        canvas.paste(img, (0, 0))
        canvas.paste(overlay, (W + 12, 0))
        d = ImageDraw.Draw(canvas)
        for k, (cid, lbl, pct) in enumerate(legend_rows):
            y = H + 8 + k * 22
            x = 8 + (k // 6) * (canvas.width // 2)   # 兩欄
            y = H + 8 + (k % 6) * 22
            d.rectangle([x, y, x + 16, y + 14], fill=palette[cid])
            d.text((x + 24, y + 1), "%5.2f%%  %s" % (pct, lbl), fill=(235, 235, 235))
        d.text((8, 4), "ORIGINAL", fill=(255, 255, 255))
        d.text((W + 20, 4), "SEGMENTATION (ADE20K 150cls)", fill=(255, 255, 255))

        out_png = os.path.join(outdir, "%s_seg.png" % name)
        canvas.save(out_png)
        print("  -> %s" % out_png)

        # 另存純 label map（uint8，供後續管線使用）
        np.save(os.path.join(outdir, "%s_labelmap.npy" % name), seg.astype(np.uint8))

    stats_path = os.path.join(outdir, "stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(
            {"model": args.model, "device": device, "num_classes": n_cls,
             "images": all_stats},
            f, ensure_ascii=False, indent=2,
        )
    print("\n[完成] 統計寫入 %s（%d 張圖）" % (stats_path, len(all_stats)))
    if not all_stats:
        print("[錯誤] 所有圖片皆處理失敗，沒有任何一張成功。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
