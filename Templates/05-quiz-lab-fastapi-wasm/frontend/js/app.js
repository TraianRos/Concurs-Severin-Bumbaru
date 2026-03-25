const statusText = document.querySelector("#status-text");
const quizList = document.querySelector("#quiz-list");
const quizDetail = document.querySelector("#quiz-detail");
const leaderboardList = document.querySelector("#leaderboard-list");

async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Unexpected error" }));
    throw new Error(payload.detail || "Unexpected error");
  }

  return response.json();
}

// WASM is the canonical scoring direction, but the fallback keeps the demo usable
// even when the binary has not been built on the current machine.
function calculateLocalScore(questions, answers) {
  const correctness = questions.map((question) => {
    const actual = String(answers[question.id] || "").trim().toLowerCase();
    return actual === String(question.correct_answer).trim().toLowerCase() ? 1 : 0;
  });
  const points = questions.map((question) => question.points);

  if (window.calculateScoreFromWasm) {
    return window.calculateScoreFromWasm(correctness, points);
  }

  return correctness.reduce((total, value, index) => total + value * points[index], 0);
}

async function loadLeaderboard() {
  const rows = await request("/api/leaderboard");
  leaderboardList.innerHTML = "";

  rows.forEach((row) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = row.player_name;

    const meta = document.createElement("span");
    meta.textContent = `${row.quiz_title} - ${row.score} points`;

    item.appendChild(title);
    item.appendChild(meta);
    leaderboardList.appendChild(item);
  });
}

function renderQuizList(quizzes) {
  quizList.innerHTML = "";

  quizzes.forEach((quiz) => {
    const block = document.createElement("article");
    block.className = "quiz-tile";

    const title = document.createElement("strong");
    title.textContent = quiz.title;

    const topic = document.createElement("span");
    topic.className = "muted-text";
    topic.textContent = quiz.topic;

    const button = document.createElement("button");
    button.type = "button";
    button.textContent = "Open quiz";
    button.addEventListener("click", () => loadQuiz(quiz.id));

    block.appendChild(title);
    block.appendChild(topic);
    block.appendChild(button);
    quizList.appendChild(block);
  });
}

async function loadQuiz(quizId) {
  const quiz = await request(`/api/quizzes/${quizId}`);
  statusText.textContent = `Loaded ${quiz.title}.`;
  quizDetail.innerHTML = "";

  const form = document.createElement("form");
  form.className = "quiz-form";
  form.id = "quiz-form";

  const heading = document.createElement("h2");
  heading.textContent = quiz.title;

  const topic = document.createElement("p");
  topic.className = "muted-text";
  topic.textContent = quiz.topic;

  const playerLabel = document.createElement("label");
  const playerLabelText = document.createElement("span");
  playerLabelText.textContent = "Player name";
  const playerInput = document.createElement("input");
  playerInput.type = "text";
  playerInput.name = "player-name";
  playerInput.required = true;
  playerLabel.appendChild(playerLabelText);
  playerLabel.appendChild(playerInput);

  form.appendChild(heading);
  form.appendChild(topic);
  form.appendChild(playerLabel);

  quiz.questions.forEach((question) => {
    const label = document.createElement("label");
    const text = document.createElement("span");
    text.textContent = `${question.prompt} (${question.points}p)`;

    const input = document.createElement("input");
    input.type = "text";
    input.name = `question-${question.id}`;
    input.required = true;

    label.appendChild(text);
    label.appendChild(input);
    form.appendChild(label);
  });

  const submitButton = document.createElement("button");
  submitButton.type = "submit";
  submitButton.textContent = "Submit answers";

  const localScoreText = document.createElement("p");
  localScoreText.id = "local-score";
  localScoreText.className = "muted-text";

  form.appendChild(submitButton);
  form.appendChild(localScoreText);
  quizDetail.appendChild(form);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const answers = {};
    const payloadAnswers = quiz.questions.map((question) => {
      const answer = form.querySelector(`[name="question-${question.id}"]`).value;
      answers[question.id] = answer;
      return { questionId: question.id, answer };
    });

    const localScore = calculateLocalScore(quiz.questions, answers);
    localScoreText.textContent = `Local score preview: ${localScore} points`;

    const payload = {
      quizId: quiz.id,
      playerName: form.querySelector('[name="player-name"]').value,
      answers: payloadAnswers,
    };

    const result = await request("/api/submissions", {
      method: "POST",
      body: JSON.stringify(payload),
    });

    statusText.textContent = `Server saved ${result.score} points for ${result.submission.player_name}.`;
    await loadLeaderboard();
  });
}

async function bootstrap() {
  try {
    const quizzes = await request("/api/quizzes");
    renderQuizList(quizzes);
    await loadLeaderboard();
    statusText.textContent = "QuizLab ready.";
  } catch (error) {
    statusText.textContent = error.message;
  }
}

bootstrap();
