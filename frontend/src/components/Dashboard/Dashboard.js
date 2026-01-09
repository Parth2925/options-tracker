import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import Footer from '../Layout/Footer';
import { useTheme } from '../../contexts/ThemeContext';
import api from '../../utils/api';
import './Dashboard.css';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js';
import { Pie } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

function Dashboard() {
  const { isDarkMode } = useTheme();
  const [summary, setSummary] = useState(null);
  const [monthlyReturns, setMonthlyReturns] = useState(null);
  const [openPositions, setOpenPositions] = useState(null);
  const [strategyPerformance, setStrategyPerformance] = useState([]);
  const [tickerPerformance, setTickerPerformance] = useState([]);
  const [marketIndices, setMarketIndices] = useState({});
  const [positionQuotes, setPositionQuotes] = useState({});
  const [companyLogos, setCompanyLogos] = useState({});
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('all');
  const [monthsBack, setMonthsBack] = useState(12);

  useEffect(() => {
    loadAccounts();
    // Load market data even if no accounts (useful for everyone)
    loadMarketData();
  }, []);

  useEffect(() => {
    if (accounts.length > 0) {
      loadSummary();
      loadMonthlyReturns();
      loadOpenPositions();
      loadStrategyPerformance();
      loadTickerPerformance();
    }
    // If no accounts, summary is already set in loadAccounts
  }, [selectedAccount, period, accounts, monthsBack]);

  useEffect(() => {
    // Load logos when openPositions changes
    // Use merge pattern to preserve logos from ticker performance
    if (openPositions && openPositions.positions && openPositions.positions.length > 0) {
      const symbols = [...new Set(openPositions.positions.map(p => p.symbol))].filter(Boolean);
      if (symbols.length > 0) {
        const loadLogos = async () => {
          try {
            const params = { symbols: symbols.join(',') };
            const response = await api.get('/dashboard/company-logos', { params });
            if (response.data && response.data.logos) {
              // Merge with existing logos instead of replacing
              setCompanyLogos(prev => ({ ...prev, ...response.data.logos }));
            }
          } catch (error) {
            console.error('Error loading company logos:', error);
          }
        };
        loadLogos();
      }
    }
  }, [openPositions]);

  // Auto-refresh market data every 5 minutes
  useEffect(() => {
    loadMarketData();
    const interval = setInterval(() => {
      loadMarketData();
    }, 5 * 60 * 1000); // 5 minutes
    
    return () => clearInterval(interval);
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await api.get('/accounts');
      const accountsData = response.data || [];
      setAccounts(accountsData);
      if (accountsData.length > 0 && !selectedAccount) {
        setSelectedAccount('all');
      } else if (accountsData.length === 0) {
        // No accounts - set loading to false and create empty summary
        setLoading(false);
        setSummary({
          total_accounts: 0,
          total_trades: 0,
          open_positions: 0,
          closed_positions: 0,
          pnl: {
            week: { realized_pnl: 0, unrealized_pnl: 0, total_pnl: 0, rate_of_return: 0 },
            month: { realized_pnl: 0, unrealized_pnl: 0, total_pnl: 0, rate_of_return: 0 },
            ytd: { realized_pnl: 0, unrealized_pnl: 0, total_pnl: 0, rate_of_return: 0 },
            year: { realized_pnl: 0, unrealized_pnl: 0, total_pnl: 0, rate_of_return: 0 },
            all: { realized_pnl: 0, unrealized_pnl: 0, total_pnl: 0, rate_of_return: 0 }
          }
        });
      }
    } catch (error) {
      console.error('Error loading accounts:', error);
      setLoading(false);
    }
  };

  const loadSummary = async () => {
    setLoading(true);
    try {
      const params = { period };
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/dashboard/summary', { params });
      setSummary(response.data);
    } catch (error) {
      console.error('Error loading summary:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMonthlyReturns = async () => {
    try {
      const params = { months: monthsBack };
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/dashboard/monthly-returns', { params });
      setMonthlyReturns(response.data);
    } catch (error) {
      console.error('Error loading monthly returns:', error);
    }
  };

  const loadOpenPositions = async () => {
    try {
      const params = {};
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/dashboard/open-positions-allocation', { params });
      setOpenPositions(response.data);
      
      // Load market data for positions after positions are loaded
      if (response.data && response.data.positions && response.data.positions.length > 0) {
        loadPositionMarketData();
      }
    } catch (error) {
      console.error('Error loading open positions:', error);
    }
  };

  const loadStrategyPerformance = async () => {
    try {
      const params = { period };
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/dashboard/strategy-performance', { params });
      setStrategyPerformance(response.data || []);
    } catch (error) {
      console.error('Error loading strategy performance:', error);
      setStrategyPerformance([]);
    }
  };

  const loadTickerPerformance = async () => {
    try {
      const params = { period };
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/dashboard/ticker-performance', { params });
      setTickerPerformance(response.data || []);
      
      // Load logos for ticker performance symbols
      // Always load logos - merge pattern ensures no duplicates
      if (response.data && response.data.length > 0) {
        const symbols = [...new Set(response.data.map(t => t.symbol))].filter(Boolean);
        if (symbols.length > 0) {
          try {
            const logoParams = { symbols: symbols.join(',') };
            const logoResponse = await api.get('/dashboard/company-logos', { params: logoParams });
            if (logoResponse.data && logoResponse.data.logos) {
              // Merge with existing logos (from openPositions or previous loads)
              // This ensures logos from both sources are preserved
              setCompanyLogos(prev => ({ ...prev, ...logoResponse.data.logos }));
            }
          } catch (error) {
            console.error('Error loading ticker performance logos:', error);
            // Retry once after a short delay to handle transient network issues
            setTimeout(async () => {
              try {
                const logoParams = { symbols: symbols.join(',') };
                const logoResponse = await api.get('/dashboard/company-logos', { params: logoParams });
                if (logoResponse.data && logoResponse.data.logos) {
                  setCompanyLogos(prev => ({ ...prev, ...logoResponse.data.logos }));
                }
              } catch (retryError) {
                console.error('Error loading ticker performance logos (retry failed):', retryError);
              }
            }, 1000);
          }
        }
      }
    } catch (error) {
      console.error('Error loading ticker performance:', error);
      setTickerPerformance([]);
    }
  };

  const loadMarketData = async () => {
    try {
      const params = { include_indices: 'true' };
      const response = await api.get('/dashboard/market-data', { params });
      if (response.data && response.data.indices) {
        setMarketIndices(response.data.indices);
      }
    } catch (error) {
      console.error('Error loading market indices:', error);
    }
  };

  const loadPositionMarketData = async () => {
    try {
      const params = {};
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/dashboard/market-data/positions', { params });
      if (response.data && response.data.quotes) {
        setPositionQuotes(response.data.quotes);
      }
    } catch (error) {
      console.error('Error loading position market data:', error);
    }
  };

  const loadCompanyLogos = async () => {
    try {
      if (!openPositions || !openPositions.positions || openPositions.positions.length === 0) {
        return;
      }

      // Get unique symbols from open positions
      const symbols = [...new Set(openPositions.positions.map(p => p.symbol))].filter(Boolean);
      
      if (symbols.length === 0) {
        return;
      }

      const params = { symbols: symbols.join(',') };
      const response = await api.get('/dashboard/company-logos', { params });
      
      if (response.data && response.data.logos) {
        setCompanyLogos(response.data.logos);
      }
    } catch (error) {
      console.error('Error loading company logos:', error);
    }
  };

  // Only show loading if we're actually loading data
  if (loading && accounts.length === 0) {
    return (
      <div className="page-wrapper">
        <Navbar />
        <div className="container">
          <div className="loading">Loading dashboard...</div>
        </div>
        <Footer />
      </div>
    );
  }

  const pnl = summary?.pnl?.[period] || {};
  const isPositive = pnl.total_pnl >= 0;

  return (
    <div className="page-wrapper">
      <Navbar />
      <div className="container">
        <h1>Dashboard</h1>
        
        {/* Market Indices (CNBC Style) */}
        {Object.keys(marketIndices).length > 0 && (
          <div className="market-indices-grid">
            {['DIA', 'SPY', 'QQQ', 'VIX'].map((index) => {
              const data = marketIndices[index];
              if (!data) return null;
              
              const isPositive = data.change >= 0;
              const indexNames = {
                'SPY': 'S&P 500',
                'DIA': 'DJIA',
                'QQQ': 'NASDAQ',
                'VIX': 'VIX'
              };
              
              // Color entire box background based on price change
              const backgroundColor = isPositive ? '#d4edda' : '#f8d7da';
              const textColor = isPositive ? '#155724' : '#721c24';
              const borderColor = isPositive ? '#28a745' : '#dc3545';
              
              return (
                <div 
                  key={index}
                  className="market-index-box"
                  style={{
                    backgroundColor: backgroundColor,
                    border: `2px solid ${borderColor}`,
                    color: textColor
                  }}
                >
                  <div className="market-index-name">
                    {indexNames[index] || index}
                  </div>
                  <div className="market-index-price">
                    ${data.current_price.toFixed(2)}
                  </div>
                  <div className="market-index-change">
                    {isPositive ? '+' : ''}{data.change.toFixed(2)} ({isPositive ? '+' : ''}{data.change_percent.toFixed(2)}%)
                  </div>
                </div>
              );
            })}
          </div>
        )}
        
        {/* Empty State for New Users */}
        {accounts.length === 0 && !loading && (
          <div className="card" style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            backgroundColor: 'var(--bg-secondary)',
            border: '2px dashed var(--border-color)',
            borderRadius: '8px',
            marginBottom: '30px'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
            <h2 style={{ marginBottom: '15px', color: 'var(--text-primary)' }}>Welcome to Options Tracker!</h2>
            <p style={{ 
              fontSize: '16px', 
              color: 'var(--text-secondary)', 
              marginBottom: '30px',
              maxWidth: '600px',
              margin: '0 auto 30px'
            }}>
              Get started by creating your first trading account and adding your options trades. 
              Track your performance, monitor your positions, and analyze your returns.
            </p>
            <div style={{ 
              display: 'flex', 
              gap: '15px', 
              justifyContent: 'center',
              flexWrap: 'wrap'
            }}>
              <Link to="/accounts" className="btn btn-primary" style={{ padding: '12px 24px', fontSize: '16px', textDecoration: 'none' }}>
                Create Your First Account
              </Link>
              <Link to="/trades" className="btn btn-secondary" style={{ padding: '12px 24px', fontSize: '16px', textDecoration: 'none' }}>
                View Trades
              </Link>
            </div>
            <div style={{ 
              marginTop: '30px', 
              padding: '20px',
              backgroundColor: 'var(--bg-tertiary)',
              borderRadius: '6px',
              textAlign: 'left',
              maxWidth: '500px',
              margin: '30px auto 0'
            }}>
              <h3 style={{ fontSize: '18px', marginBottom: '15px', color: 'var(--text-primary)' }}>Quick Start Guide:</h3>
              <ol style={{ 
                color: 'var(--text-secondary)', 
                lineHeight: '1.8',
                paddingLeft: '20px',
                margin: 0
              }}>
                <li>Create a trading account (e.g., "IRA", "Taxable", "Margin")</li>
                <li>Add your initial account balance</li>
                <li>Start adding your options trades (CSP, Covered Calls, LEAPS, etc.)</li>
                <li>View your performance on the Dashboard</li>
              </ol>
            </div>
          </div>
        )}
        
        {/* Dashboard Controls - Only show if user has accounts */}
        {accounts.length > 0 && (
          <div className="dashboard-controls">
            <div className="dashboard-filter-group">
              <label>Account</label>
              <select
                value={selectedAccount || 'all'}
                onChange={(e) => setSelectedAccount(e.target.value)}
              >
                <option value="all">All Accounts</option>
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="dashboard-filter-group">
              <label>Time Period</label>
              <select value={period} onChange={(e) => setPeriod(e.target.value)}>
                <option value="week">1 Week</option>
                <option value="month">1 Month</option>
                <option value="ytd">Year to Date</option>
                <option value="year">1 Year</option>
                <option value="last_year">Last Year</option>
                <option value="all">All Time</option>
              </select>
            </div>
            
            <div className="dashboard-filter-group">
              <label>Monthly Returns</label>
              <select value={monthsBack} onChange={(e) => setMonthsBack(parseInt(e.target.value))}>
                <option value="6">Last 6 Months</option>
                <option value="12">Last 12 Months</option>
                <option value="24">Last 24 Months</option>
                <option value="36">Last 36 Months</option>
              </select>
            </div>
          </div>
        )}

        {/* Metrics - Only show if user has accounts */}
        {accounts.length > 0 && summary && (
          <div className="metrics-grid">
            <div className={`metric-card ${isPositive ? 'positive' : 'negative'}`}>
              <h3>Total P&L</h3>
              <div className="value">
                ${pnl.total_pnl?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </div>
            </div>
            
            <div className="metric-card">
              <h3>Realized P&L</h3>
              <div className="value">
                ${pnl.realized_pnl?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </div>
            </div>
            
            <div className="metric-card">
              <h3>Unrealized P&L</h3>
              <div className="value">
                ${pnl.unrealized_pnl?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
              </div>
            </div>
            
            <div className="metric-card">
              <h3>Rate of Return</h3>
              <div className="value">
                {pnl.rate_of_return?.toFixed(2) || '0.00'}%
              </div>
            </div>
          </div>
        )}

        {/* Open Positions Snapshot */}
        {openPositions && openPositions.positions && openPositions.positions.length > 0 && (
          <div className="card">
            <h2>Open Positions Allocation</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '30px', marginTop: '20px' }}>
              {/* Pie Chart */}
              <div>
                <h3 style={{ marginBottom: '20px', fontSize: '18px' }}>Portfolio Allocation by Symbol</h3>
                {(() => {
                  const chartData = {
                    labels: openPositions.positions.map(p => p.symbol),
                    datasets: [{
                      label: 'Capital at Risk',
                      data: openPositions.positions.map(p => p.capital_at_risk),
                      backgroundColor: [
                        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
                        '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
                      ],
                      borderColor: '#fff',
                      borderWidth: 2
                    }]
                  };
                  
                  const options = {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                      legend: {
                        position: 'right',
                        labels: {
                          padding: 15,
                          font: {
                            size: 12
                          },
                          color: isDarkMode ? '#e0e0e0' : '#333'
                        }
                      },
                      tooltip: {
                        callbacks: {
                          label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(2);
                            return `${label}: $${value.toLocaleString('en-US', { minimumFractionDigits: 2 })} (${percentage}%)`;
                          }
                        }
                      }
                    }
                  };
                  
                  return <Pie data={chartData} options={options} />;
                })()}
              </div>
              
              {/* Positions Table */}
              <div>
                <h3 style={{ marginBottom: '20px', fontSize: '18px' }}>Position Details</h3>
                <div className="table-wrapper">
                  <table className="position-details-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', tableLayout: 'fixed' }}>
                    <thead>
                      <tr style={{ 
                        backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa', 
                        borderBottom: `2px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}` 
                      }}>
                        <th style={{ padding: '8px 4px', textAlign: 'left', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', width: '14%' }}>Symbol</th>
                        <th style={{ padding: '8px 4px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', width: '17%' }}>Spot Price</th>
                        <th style={{ padding: '8px 4px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', width: '22%' }}>Capital at Risk</th>
                        <th style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', width: '18%' }}>Allocation %</th>
                        <th style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', width: '12%' }}>Contracts</th>
                        <th style={{ padding: '8px 4px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', width: '17%' }}>Positions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {openPositions.positions.map((position, index) => {
                        const quote = positionQuotes[position.symbol];
                        const isPositive = quote ? quote.change >= 0 : null;
                        
                        return (
                          <tr 
                            key={position.symbol}
                            style={{ 
                              borderBottom: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`,
                              backgroundColor: index % 2 === 0 
                                ? (isDarkMode ? 'var(--bg-secondary)' : '#fff')
                                : (isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa')
                            }}
                          >
                            <td style={{ padding: '8px 4px', fontWeight: '500', color: 'var(--text-primary)' }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                                {companyLogos[position.symbol] && (
                                  <img 
                                    src={companyLogos[position.symbol]} 
                                    alt={`${position.symbol} logo`}
                                    style={{ 
                                      width: '20px', 
                                      height: '20px', 
                                      objectFit: 'contain',
                                      borderRadius: '4px',
                                      flexShrink: 0
                                    }}
                                    onError={(e) => {
                                      // Hide image if it fails to load
                                      e.target.style.display = 'none';
                                    }}
                                  />
                                )}
                                <span style={{ whiteSpace: 'nowrap' }}>{position.symbol}</span>
                              </div>
                            </td>
                            <td style={{ padding: '8px 4px', textAlign: 'right', whiteSpace: 'nowrap' }}>
                              {quote ? (
                                <div>
                                  <div style={{ 
                                    fontWeight: 'bold',
                                    color: isPositive ? '#28a745' : '#dc3545',
                                    fontSize: '13px'
                                  }}>
                                    ${quote.current_price.toFixed(2)}
                                  </div>
                                  <div style={{ 
                                    fontSize: '10px',
                                    color: isPositive ? '#28a745' : '#dc3545'
                                  }}>
                                    {isPositive ? '+' : ''}{quote.change.toFixed(2)} ({isPositive ? '+' : ''}{quote.change_percent.toFixed(2)}%)
                                  </div>
                                </div>
                              ) : (
                                <span style={{ color: 'var(--text-secondary)', fontSize: '10px' }}>Loading...</span>
                              )}
                            </td>
                            <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--text-primary)', whiteSpace: 'nowrap', fontSize: '12px' }}>
                              ${position.capital_at_risk.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </td>
                            <td style={{ padding: '8px 6px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)', whiteSpace: 'nowrap', fontSize: '13px' }}>
                              {position.allocation_percentage.toFixed(2)}%
                            </td>
                            <td style={{ padding: '8px 4px', textAlign: 'center', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>{position.contract_quantity}</td>
                            <td style={{ padding: '8px 4px', textAlign: 'center', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>{position.position_count}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                    <tfoot>
                      <tr style={{ 
                        backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#e9ecef', 
                        fontWeight: 'bold', 
                        borderTop: `2px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}` 
                      }}>
                        <td style={{ padding: '8px 4px', color: 'var(--text-primary)' }}>Total</td>
                        <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--text-primary)' }}>-</td>
                        <td style={{ padding: '8px 4px', textAlign: 'right', color: 'var(--text-primary)', whiteSpace: 'nowrap', fontSize: '12px' }}>
                          ${openPositions.total_capital_at_risk.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </td>
                        <td style={{ padding: '8px 6px', textAlign: 'right', color: 'var(--text-primary)', whiteSpace: 'nowrap', fontSize: '13px' }}>
                          {((openPositions.total_capital_at_risk / openPositions.total_capital) * 100).toFixed(2)}%
                        </td>
                        <td style={{ padding: '8px 4px', textAlign: 'center', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                          {openPositions.positions.reduce((sum, p) => sum + p.contract_quantity, 0)}
                        </td>
                        <td style={{ padding: '8px 4px', textAlign: 'center', color: 'var(--text-primary)', whiteSpace: 'nowrap' }}>
                          {openPositions.positions.reduce((sum, p) => sum + p.position_count, 0)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
                {openPositions.unallocated_capital > 0 && (
                  <div style={{ 
                    marginTop: '15px', 
                    padding: '10px', 
                    backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa', 
                    borderRadius: '4px', 
                    fontSize: '14px',
                    color: 'var(--text-primary)',
                    border: isDarkMode ? `1px solid var(--border-color)` : 'none'
                  }}>
                    <strong>Capital Not in Open Options Positions:</strong> ${openPositions.unallocated_capital.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    <span style={{ color: 'var(--text-secondary)', marginLeft: '10px' }}>
                      ({((openPositions.unallocated_capital / openPositions.total_capital) * 100).toFixed(2)}% of portfolio)
                    </span>
                    <div style={{ 
                      marginTop: '5px', 
                      fontSize: '12px', 
                      color: 'var(--text-secondary)', 
                      fontStyle: 'italic' 
                    }}>
                      Note: This capital may be tied up in assigned stocks or other positions. It does not represent available cash.
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {openPositions && (!openPositions.positions || openPositions.positions.length === 0) && (
          <div className="card">
            <h2>Open Positions Allocation</h2>
            <p style={{ color: '#666', marginTop: '20px' }}>
              No open positions found. Open positions are calculated based on opening trades that haven't been fully closed.
            </p>
          </div>
        )}

        {/* Summary Stats - Only show if user has accounts */}
        {accounts.length > 0 && summary && (
          <div className="card">
            <h2>Summary</h2>
            <div className="summary-grid">
              <div className="summary-item">
                <span className="summary-label">Total Accounts:</span>
                <span className="summary-value">{summary?.total_accounts || 0}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Total Trades:</span>
                <span className="summary-value">{summary?.total_trades || 0}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Open Positions:</span>
                <span className="summary-value">{summary?.open_positions || 0}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Closed Positions:</span>
                <span className="summary-value">{summary?.closed_positions || 0}</span>
              </div>
            </div>
          </div>
        )}

        {/* Year-to-Date Return - Only show if user has accounts */}
        {accounts.length > 0 && monthlyReturns && (
          <div className="card">
            <h2>Year-to-Date (YTD) Return - {monthlyReturns.ytd?.year}</h2>
            <div className="metrics-grid" style={{ marginTop: '20px' }}>
              <div className={`metric-card ${monthlyReturns.ytd?.total_return >= 0 ? 'positive' : 'negative'}`}>
                <h3>YTD Total Return</h3>
                <div className="value">
                  ${monthlyReturns.ytd?.total_return?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0.00'}
                </div>
              </div>
              <div className={`metric-card ${monthlyReturns.ytd?.return_percentage >= 0 ? 'positive' : 'negative'}`}>
                <h3>YTD Return %</h3>
                <div className="value">
                  {monthlyReturns.ytd?.return_percentage?.toFixed(2) || '0.00'}%
                </div>
              </div>
              <div className="metric-card">
                <h3>YTD Trades</h3>
                <div className="value">
                  {monthlyReturns.ytd?.trade_count || 0}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Monthly Returns Table - Only show if user has accounts */}
        {accounts.length > 0 && monthlyReturns && monthlyReturns.monthly_returns && monthlyReturns.monthly_returns.length > 0 && (
          <div className="card">
            <h2>Monthly Returns</h2>
            <div style={{ overflowX: 'auto', marginTop: '20px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8f9fa', borderBottom: '2px solid #dee2e6' }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold' }}>Month</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>Total Return</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold' }}>Return %</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold' }}>Trades</th>
                  </tr>
                </thead>
                <tbody>
                  {monthlyReturns.monthly_returns.map((month, index) => (
                    <tr 
                      key={`${month.year}-${month.month}`}
                      style={{ 
                        borderBottom: '1px solid #dee2e6',
                        backgroundColor: index % 2 === 0 ? '#fff' : '#f8f9fa'
                      }}
                    >
                      <td style={{ padding: '12px', fontWeight: '500' }}>
                        {month.year_month}
                      </td>
                      <td 
                        style={{ 
                          padding: '12px', 
                          textAlign: 'right',
                          color: month.total_return >= 0 ? '#28a745' : '#dc3545',
                          fontWeight: 'bold'
                        }}
                      >
                        ${month.total_return.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td 
                        style={{ 
                          padding: '12px', 
                          textAlign: 'right',
                          color: month.return_percentage >= 0 ? '#28a745' : '#dc3545',
                          fontWeight: 'bold'
                        }}
                      >
                        {month.return_percentage.toFixed(2)}%
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        {month.trade_count}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {accounts.length > 0 && monthlyReturns && (!monthlyReturns.monthly_returns || monthlyReturns.monthly_returns.length === 0) && (
          <div className="card">
            <h2>Monthly Returns</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '20px' }}>
              No monthly returns data available for the selected period. Returns are calculated based on when trades were closed.
            </p>
          </div>
        )}

        {/* Strategy Performance */}
        {strategyPerformance && strategyPerformance.length > 0 && (
          <div className="card">
            <h2>Strategy Performance</h2>
            <div className="table-wrapper" style={{ marginTop: '20px', overflowX: 'auto' }}>
              <table className="strategy-performance-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ 
                    backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa', 
                    borderBottom: `2px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}` 
                  }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold', color: 'var(--text-primary)' }}>Strategy</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)' }}>Trades</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)' }}>Win Rate</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)' }}>Total P&L</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)' }}>% of Profit</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)' }}>Open</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)' }}>Open Premium</th>
                  </tr>
                </thead>
                <tbody>
                  {strategyPerformance.map((strategy, index) => (
                    <tr 
                      key={strategy.strategy}
                      style={{ 
                        borderBottom: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`,
                        backgroundColor: index % 2 === 0 
                          ? (isDarkMode ? 'var(--bg-secondary)' : '#fff')
                          : (isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa')
                      }}
                    >
                      <td style={{ padding: '12px', fontWeight: '500', color: 'var(--text-primary)' }}>
                        {strategy.strategy}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: 'var(--text-primary)' }}>
                        {strategy.trades}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: 'var(--text-primary)' }}>
                        {strategy.win_rate.toFixed(1)}%
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'right',
                        color: strategy.total_pnl >= 0 ? '#28a745' : '#dc3545',
                        fontWeight: 'bold'
                      }}>
                        ${strategy.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: 'var(--text-primary)' }}>
                        {strategy.percent_of_profit.toFixed(1)}%
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: 'var(--text-primary)' }}>
                        {strategy.open_contracts}
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'right',
                        color: strategy.open_premium >= 0 ? '#28a745' : '#dc3545'
                      }}>
                        ${strategy.open_premium.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {accounts.length > 0 && strategyPerformance && strategyPerformance.length === 0 && (
          <div className="card">
            <h2>Strategy Performance</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '20px' }}>
              No strategy performance data available. Start trading to see performance metrics by strategy.
            </p>
          </div>
        )}

        {/* Ticker Performance */}
        {tickerPerformance && tickerPerformance.length > 0 && (
          <div className="card">
            <h2>Ticker Performance</h2>
            <div className="table-wrapper" style={{ marginTop: '20px', overflowX: 'auto' }}>
              <table className="ticker-performance-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ 
                    backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa', 
                    borderBottom: `2px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}` 
                  }}>
                    <th style={{ padding: '12px', textAlign: 'left', fontWeight: 'bold', color: 'var(--text-primary)' }}>Ticker</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)' }}>Trades</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)' }}>Win Rate</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)' }}>Total P&L</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)' }}>% of Profit</th>
                    <th style={{ padding: '12px', textAlign: 'center', fontWeight: 'bold', color: 'var(--text-primary)' }}>Open</th>
                    <th style={{ padding: '12px', textAlign: 'right', fontWeight: 'bold', color: 'var(--text-primary)' }}>Open Premium</th>
                  </tr>
                </thead>
                <tbody>
                  {tickerPerformance.map((ticker, index) => (
                    <tr 
                      key={ticker.symbol}
                      style={{ 
                        borderBottom: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`,
                        backgroundColor: index % 2 === 0 
                          ? (isDarkMode ? 'var(--bg-secondary)' : '#fff')
                          : (isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa')
                      }}
                    >
                      <td style={{ padding: '12px', fontWeight: '500', color: 'var(--text-primary)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {companyLogos[ticker.symbol] && (
                            <img 
                              src={companyLogos[ticker.symbol]} 
                              alt={ticker.symbol}
                              style={{ width: '24px', height: '24px', borderRadius: '4px' }}
                              onError={(e) => { e.target.style.display = 'none'; }}
                            />
                          )}
                          <span>{ticker.symbol}</span>
                        </div>
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: 'var(--text-primary)' }}>
                        {ticker.trades}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: 'var(--text-primary)' }}>
                        {ticker.win_rate.toFixed(1)}%
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'right',
                        color: ticker.total_pnl >= 0 ? '#28a745' : '#dc3545',
                        fontWeight: 'bold'
                      }}>
                        ${ticker.total_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: 'var(--text-primary)' }}>
                        {ticker.percent_of_profit.toFixed(1)}%
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center', color: 'var(--text-primary)' }}>
                        {ticker.open_contracts}
                      </td>
                      <td style={{ 
                        padding: '12px', 
                        textAlign: 'right',
                        color: ticker.open_premium >= 0 ? '#28a745' : '#dc3545'
                      }}>
                        ${ticker.open_premium.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {accounts.length > 0 && tickerPerformance && tickerPerformance.length === 0 && (
          <div className="card">
            <h2>Ticker Performance</h2>
            <p style={{ color: 'var(--text-secondary)', marginTop: '20px' }}>
              No ticker performance data available. Start trading to see performance metrics by ticker.
            </p>
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}

export default Dashboard;

