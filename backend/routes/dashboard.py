from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Trade, Account, Deposit, Withdrawal
from datetime import datetime, timedelta, date
from collections import defaultdict
import requests
import time

dashboard_bp = Blueprint('dashboard', __name__)

def calculate_wheel_pnl(trades):
    """
    Calculate PNL for wheel strategy trades using the Trade model's calculate_realized_pnl method.
    This properly handles the full wheel cycle:
    - CSP opened → closed early (realized P&L = opening premium - closing premium)
    - CSP expired worthless (keep full premium)
    - CSP assigned → stock position created
    - Covered calls on assigned shares → closed early or expired
    - Covered calls assigned → shares called away (premium + stock appreciation)
    """
    realized_pnl = 0
    unrealized_pnl = 0
    
    # Process each trade
    for trade in trades:
        # Use the trade's own realized P&L calculation method
        trade_realized = trade.calculate_realized_pnl()
        
        if trade.status in ['Closed', 'Assigned', 'Called Away', 'Expired']:
            # Realized P&L for closed/assigned/called away trades
            realized_pnl += trade_realized
        else:
            # Unrealized P&L for open trades
            # For open positions, use the premium (will be realized when closed)
            net_premium = float(trade.premium) if trade.premium else 0
            unrealized_pnl += net_premium
    
    return realized_pnl, unrealized_pnl

def get_total_capital(account_id, user_id):
    """
    Calculate total working capital for an account.
    Includes: initial balance + deposits - withdrawals + realized P&L from all closed trades
    
    Realized P&L is considered as working capital since profits remain in the account
    unless explicitly withdrawn via the withdrawal feature.
    """
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    if not account:
        return 0
    
    # Start with initial balance
    total = float(account.initial_balance) if account.initial_balance else 0
    
    # Add deposits
    deposits = Deposit.query.filter_by(account_id=account_id).all()
    for deposit in deposits:
        total += float(deposit.amount) if deposit.amount else 0
    
    # Subtract withdrawals
    withdrawals = Withdrawal.query.filter_by(account_id=account_id).all()
    for withdrawal in withdrawals:
        total -= float(withdrawal.amount) if withdrawal.amount else 0
    
    # Add realized P&L from all closed trades (profits that are now working capital)
    # Get all trades for this account
    trades = Trade.query.filter_by(account_id=account_id).all()
    
    # Filter out closing trades (two-entry approach) - only include opening trades for P&L calculation
    # Closing trades' P&L is already included in their parent trade's P&L calculation
    filtered_trades = [
        trade for trade in trades 
        if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
    ]
    
    # Calculate realized P&L from closed trades
    realized_pnl = 0
    for trade in filtered_trades:
        # Only count realized P&L from closed/assigned/called away/expired trades
        # CRITICAL: Must include 'Called Away' to match calculate_wheel_pnl logic
        if trade.status in ['Closed', 'Assigned', 'Called Away', 'Expired']:
            trade_realized = trade.calculate_realized_pnl()
            realized_pnl += trade_realized
    
    # Add realized P&L to total capital (these profits are now working in the account)
    total += realized_pnl
    
    return total

@dashboard_bp.route('/positions', methods=['GET'])
@jwt_required()
def get_positions():
    user_id = get_jwt_identity()
    account_id = request.args.get('account_id', type=int)
    status = request.args.get('status', 'Open')  # 'Open', 'Closed', 'All'
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify({'open': [], 'closed': []}), 200
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    if status == 'Open':
        query = query.filter_by(status='Open')
    elif status == 'Closed':
        query = query.filter_by(status='Closed')
    
    trades = query.order_by(Trade.trade_date.desc()).all()
    
    # Filter out closing trades (two-entry approach) - only show opening trades
    filtered_trades = [
        trade for trade in trades 
        if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
    ]
    
    open_trades = [t.to_dict() for t in filtered_trades if t.status == 'Open']
    closed_trades = [t.to_dict() for t in filtered_trades if t.status in ['Closed', 'Assigned', 'Called Away', 'Expired']]
    
    return jsonify({
        'open': open_trades,
        'closed': closed_trades
    }), 200

