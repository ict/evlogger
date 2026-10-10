import { useEffect, useState } from 'react';
import Modal from '../components/Modal.jsx';
import ConfirmDialog from '../components/ConfirmDialog.jsx';

function fmtDate(iso) {
  if (!iso) return 'Never';
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function ApiTokensModal({ open, onClose, api, toast }) {
  const [tokens, setTokens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [name, setName] = useState('');
  const [expiresAt, setExpiresAt] = useState('');
  const [creating, setCreating] = useState(false);
  const [err, setErr] = useState('');
  const [newToken, setNewToken] = useState(null);
  const [copied, setCopied] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      setTokens(await api.listApiTokens());
    } catch (e) {
      toast(e.message, 'error');
    }
    setLoading(false);
  };

  useEffect(() => {
    if (open) {
      setName('');
      setExpiresAt('');
      setErr('');
      setNewToken(null);
      setCopied(false);
      load();
    }
  }, [open]);

  const handleCreate = async () => {
    if (!name.trim()) { setErr('Name is required.'); return; }
    setCreating(true);
    setErr('');
    try {
      const result = await api.createApiToken({ name: name.trim(), expires_at: expiresAt || null });
      setNewToken(result.token);
      setName('');
      setExpiresAt('');
    } catch (e) {
      setErr(e.message);
    }
    setCreating(false);
  };

  const handleDoneReveal = async () => {
    setNewToken(null);
    setCopied(false);
    await load();
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(newToken).then(() => setCopied(true));
  };

  const handleDelete = async () => {
    const id = confirmDelete;
    setConfirmDelete(null);
    try {
      await api.deleteApiToken(id);
      toast('Token deleted.', 'success');
      await load();
    } catch (e) {
      toast(e.message, 'error');
    }
  };

  const tokenName = confirmDelete ? tokens.find((t) => t.id === confirmDelete)?.name : '';

  return (
    <>
      <Modal open={open} onClose={newToken ? undefined : onClose} title="API Tokens" width={600}
        footer={newToken ? (
          <button className="btn btn-primary" onClick={handleDoneReveal}>Done</button>
        ) : (
          <button className="btn btn-ghost" onClick={onClose}>Close</button>
        )}>
        {newToken ? (
          <div>
            <div style={{ background: 'var(--accent-bg)', border: '1px solid var(--accent-border)', borderRadius: 8, padding: '12px 14px', marginBottom: 16 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>Copy this token now — it will not be shown again.</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>Store it somewhere safe. You can always delete and recreate tokens.</div>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <code style={{ flex: 1, background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 6, padding: '8px 12px', fontSize: 12, fontFamily: 'monospace', wordBreak: 'break-all', lineHeight: 1.6 }}>{newToken}</code>
              <button className="btn btn-sm btn-ghost" style={{ flexShrink: 0 }} onClick={handleCopy}>{copied ? 'Copied!' : 'Copy'}</button>
            </div>
          </div>
        ) : (
          <div>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)', fontSize: 13 }}>Loading…</div>
            ) : tokens.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '16px 0 20px', color: 'var(--text-muted)', fontSize: 13 }}>No tokens yet.</div>
            ) : (
              <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: 20, fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: 'var(--text-muted)', fontSize: 12 }}>Name</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: 'var(--text-muted)', fontSize: 12 }}>Preview</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: 'var(--text-muted)', fontSize: 12 }}>Created</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: 'var(--text-muted)', fontSize: 12 }}>Expires</th>
                    <th style={{ textAlign: 'left', padding: '6px 8px', fontWeight: 600, color: 'var(--text-muted)', fontSize: 12 }}>Last used</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {tokens.map((t) => (
                    <tr key={t.id} style={{ borderBottom: '1px solid var(--border)' }}>
                      <td style={{ padding: '8px 8px', fontWeight: 600 }}>{t.name}</td>
                      <td style={{ padding: '8px 8px' }}><code style={{ fontSize: 12, fontFamily: 'monospace', background: 'var(--bg)', padding: '2px 6px', borderRadius: 4 }}>{t.preview}…</code></td>
                      <td style={{ padding: '8px 8px', color: 'var(--text-muted)' }}>{fmtDate(t.created_at)}</td>
                      <td style={{ padding: '8px 8px', color: 'var(--text-muted)' }}>{fmtDate(t.expires_at)}</td>
                      <td style={{ padding: '8px 8px', color: 'var(--text-muted)' }}>{fmtDate(t.last_used_at)}</td>
                      <td style={{ padding: '8px 8px' }}>
                        <button className="btn btn-sm btn-danger" onClick={() => setConfirmDelete(t.id)}>Delete</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 12 }}>Create new token</div>
              {err && (
                <div style={{ background: 'var(--danger-bg)', border: '1px solid var(--danger-border)', borderRadius: 8, padding: '9px 13px', fontSize: 13, color: 'var(--red)', marginBottom: 12 }}>{err}</div>
              )}
              <div className="form-row">
                <div className="form-group" style={{ flex: 2 }}>
                  <label className="form-label">Name</label>
                  <input type="text" className="form-input" placeholder="e.g. Home Assistant" value={name} onChange={(e) => setName(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleCreate()} />
                </div>
                <div className="form-group" style={{ flex: 1 }}>
                  <label className="form-label">Expires (optional)</label>
                  <input type="date" className="form-input" value={expiresAt} onChange={(e) => setExpiresAt(e.target.value)} />
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>{creating ? 'Creating…' : 'Create token'}</button>
              </div>
            </div>
          </div>
        )}
      </Modal>
      <ConfirmDialog
        open={!!confirmDelete}
        message={`Delete token "${tokenName}"? Any integrations using it will stop working.`}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(null)}
      />
    </>
  );
}
