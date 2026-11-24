# Agent Topology — brownfield

## Overview

Two independent single-file Python agents, each a self-contained tool-calling loop backed by
`claude-opus-5-5`. Neither agent orchestrates the other. This PoC adds a shared
`CAPABILITY_MAP` security layer to both agents' executors and brings the QA agent's iteration
guard in line with the main agent.

## Agent Topology Diagram

```mermaid
graph TB
    subgraph "Main Agent"
        A1[run_agent<br/>sync · MAX_ITERATIONS=20]
        A1EXEC[execute_tool<br/>CapabilityGuard]
        A1CAPS[filesystem.read · filesystem.write<br/>shell.exec]
    end

    subgraph "QA Agent"
        A2[run<br/>async · MAX_ITERATIONS=20]
        A2EXEC[_run_tool<br/>CapabilityGuard]
        A2CAPS[browser.navigate · browser.interact<br/>browser.viewport · browser.read · memory.write]
    end

    subgraph "Security Gate"
        CAPMAP[CAPABILITY_MAP<br/>11 tools annotated]
        CAPERR[CapabilityError<br/>blocked on violation]
    end

    CLAUDE[Anthropic API<br/>claude-opus-5-5]
    FS[(Project Filesystem)]
    BROWSER[Chromium<br/>Playwright]

    A1 <-->|inference| CLAUDE
    A1 --> A1EXEC
    A1EXEC -->|validate caps| CAPMAP
    CAPMAP -->|blocks| CAPERR
    A1EXEC --> A1CAPS
    A1CAPS --> FS

    A2 <-->|inference| CLAUDE
    A2 --> A2EXEC
    A2EXEC -->|validate caps| CAPMAP
    A2EXEC --> A2CAPS
    A2CAPS --> BROWSER

    classDef agent fill:#dbeafe,stroke:#2563eb
    classDef security fill:#fef3c7,stroke:#d97706
    classDef external fill:#f1f5f9,stroke:#64748b
    class A1,A1EXEC,A1CAPS,A2,A2EXEC,A2CAPS agent
    class CAPMAP,CAPERR security
    class CLAUDE,FS,BROWSER external
```

## Agent Profiles

### Agent 1 — `agentic_app.py`

| Property | Value |
|----------|-------|
| Entry point | `run_agent(user_task: str) → str` |
| Loop style | Synchronous (`Anthropic` client) |
| Iteration cap | `MAX_ITERATIONS = 20` (pre-existing) |
| Model | `claude-opus-5-5`, adaptive thinking |
| Tool count | 5 |
| Capability classes | `filesystem.read`, `filesystem.write`, `shell.exec` |
| Executor | `execute_tool(name, inputs) → str` at line 142 |
| Safety boundary | `run_command` keyword blocklist (pre-existing; safelist deferred) |

### Agent 2 — `agentic_tester.py`

| Property | Value |
|----------|-------|
| Entry point | `run(html_path: str) → None` (async) |
| Loop style | Asynchronous (`AsyncAnthropic` client + `asyncio`) |
| Iteration cap | `MAX_ITERATIONS = 20` (added by this PoC) |
| Model | `claude-opus-5-5`, adaptive thinking |
| Tool count | 6 |
| Capability classes | `browser.navigate`, `browser.interact`, `browser.viewport`, `browser.read`, `memory.write` |
| Executor | `_run_tool(name, inputs) → str` (async) at line 150 |
| Browser state | Module-level `_browser` / `_page` globals (isolation deferred) |

## Capability Map

| Tool | Agent | Allowed Capabilities |
|------|-------|---------------------|
| `read_file` | Main | `filesystem.read` |
| `list_files` | Main | `filesystem.read` |
| `run_command` | Main | `shell.exec` |
| `write_file` | Main | `filesystem.write` |
| `search_in_file` | Main | `filesystem.read` |
| `open_page` | QA | `browser.navigate` |
| `click_button` | QA | `browser.interact` |
| `fill_and_submit` | QA | `browser.interact`, `browser.submit` |
| `resize_viewport` | QA | `browser.viewport` |
| `get_computed_style` | QA | `browser.read` |
| `record_result` | QA | `memory.write` |

## Deferred Agent Concerns

The following concerns were identified during the discuss phase but are out of PoC scope:

| Concern | Location | Reason Deferred |
|---------|----------|----------------|
| `run_command` safelist | `agentic_app.py:172` | Requires safelist definition + user approval of allowed commands |
| `check_env()` wiring | Both agents | Incremental; not a functional blocker for capability auth |
| `REQUIRED_ENV` hardening | `config/env_check.py` | Same as above |
| Browser state isolation | `agentic_tester.py:27–29` | Requires refactor of module-level globals; out of PoC scope |

## Provenance

| Section | Origin | Source |
|---------|--------|--------|
| Overview | Authored | `.aah/codebase-intel/codebase-learning.md §3`, `decision-registry.yaml → tester-iteration-cap` |
| Agent Topology Diagram | Authored | `agentic_app.py:30–138`, `agentic_tester.py:32–146`, `decision-registry.yaml → auth-outbound-approach` |
| Agent Profiles | Authored | `.aah/codebase-intel/codebase-learning.md §7`, `agentic_app.py:30–34`, `agentic_tester.py:27–30` |
| Capability Map | Authored | `agentic_app.py:37–138`, `agentic_tester.py:32–146`, `discuss-prd.md §Solution` |
| Deferred Agent Concerns | Inherited | `discuss-prd.md §Deferred`, `.aah/codebase-intel/codebase-learning.md §11` |
