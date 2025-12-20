from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Account, Deposit
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
    return jsonify([account.to_dict() for account in accounts]), 200

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
        return jsonify(account.to_dict()), 201
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
    
    return jsonify(account.to_dict()), 200

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
        return jsonify(account.to_dict()), 200
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