@dashboard_bp.route('/pnl', methods=['GET'])
@jwt_required()
def get_pnl():
    user_id = get_jwt_identity()
    account_id = request.args.get('account_id', type=int)
    period = request.args.get('period', 'all')  # 'week', 'month', 'year', 'all'
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify({
            'realized_pnl': 0,
            'unrealized_pnl': 0,
            'total_pnl': 0,
            'rate_of_return': 0
        }), 200
    
    # Filter by date range
    now = datetime.now().date()
    date_filter = None
    
    if period == 'week':
        date_filter = now - timedelta(days=7)
    elif period == 'month':
        date_filter = now - timedelta(days=30)
    elif period == 'year':
        date_filter = now - timedelta(days=365)
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
        accounts_to_calc = [account_id]
    else:
        accounts_to_calc = account_ids
    
    if date_filter:
        query = query.filter(Trade.trade_date >= date_filter)
    
    trades = query.all()
    
    # Filter out closing trades (two-entry approach) - only include opening trades for P&L calculation
    # Closing trades are only for partial closes tracking
    filtered_trades = [
        trade for trade in trades 
        if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
    ]
    
    # Calculate PNL using improved wheel strategy logic
    realized_pnl = 0
    unrealized_pnl = 0
    
    # Group trades by account and symbol
    for acc_id in accounts_to_calc:
        acc_trades = [t for t in filtered_trades if t.account_id == acc_id]
        acc_realized, acc_unrealized = calculate_wheel_pnl(acc_trades)
        realized_pnl += acc_realized
        unrealized_pnl += acc_unrealized
    
    # Calculate total capital
    total_capital = 0
    for acc_id in accounts_to_calc:
        total_capital += get_total_capital(acc_id, user_id)
    
    total_pnl = realized_pnl + unrealized_pnl
    rate_of_return = (total_pnl / total_capital * 100) if total_capital > 0 else 0
    
    return jsonify({
        'realized_pnl': round(realized_pnl, 2),
        'unrealized_pnl': round(unrealized_pnl, 2),
        'total_pnl': round(total_pnl, 2),
        'rate_of_return': round(rate_of_return, 2),
        'total_capital': round(total_capital, 2),
        'period': period
    }), 200

@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    user_id = get_jwt_identity()
    account_id = request.args.get('account_id', type=int)
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify({
            'total_accounts': 0,
            'total_trades': 0,
            'open_positions': 0,
            'closed_positions': 0
        }), 200
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    all_trades = query.all()
    
    # Filter out closing trades (two-entry approach) - only count opening trades
    filtered_trades = [
        trade for trade in all_trades 
        if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
    ]
    
    # Get PNL for different periods
    week_pnl = get_pnl_data(user_id, account_id, 'week', account_ids)
    month_pnl = get_pnl_data(user_id, account_id, 'month', account_ids)
    year_pnl = get_pnl_data(user_id, account_id, 'year', account_ids)
    all_pnl = get_pnl_data(user_id, account_id, 'all', account_ids)
    
    return jsonify({
        'total_accounts': len(accounts),
        'total_trades': len(filtered_trades),
        'open_positions': len([t for t in filtered_trades if t.status == 'Open']),
        'closed_positions': len([t for t in filtered_trades if t.status in ['Closed', 'Assigned', 'Expired']]),
        'pnl': {
            'week': week_pnl,
            'month': month_pnl,
            'year': year_pnl,
            'all': all_pnl
        }
    }), 200

def get_pnl_data(user_id, account_id, period, account_ids):
    """Helper function to get PNL data for a period"""
    now = datetime.now().date()
    date_filter = None
    
    if period == 'week':
        date_filter = now - timedelta(days=7)
    elif period == 'month':
        date_filter = now - timedelta(days=30)
    elif period == 'year':
        date_filter = now - timedelta(days=365)
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    if date_filter:
        query = query.filter(Trade.trade_date >= date_filter)
    
    trades = query.all()
    
    # Filter out closing trades (two-entry approach) - only include opening trades for P&L calculation
    # Closing trades' P&L is already included in their parent trade's P&L calculation
    filtered_trades = [
        trade for trade in trades 
        if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
    ]
    
    # Use improved wheel PNL calculation
    realized, unrealized = calculate_wheel_pnl(filtered_trades)
    
    accounts_to_calc = [account_id] if account_id and account_id in account_ids else account_ids
    total_capital = sum([get_total_capital(acc_id, user_id) for acc_id in accounts_to_calc])
    
    total = realized + unrealized
    ror = (total / total_capital * 100) if total_capital > 0 else 0
    
    return {
        'realized_pnl': round(realized, 2),
        'unrealized_pnl': round(unrealized, 2),
        'total_pnl': round(total, 2),
        'rate_of_return': round(ror, 2)
    }

