import { test, expect } from '@playwright/test'

async function settled(page) {
  await expect(page.getByText('Loading supervisory data').first()).toHaveCount(0, { timeout: 90000 })
  await expect(page.getByText('Loading alert…').first()).toHaveCount(0)
  await expect(page.getByRole('alert')).toHaveCount(0)
  await expect(page.locator('main h1')).toBeVisible()
}
async function noOverflow(page) {
  const dimensions = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: window.innerWidth }))
  expect(dimensions.width).toBeLessThanOrEqual(dimensions.viewport)
}

test('every supervisor screen remains usable at 1366 × 768', async ({ page, request }) => {
  test.setTimeout(240000)
  await page.setViewportSize({ width: 1366, height: 768 })
  const response = await request.get('/api/risk/entities', { timeout: 90000 })
  expect(response.ok()).toBeTruthy()
  const reports = await response.json()
  const report = reports[0]
  const findings = reports.flatMap(r => r.findings)
  const paths = [
    ['overview', '/'], ['organizations', '/entities'],
    ['entity', `/entities/${report.entity_id}`],
    ['entity-assets', `/entities/${report.entity_id}?tab=assets`],
    ['entity-evidence', `/entities/${report.entity_id}?tab=evidence`],
    ['findings', '/findings'], ['priority', '/priority-cases'],
    ['case', `/cases/${report.priority_cases[0].case_id}`],
    ['workflow', '/workflow'], ['benchmark', '/benchmarking'],
    ['reports', '/reports'], ['audit', '/audit'], ['system', '/system'],
    ...['R005', 'R006', 'R007', 'R008', 'R009'].map(rule => [rule, `/findings/${findings.find(f => f.rule_id === rule).finding_id}`]),
  ]
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  for (const [name, path] of paths) {
    await page.goto(path)
    await settled(page)
    await noOverflow(page)
    await page.screenshot({ path: `/tmp/shadowwatch-w8-${name}.png`, fullPage: true })
  }
  expect(errors).toEqual([])
})

for (const viewport of [{ width: 1440, height: 900 }, { width: 1920, height: 1080 }]) {
  test(`overview uses workstation space at ${viewport.width} × ${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport)
    await page.goto('/')
    await settled(page)
    await noOverflow(page)
    await expect(page.getByRole('navigation')).toBeVisible()
    await expect(page.locator('.metric')).toHaveCount(4)
    await page.screenshot({ path: `/tmp/shadowwatch-w8-${viewport.width}.png`, fullPage: true })
  })
}

test('loading, unavailable API and empty assessment keep clear visual states', async ({ page }) => {
  await page.setViewportSize({ width: 1366, height: 768 })
  let release
  const gate = new Promise(resolve => { release = resolve })
  await page.route('**/api/risk/entities', async route => {
    await gate
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Database operation unavailable' }) })
  })
  await page.goto('/')
  await expect(page.getByRole('status')).toContainText('Loading supervisory data')
  await page.screenshot({ path: '/tmp/shadowwatch-w8-loading.png', fullPage: true })
  release()
  await expect(page.getByRole('alert')).toContainText('Database operation unavailable')
  await noOverflow(page)
  await page.screenshot({ path: '/tmp/shadowwatch-w8-error.png', fullPage: true })
  await page.unroute('**/api/risk/entities')
  await page.route('**/api/risk/entities', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.reload()
  await expect(page.getByRole('heading', { name: 'No organizations available' })).toBeVisible()
  await noOverflow(page)
  await page.screenshot({ path: '/tmp/shadowwatch-w8-empty.png', fullPage: true })
})
