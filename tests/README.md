# Unity MCP Build Service - API Tests

## End-to-End API Tests

### Quick Start

```bash
python3 tests/test_api_e2e.py <BASE_URL> <API_KEY>
```

**Example:**
```bash
python3 tests/test_api_e2e.py http://35.226.93.88 013e283d7f3a2d45dcdbe7a2b4676a61ff58e7a576930ac3ea66c85d3882f197
```

### Test Coverage

The test suite covers all API endpoints:

1. **Root Endpoint** (`/`) - Service info
2. **Health Check** (`/health`) - Service health status
3. **List Themes** (`/themes`) - Available game themes
4. **Service Status** (`/status`) - Build statistics (auth required)
5. **Authentication** - Validates API key requirement
6. **Build Creation** (`POST /build`) - Create new Unity builds
7. **Build Status** (`GET /build/{id}/status`) - Check build progress
8. **Build Stop** (`PUT /build/{id}/stop`) - Stop running builds
9. **Error Handling** - 404, 401, 422 responses
10. **Theme Variations** - City, Farm, Space themes
11. **Interactive Objects** - Build with custom game objects

### Requirements

```bash
pip install requests
```

### Expected Output

```
============================================================
Unity MCP Build Service - End-to-End API Tests
============================================================
Base URL: http://35.226.93.88
API Key: 013e283d7f...
============================================================

--- Test 1: Root Endpoint (/) ---
✅ PASS: Root endpoint

--- Test 2: Health Check (/health) ---
✅ PASS: Health check

[... more tests ...]

============================================================
Test Summary
============================================================
Total Tests: 15
Passed: 15 ✅
Failed: 0 ❌
Success Rate: 100.0%
============================================================
```

### Test Results

See [TEST_RESULTS_E2E.md](../TEST_RESULTS_E2E.md) for the latest test results.

### Available Tests

- `test_api_e2e.py` - Comprehensive end-to-end API tests (15 tests)
- `test_build_service_api.py` - Legacy async test suite (deprecated)

### Notes

- Tests create real Unity builds that will be queued on the server
- Tests automatically stop builds they create to avoid resource usage
- Authentication is required for most endpoints
- API key is available in `src/production_unity_service.py`
