"""
Tests for P&L calculation edge cases
"""
import pytest
from datetime import date
from models import db, Trade, Account, User

class TestPNLCalculations:
    """Test P&L calculation edge cases"""
    
    def test_pnl_with_fees(self, test_app, test_account):
        """Test P&L calculation includes fees correctly"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP with fees
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
                premium=200.00,  # 2.00 * 1 * 100 - 0 fees
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Closed',
                close_date=date(2025, 1, 15),
                close_price=0.50,
                close_fees=1.50,
                close_premium=-51.50,  # -(0.50 * 1 * 100 + 1.50)
                close_method='buy_to_close',
                open_date=date(2025, 1, 1)
            )
            db.session.add(csp)
            db.session.commit()
            
            # Calculate P&L
            realized_pnl = csp.calculate_realized_pnl()
            
            # Expected: 200 + (-51.50) = 148.50
            assert realized_pnl == 148.50
    
    def test_pnl_expired_worthless(self, test_app, test_account):
        """Test P&L for expired worthless trade (full premium)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP that expires worthless
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
                status='Expired',
                close_date=date(2025, 1, 15),
                close_price=None,
                close_fees=0,
                close_premium=0,
                close_method='expired',
                open_date=date(2025, 1, 1)
            )
            db.session.add(csp)
            db.session.commit()
            
            # Calculate P&L
            realized_pnl = csp.calculate_realized_pnl()
            
            # Expected: 200 + 0 = 200 (full premium)
            assert realized_pnl == 200.00
    
    def test_pnl_assigned_csp(self, test_app, test_account):
        """Test P&L for assigned CSP"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP that gets assigned
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
                status='Assigned',
                close_date=date(2025, 1, 15),
                close_price=None,
                close_fees=0,
                close_premium=0,
                close_method='assigned',
                assignment_price=150.00,
                open_date=date(2025, 1, 1)
            )
            db.session.add(csp)
            db.session.commit()
            
            # Calculate P&L
            realized_pnl = csp.calculate_realized_pnl()
            
            # Expected: 200 + 0 = 200 (full premium, assignment doesn't affect premium)
            assert realized_pnl == 200.00
    
    def test_pnl_partial_close_calculation(self, test_app, test_account):
        """Test P&L calculation for partial close"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening CSP with 2 contracts
            csp = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=2,
                trade_price=2.00,
                trade_action='Sold to Open',
                premium=400.00,  # 2.00 * 2 * 100
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(csp)
            db.session.flush()
            csp_id = csp.id
            
            # Create closing trade (partial close - 1 contract)
            closing_trade = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Close',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=0.50,
                trade_action='Bought to Close',
                premium=-51.50,  # -(0.50 * 1 * 100 + 1.50)
                fees=1.50,
                trade_date=date(2025, 1, 15),
                open_date=date(2025, 1, 1),
                close_date=date(2025, 1, 15),
                status='Closed',
                parent_trade_id=csp_id
            )
            db.session.add(closing_trade)
            db.session.commit()
            
            # Calculate P&L for closing trade
            realized_pnl = closing_trade.calculate_realized_pnl()
            
            # Expected: (400/2) + (-51.50) = 200 - 51.50 = 148.50
            assert realized_pnl == 148.50
    
    def test_pnl_negative_result(self, test_app, test_account):
        """Test P&L calculation for losing trade"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create CSP that closes at a loss
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
                close_price=3.00,  # Higher than opening price (loss)
                close_fees=1.50,
                close_premium=-301.50,  # -(3.00 * 1 * 100 + 1.50)
                close_method='buy_to_close',
                open_date=date(2025, 1, 1)
            )
            db.session.add(csp)
            db.session.commit()
            
            # Calculate P&L
            realized_pnl = csp.calculate_realized_pnl()
            
            # Expected: 200 + (-301.50) = -101.50 (loss)
            assert realized_pnl == -101.50
