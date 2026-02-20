# ConceptLens

AI-powered concept readiness analysis platform for instructors and students.

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ / pnpm
- PostgreSQL database (or Neon serverless)
- OpenAI API key (for AI / chat features)

### Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env with your DATABASE_URL and OPENAI_API_KEY

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Backend runs at `http://localhost:8000`. API docs at `/docs`.

### Frontend Setup

```bash
cd frontend
cp .env.example .env
# Edit .env if backend is not on localhost:8000

pnpm install
pnpm dev
```

Frontend runs at `http://localhost:5173`.

### Environment Variables

#### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | — | PostgreSQL connection string |
| `OPENAI_API_KEY` | Yes (for AI) | `""` | OpenAI API key |
| `OPENAI_MODEL` | No | `gpt-4o` | Model name |
| `OPENAI_TIMEOUT_SECONDS` | No | `30` | Request timeout |
| `OPENAI_MAX_RETRIES` | No | `2` | Retry count |
| `INSTRUCTOR_USERNAME` | No | `admin` | Basic Auth username |
| `INSTRUCTOR_PASSWORD` | No | `admin` | Basic Auth password |
| `STUDENT_TOKEN_EXPIRY_DAYS` | No | `30` | Token validity |
| `EXPORT_DIR` | No | `/tmp/conceptlens_exports` | Export output path |

#### Frontend (`frontend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | No | `http://localhost:8000` | Backend API URL |
| `VITE_INSTRUCTOR_USERNAME` | No | `""` | Pre-fill login username |
| `VITE_INSTRUCTOR_PASSWORD` | No | `""` | Pre-fill login password |

## Architecture

```
frontend/          React + Vite + Tailwind
  app/
    services/      Typed API client + service modules
    pages/         UploadWizard, Dashboard, Trace, StudentReport
    components/    Reusable UI components (DAG, Heatmap, etc.)
    constants/     Placeholder definitions

backend/           FastAPI + SQLAlchemy + Alembic
  app/
    routers/       REST endpoints
    services/      Business logic
    models/        ORM models
    schemas/       Pydantic request/response models
```
