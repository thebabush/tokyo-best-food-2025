# Static Site Testing Guide

This project now includes comprehensive automated tests for the static Gotanda restaurant map website using Playwright.

## Test Coverage

The test suite (`test_static_site.py`) includes 26 tests covering:

### 1. Map Loading (7 tests)
- ✓ Page loads correctly
- ✓ Map container exists and is visible
- ✓ Leaflet library is initialized
- ✓ Restaurant data loads from JSON
- ✓ Markers are displayed on the map
- ✓ Marker clustering works
- ✓ Legend exists and is visible

### 2. Template Replacement (2 tests)
- ✓ Template variables ({{ }}) are properly replaced with actual values
- ✓ No Jinja2 template syntax remains in the page
- ✓ Restaurant count badge shows correct number (1094 restaurants)

### 3. Quick Filters - Rating Legend (2 tests)
- ✓ Legend items are clickable
- ✓ High rating filter (3.8+) works via legend click

### 4. Advanced Filters (10 tests)
- ✓ Filter dialog opens and closes
- ✓ Category dropdown is populated from categories.json
- ✓ Search filter works (text search, auto-applied)
- ✓ Minimum rating filter works (auto-applied)
- ✓ Price range filter works (auto-applied)
- ✓ Category filter works (auto-applied)
- ✓ Combined filters work together (auto-applied)
- ✓ Filters can be reset individually
- ✓ Clear button resets all filters at once

### 5. Marker Interaction (3 tests)
- ✓ Clicking a marker opens the info sheet
- ✓ Info sheet displays restaurant details
- ✓ Info sheet can be closed

### 6. Responsiveness (2 tests)
- ✓ Works on mobile viewport (375x667)
- ✓ Works on tablet viewport (768x1024)

## Running the Tests

### Prerequisites

The testing environment is already set up with:
- Playwright for Python (via uv)
- pytest and pytest-playwright
- Chromium browser (headless)

### Run All Tests

```bash
uv run pytest test_static_site.py -v
```

### Run Specific Test Classes

```bash
# Test only map loading
uv run pytest test_static_site.py::TestMapLoading -v

# Test only filters
uv run pytest test_static_site.py::TestAdvancedFilters -v

# Test only template replacement
uv run pytest test_static_site.py::TestTemplateReplacement -v
```

### Run a Single Test

```bash
uv run pytest test_static_site.py::TestMapLoading::test_page_loads -v
```

### Run with Detailed Output

```bash
# Show print statements and verbose output
uv run pytest test_static_site.py -v -s

# Show browser in headed mode (not headless)
uv run pytest test_static_site.py --headed
```

## How Tests Work

1. **Server Setup**: The tests automatically start an HTTP server on port 8765 to serve the static site
2. **Browser Automation**: Playwright controls a Chromium browser to interact with the site
3. **Assertions**: Each test verifies specific functionality works as expected
4. **Cleanup**: The server and browser are automatically cleaned up after tests complete

## Test Files

- `test_static_site.py` - Main test suite with all test cases
- `conftest.py` - Pytest configuration and fixtures (HTTP server setup)

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    uv pip install playwright pytest pytest-playwright
    uv run playwright install chromium
    uv run pytest test_static_site.py -v
```

## Rebuilding the Static Site

If you make changes to the source code, rebuild the static site before running tests:

```bash
uv run python build_complete_static.py
```

This script:
1. Exports restaurant and category data to JSON
2. Extracts HTML/CSS/JS from the Flask template
3. Replaces template variables with actual values
4. Creates a production-ready static site in `static_site/`

## Test Results

**Current Status**: ✅ All 26 tests passing

The tests verify that the static site is fully functional and ready for deployment to GitHub Pages or any static hosting service.
