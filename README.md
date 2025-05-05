# ReCUR – Recursive Cognition Upgrade Routine

ReCUR utilizes a **Feedback-Driven Refinement Loop**. A Large-Language-Model (LLM)'s answer is fed to a grading agent, and the LLM then iteratively refines its output based on the agent's evaluation until the grading agent signals that the process is complete.

> "Ask once, iterate thrice, deliver the best." – ReCUR mantra

---

## ✨ Key Features

| Category                | Capability                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | --- |
| **Iterative Reasoning** | Base answer → heuristic round counter → N alternatives per round → grading and promotion of the current best → final voting. |
| **Pluggable LLMs**      | Abstract `LLM` interface defaults to **Google GenAI Gemini‑2 Flash**. Pass `--echo` to dry‑run without network.              |
| **Custom Rubrics**      | Drop any plain‑text rubric via `--rubric-file` (e.g., coding, general, education).                                           |
| **Structured Logs**     | JSON‑line logs via `loguru`; pipe into `jq` or any SIEM.                                                                     |
| **Audit Chronicle**     | `--audit-json` captures every base & alt with scores for offline analysis.                                                   |
| **Async & Concurrent**  | `asyncio` + `gather` generates alternatives in parallel for high throughput.                                                 |
| **Config Everywhere**   | YAML file, environment variables, **and** CLI flags—merged with CLI precedence.                                              |
| <!--                    | **Dev Tooling**                                                                                                              | Black, Ruff, Mypy, Pytest (+90 % coverage target) and GitHub Actions CI. | --> |
| **Extensible Agents**   | Subclass responder, grader, or selector to experiment with new strategies.                                                   |

---

## 🏗️ Architecture Overview

```
User Prompt
    │
    ▼
BaseResponder  ──────────────┐
    │                       │  heuristic_rounds()
    ▼                       │
RoundCounter  (R rounds)    │
    │                       │
    ▼                       │
Async AltResponders (N)     │  per round
    │                       │
    ▼                       │
RubricGrader  ◀──────────────┘  pick better
    │
    ▼
FinalSelector  (vote)
    │
    ▼
  Best Answer + Audit Log
```

---

## 🔧 Installation

```bash
# 1. Clone
$ git clone https://github.com/monster0506/recur.git && cd recur

# 2. Create venv via uv & install project + deps
$ uv pip install -e .
```

> **Tip:** `uv` resolves and caches wheels for ultra‑fast, reproducible installs.

---

## 🚀 Quick Start

```bash
# Simplest run – default YAML + CLI prompt
$ uv run recur -p "Explain relativity like I'm 12"

# Dry‑run without hitting GenAI (echo model)
$ uv run recur -p "Ping" --echo

# Custom rubric & more exploration per round
$ uv run recur -p "Design a REST API" \
            -b rubrics/coding_rubric.txt \
            -a 5 -n 2 -t 0.6 \
            -j audits/{{timestamp}}.jsonl
```

---

## 📝 Configuration

1. **Default file** `config/default.yaml` – copy & edit.
2. **Environment** – set `GOOGLE_API_KEY` for GenAI.
3. **CLI flags** – override any YAML key (see below).

> YAML → overridden by CLI if duplicate key.

### Full YAML Template

```yaml
prompt: ""
model: gemini-2.0-flash-001
temperature: 0.4
rounds: null
alts: 3
rubric_file: null
log_level: INFO
logfile: null
audit_json: null
output_file: null
echo: false
```

---

## 🖥️ Command‑Line Reference

```
recur [-h] [-p PROMPT] [-c YAML] [-b FILE] [-n INT] [-a INT] [-t FLOAT]
      [-l PATH] [-L LEVEL] [-o PATH] [-j PATH] [--echo]
```

| Flag                | Purpose                               | Config Key    |
| ------------------- | ------------------------------------- | ------------- |
| `-p, --prompt`      | User prompt (required if not in YAML) | `prompt`      |
| `-c, --config`      | YAML config path                      | –             |
| `-b, --rubric-file` | Custom rubric file                    | `rubric_file` |
| `-n, --rounds`      | Fixed number of rounds                | `rounds`      |
| `-a, --alts`        | Alternatives per round                | `alts`        |
| `-t, --temperature` | LLM sampling temperature              | `temperature` |
| `-l, --logfile`     | JSON log file                         | `logfile`     |
| `-L, --log-level`   | DEBUG/INFO/WARNING/ERROR              | `log_level`   |
| `-o, --output-file` | Save final answer only                | `output_file` |
| `-j, --audit-json`  | Save full chronicle                   | `audit_json`  |
| `--echo`            | Use EchoLLM stub                      | `echo`        |

---

## 🔍 Logging & Auditing

- **Console** – human‑readable logs (stderr).
- **`--logfile run.jsonl`** – newline‑delimited JSON; pipe to `jq`.
- **`--audit-json all.json`** – structure:

  ```json
  {
    "prompt": "...",
    "chronicle": [
      { "agent": "base", "score": 72.3, "text": "..." },
      { "agent": "alt_0", "score": 80.1, "text": "..." },
      { "agent": "final", "score": 80.1, "text": "..." }
    ]
  }
  ```

---

<!-- ## Testing & Quality Gates -->

<!-- | Tool       | Command            | Purpose                              | -->
<!-- | ---------- | ------------------ | ------------------------------------ | -->
<!-- | **Pytest** | `uv run pytest -q` | unit + async tests (≥ 90 % coverage) | -->
<!-- | **mypy**   | `uv run mypy src`  | Static typing, strict mode           | -->
<!-- | **Ruff**   | `uv run ruff .`    | Linting, quick fixes with `--fix`    | -->
<!-- | **Black**  | `uv run black .`   | Code formatter                       | -->

<!-- CI runs all the above in GitHub Actions. -->

---

## Contributing

1. Fork & clone.
2. `uv pip install -e .[dev]`
3. Create feature branch, add tests.
4. PR with clear description.
5. Ensure CI is green.

---

## License

MIT – see `LICENSE` file.

---

## Acknowledgements

- [Google GenAI](https://ai.google.dev/) for model APIs.
- [uv](https://github.com/astral-sh/uv) for blazing‑fast dependency solves.
- [loguru](https://github.com/Delgan/loguru) for zero‑boilerplate logging.
- Community inspiration from the original “Chain‑of‑Thought” paper.

---

> Happy recursive reasoning!
