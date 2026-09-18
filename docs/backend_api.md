# Backend API and data handoff

Run from the repository root:

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
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
| `/risk/entities` | Risk intelligence for all organizations |
| `/entities/{entity_id}/risk` | Component scores, aggregation, evidence, priorities and peers |
| `/entities/{entity_id}/priority-cases` | Review order; limit 1–1000 (default 20), offset >= 0 |
| `/entities/{entity_id}/peer-benchmark` | Same-sector/group rate comparisons excluding the selected entity |
| `/entities/{entity_id}/supervisory-summary` | Deterministic risk explanation, peer context and top five cases |

Risk outputs are prototype supervisory indicators, not official NCIIPC thresholds.
They consume existing findings and auditor results. Unknown denominators remain
unavailable; duplicate findings cannot inflate exposure scores. See
[Risk Intelligence](risk_intelligence.md) for formulas, configuration, Gamma's
stored Banking peer group, evidence coverage and new response contracts.

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
- `REVIEW_REQUIRED`: telemetry blind spots, timestamp contradictions, and R006–R009 behaviour indicators.

Behaviour findings share the request database session and the same deterministic
finding format. Investigation IDs and similarity/duration details are in
`evidence`; R008 returns one finding per affected case with the complete window
as evidence. Case requests retain the organization's full comparison baseline.
See [behaviour analytics](behaviour_analytics.md) for prototype thresholds and
[verification](devenanda_behaviour_verification.md) for accuracy limitations.

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
cd backend
source venv/bin/activate
python3 -m scripts.validate_all_datasets
python3 -m scripts.import_data ../data/beta_bank
python3 -m scripts.import_all_entities
python3 -m scripts.verify_database
python3 -m unittest tests.unit.test_behaviour_analytics tests.integration.test_backend_api tests.integration.test_ingestion tests.unit.test_contradiction_engine tests.unit.test_workflow_auditor tests.unit.test_negative_space
python3 -m tests.integration.test_backend_live
python3 -m tests.integration.test_analytics_live
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
