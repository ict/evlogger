import { useEffect, useState } from 'react';
import Modal from '../components/Modal.jsx';
import { parseMoney } from '../format.js';

const pad = (n) => String(n).padStart(2, '0');
const today = () => { const d = new Date(); return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`; };

export default function RetireCarModal({ open, onClose, onSaved, car, api, toast }) {
  const [f, setF] = useState({ sale_date: today(), sale_price: '', sale_odometer: '' });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  useEffect(() => {
    if (open) {
      setF({ sale_date: today(), sale_price: '', sale_odometer: car?.odometer != null ? car.odometer.toString() : '' });
      setErr('');
    }
  }, [open, car]);

  const submit = async () => {
    if (!car) return;
    if (!f.sale_date) { setErr('Sale date is required.'); return; }
    let salePrice = 0;
    if (f.sale_price.trim()) {
      salePrice = parseMoney(f.sale_price);
      if (salePrice == null || salePrice < 0) { setErr('Sale price is invalid.'); return; }
    }
    if (f.sale_odometer === '' || isNaN(parseInt(f.sale_odometer))) { setErr('Final odometer is required.'); return; }
    setSaving(true); setErr('');
    try {
      await api.updateCar(car.id, {
        name: car.name,
        make: car.make || undefined,
        model: car.model || undefined,
        color: car.color,
        odometer: car.odometer,
        battery_capacity: car.battery_capacity,
        purchase_price: car.purchase_price ?? null,
        purchase_date: car.purchase_date ?? null,
        purchase_odometer: car.purchase_odometer ?? null,
        sale_price: salePrice,
        sale_date: f.sale_date,
        sale_odometer: parseInt(f.sale_odometer),
      });
      toast(`${car.name} retired`, 'success');
      onSaved();
    } catch (e) { setErr(e.message); }
    setSaving(false);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Retire ${car?.name || ''}`}
      footer={(
        <>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>{saving ? 'Saving…' : 'Retire car'}</button>
        </>
      )}
    >
      {err && <div style={{ background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', borderRadius: 8, padding: '9px 13px', fontSize: 13, color: 'var(--red)', marginBottom: 14 }}>{err}</div>}
      <p style={{ fontSize: 13, lineHeight: 1.5, color: 'var(--text-muted)', marginBottom: 16 }}>
        Retiring freezes the car: no new charges or expenses can be added after the sale date.
        The final cost of ownership is computed from the sale.
      </p>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Sale date</label>
          <input type="date" className="form-input" value={f.sale_date} onChange={(e) => set('sale_date', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Sale price (€) <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
          <input type="text" inputMode="decimal" className="form-input" placeholder="0" value={f.sale_price} onChange={(e) => set('sale_price', e.target.value)} />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Final odometer (km)</label>
        <input type="number" className="form-input" min="0" value={f.sale_odometer} onChange={(e) => set('sale_odometer', e.target.value)} />
        <p className="form-hint">Leave the sale price empty if the car was scrapped or given away (counts as 0 €).</p>
      </div>
    </Modal>
  );
}
