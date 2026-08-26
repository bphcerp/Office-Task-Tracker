# Office Task Tracker

An office task tracker that **scrapes email**, passes each message to an **LLM agent** that
classifies it into a **Person**, **Task**, and **Summary**, stores the result, and displays it
in a web frontend.

## Architecture

| Layer     | Tech                                                  |
| --------- | ----------------------------------------------------- |
| Frontend  | [Astro](https://astro.build) 5 + Vite + pnpm          |
| Backend   | Python / FastAPI, managed with [uv](https://docs.astral.sh/uv/) |
| Storage   | PostgreSQL 16                                         |
| Scheduler | APScheduler (background mail polling)                 |
| Agent     | Provider-agnostic LLM via [LiteLLM](https://docs.litellm.ai/) |

```
         ┌────────────┐   /api    ┌────────────┐   poll    ┌──────────┐
 Email ─►│  frontend  │ ◄───────► │  backend   │ ◄────────► │ postgres │
  IMAP   └────────────┘           │ (FastAPI)  │            └──────────┘
                                  │  └─ scrape → agent → store │
                                  └────────────┘
```

## Repository layout

```
.
├── .env.example          # single source of truth for ALL env vars
├── docker-compose.yml    # dev + prod profiles
├── backend/              # Python (uv) FastAPI app
│   ├── pyproject.toml    # dependencies + tool config
│   ├── Dockerfile        # dev / prod targets
│   └── app/
│       ├── main.py       # app entrypoint, lifespan, router mounting
│       ├── config.py     # pydantic-settings reading .env
│       ├── db.py         # async SQLAlchemy engine / session
│       ├── models.py     # Person, Task, Summary ORM models
│       ├── schemas.py    # Pydantic API schemas
│       ├── jobs.py       # APScheduler mail-polling job
│       ├── routers/tasks.py
│       └── services/
│           ├── mail.py   # IMAP scraping (stub)
│           └── agent.py  # LLM classification (stub)
└── frontend/             # Astro (pnpm + Vite)
    ├── astro.config.mjs  # node adapter (SSR)
    ├── Dockerfile        # dev / build / prod targets
    └── src/
        ├── pages/index.astro
        ├── layouts/Layout.astro
        └── components/TaskList.astro
```

## Configuration

Everything is driven by a **single root `.env`** file. Docker Compose passes it to every
service via `env_file`, so there is no per-service duplication.

```sh
cp .env.example .env
```

Open `.env` and fill in at least:

- `POSTGRES_PASSWORD` — database password
- `IMAP_HOST`, `IMAP_USER`, `IMAP_PASSWORD` — mailbox for scraping
- `LITELLM_MODEL` + a provider key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, …) for the agent

> `BACKEND_UPSTREAM` is the URL the Astro SSR server uses to reach the backend API.
> Docker Compose sets this automatically (`http://backend:8000` in dev,
> `http://backend-prod:8000` in prod). For local frontend dev without Docker it
> defaults to `http://localhost:8000`.

## Prerequisites

- [Docker](https://docs.docker.com/engine/install/) with Compose v2
- [uv](https://docs.astral.sh/uv/#installation) (local dev / lockfile generation)
- [Node.js](https://nodejs.org) ≥ 22 and [pnpm](https://pnpm.io/installation) (via `corepack enable`)

## Run it

### Option A — Docker Compose (recommended)

**Development profile** — hot reload, ports exposed:

```sh
docker compose --profile dev up --build
```

> **Build networking note:** compose builds use `network: host` so `uv`/`pnpm` can
> download dependencies when the default bridge network has no outbound internet.
> If your Docker daemon already has build-network access, you can remove these
> `network: host` lines.

- Frontend: http://localhost:4321
- Backend API + Swagger UI: http://localhost:8000/docs

**Production profile** — built images, production servers:

```sh
docker compose --profile prod up -d --build
```

Stop / clean up:

```sh
docker compose down          # stop containers (keeps DB data)
docker compose down -v       # stop + delete the postgres volume
```

### Option B — Local (no Docker, only Postgres in Docker)

Run the database, then the app from your host:

```sh
# terminal 1: postgres
docker compose --profile dev up postgres

# terminal 2: backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# terminal 3: frontend
cd frontend
corepack enable && pnpm install
pnpm dev
```

## Mail ingestion modes

The `MAIL_INGESTION_MODE` env var controls how emails are scraped:

| Value      | Behaviour                                                        |
| ---------- | ---------------------------------------------------------------- |
| `background` | APScheduler polls the inbox every `MAIL_POLL_SECONDS` seconds |
| `manual`   | Nothing runs automatically; call `POST /api/tasks/ingest`        |

Manual trigger example:

```sh
curl -X POST http://localhost:8000/api/tasks/ingest -H 'Content-Type: application/json' \
  -d '{"limit": 25}'
```

## API

| Method | Endpoint            | Description                              |
| ------ | ------------------- | ---------------------------------------- |
| GET    | `/api/tasks`        | List classified tasks (newest first)     |
| GET    | `/api/tasks/{id}`   | Fetch a single task                      |
| POST   | `/api/tasks/ingest` | Manually scrape + classify emails        |
