import { test, expect } from '@playwright/test'
let reports
let findings
let first
const loaded = async page => { await expect(page.getByText('Loading supervisory data').first()).toHaveCount(0, { timeout: 90000 }) }
test.beforeAll(async ({ request }) => {
  const response = await request.get('/api/risk/entities', { timeout: 90000 })
  expect(response.ok()).toBeTruthy()
  reports = await response.json()
  expect(reports.length).toBeGreaterThan(0)
  first = reports[0]
  findings = reports.flatMap(r => r.findings)
})

test('overview displays actual backend counts and navigates through the shell', async ({ page }) => {
  const errors = []
  page.on('pageerror', e => errors.push(e.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Supervisory overview' })).toBeVisible()
  await expect(page.locator('.metric').filter({ hasText: 'Organizations' }).locator('.metric-value')).toHaveText(String(reports.length))
  await expect(page.locator('.metric').filter({ hasText: 'Supervisory findings' }).locator('.metric-value')).toHaveText(findings.length.toLocaleString('en'))
  await expect(page.getByText('System connected')).toBeVisible()
  await page.screenshot({ path: '/tmp/shadowwatch-overview.png', fullPage: true })
  await page.getByRole('navigation').getByRole('link', { name: 'Organizations' }).click()
  await expect(page.getByRole('heading', { name: 'Organizations', exact: true })).toBeVisible()
  expect(errors).toEqual([])
})

test('organization filters, details, all assets and backend component scores', async ({ page }) => {
  await page.goto('/entities')
  await loaded(page)
  await page.getByLabel('Search organizations').fill(first.entity_name)
  await expect(page.locator('tbody tr')).toHaveCount(1)
  await page.getByRole('link', { name: new RegExp(first.entity_name) }).click()
  await expect(page.getByRole('heading', { name: first.entity_name, exact: true })).toBeVisible()
  await expect(page.locator('.entity-score-banner')).toContainText(first.overall_score.toFixed(2))
  await page.getByRole('tab', { name: 'Assets', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Organization assets' })).toBeVisible()
  await expect(page.locator('tbody tr').first()).toBeVisible()
  await page.getByRole('tab', { name: 'Evidence', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Evidence coverage' })).toBeVisible()
})

test('findings search, structured evidence, disabled review controls and deep-link refresh', async ({ page }) => {
  const f = findings.find(f => f.rule_id === 'R006')
  await page.goto('/findings')
  await loaded(page)
  await page.getByLabel('Rule', { exact: true }).selectOption('R006')
  await expect(page.locator('tbody tr').first()).toContainText('R006')
  await page.getByLabel('Search findings').fill('no-such-source-identifier-zzz')
  await expect(page.getByRole('heading', { name: 'No matching records' })).toBeVisible()
  await page.goto(`/findings/${f.finding_id}`)
  await expect(page.getByRole('heading', { name: 'Investigation note similarity' })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Structured source evidence' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Confirm finding' })).toBeDisabled()
  await expect(page.getByRole('button', { name: 'Save review' })).toBeDisabled()
  await page.reload()
  await expect(page.getByRole('heading', { name: 'Investigation note similarity' })).toBeVisible()
})

test('all behaviour evidence types use actual backend evidence', async ({ page }) => {
  for (const [rule, title] of [['R007', 'Investigation duration comparison'], ['R008', 'Recurring incident window'], ['R009', 'Combined behavioural indicators']]) {
    const f = findings.find(f => f.rule_id === rule)
    expect(f, `${rule} live finding required by current demo dataset`).toBeTruthy()
    await page.goto(`/findings/${f.finding_id}`)
    await expect(page.getByRole('heading', { name: title })).toBeVisible()
    await expect(page.getByRole('heading', { name: 'Structured source evidence' })).toBeVisible()
  }
})

test('negative-space telemetry shows real recorded observations', async ({ page, request }) => {
  const f = findings.find(f => f.rule_id === 'R005')
  const response = await request.get(`/api/assets/${f.asset_id}/telemetry?entity_id=${f.entity_id}&limit=5000`)
  const records = await response.json()
  await page.goto(`/findings/${f.finding_id}`)
  await expect(page.getByRole('heading', { name: 'Monitoring visibility' })).toBeVisible()
  await expect(page.locator('.telemetry-chart svg')).toBeVisible()
  await expect(page.locator('.telemetry-chart circle')).toHaveCount(records.filter(r => r.event_count != null).length)
  await page.screenshot({ path: '/tmp/shadowwatch-telemetry.png', fullPage: true })
})

test('priority order and case investigation preserve backend score and workflow policy', async ({ page, request }) => {
  const ranked = reports.flatMap(r => r.priority_cases).sort((a, b) => b.priority_score - a.priority_score || a.entity_id.localeCompare(b.entity_id) || a.case_id.localeCompare(b.case_id))
  await page.goto('/priority-cases')
  await expect(page.locator('tbody tr').first()).toContainText(ranked[0].case_id)
  await page.getByRole('link', { name: ranked[0].case_id, exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Expected vs observed' })).toBeVisible()
  const response = await request.get(`/api/cases/${ranked[0].case_id}`)
  const source = await response.json()
  for (const [stage, expected] of Object.entries(source.workflow.expected)) {
    const row = page.locator('.workflow-stage').filter({ has: page.locator('strong', { hasText: new RegExp(`^${stage}$`, 'i') }) })
    await expect(row).toContainText(expected === true ? 'Required' : 'No policy')
  }
  await expect(page.locator('.case-summary-strip')).toContainText(ranked[0].priority_score.toFixed(2))
  await page.screenshot({ path: '/tmp/shadowwatch-case.png', fullPage: true })
})

test('banking peers come from backend and singleton sectors show unavailable', async ({ page }) => {
  const comparable = reports.find(r => r.peer_context.peer_entity_ids.length > 0)
  await page.goto(`/benchmarking?entity=${comparable.entity_id}`)
  await expect(page.locator('.peer-context')).toContainText(comparable.entity_name)
  for (const id of comparable.peer_context.peer_entity_ids) await expect(page.locator('.peer-context')).toContainText(reports.find(r => r.entity_id === id).entity_name)
  const singleton = reports.find(r => r.peer_context.status === 'NO_VALID_PEERS')
  await page.getByLabel('Selected organization').selectOption(singleton.entity_id)
  await expect(page.getByRole('heading', { name: 'Insufficient comparable peer data' })).toBeVisible()
})

test('report preview and audit capability are honest about persistence and export', async ({ page }) => {
  await page.goto(`/reports?entity=${first.entity_id}`)
  await expect(page.locator('.report-cover')).toContainText(first.entity_name)
  await expect(page.getByText('Live preview · PDF export is not available')).toBeVisible()
  await page.getByRole('navigation').getByRole('link', { name: 'Audit trail' }).click()
  await expect(page.getByRole('heading', { name: 'No persisted audit capability' })).toBeVisible()
})

test('workflow route and unknown routes have intentional states', async ({ page }) => {
  await page.goto('/workflow')
  await expect(page.locator('.workflow-stage')).toHaveCount(5)
  await page.goto('/unknown-supervisor-route')
  await expect(page.getByRole('heading', { name: 'Page not found' })).toBeVisible()
})

test('API failure is visible and retry recovers', async ({ page }) => {
  await page.route('**/api/risk/entities', route => route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Database operation unavailable' }) }))
  await page.goto('/')
  await expect(page.getByRole('alert')).toContainText('Database operation unavailable')
  await page.unroute('**/api/risk/entities')
  await page.getByRole('button', { name: 'Retry connection' }).click()
  await expect(page.getByRole('heading', { name: 'Organization watchlist' })).toBeVisible()
})

test('empty data is represented without fabricated organizations', async ({ page }) => {
  await page.route('**/api/risk/entities', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'No organizations available' })).toBeVisible()
  await expect(page.locator('.metric')).toHaveCount(0)
})

test('narrow layout has usable navigation and no page overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'Organization watchlist' })).toBeVisible()
  await page.getByRole('button', { name: 'Open menu' }).click()
  await page.getByRole('navigation').getByRole('link', { name: 'Organizations' }).click()
  await expect(page.getByRole('heading', { name: 'Organizations', exact: true })).toBeVisible()
  const sizes = await page.evaluate(() => ({ content: document.documentElement.scrollWidth, viewport: window.innerWidth }))
  expect(sizes.content).toBeLessThanOrEqual(sizes.viewport)
  await page.screenshot({ path: '/tmp/shadowwatch-mobile.png', fullPage: true })
})
