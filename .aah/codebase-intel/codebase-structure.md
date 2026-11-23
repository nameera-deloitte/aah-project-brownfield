# Codebase Structure

## Directory Layout

```
brownfield/
├── agentic_app.py          # Main agent: filesystem + shell tool-calling loop
├── agentic_tester.py       # QA agent: Playwright browser automation loop
├── requirements.txt        # Python dependencies
├── ruff.toml               # Linter configuration (Ruff, Python 3.12)
└── config/
    └── env_check.py        # Startup env-var validation; no external deps
```

## Entry Points

| File | Role | Description |
|------|------|-------------|
| `agentic_app.py` | Main agent | `run_agent(user_task)` drives the synchronous tool-calling loop; `__main__` runs Task 1 by default |
| `agentic_tester.py` | QA agent | `run(html_path)` drives the async Playwright + Claude loop; `__main__` targets `sample/index.html` |
| `config/env_check.py` | Config validator | `check_env()` checks required env vars at startup; also runnable as `python config/env_check.py` |

## API Routes

None — this is a CLI/library application with no HTTP server.

## Module Organization

Flat, two-module structure at the project root. `config/` holds a single standalone helper with no third-party imports, by design (the module's own docstring specifies this so the delivered app runs without the AAH harness).
