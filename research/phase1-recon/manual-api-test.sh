#!/bin/bash
# Manual API testing for Conbud Dutchie platform

echo "Testing Dutchie API endpoints..."

# Try to query the dispensary menu via GraphQL
curl -X POST https://api.dutchie.com/graphql \
  -H "Content-Type: application/json" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  -d '{
    "operationName": "FilteredProducts",
    "variables": {
      "dispensaryId": "6430f42042cf3c004e37f0f8",
      "limit": 10
    },
    "query": "query FilteredProducts($dispensaryId: ID!, $limit: Int) { dispensary(id: $dispensaryId) { id name products(limit: $limit) { id name brand { name } category price thcPercent cbdPercent image } } }"
  }' \
  2>&1 | jq '.' || echo "GraphQL query failed or returned non-JSON"
