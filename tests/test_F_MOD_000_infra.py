"""Tests for F-MOD-000: pytest infrastructure and shared conftest fixtures.

These tests verify the behavioral expectations of the module:
- requirements-dev.txt content
- pytest collection health
- mock_anthropic_client fixture behavior
- mock_page fixture behavior
- asyncio_mode=auto configuration
- .env.example ANTHROPIC_API_KEY entry
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


# ── Slice 1: requirements-dev.txt ─────────────────────────────────────────────


def test_F_MOD_000_requirements_dev_txt_content():
    """requirements-dev.txt must list pytest>=8 and pytest-asyncio."""
    req_path = PROJECT_ROOT / "requirements-dev.txt"
    assert req_path.exists(), "requirements-dev.txt must exist at the project root"
    text = req_path.read_text()
    assert "pytest>=8" in text, "pytest>=8 must appear in requirements-dev.txt"
    assert "pytest-asyncio" in text, "pytest-asyncio must appear in requirements-dev.txt"


def test_F_MOD_000_requirements_no_conflict_with_production():
    """requirements-dev.txt must not conflict with requirements.txt packages."""
    prod_path = PROJECT_ROOT / "requirements.txt"
    dev_path = PROJECT_ROOT / "requirements-dev.txt"
    # Both files must exist; we do a name-only check (no duplicate base names)
    if not prod_path.exists() or not dev_path.exists():
        return  # nothing to compare
    prod_names = {line.split(">=")[0].split("==")[0].strip().lower()
                  for line in prod_path.read_text().splitlines()
                  if line.strip() and not line.startswith("#")}
    dev_names = {line.split(">=")[0].split("==")[0].strip().lower()
                 for line in dev_path.read_text().splitlines()
                 if line.strip() and not line.startswith("#")}
    overlap = prod_names & dev_names
    assert not overlap, (
        f"requirements-dev.txt duplicates production packages: {overlap}. "
        "This risks version conflicts."
    )


# ── Slice 2: pytest collection ────────────────────────────────────────────────


def test_F_MOD_000_pytest_collect_only_clean():
    """pytest --collect-only must exit 0 with no collection errors."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )
    assert result.returncode == 0, (
        f"pytest --collect-only failed (exit {result.returncode}):\n"
        f"stdout: {result.stdout}\n"
        f"stderr: {result.stderr}"
    )
    assert "error" not in result.stdout.lower() or "0 error" in result.stdout.lower(), (
        f"Collection errors present:\n{result.stdout}"
    )


# ── Slice 3: mock_anthropic_client fixture ────────────────────────────────────


def test_F_MOD_000_mock_client_first_call_tool_use(mock_anthropic_client):
    """messages.create must return stop_reason='tool_use' on the first call."""
    response = mock_anthropic_client.messages.create(
        model="claude-opus-5-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}],
        tools=[],
    )
    assert response.stop_reason == "tool_use"


def test_F_MOD_000_mock_client_second_call_end_turn(mock_anthropic_client):
    """messages.create must return stop_reason='end_turn' on the second call."""
    mock_anthropic_client.messages.create(
        model="claude-opus-5-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}],
        tools=[],
    )
    response = mock_anthropic_client.messages.create(
        model="claude-opus-5-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}],
        tools=[],
    )
    assert response.stop_reason == "end_turn"


def test_F_MOD_000_mock_client_content_tool_use_block(mock_anthropic_client):
    """First response must carry a content list with a tool_use block."""
    response = mock_anthropic_client.messages.create(
        model="claude-opus-5-5",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}],
        tools=[],
    )
    assert len(response.content) >= 1, "content list must be non-empty"
    block = response.content[0]
    assert block.type == "tool_use"
    assert isinstance(block.name, str) and block.name, "tool block must have a non-empty name"
    assert isinstance(block.input, dict), "tool block input must be a dict"


def test_F_MOD_000_mock_client_no_http_connection(mock_anthropic_client):
    """mock_anthropic_client must not open a real HTTP connection."""
    # If the fixture is a MagicMock, calling create never touches the network.
    # We verify this by checking the mock object's type, not by intercepting sockets.
    from unittest.mock import MagicMock
    assert isinstance(mock_anthropic_client, MagicMock), (
        "mock_anthropic_client must be a MagicMock — not a real Anthropic client"
    )


# ── Slice 4: mock_page fixture ────────────────────────────────────────────────


async def test_F_MOD_000_mock_page_async_methods(mock_page):
    """mock_page async methods must resolve without error and without spawning Chromium."""
    # Each await must complete without raising
    await mock_page.goto("https://example.com")
    await mock_page.click("#btn")
    await mock_page.fill("#input", "text")
    await mock_page.evaluate("1 + 1")
    await mock_page.query_selector("#el")


def test_F_MOD_000_mock_page_is_async_mock(mock_page):
    """mock_page must be an AsyncMock (awaitable methods, no real browser)."""
    from unittest.mock import AsyncMock
    assert isinstance(mock_page, AsyncMock), "mock_page must be an AsyncMock"


# ── Slice 5: asyncio_mode=auto ────────────────────────────────────────────────


async def test_F_MOD_000_asyncio_mode_auto():
    """An async def test must run with asyncio_mode=auto (no @pytest.mark.asyncio needed)."""
    import asyncio
    result = await asyncio.sleep(0)  # trivial coroutine
    # If we get here, asyncio_mode=auto is working
    assert result is None


# ── Slice 6: .env.example ─────────────────────────────────────────────────────


def test_F_MOD_000_env_example_api_key():
    """ANTHROPIC_API_KEY must appear in .env.example with a safe placeholder."""
    env_example = PROJECT_ROOT / ".env.example"
    assert env_example.exists(), ".env.example must exist at the project root"
    text = env_example.read_text()
    assert "ANTHROPIC_API_KEY" in text, (
        "ANTHROPIC_API_KEY must be listed in .env.example"
    )
    # Must have a placeholder (non-empty value or the key itself present)
    for line in text.splitlines():
        if line.startswith("ANTHROPIC_API_KEY="):
            value = line.split("=", 1)[1].strip()
            assert value, (
                "ANTHROPIC_API_KEY in .env.example must have a placeholder value "
                "(e.g. your-api-key-here), not an empty string"
            )
            break
