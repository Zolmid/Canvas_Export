<div align="center" id="readme-top">

# 📥 CanvasDownloader

[![Build Status](https://img.shields.io/github/actions/workflow/status/Zolmid/CanvasDownloader/build_release.yml?label=Build&logo=github&style=for-the-badge)](https://github.com/Zolmid/CanvasDownloader/actions)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/Zolmid/CanvasDownloader?style=for-the-badge&logo=github)](https://github.com/Zolmid/CanvasDownloader/releases)
[![License](https://img.shields.io/badge/license-GPLv3-green.svg?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg?logo=python&logoColor=white&style=for-the-badge)](https://www.python.org/)

<p align="center">
  <strong>全平台 Canvas LMS 课程内容一键导出工具</strong>
  <br>
  🚀 多线程并发 · 🛡️ 智能防封 · 📚 离线浏览 · 🎨 原始样式还原
</p>

<p align="center">
  <a href="#english">🇺🇸 English</a> •
  <a href="#chinese">🇨🇳 中文</a>
</p>

</div>

---

<div id="english"></div>

# CanvasDownloader (English)

A robust command-line tool for exporting Canvas LMS course content. It supports parallel module scanning, content downloading, Markdown conversion, and features adaptive rate limiting to bypass firewalls. Optionally downloads images locally while preserving original styles and anchor navigation in the exported Markdown.

## 🚀 Quick Start (No Python Required)

If you are not a developer, you don't need to install Python. Just download the executable:

1.  Go to the [**Releases**](../../releases/latest) page.
2.  Download the file matching your OS:
    * **Windows**: `CanvasDownloader-Windows.exe`
    * **macOS (Intel)**: `CanvasDownloader-MacOS-Intel`
    * **macOS (M1/M2/M3)**: `CanvasDownloader-MacOS-Silicon`
    * **Linux**: `CanvasDownloader-Linux-x64` (or ARM64)
3.  **Run it**:
    * **Windows**: Double-click. (If SmartScreen appears, click "More Info" -> "Run Anyway").
    * **macOS**: Right-click -> Open. You may need to run `chmod +x` in terminal if it doesn't open.
4.  **Follow the prompts**:
    * Enter your Canvas Token (refer to [**Token Setup Guide**](#token-setup-en) below).
    * Select courses to export.

---

## ✨ Features

* **High Performance**: Parallel processing for modules and items to speed up exporting.
* **Smart Anti-Blocking**: Adaptive rate limiting and exponential backoff to handle 429/403 errors and firewalls.
* **Rich Content**: Exports `Page`, `File`, `Assignment`, and `ExternalUrl` with Table of Contents and navigation anchors.
* **Offline Images**: Optionally downloads images to a local `images/` directory, preserving HTML styling in Markdown.
* **Beautiful UI**: User-friendly progress bars and status displays powered by `rich`.

## 🛠 Installation (For Developers)

### Requirements
* Python >= 3.10
* Dependencies: `canvasapi`, `markdownify`, `beautifulsoup4`, `rich`, `requests`

### Setup
1.  **Install Dependencies**:
    ```bash
    # Recommended: Use a virtual environment
    python -m venv .venv
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    
    pip install -U pip
    pip install canvasapi markdownify beautifulsoup4 rich requests
    ```

2.  **Run the Script**:
    ```bash
    python export_canvas.py
    ```

<div id="token-setup-en"></div>

## 🔑 Canvas Token Setup
1.  Log in to your Canvas dashboard.
2.  Go to **Account** -> **Settings**.
3.  Scroll down to **Approved Integrations** and click **+ New Access Token**.
4.  Copy the token.
5.  *Note: The default API URL is set to SIM (`https://onlinelearn.sim.edu.sg`). Change `API_URL` in the script header if needed.*

## 📂 Output Structure

```text
Canvas_Exports/
└── <Course Name>/
    ├── <Course Name>.md       # The main content file
    └── images/                # (Optional) Local images
```

## ⚙️ Configuration

You can tweak the following constants at the top of `export_canvas.py`:

  * **Concurrency**: `WORKER_COUNT` (Default: 16)
  * **Rate Limiting**: `INITIAL_REQUEST_INTERVAL`, `MAX_REQUEST_INTERVAL`
  * **Backoff Strategy**: `MAX_RETRIES`, `BACKOFF_FACTOR`

## 🏗 Build & Release

This project uses **GitHub Actions** for cross-platform building:

  * **Triggers**: Push to `main` or tag starting with `v*`.
  * **Artifacts**: Automatically uploads built binaries to GitHub Releases.
  * **Manual Build**: `pyinstaller --onefile --name "CanvasDownloader" export_canvas.py`

## 📄 License

This project is licensed under the **GPL-3.0 License**. See the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for personal study backup and offline viewing only. Please comply with your institution's usage policies and relevant laws.

<br>
<div align="center"> <a href="#readme-top">⬆️ Back to Top</a> </div>
<br>

-----

<div id="chinese"></div>

# CanvasDownloader (中文文档)

一个用于导出 Canvas 课程内容的命令行工具。支持并行扫描模块、内容下载与 Markdown 转换，并提供自适应速率限制与防火墙应对策略。可选本地下载图片并在导出的 Markdown 中保留原始样式及锚点导航。

## 🚀 小白快速使用教程 (无需 Python)

如果你不想配置代码环境，可以直接下载打包好的程序：

1.  打开本仓库的 [**Releases**](../../releases/latest) 页面。
2.  在 `Assets` 列表下载与你的系统匹配的文件：
      * **Windows**: `CanvasDownloader-Windows.exe`
      * **macOS Intel**: `CanvasDownloader-MacOS-Intel`
      * **macOS Apple Silicon (M1/M2/M3)**: `CanvasDownloader-MacOS-Silicon`
      * **Linux**: `CanvasDownloader-Linux-x64` 或 ARM64
3.  **运行**：
      * **Windows**: 双击运行；若出现 SmartScreen 拦截，点击“更多信息”→“仍要运行”。
      * **macOS**:
          * 方式一：在 Finder 里右键文件→“打开”，如弹出安全提示再次点“打开”。
          * 方式二（终端）：
            ```bash
            chmod +x ~/Downloads/CanvasDownloader-MacOS-Silicon
            # 移除安全隔离标记（如果打不开）
            xattr -dr com.apple.quarantine ~/Downloads/CanvasDownloader-MacOS-Silicon
            ~/Downloads/CanvasDownloader-MacOS-Silicon
            ```
4.  **操作**：
      * 首次启动将弹出终端窗口。
      * 输入你的 Canvas API Token（获取方法见下方 [**Canvas 设置与 Token**](#token-setup-zh)）。
      * 选择要导出的课程；输入 `y` 可下载图片到本地。

-----

## ✨ 功能特性

  * **极速导出**：并行处理课程模块与条目，充分利用带宽。
  * **智能防封**：动态速率限制与重试退避机制，自动应对 429/403 等限流与防火墙场景。
  * **内容丰富**：支持导出 `Page`、`File`、`Assignment` 等内容类型，并自动生成目录与跳转锚点。
  * **离线阅读**：可选下载页面中的图片到本地 `images/` 目录，Markdown 中保留原始 CSS 样式（大小自适应）。
  * **交互友好**：基于 `rich` 库构建的现代化控制台界面，提供详细的进度展示。

## 🛠 安装与运行 (开发者)

### 环境要求

  * Python >= 3.10
  * 依赖库：`canvasapi`、`markdownify`、`beautifulsoup4`、`rich`、`requests`

### 安装步骤

1.  **安装依赖**：

    ```bash
    # 推荐使用虚拟环境
    python -m venv .venv
    # Windows: .venv\Scripts\activate
    # Mac/Linux: source .venv/bin/activate

    pip install -U pip
    pip install canvasapi markdownify beautifulsoup4 rich requests
    ```

2.  **运行工具**：

    ```bash
    python export_canvas.py
    ```

<div id="token-setup-zh"></div>

## 🔑 Canvas 设置与 Token

1.  登录你的 Canvas 网页端后台。
2.  点击左侧 **Account (账户)** -> **Settings (设置)**。
3.  向下滚动找到 **Approved Integrations**，点击 **+ New Access Token**。
4.  复制生成的 Token。
5.  *注意：脚本默认 API 地址为 SIM (`https://onlinelearn.sim.edu.sg`)。如需更改，请编辑脚本顶部的 `API_URL`。*

## 📂 导出结果

  * **导出目录**：`Canvas_Exports/<课程名称>/`
  * **核心文件**：`<课程名称>.md` (包含所有课程内容的 Markdown 汇总)
  * **图片资源**：`Canvas_Exports/<课程名称>/images/` (如果开启图片下载)

## ⚙️ 主要配置

你可以在 `export_canvas.py` 顶部修改以下核心参数：

  * **并发与限流**：`WORKER_COUNT` (默认 16), `INITIAL_REQUEST_INTERVAL`
  * **重试策略**：`MAX_RETRIES`, `BACKOFF_FACTOR`
  * **防火墙应对**：`RATE_LIMIT_COOLDOWN` (触发封锁后的冷却时间)

## 📦 打包与发布

本项目使用 **GitHub Actions** 进行全平台自动构建：

  * **触发条件**：推送到 `main` 分支或推送 `v*` 标签。
  * **自动发布**：构建完成后会自动将 Windows, macOS, Linux 的可执行文件上传至 GitHub Releases。
  * **本地打包**：
    ```bash
    pip install pyinstaller
    pyinstaller --onefile --name "CanvasDownloader" export_canvas.py
    ```

## 📄 许可证

本项目采用 **GNU General Public License v3.0 (GPL-3.0)** 许可证发布。
你可以复制、使用、修改并分发本软件，但分发的衍生作品必须继续以 GPLv3 许可证发布，并开源相应源代码。

## ⚠️ 免责声明

本工具仅用于个人学习备份与课程内容离线查看，请遵守所在机构的使用政策与相关法律法规。

<br>
<div align="center"> <a href="#readme-top">⬆️ 回到顶部</a> </div>
