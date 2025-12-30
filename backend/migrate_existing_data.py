#!/usr/bin/env python3
"""
Migration script to handle existing data for stock positions feature.

This script:
1. Creates stock positions from existing Assignment trades
2. Links existing Covered Call trades to stock positions (or creates positions if needed)
3. Handles partial assignments and multiple covered calls

Usage:
    python migrate_existing_data.py [--database-url DATABASE_URL] [--dry-run]
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask
from sqlalchemy import and_

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def get_db_url():
    return os.getenv('DATABASE_URL', 'sqlite:///options_tracker.db')

def setup_app_and_db(database_url):
    """Setup Flask app and database connection"""
    app = Flask(__name__)
    
    # Configure database URL
    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        if 'sslmode' not in database_url:
            separator = '&' if '?' in database_url else '?'
            database_url = f"{database_url}{separator}sslmode=require"
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 5,
        'max_overflow': 10,
    } if database_url.startswith('postgresql://') or database_url.startswith('postgres://') else {}
    
    from models import db, Trade, StockPosition
    db.init_app(app)
    
    return app, db, Trade, StockPosition

def migrate_existing_data(database_url, dry_run=True):
    """Migrate existing trades to use stock positions"""
    app, db, Trade, StockPosition = setup_app_and_db(database_url)
    
    with app.app_context():
        print(f"\n{'='*80}")
        print(f"Stock Positions Migration for Existing Data")
        print(f"{'='*80}")
        print(f"Database: {database_url[:50]}...")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print(f"{'='*80}\n")
        
        stats = {
            'assignments_processed': 0,
            'stock_positions_created': 0,
            'covered_calls_linked': 0,
            'covered_calls_need_manual_review': 0,
            'errors': []
        }
        
        try:
            # Step 1: Create stock positions from existing Assignment trades
            print("Step 1: Processing Assignment trades...")
            assignment_trades = Trade.query.filter(
                Trade.trade_type == 'Assignment'
            ).all()
            
            for assignment in assignment_trades:
                stats['assignments_processed'] += 1
                
                # Check if stock position already exists for this assignment
                existing_position = StockPosition.query.filter_by(
                    source_trade_id=assignment.id
                ).first()
                
                if existing_position:
                    print(f"  ✓ Assignment #{assignment.id} already has stock position #{existing_position.id}")
                    continue
                
                # Validate assignment has required data
                if not assignment.assignment_price or not assignment.contract_quantity:
                    stats['errors'].append(f"Assignment #{assignment.id}: Missing assignment_price or contract_quantity")
                    print(f"  ⚠ Assignment #{assignment.id}: Missing required data (assignment_price or contract_quantity)")
                    continue
                
                shares = assignment.contract_quantity * 100
                cost_basis = float(assignment.assignment_price)
                
                if dry_run:
                    print(f"  [DRY RUN] Would create stock position:")
                    print(f"    - Symbol: {assignment.symbol}")
                    print(f"    - Shares: {shares}")
                    print(f"    - Cost Basis: ${cost_basis:.2f}/share")
                    print(f"    - Account: {assignment.account_id}")
                    print(f"    - Source: Assignment trade #{assignment.id}")
                else:
                    stock_position = StockPosition(
                        account_id=assignment.account_id,
                        symbol=assignment.symbol,
                        shares=shares,
                        cost_basis_per_share=cost_basis,
                        acquired_date=assignment.trade_date or datetime.now().date(),
                        status='Open',
                        source_trade_id=assignment.id,
                        notes=f'Migrated from Assignment trade #{assignment.id}'
                    )
                    db.session.add(stock_position)
                    db.session.flush()  # Get the ID
                    stats['stock_positions_created'] += 1
                    print(f"  ✓ Created stock position #{stock_position.id} from Assignment #{assignment.id}")
            
            if not dry_run:
                db.session.commit()
            
            # Step 2: Link existing Covered Call trades to stock positions
            print(f"\nStep 2: Processing Covered Call trades...")
            covered_calls = Trade.query.filter(
                Trade.trade_type == 'Covered Call'
            ).all()
            
            for cc in covered_calls:
                # Skip if already linked
                if cc.stock_position_id:
                    print(f"  ✓ Covered Call #{cc.id} already linked to stock position #{cc.stock_position_id}")
                    continue
                
                # Try to find matching stock position
                # First, check if there's a parent Assignment trade
                stock_position = None
                
                if cc.parent_trade_id:
                    parent = Trade.query.get(cc.parent_trade_id)
                    if parent and parent.trade_type == 'Assignment':
                        # Find stock position created from this assignment
                        stock_position = StockPosition.query.filter_by(
                            source_trade_id=parent.id,
                            account_id=cc.account_id,
                            symbol=cc.symbol
                        ).first()
                
                # If no parent assignment, try to find any matching stock position
                if not stock_position:
                    stock_positions = StockPosition.query.filter(
                        and_(
                            StockPosition.account_id == cc.account_id,
                            StockPosition.symbol == cc.symbol,
                            StockPosition.status == 'Open'
                        )
                    ).all()
                    
                    # Try to find one with enough available shares
                    for sp in stock_positions:
                        available = sp.get_available_shares()
                        needed = cc.contract_quantity * 100
                        if available >= needed:
                            stock_position = sp
                            break
                    
                    # If still no match, use the first one (user will need to review)
                    if not stock_position and stock_positions:
                        stock_position = stock_positions[0]
                
                if stock_position:
                    shares_needed = cc.contract_quantity * 100
                    available_shares = stock_position.get_available_shares()
                    
                    if available_shares >= shares_needed or dry_run:
                        if dry_run:
                            print(f"  [DRY RUN] Would link Covered Call #{cc.id} to stock position #{stock_position.id}")
                            print(f"    - Shares needed: {shares_needed}")
                            print(f"    - Available: {available_shares}")
                        else:
                            cc.stock_position_id = stock_position.id
                            cc.shares_used = shares_needed
                            stats['covered_calls_linked'] += 1
                            print(f"  ✓ Linked Covered Call #{cc.id} to stock position #{stock_position.id}")
                    else:
                        stats['covered_calls_need_manual_review'] += 1
                        print(f"  ⚠ Covered Call #{cc.id}: Insufficient shares in position #{stock_position.id}")
                        print(f"     Needed: {shares_needed}, Available: {available_shares}")
                else:
                    stats['covered_calls_need_manual_review'] += 1
                    print(f"  ⚠ Covered Call #{cc.id}: No matching stock position found")
                    print(f"     Symbol: {cc.symbol}, Account: {cc.account_id}")
                    print(f"     Manual review required - may need to create stock position manually")
            
            if not dry_run:
                db.session.commit()
            
            # Print summary
            print(f"\n{'='*80}")
            print(f"Migration Summary")
            print(f"{'='*80}")
            print(f"Assignments processed: {stats['assignments_processed']}")
            print(f"Stock positions created: {stats['stock_positions_created']}")
            print(f"Covered calls linked: {stats['covered_calls_linked']}")
            print(f"Covered calls needing manual review: {stats['covered_calls_need_manual_review']}")
            if stats['errors']:
                print(f"\nErrors encountered: {len(stats['errors'])}")
                for error in stats['errors']:
                    print(f"  - {error}")
            print(f"{'='*80}\n")
            
            if dry_run:
                print("This was a DRY RUN. No changes were made.")
                print("Run without --dry-run to apply changes.\n")
            else:
                print("✅ Migration completed successfully!\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate existing trades to use stock positions')
    parser.add_argument('--database-url', type=str, help='Database URL (defaults to DATABASE_URL env var)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no changes made)')
    
    args = parser.parse_args()
    
    database_url = args.database_url or get_db_url()
    
    if not database_url:
        print("❌ Error: DATABASE_URL not provided and not found in environment variables")
        print("\nUsage:")
        print("  python migrate_existing_data.py --database-url 'postgresql://...'")
        print("  OR")
        print("  export DATABASE_URL='postgresql://...'")
        print("  python migrate_existing_data.py")
        sys.exit(1)
    
    migrate_existing_data(database_url, dry_run=args.dry_run)
