# Supervisor application delivery and verification

## Delivered scope

The Vite starter is now a responsive, dark supervisor application backed by the
existing FastAPI/PostgreSQL data. No backend analytics, R001–R009 definitions,
risk weights, datasets or ground truth were changed for this frontend task.
Earlier Gamma metadata cleanup changes in the working tree are preserved.

### Pages and real-data integration

| Route | Delivered behaviour |
| --- | --- |
| `/`, `/overview` | Organization and finding counts, high/critical priorities, blind-spot/behaviour counts, risk and severity charts, organization watchlist, leading review queue |
| `/entities` | All API organizations; search, sector and risk-level filters; scores, peer groups, counts and coverage |
| `/entities/:entityId` | Backend score and components, contributors; overview/findings/priority cases/assets/benchmark/evidence tabs |
| `/findings` | Normalized findings with organization, severity, rule and problem filters; search; source and explicitly unavailable review status |
| `/findings/:findingId` | Full rationale, linked records, source evidence, specialised R005–R009 views and disabled review structure |
| `/priority-cases` | Backend scores, levels and reasons; organization/level/search filters; actual case alert metadata |
| `/cases/:caseId` | Case, alert, asset, all investigations/escalations, findings, backend priority explanation and recorded-event timeline |
| `/workflow` | Case selection and prominent expected-versus-observed comparison |
| `/benchmarking` | Backend peer membership and metrics; singleton sectors show insufficient comparable peer data |
| `/reports` | Organization report preview with scores/components, leading evidence, gap/visibility/quality indicators, priorities, peers and limitations |
| `/audit` | Honest missing-capability state; no invented reviewer activity |
| `/system` | Actual backend/database health and per-entity analytics engine availability |

Unknown routes and identifiers have intentional empty/error states. The shell
provides route navigation, organization context, refresh, health and responsive
navigation. Inputs have labels, focus states are visible, tables are keyboard
scrollable, severity is text-labelled, and the app has a skip link.

## Evidence and score integrity

- Expected vs observed reads backend workflow policy and observations. Required
  but absent stages are highlighted. Unknown expectations remain “No policy”;
  closure is not falsely described as mandatory. Missing timestamps are listed
  separately from recorded chronological events.
- R005 displays baseline, observed activity, percentage drop and episode bounds.
  The chart plots actual event-count observations, baseline and detected window.
  It does not join missing samples or invent recovery. Null counts are disclosed.
- R006 shows similarity, threshold, note excerpt and compared-case references;
  R007 shows observed duration and baseline; R008 shows recurrence window and
  linked cases; R009 shows contributing behavioural indicators. Structured source
  evidence remains available in full rather than only as a sentence.
- Risk charts use backend scores on a 0–100 scale and preserve partial coverage.
  Priority sorting uses the backend score, with deterministic IDs for ties. React
  performs display counts/filtering only; it never calculates risk or priority.
- Peer means/medians/differences and valid peer counts come from the backend.
  The selected entity is excluded by backend policy; Telecom and Energy are not
  substituted for Banking peers.
- Findings use risk-normalized IDs so priority links resolve, including additional
  Workflow Auditor findings. The live verification snapshot contained 5 entities
  and 470 normalized findings; these numbers are not hard-coded in the interface.
  Engine `CONFIRMED_GAP` assessments are distinguished from human decisions.

## Architecture and file manifest

API inventory: [all discovered endpoints, parameters and contracts](frontend_api_inventory.md).

Created:

- `frontend/src/api/client.js`: environment-based base URL, JSON validation,
  timeout, abort propagation, error messages and complete paginated reads.
- `frontend/src/hooks/useApi.js`: cancellable request state keyed by request and
  refresh revision; stale responses cannot replace current data.
- `frontend/src/context/workspace.js`, `WorkspaceProvider.jsx`: shared reports,
  registry, health, findings, priorities and refresh lifecycle.
- `frontend/src/utils/format.js`: presentation-only formatting and component labels.
- `frontend/src/components/`: `Layout`, `Common`, `Charts`, `Tables`, `Workflow`,
  `Evidence`, `Telemetry`, `Benchmark`, `ErrorBoundary`.
- `frontend/src/pages/`: `Overview`, `Entities`, `EntityDetails`, `Findings`,
  `FindingDetails`, `PriorityCases`, `CaseDetails`, `WorkflowPage`, `Benchmarking`,
  `Reports`, `Audit`, `System` (all `.jsx`).
