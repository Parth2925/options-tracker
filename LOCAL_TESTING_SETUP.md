# Local Testing Setup - New Database

## ✅ Setup Complete

Your local backend is now configured to use the **new v1.4.0 database** for testing.

### What Changed

- **Updated `.env` file** in `backend/` directory
- **DATABASE_URL** now points to: `options_tracker_new_db`
- **Old .env backed up** to `.env.backup` (if it existed)

### Current Configuration

**Local Backend → New Database (v1.4.0)**
- Database: `options_tracker_new_db`
- Schema: v1.4.0 (with all new features)
- Status: Empty (ready for testing)

**Production → Old Database (v1.3.0)**
- Database: `options_tracker_peqw`
- Schema: v1.3.0
- Status: Running production (untouched)

## Testing Steps

### 1. Start Backend
```bash
cd backend
python3 app.py
```

### 2. Start Frontend
```bash
cd frontend
npm start
```

### 3. Test v1.4.0 Features

#### A. Basic Functionality
- [ ] Login/Create account
- [ ] Create account with default fee
- [ ] View accounts (should show default_fee field)

#### B. Stock Positions (New Feature)
- [ ] Navigate to Positions page
- [ ] Switch to "Stocks" tab
- [ ] Click "Add Stock Position"
- [ ] Create a stock position
- [ ] Edit stock position
- [ ] Delete stock position

#### C. Enhanced Close Workflow (New Feature)
- [ ] Create a trade (CSP, LEAPS, or Covered Call)
- [ ] Click "Close" button on the trade
- [ ] Test different close methods:
  - [ ] Buy to Close
  - [ ] Expired
  - [ ] Assigned
  - [ ] Exercise (for LEAPS)
- [ ] Verify P&L calculations
- [ ] Edit closing details after closing

#### D. Default Fees (New Feature)
- [ ] Edit an account
- [ ] Set a default fee (e.g., $0.65)
- [ ] Create a new trade for that account
- [ ] Verify fee field auto-populates with default fee
- [ ] Verify you can still override the fee

#### E. Trade History (New Feature)
- [ ] Create a trade with multiple contracts
- [ ] Do partial closes (e.g., close 1 of 2 contracts)
- [ ] Click "History" button
- [ ] Verify history shows all partial closes

#### F. Other Features
- [ ] Dashboard loads correctly
- [ ] Trades page works
- [ ] Positions page (Options tab) works
- [ ] Accounts page works
- [ ] Export/Import works

## Restoring Old Database (If Needed)

If you want to switch back to local SQLite or old database:

```bash
cd backend

# Restore from backup
cp .env.backup .env

# OR manually edit .env and change DATABASE_URL back to:
# DATABASE_URL=sqlite:///instance/options_tracker.db
# (or your old PostgreSQL URL)
```

## Notes

- **New database is empty** - You'll need to create test data
- **Production is unaffected** - Still using old database
- **Can switch back anytime** - Just update .env file
- **Old database is safe** - Serves as backup

## Next Steps After Testing

Once you've verified everything works:

1. **Migrate production data** to new database
2. **Switch production** to new database
3. **Keep old database** as backup for 1-2 weeks

## Troubleshooting

### Connection Issues
- Check that DATABASE_URL in .env is correct
- Verify SSL mode is set (should be automatic)
- Check network connectivity

### Schema Issues
- Verify database was initialized: `python3 initialize_new_database.py`
- Check that all v1.4.0 tables/columns exist

### Feature Not Working
- Check browser console for errors
- Check backend logs
- Verify you're on `feature/functional-improvements` branch

