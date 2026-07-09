# Mechamind OS - Industrial Knowledge Intelligence Platform

![Mechamind OS](https://img.shields.io/badge/Mechamind%20OS-v1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Node](https://img.shields.io/badge/Node-20%2B-green)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)

An AI-powered platform for industrial knowledge management, maintenance intelligence, and safety compliance. Built for asset-intensive industries (power, oil & gas, manufacturing, mining).

## 🎯 Problem Statement

Industrial organizations face critical challenges:
- **35% of working hours** spent searching for information (McKinsey 2024)
- **7-12 disconnected document systems** per large plant (NASSCOM-EY)
- **18-22% unplanned downtime** from knowledge fragmentation (BIS Research)
- **25% workforce retirement** in next decade taking undocumented knowledge
- **6,500+ fatal accidents/year** in Indian heavy industry (DGFASLI)

## 💡 Solution

Mechamind OS creates a **unified intelligence layer** that:
1. **Ingests** heterogeneous documents (PDFs, P&IDs, spreadsheets, videos, emails)
2. **Extracts** entities & relationships into a knowledge graph
3. **Enables** natural language queries with source citations
4. **Learns continuously** from user feedback and new solutions
5. **Predicts** maintenance needs and compliance gaps

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js 14)                     │
│  Dashboard │ Chat Copilot │ Search │ Equipment │ Maintenance │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API
┌────────────────────────────▼────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│  Documents │ Chat │ Search │ Equipment │ Maintenance │ Safety │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐         ┌───────────┐        ┌─────────┐
   │PostgreSQL│        │   Qdrant  │        │  Neo4j  │
   │+ pgvector│        │ (Vectors) │        │ (Graph) │
   └─────────┘         └───────────┘        └─────────┘
        ▲                    ▲                    ▲
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼────────┐
                    │     Redis       │
                    │  (Queue/Cache)  │
                    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- API keys for at least one LLM provider:
  - OpenAI (recommended)
  - Anthropic
  - Ollama (local, free)

### 1. Clone & Configure
```bash
git clone <repo-url>
cd meachamind-os

# Copy and edit environment
cp .env.example .env
# Add your API keys to .env
```

### 2. Start with Docker
```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# View logs
docker-compose -f docker/docker-compose.yml logs -f

# Initialize database
docker exec -it meachamind-backend alembic upgrade head

# Seed equipment catalog (100+ assets with known issues)
docker exec -it meachamind-backend python scripts/seed_database.py
```

### 3. Access Points
| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:3000 |
| **Backend API** | http://localhost:8000 |
| **API Docs** | http://localhost:8000/docs |
| **Qdrant** | http://localhost:6333 |
| **Neo4j Browser** | http://localhost:7474 (neo4j/password) |
| **PostgreSQL** | localhost:5432 (postgres/postgres) |

## 🏭 Core Features

### Phase 1: Knowledge Intelligence ✅
- **Universal Document Ingestion**: PDF, images (OCR), spreadsheets, videos (Whisper), emails
- **Knowledge Graph**: Auto-extracted entities (equipment, personnel, procedures, regulations)
- **RAG Copilot**: Chat with citations across all documents
- **Hybrid Search**: Semantic + keyword search
- **Equipment Registry**: 100+ pre-seeded assets with known failure modes
- **Crowdsourced Solutions**: Users submit/upvote fixes, system learns
- **Maintenance Intelligence**: RCA, predictive scheduling, MTBF analysis
- **Compliance Tracking**: Factory Act, OISD, PESO, IBR, Environmental regulations

### Phase 2: Safety Intelligence (Planned)
- Compound risk detection (multi-sensor correlation)
- Geospatial risk heatmaps
- Permit-to-work conflict detection
- Emergency response orchestration
- CCTV analytics integration

## 📁 Project Structure

```
meachamind-os/
├── backend/
│   ├── app/
│   │   ├── api/routes/         # API endpoints
│   │   ├── core/               # Config, security
│   │   ├── db/                 # Models, session
│   │   ├── models/             # Pydantic schemas
│   │   ├── services/
│   │   │   ├── ingestion/      # Document processing
│   │   │   ├── rag/            # RAG chain, embeddings
│   │   │   ├── vector_store/   # Qdrant client
│   │   │   ├── knowledge_graph/# Neo4j extraction
│   │   │   └── agents/         # Maintenance, Compliance, Safety
│   │   └── main.py
│   ├── scripts/seed_database.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                # Next.js 14 pages
│   │   │   ├── chat/           # Knowledge Copilot
│   │   │   ├── equipment/      # Equipment registry
│   │   │   ├── maintenance/    # Maintenance dashboard
│   │   │   ├── compliance/     # Compliance tracking
│   │   │   └── safety/         # Safety (Phase 2)
│   │   ├── components/
│   │   │   ├── ui/             # Shadcn-style components
│   │   │   ├── chat/           # Chat interface
│   │   │   └── equipment/      # Equipment cards/tables
│   │   └── lib/                # Utilities, API client
│   └── package.json
├── docker/
│   └── docker-compose.yml
├── .env.example
└── package.json (workspace root)
```

## 🔧 API Endpoints

### Documents
- `POST /api/v1/documents/upload` - Upload document
- `GET /api/v1/documents` - List documents
- `GET /api/v1/documents/{id}/chunks` - Get chunks

### Chat
- `POST /api/v1/chat` - Send message (RAG)
- `POST /api/v1/chat/stream` - Streaming response
- `GET /api/v1/chat/sessions` - List sessions

### Search
- `POST /api/v1/search` - Hybrid search
- `GET /api/v1/search/suggestions` - Autocomplete

### Equipment
- `GET /api/v1/equipment` - List equipment
- `POST /api/v1/equipment` - Create equipment
- `GET /api/v1/equipment/{id}/issues` - Known issues
- `GET /api/v1/equipment/{id}/solutions` - Solutions
- `POST /api/v1/equipment/solutions/{id}/vote` - Vote on solution

### Maintenance
- `GET /api/v1/maintenance/records` - History
- `POST /api/v1/maintenance/predict/{id}` - Predict next failure
- `POST /api/v1/maintenance/rca` - Root cause analysis

### Compliance
- `GET /api/v1/compliance/checks` - Compliance checks
- `POST /api/v1/compliance/audit/evidence-package` - Generate audit package

## 🧠 LLM Providers

Configure in `.env`:
```env
# OpenAI (recommended)
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
DEFAULT_LLM_PROVIDER=openai

# Anthropic
ANTHROPIC_API_KEY=sk-ant-xxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Ollama (local, free)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:70b
```

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## 📦 Deployment

### Production Docker
```bash
# Build production images
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml build

# Deploy
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

### Kubernetes (Helm chart planned)
```bash
helm install meachamind ./helm/meachamind
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **LangChain/LangGraph** for agent framework
- **Qdrant** for vector search
- **Neo4j** for knowledge graphs
- **Supabase** for PostgreSQL + pgvector
- **Radix UI** for accessible components
- **Tailwind CSS** for styling

---

**Built for industrial engineers, by industrial engineers.** 🏭🤖