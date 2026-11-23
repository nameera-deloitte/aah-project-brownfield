# Module Dependencies

## Overview

Three independent modules; no internal cross-imports. `config/env_check.py` exists as a standalone helper that neither agent imports yet — it is wired by convention (call `check_env()` at the entrypoint), not by import.

## Dependency Graph

```mermaid
graph LR
    subgraph "Internal Modules"
        APP[agentic_app.py]
        TESTER[agentic_tester.py]
        CFG[config/env_check.py]
    end

    subgraph "External"
        ANTHROPIC[anthropic]
        PLAYWRIGHT[playwright.async_api]
        PATHLIB[pathlib]
        JSON[json]
        OS[os]
        SUBPROCESS[subprocess]
        ASYNCIO[asyncio]
        SYS[sys]
    end

    APP --> ANTHROPIC
    APP --> PATHLIB
    APP --> JSON
    APP --> OS
    APP --> SUBPROCESS

    TESTER --> ANTHROPIC
    TESTER --> PLAYWRIGHT
    TESTER --> PATHLIB
    TESTER --> JSON
    TESTER --> ASYNCIO

    CFG --> PATHLIB
    CFG --> OS
    CFG --> SYS
```

## Coupling Analysis

| Module | Fan-In | Fan-Out | Assessment |
|--------|--------|---------|------------|
| `agentic_app.py` | 0 (entry point) | 5 | Independent; safe to modify |
| `agentic_tester.py` | 0 (entry point) | 5 | Independent; safe to modify |
| `config/env_check.py` | 0 (not yet imported) | 3 | Standalone utility; wired by convention |

## Circular Dependencies

None detected.
