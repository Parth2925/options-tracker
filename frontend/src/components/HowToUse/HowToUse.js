import React, { useState } from 'react';
import Navbar from '../Layout/Navbar';
import Footer from '../Layout/Footer';
import './HowToUse.css';

function HowToUse() {
  const [expandedSection, setExpandedSection] = useState(null);

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  const sections = [
    {
      id: 'getting-started',
      title: '🚀 Getting Started',
      icon: '🚀',
      content: (
        <div className="guide-content">
          <h3>Welcome to Options Tracker!</h3>
          <p>This guide will walk you through the key features and how to use them.</p>
          
          <div className="step-section">
            <h4>Step 1: Create Your First Account</h4>
            <ol>
              <li>Navigate to the <strong>Accounts</strong> page from the main menu</li>
              <li>Click the <strong>"Add Account"</strong> button</li>
              <li>Fill in the account details:
                <ul>
                  <li><strong>Account Name:</strong> Give your account a descriptive name (e.g., "Main Trading Account")</li>
                  <li><strong>Account Type:</strong> Select either "Cash" or "Margin"</li>
                  <li><strong>Initial Balance:</strong> Enter your starting account balance</li>
                  <li><strong>Default Fee per Contract:</strong> (Optional) Set a default fee that will auto-populate when creating trades for this account</li>
                </ul>
              </li>
              <li>Click <strong>"Create Account"</strong></li>
            </ol>
            <div className="tip-box">
              <strong>💡 Tip:</strong> You can create multiple accounts to track different strategies or brokerages separately. You can also edit account details later by clicking the edit icon (✏️) next to any account.
            </div>
          </div>

          <div className="step-section">
            <h4>Step 2: Understanding the Dashboard</h4>
            <p>The Dashboard is your command center. It shows:</p>
            <ul>
              <li><strong>Market Data:</strong> Real-time prices for SPY, QQQ, DIA, and VIX</li>
              <li><strong>Account Summary:</strong> Total capital, available capital, and allocated capital</li>
              <li><strong>P&L Metrics:</strong> Total P&L, return percentage, and monthly returns</li>
              <li><strong>Position Details:</strong> All your open positions with company logos</li>
            </ul>
            <p>Use the filters at the top to view data for specific accounts or time periods.</p>
          </div>
        </div>
      )
    },
    {
      id: 'csp',
      title: '📉 Cash-Secured Puts (CSP)',
      icon: '📉',
      content: (
        <div className="guide-content">
          <h3>How to Create and Manage Cash-Secured Puts</h3>
          <p>A Cash-Secured Put (CSP) is when you sell a put option and have enough cash to buy the underlying stock if assigned.</p>
          
          <div className="step-section">
            <h4>Creating a CSP Trade</h4>
            <ol>
              <li>Go to the <strong>Trades</strong> page</li>
              <li>Click <strong>"Add Trade"</strong></li>
              <li>Fill in the trade details:
                <ul>
                  <li><strong>Account:</strong> Select the account for this trade</li>
                  <li><strong>Trade Type:</strong> Select "Cash-Secured Put"</li>
                  <li><strong>Symbol:</strong> Enter the stock ticker (e.g., AAPL)</li>
                  <li><strong>Trade Action:</strong> Select "Sold to Open"</li>
                  <li><strong>Trade Date:</strong> The date you opened the position</li>
                  <li><strong>Strike Price:</strong> The strike price of the put option</li>
                  <li><strong>Expiration Date:</strong> When the option expires</li>
                  <li><strong>Premium:</strong> The premium you received (per share)</li>
                  <li><strong>Contract Quantity:</strong> Number of contracts</li>
                  <li><strong>Fees:</strong> Commission and fees (will auto-populate if you set a default fee for the account)</li>
                </ul>
              </li>
              <li>Click <strong>"Create"</strong></li>
            </ol>
          </div>

          <div className="step-section">
            <h4>Closing a CSP Trade</h4>
            <p>When your CSP expires or you want to close it early, you have three options:</p>
            
            <div className="sub-step">
              <h5>Option 1: Buy to Close</h5>
              <ol>
                <li>Find your open CSP trade in the Trades table</li>
                <li>Click the <strong>"Close"</strong> button</li>
                <li>Select <strong>"Buy to Close"</strong> as the close method</li>
                <li>Enter:
                  <ul>
                    <li><strong>Close Date:</strong> Date you closed the position</li>
                    <li><strong>Buy to Close Price:</strong> Price per share you paid to buy back</li>
                    <li><strong>Fees:</strong> Closing fees</li>
                    <li><strong>Contract Quantity:</strong> Number of contracts to close (for partial closes)</li>
                  </ul>
                </li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
              <p>The system will automatically calculate your P&L, return percentage, and days held.</p>
            </div>

            <div className="sub-step">
              <h5>Option 2: Expired Worthless</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open CSP</li>
                <li>Select <strong>"Expired"</strong> as the close method</li>
                <li>Enter the <strong>Close Date</strong> (defaults to expiration date)</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
              <p>You keep the full premium received, and the system calculates your profit.</p>
            </div>

            <div className="sub-step">
              <h5>Option 3: Assigned</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open CSP</li>
                <li>Select <strong>"Assigned"</strong> as the close method</li>
                <li>Enter the <strong>Assignment Date</strong> (defaults to expiration date)</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
              <p><strong>Important:</strong> When a CSP is assigned, the system automatically creates a stock position for you! You can view it in the <strong>Positions</strong> page under the "Stocks" tab.</p>
            </div>
          </div>

          <div className="tip-box">
            <strong>💡 Tip:</strong> You can partially close a CSP by entering a smaller contract quantity. The system will track the remaining open contracts separately.
          </div>
        </div>
      )
    },
    {
      id: 'leaps',
      title: '📈 LEAPS',
      icon: '📈',
      content: (
        <div className="guide-content">
          <h3>How to Create and Manage LEAPS</h3>
          <p>LEAPS (Long-Term Equity Anticipation Securities) are long-term options contracts, typically with expiration dates more than one year away.</p>
          
          <div className="step-section">
            <h4>Creating a LEAPS Trade</h4>
            <ol>
              <li>Go to the <strong>Trades</strong> page</li>
              <li>Click <strong>"Add Trade"</strong></li>
              <li>Fill in the trade details:
                <ul>
                  <li><strong>Trade Type:</strong> Select "LEAPS"</li>
                  <li><strong>Trade Action:</strong> Select "Bought to Open" (for long LEAPS) or "Sold to Open" (for short LEAPS)</li>
                  <li><strong>Symbol:</strong> Enter the stock ticker</li>
                  <li><strong>Strike Price:</strong> The strike price of the LEAPS</li>
                  <li><strong>Expiration Date:</strong> The expiration date (typically 1-2 years out)</li>
                  <li><strong>Premium:</strong> The premium paid (for long) or received (for short) per share</li>
                  <li><strong>Contract Quantity:</strong> Number of contracts</li>
                  <li><strong>Fees:</strong> Commission and fees</li>
                </ul>
              </li>
              <li>Click <strong>"Create"</strong></li>
            </ol>
          </div>

          <div className="step-section">
            <h4>Closing a LEAPS Trade</h4>
            <p>LEAPS can be closed in three ways:</p>
            
            <div className="sub-step">
              <h5>Option 1: Sell to Close (for long LEAPS)</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open LEAPS</li>
                <li>Select <strong>"Sell to Close"</strong></li>
                <li>Enter the close date, sell price, fees, and contract quantity</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
            </div>

            <div className="sub-step">
              <h5>Option 2: Buy to Close (for short LEAPS)</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open LEAPS</li>
                <li>Select <strong>"Buy to Close"</strong></li>
                <li>Enter the close date, buy price, fees, and contract quantity</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
            </div>

            <div className="sub-step">
              <h5>Option 3: Exercise</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open LEAPS</li>
                <li>Select <strong>"Exercise"</strong></li>
                <li>Enter the <strong>Exercise Date</strong></li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
              <p><strong>Important:</strong> When you exercise a LEAPS, the system automatically creates a stock position for you!</p>
            </div>

            <div className="sub-step">
              <h5>Option 4: Expired Worthless</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open LEAPS</li>
                <li>Select <strong>"Expired"</strong></li>
                <li>Enter the close date (defaults to expiration date)</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'covered-call',
      title: '📊 Covered Calls',
      icon: '📊',
      content: (
        <div className="guide-content">
          <h3>How to Create and Manage Covered Calls</h3>
          <p>A Covered Call is when you sell a call option against stock you already own. The stock "covers" the call, limiting your risk.</p>
          
          <div className="step-section">
            <h4>Prerequisites: Stock Position</h4>
            <p>Before creating a covered call, you need to have a stock position. Stock positions can be created in two ways:</p>
            <ul>
              <li><strong>Automatically:</strong> When a CSP is assigned or a LEAPS is exercised, a stock position is automatically created</li>
              <li><strong>Manually:</strong> Go to <strong>Positions</strong> → <strong>Stocks</strong> tab → Click <strong>"Add Stock Position"</strong></li>
            </ul>
          </div>

          <div className="step-section">
            <h4>Creating a Covered Call Trade</h4>
            <ol>
              <li>Go to the <strong>Trades</strong> page</li>
              <li>Click <strong>"Add Trade"</strong></li>
              <li>Fill in the trade details:
                <ul>
                  <li><strong>Trade Type:</strong> Select "Covered Call"</li>
                  <li><strong>Account:</strong> Select the account (must match the stock position's account)</li>
                  <li><strong>Stock Position:</strong> Select the stock position you want to write calls against</li>
                  <li><strong>Trade Action:</strong> Select "Sold to Open"</li>
                  <li><strong>Symbol:</strong> Enter the stock ticker (must match the stock position)</li>
                  <li><strong>Strike Price:</strong> The strike price of the call option</li>
                  <li><strong>Expiration Date:</strong> When the option expires</li>
                  <li><strong>Premium:</strong> The premium received per share</li>
                  <li><strong>Contract Quantity:</strong> Number of contracts (system validates you have enough shares)</li>
                  <li><strong>Shares Used:</strong> Automatically calculated (1 contract = 100 shares)</li>
                  <li><strong>Fees:</strong> Commission and fees</li>
                </ul>
              </li>
              <li>Click <strong>"Create"</strong></li>
            </ol>
            <div className="tip-box">
              <strong>💡 Tip:</strong> The system automatically tracks which shares are being used by covered calls. You can write multiple covered calls against the same stock position as long as you have enough available shares.
            </div>
          </div>

          <div className="step-section">
            <h4>Closing a Covered Call Trade</h4>
            <p>Covered calls can be closed in three ways:</p>
            
            <div className="sub-step">
              <h5>Option 1: Buy to Close</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open covered call</li>
                <li>Select <strong>"Buy to Close"</strong></li>
                <li>Enter the close date, buy price, fees, and contract quantity</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
              <p><strong>Important:</strong> When you buy to close a covered call early, the shares are immediately returned to your available stock position!</p>
            </div>

            <div className="sub-step">
              <h5>Option 2: Expired Worthless</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open covered call</li>
                <li>Select <strong>"Expired"</strong></li>
                <li>Enter the close date (defaults to expiration date)</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
              <p>You keep the premium and your shares. The shares are returned to your available stock position.</p>
            </div>

            <div className="sub-step">
              <h5>Option 3: Assigned</h5>
              <ol>
                <li>Click <strong>"Close"</strong> on your open covered call</li>
                <li>Select <strong>"Assigned"</strong></li>
                <li>Enter the assignment date (defaults to expiration date)</li>
                <li>Click <strong>"Close Trade"</strong></li>
              </ol>
              <p>Your shares are sold at the strike price. The system automatically updates your stock position to reflect the reduced shares.</p>
            </div>
          </div>
        </div>
      )
    },
    {
      id: 'stock-positions',
      title: '💼 Stock Positions',
      icon: '💼',
      content: (
        <div className="guide-content">
          <h3>How to Manage Stock Positions</h3>
          <p>Stock positions represent shares you own. They can be created automatically from CSP assignments or LEAPS exercises, or added manually.</p>
          
          <div className="step-section">
            <h4>Viewing Stock Positions</h4>
            <ol>
              <li>Go to the <strong>Positions</strong> page</li>
              <li>Click on the <strong>"Stocks"</strong> tab</li>
              <li>You'll see all your stock positions with:
                <ul>
                  <li>Symbol and company logo</li>
                  <li>Total shares</li>
                  <li>Shares used by covered calls</li>
                  <li>Available shares</li>
                  <li>Average cost basis</li>
                  <li>Current market price</li>
                  <li>Unrealized P&L</li>
                </ul>
              </li>
            </ol>
          </div>

          <div className="step-section">
            <h4>Adding a Stock Position Manually</h4>
            <ol>
              <li>Go to <strong>Positions</strong> → <strong>Stocks</strong> tab</li>
              <li>Click <strong>"Add Stock Position"</strong></li>
              <li>Fill in the details:
                <ul>
                  <li><strong>Account:</strong> Select the account</li>
                  <li><strong>Symbol:</strong> Enter the stock ticker</li>
                  <li><strong>Quantity:</strong> Number of shares</li>
                  <li><strong>Cost Basis:</strong> Average price per share you paid</li>
                  <li><strong>Purchase Date:</strong> When you acquired the shares</li>
                </ul>
              </li>
              <li>Click <strong>"Create"</strong></li>
            </ol>
            <div className="tip-box">
              <strong>💡 Tip:</strong> Stock positions are automatically created when:
              <ul>
                <li>A CSP is assigned (shares purchased at strike price)</li>
                <li>A LEAPS is exercised (shares purchased at strike price)</li>
              </ul>
              You typically only need to add positions manually if you bought shares directly or transferred them from another account.
            </div>
          </div>

          <div className="step-section">
            <h4>Editing or Deleting Stock Positions</h4>
            <ol>
              <li>Find the stock position in the <strong>Stocks</strong> tab</li>
              <li>Click the <strong>Edit</strong> icon (✏️) to modify details</li>
              <li>Click the <strong>Delete</strong> icon (🗑️) to remove the position</li>
            </ol>
            <div className="warning-box">
              <strong>⚠️ Warning:</strong> You cannot delete a stock position that has active covered calls. Close all covered calls first, then you can delete the position.
            </div>
          </div>

          <div className="step-section">
            <h4>Understanding Available Shares</h4>
            <p>The system automatically tracks:</p>
            <ul>
              <li><strong>Total Shares:</strong> All shares you own in this position</li>
              <li><strong>Shares Used:</strong> Shares currently tied up in open covered calls</li>
              <li><strong>Available Shares:</strong> Shares available to write new covered calls against</li>
            </ul>
            <p>When you close a covered call (buy to close or expired), the shares are immediately returned to your available shares.</p>
          </div>
        </div>
      )
    },
    {
      id: 'dashboard',
      title: '📊 Dashboard Analytics',
      icon: '📊',
      content: (
        <div className="guide-content">
          <h3>Using the Dashboard for Analytics</h3>
          <p>The Dashboard provides comprehensive analytics to help you track your trading performance.</p>
          
          <div className="step-section">
            <h4>Market Data</h4>
            <p>At the top of the Dashboard, you'll see real-time market data for:</p>
            <ul>
              <li><strong>SPY:</strong> S&P 500 ETF</li>
              <li><strong>QQQ:</strong> Nasdaq-100 ETF</li>
              <li><strong>DIA:</strong> Dow Jones ETF</li>
              <li><strong>VIX:</strong> Volatility Index</li>
            </ul>
            <p>These prices update automatically and help you gauge market conditions.</p>
          </div>

          <div className="step-section">
            <h4>Account Summary</h4>
            <p>The Account Summary section shows:</p>
            <ul>
              <li><strong>Total Capital:</strong> Sum of all account balances</li>
              <li><strong>Allocated Capital:</strong> Capital tied up in open positions</li>
              <li><strong>Available Capital:</strong> Capital available for new trades</li>
            </ul>
            <p>Use the <strong>Account</strong> filter to view data for a specific account.</p>
          </div>

          <div className="step-section">
            <h4>P&L Metrics</h4>
            <p>The P&L section displays:</p>
            <ul>
              <li><strong>Total P&L:</strong> Combined profit/loss from all closed trades</li>
              <li><strong>Return %:</strong> Percentage return on your capital</li>
              <li><strong>Monthly Returns:</strong> Returns broken down by month</li>
            </ul>
            <p>Use the <strong>Time Period</strong> filter to view P&L for specific date ranges (Last 7 Days, Last 30 Days, Last 90 Days, YTD, All Time).</p>
          </div>

          <div className="step-section">
            <h4>Position Details</h4>
            <p>The Position Details table shows all your open positions with:</p>
            <ul>
              <li>Company logos and symbols</li>
              <li>Trade type (CSP, Covered Call, LEAPS)</li>
              <li>Strike prices and expiration dates</li>
              <li>Contract quantities</li>
              <li>Unrealized P&L</li>
            </ul>
            <p>This gives you a quick overview of all your active positions at a glance.</p>
          </div>

          <div className="step-section">
            <h4>Using Filters</h4>
            <p>The Dashboard has three main filters:</p>
            <ol>
              <li><strong>Account:</strong> Filter by specific account or view all accounts</li>
              <li><strong>Time Period:</strong> Filter P&L and returns by date range</li>
              <li><strong>Monthly Returns:</strong> Toggle to show/hide monthly return breakdown</li>
            </ol>
            <p>These filters help you analyze performance for specific accounts or time periods.</p>
          </div>
        </div>
      )
    },
    {
      id: 'other-features',
      title: '🔧 Other Features',
      icon: '🔧',
      content: (
        <div className="guide-content">
          <h3>Additional Features and Tips</h3>
          
          <div className="step-section">
            <h4>Exporting and Importing Trades</h4>
            <p>You can export your trades to CSV or Excel format:</p>
            <ol>
              <li>Go to the <strong>Trades</strong> page</li>
              <li>Click <strong>"Export CSV"</strong> or <strong>"Export Excel"</strong></li>
              <li>The file will download with all your trade data</li>
            </ol>
            <p>To import trades:</p>
            <ol>
              <li>Click <strong>"Import"</strong> on the Trades page</li>
              <li>Select a CSV or Excel file</li>
              <li>The system will import all trades from the file</li>
            </ol>
            <div className="tip-box">
              <strong>💡 Tip:</strong> The import feature supports both old format (separate open/close entries) and new format (single entry with close details). The system automatically handles both.
            </div>
          </div>

          <div className="step-section">
            <h4>Editing Trades</h4>
            <p>You can edit any trade after it's been created:</p>
            <ol>
              <li>Find the trade in the <strong>Trades</strong> table</li>
              <li>Click the <strong>Edit</strong> icon (✏️)</li>
              <li>Modify any fields (including account and trade type)</li>
              <li>For closed trades, you can also edit close details (price, fees, date, method)</li>
              <li>Click <strong>"Update"</strong></li>
            </ol>
            <p>The system automatically recalculates P&L, return percentage, and days held when you update a trade.</p>
          </div>

          <div className="step-section">
            <h4>Partial Closes and History</h4>
            <p>If you partially close a trade (e.g., close 2 out of 5 contracts):</p>
            <ul>
              <li>The system creates a new closing entry for the partial close</li>
              <li>The original trade shows the remaining open quantity</li>
              <li>Click the <strong>"History"</strong> button to see all partial closes for that trade</li>
            </ul>
            <p>The History dialog shows each close method, date, quantity, and individual P&L.</p>
          </div>

          <div className="step-section">
            <h4>Account Management</h4>
            <p>You can manage your accounts:</p>
            <ul>
              <li><strong>Edit:</strong> Click the edit icon (✏️) to change account name, type, initial balance, or default fee</li>
              <li><strong>Add Deposits:</strong> Record money added to an account</li>
              <li><strong>Add Withdrawals:</strong> Record money removed from an account</li>
              <li><strong>Delete:</strong> Click the delete icon (🗑️) to remove an account (all associated trades will be deleted)</li>
            </ul>
          </div>

          <div className="step-section">
            <h4>Positions Page</h4>
            <p>The Positions page has two tabs:</p>
            <ul>
              <li><strong>Options:</strong> Shows all open options positions (CSP, Covered Calls, LEAPS)</li>
              <li><strong>Stocks:</strong> Shows all stock positions</li>
            </ul>
            <p>Each position shows detailed information including P&L, fees, premiums, and more.</p>
          </div>

          <div className="step-section">
            <h4>Tools Page</h4>
            <p>The Tools page includes:</p>
            <ul>
              <li><strong>VIX Cash Allocation Calculator:</strong> Helps you determine how much capital to allocate based on VIX levels</li>
            </ul>
            <p>More tools may be added in future updates!</p>
          </div>
        </div>
      )
    }
  ];

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="container">
        <h1>How to Use Options Tracker</h1>
        <p className="guide-intro">
          Welcome to the interactive guide! Click on any section below to expand it and learn step-by-step instructions for using Options Tracker.
        </p>

        <div className="guide-sections">
          {sections.map((section) => (
            <div key={section.id} className={`guide-section ${expandedSection === section.id ? 'expanded' : ''}`}>
              <button
                className="guide-section-header"
                onClick={() => toggleSection(section.id)}
                aria-expanded={expandedSection === section.id}
              >
                <span className="guide-section-icon">{section.icon}</span>
                <span className="guide-section-title">{section.title}</span>
                <span className="guide-section-arrow">
                  {expandedSection === section.id ? '▼' : '▶'}
                </span>
              </button>
              {expandedSection === section.id && (
                <div className="guide-section-content">
                  {section.content}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}

export default HowToUse;

