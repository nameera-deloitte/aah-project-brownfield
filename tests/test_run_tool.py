"""F-MOD-002: Async unit tests for _run_tool() in agentic_tester.py.

Covers:
  (a) Capability validation — CapabilityError raised for unknown tool names.
  (b) open_page — dispatches to _page.goto with file:/// URL and returns JSON
      with keys: title, buttons, input_count, form_count.
  (c) record_result — appends to agentic_tester._results and returns a
      non-error success string.

Uses the mock_page fixture from tests/conftest.py (AsyncMock Playwright page).
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

# ── (a) Capability validation ─────────────────────────────────────────────────


async def test_F_MOD_002_run_tool_capability_error():
    """CapabilityError is raised when tool name is not in CAPABILITY_MAP."""
    import agentic_tester

    with pytest.raises(agentic_tester.CapabilityError):
        await agentic_tester._run_tool("nonexistent_tool_xyz", {})


# ── (b) open_page ─────────────────────────────────────────────────────────────


async def test_F_MOD_002_run_tool_open_page(mock_page):
    """open_page calls _page.goto with a file:/// URL and returns JSON with the four required keys."""
    import agentic_tester

    # Configure the mock page so open_page can complete without errors.
    mock_page.title = AsyncMock(return_value="Sample Page")

    # locator("button").all_text_contents() and locator(...).count() must be awaitable.
    loc_mock = MagicMock()
    loc_mock.all_text_contents = AsyncMock(return_value=["Click me"])
    loc_mock.count = AsyncMock(return_value=1)
    mock_page.locator = MagicMock(return_value=loc_mock)

    # Redirect agentic_tester._page to our mock
    orig_page = agentic_tester._page
    agentic_tester._page = mock_page
    try:
        result = await agentic_tester._run_tool(
            "open_page", {"file_path": "/tmp/index.html"}
        )
    finally:
        agentic_tester._page = orig_page

    # Result must be valid JSON
    data = json.loads(result)

    # Must contain all four required keys
    assert "title" in data, "open_page JSON must include 'title'"
    assert "buttons" in data, "open_page JSON must include 'buttons'"
    assert "input_count" in data, "open_page JSON must include 'input_count'"
    assert "form_count" in data, "open_page JSON must include 'form_count'"

    # goto must have been called with a file:/// URL
    mock_page.goto.assert_awaited_once()
    goto_url = mock_page.goto.call_args[0][0]
    assert goto_url.startswith("file:///"), (
        f"_page.goto must be called with a file:/// URL, got {goto_url!r}"
    )


# ── (c) record_result ─────────────────────────────────────────────────────────


async def test_F_MOD_002_run_tool_record_result():
    """record_result appends the entry to agentic_tester._results and returns a non-error string."""
    import agentic_tester

    orig_results = list(agentic_tester._results)
    agentic_tester._results.clear()
    try:
        payload = {
            "test_id": "T1",
            "test_name": "example",
            "passed": True,
            "expected": "x",
            "actual": "x",
        }
        result = await agentic_tester._run_tool("record_result", payload)

        # Must be a valid JSON string and not an error
        assert isinstance(result, str)
        assert result
        parsed = json.loads(result)
        # The implementation returns {"status": "recorded", "test_id": ...}
        assert parsed.get("status") == "recorded"

        # The entry must have been appended to _results
        assert len(agentic_tester._results) == 1
        assert agentic_tester._results[0] == payload
    finally:
        agentic_tester._results[:] = orig_results
