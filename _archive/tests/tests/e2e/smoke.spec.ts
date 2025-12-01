import { test, expect } from '@playwright/test';

const BASE = process.env.E2E_BASE_URL || 'http://localhost:8000';

test('Accueil charge: navbar visible', async ({ page }) => {
  await page.goto(BASE + '/');
  await expect(page.locator('nav.navbar')).toBeVisible();
});

test('Login page reachable', async ({ page }) => {
  await page.goto(BASE + '/auth/login/');
  await expect(page).toHaveURL(/\/auth\/login\/?/);
  await expect(page.getByRole('button', { name: /se connecter/i })).toBeVisible();
});
