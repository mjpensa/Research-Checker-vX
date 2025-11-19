# Testing Guide - Research Checker

Comprehensive testing documentation for the Cross-LLM Research Synthesis System.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Writing Tests](#writing-tests)
- [CI/CD Pipeline](#cicd-pipeline)
- [Coverage Reports](#coverage-reports)
- [Troubleshooting](#troubleshooting)

## Overview

The Research Checker project uses a comprehensive testing strategy covering:

- **Unit Tests**: Individual components and functions
- **Integration Tests**: Multi-component workflows
- **E2E Tests**: Full user journeys through the frontend
- **API Tests**: All backend endpoints
- **Worker Tests**: Background job processing

### Test Stack

- **Backend**: pytest, pytest-asyncio, pytest-cov
- **Frontend**: Playwright
- **Coverage**: Codecov, HTML reports
- **CI/CD**: GitHub Actions

## Test Structure

```
Research-Checker-vX/
├── tests/
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── unit/
│   │   ├── api/
│   │   │   ├── test_pipelines.py    # Pipeline API tests
│   │   │   ├── test_claims.py       # Claims API tests
│   │   │   └── test_reports.py      # Reports API tests
│   │   └── workers/
│   │       └── test_extraction_worker.py
│   └── integration/
│       └── workflows/
│           └── test_full_pipeline.py
│
├── apps/frontend/
│   ├── e2e/
│   │   ├── dashboard.spec.ts
│   │   └── pipeline-details.spec.ts
│   └── playwright.config.ts
│
├── pytest.ini
└── .github/workflows/test.yml
```

## Running Tests

### Backend Tests

```bash
# All tests
pytest

# With coverage
pytest --cov --cov-report=html

# Specific tests
pytest tests/unit/api/test_pipelines.py -v
pytest -k "pipeline" -v
pytest -m unit

# Watch mode
pytest-watch
```

### Frontend E2E Tests

```bash
cd apps/frontend

# Install
pnpm install
pnpm exec playwright install

# Run tests
pnpm exec playwright test

# With UI
pnpm exec playwright test --ui

# Debug
pnpm exec playwright test --debug
```

## CI/CD Pipeline

GitHub Actions runs automatically on push/PR:

1. Backend unit tests
2. Integration tests  
3. Frontend E2E tests
4. Type checking
5. Linting
6. Security scan

## Coverage

```bash
# Generate coverage
pytest --cov --cov-report=html

# View report
open htmlcov/index.html
```

**Targets:**
- Backend: 80%+
- API: 100% desired
- Workers: 75%+

## Writing Tests

### Backend
```python
import pytest

@pytest.mark.unit
@pytest.mark.api
def test_create_pipeline(test_client, sample_pipeline_data):
    response = test_client.post("/api/v1/pipelines/", json=sample_pipeline_data)
    assert response.status_code == 200
```

### Frontend
```typescript
test('should create pipeline', async ({ page }) => {
  await page.goto('/dashboard');
  await page.getByRole('button', { name: /create/i }).click();
  await expect(page.getByText(/pipeline/i)).toBeVisible();
});
```

## Troubleshooting

### Database issues
```bash
docker ps | grep postgres
dropdb research_checker_test
createdb research_checker_test
```

### Redis issues
```bash
redis-cli ping  # Should return PONG
```

### Playwright issues
```bash
pnpm exec playwright install --force
rm -rf .next
```

For more help, see full documentation in project wiki.

---
**Version:** 1.0.0  
**Last Updated:** December 19, 2024
