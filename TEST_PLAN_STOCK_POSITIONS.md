# Test Plan: Stock Positions & Enhanced Close Workflow

## Overview
This test plan covers all 6 phases of the stock positions and enhanced close workflow implementation. Test systematically to ensure all features work correctly and existing functionality remains intact.

---

## Pre-Testing Setup

### 1. Database Migration
- [ ] Run schema migration: `python backend/migrate_add_stock_positions.py`
- [ ] Verify `stock_positions` table exists
- [ ] Verify `trades` table has `stock_position_id` and `shares_used` columns
- [ ] If you have existing data, run: `python backend/migrate_existing_data.py --dry-run` first
- [ ] Review dry-run output for any issues
- [ ] Run actual migration: `python backend/migrate_existing_data.py`

### 2. Environment Setup
- [ ] Backend server is running
- [ ] Frontend is running
- [ ] You have at least one account created
- [ ] You're logged in

---

## Phase 1: Data Model & Backend Foundation

### Test 1.1: Stock Position API Endpoints

#### Test 1.1.1: Create Stock Position
1. Navigate to Positions → Stocks tab
2. Click "Add Stock Position"
3. Fill in form:
   - Account: Select an account
   - Symbol: `AAPL`
   - Shares: `100`
   - Cost Basis per Share: `150.00`
   - Acquired Date: Today's date
   - Status: `Open`
   - Notes: `Test position`
4. Click "Create"
- **Expected**: 
  - Stock position created successfully
  - Appears in Stocks tab
  - Shows 100 shares available
  - Cost basis shows correctly

#### Test 1.1.2: List Stock Positions
1. Navigate to Positions → Stocks tab
2. View the list
- **Expected**:
  - All stock positions are listed
  - Shows symbol, shares, cost basis, available shares
  - Company logos display (if available)

#### Test 1.1.3: Get Single Stock Position
1. Create a stock position (from Test 1.1.1)
2. Note the position ID
3. Use API: `GET /api/stock-positions/<id>`
- **Expected**:
  - Returns position details
  - Includes `available_shares` and `shares_used` fields

#### Test 1.1.4: Update Stock Position
1. Navigate to Positions → Stocks tab
2. Click "Edit" on an existing position
3. Change shares to `200`
4. Update cost basis to `155.00`
5. Click "Update"
- **Expected**:
  - Position updated successfully
  - Changes reflected in list
  - Available shares recalculated

#### Test 1.1.5: Delete Stock Position (No Active Covered Calls)
1. Create a stock position with no covered calls
2. Click "Delete"
3. Confirm deletion
- **Expected**:
  - Position deleted successfully
  - Removed from list

#### Test 1.1.6: Delete Stock Position (With Active Covered Calls)
1. Create a stock position
2. Create a covered call using this position
3. Try to delete the stock position
- **Expected**:
  - Error message: "Cannot delete position. It has X active covered call(s)"
  - Position remains in list

#### Test 1.1.7: Get Available Stock Positions
1. Create multiple stock positions for same symbol
2. Create a covered call using one position
3. Use API: `GET /api/stock-positions/available?symbol=AAPL&account_id=X`
- **Expected**:
  - Returns only positions with available shares
  - Position with used shares shows correct available amount

---

## Phase 2: Stock Positions Management UI

### Test 2.1: Positions Page Tabs
1. Navigate to Positions page
2. Check for two tabs: "Options" and "Stocks"
- **Expected**:
  - Both tabs visible
  - Options tab shows existing options trades
  - Stocks tab shows stock positions

### Test 2.2: Stock Positions Table
1. Navigate to Positions → Stocks tab
2. View the table
- **Expected**:
  - Columns: Symbol, Shares, Cost Basis/Share, Total Cost Basis, Acquired Date, Available Shares, Shares Used, Status, Actions
  - Data displays correctly
  - Sorting works on sortable columns

### Test 2.3: Stock Position Form
1. Click "Add Stock Position"
2. Verify form fields
- **Expected**:
  - All required fields present
  - Account dropdown populated
  - Date picker works
  - Validation works (try submitting empty form)

### Test 2.4: Search and Filter
1. Create multiple stock positions with different symbols
2. Use search box to filter by symbol
3. Filter by account
4. Filter by status
- **Expected**:
  - Search filters correctly
  - Account filter works
  - Status filter works

---

## Phase 3: Auto-Creation from Trades

### Test 3.1: CSP Assignment Auto-Creates Stock Position

