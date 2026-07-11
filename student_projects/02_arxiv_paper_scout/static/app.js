// ГЛАВНАЯ ЛОГИКА ФАЙЛА:
// Vanilla JS UI без фреймворков и сборки. Три кнопки вызывают три backend
// endpoint'а (/papers/raw, /papers/analyze, /papers/llm-report) через fetch().
// Полученные данные рендерятся в DOM руками (без innerHTML для пользовательских
// данных — только textContent, чтобы избежать XSS). Список статей хранится в
// currentPapers и пересортировывается на клиенте при смене select#sortSelect
// (Relevance / Newest first / Oldest first) без повторного запроса к серверу.

const queryInput = document.querySelector("#queryInput");
const maxResultsInput = document.querySelector("#maxResultsInput");
const rawButton = document.querySelector("#rawButton");
const analyzeButton = document.querySelector("#analyzeButton");
const reportButton = document.querySelector("#reportButton");
const statusBox = document.querySelector("#status");
const jsonOutput = document.querySelector("#jsonOutput");
const reportOutput = document.querySelector("#reportOutput");

const countValue = document.querySelector("#countValue");
const averageValue = document.querySelector("#averageValue");
const topScoreValue = document.querySelector("#topScoreValue");
const newestValue = document.querySelector("#newestValue");
const keywordsBox = document.querySelector("#keywordsBox");
const signalsList = document.querySelector("#signalsList");
const risksList = document.querySelector("#risksList");
const papersBox = document.querySelector("#papersBox");
const sortSelect = document.querySelector("#sortSelect");

const buttons = [rawButton, analyzeButton, reportButton];

// Последний загруженный список статей (в исходном порядке от сервера).
// Храним его отдельно, чтобы сортировка могла перерисовывать список без
// повторного запроса к API.
let currentPapers = [];

rawButton.addEventListener("click", () => runAction("Fetching raw arXiv papers...", fetchRaw));
analyzeButton.addEventListener("click", () => runAction("Analyzing relevance...", fetchAnalysis));
reportButton.addEventListener("click", () => runAction("Generating LLM report...", fetchReport));
sortSelect.addEventListener("change", () => renderPapers(currentPapers));

async function runAction(loadingMessage, action) {
  // Общая обертка для всех трех кнопок: блокирует кнопки на время запроса,
  // показывает статус загрузки и ловит ошибки в единый error-статус.
  setLoading(true);
  setStatus(loadingMessage);

  try {
    await action();
  } catch (error) {
    setStatus(error.message || "Request failed.", true);
  } finally {
    setLoading(false);
  }
}

async function fetchRaw() {
  // /papers/raw — сырые данные без score. Оборачиваем каждую статью в
  // { paper } (без relevance_score), чтобы renderPapers понимал оба формата.
  const data = await getJson(`/papers/raw${queryString()}`);
  countValue.textContent = data.returned;
  newestValue.textContent = newestDate(data.papers);
  renderPapers(data.papers.map((paper) => ({ paper })));
  renderJson(data);
  setStatus(`Loaded ${data.returned} of ${data.total_results} matching papers.`);
}

async function fetchAnalysis() {
  // /papers/analyze — статьи уже со score, keywords, signals и risks.
  const data = await getJson(`/papers/analyze${queryString()}`);
  renderAnalysis(data);
  setStatus("Relevance analysis complete.");
}

async function fetchReport() {
  // /papers/llm-report — текстовый отчет от LLM поверх готового анализа.
  const data = await getJson(`/papers/llm-report${queryString()}`);
  countValue.textContent = data.paper_count;
  averageValue.textContent = data.average_relevance;
  reportOutput.textContent = data.llm_report;
  renderJson(data);
  setStatus("LLM report generated.");
}

function queryString() {
  // Собирает query-параметры из полей ввода для всех трех endpoint'ов.
  const params = new URLSearchParams({
    query: queryInput.value.trim(),
    max_results: maxResultsInput.value || "10",
  });
  return `?${params.toString()}`;
}

async function getJson(url) {
  // Общий helper для запросов: если backend вернул ошибку (4xx/5xx),
  // достает detail из JSON-тела и бросает Error с понятным сообщением.
  const response = await fetch(url);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof body === "object" ? body.detail || JSON.stringify(body) : body;
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return body;
}

