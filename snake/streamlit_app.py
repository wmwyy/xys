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

st.set_page_config(page_title="贪吃蛇 - 炫酷版", layout="centered")
st.title("🐍 贪吃蛇 - 炫酷版")
st.markdown("""
<div style="text-align: center; margin-bottom: 20px; color: #666;">
  🎮 使用方向键或触摸按钮控制蛇的移动<br>
  🍎 吃到食物获得分数，躲避撞到自己<br>
  📱 支持移动端触摸控制
</div>
""", unsafe_allow_html=True)

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
canvas_px = 680

html = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    body {{
      margin:0; padding:0;
      background: linear-gradient(45deg, #0a0a0a, #1a1a2e, #16213e, #0f0f23);
      background-size: 400% 400%;
      animation: gradientShift 8s ease infinite;
      color:#eef2f3;
      font-family: 'Segoe UI', Inter, Arial, Helvetica, sans-serif;
      overflow-x: hidden;
    }}
    @keyframes gradientShift {{
      0% {{ background-position: 0% 50%; }}
      50% {{ background-position: 100% 50%; }}
      100% {{ background-position: 0% 50%; }}
    }}
    body::before {{
      content: '';
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                  radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.2) 0%, transparent 50%),
                  radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.1) 0%, transparent 50%);
      pointer-events: none;
      z-index: -1;
    }}
    #container {{ display:flex; align-items:flex-start; justify-content:center; padding:18px; gap:20px; }}
    canvas {{
      background: linear-gradient(135deg, #1a1a2e, #16213e);
      border-radius:16px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.8),
                  0 0 60px rgba(120, 119, 198, 0.2),
                  inset 0 2px 0 rgba(255,255,255,0.1),
                  inset 0 -2px 0 rgba(0,0,0,0.2);
      border:2px solid rgba(120, 119, 198, 0.3);
      position: relative;
      overflow: hidden;
    }}
    canvas::before {{
      content: '';
      position: absolute;
      top: -50%; left: -50%; right: -50%; bottom: -50%;
      background: conic-gradient(from 0deg, transparent, rgba(255,255,255,0.1), transparent);
      animation: rotate 4s linear infinite;
      pointer-events: none;
    }}
    @keyframes rotate {{
      from {{ transform: rotate(0deg); }}
      to {{ transform: rotate(360deg); }}
    }}
    #info {{ display:none; }}
    /* scorecard (placed left of canvas to avoid overlap) */
    #scorecard {{
      background: linear-gradient(135deg, rgba(26, 26, 46, 0.9), rgba(22, 33, 62, 0.9));
      color:#fff;
      padding:16px 18px;
      border-radius:14px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.6),
                  0 0 0 1px rgba(255,255,255,0.1),
                  inset 0 1px 0 rgba(255,255,255,0.2);
      font-size:16px;
      min-width:100px;
      backdrop-filter: blur(10px);
      border: 1px solid rgba(120, 119, 198, 0.3);
      animation: glow 2s ease-in-out infinite alternate;
    }}
    @keyframes glow {{
      from {{ box-shadow: 0 8px 32px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.1), inset 0 1px 0 rgba(255,255,255,0.2); }}
      to {{ box-shadow: 0 8px 32px rgba(120, 119, 198, 0.3), 0 0 20px rgba(120, 119, 198, 0.2), inset 0 1px 0 rgba(255,255,255,0.2); }}
    }}
    #scorecard .label {{ color:#a8b2d1; font-size:12px; }}
    .game-area {{ flex: 1 1 auto; display:flex; align-items:flex-start; justify-content:center; }}
    /* mobile control styles */
    .controls {{ position: fixed; left: 50%; transform: translateX(-50%); bottom: 22px; display:flex; flex-direction:column; align-items:center; gap:18px; z-index:9999; }}
    .controls .hrow {{ display:flex; gap:36px; }}
    .control-btn {{
      width:68px; height:68px;
      border-radius:16px;
      background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
      color:#fff;
      border:2px solid rgba(120, 119, 198, 0.4);
      font-size:28px;
      touch-action: none;
      box-shadow: 0 8px 24px rgba(0,0,0,0.6),
                  0 0 0 1px rgba(255,255,255,0.1),
                  inset 0 1px 0 rgba(255,255,255,0.2);
      transition: all 0.2s ease;
      position: relative;
      overflow: hidden;
    }}
    .control-btn::before {{
      content: '';
      position: absolute;
      top: 0; left: -100%; width: 100%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      transition: left 0.5s;
    }}
    .control-btn:hover {{
      transform: translateY(-2px);
      box-shadow: 0 12px 32px rgba(0,0,0,0.8),
                  0 0 20px rgba(120, 119, 198, 0.3),
                  inset 0 1px 0 rgba(255,255,255,0.3);
    }}
    .control-btn:active {{
      transform: translateY(0);
      box-shadow: 0 4px 16px rgba(0,0,0,0.8),
                  inset 0 2px 4px rgba(0,0,0,0.3);
    }}
    .control-btn:active::before {{ left: 100%; }}
    @media (min-width:700px) {{ .controls {{ display:none; }} }}
    /* responsive: stack on small screens */
    @media (max-width:700px) {{
      #container {{ flex-direction:column; align-items:center; padding:12px; gap:12px; }}
      .game-area {{ width:100%; }}
      canvas {{ width: min(96vw, {canvas_px}px); height: auto; }}
      #scorecard {{ position: relative; left:0; top:0; margin-bottom:8px; }}
      #scorebuttons {{ position: relative; left:0; top:0; margin-top:8px; }}
      .controls {{ position: static; transform:none; bottom:auto; left:auto; }}
    }}
    /* level HUD */
    .level-hud {{
      position: fixed; left:50%; top:14vh; transform:translateX(-50%) scale(0.8);
      background: linear-gradient(135deg, rgba(120, 119, 198, 0.9), rgba(255, 119, 198, 0.8));
      color:#fff; padding:18px 26px; border-radius:16px;
      font-size:24px; font-weight: bold;
      box-shadow: 0 20px 60px rgba(120, 119, 198, 0.4),
                  0 0 40px rgba(255, 119, 198, 0.3);
      opacity:0; pointer-events:none; z-index:99999;
      transition: all 0.5s cubic-bezier(.2,.8,.2,1);
      border: 2px solid rgba(255,255,255,0.3);
      backdrop-filter: blur(15px);
    }}
    .level-hud.show {{
      opacity:1; transform:translateX(-50%) scale(1.1);
      animation: levelPulse 1.4s ease-in-out;
    }}
    @keyframes levelPulse {{
      0%, 100% {{ transform: translateX(-50%) scale(1.1); }}
      50% {{ transform: translateX(-50%) scale(1.15); }}
    }}
    /* score buttons */
    #scorebuttons button {{
      background: linear-gradient(135deg, rgba(26, 26, 46, 0.8), rgba(22, 33, 62, 0.8));
      color:#fff;
      border-radius:10px;
      padding:8px 12px;
      border:1px solid rgba(120, 119, 198, 0.3);
      box-shadow: 0 4px 16px rgba(0,0,0,0.4);
      transition: all 0.2s ease;
      font-weight: 500;
    }}
    #scorebuttons button:hover {{
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(120, 119, 198, 0.3);
    }}
    #scorebuttons button:active {{
      transform: translateY(0);
      box-shadow: 0 2px 8px rgba(0,0,0,0.4);
    }}
  </style>
