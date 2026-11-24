# AI Risk Classification Report — brownfield

**Classified:** 2026-11-24 | **Tool Type:** Client-facing | **Pipeline:** brownfield-app-dev / agentic-app

## Dimension Scores

| Dimension | Label | Rating | Score | Justification |
|-----------|-------|--------|-------|---------------|
| DIM-001 | Consequence Severity | **High** | 2 | A bad output could become visible outside Deloitte or the client (user confirmed) |
| DIM-002 | Intended Usage | **High** | 2 | Purpose-built developer tool — two specific-function agents, not a general-purpose assistant |
| DIM-003 | Autonomy | **Low** | 0 | Formal sign-off required after every individual AI output before the process continues |
| DIM-004 | Complexity | **High** | 2 | Both agents use a tool-calling agentic loop where Claude decides which tool to invoke at runtime |
| DIM-005 | Data Sensitivity | **High** | 2 | Processes data that identifies or could be linked back to a specific individual, client, or org (user confirmed) |
| DIM-006 | Authority & Interconnectivity | **Medium** | 1 | Authority: writes to local filesystem with approval (Medium); Interconnectivity: 2 Claude-based agents (Medium) |
| **Total** | | | **9 / 12** | |

## Overall Risk Band

| Band | Range | Result |
|------|-------|--------|
| Low | 0–3 | |
| Medium | 4–7 | |
| **High** | **8–12** | **✅ 9 — HIGH** |

## DIM-006 Sub-scores

| Sub-dimension | Rating | Score | Rationale |
|---------------|--------|-------|-----------|
| Authority | Medium | 1 | `write_file` and `run_command` act on a local developer filesystem — non-critical system with per-action developer approval |
| Interconnectivity | Medium | 1 | 2 Claude-based agents in the project (main agent + QA agent), each with its own agentic loop — 1–2 AI components = Medium |
| **DIM-006 (max)** | **Medium** | **1** | max(1, 1) = 1 |

## Risk Narrative

This brownfield security hardening project scores **High (9/12)**. The score is driven by four High-rated
dimensions: (1) outputs could reach external parties, (2) both agents are purpose-built tools with no
general-purpose flexibility, (4) both use full agentic tool-calling loops, and (5) the data processed
identifies real individuals or organizations. These are partially offset by **Low autonomy (DIM-003)**:
the developer formally approves every AI output before the pipeline proceeds, which is a meaningful
control. The DIM-006 score reflects moderate authority (local filesystem, non-critical) and two
independently operating AI agents.

The principal controls added by this PoC — capability-scoped authentication, iteration cap, and test
coverage — directly address the most exploitable pre-existing risks (R-001: no tool-level auth,
R-002: no regression detection, R-003: unbounded tester loop).

## Controls in Scope (this PoC)

| Risk | Control | Residual Band |
|------|---------|---------------|
| R-001: No tool-level authz | CAPABILITY_MAP + CapabilityError on undeclared cap | Medium |
| R-002: No unit tests or evals | pytest suite + golden set for run_command | Low |
| R-003: Tester iteration runaway | MAX_ITERATIONS = 20 in agentic_tester.py | Low |

## Deferred Controls

| Risk | Deferred Item |
|------|---------------|
| R-004: run_command blocklist bypassable | Safelist definition — out of PoC scope |
| R-005: check_env() not wired | Incremental env hardening — out of PoC scope |
| R-006: Browser globals not isolated | agentic_tester.py refactor — out of PoC scope |
