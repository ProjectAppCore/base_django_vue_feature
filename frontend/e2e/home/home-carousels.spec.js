import { test, expect } from '../helpers/test.js';
import { HOME_CAROUSEL_NAVIGATE } from '../helpers/flow-tags.js';

// Keep the existing flow/component names; trending content now uses static grids.
const viewports = [
  { width: 835, height: 1194, columns: 2 },
  { width: 412, height: 915, columns: 1 },
  { width: 1195, height: 835, columns: 5 },
  { width: 1440, height: 900, columns: 5 },
  { width: 2560, height: 1440, columns: 5 },
];

for (const viewport of viewports) {
  test.describe(`Home — trending grids @ ${viewport.width}`, () => {
    test.use({ viewport: { width: viewport.width, height: viewport.height } });

    test('opens the last product from the complete trending grid', {
      tag: [...HOME_CAROUSEL_NAVIGATE, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      const response = page.waitForResponse((r) => r.url().endsWith('/api/products/') && r.request().method() === 'GET');
      await page.goto('/');
      const products = await (await response).json();
      expect(products.length).toBeGreaterThan(5);
      const grid = page.getByTestId('product-carousel-list');
      await expect(grid.getByTestId('product-carousel-item')).toHaveCount(products.length);
      expect(await grid.evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(viewport.columns);
      const lastProduct = products.at(-1);
      const lastCard = grid.getByTestId('product-carousel-item').last();
      await lastCard.scrollIntoViewIfNeeded();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await lastCard.click();
      await page.mouse.move(0, 0);
      await expect(page).toHaveURL(new RegExp(`/product/${lastProduct.id}$`));
      await expect(page.getByRole('heading', { name: lastProduct.title, exact: true, level: 1 })).toHaveText(lastProduct.title);
    });

    test('opens the last blog from the complete trending grid', {
      tag: [...HOME_CAROUSEL_NAVIGATE, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      const response = page.waitForResponse((r) => r.url().endsWith('/api/blogs/') && r.request().method() === 'GET');
      await page.goto('/');
      const blogs = await (await response).json();
      expect(blogs.length).toBeGreaterThan(5);
      const grid = page.getByTestId('blog-carousel-list');
      await expect(grid.getByTestId('blog-carousel-item')).toHaveCount(blogs.length);
      expect(await grid.evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(' ').length)).toBe(viewport.columns);
      const lastBlog = blogs.at(-1);
      const lastCard = grid.getByTestId('blog-carousel-item').last();
      await lastCard.scrollIntoViewIfNeeded();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await lastCard.click();
      await expect(page).toHaveURL(new RegExp(`/blog/${lastBlog.id}$`));
      await expect(page.getByRole('heading', { name: lastBlog.title, exact: true, level: 1 })).toHaveText(lastBlog.title);
    });
  });
}
