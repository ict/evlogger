import { useState } from 'react';
import { makeApi } from '../api.js';

const API_BASE = '/api';

const safeStorage = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
};

export default function LoginScreen({ onLogin, onDemo }) {
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
    <div className="login-page">
      <form className="login-card" onSubmit={submit}>
        <div className="login-logo">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
          </svg>
          <div className="login-logo-text">Charge<span>Logger</span></div>
        </div>
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
      </form>
    </div>
  );
}
