# Version Management

This project uses semantic versioning starting at **1.0.0**.

## Current Version
- **Backend**: Defined in `backend/version.py`
- **Frontend**: Defined in `frontend/src/utils/version.js` and `frontend/package.json`

## Version Display
The version is displayed in:
- **Navbar**: Shows as a badge next to the user profile (desktop)
- **Mobile Menu**: Shows in the footer section (mobile)

## Incrementing Version

### Automatic Increment (Recommended)
Use the provided script to increment the minor version:

```bash
./increment-version.sh
```

This script will:
1. Read the current version from `backend/version.py`
2. Increment the minor version (e.g., 1.0.0 → 1.1.0)
3. Update all version files:
   - `backend/version.py`
   - `frontend/src/utils/version.js`
   - `frontend/package.json`

### Manual Increment
If you prefer to update manually:

1. Update `backend/version.py`:
   ```python
   VERSION = "1.1.0"  # Change minor version
   ```

2. Update `frontend/src/utils/version.js`:
   ```javascript
   export const VERSION = "1.1.0";  # Same version
   ```

3. Update `frontend/package.json`:
   ```json
   "version": "1.1.0"  # Same version
   ```

## Version Format
- **Major.Minor.Patch** (e.g., 1.0.0)
- **Major**: Increment for breaking changes
- **Minor**: Increment for new features or improvements (current workflow)
- **Patch**: Increment for bug fixes (not currently automated)

## Workflow
1. Make your changes
2. Before pushing to production, run: `./increment-version.sh`
3. Commit the version changes along with your feature changes
4. Push to main branch

The version will automatically be displayed in the UI after deployment.


