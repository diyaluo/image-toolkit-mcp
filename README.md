# image-toolkit-mcp

Local, offline batch image processing as an MCP (Model Context Protocol) server.
100% local — no API key, no network, images never leave the machine. Built on Pillow.

## Tools

| Tool | Purpose |
|---|---|
| `image_resize` | Batch resize by long edge / explicit width-height / percent (shrink-only) |
| `image_convert` | Convert between jpg / png / webp / bmp / tiff |
| `image_compress` | Quality-based compression (1-100) |
| `image_watermark` | Semi-transparent corner text watermark |
| `image_strip` | Remove EXIF metadata (camera, GPS, timestamp) for privacy |
| `image_selftest` | Run the built-in engine self-test |

Each tool takes a local file or a whole folder and writes to an output directory.

## Run (stdio)

```bash
pip install -e .
python -m image_toolkit_mcp.server
```

## Run (Docker)

```bash
docker run -i --rm -v /path/to/images:/data ghcr.io/diyaluo/image-toolkit-mcp:v0.1.0
```

## License

MIT
