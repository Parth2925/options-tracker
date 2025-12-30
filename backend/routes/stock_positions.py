from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, StockPosition, Account, Trade
from datetime import datetime

stock_positions_bp = Blueprint('stock_positions', __name__)

def get_user_id():
    """Helper to get user ID from JWT token"""
    user_id_str = get_jwt_identity()
    return int(user_id_str) if user_id_str else None

@stock_positions_bp.route('', methods=['GET'])
@jwt_required()
def get_stock_positions():
    """Get all stock positions for the authenticated user"""
    user_id = get_user_id()
    account_id = request.args.get('account_id', type=int)
    status = request.args.get('status')  # 'Open', 'Called Away', 'All'
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify([]), 200
    
    query = StockPosition.query.filter(StockPosition.account_id.in_(account_ids))
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    if status and status != 'All':
        query = query.filter_by(status=status)
    
    positions = query.order_by(StockPosition.acquired_date.desc()).all()
    
    return jsonify([pos.to_dict(include_available_shares=True) for pos in positions]), 200

@stock_positions_bp.route('/<int:position_id>', methods=['GET'])
@jwt_required()
def get_stock_position(position_id):
    """Get a specific stock position"""
    user_id = get_user_id()
    position = StockPosition.query.get(position_id)
    
    if not position:
        return jsonify({'error': 'Stock position not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=position.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(position.to_dict(include_available_shares=True)), 200

@stock_positions_bp.route('', methods=['POST'])
@jwt_required()
def create_stock_position():
    """Create a new stock position"""
    user_id = get_user_id()
    data = request.get_json()
    
    if not data or not data.get('account_id') or not data.get('symbol') or not data.get('shares'):
        return jsonify({'error': 'account_id, symbol, and shares are required'}), 400
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=data['account_id'], user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    # Validate required fields
    if not data.get('cost_basis_per_share'):
        return jsonify({'error': 'cost_basis_per_share is required'}), 400
    
    if not data.get('acquired_date'):
        return jsonify({'error': 'acquired_date is required'}), 400
    
    try:
        position = StockPosition(
            account_id=data['account_id'],
            symbol=data['symbol'].upper(),
            shares=int(data['shares']),
            cost_basis_per_share=float(data['cost_basis_per_share']),
            acquired_date=datetime.strptime(data['acquired_date'], '%Y-%m-%d').date(),
            status=data.get('status', 'Open'),
            source_trade_id=data.get('source_trade_id'),
            notes=data.get('notes')
        )
        
        db.session.add(position)
        db.session.commit()
        
        return jsonify(position.to_dict(include_available_shares=True)), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({'error': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@stock_positions_bp.route('/<int:position_id>', methods=['PUT'])
@jwt_required()
def update_stock_position(position_id):
    """Update a stock position"""
    user_id = get_user_id()
    position = StockPosition.query.get(position_id)
    
    if not position:
        return jsonify({'error': 'Stock position not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=position.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if position has active covered calls
    active_covered_calls = [t for t in position.covered_calls if t.status == 'Open']
    if active_covered_calls and 'shares' in request.get_json():
        # Check if reducing shares would conflict with active covered calls
        new_shares = int(request.get_json()['shares'])
        total_used = sum(t.shares_used for t in active_covered_calls)
        if new_shares < total_used:
            return jsonify({
                'error': f'Cannot reduce shares to {new_shares}. {total_used} shares are currently used by active covered calls.'
            }), 400
    
    data = request.get_json()
    
    if data.get('symbol'):
        position.symbol = data['symbol'].upper()
    if data.get('shares') is not None:
        position.shares = int(data['shares'])
    if data.get('cost_basis_per_share') is not None:
        position.cost_basis_per_share = float(data['cost_basis_per_share'])
    if data.get('acquired_date'):
        position.acquired_date = datetime.strptime(data['acquired_date'], '%Y-%m-%d').date()
    if data.get('status'):
        position.status = data['status']
    if data.get('notes') is not None:
        position.notes = data['notes']
    
    try:
        db.session.commit()
        return jsonify(position.to_dict(include_available_shares=True)), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@stock_positions_bp.route('/<int:position_id>', methods=['DELETE'])
@jwt_required()
def delete_stock_position(position_id):
    """Delete a stock position"""
    user_id = get_user_id()
    position = StockPosition.query.get(position_id)
    
    if not position:
        return jsonify({'error': 'Stock position not found'}), 404
    
    # Verify account belongs to user
    account = Account.query.filter_by(id=position.account_id, user_id=user_id).first()
    if not account:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Check if position has active covered calls
    active_covered_calls = [t for t in position.covered_calls if t.status == 'Open']
    if active_covered_calls:
        return jsonify({
            'error': f'Cannot delete position. It has {len(active_covered_calls)} active covered call(s). Close or delete those trades first.'
        }), 400
    
    try:
        db.session.delete(position)
        db.session.commit()
        return jsonify({'message': 'Stock position deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@stock_positions_bp.route('/available', methods=['GET'])
@jwt_required()
def get_available_positions():
    """Get stock positions with available shares for creating covered calls"""
    user_id = get_user_id()
    account_id = request.args.get('account_id', type=int)
    symbol = request.args.get('symbol')  # Optional: filter by symbol
    
    # Get user's account IDs
    accounts = Account.query.filter_by(user_id=user_id).all()
    account_ids = [acc.id for acc in accounts]
    
    if not account_ids:
        return jsonify([]), 200
    
    query = StockPosition.query.filter(
        StockPosition.account_id.in_(account_ids),
        StockPosition.status == 'Open'
    )
    
    if account_id and account_id in account_ids:
        query = query.filter_by(account_id=account_id)
    
    if symbol:
        query = query.filter_by(symbol=symbol.upper())
    
    positions = query.order_by(StockPosition.acquired_date).all()
    
    # Filter to only positions with available shares and include availability info
    available_positions = []
    for pos in positions:
        available_shares = pos.get_available_shares()
        if available_shares > 0:
            pos_dict = pos.to_dict(include_available_shares=True)
            available_positions.append(pos_dict)
    
    return jsonify(available_positions), 200
