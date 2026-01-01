import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';
import './Accounts.css';

function AccountFormDialog({ account, onSuccess, onCancel }) {
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
    name: '',
    account_type: '',
    initial_balance: '',
    default_fee: '',
    assignment_fee: '',
  });

  // Initialize form data if editing
  useEffect(() => {
    if (account) {
      setFormData({
        name: account.name || '',
        account_type: account.account_type || '',
        initial_balance: account.initial_balance || '',
        default_fee: account.default_fee || '',
        assignment_fee: account.assignment_fee || '',
      });
    }
  }, [account]);

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
    
    if (!formData.name || formData.name.trim() === '') {
      errors.name = 'Account name is required';
    } else if (formData.name.trim().length > 100) {
      errors.name = 'Account name must be 100 characters or less';
    }
    
    if (formData.initial_balance) {
      const balanceStr = String(formData.initial_balance);
      if (balanceStr.trim() !== '') {
        const balance = parseFloat(formData.initial_balance);
        if (isNaN(balance)) {
          errors.initial_balance = 'Initial balance must be a number';
        } else if (balance < 0) {
          errors.initial_balance = 'Initial balance cannot be negative';
        } else if (balance > 100000000) {
          errors.initial_balance = 'Initial balance seems unusually high. Please verify.';
        }
      }
    }
    
    if (formData.default_fee) {
      const feeStr = String(formData.default_fee);
      if (feeStr.trim() !== '') {
        const fee = parseFloat(formData.default_fee);
        if (isNaN(fee)) {
          errors.default_fee = 'Default fee must be a number';
        } else if (fee < 0) {
          errors.default_fee = 'Default fee cannot be negative';
        } else if (fee > 1000) {
          errors.default_fee = 'Default fee seems unusually high. Please verify.';
        }
      }
    }
    
    if (formData.assignment_fee) {
      const feeStr = String(formData.assignment_fee);
      if (feeStr.trim() !== '') {
        const fee = parseFloat(formData.assignment_fee);
        if (isNaN(fee)) {
          errors.assignment_fee = 'Assignment fee must be a number';
        } else if (fee < 0) {
          errors.assignment_fee = 'Assignment fee cannot be negative';
        } else if (fee > 1000) {
          errors.assignment_fee = 'Assignment fee seems unusually high. Please verify.';
        }
      }
    }
    
    if (!formData.account_type) {
      errors.account_type = 'Account type is required';
    }
    
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      const firstError = Object.values(fieldErrors)[0];
      showToast(firstError || 'Please fix the errors in the form', 'error');
      // Scroll to first error field
      const firstErrorField = document.querySelector('.error-field');
      if (firstErrorField) {
        firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        firstErrorField.focus();
      }
      return;
    }
    
    setLoading(true);

    try {
      const payload = {
        ...formData,
        initial_balance: formData.initial_balance ? parseFloat(formData.initial_balance) : 0,
        default_fee: formData.default_fee ? parseFloat(formData.default_fee) : 0,
        assignment_fee: formData.assignment_fee ? parseFloat(formData.assignment_fee) : 0,
      };

      if (account) {
        // Update existing account
        await api.put(`/accounts/${account.id}`, payload);
        showToast('Account updated successfully!', 'success');
      } else {
        // Create new account
        await api.post('/accounts', payload);
        showToast('Account created successfully!', 'success');
      }
      onSuccess();
    } catch (err) {
      showToast(err.response?.data?.error || err.response?.data?.msg || 'Failed to create account', 'error');
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
          <h2>{account ? 'Edit Account' : 'Create New Account'}</h2>
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
              <label>Account Type *</label>
              <select
                name="account_type"
                value={formData.account_type}
                onChange={handleChange}
                required
                className={fieldErrors.account_type ? 'error-field' : ''}
              >
                <option value="">Select Type</option>
                <option value="IRA">IRA</option>
                <option value="Taxable">Taxable</option>
                <option value="Margin">Margin</option>
                <option value="Cash">Cash</option>
              </select>
              {fieldErrors.account_type && (
                <div className="field-error">{fieldErrors.account_type}</div>
              )}
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

            <div className="form-group">
              <label>Default Fee per Contract</label>
              <input
                type="number"
                step="0.01"
                name="default_fee"
                value={formData.default_fee}
                onChange={handleChange}
                placeholder="0.00"
                className={fieldErrors.default_fee ? 'error-field' : ''}
              />
              <small style={{ color: 'var(--text-secondary)', fontSize: '12px', display: 'block', marginTop: '5px' }}>
                This fee will be automatically filled when creating new trades for this account. You can still override it per trade.
              </small>
              {fieldErrors.default_fee && (
                <div className="field-error">{fieldErrors.default_fee}</div>
              )}
            </div>

            <div className="form-group">
              <label>Default Assignment Fee</label>
              <input
                type="number"
                step="0.01"
                name="assignment_fee"
                value={formData.assignment_fee}
                onChange={handleChange}
                placeholder="0.00"
                className={fieldErrors.assignment_fee ? 'error-field' : ''}
              />
              <small style={{ color: 'var(--text-secondary)', fontSize: '12px', display: 'block', marginTop: '5px' }}>
                Default fee charged by your broker for assignment/exercise (typically $15-25). This will be auto-populated when closing trades as "Assigned" or "Called Away". You can still override it per trade.
              </small>
              {fieldErrors.assignment_fee && (
                <div className="field-error">{fieldErrors.assignment_fee}</div>
              )}
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Saving...' : (account ? 'Update' : 'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AccountFormDialog;