#### Test 3.1.1: Full Assignment
1. Create a CSP trade:
   - Symbol: `AAPL`
   - Strike: `150`
   - Contracts: `1`
   - Trade Action: `Sold to Open`
   - Premium: `$2.00`
2. Use Close button on the CSP
3. Select "Assigned" as close method
4. Set assignment price: `150.00`
5. Set close date: Today
6. Click "Close Trade"
- **Expected**:
  - Assignment trade created
  - Stock position auto-created:
    - Symbol: `AAPL`
    - Shares: `100` (1 contract × 100)
    - Cost Basis: `$150.00`
    - Status: `Open`
    - Source: Assignment trade
  - CSP status: `Assigned`

#### Test 3.1.2: Partial Assignment
1. Create a CSP with 2 contracts
2. Close with "Assigned" method
3. Set contract quantity: `1` (partial)
- **Expected**:
  - Stock position created with 100 shares
  - CSP remains `Open` (not fully assigned)
  - Can assign remaining contract later

### Test 3.2: LEAPS Exercise Auto-Creates Stock Position

#### Test 3.2.1: Full Exercise
1. Create a LEAPS trade:
   - Symbol: `AAPL`
   - Strike: `150`
   - Contracts: `1`
   - Trade Action: `Bought to Open`
   - Premium: `$10.00`
2. Use Close button on the LEAPS
3. Select "Exercise" as close method
4. Set close date: Today
5. Click "Close Trade"
- **Expected**:
  - LEAPS status: `Closed`
  - Stock position auto-created:
    - Symbol: `AAPL`
    - Shares: `100`
    - Cost Basis: `$150.00` (strike price)
    - Status: `Open`
    - Source: LEAPS trade

#### Test 3.2.2: Partial Exercise
1. Create a LEAPS with 2 contracts
2. Exercise 1 contract
- **Expected**:
  - Stock position created with 100 shares
  - LEAPS remains `Open` (1 contract remaining)
  - Can exercise remaining contract later

### Test 3.3: Verify Source Trade Links
1. Create stock positions from assignments/exercises (from Tests 3.1 and 3.2)
2. Check stock position details
- **Expected**:
  - `source_trade_id` points to correct Assignment/LEAPS trade
  - Notes mention source trade

---

## Phase 4: Covered Call Integration

### Test 4.1: Create Covered Call (Requires Stock Position)

#### Test 4.1.1: Create with Valid Stock Position
1. Create a stock position (100 shares of AAPL)
2. Navigate to Trades → Add Trade
3. Fill in:
   - Trade Type: `Covered Call`
   - Symbol: `AAPL`
   - Stock Position: Select the position created
   - Strike: `155`
   - Contracts: `1`
   - Trade Action: `Sold to Open`
   - Premium: `$1.50`
4. Submit
- **Expected**:
  - Covered call created successfully
  - Stock position shows: Available Shares = 0, Shares Used = 100
  - Covered call has `stock_position_id` set
  - `shares_used` = 100

#### Test 4.1.2: Create Without Stock Position (Should Fail)
1. Navigate to Trades → Add Trade
2. Fill in:
   - Trade Type: `Covered Call`
   - Symbol: `AAPL`
   - Leave Stock Position empty
3. Try to submit
- **Expected**:
  - Validation error: "stock_position_id is required for Covered Call trades"
  - Form does not submit

#### Test 4.1.3: Create with Insufficient Shares
1. Create stock position with 50 shares
2. Try to create covered call with 1 contract (needs 100 shares)
- **Expected**:
  - Validation error: "Insufficient shares available. Need 100 shares, but only 50 available"
  - Form does not submit

#### Test 4.1.4: Create with Wrong Symbol
1. Create stock position for `AAPL`
2. Try to create covered call for `MSFT` using AAPL position
- **Expected**:
  - Validation error: "Stock position symbol (AAPL) does not match trade symbol (MSFT)"
  - Form does not submit

#### Test 4.1.5: Create with Closed Stock Position
1. Create stock position
2. Change status to "Called Away"
3. Try to create covered call using this position
- **Expected**:
  - Validation error: "Stock position is not open (status: Called Away)"
  - Form does not submit

### Test 4.2: Multiple Covered Calls on Same Position

#### Test 4.2.1: Two Covered Calls (Partial Usage)
1. Create stock position with 200 shares
2. Create first covered call (1 contract = 100 shares)
3. Create second covered call (1 contract = 100 shares)
- **Expected**:
  - Both covered calls created successfully
  - Stock position shows: Available = 0, Used = 200
  - Both calls linked to same position

