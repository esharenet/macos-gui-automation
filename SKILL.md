---
title: "AI Agent 可操作的 macOS GUI 自动化（点任意原生 App 按钮）"
summary: "macOS GUI automation for AI Agents: click buttons in any native macOS app with real mouse events (PyObjC + Quartz/AX), bypassing the TCC wall that blocks osascript/System Events. 让 AI Agent 用真实鼠标点击任意原生 App 的按钮/开关，绕开 TCC 对 osascript 的封锁。"
agent_created: true
read_when:
  - 需要自动点击 macOS 原生 App 的按钮/开关（启动、停止、确定、保存、切换等）
  - osascript / System Events 报 -10004 权限违例
  - screencapture 报 could not create image from display
  - 需要模拟人类鼠标/键盘操作原生应用
---

# AI Agent 可操作的 macOS GUI 自动化（点任意原生 App 按钮）
# macOS GUI Automation for AI Agents — click any button in any native app

> 中文（English below）｜文档：`README.md`（发布仓库内完整双语版）

## 为什么不用 osascript（核心结论）
| 路径 | 结果 | 原因 |
|---|---|---|
| `osascript` + System Events | `-10004 权限违例` | TCC 封禁后台/沙盒进程的 UI 自动化；重开权限+重启宿主未必生效 |
| `screencapture` | 有时 `could not create image from display` | 宿主重启后屏幕录制 TCC 身份可能失效 |
| **PyObjC + Quartz/AX 底层 API** | ✅ 可用 | `AXIsProcessTrusted()`==True 时，`CGEventPost` 真实鼠标/键盘与 AX API 全通，无需 osascript 中转 |

## 环境准备（一次性）
```bash
[ -d "$HOME/.workbuddy/binaries/python/envs/gui" ] || $HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m venv "$HOME/.workbuddy/binaries/python/envs/gui"
"$HOME/.workbuddy/binaries/python/envs/gui/bin/pip" install -q pyobjc-framework-Quartz pyobjc-framework-ApplicationServices pyobjc-framework-Cocoa Pillow
```

## 标准工作流
```
0) env_check.py           权限自检（宿主重启后 TCC 身份会变，务必每次重查）
1) 定位按钮（三法，按优先级）
   A. AX 树:   ax_find_buttons.py "App" [--press N]      ← AppKit 标准控件首选
   B. 实时CV:  screenshot.py + PIL 颜色/形状识别           ← 窗口可见可截时
   C. 参考截图+相对坐标换算:                                ← 实时截图被 TCC 挡时兜底
      abs_x = Wnd.X + rx*Wnd.W;  abs_y = Wnd.Y + ry*Wnd.H
      (rx,ry) 取自历史参考图里按钮相对窗口的位置; Wnd.* 用 CGWindowListCopyWindowInfo 实时取
2) 强制激活:  click_at.py "App" --activate-only
      NSRunningApplication.activateWithOptions_(AllWindows | IgnoringOtherApps)
      ← 全屏/多空间下必须用此选项，普通 osascript activate 切不过去
3) 真实点击:  click_at.py "App" X Y --verify-port 7890 --expect open|closed
4) 客观验证:  端口/进程/文件（勿看 UI）
5) 收尾:      切回原前台 App
```

## 彻底退出 App
```bash
osascript -e 'quit app "App名"'   # 报 -10004 则:
kill <PID>                         # SIGTERM（同用户无需 TCC）
```

## 常见问题与解法（详见 README FAQ）
- `-10004` → 走 PyObjC 底层 API，不走 osascript
- 截图被挡/只看到壁纸 → 参考截图 + 坐标换算
- 窗口在别的空间/被全屏遮挡 → IgnoringOtherApps 强制激活
- Flutter/Electron AX 稀疏、AXPress 无效 → CGEvent 按坐标真实点击
- 点击没反应 → 先重查窗口当前 bounds（重启后位置会变）+ 等渲染完成

## 已验证案例：FlClash 启停（2026-08-25）
- 按钮：仪表盘右下角粉色 ▶，窗口内相对位置 ≈ (0.932, 0.921)
- 验证：`socket.create_connection(('127.0.0.1',7890),0.5)` 双向切换，同一点=启停开关
- 退出：`kill` 后主程序与 FlClashCore 均退出
- 脚本：本仓库 `scripts/` 下 4 个脚本即本次工程化产物

---

## English

### Why not osascript (key takeaway)
`osascript` + System Events GUI scripting is frequently blocked by TCC in sandboxed/background processes (`-10004`), and re-granting + restart often doesn't fix it. **PyObjC low-level APIs work** whenever `AXIsProcessTrusted()` is `True`: real mouse/keyboard via `CGEventPost`, plus the full AX API — no `osascript` middleman needed.

### One-time setup
```bash
[ -d "$HOME/.workbuddy/binaries/python/envs/gui" ] || $HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m venv "$HOME/.workbuddy/binaries/python/envs/gui"
"$HOME/.workbuddy/binaries/python/envs/gui/bin/pip" install -q pyobjc-framework-Quartz pyobjc-framework-ApplicationServices pyobjc-framework-Cocoa Pillow
```

### Standard workflow
```
0) env_check.py           permission self-check (TCC identity changes after host restart — re-check each time)
1) Locate button          (priority) A. AX tree → B. live CV → C. reference screenshot + coordinate mapping:
                           abs_x = Wnd.X + rx*Wnd.W; abs_y = Wnd.Y + ry*Wnd.H
2) Force-activate         click_at.py "App" --activate-only  (IgnoringOtherApps — required across Spaces/fullscreen)
3) Real click             click_at.py "App" X Y --verify-port 7890 --expect open|closed
4) Verify objectively     port / process / file state (never by looking at UI)
5) Clean up               activate the original app again
```

### Quit an app completely
```bash
osascript -e 'quit app "AppName"'   # if -10004, use:
kill <PID>                           # SIGTERM — same-user, no TCC needed
```

### Verified case: FlClash (2026-08-25)
- Button: pink ▶ on the dashboard, window-relative ≈ (0.932, 0.921)
- Verify: `socket.create_connection(('127.0.0.1',7890),0.5)` — same point toggles start/stop
- Quit: `kill` removes main process + FlClashCore
- The 4 scripts in `scripts/` are the engineering output of this case
