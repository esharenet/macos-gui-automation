#!/usr/bin/env python3
"""权限自检：辅助功能(AX)与屏幕录制状态。用法: env_check.py"""
import Quartz
from ApplicationServices import AXIsProcessTrusted, AXIsProcessTrustedWithOptions, kAXTrustedCheckOptionPrompt

ax = AXIsProcessTrusted()
print("ax_trusted =", ax)
print("screen_cap =", Quartz.CGPreflightScreenCaptureAccess())

if not ax:
    print("ax_trusted=False → 尝试触发系统授权弹窗...")
    AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
    print("请在弹出的系统设置中勾选对应 App 的『辅助功能』，然后重试。")
