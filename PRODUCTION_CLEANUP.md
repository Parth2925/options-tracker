# Cleaning Up Production Database

This guide explains how to clean up test users from your **production database** on Render.

## Option 1: Run Script Locally with Production Database URL (Recommended)

This is the safest and easiest method. You'll run the cleanup script on your local machine but connect to the production database.

### Step 1: Get Production Database URL

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your **PostgreSQL database** (not the web service)
3. Go to the **"Info"** or **"Connections"** tab
4. Find **"Internal Database URL"** or **"External Connection String"**
   - **Internal Database URL**: Use this if running from Render's environment
   - **External Connection String**: Use this if running from your local machine
5. Copy the connection string (it looks like: `postgresql://user:password@host:port/dbname`)

### Step 2: Run Cleanup Script

**Method A: Pass DATABASE_URL as command line argument** (Recommended)
```bash
cd backend

# List all users (replace with your actual database URL)
python cleanup_test_users.py --database-url "postgresql://user:pass@host:port/dbname?sslmode=require" --list

# Preview deletion (dry run)
python cleanup_test_users.py --database-url "postgresql://user:pass@host:port/dbname?sslmode=require" --email-pattern 'dev.nondon.store'

# Actually delete
python cleanup_test_users.py --database-url "postgresql://user:pass@host:port/dbname?sslmode=require" --email-pattern 'dev.nondon.store' --execute
```

**Method B: Set DATABASE_URL in environment variable**
```bash
cd backend

# Set environment variable (Linux/Mac)
export DATABASE_URL="postgresql://user:pass@host:port/dbname?sslmode=require"

# Or create a .env.production file temporarily
echo 'DATABASE_URL=postgresql://user:pass@host:port/dbname?sslmode=require' > .env.production

# Run the script
python cleanup_test_users.py --list
python cleanup_test_users.py --email-pattern 'dev.nondon.store' --execute
```

**Method C: Use a temporary .env file**
```bash
cd backend

# Create temporary .env file (backup your existing .env first!)
cp .env .env.backup
echo 'DATABASE_URL=postgresql://user:pass@host:port/dbname?sslmode=require' > .env

# Run cleanup
python cleanup_test_users.py --list
python cleanup_test_users.py --email-pattern 'dev.nondon.store' --execute

# Restore original .env
mv .env.backup .env
```

### Step 3: Verify Deletion

```bash
python cleanup_test_users.py --database-url "your-production-url" --list
```

## Option 2: Create Admin API Endpoint (More Secure)

If you prefer to do it via API endpoint, we can create an admin-only endpoint. However, this requires authentication.

## Option 3: Direct PostgreSQL Access (Advanced)

If you have `psql` installed and the database allows external connections:

```bash
# Connect to PostgreSQL
psql "postgresql://user:pass@host:port/dbname?sslmode=require"

# List users
SELECT id, email, first_name, last_name, email_verified, created_at FROM users ORDER BY created_at DESC;

# Delete users by email pattern
DELETE FROM users WHERE email LIKE '%dev.nondon.store%';

# Delete unverified users
DELETE FROM users WHERE email_verified = FALSE;

# Exit
\q
```

**⚠️ WARNING**: Direct SQL deletion bypasses cascade deletes in SQLAlchemy models. You may need to manually delete related records:

```sql
-- Delete related data first
DELETE FROM deposits WHERE account_id IN (SELECT id FROM accounts WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%'));
DELETE FROM trades WHERE account_id IN (SELECT id FROM accounts WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%'));
DELETE FROM accounts WHERE user_id IN (SELECT id FROM users WHERE email LIKE '%test%');
DELETE FROM users WHERE email LIKE '%test%';
```

## Recommended Workflow

1. **Always do a dry run first:**
   ```bash
   python cleanup_test_users.py --database-url "your-url" --list
   python cleanup_test_users.py --database-url "your-url" --email-pattern 'pattern'  # No --execute
   ```

2. **Verify the users to be deleted are test users only**

3. **Execute the deletion:**
   ```bash
   python cleanup_test_users.py --database-url "your-url" --email-pattern 'pattern' --execute
   ```

4. **Verify deletion:**
   ```bash
   python cleanup_test_users.py --database-url "your-url" --list
   ```

## Security Notes

- ⚠️ **Never commit your production DATABASE_URL to git**
- ⚠️ **Always backup before deleting** (Render provides automatic backups on paid plans)
- ⚠️ **Double-check email patterns** - you don't want to delete real users
- ⚠️ **Test on a small subset first** (e.g., delete by user-id before bulk deleting)

## Common Patterns for Test Users

- Emails ending with test domains: `--email-pattern 'dev.nondon.store'`
- Emails containing "test": `--email-pattern 'test'`
- Unverified emails: `--unverified --execute`
- Recent test users: `--days-ago 7 --execute`

