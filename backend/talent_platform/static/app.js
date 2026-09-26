const dataNode = document.querySelector("#demo-data");
const data = JSON.parse(dataNode.textContent);
const jobSelect = document.querySelector("#job-select");
const searchInput = document.querySelector("#search-input");
const locationSelect = document.querySelector("#location-select");
const savedFilter = document.querySelector("#saved-filter");
const savedCount = document.querySelector("#saved-count");
const candidateList = document.querySelector("#candidate-list");
const candidateDetail = document.querySelector("#candidate-detail");
const emptyState = document.querySelector("#empty-state");
const resultsCount = document.querySelector("#results-count");
const savedCandidates = new Set();
let showingSavedOnly = false;
let selectedCandidateId = data.candidates[0]?.id ?? null;

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function activeJob() {
  return data.jobs.find((job) => job.id === jobSelect.value) ?? data.jobs[0];
}

function evidenceFor(candidate, skill) {
  return candidate.evidence.find((item) => item.skill.toLowerCase() === skill.toLowerCase());
}

function coverageFor(candidate, job) {
  return job.requirements.filter((skill) => evidenceFor(candidate, skill)).length;
}

function fillJobOptions() {
  for (const job of data.jobs) {
    const option = makeElement("option", "", job.title);
    option.value = job.id;
    jobSelect.append(option);
  }
  jobSelect.value = data.default_job;
}

function renderJob() {
  const job = activeJob();
  document.querySelector("#role-title").textContent = job.title;
  document.querySelector("#role-meta").replaceChildren(
    document.createTextNode(`${job.team} / ${job.type} / ${job.location}`),
  );
  const chips = document.querySelector("#requirement-chips");
  chips.replaceChildren();
  for (const requirement of job.requirements) {
    chips.append(makeElement("span", "requirement-chip", requirement));
  }
}

function candidateMatchesFilters(candidate) {
  const search = searchInput.value.trim().toLowerCase();
  const searchableText = [
    candidate.name,
    candidate.headline,
    candidate.location,
    ...candidate.evidence.map((item) => item.skill),
  ].join(" ").toLowerCase();
  const locationMatches = locationSelect.value === "all"
    || candidate.location_group === locationSelect.value;
  const savedMatches = !showingSavedOnly || savedCandidates.has(candidate.id);
  return searchableText.includes(search) && locationMatches && savedMatches;
}

function createCandidateRow(candidate, job) {
  const covered = coverageFor(candidate, job);
  const total = job.requirements.length;
  const row = makeElement("button", "candidate-row");
  row.type = "button";
  row.dataset.candidateId = candidate.id;
  row.setAttribute("aria-pressed", String(candidate.id === selectedCandidateId));

  row.append(makeElement("span", "avatar", candidate.initials));
  const primary = makeElement("span", "candidate-primary");
  primary.append(makeElement("span", "candidate-name", candidate.name));
  primary.append(makeElement("span", "candidate-headline", candidate.headline));
  primary.append(makeElement("span", "candidate-location", `${candidate.location} / ${candidate.availability}`));
  row.append(primary);

  const coverageClass = covered === total ? "coverage-pill complete" : "coverage-pill partial";
  row.append(makeElement("span", coverageClass, `${covered}/${total}`));
  return row;
}

function visibleCandidates() {
  return data.candidates.filter(candidateMatchesFilters);
}

function renderCandidateList(candidates, job) {
  candidateList.replaceChildren();
  resultsCount.textContent = `${candidates.length} ${candidates.length === 1 ? "candidate" : "candidates"}`;
  emptyState.hidden = candidates.length > 0;
  candidateList.hidden = candidates.length === 0;
  for (const candidate of candidates) {
    candidateList.append(createCandidateRow(candidate, job));
  }
}

