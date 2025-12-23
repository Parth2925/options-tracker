import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../Layout/Navbar';
import api, { API_BASE_URL } from '../../utils/api';
import TradeForm from './TradeForm';
import { useToast } from '../../contexts/ToastContext';
import { useTheme } from '../../contexts/ThemeContext';
import './Trades.css';

function Trades() {
  const { showToast } = useToast();
  const { isDarkMode } = useTheme();
  const navigate = useNavigate();
  const [trades, setTrades] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editingTrade, setEditingTrade] = useState(null);
  const [showImport, setShowImport] = useState(false);
  const [loading, setLoading] = useState(true);
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [tradeTypeFilter, setTradeTypeFilter] = useState('all');
  
  // Sorting state
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (accounts.length > 0) {
      loadTrades();
    }
  }, [selectedAccount, accounts]);

  const loadAccounts = async () => {
    try {
      const response = await api.get('/accounts');
      setAccounts(response.data);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const loadTrades = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/trades', { params });
      setTrades(response.data);
    } catch (error) {
      console.error('Error loading trades:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTradeCreated = () => {
    setShowForm(false);
    setEditingTrade(null);
    loadTrades();
    showToast(editingTrade ? 'Trade updated successfully!' : 'Trade created successfully!', 'success');
  };

  const handleEdit = (trade) => {
    navigate(`/trades/${trade.id}/edit`);
  };

  const handleCancel = () => {
    setShowForm(false);
    setEditingTrade(null);
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!selectedAccount || selectedAccount === 'all') {
      showToast('Please select an account before importing', 'warning');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('account_id', selectedAccount);

    try {
      const response = await api.post('/trades/import', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      showToast(`Successfully imported ${response.data.count} trades!`, 'success');
      setShowImport(false);
      loadTrades();
    } catch (error) {
      showToast(error.response?.data?.error || 'Import failed', 'error');
    }
  };

  const handleDelete = async (tradeId) => {
    if (!window.confirm('Are you sure you want to delete this trade?')) {
      return;
    }

    try {
      await api.delete(`/trades/${tradeId}`);
      showToast('Trade deleted successfully!', 'success');
      loadTrades();
    } catch (error) {
      showToast(error.response?.data?.error || 'Delete failed', 'error');
    }
  };

  // Sorting handler
  const handleSort = (key) => {
    let direction = 'asc';
    if (sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  // Filter and sort trades
  const filteredAndSortedTrades = useMemo(() => {
    let filtered = [...trades];

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(trade => 
        trade.symbol?.toLowerCase().includes(term) ||
        trade.trade_type?.toLowerCase().includes(term) ||
        trade.trade_action?.toLowerCase().includes(term) ||
        trade.notes?.toLowerCase().includes(term) ||
        trade.strike_price?.toString().includes(term)
      );
    }

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(trade => trade.status?.toLowerCase() === statusFilter.toLowerCase());
    }

    // Apply trade type filter
    if (tradeTypeFilter !== 'all') {
      filtered = filtered.filter(trade => trade.trade_type?.toLowerCase() === tradeTypeFilter.toLowerCase());
    }

    // Apply sorting
    if (sortConfig.key) {
      filtered.sort((a, b) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        // Handle different data types
        if (sortConfig.key === 'trade_date' || sortConfig.key === 'expiration_date' || sortConfig.key === 'close_date') {
          aVal = aVal ? new Date(aVal).getTime() : 0;
          bVal = bVal ? new Date(bVal).getTime() : 0;
        } else if (typeof aVal === 'string') {
          aVal = aVal.toLowerCase();
          bVal = bVal?.toLowerCase() || '';
        } else if (aVal === null || aVal === undefined) {
          aVal = 0;
        }
        if (bVal === null || bVal === undefined) {
          bVal = 0;
        }

        if (aVal < bVal) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aVal > bVal) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return filtered;
  }, [trades, searchTerm, statusFilter, tradeTypeFilter, sortConfig]);

  // Get unique trade types for filter
  const uniqueTradeTypes = useMemo(() => {
    const types = [...new Set(trades.map(t => t.trade_type).filter(Boolean))];
    return types.sort();
  }, [trades]);

  return (
    <>
      <Navbar />
      <div className="container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h1>Trades</h1>
          <div>
            <button 
              className="btn btn-secondary" 
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token');
                  const params = new URLSearchParams();
                  if (selectedAccount && selectedAccount !== 'all') {
                    params.append('account_id', selectedAccount);
                  }
                  params.append('format', 'csv');
                  const response = await fetch(`${API_BASE_URL}/trades/export?${params.toString()}`, {
                    headers: {
                      'Authorization': `Bearer ${token}`
                    }
                  });
                  if (!response.ok) throw new Error('Export failed');
                  const blob = await response.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  const contentDisposition = response.headers.get('Content-Disposition');
                  const filename = contentDisposition 
                    ? contentDisposition.split('filename=')[1]?.replace(/"/g, '') 
                    : 'trades_export.csv';
                  a.download = filename;
                  document.body.appendChild(a);
                  a.click();
                  window.URL.revokeObjectURL(url);
                  document.body.removeChild(a);
                  showToast('Trades exported successfully!', 'success');
                } catch (error) {
                  showToast(error.response?.data?.error || 'Export failed', 'error');
                }
              }}
              style={{ marginRight: '10px' }}
            >
              Export CSV
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={async () => {
                try {
                  const token = localStorage.getItem('token');
                  const params = new URLSearchParams();
                  if (selectedAccount && selectedAccount !== 'all') {
                    params.append('account_id', selectedAccount);
                  }
                  params.append('format', 'xlsx');
                  const response = await fetch(`${API_BASE_URL}/trades/export?${params.toString()}`, {
                    headers: {
                      'Authorization': `Bearer ${token}`
                    }
                  });
                  if (!response.ok) throw new Error('Export failed');
                  const blob = await response.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  const contentDisposition = response.headers.get('Content-Disposition');
                  const filename = contentDisposition 
                    ? contentDisposition.split('filename=')[1]?.replace(/"/g, '') 
                    : 'trades_export.xlsx';
                  a.download = filename;
                  document.body.appendChild(a);
                  a.click();
                  window.URL.revokeObjectURL(url);
                  document.body.removeChild(a);
                  showToast('Trades exported successfully!', 'success');
                } catch (error) {
                  showToast(error.response?.data?.error || 'Export failed', 'error');
                }
              }}
              style={{ marginRight: '10px' }}
            >
              Export Excel
            </button>
            <button 
              className="btn btn-secondary" 
              onClick={() => setShowImport(!showImport)} 
              style={{ marginRight: '10px' }}
            >
              Import CSV/Excel
            </button>
            <button className="btn btn-primary" onClick={() => {
              setEditingTrade(null);
              setShowForm(!showForm);
            }}>
              {showForm ? 'Cancel' : 'Add Trade'}
            </button>
          </div>
        </div>


        {showImport && (
          <div className="card">
            <h3>Import Trades from File</h3>
            <p>Select a CSV or Excel file with your trades. Download the template below to see the required format.</p>
            <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Required Columns:</strong>
              <ul style={{ marginTop: '10px', marginLeft: '20px', color: 'var(--text-secondary)' }}>
                <li><strong>symbol</strong> - Stock symbol (e.g., AAPL, TSLA)</li>
                <li><strong>trade_type</strong> - CSP, Covered Call, LEAPS, etc.</li>
                <li><strong>strike_price</strong> - Strike price (numeric)</li>
                <li><strong>expiration_date</strong> - YYYY-MM-DD format</li>
                <li><strong>contract_quantity</strong> - Number of contracts</li>
                <li><strong>trade_price</strong> - Price per contract</li>
                <li><strong>trade_action</strong> - Sold to Open, Bought to Open, Bought to Close, Sold to Close</li>
                <li><strong>premium</strong> - Total premium (calculated automatically if trade_price provided)</li>
                <li><strong>fees</strong> - Trading fees</li>
                <li><strong>trade_date</strong> - YYYY-MM-DD format</li>
                <li><strong>status</strong> - Open, Closed, Assigned, Expired (optional)</li>
                <li><strong>notes</strong> - Additional notes (optional)</li>
              </ul>
            </div>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <button 
                className="btn btn-secondary" 
                onClick={async () => {
                  try {
                    const token = localStorage.getItem('token');
                    const response = await fetch(`${API_BASE_URL}/trades/export-template?format=csv`, {
                      headers: {
                        'Authorization': `Bearer ${token}`
                      }
                    });
                    if (!response.ok) throw new Error('Download failed');
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'trades_template.csv';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    showToast('Template downloaded successfully', 'success');
                  } catch (error) {
                    showToast('Failed to download template', 'error');
                  }
                }}
              >
                Download CSV Template
              </button>
              <button 
                className="btn btn-secondary" 
                onClick={async () => {
                  try {
                    const token = localStorage.getItem('token');
                    const response = await fetch(`${API_BASE_URL}/trades/export-template?format=xlsx`, {
                      headers: {
                        'Authorization': `Bearer ${token}`
                      }
                    });
                    if (!response.ok) throw new Error('Download failed');
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'trades_template.xlsx';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    showToast('Template downloaded successfully', 'success');
                  } catch (error) {
                    showToast('Failed to download template', 'error');
                  }
                }}
              >
                Download Excel Template
              </button>
            </div>
            <div className="form-group">
              <label>Select Account *</label>
              <select
                value={selectedAccount === 'all' ? '' : selectedAccount}
                onChange={(e) => {
                  setSelectedAccount(e.target.value || 'all');
                }}
                style={{ cursor: 'pointer' }}
              >
                <option value="">-- Select Account --</option>
                {accounts.length === 0 ? (
                  <option value="" disabled>No accounts available. Create an account first.</option>
                ) : (
                  accounts.map((acc) => (
                    <option key={acc.id} value={acc.id}>
                      {acc.name}
                    </option>
                  ))
                )}
              </select>
              {accounts.length === 0 && (
                <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '5px' }}>
                  You need to create an account first. Go to the Accounts page to create one.
                </p>
              )}
            </div>
            <div className="form-group">
              <label>Upload File</label>
              <input type="file" accept=".csv,.xlsx,.xls" onChange={handleImport} />
            </div>
          </div>
        )}

        {showForm && (
          <TradeForm
            accounts={accounts}
            trade={editingTrade}
            trades={trades}
            onSuccess={handleTradeCreated}
            onCancel={handleCancel}
          />
        )}

        {/* Search and Filter Controls */}
        <div className="card" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Search</label>
              <input
                type="text"
                placeholder="Search by symbol, type, action, notes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Filter by Account</label>
              <select
                value={selectedAccount}
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
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Filter by Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All Statuses</option>
                <option value="open">Open</option>
                <option value="closed">Closed</option>
                <option value="assigned">Assigned</option>
                <option value="expired">Expired</option>
              </select>
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Filter by Trade Type</label>
              <select
                value={tradeTypeFilter}
                onChange={(e) => setTradeTypeFilter(e.target.value)}
              >
                <option value="all">All Types</option>
                {uniqueTradeTypes.map((type) => (
                  <option key={type} value={type.toLowerCase()}>
                    {type}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading trades...</div>
        ) : (
          <div className="card">
            <div style={{ marginBottom: '15px', color: 'var(--text-secondary)', fontSize: '14px' }}>
              Showing {filteredAndSortedTrades.length} of {trades.length} trades
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table>
                <thead>
                  <tr>
                    <th 
                      onClick={() => handleSort('trade_date')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Date {sortConfig.key === 'trade_date' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('symbol')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Symbol {sortConfig.key === 'symbol' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('trade_type')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Type {sortConfig.key === 'trade_type' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('trade_action')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Action {sortConfig.key === 'trade_action' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('strike_price')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Strike {sortConfig.key === 'strike_price' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('expiration_date')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Expiration {sortConfig.key === 'expiration_date' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('premium')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Premium {sortConfig.key === 'premium' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('realized_pnl')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Realized P&L {sortConfig.key === 'realized_pnl' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('days_held')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Days Held {sortConfig.key === 'days_held' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('simple_return_pct')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Return % {sortConfig.key === 'simple_return_pct' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('status')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Status {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAndSortedTrades.length === 0 ? (
                    <tr>
                      <td colSpan="12" style={{ textAlign: 'center' }}>
                        {trades.length === 0 
                          ? 'No trades found. Add your first trade!' 
                          : 'No trades match your search/filter criteria.'}
                      </td>
                    </tr>
                  ) : (
                    filteredAndSortedTrades.map((trade) => {
                      // Determine if trade is closed/assigned for visual styling
                      const isClosed = trade.status === 'Closed' || trade.status === 'Assigned' || trade.status === 'Expired';
                      return (
                    <tr 
                      key={trade.id}
                      style={isClosed ? {
                        backgroundColor: isDarkMode ? '#3a3a3a' : '#e9ecef',
                        borderLeft: '4px solid #6c757d'
                      } : {}}
                    >
                      <td>{trade.trade_date ? (() => {
                        // Parse date as local date to avoid timezone issues
                        const [year, month, day] = trade.trade_date.split('T')[0].split('-');
                        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
                      })() : '-'}</td>
                      <td>{trade.symbol}</td>
                      <td>{trade.trade_type}</td>
                      <td>{trade.trade_action || '-'}</td>
                      <td>{trade.strike_price ? `$${trade.strike_price}` : '-'}</td>
                      <td>{trade.expiration_date ? (() => {
                        // Parse date as local date to avoid timezone issues
                        const [year, month, day] = trade.expiration_date.split('T')[0].split('-');
                        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
                      })() : '-'}</td>
                      <td>${trade.premium?.toFixed(2) || '0.00'}</td>
                      <td style={{ 
                        color: trade.realized_pnl >= 0 ? '#28a745' : '#dc3545',
                        fontWeight: 'bold'
                      }}>
                        {trade.realized_pnl !== undefined ? `$${trade.realized_pnl.toFixed(2)}` : '-'}
                      </td>
                      <td>
                        {trade.days_held !== null && trade.days_held !== undefined ? `${trade.days_held} days` : '-'}
                      </td>
                      <td>
                        {trade.simple_return_pct !== null && trade.simple_return_pct !== undefined ? (
                          <div>
                            <div style={{ 
                              color: trade.simple_return_pct >= 0 ? '#28a745' : '#dc3545',
                              fontWeight: 'bold'
                            }} title="Simple return: (Realized P&L / Capital at Risk) × 100. Does not depend on time held.">
                              {trade.simple_return_pct.toFixed(2)}%
                            </div>
                            {trade.annualized_return_pct !== null && trade.annualized_return_pct !== undefined && (
                              <small style={{ color: '#666', fontSize: '10px' }} title="Annualized return: adjusts for time held. Changes when days held changes.">
                                ({trade.annualized_return_pct.toFixed(2)}% annualized)
                              </small>
                            )}
                          </div>
                        ) : '-'}
                      </td>
                      <td>
                        <span className={`status-badge status-${trade.status.toLowerCase()}`}>
                          {trade.status}
                        </span>
                      </td>
                      <td>
                        <div style={{ display: 'flex', gap: '5px' }}>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            onClick={() => handleEdit(trade)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-danger"
                            style={{ padding: '5px 10px', fontSize: '12px' }}
                            onClick={() => handleDelete(trade.id)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                    );
                    })
                  )}
              </tbody>
            </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default Trades;

