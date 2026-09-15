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
         ┌────────────┐  SSR/API  ┌────────────┐           ┌──────────┐
 Browser │  frontend  │ ◄───────► │  backend   │ ◄────────► │ postgres │
         │   (Astro)  │  proxies  │ (FastAPI)  │           └──────────┘
         └────────────┘           │ scrape →   │
              ▲                   │ agent →    │
              │ ingest/settings   │ store      │
              └───────────────────┴─────┬──────┘
                                        │
                                   IMAP (email)
```

## Repository layout

```
.
├── .env.example          # single source of truth for ALL env vars
├── docker-compose.yml    # dev + prod profiles
├── backend/              # Python (uv) FastAPI app
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── app/
│       ├── main.py       # app entrypoint, lifespan, router mounting
│       ├── config.py     # pydantic-settings reading .env
│       ├── db.py         # async SQLAlchemy engine / session
│       ├── models.py     # Person, Task, Summary, IngestionSettings
│       ├── schemas.py    # Pydantic API schemas
│       ├── jobs.py       # APScheduler background polling
│       ├── routers/
│       │   ├── tasks.py      # task list/detail, status, delete, ingest
│       │   └── settings.py   # runtime ingestion settings
│       └── services/
│           ├── mail.py               # IMAP scrape + ingest pipeline
│           ├── agent.py              # LLM classification via LiteLLM
│           └── ingestion_settings.py # DB-backed settings singleton
└── frontend/             # Astro SSR (pnpm + Vite)
    ├── astro.config.mjs
    ├── Dockerfile
    └── src/
        ├── pages/
        │   ├── index.astro           # task list
        │   ├── settings.astro        # ingestion settings UI
        │   ├── tasks/[id].astro      # task detail
        │   └── api/                  # browser → backend proxies (ingest, tasks, settings)
        ├── components/               # TaskList, TaskDetail, IngestButton, …
        ├── layouts/Layout.astro
        ├── lib/                      # api client, task UI helpers, theme
        └── styles/                   # tokens.css + global.css (light/dark)
```

## App overview

| Route | What it does |
| ----- | ------------ |
| `/` | Task list with search, sort, and status filters; manual ingest button |
| `/tasks/{id}` | Task detail — summary, assignee, status picker, delete |
| `/settings` | Ingestion mode, mark-as-read, poll interval (hours), batch size |

SSR pages read from the backend directly (`BACKEND_UPSTREAM`). Browser mutations (ingest, status update, delete, settings save) go through Astro API routes under `src/pages/api/`.

## Configuration

Everything is driven by a **single root `.env`** file. Docker Compose passes it to every
service via `env_file`, so there is no per-service duplication.

```sh
cp .env.example .env
```

Then complete the [Setup](#setup) steps below before starting the app.

Ingestion defaults (`MAIL_INGESTION_MODE`, `MAIL_POLL_HOURS`, `MAIL_MARK_AS_READ`, `MAIL_BATCH_LIMIT`) can be changed at runtime on the **Settings** page (`/settings`); env vars seed the database row on first startup.

> `BACKEND_UPSTREAM` is the URL the Astro SSR server uses to reach the backend API.
> Docker Compose sets this automatically (`http://backend:8000` in dev,
> `http://backend-prod:8000` in prod). For local frontend dev without Docker it
> defaults to `http://localhost:8000`.

## Setup

### 1. PostgreSQL

Set a real password in `.env`:

```env
POSTGRES_PASSWORD=your-secure-password
```

The backend derives `DATABASE_URL` from the other `POSTGRES_*` vars automatically.

### 2. Gmail (IMAP)

The app connects over **IMAP with SSL** and only fetches **unread** messages from the folder set in `IMAP_FOLDER` (default `INBOX`).

**Enable IMAP in Gmail** (if needed):

