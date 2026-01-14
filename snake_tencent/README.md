Tencent-style Snake (Streamlit + Canvas)

Quick start
1. Create virtualenv and install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run Streamlit app:

```bash
streamlit run app.py
```

Project layout
- `app.py` — Streamlit frontend and bridge
- `requirements.txt`
- `backend/db.py` — SQLite leaderboard
- `backend/config.py` — defaults
- `frontend/` — static files (index.html, game.js, styles.css, skins.js)
- `data/leaderboard.db` — SQLite DB (created automatically)

Notes
- Game runs entirely in browser via Canvas and `requestAnimationFrame`. Streamlit is used only for UI embedding and leaderboard persistence.
- If running on mobile make sure to allow full-screen; touch controls are provided.

