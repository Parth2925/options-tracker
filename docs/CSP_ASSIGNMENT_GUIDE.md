# Cash Secured Put (CSP) Assignment Testing Guide

This guide explains how to test the complete CSP assignment workflow, from opening a CSP to logging when it gets assigned at expiration.

## Overview

The CSP assignment workflow consists of two trades:
1. **Initial CSP Trade**: Opening a Cash Secured Put (Sold to Open)
2. **Assignment Trade**: Logging when the CSP gets assigned at expiration

## Step-by-Step Instructions

### Step 1: Create the Initial CSP Trade

1. **Navigate to Trades Page**
   - Log into your Options Tracker account
   - Click on **"Trades"** in the navigation bar
   - Click **"Add New Trade"** button

2. **Fill in CSP Opening Trade Details**
   - **Account**: Select your trading account
   - **Symbol**: Enter the stock symbol (e.g., `AAPL`, `MSFT`, `TSLA`)
   - **Trade Type**: Select **"CSP"** (Cash Secured Put)
   - **Position Type**: Select **"Open"**
   - **Strike Price**: Enter the strike price (e.g., `150.00`)
   - **Expiration Date**: Enter the expiration date (e.g., `2025-01-17`)
   - **Contract Quantity**: Enter number of contracts (e.g., `1`)
   - **Trade Action**: Select **"Sold to Open"**
   - **Trade Price**: Enter the premium received per contract (e.g., `3.50`)
   - **Fees**: Enter commission/fees (e.g., `0.50`)
   - **Trade Date**: Enter the date you opened the CSP (defaults to today)
   - **Status**: Should be **"Open"** (default)
   - **Notes**: Optional - add any notes about the trade

3. **Verify Premium Calculation**
   - The form should automatically calculate:
     - **Calculated Premium**: `(Trade Price × Contract Quantity × 100) - (Fees × Contract Quantity)`
     - Example: `($3.50 × 1 × 100) - ($0.50 × 1) = $350.00 - $0.50 = $349.50`

4. **Save the Trade**
   - Click **"Save Trade"** or **"Add Trade"**
   - The CSP trade should now appear in your trades list with status **"Open"**

### Step 2: Log the Assignment (When CSP Expires and Gets Assigned)

**When to do this**: After the CSP expiration date, if the stock price is below the strike price, the CSP will be assigned. You'll receive the stock at the strike price.

1. **Navigate to Trades Page**
   - Go to **"Trades"** page
   - Click **"Add New Trade"** button

2. **Fill in Assignment Trade Details**
   - **Account**: Select the **same account** as the CSP
   - **Symbol**: Enter the **same symbol** as the CSP (e.g., `AAPL`)
   - **Trade Type**: Select **"Assignment"**
   - **Position Type**: This will auto-set to **"Assignment"**
   - **Parent Trade**: **IMPORTANT** - Select the CSP trade you created in Step 1
     - This dropdown will show all open CSPs for the selected symbol
   - **Strike Price**: Will auto-fill from parent CSP (usually the same as strike)
   - **Expiration Date**: Will auto-fill from parent CSP
   - **Contract Quantity**: Will auto-fill from parent CSP (usually `1`)
   - **Trade Action**: Leave blank (not needed for Assignment)
   - **Trade Price**: Leave blank (not needed for Assignment)
   - **Fees**: Enter any assignment fees (usually `0` or minimal)
   - **Assignment Price**: Will auto-fill from parent CSP's strike price
     - This is the price at which you received the stock
     - Usually equals the strike price
   - **Trade Date**: Enter the assignment date (usually the expiration date or the Monday after)
   - **Status**: Will auto-set to **"Assigned"** (cannot be changed)
   - **Notes**: Optional - add notes like "Assigned at expiration" or "Stock price was $145 at expiration"

3. **Verify Assignment Information**
   - The form should show:
     - **Parent CSP Premium**: The premium you received from the CSP
     - **Assignment Price**: The strike price (price you paid for the stock)
     - **Status**: Automatically set to "Assigned"

4. **Save the Assignment Trade**
   - Click **"Save Trade"** or **"Add Trade"**
   - The Assignment trade will appear in your trades list
   - The parent CSP trade status will automatically change to **"Closed"**

