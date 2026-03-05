# CI/CD Setup Documentation

## Overview

BudAlert uses GitHub Actions for continuous integration and testing. All tests run automatically on push and pull requests.

---

## GitHub Actions Workflows

### Test Suite (`test.yml`)

**Triggers:**
- Push to `main`, `scraping-research-exercise`, or `develop` branches
- Pull requests to `main`

**Jobs:**

#### 1. Test Job
Runs on multiple Node.js versions (20.x, 22.x) to ensure compatibility.

**Steps:**
1. Checkout code
2. Setup Node.js with caching
3. Install dependencies (`npm ci`)
4. Run linter (optional)
5. Run unit tests
6. Run integration tests
7. Generate coverage report
8. Upload coverage to Codecov
9. Archive test results
10. Comment PR with coverage (for PRs only)

**Artifacts:**
- Test results (30-day retention)
- Coverage reports

#### 2. Lint Job
Code quality checks with Prettier (optional).

#### 3. Security Job
Runs `npm audit` to check for vulnerabilities.

---

## Local Testing

### Quick Start

```bash
# Run all tests
npm test

# Run with watch mode
npm run test:watch

# Run specific suites
npm run test:unit
npm run test:integration

# Generate coverage
npm run test:coverage

# Interactive UI
npm run test:ui
```

### CI Simulation Script

```bash
# Run the same checks as CI
./scripts/run-tests-ci.sh
```

This script:
- Runs all test suites
- Generates coverage
- Provides colored output
- Exits with proper error codes

---

## Coverage Requirements

### Current Thresholds

Set in `vitest.config.js`:

| Metric | Threshold |
|--------|-----------|
| Lines | 70% |
| Functions | 70% |
| Branches | 60% |
| Statements | 70% |

### Coverage Reports

**Locations:**
- `coverage/index.html` - Interactive HTML report
- `coverage/lcov.info` - LCOV format for Codecov
- `coverage/coverage-final.json` - JSON summary

**View locally:**
```bash
npm run test:coverage
open coverage/index.html
```

---

## Pre-commit Hooks (Optional)

### Setup with Husky

```bash
npm install --save-dev husky
npx husky install
npx husky add .husky/pre-commit "npm test"
```

### Manual Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/sh
npm test
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Codecov Integration

### Setup

1. Sign up at [codecov.io](https://codecov.io)
2. Add repository
3. Get upload token
4. Add as GitHub secret: `CODECOV_TOKEN`

### Badge

Add to README.md:
```markdown
[![codecov](https://codecov.io/gh/OWNER/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/OWNER/REPO)
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/              # Isolated function tests
│   ├── scrapers/      # Scraper unit tests
│   └── convex/        # Convex function tests
├── integration/       # Component interaction tests
├── e2e/              # End-to-end tests (future)
└── fixtures/         # Test data files
```

### Test File Naming

- Unit tests: `*.test.mjs`
- Integration tests: `*.test.mjs`
- Fixtures: `*-sample.{html,json}`

---

## Continuous Deployment (Future)

### Production Deployment

When tests pass on `main`:
1. Run full test suite
2. Build production artifacts
3. Deploy to Convex
4. Deploy scrapers to AWS Lambda/Cloudflare Workers
5. Run smoke tests

### Staging Deployment

On `develop` branch:
1. Deploy to staging environment
2. Run integration tests against staging
3. Manual approval for production

---

## Monitoring & Alerts

### Test Failures

**GitHub Actions:**
- Email notifications on failure
- Slack/Discord webhooks (configure in workflow)

**Codecov:**
- Coverage decrease alerts
- PR comments with coverage changes

### Health Checks

**Daily Cron:**
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
```

Runs:
- All tests
- Security audit
- Dependency updates check

---

## Troubleshooting

### Tests Fail Locally But Pass in CI

**Causes:**
- Node.js version mismatch
- Missing environment variables
- OS-specific path issues

**Solution:**
```bash
# Use same Node version as CI
nvm use 22

# Check environment
printenv | grep -i test

# Clean install
rm -rf node_modules package-lock.json
npm install
```

### Coverage Upload Fails

**Causes:**
- Missing Codecov token
- Network issues
- Rate limiting

**Solution:**
```yaml
# In workflow, set fail_ci_if_error: false
fail_ci_if_error: false
```

### Slow Test Execution

**Optimizations:**
- Use `vi.mock()` instead of real HTTP calls
- Run integration tests in parallel
- Skip expensive E2E tests on draft PRs

```yaml
# Skip tests on draft PRs
if: github.event.pull_request.draft == false
```

---

## Best Practices

1. **Fast Tests:** Unit tests should run in <1 second
2. **Deterministic:** No flaky tests (use fixtures, not live data)
3. **Isolated:** Tests don't depend on each other
4. **Descriptive:** Clear test names and error messages
5. **Maintained:** Update fixtures when scrapers change

---

## Maintenance

### Weekly Tasks
- Review test coverage trends
- Update test fixtures if scrapers change
- Check for flaky tests

### Monthly Tasks
- Update dependencies
- Review CI/CD performance
- Optimize slow tests

---

## Resources

- **Vitest Docs:** https://vitest.dev/
- **GitHub Actions:** https://docs.github.com/en/actions
- **Codecov:** https://docs.codecov.io/
- **Testing Best Practices:** https://kentcdodds.com/blog/common-mistakes-with-react-testing-library

---

**Last Updated:** 2026-03-05  
**Maintainer:** BudAlert Team
