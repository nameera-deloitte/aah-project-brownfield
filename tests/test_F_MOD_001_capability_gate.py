"""Tests for F-MOD-001: Capability-Scoped Auth Gate for Agent Tools.

Covers all 12 behavioral expectations from the feature spec.
Test names follow the pattern test_F_MOD_001_<short_description>.
"""

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent


# ── Slice 1: agentic_app.CAPABILITY_MAP ───────────────────────────────────────


def test_F_MOD_001_app_capability_map_entries():
    """CAPABILITY_MAP in agentic_app must have exactly 5 entries with correct mappings."""
    import agentic_app

    cap = agentic_app.CAPABILITY_MAP
    assert isinstance(cap, dict), "CAPABILITY_MAP must be a dict"
    assert len(cap) == 5, f"Expected 5 entries, got {len(cap)}"
    assert cap["read_file"] == ["filesystem.read"]
    assert cap["list_files"] == ["filesystem.read"]
    assert cap["run_command"] == ["shell.exec"]
    assert cap["write_file"] == ["filesystem.write"]
    assert cap["search_in_file"] == ["filesystem.read"]


# ── Slice 2: agentic_tester.CAPABILITY_MAP ────────────────────────────────────


def test_F_MOD_001_tester_capability_map_entries():
    """CAPABILITY_MAP in agentic_tester must have exactly 6 entries with correct mappings."""
    import agentic_tester

    cap = agentic_tester.CAPABILITY_MAP
    assert isinstance(cap, dict), "CAPABILITY_MAP must be a dict"
    assert len(cap) == 6, f"Expected 6 entries, got {len(cap)}"
    assert cap["open_page"] == ["browser.navigate"]
    assert cap["click_button"] == ["browser.interact"]
    assert cap["fill_and_submit"] == ["browser.interact", "browser.submit"]
    assert cap["resize_viewport"] == ["browser.viewport"]
    assert cap["get_computed_style"] == ["browser.read"]
    assert cap["record_result"] == ["memory.write"]


# ── Slice 3: agentic_tester.MAX_ITERATIONS ────────────────────────────────────


def test_F_MOD_001_tester_max_iterations():
    """MAX_ITERATIONS in agentic_tester must equal 20."""
    import agentic_tester

    assert agentic_tester.MAX_ITERATIONS == 20


# ── Slice 4: execute_tool allowed path ────────────────────────────────────────


def test_F_MOD_001_execute_tool_allowed_passes_through():
    """execute_tool for an allowed tool (list_files) must return a valid JSON list."""
    import agentic_app

    # list_files is in CAPABILITY_MAP — must not raise CapabilityError
    result = agentic_app.execute_tool("list_files", {"directory": "."})
    assert isinstance(result, str), "execute_tool must return a string"
    parsed = json.loads(result)
    assert isinstance(parsed, list)


# ── Slice 5: execute_tool blocked path ────────────────────────────────────────


def test_F_MOD_001_execute_tool_blocked_raises_capability_error():
    """execute_tool for a tool not in CAPABILITY_MAP must raise CapabilityError."""
    import agentic_app

    with pytest.raises(agentic_app.CapabilityError):
        agentic_app.execute_tool("unknown_tool_xyz", {"foo": "bar"})


# ── Slice 6: _run_tool allowed path ───────────────────────────────────────────


async def test_F_MOD_001_run_tool_allowed_passes_through():
    """_run_tool for record_result (in CAPABILITY_MAP, no _page needed) must return JSON."""
    import agentic_tester

    orig_results = list(agentic_tester._results)
    agentic_tester._results.clear()
    try:
        result = await agentic_tester._run_tool(
            "record_result",
            {
                "test_id": "BC-001",
                "test_name": "counter test",
                "passed": True,
                "expected": "counter increments",
                "actual": "counter incremented",
            },
        )
        parsed = json.loads(result)
        assert parsed["status"] == "recorded"
        assert parsed["test_id"] == "BC-001"
    finally:
        agentic_tester._results[:] = orig_results


