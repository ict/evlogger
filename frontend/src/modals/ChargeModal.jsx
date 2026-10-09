import { useEffect, useState } from 'react';
import Modal from '../components/Modal.jsx';
import { fmtEur, fmtDateTimeInput, fmtDay } from '../format.js';

export default function ChargeModal({ open, onClose, onSaved, charge, cars, cpos, charges, api, toast, preselectedCarId }) {
  const sortedCpos = (() => {
    const counts = {};
    for (const c of charges || []) counts[c.cpo_id] = (counts[c.cpo_id] || 0) + 1;
    const top3 = [...cpos]
      .filter((c) => counts[c.id])
      .sort((a, b) => counts[b.id] - counts[a.id] || a.name.localeCompare(b.name))
      .slice(0, 3);
    const top3Ids = new Set(top3.map((c) => c.id));
    const rest = cpos.filter((c) => !top3Ids.has(c.id)).sort((a, b) => a.name.localeCompare(b.name));
    return { top3, rest };
  })();

  const blank = () => ({
    date: new Date().toISOString().slice(0, 16),
    car_id: preselectedCarId || (cars[0]?.id || ''),
    kwh: '',
    cpo_id: sortedCpos.top3[0]?.id || sortedCpos.rest[0]?.id || '',
    charge_type: 'AC',
    odometer: '',
    soc_after: '',
    price_mode: 'auto',
    price_total: '',
    price_per_kwh_val: '',
    note: '',
  });
  const [f, setF] = useState(blank);
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');

  useEffect(() => {
    if (open) {
      if (charge) {
        const priceMode = charge.price_total != null ? 'total' : 'auto';
        setF({
          date: fmtDateTimeInput(charge.date),
          car_id: charge.car_id,
          kwh: (charge.kwh_charged / 100).toString(),
          cpo_id: charge.cpo_id,
          charge_type: charge.charge_type,
          odometer: charge.car_odometer?.toString() || '',
          soc_after: charge.car_soc_after?.toString() || '',
          price_mode: priceMode,
          price_total: charge.price_total != null ? fmtEur(charge.price_total) : '',
          price_per_kwh_val: charge.price_per_kwh ? fmtEur(charge.price_per_kwh) : '',
          note: charge.note || '',
        });
      } else {
        setF(blank());
      }
      setErr('');
    }
  }, [open, charge]);

  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  const submit = async () => {
    if (!f.kwh || isNaN(parseFloat(f.kwh))) { setErr('kWh is required.'); return; }
    const chosenCar = cars.find((c) => c.id === f.car_id);
    if (chosenCar?.sale_date && f.date.slice(0, 10) > chosenCar.sale_date) { setErr(`Car was retired on ${fmtDay(chosenCar.sale_date)}.`); return; }
    setSaving(true); setErr('');
    try {
      const kwh_charged = Math.round(parseFloat(f.kwh) * 100);
      let price_total = null;
      if (f.price_mode === 'total' && f.price_total) price_total = Math.round(parseFloat(f.price_total) * 100);
      if (f.price_mode === 'per_kwh' && f.price_per_kwh_val) price_total = Math.round(parseFloat(f.price_per_kwh_val) * kwh_charged);

      const payload = {
        date: new Date(f.date).toISOString(),
        car_id: f.car_id,
        kwh_charged,
        cpo_id: f.cpo_id,
        charge_type: f.charge_type,
        car_odometer: f.odometer ? parseInt(f.odometer) : undefined,
        car_soc_after: f.soc_after ? parseInt(f.soc_after) : undefined,
        price_total,
        note: f.note || undefined,
      };
      if (charge) await api.updateCharge(charge.id, payload);
      else await api.createCharge(payload);
      toast('Charge saved!', 'success');
      onSaved();
    } catch (e) { setErr(e.message); }
    setSaving(false);
  };

  const selectedCpo = cpos.find((c) => c.id === f.cpo_id);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={charge ? 'Edit Charge' : 'New Charge'}
      footer={(
        <>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>{saving ? 'Saving…' : 'Save charge'}</button>
        </>
      )}
    >
      {err && <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '9px 13px', fontSize: 13, color: 'var(--red)', marginBottom: 14 }}>{err}</div>}
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Date & Time</label>
          <input type="datetime-local" className="form-input" value={f.date} onChange={(e) => set('date', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Car</label>
          <select className="form-input form-select" value={f.car_id} onChange={(e) => set('car_id', e.target.value)}>
            {cars.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">kWh charged</label>
          <input type="number" className="form-input" placeholder="e.g. 45.5" step="0.1" min="0" value={f.kwh} onChange={(e) => set('kwh', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Charge type</label>
          <div className="toggle-group">
            {['AC', 'DC'].map((t) => (
              <button key={t} className={`toggle-btn${f.charge_type === t ? ' active' : ''}`} onClick={() => set('charge_type', t)}>{t}</button>
            ))}
          </div>
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">CPO (Charge Point Operator)</label>
        <select className="form-input form-select" value={f.cpo_id} onChange={(e) => set('cpo_id', e.target.value)}>
          {sortedCpos.top3.map((c) => <option key={c.id} value={c.id}>{c.name} — {fmtEur(c.default_price)} €/kWh</option>)}
          {sortedCpos.top3.length > 0 && sortedCpos.rest.length > 0 && <option disabled>──────────</option>}
          {sortedCpos.rest.map((c) => <option key={c.id} value={c.id}>{c.name} — {fmtEur(c.default_price)} €/kWh</option>)}
        </select>
      </div>
      <div className="form-group">
        <label className="form-label">Price</label>
        <div className="price-mode-btns" style={{ marginBottom: 10 }}>
          {[['auto', 'Auto (CPO default)'], ['total', 'Total cost'], ['per_kwh', 'Price per kWh']].map(([k, l]) => (
            <button key={k} className={`price-mode-btn${f.price_mode === k ? ' active' : ''}`} onClick={() => set('price_mode', k)}>{l}</button>
          ))}
        </div>
        {f.price_mode === 'auto' && selectedCpo && <p className="form-hint">Will use last price from {selectedCpo.name} ({fmtEur(selectedCpo.default_price)} €/kWh default)</p>}
        {f.price_mode === 'total' && <input type="number" className="form-input" placeholder="Total cost in €" step="0.01" min="0" value={f.price_total} onChange={(e) => set('price_total', e.target.value)} />}
        {f.price_mode === 'per_kwh' && <input type="number" className="form-input" placeholder="Price per kWh in €" step="0.001" min="0" value={f.price_per_kwh_val} onChange={(e) => set('price_per_kwh_val', e.target.value)} />}
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Odometer (km) <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
          <input type="number" className="form-input" placeholder="e.g. 24500" step="1" min="0" value={f.odometer} onChange={(e) => set('odometer', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">SoC after (%) <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
          <input type="number" className="form-input" placeholder="0–100" min="0" max="100" value={f.soc_after} onChange={(e) => set('soc_after', e.target.value)} />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Note <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
        <textarea className="form-input" placeholder="Any notes…" rows="2" style={{ resize: 'vertical' }} value={f.note} onChange={(e) => set('note', e.target.value)} />
      </div>
    </Modal>
  );
}
