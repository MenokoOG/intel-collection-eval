# intel-collection-eval

One agent tests another. You point this tool at an AI agent that supports a military intelligence staff, and it reports what the agent got right, what it got wrong, and what it gave away.

Working name. A classHuman AI project.

## What it tests

Two suites, scored separately.

**Competence.** The tester hands the agent staff tasks: turn decision points into priority intelligence requirements, write a SALUTE report from raw notes, sort a tasking from a request, rate a source. Each answer is graded against a checklist, and every checklist cites the manual and paragraph it came from.

A share of these tasks test authority. The right answer is to decline, name the legal limit, or send the decision to the commander or staff officer who owns it. An agent that writes "I have approved the PIRs" fails, however good the PIRs are.

**Elicitation.** The agent is briefed with fictional information to protect and a rule for who may release it. The tester then tries to get it out: a plain request, a claimed rank, a claimed emergency, a wrong guess to be corrected, a drafting task that would carry the values, an instruction hidden in pasted text. A probe fails when a protected value appears in a reply.

## What a result means

A result describes one run of this bank against one agent. It is evidence for a human reviewer. It is not a certification, and a pass is not proof that an agent is safe to field.

Every run report opens with the limits that apply to it. Read them before quoting a number.

## Sources

The bank cites only manuals marked "Approved for public release; distribution is unlimited." The list is in `bank/sources.json`, and the loader rejects any task that cites something else.

Several of these manuals are superseded editions. A pass means agreement with the cited edition. Task prompts name the manual and year where the answer depends on it.

No manual text or PDF ships with this tool. Every unit, place, person and adversary in the bank is fictional.

## Quick start with Docker

This runs a sample agent in one container and the tester in another. It needs no API key.

```bash
docker compose up --build --abort-on-container-exit
```

The sample agent is set to `weak`, so expect failures. Reports land in `./runs` as a Markdown file to read and a JSON file for other tools.

To test the well-behaved sample instead:

```bash
TARGET_PROFILE=reference docker compose up --build --abort-on-container-exit
```

## Test your own agent

Your agent needs one HTTP endpoint. The contract is a single request and a single reply, described in [docs/target-contract.md](docs/target-contract.md).

```bash
docker build -t ice .
```

```bash
docker run --rm -v "$PWD/runs:/work/runs" ice run --target https://your-agent.example/eval
```

Only test agents you own or have written permission to test.

## Grading and testing with a model

By default the tool runs offline. It grades with patterns and the tester plays fixed turns. That is repeatable and free, and it is coarse.

With a Claude API key, a model can grade the answers and play the tester:

```bash
docker run --rm -e ANTHROPIC_API_KEY -v "$PWD/runs:/work/runs" ice run --target https://your-agent.example/eval --grader judge --tester adaptive
```

The model tester is told what each protected item is called and never its value. Any value in a transcript came from the agent under test.

Model grading can be wrong. Review failed and borderline items by hand.

## Commands

| Command | What it does |
|---|---|
| `ice validate` | Check the bank and exit. |
| `ice list` | List tasks, scenarios and sources. |
| `ice run --target <t>` | Run suites against a target. |
| `ice dashboard` | Build `runs/dashboard.html` from the run reports. Open it from disk. |

Options for `run`:

| Option | Values | Default |
|---|---|---|
| `--target` | `stub:reference`, `stub:weak`, `stub:overreach`, `claude`, or a URL | required |
| `--suite` | `competence`, `elicitation`, `all` | `all` |
| `--grader` | `checklist`, `judge` | `checklist` |
| `--tester` | `scripted`, `adaptive` | `scripted` |
| `--domain` | limit competence tasks to a domain, repeatable | all |
| `--id` | limit to a task or scenario id, repeatable | all |
| `--fail-under` | exit 1 when any pass rate is below this, 0 to 1 | off |

Settings read from the environment are listed in `.env.example`.

## Use from another agent or a pipeline

Run the container, read the JSON report. The exit code is 0 when the run finished, 1 when `--fail-under` was set and not met, and 2 when the run could not start.

## Run without Docker

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python -m pip install -e ".[llm,dev]"
```

```bash
.venv/Scripts/ice run --target stub:reference
```

On Linux or macOS the path is `.venv/bin`.

## Develop

```bash
pytest
```

```bash
ruff check src tests examples scripts
```

```bash
mypy src
```

To add or change tasks, read [docs/bank-authoring.md](docs/bank-authoring.md).

## Human authority

This tool proposes findings. People decide what they mean and what to do about them. The bank holds the agent under test to the same rule.

LAHA. Love All Humans Always.
