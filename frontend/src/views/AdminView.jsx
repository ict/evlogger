import { useEffect, useState } from 'react';

export default function AdminView({ api, toast }) {
  const [settings, setSettings] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getAdminSettings().then(setSettings).catch(() => {});
  }, [api]);

  const toggle = async () => {
    setSaving(true);
    try {
      const updated = await api.updateAdminSettings({ registration_enabled: !settings.registration_enabled });
      setSettings(updated);
      toast('Settings saved.');
    } catch (e) { toast(e.message, 'error'); }
    setSaving(false);
  };

  return (
    <div style={{ maxWidth: 520, margin: '0 auto' }}>
      <div className="section-header">
        <div className="section-title">Admin</div>
      </div>
      <div className="card">
        <div className="card-header"><div className="card-title">Site Settings</div></div>
        <div className="card-body">
          {settings === null ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading…</div>
          ) : (
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
              <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>Allow new registrations</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>
                  When disabled, new users cannot sign up. The first-ever user can always register.
                </div>
              </div>
              <button
                className={`btn btn-sm ${settings.registration_enabled ? 'btn-primary' : 'btn-ghost'}`}
                onClick={toggle}
                disabled={saving}
                style={{ whiteSpace: 'nowrap' }}
              >
                {settings.registration_enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