1. Open [Gmail](https://mail.google.com) → **Settings** (gear) → **See all settings**
2. Go to **Forwarding and POP/IMAP**
3. Under **IMAP access**, select **Enable IMAP** → **Save Changes**

**Create an app password** (required — your normal Gmail password will not work):

1. Turn on [2-Step Verification](https://myaccount.google.com/signinoptions/two-step-verification) for your Google account
2. Open [App passwords](https://myaccount.google.com/apppasswords) (Google Account → Security → App passwords)
3. Create a password for **Mail** (or a custom name like `Office Task Tracker`)
4. Copy the 16-character password Google shows you

**Add to `.env`:**

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=you@gmail.com
IMAP_PASSWORD=your-16-char-app-password
IMAP_FOLDER=INBOX
```

Use the app password **without spaces**. Do not commit `.env` — it is gitignored.

> **Workspace accounts:** your admin may need to allow IMAP or app passwords.
> **Re-ingesting:** deleting a task removes the DB record but the email may stay read in Gmail; turn off **Mark as read** on `/settings` if you want unread messages to be picked up again.

### 3. LLM provider

Classification runs through [LiteLLM](https://docs.litellm.ai/). Set the model and the matching API key.

**OpenAI example:**

```env
LITELLM_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=sk-...
```

**Groq example:**

```env
LITELLM_MODEL=groq/qwen/qwen3-6-27b
GROQ_API_KEY=gsk_...
```

**Anthropic example:**

```env
LITELLM_MODEL=anthropic/claude-3-5-sonnet-20241022
ANTHROPIC_API_KEY=sk-ant-...
```

Only the key for your chosen provider is required. See [LiteLLM providers](https://docs.litellm.ai/docs/providers) for other models.

### 4. Ingestion defaults (optional)

For local dev or a demo, these `.env` values are a good starting point:

```env
MAIL_INGESTION_MODE=manual
MAIL_MARK_AS_READ=false
MAIL_BATCH_LIMIT=5
MAIL_POLL_HOURS=1
```

- **manual** — ingest only when you click the button (predictable for demos)
- **mark-as-read false** — emails stay unread so you can re-run ingest safely
- **batch limit** — max unread emails fetched per run

You can change all of these later on `/settings` without editing `.env`.

### 5. Verify

1. Start the stack (see [Run it](#run-it))
2. Open http://localhost:4321
3. Leave a few emails **unread** in the Gmail inbox you configured
4. Click **Ingest emails** — you should see a result like `Scraped 3, classified 2, created 2 tasks`
5. If scraping returns `Scraped 0`, check that messages are still unread and IMAP credentials are correct (backend logs will show `IMAP scrape failed` on auth errors)

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

## Mail ingestion

Ingestion can run automatically (background polling) or manually (ingest button / API). Runtime options — mode, mark-as-read, poll interval, batch size — are configured at **`/settings`** and stored in the database. Env vars seed defaults on first run:

| Env var | Default | Purpose |
| ------- | ------- | ------- |
| `MAIL_INGESTION_MODE` | `background` | `background` or `manual` |
| `MAIL_POLL_HOURS` | `1` | Hours between automatic polls |
| `MAIL_MARK_AS_READ` | `true` | Mark emails read when fetching |
| `MAIL_BATCH_LIMIT` | `25` | Max unread emails per ingest run |

| Mode | Behaviour |
| ---- | --------- |
| `background` | APScheduler polls the inbox every `poll_hours` (from settings) |
| `manual` | Nothing runs automatically; use the ingest button or `POST /api/tasks/ingest` |

Manual trigger example (uses `batch_limit` from settings when body is empty):

```sh
curl -X POST http://localhost:8000/api/tasks/ingest -H 'Content-Type: application/json' -d '{}'
```

## API

| Method | Endpoint                    | Description                              |
| ------ | --------------------------- | ---------------------------------------- |
| GET    | `/api/tasks`                | List classified tasks (newest first)     |
| GET    | `/api/tasks/{id}`           | Fetch a single task                      |
| PATCH  | `/api/tasks/{id}`           | Update task status (`todo`, `in_progress`, `done`) |
| DELETE | `/api/tasks/{id}`           | Delete a task                            |
| POST   | `/api/tasks/ingest`         | Manually scrape + classify emails        |
| GET    | `/api/settings/ingestion`   | Read ingestion settings                  |
| PATCH  | `/api/settings/ingestion`   | Update ingestion settings                |
