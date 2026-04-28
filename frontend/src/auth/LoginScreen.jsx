import { useState } from 'react';
import { makeApi } from '../api.js';

const API_BASE = '/api';

const safeStorage = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
};

const COLORS = ['#6366f1', '#22c55e', '#f97316', '#ec4899', '#14b8a6', '#f59e0b', '#3b82f6', '#8b5cf6'];

function Logo() {
  return (
    <div className="login-logo">
      <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
      </svg>
      <div className="login-logo-text">Charge<span>Logger</span></div>
    </div>
  );
}

function LoginForm({ onLogin, onDemo, onRegister }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const tmpApi = makeApi(API_BASE, null);
      const { access_token } = await tmpApi.login(username, password);
      const api = makeApi(API_BASE, access_token);
      const user = await api.getMe();
      const auth = { token: access_token, baseUrl: API_BASE, user };
      safeStorage.set('cl_auth', JSON.stringify(auth));
      onLogin(auth);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  return (
    <form className="login-card" onSubmit={submit}>
      <Logo />
      <div className="login-title">Welcome back</div>
      <div className="login-sub">Sign in to track your EV charging sessions</div>
      {error && <div className="login-error">{error}</div>}
      <div className="form-group">
        <label className="form-label">Username</label>
        <input className="form-input" type="text" placeholder="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
      </div>
      <div className="form-group">
        <label className="form-label">Password</label>
        <input className="form-input" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '11px 0', marginTop: 4 }} disabled={loading}>
        {loading ? 'Signing in…' : 'Sign in'}
      </button>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '20px 0 0' }}>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }}></div>
        <span style={{ fontSize: 12, color: 'var(--text-light)' }}>or</span>
        <div style={{ flex: 1, height: 1, background: 'var(--border)' }}></div>
      </div>
      <button type="button" className="btn btn-ghost" style={{ width: '100%', justifyContent: 'center', padding: '10px 0', marginTop: 12 }} onClick={onDemo}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>
        Try demo — no account needed
      </button>
      <div style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--text-muted)' }}>
        No account?{' '}
        <button type="button" onClick={onRegister} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: 13, fontWeight: 600, padding: 0 }}>
          Create one
        </button>
      </div>
    </form>
  );
}

function RegisterStep1({ onDone, onBack }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const submit = async (e) => {
    e.preventDefault();
    if (password !== confirm) { setError('Passwords do not match'); return; }
    setLoading(true); setError('');
    try {
      const unauthApi = makeApi(API_BASE, null);
      await unauthApi.register({ username, password, email: email || undefined, full_name: fullName || undefined });
      const { access_token } = await unauthApi.login(username, password);
      const authedApi = makeApi(API_BASE, access_token);
      const user = await authedApi.getMe();
      const auth = { token: access_token, baseUrl: API_BASE, user };
      safeStorage.set('cl_auth', JSON.stringify(auth));
      onDone(auth, authedApi);
    } catch (e) {
      const msg = e.message === 'Registration is disabled'
        ? 'Registration is currently disabled by the administrator.'
        : e.message;
      setError(msg);
    }
    setLoading(false);
  };

  return (
    <form className="login-card" onSubmit={submit}>
      <Logo />
      <div className="login-title">Create account</div>
      <div className="login-sub">Step 1 of 2 — your details</div>
      {error && <div className="login-error">{error}</div>}
      <div className="form-group">
        <label className="form-label">Username <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" type="text" placeholder="username" value={username} onChange={(e) => setUsername(e.target.value)} required />
      </div>
      <div className="form-group">
        <label className="form-label">Password <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" type="password" placeholder="••••••••" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </div>
      <div className="form-group">
        <label className="form-label">Confirm password <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" type="password" placeholder="••••••••" value={confirm} onChange={(e) => setConfirm(e.target.value)} required />
      </div>
      <div className="form-group">
        <label className="form-label">Full name <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
        <input className="form-input" type="text" placeholder="Jane Smith" value={fullName} onChange={(e) => setFullName(e.target.value)} />
      </div>
      <div className="form-group">
        <label className="form-label">Email <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>(optional)</span></label>
        <input className="form-input" type="email" placeholder="jane@example.com" value={email} onChange={(e) => setEmail(e.target.value)} />
      </div>
      <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '11px 0', marginTop: 4 }} disabled={loading}>
        {loading ? 'Creating account…' : 'Continue'}
      </button>
      <div style={{ textAlign: 'center', marginTop: 16, fontSize: 13, color: 'var(--text-muted)' }}>
        Already have an account?{' '}
        <button type="button" onClick={onBack} style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: 13, fontWeight: 600, padding: 0 }}>
          Sign in
        </button>
      </div>
    </form>
  );
}

