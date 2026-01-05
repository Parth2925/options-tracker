import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import './ExpirationCalendar.css';

function ExpirationCalendar({ accountId, daysAhead = 90 }) {
  const [expirationGroups, setExpirationGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedDates, setExpandedDates] = useState(new Set());
  const [selectedDaysAhead, setSelectedDaysAhead] = useState(daysAhead);

  useEffect(() => {
    loadExpirationCalendar();
  }, [accountId, selectedDaysAhead]);

  const loadExpirationCalendar = async () => {
    setLoading(true);
    try {
      const params = { days_ahead: selectedDaysAhead };
      if (accountId && accountId !== 'all') {
        params.account_id = accountId;
      }
      
      const response = await api.get('/dashboard/expiration-calendar', { params });
      setExpirationGroups(response.data || []);
    } catch (error) {
      console.error('Error loading expiration calendar:', error);
      setExpirationGroups([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (expirationDate) => {
    const newExpanded = new Set(expandedDates);
    if (newExpanded.has(expirationDate)) {
      newExpanded.delete(expirationDate);
    } else {
      newExpanded.add(expirationDate);
    }
    setExpandedDates(newExpanded);
  };

  const getUrgencyClass = (daysUntil) => {
    if (daysUntil <= 7) return 'urgent';
    if (daysUntil <= 14) return 'warning';
    return 'normal';
  };

  const formatExpirationDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric'
    });
  };

  const formatFullDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'long',
      month: 'long', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  // Calculate summary metrics for each expiration group
  // Note: All positions in expiration calendar are OPEN positions
  const calculateSummary = (group) => {
    let cspCapital = 0;
    let ccCapital = 0;
    let totalPremium = 0;
    let unrealizedPnl = 0;
    let itmPositions = 0;
    let totalContracts = 0;

    group.positions.forEach(position => {
      const capital = (position.strike_price || 0) * (position.contract_quantity || 0) * 100;
      const premium = position.premium || 0;
      
      if (position.trade_type === 'CSP') {
        cspCapital += capital;
      } else if (position.trade_type === 'Covered Call') {
        ccCapital += capital;
      }
      
      totalPremium += premium;
      unrealizedPnl += premium; // For open positions, unrealized P&L = premium received/paid
      totalContracts += position.contract_quantity || 0;
      
      if (position.is_itm) {
        itmPositions++;
      }
    });

    const totalCapital = cspCapital + ccCapital;
    const yieldPct = totalCapital > 0 ? (totalPremium / totalCapital * 100) : 0;

    return {
      cspCapital,
      ccCapital,
      totalCapital,
      totalPremium,
      unrealizedPnl,
      yieldPct,
      itmPositions,
      totalContracts
    };
  };

  // Group positions by type (Calls vs Puts)
  const groupPositionsByType = (positions) => {
    const calls = positions.filter(p => p.trade_type === 'Covered Call');
    const puts = positions.filter(p => p.trade_type === 'CSP');
    return { calls, puts };
  };

  const getActionAbbreviation = (action) => {
    const map = {
      'Sold to Open': 'STO',
      'Bought to Open': 'BTO',
      'Bought to Close': 'BTC',
      'Sold to Close': 'STC'
    };
    return map[action] || action;
  };

  if (loading) {
    return (
      <div className="expiration-calendar-section">
        <div className="loading">Loading expiration calendar...</div>
      </div>
    );
  }

  if (expirationGroups.length === 0) {
    return (
      <div className="expiration-calendar-section">
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <div className="empty-state-message">No upcoming expirations</div>
          <div className="empty-state-hint">Open positions will appear here grouped by expiration date</div>
        </div>
      </div>
    );
  }

  return (
    <div className="expiration-calendar-section">
      <div className="calendar-header">
        <div className="header-content">
          <h2>Expiration Calendar</h2>
          <p className="header-subtitle">Track your upcoming option expirations and manage risk</p>
        </div>
        <div className="calendar-controls">
          <label>Time Range:</label>
          <select 
            value={selectedDaysAhead} 
            onChange={(e) => setSelectedDaysAhead(Number(e.target.value))}
            className="days-select"
          >
            <option value={30}>Next 30 Days</option>
            <option value={60}>Next 60 Days</option>
            <option value={90}>Next 90 Days</option>
          </select>
        </div>
      </div>

      <div className="expiration-sections">
        {expirationGroups.map((group) => {
          const isExpanded = expandedDates.has(group.expiration_date);
          const urgencyClass = getUrgencyClass(group.days_until_expiration);
          const summary = calculateSummary(group);
          const { calls, puts } = groupPositionsByType(group.positions);
          const expDate = new Date(group.expiration_date);
          const isToday = group.expiration_date === new Date().toISOString().split('T')[0];
          
          return (
            <div
              key={group.expiration_date}
              className={`expiration-section ${urgencyClass} ${isToday ? 'today' : ''}`}
            >
              <div 
                className="expiration-section-header"
                onClick={() => toggleExpand(group.expiration_date)}
              >
                <div className="section-title-area">
                  <div className="section-title-row">
                    <h3 className="section-title">{formatExpirationDate(group.expiration_date)}</h3>
                    <span className="expiration-label">Expirations</span>
                  </div>
                  <div className="section-subtitle">
                    {formatFullDate(group.expiration_date)}
                  </div>
                </div>
                
                <div className="header-stats">
                  <div className="header-stat">
                    <span className="stat-value">{group.positions_count}</span>
                    <span className="stat-label">Positions</span>
                  </div>
                  <div className="header-stat">
                    <span className="stat-value">${(summary.totalCapital / 1000).toFixed(1)}k</span>
                    <span className="stat-label">Exposure</span>
                  </div>
                  {summary.itmPositions > 0 && (
                    <div className="header-stat itm-stat">
                      <span className="stat-value itm">⚠️ {summary.itmPositions}</span>
                      <span className="stat-label">ITM</span>
                    </div>
                  )}
                </div>
                
                <div className="days-indicator">
                  <div className="days-number">{group.days_until_expiration}</div>
                  <div className="days-label">
                    {group.days_until_expiration === 0 
                      ? 'Today' 
                      : group.days_until_expiration === 1
                      ? 'Day'
                      : 'Days'}
                  </div>
                </div>
                
                <div className="expand-toggle">
                  <span className="toggle-icon">{isExpanded ? '▼' : '▶'}</span>
                </div>
              </div>

              <div className="summary-metrics">
                <div className="metric-card primary">
                  <div className="metric-icon">💰</div>
                  <div className="metric-content">
                    <div className="metric-value blue">${(summary.totalCapital / 1000).toFixed(1)}k</div>
                    <div className="metric-label">Capital Exposure</div>
                    <div className="metric-breakdown">
                      <span className="breakdown-item">CSP: ${(summary.cspCapital / 1000).toFixed(1)}k</span>
                      <span className="breakdown-item">CC: ${(summary.ccCapital / 1000).toFixed(1)}k</span>
                    </div>
                  </div>
                </div>
                
                <div className="metric-card">
                  <div className="metric-icon">📊</div>
                  <div className="metric-content">
                    <div className={`metric-value ${summary.totalPremium >= 0 ? 'green' : 'red'}`}>
                      {summary.totalPremium >= 0 ? '+' : ''}${summary.totalPremium.toFixed(0)}
                    </div>
                    <div className="metric-label">Total Premiums</div>
                    <div className="metric-detail">{summary.yieldPct.toFixed(2)}% yield</div>
                  </div>
                </div>
                
                <div className="metric-card">
                  <div className="metric-icon">📈</div>
                  <div className="metric-content">
                    <div className={`metric-value ${summary.unrealizedPnl >= 0 ? 'green' : 'red'}`}>
                      {summary.unrealizedPnl >= 0 ? '+' : ''}${summary.unrealizedPnl.toFixed(0)}
                    </div>
                    <div className="metric-label">Unrealized P&L</div>
                    <div className="metric-detail">Premium received/paid</div>
                  </div>
                </div>
                
                <div className="metric-card">
                  <div className="metric-icon">📋</div>
                  <div className="metric-content">
                    <div className="metric-value">{summary.totalContracts}</div>
                    <div className="metric-label">Total Contracts</div>
                    <div className="metric-detail">{group.positions_count} positions</div>
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="expiration-details">
                  {calls.length > 0 && (
                    <div className="trades-group">
                      <div className="group-header">
                        <div className="group-title-area">
                          <div className="group-icon calls-icon">📞</div>
                          <h4 className="group-title calls-title">Covered Calls</h4>
                          <span className="group-count">({calls.length})</span>
                        </div>
                      </div>
                      <div className="trades-list">
                        {calls.map((position) => (
                          <div key={position.id} className={`trade-card ${position.is_itm ? 'itm' : 'otm'}`}>
                            <div className="trade-main">
                              <div className="trade-symbol-area">
                                <div className="trade-symbol">{position.symbol}</div>
                                <span className="trade-type-badge cc-badge">CC</span>
                              </div>
                              <div className="trade-action-badge">
                                {getActionAbbreviation(position.trade_action)} • {position.contract_quantity}x
                              </div>
                            </div>
                            <div className="trade-details-grid">
                              <div className="trade-detail">
                                <span className="detail-label">Premium</span>
                                <span className="detail-value green">+${(position.premium || 0).toFixed(0)}</span>
                              </div>
                              <div className="trade-detail">
                                <span className="detail-label">Strike</span>
                                <span className="detail-value">${position.strike_price || '-'}</span>
                              </div>
                              {position.spot_price > 0 && (
                                <div className="trade-detail">
                                  <span className="detail-label">Current</span>
                                  <span className={`detail-value ${position.is_itm ? 'itm' : 'otm'}`}>
                                    ${position.spot_price.toFixed(2)}
                                    <span className="itm-indicator">{position.is_itm ? ' ⚠️ ITM' : ' ✓ OTM'}</span>
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {puts.length > 0 && (
                    <div className="trades-group">
                      <div className="group-header">
                        <div className="group-title-area">
                          <div className="group-icon puts-icon">📉</div>
                          <h4 className="group-title puts-title">Cash-Secured Puts</h4>
                          <span className="group-count">({puts.length})</span>
                        </div>
                      </div>
                      <div className="trades-list">
                        {puts.map((position) => (
                          <div key={position.id} className={`trade-card ${position.is_itm ? 'itm' : 'otm'}`}>
                            <div className="trade-main">
                              <div className="trade-symbol-area">
                                <div className="trade-symbol">{position.symbol}</div>
                                <span className="trade-type-badge csp-badge">CSP</span>
                              </div>
                              <div className="trade-action-badge">
                                {getActionAbbreviation(position.trade_action)} • {position.contract_quantity}x
                              </div>
                            </div>
                            <div className="trade-details-grid">
                              <div className="trade-detail">
                                <span className="detail-label">Premium</span>
                                <span className="detail-value green">+${(position.premium || 0).toFixed(0)}</span>
                              </div>
                              <div className="trade-detail">
                                <span className="detail-label">Strike</span>
                                <span className="detail-value">${position.strike_price || '-'}</span>
                              </div>
                              {position.spot_price > 0 && (
                                <div className="trade-detail">
                                  <span className="detail-label">Current</span>
                                  <span className={`detail-value ${position.is_itm ? 'itm' : 'otm'}`}>
                                    ${position.spot_price.toFixed(2)}
                                    <span className="itm-indicator">{position.is_itm ? ' ⚠️ ITM' : ' ✓ OTM'}</span>
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ExpirationCalendar;
