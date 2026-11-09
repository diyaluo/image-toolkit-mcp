#!/usr/bin/env python3
"""stdio 三重验证：initialize 握手 + notifications/initialized + tools/list + selftest 工具调用。"""
import json, subprocess, sys, os

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))


def send(proc, obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def read_msg(proc):
    line = proc.stdout.readline()
    if not line:
        raise RuntimeError("server closed stdout")
    return json.loads(line)


def main():
    proc = subprocess.Popen(
        [sys.executable, "-m", "image_toolkit_mcp.server"],
        cwd=ROOT, env=ENV, stdin=subprocess.PIPE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        send(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18",
                               "capabilities": {},
                               "clientInfo": {"name": "test", "version": "0"}}})
        init = read_msg(proc)
        assert "result" in init and "serverInfo" in init["result"], init
        print("initialize OK:", init["result"]["serverInfo"])

        send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

        send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tl = read_msg(proc)
        tools = [t["name"] for t in tl["result"]["tools"]]
        print("tools/list:", tools)
        expect = {"image_resize", "image_convert", "image_compress",
                  "image_watermark", "image_strip", "image_selftest"}
        assert expect.issubset(set(tools)), f"missing: {expect - set(tools)}"

        send(proc, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "image_selftest", "arguments": {}}})
        call = read_msg(proc)
        payload = call["result"]["content"][0]["text"]
        print("selftest call:", payload[:200])
        parsed = json.loads(payload)
        assert parsed.get("ok") is True, payload
        print("\nALL STDIO CHECKS PASSED")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
