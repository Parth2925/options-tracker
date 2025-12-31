import React, { useState, useEffect } from 'react';

function HistoryDialog({ trade, onClose }) {
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
        onClose();
      }
    }
    setDragStartPos(null);
    setDragStartTarget(null);
  };

  if (!trade || !trade.closing_trades || trade.closing_trades.length === 0) {
    return null;
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    const [year, month, day] = dateStr.split('T')[0].split('-');
    return new Date(parseInt(year), parseInt(month) - 1, parseInt(day)).toLocaleDateString();
  };

  const formatCloseMethod = (closeMethod, status, tradeAction) => {
    if (closeMethod) {
      return closeMethod.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    if (status === 'Expired') return 'Expired';
    if (status === 'Assigned') return 'Assigned';
    if (tradeAction === 'Bought to Close') return 'Buy to Close';
    if (tradeAction === 'Sold to Close') return 'Sell to Close';
    return status || tradeAction || 'Unknown';
  };

  const totalClosed = trade.closing_trades.reduce((sum, ct) => sum + (ct.contract_quantity || 0), 0);
  const totalPnl = trade.closing_trades.reduce((sum, ct) => sum + (ct.realized_pnl || 0), 0);

  return (
    <div 
      className="modal-overlay" 
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    >
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '700px' }}>
        <div className="modal-header">
          <h2>Close History</h2>
          <button 
            className="modal-close" 
            onClick={onClose}
            type="button"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="modal-body">
          <div style={{ marginBottom: '20px' }} className="history-summary">
            <div className="history-summary-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <strong>Symbol:</strong> {trade.symbol}
              </div>
              <div>
                <strong>Trade Type:</strong> {trade.trade_type}
              </div>
            </div>
            <div className="history-summary-row" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <strong>Total Contracts:</strong> {trade.contract_quantity}
              </div>
              <div>
                <strong>Remaining:</strong> {trade.remaining_open_quantity || 0} contracts
              </div>
            </div>
            <div className="history-summary-row" style={{ display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <strong>Closed:</strong> {totalClosed} contracts
              </div>
              <div style={{ 
                color: totalPnl >= 0 ? '#28a745' : '#dc3545',
                fontWeight: 'bold'
              }}>
                <strong>Total P&L:</strong> ${totalPnl.toFixed(2)}
              </div>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: 'var(--bg-tertiary)' }}>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Method</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>Date</th>
                  <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>Quantity</th>
                  <th style={{ padding: '10px', textAlign: 'right', borderBottom: '2px solid var(--border-color)' }}>P&L</th>
                </tr>
              </thead>
              <tbody>
                {trade.closing_trades.map((ct, index) => (
                  <tr key={ct.id || index} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '10px' }}>
                      {formatCloseMethod(ct.close_method, ct.status, ct.trade_action)}
                    </td>
                    <td style={{ padding: '10px' }}>
                      {formatDate(ct.close_date || ct.trade_date)}
                    </td>
                    <td style={{ padding: '10px', textAlign: 'right' }}>
                      {ct.contract_quantity || 0}
                    </td>
                    <td style={{ 
                      padding: '10px', 
                      textAlign: 'right',
                      color: (ct.realized_pnl || 0) >= 0 ? '#28a745' : '#dc3545',
                      fontWeight: 'bold'
                    }}>
                      ${(ct.realized_pnl || 0).toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ backgroundColor: 'var(--bg-tertiary)', fontWeight: 'bold' }}>
                  <td style={{ padding: '10px' }} colSpan="2">Total</td>
                  <td style={{ padding: '10px', textAlign: 'right' }}>{totalClosed}</td>
                  <td style={{ 
                    padding: '10px', 
                    textAlign: 'right',
                    color: totalPnl >= 0 ? '#28a745' : '#dc3545'
                  }}>
                    ${totalPnl.toFixed(2)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
        <div className="modal-footer">
          <button 
            className="btn btn-secondary" 
            onClick={onClose}
            type="button"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

export default HistoryDialog;

