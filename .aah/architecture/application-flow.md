# Application Flow — brownfield

## Overview

Both agents follow the same standard Claude tool-calling loop: build a messages list, call
`messages.create`, dispatch any `tool_use` blocks through the capability-validated executor,
append results, and repeat until `stop_reason == "end_turn"` or `MAX_ITERATIONS` is reached.
The sequence below shows the main agent's flow; the QA agent's async flow is identical in
structure, with `_run_tool` and `MAX_ITERATIONS = 20` in place of `execute_tool`.

## Tool-Calling Loop with Capability Validation

```mermaid
sequenceDiagram
    autonumber
    participant DEV as Developer
    participant LOOP as run_agent
    participant CAPMAP as CAPABILITY_MAP
    participant CLAUDE as Anthropic API
    participant TOOL as Tool Implementation

    DEV->>LOOP: run_agent(user_task)

    loop up to MAX_ITERATIONS (20)
        LOOP->>CLAUDE: messages.create(tools, messages)
        CLAUDE-->>LOOP: response

        alt stop_reason == end_turn
            LOOP-->>DEV: final text answer
        else stop_reason == tool_use
            LOOP->>CAPMAP: execute_tool(name, inputs)

            alt capability blocked
                CAPMAP-->>LOOP: CapabilityError
                LOOP->>LOOP: append error as tool_result
            else capability allowed
                CAPMAP->>TOOL: dispatch to implementation
                TOOL-->>CAPMAP: result string
                CAPMAP-->>LOOP: result string
                LOOP->>LOOP: append result as tool_result
            end
        end
    end

    Note over LOOP,CLAUDE: Loop exits on end_turn or MAX_ITERATIONS reached
```

## Flow Variants

### Happy path — tool call succeeds
1. Claude returns a `tool_use` block.
2. `execute_tool` looks up the tool name in `CAPABILITY_MAP` — capability is in the allow-list.
3. Tool implementation runs (e.g. `read_file` reads from filesystem).
4. Result string appended to `messages` as `tool_result`.
5. Loop continues.

### Blocked path — capability violation
1. Claude requests a tool call.
2. `execute_tool` finds the tool's declared capabilities do not cover the requested operation.
3. `CapabilityError` raised; its message returned as `tool_result` content.
4. Claude sees the error and either tries a different tool or ends the turn.

### Iteration cap path — runaway guard
1. Loop counter reaches `MAX_ITERATIONS` (20).
2. Loop exits regardless of `stop_reason`.
3. Last accumulated response returned to caller.

## QA Agent Differences

| Aspect | Main Agent (`agentic_app.py`) | QA Agent (`agentic_tester.py`) |
|--------|-------------------------------|--------------------------------|
| Executor | `execute_tool` (sync) | `_run_tool` (async) |
| Iteration cap | Pre-existing `MAX_ITERATIONS = 20` | Added by this PoC: `MAX_ITERATIONS = 20` |
| Tools | 5 filesystem/shell tools | 6 Playwright browser tools |
| Final output | Returns string to caller | Prints `_results` to stdout |

## Provenance

| Section | Origin | Source |
|---------|--------|--------|
| Overview | Authored | `.aah/codebase-intel/codebase-learning.md §3` |
| Tool-Calling Loop diagram | Authored | `agentic_app.py:241–300`, `decision-registry.yaml → auth-outbound-approach`, `decision-registry.yaml → tester-iteration-cap` |
| Flow Variants | Authored | `agentic_app.py:142–218`, `discuss-prd.md §Solution` |
| QA Agent Differences table | Authored | `agentic_tester.py:150–240`, `decision-registry.yaml → tester-iteration-cap` |
