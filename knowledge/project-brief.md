# Project Brief — Original Context

Improve security of the existing agentic application.

The current application (`agentic_app.py`, `agentic_tester.py`) has known security gaps:
- `run_command` relies on a keyword denylist (blocklist) rather than a safelist — easily bypassed
- `ANTHROPIC_API_KEY` is not validated at startup via `check_env()`
- `REQUIRED_ENV` tuple is empty — no env-var enforcement at boot
- No authentication or authorisation for outbound tool calls beyond the API key
- No unit tests or evaluations on the tool execution path
- Module-global browser state in `agentic_tester.py` is not safe for concurrent use

User stated intent: "security"
