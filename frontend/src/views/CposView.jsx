import { useState } from 'react';
import Spinner from '../components/Spinner.jsx';
import ConfirmDialog from '../components/ConfirmDialog.jsx';
import CpoModal from '../modals/CpoModal.jsx';
import { fmtEur } from '../format.js';

export default function CposView({ api, cpos, loading, reload, toast }) {
  const [showModal, setShowModal] = useState(false);
  const [editCpo, setEditCpo] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);

  const doDelete = async () => {
    try { await api.deleteCpo(deleteTarget); toast('CPO deleted.', 'success'); reload(); }
    catch (e) { toast(e.message, 'error'); }
    setDeleteTarget(null);
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="section-header">
        <div className="section-title">Charge Point Operators</div>
        <button className="btn btn-primary btn-sm" onClick={() => { setEditCpo(null); setShowModal(true); }}>+ Add CPO</button>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Name</th><th>Default price</th><th></th></tr></thead>
              <tbody>
                {cpos.length === 0 && <tr><td colSpan="3"><div className="empty-state"><div className="empty-state-icon">🔌</div><div className="empty-state-text">No CPOs yet.</div></div></td></tr>}
                {cpos.map((c) => (
                  <tr key={c.id}>
                    <td style={{ fontWeight: 500 }}>{c.name}</td>
                    <td className="muted">{fmtEur(c.default_price)} €/kWh</td>
                    <td>
                      <div className="row-actions">
                        <button className="action-btn" onClick={() => { setEditCpo(c); setShowModal(true); }}>✎</button>
                        <button className="action-btn danger" onClick={() => setDeleteTarget(c.id)}>🗑</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <CpoModal open={showModal} onClose={() => setShowModal(false)} onSaved={() => { setShowModal(false); reload(); }} cpo={editCpo} api={api} toast={toast} />
      <ConfirmDialog open={!!deleteTarget} message="Delete this CPO? This cannot be undone." onConfirm={doDelete} onCancel={() => setDeleteTarget(null)} />
    </div>
  );
}
