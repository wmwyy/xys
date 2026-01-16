// 游戏配置
const GRID_SIZE = 20;
const CANVAS_SIZE = 400;
const INITIAL_SPEED = 150;

// 游戏状态
let canvas, ctx;
let snake = [];
let food = {};
let direction = { x: 0, y: 0 };
let nextDirection = { x: 0, y: 0 };
let score = 0;
let highScore = localStorage.getItem('snakeHighScore') || 0;
let gameRunning = false;
let gamePaused = false;
let gameLoop;
// 图片资源（将图片放到 snake/ 目录，命名为 head.png 和 food.png）
const headImg = new Image();
const foodImg = new Image();
let headImgLoaded = false;
let foodImgLoaded = false;
// 内嵌回退图片（SVG data URL），以防文件缺失
const fallbackHeadSrc = 'data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><circle cx=\"50\" cy=\"50\" r=\"50\" fill=\"%23e74c3c\"/></svg>';
const fallbackSeedSrc = 'data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 100 100\"><circle cx=\"50\" cy=\"50\" r=\"50\" fill=\"%23f39c12\"/></svg>';
// 先尝试常用命名，再回退到 seed.png（有些用户以 seed.png 命名食物图片）
headImg.src = 'head.png';
headImg.onload = () => { headImgLoaded = true; };
headImg.onerror = () => {
    // 如果本地 head.png 不存在，回退到内嵌 SVG（避免破图）
    if (!headImgLoaded && !headImg._triedFallback) {
        headImg._triedFallback = true;
        headImg.src = fallbackHeadSrc;
    }
};

// 先尝试 food.png，失败时回退到 seed.png
foodImg.onload = () => { foodImgLoaded = true; };
foodImg.onerror = () => {
    // 先尝试使用项目内的 seed.png 回退，如果不存在则使用内嵌SVG
    if (!foodImgLoaded && !foodImg._triedSeed) {
        foodImg._triedSeed = true;
        foodImg.src = 'seed.png';
    } else if (!foodImgLoaded && !foodImg._triedFallback) {
        foodImg._triedFallback = true;
        foodImg.src = fallbackSeedSrc;
    }
};
foodImg.src = 'food.png';

// 绘制圆形图片的工具函数
function drawCircularImage(img, x, y, size) {
    const cx = x + size / 2;
    const cy = y + size / 2;
    const radius = size / 2;
    ctx.save();
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.closePath();
    ctx.clip();
    ctx.drawImage(img, x, y, size, size);
    ctx.restore();
}

// DOM 元素
let scoreElement, highScoreElement, startBtn, pauseBtn, resetBtn;

// 初始化游戏
function init() {
    canvas = document.getElementById('game-canvas');
    ctx = canvas.getContext('2d');

    scoreElement = document.getElementById('score');
    highScoreElement = document.getElementById('high-score');
    startBtn = document.getElementById('start-btn');
    pauseBtn = document.getElementById('pause-btn');
    resetBtn = document.getElementById('reset-btn');

    highScoreElement.textContent = highScore;

    // 绑定事件监听器
    bindEvents();

    // 初始化蛇的位置
    resetGame();
}

// 绑定事件监听器
function bindEvents() {
    // 按钮事件
    startBtn.addEventListener('click', startGame);
    pauseBtn.addEventListener('click', togglePause);
    resetBtn.addEventListener('click', resetGame);

    // 键盘事件
    document.addEventListener('keydown', handleKeyPress);

    // 触摸控制事件
    const controlBtns = document.querySelectorAll('.control-btn');
    controlBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const dir = e.target.dataset.direction;
            handleDirectionChange(dir);
        });
        // 支持触摸开始事件，提升移动端响应速度
        btn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const dir = e.currentTarget.dataset.direction;
            handleDirectionChange(dir);
        }, { passive: false });
    });

    // 绑定移动端固定 D-pad 按键（如果存在）
    const dpadBtns = document.querySelectorAll('.mobile-dpad .dpad-btn');
    dpadBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const dir = e.currentTarget.dataset.direction;
            handleDirectionChange(dir);
        });
        btn.addEventListener('touchstart', (e) => {
            e.preventDefault();
            const dir = e.currentTarget.dataset.direction;
            handleDirectionChange(dir);
        }, { passive: false });
    });

    // 触摸事件（屏幕点击控制）
    canvas.addEventListener('touchstart', handleTouch, { passive: false });
}

