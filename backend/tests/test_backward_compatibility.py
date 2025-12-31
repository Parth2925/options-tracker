"""
Test backward compatibility with old format (2-entry) trades.
This ensures existing users' data will work correctly after the migration.
"""
import pytest
from models import Trade, Account, User, db
from routes.dashboard import calculate_wheel_pnl
from datetime import date, timedelta


def test_old_format_csp_assignment_pnl(test_app, test_user, test_account):
    """Test that old format CSP assignment (2-entry) calculates P&L correctly"""
    with test_app.app_context():
        # Create old format CSP: Opening trade
        opening_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Sold to Open',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=200.0,  # $1.00 per share × 2 contracts × 100 shares
            fees=2.0,
            trade_date=date.today() - timedelta(days=30),
            status='Open',
            position_type='Open'
        )
        db.session.add(opening_trade)
        db.session.flush()
        
        # Create old format closing trade: Assignment
        assignment_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='Assignment',
            trade_action='Assigned',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=0,
            fees=0,
            trade_date=date.today(),
            assignment_price=150.0,
            status='Assigned',
            parent_trade_id=opening_trade.id,
            position_type='Assignment'
        )
        db.session.add(assignment_trade)
        db.session.commit()
        
        # Verify opening trade P&L (should include premium from assignment)
        opening_pnl = opening_trade.calculate_realized_pnl()
        # For CSP assignment, P&L = premium received (no closing cost)
        assert opening_pnl == 200.0, f"Expected P&L 200.0, got {opening_pnl}"
        
        # Verify assignment trade P&L (should be 0, parent handles it)
        assignment_pnl = assignment_trade.calculate_realized_pnl()
        assert assignment_pnl == 0, f"Assignment trade P&L should be 0, got {assignment_pnl}"


def test_old_format_buy_to_close_pnl(test_app, test_user, test_account):
    """Test that old format Buy to Close (2-entry) calculates P&L correctly"""
    with test_app.app_context():
        # Create opening trade
        opening_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Sold to Open',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=5,
            premium=500.0,  # $1.00 per share × 5 contracts × 100 shares
            fees=5.0,
            trade_date=date.today() - timedelta(days=30),
            status='Open',
            position_type='Open'
        )
        db.session.add(opening_trade)
        db.session.flush()
        
        # Create closing trade: Buy to Close (partial - 2 contracts)
        closing_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Bought to Close',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=-80.0,  # Paid $0.40 per share × 2 contracts × 100 shares = -$80
            fees=2.0,
            trade_date=date.today(),
            status='Closed',
            parent_trade_id=opening_trade.id,
            position_type='Close'
        )
        db.session.add(closing_trade)
        db.session.commit()
        
        # Verify closing trade P&L
        # Opening premium for 2 contracts = (500/5) * 2 = 200
        # Closing premium = -80
        # P&L = 200 + (-80) = 120
        closing_pnl = closing_trade.calculate_realized_pnl()
        expected_pnl = (500.0 / 5 * 2) + (-80.0)  # 200 - 80 = 120
        assert abs(closing_pnl - expected_pnl) < 0.01, f"Expected P&L {expected_pnl}, got {closing_pnl}"
        
        # Verify parent trade P&L (should be same as closing trade for partial close)
        opening_pnl = opening_trade.calculate_realized_pnl()
        assert abs(opening_pnl - expected_pnl) < 0.01, f"Parent P&L should be {expected_pnl}, got {opening_pnl}"


def test_old_format_expired_pnl(test_app, test_user, test_account):
    """Test that old format Expired (2-entry) calculates P&L correctly"""
    with test_app.app_context():
        # Create opening trade
        opening_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Sold to Open',
            strike_price=150.0,
            expiration_date=date.today() - timedelta(days=1),  # Expired yesterday
            contract_quantity=3,
            premium=300.0,  # $1.00 per share × 3 contracts × 100 shares
            fees=3.0,
            trade_date=date.today() - timedelta(days=30),
            status='Open',
            position_type='Open'
        )
        db.session.add(opening_trade)
        db.session.flush()
        
        # Create closing trade: Expired
        expired_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Expired',
            strike_price=150.0,
            expiration_date=date.today() - timedelta(days=1),
            contract_quantity=3,
            premium=0,
            fees=0,
            trade_date=date.today() - timedelta(days=1),
            status='Expired',
            parent_trade_id=opening_trade.id,
            position_type='Close'
        )
        db.session.add(expired_trade)
        db.session.commit()
        
        # Verify expired trade P&L
        # Opening premium for 3 contracts = 300
        # Closing premium = 0 (expired worthless)
        # P&L = 300 + 0 = 300
        expired_pnl = expired_trade.calculate_realized_pnl()
        expected_pnl = 300.0
        assert abs(expired_pnl - expected_pnl) < 0.01, f"Expected P&L {expected_pnl}, got {expired_pnl}"
        
        # Verify parent trade P&L
        opening_pnl = opening_trade.calculate_realized_pnl()
        assert abs(opening_pnl - expected_pnl) < 0.01, f"Parent P&L should be {expected_pnl}, got {opening_pnl}"


