#!/usr/bin/env python3
"""
image-toolkit MCP Server — 本地图片批量处理（不联网、不上传，文件进文件出）

暴露工具：
  image_resize(input_path, output_dir, long_side/width/height/percent)
  image_convert(input_path, output_dir, fmt)
  image_compress(input_path, output_dir, quality)
  image_watermark(input_path, output_dir, text, size_ratio, opacity)
  image_strip(input_path, output_dir)   # 去 EXIF 隐私信息
  image_selftest()

基于 image-toolkit（image_core.py，纯 Pillow）。
传输：stdio（默认）/ streamable-http（--transport streamable-http --port N）
兼容 mcp SDK 1.x（FastMCP）与 2.x（MCPServer）。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from . import image_core as core
except ImportError:
    import image_core as core

try:  # mcp 2.x
    from mcp.server.mcpserver import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

mcp = MCPServer(
    name="image-toolkit",
    instructions=(
        "本地图片批量处理服务，绝不访问网络、不上传图片，照片不离开本机。"
        "支持整文件夹或单文件：resize（按长边/宽高/百分比，只缩不放）、"
        "convert（jpg/png/webp/bmp/tiff 互转）、compress（质量压缩）、"
        "watermark（右下角半透明文字水印）、strip（清除 EXIF 拍摄地点设备）。"
        "所有路径必须是服务器本地绝对路径。"
    ),
)


def _resolve(p):
    return os.path.abspath(os.path.expanduser(p))


@mcp.tool(
    name="image_resize",
    description=(
        "批量调整图片尺寸。input_path 可为单文件或目录；输出到 output_dir。"
        "四选一：long_side（按长边等比缩，只缩不放）、width+height（精确）、"
        "width（定宽等比）、percent（百分比，如 50 表示缩到一半）。"
        "返回处理张数与输出目录。"
    ),
)
def image_resize(input_path: str, output_dir: str, long_side: int = 0,
                 width: int = 0, height: int = 0, percent: float = 0) -> dict:
    src = _resolve(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"输入不存在: {src}")
    out = _resolve(output_dir)
    os.makedirs(out, exist_ok=True)
    n = core.cmd_resize(src, out, long_side=long_side or None,
                        width=width or None, height=height or None,
                        percent=percent or None)
    return {"ok": True, "processed": n, "input": src, "output_dir": out}


@mcp.tool(
    name="image_convert",
    description=(
        "批量格式转换，fmt 取 jpg/png/webp/bmp/tiff（不带点也行）。"
        "input_path 可为单文件或目录。"
    ),
)
def image_convert(input_path: str, output_dir: str, fmt: str = "webp") -> dict:
    src = _resolve(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"输入不存在: {src}")
    out = _resolve(output_dir)
    os.makedirs(out, exist_ok=True)
    n = core.cmd_convert(src, out, fmt)
    return {"ok": True, "processed": n, "format": fmt.lstrip(".").lower(),
            "input": src, "output_dir": out}


@mcp.tool(
    name="image_compress",
    description="批量按质量压缩（quality 1-100，越小文件越小，常用 60-85）。",
)
def image_compress(input_path: str, output_dir: str, quality: int = 85) -> dict:
    src = _resolve(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"输入不存在: {src}")
    quality = max(1, min(100, int(quality)))
    out = _resolve(output_dir)
    os.makedirs(out, exist_ok=True)
    n = core.cmd_compress(src, out, quality)
    return {"ok": True, "processed": n, "quality": quality,
            "input": src, "output_dir": out}


@mcp.tool(
    name="image_watermark",
    description=(
        "批量加右下角半透明文字水印。text 为水印文字；size_ratio 为字号占图宽比例"
        "（默认 0.05）；opacity 0-255（默认 160）。"
    ),
)
def image_watermark(input_path: str, output_dir: str, text: str,
                    size_ratio: float = 0.05, opacity: int = 160) -> dict:
    if not text:
        raise ValueError("text 水印文字不能为空")
    src = _resolve(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"输入不存在: {src}")
    out = _resolve(output_dir)
    os.makedirs(out, exist_ok=True)
    n = core.cmd_watermark(src, out, text, size_ratio=float(size_ratio),
                           opacity=int(opacity))
    return {"ok": True, "processed": n, "watermark": text,
            "input": src, "output_dir": out}


@mcp.tool(
    name="image_strip",
    description="批量清除 EXIF 元数据（拍摄地点、设备、时间等隐私信息），重写图片。",
)
def image_strip(input_path: str, output_dir: str) -> dict:
    src = _resolve(input_path)
    if not os.path.exists(src):
        raise FileNotFoundError(f"输入不存在: {src}")
    out = _resolve(output_dir)
    os.makedirs(out, exist_ok=True)
    n = core.cmd_strip(src, out)
    return {"ok": True, "processed": n, "stripped_exif": True,
            "input": src, "output_dir": out}


@mcp.tool(
    name="image_selftest",
    description="运行核心引擎自检（resize/convert/strip/watermark/compress 五项）。",
)
def image_selftest() -> dict:
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = core.selftest()
    return {"ok": rc == 0, "detail": buf.getvalue().strip()}


def main():
    import argparse
    ap = argparse.ArgumentParser(description="image-toolkit MCP server")
    ap.add_argument("--transport", default="stdio",
                    choices=["stdio", "streamable-http", "sse"])
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8768)
    args = ap.parse_args()
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
