# Professional structure refactor — verification

Date: 2026-09-18. Scope: `work/w6.txt`; structure, configuration and verification
only. No new analytics or frontend feature was added. All previously uncommitted
Risk Intelligence changes were preserved.

## Before / migration / final tree

The original repository mixed runtime code, command-line reports and tests in
`backend/`, with extra scripts under root and `tests/tests/`. The final layout
separates `app/core`, `app/api/routes`, analytics/ingestion/risk services,
`scripts`, and unit/integration tests. Models and schemas remain single files.

[Project structure](project_structure.md) contains the full five-level tree and
all **72 old-to-new paths**, including renamed report scripts. The
[JSON manifest](refactor_manifest.json) also records removals. Git-tracked files
used `git mv`; untracked files were renamed. No old/new source duplicates remain.
The `tree` executable is absent on this machine; the recorded equivalent was
rendered using Python without installing an unnecessary tool.

No source code, functionality, test assertion, dataset, backup or archive was
deleted. Only **44 regenerable bytecode files** and empty retired/placeholder
directories were removed. Historical source utilities remain under
`scripts/legacy` or `scripts/maintenance`; the original behaviour handoff and
PowerGrid source ZIP were relocated, not discarded.

New files: package markers, `backend/pyproject.toml`,
`backend/app/core/config.py`, `backend/app/services/ingestion/importer.py`
(extracted unchanged transactional helpers), `backend/scripts/verify_system.py`,
`backend/tests/unit/test_configuration.py`, and migration/verification documents.
Imports/mock targets use `app.*`, `scripts.*`, `tests.*`. Both `sys.path.insert`
workarounds were removed. README and maintained module documents now use current
module commands. `.env` is ignored; the placeholder `.env.example` remains tracked.

## Regression evidence

| Check | Result |
| --- | --- |
| Before-refactor baseline | 106 tests passed |
| Pure tests after refactor | 78 tests passed in the final full discovery run |
| SQLite/import/API contracts | 31 tests passed |
| Live PostgreSQL regression runners | 3 discovered tests passed |
| Full unittest discovery | **112 discovered, 112 passed, 0 failed, 0 skipped** |
| Default discovery without PostgreSQL flag | Existing 106 tests passed; 3 live checks explicitly skipped before adding 3 configuration tests |
| Seven tracked analytics modules | Executable AST identical before/after, excluding import changes |
| Complete risk output | Parsed full JSON equal before/after for all entities, including evidence, priorities, peers and summaries |
| Source datasets | All 40 CSV hashes unchanged; all five organization validations pass |
| Import CLI | Dry-run validation passes; operational PostgreSQL was not rewritten |
| Installed packages | `pip check`: no broken requirements |
| Application/script package imports | All 39 app and 31 script modules import from `/tmp` without executing reports or dataset writes |
| Preserved edge-case launcher | 15 tests pass when invoked from `/tmp` |
| Relocated report entry points | Rules, negative space, workflow, contradictions, behaviour, risk and peers run successfully; negative-space/behaviour evaluation and the preserved Alpha validator also run |
| Frontend starter | `npm run lint` and `npm run build` pass |
| Whitespace / obsolete imports | `git diff --check` passes; no old unqualified app imports or sys.path insertion remains |

Existing detection thresholds and expected test values were not altered to make
checks pass. Mechanical CLI import rewriting initially produced syntax errors;
these were corrected before running tests. Editable packaging initially omitted
the test package used by a preserved launcher; package discovery now includes it,
and all module imports were retested successfully. Sandbox restrictions on
PostgreSQL/threading and the setuptools download were handled with approved
execution outside the sandbox; they were not treated as code/test failures.

## Database and organization verification

SQLAlchemy uses the existing `backend/.env` connection. All five organizations
and source values/counts match the datasets. Relationships were checked for
asset/entity ownership, case/alert ownership, investigation and escalation parents,
and telemetry/asset ownership. Ground truth is not a database table.

| Entity | Sector | Stored peer group | Assets | Alerts | Cases | Investigations | Escalations | Telemetry |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E001 Alpha Bank | Banking | Banking | 30 | 204 | 97 | 94 | 71 | 2016 |
| E002 Beta Bank | Banking | Banking | 32 | 210 | 104 | 102 | 62 | 2304 |
| E003 Gamma Bank | Banking | NULL | 30 | 204 | 97 | 94 | 66 | 2016 |
| E004 Metro Telecom | Telecom | Telecom | 30 | 204 | 100 | 95 | 100 | 2016 |
| E005 PowerGrid Utility | Energy | Energy | 30 | 200 | 100 | 99 | 59 | 1440 |

## Engines, risk and API

- R001–R004: positive/normal/NULL/boundary tests pass, including multiple gaps;
  existing Alpha fixture expectations remain intact. Live critical-case findings:
  Alpha 5, Beta 6, Gamma 11, Metro 12, PowerGrid 14.
