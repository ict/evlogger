import { useMemo, useState } from 'react';
import Spinner from '../components/Spinner.jsx';
import Badge from '../components/Badge.jsx';
import ConfirmDialog from '../components/ConfirmDialog.jsx';
import ChargeModal from '../modals/ChargeModal.jsx';
import { fmtKwh, fmtEur, fmtDate } from '../format.js';

const PAGE_SIZE = 20;

export default function ChargesView({ api, charges, loading, reload, cars, cpos, selectedCarId, toast }) {
  const [showModal, setShowModal] = useState(false);
  const [editCharge, setEditCharge] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');

  const distanceMap = useMemo(() => {
    const sorted = charges
      .filter((c) => c.car_id === selectedCarId && c.car_odometer)
      .sort((a, b) => new Date(a.date) - new Date(b.date));
    const map = {};
    for (let i = 1; i < sorted.length; i++) {
      const km = sorted[i].car_odometer - sorted[i - 1].car_odometer;
      if (km > 0) map[sorted[i].id] = km;
    }
    return map;
  }, [charges, selectedCarId]);

  const carCharges = useMemo(() => {
    let list = charges.filter((c) => c.car_id === selectedCarId).sort((a, b) => new Date(b.date) - new Date(a.date));
    if (search) {
      const q = search.toLowerCase();
      list = list.filter((c) => (c.cpo_name || '').toLowerCase().includes(q) || (c.note || '').toLowerCase().includes(q) || c.charge_type.toLowerCase().includes(q));
    }
    return list;
  }, [charges, selectedCarId, search]);

  const pages = Math.ceil(carCharges.length / PAGE_SIZE);
  const pageCharges = carCharges.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  const doDelete = async () => {
    try { await api.deleteCharge(deleteTarget); toast('Deleted.', 'success'); reload(); }
    catch (e) { toast(e.message, 'error'); }
    setDeleteTarget(null);
  };

  return (
    <div>
      <div className="section-header">
        <div className="section-title">Charges</div>
        <div style={{ display: 'flex', gap: 10 }}>
          <input className="input-sm" placeholder="Search CPO, note…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(0); }} style={{ width: 180 }} />
          <button className="btn btn-primary btn-sm" onClick={() => { setEditCharge(null); setShowModal(true); }}>+ Add charge</button>
        </div>
      </div>

      <div className="card">
        {loading ? <Spinner /> : (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>kWh</th>
                    <th>Type</th>
                    <th>CPO</th>
                    <th>€ total</th>
                    <th>€/kWh</th>
                    <th>Odometer</th>
                    <th>Distance</th>
                    <th>SoC</th>
                    <th>Note</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {pageCharges.length === 0 && (
                    <tr><td colSpan="11"><div className="empty-state"><div className="empty-state-icon">⚡</div><div className="empty-state-text">No charges yet. Add your first one!</div></div></td></tr>
                  )}
                  {pageCharges.map((c) => (
                    <tr key={c.id}>
                      <td style={{ whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums' }}>{fmtDate(c.date)}</td>
                      <td style={{ fontWeight: 600 }}>{fmtKwh(c.kwh_charged)}</td>
                      <td><Badge type={c.charge_type} /></td>
                      <td style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.cpo_name || '—'}</td>
                      <td className="muted">{c.price_total != null ? fmtEur(c.price_total) + ' €' : '—'}</td>
                      <td className="muted">{c.price_per_kwh ? fmtEur(c.price_per_kwh) : '—'}</td>
                      <td className="muted">{c.car_odometer ? c.car_odometer.toLocaleString('de-DE') + ' km' : '—'}</td>
                      <td className="muted" style={{ color: distanceMap[c.id] ? 'var(--text)' : undefined, fontWeight: distanceMap[c.id] ? 500 : undefined }}>{distanceMap[c.id] ? '+' + distanceMap[c.id].toLocaleString('de-DE') + ' km' : '—'}</td>
                      <td className="muted">{c.car_soc_after != null ? c.car_soc_after + '%' : '—'}</td>
                      <td className="muted" style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={c.note || ''}>{c.note || '—'}</td>
                      <td>
                        <div className="row-actions">
                          <button className="action-btn" title="Edit" onClick={() => { setEditCharge(c); setShowModal(true); }}>✎</button>
                          <button className="action-btn danger" title="Delete" onClick={() => setDeleteTarget(c.id)}>🗑</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {pages > 1 && (
              <div className="pagination">
                <button className="page-btn" onClick={() => setPage((p) => p - 1)} disabled={page === 0}>‹</button>
                {Array.from({ length: pages }, (_, i) => (
                  <button key={i} className={`page-btn${page === i ? ' active' : ''}`} onClick={() => setPage(i)}>{i + 1}</button>
                )).slice(Math.max(0, page - 2), page + 3)}
                <button className="page-btn" onClick={() => setPage((p) => p + 1)} disabled={page === pages - 1}>›</button>
                <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 6 }}>{carCharges.length} total</span>
              </div>
            )}
          </>
        )}
      </div>

      <ChargeModal
        open={showModal}
        onClose={() => setShowModal(false)}
        onSaved={() => { setShowModal(false); reload(); }}
        charge={editCharge}
        cars={cars}
        cpos={cpos}
        api={api}
        toast={toast}
        preselectedCarId={selectedCarId}
      />
      <ConfirmDialog open={!!deleteTarget} message="Delete this charge? This cannot be undone." onConfirm={doDelete} onCancel={() => setDeleteTarget(null)} />
    </div>
  );
}
