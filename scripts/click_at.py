#!/usr/bin/env python3
"""强制激活 App 并按坐标真实鼠标点击（可选客观验证）。
用法:
  click_at.py "App名"                          # 仅强制激活(跨空间切前台)
  click_at.py "App名" X Y                       # 激活 + 点击
  click_at.py "App名" X Y --verify-port 7890 --expect open|closed
  click_at.py "App名" X Y --verify-process 名称 --expect present|absent
"""
import argparse
import socket
import subprocess
import sys
import time

import Quartz
from AppKit import (
    NSWorkspace,
    NSApplicationActivateAllWindows,
    NSApplicationActivateIgnoringOtherApps,
)


def port_open(p, host="127.0.0.1", t=0.4):
    try:
        with socket.create_connection((host, p), timeout=t):
            return True
    except Exception:
        return False


def process_present(name):
    r = subprocess.run(["pgrep", "-f", name], capture_output=True, text=True)
    return bool(r.stdout.strip())


def click(x, y):
    pt = Quartz.CGPoint(x, y)
    Quartz.CGEventPost(
        Quartz.kCGHIDEventTap,
        Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseDown, pt, Quartz.kCGMouseButtonLeft),
    )
    time.sleep(0.08)
    Quartz.CGEventPost(
        Quartz.kCGHIDEventTap,
        Quartz.CGEventCreateMouseEvent(None, Quartz.kCGEventLeftMouseUp, pt, Quartz.kCGMouseButtonLeft),
    )


def wait_until(check, expect, timeout_s=6.0, label=""):
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        now = check()
        if now == expect:
            print(f"  ✓ {label} -> {now} (期望 {expect})")
            return True
        time.sleep(0.5)
    print(f"  ✗ {label} -> {now} (期望 {expect}) 超时")
    return False


def main():
    ap = argparse.ArgumentParser(description="激活+点击+验证")
    ap.add_argument("app")
    ap.add_argument("x", nargs="?", type=int)
    ap.add_argument("y", nargs="?", type=int)
    ap.add_argument("--verify-port", type=int)
    ap.add_argument("--verify-process", type=str)
    ap.add_argument("--expect", choices=["open", "closed", "present", "absent"])
    a = ap.parse_args()

    app = next(
        (x for x in NSWorkspace.sharedWorkspace().runningApplications() if x.localizedName() == a.app),
        None,
    )
    if app is None:
        print(f"APP NOT RUNNING: {a.app}")
        return 1
    app.activateWithOptions_(NSApplicationActivateAllWindows | NSApplicationActivateIgnoringOtherApps)
    time.sleep(1.2)
    print(f"activated {a.app}")

    if a.x is None or a.y is None:
        return 0

    click(a.x, a.y)
    print(f"clicked ({a.x}, {a.y})")

    ok = True
    if a.verify_port is not None and a.expect in ("open", "closed"):
        ok = wait_until(lambda: "open" if port_open(a.verify_port) else "closed",
                        a.expect, label=f"port {a.verify_port}")
    if a.verify_process is not None and a.expect in ("present", "absent"):
        ok = wait_until(lambda: "present" if process_present(a.verify_process) else "absent",
                        a.expect, label=f"process {a.verify_process}") and ok
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
