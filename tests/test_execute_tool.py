"""F-MOD-002: Unit tests for execute_tool() in agentic_app.py.

Covers:
  (a) Capability validation — CapabilityError raised for unknown tool names.
  (b) File dispatch — read_file returns contents, write_file writes and reports.
  (c) run_command blocklist — blocked keywords produce "BLOCKED:" without subprocess.
  (d) run_command safe path — safe command returns stdout or "(no output)".
"""

import pytest

# ── (a) Capability validation ─────────────────────────────────────────────────


def test_F_MOD_002_execute_tool_capability_error():
    """CapabilityError is raised when tool name is not in CAPABILITY_MAP."""
    import agentic_app

    with pytest.raises(agentic_app.CapabilityError):
        agentic_app.execute_tool("nonexistent_tool_xyz", {})


# ── (b) File dispatch ─────────────────────────────────────────────────────────


def test_F_MOD_002_execute_tool_read_file(tmp_path, monkeypatch):
    """read_file returns the UTF-8 file contents as a string."""
    import agentic_app

    target = tmp_path / "sample.txt"
    target.write_text("hello from test", encoding="utf-8")

    monkeypatch.setattr(agentic_app, "PROJECT_ROOT", tmp_path)
    result = agentic_app.execute_tool("read_file", {"path": "sample.txt"})

    assert result == "hello from test"


def test_F_MOD_002_execute_tool_write_file(tmp_path, monkeypatch):
    """write_file writes content to disk and returns a non-error success string."""
    import agentic_app

    monkeypatch.setattr(agentic_app, "PROJECT_ROOT", tmp_path)
    result = agentic_app.execute_tool(
        "write_file", {"path": "output.txt", "content": "written content"}
    )

    # Return string must be non-empty and not start with ERROR
    assert isinstance(result, str)
    assert result
    assert not result.startswith("ERROR")
    # Verify content was actually written
    assert (tmp_path / "output.txt").read_text(encoding="utf-8") == "written content"


# ── (c) run_command blocklist ─────────────────────────────────────────────────

BLOCKED_COMMANDS = [
    "rm -rf /",
    "del /f /s /q C:\\Windows",
    "format C:",
    "mkfs.ext4 /dev/sda1",
    "sudo apt-get install vim",
    "shutdown -r now",
    ":(){ :|:& };:",
]


@pytest.mark.parametrize("command", BLOCKED_COMMANDS)
def test_F_MOD_002_execute_tool_run_command_blocked_keywords(command, monkeypatch):
    """Commands containing a blocked keyword return a BLOCKED: string without spawning subprocess."""
    import subprocess

    import agentic_app

    spawn_called = []

    def _no_subprocess(*args, **kwargs):
        spawn_called.append(True)
        raise AssertionError("subprocess.run must NOT be called for blocked commands")

    monkeypatch.setattr(subprocess, "run", _no_subprocess)
    result = agentic_app.execute_tool("run_command", {"command": command})

    assert result.startswith("BLOCKED:"), (
        f"Expected result to start with 'BLOCKED:' for command {command!r}, got {result!r}"
    )
    assert not spawn_called, "subprocess.run must not be invoked for blocked commands"


# ── (d) run_command safe path ─────────────────────────────────────────────────


def test_F_MOD_002_execute_tool_run_command_safe():
    """A safe command (echo) is executed and stdout (or '(no output)') is returned."""
    import agentic_app

    result = agentic_app.execute_tool("run_command", {"command": "echo hello"})

    assert isinstance(result, str)
    # Must not be a BLOCKED or ERROR response
    assert not result.startswith("BLOCKED:")
    assert not result.startswith("ERROR")
    # echo hello produces at least some output
    assert len(result) > 0
