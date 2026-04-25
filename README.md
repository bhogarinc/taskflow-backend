# TaskFlow Backend

Lightweight task management REST API built with FastAPI and PostgreSQL.

## Features

- **Authentication**: JWT-based auth with access and refresh tokens
- **Task Management**: Full CRUD with Kanban-style status tracking
- **Boards**: Organize tasks in boards with role-based access
- **Teams**: Group users and share boards across teams
- **API**: RESTful API with OpenAPI documentation

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

4. **Start the server**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker

```bash
cd docker
docker-compose up -d
```

The API will be available at `http://localhost:8000`.

## API Documentation

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Project Structure

```
app/
├── api/            # API routes
├── core/           # Security, logging
├── middleware/     # Custom middleware
├── models/         # SQLAlchemy models
├── schemas/        # Pydantic schemas
├── services/       # Business logic
├── config.py       # Settings
├── database.py     # Database setup
└── main.py         # Application entry
```

## Testing

```bash
pytest
```

## License

MIT