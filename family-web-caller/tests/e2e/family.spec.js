import { test, expect } from '@playwright/test';

test.describe('family-web-caller', () => {
  test('login page renders', async ({ page }) => {
    await page.goto('/index.html');
    await expect(page.locator('h1')).toHaveText('家庭端视频通话');
    await expect(page.locator('#login-form')).toBeVisible();
  });

  test('dashboard requires login', async ({ page }) => {
    await page.goto('/dashboard.html');
    await page.waitForURL(/\/index\.html/);
  });

  test('login navigates to dashboard', async ({ page, request }) => {
    await request.post('/api/auth/register', {
      data: {
        email: 'test@example.com',
        password: 'password',
        full_name: 'Test User',
      },
      failOnStatusCode: false,
    });

    await page.goto('/index.html');
    await page.fill('#email', 'test@example.com');
    await page.fill('#password', 'password');

    await page.click('button[type="submit"]');
    await page.waitForURL(/\/dashboard\.html/);
    await expect(page.locator('#device-list')).toBeVisible();
  });
});