</head>
<body>
  <div id="level-hud" class="level-hud" aria-hidden="true">关卡 1</div>
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
  <div id="scorebuttons" style="position: fixed; right: 18px; top: 80px; left: auto; display:flex; gap:8px; z-index:10000;">
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
let speed = {speed};
const scoreEl = document.getElementById('score-current');
const bestEl = document.getElementById('score-best');
const btnPause = document.getElementById('btn-pause');
const btnReset = document.getElementById('btn-reset');
// Leveling and animation state
let level = 1;
let eatenSinceLevel = 0;
let seedsToLevel = 5;
const levelEl = null; // placeholder if needed
// particle effects for eat animation
let particles = [];


// responsive: adapt canvas size for mobile while keeping pixel size prop
function resizeCanvasForDevice() {{
  const maxW = Math.min(window.innerWidth - 24, {canvas_px});
  canvas.width = maxW;
  canvas.height = maxW;
  tileSize = canvas.width / tileCount;
  // Reinitialize background particles when canvas resizes
  initBackgroundParticles();
}}
resizeCanvasForDevice();
window.addEventListener('resize', resizeCanvasForDevice);

// Initialize background particles
initBackgroundParticles();

// Startup animation
function startupAnimation() {{
  const centerX = canvas.width / 2;
  const centerY = canvas.height / 2;

  // Create explosion effect at startup
  for (let i = 0; i < 20; i++) {{
    setTimeout(() => {{
      spawnParticles(centerX, centerY, 8);
    }}, i * 100);
  }}

  // Add some initial particles around the snake
  setTimeout(() => {{
    for (let i = 0; i < snake.length; i++) {{
      const segment = snake[i];
      spawnParticles(segment.x * tileSize + tileSize/2, segment.y * tileSize + tileSize/2, 3);
    }}
  }}, 1000);
}}

