import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';
import './Positions.css';

function StockPositionFormDialog({ position, accounts, onSuccess, onCancel }) {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [dragStartPos, setDragStartPos] = useState(null);
  const [dragStartTarget, setDragStartTarget] = useState(null);
  
  // Prevent body scroll when modal is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Handle mouse down to track drag operations
  const handleMouseDown = (e) => {
    if (e.target.classList.contains('modal-overlay')) {
      setDragStartPos({ x: e.clientX, y: e.clientY });
      setDragStartTarget(e.target);
    }
  };

  // Handle mouse up - only close if it wasn't a drag operation
  const handleMouseUp = (e) => {
    if (dragStartTarget && e.target === dragStartTarget) {
      const moved = dragStartPos && (
        Math.abs(e.clientX - dragStartPos.x) > 5 || 
        Math.abs(e.clientY - dragStartPos.y) > 5
      );
      
      if (!moved) {
        onCancel();
      }
    }
    setDragStartPos(null);
    setDragStartTarget(null);
  };

  const [formData, setFormData] = useState({
    account_id: accounts && accounts.length === 1 ? accounts[0].id : '', // Only auto-select if there's exactly one account
    symbol: '',
    shares: '',
    cost_basis_per_share: '',
    acquired_date: new Date().toISOString().split('T')[0],
    status: 'Open',
    notes: ''
  });

  // Initialize form data if editing
  useEffect(() => {
    if (position) {
      setFormData({
        account_id: position.account_id || (accounts && accounts.length === 1 ? accounts[0].id : ''), // Only auto-select if there's exactly one account
        symbol: position.symbol || '',
        shares: position.shares || '',
        cost_basis_per_share: position.cost_basis_per_share || '',
        acquired_date: position.acquired_date ? position.acquired_date.split('T')[0] : new Date().toISOString().split('T')[0],
        status: position.status || 'Open',
        notes: position.notes || ''
      });
    }
  }, [position, accounts]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Auto-uppercase symbol input
    const processedValue = name === 'symbol' ? value.toUpperCase() : value;
    
    setFormData(prev => ({
      ...prev,
      [name]: processedValue
    }));
    
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const errors = {};
    
    if (!formData.account_id) {
      errors.account_id = 'Account is required';
    }
    if (!formData.symbol || formData.symbol.trim() === '') {
      errors.symbol = 'Symbol is required';
    }
    if (!formData.shares || parseInt(formData.shares) < 1) {
      errors.shares = 'Shares must be at least 1';
    }
    if (!formData.cost_basis_per_share || parseFloat(formData.cost_basis_per_share) < 0) {
      errors.cost_basis_per_share = 'Cost basis per share must be 0 or greater';
    }
    if (!formData.acquired_date) {
      errors.acquired_date = 'Acquired date is required';
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      showToast('Please fix the errors in the form', 'error');
      return;
    }

    setLoading(true);

    try {
      const payload = {
        account_id: parseInt(formData.account_id),
        symbol: formData.symbol.trim().toUpperCase(),
        shares: parseInt(formData.shares),
        cost_basis_per_share: parseFloat(formData.cost_basis_per_share),
        acquired_date: formData.acquired_date,
        status: formData.status,
        notes: formData.notes || null,
      };

      if (position) {
        await api.put(`/stock-positions/${position.id}`, payload);
        showToast('Stock position updated successfully!', 'success');
      } else {
        await api.post('/stock-positions', payload);
        showToast('Stock position created successfully!', 'success');
      }

      onSuccess();
    } catch (error) {
      console.error('Error saving stock position:', error);
      showToast(error.response?.data?.error || `Failed to ${position ? 'update' : 'create'} stock position`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="modal-overlay" 
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{position ? 'Edit Stock Position' : 'Add Stock Position'}</h2>
          <button 
            className="modal-close" 
            onClick={onCancel}
            type="button"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label>Account *</label>
              <select
                name="account_id"
                value={formData.account_id}
                onChange={handleChange}
                required
                className={fieldErrors.account_id ? 'error-field' : ''}
                disabled={!!position} // Don't allow changing account when editing
              >
                <option value="">Select Account</option>
                {accounts && accounts.map(account => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
              {fieldErrors.account_id && (
                <div className="field-error">{fieldErrors.account_id}</div>
              )}
            </div>

            <div className="form-group">
              <label>Symbol *</label>
              <input
                type="text"
                name="symbol"
                value={formData.symbol}
                onChange={handleChange}
                required
                placeholder="e.g., AAPL"
                className={fieldErrors.symbol ? 'error-field' : ''}
                style={{ textTransform: 'uppercase' }}
              />
              {fieldErrors.symbol && (
                <div className="field-error">{fieldErrors.symbol}</div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
              <div className="form-group">
                <label>Shares *</label>
                <input
                  type="number"
                  name="shares"
                  value={formData.shares}
                  onChange={handleChange}
                  required
                  min="1"
                  placeholder="100"
                  className={fieldErrors.shares ? 'error-field' : ''}
                />
                {fieldErrors.shares && (
                  <div className="field-error">{fieldErrors.shares}</div>
                )}
              </div>

              <div className="form-group">
                <label>Cost Basis per Share *</label>
                <input
                  type="number"
                  name="cost_basis_per_share"
                  value={formData.cost_basis_per_share}
                  onChange={handleChange}
                  required
                  min="0"
                  step="0.01"
                  placeholder="150.00"
                  className={fieldErrors.cost_basis_per_share ? 'error-field' : ''}
                />
                {fieldErrors.cost_basis_per_share && (
                  <div className="field-error">{fieldErrors.cost_basis_per_share}</div>
                )}
              </div>
            </div>

            <div className="form-group">
              <label>Acquired Date *</label>
              <input
                type="date"
                name="acquired_date"
                value={formData.acquired_date}
                onChange={handleChange}
                required
                className={fieldErrors.acquired_date ? 'error-field' : ''}
              />
              {fieldErrors.acquired_date && (
                <div className="field-error">{fieldErrors.acquired_date}</div>
              )}
            </div>

            <div className="form-group">
              <label>Status</label>
              <select
                name="status"
                value={formData.status}
                onChange={handleChange}
              >
                <option value="Open">Open</option>
                <option value="Called Away">Called Away</option>
              </select>
            </div>

            <div className="form-group">
              <label>Notes</label>
              <textarea
                name="notes"
                value={formData.notes}
                onChange={handleChange}
                rows="3"
                placeholder="Optional notes about this position..."
              />
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : (position ? 'Update' : 'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default StockPositionFormDialog;

