# Scripts

This directory contains utility scripts for database management, migrations, and development tasks.

## Migration Scripts
- `migrate_add_stock_positions.py` - Creates stock_positions table and adds related columns
- `migrate_add_close_fields.py` - Adds close fields to trades table
- `migrate_add_default_fee.py` - Adds default_fee column to accounts table
- `migrate_existing_data.py` - Migrates existing data for stock positions
- `migrate_add_trade_fields.py` - Adds trade fields (legacy)
- `verify_migration.py` - Verifies database schema after migration

## Database Management
- `initialize_new_database.py` - Initialize a new database with schema
- `migrate_data_to_new_db.py` - Migrate data between databases
- `fix_production_schema.py` - Fix production database schema
- `simple_migrate.py` - Simple migration utility
- `verify_and_migrate_prod.py` - Verify and migrate production database

## User Management
- `create_test_user.py` - Create a test user for development
- `query_users.py` - Query user information
- `list_users.py` - List all users
- `check_user.py` - Check user details
- `find_user_in_all_dbs.py` - Find user across all databases
- `cleanup_prod_users.py` - Clean up production users
- `cleanup_test_users.py` - Clean up test users

## Utilities
- `test_connection.py` - Test database connection
- `import_from_excel.py` - Import data from Excel file
- `add_columns.py` - Add columns to database (legacy)
