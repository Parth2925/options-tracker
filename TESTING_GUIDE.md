# Testing Guide for Options Trading Tracker

This guide will walk you through testing the application step by step.

## Prerequisites Check

Before starting, make sure you have:
- Python 3.8 or higher installed
- Node.js 14 or higher and npm installed

Verify installations:
```bash
python --version
node --version
npm --version
```

## Step 1: Start the Backend Server

1. Open a terminal and navigate to the backend directory:
```bash
cd /Users/parthsoni/Documents/options-tracker/backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Start the Flask server:
```bash
python app.py
```

You should see output like:
```
==================================================
Backend server starting...
Server will run on: http://127.0.0.1:5001
API endpoints available at: http://127.0.0.1:5001/api
Health check: http://127.0.0.1:5001/api/health
==================================================
 * Running on http://127.0.0.1:5001
 * Debug mode: on
```

**Keep this terminal open** - the backend needs to keep running.

## Step 2: Start the Frontend Server

1. Open a **new terminal window** (keep the backend terminal running)

2. Navigate to the frontend directory:
```bash
cd /Users/parthsoni/Documents/options-tracker/frontend
```

3. Install Node.js dependencies (first time only):
```bash
npm install
```

This may take a few minutes. You should see a success message when complete.

4. Start the React development server:
```bash
npm start
```

The browser should automatically open to `http://localhost:3000`. If not, manually navigate to that URL.

**Keep this terminal open** as well.

## Step 3: Test the Application

### Test 1: User Registration

1. You should see the Login page
2. Click "Register here" or navigate to `/register`
3. Fill in the registration form:
   - Email: `test@example.com` (or any email)
   - Password: `password123` (at least 6 characters)
   - Confirm Password: `password123`
4. Click "Register"
5. **Expected**: You should be automatically logged in and redirected to the Dashboard

### Test 2: Create an Account

1. After registration, you should be on the Dashboard
2. Click "Accounts" in the navigation bar
3. Click "Add Account"
4. Fill in the form:
   - Account Name: `Main Trading Account`
   - Account Type: `Taxable` (or any type)
   - Initial Balance: `10000`
5. Click "Create Account"
6. **Expected**: Account appears in the accounts list with your initial balance

### Test 3: Add a Deposit

1. Still on the Accounts page, click on the account you just created
2. Click "Add Deposit"
3. Fill in:
   - Amount: `5000`
   - Deposit Date: Today's date (or any date)
   - Notes: `Initial deposit` (optional)
4. Click "Add Deposit"
5. **Expected**: Deposit appears in the deposits table, and "Total Capital" updates

### Test 4: Add a Trade (Manual Entry - CSP)

1. Click "Trades" in the navigation bar
2. Click "Add Trade"
3. Fill in the trade form:
   - Account: Select your account
   - Symbol: `AAPL`
   - Trade Type: `CSP` (Cash-Secured Put)
   - Trade Action: `Sold to Open`
   - Position Type: `Open`
   - Strike Price: `150.00`
   - Expiration Date: Pick a future date (e.g., 30 days from today)
   - Contract Quantity: `2`
   - **Trade Price**: `5.00` (price per contract - premium will be calculated automatically)
   - Fees: `0.50` (per contract)
   - Trade Date: Today's date
   - Status: `Open`
4. **Verify**: The "Calculated Premium" field shows the premium (should be approximately $998.00 for 2 contracts: $5.00 × 2 × 100 - $0.50 × 2)
5. Click "Create Trade"
6. **Expected**: Trade appears in the trades table with the calculated premium

### Test 5: View Dashboard Metrics

1. Click "Dashboard" in the navigation
2. **Expected**: You should see:
   - Total P&L (should show the premium minus fees)
   - Unrealized P&L (since trade is open)
   - Rate of Return
   - Summary stats (1 account, 1 trade, 1 open position)

### Test 6: Test Time Period Filters

1. On the Dashboard, try changing the "Time Period" dropdown:
   - This Week
   - This Month
   - This Year
   - All Time
2. **Expected**: Metrics update based on the selected period

