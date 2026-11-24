## Id
- F-MOD-002

## Title
- pytest Test Suite and Golden Evals

## Module Ref
- MOD-002

## Description
This module creates the automated test suite for the security controls introduced in MOD-001, as described in `architecture-overview.md` (Test Suite layer) and grounded in user story 2 and 4 from `discuss/discuss-prd.md`. It produces four pytest test files and one golden evaluation YAML file, all under a new `tests/` tree built on the scaffold established by MOD-000. No model calls are needed to run the suite — the Anthropic client is replaced by the mock fixture in `tests/conftest.py`.

The five artefacts and their responsibilities:

**`tests/test_execute_tool.py`** — unit tests for `execute_tool()` in `agentic_app.py` (see lines 142–218 as profiled in `.aah/codebase-intel/codebase-learning.md §7`). Covers: (a) capability validation — `CapabilityError` is raised when a tool name is absent from `CAPABILITY_MAP` or its declared capabilities do not cover the requested operation; (b) successful file dispatch — `read_file` returns file contents and `write_file` writes content and returns a success string; (c) `run_command` blocklist enforcement — blocked keywords at `agentic_app.py:172` (`"rm "`, `"del "`, `"format "`, `"mkfs"`, `"sudo"`, `"shutdown"`, `":(){"`) produce a `"BLOCKED:"` return without spawning a subprocess, and a safe command (e.g. `"echo hello"`) returns its stdout.

**`tests/test_run_tool.py`** — unit tests for `_run_tool()` in `agentic_tester.py` (lines 150–240). Uses the async mock Playwright page from `tests/conftest.py` (MOD-000). Covers: (a) capability validation — `CapabilityError` is raised when a tool call exceeds its declared capability envelope; (b) `open_page` dispatches to `_page.goto` and returns a JSON payload with `title`, `buttons`, `input_count`, `form_count`; (c) `record_result` appends to the module-global `_results` list and returns a success string.

**`tests/test_iteration_cap.py`** — single regression assertion: imports `agentic_tester` and asserts `agentic_tester.MAX_ITERATIONS == 20`, guarding the guard added in MOD-001 against accidental removal.

**`tests/test_golden.py`** — parametrized pytest test that reads `tests/golden/run_command_golden.yaml` at collection time, iterates over every entry, and asserts the actual blocklist decision for each `command` matches its `expected_outcome` (`allow` or `block`). No subprocess is spawned; the test exercises only the keyword-matching logic extracted from `execute_tool` → `run_command` at `agentic_app.py:172`.

**`tests/golden/run_command_golden.yaml`** — a YAML list of evaluation cases. Each entry is a mapping with `command` (string), `expected_outcome` (one of `allow` or `block`), and `rationale` (string). The set must include at minimum: benign commands that the blocklist allows (`echo`, `python --version`, `ls`, `git status`, `cat README.md`) and adversarial commands that it blocks (`rm -rf /`, `sudo apt-get install`, `del /f /s /q`, `shutdown -r`, `mkfs.ext4`, the fork-bomb prefix `:(){ :|:& };:`). The YAML is read-only at test time and is never written by either agent (see `data-model.md` §Key Data Structures — Golden set entry).

The full capability-validation and flow mechanics are specified in `architecture-overview.md` (Security Controls layer), `application-flow.md` (Blocked path variant), and `data-model.md` (CAPABILITY_MAP and CapabilityError structures). The `codebase-intel/codebase-learning.md §9` confirms there are zero existing test files; all five artefacts are new.

**Behavioral expectations** (the acceptance intent — the build-phase implementer writes TDD tests from these; there is no separate Test Cases section):

- Given `execute_tool` with `CAPABILITY_MAP` populated by MOD-001, when a tool name maps to a capability envelope that does not include the requested operation, then `CapabilityError` is raised and its message is returned as the tool_result string without reaching the tool implementation.
- Given `execute_tool` with a readable file at a known temporary path, when `execute_tool("read_file", {"path": <relative-path>})` is called, then the file's UTF-8 contents are returned as a string.
- Given `execute_tool` with `write_file` capability in scope, when `execute_tool("write_file", {"path": <relative-path>, "content": "hello"})` is called, then the content is written to disk and a non-error string is returned.
- Given `execute_tool`'s `run_command` with a command containing any of the seven blocked keywords at `agentic_app.py:172` (`"rm "`, `"del "`, `"format "`, `"mkfs"`, `"sudo"`, `"shutdown"`, `":(){"`), when `execute_tool("run_command", {"command": <command>})` is called, then the return string begins with `"BLOCKED:"` and no subprocess is spawned.
- Given `execute_tool`'s `run_command` with a safe command containing none of the blocked keywords, when called, then `subprocess.run` is invoked and stdout (or `"(no output)"`) is returned.
- Given `_run_tool` with `CAPABILITY_MAP` populated by MOD-001, when a call is made with a tool name whose declared capabilities do not cover the requested operation, then `CapabilityError` is raised and its message is returned without reaching the Playwright page.
- Given `_run_tool` and the async mock Playwright page fixture from `tests/conftest.py`, when `_run_tool("open_page", {"file_path": <path>})` is awaited, then `_page.goto` is awaited with a `file:///` URL and the return value is a JSON string containing `title`, `buttons`, `input_count`, and `form_count` keys.
- Given `_run_tool` and the async mock Playwright page fixture, when `_run_tool("record_result", {"test_id": "T1", "test_name": "example", "passed": True, "expected": "x", "actual": "x"})` is awaited, then the entry is appended to `agentic_tester._results` and a non-error string is returned.
- Given `agentic_tester` imported after MOD-001 adds `MAX_ITERATIONS`, when `agentic_tester.MAX_ITERATIONS` is read, then it equals `20` exactly.
- Given `tests/golden/run_command_golden.yaml` exists as a valid YAML list, when each entry is loaded at pytest collection time by `test_golden.py`, then every entry has the keys `command`, `expected_outcome`, and `rationale`, and `expected_outcome` is one of `allow` or `block`.
- Given the golden YAML parametrized in `test_golden.py`, when the blocklist logic from `agentic_app.py:172` is applied to each `command`, then the computed outcome matches `expected_outcome` for every case with no failures.
- Given the golden YAML, when the full set is loaded, then at least one entry has `expected_outcome: allow` and at least one has `expected_outcome: block`, ensuring the golden set covers both safe and adversarial inputs.
- Given `pytest tests/ -v` is run after MOD-001 is applied, when all five artefacts are present, then the command exits with code 0 and all collected tests pass.

## Layers
- tests
- evals

## Dependencies
- F-MOD-001

## Required Env Variables

## Lint Config

## Constraints

## Existing Code Touched
| file | current responsibility | action | why |
|------|----------------------|--------|-----|
| agentic_app.py | filesystem/shell tool-calling loop; `execute_tool` (line 142) with `run_command` blocklist (line 172) | leave | confirmed at lines 142–218; this module's test files import and test these functions but do not change the source file |
| agentic_tester.py | async browser QA agent; `_run_tool` (line 150) and module-global `_results` | leave | confirmed at lines 150–253; this module's test files import and test these functions but do not change the source file |

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