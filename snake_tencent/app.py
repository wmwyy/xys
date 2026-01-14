import streamlit as st
from pathlib import Path
import streamlit.components.v1 as components
import json
from backend import db
from backend import config

ROOT = Path(__file__).parent
FRONTEND = ROOT / "frontend"

st.set_page_config(page_title="贪吃蛇 - Tencent Style", layout="wide")
st.title("贪吃蛇 — 腾讯风")

with st.sidebar:
    st.header("设置")
    skin = st.selectbox("皮肤", config.SKINS, index=config.SKINS.index(config.DEFAULT_SKIN))
    difficulty = st.selectbox("难度", ["Easy", "Normal", "Hard"], index=["Easy","Normal","Hard"].index(config.DEFAULT_DIFFICULTY))
    name = st.text_input("昵称", value="玩家")
    st.markdown("---")
    if st.button("开始游戏"):
        st.session_state.start = True

if "start" not in st.session_state:
    st.session_state.start = False

col1, col2 = st.columns([1,3])
with col1:
    st.subheader("排行榜")
    rows = db.top_n(10)
    for r in rows:
        st.write(f"{r['name']} — {r['score']}  ({r['ts']})")
    st.markdown("---")
    st.write("说明：游戏运行在右侧，结束后在弹窗提交得分。")

with col2:
    st.subheader("游戏")
    # load frontend files
    index_html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    styles = (FRONTEND / "styles.css").read_text(encoding="utf-8")
    skins_js = (FRONTEND / "skins.js").read_text(encoding="utf-8")
    game_js = (FRONTEND / "game.js").read_text(encoding="utf-8")

    # build final HTML embedding CSS and JS, and injecting config
    cfg = {
        "skin": skin,
        "speed": config.DIFFICULTY_SETTINGS[difficulty]["speed"],
        "seedsToLevel": config.DIFFICULTY_SETTINGS[difficulty]["seedsToLevel"],
        "grid": 12,
        "width": 640,
        "height": 640,
    }

    final_html = f"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>{styles}</style>
    </head><body>
    {index_html}
    <script>window.GAME_INITIAL_SETTINGS = {json.dumps(cfg)};</script>
    <script>{skins_js}</script>
    <script>{game_js}</script>
    </body></html>"""

    # Embed and capture messages (component returns last Streamlit.setComponentValue call)
    result = components.html(final_html, height=780, scrolling=True)
    if result and isinstance(result, dict):
        # expected: {'score':..., 'event':'gameover', 'name': optional}
        if result.get("event") == "gameover":
            final_score = int(result.get("score", 0))
            submit = st.button("提交得分到排行榜")
            if submit:
                db.add_score(name or "玩家", final_score)
                st.success(f"已提交：{name} — {final_score}")

