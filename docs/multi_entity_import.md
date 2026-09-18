# Multi-organization validation and PostgreSQL import

All five datasets now pass strict validation and are present in PostgreSQL:
Alpha Bank (E001), Beta Bank (E002), Gamma Bank (E003), Metro Telecom (E004),
and PowerGrid Utility (E005). No exception flags are needed.

## Commands

From the repository root:

```bash
cd backend
source venv/bin/activate
python3 -m scripts.validate_all_datasets
python3 -m scripts.import_all_entities
python3 -m scripts.verify_database
python3 -m unittest tests.integration.test_ingestion tests.unit.test_contradiction_engine tests.unit.test_workflow_auditor tests.unit.test_negative_space
python3 -m tests.integration.test_analytics_live
```

The importer discovers folders, validates each source and cross-organization
IDs, then inserts only entities, assets, alerts, cases, investigations,
escalations, and telemetry. Ground truth is used for validation only; it is
never inserted into PostgreSQL or supplied to detection engines.

Existing organizations are skipped without changes. Each new organization
uses one transaction; any insert or value-verification failure rolls back that
organization. Every supplied value is compared before commit. The verifier
compares IDs, counts, values and ownership against all sources. Child record
ownership is checked through case links and compared with the source folder.

`--dry-run` validates without writes. `--only gamma_bank powergrid_utility`
selects organizations while retaining cross-organization ID validation.
There is no deletion/replacement option. Existing partial organizations require
separate review; they are not overwritten automatically.

## Authorized dataset repairs

The user requested Gamma and PowerGrid fixes after validation identified their
issues. Original files are backed up in:

`work/dataset_backups/before_gamma_powergrid_repair/`

`docs/dataset_repairs.json` records field-level before/after values and reasons.
`backend/scripts/maintenance/repair_organization_datasets.py` records the one-shot repair procedure;
it refuses to rerun while its backup exists. Do not rerun it during normal setup.

Gamma's eight CSVs were converted to canonical headers. Severity, criticality,
and case status were normalized to uppercase. Five alerts were aligned with the
explicit CRITICAL severity of their source cases, preserving their short closure
durations. Three synthetic escalation timestamps were moved to the case closure
boundary. These are documented synthetic corrections, not recovered event times.

Gamma mappings:

- Entity ID/Organization/Sector become entity_id/entity_name/sector.
- Alert alert_type becomes category without changing its text.
- Investigation analyst/investigation_notes become analyst_id/analyst_notes.
- Complete evidence package/Missing evidence become evidence_present true/false.
- Ground-truth expected_rule becomes problem_type; NONE means expected_detection false.
- Missing database fields remain blank (SQL NULL).

Source-only Member, case severity, investigation duration_minutes, and telemetry
event_type/event_status remain available in the original backups. No timestamps,
evidence counts, escalation flags, or telemetry source/status were invented.

PowerGrid's two deliberately short case closure intervals were preserved. Their
investigation start/completion and escalation timestamps were regenerated within
those intervals at one-third, two-thirds and five-sixths of the interval,
respectively. The LOW alert attached to the labelled FAST_CRITICAL_CLOSURE case
E005-C0021 was corrected to CRITICAL. Two duplicate S06 ground-truth IDs became
S06-2 and S06-3, preserving the three distinct case labels.

## Remaining data limitations

Schema/relationship validity does not prove measurement completeness or detection
accuracy. Gamma has no investigation timestamps or evidence counts. The existing
R002 rule treats NULL evidence counts as missing evidence even where the source
says a complete evidence package exists. Its escalation flags are unknown, and
its telemetry is irregular rather than hourly, limiting the current R005 model.
No analytics logic was changed to hide these limitations.

## Verified results

| Entity | Assets | Alerts | Cases | Investigations | Escalations | Telemetry |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| E001 Alpha | 30 | 204 | 97 | 94 | 71 | 2016 |
| E002 Beta | 32 | 210 | 104 | 102 | 62 | 2304 |
| E003 Gamma | 30 | 204 | 97 | 94 | 66 | 2016 |
| E004 Metro | 30 | 204 | 100 | 95 | 100 | 2016 |
| E005 PowerGrid | 30 | 200 | 100 | 99 | 59 | 1440 |

All 42 unit tests pass. Strict validation, cross-organization ID uniqueness,
source/database comparison and ownership checks pass. All four analytics modules
execute across the database organizations. Alpha retains its five critical-case
findings and two R005 findings; all organizations currently have zero C001-C004
contradictions. These are execution/regression results, not multi-entity precision
or recall estimates.

The four analytics services contain no E001/alpha_bank filters and required no
modifications. Existing Alpha-only ground-truth evaluation scripts should not
be interpreted as multi-organization evaluation.
