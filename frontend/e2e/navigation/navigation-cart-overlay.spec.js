import { test, expect } from '../helpers/test.js';
import { HEADER_CART_OVERLAY } from '../helpers/flow-tags.js';

const viewports = [
  { width: 835, height: 1194 },
  { width: 412, height: 915 },
  { width: 1195, height: 835 },
  { width: 1440, height: 900 },
  { width: 2560, height: 1440 },
];

async function addProductThroughCatalog(page) {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem('e2e-cart-overlay-storage-cleared')) {
      localStorage.clear();
      sessionStorage.setItem('e2e-cart-overlay-storage-cleared', 'true');
    }
  });
  await page.goto('/catalog');
  // quality: allow-fragile-selector (select one real product from the scratch database)
  await page.locator('a[href*="/product/"]').first().click();
  await expect(page).toHaveURL(/\/product\/\d+$/);
  await page.mouse.move(0, 0);
  await page.getByTestId('add-to-cart').click();
  await page.getByRole('button', { name: 'OK', exact: true }).click();
  const storedCart = await page.evaluate(() => localStorage.getItem('cartProducts'));
  expect(JSON.parse(storedCart)).toHaveLength(1);
  return { storedCart, product: JSON.parse(storedCart)[0] };
}

async function expectHeaderTargets(page) {
  const targets = await page.getByRole('navigation', { name: 'Global' }).locator('button:visible').evaluateAll((buttons) =>
    buttons.map((button) => {
      const rect = button.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    }),
  );
  expect(Math.min(...targets.map((target) => Math.min(target.width, target.height)))).toBeGreaterThanOrEqual(44);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
}

for (const viewport of viewports) {
  test.describe(`Navigation — cart overlay @ ${viewport.width}`, () => {
    test.use({ viewport });

    test('reopens the preserved shopping cart before checkout', {
      tag: [...HEADER_CART_OVERLAY, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      const { storedCart, product } = await addProductThroughCatalog(page);
      await expectHeaderTargets(page);
      const cartButton = page.getByTestId('header-cart');
      await cartButton.click();
      const header = page.getByRole('banner');
      await expect(header.getByText('Qty 1', { exact: true })).toHaveText('Qty 1');
      const subtotal = await header.getByText(/^\$\s+/).innerText();
      await page.getByTestId('cart-close').click();
      await expect(page.getByTestId('cart-overlay')).toBeHidden();
      await cartButton.click();
      await expect(header.getByRole('heading', { name: product.title, exact: true })).toHaveText(product.title);
      await expect(header.getByText('Qty 1', { exact: true })).toHaveText('Qty 1');
      await expect(header.getByText(subtotal, { exact: true })).toHaveText(subtotal);
      expect(await page.evaluate(() => localStorage.getItem('cartProducts'))).toBe(storedCart);
      await header.getByRole('link', { name: 'Checkout', exact: true }).click();
      await page.getByTestId('cart-close').click();
      await expect(page).toHaveURL(/\/checkout$/);
    });

    test('renders the empty-cart message', {
      tag: [...HEADER_CART_OVERLAY, '@role:shared', '@outcome:display'],
    }, async ({ page }) => {
      await page.addInitScript(() => localStorage.clear());
      await page.goto('/');
      await page.getByTestId('header-cart').click();
      await expect(page.getByRole('banner').getByText('No products', { exact: true })).toHaveText('No products');
      await page.getByRole('link', { name: 'Continue Shopping', exact: true }).click();
      await page.getByTestId('cart-close').click();
      await expect(page).toHaveURL(/\/catalog$/);
    });
  });
}

// The existing backdrop close remains testable where the cart leaves a visible backdrop.
// At compact/portrait the panel fills the viewport, so the close button is the real UI path.
for (const viewport of viewports.filter(({ width }) => width >= 1024)) {
  test.describe(`Navigation — cart backdrop @ ${viewport.width}`, () => {
    test.use({ viewport });

    test('preserves the cart after closing its backdrop', {
      tag: [...HEADER_CART_OVERLAY, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      const { product } = await addProductThroughCatalog(page);
      await page.getByTestId('header-cart').click();
      await page.getByTestId('cart-overlay').click({ position: { x: 16, y: 100 } });
      await expect(page.getByTestId('cart-overlay')).toBeHidden();
      await page.getByTestId('header-cart').click();
      await expect(page.getByRole('banner').getByRole('heading', { name: product.title, exact: true })).toHaveText(product.title);
    });
  });
}
