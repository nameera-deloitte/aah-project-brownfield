## Id
- F-MOD-001

## Title
- Capability-Scoped Auth Gate for Agent Tools

## Module Ref
- MOD-001

## Description
MOD-001 is a purely additive security-hardening patch to two existing Python CLI agents. It annotates
all 11 tool calls with a `CAPABILITY_MAP` constant, inserts a pre-dispatch capability check inside
both `execute_tool()` (`agentic_app.py:142`) and `_run_tool()` (`agentic_tester.py:150`), introduces
a `CapabilityError` custom exception raised on blocked calls, and adds `MAX_ITERATIONS = 20` to
`agentic_tester.py` to match the main agent's pre-existing iteration cap. The stack is Python 3.12
with the `anthropic` SDK; no new third-party dependencies are introduced. Changes are confined to
`agentic_app.py` and `agentic_tester.py` as additive patches — no rewrite.

Refer to these architecture sources for normative detail:

- `.aah/architecture/agent-topology.md` — Agent Profiles (executor entry points, loop style,
  iteration cap) and Capability Map table (the definitive tool-to-capability mapping for all 11 tools).
- `.aah/architecture/data-model.md` — `CAPABILITY_MAP` and `CapabilityError` data structure
  definitions; capability check data-flow diagram showing how `CapabilityError` feeds back into the
  `tool_result` path.
- `.aah/architecture/application-flow.md` — Tool-Calling Loop with Capability Validation sequence
  diagram; happy-path, blocked-path, and iteration-cap-path variants; QA Agent Differences table.
- `.aah/architecture/architecture-overview.md` — Security Controls layer, full Architecture Diagram,
  and Constraints section (explicitly deferred items: `run_command` safelist, `check_env()` wiring,
  `REQUIRED_ENV` hardening, browser state isolation).

The 5 main-agent tools and their capability strings (from `.aah/architecture/agent-topology.md`
Capability Map table): `read_file → ["filesystem.read"]`, `list_files → ["filesystem.read"]`,
`run_command → ["shell.exec"]`, `write_file → ["filesystem.write"]`,
`search_in_file → ["filesystem.read"]`.

The 6 QA-agent tools and their capability strings: `open_page → ["browser.navigate"]`,
`click_button → ["browser.interact"]`, `fill_and_submit → ["browser.interact", "browser.submit"]`,
`resize_viewport → ["browser.viewport"]`, `get_computed_style → ["browser.read"]`,
`record_result → ["memory.write"]`.

**Behavioral expectations:**

- Given `agentic_app` is imported, when `CAPABILITY_MAP` is accessed at module level, then it is a
  `dict[str, list[str]]` with exactly 5 entries — `read_file`, `list_files`, `run_command`,
  `write_file`, `search_in_file` — each mapped to the capability strings shown in the Capability Map
  table of `.aah/architecture/agent-topology.md`; `len(CAPABILITY_MAP) == 5` is true.
- Given `agentic_tester` is imported, when `CAPABILITY_MAP` is accessed at module level, then it is a
  `dict[str, list[str]]` with exactly 6 entries — `open_page`, `click_button`, `fill_and_submit`,
  `resize_viewport`, `get_computed_style`, `record_result` — each mapped to the capability strings
  shown in the Capability Map table of `.aah/architecture/agent-topology.md`; `len(CAPABILITY_MAP) == 6`
  is true.
- Given `agentic_tester` is imported, when `MAX_ITERATIONS` is accessed at module level, then
  `MAX_ITERATIONS == 20` is true, matching the main agent's pre-existing cap per the QA Agent
  Differences table in `.aah/architecture/application-flow.md`.
- Given `execute_tool` is called with a tool name whose `CAPABILITY_MAP` entry covers the requested
  operation, when the pre-dispatch capability check passes, then the existing tool implementation
  executes and returns the same result string as the pre-patch code — no behavior regression for
  allowed calls.
- Given `execute_tool` is called with a tool name whose `CAPABILITY_MAP` entry does not cover the
  requested operation (e.g. `write_file` with `filesystem.write` blocked), when the pre-dispatch
  check fails, then `CapabilityError` is raised before the tool implementation runs and before any
  filesystem or subprocess action occurs.
- Given `_run_tool` is called (async) with a tool name whose `CAPABILITY_MAP` entry covers the
  requested operation, when the pre-dispatch capability check passes, then the existing async browser
  tool implementation executes and returns the same JSON-encoded result string as the pre-patch code.
- Given `_run_tool` is called (async) with a tool name whose `CAPABILITY_MAP` entry does not cover
  the requested operation (e.g. `open_page` with `browser.navigate` blocked), when the pre-dispatch
  check fails, then `CapabilityError` is raised before the browser implementation runs.
- Given `CapabilityError` is instantiated with a message string, when it is raised and caught, then
  it is a subclass of `Exception`, and both `str(err)` and `err.args[0]` return the original
  message; the calling agent loop can use that message as `tool_result` content so the loop continues
  without crashing, as described in the blocked-path flow in `.aah/architecture/application-flow.md`.
- Given `agentic_tester.py`'s async `run` loop, when the iteration counter reaches `MAX_ITERATIONS`
  (20) before `stop_reason == "end_turn"`, then the while loop exits cleanly, `_results` are printed
  to stdout, and no unhandled exception is raised — mirroring the iteration-cap path described in
  `.aah/architecture/application-flow.md`.
- Given all 5 tools in `agentic_app.py` are called through `execute_tool` with inputs that pass the
  capability check, when each runs against its pre-existing implementation, then each returns the same
  result as the pre-patch code; the capability-auth patch introduces no behavior regression on the
  allowed path.
- Given all 6 browser tools in `agentic_tester.py` are called through `_run_tool` (async) with
  inputs that pass the capability check, when each runs against its pre-existing implementation, then
  each returns the same JSON-encoded result as the pre-patch code; no behavior regression on the
  allowed path.
- Given the project is configured for first use, when `.env.example` is inspected, then it contains
  an entry for `ANTHROPIC_API_KEY` with a placeholder value (the `check_env()` startup wiring is
  explicitly deferred per `.aah/architecture/architecture-overview.md` Constraints and is not in
  scope for this module).

## Layers
- agent
- tools

## Dependencies
- F-MOD-000

## Lint Config

## Constraints

## Required Env Variables
- ANTHROPIC_API_KEY — Anthropic API key consumed by both agents at inference time via the Anthropic SDK

## Existing Code Touched
| file | current responsibility | action | why |
|------|----------------------|--------|-----|
| agentic_app.py | Synchronous main agent: 5-tool filesystem/shell executor (`execute_tool` at line 142), tool-calling loop (`run_agent` at line 241), pre-existing `MAX_ITERATIONS = 20`; no `CAPABILITY_MAP` or `CapabilityError` present | extend | Confirmed by reading lines 37–221: `TOOLS` list at line 37 defines 5 tool schemas; `execute_tool` at line 142 dispatches by tool name with no pre-dispatch capability check; `CAPABILITY_MAP` is absent; this module adds `CAPABILITY_MAP` and inserts the capability check before dispatch |
| agentic_tester.py | Async QA agent: 6-tool browser executor (`_run_tool` at line 150), async tool-calling loop (`run` at line 253) with an unbounded `while True`; no `CAPABILITY_MAP`, no `CapabilityError`, no `MAX_ITERATIONS` | extend | Confirmed by reading lines 32–223: `TOOLS` list at line 32 defines 6 browser tool schemas; `_run_tool` at line 150 dispatches by tool name with no pre-dispatch capability check; `CAPABILITY_MAP` and `MAX_ITERATIONS` are both absent; this module adds all three |

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
done
