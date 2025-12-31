import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';

function StockPositionForm({ accounts, position, onSuccess, onCancel }) {
  const { showToast } = useToast();
  const [formData, setFormData] = useState({
    account_id: accounts.length > 0 ? accounts[0].id : '',
    symbol: '',
    shares: '',
    cost_basis_per_share: '',
    acquired_date: new Date().toISOString().split('T')[0],
    status: 'Open',
    notes: ''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (position) {
      setFormData({
        account_id: position.account_id,
        symbol: position.symbol || '',
        shares: position.shares || '',
        cost_basis_per_share: position.cost_basis_per_share || '',
        acquired_date: position.acquired_date ? position.acquired_date.split('T')[0] : new Date().toISOString().split('T')[0],
        status: position.status || 'Open',
        notes: position.notes || ''
      });
    }
  }, [position]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (position) {
        // Update existing position
        await api.put(`/stock-positions/${position.id}`, formData);
      } else {
        // Create new position
        await api.post('/stock-positions', formData);
      }
      onSuccess();
    } catch (error) {
      console.error('Error saving stock position:', error);
      showToast(error.response?.data?.error || 'Failed to save stock position', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '20px' }}>
      <h2>{position ? 'Edit Stock Position' : 'Add Stock Position'}</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Account *</label>
          <select
            name="account_id"
            value={formData.account_id}
            onChange={handleChange}
            required
            disabled={position !== null} // Don't allow changing account for existing positions
          >
            <option value="">-- Select Account --</option>
            {accounts.map((acc) => (
              <option key={acc.id} value={acc.id}>
                {acc.name}
              </option>
            ))}
          </select>
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
            style={{ textTransform: 'uppercase' }}
          />
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
            />
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
            />
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
          />
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

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : (position ? 'Update' : 'Create')}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default StockPositionForm;
