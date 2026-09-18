# Gamma Bank peer-group correction

E003 Gamma Bank now stores `peer_group = Banking` in both
`data/gamma_bank/entities.csv` and local PostgreSQL. Its existing Banking sector
and all other entity fields were preserved. No cases, investigations, telemetry,
ground-truth labels or other operational records were changed.

The guarded migration is `database/migrations/001_gamma_peer_group.sql`. It
requires the expected entity ID/name/sector, rejects an unexpected non-null peer
group, and only updates a NULL group. It was applied transactionally and applied
a second time to confirm idempotence. Comparison of every entity row before and
after confirmed that only Gamma's peer group changed.

For another existing database, apply from repository root using that database's
own connection credentials:

```bash
psql -h localhost -U shadowwatch_user -d shadowwatch_db -v ON_ERROR_STOP=1 -f database/migrations/001_gamma_peer_group.sql
```

Fresh imports read the corrected CSV. Existing entities are intentionally skipped
by the importer, so rerunning the importer is not a substitute for this migration.

Default `peer_group_fallbacks` is now `{}`. Missing peer metadata therefore
returns unavailable instead of being inferred from sector. Explicit custom
fallbacks remain supported and labelled for callers who opt in.

## Verification

- 112 tests discovered: **109 passed, 3 live regression tests explicitly skipped**
  in the standard discovery run. No failures.
- The master verifier ran separately against live PostgreSQL: **FINAL STATUS: PASS**,
  including all five organizations, exact source values/counts and relationships.
- Live API checks for Alpha, Beta and Gamma returned `peer_group_source=stored`
  and `stored_peer_group=Banking`. Each bank compares with the other two; peer
  members also show `source=stored`.
- All organization risk scores, metrics and peer metric comparisons are unchanged.
- Unit tests confirm that absent stored metadata has no peers by default and
  that an explicitly configured fallback is still labelled correctly.
- `docs/risk_results.json` and maintained peer documentation reflect stored metadata.

Gamma's unrelated missing investigation timestamps and unknown monitoring
expectations remain unchanged. Its risk report still correctly marks the
monitoring component unavailable; this cleanup is not a broader data repair.

Manual psql check:

```sql
SELECT entity_id, entity_name, sector, peer_group
FROM entities
WHERE entity_id IN ('E001', 'E002', 'E003')
ORDER BY entity_id;
```
