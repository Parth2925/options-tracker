from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Trade, Account, StockPosition
from datetime import datetime
import pandas as pd
import io
from utils.import_utils import parse_trade_file

trades_bp = Blueprint('trades', __name__)

def get_user_id():
    """Helper to get user ID from JWT token, converting string to int"""
    user_id_str = get_jwt_identity()
    return int(user_id_str) if user_id_str else None

def calculate_premium(trade_price, trade_action, contract_quantity, fees):
    """
    Calculate premium based on trade price, action, quantity, and fees.
    
    Options contract size: 1 contract = 100 shares
    
    Trade actions:
    - Sold to Open: Receive premium, subtract fees
    - Bought to Close: Pay premium, add fees (negative)
    - Bought to Open: Pay premium, add fees (negative)
    - Sold to Close: Receive premium, subtract fees
    
    Formula:
    - Base premium = trade_price * contract_quantity * 100
    - Total fees = fees * contract_quantity
    
    For "Sold" actions: premium = base_premium - total_fees (positive)
    For "Bought" actions: premium = -(base_premium + total_fees) (negative)
    """
    if not trade_price or not trade_action or not contract_quantity:
        return 0
    
    trade_price = float(trade_price)
    contract_quantity = int(contract_quantity)
    fees = float(fees) if fees else 0
    
    # Base premium: price per contract * quantity * 100 (options contract size)
    base_premium = trade_price * contract_quantity * 100
    
    # Total fees: fee per contract * quantity
    total_fees = fees * contract_quantity
    
    # Calculate premium based on trade action
    if trade_action in ['Sold to Open', 'Sold to Close']:
        # Receiving premium, subtract fees
        premium = base_premium - total_fees
    elif trade_action in ['Bought to Close', 'Bought to Open']:
        # Paying premium, add fees (make negative)
        premium = -(base_premium + total_fees)
    else:
        # Fallback: if no action specified, assume it's already calculated
        premium = base_premium - total_fees
    
    return round(premium, 2)

@trades_bp.route('', methods=['GET'])
@jwt_required()
def get_trades():
    user_id = get_user_id()
    account_id = request.args.get('account_id', type=int)
    status = request.args.get('status')  # 'Open', 'Closed', 'All'
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify([]), 200
    
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    if status and status != 'All':
        query = query.filter_by(status=status)
    
    trades = query.order_by(Trade.trade_date.desc()).all()
    # Auto-update status for all trades and include realized P&L
    # BUT: Don't override status for trades that were explicitly set during creation/update
    # Only auto-update if status seems incorrect (e.g., expired trades)
    for trade in trades:
        # Only auto-update if the trade appears to need status correction
        # Don't override status that was explicitly set during partial close handling
        if trade.trade_action in ['Sold to Open', 'Bought to Open']:
            # For opening trades, check if status should be updated based on child trades
            # BUT: If trade is explicitly "Open" and has remaining quantity, don't override
            remaining_qty = trade.get_remaining_open_quantity()
            if trade.status == 'Open' and remaining_qty > 0:
                # Trade is explicitly Open with remaining quantity - don't override
                continue
            
            # Don't override special statuses (Called Away, Assigned) that were explicitly set
            if trade.status in ['Called Away', 'Assigned']:
                continue
            
            # Don't override manually set 'Closed' status (e.g., for expired worthless trades)
            # If user manually set status to 'Closed', respect that choice
            if trade.status == 'Closed' and not trade.close_date:
                # This is likely a manually marked expired worthless trade - don't override
                continue
            
            new_status = trade.auto_determine_status()
            if new_status != trade.status:
                trade.status = new_status
    db.session.commit()
    
    # Filter out closing trades (two-entry approach) - only show opening trades
    # Closing trades are only for partial closes tracking and shouldn't appear in main list
    filtered_trades = [
        trade for trade in trades 
        if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
    ]
    
    return jsonify([trade.to_dict(include_realized_pnl=True) for trade in filtered_trades]), 200