function renderAnalysis(analysis) {
  // Заполняет карточки метрик и все секции (keywords/signals/risks/papers)
  // данными из ответа /papers/analyze.
  countValue.textContent = analysis.paper_count;
  averageValue.textContent = analysis.average_relevance;
  // papers уже отсортированы backend'ом по relevance_score, поэтому [0] — лучший.
  topScoreValue.textContent = analysis.papers.length ? analysis.papers[0].relevance_score : "-";
  newestValue.textContent = newestDate(analysis.papers.map((item) => item.paper));
  renderKeywords(analysis.top_keywords);
  renderList(signalsList, analysis.signals);
  renderList(risksList, analysis.risks);
  renderPapers(analysis.papers);
  renderJson(analysis);
}

function renderPapers(items) {
  // Рисует список карточек статей. items — массив вида { paper, relevance_score? }.
  // Сохраняем items как currentPapers, чтобы sortSelect мог перерисовать список
  // без повторного fetch.
  currentPapers = items;
  papersBox.innerHTML = "";

  if (!items.length) {
    papersBox.textContent = "No papers found for this query.";
    return;
  }

  for (const item of sortPapers(items)) {
    const paper = item.paper;
    const article = document.createElement("article");
    article.className = "paper";

    const head = document.createElement("div");
    head.className = "paper-head";

    // Заголовок статьи — кликабельная ссылка на страницу arXiv.
    const title = document.createElement("h3");
    title.className = "paper-title";
    const link = document.createElement("a");
    link.href = paper.link;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = paper.title;
    title.appendChild(link);
    head.appendChild(title);

    // relevance_score есть только у статей из /papers/analyze и /papers/llm-report,
    // у "сырых" статей из /papers/raw его нет — бейдж просто не рисуется.
    if (typeof item.relevance_score === "number") {
      const score = document.createElement("span");
      score.className = "paper-score";
      score.textContent = `${item.relevance_score}/100`;
      head.appendChild(score);
    }

    const meta = document.createElement("p");
    meta.className = "paper-meta";
    meta.textContent = [
      formatAuthors(paper.authors),
      formatDate(paper.published),
      paper.primary_category || paper.categories[0] || "",
    ]
      .filter(Boolean)
      .join(" · ");

    const summary = document.createElement("p");
    summary.className = "paper-summary";
    summary.textContent = truncate(paper.summary, 300);

    article.append(head, meta, summary);
    papersBox.appendChild(article);
  }
}

function sortPapers(items) {
  // Клиентская сортировка списка статей без обращения к серверу:
  //   relevance — оставляем порядок как есть (уже отсортирован backend'ом по score);
  //   newest/oldest — сортируем по ISO-дате published (лексикографическое
  //   сравнение работает, т.к. формат даты "YYYY-MM-DD..." сортируется как строка).
  const mode = sortSelect.value;
  if (mode === "relevance") return items;

  const sorted = [...items].sort((a, b) => {
    const dateA = a.paper.published || "";
    const dateB = b.paper.published || "";
    return dateA.localeCompare(dateB);
  });

  return mode === "newest" ? sorted.reverse() : sorted;
}

function renderKeywords(keywords) {
  keywordsBox.innerHTML = "";
  for (const keyword of keywords || []) {
    const chip = document.createElement("span");
    chip.className = "keyword";
    chip.textContent = keyword;
    keywordsBox.appendChild(chip);
  }
}

function renderList(element, items) {
  // Общая функция для рендера <ul> списков (signals, risks).
  element.innerHTML = "";
  for (const item of items || []) {
    const li = document.createElement("li");
    li.textContent = item;
    element.appendChild(li);
  }
}

function renderJson(data) {
  // Показывает сырой JSON ответа в блоке "Raw JSON" для отладки/учебных целей.
  jsonOutput.textContent = JSON.stringify(data, null, 2);
}

function setStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
}

function setLoading(isLoading) {
  // Блокирует все три кнопки во время запроса, чтобы нельзя было
  // одновременно нажать несколько (loading state).
  for (const button of buttons) {
    button.disabled = isLoading;
  }
}

function newestDate(papers) {
  // Ищет самую позднюю дату публикации среди статей для карточки "Newest paper".
  const dates = (papers || []).map((paper) => paper.published).filter(Boolean).sort();
  return dates.length ? formatDate(dates[dates.length - 1]) : "-";
}

function formatDate(value) {
  // Обрезаем ISO-строку до "YYYY-MM-DD", отбрасывая время.
  if (!value) return "";
  return value.slice(0, 10);
}

function formatAuthors(authors) {
  // Показываем максимум 3 авторов, остальных сворачиваем в "+N more".
  if (!authors || !authors.length) return "Unknown authors";
  if (authors.length <= 3) return authors.join(", ");
  return `${authors.slice(0, 3).join(", ")} +${authors.length - 3} more`;
}

function truncate(text, limit) {
  if (!text) return "";
  return text.length > limit ? `${text.slice(0, limit).trimEnd()}...` : text;
}
