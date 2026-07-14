<div align="center">

```
 █████╗  ██████╗ ███████╗██╗   ██╗ █████╗ ██╗      ██████╗ ███████╗███╗   ███╗
██╔══██╗██╔════╝ ██╔════╝██║   ██║██╔══██╗██║     ██╔═══██╗██╔════╝████╗ ████║
███████║██║  ███╗███████╗██║   ██║███████║██║     ██║   ██║█████╗  ██╔████╔██║
██╔══██║██║   ██║╚════██║╚██╗ ██╔╝██╔══██║██║     ██║   ██║██╔══╝  ██║╚██╔╝██║
██║  ██║╚██████╔╝███████║ ╚████╔╝ ██║  ██║███████╗╚██████╔╝███████╗██║ ╚═╝ ██║
╚═╝  ╚═╝ ╚═════╝ ╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚══════╝╚═╝     ╚═╝
```

<h3>⚡ 生死狙击2 · 瞄准小球 · 自动连点辅助系统 ⚡</h3>

<p>
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white" alt="Windows">
  <img src="https://img.shields.io/badge/Status-v1.0-00D9FF?style=for-the-badge&logo=probot&logoColor=white" alt="Version">
  <img src="https://img.shields.io/badge/License-MIT-00FF88?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="License">
</p>

<p>
  <b>🛸 基于计算机视觉的实时小球识别 · 零延迟 SendInput 高速点击引擎 🛸</b>
</p>

<p>
  <i>HSV 色彩空间过滤 → 形态学降噪 → 轮廓圆形度验证 → 绝对坐标瞬时点击</i>
</p>

---

</div>

## 🌌 系统概览

`Auto Ball Clicker` 是一款专为《生死狙击2》"瞄准小球"小游戏设计的自动化辅助工具。系统通过 **OpenCV 计算机视觉** 实时截取游戏画面，利用 **HSV 色彩空间** 精准提取高饱和度小球目标，经形态学处理与圆形度校验后，驱动 **Windows SendInput API** 以毫秒级延迟完成自动点击。

> ⚠️ **免责声明**：本工具仅供学习与技术交流使用。请遵守游戏服务条款，因使用本工具产生的任何封号或其他后果，由使用者自行承担。

---

## ✨ 核心特性

<table>
<tr>
<td width="50%" valign="top">

### 🎯 智能小球检测

```
┌─────────────────────────────────┐
│  HSV 色彩空间分离               │
│  ├─ 饱和度阈值过滤 (S > 60)     │
│  ├─ 亮度阈值过滤   (V > 120)    │
│  ├─ 形态学 Close + Open 降噪    │
│  ├─ 轮廓面积过滤 (> 60px²)     │
│  ├─ 圆形度校验   (> 0.55)      │
│  └─ 中心点饱和度二次验证        │
└─────────────────────────────────┘
```

</td>
<td width="50%" valign="top">

### ⚡ 高速点击引擎

```
┌─────────────────────────────────┐
│  Win32 SendInput API            │
│  ├─ 绝对坐标瞬时移动            │
│  ├─ 按压 30ms 确保注册          │
│  ├─ 释放 10ms 快速复位          │
│  ├─ 球间间隔 30ms               │
│  └─ DirectInput 完全兼容        │
│                                 │
│  单帧扫描周期: 50ms (20 FPS)    │
└─────────────────────────────────┘
```

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🖥️ 双模式运行

| 模式 | 命令 | 说明 |
|:---:|:---|:---|
| **GUI** | `python auto_ball_clicker.py` | 图形界面 + 实时统计 |
| **CLI** | `python auto_ball_clicker.py --cli` | 纯命令行交互 |
| **Debug** | `python auto_ball_clicker.py --debug` | 可视化检测窗口 |
| **Slow** | `python auto_ball_clicker.py --slow` | 慢速调试模式 |

</td>
<td width="50%" valign="top">

### 🎛️ 全局热键控制

```
  ┌──────────────────────────────────┐
  │                                  │
  │   [ F6 ]  ▸  启动 / 停止 切换    │
  │   [ F7 ]  ▸  强制停止           │
  │                                  │
  │   无需管理员权限                 │
  │   GetAsyncKeyState 轮询检测      │
  │   50ms 采样间隔 · 上升沿触发     │
  │                                  │
  └──────────────────────────────────┘
```

</td>
</tr>
</table>

---

## 🏗️ 系统架构

<div align="center">

