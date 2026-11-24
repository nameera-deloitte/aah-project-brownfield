## Problem Statement

The existing agentic application (`agentic_app.py`, `agentic_tester.py`) has a security posture typical of a demonstration-grade PoC that was never hardened for real use. The application gives an LLM access to filesystem read/write, shell command execution, and browser automation — a wide action surface with minimal enforcement. As stated in the project brief:

> *"run_command relies on a keyword denylist (blocklist) rather than a safelist — easily bypassed; ANTHROPIC_API_KEY is not validated at startup via check_env(); REQUIRED_ENV tuple is empty — no env-var enforcement at boot; no authentication or authorisation for outbound tool calls beyond the API key; no unit tests or evaluations on the tool execution path; module-global browser state in agentic_tester.py is not safe for concurrent use."*

The improvement_type is **enhancement** — this is not a rewrite, but a targeted security hardening pass on two in-scope gaps: (1) absence of authentication/authorisation for individual tool calls beyond the shared API key, and (2) absence of any automated test coverage or eval suite.

## Solution

The hardened system is a local, on-premises Python CLI tool with no cloud deployment, no container runtime, and no custom UI. It runs the two existing agents (`agentic_app.py` and `agentic_tester.py`) exactly as before but adds two security controls:

**Authentication & authorisation for outbound tool calls** (`auth-outbound-approach = capability-scoped-per-tool`): Each of the 11 tools (5 in the main agent, 6 in the tester) is annotated with an explicit allow/deny capability list. The tool executor validates that the requested operation is within the tool's declared capability envelope before passing it to the underlying implementation. This is a deterministic skeleton control — the LLM cannot call a tool's undeclared capability regardless of the prompt.

**Unit tests and a golden evaluation set** (`eval-suite-scope = unit-tests-golden-set`): pytest-based unit tests are added for `execute_tool` (agentic_app.py) and `_run_tool` (agentic_tester.py). A golden set of run_command inputs with expected outcomes (allow/block decisions) is included to guard against security-control regressions. No model calls are needed to run the suite.

An **iteration cap** is added to `agentic_tester.py` (`tester-iteration-cap = yes`), matching the main agent's `MAX_ITERATIONS = 20`, closing the runaway-loop risk flagged in the codebase intel.

The system runs entirely on-prem (`cloud-vs-local = local`, `compliance-regimes = [on-prem]`). There is no persistent data store (`data-storage-present = no`), no frontend (`custom-ui-required = no`), and no Docker requirement (`docker-installed = no`). The technical archetype is ai-applications; no industry domain brief applies.

The following four gaps from the brief are **deferred** out of PoC scope: `run_command` safelist, `check_env()` wiring, `REQUIRED_ENV` hardening, and browser state isolation.

## User Stories

1. As a developer deploying the coding assistant, I want each tool to declare its capability envelope, so that the agent cannot be directed to exercise undeclared capabilities regardless of prompt input.
2. As a developer maintaining the codebase, I want unit tests for the tool execution path, so that any regression in security controls is caught automatically before it reaches production.
3. As a developer running the QA tester, I want a `MAX_ITERATIONS` guard in `agentic_tester.py`, so that a model loop that never stops calling tools is bounded and fails cleanly.
4. As a security reviewer, I want a golden input/output set for run_command safety, so that the denylist (or any future safelist) is verified against known adversarial inputs on every CI run.
