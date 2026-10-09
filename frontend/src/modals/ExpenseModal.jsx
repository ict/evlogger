import { useEffect, useState } from 'react';
import Modal from '../components/Modal.jsx';
import { EXPENSE_CATEGORIES, EXPENSE_CATEGORY_MAP } from '../components/icons.jsx';
import { fmtEur, fmtDay, parseMoney } from '../format.js';

const pad = (n) => String(n).padStart(2, '0');
const ymd = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

export default function ExpenseModal({ open, onClose, onSaved, expense, car, api, toast }) {
  const [f, setF] = useState({ date: ymd(new Date()), kind: 'expense', category: '', amount: '', note: '' });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState('');
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));

  useEffect(() => {
    if (open) {
      if (expense) {
        setF({
          date: ymd(new Date(expense.date)),
          kind: expense.kind === 'income' ? 'income' : 'expense',
          category: EXPENSE_CATEGORY_MAP[expense.category] ? expense.category : 'other',
          amount: fmtEur(expense.amount),
          note: expense.note || '',
        });
      } else {
        setF({ date: ymd(new Date()), kind: 'expense', category: '', amount: '', note: '' });
      }
      setErr('');
    }
  }, [open, expense]);

  const income = f.kind === 'income';

  const submit = async () => {
    if (!f.date) { setErr('Date is required.'); return; }
    if (!f.category) { setErr('Please select a category.'); return; }
    const amount = parseMoney(f.amount);
    if (amount == null || amount <= 0) { setErr('Amount must be greater than 0.'); return; }
    const carId = expense?.car_id || car?.id;
    if (!carId) { setErr('No car selected.'); return; }
    if (car?.sale_date && f.date > car.sale_date) { setErr(`Car was retired on ${fmtDay(car.sale_date)}.`); return; }
    setSaving(true); setErr('');
    try {
      const payload = {
        // noon local time keeps the calendar day stable across timezones
        date: new Date(f.date + 'T12:00:00').toISOString(),
        car_id: carId,
        category: f.category,
        kind: f.kind,
        amount,
        note: f.note.trim() || undefined,
      };
      if (expense) await api.updateExpense(expense.id, payload);
      else await api.createExpense(payload);
      toast(income ? 'Income saved!' : 'Expense saved!', 'success');
      onSaved();
    } catch (e) { setErr(e.message); }
    setSaving(false);
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`${expense ? 'Edit' : 'New'} ${income ? 'Income' : 'Expense'}`}
      footer={(
        <>
          <button className="btn btn-ghost" onClick={onClose}>Cancel</button>
          <button className="btn btn-primary" onClick={submit} disabled={saving}>{saving ? 'Saving…' : income ? 'Save income' : 'Save expense'}</button>
        </>
      )}
    >
      {err && <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '9px 13px', fontSize: 13, color: 'var(--red)', marginBottom: 14 }}>{err}</div>}
      <div className="form-group">
        <div className="toggle-group">
          <button type="button" className={`toggle-btn${!income ? ' active' : ''}`} onClick={() => set('kind', 'expense')}>Expense</button>
          <button
            type="button"
            className={`toggle-btn${income ? ' active' : ''}`}
            style={income ? { background: 'var(--green)' } : undefined}
            onClick={() => set('kind', 'income')}
          >Income</button>
        </div>
        {income && <p className="form-hint">Money back, e.g. sold tires or a refund. Lowers the car's cost of ownership.</p>}
      </div>
      <div className="form-group">
        <label className="form-label">Category</label>
        <div className="cat-grid">
          {EXPENSE_CATEGORIES.map((c) => {
            const active = f.category === c.key;
            return (
              <button
                key={c.key}
                type="button"
                className="cat-btn"
                style={active ? { borderColor: c.color, background: c.color + '1f', color: c.color } : undefined}
                onClick={() => set('category', c.key)}
              >
                <c.Icon size={22} />
                {c.label}
              </button>
            );
          })}
        </div>
      </div>
      <div className="form-row">
        <div className="form-group">
          <label className="form-label">Date</label>
          <input type="date" className="form-input" value={f.date} onChange={(e) => set('date', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Amount (€)</label>
          <input type="text" inputMode="decimal" className="form-input" placeholder="e.g. 123.45" value={f.amount} onChange={(e) => set('amount', e.target.value)} />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Note <span style={{ fontWeight: 400, color: 'var(--text-light)' }}>optional</span></label>
        <textarea className="form-input" placeholder="Any notes…" rows="2" style={{ resize: 'vertical' }} value={f.note} onChange={(e) => set('note', e.target.value)} />
      </div>
      {(expense?.car_name || car?.name) && <p className="form-hint">Car: {expense?.car_name || car?.name}</p>}
    </Modal>
  );
}
