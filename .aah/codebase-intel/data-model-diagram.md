# Data Model

## Overview

No persistent data storage. All state is in-memory and per-run. The two notable runtime data structures are the Claude messages conversation list (shared across iterations) and the QA test results list.

## Entity Relationship Diagram

```mermaid
classDiagram
    class Message {
        +str role
        +list~ContentBlock~ content
    }
    class ToolResult {
        +str type
        +str tool_use_id
        +str content
    }
    class TestResult {
        +str test_id
        +str test_name
        +bool passed
        +str expected
        +str actual
    }
    class ToolDefinition {
        +str name
        +str description
        +dict input_schema
    }

    Message "1..*" --> "0..*" ToolResult : contains in user turn
    TestResult "*" --* "_results list" : accumulated in
    ToolDefinition "*" --* "TOOLS const" : defined in
```

## Key Entities

| Entity | Purpose | Key Fields | Relationships |
|--------|---------|------------|---------------|
| `Message` | Claude conversation turn | `role` (user/assistant), `content` (list of blocks) | Accumulated in `messages` list per run |
| `ToolResult` | Result of one tool call | `type`, `tool_use_id`, `content` (string) | Returned to Claude in next user turn |
| `TestResult` | QA outcome for one behavior | `test_id`, `test_name`, `passed`, `expected`, `actual` | Accumulated in module-global `_results` list |
| `ToolDefinition` | Tool schema sent to Claude | `name`, `description`, `input_schema` | Defined as `TOOLS` constant; never mutated at runtime |

## Data Stores

| Store | Type | Purpose |
|-------|------|---------|
| In-memory `messages` list | Python list | Conversation history per `run_agent` / `run` call; not persisted |
| Module-global `_results` | Python list | QA test results during `agentic_tester.py` run; not persisted |
| Local filesystem | OS files | Only data store written to: `write_file` tool in `agentic_app.py` |