@dashboard_bp.route('/monthly-returns', methods=['GET'])
@jwt_required()
def get_monthly_returns():
    """
    Get monthly returns breakdown with YTD summary.
    Returns realized P&L grouped by year-month based on close_date.
    """
    user_id = get_jwt_identity()
    account_id = request.args.get('account_id', type=int)
    months_back = request.args.get('months', type=int, default=12)  # Default to last 12 months
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify({
            'monthly_returns': [],
            'ytd': {
                'total_return': 0,
                'return_percentage': 0,
                'year': date.today().year
            }
        }), 200
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
        accounts_to_calc = [account_id]
    else:
        accounts_to_calc = account_ids
    
    # Get all trades (we'll filter by close_date in Python for better control)
    all_trades = query.all()
    
    # Filter out closing trades (two-entry approach) - only include opening trades for P&L calculation
    # Closing trades' P&L is already included in their parent trade's P&L calculation
    filtered_trades = [
        trade for trade in all_trades 
        if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
    ]
    
    # Calculate total capital for return percentage calculation
    total_capital = sum([get_total_capital(acc_id, user_id) for acc_id in accounts_to_calc])
    
    # Group realized P&L by year-month based on close_date
    # For trades without close_date but with status 'Closed', use trade_date
    monthly_pnl = defaultdict(float)
    monthly_trades = defaultdict(list)
    
    today = date.today()
    current_year = today.year
    current_month = today.month
    
    # Calculate date threshold for last N months
    threshold_date = today - timedelta(days=months_back * 30)  # Approximate
    
    for trade in filtered_trades:
        # Determine the date to use for monthly grouping
        # Use close_date if available, otherwise use trade_date for closed trades
        pnl_date = None
        if trade.close_date:
            pnl_date = trade.close_date
        elif trade.status in ['Closed', 'Assigned', 'Called Away', 'Expired'] and trade.trade_date:
            pnl_date = trade.trade_date
        
        if not pnl_date:
            continue  # Skip trades without a date
        
        # Only include trades within the requested time range
        if pnl_date < threshold_date:
            continue
        
        # Calculate realized P&L for this trade
        realized_pnl = trade.calculate_realized_pnl()
        
        if realized_pnl != 0:  # Only include trades with realized P&L
            year_month = (pnl_date.year, pnl_date.month)
            monthly_pnl[year_month] += realized_pnl
            monthly_trades[year_month].append({
                'id': trade.id,
                'symbol': trade.symbol,
                'pnl': realized_pnl
            })
    
    # Convert to sorted list format with year-month labels
    monthly_returns = []
    for (year, month) in sorted(monthly_pnl.keys(), reverse=True):
        month_pnl = monthly_pnl[(year, month)]
        month_name = date(year, month, 1).strftime('%B')
        return_pct = (month_pnl / total_capital * 100) if total_capital > 0 else 0
        
        monthly_returns.append({
            'year': year,
            'month': month,
            'month_name': month_name,
            'year_month': f"{month_name} {year}",
            'total_return': round(month_pnl, 2),
            'return_percentage': round(return_pct, 2),
            'trade_count': len(monthly_trades[(year, month)])
        })
    
    # Calculate YTD (Year-to-Date) return
    # Sum all returns from January 1 of current year to today
    ytd_pnl = 0
    ytd_trades = []
    year_start = date(current_year, 1, 1)
    
    # Use filtered_trades (already filtered above) to avoid double-counting closing trades
    for trade in filtered_trades:
        pnl_date = None
        if trade.close_date:
            pnl_date = trade.close_date
        elif trade.status in ['Closed', 'Assigned', 'Called Away', 'Expired'] and trade.trade_date:
            pnl_date = trade.trade_date
        
        if pnl_date and year_start <= pnl_date <= today:
            realized_pnl = trade.calculate_realized_pnl()
            if realized_pnl != 0:
                ytd_pnl += realized_pnl
                ytd_trades.append(trade.id)
    
    ytd_return_pct = (ytd_pnl / total_capital * 100) if total_capital > 0 else 0
    
    return jsonify({
        'monthly_returns': monthly_returns,
        'ytd': {
            'total_return': round(ytd_pnl, 2),
            'return_percentage': round(ytd_return_pct, 2),
            'year': current_year,
            'trade_count': len(ytd_trades)
        },
        'total_capital': round(total_capital, 2)
    }), 200

