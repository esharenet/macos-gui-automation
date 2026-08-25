# macOS GUI Automation for AI Agents

> **AI Agent 可操作的 macOS GUI 自动化** · 点击任意原生 App 按钮 / Click any button in any native macOS app

让 AI Agent 像人类一样真实点击 macOS 原生 App 的按钮、开关、菜单项，并在沙盒 / 后台进程环境下绕过 macOS TCC 权限墙。
An AI-agent-friendly toolkit that lets agents click buttons, toggles and menu items in native macOS apps with **real mouse events**, working around the TCC permission wall that blocks `osascript` / System Events in sandboxed or background processes.

Proven in production with **FlClash** (start/stop proxy at `127.0.0.1:7890`). Battle-tested on 2026-08-25.

---

## 🇬🇧 English

### Why this exists

On macOS, automating GUI from a sandboxed / background process usually fails:

| Approach | Result | Why |
|---|---|---|
| `osascript -e 'tell application "System Events" to click at ...'` | `-10004 权限违例` (permission violation) | TCC blocks System Events automation for background processes; re-granting + restart often doesn't help |
| `screencapture -x ...` | Sometimes `could not create image from display` | Screen-recording TCC identity can be lost after the host app restarts |
| **PyObjC + Quartz / Accessibility (AX) APIs** | ✅ **Works** | As long as `AXIsProcessTrusted()` returns `True`, real mouse/keyboard events (`CGEventPost`) and AX APIs work — no `osascript` middleman |

### Quick start

```bash
# One-time environment setup
[ -d "$HOME/.workbuddy/binaries/python/envs/gui" ] || \
  $HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m venv "$HOME/.workbuddy/binaries/python/envs/gui"
"$HOME/.workbuddy/binaries/python/envs/gui/bin/pip" install -q pyobjc-framework-Quartz pyobjc-framework-ApplicationServices pyobjc-framework-Cocoa Pillow

# 0) Permission check (always first)
scripts/env_check.py
#    expect: ax_trusted = True   (screen_cap is informational only)

# 1) List buttons of an app via the Accessibility tree (no coordinates needed)
scripts/ax_find_buttons.py "FlClash"                 # list all buttons
scripts/ax_find_buttons.py "FlClash" --press 3       # press the 3rd button

# 2) Force-activate app across Spaces, click, and verify objectively
scripts/click_at.py "FlClash" 1756 784 --verify-port 7890 --expect open

# 3) Take a screenshot when screencapture is broken
scripts/screenshot.py /tmp/shot.png
```

### How to locate a button (3 methods, by priority)

1. **Accessibility (AX) tree** — most reliable, no screen coordinates. Works for standard AppKit controls. **Note:** Flutter/Electron apps expose sparse AX trees (few buttons, no titles) — fall through to method 3.
2. **Live screenshot + color/shape detection** — `scripts/screenshot.py` + PIL when the window is capturable.
3. **Reference screenshot + relative-coordinate mapping** — when TCC blocks live capture (common!), use any *historical* screenshot that shows the window, detect the button's position *relative to the window* `(rx, ry)` (0~1), then map onto the window's **current** bounds from `CGWindowListCopyWindowInfo`:
   `abs_x = X + rx*W; abs_y = Y + ry*H` — then click and verify; fine-tune if needed.

### Standard workflow

```
0. env_check.py           → permission self-check (TCC identity changes after host restarts — always re-check)
1. Locate button          → AX tree → live CV → reference screenshot + coordinate mapping
2. Force-activate app     → NSRunningApplication.activateWithOptions_(AllWindows | IgnoringOtherApps)
                           (plain `osascript activate` cannot switch Spaces under a fullscreen IDE)
3. Real click             → CGEventPostMouseEvent (left down/up), exactly like a human
4. Verify objectively     → port / process / file state (e.g. `nc -z 127.0.0.1 7890`)
5. Clean up               → activate the original app (e.g. WorkBuddy) again
```

### Quit an app completely

```bash
osascript -e 'quit app "AppName"'    # if -10004, fall back to:
kill <PID>                            # SIGTERM — graceful, same-user, no TCC needed
# verify: pgrep -f "AppName" ; kill child processes (e.g. core daemons) if any remain
```

### Common pitfalls (FAQ)

| Pitfall | Fix |
|---|---|
| `osascript` System Events → `-10004` | Use PyObjC low-level APIs (`AXIsProcessTrusted`, `CGEventPost`) instead of `osascript` |
| `screencapture` → `could not create image from display` | Use `scripts/screenshot.py` (CGWindowListCreateImage) |
| Live capture shows the window missing / only wallpaper | TCC scoped capture — use method 3 (reference screenshot + coordinate mapping) |
| Window is on another Space / covered by a fullscreen app | Force-activate with `IgnoringOtherApps` option |
| Flutter/Electron app: AX tree sparse, `AXPress` no-op | CGEvent real click at mapped coordinates (method 3) still works |
| Click landed but nothing happened | Re-check the window's **current** bounds first (position changes after relaunch); ensure the app is fully rendered before clicking |
| Verify by UI? | Don't. Verify by port / process / file state |

---

## 🇨🇳 中文

### 为什么需要这个

在 macOS 上，从沙盒 / 后台进程做 GUI 自动化经常失败：

