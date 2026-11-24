## Id
F-MOD-000

## Title
pytest Infrastructure and Shared Conftest Fixtures

## Module Ref
MOD-000

## Description
This module creates the entire pytest dev infrastructure for the brownfield project: a
`requirements-dev.txt` at the project root with `pytest>=8` and `pytest-asyncio`, an empty
`tests/__init__.py` package marker, and a `tests/conftest.py` that provides the shared fixtures
consumed by every downstream test module.

The project context is a two-agent Python CLI application described in
`.aah/architecture/architecture-overview.md` (§Layer Summary, §Technology Decisions). The two
agents — `agentic_app.py` (synchronous filesystem/shell coding assistant) and `agentic_tester.py`
(async Playwright browser QA agent) — both call the Anthropic SDK and, in the tester's case, drive
a real Chromium process. The testing landscape and coupling risks are documented in
`.aah/codebase-intel/codebase-learning.md` (§9 Testing Landscape, §11 Technical Debt). The module
only scaffolds the dev infrastructure; it does not write any test assertions — those belong to
MOD-002 as recorded in `.aah/architecture/module-map.yaml`.

**Stack:** Python 3.12, pytest>=8, pytest-asyncio, `unittest.mock` (stdlib). No model calls and no
browser process are started during the test run; both are replaced by mock fixtures so the suite
runs fully offline.

**conftest.py fixtures to implement:**

1. `mock_anthropic_client` (function-scoped) — a `unittest.mock.MagicMock` (or `AsyncMock` for
   async paths) that replicates the `anthropic.Anthropic` / `anthropic.AsyncAnthropic` client
   interface. Its `messages.create` (and `messages.acreate`) return a controlled response object
   whose `stop_reason` is `"tool_use"` on the first call and `"end_turn"` on the second, with a
   `content` list carrying a `tool_use` block containing a predictable `name` and `input` dict.
   This allows tests for `execute_tool` and `_run_tool` to exercise the full dispatch path without
   any network call.

2. `mock_page` (function-scoped, `pytest.mark.asyncio` compatible) — an `AsyncMock` that replicates
   the `playwright.async_api.Page` interface. At minimum it must expose `goto`, `click`,
   `fill`, `evaluate`, and `query_selector` as async stubs returning sensible defaults so that
   browser-tool unit tests in `tests/test_run_tool.py` can call `_run_tool` with predictable
   outcomes.

Both fixtures must be defined at the top of `tests/conftest.py` with standard pytest `@pytest.fixture`
decorators. `pytest-asyncio` must be configured for `asyncio_mode = "auto"` (via a `pytest.ini_options`
section in `pyproject.toml` or a `[pytest]` section in `pytest.ini`, or as a `conftest.py`-level
`pytest_configure` hook) so that async test functions in MOD-002 do not require per-test
`@pytest.mark.asyncio` decoration.

**Behavioral expectations:**

- Given `requirements-dev.txt` is created at the project root with `pytest>=8` and
  `pytest-asyncio`, when a developer runs `pip install -r requirements-dev.txt`, then the command
  exits 0, both `pytest` and `pytest_asyncio` are importable, and no package listed conflicts with
  the production `requirements.txt` (`anthropic>=1.0.0`, `playwright>=1.40.0`).
- Given the `tests/` package exists with `tests/__init__.py` and `tests/conftest.py`, when
  `pytest --collect-only` is run from the project root, then the command exits 0 with no collection
  errors (the package is discoverable and no syntax errors are present in conftest).
- Given `tests/conftest.py` exports the `mock_anthropic_client` fixture, when a test function
  requests it, then it receives a mock whose `messages.create` returns an object with
  `stop_reason = "tool_use"` on the first call and `stop_reason = "end_turn"` on the second, and no
  HTTP connection to `api.anthropic.com` is opened during the test.
- Given `tests/conftest.py` exports the `mock_page` fixture, when an async test function requests
  it, then it receives an `AsyncMock` Page object whose awaitable methods (`goto`, `click`, `fill`,
  `evaluate`, `query_selector`) resolve without error and no Chromium browser process is spawned.
- Given `pytest-asyncio` is configured with `asyncio_mode = "auto"`, when an `async def test_*`
  function in the `tests/` package runs, then it completes without the
  `PytestUnraisableExceptionWarning` or `no event loop` errors that arise from missing asyncio
  mode configuration.
- Given `ANTHROPIC_API_KEY` is the runtime secret required by both agents (see
  `.aah/architecture/architecture-overview.md` §Technology Decisions and
  `.aah/codebase-intel/codebase-learning.md` §10 Build and Deployment), when the project's
  `.env.example` file is inspected, then `ANTHROPIC_API_KEY` appears as a named entry with a safe
  placeholder value (e.g. `your-api-key-here`), confirming the variable is documented for
  developers who clone the repo.
- Given the conftest fixtures mock the Anthropic client and Playwright page, when the full test
  suite (`pytest tests/ -v`) is run without a real `ANTHROPIC_API_KEY` set in the environment,
  then all tests that use only these fixtures still pass — the mock layer must fully isolate the
  suite from the live API and browser.

## Layers
- tests

## Dependencies

## Required Env Variables
- ANTHROPIC_API_KEY — Anthropic API key required at agent runtime; the conftest mock fixtures replace the live client so tests do not call the real API, but the variable must be listed in `.env.example` as the documented secret name

## Lint Config
Before writing any application code, for each root below: create its manifest first, then run
`aah agentic run core.scaffold.project ensure-lint-config --project-path "$PROJECT_DIR" --package-root <root> --install`
— it reads the manifest to pick the linter, writes the config, adds the linter to dev dependencies
and installs it, and never clobbers an existing config. Where a source path is given, copy that file
into the root first, then run the same command. Commit the configs with this module.

- backend — ruff.toml

## Constraints

## Existing Code Touched
None — no existing implementation for this module.

## Applicable Standards
- Total rules: 12
- Critical:
  - PY-SEC-001
  - PY-SEC-002
  - PY-SEC-003
- High:
  - PY-SEC-004
  - PY-TEST-001
  - PY-ERR-001
- Medium:
  - PY-ERR-002
  - PY-PERF-001
  - PY-PERF-002
- Low:
  - PY-CONV-001
  - PY-CONV-002
  - PY-CONV-003

## Status
planned