function RegisterStep2({ auth, authedApi, onLogin }) {
  const [name, setName] = useState('');
  const [make, setMake] = useState('');
  const [model, setModel] = useState('');
  const [color, setColor] = useState(COLORS[0]);
  const [capacity, setCapacity] = useState('');
  const [odometer, setOdometer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const skip = () => onLogin(auth);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      await authedApi.createCar({
        name,
        make: make || undefined,
        model: model || undefined,
        color,
        battery_capacity: capacity ? Math.round(parseFloat(capacity) * 100) : 0,
        odometer: odometer ? parseInt(odometer, 10) : 0,
      });
      onLogin(auth);
    } catch (e) {
      setError(e.message);
      // Don't block login on car creation failure — user can add car from within the app
    }
    setLoading(false);
  };

  return (
    <form className="login-card" onSubmit={submit}>
      <Logo />
      <div className="login-title">Add your first car</div>
      <div className="login-sub">Step 2 of 2 — optional, you can do this later</div>
      {error && <div className="login-error">{error} <button type="button" onClick={skip} style={{ marginLeft: 8, background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: 12, fontWeight: 600, padding: 0 }}>Skip anyway</button></div>}
      <div className="form-group">
        <label className="form-label">Car name <span style={{ color: 'var(--red)' }}>*</span></label>
        <input className="form-input" type="text" placeholder="My Tesla" value={name} onChange={(e) => setName(e.target.value)} required />
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div className="form-group">
          <label className="form-label">Make</label>
          <input className="form-input" type="text" placeholder="Tesla" value={make} onChange={(e) => setMake(e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">Model</label>
          <input className="form-input" type="text" placeholder="Model 3" value={model} onChange={(e) => setModel(e.target.value)} />
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div className="form-group">
          <label className="form-label">Battery capacity (kWh) <span style={{ color: 'var(--red)' }}>*</span></label>
          <input className="form-input" type="number" min="1" step="0.1" placeholder="75" value={capacity} onChange={(e) => setCapacity(e.target.value)} required />
        </div>
        <div className="form-group">
          <label className="form-label">Odometer (km)</label>
          <input className="form-input" type="number" min="0" placeholder="0" value={odometer} onChange={(e) => setOdometer(e.target.value)} />
        </div>
      </div>
      <div className="form-group">
        <label className="form-label">Color</label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 4 }}>
          {COLORS.map((c) => (
            <div key={c} onClick={() => setColor(c)} style={{ width: 28, height: 28, borderRadius: '50%', background: c, cursor: 'pointer', border: color === c ? '3px solid var(--text)' : '3px solid transparent', boxSizing: 'border-box' }} />
          ))}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
        <button type="button" className="btn btn-ghost" style={{ flex: 1, justifyContent: 'center', padding: '10px 0' }} onClick={skip}>
          Skip for now
        </button>
        <button type="submit" className="btn btn-primary" style={{ flex: 2, justifyContent: 'center', padding: '11px 0' }} disabled={loading}>
          {loading ? 'Adding car…' : 'Add car & continue'}
        </button>
      </div>
    </form>
  );
}

export default function LoginScreen({ onLogin, onDemo }) {
  const [screen, setScreen] = useState('login');
  const [regAuth, setRegAuth] = useState(null);
  const [regApi, setRegApi] = useState(null);

  if (screen === 'register-step2') {
    return (
      <div className="login-page">
        <RegisterStep2 auth={regAuth} authedApi={regApi} onLogin={onLogin} />
      </div>
    );
  }

  if (screen === 'register') {
    return (
      <div className="login-page">
        <RegisterStep1
          onDone={(auth, api) => { setRegAuth(auth); setRegApi(api); setScreen('register-step2'); }}
          onBack={() => setScreen('login')}
        />
      </div>
    );
  }

  return (
    <div className="login-page">
      <LoginForm onLogin={onLogin} onDemo={onDemo} onRegister={() => setScreen('register')} />
    </div>
  );
}