#### Test 4.2.2: Third Covered Call (Should Fail)
1. From Test 4.2.1, try to create third covered call
- **Expected**:
  - Validation error: "Insufficient shares available"
  - Form does not submit

### Test 4.3: P&L Calculation Uses Cost Basis

#### Test 4.3.1: Covered Call Assigned
1. Create stock position: 100 shares @ $150 cost basis
2. Create covered call: Strike $155, Premium $2.00
3. Close covered call as "Assigned"
- **Expected**:
  - Realized P&L = Premium ($200) + Stock Appreciation (($155 - $150) × 100) = $700
  - Uses actual cost basis from stock position, not assignment price

#### Test 4.3.2: Covered Call Without Stock Position (Legacy)
1. Create covered call without stock_position_id (if possible via API)
2. Assign it
- **Expected**:
  - P&L calculation falls back to assignment_price method
  - Still calculates correctly

---

## Phase 5: Enhanced Close Workflow

### Test 5.1: CSP Close Options

#### Test 5.1.1: Buy to Close
1. Create CSP trade (Sold to Open)
2. Click "Close" button
3. Select "Buy to Close"
4. Fill in:
   - Close Date: Today
   - Trade Price: `0.50`
   - Fees: `1.00`
   - Contract Quantity: `1`
5. Submit
- **Expected**:
  - Closing trade created
  - CSP status: `Closed`
  - Realized P&L calculated correctly

#### Test 5.1.2: Expired
1. Create CSP trade
2. Click "Close" button
3. Select "Expired"
4. Set close date (expiration date)
5. Submit
- **Expected**:
  - CSP status: `Closed`
  - Close date set
  - Realized P&L = full premium (expired worthless)

#### Test 5.1.3: Assigned (Full)
1. Create CSP trade
2. Click "Close" button
3. Select "Assigned"
4. Set assignment price and date
5. Submit
- **Expected**:
  - Assignment trade created
  - Stock position auto-created
  - CSP status: `Assigned`

#### Test 5.1.4: Assigned (Partial)
1. Create CSP with 2 contracts
2. Close as "Assigned" with quantity: `1`
- **Expected**:
  - Stock position created (100 shares)
  - CSP remains `Open` (1 contract remaining)

### Test 5.2: Covered Call Close Options

#### Test 5.2.1: Buy to Close
1. Create covered call (using stock position)
2. Click "Close" button
3. Select "Buy to Close"
4. Fill in trade price and fees
5. Submit
- **Expected**:
  - Closing trade created
  - Covered call status: `Closed`
  - Stock position: Available shares increase (shares returned)
  - Realized P&L calculated

#### Test 5.2.2: Expired
1. Create covered call
2. Close as "Expired"
- **Expected**:
  - Covered call status: `Closed`
  - Stock position: Shares returned (available increases)
  - Realized P&L = premium received

#### Test 5.2.3: Assigned (Shares Called Away)
1. Create covered call
2. Close as "Assigned"
3. Set assignment price
- **Expected**:
  - Covered call status: `Assigned`
  - Stock position: Shares reduced or status changed
  - Realized P&L includes stock appreciation

### Test 5.3: LEAPS Close Options

#### Test 5.3.1: Sell to Close
1. Create LEAPS (Bought to Open)
2. Click "Close" button
3. Select "Sell to Close"
4. Fill in trade price and fees
5. Submit
- **Expected**:
  - Closing trade created
  - LEAPS status: `Closed`
  - Realized P&L calculated

#### Test 5.3.2: Expired
1. Create LEAPS
2. Close as "Expired"
- **Expected**:
  - LEAPS status: `Closed`
  - Realized P&L = negative premium (loss)

#### Test 5.3.3: Exercise
1. Create LEAPS
2. Close as "Exercise"
- **Expected**:
  - LEAPS status: `Closed`
  - Stock position auto-created
  - Cost basis = strike price

### Test 5.4: Close Dialog UI
1. Click "Close" on various trade types
- **Expected**:
  - Dialog shows correct close methods based on trade type
  - CSP/CC: Buy to Close, Expired, Assigned
  - LEAPS: Sell to Close, Expired, Exercise
  - Form fields adapt based on selected method
  - Validation works

---

## Phase 6: Edge Cases & Backward Compatibility

### Test 6.1: Partial Operations

#### Test 6.1.1: Partial Close (CSP)
1. Create CSP with 3 contracts
2. Close 1 contract (Buy to Close)
3. Close another 1 contract
4. Close final contract
- **Expected**:
  - Each close creates separate closing trade
  - CSP remains `Open` until all closed
  - Final close sets CSP to `Closed`

