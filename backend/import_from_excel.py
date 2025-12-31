#!/usr/bin/env python3
"""
Import trades from Excel file to database
"""
import sys
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import User, Account, Trade

load_dotenv()

def parse_excel_date(date_val):
    """Parse Excel date to Python date"""
    if pd.isna(date_val):
        return None
    if isinstance(date_val, str):
        try:
            return datetime.strptime(date_val, '%Y-%m-%d').date()
        except:
            return None
    if isinstance(date_val, pd.Timestamp):
        return date_val.date()
    return None

def map_strategy_to_trade_type(strategy):
    """Map Excel strategy to trade type"""
    if pd.isna(strategy):
        return 'CSP'
    
    strategy_str = str(strategy).lower()
    if 'put' in strategy_str:
        return 'CSP'
    elif 'call' in strategy_str and 'covered' in strategy_str:
        return 'Covered Call'
    elif 'call' in strategy_str:
        return 'LEAPS'
    else:
        return 'CSP'

def map_action_to_trade_action(action):
    """Map Excel action to trade action"""
    if pd.isna(action):
        return 'Sold to Open'
    
    action_str = str(action).lower()
    if 'open' in action_str:
        return 'Sold to Open'
    elif 'close' in action_str:
        return 'Bought to Close'
    elif 'assignment' in action_str:
        return 'Assigned'
    else:
        return 'Sold to Open'

def import_trades_from_excel(excel_path, user_email='test@example.com'):
    """Import trades from Excel file"""
    with app.app_context():
        # Get user
        user = User.query.filter_by(email=user_email).first()
        if not user:
            print(f'User {user_email} not found')
            return
        
        # Get or create account
        account = Account.query.filter_by(user_id=user.id).first()
        if not account:
            account = Account(
                user_id=user.id,
                name='Main',
                initial_balance=80000.00  # From Excel dashboard
            )
            db.session.add(account)
            db.session.commit()
            print(f'Created account: {account.name}')
        
        # Read Excel file
        print(f'Reading Excel file: {excel_path}')
        df = pd.read_excel(excel_path, sheet_name='Options Tracker')
        
        print(f'Found {len(df)} rows in Excel file')
        
        imported = 0
        skipped = 0
        
        for idx, row in df.iterrows():
            try:
                # Skip rows without Trade ID
                if pd.isna(row.get('Trade ID')):
                    continue
                
                trade_id = str(row['Trade ID'])
                ticker = str(row['Ticker']) if not pd.isna(row.get('Ticker')) else None
                
                if not ticker:
                    print(f'Skipping row {idx}: No ticker')
                    skipped += 1
                    continue
                
                # Determine if this is an opening or closing trade
                action = map_action_to_trade_action(row.get('Action (Open/Close/Roll/Assignment)'))
                is_closing = 'close' in str(action).lower() or 'assignment' in str(action).lower()
                
                # Get dates
                open_date = parse_excel_date(row.get('Open Date'))
                close_date = parse_excel_date(row.get('Close Date'))
                
                if not open_date:
                    print(f'Skipping row {idx}: No open date')
                    skipped += 1
                    continue
                
                # Get premium
                premium_val = row.get('Premium Collected (+) / Paid (-)')
                if pd.isna(premium_val):
                    premium = 0
                else:
                    premium = float(premium_val)
                
                # Get fees
                fees_val = row.get('Fees ($0.65 per contract per trade)')
                if pd.isna(fees_val):
                    fees = 0
                else:
                    fees = float(fees_val)
                
                # Get strike and expiration
                strike = float(row.get('Strike')) if not pd.isna(row.get('Strike')) else None
                expiration = parse_excel_date(row.get('Expiration'))
                
                # Get contracts
                contracts = int(row.get('Contracts', 1)) if not pd.isna(row.get('Contracts')) else 1
                
                # Determine trade type
                trade_type = map_strategy_to_trade_type(row.get('Strategy (Put/Call/CC/Wheel)'))
                
                # Determine status
                if is_closing:
                    status = 'Closed'
                    position_type = 'Close'
                else:
                    status = 'Open'
                    position_type = 'Open'
                
                # Check if trade already exists
                existing = Trade.query.filter_by(
                    account_id=account.id,
                    symbol=ticker,
                    trade_date=open_date,
                    trade_action=action
                ).first()
                
                if existing:
                    print(f'Skipping {trade_id}: Already exists')
                    skipped += 1
                    continue
                
                # Create trade
                trade = Trade(
                    account_id=account.id,
                    symbol=ticker,
                    trade_type=trade_type,
                    position_type=position_type,
                    strike_price=strike,
                    expiration_date=expiration,
                    contract_quantity=contracts,
                    trade_price=abs(premium) / (contracts * 100) if premium != 0 else 0,
                    trade_action=action,
                    premium=premium,
                    fees=fees,
                    trade_date=open_date,
                    open_date=open_date,
                    close_date=close_date if is_closing else None,
                    status=status,
                    notes=str(row.get('Notes', '')) if not pd.isna(row.get('Notes')) else None
                )
                
                # If closing, try to find parent trade
                if is_closing and not pd.isna(row.get('Trade ID')):
                    # Try to find opening trade with same ID prefix
                    parent_id_str = trade_id.split('_')[0] if '_' in trade_id else trade_id
                    parent = Trade.query.filter(
                        Trade.account_id == account.id,
                        Trade.symbol == ticker,
                        Trade.trade_action == 'Sold to Open',
                        Trade.status == 'Open'
                    ).first()
                    
                    if parent:
                        trade.parent_trade_id = parent.id
                        # Update parent status if fully closed
                        if contracts >= parent.contract_quantity:
                            parent.status = 'Closed'
                            parent.close_date = close_date
                
                db.session.add(trade)
                imported += 1
                print(f'Imported: {trade_id} - {ticker} {action} on {open_date}')
                
            except Exception as e:
                print(f'Error importing row {idx}: {e}')
                skipped += 1
                continue
        
        db.session.commit()
        print(f'\nImport complete!')
        print(f'Imported: {imported} trades')
        print(f'Skipped: {skipped} rows')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        excel_path = sys.argv[1]
    else:
        excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'options_tracker.xlsx')
        # Also check Documents folder
        if not os.path.exists(excel_path):
            excel_path = os.path.join(os.path.expanduser('~'), 'Documents', 'options_tracker.xlsx')
    
    if not os.path.exists(excel_path):
        print(f'Excel file not found: {excel_path}')
        print('Please provide the path to the Excel file as an argument')
        sys.exit(1)
    
    import_trades_from_excel(excel_path)
