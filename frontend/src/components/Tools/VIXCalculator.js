import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { useTheme } from '../../contexts/ThemeContext';
import './VIXCalculator.css';

function VIXCalculator() {
  const { isDarkMode } = useTheme();
  const [vixPrice, setVixPrice] = useState(null);
  const [accounts, setAccounts] = useState([]);
  const [customBalance, setCustomBalance] = useState('');
  const [viewMode, setViewMode] = useState('all'); // 'all', 'individual', 'custom'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVIXPrice();
    loadAccounts();
  }, []);

  const loadVIXPrice = async () => {
    try {
      const response = await api.get('/dashboard/market-data', { 
        params: { include_indices: 'true' } 
      });
      if (response.data && response.data.indices && response.data.indices.VIX) {
        const vixData = response.data.indices.VIX;
        // VIX data structure: { current_price, change, change_percent, ... }
        setVixPrice(vixData.current_price || vixData.price || null);
      }
    } catch (error) {
      console.error('Error loading VIX price:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAccounts = async () => {
    try {
      const response = await api.get('/accounts');
      const accountsData = response.data || [];
      
      // Calculate total capital for each account (initial balance + deposits)
      const accountsWithCapital = await Promise.all(accountsData.map(async (account) => {
        try {
          const depositsResponse = await api.get(`/accounts/${account.id}/deposits`);
          const deposits = depositsResponse.data || [];
          const totalDeposits = deposits.reduce((sum, d) => sum + (parseFloat(d.amount) || 0), 0);
          const totalCapital = (parseFloat(account.initial_balance) || 0) + totalDeposits;
          return { ...account, totalCapital };
        } catch (error) {
          console.error(`Error loading deposits for account ${account.id}:`, error);
          return { ...account, totalCapital: parseFloat(account.initial_balance) || 0 };
        }
      }));
      
      setAccounts(accountsWithCapital);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const getCashAllocationRange = (vix) => {
    if (!vix) return null;
    
    if (vix <= 12) {
      return { min: 40, max: 50, label: 'Extreme Greed' };
    } else if (vix > 12 && vix <= 15) {
      return { min: 30, max: 40, label: 'Greed' };
    } else if (vix > 15 && vix <= 20) {
      return { min: 20, max: 25, label: 'Slight Fear' };
    } else if (vix > 20 && vix <= 25) {
      return { min: 10, max: 15, label: 'Fear' };
    } else if (vix > 25 && vix < 30) {
      return { min: 5, max: 10, label: 'Very Fearful' };
    } else { // vix >= 30
      return { min: 0, max: 5, label: 'Extreme Fear' };
    }
  };

  const calculateRecommendation = (balance) => {
    if (!balance || balance <= 0) return null;
    const range = getCashAllocationRange(vixPrice);
    if (!range) return null;
    
    return {
      minCash: (balance * range.min) / 100,
      maxCash: (balance * range.max) / 100,
      minPercent: range.min,
      maxPercent: range.max,
      label: range.label
    };
  };

  const getAllAccountsTotal = () => {
    return accounts.reduce((sum, acc) => sum + (acc.totalCapital || 0), 0);
  };

  const range = getCashAllocationRange(vixPrice);
  const allAccountsTotal = getAllAccountsTotal();
  const allAccountsRecommendation = calculateRecommendation(allAccountsTotal);
  const customRecommendation = customBalance ? calculateRecommendation(parseFloat(customBalance)) : null;

  return (
    <div className="card">
      <div style={{ marginBottom: '15px' }}>
        <h2 style={{ marginBottom: '8px' }}>VIX Cash Allocation Calculator</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '14px', margin: 0 }}>
          Recommended cash allocation based on current VIX levels. Higher VIX (fear) = lower cash. Lower VIX (complacency) = higher cash.
        </p>
      </div>

      {loading ? (
        <div className="loading">Loading VIX data...</div>
      ) : (
        <>
          {/* Compact VIX and Recommendation Header */}
          {vixPrice !== null && range && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '15px',
              marginBottom: '25px',
              padding: '15px',
              backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa',
              borderRadius: '8px',
              border: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`
            }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Current VIX
                </div>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                  {vixPrice.toFixed(2)}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '5px', fontStyle: 'italic' }}>
                  {range.label}
                </div>
              </div>
              <div style={{ textAlign: 'center', borderLeft: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`, paddingLeft: '15px' }}>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  Recommended Cash
                </div>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#007bff' }}>
                  {range.min}% - {range.max}%
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '5px' }}>
                  Allocation Range
                </div>
              </div>
            </div>
          )}

          {/* View Mode Tabs - Compact */}
          <div style={{ 
            display: 'flex', 
            gap: '5px', 
            marginBottom: '20px',
            flexWrap: 'wrap'
          }}>
            <button
              className={`view-mode-tab ${viewMode === 'all' ? 'active' : ''}`}
              onClick={() => setViewMode('all')}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: viewMode === 'all' ? '#007bff' : (isDarkMode ? 'var(--bg-tertiary)' : '#e9ecef'),
                color: viewMode === 'all' ? '#fff' : 'var(--text-secondary)',
                fontWeight: viewMode === 'all' ? '600' : 'normal',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '14px'
              }}
            >
              All Accounts
            </button>
            <button
              className={`view-mode-tab ${viewMode === 'individual' ? 'active' : ''}`}
              onClick={() => setViewMode('individual')}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: viewMode === 'individual' ? '#007bff' : (isDarkMode ? 'var(--bg-tertiary)' : '#e9ecef'),
                color: viewMode === 'individual' ? '#fff' : 'var(--text-secondary)',
                fontWeight: viewMode === 'individual' ? '600' : 'normal',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '14px'
              }}
            >
              By Account
            </button>
            <button
              className={`view-mode-tab ${viewMode === 'custom' ? 'active' : ''}`}
              onClick={() => setViewMode('custom')}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '6px',
                backgroundColor: viewMode === 'custom' ? '#007bff' : (isDarkMode ? 'var(--bg-tertiary)' : '#e9ecef'),
                color: viewMode === 'custom' ? '#fff' : 'var(--text-secondary)',
                fontWeight: viewMode === 'custom' ? '600' : 'normal',
                cursor: 'pointer',
                transition: 'all 0.2s',
                fontSize: '14px'
              }}
            >
              Custom
            </button>
          </div>

          {/* All Accounts Combined View */}
          {viewMode === 'all' && (
            allAccountsRecommendation ? (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                gap: '15px',
                padding: '20px',
                backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa',
                borderRadius: '8px',
                border: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`
              }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Total Capital
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                    ${allAccountsTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                </div>
                <div style={{ borderLeft: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`, paddingLeft: '15px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Recommended Cash
                  </div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff', marginBottom: '5px' }}>
                    ${allAccountsRecommendation.minCash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} - 
                    ${allAccountsRecommendation.maxCash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </div>
                  <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                    {allAccountsRecommendation.minPercent}% - {allAccountsRecommendation.maxPercent}%
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                No accounts found. Create an account to see recommendations.
              </div>
            )
          )}

          {/* Individual Accounts View */}
          {viewMode === 'individual' && (
            <div>
              {accounts.length === 0 ? (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                  No accounts found. Create an account to see individual recommendations.
                </div>
              ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '15px' }}>
                  {accounts.map((account) => {
                    const recommendation = calculateRecommendation(account.totalCapital);
                    return (
                      <div key={account.id} style={{
                        padding: '18px',
                        backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa',
                        borderRadius: '8px',
                        border: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`
                      }}>
                        <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '15px', color: 'var(--text-primary)' }}>
                          {account.name}
                        </div>
                        <div style={{ 
                          display: 'grid', 
                          gridTemplateColumns: '1fr 1fr', 
                          gap: '15px',
                          paddingTop: '15px',
                          borderTop: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`
                        }}>
                          <div>
                            <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                              Capital
                            </div>
                            <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                              ${account.totalCapital.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </div>
                          </div>
                          {recommendation && (
                            <div>
                              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                                Cash Range
                              </div>
                              <div style={{ fontSize: '18px', fontWeight: 'bold', color: '#007bff', marginBottom: '3px' }}>
                                ${recommendation.minCash.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} - 
                                ${recommendation.maxCash.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                              </div>
                              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                                {recommendation.minPercent}% - {recommendation.maxPercent}%
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* Custom Balance View */}
          {viewMode === 'custom' && (
            <div>
              <div className="form-group" style={{ marginBottom: '20px' }}>
                <label style={{ fontSize: '14px', fontWeight: '500', marginBottom: '8px', display: 'block' }}>
                  Enter Custom Balance
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={customBalance}
                  onChange={(e) => setCustomBalance(e.target.value)}
                  placeholder="Enter balance amount (e.g., 10000)"
                  style={{
                    width: '100%',
                    padding: '12px',
                    fontSize: '16px',
                    border: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`,
                    borderRadius: '6px',
                    backgroundColor: isDarkMode ? 'var(--bg-secondary)' : '#fff',
                    color: 'var(--text-primary)'
                  }}
                />
              </div>
              {customRecommendation && (
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
                  gap: '15px',
                  padding: '20px',
                  backgroundColor: isDarkMode ? 'var(--bg-tertiary)' : '#f8f9fa',
                  borderRadius: '8px',
                  border: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`
                }}>
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Entered Balance
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                      ${parseFloat(customBalance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                  </div>
                  <div style={{ borderLeft: `1px solid ${isDarkMode ? 'var(--border-color)' : '#dee2e6'}`, paddingLeft: '15px' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                      Recommended Cash
                    </div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#007bff', marginBottom: '5px' }}>
                      ${customRecommendation.minCash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} - 
                      ${customRecommendation.maxCash.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </div>
                    <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
                      {customRecommendation.minPercent}% - {customRecommendation.maxPercent}%
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default VIXCalculator;

