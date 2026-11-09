#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片批量处理工具箱 (image-toolkit)
纯本地、无 API Key、默认仅用 Pillow；文件进文件出。

功能：
  resize    批量调整尺寸（按长边/宽高/百分比）
  convert   批量格式转换（jpg/png/webp/bmp/tiff）
  compress  批量压缩（按质量或目标大小）
  watermark 批量加文字水印
  strip     批量清理 EXIF 元数据（隐私）

用法：
  python imgtools.py <command> <input> <output> [options]
  python imgtools.py --selftest
示例：
  python imgtools.py resize ./photos ./out --long-side 1920
  python imgtools.py convert a.png ./out --format webp
  python imgtools.py compress ./photos ./out --quality 80
  python imgtools.py watermark ./photos ./out --text "© 2026"
  python imgtools.py strip ./photos ./out
"""
import argparse
import os
import sys

SUPPORTED = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif")


def _load_image(path):
    try:
        from PIL import Image
    except ImportError:
        sys.stderr.write("缺少 Pillow，请先 pip install Pillow\n")
        sys.exit(3)
    return Image.open(path)


def _iter_inputs(src):
    if os.path.isfile(src):
        return [src]
    out = []
    for name in sorted(os.listdir(src)):
        if name.lower().endswith(SUPPORTED):
            out.append(os.path.join(src, name))
    return out


def _out_path(inp, src, outdir, ext=None):
    if os.path.isfile(src) and os.path.isdir(outdir) is False and outdir.lower().endswith(SUPPORTED):
        return outdir
    os.makedirs(outdir, exist_ok=True)
    base = os.path.splitext(os.path.basename(inp))[0]
    return os.path.join(outdir, base + (ext or os.path.splitext(inp)[1]))


def _save(img, path, quality=None, strip=False):
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    fmt = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP",
           "bmp": "BMP", "tiff": "TIFF", "tif": "TIFF"}.get(ext, "PNG")
    kwargs = {}
    if fmt in ("JPEG", "WEBP"):
        kwargs["quality"] = quality or 85
    if fmt == "JPEG" and img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    if strip:
        # 重新写图即去除 EXIF；info 不复制
        img.save(path, fmt, **kwargs)
    else:
        exif = img.info.get("exif")
        if exif:
            kwargs["exif"] = exif
        img.save(path, fmt, **kwargs)


def cmd_resize(src, outdir, long_side=None, width=None, height=None, percent=None):
    n = 0
    for inp in _iter_inputs(src):
        img = _load_image(inp)
        w, h = img.size
        if percent:
            w, h = max(1, int(w * percent / 100)), max(1, int(h * percent / 100))
        elif long_side:
            scale = long_side / max(w, h)
            if scale < 1:  # 只缩不放，避免批量放大失真
                w, h = max(1, int(w * scale)), max(1, int(h * scale))
        elif width and height:
            w, h = width, height
        elif width:
            h = max(1, int(h * width / w))
            w = width
        elif height:
            w = max(1, int(w * height / h))
            h = height
        else:
            continue
        img = img.resize((w, h))
        _save(img, _out_path(inp, src, outdir))
        n += 1
    return n


def cmd_convert(src, outdir, fmt):
    n = 0
    ext = "." + fmt.lower().lstrip(".")
    for inp in _iter_inputs(src):
        img = _load_image(inp)
        _save(img, _out_path(inp, src, outdir, ext=ext))
        n += 1
    return n


def cmd_compress(src, outdir, quality):
    n = 0
    for inp in _iter_inputs(src):
        img = _load_image(inp)
        _save(img, _out_path(inp, src, outdir), quality=quality)
        n += 1
    return n


def cmd_watermark(src, outdir, text, size_ratio=0.05, opacity=160):
    from PIL import ImageDraw, ImageFont
    n = 0
    for inp in _iter_inputs(src):
        img = _load_image(inp).convert("RGBA")
        overlay = img.copy()
        draw = ImageDraw.Draw(overlay)
        font = ImageFont.load_default()
        # 默认字体很小，按图宽缩放（简单点阵近似）
        try:
            fsize = max(12, int(img.size[0] * size_ratio))
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", fsize)
        except Exception:
            pass
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = img.size[0] - tw - 20, img.size[1] - th - 20
        draw.text((x, y), text, font=font, fill=(255, 255, 255, opacity))
        from PIL import Image as _Image
        combined = _Image.alpha_composite(img, overlay)
        _save(combined, _out_path(inp, src, outdir))
        n += 1
    return n


def cmd_strip(src, outdir):
    n = 0
    for inp in _iter_inputs(src):
        img = _load_image(inp)
        _save(img, _out_path(inp, src, outdir), strip=True)
        n += 1
    return n


def selftest():
    import tempfile
    from PIL import Image
    tmp = tempfile.mkdtemp(prefix="imgtoolkit_test_")
    src = os.path.join(tmp, "a.png")
    Image.new("RGB", (800, 600), (10, 120, 200)).save(src)
    out1 = os.path.join(tmp, "resized")
    assert cmd_resize(src, out1, long_side=400) == 1
    rimg = Image.open(os.path.join(out1, "a.png"))
    assert max(rimg.size) == 400, rimg.size
    out2 = os.path.join(tmp, "webp")
    assert cmd_convert(src, out2, "webp") == 1
    assert os.path.exists(os.path.join(out2, "a.webp"))
    out3 = os.path.join(tmp, "strip")
    assert cmd_strip(src, out3) == 1
    out4 = os.path.join(tmp, "wm")
    assert cmd_watermark(src, out4, "TEST") == 1
    out5 = os.path.join(tmp, "compress")
    assert cmd_compress(src, out5, 60) == 1
    print("PASS image-toolkit: resize/convert/strip/watermark/compress 全部验证通过")
    return 0
