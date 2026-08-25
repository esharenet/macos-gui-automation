#!/usr/bin/env python3
"""截全屏（screencapture 失效时的替代）。用法: screenshot.py [out.png]"""
import sys

import Quartz

out = sys.argv[1] if len(sys.argv) > 1 else "/tmp/shot.png"
img = Quartz.CGWindowListCreateImage(
    Quartz.CGRectNull,
    Quartz.kCGWindowListOptionOnScreenOnly,
    Quartz.kCGNullWindowID,
    Quartz.kCGWindowImageDefault,
)
if img is None:
    print("capture failed")
    sys.exit(1)
dest = Quartz.CGImageDestinationCreateWithURL(
    Quartz.CFURLCreateWithFileSystemPath(None, out, Quartz.kCFURLPOSIXPathStyle, False),
    "public.png", 1, None,
)
Quartz.CGImageDestinationAddImage(dest, img, None)
Quartz.CGImageDestinationFinalize(dest)
print("saved", out)
