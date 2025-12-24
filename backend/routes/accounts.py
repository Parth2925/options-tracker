from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Account, Deposit, Withdrawal, Trade
from datetime import datetime

accounts_bp = Blueprint('accounts', __name__)

def get_user_id():
    """Helper to get user ID from JWT token, converting string to int"""
    user_id_str = get_jwt_identity()
    return int(user_id_str) if user_id_str else None

@accounts_bp.route('', methods=['GET'])
@jwt_required()
def get_accounts():
    user_id = get_user_id()
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    # Add total_capital to each account (including realized P&L)
    account_dicts = []
    for account in accounts:
        account_dict = account.to_dict()
        # Calculate total capital (initial balance + deposits + realized P&L)
        total = float(account.initial_balance) if account.initial_balance else 0
        
        # Add deposits
        for deposit in account.deposits:
            total += float(deposit.amount) if deposit.amount else 0
        
        # Subtract withdrawals
        for withdrawal in account.withdrawals:
            total -= float(withdrawal.amount) if withdrawal.amount else 0
        
        # Add realized P&L from closed trades
        realized_pnl = 0
        for trade in account.trades:
            if trade.status in ['Closed', 'Assigned', 'Expired']:
                realized_pnl += trade.calculate_realized_pnl()
        
        total += realized_pnl
        account_dict['total_capital'] = round(total, 2)
        account_dicts.append(account_dict)
    
    return jsonify(account_dicts), 200

@accounts_bp.route('', methods=['POST'])
@jwt_required()
def create_account():
    try:
        user_id = get_user_id()
        if not user_id:
            return jsonify({'error': 'Invalid user identity'}), 401
    except Exception as jwt_error:
        return jsonify({'error': f'Authentication error: {str(jwt_error)}'}), 401
    
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Account name is required'}), 400
    
    # Convert initial_balance to proper type
    initial_balance = data.get('initial_balance', 0)
    if initial_balance is not None:
        try:
            initial_balance = float(initial_balance)
        except (ValueError, TypeError):
            initial_balance = 0
    
    account = Account(
        user_id=user_id,
        name=data['name'],
        account_type=data.get('account_type'),
        initial_balance=initial_balance
    )
    
    try:
        db.session.add(account)
        db.session.commit()
        account_dict = account.to_dict()
        # For new account, total_capital is just initial_balance (no deposits or realized P&L yet)
        account_dict['total_capital'] = round(float(account.initial_balance) if account.initial_balance else 0, 2)
        return jsonify(account_dict), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    account_dict = account.to_dict()
    # Calculate total capital (initial balance + deposits - withdrawals + realized P&L)
    total = float(account.initial_balance) if account.initial_balance else 0
    
    # Add deposits
    for deposit in account.deposits:
        total += float(deposit.amount) if deposit.amount else 0
    
    # Subtract withdrawals
    for withdrawal in account.withdrawals:
        total -= float(withdrawal.amount) if withdrawal.amount else 0
    
    # Add realized P&L from closed trades
    realized_pnl = 0
    for trade in account.trades:
        if trade.status in ['Closed', 'Assigned', 'Expired']:
            realized_pnl += trade.calculate_realized_pnl()
    
    total += realized_pnl
    account_dict['total_capital'] = round(total, 2)
    
    return jsonify(account_dict), 200

@accounts_bp.route('/<int:account_id>', methods=['PUT'])
@jwt_required()
def update_account(account_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    if data.get('name'):
        account.name = data['name']
    if data.get('account_type') is not None:
        account.account_type = data['account_type']
    if data.get('initial_balance') is not None:
        account.initial_balance = data['initial_balance']
    
    try:
        db.session.commit()
        account_dict = account.to_dict()
        # Calculate total capital (initial balance + deposits + realized P&L)
        total = float(account.initial_balance) if account.initial_balance else 0
        
        # Add deposits
        for deposit in account.deposits:
            total += float(deposit.amount) if deposit.amount else 0
        
        # Subtract withdrawals
        for withdrawal in account.withdrawals:
            total -= float(withdrawal.amount) if withdrawal.amount else 0
        
        # Add realized P&L from closed trades
        realized_pnl = 0
        for trade in account.trades:
            if trade.status in ['Closed', 'Assigned', 'Expired']:
                realized_pnl += trade.calculate_realized_pnl()
        
        total += realized_pnl
        account_dict['total_capital'] = round(total, 2)
        return jsonify(account_dict), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    try:
        db.session.delete(account)
        db.session.commit()
        return jsonify({'message': 'Account deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>/deposits', methods=['GET'])
@jwt_required()
def get_deposits(account_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    deposits = Deposit.query.filter_by(account_id=account_id).order_by(Deposit.deposit_date.desc()).all()
    return jsonify([deposit.to_dict() for deposit in deposits]), 200

@accounts_bp.route('/<int:account_id>/deposits', methods=['POST'])
@jwt_required()
def create_deposit(account_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('amount') or not data.get('deposit_date'):
        return jsonify({'error': 'Amount and deposit_date are required'}), 400
    
    # Convert deposit_date string to Python date object
    try:
        deposit_date_str = data['deposit_date']
        if isinstance(deposit_date_str, str):
            deposit_date = datetime.strptime(deposit_date_str, '%Y-%m-%d').date()
        else:
            deposit_date = deposit_date_str
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid date format. Use YYYY-MM-DD: {str(e)}'}), 400
    
    deposit = Deposit(
        account_id=account_id,
        amount=data['amount'],
        deposit_date=deposit_date,
        notes=data.get('notes')
    )
    
    try:
        db.session.add(deposit)
        db.session.commit()
        return jsonify(deposit.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>/withdrawals', methods=['GET'])
@jwt_required()
def get_withdrawals(account_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    withdrawals = Withdrawal.query.filter_by(account_id=account_id).order_by(Withdrawal.withdrawal_date.desc()).all()
    return jsonify([withdrawal.to_dict() for withdrawal in withdrawals]), 200

@accounts_bp.route('/<int:account_id>/withdrawals', methods=['POST'])
@jwt_required()
def create_withdrawal(account_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('amount') or not data.get('withdrawal_date'):
        return jsonify({'error': 'Amount and withdrawal_date are required'}), 400
    
    # Convert withdrawal_date string to Python date object
    try:
        withdrawal_date_str = data['withdrawal_date']
        if isinstance(withdrawal_date_str, str):
            withdrawal_date = datetime.strptime(withdrawal_date_str, '%Y-%m-%d').date()
        else:
            withdrawal_date = withdrawal_date_str
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid date format. Use YYYY-MM-DD: {str(e)}'}), 400
    
    withdrawal = Withdrawal(
        account_id=account_id,
        amount=data['amount'],
        withdrawal_date=withdrawal_date,
        notes=data.get('notes')
    )
    
    try:
        db.session.add(withdrawal)
        db.session.commit()
        return jsonify(withdrawal.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@accounts_bp.route('/<int:account_id>/withdrawals/<int:withdrawal_id>', methods=['DELETE'])
@jwt_required()
def delete_withdrawal(account_id, withdrawal_id):
    user_id = get_user_id()
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    withdrawal = Withdrawal.query.filter_by(id=withdrawal_id, account_id=account_id).first()
    
    if not withdrawal:
        return jsonify({'error': 'Withdrawal not found'}), 404
    
    try:
        db.session.delete(withdrawal)
        db.session.commit()
        return jsonify({'message': 'Withdrawal deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

