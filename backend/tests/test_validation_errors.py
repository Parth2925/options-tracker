"""
Tests for validation errors and edge cases
"""
import pytest
from datetime import date
from models import db, Trade, Account, User, StockPosition
from routes.trades import handle_buy_to_close, handle_sell_to_close, handle_expired, handle_assigned

class TestValidationErrors:
    """Test validation and error handling"""
    
    def test_close_already_closed_trade(self, test_app, test_account):
        """Test that closing an already closed trade fails"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create and close CSP
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
                status='Closed',
                close_date=date(2025, 1, 15),
                close_price=0.50,
                close_fees=1.50,
                close_premium=-51.50,
                close_method='buy_to_close',
                open_date=date(2025, 1, 1)
            )
            db.session.add(csp)
            db.session.commit()
            
            # Try to close again
            data = {
                'close_method': 'buy_to_close',
                'close_date': '2025-01-20',
                'trade_price': '0.30',
                'fees': '1.00',
                'contract_quantity': 1
            }
            
            result = handle_buy_to_close(csp, data)
            response_data = result[0].get_json()
            
            # Should fail
            assert result[1] == 400
            assert 'No contracts remaining' in response_data['error']
    
    def test_close_insufficient_quantity(self, test_app, test_account):
        """Test that closing more than available quantity fails"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP with 1 contract
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
            
            # Try to close 2 contracts
            data = {
                'close_method': 'buy_to_close',
                'close_date': '2025-01-15',
                'trade_price': '0.50',
                'fees': '1.50',
                'contract_quantity': 2  # More than available
            }
            
            result = handle_buy_to_close(csp, data)
            response_data = result[0].get_json()
            
            # Should fail
            assert result[1] == 400
            assert 'Cannot close' in response_data['error']
    
    def test_invalid_close_method_for_trade_action(self, test_app, test_account):
        """Test that invalid close methods are rejected"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP (Sold to Open)
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
            
            # Try to use sell_to_close (invalid for CSP)
            data = {
                'close_method': 'sell_to_close',
                'close_date': '2025-01-15',
                'trade_price': '0.50',
                'fees': '1.50',
                'contract_quantity': 1
            }
            
            result = handle_sell_to_close(csp, data)
            response_data = result[0].get_json()
            
            # Should fail
            assert result[1] == 400
            assert 'Sell to Close is only for trades opened with "Bought to Open"' in response_data['error']
    
    def test_missing_required_fields(self, test_app, test_account):
        """Test that missing required fields cause errors"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP
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
            
            # Try to close without trade_price
            data = {
                'close_method': 'buy_to_close',
                'close_date': '2025-01-15',
                # Missing trade_price
                'fees': '1.50',
                'contract_quantity': 1
            }
            
            result = handle_buy_to_close(csp, data)
            response_data = result[0].get_json()
            
            # Should fail
            assert result[1] == 400
            assert 'trade_price is required' in response_data['error']
    
    def test_multiple_partial_closes(self, test_app, test_account):
        """Test multiple partial closes on same trade"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP with 3 contracts
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
            db.session.flush()
            csp_id = csp.id
            
            # First partial close: 1 contract
            close1 = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Close',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=0.50,
                trade_action='Bought to Close',
                premium=-51.50,
                fees=1.50,
                trade_date=date(2025, 1, 15),
                open_date=date(2025, 1, 1),
                close_date=date(2025, 1, 15),
                status='Closed',
                parent_trade_id=csp_id
            )
            db.session.add(close1)
            db.session.flush()
            
            # Second partial close: 1 contract
            close2 = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Close',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=0.40,
                trade_action='Bought to Close',
                premium=-41.00,
                fees=1.00,
                trade_date=date(2025, 2, 1),
                open_date=date(2025, 1, 1),
                close_date=date(2025, 2, 1),
                status='Closed',
                parent_trade_id=csp_id
            )
            db.session.add(close2)
            db.session.commit()
            
            # Verify both closing trades exist
            closing_trades = Trade.query.filter_by(parent_trade_id=csp_id).all()
            assert len(closing_trades) == 2
            
            # Verify remaining quantity
            remaining = csp.get_remaining_open_quantity()
            assert remaining == 1  # 3 - 1 - 1 = 1
            
            # Verify parent is still open
            updated_csp = Trade.query.get(csp_id)
            assert updated_csp.status == 'Open'
