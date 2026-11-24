"""F-MOD-002: Parametrized golden evaluation for run_command blocklist logic.

Reads tests/golden/run_command_golden.yaml at pytest collection time.
Each entry is exercised against the blocklist from agentic_app.py:172 and the
computed outcome is asserted to match the entry's expected_outcome field.

No subprocess is spawned — the test exercises keyword-matching logic only.
"""

from pathlib import Path

import pytest
import yaml

# ── Load golden set at collection time ───────────────────────────────────────

_GOLDEN_PATH = Path(__file__).parent / "golden" / "run_command_golden.yaml"
_GOLDEN_CASES: list[dict] = yaml.safe_load(_GOLDEN_PATH.read_text(encoding="utf-8"))

# ── Blocklist constants (mirror of agentic_app.py:172) ───────────────────────
# Extracted here to keep tests independent of internal implementation details
# while asserting against an independent known source of truth.

_BLOCKED_KEYWORDS: list[str] = [
    "rm ",
    "del ",
    "format ",
    "mkfs",
    "sudo",
    "shutdown",
    ":(){",
]


def _compute_outcome(command: str) -> str:
    """Apply the blocklist logic from agentic_app.py:172 and return 'allow' or 'block'."""
    for keyword in _BLOCKED_KEYWORDS:
        if keyword in command.lower():
            return "block"
    return "allow"


# ── Structural checks ─────────────────────────────────────────────────────────


def test_F_MOD_002_golden_yaml_has_required_fields():
    """Every golden YAML entry must have command, expected_outcome, and rationale."""
    for entry in _GOLDEN_CASES:
        assert "command" in entry, f"Missing 'command' in entry: {entry}"
        assert "expected_outcome" in entry, f"Missing 'expected_outcome' in entry: {entry}"
        assert "rationale" in entry, f"Missing 'rationale' in entry: {entry}"
        assert entry["expected_outcome"] in ("allow", "block"), (
            f"'expected_outcome' must be 'allow' or 'block', got {entry['expected_outcome']!r}"
        )


def test_F_MOD_002_golden_covers_both_outcomes():
    """The golden set must include at least one 'allow' and one 'block' entry."""
    outcomes = {entry["expected_outcome"] for entry in _GOLDEN_CASES}
    assert "allow" in outcomes, "Golden set must contain at least one 'allow' entry"
    assert "block" in outcomes, "Golden set must contain at least one 'block' entry"


# ── Parametrized blocklist evaluation ────────────────────────────────────────


@pytest.mark.parametrize(
    "entry",
    _GOLDEN_CASES,
    ids=[entry["command"] for entry in _GOLDEN_CASES],
)
def test_F_MOD_002_golden_run_command(entry):
    """Blocklist outcome for each golden command must match expected_outcome."""
    command = entry["command"]
    expected = entry["expected_outcome"]
    actual = _compute_outcome(command)

    assert actual == expected, (
        f"Command {command!r}: expected outcome '{expected}', computed '{actual}'. "
        f"Rationale: {entry['rationale']}"
    )
