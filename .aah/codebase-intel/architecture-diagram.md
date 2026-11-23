# System Architecture

## Overview

A two-agent Python application: one general-purpose AI coding assistant that operates on the local filesystem via tool-calling, and one autonomous QA agent that drives a headless browser to test a web application against a behavior catalog. Both agents use claude-opus-5-5 with adaptive thinking.

## Architecture Diagram

```mermaid
graph TB
    subgraph "External"
        ANTHROPIC[Anthropic API<br/>claude-opus-5-5]
        CHROMIUM[Headless Chromium<br/>Playwright]
        FS[Local Filesystem<br/>Project Root]
        ENV[Environment<br/>ANTHROPIC_API_KEY]
    end

    subgraph "Application Boundary"
        subgraph "Main Agent"
            APP[agentic_app.py<br/>run_agent]
            APP_TOOLS[Tool Executor<br/>execute_tool]
        end

        subgraph "QA Agent"
            TESTER[agentic_tester.py<br/>run async]
            TESTER_TOOLS[Browser Tool Executor<br/>_run_tool async]
        end

        subgraph "Config"
            ENV_CHECK[config/env_check.py<br/>check_env]
        end
    end

    USER([User / CLI]) -->|user_task str| APP
    USER -->|html_path str| TESTER

    APP -->|messages API + tools| ANTHROPIC
    ANTHROPIC -->|tool_use blocks| APP
    APP --> APP_TOOLS
    APP_TOOLS -->|read/write/list/run/search| FS

    TESTER -->|messages API + tools| ANTHROPIC
    ANTHROPIC -->|tool_use blocks| TESTER
    TESTER --> TESTER_TOOLS
    TESTER_TOOLS -->|page navigation + interaction| CHROMIUM
    CHROMIUM -->|DOM / CSS / events| TESTER_TOOLS

    ENV -->|os.environ| APP
    ENV -->|os.environ| TESTER
    ENV_CHECK -->|check_env| ENV
```

## Layer Summary

| Layer | Purpose | Key Components |
|-------|---------|----------------|
| External | Third-party services and OS resources | Anthropic API, Playwright Chromium, filesystem, env vars |
| Main Agent | Filesystem + shell task execution via LLM | `agentic_app.py`, `execute_tool` |
| QA Agent | Browser-based behavioral testing via LLM | `agentic_tester.py`, `_run_tool` |
| Config | Startup environment validation | `config/env_check.py` |

## External Integrations

- **Anthropic API** (`anthropic.Anthropic` / `anthropic.AsyncAnthropic`): both agents call `messages.create` with `tool_use` and `adaptive` thinking enabled. API key read from `ANTHROPIC_API_KEY`.
- **Playwright Chromium**: `agentic_tester.py` launches `chromium` headless via `async_playwright`. Browser state is shared across the entire test run via module-level globals `_browser` and `_page`.
- **Local filesystem**: `agentic_app.py` tools operate within `PROJECT_ROOT = Path(__file__).parent`.
