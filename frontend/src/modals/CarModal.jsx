import { useEffect, useState } from 'react';
import Modal from '../components/Modal.jsx';
import { fmtEur, fmtMoney0, fmtDay, parseMoney } from '../format.js';
import { DEFAULT_DEPRECIATION_RATE, estimateValue } from '../costs.js';

export default function CarModal({ open, onClose, onSaved, car, api, toast }) {
  const [f, setF] = useState({ name: '', make: '', model: '', color: '#3b82f6', odometer: '', battery_capacity: '', purchase_price: '', purchase_date: '', purchase_odometer: '', depreciation_rate: '', estimated_value: '' });
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
        purchase_price: car?.purchase_price != null ? fmtEur(car.purchase_price) : '',
        purchase_date: car?.purchase_date || '',
        purchase_odometer: car?.purchase_odometer != null ? car.purchase_odometer.toString() : '',
        depreciation_rate: car?.depreciation_rate != null ? car.depreciation_rate.toString() : '',
        estimated_value: car?.estimated_value != null ? fmtEur(car.estimated_value) : '',
      });
      setErr('');
    }
  }, [open, car]);

  // Live preview of the formula estimate for the values currently in the form
  const previewPrice = f.purchase_price.trim() ? parseMoney(f.purchase_price) : null;
  const preview = previewPrice != null && f.purchase_date
    ? estimateValue({ purchase_price: previewPrice, purchase_date: f.purchase_date, depreciation_rate: f.depreciation_rate.trim() !== '' ? Number(f.depreciation_rate) : null })
    : null;
  const formulaHint = preview ? ` Today ≈ ${fmtMoney0(preview.value)} €.` : '';

  const submit = async () => {
    if (!f.name.trim()) { setErr('Name is required.'); return; }
    if (!f.battery_capacity) { setErr('Battery capacity is required.'); return; }
    const purchasePrice = f.purchase_price.trim() ? parseMoney(f.purchase_price) : null;
    if (f.purchase_price.trim() && (purchasePrice == null || purchasePrice < 0)) { setErr('Purchase price is invalid.'); return; }
    const rate = f.depreciation_rate.trim() !== '' ? Number(f.depreciation_rate) : null;
    if (rate != null && !(Number.isInteger(rate) && rate >= 0 && rate <= 100)) { setErr('Depreciation must be a whole number between 0 and 100.'); return; }
    const estValue = f.estimated_value.trim() ? parseMoney(f.estimated_value) : null;
    if (f.estimated_value.trim() && (estValue == null || estValue < 0)) { setErr('Estimated value is invalid.'); return; }
    setSaving(true); setErr('');
    try {
      const payload = {
        name: f.name,
        make: f.make || undefined,
        model: f.model || undefined,
        color: f.color,
        odometer: parseInt(f.odometer) || 0,
        battery_capacity: parseInt(f.battery_capacity),
        purchase_price: purchasePrice,
        purchase_date: f.purchase_date || null,
        purchase_odometer: f.purchase_odometer !== '' ? parseInt(f.purchase_odometer) : null,
        depreciation_rate: rate,
        estimated_value: estValue,
      };
      // Retirement is edited elsewhere; the backend replaces fields, so pass existing values through
      if (car) {
        payload.sale_price = car.sale_price ?? null;
        payload.sale_date = car.sale_date ?? null;
        payload.sale_odometer = car.sale_odometer ?? null;
      }
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
      {err && <div style={{ background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', borderRadius: 8, padding: '9px 13px', fontSize: 13, color: 'var(--red)', marginBottom: 14 }}>{err}</div>}
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
      <div className="form-section">Purchase</div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Purchase price (€) <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
          <input type="text" inputMode="decimal" className="form-input" placeholder="e.g. 42900" value={f.purchase_price} onChange={(e) => set('purchase_price', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Purchase date <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
          <input type="date" className="form-input" value={f.purchase_date} onChange={(e) => set('purchase_date', e.target.value)} />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Odometer at purchase (km) <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
        <input type="number" className="form-input" placeholder="0" min="0" value={f.purchase_odometer} onChange={(e) => set('purchase_odometer', e.target.value)} />
        <p className="form-hint">For used cars.</p>
      </div>
      {!car?.retired && (
        <div className="form-row">
          <div className="form-group">
            <label className="form-label">Depreciation (% / year) <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
            <input type="number" className="form-input" placeholder={String(DEFAULT_DEPRECIATION_RATE)} min="0" max="100" value={f.depreciation_rate} onChange={(e) => set('depreciation_rate', e.target.value)} />
            <p className="form-hint">Default {DEFAULT_DEPRECIATION_RATE} %.{formulaHint}</p>
          </div>
          <div className="form-group">
            <label className="form-label">Estimated value (€) <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
            <input type="text" inputMode="decimal" className="form-input" placeholder="from formula" value={f.estimated_value} onChange={(e) => set('estimated_value', e.target.value)} />
            <p className="form-hint">Overrides the formula, e.g. from a real offer.</p>
          </div>
        </div>
      )}
      {car?.retired && (
        <div className="form-group">
          <label className="form-label">Sold</label>
          <div style={{ fontSize: 13.5 }}>
            {fmtDay(car.sale_date)} · {fmtEur(car.sale_price ?? 0)} € · {(car.sale_odometer ?? car.odometer ?? 0).toLocaleString('de-DE')} km
          </div>
          <p className="form-hint">Use Reactivate in the car menu to undo.</p>
        </div>
      )}
    </Modal>
  );
}
