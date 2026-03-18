const scoreNode = document.getElementById('score');
const timeNode = document.getElementById('time');
const startButton = document.getElementById('start-button');
const resetButton = document.getElementById('reset-button');
const planet = document.getElementById('planet');
const board = document.querySelector('.game-board');

let score = 0;
let timeLeft = 45;
let timerId = null;
let running = false;

function randomPosition() {
  const boardRect = board.getBoundingClientRect();
  const size = planet.offsetWidth || 76;
  const padding = 24;
  const maxX = Math.max(padding, boardRect.width - size - padding);
  const maxY = Math.max(padding, boardRect.height - size - padding);

  return {
    x: Math.floor(Math.random() * maxX),
    y: Math.floor(Math.random() * maxY),
  };
}

function movePlanet() {
  const { x, y } = randomPosition();
  planet.style.left = `${x}px`;
  planet.style.top = `${y}px`;
}

function updateHud() {
  scoreNode.textContent = String(score);
  timeNode.textContent = String(timeLeft);
}

function finishGame() {
  running = false;
  clearInterval(timerId);
  timerId = null;
  startButton.textContent = '再玩一次';
}

function startGame() {
  score = 0;
  timeLeft = 45;
  running = true;
  updateHud();
  movePlanet();
  startButton.textContent = '游戏进行中';

  clearInterval(timerId);
  timerId = window.setInterval(() => {
    timeLeft -= 1;
    updateHud();

    if (timeLeft <= 0) {
      finishGame();
    }
  }, 1000);
}

planet.addEventListener('click', () => {
  if (!running) return;
  score += 1;
  updateHud();
  movePlanet();
});

startButton.addEventListener('click', () => {
  startGame();
});

resetButton.addEventListener('click', () => {
  finishGame();
  score = 0;
  timeLeft = 45;
  updateHud();
  movePlanet();
  startButton.textContent = '开始游戏';
});

window.addEventListener('resize', movePlanet);

updateHud();
movePlanet();
