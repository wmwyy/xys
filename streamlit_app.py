import streamlit as st
import streamlit.components.v1 as components
import os
import base64

# 设置页面配置
st.set_page_config(
    page_title="游戏中心",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 读取CSS文件
def load_css(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f"<style>{f.read()}</style>"

# 读取HTML文件
def load_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

# 读取JavaScript文件
def load_js(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return f"<script>{f.read()}</script>"

# 获取图片的base64编码
def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


# 返回 image 的 data URL（根据文件扩展名设定 MIME）
def get_image_data_url(image_path):
    if not os.path.exists(image_path):
        return None
    b64 = get_image_base64(image_path)
    ext = os.path.splitext(image_path)[1].lstrip('.').lower()
    # 常见扩展名映射
    if ext in ('png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'):
        mime = f"image/{'jpeg' if ext == 'jpg' else ext}"
    else:
        mime = "application/octet-stream"
    return f"data:{mime};base64,{b64}"

# 主页面
def main():
    st.title("🎮 游戏中心")
    st.markdown("### 选择你想玩的游戏：")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🐍 贪吃蛇游戏")
        st.markdown("经典的贪吃蛇游戏，支持键盘和触摸控制")
        if st.button("开始玩贪吃蛇", key="snake_btn", use_container_width=True):
            st.session_state.game = "snake"
            st.rerun()

    with col2:
        st.markdown("### 🐭 打地鼠游戏")
        st.markdown("有趣的打地鼠游戏，考验你的反应速度")
        if st.button("开始玩打地鼠", key="dds_btn", use_container_width=True):
            st.session_state.game = "dds"
            st.rerun()

    # 添加一些说明
    st.markdown("---")
    st.markdown("### 📱 移动端支持")
    st.markdown("这两个游戏都完全支持在手机和平板上的触摸控制，可以随时随地享受游戏乐趣！")

    st.markdown("### 🎯 游戏特色")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**贪吃蛇游戏：**")
        st.markdown("- 🎮 键盘控制 (WASD/方向键)")
        st.markdown("- 👆 触摸控制 (屏幕点击)")
        st.markdown("- 📊 分数统计和最高分记录")
        st.markdown("- 🎨 精美界面和动画效果")

    with col2:
        st.markdown("**打地鼠游戏：**")
        st.markdown("- ⏰ 30秒限时挑战")
        st.markdown("- 🖱️ 鼠标点击或触摸击打")
        st.markdown("- 🎯 随机出现的地鼠")
        st.markdown("- 🏆 分数统计和评价系统")

# 贪吃蛇游戏页面
def snake_game():
    st.title("🐍 贪吃蛇游戏")

    if st.button("← 返回游戏选择", key="back_snake"):
        st.session_state.game = None
        st.rerun()
        return

    st.markdown("### 操作说明：")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**电脑端：**")
        st.markdown("- ↑↓←→ 或 WASD 控制方向")
        st.markdown("- 空格键 暂停/继续")

    with col2:
        st.markdown("**移动端：**")
        st.markdown("- 点击屏幕相应区域控制方向")
        st.markdown("- 或使用底部的方向按钮")

    # 读取游戏文件
    try:
        css_content = load_css("snake/style.css")
        html_content = load_html("snake/index.html")
        js_content = load_js("snake/script.js")

        # 将 snake 目录下的图片内联为 data-URL，避免 components.html 中的相对路径失效
        snake_image_map = {
            'head.png': 'snake/head.png',
            'food.png': 'snake/food.png',
            'seed.png': 'snake/seed.png',
        }
        for filename, path in snake_image_map.items():
            data_url = get_image_data_url(path)
            if data_url:
                # 替换单引号和双引号两种情况
                js_content = js_content.replace(f"'{filename}'", f"'{data_url}'")
                js_content = js_content.replace(f"\"{filename}\"", f"\"{data_url}\"")

        # 替换HTML中的相对路径为绝对路径
        html_content = html_content.replace('src="style.css"', "")
        html_content = html_content.replace('<link rel="stylesheet" href="style.css">', "")
        html_content = html_content.replace('src="script.js"', "")
        html_content = html_content.replace('<script src="script.js"></script>', "")

        # 创建完整的HTML
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>贪吃蛇游戏</title>
            {css_content}
        </head>
        <body>
            <div class="container">
                <h1>贪吃蛇游戏</h1>
                <div class="game-info">
                    <div class="score">分数: <span id="score">0</span></div>
                    <div class="high-score">最高分: <span id="high-score">0</span></div>
                </div>
                <div class="game-container">
                    <canvas id="game-canvas" width="400" height="400"></canvas>
                </div>
                <div class="controls">
                    <button id="start-btn">开始游戏</button>
                    <button id="pause-btn" disabled>暂停</button>
                    <button id="reset-btn">重新开始</button>
                </div>
                <div class="instructions">
                    <h3>操作说明：</h3>
                    <p><strong>键盘：</strong>↑↓←→ 或 WASD 控制方向</p>
                    <p><strong>触摸：</strong>点击屏幕相应区域控制方向</p>
                    <p><strong>空格键：</strong>暂停/继续游戏</p>
                </div>
                <div class="touch-controls">
                    <div class="control-row">
                        <div class="control-btn" data-direction="up">↑</div>
                    </div>
                    <div class="control-row">
                        <div class="control-btn" data-direction="left">←</div>
                        <div class="control-btn" data-direction="down">↓</div>
                        <div class="control-btn" data-direction="right">→</div>
                    </div>
                </div>
            </div>
            {js_content}
        </body>
        </html>
        """

        # 使用Streamlit的HTML组件显示游戏
        components.html(full_html, height=800, scrolling=True)

    except FileNotFoundError as e:
        st.error(f"游戏文件未找到: {e}")
        st.info("请确保snake目录下的文件完整")

# 打地鼠游戏页面
def dds_game():
    st.title("🐭 打地鼠游戏")

    if st.button("← 返回游戏选择", key="back_dds"):
        st.session_state.game = None
        st.rerun()
        return

    st.markdown("### 游戏规则：")
    st.markdown("- 游戏时间：30秒")
    st.markdown("- 点击出现的地鼠获得分数")
    st.markdown("- 每击中一个地鼠得10分")
    st.markdown("- 游戏结束后根据分数获得评价")

    # 读取游戏文件
    try:
        css_content = load_css("dds/style.css")
        html_content = load_html("dds/index.html")
        js_content = load_js("dds/script.js")

        # 将 dds 目录下的图片内联为 data-URL（支持 mole1/mole2/head/seed）
        dds_candidates = {
            './mole1.png': 'dds/mole1.png',
            './mole2.png': 'dds/mole2.png',
            'mole1.png': 'dds/mole1.png',
            'mole2.png': 'dds/mole2.png',
            './head.png': 'dds/head.png',
            './seed.png': 'dds/seed.png',
            'head.png': 'dds/head.png',
            'seed.png': 'dds/seed.png',
        }
        for token, path in dds_candidates.items():
            data_url = get_image_data_url(path)
            if data_url:
                js_content = js_content.replace(f"'{token}'", f"'{data_url}'")
                js_content = js_content.replace(f"\"{token}\"", f"\"{data_url}\"")

        # 替换HTML中的相对路径为绝对路径
        html_content = html_content.replace('src="style.css"', "")
        html_content = html_content.replace('<link rel="stylesheet" href="style.css">', "")
        html_content = html_content.replace('src="script.js"', "")
        html_content = html_content.replace('<script src="script.js"></script>', "")

        # 创建完整的HTML
        full_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>打地鼠游戏</title>
            {css_content}
        </head>
        <body>
            <div class="game-container">
                <h1>打地鼠游戏</h1>

                <div class="game-info">
                    <div class="score">得分: <span id="score">0</span></div>
                    <div class="time">时间: <span id="time">30</span>秒</div>
                </div>

                <div class="game-board">
                    <div class="hole" id="hole-0">
                        <div class="mole" id="mole-0"></div>
                    </div>
                    <div class="hole" id="hole-1">
                        <div class="mole" id="mole-1"></div>
                    </div>
                    <div class="hole" id="hole-2">
                        <div class="mole" id="mole-2"></div>
                    </div>
                    <div class="hole" id="hole-3">
                        <div class="mole" id="mole-3"></div>
                    </div>
                    <div class="hole" id="hole-4">
                        <div class="mole" id="mole-4"></div>
                    </div>
                    <div class="hole" id="hole-5">
                        <div class="mole" id="mole-5"></div>
                    </div>
                    <div class="hole" id="hole-6">
                        <div class="mole" id="mole-6"></div>
                    </div>
                    <div class="hole" id="hole-7">
                        <div class="mole" id="mole-7"></div>
                    </div>
                    <div class="hole" id="hole-8">
                        <div class="mole" id="mole-8"></div>
                    </div>
                </div>

                <div class="controls">
                    <button id="start-btn">开始游戏</button>
                    <button id="reset-btn">重置游戏</button>
                </div>

                <div class="message" id="message"></div>
            </div>
            {js_content}
        </body>
        </html>
        """

        # 使用Streamlit的HTML组件显示游戏
        components.html(full_html, height=900, scrolling=True)

    except FileNotFoundError as e:
        st.error(f"游戏文件未找到: {e}")
        st.info("请确保dds目录下的文件完整")

# 主程序逻辑
if __name__ == "__main__":
    if 'game' not in st.session_state:
        st.session_state.game = None

    if st.session_state.game == "snake":
        snake_game()
    elif st.session_state.game == "dds":
        dds_game()
    else:
        main()