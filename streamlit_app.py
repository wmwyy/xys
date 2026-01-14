import base64
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
# prefer new `snake/` directory; fallback to original `贪吃蛇/` if not present
IMG_HEAD = ROOT / "snake" / "head.png"
IMG_SEED = ROOT / "snake" / "seed.png"
OLD_IMG_HEAD = ROOT / "贪吃蛇" / "微信图片_2026-01-08_172321_991.png"
OLD_IMG_SEED = ROOT / "贪吃蛇" / "微信图片_2026-01-14_165401_643.png"

def image_to_data_url(path: Path) -> str:
    data = path.read_bytes()
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{b64}"

st.set_page_config(page_title="贪吃蛇 (Snake)", layout="centered")
st.title("贪吃蛇 — Streamlit 内嵌 HTML 版本")

if not IMG_HEAD.exists() or not IMG_SEED.exists():
    # try to copy from old locations if available
    try:
        if OLD_IMG_HEAD.exists():
            (ROOT / "snake").mkdir(exist_ok=True)
            (ROOT / "snake" / "head.png").write_bytes(OLD_IMG_HEAD.read_bytes())
        if OLD_IMG_SEED.exists():
            (ROOT / "snake").mkdir(exist_ok=True)
            (ROOT / "snake" / "seed.png").write_bytes(OLD_IMG_SEED.read_bytes())
    except Exception:
        pass
    if not IMG_HEAD.exists() or not IMG_SEED.exists():
        st.error(f"找不到图片文件，请确保仓库中存在:\n`{IMG_HEAD}` 和 `{IMG_SEED}` 或旧路径 `{OLD_IMG_HEAD}` `{OLD_IMG_SEED}`")
        st.stop()

head_data = image_to_data_url(IMG_HEAD)
seed_data = image_to_data_url(IMG_SEED)

# Fixed gameplay parameters per user request
speed = 10
grid_size = 12
canvas_px = 500

html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{ margin:0; padding:0; background:#111; color:#eee; font-family: Arial, Helvetica, sans-serif; }}
    #container {{ display:flex; align-items:center; justify-content:center; padding:10px; }}
    canvas {{ background:#222; border-radius:8px; box-shadow: 0 6px 24px rgba(0,0,0,0.6); }}
    #info {{ color:#ccc; font-size:14px; text-align:center; margin-top:8px; }}
    /* mobile control styles */
    .controls {{ position: fixed; left: 50%; transform: translateX(-50%); bottom: 18px; display:flex; flex-direction:column; align-items:center; gap:8px; z-index:9999; }}
    .controls .hrow {{ display:flex; gap:8px; }}
    .control-btn {{ width:56px; height:56px; border-radius:12px; background:rgba(255,255,255,0.06); color:#fff; border:1px solid rgba(255,255,255,0.08); font-size:22px; touch-action: none; }}
    @media (min-width:700px) {{ .controls {{ display:none; }} }}
  </style>
</head>
<body>
  <div id="container">
    <canvas id="game" width="{canvas_px}" height="{canvas_px}"></canvas>
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
  const px = x + tileSize/2;
  const py = y + tileSize/2;
  let angle = 0;
  if (dirX === 1 && dirY === 0) angle = 0;
  if (dirX === -1 && dirY === 0) angle = Math.PI;
  if (dirX === 0 && dirY === -1) angle = -Math.PI/2;
  if (dirX === 0 && dirY === 1) angle = Math.PI/2;
  ctx.save();
  ctx.translate(px, py);
  ctx.rotate(angle);
  ctx.drawImage(image, -tileSize/2, -tileSize/2, tileSize, tileSize);
  ctx.restore();
}

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

  // 画蛇身体（方块）
  for (let i = snake.length-1; i >= 1; i--) {{
    const s = snake[i];
    ctx.fillStyle = i%2===0 ? '#4caf50' : '#2e7d32';
    ctx.fillRect(s.x*tileSize+2, s.y*tileSize+2, tileSize-4, tileSize-4);
  }}

  // 画蛇头（图片，带方向）
  const headPx = snake[0].x * tileSize;
  const headPy = snake[0].y * tileSize;
  drawRotatedImage(headImg, headPx, headPy, velocity.x, velocity.y);
 
  // 绘制分数
  ctx.fillStyle = 'rgba(0,0,0,0.6)';
  ctx.fillRect(8,8,120,44);
  ctx.fillStyle = '#fff';
  ctx.font = Math.max(12, tileSize*0.4) + 'px Arial';
  ctx.textAlign = 'left';
  ctx.fillText('得分: ' + score, 14, 30);
  ctx.fillText('最高: ' + bestScore, 14, 48);
}}

// 启动主循环
setInterval(gameLoop, 1000 / speed);

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