@trades_bp.route('', methods=['POST'])
@jwt_required()
def create_trade():
    user_id = get_user_id()
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request data is required'}), 400
    
    if not data.get('account_id'):
        return jsonify({'error': 'Please select an account'}), 400
    
    if not data.get('symbol') or not data.get('symbol').strip():
        return jsonify({'error': 'Symbol is required (e.g., AAPL, TSLA)'}), 400
    
    if not data.get('trade_type'):
        return jsonify({'error': 'Trade type is required'}), 400
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=data['account_id'], user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    # For Assignment trades, handle differently - no trade_price or trade_action needed
    trade_type = data.get('trade_type')
    is_assignment = trade_type == 'Assignment'
    
    trade_price = data.get('trade_price') if not is_assignment else None
    trade_action = data.get('trade_action') if not is_assignment else None
    contract_quantity = data.get('contract_quantity', 1)
    fees = data.get('fees', 0)
    
    # Calculate premium automatically if trade_price is provided (not for Assignment)
    if is_assignment:
        # Assignment trades have no premium - P&L comes from parent CSP
        premium = 0
    elif trade_price and trade_action:
        premium = calculate_premium(trade_price, trade_action, contract_quantity, fees)
    else:
        # Fallback to provided premium or 0
        premium = data.get('premium', 0)
    
    # Validate closing trade quantity doesn't exceed available
    if data.get('parent_trade_id') and trade_action in ['Bought to Close', 'Sold to Close']:
        parent = Trade.query.get(data['parent_trade_id'])
        if parent:
            remaining_qty = parent.get_remaining_open_quantity()
            if contract_quantity > remaining_qty:
                return jsonify({
                    'error': f'Cannot close {contract_quantity} contracts. Only {remaining_qty} contracts remaining open.'
                }), 400
    
    # Validate covered call requires stock position
    if trade_type == 'Covered Call':
        stock_position_id = data.get('stock_position_id')
        if not stock_position_id:
            return jsonify({'error': 'Please select a stock position. You need to own shares to write a covered call.'}), 400
        
        # Verify stock position exists and belongs to user's account
        stock_position = StockPosition.query.get(stock_position_id)
        if not stock_position:
            return jsonify({'error': 'Stock position not found'}), 404
        
        # Verify stock position belongs to the same account
        if stock_position.account_id != data['account_id']:
            return jsonify({'error': 'Stock position must belong to the same account'}), 400
        
        # Verify symbol matches
        if stock_position.symbol.upper() != data.get('symbol', '').upper():
            return jsonify({'error': f'Stock position symbol ({stock_position.symbol}) does not match trade symbol ({data.get("symbol")})'}), 400
        
        # Verify stock position is open
        if stock_position.status != 'Open':
            return jsonify({'error': f'Stock position is not open (status: {stock_position.status})'}), 400
        
        # Calculate shares needed (contracts × 100)
        shares_needed = contract_quantity * 100
        
        # Get available shares (total - used by other open covered calls)
        available_shares = stock_position.get_available_shares()
        
        if shares_needed > available_shares:
            return jsonify({
                'error': f'Insufficient shares available. Need {shares_needed} shares, but only {available_shares} available in stock position.'
            }), 400
    
    trade_date = datetime.strptime(data['trade_date'], '%Y-%m-%d').date() if data.get('trade_date') else datetime.now().date()
    close_date = datetime.strptime(data['close_date'], '%Y-%m-%d').date() if data.get('close_date') else None
    
    # Determine open_date: if this is a closing trade, use parent's trade_date
    # For Assignment trades, use parent's trade_date (when CSP was opened) if available, otherwise use assignment date
    open_date = data.get('open_date')
    if open_date:
        open_date = datetime.strptime(open_date, '%Y-%m-%d').date()
    else:
        open_date = None
    
    if data.get('parent_trade_id') and trade_action in ['Bought to Close', 'Sold to Close']:
        parent = Trade.query.get(data['parent_trade_id'])
        if parent:
            open_date = parent.trade_date
            # Set close_date to this trade's date if not provided
            if not close_date:
                close_date = trade_date
    
    # Auto-determine position_type based on trade_action if not explicitly provided
    position_type = data.get('position_type')
    if not position_type:
        if is_assignment:
            position_type = 'Assignment'
        elif trade_action in ['Bought to Close', 'Sold to Close']:
            position_type = 'Close'
        elif trade_action in ['Sold to Open', 'Bought to Open']:
            position_type = 'Open'
        else:
            position_type = 'Open'  # Default fallback
    
    # Initialize variables
    status = data.get('status', 'Open')
    assignment_price = data.get('assignment_price')
    symbol = data.get('symbol')
    strike_price = data.get('strike_price')
    
    # For Assignment trades, ensure status is 'Assigned' and set assignment_price from parent if not provided
    if is_assignment:
        # Auto-set status to Assigned
        status = 'Assigned'
        
        # If parent_trade_id is provided, auto-fill missing fields from parent
        if data.get('parent_trade_id'):
            parent = Trade.query.get(data['parent_trade_id'])
            if parent:
                # Auto-fill assignment_price from parent's strike_price if not provided
                if not data.get('assignment_price') and parent.strike_price:
                    assignment_price = float(parent.strike_price)
                else:
                    assignment_price = data.get('assignment_price')
                
                # Auto-fill symbol, strike_price, contract_quantity from parent if not provided
                symbol = data.get('symbol') or parent.symbol
                strike_price = data.get('strike_price') or parent.strike_price
                contract_quantity = data.get('contract_quantity') or parent.contract_quantity
                
                # Set open_date to parent's trade_date (when the CSP was opened)
                # This ensures days_held is calculated from when the position was originally opened
                # For Assignment trades, we track from when the CSP was opened, not just when assigned
                if not open_date:
                    open_date = parent.trade_date
    
    trade = Trade(
        account_id=data['account_id'],
        symbol=(symbol or data.get('symbol', '')).upper(),
        trade_type=data['trade_type'],
        position_type=position_type,
        strike_price=strike_price or data.get('strike_price'),
        expiration_date=datetime.strptime(data['expiration_date'], '%Y-%m-%d').date() if data.get('expiration_date') else None,
        contract_quantity=contract_quantity,
        trade_price=trade_price,
        trade_action=trade_action,
        premium=premium,
        fees=fees if not is_assignment else 0,  # No fees for Assignment trades
        assignment_price=assignment_price,
        trade_date=trade_date,
        open_date=open_date,
        close_date=close_date,
        status=status,
        parent_trade_id=data.get('parent_trade_id'),
        stock_position_id=data.get('stock_position_id'),
        shares_used=(contract_quantity * 100) if trade_type == 'Covered Call' and data.get('stock_position_id') else None,
        notes=data.get('notes')
    )
    
    try:
        db.session.add(trade)
        # Don't commit yet - we need to update parent status first
        
        # For closing trades, ALWAYS set status to 'Closed' regardless of user input
        # This ensures closing trades are never marked as 'Open'
        if trade.trade_action in ['Bought to Close', 'Sold to Close']:
            trade.status = 'Closed'
            # Also ensure close_date is set if not provided
            if not trade.close_date:
                trade.close_date = trade.trade_date
        # Auto-determine status for other trades if not explicitly set
        elif not data.get('status'):
            trade.status = trade.auto_determine_status()
        
        # If this is a closing trade, update parent status and dates BEFORE commit
        # This ensures parent status is correct when we commit
        if trade.parent_trade_id:
            parent = Trade.query.get(trade.parent_trade_id)
            if parent:
                if trade.trade_action in ['Bought to Close', 'Sold to Close']:
                    # Check if this is a partial close or full close
                    # Count total closed quantity for this parent
                    # IMPORTANT: Query database directly to avoid counting the current trade that's in memory
                    # The current trade is added to session but not yet committed, so it won't be in the database yet
                    # Query directly from database to get only committed closing trades
                    from sqlalchemy import and_
                    if trade.id:
                        # Trade exists in DB (being updated), exclude it from query
                        existing_closing_trades = Trade.query.filter(
                            and_(
                                Trade.parent_trade_id == parent.id,
                                Trade.trade_action.in_(['Bought to Close', 'Sold to Close']),
                                Trade.id != trade.id
                            )
                        ).all()
                    else:
                        # New trade (not in DB yet), query all closing trades for this parent
                        existing_closing_trades = Trade.query.filter(
                            and_(
                                Trade.parent_trade_id == parent.id,
                                Trade.trade_action.in_(['Bought to Close', 'Sold to Close'])
                            )
                        ).all()
                    # Calculate total closed quantity
                    # IMPORTANT: Use relationship-based calculation instead of database query
                    # The relationship reflects the actual committed state, while database query might find stale/duplicate trades
                    # Get remaining open quantity from relationship (doesn't include current trade yet)
                    remaining_from_relationship = parent.get_remaining_open_quantity()
                    # Calculate how many will be closed after adding current trade
                    # Formula: (parent_qty - remaining_open) + current_trade_qty
                    total_closed_qty = (parent.contract_quantity - remaining_from_relationship) + trade.contract_quantity
                    
                    # Only mark parent as closed if all contracts are closed
                    if total_closed_qty >= parent.contract_quantity:
                        parent.status = 'Closed'
                        parent.close_date = trade.trade_date
                    else:
                        # Partial close - explicitly keep parent open
                        parent.status = 'Open'
                        parent.close_date = None  # Clear close_date if it was set
                    # Set parent's open_date if not set (should be parent's own trade_date)
                    if not parent.open_date:
                        parent.open_date = parent.trade_date
                    
                    # IMPORTANT: Ensure closing trade's open_date is set from parent
                    # This is critical for return calculations
                    if not trade.open_date:
                        trade.open_date = parent.trade_date
                    # Also ensure close_date is set
                    if not trade.close_date:
                        trade.close_date = trade.trade_date
                elif trade.trade_type == 'Assignment':
                    # Assignment trade - mark parent CSP as Assigned
                    if parent.trade_type == 'CSP':
                        parent.status = 'Assigned'
                        parent.assignment_price = trade.assignment_price or parent.strike_price
                        # Set parent's close_date to assignment date (expiration date)
                        # This is critical for Days Held and Return % calculations
                        parent.close_date = trade.trade_date
                        # Set parent's open_date if not set
                        if not parent.open_date:
                            parent.open_date = parent.trade_date
                        
                        # Auto-create stock position from CSP assignment
                        # Shares = contracts × 100, Cost basis = assignment_price (strike price)
                        shares = trade.contract_quantity * 100
                        cost_basis = float(trade.assignment_price) if trade.assignment_price else float(parent.strike_price) if parent.strike_price else 0
                        
                        if shares > 0 and cost_basis > 0:
                            stock_position = StockPosition(
                                account_id=trade.account_id,
                                symbol=trade.symbol,
                                shares=shares,
                                cost_basis_per_share=cost_basis,
                                acquired_date=trade.trade_date,
                                status='Open',
                                source_trade_id=trade.id,
                                notes=f'Assigned from CSP trade #{parent.id}'
                            )
                            db.session.add(stock_position)
                elif trade.trade_type == 'Covered Call' and parent.trade_type == 'Assignment':
                    # Covered call on assigned shares - no status change needed
                    pass
        
        # Now commit all changes (trade and parent updates)
        db.session.commit()
        
        return jsonify(trade.to_dict(include_realized_pnl=True)), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/<int:trade_id>', methods=['GET'])