@dashboard_bp.route('/open-positions-allocation', methods=['GET'])
@jwt_required()
def get_open_positions_allocation():
    """
    Get open positions with capital allocation percentages for pie chart.
    Groups by symbol and calculates capital at risk.
    """
    user_id = get_jwt_identity()
    account_id = request.args.get('account_id', type=int)
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify({
            'positions': [],
            'total_capital_at_risk': 0,
            'total_capital': 0
        }), 200
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
        accounts_to_calc = [account_id]
    else:
        accounts_to_calc = account_ids
    
    # Get only open positions (opening trades that haven't been fully closed)
    query = query.filter_by(status='Open')
    open_trades = query.filter(
        Trade.trade_action.in_(['Sold to Open', 'Bought to Open'])
    ).all()
    
    # Calculate total capital for percentage calculation
    total_capital = sum([get_total_capital(acc_id, user_id) for acc_id in accounts_to_calc])
    
    # Group by symbol and calculate capital at risk
    symbol_allocation = defaultdict(lambda: {
        'symbol': '',
        'capital_at_risk': 0,
        'contract_quantity': 0,
        'positions': []
    })
    
    total_capital_at_risk = 0
    
    for trade in open_trades:
        # Calculate remaining open quantity
        remaining_qty = trade.get_remaining_open_quantity()
        if remaining_qty <= 0:
            continue  # Skip fully closed positions
        
        # Calculate capital at risk for this position
        # For CSP: strike_price × remaining_quantity × 100
        # For Covered Call: assignment_price × remaining_quantity × 100 (if assigned) or strike × quantity × 100
        # For LEAPS: strike_price × remaining_quantity × 100 (for long positions)
        capital_at_risk = 0
        
        if trade.strike_price:
            capital_at_risk = float(trade.strike_price) * remaining_qty * 100
        
        # For assigned positions (Covered Calls), use assignment_price if available
        if trade.trade_type == 'Covered Call' and trade.parent_trade_id:
            parent = Trade.query.get(trade.parent_trade_id)
            if parent and parent.trade_type == 'Assignment' and parent.assignment_price:
                capital_at_risk = float(parent.assignment_price) * remaining_qty * 100
        
        symbol = trade.symbol
        symbol_allocation[symbol]['symbol'] = symbol
        symbol_allocation[symbol]['capital_at_risk'] += capital_at_risk
        symbol_allocation[symbol]['contract_quantity'] += remaining_qty
        symbol_allocation[symbol]['positions'].append({
            'id': trade.id,
            'trade_type': trade.trade_type,
            'strike_price': float(trade.strike_price) if trade.strike_price else None,
            'expiration_date': trade.expiration_date.isoformat() if trade.expiration_date else None,
            'contract_quantity': remaining_qty,
            'premium': float(trade.premium) if trade.premium else 0
        })
        
        total_capital_at_risk += capital_at_risk
    
    # Convert to list and calculate percentages
    positions = []
    for symbol, data in symbol_allocation.items():
        allocation_pct = (data['capital_at_risk'] / total_capital * 100) if total_capital > 0 else 0
        positions.append({
            'symbol': symbol,
            'capital_at_risk': round(data['capital_at_risk'], 2),
            'allocation_percentage': round(allocation_pct, 2),
            'contract_quantity': data['contract_quantity'],
            'position_count': len(data['positions']),
            'positions': data['positions']
        })
    
    # Sort by capital at risk (descending)
    positions.sort(key=lambda x: x['capital_at_risk'], reverse=True)
    
    return jsonify({
        'positions': positions,
        'total_capital_at_risk': round(total_capital_at_risk, 2),
        'total_capital': round(total_capital, 2),
        'unallocated_capital': round(total_capital - total_capital_at_risk, 2) if total_capital > 0 else 0
    }), 200

# Simple in-memory cache for market data (5 minute TTL)
_market_data_cache = {}
_cache_timestamps = {}