| 方式 | 结果 | 原因 |
|---|---|---|
| `osascript -e 'tell application "System Events" to click at ...'` | `-10004 权限违例` | TCC 对后台进程封禁 System Events 自动化，重开权限 + 重启宿主也常常无效 |
| `screencapture -x ...` | 有时 `could not create image from display` | 宿主重启后，屏幕录制 TCC 身份可能失效 |
| **PyObjC + Quartz / 无障碍(AX) 底层 API** | ✅ **可用** | 只要 `AXIsProcessTrusted()` 为 True，真实鼠标/键盘事件（`CGEventPost`）与 AX API 全通，无需 osascript 中转 |

### 快速上手

```bash
# 一次性环境准备
[ -d "$HOME/.workbuddy/binaries/python/envs/gui" ] || \
  $HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3 -m venv "$HOME/.workbuddy/binaries/python/envs/gui"
"$HOME/.workbuddy/binaries/python/envs/gui/bin/pip" install -q pyobjc-framework-Quartz pyobjc-framework-ApplicationServices pyobjc-framework-Cocoa Pillow

# 0) 权限自检（每次必做）
scripts/env_check.py
#    期望 ax_trusted = True（screen_cap 仅供参考）

# 1) 用 AX 树列出 App 的按钮（无需坐标）
scripts/ax_find_buttons.py "FlClash"                # 列出所有按钮
scripts/ax_find_buttons.py "FlClash" --press 3      # 直接按下第 3 个

# 2) 跨空间强制激活 + 真实点击 + 客观验证
scripts/click_at.py "FlClash" 1756 784 --verify-port 7890 --expect open

# 3) screencapture 失效时截图
scripts/screenshot.py /tmp/shot.png
```

### 定位按钮三法（按优先级）

1. **AX 无障碍树** —— 最可靠、不需要屏幕坐标。适用于 AppKit 标准控件。**注意**：Flutter/Electron 的 AX 树很稀疏（按钮少、无标题），请落到方法 3。
2. **实时截图 + 颜色/形状识别** —— `scripts/screenshot.py` + PIL，在窗口可见时可截时用。
3. **参考截图 + 相对坐标换算** —— TCC 挡掉实时截图时（很常见！），找一张**历史上能看到目标窗口**的截图，识别按钮在**窗口内**的相对位置 `(rx, ry)`（0~1），再用 `CGWindowListCopyWindowInfo` 取窗口**当前** bounds 换算：
   `abs_x = X + rx*W; abs_y = Y + ry*H` —— 点击后必须验证，失败则微调。

### 标准流程

```
0. env_check.py           → 权限自检（宿主重启后 TCC 身份会变，务必每次重查）
1. 定位按钮              → AX 树 → 实时 CV → 参考截图+坐标换算
2. 强制激活 App          → NSRunningApplication.activateWithOptions_(AllWindows | IgnoringOtherApps)
                           （全屏 IDE 下普通 osascript activate 切不过去空间）
3. 真实点击              → CGEventPostMouseEvent（左键 down/up），与人类操作一致
4. 客观验证              → 端口 / 进程 / 文件状态（如 `nc -z 127.0.0.1 7890`）
5. 收尾                  → 把前台切回原 App（如 WorkBuddy）
```

### 彻底退出 App

```bash
osascript -e 'quit app "App名"'    # 若报 -10004，改用：
kill <PID>                          # SIGTERM 优雅终止（同用户无需 TCC 权限）
# 验证: pgrep -f "App名" 无残留；有子进程(如 core)再逐个 kill
```

### 常见问题（FAQ）

| 问题 | 解法 |
|---|---|
| `osascript` System Events 报 `-10004` | 改用 PyObjC 底层 API（`AXIsProcessTrusted` / `CGEventPost`），不走 osascript 中转 |
| `screencapture` 报 `could not create image from display` | 用 `scripts/screenshot.py`（CGWindowListCreateImage）|
| 实时截图看不到目标窗口 / 只有壁纸 | TCC 限定捕获范围 —— 用方法 3（参考截图 + 坐标换算）|
| 窗口在另一个空间 / 被全屏 App 遮挡 | 用 `IgnoringOtherApps` 选项强制激活 |
| Flutter/Electron：AX 树稀疏、`AXPress` 无效 | 用 CGEvent 按坐标真实点击（方法 3）仍有效 |
| 点了没反应 | 先重查窗口**当前** bounds（重启后位置会变）；确保 App 渲染完成后再点 |
| 靠 UI 判断结果？ | 别。用端口 / 进程 / 文件状态客观验证 |

---

## Scripts / 脚本

| Script | Purpose / 用途 | Usage / 用法 |
|---|---|---|
| `scripts/env_check.py` | Permission self-check / 权限自检 | `env_check.py` |
| `scripts/ax_find_buttons.py` | List & press AX buttons / AX 按钮枚举与触发 | `ax_find_buttons.py "App" [--press N]` |
| `scripts/click_at.py` | Force-activate + real click + verify / 强制激活+真实点击+验证 | `click_at.py "App" [X Y] [--verify-port P --expect open\|closed]` |
| `scripts/screenshot.py` | Screenshot via CGWindowList / 截图 | `screenshot.py [out.png]` |

## Verified case / 已验证案例：FlClash

- Button: pink ▶ start/stop on the dashboard (window-relative position ≈ 0.932, 0.921).
- Verification: `socket.create_connection(('127.0.0.1', 7890), timeout=0.5)` — OPEN/CLOSED within 0.5 s; the same point toggles both ways.
- Quit: `kill` removes both the main process and `FlClashCore`.

## License

MIT
