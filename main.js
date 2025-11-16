const WIDTH = 288;
const HEIGHT = 512;
const FPS = 60;
const PIPE_GAP = 160;
const PIPE_WIDTH = 70;
const PIPE_SPEED = 3;
const BIRD_X = 80;
const GRAVITY = 0.35;
const FLAP_STRENGTH = -7.5;
const BASE_HEIGHT = 80;
const BACKGROUND_COLOR = "#87CEEB";
const BIRD_FLAP_INTERVAL_MS = 120;
const CLOUD_SIZE_SCALE = 1.7;

const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");

const birdFramePaths = [
  "yellowbird-midflap.png",
  "yellowbird-downflap.png",
  "yellowbird-upflap.png",
];

let birdFrames = [];
let flapTimer = 0;
let lastTime = 0;

const jumpSound = createSound("jump.wav");
const hitSound = createSound("hit.wav");

class Bird {
  constructor(x, y) {
    this.x = x;
    this.y = y;
    this.velocity = 0;
    this.angle = 0;
    this.alive = true;
    this.frameIndex = 0;
    this.radius = Math.ceil(
      Math.max(birdFrames[0].width, birdFrames[0].height) / 2
    );
  }

  flap() {
    if (!this.alive) return;
    this.velocity = FLAP_STRENGTH;
    playSound(jumpSound);
  }

  update(dt) {
    this.velocity += GRAVITY * dt;
    this.velocity = Math.min(this.velocity, 10);
    this.y += this.velocity * dt;
    if (this.velocity < 0) {
      this.angle = Math.max(-25, this.angle - 5 * dt);
    } else {
      this.angle = Math.min(90, this.angle + 3 * dt);
    }
  }

  animate() {
    if (!this.alive) return;
    this.frameIndex = (this.frameIndex + 1) % birdFrames.length;
  }

  rect() {
    const frame = birdFrames[this.frameIndex];
    const halfWidth = frame.width / 2;
    const halfHeight = frame.height / 2;
    return {
      left: this.x - halfWidth,
      right: this.x + halfWidth,
      top: this.y - halfHeight,
      bottom: this.y + halfHeight,
    };
  }

  draw() {
    const frame = birdFrames[this.frameIndex];
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate((this.angle * Math.PI) / 180);
    ctx.drawImage(frame, -frame.width / 2, -frame.height / 2);
    ctx.restore();
  }
}

class Pipe {
  constructor(x, gapY) {
    this.x = x;
    this.gapY = gapY;
    this.passed = false;
  }

  topRect() {
    return {
      x: this.x,
      y: 0,
      width: PIPE_WIDTH,
      height: this.gapY - PIPE_GAP / 2,
    };
  }

  bottomRect() {
    const y = this.gapY + PIPE_GAP / 2;
    return {
      x: this.x,
      y,
      width: PIPE_WIDTH,
      height: HEIGHT - BASE_HEIGHT - y,
    };
  }

  update(dt) {
    this.x -= PIPE_SPEED * dt;
  }

  isOffscreen() {
    return this.x + PIPE_WIDTH < 0;
  }

  drawRect(rect) {
    const bodyColor = "#4cbb17";
    const shadeColor = "#389112";
    const highlightColor = "#8ce360";
    const rimColor = "#60cf2b";
    const rimHeight = 20;

    ctx.fillStyle = bodyColor;
    ctx.fillRect(rect.x, rect.y, rect.width, rect.height);

    ctx.fillStyle = shadeColor;
    ctx.fillRect(rect.x + rect.width - 14, rect.y, 14, rect.height);

    ctx.fillStyle = highlightColor;
    ctx.fillRect(rect.x + 6, rect.y, 8, rect.height);

    if (rect.y === 0) {
      ctx.fillStyle = rimColor;
      ctx.fillRect(rect.x - 6, rect.y + rect.height - rimHeight, rect.width + 12, rimHeight);
    } else {
      ctx.fillStyle = rimColor;
      ctx.fillRect(rect.x - 6, rect.y, rect.width + 12, rimHeight);
    }

    ctx.strokeStyle = shadeColor;
    ctx.lineWidth = 3;
    roundRect(rect.x, rect.y, rect.width, rect.height, 2);
  }

  draw() {
    const top = this.topRect();
    const bottom = this.bottomRect();
    this.drawRect(top);
    this.drawRect(bottom);
  }
}

class Base {
  constructor(y) {
    this.y = y;
    this.x1 = 0;
    this.x2 = WIDTH;
    this.speed = PIPE_SPEED;
  }

