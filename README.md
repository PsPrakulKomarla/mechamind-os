# Mechamind OS

Mechamind OS is an industrial knowledge intelligence platform built for maintenance, compliance, search, and decision support. The repository contains a FastAPI backend, a Next.js frontend, and Docker Compose infrastructure for local development.

## What's Included

- Document ingestion and retrieval workflows
- Chat and search APIs for knowledge lookup
- Equipment, maintenance, compliance, and safety modules
- Knowledge graph and vector store integrations
- A Next.js UI for the main workspace and operational views

## Tech Stack

- Backend: FastAPI, Alembic, PostgreSQL, Redis, Qdrant, Neo4j
- Frontend: Next.js 14, React 18, Tailwind CSS, Radix UI
- Tooling: npm workspaces, Python 3.11+, Docker Compose

## Repository Layout

```
.
├── backend/        # FastAPI app, services, migrations, tests
├── frontend/       # Next.js app and UI components
├── docker/         # Docker Compose setup and initialization scripts
├── scripts/        # Utility scripts such as database seeding
├── shared/         # Shared schemas and types
├── package.json    # Root workspace scripts
└── README.md
```

## Prerequisites

- Node.js 20+
- Python 3.11+
- Docker and Docker Compose
- At least one LLM provider configured in `.env`

## Configuration

1. Copy `.env.example` to `.env`.
2. Set your database, vector store, graph database, and LLM credentials.
3. If you plan to run locally without cloud services, keep the default local endpoints in the example file.

The most important variables are:

- `DATABASE_URL`
- `REDIS_URL`
- `QDRANT_URL`
- `NEO4J_URI`
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OLLAMA_BASE_URL`

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

## Run Locally

Install dependencies for the workspace and each app:

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

## Common URLs

| Service | URL |
| --- | --- |
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Qdrant | http://localhost:6333 |
| Neo4j Browser | http://localhost:7474 |
| PostgreSQL | localhost:5432 |

## Available Backend Areas

The backend exposes routes for:

- Chat
- Compliance
- Documents
- Equipment
- Knowledge graph
- Maintenance
- Safety
- Search

## Scripts

Root-level scripts in `package.json` include:

- `npm run dev` - start backend and frontend together
- `npm run dev:backend` - start FastAPI with Uvicorn
- `npm run dev:frontend` - start Next.js
- `npm run db:migrate` - apply Alembic migrations
- `npm run db:seed` - seed sample data
- `npm run test` - run frontend tests and backend pytest

## Testing

```bash
cd frontend
npm test

cd ../backend
pytest tests/ -v
```

## License

MIT
