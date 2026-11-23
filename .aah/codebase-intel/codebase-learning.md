# Codebase Learning Document

**Project**: brownfield
**Profiled**: 2026-11-23
**Primary Language**: Python
**Codebase Size**: 4 files, 863 lines

---

## 1. System Purpose and Context

A two-agent Python application that demonstrates and tests Claude-powered agentic behavior. The main agent (`agentic_app.py`) acts as an AI coding assistant with filesystem and shell access; it can explore a project, answer questions, and write reports. The QA agent (`agentic_tester.py`) drives a headless browser to verify a web application against a declared behavior catalog. Both agents use `claude-opus-5-5` with adaptive thinking enabled.

The project is a development/demonstration tool, not a production service: no server, no deployment config, no persistent storage.

---

## 2. Technology Stack

| Category | Technology | Version (if known) | Notes |
|----------|------------|-------------------|-------|
| Language | Python | 3.12 (ruff target) | Async (`asyncio`) used in tester |
| AI SDK | Anthropic | >=1.0.0 | `Anthropic` (sync) and `AsyncAnthropic` (async) clients |
| AI Model | claude-opus-5-5 | — | Both agents; adaptive thinking |
| Browser | Playwright + Chromium | >=1.40.0 | Headless, `async_playwright` |
| Linter | Ruff | — | E+F rules, B008 suppressed for DI idiom |

---

## 3. Architecture Overview

- **Architectural style**: Two independent single-file CLI agents with no orchestration layer between them. Each is a self-contained agentic loop.
- **Layer structure**: User input → Claude (inference) → tool dispatch → result → back to Claude. Repeats until `stop_reason != "tool_use"`.
- **Key design patterns**:
  - *Tool-use loop*: standard Claude tool-calling pattern — build `messages`, call `messages.create`, route `tool_use` blocks, append `tool_result` back, repeat.
  - *Safety boundary*: `run_command` maintains a keyword blocklist before passing to `subprocess.run`.
  - *Adaptive thinking*: both agents pass `thinking={"type": "adaptive", "display": "summarized"}` to surface reasoning.

**Agent 1 — `agentic_app.py`**: synchronous loop, up to 20 iterations (`MAX_ITERATIONS`), 5 tools.

**Agent 2 — `agentic_tester.py`**: async loop, no iteration cap, 6 browser tools. Browser and page are module-level globals (`_browser`, `_page`) shared across all tool calls.

---

## 4. Codebase Structure

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `/` (root) | Agent entry points, deps, linter config | `agentic_app.py`, `agentic_tester.py`, `requirements.txt`, `ruff.toml` |
| `config/` | Standalone startup helper | `env_check.py` |

---

## 5. Data Architecture

No persistent data stores. All data is in-memory and scoped to a single run:

- **Conversation state**: `messages: list[dict]` accumulated in each loop function; not persisted.
- **Test results**: module-global `_results: list[dict]` in `agentic_tester.py`; printed at the end of each `run()` call; not persisted.
- **Filesystem**: the only "store" is the local project filesystem, written to by the `write_file` tool in `agentic_app.py`.
- **Data flow pattern**: synchronous request/response (main agent); async request/response (tester).
- **Migration strategy**: none — no database.

---

## 6. API Surface

| Endpoint/Interface | Method | Purpose |
|-------------------|--------|---------|
| `run_agent(user_task: str) → str` | Python function | Main agentic loop; returns final text answer |
| `run(html_path: str) → None` | Async Python function | QA agentic loop; prints results to stdout |
| `check_env(required?)` | Python function | Validates env vars at startup; raises `ConfigError` |
| `load_dotenv(path?)` | Python function | Minimal `.env` parser; patches `os.environ` without overriding |

No HTTP server, no REST endpoints.

---

## 7. Key Abstractions

| Concept | Implementation | Files |
|---------|---------------|-------|
| Tool definition | `TOOLS: list[dict]` — JSON schema objects passed to `messages.create` | `agentic_app.py:37`, `agentic_tester.py:32` |
| Tool executor | `execute_tool(name, inputs)` / `_run_tool(name, inputs)` — routes tool name to implementation | `agentic_app.py:142`, `agentic_tester.py:150` |
| Agentic loop | `run_agent` / `run` — builds messages, calls Claude, dispatches tools, appends results, repeats | `agentic_app.py:241`, `agentic_tester.py:253` |
| System prompt | `SYSTEM_PROMPT` constant — persona and task framing for Claude | `agentic_app.py:226`, `agentic_tester.py:228` |
| Safety blocklist | Hardcoded keyword list in `execute_tool` → `run_command` | `agentic_app.py:172` |
| Env validation | `REQUIRED_ENV` tuple + `check_env()` | `config/env_check.py:28` |

