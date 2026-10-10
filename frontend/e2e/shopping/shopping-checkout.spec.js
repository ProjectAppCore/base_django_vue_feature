import { test, expect } from '../helpers/test.js';
import { SHOPPING_CHECKOUT_COMPLETE } from '../helpers/flow-tags.js';

async function openCheckoutWithProduct(page) {
  await page.goto('/catalog');
  const productLinks = page.locator('a[href*="/product/"]');
  // quality: allow-fragile-selector (products come from the scratch database; select one real product)
  await expect(productLinks.first()).toBeVisible({ timeout: 15000 });
  await productLinks.first().click();
  await expect(page).toHaveURL(/\/product\/\d+$/);
  // Leave the image hover zoom, which temporarily replaces purchase controls.
  await page.mouse.move(0, 0);
  await page.getByRole('button', { name: /add to cart/i }).click();
  await page.getByRole('button', { name: 'OK', exact: true }).click();
  await page.getByTestId('header-cart').click();
  await expect(page.getByText('Qty 1', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Checkout', exact: true }).click();
  await expect(page).toHaveURL(/\/checkout$/);
  await page.getByTestId('cart-close').click();
  await expect(page.getByTestId('cart-overlay')).toBeHidden();
  await expect(page.getByText('Qty 1', { exact: true })).toBeVisible();
  const cart = await page.evaluate(() => JSON.parse(localStorage.getItem('cartProducts')));
  expect(cart).toHaveLength(1);
  return cart;
}

async function fillCheckout(page) {
  const fields = {
    email: 'buyer@example.com', 'card-number': '4111111111111111',
    expiry: '12/28', cvc: '123', address: '123 Main St',
    city: 'City', state: 'State', 'postal-code': '12345',
  };
  for (const [field, value] of Object.entries(fields)) {
    await page.getByTestId(`checkout-${field}`).fill(value);
  }
}

test.describe('Shopping — checkout', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.addInitScript(() => {
      if (!sessionStorage.getItem('e2e-checkout-storage-cleared')) {
        localStorage.clear();
        sessionStorage.setItem('e2e-checkout-storage-cleared', 'true');
      }
    });
  });

  test('confirms a real order creation', {
    tag: [...SHOPPING_CHECKOUT_COMPLETE, '@role:shared', '@outcome:success'],
    timeout: 60000,
  }, async ({ page }) => {
    const cart = await openCheckoutWithProduct(page);
    await fillCheckout(page);
    const created = page.waitForResponse((response) =>
      response.url().endsWith('/api/create-sale/') && response.request().method() === 'POST',
    );

    await page.getByRole('button', { name: 'Pay Now', exact: true }).click();
    const response = await created;

    expect(response.status()).toBe(201);
    expect(response.request().postDataJSON().sold_products).toEqual([
      { product_id: cart[0].id, quantity: cart[0].quantity },
    ]);
    await expect(page.getByRole('heading', { name: 'Order created successfully', exact: true })).toBeVisible();
    await expect(page).toHaveURL(/\/$/);
    await page.getByRole('button', { name: 'OK', exact: true }).click();
    await page.getByTestId('header-cart').click();
    await expect(page.getByText('No products', { exact: true })).toBeVisible();
  });

  test('validates required checkout fields', {
    tag: [...SHOPPING_CHECKOUT_COMPLETE, '@role:shared', '@outcome:error'],
  }, async ({ page }) => {
    await openCheckoutWithProduct(page);

    await page.getByRole('button', { name: 'Pay Now', exact: true }).click();

    await expect(page).toHaveURL(/\/checkout$/);
    expect(await page.getByTestId('checkout-email').evaluate((input) => input.validity.valueMissing)).toBe(true);
    await expect(page.getByText('Qty 1', { exact: true })).toBeVisible();
  });

  const failures = [
    { name: 'HTTP 400', reply: (route) => route.fulfill({ status: 400, json: { error: 'Product unavailable' } }) },
    { name: 'HTTP 500', reply: (route) => route.fulfill({ status: 500, json: { error: 'Server unavailable' } }) },
    { name: 'network failure', reply: (route) => route.abort('failed') },
  ];
  for (const failure of failures) {
    test(`preserves checkout after ${failure.name}`, {
      tag: [...SHOPPING_CHECKOUT_COMPLETE, '@role:shared', '@outcome:failure'],
      timeout: 60000,
    }, async ({ page }) => {
      const cart = await openCheckoutWithProduct(page);
      await fillCheckout(page);
      await page.route('**/api/create-sale/', failure.reply);

      await page.getByRole('button', { name: 'Pay Now', exact: true }).click();

      await expect(page.getByRole('alert')).toHaveText(
        'We could not create your order. Your cart has been kept. Please try again.',
      );
      await expect(page).toHaveURL(/\/checkout$/);
      await expect(page.getByTestId('checkout-email')).toHaveValue('buyer@example.com');
      await expect(page.getByTestId('checkout-address')).toHaveValue('123 Main St');
      await expect(page.getByText('Qty 1', { exact: true })).toBeVisible();
      expect(await page.evaluate(() => JSON.parse(localStorage.getItem('cartProducts')))).toEqual(cart);
      await expect(page.getByRole('button', { name: 'Pay Now', exact: true })).toBeEnabled();
    });
  }
});
