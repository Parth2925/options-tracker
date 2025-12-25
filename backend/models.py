from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    verification_token_expires = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email_verified': self.email_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50))  # e.g., 'IRA', 'Taxable', 'Margin'
    initial_balance = db.Column(db.Numeric(15, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    deposits = db.relationship('Deposit', backref='account', lazy=True, cascade='all, delete-orphan')
    withdrawals = db.relationship('Withdrawal', backref='account', lazy=True, cascade='all, delete-orphan')
    trades = db.relationship('Trade', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'account_type': self.account_type,
            'initial_balance': float(self.initial_balance) if self.initial_balance else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Deposit(db.Model):
    __tablename__ = 'deposits'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    deposit_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'amount': float(self.amount) if self.amount else 0,
            'deposit_date': self.deposit_date.isoformat() if self.deposit_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Withdrawal(db.Model):
    __tablename__ = 'withdrawals'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    withdrawal_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'amount': float(self.amount) if self.amount else 0,
            'withdrawal_date': self.withdrawal_date.isoformat() if self.withdrawal_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Trade(db.Model):
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    
    # Trade identification
    symbol = db.Column(db.String(20), nullable=False, index=True)
    trade_type = db.Column(db.String(50), nullable=False)  # 'CSP', 'Covered Call', 'LEAPS', 'Assignment', 'Rollover'
    position_type = db.Column(db.String(20), nullable=False)  # 'Open', 'Close', 'Assignment'
    
    # Option details
    strike_price = db.Column(db.Numeric(10, 2))
    expiration_date = db.Column(db.Date)
    contract_quantity = db.Column(db.Integer, default=1)
    
    # Financial details
    trade_price = db.Column(db.Numeric(10, 2))  # Price per contract entered by user
    trade_action = db.Column(db.String(30))  # 'Sold to Open', 'Bought to Close', 'Bought to Open', 'Sold to Close'
    premium = db.Column(db.Numeric(15, 2))  # Calculated: Positive for received, negative for paid
    fees = db.Column(db.Numeric(10, 2), default=0)
    assignment_price = db.Column(db.Numeric(10, 2))  # Price at which stock was assigned
    
    # Dates
    trade_date = db.Column(db.Date, nullable=False, index=True)  # Date of this trade entry
    open_date = db.Column(db.Date)  # When position was originally opened (for closing trades, this is parent's trade_date)
    close_date = db.Column(db.Date)  # When position was closed
    
    # Status
    status = db.Column(db.String(20), default='Open')  # 'Open', 'Closed', 'Assigned'
    
    # Relationships for wheel strategy
    parent_trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'))  # For rollovers/assignments
    child_trades = db.relationship('Trade', backref=db.backref('parent_trade', remote_side=[id]))
    
    # Additional fields
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_realized_pnl(self):
        """
        Calculate realized P&L for this trade based on its lifecycle.
        
        Key Formula: Realized P&L = Opening Premium - Closing Premium
        
        Scenarios:
        1. CSP/CC closed early: Opening Premium (from parent) - Closing Premium (this trade)
        2. CSP/CC expired worthless: Keep full premium (Opening Premium - 0)
        3. CSP assigned: Keep premium, stock position created
        4. Covered call assigned (shares called away): Premium + Stock Appreciation
        """
        realized_pnl = 0
        
        # Scenario 1: This is a closing trade (Bought to Close or Sold to Close)
        # Realized P&L = Opening Premium - Closing Premium
        # Handle partial closes by calculating proportional premium
        if self.parent_trade_id and self.trade_action in ['Bought to Close', 'Sold to Close']:
            parent = Trade.query.get(self.parent_trade_id)
            if parent:
                parent_premium = float(parent.premium) if parent.premium else 0
                closing_premium = float(self.premium) if self.premium else 0
                parent_qty = parent.contract_quantity or 1
                closing_qty = self.contract_quantity or 1
                
                # Calculate proportional opening premium for the closed contracts
                # Example: Opened 10 contracts with $497.50, closing 5 contracts
                # Opening premium per contract = $497.50 / 10 = $49.75
                # Opening premium for 5 contracts = $49.75 * 5 = $248.75
                opening_premium_per_contract = parent_premium / parent_qty if parent_qty > 0 else 0
                opening_premium_for_closed = opening_premium_per_contract * closing_qty
                
                # Realized P&L calculation for closing trades
                # The unified formula is: Realized P&L = Opening Premium + Closing Premium
                # This works because premiums are already signed correctly:
                # - Positive premium = money received
                # - Negative premium = money paid
                #
                # Examples:
                # CSP: Opening +$497.50 (received), Closing -$252.50 (paid)
                #   P&L = $497.50 + (-$252.50) = $245 ✓
                #
                # LEAPS: Opening -$8000 (paid), Closing +$9000 (received)
                #   P&L = -$8000 + $9000 = $1000 ✓
                #
                # The key insight: Adding the premiums (which are already signed) gives us the net P&L
                realized_pnl = opening_premium_for_closed + closing_premium
        
        # Scenario 2: Opening trade that expired worthless (no closing trade)
        elif self.status == 'Closed' and not self.close_date and not any(
            child.trade_action in ['Bought to Close', 'Sold to Close'] for child in self.child_trades
        ):
            # Keep the full premium (expired worthless, no cost to close)
            opening_premium = float(self.premium) if self.premium else 0
            realized_pnl = opening_premium
        
        # Scenario 3: CSP was assigned - keep the premium, stock position created
        elif self.trade_type == 'CSP' and self.status == 'Assigned':
            # Keep the premium received
            opening_premium = float(self.premium) if self.premium else 0
            realized_pnl = opening_premium
        
        # Scenario 4: Covered call was assigned (shares called away)
        elif self.trade_type == 'Covered Call' and self.status == 'Assigned':
            # Find the assignment trade (stock position) - it should be the parent
            assignment_trade = None
            if self.parent_trade_id:
                assignment_trade = Trade.query.get(self.parent_trade_id)
            
            # If parent is assignment, calculate stock appreciation
            if assignment_trade and assignment_trade.trade_type == 'Assignment' and assignment_trade.assignment_price and self.strike_price:
                # Premium from covered call
                call_premium = float(self.premium) if self.premium else 0
                # Stock appreciation: (Call Strike - Assignment Price) × Quantity × 100
                stock_appreciation = (float(self.strike_price) - float(assignment_trade.assignment_price)) * self.contract_quantity * 100
                realized_pnl = call_premium + stock_appreciation
            else:
                # Just the premium if we can't find assignment details
                call_premium = float(self.premium) if self.premium else 0
                realized_pnl = call_premium
        
        # Scenario 5: Assignment trade itself - calculate P&L when closed
        elif self.trade_type == 'Assignment':
            # Check if Assignment has been closed by a child trade or by having close_date set
            # If closed, calculate P&L: (Sale Price - Assignment Price) × Quantity × 100
            if self.status == 'Closed' or self.close_date:
                # Check for closing trades (child trades that close this Assignment)
                closing_trades = [child for child in self.child_trades 
                                 if child.trade_action in ['Bought to Close', 'Sold to Close']]
                if closing_trades:
                    # Calculate P&L from closing trades (like CSP/CC)
                    for closing_trade in closing_trades:
                        assignment_cost = float(self.assignment_price) * self.contract_quantity * 100 if self.assignment_price else 0
                        sale_proceeds = float(closing_trade.trade_price) * closing_trade.contract_quantity * 100 if closing_trade.trade_price else 0
                        # P&L = Sale Proceeds - Assignment Cost
                        trade_pnl = sale_proceeds - assignment_cost
                        realized_pnl += trade_pnl
                elif self.trade_price and self.assignment_price:
                    # Assignment was closed directly (no child closing trade) - use trade_price as sale price
                    assignment_cost = float(self.assignment_price) * self.contract_quantity * 100
                    sale_proceeds = float(self.trade_price) * self.contract_quantity * 100
                    realized_pnl = sale_proceeds - assignment_cost
                else:
                    # Assignment is closed but no closing trade or sale price
                    # For closed Assignment trades, the realized P&L is the parent CSP's premium
                    # This represents the premium received from the CSP that was assigned
                    if self.parent_trade_id:
                        parent = Trade.query.get(self.parent_trade_id)
                        if parent and parent.trade_type == 'CSP' and parent.premium:
                            # Use parent CSP's premium as realized P&L
                            realized_pnl = float(parent.premium)
                        else:
                            realized_pnl = 0
                    else:
                        realized_pnl = 0
            else:
                # Assignment still open - no realized P&L
                realized_pnl = 0
        
        # Default: For open positions, no realized P&L yet
        else:
            realized_pnl = 0
        
        return round(realized_pnl, 2)
    
    def get_remaining_open_quantity(self):
        """Calculate how many contracts are still open (not yet closed)"""
        if self.trade_action not in ['Sold to Open', 'Bought to Open']:
            # Not an opening trade, return 0
            return 0
        
        # Find all closing trades for this position
        closing_trades = [child for child in self.child_trades 
                         if child.trade_action in ['Bought to Close', 'Sold to Close']]
        total_closed_qty = sum(child.contract_quantity for child in closing_trades)
        remaining = self.contract_quantity - total_closed_qty
        
        return max(0, remaining)  # Don't return negative
    
    def get_days_held(self):
        """Calculate number of days the position was held"""
        from datetime import date
        
        open_dt = self.open_date or self.trade_date
        # For Assignment trades, treat 'Assigned' status as open (still holding stock)
        # For other trades, only 'Open' status means still open
        is_open = self.status == 'Open' or (self.trade_type == 'Assignment' and self.status == 'Assigned')
        close_dt = self.close_date or (date.today() if is_open else None)
        
        if open_dt and close_dt:
            return (close_dt - open_dt).days
        return None
    
    def calculate_time_based_return(self):
        """
        Calculate time-based return metrics:
        - Days held
        - Annualized return (if closed)
        """
        days_held = self.get_days_held()
        realized_pnl = self.calculate_realized_pnl()
        
        # For Assignment trades, use parent CSP's premium as realized P&L for return % calculation
        if self.trade_type == 'Assignment' and self.parent_trade_id and realized_pnl == 0:
            parent = Trade.query.get(self.parent_trade_id)
            if parent and parent.trade_type == 'CSP' and parent.premium:
                # Use parent CSP's premium as the realized P&L for return calculation
                realized_pnl = float(parent.premium)
        
        if days_held and days_held > 0 and realized_pnl != 0:
            # Get the capital at risk (for options, this is typically the strike × quantity × 100)
            # For CSP: strike × quantity × 100
            # For Assignment: assignment_price × quantity × 100 (the capital tied up in the stock)
            # For Covered Call: assignment_price × quantity × 100 (if assigned) or strike × quantity × 100
            capital_at_risk = 0
            if self.trade_type == 'Assignment' and self.assignment_price:
                # For Assignment trades, use assignment_price as the capital at risk
                capital_at_risk = float(self.assignment_price) * self.contract_quantity * 100
            elif self.strike_price:
                capital_at_risk = float(self.strike_price) * self.contract_quantity * 100
            
            if capital_at_risk > 0:
                # Simple return
                simple_return = (realized_pnl / capital_at_risk) * 100
                # Annualized return
                annualized_return = ((1 + (realized_pnl / capital_at_risk)) ** (365 / days_held) - 1) * 100
                
                return {
                    'days_held': days_held,
                    'simple_return_pct': round(simple_return, 2),
                    'annualized_return_pct': round(annualized_return, 2),
                    'realized_pnl': realized_pnl,
                    'capital_at_risk': capital_at_risk
                }
        
        return {
            'days_held': days_held,
            'simple_return_pct': None,
            'annualized_return_pct': None,
            'realized_pnl': realized_pnl,
            'capital_at_risk': None
        }
    
    def auto_determine_status(self):
        """
        Automatically determine trade status based on dates and relationships.
        Returns: 'Open', 'Closed', 'Assigned', or 'Expired'
        """
        from datetime import date
        
        today = date.today()
        
        # If there's a close_date, it's closed
        if self.close_date:
            return 'Closed'
        
        # If this is a closing trade (Bought to Close or Sold to Close), it's closed
        if self.trade_action in ['Bought to Close', 'Sold to Close']:
            return 'Closed'
        
        # If status is explicitly set to Assigned, keep it
        if self.status == 'Assigned':
            return 'Assigned'
        
        # If it's an assignment trade, it's assigned
        if self.trade_type == 'Assignment':
            return 'Assigned'
        
        # If expiration date has passed and no close_date, check status
        if self.expiration_date and self.expiration_date < today:
            # Check if there's an assignment trade linked (child trade)
            if any(child.trade_type == 'Assignment' for child in self.child_trades):
                return 'Assigned'
            else:
                # Expired worthless - keep premium, mark as closed
                return 'Closed'
        
        # If there's a child trade that closed this position, check if it's a full or partial close
        closing_trades = [child for child in self.child_trades if child.trade_action in ['Bought to Close', 'Sold to Close']]
        if closing_trades:
            # Calculate total closed quantity
            total_closed_qty = sum(child.contract_quantity for child in closing_trades)
            
            # Only mark as closed if all contracts are closed
            # IMPORTANT: If status is explicitly "Open" and we have remaining quantity, keep it Open
            # This prevents auto_determine_status from overriding explicit status set during partial closes
            if total_closed_qty >= self.contract_quantity:
                return 'Closed'
            else:
                # Partial close - keep as Open (don't override explicit status)
                # If status was explicitly set to Open, return it; otherwise return current status
                if self.status == 'Open':
                    return 'Open'
                # If status is currently Closed but we have remaining quantity, it should be Open
                if self.status == 'Closed' and total_closed_qty < self.contract_quantity:
                    return 'Open'
            # Otherwise, it's a partial close - keep it open
            return 'Open'
        
        # Default to current status or Open
        return self.status or 'Open'
    
    def get_trade_chain(self):
        """
        Get the full trade chain: parent -> this -> children
        Returns a dict with parent, current, and children trades
        """
        parent = Trade.query.get(self.parent_trade_id) if self.parent_trade_id else None
        children = self.child_trades
        
        return {
            'parent': parent.to_dict() if parent else None,
            'current': self.to_dict(),
            'children': [child.to_dict() for child in children]
        }
    
    def to_dict(self, include_realized_pnl=False):
        result = {
            'id': self.id,
            'account_id': self.account_id,
            'symbol': self.symbol,
            'trade_type': self.trade_type,
            'position_type': self.position_type,
            'strike_price': float(self.strike_price) if self.strike_price else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'contract_quantity': self.contract_quantity,
            'trade_price': float(self.trade_price) if self.trade_price else None,
            'trade_action': self.trade_action,
            'premium': float(self.premium) if self.premium else 0,
            'fees': float(self.fees) if self.fees else 0,
            'assignment_price': float(self.assignment_price) if self.assignment_price else None,
            'trade_date': self.trade_date.isoformat() if self.trade_date else None,
            'open_date': self.open_date.isoformat() if self.open_date else None,
            'close_date': self.close_date.isoformat() if self.close_date else None,
            'status': self.status,
            'parent_trade_id': self.parent_trade_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_realized_pnl:
            realized_pnl = self.calculate_realized_pnl()
            # For Assignment trades, show parent CSP's premium as realized P&L
            if self.trade_type == 'Assignment' and realized_pnl == 0 and self.parent_trade_id:
                parent = Trade.query.get(self.parent_trade_id)
                if parent and parent.trade_type == 'CSP' and parent.premium:
                    realized_pnl = float(parent.premium)
            result['realized_pnl'] = realized_pnl
            # Add time-based return metrics
            return_metrics = self.calculate_time_based_return()
            result['days_held'] = return_metrics['days_held']
            result['simple_return_pct'] = return_metrics['simple_return_pct']
            result['annualized_return_pct'] = return_metrics['annualized_return_pct']
        
        # Add remaining open quantity for opening trades
        if self.trade_action in ['Sold to Open', 'Bought to Open']:
            result['remaining_open_quantity'] = self.get_remaining_open_quantity()
        
        return result

