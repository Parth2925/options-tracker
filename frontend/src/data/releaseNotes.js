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

