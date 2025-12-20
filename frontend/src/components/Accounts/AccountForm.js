import React, { useState } from 'react';
import api from '../../utils/api';

function AccountForm({ onSuccess, onCancel }) {
  const [formData, setFormData] = useState({
    name: '',
    account_type: '',
    initial_balance: '',
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
        initial_balance: formData.initial_balance ? parseFloat(formData.initial_balance) : 0,
      };

      await api.post('/accounts', payload);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.msg || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '20px' }}>
      <h3>Create New Account</h3>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Account Name *</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="e.g., Main Trading Account"
          />
        </div>

        <div className="form-group">
          <label>Account Type</label>
          <select
            name="account_type"
            value={formData.account_type}
            onChange={handleChange}
          >
            <option value="">Select Type</option>
            <option value="IRA">IRA</option>
            <option value="Taxable">Taxable</option>
            <option value="Margin">Margin</option>
            <option value="Cash">Cash</option>
          </select>
        </div>

        <div className="form-group">
          <label>Initial Balance</label>
          <input
            type="number"
            step="0.01"
            name="initial_balance"
            value={formData.initial_balance}
            onChange={handleChange}
            placeholder="0.00"
          />
        </div>

        {error && <div className="error">{error}</div>}

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Account'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default AccountForm;

