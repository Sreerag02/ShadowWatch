# Frontend visual refinement — w8

## Audit and direction

The previous interface worked, but separate rounded metric cards, repeated icons,
organization monograms, blue selected surfaces, multicolored component bars,
large score treatments and generous panel padding gave it a generic dashboard
appearance. Repeated workspace introductions and nested report panels added
visual weight without adding evidence. Decorative gradients were not present;
there were no gradients to remove.

The revised direction is a compact supervisory workstation: grouped navigation,
neutral surfaces, clear record boundaries, technical identifiers and restrained
semantic indicators. Existing API calls, routing, filters, data selection and
analytics remain intact. No new operational features were introduced.

## Design tokens

Tokens live in `frontend/src/index.css`; layout and component rules are grouped
by purpose in `frontend/src/App.css`.

| Role | Value |
| --- | --- |
| Application background | `#0B0E11` |
| Primary / secondary surface | `#11151A` / `#151A20` |
| Selected surface | `#1A2027` |
| Border / subtle border | `#262D35` / `#1E252C` |
| Primary / secondary text | `#E7EAEE` / `#9AA4AF` |
| Muted text | `#85909C` — lighter than the suggested gray for small-text legibility |
| Accent / hover | `#4E8FA8` / `#65A5BC` |
| Critical / high | `#D65A5A` / `#C9824A` |
| Medium / low / informational | `#C1A452` / `#648B72` / `#6689A3` |

Critical/high/low text has lighter dedicated variants for dark surfaces; chart
fills use the base semantic colors. Colors in rendered components reference
central CSS tokens rather than scattered hexadecimal values.

Typography uses the system sans-serif stack, with SFMono-Regular/Consolas/
Liberation Mono for IDs, timestamps, structured evidence and scores. Page titles
are 24–26px, section headings 15px, body 12–13px, table records 12px, metadata
10–11px, and key metrics 26–28px. No remote fonts or new dependencies were added.

Spacing uses 4, 8, 12, 16, 24 and 32px tokens. Panel radius is 4px, controls 3px,
and rule tags 2px. Hierarchy uses borders and surfaces; there are no decorative
gradients or shadows. Only request loading indicators continuously animate.

## Changes by screen and component

- **Shell:** 204px sidebar (188px at intermediate widths), MONITOR/ANALYZE/REVIEW
  groups, thin active-navigation rule, sparse icons and a 48px header. All links,
  responsive menu behaviour, refresh and health reporting are preserved.
- **Overview:** one divided metric strip replaces four isolated cards. Compact
  charts use one measure accent and meaningful severity colors. Secondary counts
  sit between rules. Decorative summary icons and repeated introductions were
  removed; all count definitions remain unchanged.
- **Organizations / assessment:** compact tables without monogram tiles, technical
  entity IDs, restrained score strip, thin tabs, component bars and contributor
  rows. Partial coverage and limitations remain visible.
- **Findings:** record-oriented table with small severity indicators and rule tags.
  Finding details place rationale/review controls on the left and source evidence
  on the right. Disabled review controls remain disabled and visually subdued.
- **Priority cases / case investigation:** aligned score/count columns, compact
  queue rows, technical summary strip, simple timestamp timeline and full source
  records. Priority order and case navigation are unchanged.
- **Expected vs observed:** aligned control matrix; required-but-absent rows have
  a narrow amber rule and faint background. Labels/icons convey state without
  relying on color. Policy expectations and gap logic were not altered.
- **Negative space:** thin telemetry stems/grid, muted actual series, dashed
  baseline and labelled blind-spot interval. Actual observations, episode bounds,
  hover/focus details and absent-record handling remain unchanged.
- **Behaviour analytics:** neutral evidence panels, monospace notes and case
  links, divided observed/baseline duration values instead of nested cards.
  Original R006–R009 evidence and calculations are preserved.
- **Peer comparison:** restrained table with right-aligned entity, median, mean,
  difference and valid-peer columns. Backend context and unavailable-peer states
  are preserved; no new comparison computation or chart was added.
- **Reports:** document sections and thin dividers replace cards within cards.
  Preview content, organization selection and export availability are unchanged.
- **Audit / system:** the same typography, surface and status treatment, retaining
  honest capability states and actual health/engine responses.

Tables use sticky headers inside a bounded scroll region, subtle row separators,
hover feedback and right-aligned numerical headers/values. Pagination and full
record navigation remain available. Full reasons are accessible through existing
case/finding views; queue summaries retain their existing two-line truncation.

## Responsive and accessibility checks

Workstation checks target 1366×768, 1440×900 and 1920×1080. The existing drawer is
retained below 1000px. At narrow widths the summary becomes two columns and
assessment/evidence panels stack; wide tables and telemetry scroll within their
own regions. Labels, keyboard focus, skip navigation and reduced-motion support
remain available. No fake data is used for screenshots.

## Verification

- `npm run lint`: passed, no errors.
- `npm run build`: passed; final bundle approximately 293.65 kB JavaScript
  (90.92 kB gzip) and 28.99 kB CSS (5.92 kB gzip).
- Existing functional browser suite: **12 passed** against FastAPI/PostgreSQL,
  including navigation, filters, evidence, priorities, workflow expectations,
  peers, report/audit availability, API failure/retry, empty results and mobile.
- Visual suite: **4 passed** after final refinements. It visits 18 route/evidence
  views at 1366×768, checks page overflow and runtime errors, captures overview
  at 1440×900 and 1920×1080, and exercises loading/error/empty presentations.
  These state scenarios use test-only request interception; normal screens use
  real API responses. All 16 distinct browser checks passed across the runs.
- Desktop screens, R005–R009 evidence, workflow, reports, peer comparison,
  inventory, system/audit and the 390px mobile layout were visually inspected.
  Final refinements removed the whole-workspace focus outline (retaining control
  focus), enlarged scaled telemetry labels, aligned the findings filter row, and
  stopped short panels from stretching to fill taller neighbours.
- `git diff --check`: passed.

Temporary screenshots use `/tmp/shadowwatch-w8-*.png`; the functional suite also
writes `/tmp/shadowwatch-mobile.png`. They can be regenerated with
`npm run test:e2e`. A previous interrupted run had timeouts while analytics was
loading and a closed browser session; the subsequent fresh run passed those
checks without changes to the API or analytics.

The API client, request hook, shared data provider, route configuration, backend,
datasets and database source files were compared with pre-edit SHA-256 hashes:
**143 files checked; zero changed**.
The task makes no database writes. Review persistence and PDF export remain
existing backend limitations, not part of this visual-only change.


## Remaining visual limits

No blocking visual issues were found in the inspected layouts. Wide evidence
records and tables deliberately scroll inside bounded regions, particularly on
phones; long report/source evidence still requires vertical scrolling. Chromium
was tested, not every browser or assistive technology. No desktop packaging,
authentication or backend feature work was included.
