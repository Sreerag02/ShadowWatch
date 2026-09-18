# ShadowWatch

Offline supervisory analytics for SOC investigation workflows. ShadowWatch turns
operational records into explainable execution gaps, monitoring blind spots,
behaviour indicators and prototype risk summaries for human review.

The backend uses Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL, Pandas and
scikit-learn. The React/Vite frontend currently contains the starter application;
a supervisor dashboard has not been implemented.

## Architecture

```text
Operational CSVs → validation → PostgreSQL
                                  ↓
                  Core R001–R005 + workflow + contradictions
                                  +
                        Behaviour R006–R009
                                  ↓
                      Normalized findings
                                  ↓
           Entity risk · Case priority · Peer benchmarks
                                  ↓
                              FastAPI
```

Ground truth is evaluation-only and is never imported or used for detection/risk.
All analytics run offline after dependencies are installed. Default Swagger UI
loads its presentation assets from a CDN; the JSON API does not require it.
Risk scores are prototype supervisory indicators, not official NCIIPC ratings.

## Layout

```text
backend/
  app/
    core/                  # environment, database, risk configuration
    api/routes/            # FastAPI endpoints
    services/
      analytics/           # existing detectors and findings adapters
      ingestion/           # validation and transactional imports
      risk/                # scoring, prioritization, benchmarks, explanations
    models.py              # SQLAlchemy models
    schemas.py             # API contracts
    main.py
  scripts/                 # module-based reports, imports and verification
    legacy/                # preserved historical diagnostics
    maintenance/           # explicit tools that can modify datasets
  tests/
    unit/                  # pure analytics/configuration tests
    integration/           # SQLite contracts and opt-in PostgreSQL regressions
  requirements.txt
  pyproject.toml
  .env.example
frontend/                  # existing React/Vite starter
data/                      # committed organization CSVs (see below)
database/schema.sql
docs/                      # design, API, migration and verification reports
work/                      # task notes, repair backups and source archives
```

The dataset directory is `data/` at repository root. Full tree and old-to-new
paths: [directory migration](docs/project_structure.md).

## Backend setup

From repository root:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install --no-deps -e .
cp .env.example .env
```

For an existing checkout, retain the existing `.env` instead of replacing it.
Set `DATABASE_URL` in `backend/.env` to your local PostgreSQL connection using
your own credentials. It is ignored by Git; `.env.example` contains placeholders.
Explicit environment variables override `.env`. Configuration always loads this
file by its absolute repository location, independent of the launch directory.
Editable installation enables `app` and `scripts` imports from any directory.
It requires standard setuptools build tooling; no new runtime dependency was
added by the refactor.

Create a PostgreSQL role/database using your local administration process. For a
fresh database only, these commands illustrate the expected names and schema:

```bash
# Run as an appropriate PostgreSQL administrator; enter your own password.
createuser --pwprompt shadowwatch_user
createdb --owner=shadowwatch_user shadowwatch_db
# From repository root, apply the schema only to a fresh database:
psql -h localhost -U shadowwatch_user -d shadowwatch_db -f database/schema.sql
```

Do not rerun schema creation on an already initialized database.

## Validate and import

From `backend`, with the virtual environment active:

```bash
python -m scripts.validate_all_datasets
python -m scripts.import_all_entities --dry-run
python -m scripts.import_all_entities
python -m scripts.verify_database
```

The importer validates first, imports operational tables transactionally and
skips existing organizations. It does not overwrite them or import ground truth.
A single-folder import is available through
`python -m scripts.import_data ../data/beta_bank`.
Maintenance scripts are outside normal setup; they can change source CSVs and
should not be run as health checks.

## Run the API

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`, `/health` or `/openapi.json`.
[API contracts](docs/backend_api.md) include findings, risk, priority cases,
peer benchmarks and supervisory summaries.

## Tests and system verification

From `backend`, with the environment active:

```bash
# Pure tests only; no database connection:
python -m unittest discover -s tests/unit -t . -p 'test_*.py'
# Pure tests and isolated SQLite/API contracts; PostgreSQL checks explicitly skip:
python -m unittest discover -s tests -t . -p 'test_*.py'
# Full verification, including read-only checks of the populated local PostgreSQL DB:
SHADOWWATCH_RUN_POSTGRES_TESTS=1 python -m unittest discover -s tests -t . -p 'test_*.py' -v
python -m scripts.verify_system
```

The environment flag deliberately separates ordinary tests from database
availability. PostgreSQL integration fixtures include known Alpha regression
cases; use the project's imported datasets for the full regression suite.
The system verifier discovers current database entities rather than requiring a
hard-coded ID. Both workflows return nonzero on failure.

Useful reports:

```bash
python -m scripts.report_rules
python -m scripts.report_behaviour --summary
python -m scripts.report_risk
python -m scripts.report_peers
python -m scripts.validate_behaviour_ground_truth --json
```

## Frontend

From repository root:

```bash
cd frontend
npm ci
npm run dev
# Verification:
npm run lint
npm run build
```

This starts the existing starter only. No dashboard feature was added during
reorganization.

## Documentation

- [Refactor verification and remaining limitations](docs/refactor_verification.md)
- [Directory tree and complete migration manifest](docs/project_structure.md)
- [Backend API](docs/backend_api.md)
- [Multi-organization ingestion](docs/multi_entity_import.md)
- [Behaviour analytics](docs/behaviour_analytics.md)
- [Risk formulas, configuration and benchmarking](docs/risk_intelligence.md)

Data-quality and detector-calibration limitations remain visible in reports.
Passing software tests does not establish detection accuracy or compliance.
