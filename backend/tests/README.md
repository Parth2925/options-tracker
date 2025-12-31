# Test Suite for Single-Entry Close Implementation

## Overview
This comprehensive test suite verifies the single-entry close implementation, ensuring that:
- Full closes update the original trade (single entry)
- Partial closes create closing trades (two entries)
- P&L calculations work for both approaches
- Closing trades are filtered from lists
- Backward compatibility is maintained
- All trade types (CSP, Covered Call, LEAPS) work correctly
- Validation and error handling work properly

## Running Tests

```bash
# Run all tests
cd backend
pytest tests/ -v

# Run specific test file
pytest tests/test_single_entry_close.py -v

# Run specific test
pytest tests/test_single_entry_close.py::TestSingleEntryClose::test_full_close_csp_updates_original_trade -v

# Run with coverage (if pytest-cov installed)
pytest tests/ --cov=. --cov-report=html
```

## Test Files

### `test_single_entry_close.py` (10 tests)
Core functionality tests:
- ✅ Full close updates original trade
- ✅ Partial close creates closing trade
- ✅ Expired updates original trade
- ✅ P&L calculation for single-entry
- ✅ P&L calculation for two-entry
- ✅ Remaining quantity calculation
- ✅ Filtering closing trades
- ✅ Backward compatibility
- ✅ LEAPS sell to close

### `test_close_endpoint.py` (3 tests)
Integration tests for close endpoint:
- ✅ Full close via endpoint
- ✅ Partial close via endpoint
- ✅ Expired via endpoint

### `test_dashboard_filtering.py` (2 tests)
Dashboard filtering tests:
- ✅ P&L excludes closing trades
- ✅ Positions exclude closing trades

### `test_covered_call_closes.py` (4 tests)
Covered Call closing scenarios:
- ✅ Full close of Covered Call (buy to close)
- ✅ Partial close of Covered Call
- ✅ Covered Call expired
- ✅ Covered Call assigned

### `test_leaps_scenarios.py` (3 tests)
LEAPS scenarios:
- ✅ LEAPS exercise
- ✅ LEAPS expired
- ✅ LEAPS partial close

### `test_assignment_scenarios.py` (2 tests)
Assignment scenarios:
- ✅ CSP assigned creates stock position
- ✅ Partial CSP assignment

### `test_validation_errors.py` (5 tests)
Validation and error handling:
- ✅ Close already closed trade (fails)
- ✅ Close insufficient quantity (fails)
- ✅ Invalid close method for trade action (fails)
- ✅ Missing required fields (fails)
- ✅ Multiple partial closes

### `test_pnl_calculations.py` (5 tests)
P&L calculation edge cases:
- ✅ P&L with fees
- ✅ P&L expired worthless
- ✅ P&L assigned CSP
- ✅ P&L partial close calculation
- ✅ P&L negative result (loss)

## Test Results

**All 34 tests passing** ✅

- 10 tests in `test_single_entry_close.py`
- 3 tests in `test_close_endpoint.py`
- 2 tests in `test_dashboard_filtering.py`
- 4 tests in `test_covered_call_closes.py`
- 3 tests in `test_leaps_scenarios.py`
- 2 tests in `test_assignment_scenarios.py`
- 5 tests in `test_validation_errors.py`
- 5 tests in `test_pnl_calculations.py`

## Coverage

The tests cover:
1. **Single-entry approach**: Full closes update original trade
2. **Two-entry approach**: Partial closes create closing trades
3. **P&L calculations**: Both approaches calculate correctly, including edge cases
4. **Filtering**: Closing trades excluded from lists
5. **Backward compatibility**: Existing closing trades still work
6. **Trade types**: CSP, Covered Call, LEAPS, Assignment
7. **Close methods**: Buy to Close, Sell to Close, Expired, Assigned, Exercise
8. **Validation**: Error handling for invalid inputs
9. **Edge cases**: Multiple partial closes, fees, losses, etc.
10. **Stock positions**: Integration with stock positions for Covered Calls and Assignments

## Pre-Push Checklist

Before pushing to main branch, ensure:
- ✅ All tests pass: `pytest tests/ -v`
- ✅ No linter errors
- ✅ Database migrations are tested
- ✅ Backward compatibility verified

## Notes

- Tests use in-memory SQLite database for isolation
- Each test runs in its own transaction and is rolled back
- Fixtures create test users and accounts automatically
- Tests verify both database state and API responses
