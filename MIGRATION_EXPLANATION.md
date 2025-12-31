# Database Migration Explanation - Version 1.4.0

## Overview

Version 1.4.0 introduced major new features that require database schema changes. These migrations add new tables and columns to support:

1. **Stock Positions Tracking** - Track actual stock holdings
2. **Enhanced Close Workflow** - Single-entry system for closing trades
3. **Default Fees** - Set default fees per account

---

## Migration 1: Stock Positions (`migrate_add_stock_positions.py`)

### What It Does:
1. **Creates `stock_positions` table** - A new table to track actual stock holdings
2. **Adds `stock_position_id` column to `trades` table** - Links covered calls to stock positions
3. **Adds `shares_used` column to `trades` table** - Tracks how many shares a covered call uses

### Why It's Needed:
**Feature: Stock Positions System**

Before v1.4.0, the app only tracked options trades. Now it can also track:
- **Stock positions** created from CSP assignments (when you get assigned stock)
- **Stock positions** created from LEAPS exercises (when you exercise a LEAPS contract)
- **Covered calls** that reference specific stock positions with cost basis tracking

**Example Use Case:**
1. You sell a CSP (Cash-Secured Put) on AAPL
2. You get assigned → You now own 100 shares of AAPL
3. The system automatically creates a stock position entry
4. Later, you sell a covered call using those shares
5. The covered call is linked to the stock position, so P&L calculations use the correct cost basis

### What Breaks Without It:
- Stock Positions page won't work
- Covered calls can't be linked to stock positions
- Cost basis tracking for covered calls won't work
- Auto-creation of stock positions from assignments/exercises won't work

---

## Migration 2: Close Fields (`migrate_add_close_fields.py`)

### What It Does:
Adds 4 new columns to the `trades` table:
- **`close_price`** - Price per contract when the trade was closed
- **`close_fees`** - Fees paid when closing the trade
- **`close_premium`** - Calculated closing premium (net of fees)
- **`close_method`** - How the trade was closed: 'buy_to_close', 'sell_to_close', 'expired', 'assigned', 'exercise'

### Why It's Needed:
**Feature: Enhanced Close Workflow (Single-Entry System)**

Before v1.4.0, closing a trade required creating a separate "closing trade" entry. Now:
- **Full closes** update the original trade entry directly (single entry)
- **Partial closes** still create separate entries (for history tracking)
- All closing information is stored in the original trade entry

**Example Use Case:**
1. You open a CSP trade (1 entry)
2. You click "Close" → Select "Expired"
3. The system updates the same trade entry with:
   - `close_date` = expiration date
   - `close_method` = 'expired'
   - `close_premium` = 0 (expired worthless)
   - `status` = 'Closed'
4. P&L is calculated automatically

**Benefits:**
- Cleaner trade list (no duplicate entries for full closes)
- Easier to see complete trade history in one place
- Better P&L tracking
- Can edit closing details after the fact

### What Breaks Without It:
- "Close" button won't work
- Can't update trades with closing information
- P&L calculations for closed trades will fail
- Editing closing details won't work

---

## Migration 3: Default Fee (`migrate_add_default_fee.py`)

### What It Does:
Adds **`default_fee` column to `accounts` table** - Stores a default fee per contract for each account

### Why It's Needed:
**Feature: Default Fees for Accounts**

Before v1.4.0, you had to enter fees manually for every trade. Now:
- You can set a default fee per account (e.g., $0.65 per contract)
- When creating a new trade, the fee field auto-populates with the account's default fee
- You can still override it if needed

**Example Use Case:**
1. You have Account A with default fee = $0.65
2. You have Account B with default fee = $1.00
3. When creating a trade for Account A, the fee field automatically shows $0.65
4. When creating a trade for Account B, the fee field automatically shows $1.00
5. Saves time and reduces errors

**Benefits:**
- Faster trade entry (one less field to fill)
- Consistent fee tracking
- Less chance of forgetting to enter fees

### What Breaks Without It:
- Default fee feature won't work
- Accounts page will crash when trying to load accounts (the code expects this column)
- Error: `column accounts.default_fee does not exist`

---

## Summary

| Migration | Purpose | Feature Enabled | Critical? |
|-----------|---------|-----------------|----------|
| **Stock Positions** | Track stock holdings | Stock Positions page, Covered Call integration | Yes |
| **Close Fields** | Single-entry close system | Enhanced close workflow, Edit closing details | Yes |
| **Default Fee** | Auto-populate fees | Default fees per account | **YES - App crashes without it** |

---

## Current Production Issue

Production is currently showing:
```
column accounts.default_fee does not exist
```

This means **Migration 3 (Default Fee)** hasn't been run yet. The code expects this column, but it doesn't exist in the production database.

**Solution:** Run all three migrations on production to enable all v1.4.0 features.

