import { useEffect, useState } from 'react';
import Modal from '../components/Modal.jsx';
import { fmtEur } from '../format.js';

export default function CpoModal({ open, onClose, onSaved, cpo, api, toast }) {
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (open) {
      setName(cpo?.name || '');
      setPrice(cpo ? fmtEur(cpo.default_price) : '');
      setErr('');
    }
  }, [open, cpo]);

  const submit = async () => {
    if (!name.trim()) { setErr('Name is required.'); return; }
    if (!price || isNaN(parseFloat(price))) { setErr('Default price is required.'); return; }
    setSaving(true); setErr('');
    try {
      const payload = { name: name.trim(), default_price: Math.round(parseFloat(price) * 100) };
      if (cpo) await api.updateCpo(cpo.id, payload);
      else await api.createCpo(payload);
      toast('CPO saved!', 'success');
      onSaved();
    } catch (e) { setErr(e.message); }
    setSaving(false);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={cpo ? 'Edit CPO' : 'New CPO'}
      footer={(
        <>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>{saving ? 'Saving…' : 'Save CPO'}</button>
        </>
      )}
    >
      {err && <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '9px 13px', fontSize: 13, color: 'var(--red)', marginBottom: 14 }}>{err}</div>}
      <div className="form-group">
        <label className="form-label">CPO Name</label>
        <input type="text" className="form-input" placeholder="e.g. Ionity, EnBW" value={name} onChange={(e) => setName(e.target.value)} />
      </div>
      <div className="form-group">
        <label className="form-label">Default price per kWh (€)</label>
        <input type="number" className="form-input" placeholder="e.g. 0.49" step="0.001" min="0" value={price} onChange={(e) => setPrice(e.target.value)} />
        <p className="form-hint">Used when no price is specified at charging time.</p>
      </div>
    </Modal>
  );
}
