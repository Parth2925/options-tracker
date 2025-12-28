import React, { useState } from 'react';
import api from '../../utils/api';

function WithdrawalForm({ accountId, onSuccess, onCancel }) {
  // Helper function to get today's date in local timezone (YYYY-MM-DD format)
  const getTodayLocalDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [formData, setFormData] = useState({
    amount: '',
    withdrawal_date: getTodayLocalDate(),
    notes: '',
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
    
    // Amount is required and must be positive
    if (!formData.amount || formData.amount === '') {
      errors.amount = 'Withdrawal amount is required';
    } else if (isNaN(parseFloat(formData.amount)) || parseFloat(formData.amount) <= 0) {
      errors.amount = 'Withdrawal amount must be a positive number';
    }
    
    // Withdrawal date is required
    if (!formData.withdrawal_date) {
      errors.withdrawal_date = 'Withdrawal date is required';
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
        amount: parseFloat(formData.amount),
      };

      await api.post(`/accounts/${accountId}/withdrawals`, payload);
      onSuccess();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to add withdrawal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ marginBottom: '20px' }}>
      <h3>Add Withdrawal</h3>
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
            className={fieldErrors.amount ? 'error-field' : ''}
          />
          {fieldErrors.amount && (
            <div className="field-error">{fieldErrors.amount}</div>
          )}
        </div>

        <div className="form-group">
          <label>Withdrawal Date *</label>
          <input
            type="date"
            name="withdrawal_date"
            value={formData.withdrawal_date}
            onChange={handleChange}
            required
            className={fieldErrors.withdrawal_date ? 'error-field' : ''}
          />
          {fieldErrors.withdrawal_date && (
            <div className="field-error">{fieldErrors.withdrawal_date}</div>
          )}
        </div>

        <div className="form-group">
          <label>Notes</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows="3"
            placeholder="Optional notes about this withdrawal..."
          />
        </div>

        {error && <div className="error">{error}</div>}

        <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Adding...' : 'Add Withdrawal'}
          </button>
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}

export default WithdrawalForm;