```
                          ┌─────────────────────┐
                          │    AutoBallClicker   │
                          │    (主控制器)         │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                │                │
                    ▼                ▼                ▼
          ┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
          │  WindowManager  │ │ BallDetector│ │  FastClicker │
          │  (窗口管理)      │ │ (小球检测)   │ │ (高速点击)   │
          └────────┬────────┘ └──────┬──────┘ └──────┬───────┘
                   │                 │               │
                   │                 │               │
      ┌────────────┴───────┐ ┌───────┴────────┐ ┌────┴─────────────┐
      │ · EnumWindows 查找 │ │ · HSV 色彩转换 │ │ · SendInput API   │
      │ · ClientRect 获取  │ │ · 阈值二值化    │ │ · 绝对坐标映射    │
      │ · ImageGrab 截图   │ │ · 形态学处理    │ │ · 按压/释放时序   │
      │ · DPI 感知适配     │ │ · 轮廓分析      │ │ · DirectInput 兼容│
      │ · 检测区域裁剪     │ │ · 去重处理      │ │                   │
      └────────────────────┘ └────────────────┘ └──────────────────┘
                                                                │
                          ┌─────────────────────┐               │
                          │ GlobalHotkeyManager  │               │
                          │ (全局热键管理)        │               │
                          └──────────┬──────────┘               │
                                     │                          │
                          ┌──────────┴──────────┐               │
                          │ · GetAsyncKeyState  │               │
                          │ · F6 / F7 轮询监听   │               │
                          │ · 上升沿单次触发     │               │
                          └─────────────────────┘               │
```

</div>

---

## 🚀 快速开始

### 📋 环境要求

| 依赖 | 最低版本 | 用途 |
|:---|:---:|:---|
| Python | 3.8+ | 运行环境 |
| opencv-python | 4.8.0+ | 图像处理 / 小球检测 |
| numpy | 1.24.0+ | 矩阵运算 |
| pywin32 | 305+ | Windows API 调用 |
| Pillow | 9.5.0+ | 屏幕截图 |

### 🔧 安装

```bash
# 克隆仓库
git clone https://github.com/your-username/auto-ball-clicker.git
cd auto-ball-clicker

# 安装依赖
pip install -r requirements.txt
```

<details>
<summary>📦 或使用一键脚本（Windows）</summary>

```bat
:: 双击 启动.bat 即可自动安装依赖并运行
:: 提供两种模式选择：
::   [1] 正常模式 — 高速自动点击
::   [2] 慢速调试 — 鼠标移动可视化
```

</details>

### 🎮 使用方法

```
  ╔═══════════════════════════════════════════════════════════╗
  ║                                                           ║
  ║   Step 1 ➜  启动《生死狙击2》，进入"瞄准小球"小游戏       ║
  ║                                                           ║
  ║   Step 2 ➜  运行本工具 (GUI 或 CLI 模式)                  ║
  ║                                                           ║
  ║   Step 3 ➜  切回游戏窗口，按 [F6] 启动自动点击            ║
  ║                                                           ║
  ║   Step 4 ➜  按 [F6] 或 [F7] 停止                          ║
  ║                                                           ║
  ╚═══════════════════════════════════════════════════════════╝
```

---

## ⚙️ 参数配置

所有参数集中在 `auto_ball_clicker.py` 的 `Config` 类中，可根据实际游戏画面调整：

| 参数 | 默认值 | 说明 |
|:---|:---:|:---|
| `WINDOW_TITLE_KEYWORD` | `"生死狙击2"` | 游戏窗口标题匹配关键词 |
| `SATURATION_THRESHOLD` | `60` | HSV 饱和度阈值，越高越严格 |
| `VALUE_THRESHOLD` | `120` | HSV 亮度阈值，越高越严格 |
| `MIN_BALL_RADIUS` | `8` | 小球最小半径（像素） |
| `MAX_BALL_RADIUS` | `60` | 小球最大半径（像素） |
| `MIN_CONTOUR_AREA` | `60` | 轮廓面积下限（像素²），过滤噪点 |
| `MIN_CIRCULARITY` | `0.55` | 圆形度阈值（0~1），越高越圆 |
| `MIN_BALL_DISTANCE` | `15` | 去重距离（像素），防止重复检测 |
| `DETECT_LEFT` | `0.14` | 检测区域左侧裁剪比例 |
| `DETECT_RIGHT` | `0.22` | 检测区域右侧裁剪比例 |
| `DETECT_TOP` | `0.18` | 检测区域顶部裁剪比例 |
| `DETECT_BOTTOM` | `0.22` | 检测区域底部裁剪比例 |
| `FAST_CLICK_HOLD` | `0.030` | 按住时长（秒），确保游戏注册 |
| `FAST_BALL_GAP` | `0.030` | 球间点击间隔（秒） |
| `DETECT_INTERVAL` | `0.05` | 检测循环周期（秒） |

<details>
<summary>🔧 检测区域可视化</summary>

```
  ┌──────────────────────────────────────────────┐
  │  ░░░░░░░░░░  顶部 UI (18%)  ░░░░░░░░░░░░░░  │
  │  ░░┌──────────────────────────────────────┐  │
  │  L │                                      │  R
  │  侧│         ██  ██                       │  侧
  │  菜│              ██   ██                 │  面
  │  单│    ██                              │  板
  │  14│         ██       ██                  │  22
  │  % │   ██          ██                     │  %
  │  ░░│                                      │  ░░
  │  ░░└──────────────────────────────────────┘  ░░
  │  ░░░░░░░░░░  底部 UI (22%)  ░░░░░░░░░░░░░░  │
  └──────────────────────────────────────────────┘

  ██ = 检测到的小球目标
  ░░ = 被裁剪排除的 UI 区域
```