- `frontend/.env.example`, `playwright.config.js`, `tests/supervisor.spec.js`.
- This report and `docs/frontend_api_inventory.md`.

Modified:

- `frontend/src/App.jsx`, `App.css`, `index.css`: routes and visual design.
- `frontend/index.html`, `public/favicon.svg`: application identity.
- `frontend/vite.config.js`: development/preview same-origin API proxy.
- `frontend/package.json`, `package-lock.json`: React Router, Lucide icons,
  Playwright and browser-test script.
- `frontend/.gitignore`: generated browser reports excluded.
- `frontend/README.md`, root `README.md`: accurate launch/configuration/test docs.

The bulk risk response supplies organization detail, findings, priority, peer and
report screens. Case/asset/telemetry requests load their additional source records.
Charts are lightweight HTML/SVG, with labels, units, empty states and observation
focus/hover details. There are no external analytics services or CDN UI assets.

## Review, audit and export status

The inspected backend has no review/comment persistence, reviewer identity,
audit events or PDF export. Finding review buttons and comment entry are disabled.
No localStorage, browser-only statuses or fabricated history are used. The review
filter correctly indicates unavailable persistence instead of pretending findings
are NEW. Reports are usable live previews; PDF export is explicitly unavailable.

### Minimal future backend contract (proposal, not implemented)

1. Persist a finding snapshot/identity, including entity, rule, linked records,
   evidence fingerprint, source finding IDs, algorithm/config version and first/
   last-seen times. Current findings are recomputed; define identity and changed-
   evidence behaviour before attaching durable reviews to a hash.
2. Store a review record with finding identity, status (`NEW`, `UNDER_REVIEW`,
   `CONFIRMED`, `DISMISSED`), reviewer identity, server timestamps and version.
   Store comments separately with author and server timestamp.
3. Add `GET /findings/{id}/review`, `PATCH /findings/{id}/review` (status,
   expected version; conflict on concurrent changes), and
   `POST /findings/{id}/comments`. Resolve IDs against persisted snapshots, validate
   allowed transitions and obtain reviewer identity from trusted server context.
4. Append immutable audit events transactionally with review/comment changes;
   include action, target, actor, timestamp, previous/new state and comment link.
   Expose `GET /audit-events` with entity/finding/case/actor/action filters and
   cursor pagination. A persisted finding-open event needs a separately defined
   event action; ordinary GET requests currently create no audit history.
5. Define the reviewer/session boundary before enabling writes. Cloud auth and
   desktop packaging are outside this task. PDF generation can follow separately
   once snapshot/report reproducibility requirements are defined.

## Verification

Commands from `frontend/`:

```bash
npm run lint
npm run build
npm run test:e2e
```

Lint and production build pass. Chromium E2E: **12 passed**, against a real
FastAPI process and the existing PostgreSQL database. Coverage includes:

- API-derived counts, entity navigation/filtering, backend component score,
  inventory and evidence tabs;
- finding filters, empty search, direct-link reload, R005–R009 source views;
- plotted telemetry count matched to actual API observations;
- priority ordering and case score, exact backend workflow expectations;
- valid Banking peers and unavailable singleton comparisons;
- report preview, disabled review actions and unavailable audit capability;
- workflow route, unknown route, API failure with successful retry and empty API;
- 390-pixel navigation/layout without page overflow.

Desktop overview, case investigation, telemetry evidence and mobile screenshots
were inspected. Tests save them to `/tmp/shadowwatch-{overview,case,telemetry,mobile}.png`.
The suite performs read-only database access and owns temporary servers on ports
8123 and 5174. Error/empty scenarios use test-only request interception. A React
key-spread warning found during browser testing was fixed in the request hook.

## Remaining work and limits

- Implement the persisted review/audit contract before demonstrating saved human
  decisions; add trusted reviewer identity and concurrency tests at that stage.
- Add PDF export only when needed; the report preview is implemented now.
- Deploy the SPA with route fallback and a same-origin `/api` reverse proxy.
  Vite proxy configuration alone does not configure production hosting.
- Browser checks cover Chromium and representative mobile dimensions, not every
  browser or a formal accessibility audit.
- The current bulk endpoint recomputes analytics on refresh. Large future datasets
  may require backend caching/pagination; the frontend does not silently truncate
  current inventory or telemetry. No historic trend or detection-accuracy claim
  is inferred from passing UI tests.
