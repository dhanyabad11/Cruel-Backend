# AI Cruel Backend

Python FastAPI backend for the AI Cruel deadline management system.

## Features

-   🚀 FastAPI with async support
-   🔐 JWT-based authentication
-   📊 SQLAlchemy ORM with database migrations
-   🕷️ Portal scraping capabilities
-   📱 Twilio integration for notifications
-   ⚡ Background task processing with Celery
-   🧪 Comprehensive testing suite

## Setup

1. **Create virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Environment configuration:**

    ```bash
    cp .env.example .env
    # Edit .env with your configuration
    ```

4. **Run the application:**
    ```bash
    python main.py
    ```

## API Documentation

Once running, visit:

-   Swagger UI: http://localhost:8000/docs
-   ReDoc: http://localhost:8000/redoc

## Database Migrations

```bash
# Initialize migrations
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

## Testing

```bash
pytest tests/
```

## Deployment

The backend is ready for production deployment on:

-   Railway
-   Heroku
-   DigitalOcean App Platform
-   AWS Lambda (with Mangum adapter)

## API Endpoints

### Authentication

-   `POST /api/auth/register` - Register new user
-   `POST /api/auth/login` - User login
-   `GET /api/auth/me` - Get current user

### Deadlines

-   `GET /api/deadlines` - List user deadlines
-   `POST /api/deadlines` - Create deadline
-   `PUT /api/deadlines/{id}` - Update deadline
-   `DELETE /api/deadlines/{id}` - Delete deadline

### Portals

-   `GET /api/portals` - List connected portals
-   `POST /api/portals` - Connect new portal
-   `POST /api/portals/{id}/sync` - Sync portal data
