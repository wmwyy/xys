import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
# Images live alongside this app in `snake/` — ROOT is already snake/, so reference files directly.
IMG_HEAD = ROOT / "head.png"
IMG_SEED = ROOT / "seed.png"
# Older locations (if images were kept in the parent folder named with Chinese chars)
OLD_IMG_HEAD = ROOT.parent / "贪吃蛇" / "微信图片_2026-01-08_172321_991.png"
OLD_IMG_SEED = ROOT.parent / "贪吃蛇" / "微信图片_2026-01-14_165401_643.png"

def image_to_data_url(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"

def svg_placeholder_data_url(kind: str, size: int = 256) -> str:
    # simple SVG placeholders: head (circle with glasses-like), seed (small circle)
    if kind == "head":
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="12" fill="#20323a"/>
  <circle cx="50" cy="44" r="22" fill="#8fbf9f"/>
  <rect x="30" y="58" width="40" height="6" rx="3" fill="#7aa98b"/>
  </svg>'''
    else:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 100 100">
  <rect width="100" height="100" rx="12" fill="#112227"/>
  <circle cx="50" cy="50" r="18" fill="#ffd27f"/>
  </svg>'''
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"

st.set_page_config(page_title="贪吃蛇", layout="centered")
st.title("贪吃蛇")

missing_head = not IMG_HEAD.exists()
missing_seed = not IMG_SEED.exists()
if missing_head or missing_seed:
    # try to copy from older locations if available
    try:
        if missing_head and OLD_IMG_HEAD.exists():
            IMG_HEAD.write_bytes(OLD_IMG_HEAD.read_bytes())
            missing_head = False
        if missing_seed and OLD_IMG_SEED.exists():
            IMG_SEED.write_bytes(OLD_IMG_SEED.read_bytes())
            missing_seed = False
    except Exception:
        pass
    # if still missing, use SVG placeholders (graceful fallback)
    if missing_head:
        head_data = svg_placeholder_data_url("head", size=512)
    if missing_seed:
        seed_data = svg_placeholder_data_url("seed", size=512)

# If placeholders not assigned above, convert real images to data URLs
if 'head_data' not in locals():
    head_data = image_to_data_url(IMG_HEAD)
if 'seed_data' not in locals():
    seed_data = image_to_data_url(IMG_SEED)

# Fixed gameplay parameters for a smoother experience
speed = 5
grid_size = 12
canvas_px = 500

html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{ margin:0; padding:0; background: linear-gradient(180deg,#071016 0%, #0b1216 60%); color:#eef2f3; font-family: Inter, Arial, Helvetica, sans-serif; }}
    #container {{ display:flex; align-items:flex-start; justify-content:center; padding:18px; gap:20px; }}
    canvas {{ background: linear-gradient(180deg,#132029,#0f1720); border-radius:12px; box-shadow: 0 10px 30px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.03); }}
    #info {{ display:none; }}
    /* scorecard (placed left of canvas to avoid overlap) */
    #scorecard {{ background: rgba(0,0,0,0.45); color:#fff; padding:12px 14px; border-radius:10px; box-shadow: 0 6px 18px rgba(0,0,0,0.6); font-size:14px; min-width:92px; }}
    #scorecard .label {{ color:#cbd5da; font-size:12px; }}
    .game-area {{ flex: 1 1 auto; display:flex; align-items:flex-start; justify-content:center; }}
    /* mobile control styles */
    .controls {{ position: fixed; left: 50%; transform: translateX(-50%); bottom: 22px; display:flex; flex-direction:column; align-items:center; gap:18px; z-index:9999; }}
    .controls .hrow {{ display:flex; gap:36px; }}
    .control-btn {{ width:64px; height:64px; border-radius:14px; background: rgba(255,255,255,0.04); color:#fff; border:1px solid rgba(255,255,255,0.06); font-size:24px; touch-action: none; box-shadow: 0 6px 20px rgba(0,0,0,0.5); }}
    @media (min-width:700px) {{ .controls {{ display:none; }} }}
  </style>
</head>
<body>
  <div id="container">
    <div id="scorecard">
      <div id="score-current">得分: 0</div>
      <div id="score-best" class="label">最高: 0</div>
    </div>
    <div class="game-area">
      <canvas id="game" width="{canvas_px}" height="{canvas_px}"></canvas>
    </div>
  </div>
  <!-- control buttons: pause / reset -->
  <div id="scorebuttons" style="position: fixed; left: 18px; top: 80px; display:flex; gap:8px;">
    <button id="btn-pause" style="background:rgba(255,255,255,0.04); color:#fff; border-radius:8px; padding:6px 10px; border:1px solid rgba(255,255,255,0.06);">暂停</button>
    <button id="btn-reset" style="background:rgba(255,255,255,0.04); color:#fff; border-radius:8px; padding:6px 10px; border:1px solid rgba(255,255,255,0.06);">重置</button>
  </div>
  <!-- mobile on-screen controls (removed the previous instructional text) -->
  <div id="controls" class="controls" aria-hidden="false">
    <button id="btn-up" class="control-btn" aria-label="up">▲</button>
    <div class="hrow">
      <button id="btn-left" class="control-btn" aria-label="left">◀</button>
      <button id="btn-right" class="control-btn" aria-label="right">▶</button>
    </div>
    <button id="btn-down" class="control-btn" aria-label="down">▼</button>
  </div>
<script>
const headImg = new Image();
headImg.src = "{head_data}";
const seedImg = new Image();
seedImg.src = "{seed_data}";

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const tileCount = {grid_size};
let tileSize = canvas.width / tileCount;
const speed = {speed};
const scoreEl = document.getElementById('score-current');
const bestEl = document.getElementById('score-best');
const btnPause = document.getElementById('btn-pause');
const btnReset = document.getElementById('btn-reset');

// responsive: adapt canvas size for mobile while keeping pixel size prop
function resizeCanvasForDevice() {{
  const maxW = Math.min(window.innerWidth - 24, {canvas_px});
  canvas.width = maxW;
  canvas.height = maxW;
  tileSize = canvas.width / tileCount;
}}
resizeCanvasForDevice();
window.addEventListener('resize', resizeCanvasForDevice);

let snake = [ {{ x: Math.floor(tileCount/2), y: Math.floor(tileCount/2) }} ];
let velocity = {{ x: 1, y: 0 }};
let food = spawnFood();
let tail = 4;
let gameOver = false;
let score = 0;
let bestScore = localStorage.getItem('snake_best_score') ? parseInt(localStorage.getItem('snake_best_score')) : 0;
let running = true;

document.addEventListener('keydown', (e) => {{
  if (e.key === 'ArrowLeft' && velocity.x !== 1) {{ velocity = {{x:-1,y:0}}; }}
  if (e.key === 'ArrowUp' && velocity.y !== 1) {{ velocity = {{x:0,y:-1}}; }}
  if (e.key === 'ArrowRight' && velocity.x !== -1) {{ velocity = {{x:1,y:0}}; }}
  if (e.key === 'ArrowDown' && velocity.y !== -1) {{ velocity = {{x:0,y:1}}; }}
}});

// touch support: swipe detection
let touchStartX = 0, touchStartY = 0;
canvas.addEventListener('touchstart', (e) => {{
  const t = e.touches[0];
  touchStartX = t.clientX;
  touchStartY = t.clientY;
}});
canvas.addEventListener('touchend', (e) => {{
  const t = e.changedTouches[0];
  const dx = t.clientX - touchStartX;
  const dy = t.clientY - touchStartY;
  if (Math.abs(dx) > Math.abs(dy)) {{
    if (dx < -20 && velocity.x !== 1) velocity = {{x:-1,y:0}};
    if (dx > 20 && velocity.x !== -1) velocity = {{x:1,y:0}};
  }} else {{
    if (dy < -20 && velocity.y !== 1) velocity = {{x:0,y:-1}};
    if (dy > 20 && velocity.y !== -1) velocity = {{x:0,y:1}};
  }}
}});

// on-screen button controls (touch and click)
function setDirectionFromButton(dx, dy, evt) {{
  if (evt) evt.preventDefault();
  if (dx === -velocity.x && dy === -velocity.y) return;
  velocity = {{x:dx, y:dy}};
}}
const btnUp = document.getElementById('btn-up');
const btnDown = document.getElementById('btn-down');
const btnLeft = document.getElementById('btn-left');
const btnRight = document.getElementById('btn-right');
for (const btn of [btnUp, btnDown, btnLeft, btnRight]) {{
  if (!btn) continue;
  btn.addEventListener('touchstart', (e) => {{ e.preventDefault(); }}, {{passive:false}});
}}
if (btnUp) {{ btnUp.addEventListener('click', (e) => setDirectionFromButton(0,-1,e)); btnUp.addEventListener('touchend', (e)=>setDirectionFromButton(0,-1,e)); }}
if (btnDown) {{ btnDown.addEventListener('click', (e) => setDirectionFromButton(0,1,e)); btnDown.addEventListener('touchend', (e)=>setDirectionFromButton(0,1,e)); }}
if (btnLeft) {{ btnLeft.addEventListener('click', (e) => setDirectionFromButton(-1,0,e)); btnLeft.addEventListener('touchend', (e)=>setDirectionFromButton(-1,0,e)); }}
if (btnRight) {{ btnRight.addEventListener('click', (e) => setDirectionFromButton(1,0,e)); btnRight.addEventListener('touchend', (e)=>setDirectionFromButton(1,0,e)); }}

function spawnFood() {{
  let p;
  while (true) {{
    p = {{ x: Math.floor(Math.random()*tileCount), y: Math.floor(Math.random()*tileCount) }};
    if (!snake.some(s => s.x === p.x && s.y === p.y)) break;
  }}
  return p;
}}

function drawRotatedImage(image, x, y, dirX, dirY) {{
  // Keep snake head horizontal; mirror horizontally when moving left
  ctx.save();
  if (dirX === -1) {{
    // mirror horizontally around cell
    ctx.translate(x + tileSize, y);
    ctx.scale(-1, 1);
    ctx.drawImage(image, 0, 0, tileSize, tileSize);
  }} else {{
    ctx.drawImage(image, x, y, tileSize, tileSize);
  }}
  ctx.restore();
}}

function gameLoop() {{
  if (gameOver) {{
    ctx.fillStyle = 'rgba(0,0,0,0.6)';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#fff';
    ctx.font = '28px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('游戏结束 — 按 F5 刷新重玩', canvas.width/2, canvas.height/2);
    return;
  }}
  // If paused, draw overlay and skip game updates
  if (!running) {{
    ctx.fillStyle = 'rgba(0,0,0,0.4)';
    ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.fillStyle = '#fff';
    ctx.font = '28px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('已暂停', canvas.width/2, canvas.height/2);
    return;
  }}

  // 移动蛇头
  const head = {{ x: (snake[0].x + velocity.x + tileCount) % tileCount, y: (snake[0].y + velocity.y + tileCount) % tileCount }};
  // 碰撞自身
  if (snake.some((s, idx) => idx>0 && s.x === head.x && s.y === head.y)) {{
    gameOver = true;
    return;
  }}
  snake.unshift(head);
  while (snake.length > tail) snake.pop();

  // 吃到食物
  if (head.x === food.x && head.y === food.y) {{
    tail += 1;
    score += 1;
    if (score > bestScore) {{
      bestScore = score;
      localStorage.setItem('snake_best_score', bestScore);
    }}
    food = spawnFood();
  }}

  // 绘制
  ctx.clearRect(0,0,canvas.width,canvas.height);

  // 画食物（居中）
  ctx.drawImage(seedImg, food.x*tileSize, food.y*tileSize, tileSize, tileSize);

  // 画蛇身体（圆角矩形段，渐变填充，更像真实蛇身）
  function drawSegmentAt(cellX, cellY, t) {{
    const x = cellX * tileSize;
    const y = cellY * tileSize;
    const w = tileSize * 0.88;
    const h = tileSize * 0.7;
    const rx = Math.max(4, tileSize * 0.12);
    const cx = x + (tileSize - w) / 2;
    const cy = y + (tileSize - h) / 2;
    const hue = 120 - t * 60;
    const light1 = 48 - t * 18;
    const light2 = 30 - t * 10;
    const grad = ctx.createLinearGradient(cx, cy, cx + w, cy + h);
    grad.addColorStop(0, `hsl(${hue},70%,${light1}%)`);
    grad.addColorStop(1, `hsl(${Math.max(0,hue-20)},60%,${Math.max(18,light2)}%)`);
    ctx.beginPath();
    ctx.moveTo(cx + rx, cy);
    ctx.lineTo(cx + w - rx, cy);
    ctx.quadraticCurveTo(cx + w, cy, cx + w, cy + rx);
    ctx.lineTo(cx + w, cy + h - rx);
    ctx.quadraticCurveTo(cx + w, cy + h, cx + w - rx, cy + h);
    ctx.lineTo(cx + rx, cy + h);
    ctx.quadraticCurveTo(cx, cy + h, cx, cy + h - rx);
    ctx.lineTo(cx, cy + rx);
    ctx.quadraticCurveTo(cx, cy, cx + rx, cy);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.lineWidth = Math.max(1, tileSize*0.03);
    ctx.strokeStyle = 'rgba(0,0,0,0.25)';
    ctx.stroke();
  }}
  for (let i = snake.length-1; i >= 1; i--) {{
    const s = snake[i];
    const t = i / Math.max(1, snake.length);
    drawSegmentAt(s.x, s.y, t);
  }}

  // 画蛇头（图片，带方向）
  const headPx = snake[0].x * tileSize;
  const headPy = snake[0].y * tileSize;
  drawRotatedImage(headImg, headPx, headPy, velocity.x, velocity.y);
 
  // 更新并显示分数卡片
  if (scoreEl) scoreEl.innerText = '得分: ' + score;
  if (bestEl) bestEl.innerText = '最高: ' + bestScore;
}}

// 启动主循环
setInterval(gameLoop, 1000 / speed);

// Pause / Reset handlers
if (btnPause) {{
  btnPause.addEventListener('click', () => {{
    running = !running;
    btnPause.innerText = running ? '暂停' : '继续';
  }});
}}
if (btnReset) {{
  btnReset.addEventListener('click', () => {{
    // reset game state
    snake = [ {{ x: Math.floor(tileCount/2), y: Math.floor(tileCount/2) }} ];
    velocity = {{ x: 1, y: 0 }};
    food = spawnFood();
    tail = 4;
    score = 0;
    gameOver = false;
    running = true;
    if (btnPause) btnPause.innerText = '暂停';
  }});
}}

// expose score to parent window (optional)
window.addEventListener('message', (e) => {{
  if (e.data && e.data.type === 'get_score') {{
    e.source.postMessage({{ type: 'score', score, bestScore }}, '*');
  }}
}});
</script>
</body>
</html>
"""

# We previously used an f-string and doubled JS braces to avoid Python interpolation.
# Now convert doubled braces back to single braces for valid JS, then inject values.
html = html.replace("{{", "{").replace("}}", "}")

# Inject dynamic values into placeholders
html = html.replace("{head_data}", head_data).replace("{seed_data}", seed_data)
html = html.replace("{canvas_px}", str(canvas_px)).replace("{grid_size}", str(grid_size)).replace("{speed}", str(speed))

components.html(html, height=canvas_px + 120)