# Company logo cache (24 hour TTL - logos don't change often)
_company_logo_cache = {}
_logo_cache_timestamps = {}
LOGO_CACHE_TTL = 86400  # 24 hours

def _get_cached_market_data(symbol, cache_ttl=300):
    """Get market data from cache if available and not expired"""
    cache_key = symbol
    now = time.time()
    
    if cache_key in _market_data_cache:
        if now - _cache_timestamps.get(cache_key, 0) < cache_ttl:
            return _market_data_cache[cache_key]
    
    return None

def _set_cached_market_data(symbol, data):
    """Store market data in cache"""
    cache_key = symbol
    _market_data_cache[cache_key] = data
    _cache_timestamps[cache_key] = time.time()

def _fetch_quote_from_finnhub(symbol):
    """Fetch quote from Finnhub API"""
    api_key = current_app.config.get('FINNHUB_API_KEY')
    if not api_key:
        return None
    
    try:
        # URL encode the symbol in case it has special characters
        from urllib.parse import quote
        encoded_symbol = quote(symbol, safe='')
        url = f'https://finnhub.io/api/v1/quote?symbol={encoded_symbol}&token={api_key}'
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got valid data (not error response)
            if 'c' in data and data['c'] is not None:
                return {
                    'current_price': data.get('c', 0),
                    'previous_close': data.get('pc', 0),
                    'change': data.get('c', 0) - data.get('pc', 0),
                    'change_percent': ((data.get('c', 0) - data.get('pc', 0)) / data.get('pc', 1) * 100) if data.get('pc', 0) != 0 else 0,
                    'high': data.get('h', 0),
                    'low': data.get('l', 0),
                    'open': data.get('o', 0),
                    'timestamp': data.get('t', 0)
                }
    except Exception as e:
        print(f"Error fetching quote for {symbol}: {str(e)}")
    
    return None

@dashboard_bp.route('/market-data', methods=['GET'])
@jwt_required()
def get_market_data():
    """
    Get market data for symbols and indices.
    Supports:
    - Individual symbols (comma-separated)
    - Market indices: SPY (S&P 500), DIA (DJIA), QQQ (NASDAQ), VIX
    """
    user_id = get_jwt_identity()
    symbols_param = request.args.get('symbols', '')
    include_indices = request.args.get('include_indices', 'true').lower() == 'true'
    
    # Default market indices (ordered: DJIA, S&P 500, NASDAQ, VIX)
    # Finnhub quote endpoint doesn't support index symbols directly
    # Using ETF symbols and converting to index values
    # Mapping: display symbol -> (API symbol, conversion_factor)
    index_symbol_mapping = {
        'DIA': ('DIA', 100.0),        # DIA ETF × 100 = DJIA index
        'SPY': ('SPY', 10.0),         # SPY ETF × 10 = S&P 500 index
        'QQQ': ('QQQ', 37.7),         # QQQ ETF × 37.7 = NASDAQ index
        'VIX': ('VIXY', 0.56)         # VIXY ETF price × 0.56 ≈ VIX index (VIXY doesn't track 1:1)
    }
    
    market_indices = list(index_symbol_mapping.keys()) if include_indices else []
    
    # Parse symbols
    symbols = []
    if symbols_param:
        symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
    
    # Combine user symbols and indices
    all_symbols = list(set(symbols + market_indices))
    
    if not all_symbols:
        return jsonify({
            'quotes': {},
            'indices': {}
        }), 200
    
    quotes = {}
    indices = {}
    
    for symbol in all_symbols:
        quote_data = None
        
        # Determine the actual symbol to fetch from API and conversion factor
        # For indices, use the mapped API symbol; otherwise use symbol as-is
        if symbol in index_symbol_mapping:
            fetch_symbol, conversion_factor = index_symbol_mapping[symbol]
        else:
            fetch_symbol = symbol
            conversion_factor = 1.0
        
        # Try cache first (use fetch_symbol for cache key)
        cached_data = _get_cached_market_data(fetch_symbol)
        if cached_data:
            quote_data = cached_data
        else:
            # Fetch from API
            quote_data = _fetch_quote_from_finnhub(fetch_symbol)
            
            if quote_data:
                # Cache using the fetch_symbol (actual API symbol)
                _set_cached_market_data(fetch_symbol, quote_data)
        
        if quote_data:
            if symbol in market_indices:
                # Convert ETF prices to actual index values
                converted_data = {
                    'current_price': quote_data['current_price'] * conversion_factor,
                    'previous_close': quote_data['previous_close'] * conversion_factor,
                    'change': quote_data['change'] * conversion_factor,
                    'change_percent': quote_data['change_percent'],  # Percentage doesn't change
                    'high': quote_data.get('high', 0) * conversion_factor if quote_data.get('high') else 0,
                    'low': quote_data.get('low', 0) * conversion_factor if quote_data.get('low') else 0,
                    'open': quote_data.get('open', 0) * conversion_factor if quote_data.get('open') else 0,
                    'timestamp': quote_data.get('timestamp', 0)
                }
                indices[symbol] = converted_data
            else:
                quotes[symbol] = quote_data
    
    return jsonify({
        'quotes': quotes,
        'indices': indices
    }), 200

