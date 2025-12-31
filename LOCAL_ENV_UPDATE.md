# Update Local Environment for Development

## Current Status

✅ Production is using the new PostgreSQL database  
✅ You want to use local SQLite database for development  

## Update Local .env File

Edit `backend/.env` and change:

**From:**
```
DATABASE_URL=postgresql://options_tracker_new_db_user:J7qsnDUWd1Y7yKgOLjFX2qnnimMU60vp@dpg-d5aleduuk2gs73er5c40-a.ohio-postgres.render.com/options_tracker_new_db
```

**To:**
```
DATABASE_URL=sqlite:///instance/options_tracker.db
```

Or if there's a commented line, uncomment it:
```
DATABASE_URL=sqlite:///instance/options_tracker.db
```

## After Update

1. **Restart your local backend server** to pick up the new DATABASE_URL
2. **Test locally** - make sure you can login and see your local data
3. **Verify** - local should use SQLite, production uses PostgreSQL

## Summary

- **Production**: Uses new PostgreSQL database (`options_tracker_new_db`)
- **Local**: Uses SQLite database (`instance/options_tracker.db`)

This is the standard setup - production uses PostgreSQL, local development uses SQLite.

