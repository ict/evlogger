export default function ConfirmDialog({ open, message, onConfirm, onCancel, title = 'Confirm delete', confirmLabel = 'Delete', danger = true }) {
  if (!open) return null;
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal-box" style={{ maxWidth: 380 }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header"><div className="modal-title">{title}</div></div>
        <div className="modal-body">
          <p style={{ marginBottom: 20, lineHeight: 1.5, color: 'var(--text-muted)' }}>{message}</p>
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
            <button className="btn btn-ghost" onClick={onCancel}>Cancel</button>
            <button className={`btn ${danger ? 'btn-danger' : 'btn-primary'}`} onClick={onConfirm}>{confirmLabel}</button>
          </div>
        </div>
      </div>
    </div>
  );
}
