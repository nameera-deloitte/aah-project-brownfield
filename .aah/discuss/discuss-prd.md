# Discuss PRD — brownfield

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

## Overview & Intent

| Field | Value |
|-------|-------|
| Project | `brownfield` |
| Complexity tier | `poc` |
| Business domain(s) | _None selected._ |
| Technical archetype(s) | `ai-applications` |
| Discovery started | 2026-11-24 |

## Scope

**In scope** — every decision recorded below.

## Decisions Made

| slug_id | Area | Decision | Rationale |
|---------|------|----------|-----------|
| `data-pipeline-delivery` | routing | no | Route=application: no data signals, agentic app counter-signals present |
| `compliance-regimes` | Security & Compliance | `[on-prem]` | User selected on-premises only — consistent with cloud-vs-local=local; local developer tool, no cloud deployment |
| `docker-installed` | Infrastructure | no | No container runtime — this is a local Python CLI tool; no containerisation needed |
| `technical-archetype` | Domain & Archetype | `[ai-applications]` | Confirmed: project is an agentic workflow coding assistant — ai-applications playbook applies |
| `business-domain` | Domain & Archetype | _(none)_ | No domain match: project is developer tooling (security hardening of a Python agentic app), not a financial-services use case |
| `security-gap-scope` | Scope & Prioritization | `[auth-outbound-calls, unit-tests-evals]` | User selected: auth for outbound calls and unit tests/evals. Deferred: safelist, check_env wiring, REQUIRED_ENV, browser isolation |
| `eval-suite-scope` | Agentic Safeguards | `unit-tests-golden-set` | pytest unit tests for execute_tool and _run_tool, plus a small golden input/expected-output set for run_command safety checks |
| `auth-outbound-approach` | Agentic Safeguards | `capability-scoped-per-tool` | Annotate each tool with allowed capabilities; validate capability before tool execution proceeds |
| `tester-iteration-cap` ⚡ | Agentic Safeguards | yes | Add MAX_ITERATIONS matching main agent (20); prevents runaway loop if model never stops calling tools |

## Pre-Resolved (brownfield / inferred)

| slug_id | Value | Source | Inferred? |
|---------|-------|--------|-----------|
| `data-pipeline-delivery` | no | inferred | From `knowledge/project-brief.md` — no ETL/migration signals |
| `cloud-vs-local` | local | codebase | From `.aah/codebase-intel/codebase-learning.md` — no server, no deployment config |
| `data-storage-present` | no | codebase | From `.aah/codebase-intel/codebase-learning.md` — in-memory only, no persistent store |
| `custom-ui-required` | no | codebase | From `.aah/codebase-intel/codebase-learning.md` — CLI scripts only, no HTTP server |

## Constraints & Compliance

Constraint gate: **PASS** (no blocking violations).

Compliance regime: **on-prem only** — the tool runs locally on developer machines; no cloud egress, no container runtime, no network-accessible service.

## Open Questions for Analysis

_None — resolved during discovery._

## Constraint Audit — Checks A-F

**Overall:** ✅ PASS
**Ran at:** 2026-11-24

| Check | Result | Detail |
|-------|--------|--------|
| A — Mandatory coverage | PASS | clean |
| B — Forbidden options | PASS | clean |
| C — Whitelist adherence | PASS | clean |
| D — Service scope | PASS | clean |
| E — Mandated options | PASS | clean |
| F — Elimination provenance | PASS | clean |

---

_Generated by /aah-discuss Step 10b from the slug registry + confirmed header.
Do not hand-edit — regenerate by re-running Step 10b._