# ── Slice 7: _run_tool blocked path ───────────────────────────────────────────


async def test_F_MOD_001_run_tool_blocked_raises_capability_error():
    """_run_tool for a tool not in CAPABILITY_MAP must raise CapabilityError."""
    import agentic_tester

    with pytest.raises(agentic_tester.CapabilityError):
        await agentic_tester._run_tool("unknown_tool_xyz", {})


# ── Slice 8: CapabilityError properties ───────────────────────────────────────


def test_F_MOD_001_capability_error_properties():
    """CapabilityError in agentic_app must be an Exception subclass with correct message."""
    import agentic_app

    msg = "tool 'xyz' is not authorized"
    err = agentic_app.CapabilityError(msg)
    assert isinstance(err, Exception), "CapabilityError must be a subclass of Exception"
    assert str(err) == msg, f"str(err) must return the message, got '{str(err)}'"
    assert err.args[0] == msg, f"err.args[0] must return the message"


def test_F_MOD_001_tester_capability_error_properties():
    """CapabilityError in agentic_tester must be an Exception subclass with correct message."""
    import agentic_tester

    msg = "tool 'xyz' is not authorized"
    err = agentic_tester.CapabilityError(msg)
    assert isinstance(err, Exception)
    assert str(err) == msg
    assert err.args[0] == msg


# ── Slice 9: Iteration cap in agentic_tester.run ──────────────────────────────


async def test_F_MOD_001_tester_run_loop_iteration_cap():
    """run() must exit cleanly after MAX_ITERATIONS when stop_reason never becomes end_turn."""
    import agentic_tester

    # Always-tool_use response (record_result needs no _page)
    def _make_tool_use_resp():
        block = SimpleNamespace(
            type="tool_use",
            name="record_result",
            id="toolu_cap_test",
            input={
                "test_id": "BC-CAP",
                "test_name": "cap test",
                "passed": True,
                "expected": "exits at cap",
                "actual": "exits at cap",
            },
        )
        resp = MagicMock()
        resp.stop_reason = "tool_use"
        resp.content = [block]
        return resp

    call_count = 0

    async def _always_tool_use(**kwargs):
        nonlocal call_count
        call_count += 1
        return _make_tool_use_resp()

    # Playwright mocks
    mock_page_inner = AsyncMock()
    mock_browser_inner = AsyncMock()
    mock_browser_inner.new_page = AsyncMock(return_value=mock_page_inner)
    mock_browser_inner.close = AsyncMock()

    mock_pw = AsyncMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser_inner)

    mock_playwright_cm = AsyncMock()
    mock_playwright_cm.__aenter__ = AsyncMock(return_value=mock_pw)
    mock_playwright_cm.__aexit__ = AsyncMock(return_value=False)

    mock_client = AsyncMock()
    mock_client.messages.create = _always_tool_use

    orig_results = list(agentic_tester._results)
    agentic_tester._results.clear()
    try:
        with (
            patch("agentic_tester.anthropic.AsyncAnthropic", return_value=mock_client),
            patch("agentic_tester.async_playwright", return_value=mock_playwright_cm),
        ):
            # Must not raise; must exit after MAX_ITERATIONS
            await agentic_tester.run("/fake/path/index.html")
    finally:
        agentic_tester._results[:] = orig_results

    assert call_count == agentic_tester.MAX_ITERATIONS, (
        f"Loop must call messages.create exactly {agentic_tester.MAX_ITERATIONS} times "
        f"(MAX_ITERATIONS), got {call_count}"
    )


# ── Slice 10: All 5 app tools no regression ───────────────────────────────────


