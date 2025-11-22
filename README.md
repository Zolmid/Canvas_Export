# CanvasDownloader

一个用于导出 Canvas 课程内容的命令行工具。支持并行扫描模块、内容下载与 Markdown 转换，并提供自适应速率限制与防火墙应对策略。可选本地下载图片并在导出的 Markdown 中保留原始样式及锚点导航。

[👉 小白快速使用教程，直接下载运行](#quickstart)

## 目录
- [功能特性](#features)
- [环境要求](#requirements)
- [安装与运行](#install-run)
- [Canvas 设置与 Token](#token)
- [导出结果](#output)
- [从 Releases 下载并运行（无需 Python，适合小白）](#quickstart)
- [主要配置](#config)
- [打包与发布](#build-release)
- [常见问题](#faq)
- [项目结构（简要）](#structure)
- [许可证](#license)
- [免责声明](#disclaimer)

<span id="features"></span>
## 功能特性
- 并行处理课程模块与条目，加速导出。
- 动态速率限制与重试退避，自动应对 429/403 等限流与防火墙场景。
- 支持导出 `Page`、`File`、`Assignment` 等内容类型，并生成目录与锚点。
- 可选下载页面中的图片到本地 `images/` 目录，Markdown 中保留原始样式。
- 友好的进度/状态展示，基于 `rich` 控制台组件。

<span id="requirements"></span>
## 环境要求
- `Python >= 3.10`
- 依赖：`canvasapi`、`markdownify`、`beautifulsoup4`、`rich`、`requests`

<span id="install-run"></span>
## 安装与运行
- 安装依赖：
  - 使用系统 Python：
    - `pip install canvasapi markdownify beautifulsoup4 rich requests`
  - 或使用虚拟环境（推荐）：
    - `python -m venv .venv && source .venv/bin/activate`
    - `pip install -U pip`
    - `pip install canvasapi markdownify beautifulsoup4 rich requests`

- 运行工具：
  - `python export_canvas.py`
  - 启动后按提示输入 Canvas API Token；支持交互式选择要导出的课程，并可选择是否下载图片。

<span id="token"></span>
## Canvas 设置与 Token
- 登录你的 Canvas 后台，打开 `Profile -> Settings`，创建并复制 `Access Token`。
- 脚本默认使用 `API_URL = "https://onlinelearn.sim.edu.sg"`。如果你的学校/机构域名不同，请编辑 `export_canvas.py` 顶部配置区域中的 `API_URL`。

<span id="output"></span>
## 导出结果
 - 导出目录：`Canvas_Exports/<课程名称>/`
- 导出文件：`<课程名称>.md`
- 图片目录（如果选择下载图片）：`Canvas_Exports/<课程名称>/images/`

<span id="quickstart"></span>
## 从 Releases 下载并运行（无需 Python，适合小白）
- 打开仓库的 GitHub `Releases` 页面，进入 `Latest` 发布（CI 会自动构建并发布）。
- 在 `Assets` 列表下载与你的系统匹配的文件：
  - Windows：`CanvasDownloader-Windows.exe`
  - macOS Intel：`CanvasDownloader-MacOS-Intel`
  - macOS Apple Silicon：`CanvasDownloader-MacOS-Silicon`
  - Linux x64：`CanvasDownloader-Linux-x64`
  - Linux ARM64：`CanvasDownloader-Linux-ARM64`
- 下载后运行：
  - Windows：双击运行；若出现 SmartScreen 拦截，点击“更多信息”→“仍要运行”。
  - macOS：
    - 方式一：在 Finder 里右键文件→“打开”，如弹出安全提示再次点“打开”。
    - 方式二（命令行）：
      - `chmod +x ~/Downloads/CanvasDownloader-MacOS-Silicon`
      - `xattr -dr com.apple.quarantine ~/Downloads/CanvasDownloader-MacOS-Silicon`
      - `~/Downloads/CanvasDownloader-MacOS-Silicon`
    - Intel 机型将上述文件名替换为 `CanvasDownloader-MacOS-Intel`。
  - Linux：
    - `chmod +x ~/Downloads/CanvasDownloader-Linux-x64`
    - `~/Downloads/CanvasDownloader-Linux-x64`
    - ARM 设备下载并运行 `CanvasDownloader-Linux-ARM64`。
- 首次启动将弹出终端窗口，按提示：
  - 输入你的 Canvas API Token（见下文“Canvas 设置与 Token”）。
  - 选择要导出的课程；可选是否下载图片到本地。
- 运行完成后在 `Canvas_Exports/<课程名称>/` 查看导出的 Markdown 和图片。
- 说明：构建包已打包所有依赖，无需安装 Python。

<span id="config"></span>
## 主要配置（`export_canvas.py` 顶部）
- 并发与限流：`WORKER_COUNT`、`INITIAL_REQUEST_INTERVAL`、`MIN_REQUEST_INTERVAL`、`MAX_REQUEST_INTERVAL`
- 重试与退避：`MAX_RETRIES`、`BASE_BACKOFF_TIME`、`BACKOFF_FACTOR`、`JITTER_RANGE`
- 防火墙应对：`RATE_LIMIT_COOLDOWN`、`SUCCESS_THRESHOLD_TO_SPEEDUP`、`SLOWDOWN_FACTOR`

<span id="build-release"></span>
## 打包与发布
- GitHub Actions 已配置跨平台构建（`Windows`、`Linux x64`、`macOS Intel`、`macOS Apple Silicon`、另含 `Linux ARM64`）：
  - 触发：推送到 `main` 分支或手动 `workflow_dispatch`。
  - 发布：构建完成后自动上传至 GitHub Releases（在 Latest 发布页下载）。
  - 依赖安装：`pip install canvasapi markdownify beautifulsoup4 rich requests pyinstaller`
  - 构建命令：`pyinstaller --onefile --name "CanvasDownloader" export_canvas.py`
  - 构建产物将作为 Artifact 上传，并按目标平台重命名。

- 本地打包（可选）：
  - `pip install pyinstaller`
  - `pyinstaller --onefile --name "CanvasDownloader" export_canvas.py`
  - 产物位于 `dist/CanvasDownloader`（Windows 为 `CanvasDownloader.exe`）。

<span id="faq"></span>
## 常见问题
- 403/验证码或触发防火墙：脚本带有自适应冷却与降速策略；若仍受限，请减小 `WORKER_COUNT` 或增大请求间隔。
- 域名不同：修改 `API_URL` 为你的 Canvas 实例地址。
- 代理与网络：如需代理，可在运行前设置环境变量 `HTTPS_PROXY`/`HTTP_PROXY`。

<span id="structure"></span>
## 项目结构（简要）
- `export_canvas.py`：主脚本与并行/限流/Markdown 处理逻辑。
- `.github/workflows/build_release.yml`：跨平台构建与发布流水线。

<span id="license"></span>
## 许可证
- 本项目采用 `GNU General Public License v3.0 (GPL-3.0)` 许可证发布。
- 你可以复制、使用、修改并分发本软件，但分发的衍生作品必须继续以 GPLv3 许可证发布，并开源相应源代码。
- 完整条款见仓库根目录的 `LICENSE` 文件或访问 https://www.gnu.org/licenses/gpl-3.0.txt。

<span id="disclaimer"></span>
## 免责声明
- 本工具仅用于个人学习备份与课程内容离线查看，请遵守所在机构的使用政策与相关法律法规。