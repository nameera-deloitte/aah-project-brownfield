"""F-MOD-002: Regression guard — agentic_tester.MAX_ITERATIONS must equal 20.

A single assertion that the constant introduced by MOD-001 has not been removed
or accidentally changed.
"""


def test_F_MOD_002_iteration_cap():
    """MAX_ITERATIONS must equal 20 — guards against accidental removal of the safety cap."""
    import agentic_tester

    assert agentic_tester.MAX_ITERATIONS == 20
