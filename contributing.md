# Contributing

Contributions are welcome: new engines, corrections, missing hardware or model constraints, broken links, and better primary sources.

## What belongs here

- A publicly inspectable project with a documented, runnable inference path. It can be general-purpose or deliberately narrow in model and hardware support.
- A distinctive fork with meaningful execution changes, described alongside its upstream lineage.
- A relevant serving, orchestration, or kernel project in its **own category**, not misrepresented as a standalone engine.
- Links to the **upstream repository** and primary technical documentation; measurements should identify their test conditions.

Do not add an implementation that is merely announced, a renamed duplicate, a benchmark-only repository, an inactive/archived engine to the active index, or promotional claims without enough evidence to interpret them. Historically significant projects can be proposed for [historical.md](historical.md).

## Make an edit

Use one entry per line in the relevant section, sorted alphabetically:

```markdown
- [Project Name](https://github.com/owner/repository) - Specific capability and the hardware or model constraint that distinguishes it.
```

Keep descriptions factual, sentence-cased, and ending with a period. Avoid star counts, unqualified best/fastest claims, screenshots used as evidence of performance, and claims that a project supports a model merely because its dependency does.

If correcting a technical claim, link to an upstream release, documentation, issue, paper, or a reproducible benchmark. Engine authors are welcome to contribute; disclose project affiliation when relevant.

Open a focused pull request explaining what changed and why it is useful. No issue or approval ceremony is required for a straightforward correction.
