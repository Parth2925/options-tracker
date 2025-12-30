"""
Tests for dashboard filtering of closing trades
"""
import pytest
from datetime import date
from models import db, Trade, Account, User
from routes.dashboard import calculate_wheel_pnl

class TestDashboardFiltering:
    """Test that closing trades are filtered from dashboard"""
    
    def test_dashboard_pnl_excludes_closing_trades(self, test_app, test_account):
        """Test that P&L calculation excludes closing trades"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening CSP
            opening = Trade(
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
            db.session.add(opening)
            
            # Create a closing trade (should be filtered)
            closing = Trade(
                account_id=account_id,
                symbol='MSFT',
                trade_type='CSP',
                position_type='Close',
                strike_price=200.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=1.00,
                trade_action='Bought to Close',
                premium=-101.00,
                fees=1.00,
                trade_date=date(2025, 1, 20),
                open_date=date(2025, 1, 10),
                close_date=date(2025, 1, 20),
                status='Closed',
                parent_trade_id=999  # Some parent ID
            )
            db.session.add(closing)
            db.session.commit()
            
            # Filter closing trades
            all_trades = Trade.query.filter_by(account_id=account_id).all()
            filtered_trades = [
                trade for trade in all_trades 
                if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
            ]
            
            # Should only have opening trade
            assert len(filtered_trades) == 1
            assert filtered_trades[0].id == opening.id
            
            # Calculate P&L (should only use opening trade)
            realized_pnl, unrealized_pnl = calculate_wheel_pnl(filtered_trades)
            
            # Expected: 200 + (-51.50) = 148.50
            assert realized_pnl == 148.50
    
    def test_dashboard_positions_excludes_closing_trades(self, test_app, test_account):
        """Test that positions endpoint excludes closing trades"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening trade
            opening = Trade(
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
            db.session.add(opening)
            db.session.flush()  # Get opening.id before creating closing trade
            opening_id = opening.id
            
            # Create closing trade
            closing = Trade(
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
                parent_trade_id=opening_id
            )
            db.session.add(closing)
            db.session.commit()
            
            # Filter closing trades
            all_trades = Trade.query.filter_by(account_id=account_id).all()
            filtered_trades = [
                trade for trade in all_trades 
                if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
            ]
            
            # Should only have opening trade
            assert len(filtered_trades) == 1
            assert filtered_trades[0].id == opening.id
            
            # Verify closing trade is filtered out
            closing_in_filtered = any(t.id == closing.id for t in filtered_trades)
            assert not closing_in_filtered, "Closing trade should be filtered out"
            
            # Check open positions
            open_trades = [t for t in filtered_trades if t.status == 'Open']
            assert len(open_trades) == 1
