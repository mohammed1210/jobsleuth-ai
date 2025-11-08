#!/bin/bash
# Smoke test script for JobSleuth AI backend

set -e

BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

echo "🧪 Running backend smoke tests..."
echo "Backend URL: $BACKEND_URL"
echo

# Test 1: Health endpoint
echo "Test 1: Health endpoint"
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/health")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "✅ Health check passed (HTTP $http_code)"
    echo "   Response: $body"
else
    echo "❌ Health check failed (HTTP $http_code)"
    exit 1
fi
echo

# Test 2: Jobs listing
echo "Test 2: Jobs listing"
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/jobs?page=1&per_page=5")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "✅ Jobs listing passed (HTTP $http_code)"
    job_count=$(echo "$body" | grep -o '"jobs":\[' | wc -l)
    echo "   Jobs endpoint responded successfully"
else
    echo "❌ Jobs listing failed (HTTP $http_code)"
    exit 1
fi
echo

# Test 3: User plan endpoint (should work without auth)
echo "Test 3: User plan endpoint (no auth fallback)"
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/users/plan?email=test@example.com")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

if [ "$http_code" = "200" ]; then
    echo "✅ User plan endpoint passed (HTTP $http_code)"
    echo "   Response: $body"
else
    echo "❌ User plan endpoint failed (HTTP $http_code)"
    exit 1
fi
echo

echo "🎉 All smoke tests passed!"
