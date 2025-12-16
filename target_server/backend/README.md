# Target Server Backend

FastAPI backend for the Universal AI Ops Engineer target server.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Update database URL in `.env` if needed.

4. Run the application:

```bash
python main.py
```

The API will be available at http://localhost:8000

## Health Check Endpoints

- `GET /healthz` - Simple health check
- `GET /api/v1/health` - Detailed health check with system metrics

## Project Structure

```
backend/
├── main.py                 # FastAPI application + server runner
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py      # Configuration settings
│   │   ├── database.py    # Database connection and session
│   │   └── models.py      # SQLAlchemy models
│   └── routes/
│       ├── __init__.py
│       └── health.py      # Health check routes
```

## Development

Run with auto-reload:

```bash
python main.py
```

Or use uvicorn directly:

```bash
uvicorn main:app --reload
```

## Docker Commands

### Start Services

```bash
# From target_server directory
# Start all services (database + backend)
docker-compose up --build

# Start in background
docker-compose up -d --build

# Start only database
docker-compose up db

# Start only backend
docker-compose up api
```

### Manage Containers

```bash
# View container status
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs db
docker-compose logs api

# Stop services
docker-compose down

# Remove volumes (reset database)
docker-compose down -v

# Restart services
docker-compose restart
```

### Database Operations in Docker

```bash
# Connect to database directly
docker-compose exec db psql -U postgres -d target_server

# Check database connectivity
docker-compose exec db pg_isready -U postgres -d target_server

# Run SQL commands
docker-compose exec db psql -U postgres -d target_server -c "SELECT * FROM items;"
```

## Database Migrations (Alembic)

### Setup

Alembic is already configured in this project. The configuration is in `alembic.ini` and migration scripts are in `alembic/versions/`.

### Basic Commands

```bash
# Apply all pending migrations (sync database)
alembic upgrade head

# Create new migration based on model changes
alembic revision --autogenerate -m "migration message"

# Show current migration status
alembic current

# Show migration history
alembic history

# Check if database is up to date
alembic check
```

### Migration Workflow

```bash
# 1. Make changes to your models in app/core/models.py
# 2. Generate migration
alembic revision --autogenerate -m "add new field to user model"

# 3. Review the generated migration in alembic/versions/
# 4. Apply the migration
alembic upgrade head

# 5. (Optional) Downgrade if needed
alembic downgrade -1
```

### Advanced Commands

```bash
# Show detailed migration info
alembic show head

# Create empty migration
alembic revision -m "empty migration"

# Apply specific migration
alembic upgrade 001

# Downgrade to specific version
alembic downgrade base
```
