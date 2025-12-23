import pandas as pd
from datetime import datetime
from models import Trade

def parse_trade_file(file, account_id):
    """
    Parse CSV or Excel file and convert to Trade objects.
    Expected columns (case-insensitive):
    - symbol, trade_type, strike_price, expiration_date, contract_quantity,
    - premium, fees, trade_date, status, notes, assignment_price, close_date
    """
    try:
        # Read file based on extension
        filename = file.filename.lower()
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            raise ValueError('Unsupported file format. Please use CSV or Excel files.')
        
        # Normalize column names (lowercase, strip whitespace)
        df.columns = df.columns.str.lower().str.strip()
        
        trades = []
        for _, row in df.iterrows():
            # Parse dates - include all date fields needed for calculations
            trade_date = None
            open_date = None
            expiration_date = None
            close_date = None
            
            if 'trade_date' in row and pd.notna(row['trade_date']):
                trade_date = pd.to_datetime(row['trade_date']).date()
            else:
                trade_date = datetime.now().date()
            
            # Parse open_date - critical for days_held and return % calculations
            if 'open_date' in row and pd.notna(row['open_date']):
                open_date = pd.to_datetime(row['open_date']).date()
            
            if 'expiration_date' in row and pd.notna(row['expiration_date']):
                expiration_date = pd.to_datetime(row['expiration_date']).date()
            
            if 'close_date' in row and pd.notna(row['close_date']):
                close_date = pd.to_datetime(row['close_date']).date()
            
            # Parse trade_price and trade_action - needed for premium calculation if not provided
            trade_price = float(row['trade_price']) if pd.notna(row.get('trade_price')) else None
            trade_action = str(row.get('trade_action', '')).strip() if pd.notna(row.get('trade_action')) else None
            
            trade = Trade(
                account_id=account_id,
                symbol=str(row.get('symbol', '')).upper().strip(),
                trade_type=str(row.get('trade_type', '')).strip(),
                position_type=str(row.get('position_type', 'Open')).strip(),
                strike_price=float(row['strike_price']) if pd.notna(row.get('strike_price')) else None,
                expiration_date=expiration_date,
                contract_quantity=int(row.get('contract_quantity', 1)) if pd.notna(row.get('contract_quantity')) else 1,
                trade_price=trade_price,
                trade_action=trade_action,
                premium=float(row.get('premium', 0)) if pd.notna(row.get('premium')) else 0,
                fees=float(row.get('fees', 0)) if pd.notna(row.get('fees')) else 0,
                assignment_price=float(row['assignment_price']) if pd.notna(row.get('assignment_price')) else None,
                trade_date=trade_date,
                open_date=open_date,
                close_date=close_date,
                status=str(row.get('status', 'Open')).strip(),
                parent_trade_id=int(row['parent_trade_id']) if pd.notna(row.get('parent_trade_id')) else None,
                notes=str(row.get('notes', '')) if pd.notna(row.get('notes')) else None
            )
            
            trades.append(trade)
        
        return trades
    except Exception as e:
        raise ValueError(f'Error parsing file: {str(e)}')

