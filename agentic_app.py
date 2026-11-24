"""
agentic_app.py — Claude-Powered Agentic Application
=====================================================
Use case: A multi-turn AI assistant that autonomously:
  1. Reads files from the project directory
  2. Runs shell commands to gather information
  3. Analyzes code and answers questions
  4. Writes summaries or test plans as files

The agent loop continues until Claude stops calling tools and
returns a final answer.

Requirements:
  pip install anthropic

Run:
  set ANTHROPIC_API_KEY=sk-ant-...
  python agentic_app.py
"""

import json
import os
import subprocess
from pathlib import Path

import anthropic

# ─── Configuration ────────────────────────────────────────────────────────────

MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000
PROJECT_ROOT = Path(__file__).parent           # working directory for tools
MAX_ITERATIONS = 20                            # safety cap on the agent loop

# ─── Capability Gate ──────────────────────────────────────────────────────────


class CapabilityError(Exception):
    """Raised when a tool call is not covered by the agent's capability map."""


CAPABILITY_MAP: dict[str, list[str]] = {
    "read_file": ["filesystem.read"],
    "list_files": ["filesystem.read"],
    "run_command": ["shell.exec"],
    "write_file": ["filesystem.write"],
    "search_in_file": ["filesystem.read"],
}

# ─── Tool Definitions ─────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "read_file",
        "description": (
            "Read the full text content of a file inside the project. "
            "Returns the file contents as a string."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "File path relative to the project root, e.g. 'sample/index.html'."
                    ),
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": (
            "List files and directories inside a folder of the project. "
            "Returns a JSON array of names."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": (
                        "Directory path relative to project root. "
                        "Use '.' for the root itself."
                    ),
                }
            },
            "required": ["directory"],
        },
    },
    {
        "name": "run_command",
        "description": (
            "Run a shell command inside the project root and return stdout + stderr. "
            "Use only safe, read-only commands such as: "
            "python --version, pip show <pkg>, git log --oneline -5, dir, ls."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute, e.g. 'python --version'.",
                }
            },
            "required": ["command"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write text content to a file in the project. "
            "Creates the file if it does not exist, overwrites if it does. "
            "Use this to save summaries, reports, or test plans."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Destination file path relative to project root.",
                },
                "content": {
                    "type": "string",
                    "description": "Full text content to write into the file.",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "search_in_file",
        "description": (
            "Search for a keyword or phrase inside a file. "
            "Returns all matching lines with their line numbers."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to project root.",
                },
                "keyword": {
                    "type": "string",
                    "description": "Text to search for (case-insensitive).",
                },
            },
            "required": ["path", "keyword"],
        },
    },
]

# ─── Tool Executor ────────────────────────────────────────────────────────────

def execute_tool(name: str, inputs: dict) -> str:
    """Run a tool and return its result as a string."""

    # Pre-dispatch capability check
    if name not in CAPABILITY_MAP:
        raise CapabilityError(
            f"Tool '{name}' is not in the capability map and cannot be dispatched."
        )

    if name == "read_file":
        file_path = PROJECT_ROOT / inputs["path"]
        try:
            return file_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return f"ERROR: File not found: {inputs['path']}"
        except Exception as exc:
            return f"ERROR: {exc}"

    elif name == "list_files":
        dir_path = PROJECT_ROOT / inputs["directory"]
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name))
            result = [
                {"name": e.name, "type": "dir" if e.is_dir() else "file"}
                for e in entries
                if not e.name.startswith(".")
            ]
            return json.dumps(result, indent=2)
        except FileNotFoundError:
            return f"ERROR: Directory not found: {inputs['directory']}"
        except Exception as exc:
            return f"ERROR: {exc}"

    elif name == "run_command":
        command = inputs["command"]
        # Safety: reject dangerous keywords
        blocked = ["rm ", "del ", "format ", "mkfs", "sudo", "shutdown", ":(){"]
        for word in blocked:
            if word in command.lower():
                return f"BLOCKED: Command contains a disallowed keyword '{word}'."
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(PROJECT_ROOT),
                timeout=15,
            )
            output = result.stdout or ""
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            return output.strip() or "(no output)"
        except subprocess.TimeoutExpired:
            return "ERROR: Command timed out after 15 seconds."
        except Exception as exc:
            return f"ERROR: {exc}"

    elif name == "write_file":
        file_path = PROJECT_ROOT / inputs["path"]
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(inputs["content"], encoding="utf-8")
            return f"OK: Written {len(inputs['content'])} characters to '{inputs['path']}'."
        except Exception as exc:
            return f"ERROR: {exc}"

    elif name == "search_in_file":
        file_path = PROJECT_ROOT / inputs["path"]
        keyword = inputs["keyword"].lower()
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            matches = [
                {"line": i + 1, "text": line}
                for i, line in enumerate(lines)
                if keyword in line.lower()
            ]
            if not matches:
                return f"No matches found for '{inputs['keyword']}' in '{inputs['path']}'."
            return json.dumps(matches, indent=2)
        except FileNotFoundError:
            return f"ERROR: File not found: {inputs['path']}"
        except Exception as exc:
            return f"ERROR: {exc}"

    return f"ERROR: Unknown tool '{name}'"


