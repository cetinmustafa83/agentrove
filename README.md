# Agentrove

Self-hosted AI coding workspace for single users and small teams running Claude Code, Codex, Copilot, Cursor, and OpenCode through ACP adapters inside per-workspace sandboxes with chat, editor, terminal, and git tooling.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://www.apache.org/licenses/LICENSE-2.0)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Discord](https://img.shields.io/badge/Discord-5865F2.svg?logo=discord&logoColor=white)](https://discord.gg/HvkJU8dcBA)

> **Note:** Agentrove is under active development. Expect breaking changes between releases.

## Screenshots

![Chat Interface](screenshots/chat-interface.jpeg)
## Community

Join the [Discord server](https://discord.gg/HvkJU8dcBA).

## Why Agentrove

- Run multiple coding-agent runtimes from one self-hosted interface
- Launch agent runtimes through ACP adapters
- Keep each project in its own Docker or host sandbox
- Work in chat, editor, terminal, diff, secrets, and PR review views side by side
- Organize work by workspace, then branch into sub-threads when a task needs its own track
- Reuse local auth and config inside sandboxes for a smoother local-agent workflow

## Core Architecture

```text
React/Vite Frontend
  -> FastAPI Backend
  -> SQLite + Redis (web mode)
  -> SQLite + in-memory cache/pubsub (desktop mode)
  -> Workspace sandbox (Docker or Host)
  -> Claude Code ACP / Codex ACP
  -> Claude Code CLI / Codex CLI
```

Agentrove launches agents through ACP adapters:

- **Claude** via `claude-agent-acp` + Claude Code
- **Codex** via `codex-acp` + Codex CLI
- **Copilot** via `copilot --acp --stdio`
- **Cursor** via `cursor-agent acp`
- **OpenCode** via OpenCode ACP-compatible models and tool streams

## Key Features

- Claude, Codex, Copilot, Cursor, and OpenCode in the same UI with per-chat model selection
- ACP-based agent runtime integration with agent-specific tool rendering
- Agent-specific permission modes and reasoning/thinking controls
- Workspace-based project organization with per-workspace sandboxes
- Workspace creation from an empty directory, git clone, or an existing local folder
- Docker and host sandbox providers
- Built-in editor, terminal, diff, secrets, and PR review panels
- File mentions, built-in slash commands, custom skills, and prompt enhancement in the composer
- File attachments with inline preview support for images, PDFs, and spreadsheets
- Streaming chat sessions with resumable SSE events, explicit cancellation, queued follow-up messages, and permission prompts
- Sub-threads for branching work from an existing chat, plus chat pinning
- Optional git worktree mode for isolated implementation per chat
- Git helpers for branches, checkout, pull, push, commit generation, PR description generation, PR creation, and diff restore flows
- GitHub integration for repository lookup, pull request review, comments, collaborators, and reviewer selection
- Workspace resources for custom skills and built-in slash commands
- User-configurable personas, custom instructions, custom env vars, notifications, and sandbox defaults
- Built-in authentication flows for signup, login, refresh, logout, password reset, and optional email verification
- Web app and macOS desktop app

## Workspaces

Workspaces are the top-level project unit. Each workspace owns a sandbox and groups related chats under one project context.

### Source types

- **Empty**: create a new empty directory
- **Git clone**: clone a repository into a fresh workspace
- **Local folder**: use an existing directory, typically with the host sandbox provider

### Sandbox isolation

Each workspace gets its own sandbox instance. Chats in the same workspace share the same filesystem, installed tools, auth files, and `.claude` / `.codex` resources.

### Per-workspace sandbox provider

You can choose a sandbox provider per workspace:

- **Docker**: isolated local container
- **Host**: runs directly on the host machine

### Worktree mode

For git-backed workspaces, chats can opt into worktree isolation. Agentrove creates a dedicated worktree under `.worktrees/<chat-id-prefix>` and reuses it for later turns in that chat.

## Models And Agents

Current model families exposed by the backend:

- **Claude**: `sonnet[1m]`, `opus[1m]`, `haiku`
- **Codex**: `gpt-5.5`, `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`, `gpt-5.2-codex`, `gpt-5.2`, `gpt-5.1-codex-max`, `gpt-5.1-codex-mini`
- **Copilot**: Claude and GPT model variants exposed through Copilot ACP
- **Cursor**: Cursor composer, GPT, Claude, Gemini, Grok, and other Cursor ACP model variants
- **OpenCode**: OpenCode-hosted and provider-backed ACP model variants

Agent-specific controls:

- **Claude permission modes**: `default`, `acceptEdits`, `plan`, `bypassPermissions`
- **Codex permission modes**: `default`, `read-only`, `full-access`
- **Claude thinking modes**: `low`, `medium`, `high`, `max`
- **Codex reasoning modes**: `low`, `medium`, `high`, `xhigh`

The UI also adapts tool rendering per runtime, so Claude, Codex, Copilot, Cursor, and OpenCode tool calls are shown with agent-specific formatting instead of a single generic event viewer.

## Settings Surface

Current settings in the app cover:

- General settings
- Skills
- Personas
- Environment variables
- Custom instructions

General settings include:

- GitHub personal access token
- Default sandbox provider
- Notification toggle

Workspace resources and settings together let you:

- Add and edit custom skills
- Define reusable personas with custom system prompts
- Inject custom environment variables into agent runs
- Add account-level custom instructions applied to chats

## Quick Start (Web)

### Requirements

- Docker
- Docker Compose

### Start

```bash
git clone https://github.com/Mng-dev-ai/agentrove.git
cd agentrove
cp .env.example .env
```

Set a `SECRET_KEY` in `.env`:

```bash
openssl rand -hex 32
```

Start the stack:

```bash
docker compose up -d
```

Open [http://localhost:3000](http://localhost:3000).

The web app includes built-in auth screens for sign up, login, password reset, and email verification when verification is enabled in config.

### Stop and logs

```bash
docker compose down
docker compose logs -f
```

### Developer hooks

The repo uses a root `.githooks/pre-commit` hook for frontend staged-file checks and backend `ruff` linting. Point Git at the repo hook directory once per clone:

```bash
./scripts/install-hooks.sh
pip install pre-commit
pre-commit run --all-files
```

### Default web ports

- Frontend: `3000`
- Backend API: `8080`
- Redis: `6379`

## Desktop (macOS)

Desktop mode uses Tauri with a bundled Python backend sidecar on `localhost:8081` and local SQLite storage.
The desktop sidecar bundles `claude-agent-acp` and `codex-acp`; host-mode sessions still use the user's Claude Code or Codex CLI installation for the underlying agent.

### Download prebuilt app

- Apple Silicon DMG: [Latest Release](https://github.com/Mng-dev-ai/agentrove/releases/latest)

### How it works

```text
Tauri Desktop App
  -> React frontend
  -> bundled backend sidecar (localhost:8081)
  -> local SQLite database
  -> local workspace sandbox access
```

### Build and run from source

Requirements:

- Node.js
- Rust

Dev workflow:

```bash
cd frontend
npm install
npm run desktop:dev
```

Build:

```bash
cd frontend
npm run desktop:build
```

App bundle output:

- `frontend/src-tauri/target/release/bundle/macos/Agentrove.app`

## Included Tooling

The backend and sandbox images install the tooling Agentrove needs to run coding agents locally, including:

- Claude Code
- Codex CLI
- Copilot CLI (`copilot`)
- Cursor CLI (`cursor-agent`)
- OpenCode CLI (`opencode`)
- `claude-agent-acp`
- `codex-acp`
- GitHub CLI

Agentrove also syncs local Claude and Codex auth/config files into sandboxes when available.

## API and Operations

- API docs: [http://localhost:8080/api/v1/docs](http://localhost:8080/api/v1/docs)
- Admin panel: [http://localhost:8080/admin](http://localhost:8080/admin)
- Liveness endpoint: `GET /health`
- Readiness endpoint: `GET /api/v1/readyz`
  - web mode checks database and Redis
  - desktop mode checks database only

## Deployment

- Production setup serves frontend at `/` and API under `/api/*`
- Single-host Docker production:
  ```bash
  SECRET_KEY=$(openssl rand -hex 32) \
    SERVICE_FQDN_WEB_80=https://yourdomain.com \
    APP_URL=https://yourdomain.com \
    ALLOWED_ORIGINS=https://yourdomain.com \
    docker compose -f docker-compose-production.yml up -d --build
  ```

## Tech Stack

- Frontend: React 19, TypeScript, Vite, TailwindCSS, Zustand, React Query, Monaco, xterm.js
- Backend: FastAPI, SQLAlchemy, Redis, SQLite
- Runtime: Claude Code, Codex CLI, ACP, Docker, Tauri

## License

Apache 2.0. See [LICENSE](LICENSE).

## Contributing

Contributions are welcome. Open an issue first to discuss the change, then submit a pull request.
