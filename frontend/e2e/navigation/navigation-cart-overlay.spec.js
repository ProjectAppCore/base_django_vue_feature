import { test, expect } from '../helpers/test.js';
import { HEADER_CART_OVERLAY } from '../helpers/flow-tags.js';

/**
 * E2E tests for the header cart overlay flow.
 *
 * Covers opening and closing the cart overlay from the header, and the
 * empty-cart display state.
 */

test.describe('Navigation — cart overlay', () => {
  test('reopens the preserved shopping cart', {
    tag: [...HEADER_CART_OVERLAY, '@role:shared', '@outcome:success'],
  }, async ({ page }) => {
    const viewport = page.viewportSize();
    if (viewport && viewport.width < 1024) test.skip(true, 'Desktop-only flow — cart button hidden on mobile (hidden lg:flex)');

    await page.setViewportSize({ width: 1280, height: 720 });
    await page.addInitScript(() => {
      if (!sessionStorage.getItem('e2e-cart-overlay-storage-cleared')) {
        localStorage.clear();
        sessionStorage.setItem('e2e-cart-overlay-storage-cleared', 'true');
      }
    });
    await page.goto('/catalog');
    const productLinks = page.locator('a[href*="/product/"]');
    // quality: allow-fragile-selector (select one real product from the scratch database)
    await expect(productLinks.first()).toBeVisible({ timeout: 15000 });
    await productLinks.first().click();
    await expect(page).toHaveURL(/\/product\/\d+$/);
    await page.mouse.move(0, 0);
    await page.getByRole('button', { name: /add to cart/i }).click();
    await page.getByRole('button', { name: 'OK', exact: true }).click();
    const storedCart = await page.evaluate(() => localStorage.getItem('cartProducts'));
    expect(JSON.parse(storedCart)).toHaveLength(1);

    const cartButton = page.locator('[data-testid="header-cart"]');
    await expect(cartButton).toBeVisible();
    await cartButton.click();

    const cartOverlay = page.locator('[data-testid="cart-overlay"]');
    const header = page.getByRole('banner');
    await expect(cartOverlay).toBeVisible();
    await expect(header.getByText('Qty 1', { exact: true })).toBeVisible();
    const productTitle = JSON.parse(storedCart)[0].title;
    await expect(header.getByRole('heading', { name: productTitle, exact: true })).toBeVisible();
    const subtotal = await header.getByText(/^\$\s+/).innerText();

    await page.mouse.click(200, 400);
    await expect(cartOverlay).toBeHidden();
    await cartButton.click();

    await expect(cartOverlay).toBeVisible();
    await expect(header.getByRole('heading', { name: productTitle, exact: true })).toBeVisible();
    await expect(header.getByText('Qty 1', { exact: true })).toBeVisible();
    await expect(header.getByText(subtotal, { exact: true })).toBeVisible();
    expect(await page.evaluate(() => localStorage.getItem('cartProducts'))).toBe(storedCart);

    await page.getByTestId('cart-close').click();
    await expect(cartOverlay).toBeHidden();
  });

  test('renders the empty-cart message with no products in the cart', {
    tag: [...HEADER_CART_OVERLAY, '@role:shared', '@outcome:display'],
  }, async ({ page }) => {
    const viewport = page.viewportSize();
    if (viewport && viewport.width < 1024) test.skip(true, 'Desktop-only flow — cart button hidden on mobile (hidden lg:flex)');

    // Bug this catches: the v-else empty-cart branch in ShoppingCart.vue
    // regressing — e.g. always rendering the CartProduct list (even when
    // empty) instead of "No products" + Continue Shopping, or that link
    // losing its route to the catalog.
    await page.context().clearCookies();
    await page.addInitScript(() => localStorage.clear());
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const cartButton = page.locator('[data-testid="header-cart"]');
    await expect(cartButton).toBeVisible();
    await cartButton.click();

    await expect(page.getByText('No products')).toBeVisible();
    await expect(page.getByRole('link', { name: /continue shopping/i })).toBeVisible();
  });
});
