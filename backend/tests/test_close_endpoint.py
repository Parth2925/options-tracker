"""
Integration tests for the close endpoint

Tests the actual API endpoint /trades/<id>/close
"""
import pytest
from datetime import date
from models import db, Trade, Account, User
from flask import Flask

class TestCloseEndpoint:
    """Test the close endpoint functionality"""
    
    def test_close_endpoint_full_close_csp(self, test_app, test_account):
        """Test closing a CSP via the endpoint (full close)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening CSP
            csp = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=2.00,
                trade_action='Sold to Open',
                premium=200.00,
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(csp)
            db.session.commit()
            csp_id = csp.id
            
            # Simulate close endpoint call
            from routes.trades import handle_buy_to_close
            from flask import jsonify
            
            data = {
                'close_method': 'buy_to_close',
                'close_date': '2025-01-15',
                'trade_price': '0.50',
                'fees': '1.50',
                'contract_quantity': 1
            }
            
            # Call the handler directly
            result = handle_buy_to_close(csp, data)
            response_data = result[0].get_json()
            
            # Verify response
            assert result[1] == 200  # Status code
            assert response_data['status'] == 'Closed'
            assert response_data['close_method'] == 'buy_to_close'
            assert response_data['close_price'] == 0.50
            
            # Verify no closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=csp_id).all()
            assert len(closing_trades) == 0
    
    def test_close_endpoint_partial_close_csp(self, test_app, test_account):
        """Test partial close via endpoint creates closing trade"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening CSP with 3 contracts
            csp = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=3,
                trade_price=2.00,
                trade_action='Sold to Open',
                premium=600.00,
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(csp)
            db.session.commit()
            csp_id = csp.id
            
            # Simulate partial close
            from routes.trades import handle_buy_to_close
            
            data = {
                'close_method': 'buy_to_close',
                'close_date': '2025-01-15',
                'trade_price': '0.50',
                'fees': '1.50',
                'contract_quantity': 1  # Partial close
            }
            
            result = handle_buy_to_close(csp, data)
            response_data = result[0].get_json()
            
            # Verify response
            assert result[1] == 201  # Created (closing trade)
            assert response_data['status'] == 'Closed'
            assert response_data['parent_trade_id'] == csp_id
            
            # Verify closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=csp_id).all()
            assert len(closing_trades) == 1
            
            # Verify parent is still open
            updated_csp = Trade.query.get(csp_id)
            assert updated_csp.status == 'Open'
    
    def test_close_endpoint_expired(self, test_app, test_account):
        """Test expired via endpoint updates original trade"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening CSP
            csp = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2025, 1, 15),
                contract_quantity=1,
                trade_price=2.00,
                trade_action='Sold to Open',
                premium=200.00,
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(csp)
            db.session.commit()
            csp_id = csp.id
            
            # Simulate expired
            from routes.trades import handle_expired
            
            data = {
                'close_method': 'expired',
                'close_date': '2025-01-15'
            }
            
            result = handle_expired(csp, data)
            response_data = result[0].get_json()
            
            # Verify response
            assert result[1] == 200
            assert response_data['status'] == 'Expired'
            assert response_data['close_method'] == 'expired'
            # close_premium can be None or 0, both are valid
            assert response_data.get('close_premium') in [0, None]
            
            # Verify no closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=csp_id).all()
            assert len(closing_trades) == 0
