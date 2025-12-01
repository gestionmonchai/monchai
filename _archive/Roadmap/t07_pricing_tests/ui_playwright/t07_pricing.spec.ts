// Playwright test skeleton for T07 (Pricing)
import { test, expect } from '@playwright/test';

const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test.describe('T07 Pricing UI', () => {
  test('Price lists page loads and filters work', async ({ page }) => {
    await page.goto(`${BASE_URL}/tarifs/listes`);
    await expect(page.getByRole('heading', { name: /listes de prix/i })).toBeVisible();
    await page.getByRole('combobox', { name: /segment/i }).selectOption('business');
    await page.getByRole('combobox', { name: /pays/i }).selectOption('FR');
    await expect(page.getByText(/EUR/i)).toBeVisible();
  });

  test('Simulator calculates and displays audit', async ({ page }) => {
    await page.goto(`${BASE_URL}/tarifs/simulateur/ui`);
    await page.getByLabel(/client/i).fill('Dupont');
    await page.getByLabel(/cuvée/i).fill('X');
    await page.getByLabel(/uom/i).fill('bottle_75');
    await page.getByLabel(/quantité/i).fill('12');
    await page.getByLabel(/date/i).fill('2025-10-10');
    await page.getByRole('button', { name: /simuler/i }).click();
    await expect(page.getByText(/total ttc/i)).toBeVisible();
    await expect(page.getByText(/remises appliquées/i)).toBeVisible();
  });
});