@dashboard_bp.route('/market-data/positions', methods=['GET'])
@jwt_required()
def get_positions_market_data():
    """
    Get market data for all symbols with open positions.
    Automatically fetches prices for all open positions.
    """
    user_id = get_jwt_identity()
    account_id = request.args.get('account_id', type=int)
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify({'quotes': {}}), 200
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    # Get open positions
    query = query.filter_by(status='Open')
    open_trades = query.filter(
        Trade.trade_action.in_(['Sold to Open', 'Bought to Open'])
    ).all()
    
    # Get unique symbols from open positions
    symbols = list(set([trade.symbol for trade in open_trades if trade.symbol]))
    
    if not symbols:
        return jsonify({'quotes': {}}), 200
    
    quotes = {}
    
    for symbol in symbols:
        # Try cache first
        cached_data = _get_cached_market_data(symbol)
        if cached_data:
            quotes[symbol] = cached_data
        else:
            # Fetch from API
            quote_data = _fetch_quote_from_finnhub(symbol)
            if quote_data:
                _set_cached_market_data(symbol, quote_data)
                quotes[symbol] = quote_data
    
    return jsonify({'quotes': quotes}), 200

def _get_cached_logo(symbol):
    """Get cached company logo"""
    cache_key = symbol.upper()
    if cache_key in _company_logo_cache:
        timestamp = _logo_cache_timestamps.get(cache_key, 0)
        if time.time() - timestamp < LOGO_CACHE_TTL:
            return _company_logo_cache[cache_key]
    return None

def _set_cached_logo(symbol, logo_url):
    """Store company logo in cache"""
    cache_key = symbol.upper()
    _company_logo_cache[cache_key] = logo_url
    _logo_cache_timestamps[cache_key] = time.time()

def _fetch_company_logo_from_finnhub(symbol):
    """Fetch company logo from Finnhub API"""
    api_key = current_app.config.get('FINNHUB_API_KEY')
    if not api_key:
        return None
    
    try:
        from urllib.parse import quote
        encoded_symbol = quote(symbol, safe='')
        url = f'https://finnhub.io/api/v1/stock/profile2?symbol={encoded_symbol}&token={api_key}'
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got valid data with logo
            if data and 'logo' in data and data['logo']:
                return data['logo']
    except Exception as e:
        print(f"Error fetching logo for {symbol}: {str(e)}")
    
    return None

@dashboard_bp.route('/company-logos', methods=['GET'])
@jwt_required()
def get_company_logos():
    """
    Get company logos for multiple symbols.
    Returns a dictionary mapping symbol to logo URL.
    """
    symbols_param = request.args.get('symbols', '')
    
    if not symbols_param:
        return jsonify({'logos': {}}), 200
    
    # Parse symbols (comma-separated)
    symbols = [s.strip().upper() for s in symbols_param.split(',') if s.strip()]
    
    if not symbols:
        return jsonify({'logos': {}}), 200
    
    logos = {}
    
    for symbol in symbols:
        # Try cache first
        cached_logo = _get_cached_logo(symbol)
        if cached_logo:
            logos[symbol] = cached_logo
        else:
            # Fetch from API
            logo_url = _fetch_company_logo_from_finnhub(symbol)
            if logo_url:
                _set_cached_logo(symbol, logo_url)
                logos[symbol] = logo_url
    
    return jsonify({'logos': logos}), 200