startupAnimation();

let snake = [ {{ x: Math.floor(tileCount/2), y: Math.floor(tileCount/2) }} ];
let velocity = {{ x: 1, y: 0 }};
let food = spawnFood();
let tail = 4;
// Ensure snake initial segments are visible (create initial segments equal to tail)
{{
  const center = {{ x: Math.floor(tileCount/2), y: Math.floor(tileCount/2) }};
  snake = [];
  for (let i = 0; i < tail; i++) {{
    // place segments to the left of head so snake is visible on start
    snake.push({{ x: (center.x - i + tileCount) % tileCount, y: center.y }});
  }}
}}
let gameOver = false;
let score = 0;
let bestScore = localStorage.getItem('snake_best_score') ? parseInt(localStorage.getItem('snake_best_score')) : 0;
let running = true;
// Background particles
let bgParticles = [];
let gameStartTime = Date.now();
let lastKeyTime = 0;

document.addEventListener('keydown', (e) => {{
  let newVelocity = null;
  if (e.key === 'ArrowLeft' && velocity.x !== 1) {{ newVelocity = {{x:-1,y:0}}; }}
  if (e.key === 'ArrowUp' && velocity.y !== 1) {{ newVelocity = {{x:0,y:-1}}; }}
  if (e.key === 'ArrowRight' && velocity.x !== -1) {{ newVelocity = {{x:1,y:0}}; }}
  if (e.key === 'ArrowDown' && velocity.y !== -1) {{ newVelocity = {{x:0,y:1}}; }}

  if (newVelocity && (Date.now() - lastKeyTime) > 50) {{
    velocity = newVelocity;
    lastKeyTime = Date.now();

    // Add key press particle effect
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    spawnParticles(centerX, centerY, 6);
  }}
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

  // Add touch feedback sound
  playSound(400, 0.08, 'square');

  // Add visual feedback
  if (evt && evt.target) {{
    evt.target.style.transform = 'scale(0.95)';
    setTimeout(() => {{
      evt.target.style.transform = '';
    }}, 100);
  }}
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

function spawnParticles(cx, cy, count=12) {{
  for (let i=0;i<count;i++) {{
    const angle = Math.random()*Math.PI*2;
    const speed = 1 + Math.random()*2;
    particles.push({{
      x: cx + tileSize/2,
      y: cy + tileSize/2,
      vx: Math.cos(angle)*speed,
      vy: Math.sin(angle)*speed,
      life: 40 + Math.floor(Math.random()*20),
      size: 4 + Math.random()*6,
      alpha: 1
    }});
  }}
}

function initBackgroundParticles() {{
  bgParticles = [];
  for (let i = 0; i < 50; i++) {{
    bgParticles.push({{
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.5,
      size: Math.random() * 2 + 1,
      alpha: Math.random() * 0.5 + 0.1,
      color: ['#7877c6', '#ff77c6', '#78c6ff', '#c678ff'][Math.floor(Math.random()*4)]
    }});
  }}
}}

function updateBackgroundParticles() {{
  for (const p of bgParticles) {{
    p.x += p.vx;
    p.y += p.vy;

    // Wrap around edges
    if (p.x < 0) p.x = canvas.width;
    if (p.x > canvas.width) p.x = 0;
    if (p.y < 0) p.y = canvas.height;
    if (p.y > canvas.height) p.y = 0;

    // Subtle pulsing
    p.alpha = 0.1 + 0.4 * (0.5 + 0.5 * Math.sin(Date.now() * 0.001 + p.x * 0.01));
  }}
}}

function renderBackgroundParticles() {{
  for (const p of bgParticles) {{
    ctx.globalAlpha = p.alpha;
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();

    // Add glow effect
    ctx.shadowBlur = 10;
    ctx.shadowColor = p.color;
    ctx.fill();
    ctx.shadowBlur = 0;
  }}
  ctx.globalAlpha = 1;
}}

function updateParticles() {{
  for (let i = particles.length-1; i>=0;i--) {{
    const p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    p.vy += 0.05;
    p.life -= 1;
    p.alpha = Math.max(0, p.life/60);
    if (p.life <= 0) particles.splice(i,1);
  }}
}

function renderParticles() {{
  for (const p of particles) {{
    ctx.globalAlpha = p.alpha;
    ctx.fillStyle = p.color || 'rgba(255,220,120,0.9)';
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size*0.6, 0, Math.PI*2);
    ctx.fill();

    // Add glow effect for particles
    ctx.shadowBlur = 8;
    ctx.shadowColor = p.color || '#ffd27f';
    ctx.fill();
    ctx.shadowBlur = 0;
  }}
  ctx.globalAlpha = 1;
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
    // Animated game over screen
    const time = Date.now() * 0.002;
    ctx.fillStyle = 'rgba(0,0,0,0.8)';
    ctx.fillRect(0,0,canvas.width,canvas.height);

    // Pulsing background effect
    ctx.fillStyle = `rgba(255, 107, 157, ${0.1 + 0.1 * Math.sin(time)})`;
    ctx.fillRect(0,0,canvas.width,canvas.height);

    ctx.fillStyle = '#fff';
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.shadowBlur = 10;
    ctx.shadowColor = '#ff6b9d';
    ctx.fillText('游戏结束', canvas.width/2, canvas.height/2 - 40);

    ctx.font = '18px Arial';
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#ddd';
    ctx.fillText(`最终得分: ${score}`, canvas.width/2, canvas.height/2);

    ctx.fillStyle = '#aaa';
    ctx.fillText('按 F5 刷新重玩', canvas.width/2, canvas.height/2 + 30);

    // Animated particles for game over
    if (Math.random() < 0.1) {{
      spawnParticles(Math.random() * canvas.width, Math.random() * canvas.height, 3);
    }}

    return;
  }}
  // If paused, draw overlay and skip game updates
  if (!running) {{
    const time = Date.now() * 0.003;
    ctx.fillStyle = `rgba(0,0,0,${0.5 + 0.1 * Math.sin(time)})`;
    ctx.fillRect(0,0,canvas.width,canvas.height);

    ctx.fillStyle = '#fff';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.shadowBlur = 15;
    ctx.shadowColor = '#7877c6';
    ctx.fillText('⏸️ 已暂停', canvas.width/2, canvas.height/2 - 20);

    ctx.font = '16px Arial';
    ctx.shadowBlur = 0;
    ctx.fillStyle = '#ccc';
    ctx.fillText('点击继续按钮恢复游戏', canvas.width/2, canvas.height/2 + 20);

    // Animated pause particles
    if (Math.random() < 0.05) {{
      spawnParticles(Math.random() * canvas.width, Math.random() * canvas.height, 2);
    }}
    return;
  }}

  // 移动蛇头
  const head = {{ x: (snake[0].x + velocity.x + tileCount) % tileCount, y: (snake[0].y + velocity.y + tileCount) % tileCount }};
  // 碰撞自身
  if (snake.some((s, idx) => idx>0 && s.x === head.x && s.y === head.y)) {{
    gameOver = true;
    // Play game over sound
    playSound(200, 0.8, 'sawtooth');
    return;
  }}
  snake.unshift(head);
  while (snake.length > tail) snake.pop();

  // 吃到食物
  if (head.x === food.x && head.y === food.y) {{
    tail += 1;
    score += 1;
    eatenSinceLevel += 1;
    // particles and feedback
    spawnParticles(head.x*tileSize, head.y*tileSize, 14);
    // Play eat sound
    playSound(600 + score * 20, 0.15, 'triangle');

    if (score > bestScore) {{
      bestScore = score;
      localStorage.setItem('snake_best_score', bestScore);
      // Play high score sound
      playSound(1000, 0.3, 'sine');
    }}
    // level up check
    if (eatenSinceLevel >= seedsToLevel) {{
      level += 1;
      eatenSinceLevel = 0;
      seedsToLevel = Math.floor(seedsToLevel * 1.4) + 1;
      // increase speed slightly
      speed = Math.min(22, speed + 1);
      startLoop();
      // Play level up sound
      playSound(800, 0.5, 'sawtooth');
      // show HUD animation
      const hud = document.getElementById('level-hud');
      if (hud) {{
        hud.innerText = '关卡 ' + level;
        hud.classList.add('show');
        hud.setAttribute('aria-hidden','false');
        setTimeout(()=>{{ hud.classList.remove('show'); hud.setAttribute('aria-hidden','true'); }}, 1400);
      }}
    }}
    food = spawnFood();
  }}

  // 绘制
  ctx.clearRect(0,0,canvas.width,canvas.height);

  // Update and render background particles
  updateBackgroundParticles();
  renderBackgroundParticles();

  // 画食物（居中）- 添加闪烁效果
  const foodGlow = 0.8 + 0.2 * Math.sin(Date.now() * 0.008);
  ctx.globalAlpha = foodGlow;
  ctx.shadowBlur = 15;
  ctx.shadowColor = '#ffd27f';
  ctx.drawImage(seedImg, food.x*tileSize, food.y*tileSize, tileSize, tileSize);
  ctx.shadowBlur = 0;
  ctx.globalAlpha = 1;

  // 画蛇身体（鳞片效果的圆角矩形段）
  function drawSegmentAt(cellX, cellY, t) {{
    const x = cellX * tileSize;
    const y = cellY * tileSize;
    const w = tileSize * 0.88;
    const h = tileSize * 0.7;
    const rx = Math.max(4, tileSize * 0.12);
    const cx = x + (tileSize - w) / 2;
    const cy = y + (tileSize - h) / 2;
    const hue = 120 - t * 50;
    const light1 = 46 - t * 16;
    const light2 = 28 - t * 10;
    const grad = ctx.createLinearGradient(cx, cy, cx + w, cy + h);
    grad.addColorStop(0, `hsl(${hue},72%,${light1}%)`);
    grad.addColorStop(1, `hsl(${Math.max(0,hue-18)},60%,${Math.max(18,light2)}%)`);
    // base rounded rect
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
    // draw small scale arcs
    const scaleW = Math.max(6, tileSize * 0.18);
    const rows = Math.max(2, Math.floor(h / (scaleW*0.5)));
    ctx.fillStyle = 'rgba(255,255,255,0.08)';
    for (let r = 0; r < rows; r++) {{
      const yOff = cy + r * (scaleW*0.45) + 2;
      for (let sx = 0; sx < w - 4; sx += scaleW*0.7) {{
        const px = cx + sx + (r%2 ? scaleW*0.35 : 0);
        ctx.beginPath();
        ctx.arc(px, yOff, scaleW*0.32, Math.PI, 2*Math.PI);
        ctx.fill();
      }}
    }}
    // outline
    ctx.lineWidth = Math.max(1, tileSize*0.03);
    ctx.strokeStyle = 'rgba(0,0,0,0.28)';
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
 
  // 更新并显示分数卡片与等级
  if (scoreEl) scoreEl.innerText = '得分: ' + score;
  if (bestEl) bestEl.innerText = '最高: ' + bestScore;
  // render particles
  updateParticles();
  renderParticles();
  // level UI (draw subtle level badge)
  ctx.fillStyle = 'rgba(255,255,255,0.06)';
  ctx.fillRect(canvas.width - 92, 8, 76, 34);
  ctx.fillStyle = '#fff';
  ctx.font = '14px Arial';
  ctx.textAlign = 'center';
  ctx.fillText('关卡 ' + level, canvas.width - 50, 30);
}}

// 启动主循环 -- use adjustable interval so we can change speed on level up
let intervalId = null;
function startLoop() {{
  if (intervalId) clearInterval(intervalId);
  intervalId = setInterval(gameLoop, 1000 / speed);
}}
startLoop();

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

// Audio functions
function playSound(frequency, duration, type = 'sine') {{
  try {{
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
    oscillator.type = type;

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + duration);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + duration);
  }} catch (e) {{
    // Audio not supported, silently fail
  }}
}}

// Add click sound effects to buttons
function addButtonSounds() {{
  const buttons = document.querySelectorAll('button');
  buttons.forEach(btn => {{
    btn.addEventListener('click', () => {{
      playSound(800, 0.1, 'square');
    }});
  }});
}}

// Call after DOM is ready
setTimeout(addButtonSounds, 1000);

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

