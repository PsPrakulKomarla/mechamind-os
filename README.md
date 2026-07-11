# Mechamind OS

Mechamind OS is an industrial knowledge workspace made of a FastAPI backend, a Next.js frontend, and a Docker Compose stack for local development. The codebase is partly production-style and partly prototype: the chat flow is wired to the backend, while some screens such as the equipment registry use local mock data in the UI.

## What It Does Today

- Runs a FastAPI API with health, chat, search, document, equipment, maintenance, compliance, safety, and knowledge-graph route modules
- Provides a Next.js dashboard with routes for the main dashboard, Knowledge Copilot chat, and an equipment registry view
- Uses PostgreSQL with pgvector, Redis, Qdrant, and Neo4j when started through Docker Compose
- Supports document upload and background ingestion on the backend
- Uses the chat endpoint to answer questions with RAG context and citations when the LLM and data sources are configured

## Current UI Behavior

- Dashboard cards and activity lists are static UI data
- The Knowledge Copilot page sends messages to `POST /api/v1/chat`
- The equipment registry page is currently local/mock data, not backed by the API yet
- The navigation shows more areas than are fully implemented as separate frontend pages

## Repository Layout

```
.
├── backend/        # FastAPI app, Alembic migrations, database models, services
├── frontend/       # Next.js app, pages, and UI components
├── docker/         # Docker Compose stack and database init SQL
├── scripts/        # Utility scripts such as database seeding
├── shared/         # Shared schemas and types
├── package.json    # Root workspace scripts
└── README.md
```

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Alembic, Celery
- Data services: PostgreSQL, Redis, Qdrant, Neo4j
- Frontend: Next.js 14, React 18, Tailwind CSS, Radix UI
- Tooling: npm workspaces, Python 3.11+, Docker Compose

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker and Docker Compose
- At least one LLM provider configured in `.env` if you want chat responses to work

## Configuration

Create a root `.env` file and set the service credentials and local URLs the backend expects.

Important variables include:

- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL`
- `NEO4J_URI`
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OLLAMA_BASE_URL`

The backend defaults are defined in [backend/app/config.py](backend/app/config.py).

## Run With Docker

From the repository root:

```bash
docker-compose -f docker/docker-compose.yml up -d
```

Useful follow-up commands:

```bash
docker-compose -f docker/docker-compose.yml logs -f
docker exec -it meachamind-backend alembic upgrade head
docker exec -it meachamind-backend python scripts/seed_database.py
```

This starts:

- PostgreSQL on `5432`
- Redis on `6379`
- Qdrant on `6333`
- Neo4j on `7474` and `7687`
- The FastAPI backend on `8000`
- The Next.js frontend on `3000`
- Celery worker and Celery beat

## Run Locally

Install dependencies for the root workspace, backend, and frontend:

```bash
npm install
cd backend
pip install -r requirements.txt
cd ../frontend
npm install
```

Start both apps from the repository root:

```bash
npm run dev
```

Or start them separately:

```bash
npm run dev:backend
npm run dev:frontend
```

## Key Routes

### Frontend

- `/` dashboard
- `/chat` Knowledge Copilot
- `/equipment` equipment registry

### Backend

- `GET /health` health check
- `GET /` basic service info
- `POST /api/v1/chat` chat with RAG context
- `POST /api/v1/search` hybrid search entry point
- `GET/POST /api/v1/documents` document operations and upload flow

## Notes

- Authentication is not fully wired through the backend yet; some chat session code still uses a placeholder user id
- Several backend route modules exist even if the matching frontend page is not finished
- The backend API docs are available at `/docs` when debug mode is enabled

## Testing

```bash
cd frontend
npm test

cd ../backend
pytest tests/ -v
```
