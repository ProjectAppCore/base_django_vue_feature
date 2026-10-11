import { test, expect } from '../helpers/test.js';
import { login } from '../helpers/auth.js';
import { BACKOFFICE_USERS_LIST, BACKOFFICE_SALES_LIST } from '../helpers/flow-tags.js';
import { runDjangoShell } from '../helpers/django-shell.js';

/**
 * E2E tests for the /backoffice admin views (Users + Sales tables).
 *
 * The router only guards on `requiresAuth` (frontend/src/router/index.js) —
 * the actual staff/superuser permission check happens server-side
 * (IsAdminUser). These specs prove both halves of that contract through the
 * real UI: a signed-in non-staff customer gets a permission error instead of
 * data, and a real staff user sees the real table rows. Every test reaches
 * /backoffice by clicking the "Backoffice" link on the dashboard (not a deep
 * link), which matters most for the two staff/display specs below.
 */

const STAFF_EMAIL = 'e2e-staff@example.com';
const STAFF_PASSWORD = 'password';

async function goToBackoffice(page) {
  await page.waitForURL(/\/dashboard/);
  await page.getByRole('link', { name: 'Backoffice' }).click();
  await expect(page).toHaveURL(/\/backoffice/);
}

test.describe('Backoffice — permission errors for a non-staff user', () => {
  test('non-staff user sees a permission error on the Users table', {
    tag: [...BACKOFFICE_USERS_LIST, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    // Bug this catches: the fetchUsers catch-block error message
    // disappearing, or the router silently letting a non-staff user through
    // with a 2xx response — the router only checks requiresAuth, so the
    // permission boundary is this 403 + the error message it produces.
    await login(page); // admin@gmail.com — seeded, real customer, is_staff=False
    await page.waitForURL(/\/dashboard/);

    const usersResponse = page.waitForResponse(
      (response) => response.url().includes('/api/users/') && response.request().method() === 'GET',
    );
    await page.getByRole('link', { name: 'Backoffice' }).click();
    await expect(page).toHaveURL(/\/backoffice/);

    const response = await usersResponse;
    expect(response.status()).toBe(403);
    await expect(page.getByText(/could not load backoffice data/i)).toBeVisible();
  });

  test('non-staff user sees a permission error on the Sales table', {
    tag: [...BACKOFFICE_SALES_LIST, '@role:admin', '@outcome:error'],
  }, async ({ page }) => {
    // Bug this catches: a regression isolated to fetchSales (a distinct
    // function/request from fetchUsers) failing to reject a non-staff
    // caller. Backoffice.vue renders both fetches' errors through ONE
    // shared `error` ref at the page level (Backoffice.vue:12, a sibling of
    // both <section>s, not nested in either) — the DOM text alone cannot
    // distinguish "Users failed" from "Sales failed", so this test pins the
    // Sales-specific outcome on the network response for the sales/
    // endpoint itself, the thing that's actually distinct from the Users spec.
    await login(page);
    await page.waitForURL(/\/dashboard/);

    const salesResponse = page.waitForResponse(
      (response) => response.url().includes('/api/sales/') && response.request().method() === 'GET',
    );
    await page.getByRole('link', { name: 'Backoffice' }).click();
    await expect(page).toHaveURL(/\/backoffice/);

    const response = await salesResponse;
    expect(response.status()).toBe(403);
    await expect(page.getByText(/could not load backoffice data/i)).toBeVisible();
  });
});

test.describe('Backoffice — staff user sees real data', () => {
  test.beforeAll(() => {
    runDjangoShell(
      "from django.contrib.auth.hashers import make_password; from base_feature_app.models import User; User.objects.get_or_create(email='e2e-staff@example.com', defaults={'password': lambda: make_password('password'), 'is_active': True, 'is_staff': True})",
    );
  });

  test('staff user sees their own row in the Users table', {
    tag: [...BACKOFFICE_USERS_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // Bug this catches: UserListSerializer field drift (e.g. is_staff
    // renamed/dropped) or the v-for row rendering silently falling back to
    // the "No data" row even for a real staff account.
    await login(page, STAFF_EMAIL, STAFF_PASSWORD);
    await goToBackoffice(page);

    const usersSection = page.locator('section', { hasText: 'Users' });
    const staffRow = usersSection.locator('tr', { hasText: STAFF_EMAIL });

    await expect(staffRow).toBeVisible();
    // quality: allow-fragile-selector (positional column index is the only way to target "the Staff cell" in this unlabeled table row — no data-testid or accessible name distinguishes columns, per Backoffice.vue's markup)
    await expect(staffRow.locator('td').nth(2)).toHaveText('yes');
  });

  test('staff user sees sales rows in the Sales table', {
    tag: [...BACKOFFICE_SALES_LIST, '@role:admin', '@outcome:display'],
  }, async ({ page }) => {
    // Bug this catches: a SaleListSerializer/fetchSales regression leaving
    // the table empty for a real staff user, masked by the same "No data"
    // placeholder used for the legitimate empty-database case.
    await login(page, STAFF_EMAIL, STAFF_PASSWORD);
    await goToBackoffice(page);

    const salesSection = page.locator('section', { hasText: 'Sales' });

    await expect(salesSection.getByText('No data')).toHaveCount(0);
    await expect(salesSection.locator('tbody tr').first()).toBeVisible();
  });
});
