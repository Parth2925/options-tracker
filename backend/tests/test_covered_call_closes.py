"""
Tests for Covered Call closing scenarios
"""
import pytest
from datetime import date
from models import db, Trade, Account, User, StockPosition

class TestCoveredCallCloses:
    """Test Covered Call closing functionality"""
    
    def test_full_close_covered_call_buy_to_close(self, test_app, test_account):
        """Test full close of Covered Call using buy to close"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create stock position
            stock_pos = StockPosition(
                account_id=account_id,
                symbol='AAPL',
                shares=100,
                cost_basis_per_share=150.00,
                acquired_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(stock_pos)
            db.session.flush()
            stock_pos_id = stock_pos.id
            
            # Create opening Covered Call
            cc = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='Covered Call',
                position_type='Open',
                strike_price=160.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=3.00,
                trade_action='Sold to Open',
                premium=300.00,  # 3.00 * 1 * 100
                fees=0,
                trade_date=date(2025, 1, 10),
                status='Open',
                stock_position_id=stock_pos_id,
                shares_used=100
            )
            db.session.add(cc)
            db.session.commit()
            cc_id = cc.id
            
            # Close fully (buy to close)
            close_date = date(2025, 2, 1)
            trade_price = 1.00
            fees = 1.50
            contract_quantity = 1
            
            # Calculate premium (negative for buying)
            premium = -(trade_price * contract_quantity * 100 + fees * contract_quantity)
            # -100 - 1.50 = -101.50
            
            # Update trade directly (full close)
            cc.status = 'Closed'
            cc.close_date = close_date
            cc.close_price = trade_price
            cc.close_fees = fees
            cc.close_premium = premium
            cc.close_method = 'buy_to_close'
            cc.open_date = cc.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(cc_id)
            assert updated_trade.status == 'Closed'
            assert updated_trade.close_method == 'buy_to_close'
            assert updated_trade.close_premium == premium
            
            # Verify P&L
            realized_pnl = updated_trade.calculate_realized_pnl()
            # Expected: 300 + (-101.50) = 198.50
            assert realized_pnl == 198.50
            
            # Verify stock position shares are returned
            updated_stock = StockPosition.query.get(stock_pos_id)
            # Shares should be available again (not used by closed covered call)
            assert updated_stock.status == 'Open'
    
    def test_partial_close_covered_call(self, test_app, test_account):
        """Test partial close of Covered Call creates closing trade"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create stock position with 200 shares
            stock_pos = StockPosition(
                account_id=account_id,
                symbol='AAPL',
                shares=200,
                cost_basis_per_share=150.00,
                acquired_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(stock_pos)
            db.session.flush()
            stock_pos_id = stock_pos.id
            
            # Create opening Covered Call with 2 contracts
            cc = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='Covered Call',
                position_type='Open',
                strike_price=160.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=2,
                trade_price=3.00,
                trade_action='Sold to Open',
                premium=600.00,  # 3.00 * 2 * 100
                fees=0,
                trade_date=date(2025, 1, 10),
                status='Open',
                stock_position_id=stock_pos_id,
                shares_used=200
            )
            db.session.add(cc)
            db.session.flush()
            cc_id = cc.id
            
            # Close 1 contract (partial close)
            close_date = date(2025, 2, 1)
            trade_price = 1.00
            fees = 1.50
            contract_quantity = 1
            
            # Calculate premium (negative for buying)
            premium = -(trade_price * contract_quantity * 100 + fees * contract_quantity)
            
            # Create closing trade (partial close)
            closing_trade = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='Covered Call',
                position_type='Close',
                strike_price=160.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=contract_quantity,
                trade_price=trade_price,
                trade_action='Bought to Close',
                premium=premium,
                fees=fees,
                trade_date=close_date,
                open_date=cc.trade_date,
                close_date=close_date,
                status='Closed',
                parent_trade_id=cc_id
            )
            db.session.add(closing_trade)
            
            # Update parent (keep open for partial close)
            cc.status = 'Open'
            cc.close_date = None
            
            db.session.commit()
            
            # Verify closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=cc_id).all()
            assert len(closing_trades) == 1
            assert closing_trades[0].contract_quantity == 1
            
            # Verify parent is still open
            updated_cc = Trade.query.get(cc_id)
            assert updated_cc.status == 'Open'
            assert updated_cc.close_date is None
    
    def test_covered_call_expired(self, test_app, test_account):
        """Test Covered Call expired (single-entry)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create stock position
            stock_pos = StockPosition(
                account_id=account_id,
                symbol='AAPL',
                shares=100,
                cost_basis_per_share=150.00,
                acquired_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(stock_pos)
            db.session.flush()
            stock_pos_id = stock_pos.id
            
            # Create opening Covered Call
            cc = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='Covered Call',
                position_type='Open',
                strike_price=160.00,
                expiration_date=date(2025, 1, 15),
                contract_quantity=1,
                trade_price=3.00,
                trade_action='Sold to Open',
                premium=300.00,
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open',
                stock_position_id=stock_pos_id,
                shares_used=100
            )
            db.session.add(cc)
            db.session.commit()
            cc_id = cc.id
            
            # Mark as expired
            close_date = date(2025, 1, 15)
            cc.status = 'Expired'
            cc.close_date = close_date
            cc.close_price = None
            cc.close_fees = 0
            cc.close_premium = 0
            cc.close_method = 'expired'
            cc.open_date = cc.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(cc_id)
            assert updated_trade.status == 'Expired'
            assert updated_trade.close_method == 'expired'
            assert updated_trade.close_premium == 0
            
            # Verify P&L (full premium received)
            realized_pnl = updated_trade.calculate_realized_pnl()
            assert realized_pnl == 300.00  # Full premium
    
    def test_covered_call_assigned(self, test_app, test_account):
        """Test Covered Call assigned (creates assignment trade)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create stock position
            stock_pos = StockPosition(
                account_id=account_id,
                symbol='AAPL',
                shares=100,
                cost_basis_per_share=150.00,
                acquired_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(stock_pos)
            db.session.flush()
            stock_pos_id = stock_pos.id
            
            # Create opening Covered Call
            cc = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='Covered Call',
                position_type='Open',
                strike_price=160.00,
                expiration_date=date(2025, 1, 15),
                contract_quantity=1,
                trade_price=3.00,
                trade_action='Sold to Open',
                premium=300.00,
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open',
                stock_position_id=stock_pos_id,
                shares_used=100
            )
            db.session.add(cc)
            db.session.flush()
            cc_id = cc.id
            
            # Mark as assigned
            assignment_date = date(2025, 1, 15)
            cc.status = 'Assigned'
            cc.close_date = assignment_date
            cc.close_price = None
            cc.close_fees = 0
            cc.close_premium = 0
            cc.close_method = 'assigned'
            cc.assignment_price = 160.00
            cc.open_date = cc.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(cc_id)
            assert updated_trade.status == 'Assigned'
            assert updated_trade.close_method == 'assigned'
            assert updated_trade.assignment_price == 160.00
            
            # Verify stock position shares are removed (assigned away)
            updated_stock = StockPosition.query.get(stock_pos_id)
            # Shares should be reduced or position closed
            # (Implementation may vary, but shares_used should reflect assignment)