function createRequirementRow(skill, candidate) {
  const item = evidenceFor(candidate, skill);
  const row = makeElement("div", "requirement-row");
  row.append(makeElement("div", "requirement-skill", skill));
  const result = makeElement("div", "requirement-result");
  if (!item) {
    result.append(makeElement("span", "evidence-state missing", "NO EVIDENCE LISTED"));
    result.append(makeElement("span", "evidence-title", "No evidence in this sample profile."));
  } else {
    result.append(makeElement("span", "evidence-state present", "EVIDENCE FOUND"));
    result.append(makeElement("span", "evidence-title", item.title));
    result.append(makeElement(
      "span",
      "evidence-meta",
      `${item.kind} / ${item.verification} / ${item.detail} / ${item.observed}`,
    ));
  }
  row.append(result);
  return row;
}

function renderCandidateDetail(candidate, job) {
  candidateDetail.replaceChildren();
  if (!candidate) {
    const message = makeElement("div", "no-selection");
    message.append(makeElement("p", "", "No candidate matches the current filters."));
    candidateDetail.append(message);
    return;
  }

  const header = makeElement("div", "detail-header");
  const identity = makeElement("div", "detail-identity");
  identity.append(makeElement("span", "avatar detail-avatar", candidate.initials));
  const identityText = makeElement("div", "");
  identityText.append(makeElement("h2", "detail-name", candidate.name));
  identityText.append(makeElement("p", "detail-headline", candidate.headline));
  identityText.append(makeElement("div", "detail-location", `${candidate.location} / ${candidate.availability}`));
  identity.append(identityText);

  const saveButton = makeElement("button", "save-button", savedCandidates.has(candidate.id) ? "Saved" : "Save candidate");
  saveButton.type = "button";
  saveButton.setAttribute("aria-pressed", String(savedCandidates.has(candidate.id)));
  saveButton.addEventListener("click", () => {
    if (savedCandidates.has(candidate.id)) savedCandidates.delete(candidate.id);
    else savedCandidates.add(candidate.id);
    updateView();
  });
  header.append(identity, saveButton);
  candidateDetail.append(header);

  const covered = coverageFor(candidate, job);
  const summary = makeElement("div", "coverage-summary");
  const summaryText = makeElement("div", "");
  summaryText.append(makeElement("strong", "", `${covered} of ${job.requirements.length} requirements have evidence`));
  summaryText.append(makeElement("span", "", `For ${job.title}; evidence coverage is not a skill score.`));
  summary.append(summaryText, makeElement("span", "coverage-tag", "ROLE-SPECIFIC"));
  candidateDetail.append(summary);

  const heading = makeElement("div", "section-heading");
  heading.append(makeElement("h3", "", "Requirement evidence"));
  heading.append(makeElement("span", "", "SOURCE / STATUS / RECENCY"));
  candidateDetail.append(heading);

  const requirements = makeElement("div", "requirement-list");
  for (const skill of job.requirements) requirements.append(createRequirementRow(skill, candidate));
  candidateDetail.append(requirements);

  const note = makeElement("div", "detail-footnote");
  note.append(makeElement("span", "detail-footnote-mark", "i"));
  const noteText = makeElement("span", "");
  noteText.append(makeElement("strong", "", "Sample profile. "));
  noteText.append(document.createTextNode("Evidence and assessment results are fictional and are not connected to external accounts."));
  note.append(noteText);
  candidateDetail.append(note);
}

function updateView() {
  const job = activeJob();
  renderJob();
  const candidates = visibleCandidates();
  if (!candidates.some((candidate) => candidate.id === selectedCandidateId)) {
    selectedCandidateId = candidates[0]?.id ?? null;
  }
  renderCandidateList(candidates, job);
  renderCandidateDetail(
    candidates.find((candidate) => candidate.id === selectedCandidateId) ?? null,
    job,
  );
  savedCount.textContent = String(savedCandidates.size);
  savedFilter.setAttribute("aria-pressed", String(showingSavedOnly));
}

fillJobOptions();
updateView();

jobSelect.addEventListener("change", updateView);
searchInput.addEventListener("input", updateView);
locationSelect.addEventListener("change", updateView);
savedFilter.addEventListener("click", () => {
  showingSavedOnly = !showingSavedOnly;
  updateView();
});
candidateList.addEventListener("click", (event) => {
  const row = event.target.closest("[data-candidate-id]");
  if (!row) return;
  selectedCandidateId = row.dataset.candidateId;
  updateView();
});
