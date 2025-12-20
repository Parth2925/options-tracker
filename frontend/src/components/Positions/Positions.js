import React, { useState, useEffect, useMemo } from 'react';
import Navbar from '../Layout/Navbar';
import api from '../../utils/api';
import './Positions.css';

function Positions() {
  const [positions, setPositions] = useState({ open: [], closed: [] });
  const [accounts, setAccounts] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState('all');
  const [statusFilter, setStatusFilter] = useState('Open'); // Default to Open positions
  const [loading, setLoading] = useState(true);
  
  // Search and sort state
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (accounts.length > 0) {
      loadPositions();
    }
  }, [selectedAccount, statusFilter, accounts]);

  const loadAccounts = async () => {
    try {
      const response = await api.get('/accounts');
      setAccounts(response.data);
    } catch (error) {
      console.error('Error loading accounts:', error);
    }
  };

  const loadPositions = async () => {
    setLoading(true);
    try {
      const params = { status: statusFilter };
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      
      const response = await api.get('/dashboard/positions', { params });
      setPositions(response.data);
    } catch (error) {
      console.error('Error loading positions:', error);
    } finally {
      setLoading(false);
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

  // Filter and sort positions
  const displayTrades = useMemo(() => {
    let filtered = statusFilter === 'All' 
      ? [...positions.open, ...positions.closed]
      : statusFilter === 'Open'
      ? positions.open
      : positions.closed;

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(trade => 
        trade.symbol?.toLowerCase().includes(term) ||
        trade.trade_type?.toLowerCase().includes(term) ||
        trade.strike_price?.toString().includes(term)
      );
    }

    // Apply sorting
    if (sortConfig.key) {
      filtered.sort((a, b) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        // Handle different data types
        if (sortConfig.key === 'trade_date' || sortConfig.key === 'expiration_date') {
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
  }, [positions, statusFilter, searchTerm, sortConfig]);

  return (
    <>
      <Navbar />
      <div className="container">
        <h1>Positions</h1>

        <div className="card" style={{ marginBottom: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px' }}>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Search</label>
              <input
                type="text"
                placeholder="Search by symbol, type, strike..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
            <div className="form-group" style={{ marginBottom: 0 }}>
              <label>Account</label>
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
              <label>Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="All">All</option>
                <option value="Open">Open</option>
                <option value="Closed">Closed</option>
              </select>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="loading">Loading positions...</div>
        ) : (
          <div className="card">
            <div style={{ marginBottom: '15px', color: 'var(--text-secondary)', fontSize: '14px' }}>
              Showing {displayTrades.length} position{displayTrades.length !== 1 ? 's' : ''}
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
                      onClick={() => handleSort('contract_quantity')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Quantity {sortConfig.key === 'contract_quantity' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('premium')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Premium {sortConfig.key === 'premium' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th 
                      onClick={() => handleSort('fees')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Fees {sortConfig.key === 'fees' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                    <th>Net Premium</th>
                    <th 
                      onClick={() => handleSort('status')}
                      style={{ cursor: 'pointer', userSelect: 'none' }}
                      className="sortable-header"
                    >
                      Status {sortConfig.key === 'status' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {displayTrades.length === 0 ? (
                    <tr>
                      <td colSpan="10" style={{ textAlign: 'center' }}>
                        {positions.open.length === 0 && positions.closed.length === 0
                          ? 'No positions found.'
                          : 'No positions match your search criteria.'}
                      </td>
                    </tr>
                  ) : (
                  displayTrades.map((trade) => {
                    const netPremium = (trade.premium || 0) - (trade.fees || 0);
                    return (
                      <tr key={trade.id}>
                        <td>{new Date(trade.trade_date).toLocaleDateString()}</td>
                        <td>{trade.symbol}</td>
                        <td>{trade.trade_type}</td>
                        <td>{trade.strike_price ? `$${trade.strike_price}` : '-'}</td>
                        <td>{trade.expiration_date ? new Date(trade.expiration_date).toLocaleDateString() : '-'}</td>
                        <td>{trade.contract_quantity}</td>
                        <td>${trade.premium?.toFixed(2) || '0.00'}</td>
                        <td>${trade.fees?.toFixed(2) || '0.00'}</td>
                        <td>${netPremium.toFixed(2)}</td>
                        <td>
                          <span className={`status-badge status-${trade.status.toLowerCase()}`}>
                            {trade.status}
                          </span>
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

export default Positions;

