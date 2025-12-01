import { test, expect } from '@playwright/test';

const BASE = process.env.E2E_BASE_URL || 'http://localhost:8000';

// Snapshot du header (navbar) pour détection visuelle
// Exécuter une première fois pour générer le snapshot, puis vérifier les diffs

test('Header pas cassé', async ({ page }) => {
  await page.goto(BASE + '/');
  await expect(page.locator('nav.navbar')).toHaveScreenshot('header.png', {
    maxDiffPixelRatio: 0.01,
  });
});
