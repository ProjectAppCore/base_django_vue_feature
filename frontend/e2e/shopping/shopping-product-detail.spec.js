import { test, expect } from '../helpers/test.js';
import { SHOPPING_PRODUCT_DETAIL } from '../helpers/flow-tags.js';

/**
 * E2E tests for the product detail page.
 *
 * The detail view renders its actions under `v-if="product"`, so the test waits
 * for the add-to-cart button (product loaded) before interacting, then exercises
 * the quantity control the flow is named for. The not-found case has no UI path
 * and asserts the absence of the product actions.
 */

test.describe('Shopping — product detail', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.addInitScript(() => localStorage.clear());
  });

  test('opens a product and changes its quantity', {
    tag: [...SHOPPING_PRODUCT_DETAIL, '@role:shared', '@outcome:success'],
  }, async ({ page }) => {
    await page.goto('/catalog');
    await page.waitForLoadState('domcontentloaded');

    const response = await page.request.get('/api/products/10/');
    const product = await response.json();
    await page.getByRole('link', { name: product.title, exact: true })
      .and(page.locator('[href="/product/10"]')).click();
    await expect(page).toHaveURL(/\/product\/\d+/);

    // Actions render under v-if="product": wait for the product to load.
    await expect(page.getByTestId('add-to-cart')).toBeVisible({ timeout: 15000 });

    const quantity = page.getByTestId('quantity-value');
    await expect(quantity).toHaveText('1');
    await page.getByTestId('quantity-increment').click();
    await expect(quantity).toHaveText('2');
    await page.getByTestId('quantity-decrement').click();
    await expect(quantity).toHaveText('1');
  });

  test('a non-existent product shows no add-to-cart action', {
    tag: [...SHOPPING_PRODUCT_DETAIL, '@role:shared', '@outcome:display'],
  }, async ({ page }) => {
    // quality: allow-no-interaction (there is no UI path to a non-existent product; direct navigation is the only way to exercise the missing-product case)
    // quality: allow-deep-link (same reason: there is no product link that leads to a missing id, so a UI-driven entry point does not exist for this display case)
    await page.goto('/product/999999');
    await page.waitForLoadState('domcontentloaded');

    // Detail.vue's "Trending Products" heading sits outside the `v-if="product"` block
    // (Detail.vue:96-102), so it renders unconditionally regardless of whether the id
    // resolves. This anchors the absence check below to a page that actually rendered:
    // without it, a crashed app, a blank page, or the dev server's error overlay would
    // also satisfy `toHaveCount(0)` and pass.
    await expect(page.getByRole('heading', { name: 'Trending Products', level: 2 })).toHaveText('Trending Products');
    await expect(page.getByTestId('add-to-cart')).toHaveCount(0);
  });

  for (const { width, height } of [{ width: 835, height: 1194 }, { width: 412, height: 915 }]) {
    test.describe(`Gallery — ${width}x${height}`, () => {
      test.use({ viewport: { width, height }, hasTouch: true });

      test(`selects the second gallery image by tap at ${width}x${height}`, {
        tag: [...SHOPPING_PRODUCT_DETAIL, '@role:shared', '@outcome:success'],
      }, async ({ page }) => {
        // Product 10 is on the first catalog page in the scratch seed and CI seed.
        const response = await page.request.get('/api/products/10/');
        const product = await response.json();
        const imagePaths = product.gallery_urls.map(imageUrl => new URL(imageUrl).pathname);
        expect(imagePaths[1]).not.toBe(imagePaths[0]);
        await page.goto('/catalog');
        await page.getByRole('link', { name: product.title, exact: true })
          .and(page.locator('[href="/product/10"]')).click();
        const galleryImage = page.getByRole('tabpanel').locator('img');
        await expect.poll(() => galleryImage.evaluate(image => ({
          src: image.getAttribute('src'), complete: image.complete,
          hasWidth: image.naturalWidth > 0, hasHeight: image.naturalHeight > 0,
        }))).toEqual({ src: imagePaths[0], complete: true, hasWidth: true, hasHeight: true });
        const secondTab = page.getByRole('tab', { name: 'View image 2', exact: true });

        await secondTab.tap();

        await expect(secondTab).toHaveAttribute('aria-selected', 'true');
        await expect(galleryImage).toHaveAttribute('src', imagePaths[1]);
        await expect.poll(() => galleryImage.evaluate(image => ({
          complete: image.complete,
          hasWidth: image.naturalWidth > 0, hasHeight: image.naturalHeight > 0,
        }))).toEqual({ complete: true, hasWidth: true, hasHeight: true });
        const targets = await page.getByRole('tab').evaluateAll(tabs => tabs.map(tab => {
          const bounds = tab.getBoundingClientRect();
          return { width: bounds.width >= 44, height: bounds.height >= 44 };
        }));
        expect(targets).toEqual(product.gallery_urls.map(() => ({ width: true, height: true })));
        const documentSize = await page.evaluate(() => ({
          width: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
        }));
        expect(documentSize.scrollWidth).toBeLessThanOrEqual(documentSize.width);
      });
    });
  }

  for (const { width, height } of [{ width: 1195, height: 835 }, { width: 2560, height: 1440 }]) {
    test.describe(`Gallery — ${width}x${height}`, () => {
      test.use({ viewport: { width, height }, hasTouch: false });

      test(`selects the second gallery image by keyboard at ${width}x${height}`, {
        tag: [...SHOPPING_PRODUCT_DETAIL, '@role:shared', '@outcome:success'],
      }, async ({ page }) => {
        // Product 10 is on the first catalog page in the scratch seed and CI seed.
        const response = await page.request.get('/api/products/10/');
        const product = await response.json();
        const imagePaths = product.gallery_urls.map(imageUrl => new URL(imageUrl).pathname);
        expect(imagePaths[1]).not.toBe(imagePaths[0]);
        await page.goto('/catalog');
        await page.getByRole('link', { name: product.title, exact: true })
          .and(page.locator('[href="/product/10"]')).click();
        const galleryImage = page.getByRole('tabpanel').locator('img');
        await expect.poll(() => galleryImage.evaluate(image => ({
          src: image.getAttribute('src'), complete: image.complete,
          hasWidth: image.naturalWidth > 0, hasHeight: image.naturalHeight > 0,
        }))).toEqual({ src: imagePaths[0], complete: true, hasWidth: true, hasHeight: true });
        const secondTab = page.getByRole('tab', { name: 'View image 2', exact: true });

        const firstTab = page.getByRole('tab', { name: 'View image 1', exact: true });
        await firstTab.focus();
        await firstTab.press('ArrowRight');

        await expect(secondTab).toHaveAttribute('aria-selected', 'true');
        await expect(galleryImage).toHaveAttribute('src', imagePaths[1]);
        await expect.poll(() => galleryImage.evaluate(image => ({
          complete: image.complete,
          hasWidth: image.naturalWidth > 0, hasHeight: image.naturalHeight > 0,
        }))).toEqual({ complete: true, hasWidth: true, hasHeight: true });
        const targets = await page.getByRole('tab').evaluateAll(tabs => tabs.map(tab => {
          const bounds = tab.getBoundingClientRect();
          return { width: bounds.width >= 44, height: bounds.height >= 44 };
        }));
        expect(targets).toEqual(product.gallery_urls.map(() => ({ width: true, height: true })));
        const documentSize = await page.evaluate(() => ({
          width: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
        }));
        expect(documentSize.scrollWidth).toBeLessThanOrEqual(documentSize.width);
      });
    });
  }

  test.describe('Gallery — 1440x900', () => {
    test.use({ viewport: { width: 1440, height: 900 }, hasTouch: false });

    test('selects the second gallery image by click at 1440x900', {
      tag: [...SHOPPING_PRODUCT_DETAIL, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      // Product 10 is on the first catalog page in the scratch seed and CI seed.
      const response = await page.request.get('/api/products/10/');
      const product = await response.json();
      const imagePaths = product.gallery_urls.map(imageUrl => new URL(imageUrl).pathname);
      expect(imagePaths[1]).not.toBe(imagePaths[0]);
      await page.goto('/catalog');
      await page.getByRole('link', { name: product.title, exact: true })
        .and(page.locator('[href="/product/10"]')).click();
      const galleryImage = page.getByRole('tabpanel').locator('img');
      await expect.poll(() => galleryImage.evaluate(image => ({
        src: image.getAttribute('src'), complete: image.complete,
        hasWidth: image.naturalWidth > 0, hasHeight: image.naturalHeight > 0,
      }))).toEqual({ src: imagePaths[0], complete: true, hasWidth: true, hasHeight: true });
      const secondTab = page.getByRole('tab', { name: 'View image 2', exact: true });

      await secondTab.click();

      await expect(secondTab).toHaveAttribute('aria-selected', 'true');
      await expect(galleryImage).toHaveAttribute('src', imagePaths[1]);
      await expect.poll(() => galleryImage.evaluate(image => ({
        complete: image.complete,
        hasWidth: image.naturalWidth > 0, hasHeight: image.naturalHeight > 0,
      }))).toEqual({ complete: true, hasWidth: true, hasHeight: true });
      const targets = await page.getByRole('tab').evaluateAll(tabs => tabs.map(tab => {
        const bounds = tab.getBoundingClientRect();
        return { width: bounds.width >= 44, height: bounds.height >= 44 };
      }));
      expect(targets).toEqual(product.gallery_urls.map(() => ({ width: true, height: true })));
      const documentSize = await page.evaluate(() => ({
        width: document.documentElement.clientWidth,
        scrollWidth: document.documentElement.scrollWidth,
      }));
      expect(documentSize.scrollWidth).toBeLessThanOrEqual(documentSize.width);
    });
  });
});