- R005: baseline/persistence/gap/normal cases pass; live output contains four
  blind-spot episodes. No detection threshold changed.
- Workflow Auditor: expected-versus-observed assessment retains source records,
  reasons, unknown-data issues and simultaneous gaps. HIGH prototype policy stays
  separate from CRITICAL R-rules.
- Contradictions: all supported C001–C004 synthetic tests pass. There are zero
  live contradiction findings, which is valid. No rule was weakened to invent one.
- R006–R009: copied/different/missing notes, timestamps/baselines, recurrence,
  entity isolation, duplicates and combined indicators pass. Shared live finding
  counts remain R006 329, R007 11, R008 20, R009 12. R008 here counts case-expanded
  API findings rather than detector windows.
- Aggregation retains original finding identifiers and structured evidence;
  duplicate suppression and idempotence tests pass. The risk layer still adds 15
  extra HIGH Workflow Auditor gaps without double-counting core gaps.
- Risk: all bound/zero-denominator/duplicate/size-normalization/configuration tests
  pass. Observed scores are unchanged: E001 14.62, E002 6.12, E003 12.19 (PARTIAL),
  E004 19.44, E005 16.00. All 498 priorities retain IDs, scores, findings and reasons.
- Peers: Banking comparison still uses the explicit, labelled Gamma fallback;
  stored metadata is not changed. Unrelated sectors are excluded. Telecom/Energy
  still return NO_VALID_PEERS. Zero-denominator metrics remain unavailable.
- Existing API regression: every one of 498 case responses and 152 asset telemetry
  responses passes, including global/entity/case finding parity.
- New risk APIs: risk, priorities, peer benchmarks and summaries pass for all five
  organizations, with exact response/evidence retention.

The pure tests remain in `tests/unit`; SQLite/API and live checks are under
`tests/integration`. Three original standalone live assertion scripts gained
unittest wrappers; their assertion bodies were retained. The three additional
configuration tests verify path resolution, missing configuration and explicit
environment precedence. They account for the increase from 106 to 112.

## Real FastAPI smoke and master verification

A real Uvicorn process started as `app.main:app` from `/tmp` after editable
installation, using an ephemeral local port. Root, `/health`, `/docs`,
`/openapi.json` and `/entities` returned HTTP 200; health confirmed PostgreSQL.
The process was shut down afterward. This verifies real startup/network handling
in addition to in-process API contracts.

`python -m scripts.verify_system` completed with **FINAL STATUS: PASS** for:
connection, organization listing, source values and relationships, R001–R004,
R005, Workflow Auditor, contradictions, behaviour, finding aggregation, risk,
priorities, peer benchmarking and explainability. It reports exceptions and
returns nonzero if a check fails; it does not replace unit tests.

## Commands to use now

From repository root, use the existing environment:

```bash
cd backend
source venv/bin/activate
# Already installed in this workspace; use during fresh environment setup:
python -m pip install -r requirements.txt
python -m pip install --no-deps -e .

python -m scripts.validate_all_datasets
python -m scripts.import_all_entities --dry-run
python -m scripts.verify_database
python -m scripts.verify_system

python -m unittest discover -s tests/unit -t . -p 'test_*.py'
python -m unittest discover -s tests -t . -p 'test_*.py'
SHADOWWATCH_RUN_POSTGRES_TESTS=1 python -m unittest discover -s tests -t . -p 'test_*.py' -v

uvicorn app.main:app --reload
```

The exact full-suite verification run also proved the requested shorter form:

```bash
SHADOWWATCH_RUN_POSTGRES_TESTS=1 venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
```

Reports/evaluation from `backend`:

```bash
python -m scripts.report_rules
python -m scripts.report_negative_space
python -m scripts.report_workflow --entity E001
python -m scripts.report_contradictions
python -m scripts.report_behaviour --summary
python -m scripts.report_risk
python -m scripts.report_peers
python -m scripts.validate_behaviour_ground_truth --json
```

Frontend verification from repository root:

```bash
cd frontend
npm run lint
npm run build
npm run dev
```

Do not run dataset-authoring/repair tools as verification. No actual import or
maintenance mutation was performed in this refactor; imports were exercised
against isolated SQLite fixtures and PostgreSQL source values verified read-only.

## Remaining limitations / handoff

This is a structure/functionality sign-off, not a new detection-accuracy claim.
R006 template false positives, incomplete behaviour ground-truth coverage,
Gamma's missing metadata/timestamps, small peer groups and prototype risk
calibration remain documented in the existing module reports. Historical legacy
inspectors/evaluators are retained for provenance and may be dataset-specific;
they are not authoritative multi-organization accuracy reports.

The frontend remains the Vite starter. No supervisor dashboard, cloud service,
LLM integration, new detection or score threshold change was introduced.
`git mv` staged tracked renames; content edits/new files still need normal review
and staging. No commit or push was made.
