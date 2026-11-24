# Risk, Security & Compliance — brownfield

## Overview

This document records the security risks present in the existing codebase, the controls added
by this PoC, and the residual risks deferred to future iterations. Compliance regime: on-prem only.

## In-Scope Risks and Controls (this PoC)

| Risk ID | Risk | Severity (pre-PoC) | Control Added | Residual Risk |
|---------|------|-------------------|---------------|---------------|
| R-001 | No auth/authz for individual outbound tool calls beyond the shared API key — LLM can direct any tool regardless of intended scope | High | `CAPABILITY_MAP` annotates all 11 tools; `execute_tool` / `_run_tool` raise `CapabilityError` on undeclared capability | Medium — enforcement is code-level, not cryptographic; a code change to `CAPABILITY_MAP` bypasses it |
| R-002 | No unit tests or evals on the tool execution path — security regressions are undetected | High | pytest suite for `execute_tool` and `_run_tool`; parametrized golden set for `run_command` allow/block decisions | Low — coverage limited to unit level; no CI pipeline to enforce it automatically |
| R-003 | `agentic_tester.py` has no iteration cap — runaway loop possible if the model never stops calling tools | Medium | `MAX_ITERATIONS = 20` added, matching main agent policy | Low |

## Out-of-Scope Risks (deferred)

| Risk ID | Risk | Why Deferred |
|---------|------|--------------|
| R-004 | `run_command` uses a keyword denylist (blocklist) rather than a safelist — easily bypassed by slight command variants | Requires safelist definition + user approval of allowed commands; out of PoC scope |
| R-005 | `ANTHROPIC_API_KEY` not validated at startup via `check_env()`; `REQUIRED_ENV` tuple is empty | Incremental fix; not a functional blocker for capability auth PoC |
| R-006 | Module-level `_browser` / `_page` globals in `agentic_tester.py` are not safe for concurrent use | Requires refactor; out of PoC scope |

## Threat Model Notes

**Threat actor**: a prompt-injection payload embedded in a file the main agent reads, or in a web
page the QA agent visits, that attempts to redirect tool calls outside their declared purpose.

**Current (pre-PoC) exposure**: none of the 11 tools validates whether the LLM-requested action
is within the tool's intended scope. A prompt injection could, for example, direct `write_file`
to overwrite a system path.

**Post-PoC exposure**: each tool's declared capability envelope is enforced at the executor level.
An injected payload that requests an undeclared capability receives a `CapabilityError` result
rather than executing. The LLM cannot modify `CAPABILITY_MAP` at runtime (it is a module-level
constant with no tool that writes to it).

**Remaining gap**: the denylist in `run_command` (`agentic_app.py:172`) remains bypassable. This
is documented in R-004 above and is the highest-priority deferred risk.

## Compliance

| Regime | Status | Notes |
|--------|--------|-------|
| on-prem | ✅ Applies | Local Python CLI; no egress, no server, no container |
| HIPAA / SOC2 / GDPR / PCI-DSS | Not applicable | Developer tooling; no PII, no payment data |

## Provenance

| Section | Origin | Source |
|---------|--------|--------|
| In-Scope Risks and Controls | Authored | `discuss-prd.md §Problem Statement`, `decision-registry.yaml → security-gap-scope`, `decision-registry.yaml → auth-outbound-approach`, `decision-registry.yaml → tester-iteration-cap` |
| Out-of-Scope Risks | Inherited | `discuss-prd.md §Deferred`, `.aah/codebase-intel/codebase-learning.md §11` |
| Threat Model Notes | Authored | `agentic_app.py:142–192`, `discuss-prd.md §Solution` |
| Compliance | Inherited | `decision-registry.yaml → compliance-regimes` |
