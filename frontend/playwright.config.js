/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  timeout: 30_000,
  use: {
    headless: true,
    baseURL: process.env.BASE_URL || 'http://localhost:5173'
  },
  testDir: './e2e'
}

module.exports = config
