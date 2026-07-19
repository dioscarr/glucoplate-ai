const { test, expect } = require('@playwright/test');

function collectRuntimeFailures(page) {
  const failures = [];
  page.on('pageerror', error => failures.push(`pageerror: ${error.message}`));
  page.on('console', message => {
    if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) {
      failures.push(`console.error: ${message.text()}`);
    }
  });
  page.on('response', response => {
    const url = new URL(response.url());
    if (url.origin === 'http://127.0.0.1:8000' && response.status() >= 500) {
      failures.push(`http ${response.status()}: ${url.pathname}`);
    }
  });
  page.on('requestfailed', request => {
    const url = new URL(request.url());
    if (url.origin === 'http://127.0.0.1:8000') {
      failures.push(`requestfailed: ${request.method()} ${url.pathname}`);
    }
  });
  return failures;
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/user-data/recipes', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: '[]',
  }));
  await page.route('**/api/recipes/list', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: '[]',
  }));
  await page.route('**/api/firebase-auth/config', route => route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ client_configured: false, firebase_config: {} }),
  }));
});

test('application shell loads without browser runtime failures', async ({ page }) => {
  const failures = collectRuntimeFailures(page);
  await page.goto('/');
  await expect(page).toHaveTitle('GlucoPlate AI');
  await expect(page.getByRole('heading', { name: 'Choose a cuisine. Pick a dish. Generate it.' })).toBeVisible();
  await expect(page.locator('#enterpriseAuthGate')).toBeVisible();

  expect(failures, failures.join('\n')).toEqual([]);
});

test('cached enterprise session restores the signed-in shell safely', async ({ page }) => {
  const failures = collectRuntimeFailures(page);
  await page.addInitScript(session => {
    localStorage.setItem('glucoplate_firebase_session', JSON.stringify(session));
    localStorage.setItem('glucoplate_firebase_id_token', 'playwright-placeholder-token');
  }, {
    user: { uid: 'e2e-user', email: 'e2e@example.test', name: 'Playwright Cook' },
    enterprise: { id: 'e2e-enterprise', company_name: 'GlucoPlate Test Kitchen', role: 'member' },
  });

  await page.goto('/');
  await expect(page.locator('#enterpriseAuthGate')).toHaveClass(/hidden/);
  await page.locator('.tab[data-view="discoverView"]').click();
  await expect(page.getByRole('heading', { name: '1. Choose a cuisine' })).toBeVisible();
  await page.getByRole('button', { name: 'Profile', exact: true }).click();
  await expect(page.locator('#firebaseAuthPanel')).toContainText('Playwright Cook');
  await expect(page.locator('#firebaseAuthPanel')).toContainText('GlucoPlate Test Kitchen');

  expect(failures, failures.join('\n')).toEqual([]);
});
