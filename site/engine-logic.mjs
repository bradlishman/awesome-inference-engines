/** Conservative discovery helpers. A keyword in documentation is evidence of a claim, not a tested configuration. */

const HARDWARE = {
  any: null,
  blackwell: /blackwell|sm.?120|rtx\s*50|5090/i,
  nvidia: /nvidia|cuda|rtx/i,
  apple: /apple silicon|macos|metal|mlx/i,
  amd: /amd|rocm|rdna/i,
  strix: /strix halo|ryzen ai max/i,
  hybrid: /cpu|host.ram|heterogeneous|ram|ssd/i,
};

function normalize(value) {
  return String(value || "")
    .toLocaleLowerCase()
    .replace(/[^a-z0-9]+/g, "");
}

function operatingSystems(target) {
  const systems = [];
  if (/linux/i.test(target)) systems.push("linux");
  if (/windows/i.test(target)) systems.push("windows");
  if (/macos|apple silicon/i.test(target)) systems.push("macos");
  return systems;
}

export function evaluate(engine, filters = {}) {
  const info = engine.compatibility;
  if (!info)
    return {
      status: "unknown",
      reasons: ["No detailed compatibility record yet"],
    };
  const hardware = filters.hardware || "any";
  const os = filters.os || "any";
  const model = (filters.model || "").trim();
  const reasons = [];
  let unknown = false;
  let partial = false;

  if (hardware !== "any") {
    const pattern = HARDWARE[hardware];
    const targetText =
      hardware === "hybrid" ? `${info.target} ${info.execution}` : info.target;
    if (!pattern?.test(targetText)) {
      unknown = true;
      reasons.push("Selected hardware is not documented for this engine");
    } else {
      reasons.push(
        "Hardware family appears in the upstream target description",
      );
    }
  }
  if (os !== "any") {
    const supported = operatingSystems(info.target);
    if (!supported.length) {
      partial = true;
      reasons.push("Operating system is not specified in this summary");
    } else if (!supported.includes(os)) {
      unknown = true;
      reasons.push(
        "Selected operating system is not documented in this target",
      );
    } else {
      reasons.push("Operating system appears in the documented target");
    }
  }
  if (model) {
    if (!normalize(info.models).includes(normalize(model))) {
      unknown = true;
      reasons.push("Model search term is not in the documented examples");
    } else {
      reasons.push(
        "Model name appears in documented examples; exact checkpoint still matters",
      );
    }
  }
  return {
    status: unknown ? "unknown" : partial ? "partial" : "documented",
    reasons,
  };
}

export function searchProjects(projects, query, category = "all") {
  const needle = (query || "").trim().toLocaleLowerCase();
  return projects.filter((item) => {
    if (category !== "all" && item.category !== category) return false;
    if (!needle) return true;
    const detail = item.compatibility;
    return [
      item.name,
      item.description,
      item.category,
      detail?.target,
      detail?.models,
      detail?.execution,
      detail?.interface,
    ].some((value) =>
      String(value || "")
        .toLocaleLowerCase()
        .includes(needle),
    );
  });
}

export function rankedCandidates(projects, filters) {
  const order = { documented: 0, partial: 1, unknown: 2 };
  return projects
    .filter((item) => item.kind === "project" && item.compatibility)
    .map((item) => ({ item, evaluation: evaluate(item, filters) }))
    .sort(
      (a, b) =>
        order[a.evaluation.status] - order[b.evaluation.status] ||
        a.item.name.localeCompare(b.item.name),
    );
}
