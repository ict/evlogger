import { useState } from 'react';
import Spinner from '../components/Spinner.jsx';
import ConfirmDialog from '../components/ConfirmDialog.jsx';
import CpoModal from '../modals/CpoModal.jsx';
import { fmtEur } from '../format.js';

function ArchiveIcon() {
  return (
    <svg className="archived-icon" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" role="img" aria-label="Archived">
      <title>Archived</title>
      <rect width="20" height="5" x="2" y="3" rx="1" /><path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8" /><path d="M10 12h4" />
    </svg>
  );
}

export default function CposView({ api, cpos, loading, reload, toast }) {
  const [showModal, setShowModal] = useState(false);
  const [editCpo, setEditCpo] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [selected, setSelected] = useState(() => new Set());
  const active = cpos.filter((c) => !c.archived);
  const archived = cpos.filter((c) => c.archived);
  const visible = showArchived ? [...active, ...archived] : active;

  const toggle = (id) => setSelected((prev) => {
    const next = new Set(prev);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });
  const picked = visible.filter((c) => selected.has(c.id));
  const pickedActive = picked.filter((c) => !c.archived);
  const pickedArchived = picked.filter((c) => c.archived);
  const allSelected = visible.length > 0 && picked.length === visible.length;
  const toggleAll = () => setSelected(allSelected ? new Set() : new Set(visible.map((c) => c.id)));

  const setArchived = async (targets, flag) => {
    const results = await Promise.allSettled(
      targets.map((c) => api.updateCpo(c.id, { name: c.name, default_price: c.default_price, archived: flag }))
    );
    const failed = results.filter((r) => r.status === 'rejected').length;
    const verb = flag ? 'archived' : 'restored';
    if (failed) toast(`${failed} of ${targets.length} could not be ${verb}.`, 'error');
    else toast(`${targets.length} CPO${targets.length === 1 ? '' : 's'} ${verb}.`, 'success');
    setSelected(new Set());
    reload();
  };

  const restore = async (c) => {
    try { await api.updateCpo(c.id, { name: c.name, default_price: c.default_price, archived: false }); toast('CPO restored.', 'success'); reload(); }
    catch (e) { toast(e.message, 'error'); }
  };

  const doDelete = async () => {
    try { await api.deleteCpo(deleteTarget); toast('CPO removed.', 'success'); reload(); }
    catch (e) { toast(e.message, 'error'); }
    setDeleteTarget(null);
  };

  return (
    <div style={{ maxWidth: 800, margin: '0 auto' }}>
      <div className="section-header">
        <div className="section-title">Charge Point Operators</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {picked.length > 0 && (
            <>
              <span className="muted" style={{ fontSize: 13 }}>{picked.length} selected</span>
              <button className="btn btn-ghost btn-sm" onClick={() => setSelected(new Set())}>Cancel</button>
              {pickedArchived.length > 0 && <button className="btn btn-primary btn-sm" onClick={() => setArchived(pickedArchived, false)}>Unarchive</button>}
              {pickedActive.length > 0 && <button className="btn btn-primary btn-sm" onClick={() => setArchived(pickedActive, true)}>Archive</button>}
            </>
          )}
          {archived.length > 0 && (
            <label className="muted" style={{ display: 'flex', gap: 4, alignItems: 'center', fontSize: 13 }}>
              <input type="checkbox" checked={showArchived} onChange={(e) => setShowArchived(e.target.checked)} />
              Show archived ({archived.length})
            </label>
          )}
          <button className="btn btn-primary btn-sm" onClick={() => { setEditCpo(null); setShowModal(true); }}>+ Add CPO</button>
        </div>
      </div>
      <div className="card">
        {loading ? <Spinner /> : (
          <div className="table-wrap">
            <table>
              <thead><tr>
                <th className="col-narrow"><input type="checkbox" aria-label="Select all" checked={allSelected} onChange={toggleAll} disabled={visible.length === 0} /></th>
                <th>Name</th><th>Default price</th><th className="col-narrow"></th>
              </tr></thead>
              <tbody>
                {visible.length === 0 && <tr><td colSpan="4"><div className="empty-state"><div className="empty-state-icon">🔌</div><div className="empty-state-text">No CPOs yet.</div></div></td></tr>}
                {visible.map((c) => (
                  <tr key={c.id} style={c.archived ? { opacity: 0.6 } : undefined}>
                    <td className="col-narrow">
                      <input type="checkbox" aria-label={`Select ${c.name}`} checked={selected.has(c.id)} onChange={() => toggle(c.id)} />
                    </td>
                    <td style={{ fontWeight: 500 }}>{c.name}{c.archived && <ArchiveIcon />}</td>
                    <td className="muted">{fmtEur(c.default_price)} €/kWh</td>
                    <td className="col-narrow">
                      <div className="row-actions row-actions-end">
                        <button className="action-btn" onClick={() => { setEditCpo(c); setShowModal(true); }}>✎</button>
                        {c.archived
                          ? <button className="action-btn" title="Restore" onClick={() => restore(c)}>↺</button>
                          : <button className="action-btn danger" onClick={() => setDeleteTarget(c.id)}>🗑</button>}
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
      <ConfirmDialog open={!!deleteTarget} message="Delete this CPO? If existing charges use it, it is archived instead and can be restored later." onConfirm={doDelete} onCancel={() => setDeleteTarget(null)} />
    </div>
  );
}