</details>

---

## 📊 检测算法流程

<div align="center">

```
  ┌─────────────┐
  │  屏幕截图    │ ◄── ImageGrab.grab() 全客户区捕获
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  区域裁剪    │ ◄── 排除四周边缘 UI，仅保留游戏区域
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ BGR → HSV   │ ◄── 色彩空间转换
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  双阈值过滤  │ ◄── S > 60 且 V > 120 → 二值掩膜
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  形态学处理  │ ◄── Close(填洞) + Open(去噪)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  轮廓提取    │ ◄── findContours + 面积/半径/圆形度三级过滤
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  坐标去重    │ ◄── 欧氏距离 < 15px 视为同一球，保留较大者
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  高速点击    │ ◄── 坐标映射 → SendInput 瞬时移动 + 点击
  └─────────────┘
```

</div>

---

## 📁 项目结构

```
auto-ball-clicker/
│
├── auto_ball_clicker.py    # 🔫 主程序（全部核心逻辑）
├── requirements.txt        # 📦 Python 依赖清单
├── 启动.bat                 # 🚀 一键安装并启动（正常/慢速）
├── 打包.bat                 # 📦 一键 PyInstaller 打包 EXE
├── 使用说明.txt             # 📖 中文使用说明
└── README.md               # 📄 本文件
```

---

## 🧩 技术栈

<div align="center">

| 层级 | 技术 | 说明 |
|:---:|:---|:---|
| **视觉层** | OpenCV + NumPy | HSV 色彩过滤、形态学处理、轮廓分析 |
| **截图层** | Pillow ImageGrab | 高性能屏幕区域捕获 |
| **窗口层** | pywin32 (win32gui) | 窗口枚举、客户区坐标转换 |
| **输入层** | ctypes SendInput | 绝对坐标鼠标控制，DirectInput 兼容 |
| **热键层** | GetAsyncKeyState | 无需注册的全局热键轮询 |
| **GUI 层** | Tkinter | 轻量原生界面 + 实时统计面板 |
| **DPI 层** | SetProcessDpiAwareness | 高 DPI 屏幕坐标自动适配 |

</div>

---

## 🔬 调试模式

<details>
<summary>🖥️ Debug 可视化模式</summary>

```bash
python auto_ball_clicker.py --debug
```

开启后会弹出 OpenCV 窗口，实时标注检测到的小球：
- **绿色圆圈** — 小球检测范围
- **红色圆点** — 小球中心点击坐标

</details>

<details>
<summary>🐢 Slow 慢速调试模式</summary>

```bash
python auto_ball_clicker.py --slow
```

- 鼠标平滑移动（40 步缓动），肉眼可观察
- 按压 150ms，前后延迟 200ms / 400ms
- 控制台输出每步坐标，用于排查点击偏移问题

</details>

---

## 📦 打包为 EXE

```bash
# 方式一：使用打包脚本
双击 打包.bat

# 方式二：手动 PyInstaller
pip install pyinstaller
pyinstaller --onefile --noconsole --name "AutoBallClicker" \
    --collect-all numpy --collect-all cv2 --clean auto_ball_clicker.py
```

打包完成后，`AutoBallClicker.exe` 将自动复制到桌面。

---

## ⚠️ 注意事项

> - 🔒 **建议以管理员权限运行**，确保热键在游戏全屏时仍可响应
> - 🎯 **仅作用于游戏窗口内**，不会误触外部界面
> - 🖥️ **高 DPI 屏幕**已自动适配（PerMonitorV2），坐标不会偏移
> - 🔧 **如识别不准**，优先调整 `SATURATION_THRESHOLD` 和 `MIN_CIRCULARITY`
> - ⚡ **如点击无效**，适当增大 `FAST_CLICK_HOLD`（如 `0.050`）
> - 📏 **检测区域**通过 `DETECT_*` 比例参数控制，可排除 UI 干扰

---

## 📜 License

<div align="center">

```
  MIT License

  Copyright (c) 2026 Auto Ball Clicker

  Permission is hereby granted, free of charge, to any person obtaining a copy
  of this software and associated documentation files (the "Software"), to deal
  in the Software without restriction, including without limitation the rights
  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  copies of the Software, and to permit persons to whom the Software is
  furnished to do so, subject to the following conditions:

  The above copyright notice and this permission notice shall be included in all
  copies or substantial portions of the Software.
```

</div>

---

<div align="center">

<sub>⬆️ Back to [Top](#)</sub>

<p>
  <img src="https://img.shields.io/badge/Made%20with-Python-3776AB?style=flat-square&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Powered%20by-OpenCV-5C3EE8?style=flat-square&logo=opencv&logoColor=white">
  <img src="https://img.shields.io/badge/Built%20with-WorkBuddy-00D9FF?style=flat-square">
</p>

<p><sub>🛸 Auto Ball Clicker · v1.0 · 计算机视觉 × 自动化 × 零延迟点击 🛸</sub></p>

</div>
