# Multi-organization validation and PostgreSQL import

Discovered datasets: `alpha_bank` (E001), `beta_bank` (E002), `gamma_bank`
(E003), `metro_telecom` (E004), and `powergrid_utility` (E005).

## Commands

Run strict source validation from the repository root:

```bash
python3 tests/validate_all_datasets.py
```

Strict validation reports the actual Gamma header mismatch and PowerGrid data
issues. It does not silently fix or normalize these inputs.

The explicit compatibility/exception profile is:

```bash
python3 tests/validate_all_datasets.py --gamma-adapter --allow-chronology E003 E005 --allow-source-conflicts E003 --allow-ground-truth-duplicates E005
cd backend
source venv/bin/activate
python3 import_all_entities.py --gamma-adapter --allow-chronology E003 E005 --allow-source-conflicts E003 --allow-ground-truth-duplicates E005
python3 verify_multi_entity_db.py --gamma-adapter --allow-chronology E003 E005 --allow-source-conflicts E003 --allow-ground-truth-duplicates E005
python3 -m unittest test_multi_entity_unit test_contradiction_engine_unit test_workflow_auditor_unit test_negative_space_unit
python3 test_multi_entity_analytics.py
```

Use exception flags only when accepting the reported source issues. Reports
continue to show each issue as a warning. The flags do not change timestamps,
source CSVs, analytics logic, or the database schema. Remove them after correcting
the upstream data. `--dry-run` validates without writing. `--only beta_bank
metro_telecom` selects organizations while retaining global ID validation.

## Import behavior

Only entities, assets, alerts, cases, investigations, escalations, and telemetry
are inserted, in that order. Ground truth is read for validation only and never
inserted into PostgreSQL. Each new organization uses one transaction. Any insert
or verification failure rolls back that organization's entire import. Every
source-supplied value is checked before commit.

Existing entity IDs are skipped, never overwritten or deleted. This also means
an existing partial organization is not silently repaired; use the verifier to
identify incomplete or divergent records. Other organizations can still import
if a dataset fails validation. Cross-organization duplicate IDs block both
affected folders. There is no replacement/delete option.

The verifier compares database IDs, counts, and values against each validated
source, checks entity ownership, and verifies child case links. Investigation
and escalation tables have no entity column; their ownership derives from cases.
Comparison to each organization's source detects incorrect child-case links.

## Validation exceptions and Gamma mapping

Alpha, Beta, and Metro pass strict validation. PowerGrid has two investigation
completions and two escalations after closure, plus repeated `S06` ground-truth
IDs. Gamma has three late escalation timestamps and five case severity values
that disagree with the linked alert. These are not labelled contradiction
scenarios, so strict validation rejects them. Explicit exceptions retain the
evidence for supervisory review rather than describing it as clean data.

Gamma has a different source schema. `--gamma-adapter` accepts exactly those
alternate headers and produces the canonical database columns in memory:

| Source | Database mapping |
| --- | --- |
| `Entity ID`, `Organization`, `Sector` | `entity_id`, `entity_name`, `sector` |
| Alert `alert_type` | `category`, preserving the original value |
| Severity, criticality, case status | Uppercase normalization |
| Investigation `analyst`, `investigation_notes` | `analyst_id`, `analyst_notes` |
| `Complete evidence package` / `Missing evidence` | `evidence_present=true` / `false` |
| Missing target fields | Explicit NULL, not fabricated defaults |

Source-only `Member`, case `severity`, investigation `duration_minutes` and
telemetry `event_type`/`event_status` remain in the original CSVs; there are no
equivalent database columns. Investigation/escalation `entity_id` is validated
before omitting it from those tables. No timestamps are inferred from durations.
No evidence counts are inferred from prose. No telemetry source type or logging
status is inferred from event categories/statuses. No escalation boolean is
inferred from the presence of an escalation record. Ground-truth columns are
mapped for validation only; `NONE` means expected detection is false.

Consequences for analytics: Gamma's NULL evidence counts trigger the existing
R002 semantics, and missing investigation timestamps cannot support chronology
checks. Gamma telemetry is irregular rather than hourly, so the current R005
cadence assumptions limit its usefulness on that dataset. These are source
limitations, not reasons to rewrite the working engines or invent observations.

## Analytics and tests

The four services contain no hard-coded E001/alpha_bank filter. Rule and
negative-space engines already analyze all entities. Workflow auditing takes
an entity ID, and the contradiction engine supports an optional entity filter.
No engine changes are needed.

The new tests exercise import rollback, skipping without overwrite, exclusion
of ground truth, schema/relationship/ID checks, chronology labels, explicit
Gamma mapping, and source-versus-database verification. The read-only analytics
script exercises every database entity and checks the existing Alpha findings.
The old Alpha-only evaluation scripts compare to Alpha labels; their aggregate
metrics should not be interpreted as multi-organization evaluation.