---

## 8. Dependency Analysis

- **High-impact modules**: `anthropic` (SDK); changing model or API version affects both agents immediately.
- **Well-isolated modules**: `config/env_check.py` has no external deps and is independently testable.
- **Coupling note**: `config/env_check.py` is NOT imported by either agent yet. The module docstring specifies it must be called at the entrypoint — this wiring is missing (risk: startup misconfiguration is not caught early).
- **No circular dependencies**.

---

## 9. Testing Landscape

- **Test framework detected**: none (no pytest, unittest, or test runner config).
- **Test file count**: 0 (`test_files_count: 0` from profiler).
- **Test organization**: `agentic_tester.py` is itself a behavioral/E2E testing tool (Claude-driven browser tests), but it has no unit or integration tests of its own.
- **Coverage gaps**: the main agent loop, tool executor, and env_check module have no automated tests. No golden sets or eval suites for model behavior.
- **Agentic evaluation**: none found — no eval suite, no golden inputs/expected outputs, no CI quality gate on agent behavior.

---

## 10. Build and Deployment

- **Build system**: none; pure Python, run directly.
- **Dependency management**: `pip install -r requirements.txt`; also `playwright install chromium` for the browser agent.
- **CI/CD**: none detected.
- **Environment configuration**: `ANTHROPIC_API_KEY` required (read from env or `.env` via `config/env_check.py`). `REQUIRED_ENV` tuple is currently empty — the tuple exists as a scaffold but `ANTHROPIC_API_KEY` has not been added to it.
- **Container / infrastructure**: none.

---

## 11. Technical Debt and Risks

| Area | Observation | Impact | Confidence |
|------|-------------|--------|------------|
| `check_env` not wired | Neither agent calls `check_env()` at startup; API key absence surfaces as a downstream error | Medium — unclear error on misconfiguration | High |
| `REQUIRED_ENV` empty | The env validation scaffold is in place but `ANTHROPIC_API_KEY` is not listed | Low until wired; creates false sense of safety | High |
| Module-global browser state | `_browser` and `_page` in `agentic_tester.py` are module globals; not safe for concurrent use | Low for single-run CLI use; problematic if reused | High |
| No iteration cap in tester | `agentic_tester.py`'s loop has no `MAX_ITERATIONS` guard | Medium — runaway loop possible if model never stops calling tools | Medium |
| `run_command` keyword blocklist | Blocklist approach is a denylist (easy to bypass), not a safelist | Medium — `subprocess.run(shell=True)` with user-supplied input | High |
| No test coverage | No unit or integration tests; no evals for model behavior | High — changes to tool execution logic are undetected | High |
| Hardcoded model name | `MODEL = "claude-opus-5-5"` in both files; no central config | Low — requires editing two files for model changes | High |

---

## 12. Recommendations for Modification

- **Where to start**: read `agentic_app.py:241` (`run_agent`) and `agentic_tester.py:253` (`run`) — these are the agentic loops and the core of the system.
- **What to be careful about**: `execute_tool` → `run_command` runs `subprocess.run(shell=True)` — any change that widens what commands reach it needs careful review.
- **What to test after changes**: re-run `agentic_tester.py` against `sample/index.html` as a smoke test for the browser agent; manually invoke `agentic_app.py` with a task against a known directory for the main agent.
- **Potential pitfalls**:
  - Changing `TOOLS` schema without updating `execute_tool` routing breaks tool calls silently (Claude calls a tool, executor returns "ERROR: Unknown tool").
  - Adding `ANTHROPIC_API_KEY` to `REQUIRED_ENV` without also calling `check_env()` at startup has no effect.
  - `agentic_tester.py`'s `_page` global means multiple calls to `run()` in the same process share browser state — reset the global or use a fresh process for each test run.

---

## Agentic Application Overlay

| Concern | Finding |
|---------|---------|
| **Agent boundaries** | Two independent agents: `agentic_app.py` (filesystem assistant) and `agentic_tester.py` (browser QA). No orchestration layer between them. |
| **Models and prompts** | Both use `claude-opus-5-5`. System prompts are inline `SYSTEM_PROMPT` string constants, not versioned or templated. |
| **Tools and MCP servers** | 5 filesystem/shell tools in main agent; 6 browser tools in tester. No MCP servers. |
| **Memory and retrieval** | None — stateless per run. Conversation history held in-memory `messages` list; discarded after each `run_agent` / `run` call. |
| **Identity and tool permissions** | `ANTHROPIC_API_KEY` from env. `run_command` has a hardcoded keyword denylist. No authentication for outbound tool calls beyond the API key. |
| **Existing evaluations** | None found. `agentic_tester.py` is itself a testing tool but is not tested. No golden sets, no CI quality gates on model behavior. |
