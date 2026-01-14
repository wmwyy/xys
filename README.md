贪吃蛇 Streamlit 部署说明

文件说明
- `streamlit_app.py` — 主应用文件，内嵌 HTML/JS 贪吃蛇游戏并把仓库内的两张图片作为蛇头和种子。
- `requirements.txt` — Streamlit 依赖。
- 图片位于仓库的 `贪吃蛇/` 目录下：  
  - `微信图片_2026-01-08_172321_991.png`（蛇头）  
  - `微信图片_2026-01-14_165401_643.png`（种子）

本地运行
1. 创建并激活虚拟环境（推荐）。
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 运行：

```bash
streamlit run streamlit_app.py
```

部署到 share.streamlit.io（GitHub）
1. 将整个仓库（包含图片文件夹 `贪吃蛇/`） push 到 GitHub。
2. 打开 `https://share.streamlit.io/` 并登录你的 GitHub 账号。
3. 点击 "New app" 或 "Deploy" 并选择你的仓库与分支，填写主文件路径为 `streamlit_app.py`。
4. 等待构建完成，访问分配的 URL 即可看到游戏。

注意事项
- 如果部署后图片无法显示，请确认图片已被包含在 GitHub 仓库并且路径未被更改。`streamlit_app.py` 当前按 `贪吃蛇/` 目录下的文件名读取图片。
- 若要替换图片，请把新图片覆盖原文件或修改 `streamlit_app.py` 中的路径。
 - 我已新增 `snake/` 目录支持：脚本优先从 `snake/head.png` 和 `snake/seed.png` 读取图片；如果不存在，会尝试从旧的 `贪吃蛇/` 路径自动复制到 `snake/`。
 - 移动设备支持：在手机上会自动缩放画布并支持触控滑动控制（左右上下滑动）。
 - 得分板：游戏内会显示当前得分与历史最高分（保存在浏览器 localStorage）。

把仓库推送到 GitHub
1. 在本地确认改动并提交：

```bash
git add .
git commit -m "Add snake mobile support, scoreboard, and snake/ images"
```

2. 若你已有远程仓库，添加并推送（替换为你的 remote URL）：

```bash
git remote add origin <YOUR_GIT_REMOTE_URL>
git push -u origin main
```

说明：如果你希望我帮你把仓库直接推到 GitHub，请把你的远程仓库 URL 发给我并允许我在终端运行 git 命令（我会请求 git_write 权限）。否则按上面命令在你本地执行即可。

问题反馈
如果你想要我把游戏进一步增强（触控支持、移动端友好、得分板、音效或把图像改为更小的贴图），告诉我需要的功能，我会继续实现。