// 处理键盘输入
function handleKeyPress(e) {
    e.preventDefault();

    switch(e.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
            if (direction.y === 0) nextDirection = { x: 0, y: -1 };
            break;
        case 'ArrowDown':
        case 's':
        case 'S':
            if (direction.y === 0) nextDirection = { x: 0, y: 1 };
            break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
            if (direction.x === 0) nextDirection = { x: -1, y: 0 };
            break;
        case 'ArrowRight':
        case 'd':
        case 'D':
            if (direction.x === 0) nextDirection = { x: 1, y: 0 };
            break;
        case ' ':
            togglePause();
            break;
    }
}

// 处理触摸控制
function handleDirectionChange(dir) {
    switch(dir) {
        case 'up':
            if (direction.y === 0) nextDirection = { x: 0, y: -1 };
            break;
        case 'down':
            if (direction.y === 0) nextDirection = { x: 0, y: 1 };
            break;
        case 'left':
            if (direction.x === 0) nextDirection = { x: -1, y: 0 };
            break;
        case 'right':
            if (direction.x === 0) nextDirection = { x: 1, y: 0 };
            break;
    }
}

// 处理触摸事件
function handleTouch(e) {
    e.preventDefault();

    if (!gameRunning || gamePaused) return;

    const rect = canvas.getBoundingClientRect();
    const touch = e.touches[0];
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const deltaX = touch.clientX - centerX;
    const deltaY = touch.clientY - centerY;

    // 判断触摸位置相对于蛇头的方向
    if (Math.abs(deltaX) > Math.abs(deltaY)) {
        // 水平方向
        if (deltaX > 0 && direction.x === 0) {
            nextDirection = { x: 1, y: 0 };
        } else if (deltaX < 0 && direction.x === 0) {
            nextDirection = { x: -1, y: 0 };
        }
    } else {
        // 垂直方向
        if (deltaY > 0 && direction.y === 0) {
            nextDirection = { x: 0, y: 1 };
        } else if (deltaY < 0 && direction.y === 0) {
            nextDirection = { x: 0, y: -1 };
        }
    }
}

// 开始游戏
function startGame() {
    if (gameRunning) return;

    gameRunning = true;
    gamePaused = false;
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    resetBtn.disabled = false;

    gameLoop = setInterval(gameStep, INITIAL_SPEED);
}

// 暂停/继续游戏
function togglePause() {
    if (!gameRunning) return;

    gamePaused = !gamePaused;
    pauseBtn.textContent = gamePaused ? '继续' : '暂停';

    if (gamePaused) {
        clearInterval(gameLoop);
        drawPaused();
    } else {
        gameLoop = setInterval(gameStep, INITIAL_SPEED);
        draw();
    }
}

// 重置游戏
function resetGame() {
    clearInterval(gameLoop);

    // 初始化蛇
    snake = [
        { x: 10, y: 10 },
        { x: 9, y: 10 },
        { x: 8, y: 10 }
    ];

    // 初始化方向
    direction = { x: 1, y: 0 };
    nextDirection = { x: 1, y: 0 };

    // 重置分数
    score = 0;
    scoreElement.textContent = score;

    // 生成食物
    generateFood();

    // 重置游戏状态
    gameRunning = false;
    gamePaused = false;
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    pauseBtn.textContent = '暂停';
    resetBtn.disabled = false;

    // 清除覆盖层
    draw();
}

// 生成食物
function generateFood() {
    do {
        food = {
            x: Math.floor(Math.random() * (CANVAS_SIZE / GRID_SIZE)),
            y: Math.floor(Math.random() * (CANVAS_SIZE / GRID_SIZE))
        };
    } while (snake.some(segment => segment.x === food.x && segment.y === food.y));
}