@jwt_required()
def get_trade(trade_id):
    user_id = get_user_id()
    trade = Trade.query.get(trade_id)
    
    if not trade:
        return jsonify({'error': 'Trade not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=trade.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(trade.to_dict(include_realized_pnl=True)), 200

@trades_bp.route('/<int:trade_id>', methods=['PUT'])
@jwt_required()
def update_trade(trade_id):
    user_id = get_user_id()
    trade = Trade.query.get(trade_id)
    
    if not trade:
        return jsonify({'error': 'Trade not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=trade.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    
    # Validate closing trade quantity doesn't exceed available
    if data.get('parent_trade_id') is not None and trade.trade_action in ['Bought to Close', 'Sold to Close']:
        parent = Trade.query.get(data['parent_trade_id'] or trade.parent_trade_id)
        if parent:
            # Calculate remaining quantity excluding current trade's quantity
            current_closing_qty = data.get('contract_quantity', trade.contract_quantity)
            # Get all closing trades except the current one being updated
            other_closing_trades = [child for child in parent.child_trades 
                                   if child.id != trade.id and child.trade_action in ['Bought to Close', 'Sold to Close']]
            total_closed_by_others = sum(child.contract_quantity for child in other_closing_trades)
            remaining_qty = parent.contract_quantity - total_closed_by_others
            
            if current_closing_qty > remaining_qty:
                return jsonify({
                    'error': f'Cannot close {current_closing_qty} contracts. Only {remaining_qty} contracts remaining open.'
                }), 400
    
    # Update fields
    if data.get('account_id'):
        # Validate new account belongs to user
        new_account = Account.query.filter_by(id=data['account_id'], user_id=user_id).first()
        if not new_account:
            return jsonify({'error': 'Account not found or unauthorized'}), 404
        # If changing account, validate stock_position_id belongs to new account
        if trade.stock_position_id and trade.account_id != data['account_id']:
            stock_position = StockPosition.query.get(trade.stock_position_id)
            if stock_position and stock_position.account_id != data['account_id']:
                # Clear stock_position_id if it doesn't belong to new account
                trade.stock_position_id = None
                trade.shares_used = None
        trade.account_id = data['account_id']
    if data.get('symbol'):
        trade.symbol = data['symbol'].upper()
    if data.get('trade_type'):
        # If changing trade type away from Covered Call, clear stock_position_id
        if trade.trade_type == 'Covered Call' and data['trade_type'] != 'Covered Call':
            trade.stock_position_id = None
            trade.shares_used = None
        trade.trade_type = data['trade_type']
    if data.get('position_type'):
        trade.position_type = data['position_type']
    if data.get('strike_price') is not None:
        trade.strike_price = data['strike_price']
    if data.get('expiration_date'):
        trade.expiration_date = datetime.strptime(data['expiration_date'], '%Y-%m-%d').date()
    if data.get('contract_quantity') is not None:
        trade.contract_quantity = data['contract_quantity']
    if data.get('trade_price') is not None:
        trade.trade_price = data['trade_price']
    if data.get('trade_action'):
        trade.trade_action = data['trade_action']
    if data.get('fees') is not None:
        trade.fees = data['fees']
    if data.get('assignment_price') is not None:
        trade.assignment_price = data['assignment_price']
    if data.get('trade_date'):
        trade.trade_date = datetime.strptime(data['trade_date'], '%Y-%m-%d').date()
    if data.get('open_date'):
        trade.open_date = datetime.strptime(data['open_date'], '%Y-%m-%d').date()
    # Handle close_date - allow clearing it (for expired worthless trades)
    if 'close_date' in data:
        if data['close_date'] and data['close_date'].strip():
            # Set close_date if provided and not empty
            trade.close_date = datetime.strptime(data['close_date'], '%Y-%m-%d').date()
        else:
            # Explicitly clear close_date if None or empty string is sent
            # This is important for expired worthless trades
            trade.close_date = None
    
    # Ensure open_date is set correctly for closed trades (important for days_held and return calculations)
    # For single-entry closes (trade has close_date and close_premium), open_date should be trade_date
    # For two-entry closes (closing trades with parent), open_date should be parent's trade_date
    if trade.close_date:
        if trade.parent_trade_id and trade.trade_action in ['Bought to Close', 'Sold to Close']:
            # Two-entry close: use parent's trade_date
            parent = Trade.query.get(trade.parent_trade_id)
            if parent:
                trade.open_date = parent.trade_date
        elif not trade.open_date:
            # Single-entry close: use trade's own trade_date if open_date not set
            trade.open_date = trade.trade_date
    if data.get('status'):
        trade.status = data['status']
    if data.get('parent_trade_id') is not None:
        trade.parent_trade_id = data['parent_trade_id']
        # If this is a closing trade, set open_date from parent
        if trade.parent_trade_id and trade.trade_action in ['Bought to Close', 'Sold to Close']:
            parent = Trade.query.get(trade.parent_trade_id)
            if parent:
                trade.open_date = parent.trade_date
                if not trade.close_date:
                    trade.close_date = trade.trade_date
    if data.get('notes') is not None:
        trade.notes = data['notes']
    
    # Handle close details (for editing closed trades)
    close_price_changed = 'close_price' in data
    close_fees_changed = 'close_fees' in data
    close_method_changed = 'close_method' in data
    
    if close_price_changed:
        trade.close_price = data['close_price'] if data['close_price'] is not None and data['close_price'] != '' else None
    if close_fees_changed:
        trade.close_fees = data['close_fees'] if data['close_fees'] is not None and data['close_fees'] != '' else 0
    if close_method_changed:
        trade.close_method = data['close_method'] if data['close_method'] else None
    
    # Auto-calculate close_premium if close_price or close_fees changed and close_method requires it
    # Always auto-calculate when close_price or close_fees change to keep close_premium in sync
    # User can still manually override by explicitly changing close_premium in the form
    close_premium_provided = 'close_premium' in data and data.get('close_premium') is not None and data.get('close_premium') != ''
    
    # Auto-calculate if:
    # 1. close_premium not provided (frontend didn't send it), OR
    # 2. close_price or close_fees changed (always recalculate to keep in sync), OR
    # 3. close_premium is None/empty in data (user cleared it)
    should_auto_calculate = False
    if 'close_premium' not in data:
        # close_premium not provided - auto-calculate if conditions are met
        should_auto_calculate = True
    elif close_price_changed or close_fees_changed:
        # close_price or close_fees changed - always auto-calculate to keep close_premium in sync
        # This ensures close_premium updates when user edits close_price or close_fees
        should_auto_calculate = True
    elif 'close_premium' in data and (data['close_premium'] is None or data['close_premium'] == ''):
        # close_premium is None or empty - auto-calculate if close_price or close_fees changed
        should_auto_calculate = (close_price_changed or close_fees_changed)
    
    if should_auto_calculate and trade.close_method in ['buy_to_close', 'sell_to_close']:
        if trade.close_price is not None:
            # Determine trade_action based on close_method
            trade_action = 'Bought to Close' if trade.close_method == 'buy_to_close' else 'Sold to Close'
            # Calculate premium using the same logic as the close endpoint
            trade.close_premium = calculate_premium(trade.close_price, trade_action, trade.contract_quantity, trade.close_fees or 0)
    elif close_premium_provided:
        # User explicitly provided close_premium (non-null, non-empty), use it
        trade.close_premium = data['close_premium']
    
    # Handle stock_position_id for covered calls (optional for backward compatibility)
    if 'stock_position_id' in data:
        if data['stock_position_id']:
            # Validate stock position if provided
            stock_position = StockPosition.query.get(data['stock_position_id'])
            if not stock_position:
                return jsonify({'error': 'Stock position not found'}), 404
            if stock_position.account_id != trade.account_id:
                return jsonify({'error': 'Stock position must belong to the same account'}), 400
            if stock_position.symbol.upper() != trade.symbol.upper():
                return jsonify({'error': f'Stock position symbol ({stock_position.symbol}) does not match trade symbol ({trade.symbol})'}), 400
            trade.stock_position_id = data['stock_position_id']
            # Update shares_used if it's a covered call
            if trade.trade_type == 'Covered Call':
                trade.shares_used = trade.contract_quantity * 100
        else:
            # Allow clearing stock_position_id (for backward compatibility)
            trade.stock_position_id = None
            trade.shares_used = None
    
    # Handle Assignment trades specially
    is_assignment = trade.trade_type == 'Assignment'
    
    # Recalculate premium if trade_price or trade_action changed (not for Assignment)
    if not is_assignment and (data.get('trade_price') is not None or data.get('trade_action') or data.get('contract_quantity') is not None or data.get('fees') is not None):
        if trade.trade_price and trade.trade_action:
            trade.premium = calculate_premium(trade.trade_price, trade.trade_action, trade.contract_quantity, trade.fees)
        elif data.get('premium') is not None:
            # Fallback to provided premium
            trade.premium = data['premium']
    elif is_assignment:
        # Assignment trades have no premium
        trade.premium = 0
        trade.fees = 0
    
    # For Assignment trades, always set status to 'Assigned'
    if is_assignment:
        trade.status = 'Assigned'
    # For closing trades, ALWAYS set status to 'Closed' regardless of user input
    elif trade.trade_action in ['Bought to Close', 'Sold to Close']:
        trade.status = 'Closed'
        # Also ensure close_date is set if not provided
        if not trade.close_date:
            trade.close_date = trade.trade_date
    # Auto-determine status for other trades if not explicitly set
    elif not data.get('status'):
        trade.status = trade.auto_determine_status()
    # If status was explicitly provided for non-closing trades, use it
    elif data.get('status'):
        trade.status = data['status']
    
    # If this is a closing trade, update parent status and dates
    if trade.parent_trade_id and trade.trade_action in ['Bought to Close', 'Sold to Close']:
        parent = Trade.query.get(trade.parent_trade_id)
        if parent:
            # Check if this is a partial close or full close
            # Count total closed quantity for this parent
            # IMPORTANT: Query database directly to avoid counting the current trade that's in memory
            from sqlalchemy import and_
            existing_closing_trades = Trade.query.filter(
                and_(
                    Trade.parent_trade_id == parent.id,
                    Trade.trade_action.in_(['Bought to Close', 'Sold to Close']),
                    Trade.id != trade.id  # Exclude current trade being updated
                )
            ).all()
            total_closed_qty = sum(child.contract_quantity for child in existing_closing_trades)
            total_closed_qty += trade.contract_quantity  # Include current closing trade
            
            # Only mark parent as closed if all contracts are closed
            if total_closed_qty >= parent.contract_quantity:
                parent.status = 'Closed'
                if not parent.close_date:
                    parent.close_date = trade.trade_date
            else:
                # Partial close - keep parent open
                parent.status = 'Open'
            if not parent.open_date:
                parent.open_date = parent.trade_date
    
    # Final check: Ensure open_date is set correctly for closed trades (important for days_held and return calculations)
    # This ensures open_date is correct even if close_date was set earlier in the update
    if trade.close_date:
        if trade.parent_trade_id and trade.trade_action in ['Bought to Close', 'Sold to Close']:
            # Two-entry close: use parent's trade_date
            parent = Trade.query.get(trade.parent_trade_id)
            if parent:
                trade.open_date = parent.trade_date
        elif not trade.open_date:
            # Single-entry close: use trade's own trade_date if open_date not set
            trade.open_date = trade.trade_date
    
    trade.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        # Return updated trade with recalculated P&L, days_held, and return metrics
        return jsonify(trade.to_dict(include_realized_pnl=True)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/<int:trade_id>', methods=['DELETE'])
@jwt_required()
def delete_trade(trade_id):
    user_id = get_user_id()
    trade = Trade.query.get(trade_id)
    
    if not trade:
        return jsonify({'error': 'Trade not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=trade.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(trade)
        db.session.commit()
        return jsonify({'message': 'Trade deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/<int:trade_id>/chain', methods=['GET'])
@jwt_required()
def get_trade_chain(trade_id):
    """Get the full trade chain (parent, current, children)"""
    user_id = get_user_id()
    trade = Trade.query.get(trade_id)
    
    if not trade:
        return jsonify({'error': 'Trade not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=trade.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    chain = trade.get_trade_chain()
    return jsonify(chain), 200

@trades_bp.route('/import', methods=['POST'])
@jwt_required()
def import_trades():
    user_id = get_user_id()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    account_id = request.form.get('account_id', type=int)
    
    if not account_id:
        return jsonify({'error': 'account_id is required'}), 400
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    try:
        trades = parse_trade_file(file, account_id)
        
        # IMPORTANT: parent_trade_id in the file refers to old database IDs
        # We need to import in order and create a mapping from old IDs to new IDs
        # Strategy: Import in two passes
        # 1. First pass: Import all trades without parent relationships, store old_id -> new_id mapping
        # 2. Second pass: Update parent_trade_id references using the mapping
        
        # Store original parent_trade_id from file (before we lose it)
        old_parent_ids = {}
        for idx, trade in enumerate(trades):
            old_parent_ids[idx] = trade.parent_trade_id
        
        # Post-process trades to ensure data integrity
        # Note: parent_trade_id will be cleared temporarily and restored after import
        for idx, trade in enumerate(trades):
            # Clear parent_trade_id temporarily (we'll set it after all trades are imported)
            trade.parent_trade_id = None
            
            # Only recalculate premium if it's missing or zero AND trade_price/trade_action are provided
            # This preserves the original premium value from export
            if trade.trade_type != 'Assignment':
                if (not trade.premium or trade.premium == 0) and trade.trade_price and trade.trade_action:
                    # Recalculate premium only if premium is missing/zero
                    trade.premium = calculate_premium(trade.trade_price, trade.trade_action, trade.contract_quantity, trade.fees)
        
        # Bulk insert trades (without parent relationships first)
        db.session.add_all(trades)
        db.session.flush()  # Get new IDs without committing
        
        # Build mapping: row_index -> new_trade_id
        id_mapping = {}
        for idx, trade in enumerate(trades):
            id_mapping[idx] = trade.id
        
        # Now match parent trades and update parent_trade_id
        # Since exported parent_trade_id refers to old DB IDs, we need to match by characteristics
        # Strategy: Match parent by symbol, trade_type, strike_price
        # For closing trades, parent date should be <= child date (opening happens before/on closing date)
        for idx, trade in enumerate(trades):
            original_parent_id = old_parent_ids.get(idx)
            
            if original_parent_id is not None:
                # Find the parent trade by matching characteristics
                parent_trade = None
                for parent_idx, potential_parent in enumerate(trades):
                    if parent_idx == idx:
                        continue  # Skip self
                    
                    # Match by key characteristics: symbol, trade_type, strike_price
                    # For closing trades, we DON'T match on exact trade_date because closing date is different from opening date
                    # Parent should be an opening trade (Sold to Open or Bought to Open)
                    # Parent's trade_date should be BEFORE or EQUAL to child's trade_date (closing can't happen before opening)
                    symbol_match = potential_parent.symbol == trade.symbol
                    type_match = potential_parent.trade_type == trade.trade_type
                    strike_match = potential_parent.strike_price == trade.strike_price
                    is_opening = potential_parent.trade_action in ['Sold to Open', 'Bought to Open']
                    # For closing trades, parent date should be <= child date (opening happens before/on closing date)
                    # For assignment trades, we can be more flexible
                    if trade.trade_action in ['Bought to Close', 'Sold to Close']:
                        date_valid = potential_parent.trade_date <= trade.trade_date
                    else:
                        # For other trade types (like Assignment), match on exact date
                        date_valid = potential_parent.trade_date == trade.trade_date
                    
                    if (symbol_match and type_match and strike_match and date_valid and is_opening):
                        # This looks like the parent
                        parent_trade = potential_parent
                        break
                
                if parent_trade:
                    trade.parent_trade_id = parent_trade.id
                    # Mark as modified to ensure SQLAlchemy tracks the change
                    from sqlalchemy.orm.attributes import flag_modified
                    flag_modified(trade, 'parent_trade_id')
        
        # Now update open_date and other parent-dependent fields AFTER parent relationships are set
        for trade in trades:
            # Handle single-entry closes (new format: has close_date and close_premium/close_method, no parent_trade_id)
            if trade.close_date and (trade.close_premium is not None or trade.close_method) and not trade.parent_trade_id:
                # Single-entry close: ensure open_date is set (should be trade_date if not provided)
                if not trade.open_date:
                    trade.open_date = trade.trade_date
                # Ensure status is set correctly based on close_method
                if trade.close_method == 'expired':
                    trade.status = 'Expired'
                elif trade.close_method == 'assigned':
                    trade.status = 'Assigned'
                elif trade.close_method == 'called_away':
                    trade.status = 'Called Away'
                elif trade.close_method in ['buy_to_close', 'sell_to_close', 'exercise']:
                    trade.status = 'Closed'
                elif not trade.status or trade.status == 'Open':
                    # Default to Closed if status not set
                    trade.status = 'Closed'
            
            # Handle two-entry closes (old format: has parent_trade_id)
            elif trade.parent_trade_id and trade.trade_action in ['Bought to Close', 'Sold to Close']:
                parent = Trade.query.get(trade.parent_trade_id)
                if parent:
                    if not trade.open_date:
                        trade.open_date = parent.trade_date
                    # Ensure close_date is set if not provided
                    if not trade.close_date:
                        trade.close_date = trade.trade_date
                    # Set closing trade status to Closed
                    trade.status = 'Closed'
                    # Update parent trade status if it's fully closed
                    remaining_qty = parent.get_remaining_open_quantity()
                    if remaining_qty == 0:
                        # Parent is fully closed, update its status
                        if parent.status == 'Open':
                            parent.status = 'Closed'
                        if not parent.close_date:
                            parent.close_date = trade.trade_date
                        if not parent.open_date:
                            parent.open_date = parent.trade_date
            
            # For Assignment trades, ensure status is 'Assigned'
            if trade.trade_type == 'Assignment':
                trade.status = 'Assigned'
                # Set parent's close_date if parent is a CSP
                if trade.parent_trade_id:
                    parent = Trade.query.get(trade.parent_trade_id)
                    if parent and parent.trade_type == 'CSP':
                        parent.status = 'Assigned'
                        parent.close_date = trade.trade_date
                        if not parent.open_date:
                            parent.open_date = parent.trade_date
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'message': f'Successfully imported {len(trades)} trades',
            'count': len(trades)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/export-template', methods=['GET'])
@jwt_required()
def export_template():
    """Export a template CSV/Excel file with example data showing required format"""
    format_type = request.args.get('format', 'csv').lower()
    
    # Create comprehensive template data showing various trade scenarios
    # Note: account_id should be set to your actual account ID when importing
    template_data = {
        'account_id': [1, 1, 1, 1, 1, 1, 1, 1, 1],  # Replace with your account ID
        'symbol': [
            'AAPL',           # 1. Open CSP
            'AAPL',           # 2. Closed CSP (Bought to Close)
            'GOOGL',          # 3. CSP that got Assigned
            'GOOGL',          # 4. Assignment trade (stock position)
            'GOOGL',          # 5. Covered Call opened after assignment
            'GOOGL',          # 6. Covered Call closed (Bought to Close)
            'MSFT',           # 7. LEAPS opened (Bought to Open)
            'MSFT',           # 8. LEAPS closed (Sold to Close)
            'TSLA'            # 9. Open CSP (another example)
        ],
        'trade_type': [
            'CSP',           # Cash-Secured Put
            'CSP',           # Cash-Secured Put (closing)
            'CSP',           # Cash-Secured Put (assigned)
            'Assignment',    # Assignment (stock position created)
            'Covered Call',  # Covered Call
            'Covered Call',  # Covered Call (closing)
            'LEAPS',         # Long-term Equity Anticipation Securities
            'LEAPS',         # LEAPS (closing)
            'CSP'            # Another CSP example
        ],
        'position_type': [
            'Open',          # Opening position
            'Close',         # Closing position
            'Open',          # Opening position (before assignment)
            'Assignment',    # Assignment position
            'Open',          # Opening position
            'Close',         # Closing position
            'Open',          # Opening position
            'Close',         # Closing position
            'Open'           # Opening position
        ],
        'strike_price': [
            150.00,          # CSP strike
            150.00,          # Same strike (closing)
            160.00,          # CSP strike
            160.00,          # Assignment price (same as strike)
            170.00,          # Covered call strike
            170.00,          # Same strike (closing)
            400.00,          # LEAPS strike
            400.00,          # Same strike (closing)
            200.00           # Another CSP strike
        ],
        'expiration_date': [
            '2025-12-26',    # CSP expiration
            '2025-12-26',    # Same expiration (closing)
            '2025-11-22',    # CSP expiration (assigned)
            None,            # Assignment has no expiration
            '2025-12-20',    # Covered call expiration
            '2025-12-20',    # Same expiration (closing)
            '2026-01-16',    # LEAPS expiration
            '2026-01-16',    # Same expiration (closing)
            '2025-12-19'     # Another CSP expiration
        ],
        'contract_quantity': [
            2,               # 2 contracts
            2,               # Closing all 2 contracts
            1,               # 1 contract
            1,               # 1 contract (100 shares)
            1,               # 1 covered call contract
            1,               # Closing 1 contract
            5,               # 5 LEAPS contracts
            5,               # Closing all 5 contracts
            3                # 3 contracts
        ],
        'trade_price': [
            5.00,            # $5.00 per contract (CSP)
            2.50,            # $2.50 per contract (buying to close)
            3.00,            # $3.00 per contract (CSP)
            None,            # Assignment has no trade_price
            3.50,            # $3.50 per contract (covered call)
            1.00,            # $1.00 per contract (buying to close)
            80.00,           # $80.00 per contract (LEAPS)
            95.00,           # $95.00 per contract (selling to close)
            4.50             # $4.50 per contract (CSP)
        ],
        'trade_action': [
            'Sold to Open',  # Opening CSP
            'Bought to Close', # Closing CSP
            'Sold to Open',  # Opening CSP
            None,            # Assignment has no trade_action
            'Sold to Open',  # Opening covered call
            'Bought to Close', # Closing covered call
            'Bought to Open', # Opening LEAPS
            'Sold to Close',  # Closing LEAPS
            'Sold to Open'   # Opening CSP
        ],
        'premium': [
            998.68,          # Calculated: (5.00 * 2 * 100) - (1.32 * 2)
            -502.50,         # Calculated: -(2.50 * 2 * 100 + 0.50 * 2)
            298.50,          # Calculated: (3.00 * 1 * 100) - 1.50
            0.00,            # Assignment has no premium
            348.50,          # Calculated: (3.50 * 1 * 100) - 1.50
            -101.00,         # Calculated: -(1.00 * 1 * 100 + 1.00)
            -40005.00,       # Calculated: -(80.00 * 5 * 100 + 5.00)
            47495.00,        # Calculated: (95.00 * 5 * 100) - 5.00
            1348.50          # Calculated: (4.50 * 3 * 100) - 1.50
        ],
        'fees': [
            1.32,            # $1.32 total fees
            0.50,            # $0.50 total fees
            1.50,            # $1.50 total fees
            0.00,            # Assignment has no fees
            1.50,            # $1.50 total fees
            1.00,            # $1.00 total fees
            5.00,            # $5.00 total fees
            5.00,            # $5.00 total fees
            1.50             # $1.50 total fees
        ],
        'trade_date': [
            '2025-11-20',    # CSP opened
            '2025-12-10',    # CSP closed early
            '2025-10-15',    # CSP opened
            '2025-11-22',    # CSP assigned on expiration
            '2025-11-25',    # Covered call opened after assignment
            '2025-12-15',    # Covered call closed early
            '2025-10-01',    # LEAPS opened
            '2025-12-20',    # LEAPS closed
            '2025-12-01'     # CSP opened
        ],
        'open_date': [
            None,            # Open trade - open_date will be set to trade_date automatically
            '2025-11-20',    # Closing trade - open_date from parent CSP trade_date
            None,            # Open CSP - open_date will be set to trade_date automatically
            None,            # Assignment - open_date not needed
            None,            # Open covered call - open_date will be set to trade_date automatically
            '2025-11-25',    # Closing trade - open_date from parent covered call trade_date
            None,            # Open LEAPS - open_date will be set to trade_date automatically
            '2025-10-01',    # Closing trade - open_date from parent LEAPS trade_date
            None             # Open CSP - open_date will be set to trade_date automatically
        ],
        'close_date': [
            None,            # Still open
            '2025-12-10',    # Closed on this date
            None,            # Assigned (no close_date, status is Assigned)
            None,            # Assignment creates position (no close_date)
            None,            # Still open
            '2025-12-15',    # Closed on this date
            None,            # Still open
            '2025-12-20',    # Closed on this date
            None             # Still open
        ],
        'status': [
            'Open',          # Open position
            'Closed',        # Closed position
            'Assigned',      # Assigned (stock position created)
            'Assigned',      # Assignment trade status
            'Open',          # Open position
            'Closed',        # Closed position
            'Open',          # Open position
            'Closed',        # Closed position
            'Open'           # Open position
        ],
        'parent_trade_id': [
            None,            # Opening trade (no parent)
            1,               # Closing trade (parent is row 1, but use actual ID in real import)
            None,            # Opening trade (no parent)
            3,               # Assignment (parent is row 3, but use actual ID in real import)
            4,               # Covered call (parent is row 4, but use actual ID in real import)
            5,               # Closing trade (parent is row 5, but use actual ID in real import)
            None,            # Opening trade (no parent)
            7,               # Closing trade (parent is row 7, but use actual ID in real import)
            None             # Opening trade (no parent)
        ],
        'assignment_price': [
            None,            # Not an assignment
            None,            # Not an assignment
            None,            # Not an assignment (but status is Assigned)
            160.00,          # Price at which stock was assigned
            None,            # Not an assignment
            None,            # Not an assignment
            None,            # Not an assignment
            None,            # Not an assignment
            None             # Not an assignment
        ],
        'notes': [
            'Opened CSP on AAPL at $150 strike',
            'Closed CSP early for profit',
            'Opened CSP on GOOGL, later assigned',
            'CSP assigned, received 100 shares at $160',
            'Sold covered call on assigned shares',
            'Bought back covered call early',
            'Opened LEAPS call on MSFT',
            'Sold LEAPS for profit',
            'Another CSP example on TSLA'
        ]
    }
    
    df = pd.DataFrame(template_data)
    
    if format_type == 'excel' or format_type == 'xlsx':
        # Create Excel file with instructions sheet
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write instructions sheet
            instructions_data = {
                'Instructions': [
                    'IMPORTANT: Replace account_id with your actual account ID',
                    '',
                    'Trade Types:',
                    '  - CSP: Cash-Secured Put',
                    '  - Covered Call: Call option sold on owned stock',
                    '  - LEAPS: Long-term Equity Anticipation Securities',
                    '  - Assignment: Stock position created from assigned CSP',
                    '',
                    'Position Types:',
                    '  - Open: Opening a new position',
                    '  - Close: Closing an existing position',
                    '  - Assignment: Stock position from assignment',
                    '',
                    'Trade Actions:',
                    '  - Sold to Open: Opening a short position (CSP, Covered Call)',
                    '  - Bought to Open: Opening a long position (LEAPS)',
                    '  - Bought to Close: Closing a short position',
                    '  - Sold to Close: Closing a long position',
                    '',
                    'Parent Trade ID:',
                    '  - Leave empty for opening trades',
                    '  - For closing trades: Enter the ID of the opening trade',
                    '  - For assignments: Enter the ID of the CSP that was assigned',
                    '  - For covered calls: Enter the ID of the assignment trade',
                    '',
                    'Assignment Price:',
                    '  - Only required for Assignment trade type',
                    '  - Enter the price at which stock was assigned (usually the strike price)',
                    '',
                    'Premium Calculation:',
                    '  - Premium is calculated automatically from trade_price, trade_action, and fees',
                    '  - For "Sold" actions: Premium = (trade_price × quantity × 100) - fees',
                    '  - For "Bought" actions: Premium = -((trade_price × quantity × 100) + fees)',
                    '  - You can also enter premium directly if preferred',
                    '',
                    'Example Trade Lifecycle:',
                    '  1. Open CSP: trade_type=CSP, position_type=Open, trade_action=Sold to Open',
                    '  2. Close CSP: trade_type=CSP, position_type=Close, trade_action=Bought to Close, parent_trade_id=1',
                    '  3. CSP Assigned: trade_type=Assignment, position_type=Assignment, assignment_price=strike_price, parent_trade_id=1',
                    '  4. Open Covered Call: trade_type=Covered Call, position_type=Open, trade_action=Sold to Open, parent_trade_id=3',
                    '',
                    'Status:',
                    '  - Open: Position is currently open',
                    '  - Closed: Position has been closed',
                    '  - Assigned: CSP was assigned (stock position created)',
                    '',
                    'Notes:',
                    '  - All dates should be in YYYY-MM-DD format',
                    '  - Strike prices and trade prices are per share/contract',
                    '  - Contract quantity is the number of contracts (1 contract = 100 shares)',
                    '  - Fees are total fees for the trade'
                ]
            }
            instructions_df = pd.DataFrame(instructions_data)
            instructions_df.to_excel(writer, index=False, sheet_name='Instructions')
            
            # Write template data sheet
            df.to_excel(writer, index=False, sheet_name='Trades Template')
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='trades_template.xlsx'
        )
    else:
        # Create CSV file
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='trades_template.csv'
        )

@trades_bp.route('/export', methods=['GET'])
@jwt_required()
def export_trades():
    """Export all user's trades to CSV/Excel file"""
    user_id = get_user_id()
    format_type = request.args.get('format', 'csv').lower()
    account_id = request.args.get('account_id', type=int)
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify({'error': 'No accounts found'}), 404
    
    # Build query
    query = Trade.query.filter(Trade.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    trades = query.order_by(Trade.trade_date.desc()).all()
    
    if not trades:
        return jsonify({'error': 'No trades found to export'}), 404
    
    # Prepare data for export - include ALL fields needed for calculations
    export_data = {
        'account_id': [],
        'symbol': [],
        'trade_type': [],
        'position_type': [],
        'strike_price': [],
        'expiration_date': [],
        'contract_quantity': [],
        'trade_price': [],
        'trade_action': [],
        'premium': [],
        'fees': [],
        'trade_date': [],
        'open_date': [],  # Critical for days_held and return % calculations
        'close_date': [],
        'status': [],
        'parent_trade_id': [],
        'assignment_price': [],
        'close_price': [],  # For single-entry closes
        'close_fees': [],  # For single-entry closes
        'close_premium': [],  # For single-entry closes
        'close_method': [],  # For single-entry closes
        'notes': []
    }
    
    for trade in trades:
        export_data['account_id'].append(trade.account_id)
        export_data['symbol'].append(trade.symbol)
        export_data['trade_type'].append(trade.trade_type)
        export_data['position_type'].append(trade.position_type)
        export_data['strike_price'].append(trade.strike_price if trade.strike_price else None)
        export_data['expiration_date'].append(trade.expiration_date.strftime('%Y-%m-%d') if trade.expiration_date else None)
        export_data['contract_quantity'].append(trade.contract_quantity)
        export_data['trade_price'].append(trade.trade_price if trade.trade_price else None)
        export_data['trade_action'].append(trade.trade_action if trade.trade_action else None)
        export_data['premium'].append(trade.premium)
        export_data['fees'].append(trade.fees)
        export_data['trade_date'].append(trade.trade_date.strftime('%Y-%m-%d') if trade.trade_date else None)
        export_data['open_date'].append(trade.open_date.strftime('%Y-%m-%d') if trade.open_date else None)
        export_data['close_date'].append(trade.close_date.strftime('%Y-%m-%d') if trade.close_date else None)
        export_data['status'].append(trade.status)
        export_data['parent_trade_id'].append(trade.parent_trade_id if trade.parent_trade_id else None)
        export_data['assignment_price'].append(trade.assignment_price if trade.assignment_price else None)
        export_data['close_price'].append(float(trade.close_price) if trade.close_price else None)
        export_data['close_fees'].append(float(trade.close_fees) if trade.close_fees else None)
        export_data['close_premium'].append(float(trade.close_premium) if trade.close_premium else None)
        export_data['close_method'].append(trade.close_method if trade.close_method else None)
        export_data['notes'].append(trade.notes if trade.notes else '')
    
    try:
        df = pd.DataFrame(export_data)
    except Exception as e:
        return jsonify({'error': f'Failed to create export data: {str(e)}'}), 500
    
    if format_type == 'excel' or format_type == 'xlsx':
        # Create Excel file
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Trades')
            output.seek(0)
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=f'trades_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            )
        except Exception as e:
            return jsonify({'error': f'Failed to create Excel file: {str(e)}'}), 500
    else:
        # Create CSV file
        try:
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            csv_bytes = output.getvalue().encode('utf-8')
            return send_file(
                io.BytesIO(csv_bytes),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'trades_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )
        except Exception as e:
            return jsonify({'error': f'Failed to create CSV file: {str(e)}'}), 500

@trades_bp.route('/<int:trade_id>/close', methods=['POST'])
@jwt_required()
def close_trade(trade_id):
    """
    Close a trade with one of several methods based on trade type:
    - CSP: Buy to Close, Expired, Assigned
    - Covered Call: Buy to Close, Expired, Assigned
    - LEAPS: Sell to Close, Expired, Exercise
    
    Request body:
    {
        "close_method": "buy_to_close" | "expired" | "assigned" | "sell_to_close" | "exercise",
        "close_date": "2025-01-15",
        "trade_price": 0.25,  # For buy_to_close/sell_to_close
        "fees": 1.50,         # For buy_to_close/sell_to_close
        "contract_quantity": 5,  # Optional, defaults to remaining
        "assignment_price": 100.00  # For assigned (optional, defaults to strike)
    }
    """
    user_id = get_user_id()
    trade = Trade.query.get(trade_id)
    
    if not trade:
        return jsonify({'error': 'Trade not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=trade.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Verify trade is open
    if trade.status not in ['Open', 'Assigned']:
        return jsonify({'error': f'Cannot close this trade. It is already {trade.status.lower()}. Only open or assigned trades can be closed.'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request data is required'}), 400
    
    close_method = data.get('close_method')
    
    if not close_method:
        return jsonify({'error': 'Please select a close method'}), 400
    
    try:
        # Determine available close methods based on trade type
        if trade.trade_type == 'LEAPS':
            if close_method not in ['sell_to_close', 'expired', 'exercise']:
                return jsonify({'error': f'Invalid close method for LEAPS trades. Please select: Sell to Close, Expired, or Exercise'}), 400
        elif trade.trade_type == 'CSP':
            if close_method not in ['buy_to_close', 'expired', 'assigned']:
                return jsonify({'error': f'Invalid close method for CSP trades. Please select: Buy to Close, Expired, or Assigned'}), 400
        elif trade.trade_type == 'Covered Call':
            if close_method not in ['buy_to_close', 'expired', 'called_away']:
                return jsonify({'error': f'Invalid close method for Covered Call trades. Please select: Buy to Close, Expired, or Called Away'}), 400
        else:
            return jsonify({'error': f'Close workflow is not supported for {trade.trade_type} trades'}), 400
        
        # Handle each close method
        if close_method == 'buy_to_close':
            return handle_buy_to_close(trade, data)
        elif close_method == 'sell_to_close':
            return handle_sell_to_close(trade, data)
        elif close_method == 'expired':
            return handle_expired(trade, data)
        elif close_method == 'assigned':
            return handle_assigned(trade, data)
        elif close_method == 'called_away':
            return handle_called_away(trade, data)
        elif close_method == 'exercise':
            return handle_exercise(trade, data)
        else:
            return jsonify({'error': 'Invalid close_method'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def handle_buy_to_close(trade, data):
    """Handle Buy to Close for CSP or Covered Call"""
    if trade.trade_action not in ['Sold to Open']:
        return jsonify({'error': 'Buy to Close is only for trades opened with "Sold to Open"'}), 400
    
    # Get remaining quantity
    remaining_qty = trade.get_remaining_open_quantity()
    if remaining_qty <= 0:
        return jsonify({'error': 'No contracts remaining to close'}), 400
    
    # Use provided quantity or default to remaining
    contract_quantity = data.get('contract_quantity', remaining_qty)
    if contract_quantity > remaining_qty:
        return jsonify({'error': f'Cannot close {contract_quantity} contracts. Only {remaining_qty} contracts remaining open.'}), 400
    
    # Validate required fields
    if not data.get('trade_price'):
        return jsonify({'error': 'Trade price is required for Buy to Close'}), 400
    
    try:
        trade_price = float(data['trade_price'])
        if trade_price <= 0:
            return jsonify({'error': 'Trade price must be greater than 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Trade price must be a valid number'}), 400
    
    close_date = datetime.strptime(data.get('close_date', data.get('trade_date', datetime.now().date().isoformat())), '%Y-%m-%d').date()
    trade_price = float(data['trade_price'])
    fees = float(data.get('fees', 0))
    
    # Calculate premium (negative for buying)
    premium = calculate_premium(trade_price, 'Bought to Close', contract_quantity, fees)
    
    # Check if this is a full close or partial close
    total_closed = remaining_qty - contract_quantity
    is_full_close = total_closed <= 0
    
    if is_full_close:
        # FULL CLOSE: Update original trade directly (single-entry approach)
        trade.status = 'Closed'
        trade.close_date = close_date
        trade.close_price = trade_price
        trade.close_fees = fees
        trade.close_premium = premium
        trade.close_method = 'buy_to_close'
        if data.get('notes'):
            trade.notes = (trade.notes or '') + f'\n{data["notes"]}'
        
        if not trade.open_date:
            trade.open_date = trade.trade_date
        
        db.session.commit()
        return jsonify(trade.to_dict(include_realized_pnl=True)), 200
    else:
        # PARTIAL CLOSE: Create closing trade (two-entry approach for partial closes)
        closing_trade = Trade(
            account_id=trade.account_id,
            symbol=trade.symbol,
            trade_type=trade.trade_type,
            position_type='Close',
            strike_price=trade.strike_price,
            expiration_date=trade.expiration_date,
            contract_quantity=contract_quantity,
            trade_price=trade_price,
            trade_action='Bought to Close',
            premium=premium,
            fees=fees,
            trade_date=close_date,
            open_date=trade.trade_date,
            close_date=close_date,
            status='Closed',
            parent_trade_id=trade.id,
            notes=data.get('notes')
        )
        
        db.session.add(closing_trade)
        
        # Update parent trade status (keep open for partial close)
        trade.status = 'Open'
        trade.close_date = None
        
        if not trade.open_date:
            trade.open_date = trade.trade_date
        
        db.session.commit()
        return jsonify(closing_trade.to_dict(include_realized_pnl=True)), 201

def handle_sell_to_close(trade, data):
    """Handle Sell to Close for LEAPS"""
    if trade.trade_action not in ['Bought to Open']:
        return jsonify({'error': 'Sell to Close is only for trades opened with "Bought to Open"'}), 400
    
    # Get remaining quantity
    remaining_qty = trade.get_remaining_open_quantity()
    if remaining_qty <= 0:
        return jsonify({'error': 'No contracts remaining to close'}), 400
    
    # Use provided quantity or default to remaining
    contract_quantity = data.get('contract_quantity', remaining_qty)
    if contract_quantity > remaining_qty:
        return jsonify({'error': f'Cannot close {contract_quantity} contracts. Only {remaining_qty} contracts remaining open.'}), 400
    
    # Validate required fields
    if not data.get('trade_price'):
        return jsonify({'error': 'trade_price is required for Sell to Close'}), 400
    
    close_date = datetime.strptime(data.get('close_date', data.get('trade_date', datetime.now().date().isoformat())), '%Y-%m-%d').date()
    trade_price = float(data['trade_price'])
    fees = float(data.get('fees', 0))
    
    # Calculate premium (positive for selling)
    premium = calculate_premium(trade_price, 'Sold to Close', contract_quantity, fees)
    
    # Check if this is a full close or partial close
    total_closed = remaining_qty - contract_quantity
    is_full_close = total_closed <= 0
    
    if is_full_close:
        # FULL CLOSE: Update original trade directly (single-entry approach)
        trade.status = 'Closed'
        trade.close_date = close_date
        trade.close_price = trade_price
        trade.close_fees = fees
        trade.close_premium = premium
        trade.close_method = 'sell_to_close'
        if data.get('notes'):
            trade.notes = (trade.notes or '') + f'\n{data["notes"]}'
        
        if not trade.open_date:
            trade.open_date = trade.trade_date
        
        db.session.commit()
        return jsonify(trade.to_dict(include_realized_pnl=True)), 200
    else:
        # PARTIAL CLOSE: Create closing trade (two-entry approach for partial closes)
        closing_trade = Trade(
            account_id=trade.account_id,
            symbol=trade.symbol,
            trade_type=trade.trade_type,
            position_type='Close',
            strike_price=trade.strike_price,
            expiration_date=trade.expiration_date,
            contract_quantity=contract_quantity,
            trade_price=trade_price,
            trade_action='Sold to Close',
            premium=premium,
            fees=fees,
            trade_date=close_date,
            open_date=trade.trade_date,
            close_date=close_date,
            status='Closed',
            parent_trade_id=trade.id,
            notes=data.get('notes')
        )
        
        db.session.add(closing_trade)
        
        # Update parent trade status (keep open for partial close)
        trade.status = 'Open'
        trade.close_date = None
        
        if not trade.open_date:
            trade.open_date = trade.trade_date
        
        db.session.commit()
        return jsonify(closing_trade.to_dict(include_realized_pnl=True)), 201

def handle_expired(trade, data):
    """Handle Expired (worthless) - supports partial and full closes"""
    # Get remaining quantity
    remaining_qty = trade.get_remaining_open_quantity()
    if remaining_qty <= 0:
        return jsonify({'error': 'No contracts remaining to expire'}), 400
    
    # Use provided quantity or default to remaining
    contract_quantity = data.get('contract_quantity', remaining_qty)
    if contract_quantity > remaining_qty:
        return jsonify({'error': f'Cannot expire {contract_quantity} contracts. Only {remaining_qty} contracts remaining open.'}), 400
    
    close_date = datetime.strptime(
        data.get('close_date', trade.expiration_date.isoformat() if trade.expiration_date else datetime.now().date().isoformat()),
        '%Y-%m-%d'
    ).date()
    
    # Check if this is a full close or partial close
    total_closed = remaining_qty - contract_quantity
    is_full_close = total_closed <= 0
    
    if is_full_close:
        # FULL CLOSE: Update original trade directly (single-entry approach)
        trade.status = 'Expired'
        trade.close_date = close_date
        trade.close_price = None  # No price for expired
        trade.close_fees = 0
        trade.close_premium = 0  # Expired worthless, no closing premium
        trade.close_method = 'expired'
        
        if not trade.open_date:
            trade.open_date = trade.trade_date
        
        if data.get('notes'):
            trade.notes = (trade.notes or '') + f'\n{data["notes"]}'
        
        db.session.commit()
        return jsonify(trade.to_dict(include_realized_pnl=True)), 200
    else:
        # PARTIAL CLOSE: Create closing trade entry (two-entry approach for partial closes)
        # For expired trades, we create a closing trade with the same trade_action as the parent
        # but with status='Expired' to track the partial expiration
        closing_trade = Trade(
            account_id=trade.account_id,
            symbol=trade.symbol,
            trade_type=trade.trade_type,
            position_type='Close',
            strike_price=trade.strike_price,
            expiration_date=trade.expiration_date,
            contract_quantity=contract_quantity,
            trade_price=None,  # No price for expired
            trade_action=trade.trade_action,  # Keep same action as parent (e.g., 'Sold to Open')
            premium=0,  # Expired worthless, no closing premium
            fees=0,
            trade_date=close_date,
            open_date=trade.trade_date,
            close_date=close_date,
            status='Expired',
            parent_trade_id=trade.id,
            close_method='expired',
            notes=data.get('notes')
        )
        
        db.session.add(closing_trade)
        
        # Update parent trade status (keep open for partial close)
        trade.status = 'Open'
        trade.close_date = None
        
        if not trade.open_date:
            trade.open_date = trade.trade_date
        
        db.session.commit()
        return jsonify(closing_trade.to_dict(include_realized_pnl=True)), 201

def handle_assigned(trade, data):
    """Handle Assigned - for CSP creates stock position, for Covered Call returns shares to stock position"""
    if trade.trade_type not in ['CSP', 'Covered Call']:
        return jsonify({'error': 'Assigned method is only for CSP or Covered Call trades'}), 400
    
    # Get remaining quantity
    remaining_qty = trade.get_remaining_open_quantity()
    if remaining_qty <= 0:
        return jsonify({'error': 'No contracts remaining to assign'}), 400
    
    # Use provided quantity or default to remaining
    contract_quantity = data.get('contract_quantity', remaining_qty)
    if contract_quantity > remaining_qty:
        return jsonify({'error': f'Cannot assign {contract_quantity} contracts. Only {remaining_qty} contracts remaining open.'}), 400
    
    assignment_date = datetime.strptime(
        data.get('close_date', trade.expiration_date.isoformat() if trade.expiration_date else datetime.now().date().isoformat()),
        '%Y-%m-%d'
    ).date()
    
    assignment_price = float(data.get('assignment_price', trade.strike_price)) if data.get('assignment_price') or trade.strike_price else None
    if not assignment_price:
        return jsonify({'error': 'assignment_price is required'}), 400
    
    # Handle CSP assignment (creates stock position)
    if trade.trade_type == 'CSP':
        # Create assignment trade
        assignment_trade = Trade(
            account_id=trade.account_id,
            symbol=trade.symbol,
            trade_type='Assignment',
            position_type='Assignment',
            strike_price=trade.strike_price,
            expiration_date=trade.expiration_date,
            contract_quantity=contract_quantity,
            assignment_price=assignment_price,
            trade_date=assignment_date,
            open_date=trade.trade_date,
            status='Assigned',
            parent_trade_id=trade.id,
            notes=data.get('notes')
        )
        
        db.session.add(assignment_trade)
        
        # Update parent CSP
        total_assigned = remaining_qty - contract_quantity
        is_full_assignment = total_assigned <= 0
        
        if is_full_assignment:
            # FULL ASSIGNMENT: Update original CSP directly (single-entry approach)
            trade.status = 'Assigned'
            trade.close_date = assignment_date
            trade.assignment_price = assignment_price
            trade.close_method = 'assigned'
            if data.get('notes'):
                trade.notes = (trade.notes or '') + f'\n{data["notes"]}'
        else:
            # PARTIAL ASSIGNMENT: Keep parent open, create assignment trade
            trade.status = 'Open'
            trade.close_date = None
            trade.assignment_price = assignment_price
        
        if not trade.open_date:
            trade.open_date = trade.trade_date
        
        # Auto-create stock position from assignment
        shares = contract_quantity * 100
        if shares > 0 and assignment_price > 0:
            stock_position = StockPosition(
                account_id=trade.account_id,
                symbol=trade.symbol,
                shares=shares,
                cost_basis_per_share=assignment_price,
                acquired_date=assignment_date,
                status='Open',
                source_trade_id=assignment_trade.id,
                notes=f'Assigned from CSP trade #{trade.id}'
            )
            db.session.add(stock_position)
        
        db.session.commit()
        return jsonify(assignment_trade.to_dict(include_realized_pnl=True)), 201

def handle_called_away(trade, data):
    """Handle Called Away - for Covered Call, shares are called away (sold)"""
    if trade.trade_type != 'Covered Call':
        return jsonify({'error': 'Called Away method is only for Covered Call trades'}), 400
    
    # Get remaining quantity
    remaining_qty = trade.get_remaining_open_quantity()
    if remaining_qty <= 0:
        return jsonify({'error': 'No contracts remaining to call away'}), 400
    
    # Use provided quantity or default to remaining
    contract_quantity = data.get('contract_quantity', remaining_qty)
    if contract_quantity > remaining_qty:
        return jsonify({'error': f'Cannot call away {contract_quantity} contracts. Only {remaining_qty} contracts remaining open.'}), 400
    
    assignment_date = datetime.strptime(
        data.get('close_date', trade.expiration_date.isoformat() if trade.expiration_date else datetime.now().date().isoformat()),
        '%Y-%m-%d'
    ).date()
    
    assignment_price = float(data.get('assignment_price', trade.strike_price)) if data.get('assignment_price') or trade.strike_price else None
    if not assignment_price:
        return jsonify({'error': 'assignment_price is required'}), 400
    
    # Verify the covered call has a stock position
    if not trade.stock_position_id:
        return jsonify({'error': 'Covered Call trade must be linked to a stock position'}), 400
    
    stock_position = StockPosition.query.get(trade.stock_position_id)
    if not stock_position:
        return jsonify({'error': 'Stock position not found'}), 404
    
    # Calculate shares being called away
    shares_called_away = contract_quantity * 100
    
    # Verify enough shares are available in the stock position
    if shares_called_away > stock_position.shares:
        return jsonify({'error': f'Insufficient shares in stock position. Need {shares_called_away} shares, but only {stock_position.shares} available.'}), 400
    
    # Update parent Covered Call
    total_called_away = remaining_qty - contract_quantity
    is_full_call_away = total_called_away <= 0
    
    if is_full_call_away:
        # FULL CALL AWAY: Update original Covered Call directly (single-entry approach)
        trade.status = 'Called Away'
        trade.close_date = assignment_date
        trade.assignment_price = assignment_price
        trade.close_method = 'called_away'
        trade.close_price = None  # No closing price for called away
        trade.close_fees = 0
        trade.close_premium = 0  # Called away has no closing premium (shares are called away at strike)
        if data.get('notes'):
            trade.notes = (trade.notes or '') + f'\n{data["notes"]}'
    else:
        # PARTIAL CALL AWAY: Keep parent open (this creates a new closing trade entry)
        # For partial call aways, we'll keep the parent open and create a closing trade
        trade.status = 'Open'
        trade.close_date = None
        trade.assignment_price = assignment_price
    
    if not trade.open_date:
        trade.open_date = trade.trade_date
    
    # Reduce stock position shares - shares are called away (sold)
    stock_position.shares -= shares_called_away
    
    # If all shares are called away, mark the position as closed/called away
    if stock_position.shares <= 0:
        stock_position.shares = 0  # Ensure it doesn't go negative
        stock_position.status = 'Called Away'
    
    # If this is a partial call away, create a closing trade entry
    if not is_full_call_away:
        closing_trade = Trade(
            account_id=trade.account_id,
            symbol=trade.symbol,
            trade_type='Covered Call',
            position_type='Close',
            strike_price=trade.strike_price,
            expiration_date=trade.expiration_date,
            contract_quantity=contract_quantity,
            trade_price=None,
            trade_action=trade.trade_action,
            premium=0,  # Called away has no closing premium
            fees=0,
            trade_date=assignment_date,
            open_date=trade.trade_date,
            close_date=assignment_date,
            status='Called Away',
            parent_trade_id=trade.id,
            stock_position_id=trade.stock_position_id,
            shares_used=contract_quantity * 100,  # Shares used by this partial call away
            assignment_price=assignment_price,
            close_method='called_away',
            notes=data.get('notes')
        )
        db.session.add(closing_trade)
        db.session.commit()
        return jsonify(closing_trade.to_dict(include_realized_pnl=True)), 201
    else:
        # Full call away - trade is updated directly
        db.session.commit()
        return jsonify(trade.to_dict(include_realized_pnl=True)), 200

def handle_exercise(trade, data):
    """Handle Exercise for LEAPS - creates stock position"""
    if trade.trade_type != 'LEAPS':
        return jsonify({'error': 'Exercise method is only for LEAPS trades'}), 400
    
    if trade.trade_action != 'Bought to Open':
        return jsonify({'error': 'Exercise is only for LEAPS opened with "Bought to Open"'}), 400
    
    # Get remaining quantity
    remaining_qty = trade.get_remaining_open_quantity()
    if remaining_qty <= 0:
        return jsonify({'error': 'No contracts remaining to exercise'}), 400
    
    # Use provided quantity or default to remaining
    contract_quantity = data.get('contract_quantity', remaining_qty)
    if contract_quantity > remaining_qty:
        return jsonify({'error': f'Cannot exercise {contract_quantity} contracts. Only {remaining_qty} contracts remaining open.'}), 400
    
    exercise_date = datetime.strptime(
        data.get('close_date', trade.expiration_date.isoformat() if trade.expiration_date else datetime.now().date().isoformat()),
        '%Y-%m-%d'
    ).date()
    
    # Exercise price is the strike price
    exercise_price = float(trade.strike_price) if trade.strike_price else None
    if not exercise_price:
        return jsonify({'error': 'Strike price is required for exercise'}), 400
    
    # Update LEAPS trade to closed (exercised)
    total_exercised = remaining_qty - contract_quantity
    is_full_exercise = total_exercised <= 0
    
    if is_full_exercise:
        # FULL EXERCISE: Update original LEAPS directly (single-entry approach)
        trade.status = 'Closed'
        trade.close_date = exercise_date
        trade.close_price = exercise_price  # Strike price is the exercise price
        trade.close_fees = 0
        trade.close_premium = 0  # No premium for exercise
        trade.close_method = 'exercise'
        if data.get('notes'):
            trade.notes = (trade.notes or '') + f'\n{data["notes"]}'
    else:
        # PARTIAL EXERCISE: Keep remaining open
        trade.status = 'Open'
        trade.close_date = None
    
    if not trade.open_date:
        trade.open_date = trade.trade_date
    
    # Auto-create stock position from exercise
    shares = contract_quantity * 100
    if shares > 0 and exercise_price > 0:
        # Cost basis = strike price (exercise price)
        # Note: The premium paid for LEAPS is a loss when exercised
        stock_position = StockPosition(
            account_id=trade.account_id,
            symbol=trade.symbol,
            shares=shares,
            cost_basis_per_share=exercise_price,
            acquired_date=exercise_date,
            status='Open',
            source_trade_id=trade.id,
            notes=f'Exercised from LEAPS trade #{trade.id}'
        )
        db.session.add(stock_position)
    
    if data.get('notes'):
        trade.notes = (trade.notes or '') + f'\n{data["notes"]}'
    
    db.session.commit()
    return jsonify(trade.to_dict(include_realized_pnl=True)), 200

