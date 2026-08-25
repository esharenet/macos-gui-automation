#!/usr/bin/env python3
"""枚举目标 App 的 AXButton，可选直接 AXPress 第 N 个。
用法:
  ax_find_buttons.py "App名"               # 列出所有按钮
  ax_find_buttons.py "App名" --press 3     # 直接按下第 3 个按钮
"""
import argparse
import sys

from AppKit import NSWorkspace
from ApplicationServices import (
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeValue,
    AXUIElementPerformAction,
    kAXWindowsAttribute,
    kAXChildrenAttribute,
    kAXRoleAttribute,
    kAXTitleAttribute,
    kAXDescriptionAttribute,
    kAXPressAction,
)


def get_pid(name):
    for a in NSWorkspace.sharedWorkspace().runningApplications():
        if a.localizedName() == name:
            return a.processIdentifier()
    return None


def attr(el, a):
    err, v = AXUIElementCopyAttributeValue(el, a, None)
    return v if err == 0 else None


def walk(el, depth, out, seen):
    try:
        k = id(el)
    except Exception:
        k = hash(el)
    if k in seen or depth > 12:
        return
    seen.add(k)
    if attr(el, kAXRoleAttribute) == "AXButton":
        out.append(el)
    for c in (attr(el, kAXChildrenAttribute) or []):
        walk(c, depth + 1, out, seen)


def main():
    ap = argparse.ArgumentParser(description="AX 按钮枚举/触发")
    ap.add_argument("app", help="App 显示名称，如 FlClash")
    ap.add_argument("--press", type=int, help="按第 N 个按钮（从 1 起）")
    a = ap.parse_args()

    pid = get_pid(a.app)
    if pid is None:
        print(f"APP NOT RUNNING: {a.app}")
        sys.exit(1)

    app = AXUIElementCreateApplication(pid)
    btns = []
    for w in (attr(app, kAXWindowsAttribute) or []):
        walk(w, 0, btns, set())

    print(f"{a.app} (pid={pid}): {len(btns)} AXButton(s)")
    for i, b in enumerate(btns, 1):
        t = attr(b, kAXTitleAttribute)
        d = attr(b, kAXDescriptionAttribute)
        print(f"  [{i}] title={t!r} desc={d!r}")

    if a.press:
        if 1 <= a.press <= len(btns):
            err = AXUIElementPerformAction(btns[a.press - 1], kAXPressAction)
            print(f"AXPress #{a.press} -> err={err} (0=成功)")
        else:
            print("press 索引越界")
    return 0


if __name__ == "__main__":
    sys.exit(main())
