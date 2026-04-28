import { useEffect, useState } from 'react';
import Modal from '../components/Modal.jsx';

export default function CarModal({ open, onClose, onSaved, car, api, toast }) {
  const [f, setF] = useState({ name: '', make: '', model: '', color: '#3b82f6', odometer: '', battery_capacity: '' });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  useEffect(() => {
    if (open) {
      setF({
        name: car?.name || '',
        make: car?.make || '',
        model: car?.model || '',
        color: car?.color || '#3b82f6',
        odometer: car?.odometer?.toString() || '0',
        battery_capacity: car?.battery_capacity?.toString() || '',
      });
      setErr('');
    }
  }, [open, car]);

  const submit = async () => {
    if (!f.name.trim()) { setErr('Name is required.'); return; }
    if (!f.battery_capacity) { setErr('Battery capacity is required.'); return; }
    setSaving(true); setErr('');
    try {
      const payload = {
        name: f.name,
        make: f.make || undefined,
        model: f.model || undefined,
        color: f.color,
        odometer: parseInt(f.odometer) || 0,
        battery_capacity: parseInt(f.battery_capacity),
      };
      if (car) await api.updateCar(car.id, payload);
      else await api.createCar(payload);
      toast('Car saved!', 'success');
      onSaved();
    } catch (e) { setErr(e.message); }
    setSaving(false);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={car ? 'Edit Car' : 'Add Car'}
      footer={(
        <>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>{saving ? 'Saving…' : 'Save car'}</button>
        </>
      )}
    >
      {err && <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '9px 13px', fontSize: 13, color: 'var(--red)', marginBottom: 14 }}>{err}</div>}
      <div className="form-group">
        <label className="form-label">Name / Nickname</label>
        <input type="text" className="form-input" placeholder="e.g. My Model 3" value={f.name} onChange={(e) => set('name', e.target.value)} />
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Make</label>
          <input type="text" className="form-input" placeholder="e.g. Tesla" value={f.make} onChange={(e) => set('make', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Model</label>
          <input type="text" className="form-input" placeholder="e.g. Model 3" value={f.model} onChange={(e) => set('model', e.target.value)} />
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Battery capacity (kWh)</label>
          <input type="number" className="form-input" placeholder="e.g. 75" min="1" value={f.battery_capacity} onChange={(e) => set('battery_capacity', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Initial odometer (km)</label>
          <input type="number" className="form-input" placeholder="0" min="0" value={f.odometer} onChange={(e) => set('odometer', e.target.value)} />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Color</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <input type="color" value={f.color} onChange={(e) => set('color', e.target.value)} style={{ width: 40, height: 38, padding: 2, border: '1.5px solid var(--border)', borderRadius: 8, cursor: 'pointer' }} />
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>{f.color}</span>
        </div>
      </div>
    </Modal>
  );
}
