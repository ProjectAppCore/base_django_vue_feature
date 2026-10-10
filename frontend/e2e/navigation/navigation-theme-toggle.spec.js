import { test, expect } from '../helpers/test.js';
import { THEME_TOGGLE } from '../helpers/flow-tags.js';

const viewports = [
  { width: 835, height: 1194 },
  { width: 412, height: 915 },
  { width: 1195, height: 835 },
  { width: 1440, height: 900 },
  { width: 2560, height: 1440 },
];

for (const viewport of viewports) {
  test.describe(`Navigation — theme toggle @ ${viewport.width}`, () => {
    test.use({ viewport });

    test('persists the theme selected directly from the header', {
      tag: [...THEME_TOGGLE, '@role:shared', '@outcome:success'],
    }, async ({ page }) => {
      // A fresh context is enough; clearing storage on every navigation would erase the preference under test.
      await page.goto('/');
      const toggle = page.getByRole('navigation', { name: 'Global' }).getByRole('button', { name: 'Toggle theme' });
      const rect = await toggle.boundingBox();
      expect(Math.min(rect.width, rect.height)).toBeGreaterThanOrEqual(44);
      await toggle.click();
      const dark = page.getByRole('menuitem', { name: 'Dark', exact: true });
      expect((await dark.boundingBox()).height).toBeGreaterThanOrEqual(44);
      await dark.click();
      await expect(page.locator('html')).toHaveAttribute('class', /dark/);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
      await page.reload();
      await expect(page.locator('html')).toHaveAttribute('class', /dark/);
    });
  });
}
