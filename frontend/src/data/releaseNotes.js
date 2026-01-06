/**
 * Release notes for each version
 * Add release notes here when incrementing versions
 */
export const releaseNotes = {
  "1.0.0": {
    date: "2024-12-25",
    features: [
      "Initial release of Options Tracker",
      "Track Cash-Secured Puts (CSP), Covered Calls, LEAPS, and Assigned positions",
      "Dashboard with P&L tracking, monthly returns, and position allocation",
      "Account management with deposits and withdrawals",
      "Trade import/export (CSV/Excel)",
      "Mobile-responsive design",
      "Dark mode support",
      "VIX Cash Allocation Calculator tool"
    ],
    improvements: [
      "Comprehensive trade tracking and analytics",
      "Real-time market data integration",
      "User profile management"
    ],
    bugfixes: []
  },
  "1.1.0": {
    date: "2024-12-27",
    features: [
      "Version tracking system - view current version in navbar",
      "About page - access release notes and version history"
    ],
    improvements: [
      "Mobile menu now slides in from the right side",
      "Improved mobile responsiveness for market data boxes and filters"
    ],
    bugfixes: [
      "Fixed mobile menu links not displaying in sidebar"
    ]
  },
  "1.2.0": {
    date: "2024-12-27",
    features: [
      "Footer with About link for easy access to version information and release notes"
    ],
    improvements: [
      "Moved About link from navbar to footer for less prominent placement",
      "Footer designed to accommodate future links (Guide, Contact, Feedback, etc.)"
    ],
    bugfixes: []
  },
  "1.3.0": {
    date: "2024-12-27",
    features: [
      "Company logos displayed next to stock symbols on Dashboard, Positions, and Trades pages"
    ],
    improvements: [
      "Enhanced visual identification of companies with logo integration from Finnhub API",
      "Improved user experience with brand recognition in trade listings"
    ],
    bugfixes: []
  },
  "1.4.0": {
    date: "2024-12-31",
    features: [
      "Enhanced Close Workflow: Single 'Close' button for open trades with context-aware forms (Buy to Close, Expired, Assigned, Exercise)",
      "Stock Positions System: Track actual stock holdings, auto-updated from CSP assignments and LEAPS exercises",
      "Covered Call Integration: Covered calls now reference specific stock positions, with share validation and tracking",
      "Partial Close History: View detailed history of partial closes for a trade in a dedicated pop-up window",
      "Default Account Fees: Set a default fee per account, auto-populating trade forms",
      "Account Editing: Edit account names and initial balances",
      "How to Use Guide: Interactive guide for new users on features and workflows",
      "Pagination on Trades Page: View 50 trades per page with navigation controls"
    ],
    improvements: [
      "UI Consistency: Standardized headers, buttons, filters, empty/loading states, spacing, and typography across all pages",
      "Improved Modal Dialogs: Consistent styling, scrolling behavior, and drag-prevention for Add/Edit Trade, Close Trade, Add/Edit Stock Position, Account, Deposit, and Withdrawal forms",
      "Real-time Close Premium Calculation: Live update of close premium when editing close price or fees",
      "Editable Closed Trade Details: Modify close price, fees, and other details for already closed trades",
      "Dynamic P&L Updates: P&L, return, and dashboard data update automatically after trade edits",
      "Clearer Export Errors: Specific error messages for export failures (e.g., 'No trades found')",
      "Symbol Auto-Uppercase: Ticker symbols automatically converted to capital letters on input",
      "Editable Trade Account/Type: Account and trade type fields are now editable for open trades",
      "Dynamic Fee Update on Account Change: Fees dynamically update to default account fee when account is changed in trade form",
      "Improved Trades Page Layout: Aligned rows, search/filter bar, and buttons for a more finished look",
      "Prominent Positions Tabs: 'Options' and 'Stocks' tabs on Positions page are more obvious",
      "Dashboard Layout: Market data boxes aligned left, compact position details table without horizontal scrolling",
      "Home Page Content: Updated 'Key Features' and 'How It Works' sections to reflect new functionalities",
      "Mobile Layout Improvements: Fixed filters bar staying in place while table scrolls horizontally on mobile"
    ],
    bugfixes: [
      "Fixed P&L doubling issue after importing old-format Excel files",
      "Resolved `formData.trade_price.trim is not a function` error when editing trade date",
      "Fixed `formData.initial_balance.trim is not a function` error when adding default fee to existing account",
      "Corrected Positions page to show total fees and differentiate gross/net premium",
      "Fixed `SyntaxError: Identifier 'url' has already been declared` in Trades.js",
      "Fixed `SyntaxError: Identifier 'currentPage' has already been declared` in Trades.js",
      "Fixed database connection issues for local testing (SQLite)",
      "Fixed `sqlite3.OperationalError: unable to open database file` in tests by correctly configuring test fixtures",
      "Fixed P&L calculation for old-format expired and assigned trades in `models.py`",
      "Fixed trades table layout to stay within card boundaries on desktop",
      "Fixed mobile layout where filters bar was scrolling with table"
    ]
  },
  "1.5.0": {
    date: "2025-01-01",
    features: [
      "Assignment Fee Support: Track assignment/exercise fees charged by brokers (typically $15-25)",
      "Default Assignment Fee per Account: Set a default assignment fee that auto-populates when closing trades as 'Assigned' or 'Called Away'"
    ],
    improvements: [
      "Assignment Price Validation: Options are now always assigned/called away at the strike price (enforced, read-only field)",
      "Accurate P&L Calculations: Assignment fees are now properly subtracted from P&L for assigned CSPs and called away covered calls",
      "Updated How to Use Guide: Instructions now reflect 'Called Away' terminology for covered calls and include assignment fee information",
      "Improved Close Trade Dialog: Assignment price is read-only (always equals strike), with separate assignment fee field"
    ],
    bugfixes: [
      "Fixed P&L accuracy for assigned positions by accounting for assignment fees",
      "Prevented user errors by enforcing assignment price equals strike price (options trading rule)"
    ]
  },
  "1.5.1": {
    date: "2025-01-01",
    features: [],
    improvements: [
      "Historical Trade Entry: Users can now enter trades with past expiration dates without them being auto-marked as 'Closed'",
      "Improved Status Management: System now respects explicitly set 'Open' status for historical entries, allowing users to enter past trades and close them later"
    ],
    bugfixes: [
      "Fixed issue where trades with past expiration dates were automatically marked as 'Closed' when entered, preventing historical data entry",
      "Resolved problem where users couldn't enter historical covered calls or other trades that expired in the past but were closed before expiration"
    ]
  },
  "1.5.2": {
    date: "2025-01-05",
    features: [
      "Year-to-Date (YTD) Period Filter: Added YTD option to dashboard period filters for tracking performance from January 1st of the current year"
    ],
    improvements: [
      "Accurate Return % Calculation: Return percentages are now calculated using capital at the start of the period, providing more accurate performance metrics",
      "Improved Period Filtering: Period-based filters now correctly include trades based on when P&L was realized (close_date) rather than when trades were opened",
      "Complete Unrealized P&L: All open positions are now included in unrealized P&L calculations for period-based filters, regardless of when they were opened",
      "Fixed Missing Status Types: 'Called Away' and 'Expired' statuses are now properly included in all P&L and return calculations"
    ],
    bugfixes: [
      "Fixed YTD filter showing zero values when trades were closed in the current year but opened in previous year",
      "Fixed return % calculation excluding 'Called Away' trades from total capital, causing inaccurate return percentages",
      "Fixed YTD and monthly returns missing trades with 'Called Away' or 'Expired' status",
      "Fixed unrealized P&L only showing positions opened within the period, now correctly shows all open positions"
    ]
  },
  "1.5.3": {
    date: "2025-01-05",
    features: [
      "Strategy Performance Section: New dashboard section showing performance metrics grouped by trade strategy (CSP, Covered Call, LEAPS, etc.)",
      "Ticker Performance Section: New dashboard section showing performance metrics grouped by ticker symbol with company logos"
    ],
    improvements: [
      "Enhanced Dashboard Analytics: Both Strategy and Ticker Performance sections display comprehensive metrics including trades count, win rate, total P&L, % of profit, open contracts, and open premium",
      "Accurate Partial Close Handling: Open contracts count now correctly accounts for partially closed trades using remaining open quantity",
      "Proportional Unrealized P&L: Unrealized P&L calculations now use proportional premium for remaining open contracts when trades are partially closed",
      "Improved Mobile Responsiveness: Strategy and Ticker Performance tables are optimized for mobile devices with responsive font sizes and padding",
      "Dark Mode Support: Both performance sections fully support dark mode with proper alternating row colors and contrast"
    ],
    bugfixes: [
      "Fixed open contracts count incorrectly showing full contract quantity instead of remaining open quantity for partially closed trades",
      "Fixed unrealized P&L calculation using full premium instead of proportional premium for partially closed trades"
    ]
  }
};

/**
 * Get release notes for a specific version
 */
export const getReleaseNotes = (version) => {
  return releaseNotes[version] || null;
};

/**
 * Get all release notes sorted by version (newest first)
 */
export const getAllReleaseNotes = () => {
  return Object.entries(releaseNotes)
    .sort((a, b) => {
      // Sort by version number (descending - newest first)
      const v1 = a[0].split('.').map(Number);
      const v2 = b[0].split('.').map(Number);
      for (let i = 0; i < Math.max(v1.length, v2.length); i++) {
        const num1 = v1[i] || 0;
        const num2 = v2[i] || 0;
        if (num2 !== num1) return num2 - num1;
      }
      return 0;
    })
    .map(([version, notes]) => ({ version, ...notes }));
};

