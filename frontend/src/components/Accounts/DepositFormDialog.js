import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';
import './Accounts.css';

function DepositFormDialog({ accountId, onSuccess, onCancel }) {
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

  // Helper function to get today's date in local timezone
  const getTodayLocalDate = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [formData, setFormData] = useState({
    amount: '',
    deposit_date: getTodayLocalDate(),
    notes: '',
  });

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
    
    if (!formData.amount || formData.amount === '') {
      errors.amount = 'Deposit amount is required';
    } else if (isNaN(parseFloat(formData.amount)) || parseFloat(formData.amount) <= 0) {
      errors.amount = 'Deposit amount must be a positive number';
    }
    
    if (!formData.deposit_date) {
      errors.deposit_date = 'Deposit date is required';
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
        ...formData,
        amount: parseFloat(formData.amount),
      };

      await api.post(`/accounts/${accountId}/deposits`, payload);
      showToast('Deposit added successfully!', 'success');
      onSuccess();
    } catch (err) {
      showToast(err.response?.data?.error || 'Failed to add deposit', 'error');
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
          <h2>Add Deposit</h2>
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
              <label>Deposit Date *</label>
              <input
                type="date"
                name="deposit_date"
                value={formData.deposit_date}
                onChange={handleChange}
                required
                className={fieldErrors.deposit_date ? 'error-field' : ''}
              />
              {fieldErrors.deposit_date && (
                <div className="field-error">{fieldErrors.deposit_date}</div>
              )}
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
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Adding...' : 'Add Deposit'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default DepositFormDialog;

