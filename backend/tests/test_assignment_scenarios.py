"""
Tests for Assignment scenarios (CSP assigned creates stock position)
"""
import pytest
from datetime import date
from models import db, Trade, Account, User, StockPosition

class TestAssignmentScenarios:
    """Test Assignment functionality"""
    
    def test_csp_assigned_creates_stock_position(self, test_app, test_account):
        """Test that CSP assignment creates stock position"""
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
            db.session.flush()
            csp_id = csp.id
            
            # Mark as assigned
            assignment_date = date(2025, 1, 15)
            csp.status = 'Assigned'
            csp.close_date = assignment_date
            csp.close_price = None
            csp.close_fees = 0
            csp.close_premium = 0
            csp.close_method = 'assigned'
            csp.assignment_price = 150.00
            csp.open_date = csp.trade_date
            
            # Create stock position from assignment
            shares = csp.contract_quantity * 100
            cost_basis = float(csp.assignment_price) if csp.assignment_price else float(csp.strike_price)
            
            stock_position = StockPosition(
                account_id=account_id,
                symbol=csp.symbol,
                shares=shares,
                cost_basis_per_share=cost_basis,
                acquired_date=assignment_date,
                status='Open',
                source_trade_id=csp_id,
                notes=f'Assigned from CSP trade #{csp_id}'
            )
            db.session.add(stock_position)
            db.session.commit()
            
            # Verify CSP is assigned
            updated_csp = Trade.query.get(csp_id)
            assert updated_csp.status == 'Assigned'
            assert updated_csp.close_method == 'assigned'
            assert updated_csp.assignment_price == 150.00
            
            # Verify stock position was created
            stock_positions = StockPosition.query.filter_by(account_id=account_id).all()
            assert len(stock_positions) == 1
            assert stock_positions[0].shares == 100
            assert stock_positions[0].cost_basis_per_share == 150.00
            assert stock_positions[0].source_trade_id == csp_id
    
    def test_partial_csp_assignment(self, test_app, test_account):
        """Test partial CSP assignment (if supported)"""
        with test_app.app_context():
            account_id = test_account.id
            
            # Create opening CSP with 3 contracts
            csp = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='CSP',
                position_type='Open',
                strike_price=150.00,
                expiration_date=date(2025, 1, 15),
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
            
            # Assign 1 contract (partial assignment)
            assignment_date = date(2025, 1, 15)
            contract_quantity = 1
            
            # Create assignment trade
            assignment_trade = Trade(
                account_id=account_id,
                symbol='AAPL',
                trade_type='Assignment',
                position_type='Assignment',
                strike_price=150.00,
                expiration_date=date(2025, 1, 15),
                contract_quantity=contract_quantity,
                assignment_price=150.00,
                trade_date=assignment_date,
                open_date=csp.trade_date,
                status='Assigned',
                parent_trade_id=csp_id
            )
            db.session.add(assignment_trade)
            
            # Update parent (keep open for partial assignment)
            csp.status = 'Open'
            
            # Create stock position for assigned shares
            shares = contract_quantity * 100
            stock_position = StockPosition(
                account_id=account_id,
                symbol='AAPL',
                shares=shares,
                cost_basis_per_share=150.00,
                acquired_date=assignment_date,
                status='Open',
                source_trade_id=assignment_trade.id,
                notes=f'Assigned from CSP trade #{csp_id}'
            )
            db.session.add(stock_position)
            db.session.commit()
            
            # Verify assignment trade was created
            assignment_trades = Trade.query.filter_by(parent_trade_id=csp_id, trade_type='Assignment').all()
            assert len(assignment_trades) == 1
            
            # Verify parent is still open
            updated_csp = Trade.query.get(csp_id)
            assert updated_csp.status == 'Open'
            
            # Verify stock position was created
            stock_positions = StockPosition.query.filter_by(account_id=account_id).all()
            assert len(stock_positions) == 1
            assert stock_positions[0].shares == 100
