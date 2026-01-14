// Simple Canvas 2D snake implementation with smooth rendering, particles, and HUD
(function(){
  const Streamlit = window.Streamlit || null;
  // config will be injected by app.py as window.GAME_CONFIG
  const cfg = window.GAME_CONFIG || {};
  const canvas = document.getElementById('canvas-game');
  const ctx = canvas.getContext('2d');
  let w = canvas.width = cfg.width || 600;
  let h = canvas.height = cfg.height || 600;
  let tileCount = cfg.grid || 12;
  let tileSize = Math.min(w,h)/tileCount;
  let speed = cfg.speed || 6;
  let skin = cfg.skin || { bodyGrad:['#39ff14','#00b894'], glow:'rgba(57,255,20,0.25)', foodColor:'#ffd27f' };

  // state
  let snake = [{x:Math.floor(tileCount/2), y:Math.floor(tileCount/2)}];
  let vel = {x:1,y:0};
  let tail = 4;
  let food = spawnFood();
  let score = 0;
  let running = true;
  let particles = [];
  let level = 1;

  function spawnFood(){
    while(true){
      const p={x:Math.floor(Math.random()*tileCount),y:Math.floor(Math.random()*tileCount)};
      if(!snake.some(s=>s.x===p.x&&s.y===p.y)) return p;
    }
  }

  function drawRounded(x,y,wid,hei,r,fill){
    ctx.beginPath();
    ctx.moveTo(x+r,y); ctx.lineTo(x+wid-r,y); ctx.quadraticCurveTo(x+wid,y,x+wid,y+r);
    ctx.lineTo(x+wid,y+hei-r); ctx.quadraticCurveTo(x+wid,y+hei,x+wid-r,y+hei);
    ctx.lineTo(x+r,y+hei); ctx.quadraticCurveTo(x,y+hei,x,y+hei-r);
    ctx.lineTo(x,y+r); ctx.quadraticCurveTo(x,y,x+r,y);
    ctx.closePath();
    if(fill) ctx.fill();
  }

  function draw(){
    // update
    const head = { x:(snake[0].x+vel.x+tileCount)%tileCount, y:(snake[0].y+vel.y+tileCount)%tileCount };
    if(snake.some((s,i)=>i>0 && s.x===head.x && s.y===head.y)){ running=false; sendScore(); return; }
    snake.unshift(head);
    while(snake.length>tail) snake.pop();
    if(head.x===food.x && head.y===food.y){
      tail++; score++; spawnParticles(head); food=spawnFood(); levelUpIfNeeded();
      // send immediate score to parent
      if(Streamlit && Streamlit.setComponentValue) Streamlit.setComponentValue({score});
    }
    // draw background
    ctx.fillStyle = '#071b20'; ctx.fillRect(0,0,w,h);
    // draw food glow
    ctx.save(); ctx.globalCompositeOperation='lighter';
    ctx.fillStyle = skin.foodColor || '#ffd27f';
    ctx.beginPath(); ctx.arc(food.x*tileSize+tileSize/2, food.y*tileSize+tileSize/2, tileSize*0.6,0,Math.PI*2); ctx.fill();
    ctx.restore();
    // draw snake segments with gradient and scales
    for(let i=snake.length-1;i>=1;i--){
      const s=snake[i]; const t=i/snake.length;
      const x=s.x*tileSize + tileSize*0.06, y=s.y*tileSize + tileSize*0.12;
      const wid=tileSize*0.88, hei=tileSize*0.7, r=tileSize*0.12;
      const hue = 120 - t*50;
      const g = ctx.createLinearGradient(x,y,x+wid,y+hei);
      g.addColorStop(0, `hsl(${hue},72%,${48 - t*18}%)`); g.addColorStop(1, `hsl(${Math.max(0,hue-18)},60%,${Math.max(18,28 - t*12)}%)`);
      ctx.fillStyle=g; drawRounded(x,y,wid,hei,r,true);
      // scales
      ctx.fillStyle='rgba(255,255,255,0.08)';
      const scaleW = Math.max(6,tileSize*0.18);
      const rows = Math.max(2, Math.floor(hei/(scaleW*0.5)));
      for(let r0=0;r0<rows;r0++){ const yOff=y + r0*(scaleW*0.45)+2; for(let sx=0;sx<wid-4;sx+=scaleW*0.7){ const px=x+sx+(r0%2?scaleW*0.35:0); ctx.beginPath(); ctx.arc(px,yOff,scaleW*0.32,Math.PI,2*Math.PI); ctx.fill(); } }
    }
    // head (image)
    const hx=snake[0].x*tileSize, hy=snake[0].y*tileSize;
    const headImg = new Image(); headImg.src='head.png';
    ctx.drawImage(headImg, hx, hy, tileSize, tileSize);
    // particles
    updateParticles(); renderParticles();
    // HUD level animation is handled by host via CSS
  }

  function spawnParticles(head){ for(let i=0;i<12;i++){ const angle=Math.random()*Math.PI*2; particles.push({ x: head.x*tileSize+tileSize/2, y: head.y*tileSize+tileSize/2, vx:Math.cos(angle)*(1+Math.random()*2), vy:Math.sin(angle)*(1+Math.random()*2), life:40+Math.floor(Math.random()*20) }); } }
  function updateParticles(){ for(let i=particles.length-1;i>=0;i--){ const p=particles[i]; p.x+=p.vx; p.y+=p.vy; p.vy+=0.05; p.life--; if(p.life<=0) particles.splice(i,1); } }
  function renderParticles(){ for(const p of particles){ ctx.fillStyle='rgba(255,200,120,'+Math.max(0,p.life/60)+')'; ctx.beginPath(); ctx.arc(p.x,p.y,4,0,Math.PI*2); ctx.fill(); } }

  function levelUpIfNeeded(){ if(score>0 && score%5===0){ level++; // notify host
    if(Streamlit && Streamlit.setComponentValue) Streamlit.setComponentValue({level}); const hud=document.getElementById('level-hud'); if(hud){ hud.innerText='关卡 '+level; hud.classList.add('show'); setTimeout(()=>hud.classList.remove('show'),1400); } } }

  function sendScore(){ if(Streamlit && Streamlit.setComponentValue) Streamlit.setComponentValue({score, event:'gameover'}); }

  // input
  window.addEventListener('keydown',e=>{ if(e.key==='ArrowLeft'&&vel.x!==1) vel={x:-1,y:0}; if(e.key==='ArrowUp'&&vel.y!==1) vel={x:0,y:-1}; if(e.key==='ArrowRight'&&vel.x!==-1) vel={x:1,y:0}; if(e.key==='ArrowDown'&&vel.y!==-1) vel={x:0,y:1}; });

  // loop using rAF
  let last=0; function raf(ts){ if(!last) last=ts; const dt=ts-last; const msPerFrame=1000/speed; if(dt>msPerFrame){ draw(); last=ts; } requestAnimationFrame(raf); } requestAnimationFrame(raf);

  // expose for debug
  window.__snake = { spawnFood, setSkin:(s)=>{skin=s;} };
})();

