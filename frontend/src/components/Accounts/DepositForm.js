import React, { useState } from 'react';
import api from '../../utils/api';

function DepositForm({ accountId, onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    amount: '',
    deposit_date: new Date().toISOString().split('T')[0],
    notes: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        ...formData,
        amount: parseFloat(formData.amount),
      };

      await api.post(`/accounts/${accountId}/deposits`, payload);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to add deposit');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '20px' }}>
      <h3>Add Deposit</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Amount *</label>
          <input
            type="number"
            step="0.01"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            required
            placeholder="0.00"
          />
        </div>

        <div className="form-group">
          <label>Deposit Date *</label>
          <input
            type="date"
            name="deposit_date"
            value={formData.deposit_date}
            onChange={handleChange}
            required
          />
        </div>

        <div className="form-group">
          <label>Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
            placeholder="Optional notes about this deposit..."
          />
        </div>

        {error && <div className="error">{error}</div>}

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Adding...' : 'Add Deposit'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default DepositForm;

