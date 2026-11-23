# Data Flow

## Overview

Both agents follow the same agentic loop pattern: user input → Claude inference → tool execution → result back to Claude → repeat until `stop_reason != "tool_use"`. No queues, no databases, no async pipelines outside the browser test agent's Playwright I/O.

## Data Flow Diagram

```mermaid
flowchart TD
    A([User Task / html_path]) --> B[Build initial messages list]
    B --> C{Claude messages.create\nclaude-opus-5-5}
    C -->|stop_reason=tool_use| D[Extract tool_use blocks]
    C -->|stop_reason=end_turn| Z([Final text answer])
    D --> E{Route by tool name}
    E -->|read_file / write_file\nlist_files / search_in_file| F[Filesystem I/O\nPATH_ROOT]
    E -->|run_command| G[subprocess.run\nshell=True cwd=PROJECT_ROOT]
    E -->|open_page / click_button\nfill_and_submit / resize_viewport\nget_computed_style| H[Playwright\nHeadless Chromium]
    E -->|record_result| I[Append to _results list]
    F --> J[tool_result str]
    G --> J
    H --> J
    I --> J
    J --> K[Append tool_results to messages]
    K --> C
    Z --> L{agentic_tester only}
    L -->|yes| M[Print test summary\nfrom _results]
    L -->|no| N([Done])
    M --> N
```

## Data Pipelines

| Pipeline | Source | Processing | Destination |
|----------|--------|-----------|-------------|
| Main agent tool loop | User task string | Claude inference + tool dispatch (up to 20 iterations) | Final text printed to stdout; files written to PROJECT_ROOT |
| QA agent browser loop | HTML file path | Claude inference + Playwright tool dispatch | Test results accumulated in `_results`; summary printed to stdout |
| Environment check | `.env` file (optional) | Line-by-line KEY=value parse; os.environ patched | `os.environ` (non-overriding) |

## Integration Points

- **Inbound**: user-supplied task string (`run_agent`) or HTML file path (`run`); optional `.env` file loaded at startup via `config/env_check.py`.
- **Outbound**: Anthropic API (HTTPS to `api.anthropic.com`); local filesystem writes via `write_file` tool; Playwright opens local `file:///` URLs in Chromium.
- **Safety boundary**: `run_command` in `agentic_app.py` blocks a hardcoded list of destructive keywords (`rm `, `del `, `format `, `mkfs`, `sudo`, `shutdown`, `:(){`) before calling `subprocess.run`.
