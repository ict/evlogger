import { useCallback, useEffect, useRef, useState } from 'react';
import { makeApi } from './api.js';
import { makeMockApi } from './mockApi.js';
import LoginScreen from './auth/LoginScreen.jsx';
import DashboardView from './views/DashboardView.jsx';
import ChargesView from './views/ChargesView.jsx';
import ExpensesView from './views/ExpensesView.jsx';
import CposView from './views/CposView.jsx';
import YearlyTrendsView from './views/YearlyTrendsView.jsx';
import AdminView from './views/AdminView.jsx';
import CarModal from './modals/CarModal.jsx';
import RetireCarModal from './modals/RetireCarModal.jsx';
import ConfirmDialog from './components/ConfirmDialog.jsx';
import Badge from './components/Badge.jsx';
import ApiTokensModal from './modals/ApiTokensModal.jsx';
import ToastContainer from './components/ToastContainer.jsx';

const API_BASE = '/api';

const safeStorage = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  remove(k) { try { localStorage.removeItem(k); } catch {} },
};

export default function App() {
  const [auth, setAuth] = useState(() => {
    try { return JSON.parse(safeStorage.get('cl_auth') || 'null'); } catch { return null; }
  });
  const [dashTf, setDashTf] = useState(() => safeStorage.get('cl_dashTf') || '3M');
  const [dashFrom, setDashFrom] = useState(() => safeStorage.get('cl_dashFrom') || '');
  const [dashTo, setDashTo] = useState(() => safeStorage.get('cl_dashTo') || '');
  const [tab, setTab] = useState('dashboard');
  const [cars, setCars] = useState([]);
  const [selectedCarId, setSelectedCarId] = useState(() => safeStorage.get('cl_carId') || '');
  const [cpos, setCpos] = useState([]);
  const [cposLoading, setCposLoading] = useState(false);
  const [charges, setCharges] = useState([]);
  const [chargesLoading, setChargesLoading] = useState(false);
  const [expenses, setExpenses] = useState([]);
  const [expensesLoading, setExpensesLoading] = useState(false);
  const [carDropdown, setCarDropdown] = useState(false);
  const [userDropdown, setUserDropdown] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [showCarModal, setShowCarModal] = useState(false);
  const [editCar, setEditCar] = useState(null);
  const [retireCar, setRetireCar] = useState(null);
  const [reactivateCar, setReactivateCar] = useState(null);
  const [showTokensModal, setShowTokensModal] = useState(false);
  const [toasts, setToasts] = useState([]);

  const _mockApi = useRef(null);
  const [apiClient, setApiClient] = useState(null);

  useEffect(() => {
    if (!auth) { setApiClient(null); return; }
    if (auth.demo) {
      if (!_mockApi.current) _mockApi.current = makeMockApi();
      setApiClient(_mockApi.current);
    } else {
      setApiClient(makeApi(auth.baseUrl || API_BASE, auth.token));
    }
  }, [auth]);

  const toast = useCallback((msg, type = 'success') => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, msg, type }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3000);
  }, []);

  const logout = () => {
    safeStorage.remove('cl_auth');
    setAuth(null);
    _mockApi.current = null;
    setCars([]); setCharges([]); setCpos([]); setExpenses([]); setSelectedCarId('');
  };

  const handleSetSelectedCarId = useCallback((id) => {
    setSelectedCarId(id);
    safeStorage.set('cl_carId', id);
  }, []);

  const handleSetDashTf = useCallback((v) => { setDashTf(v); safeStorage.set('cl_dashTf', v); }, []);
  const handleSetDashFrom = useCallback((v) => { setDashFrom(v); safeStorage.set('cl_dashFrom', v); }, []);
  const handleSetDashTo = useCallback((v) => { setDashTo(v); safeStorage.set('cl_dashTo', v); }, []);

  const loadCars = useCallback(() => {
    if (!apiClient) return;
    apiClient.getCars().then((data) => {
      const list = data || [];
      setCars(list);
      // keep the selection if the car still exists; otherwise first active car, else first car
      if (!list.some((c) => c.id === selectedCarId)) {
        const next = list.find((c) => !c.retired) || list[0];
        if (next) handleSetSelectedCarId(next.id);
        else if (selectedCarId) handleSetSelectedCarId('');
      }
    }).catch((e) => { if (e.status === 401) logout(); });
  }, [apiClient, selectedCarId]);

  const loadCpos = useCallback(() => {
    if (!apiClient) return;
    setCposLoading(true);
    apiClient.getCpos()
      .then((d) => setCpos(d || []))
      .catch(() => {})
      .finally(() => setCposLoading(false));
  }, [apiClient]);

  const loadCharges = useCallback(() => {
    if (!apiClient) return;
    setChargesLoading(true);
    apiClient.getCharges({ limit: 500 })
      .then((d) => setCharges(d || []))
      .catch(() => {})
      .finally(() => setChargesLoading(false));
  }, [apiClient]);

  const loadExpenses = useCallback(() => {
    if (!apiClient) return;
    setExpensesLoading(true);
    apiClient.getExpenses({ limit: 500 })
      .then((d) => setExpenses(d || []))
      .catch(() => {})
      .finally(() => setExpensesLoading(false));
  }, [apiClient]);

  useEffect(() => {
    if (apiClient) { loadCars(); loadCpos(); loadCharges(); loadExpenses(); }
  }, [apiClient]);

  useEffect(() => {
    const h = () => { setCarDropdown(false); setUserDropdown(false); setMobileMenu(false); };
    document.addEventListener('click', h);
    return () => document.removeEventListener('click', h);
  }, []);

  const handleDemo = useCallback(() => {
    _mockApi.current = makeMockApi();
    const demoAuth = { demo: true, baseUrl: '', token: 'demo', user: { username: 'demo', full_name: 'Demo User', email: 'demo@evlogger.app' } };
    setAuth(demoAuth);
  }, []);

  const reactivate = async () => {
    const car = reactivateCar;
    setReactivateCar(null);
    if (!car) return;
    try {
      await apiClient.updateCar(car.id, {
        name: car.name,
        make: car.make || undefined,
        model: car.model || undefined,
        color: car.color,
        odometer: car.odometer,
        battery_capacity: car.battery_capacity,
        purchase_price: car.purchase_price ?? null,
        purchase_date: car.purchase_date ?? null,
        purchase_odometer: car.purchase_odometer ?? null,
        sale_price: null,
        sale_date: null,
        sale_odometer: null,
      });
      toast(`${car.name} reactivated`, 'success');
      loadCars();
    } catch (e) { toast(e.message, 'error'); }
  };

  const selectedCar = cars.find((c) => c.id === selectedCarId);
  const activeCars = cars.filter((c) => !c.retired);
  const retiredCars = cars.filter((c) => c.retired);

  if (!auth) return <LoginScreen onLogin={setAuth} onDemo={handleDemo} />;

  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'charges', label: 'Charges' },
    { id: 'expenses', label: 'Expenses' },
    { id: 'trends', label: 'Yearly Trends' },
    { id: 'cpos', label: 'CPOs' },
    ...(auth?.user?.is_admin ? [{ id: 'admin', label: 'Admin' }] : []),
  ];

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-logo">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          EVLogger
        </div>

        <nav className="topbar-tabs">
          {tabs.map((t) => (
            <button key={t.id} className={`tab-btn${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
              {t.label}
            </button>
          ))}
        </nav>

        <div className="topbar-spacer" />

        <button className="hamburger-btn" onClick={(e) => { e.stopPropagation(); setMobileMenu((d) => !d); }} aria-label="Menu">
          {mobileMenu
            ? <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            : <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><line x1="3" y1="7" x2="21" y2="7"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="17" x2="21" y2="17"/></svg>
          }
        </button>

        {cars.length > 0 && (
          <div className="dropdown-wrap" onClick={(e) => e.stopPropagation()}>
            <button className="car-switcher" onClick={() => setCarDropdown((d) => !d)}>
              <div className="car-dot" style={{ background: selectedCar?.color || '#94a3b8' }}></div>
              {selectedCar?.name || 'Select car'}
              {selectedCar?.retired && <Badge type="Retired" />}
              <span className="car-chevron">▾</span>
            </button>
            {carDropdown && (
              <div className="dropdown-menu" style={{ minWidth: 220 }}>
                {[...activeCars, ...(retiredCars.length ? [null] : []), ...retiredCars].map((c) => (c === null ? <div key="retired-sep" className="dropdown-sep" /> : (
                  <div key={c.id} className={`dropdown-item${c.id === selectedCarId ? ' active' : ''}${c.retired ? ' car-retired' : ''}`} onClick={() => { handleSetSelectedCarId(c.id); setCarDropdown(false); }}>
                    <div className="car-dot" style={{ background: c.color || '#94a3b8' }}></div>
                    <div>
                      <div style={{ fontWeight: 600 }}>{c.name}</div>
                      {c.make && <div style={{ fontSize: 11.5, color: 'var(--text-muted)', fontWeight: 400 }}>{c.make} {c.model}</div>}
                    </div>
                    {c.retired && <span style={{ marginLeft: 'auto' }}><Badge type="Retired" /></span>}
                  </div>
                )))}
                <div className="dropdown-sep" />
                <div className="dropdown-item" onClick={() => { setEditCar(null); setShowCarModal(true); setCarDropdown(false); }}>
                  <span>+</span> Add car
                </div>
                {selectedCar && (
                  <div className="dropdown-item" onClick={() => { setEditCar(selectedCar); setShowCarModal(true); setCarDropdown(false); }}>
                    ✎ Edit {selectedCar.name}
                  </div>
                )}
                {selectedCar && (
                  <div className="dropdown-item" onClick={() => { setCarDropdown(false); if (selectedCar.retired) setReactivateCar(selectedCar); else setRetireCar(selectedCar); }}>
                    {selectedCar.retired ? `↺ Reactivate ${selectedCar.name}` : `⏻ Retire ${selectedCar.name}…`}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        <div className="dropdown-wrap" onClick={(e) => e.stopPropagation()}>
          <div className="user-btn" onClick={() => setUserDropdown((d) => !d)}>
            {(auth.user?.username || 'U')[0].toUpperCase()}
          </div>
          {userDropdown && (
            <div className="dropdown-menu" style={{ right: 0 }}>
              <div style={{ padding: '8px 12px 6px', borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{auth.user?.full_name || auth.user?.username}</div>
                {auth.user?.email && <div style={{ fontSize: 11.5, color: 'var(--text-muted)' }}>{auth.user.email}</div>}
              </div>
              <div className="dropdown-item" onClick={() => { setUserDropdown(false); setShowTokensModal(true); }}>API tokens</div>
              <div className="dropdown-item" onClick={() => { setUserDropdown(false); logout(); }}>Sign out</div>
            </div>
          )}
        </div>
      </header>

      {mobileMenu && (
        <div className="mobile-menu" onClick={(e) => e.stopPropagation()}>
          <nav className="mobile-menu-nav">
            {tabs.map((t) => (
              <button key={t.id} className={`mobile-menu-tab${tab === t.id ? ' active' : ''}`} onClick={() => { setTab(t.id); setMobileMenu(false); }}>
                {t.label}
              </button>
            ))}
          </nav>
          {cars.length > 0 && (
            <>
              <div className="mobile-menu-sep" />
              <div className="mobile-menu-section-label">Car</div>
              {[...activeCars, ...(retiredCars.length ? [null] : []), ...retiredCars].map((c) => (c === null ? <div key="retired-sep" className="mobile-menu-sep" /> : (
                <button key={c.id} className={`mobile-menu-tab${c.id === selectedCarId ? ' active' : ''}${c.retired ? ' car-retired' : ''}`} onClick={() => { handleSetSelectedCarId(c.id); setMobileMenu(false); }}>
                  <div className="car-dot" style={{ background: c.color || '#94a3b8' }} />
                  {c.name}
                  {c.retired && <Badge type="Retired" />}
                </button>
              )))}
              <div className="mobile-menu-sep" />
              <button className="mobile-menu-tab" onClick={() => { setEditCar(null); setShowCarModal(true); setMobileMenu(false); }}>+ Add car</button>
              {selectedCar && (
                <button className="mobile-menu-tab" onClick={() => { setEditCar(selectedCar); setShowCarModal(true); setMobileMenu(false); }}>✎ Edit {selectedCar.name}</button>
              )}
              {selectedCar && (
                <button className="mobile-menu-tab" onClick={() => { setMobileMenu(false); if (selectedCar.retired) setReactivateCar(selectedCar); else setRetireCar(selectedCar); }}>
                  {selectedCar.retired ? `↺ Reactivate ${selectedCar.name}` : `⏻ Retire ${selectedCar.name}…`}
                </button>
              )}
            </>
          )}
          <div className="mobile-menu-sep" />
          <button className="mobile-menu-tab" onClick={() => { setMobileMenu(false); logout(); }}>Sign out</button>
        </div>
      )}

      <main className="main-content">
        {tab === 'dashboard' && <DashboardView api={apiClient} selectedCarId={selectedCarId} cars={cars} charges={charges} chargesLoading={chargesLoading} expenses={expenses} expensesLoading={expensesLoading} tf={dashTf} setTf={handleSetDashTf} fromDate={dashFrom} setFromDate={handleSetDashFrom} toDate={dashTo} setToDate={handleSetDashTo} />}
        {tab === 'charges' && <ChargesView api={apiClient} charges={charges} loading={chargesLoading} reload={loadCharges} cars={cars} cpos={cpos} selectedCarId={selectedCarId} toast={toast} />}
        {tab === 'expenses' && <ExpensesView api={apiClient} expenses={expenses} loading={expensesLoading} reload={loadExpenses} cars={cars} selectedCarId={selectedCarId} toast={toast} />}
        {tab === 'trends' && <YearlyTrendsView expenses={expenses} expensesLoading={expensesLoading} charges={charges} loading={chargesLoading} selectedCarId={selectedCarId} cars={cars} />}
        {tab === 'cpos' && <CposView api={apiClient} cpos={cpos} loading={cposLoading} reload={loadCpos} toast={toast} />}
        {tab === 'admin' && auth?.user?.is_admin && <AdminView api={apiClient} toast={toast} />}
      </main>

      {cars.length === 0 && auth && (
        <div style={{ position: 'fixed', bottom: 20, left: '50%', transform: 'translateX(-50%)', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: '14px 20px', boxShadow: 'var(--shadow-md)', display: 'flex', alignItems: 'center', gap: 12, zIndex: 500 }}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>No cars yet.</span>
          <button className="btn btn-primary btn-sm" onClick={() => { setEditCar(null); setShowCarModal(true); }}>Add your first car</button>
        </div>
      )}

      <CarModal open={showCarModal} onClose={() => setShowCarModal(false)} onSaved={() => { setShowCarModal(false); loadCars(); }} car={editCar} api={apiClient} toast={toast} />
      <RetireCarModal open={!!retireCar} onClose={() => setRetireCar(null)} onSaved={() => { setRetireCar(null); loadCars(); }} car={retireCar} api={apiClient} toast={toast} />
      <ConfirmDialog open={!!reactivateCar} title="Reactivate car" confirmLabel="Reactivate" danger={false} message={`Reactivate ${reactivateCar?.name}? The sale data will be removed.`} onConfirm={reactivate} onCancel={() => setReactivateCar(null)} />
      <ApiTokensModal open={showTokensModal} onClose={() => setShowTokensModal(false)} api={apiClient} toast={toast} />
      <ToastContainer toasts={toasts} />
    </div>
  );
}