def test_dashboard_filters_old_format_closing_trades(test_app, test_user, test_account):
    """Test that dashboard filters out old format closing trades correctly"""
    with test_app.app_context():
        # Create opening trade
        opening_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Sold to Open',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=200.0,
            fees=2.0,
            trade_date=date.today() - timedelta(days=30),
            status='Closed',
            position_type='Open'
        )
        db.session.add(opening_trade)
        db.session.flush()
        
        # Create closing trade (old format)
        closing_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Bought to Close',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=-100.0,
            fees=2.0,
            trade_date=date.today(),
            status='Closed',
            parent_trade_id=opening_trade.id,
            position_type='Close'
        )
        db.session.add(closing_trade)
        db.session.commit()
        
        # Test the filtering logic directly
        trades = Trade.query.filter_by(account_id=test_account.id).all()
        filtered = [t for t in trades 
                   if not (t.trade_action in ['Bought to Close', 'Sold to Close'] and t.parent_trade_id)]
        
        # Should only have opening trade
        assert len(filtered) == 1, f"Expected 1 trade, got {len(filtered)}"
        assert filtered[0].id == opening_trade.id, "Should be opening trade"
        assert filtered[0].parent_trade_id is None, "Opening trade should not have parent"


def test_dashboard_pnl_includes_old_format_trades(test_app, test_user, test_account):
    """Test that dashboard P&L calculation includes old format trades correctly"""
    with test_app.app_context():
        # Create old format trade pair
        opening_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Sold to Open',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=200.0,
            fees=2.0,
            trade_date=date.today() - timedelta(days=30),
            status='Closed',
            position_type='Open'
        )
        db.session.add(opening_trade)
        db.session.flush()
        
        closing_trade = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Bought to Close',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=-100.0,
            fees=2.0,
            trade_date=date.today(),
            status='Closed',
            parent_trade_id=opening_trade.id,
            position_type='Close'
        )
        db.session.add(closing_trade)
        db.session.commit()
        
        # Get all trades
        trades = Trade.query.filter_by(account_id=test_account.id).all()
        
        # Filter out closing trades (dashboard logic)
        filtered_trades = [
            trade for trade in trades 
            if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
        ]
        
        # Calculate P&L from filtered trades
        realized_pnl = 0
        for trade in filtered_trades:
            if trade.status in ['Closed', 'Assigned', 'Expired']:
                trade_realized = trade.calculate_realized_pnl()
                realized_pnl += trade_realized
        
        # Expected: Opening premium (200) + Closing premium (-100) = 100
        expected_pnl = 200.0 + (-100.0)  # 100
        assert abs(realized_pnl - expected_pnl) < 0.01, f"Expected P&L {expected_pnl}, got {realized_pnl}"


def test_mixed_old_and_new_format_trades(test_app, test_user, test_account):
    """Test that system handles both old and new format trades correctly"""
    with test_app.app_context():
        # Old format: 2-entry trade
        old_opening = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Sold to Open',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=200.0,
            fees=2.0,
            trade_date=date.today() - timedelta(days=30),
            status='Closed',
            position_type='Open'
        )
        db.session.add(old_opening)
        db.session.flush()
        
        old_closing = Trade(
            account_id=test_account.id,
            symbol='AAPL',
            trade_type='CSP',
            trade_action='Bought to Close',
            strike_price=150.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=2,
            premium=-100.0,
            fees=2.0,
            trade_date=date.today(),
            status='Closed',
            parent_trade_id=old_opening.id,
            position_type='Close'
        )
        db.session.add(old_closing)
        db.session.flush()
        
        # New format: Single-entry trade
        new_trade = Trade(
            account_id=test_account.id,
            symbol='MSFT',
            trade_type='CSP',
            trade_action='Sold to Open',
            strike_price=300.0,
            expiration_date=date.today() + timedelta(days=30),
            contract_quantity=1,
            premium=150.0,
            fees=1.0,
            trade_date=date.today() - timedelta(days=20),
            close_date=date.today(),
            close_premium=-50.0,
            close_method='buy_to_close',
            status='Closed',
            position_type='Open'
        )
        db.session.add(new_trade)
        db.session.commit()
        
        # Get all trades
        trades = Trade.query.filter_by(account_id=test_account.id).all()
        
        # Filter out closing trades
        filtered_trades = [
            trade for trade in trades 
            if not (trade.trade_action in ['Bought to Close', 'Sold to Close'] and trade.parent_trade_id)
        ]
        
        # Should have 2 trades (old_opening and new_trade)
        assert len(filtered_trades) == 2, f"Expected 2 trades, got {len(filtered_trades)}"
        
        # Calculate total P&L
        total_pnl = 0
        for trade in filtered_trades:
            if trade.status in ['Closed', 'Assigned', 'Expired']:
                total_pnl += trade.calculate_realized_pnl()
        
        # Old format: 200 + (-100) = 100
        # New format: 150 + (-50) = 100
        # Total: 200
        expected_total = 200.0
        assert abs(total_pnl - expected_total) < 0.01, f"Expected total P&L {expected_total}, got {total_pnl}"

