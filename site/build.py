#!/usr/bin/env python3
"""Generate the GitHub Pages catalogue from the canonical Markdown files."""

import argparse
import json
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
EXCLUDED_HEADINGS = {"Contents", "Choose by hardware and workload", "Evaluating performance claims", "Contributing"}
ENTRY = re.compile(r"^- \[([^]]+)\]\((https?://[^)]+)\)\s+[-–]\s+(.+)$")
LINK = re.compile(r"\[([^]]+)\]\((https?://[^)]+)\)")


def plain(markdown):
    markdown = LINK.sub(r"\1", markdown)
    markdown = re.sub(r"`([^`]+)`", r"\1", markdown)
    return markdown.replace("**", "").strip()


def load_catalogue(root=ROOT):
    engines = []
    section = ""
    for line in (root / "README.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        match = ENTRY.match(line)
        if not match or section in EXCLUDED_HEADINGS:
            continue
        name, url, description = match.groups()
        if urlsplit(url).scheme != "https":
            continue
        category = section
        engines.append({
            "id": re.sub(r"[^a-z0-9]+", "-", name.casefold()).strip("-"),
            "name": name,
            "url": url,
            "description": plain(description),
            "category": category,
            "kind": "resource" if category == "Benchmarks and related lists" else "project",
            "compatibility": None,
        })
    indexed = {engine["name"].casefold(): engine for engine in engines}
    rows = 0
    for line in (root / "compatibility.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("| "):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 6 or cells[0] in ("Engine", "---"):
            continue
        engine = indexed.get(cells[0].casefold())
        if engine is None:
            raise ValueError(f"Compatibility row has no catalogue entry: {cells[0]}")
        if engine["compatibility"]:
            raise ValueError(f"Duplicate compatibility row: {cells[0]}")
        evidence = [{"title": title, "url": url} for title, url in LINK.findall(cells[5])]
        if not evidence:
            raise ValueError(f"Compatibility row lacks evidence links: {cells[0]}")
        engine["compatibility"] = {
            "target": plain(cells[1]),
            "models": plain(cells[2]),
            "execution": plain(cells[3]),
            "interface": plain(cells[4]),
            "evidence": evidence,
            "status": "upstream-documented",
        }
        rows += 1
    if len(engines) < 50 or rows < 15:
        raise ValueError(f"Unexpectedly small catalogue: {len(engines)} projects, {rows} evidence rows")
    if len({engine["id"] for engine in engines}) != len(engines):
        raise ValueError("Two catalogue names produce the same URL identity")
    return {"projects": engines, "counts": {"all": len(engines), "documented": rows,
            "resources": sum(e["kind"] == "resource" for e in engines)}}


def build(output):
    output.mkdir(parents=True, exist_ok=True)
    catalogue = load_catalogue()
    (output / "data.json").write_text(json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for filename in ("index.html", "styles.css", "app.js", "engine-logic.mjs"):
        shutil.copyfile(SITE / filename, output / filename)
    (output / ".nojekyll").touch()
    return catalogue


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "site-dist")
    args = parser.parse_args()
    result = build(args.output)
    print(f"Built {args.output}: {result['counts']['all']} entries, "
          f"{result['counts']['documented']} sourced compatibility profiles")