#### Test 6.1.2: Partial Assignment
1. Create CSP with 2 contracts
2. Assign 1 contract
3. Assign remaining contract
- **Expected**:
  - First assignment creates stock position (100 shares)
  - CSP remains `Open`
  - Second assignment adds to position or creates new?
  - CSP becomes `Assigned` when all assigned

#### Test 6.1.3: Partial Exercise
1. Create LEAPS with 2 contracts
2. Exercise 1 contract
3. Exercise remaining contract
- **Expected**:
  - First exercise creates stock position
  - LEAPS remains `Open`
  - Second exercise closes LEAPS

### Test 6.2: Multiple Covered Calls

#### Test 6.2.1: Two Calls, Close One Early
1. Create stock position (200 shares)
2. Create two covered calls (1 contract each)
3. Close first covered call early
- **Expected**:
  - First call: Status = `Closed`
  - Stock position: Available shares = 100 (one call's shares returned)
  - Second call: Still `Open`, still using 100 shares
  - Can create another covered call with the 100 available shares

#### Test 6.2.2: Three Calls on Same Position
1. Create stock position (300 shares)
2. Create three covered calls (1 contract each)
3. Verify all work correctly
- **Expected**:
  - All three calls created
  - Stock position shows: Available = 0, Used = 300
  - Each call tracks its shares_used

### Test 6.3: Shares Return on Early Close

#### Test 6.3.1: Covered Call Buy to Close
1. Create stock position (100 shares)
2. Create covered call (uses all 100)
3. Buy to close the covered call
4. Check stock position
- **Expected**:
  - Covered call: Status = `Closed`
  - Stock position: Available shares = 100 (returned)
  - Can create new covered call immediately

#### Test 6.3.2: Covered Call Expired
1. Create stock position (100 shares)
2. Create covered call
3. Close as "Expired"
- **Expected**:
  - Shares returned to available
  - Can create new covered call

### Test 6.4: Backward Compatibility

#### Test 6.4.1: Existing Covered Calls (No stock_position_id)
1. If you have existing covered calls without stock_position_id:
   - View them in Trades list
   - Edit them
   - View P&L calculations
- **Expected**:
  - All display correctly
  - Can be edited
  - P&L uses fallback method (assignment_price)
  - No errors

#### Test 6.4.2: Add stock_position_id to Existing Covered Call
1. Edit an existing covered call (without stock_position_id)
2. Add a stock_position_id via edit
3. Save
- **Expected**:
  - Updates successfully
  - Shares_used calculated
  - Stock position shows shares used

#### Test 6.4.3: Legacy Assignment Trades
1. If you have existing Assignment trades:
   - View them
   - Check if stock positions were created by migration
- **Expected**:
  - Assignment trades still work
   - Stock positions exist (if migration run)
   - Can link covered calls to positions

### Test 6.5: Migration Testing

#### Test 6.5.1: Dry Run Migration
1. Run: `python backend/migrate_existing_data.py --dry-run`
- **Expected**:
  - Shows what would be created/linked
  - No actual changes made
  - Report shows summary

#### Test 6.5.2: Actual Migration
1. Run: `python backend/migrate_existing_data.py`
- **Expected**:
  - Stock positions created from Assignment trades
  - Covered calls linked to positions
  - Report shows what was done
  - Any issues flagged for manual review

#### Test 6.5.3: Post-Migration Verification
1. After migration, check:
   - All Assignment trades have corresponding stock positions
   - Covered calls are linked to positions
   - Available shares calculated correctly
- **Expected**:
  - All data migrated correctly
  - No orphaned trades
  - Shares calculations correct

---

## Integration Tests

### Test 7.1: Full Wheel Strategy Cycle
1. Create CSP → Assign → Stock Position Created
2. Create Covered Call on Stock Position
3. Close Covered Call Early → Shares Return
4. Create Another Covered Call
5. Assign Covered Call → Shares Called Away
- **Expected**:
  - All steps work correctly
  - Stock positions track correctly
  - P&L calculations accurate throughout

### Test 7.2: Multiple Symbols
1. Create stock positions for different symbols (AAPL, MSFT, GOOGL)
2. Create covered calls for each
3. Mix operations across symbols
- **Expected**:
  - Each symbol tracked separately
  - No cross-contamination
  - All calculations correct

### Test 7.3: Multiple Accounts
1. Create stock positions in different accounts
2. Create covered calls in each account
3. Verify isolation
- **Expected**:
  - Account isolation maintained
  - No cross-account access
  - All validations work

---

## Regression Tests (Ensure Nothing Broken)

### Test 8.1: Existing Trade Operations
1. Create regular CSP (not using close workflow)
2. Create regular Covered Call (old way if possible)
3. Create LEAPS
4. Edit trades
5. Delete trades
- **Expected**:
  - All existing operations still work
  - No errors
  - Data integrity maintained

### Test 8.2: Dashboard
1. View dashboard with new trades
2. Check P&L calculations
3. Check monthly returns
4. Check position allocation
- **Expected**:
  - All metrics display correctly
  - P&L includes new stock positions
  - No calculation errors

### Test 8.3: Positions Page (Options Tab)
1. View Options tab
2. Verify existing positions display
3. Test filters and search
4. Test sorting
- **Expected**:
  - Options positions work as before
  - No regressions
  - All features functional

### Test 8.4: Trades Page
1. View all trades
2. Test filters
3. Test search
4. Test sorting
5. Export trades
- **Expected**:
  - All trades display
  - Filters work
  - Export includes new fields (stock_position_id, shares_used)

### Test 8.5: Import/Export
1. Export trades to CSV/Excel
2. Verify new fields included
3. Import trades (if supported)
- **Expected**:
  - Export includes stock_position_id and shares_used
  - Import works (if applicable)
  - Data integrity maintained

---

## Performance Tests

### Test 9.1: Large Dataset
1. Create 50+ stock positions
2. Create 100+ covered calls
3. Test page load times
4. Test API response times
- **Expected**:
  - Acceptable performance
  - No timeouts
  - UI remains responsive

### Test 9.2: Complex Queries
1. Filter positions with many covered calls
2. Calculate available shares for positions with many calls
3. Test dashboard with many trades
- **Expected**:
  - Queries execute efficiently
  - Calculations accurate
  - No performance degradation

---

## Error Handling Tests

### Test 10.1: Invalid Data
1. Try to create stock position with negative shares
2. Try to create covered call with invalid stock_position_id
3. Try to close trade with invalid method
- **Expected**:
  - Appropriate error messages
  - No crashes
  - Data not corrupted

### Test 10.2: Concurrent Operations
1. Create covered call on position
2. Simultaneously try to delete the position
3. Try to create another covered call
- **Expected**:
  - Proper validation prevents conflicts
  - Error messages clear
  - Data integrity maintained

---

## Test Checklist Summary

### Critical Path Tests (Must Pass)
- [ ] Create stock position
- [ ] Create covered call with stock position
- [ ] CSP assignment auto-creates stock position
- [ ] LEAPS exercise auto-creates stock position
- [ ] Close CSP as "Assigned"
- [ ] Close covered call early (shares return)
- [ ] Multiple covered calls on same position
- [ ] P&L uses actual cost basis

### Backward Compatibility Tests (Must Pass)
- [ ] Existing trades still work
- [ ] Existing covered calls (no stock_position_id) work
- [ ] Migration script runs successfully
- [ ] Post-migration data is correct

### Edge Case Tests (Should Pass)
- [ ] Partial assignments
- [ ] Partial exercises
- [ ] Partial closes
- [ ] Shares return on early close
- [ ] Multiple symbols/accounts

### Regression Tests (Must Pass)
- [ ] Dashboard works
- [ ] Positions page (Options tab) works
- [ ] Trades page works
- [ ] Import/Export works
- [ ] All existing features intact

---

## Test Execution Notes

1. **Test Order**: Follow the test order for dependencies (e.g., create stock position before creating covered call)

2. **Data Cleanup**: Consider creating a test account to avoid polluting real data

3. **Documentation**: Document any issues found with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable

4. **Priority**: Focus on Critical Path Tests first, then Backward Compatibility, then Edge Cases

5. **Migration**: If testing with existing data, backup database first

---

## Success Criteria

All tests should pass with:
- ✅ No errors or crashes
- ✅ Data integrity maintained
- ✅ Calculations accurate
- ✅ UI responsive and intuitive
- ✅ Backward compatibility preserved
- ✅ Performance acceptable

---

## Issues Found

Document any issues discovered during testing:

| Test ID | Issue Description | Severity | Status |
|---------|-------------------|----------|--------|
|         |                   |          |        |

---

## Sign-off

- [ ] All Critical Path Tests passed
- [ ] All Backward Compatibility Tests passed
- [ ] All Edge Case Tests passed
- [ ] All Regression Tests passed
- [ ] Performance acceptable
- [ ] Ready for production

**Tester**: _________________  
**Date**: _________________  
**Notes**: _________________
