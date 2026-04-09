# Scout Leader Lesson Architect

AI-powered lesson planning tool for Scout Leaders.

## Architecture

- **Frontend**: React + Vite + Tailwind CSS (served via nginx)
- **Backend**: FastAPI + SQLAlchemy + PostgreSQL/pgvector
- **Database**: PostgreSQL with pgvector for semantic search

## Quick Start

### Development

```bash
# Start database
docker compose up db -d

# Start backend (from backend/ directory)
cd backend
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8000

# Start frontend (from frontend/ directory)
cd frontend
npm install
npm run dev
```

### Production (Docker)

```bash
cp .env.example .env
docker compose up -d --build
```

## Services

| Service   | Port | URL              |
|-----------|------|------------------|
| Frontend  | 3000 | http://localhost:3000 |
| API       | 8000 | http://localhost:8000 |
| API Docs  | 8000 | http://localhost:8000/docs |
| Database  | 5435 | postgresql://localhost:5435 |

## Deployment with Traefik

Add to your Traefik configuration:

```yaml
# Route /api/* to backend
- "traefik.http.routers.scout-api.rule=PathPrefix(`/api`)"
- "traefik.http.services.scout-api.loadbalancer.server.port=8000"

# Route /* to frontend
- "traefik.http.routers.scout-frontend.rule=PathPrefix(`/`)"
- "traefik.http.services.scout-frontend.loadbalancer.server.port=80"
```

## Data Sources

- [Canadian Path](https://www.scouts.ca/programs/sections/canadian-path.html)
- Outdoor Adventure Skills (OAS)
- Personal Achievement Badges