### Step 3: Verify the Results

1. **Check Trades List**
   - Go to **"Trades"** page
   - You should see:
     - **CSP Trade**: Status = "Closed", linked to Assignment trade
     - **Assignment Trade**: Status = "Assigned", shows parent CSP

2. **Check Dashboard**
   - Go to **"Dashboard"** page
   - The CSP should show as closed
   - Realized P&L should reflect the premium received from the CSP

3. **Check Positions**
   - Go to **"Positions"** page
   - You should see a new **stock position** (from the Assignment)
   - The CSP should no longer appear in open positions

## Example Scenario

Let's say you sold a CSP on AAPL:

### Initial CSP Trade:
- **Symbol**: `AAPL`
- **Trade Type**: `CSP`
- **Strike Price**: `$150.00`
- **Expiration Date**: `2025-01-17`
- **Contract Quantity**: `1`
- **Trade Action**: `Sold to Open`
- **Trade Price**: `$3.50` (premium per contract)
- **Fees**: `$0.50`
- **Trade Date**: `2025-01-10`
- **Calculated Premium**: `$349.50` (received)

### Assignment Trade (after expiration):
- **Symbol**: `AAPL`
- **Trade Type**: `Assignment`
- **Parent Trade**: Select the CSP trade above
- **Assignment Price**: `$150.00` (auto-filled from strike)
- **Contract Quantity**: `1` (auto-filled)
- **Fees**: `$0`
- **Trade Date**: `2025-01-17` (expiration date)
- **Status**: `Assigned` (auto-set)

### Result:
- You received `$349.50` premium from the CSP
- You now own 100 shares of AAPL at `$150.00` per share
- Total cost basis: `$15,000 - $349.50 = $14,650.50` (strike price minus premium received)

## Next Steps After Assignment

After logging the Assignment, you can:

1. **Sell Covered Calls** on the assigned stock:
   - Create a new trade
   - Trade Type: `Covered Call`
   - Parent Trade: Select the Assignment trade
   - This continues the "Wheel Strategy"

2. **Hold the Stock**:
   - The stock position will appear in your Positions page
   - You can track unrealized P&L as the stock price moves

## Common Questions

### Q: What if the CSP expires worthless (not assigned)?
**A**: Simply create a closing trade:
- Trade Type: `CSP`
- Trade Action: `Bought to Close`
- Parent Trade: Select the CSP
- Trade Price: `$0.00` (or very small amount)
- This closes the CSP and you keep the full premium

### Q: What if I close the CSP before expiration?
**A**: Create a closing trade:
- Trade Type: `CSP`
- Trade Action: `Bought to Close`
- Parent Trade: Select the CSP
- Trade Price: Enter the premium you paid to close
- This closes the CSP early

### Q: Can I assign a CSP before expiration?
**A**: Yes, if you're assigned early:
- Create an Assignment trade
- Trade Date: Date of early assignment
- Everything else is the same

### Q: What if I'm assigned on only some contracts?
**A**: You can create multiple Assignment trades:
- First Assignment: Contract Quantity = number assigned
- Then create a closing trade for remaining contracts:
  - Trade Action: `Bought to Close`
  - Contract Quantity: remaining contracts

## Testing Checklist

- [ ] Created initial CSP trade (Sold to Open)
- [ ] Verified premium calculation is correct
- [ ] CSP appears in trades list with status "Open"
- [ ] Created Assignment trade after expiration
- [ ] Selected parent CSP in Assignment trade
- [ ] Verified assignment price auto-filled from strike
- [ ] Assignment trade saved with status "Assigned"
- [ ] Parent CSP status changed to "Closed"
- [ ] Stock position appears in Positions page
- [ ] Dashboard shows correct P&L

## Troubleshooting

### Issue: Can't find parent CSP in dropdown
**Solution**: 
- Make sure Symbol matches exactly
- Make sure CSP status is "Open"
- Check that you're using the same account

### Issue: Assignment price is wrong
**Solution**:
- Assignment price should equal the strike price
- You can manually edit it if needed
- Usually it auto-fills correctly from parent CSP

### Issue: CSP status didn't change to "Closed"
**Solution**:
- Refresh the trades list
- The status should update automatically
- If not, the backend handles this on the next page load

