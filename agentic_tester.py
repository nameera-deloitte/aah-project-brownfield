"""
Agentic App Tester — sample/index.html
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Claude Opus 5.5 drives a Playwright browser to verify every behavior in the
catalog (.aah/knowledge/behavior-catalog.yaml):

  BC-001  Counter increments on each button click
  BC-002  Greeting form shows "Hello, <name>!" after submit
  BC-003  Form stacks vertically below 480-pixel viewport width

Usage:
  python agentic_tester.py

Requires:
  pip install anthropic playwright
  playwright install chromium
"""

import asyncio
import json
from pathlib import Path

import anthropic
from playwright.async_api import Browser, Page, async_playwright

# ── Shared state ──────────────────────────────────────────────────────────────
_browser: Browser | None = None
_page: Page | None = None
_results: list[dict] = []

# ── Tool schemas ──────────────────────────────────────────────────────────────
TOOLS: list[dict] = [
    {
        "name": "open_page",
        "description": (
            "Open an HTML file in a headless Chromium browser. "
            "Returns the page title and a summary of interactive elements found."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Absolute path to the HTML file (Windows backslashes are fine).",
                },
                "viewport_width": {
                    "type": "integer",
                    "description": "Initial viewport width in pixels. Default 1280.",
                },
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "click_button",
        "description": (
            "Click an element by CSS selector. "
            "Returns the new #count value if present, plus any visible #message text."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector to click."},
                "times": {
                    "type": "integer",
                    "description": "Number of successive clicks. Default 1.",
                },
            },
            "required": ["selector"],
        },
    },
    {
        "name": "fill_and_submit",
        "description": (
            "Fill an <input> and submit its parent form. "
            "Returns the text that appears in #message after submission."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "input_selector": {
                    "type": "string",
                    "description": "CSS selector for the <input> to fill.",
                },
                "value": {"type": "string", "description": "Text to type into the input."},
                "form_selector": {
                    "type": "string",
                    "description": "CSS selector for the <form> to submit.",
                },
            },
            "required": ["input_selector", "value", "form_selector"],
        },
    },
    {
        "name": "resize_viewport",
        "description": "Resize the browser viewport. Useful for testing responsive breakpoints.",
        "input_schema": {
            "type": "object",
            "properties": {
                "width": {"type": "integer", "description": "New viewport width in pixels."},
                "height": {
                    "type": "integer",
                    "description": "New viewport height in pixels. Default 800.",
                },
            },
            "required": ["width"],
        },
    },
    {
        "name": "get_computed_style",
        "description": "Return computed CSS property values for an element.",
        "input_schema": {
            "type": "object",
            "properties": {
                "selector": {"type": "string", "description": "CSS selector."},
                "properties": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "CSS property names to read, e.g. [\"flex-direction\", \"padding\"].",
                },
            },
            "required": ["selector", "properties"],
        },
    },
    {
        "name": "record_result",
        "description": (
            "Record a test pass/fail for one behavior-catalog item. "
            "Call this once per behavior after you have verified it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "test_id": {
                    "type": "string",
                    "description": "Behavior catalog ID, e.g. BC-001.",
                },
                "test_name": {"type": "string", "description": "Short human-readable test name."},
                "passed": {"type": "boolean", "description": "True if the behavior was verified."},
                "expected": {"type": "string", "description": "What the catalog says should happen."},
                "actual": {"type": "string", "description": "What was actually observed in the browser."},
            },
            "required": ["test_id", "test_name", "passed", "expected", "actual"],
        },
    },
]

# ── Tool executor ─────────────────────────────────────────────────────────────

