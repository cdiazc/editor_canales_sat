# Testing Documentation

This directory contains the complete test suite for the Editor de Canales SAT project.

## Test Structure

```
tests/
├── __init__.py
├── fixtures/                    # Sample data files for testing
│   ├── sample.chl              # Sample CHL format file
│   └── sample_kingofsat.html   # Sample KingOfSat HTML
└── unit/                        # Unit tests
    ├── __init__.py
    ├── test_chl_parsing.py              # Tests for CHL file parsing
    ├── test_chl_to_sdx_conversion.py    # Tests for CHL to SDX conversion
    ├── test_kingofsat_parsing.py        # Tests for KingOfSat HTML parsing
    ├── test_sdx_processing.py           # Tests for SDX data processing
    └── test_utils.py                    # Tests for utility functions
```

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run all tests with default verbosity
pytest

# Run with verbose output
pytest -v

# Run tests in a specific file
pytest tests/unit/test_chl_parsing.py

# Run a specific test class
pytest tests/unit/test_chl_parsing.py::TestCHLParsing

# Run a specific test
pytest tests/unit/test_chl_parsing.py::TestCHLParsing::test_parse_chl_file_basic
```

### Code Coverage

```bash
# Run tests with coverage report
pytest --cov=channel_processor

# Generate HTML coverage report
pytest --cov=channel_processor --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Test Categories

### CHL File Parsing Tests (test_chl_parsing.py)

Tests the parsing of CHL (Channel List) files:
- ✅ Basic structure validation
- ✅ Satellite data extraction
- ✅ Transponder data extraction
- ✅ Channel data extraction
- ✅ Favorites list extraction
- ✅ Handling of empty files
- ✅ Handling of malformed JSON

**Coverage**: 7 tests

### KingOfSat HTML Parsing Tests (test_kingofsat_parsing.py)

Tests the HTML scraping functionality for KingOfSat website:
- ✅ Basic channel extraction
- ✅ Multiple frequency handling
- ✅ Duplicate removal
- ✅ Edge cases (missing data, whitespace)
- ✅ Empty HTML handling

**Coverage**: 8 tests

### CHL to SDX Conversion Tests (test_chl_to_sdx_conversion.py)

Tests the conversion from CHL format to SDX format:
- ✅ Satellite conversion
- ✅ Transponder conversion with polarization mapping
- ✅ Channel conversion
- ✅ Video codec mapping (MPEG2, H264, HEVC/H265)
- ✅ HD detection
- ✅ Audio language code mapping
- ✅ CA (encryption) flag handling
- ✅ Favorites list conversion
- ✅ Favorite names box object creation

**Coverage**: 11 tests

### SDX Data Processing Tests (test_sdx_processing.py)

Tests the processing and extraction of data from SDX objects:
- ✅ Empty data handling
- ✅ Transponder extraction
- ✅ Channel extraction and metadata
- ✅ HD/CA/UHD channel detection
- ✅ Favorites list index mapping
- ✅ Duplicate SID/TP handling
- ✅ Channel ordering
- ✅ Service type mapping

**Coverage**: 9 tests

### Utility Function Tests (test_utils.py)

Tests utility functions:
- ✅ Service type mapping for all known types
- ✅ Unknown service type handling

**Coverage**: 5 tests

## Test Statistics

- **Total Tests**: 40
- **Coverage**: 96%
- **Execution Time**: ~0.1 seconds

## Continuous Integration

Tests are designed to be run in CI/CD pipelines. They:
- ✅ Run quickly (< 1 second)
- ✅ Are completely isolated (no external dependencies)
- ✅ Use fixture files instead of live data
- ✅ Have deterministic results

## Adding New Tests

When adding new functionality:

1. Create test fixtures in `tests/fixtures/` if needed
2. Add test cases to the appropriate test file
3. Follow the existing naming convention: `test_<functionality>_<scenario>`
4. Ensure tests are isolated and don't depend on external state
5. Run the full test suite to ensure no regressions

Example:

```python
def test_new_feature_basic_case(self):
    """Test basic case for new feature."""
    # Arrange
    input_data = {...}
    
    # Act
    result = ChannelDataProcessor.new_method(input_data)
    
    # Assert
    assert result['expected_field'] == expected_value
```

## Debugging Tests

```bash
# Run with detailed output and stop at first failure
pytest -vv -x

# Run with Python debugger on failures
pytest --pdb

# Show local variables in tracebacks
pytest -l

# Run only failed tests from last run
pytest --lf
```

## Known Limitations

The current test suite focuses on:
- ✅ Business logic (parsing, conversion, processing)
- ✅ Data validation
- ✅ Edge cases and error handling

Not currently tested:
- ❌ GUI components (Tkinter widgets)
- ❌ File I/O operations (mocked via fixtures)
- ❌ Network operations (KingOfSat download)
- ❌ User interactions

These areas are difficult to test without integration/E2E testing frameworks and are not included in this unit test suite.