def test_F_MOD_001_all_app_tools_no_regression(tmp_path):
    """All 5 execute_tool tools must return valid results after the capability patch."""
    import agentic_app

    # Redirect PROJECT_ROOT so file tools operate in a temp dir
    orig_root = agentic_app.PROJECT_ROOT
    agentic_app.PROJECT_ROOT = tmp_path
    try:
        # Seed a file for read/search
        (tmp_path / "hello.txt").write_text("hello world", encoding="utf-8")

        # list_files
        r = agentic_app.execute_tool("list_files", {"directory": "."})
        entries = json.loads(r)
        assert isinstance(entries, list)
        names = [e["name"] for e in entries]
        assert "hello.txt" in names

        # read_file
        r = agentic_app.execute_tool("read_file", {"path": "hello.txt"})
        assert r == "hello world"

        # write_file
        r = agentic_app.execute_tool("write_file", {"path": "out.txt", "content": "test content"})
        assert r.startswith("OK")

        # search_in_file
        r = agentic_app.execute_tool("search_in_file", {"path": "hello.txt", "keyword": "hello"})
        matches = json.loads(r)
        assert len(matches) >= 1
        assert "hello world" in matches[0]["text"]

        # run_command — platform-independent echo
        r = agentic_app.execute_tool("run_command", {"command": "echo hi"})
        assert isinstance(r, str)
        assert len(r) > 0
    finally:
        agentic_app.PROJECT_ROOT = orig_root


# ── Slice 11: All 6 tester tools no regression ────────────────────────────────


async def test_F_MOD_001_all_tester_tools_no_regression():
    """All 6 _run_tool browser tools must return valid JSON strings after the patch."""
    import agentic_tester

    # Build a reusable mock page
    mock_page = AsyncMock()
    mock_page.set_viewport_size = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.title = AsyncMock(return_value="Test Page")
    mock_page.click = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.inner_text = AsyncMock(return_value="hello")
    mock_page.evaluate = AsyncMock(return_value="column")

    loc_mock = MagicMock()
    loc_mock.all_text_contents = AsyncMock(return_value=["Click me"])
    loc_mock.count = AsyncMock(return_value=1)
    loc_mock.press = AsyncMock()
    mock_page.locator = MagicMock(return_value=loc_mock)

    orig_page = agentic_tester._page
    orig_results = list(agentic_tester._results)
    agentic_tester._page = mock_page
    agentic_tester._results.clear()
    try:
        # open_page
        r = await agentic_tester._run_tool("open_page", {"file_path": "/tmp/index.html"})
        data = json.loads(r)
        assert "title" in data, "open_page must include 'title' in result"

        # click_button
        r = await agentic_tester._run_tool("click_button", {"selector": "#btn"})
        data = json.loads(r)
        assert "clicked_times" in data

        # fill_and_submit
        r = await agentic_tester._run_tool("fill_and_submit", {
            "input_selector": "#name",
            "value": "Alice",
            "form_selector": "form",
        })
        data = json.loads(r)
        assert "message_shown" in data

        # resize_viewport
        r = await agentic_tester._run_tool("resize_viewport", {"width": 480})
        data = json.loads(r)
        assert data["viewport"]["width"] == 480

        # get_computed_style
        r = await agentic_tester._run_tool("get_computed_style", {
            "selector": "form",
            "properties": ["flex-direction"],
        })
        data = json.loads(r)
        assert "flex-direction" in data

        # record_result
        r = await agentic_tester._run_tool("record_result", {
            "test_id": "BC-001",
            "test_name": "counter",
            "passed": True,
            "expected": "increments",
            "actual": "incremented",
        })
        data = json.loads(r)
        assert data["status"] == "recorded"
    finally:
        agentic_tester._page = orig_page
        agentic_tester._results[:] = orig_results


# ── Slice 12: .env.example ANTHROPIC_API_KEY ──────────────────────────────────


def test_F_MOD_001_env_example_has_anthropic_api_key():
    """ANTHROPIC_API_KEY must appear in .env.example with a non-empty placeholder."""
    env_path = PROJECT_ROOT / ".env.example"
    assert env_path.exists(), ".env.example must exist at the project root"
    text = env_path.read_text()
    assert "ANTHROPIC_API_KEY" in text, "ANTHROPIC_API_KEY must be listed in .env.example"
    for line in text.splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            value = line.split("=", 1)[1].strip()
            assert value, (
                "ANTHROPIC_API_KEY in .env.example must have a placeholder (non-empty value)"
            )
            break
