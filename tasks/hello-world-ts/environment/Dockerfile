FROM ubuntu:24.04

WORKDIR /app

# Toolchain the agent (and verifier) need to build and test the React component.
RUN apt-get update \
    && apt-get install -y curl unzip git \
    && rm -rf /var/lib/apt/lists/*

# Install bun and expose it on PATH for all subsequent shells.
RUN curl -fsSL https://bun.sh/install | bash
ENV BUN_INSTALL="/root/.bun"
ENV PATH="/root/.bun/bin:${PATH}"

# Install react/react-dom at the filesystem root so both /app (agent) and
# /tests (verifier) resolve them by walking up to /node_modules.
RUN cd / && bun add react react-dom

# Calibration harness: terminus-2 drives the container through tmux and records
# the session with asciinema. The runtime has no network, so the agent harness
# cannot install them itself — without tmux every attempt fails before the agent
# reads the instruction.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tmux asciinema \
    && rm -rf /var/lib/apt/lists/*

# Git baseline: the agent starts from a committed tree. Keep solution
# files and any later state out of this history.
RUN git init \
    && git config user.email "task@askable.local" \
    && git config user.name "Task Baseline" \
    && git add -A \
    && git commit -m "Task baseline" --allow-empty
