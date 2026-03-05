#!/bin/bash
#
# CI Test Runner Script
# Runs all tests with proper error handling and reporting
#

set -e

echo "🧪 BudAlert Test Suite - CI Runner"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
total_tests=0
passed_tests=0
failed_tests=0

# Function to run test suite
run_test_suite() {
  local suite_name=$1
  local npm_command=$2
  
  echo "📦 Running ${suite_name}..."
  
  if ${npm_command}; then
    echo -e "${GREEN}✅ ${suite_name} passed${NC}"
    return 0
  else
    echo -e "${RED}❌ ${suite_name} failed${NC}"
    return 1
  fi
}

# Run unit tests
echo ""
if run_test_suite "Unit Tests" "npm run test:unit"; then
  passed_tests=$((passed_tests + 1))
else
  failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))

# Run integration tests
echo ""
if run_test_suite "Integration Tests" "npm run test:integration"; then
  passed_tests=$((passed_tests + 1))
else
  failed_tests=$((failed_tests + 1))
fi
total_tests=$((total_tests + 1))

# Generate coverage report
echo ""
echo "📊 Generating coverage report..."
if npm run test:coverage > /dev/null 2>&1; then
  echo -e "${GREEN}✅ Coverage report generated${NC}"
else
  echo -e "${YELLOW}⚠️  Coverage generation failed (non-blocking)${NC}"
fi

# Print summary
echo ""
echo "=================================="
echo "📈 Test Summary"
echo "=================================="
echo "Total Suites: ${total_tests}"
echo -e "${GREEN}Passed: ${passed_tests}${NC}"
if [ ${failed_tests} -gt 0 ]; then
  echo -e "${RED}Failed: ${failed_tests}${NC}"
fi
echo ""

# Exit with appropriate code
if [ ${failed_tests} -gt 0 ]; then
  echo -e "${RED}❌ Some tests failed${NC}"
  exit 1
else
  echo -e "${GREEN}✅ All tests passed!${NC}"
  exit 0
fi
