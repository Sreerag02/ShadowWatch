# Backend API and data handoff

Run from the repository root:

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

Configure the existing local PostgreSQL connection in `backend/.env`. Open
`http://127.0.0.1:8000/docs` for Swagger and `/openapi.json` for the API contract.
FastAPI's default Swagger UI loads its UI assets from a CDN; the JSON API,
validation, ingestion, analytics, and OpenAPI schema work without internet.
No cloud service is used to process data.

## Endpoints

| GET endpoint | Response |
| --- | --- |
| `/health` | Database connection status; 503 on failure |
| `/entities` | All organizations, ordered by entity ID; `/entities/` remains supported |
| `/entities/{entity_id}` | Metadata and asset/alert/case/finding counts |
| `/entities/{entity_id}/assets` | Entity assets; limit 1–1000 (default 100), offset >= 0 |
| `/entities/{entity_id}/cases` | Case metadata with the same pagination |
| `/cases/{case_id}` | Alert, all investigations/escalations, findings, workflow assessment |
| `/assets/{asset_id}/telemetry` | Chronological telemetry; limit 1–5000 (default 500), offset >= 0 |
| `/findings` | Unified findings, optionally filtered by `entity_id` |
| `/entities/{entity_id}/findings` | Same findings scoped to one organization |
| `/analytics/summary` | Operational counts and finding counts by rule/assessment |

Telemetry accepts inclusive `start_time` and `end_time` ISO timestamps and an
optional `entity_id` ownership filter. Use naive timestamps to match the schema;
timezone-aware inputs and reversed ranges receive 422. Unknown entities, cases,
and assets receive 404. Existing assets with no matching telemetry return `[]`.
Database failures return a sanitized 503 without credentials or SQL values.

## Case evidence and findings contracts

Case responses retain SQL NULLs. `investigations` and `escalations` are lists
because the schema permits many records per case. Legacy singular fields
`investigation` and `escalation` are populated only when exactly one corresponding
record exists; otherwise they are null. Frontend integrations should use lists.
Alert details, source IDs, investigation timestamps/notes, escalation details,
case timestamps/status and resolution are included.

Each finding has a deterministic `finding_id`, `rule_id`, `problem_type`,
`entity_id`, optional case/alert/asset IDs, severity, source, assessment, reason,
and evidence. The adapter calls existing rule evaluators and detectors; it does
not replicate thresholds or read ground truth. A case-level API returns findings
linked to that case; asset-level R005 findings belong in entity/global feeds.

- `CONFIRMED_GAP`: a supported missing stage or valid fast closure.
- `INSUFFICIENT_DATA`: a raw rule trigger that cannot establish a confirmed gap,
  for example R002 caused only by a NULL count.
- `REVIEW_REQUIRED`: telemetry blind spots and timestamp contradictions.

Counts represent individual findings, not unique affected cases or a risk score.
The feed retains rule-engine triggers, including unknown-data triggers. Workflow
HIGH-only prototype gaps remain in the case's `workflow` rather than receiving
invented rule IDs. Current engines operate on demand; results are not persisted.
For large future datasets, plan pagination/caching for the global findings feed.

## Database contract

The seven operational tables remain unchanged:

| Table | Primary key | Relationships |
| --- | --- | --- |
| entities | entity_id | Organization root |
| assets | asset_id | entity_id |
| alerts | alert_id | entity_id, optional asset_id |
| cases | case_id | entity_id, alert_id |
| investigations | investigation_id | case_id; many per case |
| escalations | escalation_id | case_id; many per case |
| telemetry | telemetry_id | entity_id, asset_id |

Names required by the schema, primary IDs, relationship IDs and alert/telemetry
timestamps are validated. Other nullable fields remain unknown when absent.
The authoritative column lengths, nullability, timestamp types and defaults are
in `database/schema.sql`; ORM classes mirror the existing tables and do not run
DDL. Severity uses LOW/MEDIUM/HIGH/CRITICAL; case status uses OPEN/IN_PROGRESS/CLOSED.
Boolean CSV values accept true/false case-insensitively; counts must be
nonnegative integers and confidence must be finite and within [0,1].

## Imports and tests

```bash
# From the repository root:
python3 tests/validate_all_datasets.py
cd backend
source venv/bin/activate
python3 import_data.py ../data/beta_bank
python3 import_all_entities.py
python3 verify_multi_entity_db.py
python3 -m unittest test_backend_api_unit test_multi_entity_unit test_contradiction_engine_unit test_workflow_auditor_unit test_negative_space_unit
python3 test_backend_integration.py
python3 test_multi_entity_analytics.py
```

Both import entry points validate before insertion and use the same transactional
insert/value-verification function. Existing entities are skipped; they are not
overwritten. Failed organization imports roll back and exit nonzero. Required
missing files, malformed/zero-byte CSVs, duplicate IDs, invalid relationships,
types and chronology are rejected. Header-only optional operational tables can
be empty legitimately. Ground truth is required for dataset validation but is
never imported. Existing Alpha/Metro commands now delegate to the safe importer.

Unit tests use an isolated in-memory database. Integration tests are read-only
against PostgreSQL and check every current case and asset response, including
source evidence counts and entity isolation. Do not use the fixture import tests
against operational PostgreSQL.
