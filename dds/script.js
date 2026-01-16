class WhackAMole {
    constructor() {
        this.score = 0;
        this.timeLeft = 30;
        this.gameActive = false;
        this.currentMole = null;
        this.moleTimer = null;
        this.gameTimer = null;

        this.scoreElement = document.getElementById('score');
        this.timeElement = document.getElementById('time');
        this.messageElement = document.getElementById('message');
        this.startBtn = document.getElementById('start-btn');
        this.resetBtn = document.getElementById('reset-btn');

        this.holes = Array.from({length: 9}, (_, i) => document.getElementById(`hole-${i}`));
        this.moles = Array.from({length: 9}, (_, i) => document.getElementById(`mole-${i}`));
        // 候选图片（优先使用项目目录已存在的头像文件）
        this.candidateImages = ['./mole1.png', './mole2.png', './head.png', './seed.png'];
        this.availableImages = [];
        this.preloadImages();

        this.init();
    }

    // 预加载图片并记录可用的图片路径（便于用户只放 head.png / seed.png）
    preloadImages() {
        this.candidateImages.forEach((url) => {
            const img = new Image();
            img.onload = () => {
                // 避免重复加入
                if (!this.availableImages.includes(url)) {
                    this.availableImages.push(url);
                }
            };
            img.onerror = () => {
                // 忽略加载失败
            };
            img.src = url;
        });
    }

    init() {
        // 绑定事件监听器
        this.startBtn.addEventListener('click', () => this.startGame());
        this.resetBtn.addEventListener('click', () => this.resetGame());

        // 为每个地鼠添加点击事件
        this.moles.forEach((mole, index) => {
            mole.addEventListener('click', () => this.hitMole(index));
        });

        this.updateDisplay();
    }

    startGame() {
        if (this.gameActive) return;

        this.gameActive = true;
        this.score = 0;
        this.timeLeft = 30;
        this.currentMole = null;

        this.startBtn.disabled = true;
        this.resetBtn.disabled = false;
        this.messageElement.textContent = '游戏开始！快来打地鼠吧！';

        this.updateDisplay();

        // 开始倒计时
        this.gameTimer = setInterval(() => {
            this.timeLeft--;
            this.updateDisplay();

            if (this.timeLeft <= 0) {
                this.endGame();
            }
        }, 1000);

        // 开始显示地鼠
        this.showMole();
    }

    showMole() {
        if (!this.gameActive) return;

        // 隐藏当前地鼠
        if (this.currentMole !== null) {
            this.moles[this.currentMole].classList.remove('up');
        }

        // 随机选择一个洞
        let randomHole;
        do {
            randomHole = Math.floor(Math.random() * 9);
        } while (randomHole === this.currentMole); // 确保不是同一个洞

        this.currentMole = randomHole;

        // 选择一个可用的图片（优先使用已成功预加载的图片）
        let moleImage;
        if (this.availableImages.length > 0) {
            moleImage = this.availableImages[Math.floor(Math.random() * this.availableImages.length)];
        } else {
            // 回退到候选列表（可能会显示占位破图标，建议把图片放到 dds 并刷新）
            moleImage = this.candidateImages[Math.floor(Math.random() * this.candidateImages.length)];
        }
        this.moles[randomHole].style.backgroundImage = `url('${moleImage}')`;

        // 显示地鼠
        this.moles[randomHole].classList.add('up');

        // 设置地鼠消失的时间（1-3秒随机）
        const hideTime = Math.random() * 2000 + 1000;

        this.moleTimer = setTimeout(() => {
            if (this.gameActive && this.currentMole === randomHole) {
                this.moles[randomHole].classList.remove('up');
                // 清除图片显示
                this.moles[randomHole].style.backgroundImage = '';
                this.currentMole = null;

                // 继续显示下一个地鼠
                this.showMole();
            }
        }, hideTime);
    }

    hitMole(index) {
        if (!this.gameActive || this.currentMole !== index) return;

        // 增加分数
        this.score += 10;

        // 隐藏地鼠
        this.moles[index].classList.remove('up');
        this.moles[index].classList.add('hit');

        // 移除击中效果
        setTimeout(() => {
            this.moles[index].classList.remove('hit');
            // 击中后清除图片显示
            this.moles[index].style.backgroundImage = '';
        }, 500);

        this.currentMole = null;
        this.updateDisplay();

        // 显示击中消息
        this.showHitMessage();

        // 继续显示下一个地鼠
        this.showMole();
    }

    showHitMessage() {
        const messages = ['好棒！', '太棒了！', '厉害！', '继续加油！', '完美击中！'];
        const randomMessage = messages[Math.floor(Math.random() * messages.length)];
        this.messageElement.textContent = randomMessage;

        // 3秒后恢复默认消息
        setTimeout(() => {
            if (this.gameActive) {
                this.messageElement.textContent = '游戏进行中...';
            }
        }, 1000);
    }

    endGame() {
        this.gameActive = false;

        // 清理定时器
        clearInterval(this.gameTimer);
        clearTimeout(this.moleTimer);

        // 隐藏当前地鼠
        if (this.currentMole !== null) {
            this.moles[this.currentMole].classList.remove('up');
        }

        // 启用/禁用按钮
        this.startBtn.disabled = false;
        this.resetBtn.disabled = false;

        // 显示游戏结束消息
        this.messageElement.textContent = `游戏结束！你的得分是: ${this.score}`;

        // 显示最终得分
        if (this.score >= 200) {
            this.messageElement.textContent += ' 🎉 太厉害了！你是打地鼠高手！';
        } else if (this.score >= 100) {
            this.messageElement.textContent += ' 👍 不错的表现！';
        } else {
            this.messageElement.textContent += ' 💪 继续努力，下次会更好！';
        }
    }

    resetGame() {
        // 停止当前游戏
        this.gameActive = false;

        // 清理定时器
        clearInterval(this.gameTimer);
        clearTimeout(this.moleTimer);

        // 重置状态
        this.score = 0;
        this.timeLeft = 30;
        this.currentMole = null;

        // 隐藏所有地鼠
        this.moles.forEach(mole => {
            mole.classList.remove('up', 'hit');
            mole.style.backgroundImage = '';
        });

        // 启用/禁用按钮
        this.startBtn.disabled = false;
        this.resetBtn.disabled = false;

        // 重置显示
        this.updateDisplay();
        this.messageElement.textContent = '点击"开始游戏"开始玩吧！';
    }

    updateDisplay() {
        this.scoreElement.textContent = this.score;
        this.timeElement.textContent = this.timeLeft;
    }
}

// 初始化游戏
document.addEventListener('DOMContentLoaded', () => {
    new WhackAMole();
});