import assert from "node:assert/strict";
import test from "node:test";
import { evaluate, rankedCandidates, searchProjects } from "./engine-logic.mjs";

const basalt = {
  name: "Basalt",
  kind: "project",
  category: "Specialized",
  compatibility: {
    target: "Linux/Windows x64, NVIDIA Blackwell (sm_120)",
    models: "Qwen3.8-Flash-Next, DeepSeek-V4.1-Flash",
    execution: "RAM-resident experts",
    interface: "OpenAI",
    evidence: [{ url: "https://example.com" }],
  },
};
const kapitsa = {
  name: "Kapitsa",
  kind: "project",
  category: "Apple",
  compatibility: {
    target: "Apple Silicon M1+, macOS 14+",
    models: "Qwen",
    execution: "native Metal",
    interface: "OpenAI",
  },
};

test("matched source examples are documented, not independently verified", () => {
  const result = evaluate(basalt, {
    hardware: "blackwell",
    os: "linux",
    model: "Qwen3.8-Flash-Next",
  });
  assert.equal(result.status, "documented");
  assert.ok(
    result.reasons.some((reason) => reason.includes("exact checkpoint")),
  );
});

test("absence of source evidence is not translated into incompatibility", () => {
  const result = evaluate(basalt, {
    hardware: "apple",
    os: "macos",
    model: "Gemma 4",
  });
  assert.equal(result.status, "unknown");
  assert.ok(result.reasons.some((reason) => reason.includes("not documented")));
});

test("unknown operating systems produce conditional results", () => {
  const item = {
    name: "Example",
    compatibility: { target: "NVIDIA CUDA", models: "Qwen" },
  };
  assert.equal(
    evaluate(item, { hardware: "nvidia", os: "linux" }).status,
    "partial",
  );
});

test("hardware categories do not invent model coverage", () => {
  assert.equal(
    evaluate(kapitsa, { hardware: "apple", model: "DeepSeek V4" }).status,
    "unknown",
  );
  assert.equal(
    evaluate(kapitsa, { hardware: "apple", os: "macos" }).status,
    "documented",
  );
});

test("ranked candidates order documented entries above missing evidence", () => {
  const result = rankedCandidates([kapitsa, basalt], { hardware: "blackwell" });
  assert.equal(result[0].item.name, "Basalt");
  assert.equal(result[1].evaluation.status, "unknown");
});

test("directory search includes extra compatibility fields", () => {
  assert.equal(searchProjects([kapitsa, basalt], "Blackwell").length, 1);
  assert.equal(searchProjects([kapitsa, basalt], "", "Apple").length, 1);
});
