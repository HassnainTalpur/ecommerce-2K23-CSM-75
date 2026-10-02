# ecommerce-2K23-CSM-75

# ReadySafe - Emergency Preparedness E-Commerce Platform

## Project Overview

ReadySafe is an e-commerce platform that allows customers to purchase emergency preparedness products such as first aid supplies, emergency lighting, and safety equipment.

## Technology Stack

- Frontend: React.js
- Backend: FastAPI (Python)
- Database: PostgreSQL

## Documentation

Sprint documentation:

- [Sprint 1: Architecture & Scope Definition](docs/SPRINT_1.md)
- [Sprint 2: Catalog Data Foundation](docs/SPRINT_2.md)

## Sprint 2 - Catalog Data Foundation

Sprint 2 implements the catalog administration foundation described in `docs/SPRINT_2.md`. The implementation is under `backend/` and covers categories, products, variants, SKUs, database constraints, administrator authentication, seed data, and automated tests.

### Local setup

Requirements:

- Python 3.11+
- PostgreSQL 14+

Create a PostgreSQL database and user, then create a virtual environment and install the backend dependencies:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

Copy the environment example and update the values for your local PostgreSQL installation:

```bash
cp .env.example .env
```

Windows PowerShell equivalent:

```powershell
Copy-Item .env.example .env
```

Run the database migration:

```bash
alembic upgrade head
```

Create an administrator account. The password is supplied at the command line and is not stored in the repository:

```bash
python -m app.scripts.create_admin --email admin@example.com --name "ReadySafe Admin" --password "your-local-password"
```

Load the repeatable catalog demonstration data:

```bash
python -m app.scripts.seed_catalog
```

Start the API:

```bash
uvicorn app.main:app --reload
```

FastAPI documentation is available at `http://127.0.0.1:8000/docs`.

### Environment variables

The backend reads these values from `backend/.env`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL SQLAlchemy connection URL |
| `JWT_SECRET` | Local secret used to sign access tokens |
| `JWT_ALGORITHM` | JWT signing algorithm; defaults to `HS256` |
| `ACCESS_TOKEN_MINUTES` | Access-token lifetime in minutes |

`backend/.env` is ignored by Git. Only `.env.example` should be committed.

### Tests

Run the automated model, validation, and authorization tests from `backend/`:

```bash
pytest -q
```

The test suite uses an isolated SQLite database by default so it can run without touching local development data. The application and migration target PostgreSQL, and the migration contains PostgreSQL-side category cycle protection in addition to API validation.