# ─── Agentic Loop ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful AI coding assistant with access to the project file system.
You can read files, list directories, run safe shell commands, write files, and search within files.

When given a task:
1. Explore the project structure to understand the codebase.
2. Read relevant files to gather the information you need.
3. Use run_command to check the environment if necessary.
4. Synthesize your findings and write a report or answer the user's question.
5. If asked to produce a document, use write_file to save it.

Always explain what you are doing before calling a tool.
When you have fully answered the question, stop calling tools and give a clear final answer.
"""


def run_agent(user_task: str) -> str:
    """
    Run the agentic loop for a given user task.
    Returns the final text answer from Claude.
    """
    client = anthropic.Anthropic()

    messages: list[dict] = [{"role": "user", "content": user_task}]

    _banner("AGENTIC APP  —  Claude Opus 5.5")
    _log("Task", user_task)

    final_answer = ""

    for iteration in range(1, MAX_ITERATIONS + 1):
        _divider(f"Iteration {iteration}")

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive", "display": "summarized"},
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # Print any thinking summary
        for block in response.content:
            if block.type == "thinking" and getattr(block, "thinking", ""):
                _log("Thinking", block.thinking)

        # Print text blocks
        for block in response.content:
            if block.type == "text":
                _log("Claude", block.text)
                final_answer = block.text

        # Append assistant turn to history
        messages.append({"role": "assistant", "content": response.content})

        # Stop if no more tool calls
        if response.stop_reason != "tool_use":
            break

        # Execute all tool calls and collect results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\n  ▶ {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                result = execute_tool(block.name, block.input)
                # Truncate very long results so they don't flood the terminal
                display = result if len(result) <= 400 else result[:400] + "\n  ... (truncated)"
                print(f"  ◀ {display}")
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    }
                )

        messages.append({"role": "user", "content": tool_results})

    else:
        print(f"\n[Warning] Reached maximum iterations ({MAX_ITERATIONS}).")

    return final_answer


# ─── Helper Printers ──────────────────────────────────────────────────────────

def _banner(title: str) -> None:
    print("\n" + "═" * 65)
    print(f"  {title}")
    print("═" * 65)


def _divider(label: str) -> None:
    print(f"\n{'─' * 20}  {label}  {'─' * 20}")


def _log(label: str, text: str) -> None:
    print(f"\n[{label}]\n{text}")


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── Example tasks — change any of these to try different use cases ──────
    tasks = [
        # Task 1: Explore and summarize the project
        (
            "Explore this project directory. "
            "List the top-level files and folders, read the main HTML file, "
            "and give me a 3-bullet summary of what this app does."
        ),

        # Task 2: Analyze and write a report
        # (
        #     "Read sample/index.html and the behavior catalog at "
        #     ".aah/knowledge/behavior-catalog.yaml. "
        #     "Then write a Markdown test plan to 'test_plan.md' that maps "
        #     "each catalog behavior to a concrete manual test step."
        # ),

        # Task 3: Check environment
        # (
        #     "Check whether Python and pip are installed, then list the "
        #     "installed packages. Tell me if 'playwright' and 'anthropic' "
        #     "are present."
        # ),
    ]

    # Run the first task
    answer = run_agent(tasks[0])

    _banner("FINAL ANSWER")
    print(answer)
