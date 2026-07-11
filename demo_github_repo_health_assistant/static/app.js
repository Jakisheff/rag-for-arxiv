const ownerInput = document.querySelector("#ownerInput");
const repoInput = document.querySelector("#repoInput");
const rawButton = document.querySelector("#rawButton");
const analyzeButton = document.querySelector("#analyzeButton");
const reportButton = document.querySelector("#reportButton");
const statusBox = document.querySelector("#status");
const jsonOutput = document.querySelector("#jsonOutput");
const reportOutput = document.querySelector("#reportOutput");

const scoreValue = document.querySelector("#scoreValue");
const gradeValue = document.querySelector("#gradeValue");
const starsValue = document.querySelector("#starsValue");
const forksValue = document.querySelector("#forksValue");
const issuesValue = document.querySelector("#issuesValue");
const licenseValue = document.querySelector("#licenseValue");
const signalsList = document.querySelector("#signalsList");
const risksList = document.querySelector("#risksList");

const buttons = [rawButton, analyzeButton, reportButton];

rawButton.addEventListener("click", () => runAction("Fetching raw GitHub data...", fetchRaw));
analyzeButton.addEventListener("click", () => runAction("Analyzing repository...", fetchAnalysis));
reportButton.addEventListener("click", () => runAction("Generating LLM report...", fetchReport));

async function runAction(loadingMessage, action) {
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
  const data = await getJson(`/repo/raw${queryString()}`);
  renderRaw(data);
  setStatus("Raw data loaded.");
}

async function fetchAnalysis() {
  const data = await getJson(`/repo/analyze${queryString()}`);
  renderAnalysis(data);
  setStatus("Repository analysis complete.");
}

async function fetchReport() {
  const data = await getJson(`/repo/llm-report${queryString()}`);
  scoreValue.textContent = data.health_score;
  gradeValue.textContent = data.grade;
  reportOutput.textContent = data.llm_report;
  renderJson(data);
  setStatus("LLM report generated.");
}

function queryString() {
  const params = new URLSearchParams({
    owner: ownerInput.value.trim(),
    repo: repoInput.value.trim(),
  });
  return `?${params.toString()}`;
}

async function getJson(url) {
  const response = await fetch(url);
  const contentType = response.headers.get("content-type") || "";
  const body = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const detail = typeof body === "object" ? body.detail || JSON.stringify(body) : body;
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return body;
}

function renderRaw(raw) {
  starsValue.textContent = formatNumber(raw.stars);
  forksValue.textContent = formatNumber(raw.forks);
  issuesValue.textContent = formatNumber(raw.open_issues);
  licenseValue.textContent = raw.license || "Missing";
  renderJson(raw);
}

function renderAnalysis(analysis) {
  renderRaw(analysis.raw);
  scoreValue.textContent = analysis.health_score;
  gradeValue.textContent = analysis.grade;
  renderList(signalsList, analysis.signals);
  renderList(risksList, analysis.risks);
  renderJson(analysis);
}

function renderList(element, items) {
  element.innerHTML = "";
  for (const item of items || []) {
    const li = document.createElement("li");
    li.textContent = item;
    element.appendChild(li);
  }
}

function renderJson(data) {
  jsonOutput.textContent = JSON.stringify(data, null, 2);
}

function setStatus(message, isError = false) {
  statusBox.textContent = message;
  statusBox.classList.toggle("error", isError);
}

function setLoading(isLoading) {
  for (const button of buttons) {
    button.disabled = isLoading;
  }
}

function formatNumber(value) {
  return new Intl.NumberFormat("en").format(value || 0);
}
