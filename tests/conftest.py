"""Shared pytest fixtures for the brownfield test suite.

This module provides mock infrastructure so tests run fully offline:
no Anthropic API calls and no Chromium browser processes are started.
"""

import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

# ---------------------------------------------------------------------------
# Windows MAX_PATH guard
# ---------------------------------------------------------------------------
# The AAH regression suite runs in a long temp-dir path
# (~68 chars just for the dir name).  Combined with the deeply-nested beta
# types in the anthropic 2.x SDK, the full module path easily exceeds
# Windows' 260-char MAX_PATH limit, causing ModuleNotFoundError even when
# the file exists on disk.  Pre-registering a lightweight stub prevents
# "import anthropic" in agentic_app/agentic_tester from hitting that path.
# Neither module uses anthropic at import time (client = anthropic.Anthropic()
# is only called inside run_agent() / run()), so this stub is transparent.
if "anthropic" not in sys.modules:
    _stub = MagicMock(name="anthropic")
    _stub.Anthropic = MagicMock
    _stub.AsyncAnthropic = MagicMock
    sys.modules["anthropic"] = _stub

# ── mock_anthropic_client ─────────────────────────────────────────────────────


def _make_tool_use_response() -> MagicMock:
    """Return a fake Anthropic response with stop_reason='tool_use'."""
    tool_block = SimpleNamespace(
        type="tool_use",
        name="read_file",
        id="toolu_01",
        input={"path": "sample/index.html"},
    )
    response = MagicMock()
    response.stop_reason = "tool_use"
    response.content = [tool_block]
    return response


def _make_end_turn_response() -> MagicMock:
    """Return a fake Anthropic response with stop_reason='end_turn'."""
    text_block = SimpleNamespace(type="text", text="Done.")
    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [text_block]
    return response


@pytest.fixture()
def mock_anthropic_client() -> MagicMock:
    """Function-scoped MagicMock replicating the anthropic.Anthropic client.

    messages.create returns:
      - call 1: stop_reason="tool_use", content=[tool_use block]
      - call 2: stop_reason="end_turn",  content=[text block]

    No HTTP connection to api.anthropic.com is opened.
    """
    client = MagicMock()
    client.messages.create.side_effect = [
        _make_tool_use_response(),
        _make_end_turn_response(),
    ]
    # Also wire acreate for async callers (AsyncMock so it can be awaited)
    async_create = AsyncMock(
        side_effect=[
            _make_tool_use_response(),
            _make_end_turn_response(),
        ]
    )
    client.messages.acreate = async_create
    return client


# ── mock_page ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def mock_page() -> AsyncMock:
    """Function-scoped AsyncMock replicating playwright.async_api.Page.

    Exposes goto, click, fill, evaluate, and query_selector as async stubs
    that return sensible defaults.  No Chromium browser process is spawned.
    """
    page = AsyncMock()
    page.goto.return_value = None
    page.click.return_value = None
    page.fill.return_value = None
    page.evaluate.return_value = None
    page.query_selector.return_value = None
    return page
