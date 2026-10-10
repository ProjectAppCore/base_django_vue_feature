import { test, expect } from '../helpers/test.js';
import { HEADER_SEARCH } from '../helpers/flow-tags.js';

const viewports = [
  { width: 835, height: 1194 },
  { width: 412, height: 915 },
  { width: 1195, height: 835 },
  { width: 1440, height: 900 },
  { width: 2560, height: 1440 },
];

for (const viewport of viewports) {
  test.describe(`Navigation — search @ ${viewport.width}`, () => {
    test.use({ viewport });

    test('opens the matching product through header search', {
      tag: [...HEADER_SEARCH, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      const response = page.waitForResponse((r) => r.url().endsWith('/api/products/') && r.request().method() === 'GET');
      await page.goto('/');
      const product = (await (await response).json())[0];
      const search = page.getByTestId('header-search');
      const rect = await search.boundingBox();
      expect(Math.min(rect.width, rect.height)).toBeGreaterThanOrEqual(44);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await search.click();
      // SearchBar currently identifies this input through its placeholder, not an accessible label.
      await page.getByPlaceholder('Search...', { exact: true }).fill(product.title);
      const result = page.getByRole('banner').getByRole('link').filter({ has: page.getByText(product.title, { exact: true }) }).filter({ has: page.locator('img') });
      await expect(result).toHaveCount(1);
      await result.click();
      await page.mouse.move(0, 0);
      await expect(page).toHaveURL(new RegExp(`/product/${product.id}$`));
      await expect(page.getByRole('heading', { name: product.title, exact: true })).toHaveText(product.title);
      await expect(page.getByTestId('search-overlay')).toBeHidden();
    });

    test('closes search from its existing close button', {
      tag: [...HEADER_SEARCH, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      await page.goto('/');
      await page.getByTestId('header-search').click();
      await page.getByPlaceholder('Search...', { exact: true }).fill('no-match-for-close-contract');
      await page.getByTestId('search-close').click();
      await expect(page.getByTestId('search-overlay')).toBeHidden();
      await expect(page.getByTestId('header-search')).toBeVisible();
    });
  });
}
