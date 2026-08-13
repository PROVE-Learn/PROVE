E2E tests (Playwright)

Run the Playwright tests from `frontend/`.

Install deps and browsers:

```bash
cd frontend
npm install
npm run install-playwright
```

Set E2E credentials (optional) and run tests:

```bash
export E2E_EMAIL=you@example.com
export E2E_PASSWORD=secret
npm run test:e2e
```

If credentials aren't provided the main test will be skipped.
