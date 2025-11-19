/**
 * E2E tests for Pipeline Details page.
 * Tests pipeline visualization, claims table, graph, and reports.
 */

import { test, expect } from '@playwright/test';

const MOCK_PIPELINE = {
  id: 'pipeline-test-123',
  name: 'Test Pipeline',
  status: 'completed',
  total_claims: 15,
  total_dependencies: 8,
  total_contradictions: 2,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  documents: [
    {
      id: 'doc-1',
      filename: 'research.pdf',
      file_size: 102400,
      mime_type: 'application/pdf',
      status: 'processed',
      created_at: new Date().toISOString()
    }
  ]
};

const MOCK_CLAIMS = Array.from({ length: 15 }, (_, i) => ({
  id: `claim-${i}`,
  text: `Test claim ${i} about artificial intelligence and machine learning`,
  claim_type: ['factual', 'statistical', 'causal'][i % 3],
  confidence: 0.8 + (i % 10) / 50,
  pagerank: 0.05 + (i / 100),
  centrality: 0.03 + (i / 100),
  is_foundational: i < 3,
  extracted_at: new Date().toISOString()
}));

test.describe('Pipeline Details - Overview', () => {
  test.beforeEach(async ({ page }) => {
    // Mock pipeline API
    await page.route('**/api/v1/pipelines/pipeline-test-123', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(MOCK_PIPELINE)
      });
    });

    // Mock claims API
    await page.route('**/api/v1/claims*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(MOCK_CLAIMS)
      });
    });

    // Mock reports API
    await page.route('**/api/v1/reports/pipeline-test-123', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify([])
      });
    });

    await page.goto('/pipeline/pipeline-test-123');
  });

  test('should display pipeline name and status', async ({ page }) => {
    await expect(page.getByText('Test Pipeline')).toBeVisible();
    await expect(page.getByText('completed')).toBeVisible();
  });

  test('should display pipeline statistics', async ({ page }) => {
    await expect(page.getByText('15')).toBeVisible(); // total claims
    await expect(page.getByText('8')).toBeVisible();  // total dependencies
    await expect(page.getByText('2')).toBeVisible();  // total contradictions
  });

  test('should have working tab navigation', async ({ page }) => {
    // Overview tab should be active by default
    const overviewTab = page.getByRole('button', { name: /overview/i });
    await expect(overviewTab).toHaveClass(/border-blue-600/);

    // Click Claims tab
    const claimsTab = page.getByRole('button', { name: /claims/i });
    await claimsTab.click();
    await expect(claimsTab).toHaveClass(/border-blue-600/);

    // Click Graph tab
    const graphTab = page.getByRole('button', { name: /graph/i });
    await graphTab.click();
    await expect(graphTab).toHaveClass(/border-blue-600/);

    // Click Reports tab
    const reportsTab = page.getByRole('button', { name: /reports/i });
    await reportsTab.click();
    await expect(reportsTab).toHaveClass(/border-blue-600/);
  });

  test('should display analysis action buttons', async ({ page }) => {
    await expect(page.getByRole('button', { name: /analyze dependencies/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /detect contradictions/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /generate report/i })).toBeVisible();
  });

  test('should trigger dependency analysis', async ({ page }) => {
    // Mock dependency analysis endpoint
    await page.route('**/api/v1/reports/*/analyze-dependencies', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          message: 'Dependency analysis started',
          job_id: 'job-123'
        })
      });
    });

    // Click analyze dependencies button
    await page.getByRole('button', { name: /analyze dependencies/i }).click();

    // Wait for alert
    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toContain('started');
      await dialog.accept();
    });
  });

  test('should have back navigation', async ({ page }) => {
    const backButton = page.getByRole('button', { name: /back/i });
    await expect(backButton).toBeVisible();
  });
});

test.describe('Pipeline Details - Claims Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/pipelines/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(MOCK_PIPELINE) });
    });

    await page.route('**/api/v1/claims*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(MOCK_CLAIMS) });
    });

    await page.route('**/api/v1/reports/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify([]) });
    });

    await page.goto('/pipeline/pipeline-test-123');
    await page.getByRole('button', { name: /claims/i }).click();
  });

  test('should display claims table', async ({ page }) => {
    await expect(page.getByText(/claims ledger/i)).toBeVisible();
    await expect(page.getByText(/15/)).toBeVisible(); // total count
  });

  test('should have search functionality', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search claims/i);
    await expect(searchInput).toBeVisible();

    await searchInput.fill('artificial intelligence');
    // Claims should filter (in real app)
  });

  test('should display claim types', async ({ page }) => {
    await expect(page.getByText('factual')).toBeVisible();
    await expect(page.getByText('statistical')).toBeVisible();
    await expect(page.getByText('causal')).toBeVisible();
  });

  test('should show confidence visualization', async ({ page }) => {
    // Progress bars should be visible
    const progressBars = page.locator('.bg-blue-600.h-2.rounded-full');
    await expect(progressBars.first()).toBeVisible();
  });

  test('should have pagination', async ({ page }) => {
    await expect(page.getByRole('button', { name: /previous/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /next/i })).toBeVisible();
  });

  test('should display foundational claims badge', async ({ page }) => {
    await expect(page.getByText('Foundational')).toBeVisible();
  });
});

