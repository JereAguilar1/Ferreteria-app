# Technology Stack

## Backend
- **Language**: Python 3.11+
- **Framework**: Flask 3.0.0
- **ORM**: SQLAlchemy 2.0.36
- **Migrations**: Alembic

## Database
- **Primary Database**: PostgreSQL 16

## Frontend
- **Templating**: Jinja2
- **Dynamic Interactions**: HTMX
- **CSS Framework**: Bootstrap 5

## Infrastructure
- **Containerization**: Docker & Docker Compose
- **Server**: Gunicorn 21.2.0

## Deviations
- **2026-08-18**: Migrations are managed by modifying `db/init/001_schema.sql` directly and executing `ALTER TABLE` in the running DB, instead of using Alembic.
