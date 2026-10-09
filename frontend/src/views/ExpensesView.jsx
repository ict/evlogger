import { useMemo, useState } from 'react';
import Spinner from '../components/Spinner.jsx';
import ConfirmDialog from '../components/ConfirmDialog.jsx';
import ExpenseModal from '../modals/ExpenseModal.jsx';
import { CategoryChip, CategoryIcon, EXPENSE_CATEGORIES, EXPENSE_CATEGORY_MAP } from '../components/icons.jsx';
import { fmtEur, fmtDate, fmtDay } from '../format.js';

const safeStorage = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
};

// Unknown categories fall back to "other"
const catKey = (e) => (EXPENSE_CATEGORY_MAP[e.category] ? e.category : 'other');

export default function ExpensesView({ api, expenses, loading, reload, cars, selectedCarId, toast }) {
  const [showModal, setShowModal] = useState(false);
  const [editExpense, setEditExpense] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [cat, setCat] = useState(() => {
    const v = safeStorage.get('cl_expCat');
    return v && EXPENSE_CATEGORY_MAP[v] ? v : 'all';
  });

  const car = cars.find((c) => c.id === selectedCarId);
  const retired = !!car?.retired;

  const changeCat = (v) => { setCat(v); safeStorage.set('cl_expCat', v); };

  const carExpenses = useMemo(
    () => expenses.filter((e) => e.car_id === selectedCarId).sort((a, b) => new Date(b.date) - new Date(a.date)),
    [expenses, selectedCarId],
  );

  const filtered = useMemo(
    () => (cat === 'all' ? carExpenses : carExpenses.filter((e) => catKey(e) === cat)),
    [carExpenses, cat],
  );

  const total = useMemo(() => filtered.reduce((s, e) => s + (e.amount || 0), 0), [filtered]);

  const breakdown = useMemo(() => {
    const sums = {};
    for (const e of carExpenses) sums[catKey(e)] = (sums[catKey(e)] || 0) + (e.amount || 0);
    return Object.entries(sums).filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1]);
  }, [carExpenses]);

  const years = useMemo(() => {
    const groups = [];
    for (const e of filtered) {
      const y = new Date(e.date).getFullYear();
      let g = groups[groups.length - 1];
      if (!g || g.year !== y) { g = { year: y, items: [], sum: 0 }; groups.push(g); }
      g.items.push(e);
      g.sum += e.amount || 0;
    }
    return groups;
  }, [filtered]);

  const doDelete = async () => {
    try { await api.deleteExpense(deleteTarget); toast('Deleted.', 'success'); reload(); }
    catch (e) { toast(e.message, 'error'); }
    setDeleteTarget(null);
  };

  const openAdd = () => { setEditExpense(null); setShowModal(true); };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div className="section-header">
        <div className="section-title">Expenses</div>
        <button
          className="btn btn-primary btn-sm"
          disabled={retired || !car}
          style={retired ? { opacity: 0.5, cursor: 'not-allowed' } : undefined}
          title={retired ? `Car retired on ${fmtDay(car.sale_date)}` : undefined}
          onClick={openAdd}
        >+ Add expense</button>
      </div>

      {loading ? <div className="card"><Spinner /></div> : carExpenses.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">🧾</div>
            <div className="empty-state-text">No expenses yet. Add your first one!</div>
            {!retired && car && <button className="btn btn-primary btn-sm" style={{ marginTop: 16 }} onClick={openAdd}>+ Add expense</button>}
          </div>
        </div>
      ) : (
        <>
          <div className="exp-chips">
            <button className={`chip${cat === 'all' ? ' active' : ''}`} onClick={() => changeCat('all')}>All</button>
            {EXPENSE_CATEGORIES.map((c) => (
              <button
                key={c.key}
                className={`chip${cat === c.key ? ' active' : ''}`}
                style={cat === c.key ? { background: c.color, borderColor: c.color } : undefined}
                onClick={() => changeCat(c.key)}
              >
                <c.Icon size={14} />{c.label}
              </button>
            ))}
          </div>

          <div className="card exp-summary">
            <div className="exp-summary-total">
              <div className="stat-label">{cat === 'all' ? 'Total' : EXPENSE_CATEGORY_MAP[cat].label}</div>
              <div className="exp-total">{fmtEur(total)} €</div>
            </div>
            {cat === 'all' && breakdown.length > 1 && (
              <div className="exp-breakdown">
                {breakdown.map(([k, v]) => (
                  <span key={k} title={EXPENSE_CATEGORY_MAP[k].label}>
                    <CategoryIcon category={k} size={14} style={{ color: EXPENSE_CATEGORY_MAP[k].color }} />
                    {fmtEur(v)} €
                  </span>
                ))}
              </div>
            )}
          </div>

          <div className="card" style={{ overflow: 'hidden' }}>
            {years.length === 0 && (
              <div className="empty-state"><div className="empty-state-text">No expenses in this category.</div></div>
            )}
            {years.map((g) => (
              <div key={g.year}>
                <div className="exp-year"><span>{g.year}</span><span className="exp-year-sum">{fmtEur(g.sum)} €</span></div>
                {g.items.map((e) => {
                  const c = EXPENSE_CATEGORY_MAP[catKey(e)];
                  return (
                    <div key={e.id} className="exp-row">
                      <CategoryChip category={catKey(e)} />
                      <div className="exp-date">{fmtDate(e.date)}</div>
                      <div className="exp-main">
                        <div className="exp-cat">{c.label}</div>
                        {e.note && <div className="exp-note" title={e.note}>{e.note}</div>}
                      </div>
                      <div className="exp-amount">{fmtEur(e.amount)} €</div>
                      <div className="row-actions">
                        <button className="action-btn" title="Edit" onClick={() => { setEditExpense(e); setShowModal(true); }}>✎</button>
                        <button className="action-btn danger" title="Delete" onClick={() => setDeleteTarget(e.id)}>🗑</button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </>
      )}

      <ExpenseModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onSaved={() => { setShowModal(false); reload(); }}
        expense={editExpense}
        car={car}
        api={api}
        toast={toast}
      />
      <ConfirmDialog open={!!deleteTarget} message="Delete this expense? This cannot be undone." onConfirm={doDelete} onCancel={() => setDeleteTarget(null)} />
    </div>
  );
}
