# Target Server

A sandbox environment for testing AI Ops Engineer capabilities with FastAPI backend, PostgreSQL database, and React frontend.

## Architecture

- **Backend**: FastAPI (Python) with PostgreSQL + SQLAlchemy ORM
- **Frontend**: React + Vite (JavaScript)
- **Database**: PostgreSQL with Alembic migrations
- **Containerization**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)

### 1. Start Services with Docker Compose

```bash
# Start all services (database + backend)
docker-compose up --build

# Or start in background
docker-compose up -d --build
```

### 2. Start Frontend (in another terminal)

```bash
cd frontend
npm install
npm run dev
```

### Services

- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432

## Development

### Local Development (without Docker)

1. **Database**: Start PostgreSQL locally or use Docker:

```bash
# DB only (recommended when running backend locally)
docker compose -f docker-compose.db.yml up -d

# Or, using the main compose file:
docker compose up db -d
```

2. **Backend**: Install dependencies and run:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

3. **Frontend**: See frontend README.md

### Database Migrations

```bash
cd backend

# Create new migration
alembic revision --autogenerate -m "migration message"

# Run migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/target_server
DEBUG=true
```

You can start from `backend/env.example` and copy it to `backend/.env`.

## API Endpoints

- `GET /` - Root endpoint
- `GET /healthz` - Simple health check
- `GET /api/v1/health` - Detailed health check with metrics

## Docker Commands

```bash
# Build and start all services
docker-compose up --build

# Start only database
docker-compose up db

# Start only backend
docker-compose up api

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Remove volumes (reset database)
docker-compose down -v
```

## Project Structure

```
target_server/
├── docker-compose.yml    # Docker orchestration
├── backend/             # FastAPI application
│   ├── Dockerfile
│   ├── alembic/        # Database migrations
│   ├── app/
│   │   ├── core/       # Database, config, models
│   │   └── routes/     # API endpoints
│   └── main.py         # Application entry point
└── frontend/           # React application
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   └── services/
    └── package.json
```

## Health Checks

The system includes comprehensive health monitoring:

- **Database connectivity**
- **System metrics** (CPU, memory, disk)
- **API response times**
- **Container health**

Access the health dashboard at http://localhost:3000/health

## Troubleshooting

### Database Connection Issues

1. Ensure PostgreSQL container is running:

```bash
docker-compose ps
```

2. Check database logs:

```bash
docker-compose logs db
```

3. Reset database:

```bash
docker-compose down -v
docker-compose up db -d
```

### Backend Issues

1. Check backend logs:

```bash
docker-compose logs api
```

2. Test API directly:

```bash
curl http://localhost:8000/healthz
```

### Frontend Issues

1. Check console for errors
2. Ensure backend is running on port 8000
3. Check CORS settings if API calls fail
