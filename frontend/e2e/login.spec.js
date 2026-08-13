const { test, expect } = require('@playwright/test')

test.describe('Login and weekly plan flow', () => {
  test('login and create weekly plan (requires E2E creds)', async ({ page }) => {
    const email = process.env.E2E_EMAIL
    const password = process.env.E2E_PASSWORD
    test.skip(!email || !password, 'E2E credentials not provided')

    await page.goto('/')
    await expect(page.locator('h1')).toHaveText(/PROVE Mentor/i)

    // fill login
    await page.fill('input[type="text"]', email)
    await page.fill('input[type="password"]', password)
    await page.click('button:has-text("Sign in")')

    // after login, summary should load
    await expect(page.locator('h2')).toHaveText(/Weekly Focus|Weekly Focus/i)

    // go to weekly plan
    await page.click('button:has-text("Weekly Plan")')
    await expect(page.locator('h2')).toHaveText(/Weekly Plan/i)

    // create plan if none
    const createBtn = page.locator('button:has-text("Create plan")')
    if(await createBtn.count() > 0) {
      await createBtn.click()
      await page.click('button:has-text("Save")')
    }

    // mark first milestone complete if present
    const markBtn = page.locator('button:has-text("Mark complete")').first()
    if(await markBtn.count() > 0) {
      await markBtn.click()
    }
  })
})