// 游戏主循环
function gameStep() {
    if (gamePaused) return;

    // 更新方向
    direction = nextDirection;

    // 计算新头部位置
    const head = { x: snake[0].x + direction.x, y: snake[0].y + direction.y };

    // 检查碰撞
    if (checkCollision(head)) {
        gameOver();
        return;
    }

    // 添加新头部
    snake.unshift(head);

    // 检查是否吃到食物
    if (head.x === food.x && head.y === food.y) {
        score += 10;
        scoreElement.textContent = score;

        // 更新最高分
        if (score > highScore) {
            highScore = score;
            highScoreElement.textContent = highScore;
            localStorage.setItem('snakeHighScore', highScore);
        }

        generateFood();
    } else {
        // 移除尾部
        snake.pop();
    }

    // 绘制游戏
    draw();
}

// 检查碰撞
function checkCollision(head) {
    // 墙壁碰撞
    if (head.x < 0 || head.x >= CANVAS_SIZE / GRID_SIZE ||
        head.y < 0 || head.y >= CANVAS_SIZE / GRID_SIZE) {
        return true;
    }

    // 自身碰撞
    return snake.some(segment => segment.x === head.x && segment.y === head.y);
}

// 游戏结束
function gameOver() {
    clearInterval(gameLoop);
    gameRunning = false;
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    drawGameOver();
}

// 绘制游戏
function draw() {
    // 清空画布
    ctx.fillStyle = '#2c3e50';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    // 绘制网格（可选）
    drawGrid();

    // 绘制蛇
    drawSnake();

    // 绘制食物
    drawFood();
}

// 绘制网格
function drawGrid() {
    ctx.strokeStyle = '#34495e';
    ctx.lineWidth = 1;

    for (let i = 0; i <= CANVAS_SIZE; i += GRID_SIZE) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, CANVAS_SIZE);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(CANVAS_SIZE, i);
        ctx.stroke();
    }
}

// 绘制蛇
function drawSnake() {
    snake.forEach((segment, index) => {
        const x = segment.x * GRID_SIZE + 1;
        const y = segment.y * GRID_SIZE + 1;
        const size = GRID_SIZE - 2;

        if (index === 0 && headImgLoaded) {
            // 使用圆形裁切绘制蛇头图片
            drawCircularImage(headImg, x, y, size);
        } else if (index === 0) {
            // 蛇头图片未就绪时的回退绘制
            ctx.fillStyle = '#e74c3c';
            ctx.fillRect(x, y, size, size);
        } else {
            // 蛇身
            ctx.fillStyle = '#27ae60';
            ctx.fillRect(x, y, size, size);
        }

        // 添加边框
        ctx.strokeStyle = '#2c3e50';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, size, size);
    });
}

// 绘制食物
function drawFood() {
    const x = food.x * GRID_SIZE + 1;
    const y = food.y * GRID_SIZE + 1;
    const size = GRID_SIZE - 2;

    if (foodImgLoaded) {
        // 使用圆形裁切绘制食物图片（种子）
        drawCircularImage(foodImg, x, y, size);
    } else {
        // 回退绘制（原有样式）
        ctx.fillStyle = '#f39c12';
        ctx.fillRect(x, y, size, size);

        // 添加边框
        ctx.strokeStyle = '#e67e22';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, size, size);

        // 添加食物高亮效果
        ctx.fillStyle = '#f1c40f';
        ctx.fillRect(food.x * GRID_SIZE + 4, food.y * GRID_SIZE + 4, GRID_SIZE - 8, GRID_SIZE - 8);
    }
}

// 绘制游戏结束界面
function drawGameOver() {
    draw();

    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    ctx.fillStyle = 'white';
    ctx.font = 'bold 30px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('游戏结束!', CANVAS_SIZE / 2, CANVAS_SIZE / 2 - 50);

    ctx.font = '20px Arial';
    ctx.fillText(`最终分数: ${score}`, CANVAS_SIZE / 2, CANVAS_SIZE / 2 - 10);
    ctx.fillText(`最高分: ${highScore}`, CANVAS_SIZE / 2, CANVAS_SIZE / 2 + 20);

    ctx.font = '16px Arial';
    ctx.fillText('点击重新开始按钮开始新游戏', CANVAS_SIZE / 2, CANVAS_SIZE / 2 + 60);
}

// 绘制暂停界面
function drawPaused() {
    draw();

    ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
    ctx.fillRect(0, 0, CANVAS_SIZE, CANVAS_SIZE);

    ctx.fillStyle = 'white';
    ctx.font = 'bold 36px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('游戏暂停', CANVAS_SIZE / 2, CANVAS_SIZE / 2);
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);