  update(dt) {
    this.x1 -= this.speed * dt;
    this.x2 -= this.speed * dt;
    if (this.x1 + WIDTH < 0) this.x1 = this.x2 + WIDTH;
    if (this.x2 + WIDTH < 0) this.x2 = this.x1 + WIDTH;
  }

  draw() {
    ctx.fillStyle = "#deb887";
    ctx.fillRect(this.x1, this.y, WIDTH, BASE_HEIGHT);
    ctx.fillRect(this.x2, this.y, WIDTH, BASE_HEIGHT);
    ctx.fillStyle = "#8b4513";
    ctx.fillRect(0, this.y, WIDTH, 8);
  }
}

class Cloud {
  constructor(x, y, baseRadius, speed, offsets) {
    this.x = x;
    this.y = y;
    this.baseRadius = baseRadius;
    this.speed = speed;
    this.offsets = offsets;
  }

  get width() {
    return this.baseRadius * 4.5;
  }

  update(dt) {
    this.x -= this.speed * dt;
    if (this.x < -this.width) {
      this.x = WIDTH + Math.random() * 120 + 20;
      this.y = Math.random() * 200 + 40;
    }
  }

  draw() {
    ctx.save();
    ctx.translate(this.x, this.y);
    this.offsets.forEach((offset, index) => {
      const [dx, dy, w, h] = offset;
      const alpha = Math.max(0.7, 0.9 - index * 0.05);
      ctx.fillStyle = `rgba(255,255,255,${alpha})`;
      ctx.beginPath();
      ctx.ellipse(dx, dy, w / 2, h / 2, 0, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.restore();
  }
}

let clouds = [];
let bird;
let pipes;
let base;
let score = 0;
let highScore = 0;
let gameOver = false;

function createSound(path) {
  const audio = new Audio();
  audio.src = path;
  audio.preload = "auto";
  return audio;
}

function playSound(audio) {
  if (!audio) return;
  try {
    audio.currentTime = 0;
    audio.play();
  } catch (err) {
    // Autoplay restrictions may prevent playback; ignore errors.
  }
}

function loadImage(path) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = path;
  });
}

function initializeClouds() {
  if (clouds.length) return;
  const layers = [
    { speed: 0.25, baseRadius: 56, baseY: 60 },
    { speed: 0.4, baseRadius: 48, baseY: 110 },
    { speed: 0.65, baseRadius: 36, baseY: 160 },
  ];
  layers.forEach((layer) => {
    for (let i = 0; i < 3; i += 1) {
      const radius =
        (Math.random() * layer.baseRadius * 0.3 + layer.baseRadius * 0.85) *
        CLOUD_SIZE_SCALE;
      const x = Math.random() * WIDTH;
      const y = layer.baseY - 20 + Math.random() * 60;
      const offsets = createCloudOffsets(radius);
      clouds.push(new Cloud(x, y, radius, layer.speed, offsets));
    }
  });
}

function createCloudOffsets(baseRadius) {
  const centers = [-0.75, 0, 0.75];
  return centers.map((factor, index) => {
    const dx = factor * baseRadius + (Math.random() * 16 - 8);
    const dy = Math.random() * 16 - 8;
    const width =
      baseRadius *
      (index === 1 ? Math.random() * 0.4 + 1.4 : Math.random() * 0.4 + 1.1);
    const height = baseRadius * (Math.random() * 0.25 + 0.65);
    return [dx, dy, width, height];
  });
}

function spawnPipe() {
  const margin = 70;
  const gapCenter = Math.floor(
    Math.random() * (HEIGHT - BASE_HEIGHT - margin * 2 - PIPE_GAP) +
      margin +
      PIPE_GAP / 2
  );
  return new Pipe(WIDTH, gapCenter);
}

function checkCollision(birdObj, pipeList) {
  if (birdObj.y - birdObj.radius <= 0) return true;
  if (birdObj.y + birdObj.radius >= HEIGHT - BASE_HEIGHT) return true;
  const birdRect = birdObj.rect();
  return pipeList.some((pipe) => {
    const top = pipe.topRect();
    const bottom = pipe.bottomRect();
    return rectIntersect(birdRect, top) || rectIntersect(birdRect, bottom);
  });
}