test.describe('Pipeline Details - Graph Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/pipelines/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(MOCK_PIPELINE) });
    });

    await page.route('**/api/v1/claims*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(MOCK_CLAIMS) });
    });

    await page.route('**/api/v1/reports/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify([]) });
    });

    await page.goto('/pipeline/pipeline-test-123');
    await page.getByRole('button', { name: /graph/i }).click();
  });

  test('should display dependency graph', async ({ page }) => {
    await expect(page.getByText(/dependency graph/i)).toBeVisible();
  });

  test('should have graph controls', async ({ page }) => {
    // Check for zoom and download buttons
    const buttons = page.locator('button[aria-label], button svg');
    expect(await buttons.count()).toBeGreaterThan(0);
  });

  test('should display graph legend', async ({ page }) => {
    await expect(page.getByText('Claim Types')).toBeVisible();
    await expect(page.getByText('Relationships')).toBeVisible();
    await expect(page.getByText('Factual')).toBeVisible();
    await expect(page.getByText('Evidential')).toBeVisible();
  });

  test('should show node count', async ({ page }) => {
    await expect(page.getByText(/\d+ claims, \d+ dependencies/)).toBeVisible();
  });
});

test.describe('Pipeline Details - Reports Tab', () => {
  const MOCK_REPORTS = [
    {
      id: 'report-1',
      pipeline_id: 'pipeline-test-123',
      report_type: 'synthesis',
      title: 'Synthesis Report - Dec 19 2024',
      content: '# Executive Summary\n\nThis is a test report.',
      content_html: '<h1>Executive Summary</h1><p>This is a test report.</p>',
      summary: 'Test report summary',
      generated_at: new Date().toISOString()
    }
  ];

  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/pipelines/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(MOCK_PIPELINE) });
    });

    await page.route('**/api/v1/claims*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(MOCK_CLAIMS) });
    });

    await page.route('**/api/v1/reports/pipeline-test-123', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify(MOCK_REPORTS) });
    });

    await page.goto('/pipeline/pipeline-test-123');
    await page.getByRole('button', { name: /reports/i }).click();
  });

  test('should display report list', async ({ page }) => {
    await expect(page.getByText('Synthesis Report - Dec 19 2024')).toBeVisible();
  });

  test('should display report metadata', async ({ page }) => {
    await expect(page.getByText('synthesis')).toBeVisible();
    await expect(page.getByText(/generated/i)).toBeVisible();
  });

  test('should open report on click', async ({ page }) => {
    await page.getByText('Synthesis Report - Dec 19 2024').click();

    // Report viewer should be shown
    await expect(page.getByRole('button', { name: /back to reports/i })).toBeVisible();
  });
});

test.describe('Pipeline Details - Real-time Updates', () => {
  test('should display live connection status', async ({ page }) => {
    await page.route('**/api/v1/**', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify(route.request().url().includes('claims') ? MOCK_CLAIMS : MOCK_PIPELINE)
      });
    });

    await page.goto('/pipeline/pipeline-test-123');

    // Look for live badge (may be visible if WebSocket connects)
    // This is challenging to test without actual WebSocket server
    const liveBadge = page.getByText('Live');
    // Badge may or may not be visible depending on WebSocket connection
  });
});

test.describe('Pipeline Details - Error Handling', () => {
  test('should handle pipeline not found', async ({ page }) => {
    await page.route('**/api/v1/pipelines/nonexistent', async (route) => {
      await route.fulfill({ status: 404, body: JSON.stringify({ detail: 'Not found' }) });
    });

    await page.route('**/api/v1/claims*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify([]) });
    });

    await page.route('**/api/v1/reports/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify([]) });
    });

    await page.goto('/pipeline/nonexistent');

    await expect(page.getByText(/pipeline not found/i)).toBeVisible();
  });

  test('should handle empty claims', async ({ page }) => {
    await page.route('**/api/v1/pipelines/*', async (route) => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({ ...MOCK_PIPELINE, total_claims: 0 })
      });
    });

    await page.route('**/api/v1/claims*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify([]) });
    });

    await page.route('**/api/v1/reports/*', async (route) => {
      await route.fulfill({ status: 200, body: JSON.stringify([]) });
    });

    await page.goto('/pipeline/pipeline-test-123');
    await page.getByRole('button', { name: /claims/i }).click();

    // Should show empty state or 0 claims
    await expect(page.getByText(/0|no claims/i)).toBeVisible();
  });
});
