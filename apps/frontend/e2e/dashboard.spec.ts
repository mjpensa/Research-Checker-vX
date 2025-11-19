/**
 * E2E tests for Dashboard page.
 * Tests pipeline creation, document upload, and navigation.
 */

import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });

  test('should display dashboard title', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /research checker/i })).toBeVisible();
  });

  test('should display create pipeline button', async ({ page }) => {
    const createButton = page.getByRole('button', { name: /create new pipeline/i });
    await expect(createButton).toBeVisible();
  });

  test('should create a new pipeline', async ({ page }) => {
    // Mock API response
    await page.route('**/api/v1/pipelines/', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'test-pipeline-id-123',
            name: 'Pipeline 12/19/2024',
            status: 'pending',
            total_claims: 0,
            total_dependencies: 0,
            total_contradictions: 0,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            documents: []
          })
        });
      }
    });

    // Click create button
    const createButton = page.getByRole('button', { name: /create new pipeline/i });
    await createButton.click();

    // Wait for alert or success message
    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain('Pipeline created');
      await dialog.accept();
    });

    // Verify active pipeline is shown
    await expect(page.getByText(/active pipeline/i)).toBeVisible();
    await expect(page.getByText(/test-pipeline-id-123/)).toBeVisible();
  });

  test('should show upload area when pipeline is created', async ({ page }) => {
    // Mock pipeline creation
    await page.route('**/api/v1/pipelines/', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: 'pipeline-123',
          name: 'Test Pipeline',
          status: 'pending',
          total_claims: 0,
          total_dependencies: 0,
          total_contradictions: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          documents: []
        })
      });
    });

    // Create pipeline
    await page.getByRole('button', { name: /create new pipeline/i }).click();

    // Wait for alert and accept
    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });

    // Verify upload area is enabled
    const uploadText = page.getByText(/click to upload|drag and drop/i);
    await expect(uploadText).toBeVisible();
  });

  test('should display Phase 4 progress checklist', async ({ page }) => {
    await expect(page.getByText(/phase 4 progress/i)).toBeVisible();
    await expect(page.getByText(/next\.js 14 setup/i)).toBeVisible();
    await expect(page.getByText(/typescript & tailwind css/i)).toBeVisible();
  });

  test('should show disabled upload when no pipeline selected', async ({ page }) => {
    // Initially, upload should show a message about creating pipeline first
    await expect(page.getByText(/create a pipeline first/i)).toBeVisible();
  });
});

test.describe('Dashboard - File Upload', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');

    // Create a pipeline first
    await page.route('**/api/v1/pipelines/', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          id: 'pipeline-123',
          name: 'Test Pipeline',
          status: 'pending',
          total_claims: 0,
          total_dependencies: 0,
          total_contradictions: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          documents: []
        })
      });
    });

    await page.getByRole('button', { name: /create new pipeline/i }).click();

    page.once('dialog', async (dialog) => {
      await dialog.accept();
    });

    await page.waitForTimeout(500);
  });

  test('should upload files', async ({ page }) => {
    // Mock upload endpoint
    await page.route('**/api/v1/pipelines/*/documents', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          documents: [
            {
              id: 'doc-1',
              filename: 'test.txt',
              file_size: 1024,
              mime_type: 'text/plain',
              status: 'uploaded',
              created_at: new Date().toISOString()
            }
          ]
        })
      });
    });

    // Mock start pipeline endpoint
    await page.route('**/api/v1/pipelines/*/start', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: 'Pipeline started',
          job_ids: ['job-1', 'job-2']
        })
      });
    });

    // Create a test file
    const fileContent = 'This is a test document with research claims.';
    const buffer = Buffer.from(fileContent);

    // Set the input files
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText(/click to upload/i).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test.txt',
      mimeType: 'text/plain',
      buffer: buffer,
    });

    // Click upload button
    await page.getByRole('button', { name: /upload \d+ file/i }).click();

    // Wait for success dialogs
    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain('Uploaded');
      await dialog.accept();
    });
  });

  test('should show file preview before upload', async ({ page }) => {
    const fileContent = 'Test content';
    const buffer = Buffer.from(fileContent);

    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText(/click to upload/i).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test-document.txt',
      mimeType: 'text/plain',
      buffer: buffer,
    });

    // Should show file in list
    await expect(page.getByText('test-document.txt')).toBeVisible();

    // Should show upload button
    await expect(page.getByRole('button', { name: /upload \d+ file/i })).toBeVisible();
  });

  test('should allow removing files before upload', async ({ page }) => {
    const fileContent = 'Test content';
    const buffer = Buffer.from(fileContent);

    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.getByText(/click to upload/i).click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles({
      name: 'test-document.txt',
      mimeType: 'text/plain',
      buffer: buffer,
    });

    // File should be visible
    await expect(page.getByText('test-document.txt')).toBeVisible();

    // Click remove button (X icon)
    const removeButton = page.locator('button').filter({ hasText: '×' }).first();
    await removeButton.click();

    // File should be removed
    await expect(page.getByText('test-document.txt')).not.toBeVisible();
  });
});

test.describe('Dashboard - Navigation', () => {
  test('should redirect from home to dashboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForURL('/dashboard');
    await expect(page).toHaveURL('/dashboard');
  });

  test('should have responsive layout', async ({ page, viewport }) => {
    await page.goto('/dashboard');

    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.getByRole('heading', { name: /research checker/i })).toBeVisible();

    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByRole('heading', { name: /research checker/i })).toBeVisible();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.getByRole('heading', { name: /research checker/i })).toBeVisible();
  });
});
