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
  const [fieldErrors, setFieldErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
    
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };
  
  const validateForm = () => {
    const errors = {};
    
    // Account name is required
    if (!formData.name || formData.name.trim() === '') {
      errors.name = 'Account name is required';
    }
    
    // Initial balance validation (if provided, must be valid number)
    if (formData.initial_balance && (isNaN(parseFloat(formData.initial_balance)) || parseFloat(formData.initial_balance) < 0)) {
      errors.initial_balance = 'Initial balance must be a positive number or zero';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});
    
    // Validate form before submitting
    if (!validateForm()) {
      // Scroll to first error
      const firstErrorField = Object.keys(fieldErrors)[0];
      if (firstErrorField) {
        const element = document.querySelector(`[name="${firstErrorField}"]`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
          element.focus();
        }
      }
      return;
    }
    
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
            className={fieldErrors.name ? 'error-field' : ''}
          />
          {fieldErrors.name && (
            <div className="field-error">{fieldErrors.name}</div>
          )}
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
            className={fieldErrors.initial_balance ? 'error-field' : ''}
          />
          {fieldErrors.initial_balance && (
            <div className="field-error">{fieldErrors.initial_balance}</div>
          )}
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