async def _run_tool(name: str, inputs: dict) -> str:
    global _page

    if name == "open_page":
        path = inputs["file_path"].replace("\\", "/")
        width = inputs.get("viewport_width", 1280)
        await _page.set_viewport_size({"width": width, "height": 800})
        await _page.goto(f"file:///{path}")
        title = await _page.title()
        buttons = await _page.locator("button").all_text_contents()
        input_count = await _page.locator("input").count()
        form_count = await _page.locator("form").count()
        return json.dumps(
            {
                "title": title,
                "buttons": buttons,
                "input_count": input_count,
                "form_count": form_count,
            }
        )

    elif name == "click_button":
        selector = inputs["selector"]
        times = inputs.get("times", 1)
        for _ in range(times):
            await _page.click(selector)
        count_val = None
        try:
            count_val = await _page.inner_text("#count")
        except Exception:
            pass
        message_val = None
        try:
            message_val = await _page.inner_text("#message")
        except Exception:
            pass
        return json.dumps({"clicked_times": times, "count_text": count_val, "message_text": message_val})

    elif name == "fill_and_submit":
        await _page.fill(inputs["input_selector"], inputs["value"])
        await _page.locator(inputs["form_selector"]).press("Enter")
        await asyncio.sleep(0.1)
        message = ""
        try:
            message = await _page.inner_text("#message")
        except Exception as exc:
            message = f"error: {exc}"
        return json.dumps({"message_shown": message})

    elif name == "resize_viewport":
        width = inputs["width"]
        height = inputs.get("height", 800)
        await _page.set_viewport_size({"width": width, "height": height})
        return json.dumps({"viewport": {"width": width, "height": height}})

    elif name == "get_computed_style":
        selector = inputs["selector"]
        result: dict[str, str] = {}
        for prop in inputs["properties"]:
            val = await _page.evaluate(
                """([sel, p]) => {
                    const el = document.querySelector(sel);
                    return el ? window.getComputedStyle(el).getPropertyValue(p) : 'ELEMENT NOT FOUND';
                }""",
                [selector, prop],
            )
            result[prop] = val
        return json.dumps(result)

    elif name == "record_result":
        _results.append(inputs)
        return json.dumps({"status": "recorded", "test_id": inputs["test_id"]})

    return json.dumps({"error": f"unknown tool '{name}'"})


# ── Agent loop ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an autonomous QA agent. Your job is to test a web application using the browser tools provided.

The app is a single HTML page with three testable behaviors:

  BC-001  COUNTER — The "Click me" button increments a counter shown next to it.
           Start from 0. Click several times and confirm the number increases correctly.

  BC-002  GREETING — The form at the bottom accepts a name and shows "Hello, <name>!"
           after clicking "Say hello". The value must be trimmed (no leading/trailing spaces).

  BC-003  RESPONSIVE — Below a 480-pixel viewport width the greeting form changes from
           a horizontal row to a vertical stack (flex-direction becomes "column").

For each behavior:
  1. Use the browser tools to interact with the page.
  2. Verify the actual result matches the expected behavior.
  3. Call record_result with the pass/fail outcome.

After all three behaviors are tested, write a Markdown test report that includes:
  - A summary table (ID, Name, Status)
  - Pass/fail counts
  - Brief notes for any failures
"""


async def run(html_path: str) -> None:
    global _browser, _page

    client = anthropic.AsyncAnthropic()

    async with async_playwright() as pw:
        _browser = await pw.chromium.launch(headless=True)
        _page = await _browser.new_page()

        messages: list[dict] = [
            {
                "role": "user",
                "content": (
                    f"Please test the app located at:\n{html_path}\n\n"
                    "Open the page, test all three behaviors (BC-001, BC-002, BC-003), "
                    "record each result, and then write the final test report."
                ),
            }
        ]

        _banner("AGENTIC APP TESTER")
        print(f"  File : {html_path}")
        print(f"  Model: claude-opus-5-5  (Opus 5.5 with adaptive thinking)\n")

        while True:
            response = await client.messages.create(
                model="claude-opus-5-5",
                max_tokens=16000,
                thinking={"type": "adaptive", "display": "summarized"},
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            # Show thinking summaries
            for block in response.content:
                if block.type == "thinking" and getattr(block, "thinking", None):
                    _section("Agent reasoning")
                    print(block.thinking)

            # Show text output
            for block in response.content:
                if block.type == "text":
                    _section("Agent output")
                    print(block.text)

            # Append assistant turn
            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                break

            # Execute tool calls, collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n  → {block.name}({json.dumps(block.input, ensure_ascii=False)})")
                    result_str = await _run_tool(block.name, block.input)
                    print(f"    ← {result_str}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        }
                    )

            messages.append({"role": "user", "content": tool_results})

        await _browser.close()

    # Print machine-readable summary
    _banner("TEST RESULTS SUMMARY")
    passed = sum(1 for r in _results if r["passed"])
    failed = len(_results) - passed
    print(f"  Total {len(_results)}  |  Passed {passed}  |  Failed {failed}\n")
    for r in _results:
        icon = "✓" if r["passed"] else "✗"
        print(f"  {icon} [{r['test_id']}]  {r['test_name']}")
        if not r["passed"]:
            print(f"       expected : {r['expected']}")
            print(f"       actual   : {r['actual']}")
    print()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _banner(title: str) -> None:
    print("\n" + "═" * 60)
    print(f"  {title}")
    print("═" * 60 + "\n")


def _section(title: str) -> None:
    print(f"\n── {title} " + "─" * max(0, 50 - len(title)))


if __name__ == "__main__":
    html_path = str(Path(__file__).parent / "sample" / "index.html")
    asyncio.run(run(html_path))
