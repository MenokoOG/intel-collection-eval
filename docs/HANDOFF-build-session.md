# Handoff: build or adopt, then build

Paste the prompt at the bottom into a new session started in `F:\classHuman\intel-collection-eval`.

## State on 2026-10-10

- Branch `claude/mvp-scaffold`, commit `0ee09d6`, pushed. Not on main.
- Working: runner, CLI, stub and HTTP targets, checklist grader, scripted tester, dashboard, Docker demo. 28 tests, ruff and mypy clean.
- Written, never run live: judge grader, adaptive tester, Claude target.
- Bank: 115 competence tasks (38 authority), 3 elicitation scenarios, 16 probes. Drafted by a model. No expert review.
- Engine is about 1,000 lines of Python with pydantic as the only hard dependency.

## What is ours and what is not

Ours, keep regardless of engine choice:
- The bank format: citations, elements, forbidden rules, authority kind, protected items.
- The bank content and its public-release source rule.
- The report caveats and the guarded wording.

Candidate to replace: the runner, target adapters, graders, tester loop, report and dashboard plumbing.

## Hypotheses to check, not facts

Written from memory. Verify each against current docs before relying on it.

| Option | Why it might fit | What to check |
|---|---|---|
| Inspect AI (UK AISI) | Tasks, solvers, scorers, agent and multi-turn support, logs viewer | License, Docker and offline use, custom scorer for our checklist, log viewer versus our dashboard |
| promptfoo | YAML tests, red-team plugins, CI use | Multi-turn probes, citation traceability, offline use, license terms |
| DeepEval | Python metrics, G-Eval judges | Authority-style tasks, multi-turn, how much it assumes a cloud |
| Garak | Probe-based vulnerability scanning | Fit for scenario-specific protected values |
| PyRIT | Multi-turn red-team orchestration | Weight, fit for our leak detection |
| OpenAI Evals / lm-eval-harness | Benchmark style | Probably wrong shape for agents |
| Keep ours | Small, offline, citation-first, already works | Cost of judge calibration and maintenance |

## Decision criteria

1. Runs offline in a container with no required cloud service. Government users may be air-gapped.
2. Every result traces to a cited paragraph.
3. Can target an arbitrary HTTP agent, not only a model API.
4. Authority tasks and leak probes expressible without hacks.
5. License allows a commercial service by classHuman AI LLC.
6. Maintenance burden for one person.
7. Output a reviewer can read without our tool.

A hybrid is allowed: keep our bank format and write an exporter into one framework, or run ours and adopt a framework only for the judge and the adaptive tester.

## Rulings that stay Lawrence's

Build versus adopt, name, license, public or private repo, restricted manuals, expert review, anything that spends API money, merges to main.

## Prompt to paste

```
Continue intel-collection-eval. Read PROJECT.md, docs/HANDOFF-build-session.md and the newest log/ entry. Answer in 5 lines, then start.

Job: research whether to build the evaluation engine ourselves or adopt an existing framework. Do not write engine code yet.

1. Research each option in the handoff table from current primary sources (docs, repos, licenses). Mark every claim verified or unverified. Cite the link.
2. Score each option against the seven criteria. Use a table.
3. Prototype the cheapest test of the top two: express three of our tasks (one recall, one authority, one product) and one elicitation scenario in that framework. Time-box it. Do not migrate the bank.
4. Bring Lawrence one recommendation with the evidence and the cost of being wrong. Stop and wait for his ruling. Record the ruling in DECISIONS.md only after he gives it.

Constraints: there is no main yet, so branch a new claude/* branch off claude/mvp-scaffold and ask Lawrence before creating main. Do not spend API money without his yes. Do not describe the tool or any agent as autonomous. Do not call a run result a certification. No Claude API calls without asking first.

Fallback if research stalls: run one competence domain with --grader judge against --target claude, with his go-ahead on the spend, and compare with the checklist grader.
```
