# Shipping Company Management System

FastAPI-based shipping company management system with async PostgreSQL database, handling shipment tracking and seller registration.

## Prerequisites

- Python 3.13+
- PostgreSQL
- Redis
- Poetry

## Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd shipping-company
```

2. **Install dependencies**
```bash
poetry install
```

3. **Activate virtual environment**
```bash
poetry shell
```

4. **Create `.env` file**
```env
POSTGRES_SERVER=
POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=

JWT_SECRET=
JWT_ALGORITHM=

REDIS_HOST=
REDIS_PORT=
```

5. **Start PostgreSQL and Redis**
```bash
# Start Redis (macOS)
brew services start redis

# Start Redis (Linux)
sudo systemctl start redis

# Start Redis (manually)
redis-server

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

6. **Run database migrations**
```bash
alembic upgrade head
```

7. **Run the application**
```bash
uvicorn main:app --reload
```

The application will start at `http://localhost:8000`

## API Documentation

- Scalar Docs: http://localhost:8000/scalar
- Swagger: http://localhost:8000/docs

## Development Commands

**Run the application:**
```bash
uvicorn main:app --reload
```

**Format code:**
```bash
black .
```

**Install dependencies:**
```bash
poetry install
```

**Database migrations (Alembic):**

Alembic is already configured for async PostgreSQL migrations.

```bash
# Create a new migration
alembic revision --autogenerate -m "migration message"

# Apply all pending migrations
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history

# Downgrade to a specific revision
alembic downgrade <revision_id>

# Upgrade to a specific revision
alembic upgrade <revision_id>

# Show SQL without executing
alembic upgrade head --sql
```

**Redis commands:**
```bash
# Check Redis status
redis-cli ping

# Connect to Redis CLI
redis-cli

# Stop Redis (macOS)
brew services stop redis

# Stop Redis (Linux)
sudo systemctl stop redis

# Flush all Redis data (use with caution)
redis-cli FLUSHALL
```

**Celery commands:**

# Start celery server
celery -A worker.tasks worker --loglevel=info

# Start celery server with flower for monitoring
celery -A worker.tasks worker -E

# start flower server
 celery -A worker.tasks flower [--basic-auth=admin:verystrongpassword]


#to  start project run uvicorn server
# run redis 
# run celery
# run flower monitoring 