import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests',
  timeout: 180000,
  expect: { timeout: 60000 },
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: { baseURL: 'http://127.0.0.1:5174', headless: true, viewport: { width: 1440, height: 1050 }, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  webServer: [
    { command: 'venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8123', cwd: '../backend', url: 'http://127.0.0.1:8123/health', timeout: 60000, reuseExistingServer: false },
    { command: 'npm run dev -- --host 127.0.0.1 --port 5174 --strictPort', env: { API_PROXY_TARGET: 'http://127.0.0.1:8123', VITE_API_BASE_URL: '/api' }, url: 'http://127.0.0.1:5174', timeout: 60000, reuseExistingServer: false },
  ],
})
