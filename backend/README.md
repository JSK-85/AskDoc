# RAG Document Q&A System — Backend

FastAPI + FAISS + Celery + Google Gemini backend for document ingestion and question-answering.

## Architecture

```
INGESTION:  POST /ingest  →  loader → chunker → embed → Celery task → FAISS + Postgres
QUERY:      POST /query   →  embed query → FAISS top-k → prompt builder → Gemini LLM → JSON
```

## Quick Start

### 1. Clone and configure
```bash
cp .env.example .env
# Fill in GEMINI_API_KEY and set API_KEY
```

### 2. Start infrastructure
```bash
docker compose up -d   # Redis + PostgreSQL
```

### 3. Python environment
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Create data directory
```bash
mkdir -p data
```

### 5. Start API server
```bash
uvicorn api.main:app --reload --port 8000
```

### 6. Start Celery worker (separate terminal)
```bash
celery -A ingestion.tasks worker --loglevel=info
```

### 7. Test
Visit http://localhost:8000/docs for Swagger UI.

## API Endpoints

| Method | Route                    | Auth | Purpose                                    |
|--------|--------------------------|------|--------------------------------------------|
| GET    | /health                  | No   | Health check — `{status: 'ok'}`            |
| POST   | /api/v1/ingest           | Yes  | Upload PDF/TXT → async ingestion           |
| GET    | /api/v1/status/{doc_id}  | No   | Poll ingestion progress                    |
| GET    | /api/v1/documents        | No   | List all ingested documents                |
| POST   | /api/v1/query            | Yes  | Ask a question → grounded answer + sources |

Auth: `X-API-KEY: <your_key>` header on POST requests.

## Tech Stack

- **API**: FastAPI + Uvicorn
- **PDF Parse**: PyMuPDF (fitz)
- **Chunking**: LangChain RecursiveCharacterTextSplitter
- **Embeddings**: all-MiniLM-L6-v2 (SentenceTransformers, local)
- **Vector DB**: FAISS (faiss-cpu)
- **Metadata**: PostgreSQL 16 + SQLAlchemy 2 (async)
- **Task Queue**: Celery 5.4 + Redis 7
- **LLM**: Gemini 1.5 Flash
