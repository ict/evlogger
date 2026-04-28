import { useCallback, useEffect, useRef, useState } from 'react';
import { makeApi } from './api.js';
import { makeMockApi } from './mockApi.js';
import LoginScreen from './auth/LoginScreen.jsx';
import DashboardView from './views/DashboardView.jsx';
import ChargesView from './views/ChargesView.jsx';
import CposView from './views/CposView.jsx';
import YearlyTrendsView from './views/YearlyTrendsView.jsx';
import AdminView from './views/AdminView.jsx';
import CarModal from './modals/CarModal.jsx';
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
  const [charges, setCharges] = useState([]);
  const [chargesLoading, setChargesLoading] = useState(false);
  const [carDropdown, setCarDropdown] = useState(false);
  const [userDropdown, setUserDropdown] = useState(false);
  const [showCarModal, setShowCarModal] = useState(false);
  const [editCar, setEditCar] = useState(null);
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
    setCars([]); setCharges([]); setCpos([]); setSelectedCarId('');
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
      setCars(data || []);
      if (data?.length && !selectedCarId) handleSetSelectedCarId(data[0].id);
    }).catch((e) => { if (e.status === 401) logout(); });
  }, [apiClient, selectedCarId]);

  const loadCpos = useCallback(() => {
    if (!apiClient) return;
    apiClient.getCpos().then((d) => setCpos(d || [])).catch(() => {});
  }, [apiClient]);

  const loadCharges = useCallback(() => {
    if (!apiClient) return;
    setChargesLoading(true);
    apiClient.getCharges({ limit: 500 })
      .then((d) => setCharges(d || []))
      .catch(() => {})
      .finally(() => setChargesLoading(false));
  }, [apiClient]);

  useEffect(() => {
    if (apiClient) { loadCars(); loadCpos(); loadCharges(); }
  }, [apiClient]);

  useEffect(() => {
    const h = () => { setCarDropdown(false); setUserDropdown(false); };
    document.addEventListener('click', h);
    return () => document.removeEventListener('click', h);
  }, []);

  const handleDemo = useCallback(() => {
    _mockApi.current = makeMockApi();
    const demoAuth = { demo: true, baseUrl: '', token: 'demo', user: { username: 'demo', full_name: 'Demo User', email: 'demo@chargelogger.app' } };
    setAuth(demoAuth);
  }, []);

  const selectedCar = cars.find((c) => c.id === selectedCarId);

  if (!auth) return <LoginScreen onLogin={setAuth} onDemo={handleDemo} />;

  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'charges', label: 'Charges' },
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
          ChargeLogger
        </div>

        <nav className="topbar-tabs">
          {tabs.map((t) => (
            <button key={t.id} className={`tab-btn${tab === t.id ? ' active' : ''}`} onClick={() => setTab(t.id)}>
              <span>{t.label}</span>
            </button>
          ))}
        </nav>

        <div className="topbar-spacer" />

        {cars.length > 0 && (
          <div className="dropdown-wrap" onClick={(e) => e.stopPropagation()}>
            <button className="car-switcher" onClick={() => setCarDropdown((d) => !d)}>
              <div className="car-dot" style={{ background: selectedCar?.color || '#94a3b8' }}></div>
              {selectedCar?.name || 'Select car'}
              <span className="car-chevron">▾</span>
            </button>
            {carDropdown && (
              <div className="dropdown-menu" style={{ minWidth: 220 }}>
                {cars.map((c) => (
                  <div key={c.id} className={`dropdown-item${c.id === selectedCarId ? ' active' : ''}`} onClick={() => { handleSetSelectedCarId(c.id); setCarDropdown(false); }}>
                    <div className="car-dot" style={{ background: c.color || '#94a3b8' }}></div>
                    <div>
                      <div style={{ fontWeight: 600 }}>{c.name}</div>
                      {c.make && <div style={{ fontSize: 11.5, color: 'var(--text-muted)', fontWeight: 400 }}>{c.make} {c.model}</div>}
                    </div>
                  </div>
                ))}
                <div className="dropdown-sep" />
                <div className="dropdown-item" onClick={() => { setEditCar(null); setShowCarModal(true); setCarDropdown(false); }}>
                  <span>+</span> Add car
                </div>
                {selectedCar && (
                  <div className="dropdown-item" onClick={() => { setEditCar(selectedCar); setShowCarModal(true); setCarDropdown(false); }}>
                    ✎ Edit {selectedCar.name}
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
              <div className="dropdown-item" onClick={() => { setUserDropdown(false); logout(); }}>Sign out</div>
            </div>
          )}
        </div>
      </header>

      <main className="main-content">
        {tab === 'dashboard' && <DashboardView api={apiClient} selectedCarId={selectedCarId} cars={cars} tf={dashTf} setTf={handleSetDashTf} fromDate={dashFrom} setFromDate={handleSetDashFrom} toDate={dashTo} setToDate={handleSetDashTo} />}
        {tab === 'charges' && <ChargesView api={apiClient} charges={charges} loading={chargesLoading} reload={loadCharges} cars={cars} cpos={cpos} selectedCarId={selectedCarId} toast={toast} />}
        {tab === 'trends' && <YearlyTrendsView charges={charges} loading={chargesLoading} selectedCarId={selectedCarId} />}
        {tab === 'cpos' && <CposView api={apiClient} toast={toast} />}
        {tab === 'admin' && auth?.user?.is_admin && <AdminView api={apiClient} toast={toast} />}
      </main>

      {cars.length === 0 && auth && (
        <div style={{ position: 'fixed', bottom: 20, left: '50%', transform: 'translateX(-50%)', background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, padding: '14px 20px', boxShadow: 'var(--shadow-md)', display: 'flex', alignItems: 'center', gap: 12, zIndex: 500 }}>
          <span style={{ fontSize: 13, color: 'var(--text-muted)' }}>No cars yet.</span>
          <button className="btn btn-primary btn-sm" onClick={() => { setEditCar(null); setShowCarModal(true); }}>Add your first car</button>
        </div>
      )}

      <CarModal open={showCarModal} onClose={() => setShowCarModal(false)} onSaved={() => { setShowCarModal(false); loadCars(); }} car={editCar} api={apiClient} toast={toast} />
      <ToastContainer toasts={toasts} />
    </div>
  );
}
