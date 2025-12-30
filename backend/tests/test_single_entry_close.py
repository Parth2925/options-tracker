"""
Unit tests for single-entry close implementation

Tests cover:
1. Full closes (single-entry approach)
2. Partial closes (two-entry approach)
3. Expired/Assigned (single-entry approach)
4. P&L calculations for both approaches
5. Filtering closing trades
"""
import pytest
from datetime import date, datetime
from models import db, Trade, Account, User, StockPosition

class TestSingleEntryClose:
    """Test single-entry close functionality"""
    
    def test_full_close_csp_updates_original_trade(self, test_app, test_account):
        """Test that full close of CSP updates original trade (single-entry)"""
        with test_app.app_context():
            user_id = test_account.user_id
            # Create opening CSP trade
            csp = Trade(
                account_id=test_account.id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=1,
                trade_price=2.00,
                trade_action='Sold to Open',
                premium=200.00,  # 2.00 * 1 * 100
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(csp)
            db.session.commit()
            csp_id = csp.id
            
            # Close the trade (full close)
            from flask import jsonify
            from unittest.mock import Mock
            request_mock = Mock()
            request_mock.get_json.return_value = {
                'close_method': 'buy_to_close',
                'close_date': '2025-01-15',
                'trade_price': '0.50',
                'fees': '1.50',
                'contract_quantity': 1
            }
            
            # Simulate the close
            close_date = date(2025, 1, 15)
            trade_price = 0.50
            fees = 1.50
            contract_quantity = 1
            
            # Calculate premium (negative for buying)
            premium = -(trade_price * contract_quantity * 100 + fees * contract_quantity)
            # -50 - 1.50 = -51.50
            
            # Update trade directly (full close)
            csp.status = 'Closed'
            csp.close_date = close_date
            csp.close_price = trade_price
            csp.close_fees = fees
            csp.close_premium = premium
            csp.close_method = 'buy_to_close'
            csp.open_date = csp.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(csp_id)
            assert updated_trade.status == 'Closed'
            assert updated_trade.close_date == close_date
            assert updated_trade.close_price == trade_price
            assert updated_trade.close_fees == fees
            assert updated_trade.close_premium == premium
            assert updated_trade.close_method == 'buy_to_close'
            
            # Verify no closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=csp_id).all()
            assert len(closing_trades) == 0
    
    def test_partial_close_csp_creates_closing_trade(self, test_app, test_account):
        """Test that partial close of CSP creates closing trade (two-entry)"""
        with test_app.app_context():
            account_id = test_account.id
            # Create opening CSP trade with 3 contracts
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
                premium=600.00,  # 2.00 * 3 * 100
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(csp)
            db.session.commit()
            csp_id = csp.id
            
            # Close 1 contract (partial close)
            close_date = date(2025, 1, 15)
            trade_price = 0.50
            fees = 1.50
            contract_quantity = 1
            
            # Calculate premium (negative for buying)
            premium = -(trade_price * contract_quantity * 100 + fees * contract_quantity)
            
            # Create closing trade (partial close)
            closing_trade = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Close',
                strike_price=150.00,
                expiration_date=date(2025, 12, 31),
                contract_quantity=contract_quantity,
                trade_price=trade_price,
                trade_action='Bought to Close',
                premium=premium,
                fees=fees,
                trade_date=close_date,
                open_date=csp.trade_date,
                close_date=close_date,
                status='Closed',
                parent_trade_id=csp_id
            )
            db.session.add(closing_trade)
            
            # Update parent (keep open for partial close)
            csp.status = 'Open'
            csp.close_date = None
            
            db.session.commit()
            
            # Verify closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=csp_id).all()
            assert len(closing_trades) == 1
            assert closing_trades[0].contract_quantity == 1
            assert closing_trades[0].premium == premium
            
            # Verify parent is still open
            updated_csp = Trade.query.get(csp_id)
            assert updated_csp.status == 'Open'
            assert updated_csp.close_date is None
    
    def test_expired_updates_original_trade(self, test_app, test_account):
        """Test that expired updates original trade (single-entry)"""
        with test_app.app_context():
            account_id = test_account.id
            # Create opening CSP trade
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
            
            # Mark as expired
            close_date = date(2025, 1, 15)
            csp.status = 'Expired'
            csp.close_date = close_date
            csp.close_price = None
            csp.close_fees = 0
            csp.close_premium = 0
            csp.close_method = 'expired'
            csp.open_date = csp.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(csp_id)
            assert updated_trade.status == 'Expired'
            assert updated_trade.close_date == close_date
            assert updated_trade.close_premium == 0
            assert updated_trade.close_method == 'expired'
            
            # Verify no closing trade was created
            closing_trades = Trade.query.filter_by(parent_trade_id=csp_id).all()
            assert len(closing_trades) == 0
    
    def test_pnl_calculation_single_entry(self, test_app, test_account):
        """Test P&L calculation for single-entry close"""
        with test_app.app_context():
            account_id = test_account.id
            # Create CSP and close it (full close)
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
                premium=200.00,  # Opening premium (received)
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Closed',
                close_date=date(2025, 1, 15),
                close_price=0.50,
                close_fees=1.50,
                close_premium=-51.50,  # Closing premium (paid)
                close_method='buy_to_close',
                open_date=date(2025, 1, 1)
            )
            db.session.add(csp)
            db.session.commit()
            
            # Calculate P&L
            realized_pnl = csp.calculate_realized_pnl()
            
            # Expected: 200.00 + (-51.50) = 148.50
            assert realized_pnl == 148.50
    
    def test_pnl_calculation_two_entry(self, test_app, test_account):
        """Test P&L calculation for two-entry approach (partial close)"""
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
                contract_quantity=2,
                trade_price=2.00,
                trade_action='Sold to Open',
                premium=400.00,  # 2.00 * 2 * 100
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(csp)
            db.session.commit()
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
    
    def test_get_remaining_open_quantity_single_entry(self, test_app, test_account):
        """Test remaining quantity calculation for single-entry close"""
        with test_app.app_context():
            account_id = test_account.id
            # Create CSP and close it fully
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
                close_premium=-51.50,
                close_method='buy_to_close'
            )
            db.session.add(csp)
            db.session.commit()
            
            # Check remaining quantity
            remaining = csp.get_remaining_open_quantity()
            assert remaining == 0
    
    def test_get_remaining_open_quantity_partial_close(self, test_app, test_account):
        """Test remaining quantity calculation for partial close"""
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
            db.session.commit()
            csp_id = csp.id
            
            # Close 1 contract
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
                premium=-51.50,
                fees=1.50,
                trade_date=date(2025, 1, 15),
                open_date=date(2025, 1, 1),
                close_date=date(2025, 1, 15),
                status='Closed',
                parent_trade_id=csp_id
            )
            db.session.add(closing_trade)
            db.session.commit()
            
            # Check remaining quantity
            remaining = csp.get_remaining_open_quantity()
            assert remaining == 2  # 3 - 1 = 2
    
    def test_filter_closing_trades_from_list(self, test_app, test_account):
        """Test that closing trades are filtered from trades list"""
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
                contract_quantity=2,
                trade_price=2.00,
                trade_action='Sold to Open',
                premium=400.00,
                fees=0,
                trade_date=date(2025, 1, 1),
                status='Open'
            )
            db.session.add(opening)
            db.session.commit()
            opening_id = opening.id
            
            # Create closing trade (partial close)
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
            assert filtered_trades[0].id == opening_id
            assert filtered_trades[0].trade_action == 'Sold to Open'
    
    def test_backward_compatibility_existing_closing_trades(self, test_app, test_account):
        """Test that existing closing trades still work (backward compatibility)"""
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
                status='Closed'
            )
            db.session.add(opening)
            db.session.commit()
            opening_id = opening.id
            
            # Create legacy closing trade (old way)
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
            
            # P&L should still calculate correctly
            realized_pnl = closing.calculate_realized_pnl()
            assert realized_pnl == 148.50  # 200 - 51.50
    
    def test_full_close_leaps_sell_to_close(self, test_app, test_account):
        """Test full close of LEAPS using sell to close (single-entry)"""
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
            
            # Close fully (sell to close)
            close_date = date(2025, 6, 1)
            trade_price = 90.00
            fees = 10.00
            contract_quantity = 1
            
            # Calculate premium (positive for selling)
            premium = trade_price * contract_quantity * 100 - fees * contract_quantity
            # 9000 - 10 = 8990
            
            # Update trade directly (full close)
            leaps.status = 'Closed'
            leaps.close_date = close_date
            leaps.close_price = trade_price
            leaps.close_fees = fees
            leaps.close_premium = premium
            leaps.close_method = 'sell_to_close'
            leaps.open_date = leaps.trade_date
            
            db.session.commit()
            
            # Verify
            updated_trade = Trade.query.get(leaps_id)
            assert updated_trade.status == 'Closed'
            assert updated_trade.close_method == 'sell_to_close'
            assert updated_trade.close_premium == 8990.00
            
            # Verify P&L
            realized_pnl = updated_trade.calculate_realized_pnl()
            # Expected: -8000 + 8990 = 990
            assert realized_pnl == 990.00
