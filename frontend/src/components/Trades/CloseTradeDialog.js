import React, { useState, useEffect } from 'react';
import api from '../../utils/api';
import { useToast } from '../../contexts/ToastContext';

function CloseTradeDialog({ trade, accounts, onSuccess, onCancel }) {
  const { showToast } = useToast();
  const [loading, setLoading] = useState(false);
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
    // Only track if clicking on the overlay itself (not modal content)
    if (e.target.classList.contains('modal-overlay')) {
      setDragStartPos({ x: e.clientX, y: e.clientY });
      setDragStartTarget(e.target);
    }
  };

  // Handle mouse up - only close if it wasn't a drag operation
  const handleMouseUp = (e) => {
    if (dragStartTarget && e.target === dragStartTarget) {
      // Check if mouse moved significantly (more than 5px) - indicates a drag
      const moved = dragStartPos && (
        Math.abs(e.clientX - dragStartPos.x) > 5 || 
        Math.abs(e.clientY - dragStartPos.y) > 5
      );
      
      // Only close if it wasn't a drag operation
      if (!moved) {
        onCancel();
      }
    }
    setDragStartPos(null);
    setDragStartTarget(null);
  };
  
  // Get account's default fee
  const getAccountDefaultFee = () => {
    if (!accounts || !trade.account_id) return 0;
    const account = accounts.find(acc => acc.id === trade.account_id);
    return account?.default_fee || 0;
  };

  const [formData, setFormData] = useState({
    close_method: '',
    close_date: trade.expiration_date ? trade.expiration_date.split('T')[0] : new Date().toISOString().split('T')[0],
    trade_price: '',
    fees: '',
    contract_quantity: trade.remaining_open_quantity || trade.contract_quantity || 1,
    assignment_price: trade.strike_price || '',
    notes: ''
  });

  const getAvailableCloseMethods = () => {
    if (trade.trade_type === 'LEAPS') {
      return [
        { value: 'sell_to_close', label: 'Sell to Close' },
        { value: 'expired', label: 'Expired' },
        { value: 'exercise', label: 'Exercise' }
      ];
    } else if (trade.trade_type === 'CSP' || trade.trade_type === 'Covered Call') {
      return [
        { value: 'buy_to_close', label: 'Buy to Close' },
        { value: 'expired', label: 'Expired' },
        { value: 'assigned', label: 'Assigned' }
      ];
    }
    return [];
  };

  const availableMethods = getAvailableCloseMethods();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const updated = {
        ...prev,
        [name]: value
      };
      
      // Auto-populate default fee when close_method changes to buy_to_close or sell_to_close
      if (name === 'close_method' && (value === 'buy_to_close' || value === 'sell_to_close')) {
        const defaultFee = getAccountDefaultFee();
        // Only set if fees field is currently empty (allows user override)
        if (!prev.fees || prev.fees === '') {
          updated.fees = defaultFee > 0 ? defaultFee.toString() : '';
        }
      }
      // Clear fees if close_method changes to something that doesn't have fees
      else if (name === 'close_method' && value !== 'buy_to_close' && value !== 'sell_to_close') {
        updated.fees = '';
      }
      
      return updated;
    });
    
    // Clear field error when user starts typing
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const [fieldErrors, setFieldErrors] = useState({});

  const validateForm = () => {
    const errors = {};

    if (!formData.close_method) {
      errors.close_method = 'Please select a close method';
    }

    if (!formData.close_date) {
      errors.close_date = 'Close date is required';
    } else {
      const closeDate = new Date(formData.close_date);
      const tradeDate = new Date(trade.trade_date);
      if (closeDate < tradeDate) {
        errors.close_date = 'Close date cannot be before the trade date';
      }
      const today = new Date();
      today.setHours(23, 59, 59, 999);
      if (closeDate > today) {
        errors.close_date = 'Close date cannot be in the future';
      }
    }

    const remainingQty = trade.remaining_open_quantity || trade.contract_quantity || 1;
    if (!formData.contract_quantity || parseInt(formData.contract_quantity) <= 0) {
      errors.contract_quantity = 'Contract quantity must be at least 1';
    } else {
      const qty = parseInt(formData.contract_quantity);
      if (qty > remainingQty) {
        errors.contract_quantity = `Cannot close ${qty} contracts. Only ${remainingQty} contracts remaining open.`;
      }
    }

    if (formData.close_method === 'buy_to_close' || formData.close_method === 'sell_to_close') {
      if (!formData.trade_price || formData.trade_price.trim() === '') {
        errors.trade_price = 'Trade price is required for Buy/Sell to Close';
      } else {
        const price = parseFloat(formData.trade_price);
        if (isNaN(price) || price <= 0) {
          errors.trade_price = 'Trade price must be a positive number';
        } else if (price > 1000) {
          errors.trade_price = 'Trade price seems unusually high. Please verify.';
        }
      }
      if (formData.fees && formData.fees.trim() !== '') {
        const fees = parseFloat(formData.fees);
        if (isNaN(fees) || fees < 0) {
          errors.fees = 'Fees must be 0 or greater';
        }
      }
    } else if (formData.close_method === 'assigned') {
      if (!formData.assignment_price || formData.assignment_price.trim() === '') {
        errors.assignment_price = 'Assignment price is required';
      } else {
        const price = parseFloat(formData.assignment_price);
        if (isNaN(price) || price <= 0) {
          errors.assignment_price = 'Assignment price must be a positive number';
        }
      }
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
        close_method: formData.close_method,
        close_date: formData.close_date,
        contract_quantity: parseInt(formData.contract_quantity) || 1,
        notes: formData.notes || null
      };

      // Add method-specific fields
      if (formData.close_method === 'buy_to_close' || formData.close_method === 'sell_to_close') {
        payload.trade_price = parseFloat(formData.trade_price);
        payload.fees = parseFloat(formData.fees) || 0;
      } else if (formData.close_method === 'assigned') {
        payload.assignment_price = parseFloat(formData.assignment_price);
      }

      await api.post(`/trades/${trade.id}/close`, payload);
      showToast('Trade closed successfully!', 'success');
      onSuccess();
    } catch (error) {
      console.error('Error closing trade:', error);
      const errorMessage = error.response?.data?.error || 'Failed to close trade';
      showToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const requiresTradePrice = formData.close_method === 'buy_to_close' || formData.close_method === 'sell_to_close';
  const requiresAssignmentPrice = formData.close_method === 'assigned';

  return (
    <div 
      className="modal-overlay" 
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Close Trade</h2>
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
            <label>Close Method *</label>
            <select
              name="close_method"
              value={formData.close_method}
              onChange={handleChange}
              required
              className={fieldErrors.close_method ? 'error-field' : ''}
            >
              <option value="">Select close method</option>
              {availableMethods.map(method => (
                <option key={method.value} value={method.value}>
                  {method.label}
                </option>
              ))}
            </select>
            {fieldErrors.close_method && (
              <div className="field-error">{fieldErrors.close_method}</div>
            )}
          </div>

          <div className="form-group">
            <label>Close Date *</label>
            <input
              type="date"
              name="close_date"
              value={formData.close_date}
              onChange={handleChange}
              required
              className={fieldErrors.close_date ? 'error-field' : ''}
            />
            {fieldErrors.close_date && (
              <div className="field-error">{fieldErrors.close_date}</div>
            )}
          </div>

          {formData.close_method && (
            <>
              <div className="form-group">
                <label>Contract Quantity</label>
                <input
                  type="number"
                  name="contract_quantity"
                  value={formData.contract_quantity}
                  onChange={handleChange}
                  min="1"
                  max={trade.remaining_open_quantity || trade.contract_quantity || 1}
                  className={fieldErrors.contract_quantity ? 'error-field' : ''}
                />
                <small style={{ color: '#666', fontSize: '12px' }}>
                  Remaining: {trade.remaining_open_quantity || trade.contract_quantity || 0} contracts
                </small>
                {fieldErrors.contract_quantity && (
                  <div className="field-error">{fieldErrors.contract_quantity}</div>
                )}
              </div>

              {requiresTradePrice && (
                <>
                  <div className="form-group">
                    <label>Trade Price *</label>
                    <input
                      type="number"
                      step="0.01"
                      name="trade_price"
                      value={formData.trade_price}
                      onChange={handleChange}
                      required
                      placeholder="0.00"
                      className={fieldErrors.trade_price ? 'error-field' : ''}
                    />
                    {fieldErrors.trade_price && (
                      <div className="field-error">{fieldErrors.trade_price}</div>
                    )}
                  </div>
                  <div className="form-group">
                    <label>Fees</label>
                    <input
                      type="number"
                      step="0.01"
                      name="fees"
                      value={formData.fees}
                      onChange={handleChange}
                      placeholder={getAccountDefaultFee() > 0 ? `${getAccountDefaultFee()}` : "0.00"}
                      className={fieldErrors.fees ? 'error-field' : ''}
                    />
                    {getAccountDefaultFee() > 0 && (
                      <small style={{ color: '#666', fontSize: '12px', display: 'block', marginTop: '4px' }}>
                        Default fee: ${getAccountDefaultFee()} per contract
                      </small>
                    )}
                    {fieldErrors.fees && (
                      <div className="field-error">{fieldErrors.fees}</div>
                    )}
                  </div>
                </>
              )}

              {requiresAssignmentPrice && (
                <div className="form-group">
                  <label>Assignment Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    name="assignment_price"
                    value={formData.assignment_price}
                    onChange={handleChange}
                    required
                    placeholder={trade.strike_price || '0.00'}
                    className={fieldErrors.assignment_price ? 'error-field' : ''}
                  />
                  <small style={{ color: '#666', fontSize: '12px' }}>
                    Defaults to strike price: ${trade.strike_price || 'N/A'}
                  </small>
                  {fieldErrors.assignment_price && (
                    <div className="field-error">{fieldErrors.assignment_price}</div>
                  )}
                </div>
              )}

              <div className="form-group">
                <label>Notes</label>
                <textarea
                  name="notes"
                  value={formData.notes}
                  onChange={handleChange}
                  rows="3"
                  placeholder="Optional notes..."
                />
              </div>
            </>
          )}

          </div>
          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={onCancel} disabled={loading}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading || !formData.close_method}>
              {loading ? 'Closing...' : 'Close Trade'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default CloseTradeDialog;
