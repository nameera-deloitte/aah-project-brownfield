# ─────────────────────────────────────────────────────────────────────────────
# brownfield — Dockerfile
#
# Build:
#   docker build --build-arg ANTHROPIC_API_KEY=<key> -t brownfield:latest .
#
# Run:
#   docker run --rm -e ANTHROPIC_API_KEY=<key> brownfield:latest
#
# The API key is accepted as a build-arg (baked into the image layer) OR as a
# runtime environment variable.  Prefer the runtime form (-e) so the secret is
# never persisted in an image layer.
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim AS base

# --- system deps ---------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- install uv ----------------------------------------------------------
# Pin to a known-good release; bump deliberately.
ENV UV_VERSION=0.4.30
RUN curl -fsSL https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

# --- working directory ---------------------------------------------------
WORKDIR /app

# --- copy dependency manifests first (layer-cache friendly) --------------
COPY requirements.txt ./

# --- install Python dependencies via uv ----------------------------------
RUN uv pip install --system --no-cache -r requirements.txt

# --- install Playwright browsers (Chromium only to keep image lean) ------
RUN python -m playwright install chromium \
 && python -m playwright install-deps chromium

# --- copy application source ---------------------------------------------
COPY agentic_app.py agentic_tester.py ./
COPY config/ ./config/
COPY knowledge/ ./knowledge/

# --- runtime environment variable (never hardcode a real value) ----------
ARG ANTHROPIC_API_KEY=""
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# --- non-root user for security ------------------------------------------
RUN useradd --create-home --shell /bin/bash appuser \
 && chown -R appuser:appuser /app
USER appuser

# --- entrypoint ----------------------------------------------------------
ENTRYPOINT ["python", "agentic_app.py"]
