import React, { useState, useEffect, useMemo } from 'react';
import api from '../../utils/api';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../contexts/ToastContext';
import StockPositionFormDialog from './StockPositionFormDialog';

function StockPositions({ accounts, selectedAccount, onAccountChange }) {
  const { isDarkMode } = useTheme();
  const { showToast } = useToast();
  const [positions, setPositions] = useState([]);
  const [statusFilter, setStatusFilter] = useState('Open');
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingPosition, setEditingPosition] = useState(null);
  
  // Search and sort state
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });
  const [companyLogos, setCompanyLogos] = useState({});

  useEffect(() => {
    if (accounts.length > 0) {
      loadPositions();
    }
  }, [selectedAccount, statusFilter, accounts]);

  const loadPositions = async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedAccount && selectedAccount !== 'all') {
        params.account_id = selectedAccount;
      }
      if (statusFilter && statusFilter !== 'All') {
        params.status = statusFilter;
      }
      
      const response = await api.get('/stock-positions', { params });
      setPositions(response.data || []);
      
      // Load logos for all displayed positions
      if (response.data && response.data.length > 0) {
        const symbols = [...new Set(response.data.map(p => p.symbol).filter(Boolean))];
        if (symbols.length > 0) {
          loadCompanyLogos(symbols);
        }
      }
    } catch (error) {
      console.error('Error loading stock positions:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCompanyLogos = async (symbols) => {
    try {
      if (!symbols || symbols.length === 0) {
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

  const handlePositionCreated = () => {
    setShowForm(false);
    setEditingPosition(null);
    loadPositions();
    showToast(editingPosition ? 'Stock position updated successfully!' : 'Stock position created successfully!', 'success');
  };

  const handleEdit = (position) => {
    setEditingPosition(position);
    setShowForm(true);
  };

  const handleDelete = async (positionId) => {
    if (!window.confirm('Are you sure you want to delete this stock position?')) {
      return;
    }

    try {
      await api.delete(`/stock-positions/${positionId}`);
      loadPositions();
      showToast('Stock position deleted successfully!', 'success');
    } catch (error) {
      console.error('Error deleting stock position:', error);
      showToast(error.response?.data?.error || 'Failed to delete stock position', 'error');
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
  const displayPositions = useMemo(() => {
    let filtered = [...positions];

    // Apply search filter
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(position => 
        position.symbol?.toLowerCase().includes(term)
      );
    }

    // Apply sorting
    if (sortConfig.key) {
      filtered.sort((a, b) => {
        let aVal = a[sortConfig.key];
        let bVal = b[sortConfig.key];

        // Handle different data types
        if (sortConfig.key === 'acquired_date') {
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
  }, [positions, searchTerm, sortConfig]);

  return (
    <>
      <div className="page-header">
        <h1>Stock Positions</h1>
        <div className="page-header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => {
              setEditingPosition(null);
              setShowForm(true);
            }}
          >
            Add Stock Position
          </button>
        </div>
      </div>

      {showForm && (
        <StockPositionFormDialog
          accounts={accounts}
          position={editingPosition}
          onSuccess={handlePositionCreated}
          onCancel={() => {
            setShowForm(false);
            setEditingPosition(null);
          }}
        />
      )}

      <div className="card filters-card">
        <div className="filters-grid">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Search</label>
            <input
              type="text"
              placeholder="Search by symbol..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ width: '100%' }}
            />
          </div>
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label>Account</label>
            <select
              value={selectedAccount}
              onChange={(e) => onAccountChange(e.target.value)}
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
              <option value="Called Away">Called Away</option>
            </select>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="loading">Loading stock positions...</div>
      ) : (
        <div className="card">
          <div style={{ marginBottom: '15px', color: 'var(--text-secondary)', fontSize: '14px' }}>
            Showing {displayPositions.length} position{displayPositions.length !== 1 ? 's' : ''}
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th 
                    onClick={() => handleSort('symbol')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                    className="sortable-header"
                  >
                    Symbol {sortConfig.key === 'symbol' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th 
                    onClick={() => handleSort('shares')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                    className="sortable-header"
                  >
                    Shares {sortConfig.key === 'shares' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th 
                    onClick={() => handleSort('cost_basis_per_share')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                    className="sortable-header"
                  >
                    Cost Basis/Share {sortConfig.key === 'cost_basis_per_share' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th>Total Cost Basis</th>
                  <th 
                    onClick={() => handleSort('acquired_date')}
                    style={{ cursor: 'pointer', userSelect: 'none' }}
                    className="sortable-header"
                  >
                    Acquired Date {sortConfig.key === 'acquired_date' && (sortConfig.direction === 'asc' ? '↑' : '↓')}
                  </th>
                  <th>Available Shares</th>
                  <th>Shares Used</th>
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
                {displayPositions.length === 0 ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: 'center', padding: '40px 20px' }}>
                      <div className="empty-state">
                        <div className="empty-state-icon">
                          {positions.length === 0 ? '📊' : '🔍'}
                        </div>
                        <div className="empty-state-message">
                          {positions.length === 0
                            ? 'No stock positions found'
                            : 'No positions match your search criteria'}
                        </div>
                        <div className="empty-state-hint">
                          {positions.length === 0
                            ? 'Click "Add Stock Position" to create your first position'
                            : 'Try adjusting your search criteria'}
                        </div>
                      </div>
                    </td>
                  </tr>
                ) : (
                displayPositions.map((position) => {
                  const isCalledAway = position.status === 'Called Away';
                  return (
                    <tr 
                      key={position.id}
                      style={isCalledAway ? {
                        backgroundColor: isDarkMode ? '#3a3a3a' : '#e9ecef',
                        borderLeft: '4px solid #6c757d'
                      } : {}}
                    >
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {companyLogos[position.symbol] && (
                            <img 
                              src={companyLogos[position.symbol]} 
                              alt={`${position.symbol} logo`}
                              style={{ 
                                width: '24px', 
                                height: '24px', 
                                objectFit: 'contain',
                                borderRadius: '4px'
                              }}
                              onError={(e) => {
                                e.target.style.display = 'none';
                              }}
                            />
                          )}
                          <span>{position.symbol}</span>
                        </div>
                      </td>
                      <td>{position.shares}</td>
                      <td>${position.cost_basis_per_share?.toFixed(2) || '0.00'}</td>
                      <td>${position.total_cost_basis?.toFixed(2) || '0.00'}</td>
                      <td>{position.acquired_date ? (() => {
                        const [year, month, day] = position.acquired_date.split('T')[0].split('-');
                        return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
                      })() : '-'}</td>
                      <td>{position.available_shares || 0}</td>
                      <td>{position.shares_used || 0}</td>
                      <td>
                        <span className={`status-badge status-${position.status?.toLowerCase().replace(' ', '-') || 'open'}`}>
                          {position.status}
                        </span>
                      </td>
                      <td>
                        <div className="action-buttons">
                          <button
                            className="action-button action-button-edit"
                            onClick={() => handleEdit(position)}
                            title="Edit position"
                          >
                            <span className="action-button-icon">✏️</span>
                            <span>Edit</span>
                          </button>
                          <button
                            className="action-button action-button-delete"
                            onClick={() => handleDelete(position.id)}
                            title="Delete position"
                          >
                            <span>Delete</span>
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
    </>
  );
}

export default StockPositions;
