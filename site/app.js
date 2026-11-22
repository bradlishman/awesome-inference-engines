import { evaluate, rankedCandidates, searchProjects } from "./engine-logic.mjs";

const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (char) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
      })[char],
  );
const linksafe = (url) => (/^https:\/\//.test(url) ? esc(url) : "#");
const statusLabel = {
  documented: "Documented match",
  partial: "Check conditions",
  unknown: "Not yet evidenced",
};

let catalogue = null;
let directoryLimit = 12;
const selected = new Set();

function announce(message) {
  $("announcer").textContent = message;
}

function filters() {
  return {
    hardware: $("hardware").value,
    os: $("os").value,
    model: $("model").value.trim(),
  };
}

function saveFilters() {
  const url = new URL(location.href);
  for (const [key, value] of Object.entries(filters())) {
    if (!value || value === "any") url.searchParams.delete(key);
    else url.searchParams.set(key, value);
  }
  history.replaceState(null, "", url);
}

function restoreFilters() {
  const params = new URL(location.href).searchParams;
  for (const id of ["hardware", "os"]) {
    const value = params.get(id);
    if (value && [...$(id).options].some((option) => option.value === value))
      $(id).value = value;
  }
  $("model").value = params.get("model") || "";
}

function compareButton(item) {
  if (item.kind !== "project") return "";
  const active = selected.has(item.id);
  return `<button type="button" class="compare-toggle" data-compare="${esc(item.id)}" aria-pressed="${active}">${active ? "Selected" : "Compare"}</button>`;
}

function sourceLink(item) {
  const source = item.compatibility?.evidence?.[0];
  return `<a href="${linksafe(source?.url || item.url)}" target="_blank" rel="noopener noreferrer">${source ? "Primary evidence" : "Repository"}</a>`;
}

function finderCard(item, evaluation) {
  const info = item.compatibility;
  const statuses = {
    documented: "documented",
    partial: "partial",
    unknown: "unknown",
  };
  return `<article class="engine-card">
    <div class="card-head"><div><h4>${esc(item.name)}</h4><div class="card-sub">${esc(item.category)}</div></div>
      <span class="status ${statuses[evaluation.status]}">${statusLabel[evaluation.status]}</span></div>
    <p class="summary">${esc(item.description)}</p>
    <div class="fact-row"><span>Hardware</span><span>${esc(info.target)}</span></div>
    <div class="fact-row"><span>Models</span><span>${esc(info.models)}</span></div>
    <div class="fact-row"><span>Execution</span><span>${esc(info.execution)}</span></div>
    <div class="fact-row"><span>Assessment</span><span>${esc(evaluation.reasons[0] || "Check upstream for exact artifacts and settings")}</span></div>
    <div class="card-foot">${sourceLink(item)}${compareButton(item)}</div>
  </article>`;
}

function renderFinder() {
  if (!catalogue) return;
  const matches = rankedCandidates(catalogue.projects, filters());
  const confirmed = matches.filter(
    ({ evaluation }) => evaluation.status === "documented",
  ).length;
  const partial = matches.filter(
    ({ evaluation }) => evaluation.status === "partial",
  ).length;
  const visible = $("documented-only").checked
    ? matches.filter(({ evaluation }) => evaluation.status === "documented")
    : matches;
  $("finder-summary").textContent =
    `${confirmed} documented · ${partial} conditional · ${matches.length - confirmed - partial} require further evidence`;
  $("finder-results").innerHTML = visible.length
    ? visible
        .map(({ item, evaluation }) => finderCard(item, evaluation))
        .join("")
    : '<div class="empty-state"><h4>No documented match yet</h4><p>Try another model or hardware family, or untick “Documented matches only”.</p></div>';
}

function directoryCard(item) {
  return `<article class="directory-card">
    <h4>${esc(item.name)}</h4><p class="directory-category">${esc(item.category)}</p>
    <p>${esc(item.description)}</p>
    <div class="card-foot">${sourceLink(item)}${compareButton(item)}</div>
  </article>`;
}

function renderDirectory() {
  if (!catalogue) return;
  const matches = searchProjects(
    catalogue.projects,
    $("search").value,
    $("category").value,
  ).sort((a, b) => a.name.localeCompare(b.name));
  const visible = matches.slice(0, directoryLimit);
  $("directory-count").textContent =
    `${matches.length} project${matches.length === 1 ? "" : "s"} and resources found`;
  $("directory-results").innerHTML = visible.length
    ? visible.map(directoryCard).join("")
    : '<div class="empty-state"><h4>Nothing matched that search</h4><p>Try a model family, engine name, or capability.</p></div>';
  $("show-more").hidden = visible.length >= matches.length;
  $("show-more").textContent =
    `Show more projects (${matches.length - visible.length} remaining)`;
}

function updateCompare() {
  $("compare-dock").hidden = selected.size === 0;
  $("compare-count").textContent =
    `${selected.size} engine${selected.size === 1 ? "" : "s"} selected`;
  $("open-compare").disabled = selected.size !== 2;
  for (const button of document.querySelectorAll("[data-compare]")) {
    const active = selected.has(button.dataset.compare);
    button.setAttribute("aria-pressed", String(active));
    button.textContent = active ? "Selected" : "Compare";
  }
}

function toggleCompare(id) {
  if (selected.has(id)) selected.delete(id);
  else {
    if (selected.size >= 2) {
      announce("Two engines are already selected. Remove one first.");
      return;
    }
    selected.add(id);
  }
  updateCompare();
}

function renderComparison() {
  const items = [...selected]
    .map((id) => catalogue.projects.find((item) => item.id === id))
    .filter(Boolean);
  if (items.length !== 2) return;
  const rows = [
    ["Category", (item) => item.category],
    ["Purpose", (item) => item.description],
    ["Hardware target", (item) => item.compatibility?.target],
    ["Model examples", (item) => item.compatibility?.models],
    ["Execution approach", (item) => item.compatibility?.execution],
    ["Interface", (item) => item.compatibility?.interface],
    [
      "Evidence status",
      (item) =>
        item.compatibility ? "Upstream documented" : "No detailed profile yet",
    ],
  ];
  const table = `<table class="comparison-table"><thead><tr><th>Dimension</th>${items.map((item) => `<th>${esc(item.name)}</th>`).join("")}</tr></thead><tbody>
    ${rows.map(([label, value]) => `<tr><th scope="row">${esc(label)}</th>${items.map((item) => `<td>${esc(value(item) || "Not recorded")}</td>`).join("")}</tr>`).join("")}
    <tr><th scope="row">Sources</th>${items.map((item) => `<td>${sourceLink(item)}</td>`).join("")}</tr>
  </tbody></table>`;
  $("comparison-content").innerHTML = table;
  $("compare-dialog").showModal();
}

function start(data) {
  catalogue = data;
  $("stat-projects").textContent = data.counts.all;
  $("stat-sourced").textContent = data.counts.documented;
  const categories = [...new Set(data.projects.map((item) => item.category))];
  $("category").insertAdjacentHTML(
    "beforeend",
    categories
      .map(
        (category) =>
          `<option value="${esc(category)}">${esc(category)}</option>`,
      )
      .join(""),
  );
  restoreFilters();
  renderFinder();
  renderDirectory();
  updateCompare();

  for (const id of ["hardware", "os"])
    $(id).addEventListener("change", () => {
      saveFilters();
      renderFinder();
    });
  $("model").addEventListener("input", () => {
    saveFilters();
    renderFinder();
  });
  $("documented-only").addEventListener("change", renderFinder);
  $("clear-filters").addEventListener("click", () => {
    $("hardware").value = "any";
    $("os").value = "any";
    $("model").value = "";
    $("documented-only").checked = false;
    saveFilters();
    renderFinder();
  });
  $("share-filters").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(location.href);
      announce("Filter link copied to clipboard.");
    } catch {
      announce(
        "Clipboard unavailable. Copy the link from your browser address bar.",
      );
    }
  });
  $("search").addEventListener("input", () => {
    directoryLimit = 12;
    renderDirectory();
  });
  $("category").addEventListener("change", () => {
    directoryLimit = 12;
    renderDirectory();
  });
  $("show-more").addEventListener("click", () => {
    directoryLimit += 12;
    renderDirectory();
  });
  $("clear-compare").addEventListener("click", () => {
    selected.clear();
    updateCompare();
  });
  $("open-compare").addEventListener("click", renderComparison);
  $("close-compare").addEventListener("click", () =>
    $("compare-dialog").close(),
  );
  $("compare-dialog").addEventListener("click", (event) => {
    if (event.target === $("compare-dialog")) $("compare-dialog").close();
  });
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-compare]");
    if (button) toggleCompare(button.dataset.compare);
  });
  window.addEventListener("popstate", () => {
    restoreFilters();
    renderFinder();
  });
}

fetch("./data.json")
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then(start)
  .catch((error) => {
    $("finder-summary").textContent = "Unable to load the catalogue";
    $("finder-results").innerHTML =
      '<div class="empty-state"><h4>Catalogue temporarily unavailable</h4><p>Reload the page or browse the canonical GitHub list.</p></div>';
    $("directory-count").textContent = "Catalogue unavailable";
    console.error("Catalogue load failed:", error);
  });
