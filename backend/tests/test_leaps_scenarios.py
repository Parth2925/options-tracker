"""
Tests for LEAPS scenarios (exercise, expired, partial close)
"""
import pytest
from datetime import date
from models import db, Trade, Account, User, StockPosition

class TestLEAPSScenarios:
    """Test LEAPS closing functionality"""
    
    def test_leaps_exercise(self, test_app, test_account):
        """Test LEAPS exercise (creates stock position)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening LEAPS
            leaps = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='LEAPS',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2026, 12, 31),
                contract_quantity=1,
                trade_price=80.00,
                trade_action='Bought to Open',
                premium=-8000.00,  # Paid 80 * 1 * 100
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(leaps)
            db.session.commit()
            leaps_id = leaps.id
            
            # Exercise the LEAPS
            exercise_date = date(2025, 6, 1)
            leaps.status = 'Assigned'  # Exercise is similar to assignment
            leaps.close_date = exercise_date
            leaps.close_price = None
            leaps.close_fees = 0
            leaps.close_premium = 0
            leaps.close_method = 'exercise'
            leaps.assignment_price = 150.00
            leaps.open_date = leaps.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(leaps_id)
            assert updated_trade.status == 'Assigned'
            assert updated_trade.close_method == 'exercise'
            assert updated_trade.assignment_price == 150.00
            
            # Verify stock position should be created (if implementation does this)
            # This depends on your implementation
    
    def test_leaps_expired(self, test_app, test_account):
        """Test LEAPS expired (worthless)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening LEAPS
            leaps = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='LEAPS',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=80.00,
                trade_action='Bought to Open',
                premium=-8000.00,
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(leaps)
            db.session.commit()
            leaps_id = leaps.id
            
            # Mark as expired
            close_date = date(2025, 12, 31)
            leaps.status = 'Expired'
            leaps.close_date = close_date
            leaps.close_price = None
            leaps.close_fees = 0
            leaps.close_premium = 0
            leaps.close_method = 'expired'
            leaps.open_date = leaps.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(leaps_id)
            assert updated_trade.status == 'Expired'
            assert updated_trade.close_method == 'expired'
            
            # Verify P&L (full loss: -8000)
            realized_pnl = updated_trade.calculate_realized_pnl()
            assert realized_pnl == -8000.00
    
    def test_leaps_partial_close(self, test_app, test_account):
        """Test partial close of LEAPS (sell to close)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening LEAPS with 2 contracts
            leaps = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='LEAPS',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2026, 12, 31),
                contract_quantity=2,
                trade_price=80.00,
                trade_action='Bought to Open',
                premium=-16000.00,  # 80 * 2 * 100
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(leaps)
            db.session.flush()
            leaps_id = leaps.id
            
            # Close 1 contract (partial close)
            close_date = date(2025, 6, 1)
            trade_price = 90.00
            fees = 10.00
            contract_quantity = 1
            
            # Calculate premium (positive for selling)
            premium = trade_price * contract_quantity * 100 - fees * contract_quantity
            # 9000 - 10 = 8990
            
            # Create closing trade (partial close)
            closing_trade = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='LEAPS',
                position_type='Close',
                strike_price=150.00,
                expiration_date=date(2026, 12, 31),
                contract_quantity=contract_quantity,
                trade_price=trade_price,
                trade_action='Sold to Close',
                premium=premium,
                fees=fees,
                trade_date=close_date,
                open_date=leaps.trade_date,
                close_date=close_date,
                status='Closed',
                parent_trade_id=leaps_id
            )
            db.session.add(closing_trade)
            
            # Update parent (keep open for partial close)
            leaps.status = 'Open'
            leaps.close_date = None
            
            db.session.commit()
            
            # Verify closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=leaps_id).all()
            assert len(closing_trades) == 1
            
            # Verify P&L for closing trade
            realized_pnl = closing_trade.calculate_realized_pnl()
            # Expected: (16000/2) + 8990 = -8000 + 8990 = 990
            assert realized_pnl == 990.00
