# Dependency Map

## External Dependencies

| Package | Version | Purpose | Category |
|---------|---------|---------|----------|
| anthropic | >=1.0.0 | Claude API client; `messages.create`, tool-use, adaptive thinking | AI / LLM |
| playwright | >=1.40.0 | Headless Chromium browser automation for agentic_tester | Browser Automation |

## Internal Module Dependencies

| Module | Depends On | Depended By |
|--------|-----------|-------------|
| `agentic_app.py` | json, os, subprocess, pathlib, anthropic | (entry point — nothing imports it) |
| `agentic_tester.py` | asyncio, json, pathlib, anthropic, playwright.async_api | (entry point — nothing imports it) |
| `config/env_check.py` | os, sys, pathlib (stdlib only) | (entry point — not yet imported by either agent) |
