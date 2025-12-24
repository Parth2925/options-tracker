# Performance Improvement Testing Guide

This document outlines how to test the performance improvements implemented to handle Render free tier limitations.

## Improvements Implemented

1. **Retry Logic with Exponential Backoff** - Automatically retries failed requests up to 3 times
2. **Increased Timeout** - API timeout increased from 10s to 30s to handle cold starts
3. **Keep-Alive Mechanism** - Pings backend every 10 minutes to prevent spin-down
4. **Better Error Messages** - More informative error messages for users

## Testing the Keep-Alive Mechanism

### Test in Production (Recommended)

1. **Verify Keep-Alive Endpoint Works:**
   - Open browser developer console (F12)
   - Go to Network tab
   - Navigate to your production site
   - You should see a request to `/api/ping` when the app loads
   - After 10 minutes, you should see another `/api/ping` request

2. **Verify Backend Stays Awake:**
   - Let the app sit idle for 16+ minutes (longer than Render's 15-minute spin-down)
   - Try to create a trade or load data
   - If keep-alive is working, the request should succeed immediately (no cold start delay)

3. **Check Backend Logs (Render Dashboard):**
   - Go to your Render service logs
   - Look for incoming requests to `/api/ping`
   - Should see requests every ~10 minutes when users have the app open

### Manual Test (Development)

1. **Test Ping Endpoint:**
   ```bash
   # In browser console or using curl:
   fetch('/api/ping')
     .then(r => r.json())
     .then(console.log)
   ```

2. **Verify Keep-Alive Interval:**
   - Open browser console
   - Check that `setInterval` is set up (you can add a console.log in App.js to verify)
   - Wait 10 minutes and verify another ping is sent

## Testing Retry Logic

### Simulate Network Errors

1. **Using Browser DevTools:**
   - Open Network tab in DevTools
   - Set throttling to "Offline" or "Slow 3G"
   - Try to create a trade
   - You should see the request retry (check Network tab for multiple attempts)

2. **Test Server Errors (5xx):**
   - Temporarily modify backend to return 500 error
   - Try to create a trade
   - Should retry up to 3 times with exponential backoff
   - Check Network tab - should see retries with delays

3. **Test Cold Start Scenario:**
   - Stop your backend service (or wait for Render spin-down)
   - Try to create a trade
   - Start backend service
   - First request may fail/timeout, but retry should succeed once backend is up

### Expected Behavior:
- **Retry Count:** Up to 3 retries (total 4 attempts)
- **Retry Delays:** 1 second, 2 seconds, 4 seconds (exponential backoff)
- **Only Retries:** Network errors, 5xx server errors, 429 rate limits
- **Does NOT Retry:** 401 (unauthorized), 400 (bad request), 404 (not found)

## Testing Increased Timeout

### Test Cold Start Tolerance

1. **Simulate Cold Start:**
   - Let backend spin down (wait 15+ minutes with no activity, or manually stop it)
   - Try to create a trade or load data
   - Previously: Would fail after 10 seconds
   - Now: Should wait up to 30 seconds, giving backend time to wake up

2. **Verify Timeout Behavior:**
   - If backend is completely down, request should timeout after 30 seconds (not 10)
   - Error message should indicate timeout and suggest retrying

## Testing in Production

### Recommended Test Scenario

1. **Initial Load Test:**
   - Open the production site in a fresh browser tab
   - Check Network tab - should see `/api/ping` request immediately
   - Try creating a trade - should work normally

2. **Keep-Alive Test:**
   - Keep the site open for 20+ minutes
   - Check Network tab periodically - should see `/api/ping` every 10 minutes
   - After 20 minutes, try creating a trade
   - Should work immediately (backend stayed awake)

3. **Cold Start Recovery Test:**
   - Close all browser tabs with your site
   - Wait 20+ minutes (ensures backend spun down)
   - Open site again
   - First request may take longer (cold start), but retry logic should handle it
   - Subsequent requests should be fast

4. **Error Handling Test:**
   - Try creating a trade when backend is starting up
   - Should see retry attempts in Network tab
   - If all retries fail, should see helpful error message

### What to Look For

**✅ Success Indicators:**
- `/api/ping` requests appear every 10 minutes in Network tab
- Failed requests automatically retry (check Network tab)
- Trades/create operations succeed even after backend spin-down
- Better error messages when things fail

**❌ Issues to Watch For:**
- No `/api/ping` requests (keep-alive not working)
- Requests failing immediately without retries
- Timeouts happening too quickly (less than 30 seconds)
- Duplicate trades being created (retry logic issue)

## Browser Console Debugging

Add these to verify functionality:

```javascript
// In browser console, check if keep-alive is running:
// Look for Network requests to /api/ping every 10 minutes

// Check retry behavior:
// Open Network tab, filter for your API calls
// Look for multiple requests with same endpoint when errors occur
```

## Monitoring in Production

### Render Dashboard
- Check service logs for `/api/ping` endpoint hits
- Monitor service uptime
- Check for any timeout errors

### Browser Network Tab
- Monitor API request timing
- Check for retry attempts
- Verify keep-alive pings

### User Experience
- Trades should create successfully more often
- Less "request failed" errors
- Faster response times when backend is awake
- Better error messages when things do fail

## Expected Improvements

1. **Reduced Failed Requests:** Retry logic should catch transient failures
2. **Faster Response Times:** Keep-alive prevents cold starts for active users
3. **Better User Experience:** More informative errors, automatic retries
4. **Higher Success Rate:** Trades and other operations should succeed more consistently

## Notes

- Keep-alive only runs in production (`process.env.NODE_ENV === 'production'`)
- Keep-alive only runs when the app is open in a browser tab
- Retry logic applies to all API requests automatically
- Increased timeout applies to all API requests