### Test 7: View Positions

1. Click "Positions" in the navigation
2. **Expected**: You should see your open trade listed
3. Try filtering by:
   - Account (if you have multiple)
   - Status (Open, Closed, All)

### Test 8: Close a Trade (Full Close)

1. Go back to "Trades"
2. Click "Add Trade"
3. Fill in the closing trade form:
   - Account: Same account
   - Symbol: `AAPL` (must match opening trade)
   - Trade Type: `CSP` (must match opening trade)
   - Trade Action: `Bought to Close`
   - **Parent Trade**: Select the opening trade from the dropdown (strike and expiration will auto-fill)
   - Strike Price: Should auto-fill from parent trade
   - Expiration Date: Should auto-fill from parent trade
   - Contract Quantity: `2` (same as opening trade for full close)
   - **Trade Price**: `2.50` (price per contract to close)
   - Fees: `0.50` (per contract)
   - Trade Date: Today's date
   - Close Date: Today's date (or leave blank, will use trade date)
4. **Verify**: 
   - The "Realized P&L Calculation" section shows:
     - Opening Premium: The premium from the parent trade
     - Closing Premium: The calculated closing premium (negative, since you're paying)
     - Realized P&L: Opening Premium + Closing Premium (should show profit/loss)
5. Click "Create Trade"
6. **Expected**: 
   - Both trades appear in the list
   - Opening trade status changes to "Closed"
   - Closing trade shows the realized P&L
   - Dashboard shows realized PNL for the closed trade
   - Trades table shows "Days Held" and "Return %" columns

### Test 9: Test Partial Close

1. Create a new opening trade:
   - Symbol: `TSLA`
   - Trade Type: `CSP`
   - Trade Action: `Sold to Open`
   - Contract Quantity: `10`
   - Trade Price: `3.00`
   - Fees: `0.50`
   - Save the trade
2. Create a partial closing trade:
   - Trade Action: `Bought to Close`
   - Parent Trade: Select the TSLA trade
   - Contract Quantity: `5` (closing only 5 out of 10 contracts)
   - Trade Price: `1.50`
   - Fees: `0.50`
3. **Verify**:
   - The "Realized P&L Calculation" shows proportional opening premium for 5 contracts
   - Opening trade remains "Open" (not "Closed") since only partial quantity was closed
   - Realized P&L is calculated only for the 5 contracts closed
4. **Expected**: 
   - Opening trade shows status "Open" with 5 contracts still open
   - Closing trade shows realized P&L for 5 contracts only

### Test 10: Edit a Trade

1. Go to "Trades" page
2. Find any trade in the list
3. Click "Edit" button on the trade
4. **Verify**: 
   - Form is pre-populated with all trade data
   - If it's a closing trade, parent trade is still selected (even if parent is now "Closed")
   - Calculated premium is shown
5. Make a change (e.g., update Trade Price or Fees)
6. **Verify**: Premium recalculates automatically
7. Click "Save" or "Update Trade"
8. **Expected**: 
   - Trade is updated in the list
   - All calculations (premium, P&L, returns) are updated

### Test 11: Test Assignment Flow (Wheel Strategy)

1. Create a CSP opening trade:
   - Symbol: `MSFT`
   - Trade Type: `CSP`
   - Trade Action: `Sold to Open`
   - Strike Price: `350.00`
   - Contract Quantity: `1`
   - Trade Price: `4.00`
   - Fees: `0.50`
   - Save the trade
2. Add an Assignment trade:
   - Symbol: `MSFT`
   - Trade Type: `Assignment`
   - Trade Action: `Bought to Open` (or leave blank)
   - **Parent Trade**: Select the CSP trade
   - Assignment Price: `350.00` (strike price)
   - Contract Quantity: `1`
   - Trade Price: `0` (or leave blank)
   - Fees: `0`
   - Trade Date: Today's date
   - Status: `Assigned`
3. Add a Covered Call on the assigned stock:
   - Symbol: `MSFT`
   - Trade Type: `Covered Call`
   - Trade Action: `Sold to Open`
   - **Parent Trade**: Select the Assignment trade
   - Strike Price: `355.00`
   - Contract Quantity: `1`
   - Trade Price: `2.00`
   - Fees: `0.50`
   - Status: `Open`
4. **Expected**: 
   - Dashboard PNL should reflect the full wheel cycle
   - Assignment trade links to CSP
   - Covered Call links to Assignment

### Test 12: Test LEAPS Trade

1. Create a LEAPS opening trade:
   - Symbol: `AAPL`
   - Trade Type: `LEAPS`
   - Trade Action: `Bought to Open`
   - Strike Price: `150.00`
   - Expiration Date: Pick a date far in the future (e.g., 1-2 years)
   - Contract Quantity: `1`
   - **Trade Price**: `80.00` (price per contract)
   - Fees: `0.50`
   - Trade Date: Today's date
2. **Verify**: 
   - Calculated Premium shows negative value (e.g., -$8,000.50) since you're paying
3. Create a LEAPS closing trade:
   - Trade Action: `Sold to Close`
   - Parent Trade: Select the LEAPS opening trade
   - Contract Quantity: `1`
   - **Trade Price**: `90.00` (price per contract)
   - Fees: `0.50`
4. **Verify**:
   - Calculated Premium shows positive value (e.g., +$8,999.50) since you're receiving
   - Realized P&L Calculation shows:
     - Opening Premium: -$8,000.50 (negative, you paid)
     - Closing Premium: +$8,999.50 (positive, you received)
     - Realized P&L: Should be approximately $999.00 (profit)
5. **Expected**: 
   - Realized P&L is calculated correctly: Opening Premium + Closing Premium
   - Profit = $8,999.50 + (-$8,000.50) = $999.00 ✓

### Test 13: Test Return Calculations

1. Create a closing trade (use any of the previous closing trades)
2. **Verify in the trades table**:
   - "Days Held" column shows number of days between open_date and close_date
   - "Return %" column shows:
     - Simple Return %: (Realized P&L / Capital at Risk) × 100
     - Annualized Return %: Adjusts for time held (hover over to see tooltip)
3. Edit the closing trade's "Close Date":
   - Click "Edit" on a closing trade
   - Change the "Close Date" to a different date
   - Save
4. **Verify**:
   - "Days Held" updates
   - "Annualized Return %" updates (changes with days held)
   - "Simple Return %" stays the same (doesn't depend on time)

### Test 14: CSV/Excel Import

1. Create a CSV file with the following content (save as `trades.csv`):
```csv
symbol,trade_type,trade_action,trade_date,trade_price,fees,strike_price,expiration_date,contract_quantity,status
TSLA,CSP,Sold to Open,2024-01-15,3.50,0.65,200.00,2024-02-16,1,Open
MSFT,Covered Call,Sold to Open,2024-01-20,2.00,0.65,350.00,2024-02-23,1,Open
```

**Note**: The import now supports `trade_price` and `trade_action` fields. Premium will be calculated automatically.

2. Go to "Trades" page
3. Click "Import CSV/Excel"
4. Select an account
5. Click "Upload File" and select your `trades.csv`
6. **Expected**: Success message showing number of trades imported, and trades appear in the list with calculated premiums

## Troubleshooting

### Backend Issues

**Port 5000 already in use:**
- The backend now runs on port 5001 by default (to avoid macOS AirPlay Receiver conflict)
- If you need to change it, update `backend/app.py`: `app.run(debug=True, port=5001)`
- Update frontend API base URL in `frontend/src/utils/api.js`: `API_BASE_URL = 'http://localhost:5001/api'`

**Module not found errors:**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Database errors:**
- Delete `backend/options_tracker.db` and restart the server (it will recreate)

### Frontend Issues

**Port 3000 already in use:**
- React will ask if you want to use a different port - say yes
- Or stop the other process using port 3000

**npm install fails:**
- Try: `npm cache clean --force`
- Then: `npm install` again

**CORS errors:**
- Make sure backend is running on port 5001
- Check that backend CORS is enabled (it should be in `app.py`)
- Verify frontend API base URL points to `http://localhost:5001/api`

**Blank page or errors:**
- Open browser console (F12) to see error messages
- Check that backend is running on port 5001 (not 5000)
- Verify API calls in Network tab are going to `http://localhost:5001/api`

### Common Issues

**"Cannot GET /api/..." errors:**
- Backend is not running or wrong port
- Check backend terminal for errors

**Login/Register not working:**
- Check browser console for errors
- Verify backend is running
- Check Network tab to see if API calls are failing

**Trades not showing:**
- Make sure you selected the correct account
- Check that trades were created successfully (no error messages)
- Refresh the page

**Premium calculation issues:**
- Make sure you're entering Trade Price (per contract), not total premium
- Premium is calculated as: (Trade Price × Quantity × 100) ± (Fees × Quantity)
- For "Sold" actions: fees are subtracted
- For "Bought" actions: fees are added (and result is negative)

**P&L calculation issues:**
- Realized P&L = Opening Premium + Closing Premium (premiums are already signed)
- For CSP: Opening positive, Closing negative → profit when positive result
- For LEAPS: Opening negative, Closing positive → profit when positive result
- Check that parent trade is correctly selected when closing

## Quick Test Checklist

- [ ] Backend server starts without errors on port 5001
- [ ] Frontend server starts and opens in browser
- [ ] Can register a new user
- [ ] Can create an account
- [ ] Can add a deposit
- [ ] Can add a trade manually using Trade Price (not premium)
- [ ] Premium is calculated automatically from Trade Price
- [ ] Can close a trade with auto-fill of strike and expiration
- [ ] Realized P&L calculation shows correctly when closing
- [ ] Can edit a trade after creation
- [ ] Can perform partial closes (close only some contracts)
- [ ] Parent trade remains visible when editing closing trade
- [ ] Dashboard shows metrics
- [ ] Can filter by time period
- [ ] Can view positions
- [ ] Trades table shows Days Held and Return % columns
- [ ] Return % updates when close date is changed
- [ ] Can create and close LEAPS trades
- [ ] LEAPS P&L calculation is correct
- [ ] Can import CSV/Excel file
- [ ] PNL calculations are correct for all trade types

## Key Features to Test

### Trade Entry
- **Trade Price Entry**: Enter price per contract, not total premium
- **Automatic Premium Calculation**: Premium = (Trade Price × Quantity × 100) ± (Fees × Quantity)
- **Trade Actions**: Sold to Open, Bought to Close, Bought to Open, Sold to Close

### Closing Trades
- **Auto-fill**: Strike price and expiration auto-fill from parent trade
- **Realized P&L Preview**: See calculated P&L before saving
- **Partial Closes**: Close only some contracts, parent stays "Open"

### Trade Editing
- **Edit Any Trade**: Click "Edit" button on any trade
- **Parent Trade Persistence**: Parent trade remains selected even if it's "Closed"
- **Recalculation**: Premium and P&L recalculate when fields change

### Return Metrics
- **Days Held**: Calculated from open_date to close_date
- **Simple Return %**: (Realized P&L / Capital at Risk) × 100 (doesn't change with time)
- **Annualized Return %**: Adjusts for time held (changes when days held changes)

### LEAPS Support
- **Bought to Open**: Premium is negative (you paid)
- **Sold to Close**: Premium is positive (you received)
- **P&L Calculation**: Opening Premium + Closing Premium

## Next Steps After Testing

Once basic functionality is confirmed:
1. Test with real trading data
2. Verify PNL calculations match your expectations for all trade types
3. Test edge cases (negative premiums, multiple accounts, partial closes, etc.)
4. Check that all time period filters work correctly
5. Verify assignment and covered call linking works properly
6. Test return calculations with different holding periods
7. Verify LEAPS trades calculate correctly

## Getting Help

If you encounter issues:
1. Check the terminal output for error messages
2. Check browser console (F12) for frontend errors
3. Verify all dependencies are installed correctly
4. Make sure both servers are running
5. Check that ports 3000 and 5000 are available