function rectIntersect(birdRect, pipeRect) {
  const pipe = {
    left: pipeRect.x,
    right: pipeRect.x + pipeRect.width,
    top: pipeRect.y,
    bottom: pipeRect.y + pipeRect.height,
  };
  return !(
    birdRect.right < pipe.left ||
    birdRect.left > pipe.right ||
    birdRect.bottom < pipe.top ||
    birdRect.top > pipe.bottom
  );
}

function drawText(text, size, x, y, options = {}) {
  const { color = "#fff", shadow = true, align = "center" } = options;
  ctx.font = `${size}px 'Fira Sans', 'Segoe UI', sans-serif`;
  ctx.textAlign = align;
  ctx.textBaseline = "middle";
  if (shadow) {
    ctx.fillStyle = "rgba(0,0,0,0.45)";
    ctx.fillText(text, x + 2, y + 2);
  }
  ctx.fillStyle = color;
  ctx.fillText(text, x, y);
}

function resetGame() {
  bird = new Bird(BIRD_X, HEIGHT / 2);
  pipes = [spawnPipe()];
  base = new Base(HEIGHT - BASE_HEIGHT);
  score = 0;
  gameOver = false;
}

function update(delta) {
  const dt = Math.min(delta, 34) / (1000 / FPS);
  if (!gameOver) {
    bird.update(dt);
    pipes.forEach((pipe) => pipe.update(dt));
    base.update(dt);

    if (pipes[pipes.length - 1].x < WIDTH - 200) {
      pipes.push(spawnPipe());
    }
    pipes = pipes.filter((pipe) => !pipe.isOffscreen());

    pipes.forEach((pipe) => {
      if (!pipe.passed && pipe.x + PIPE_WIDTH < bird.x) {
        pipe.passed = true;
        score += 1;
      }
    });

    if (checkCollision(bird, pipes)) {
      playSound(hitSound);
      bird.alive = false;
      gameOver = true;
      highScore = Math.max(highScore, score);
    }
  }

  clouds.forEach((cloud) => cloud.update(dt));

  flapTimer += delta;
  if (flapTimer >= BIRD_FLAP_INTERVAL_MS) {
    bird.animate();
    flapTimer = 0;
  }
}

function drawBackground() {
  ctx.fillStyle = BACKGROUND_COLOR;
  ctx.fillRect(0, 0, WIDTH, HEIGHT);
}

function draw() {
  drawBackground();
  clouds.forEach((cloud) => cloud.draw());
  pipes.forEach((pipe) => pipe.draw());
  base.draw();
  bird.draw();
  drawText(String(score), 48, WIDTH / 2, 80);
  drawText(`HI ${highScore}`, 24, WIDTH - 70, 40);

  if (gameOver) {
    drawText("Game Over", 42, WIDTH / 2, HEIGHT / 2 - 30);
    drawText("Press Space to Retry", 20, WIDTH / 2, HEIGHT / 2 + 10);
  }
}

function loop(timestamp) {
  if (!lastTime) lastTime = timestamp;
  const delta = timestamp - lastTime;
  lastTime = timestamp;
  update(delta);
  draw();
  requestAnimationFrame(loop);
}

function roundRect(x, y, width, height, radius) {
  ctx.beginPath();
  ctx.moveTo(x + radius, y);
  ctx.lineTo(x + width - radius, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
  ctx.lineTo(x + width, y + height - radius);
  ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
  ctx.lineTo(x + radius, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
  ctx.lineTo(x, y + radius);
  ctx.quadraticCurveTo(x, y, x + radius, y);
  ctx.closePath();
  ctx.stroke();
}

function setupInput() {
  const handleJump = (event) => {
    if (event) {
      event.preventDefault();
    }
    if (!gameOver) {
      bird.flap();
    } else {
      resetGame();
    }
  };

  window.addEventListener("keydown", (event) => {
    if (event.code === "Space" || event.code === "ArrowUp") {
      handleJump(event);
    } else if (event.code === "Escape") {
      resetGame();
    }
  });

  const clickTargets = [window, canvas];
  clickTargets.forEach((target) => {
    target.addEventListener("click", handleJump);
    target.addEventListener(
      "touchstart",
      (event) => handleJump(event),
      { passive: false }
    );
  });
}

Promise.all(birdFramePaths.map((path) => loadImage(path)))
  .then((images) => {
    birdFrames = images;
    initializeClouds();
    resetGame();
    setupInput();
    requestAnimationFrame(loop);
  })
  .catch((err) => {
    console.error("Failed to load assets", err);
    drawText("Unable to load game assets", 18, WIDTH / 2, HEIGHT / 2, {
      color: "#000",
      shadow: false,
    });
  });
