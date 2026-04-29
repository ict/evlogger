import { useCallback, useEffect, useState } from 'react';

function RoleBadge({ isAdmin }) {
  return (
    <span style={{
      padding: '2px 8px',
      borderRadius: 12,
      background: isAdmin ? 'var(--primary)' : 'var(--bg-secondary)',
      color: isAdmin ? 'white' : undefined,
      fontSize: 11,
    }}>
      {isAdmin ? 'Admin' : 'User'}
    </span>
  );
}

export default function AdminView({ api, toast }) {
  const [settings, setSettings] = useState(null);
  const [saving, setSaving] = useState(false);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [userDetail, setUserDetail] = useState(null);
  const [loadingUsers, setLoadingUsers] = useState(false);

  const loadUsers = useCallback(async () => {
    setLoadingUsers(true);
    try {
      const userList = await api.getUsers();
      setUsers(userList);
    } catch (e) {
      toast(e.message, 'error');
    }
    setLoadingUsers(false);
  }, [api, toast]);

  useEffect(() => {
    api.getAdminSettings().then(setSettings).catch(() => {});
    loadUsers();
  }, [api, loadUsers]);

  const toggleSetting = async () => {
    setSaving(true);
    try {
      const updated = await api.updateAdminSettings({ registration_enabled: !settings.registration_enabled });
      setSettings(updated);
      toast('Settings saved.');
    } catch (e) { toast(e.message, 'error'); }
    setSaving(false);
  };

  const handleToggleAdmin = async (userId, username) => {
    if (!confirm(`Toggle admin status for ${username}?`)) return;
    try {
      await api.toggleUserAdmin(userId);
      toast('User admin status updated.');
      loadUsers();
    } catch (e) {
      toast(e.message, 'error');
    }
  };

  const handleDeleteUser = async (userId, username) => {
    if (!confirm(`Delete user ${username}? This will also delete all their cars, CPOs, and charges. This action cannot be undone!`)) return;
    try {
      await api.deleteUser(userId);
      toast('User deleted.');
      if (selectedUser?.id === userId) {
        setSelectedUser(null);
        setUserDetail(null);
      }
      loadUsers();
    } catch (e) {
      toast(e.message, 'error');
    }
  };

  const loadUserDetail = async (user) => {
    if (selectedUser?.id === user.id) {
      setSelectedUser(null);
      setUserDetail(null);
      return;
    }
    setSelectedUser(user);
    try {
      const detail = await api.getUserDetail(user.id);
      setUserDetail(detail);
    } catch (e) {
      toast(e.message, 'error');
    }
  };

  return (
    <div style={{ maxWidth: 900, margin: '0 auto' }}>
      <div className="section-header">
        <div className="section-title">Admin</div>
      </div>

      {/* Site Settings */}
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
                onClick={toggleSetting}
                disabled={saving}
                style={{ whiteSpace: 'nowrap' }}
              >
                {settings.registration_enabled ? 'Enabled' : 'Disabled'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* User Management */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-header">
          <div className="card-title">Users</div>
        </div>
        <div className="card-body">
          {loadingUsers ? (
            <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>Loading users…</div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
              <thead>
                <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                  <th style={{ padding: 8 }}>Username</th>
                  <th style={{ padding: 8 }}>Email</th>
                  <th style={{ padding: 8 }}>Cars</th>
                  <th style={{ padding: 8 }}>CPOs</th>
                  <th style={{ padding: 8 }}>Charges</th>
                  <th style={{ padding: 8 }}>Role</th>
                  <th style={{ padding: 8 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr
                    key={user.id}
                    style={{
                      borderBottom: '1px solid var(--border-color)',
                      cursor: 'pointer',
                      background: selectedUser?.id === user.id ? 'var(--bg-secondary)' : 'transparent',
                    }}
                    onClick={() => loadUserDetail(user)}
                  >
                    <td style={{ padding: 8 }}>
                      <div style={{ fontWeight: 500 }}>{user.username}</div>
                      {user.full_name && (
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{user.full_name}</div>
                      )}
                    </td>
                    <td style={{ padding: 8, color: 'var(--text-muted)' }}>{user.email || '—'}</td>
                    <td style={{ padding: 8 }}>{user.cars_count}</td>
                    <td style={{ padding: 8 }}>{user.cpos_count}</td>
                    <td style={{ padding: 8 }}>{user.charges_count}</td>
                    <td style={{ padding: 8 }}>
                      <RoleBadge isAdmin={user.is_admin} />
                    </td>
                    <td style={{ padding: 8 }} onClick={(e) => e.stopPropagation()}>
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => handleToggleAdmin(user.id, user.username)}
                        style={{ fontSize: 11, marginRight: 4 }}
                      >
                        {user.is_admin ? 'Remove Admin' : 'Make Admin'}
                      </button>
                      <button
                        className="btn btn-sm btn-ghost"
                        onClick={() => handleDeleteUser(user.id, user.username)}
                        style={{ fontSize: 11, color: 'var(--error)' }}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* User Detail Panel */}
      {userDetail && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-header">
            <div className="card-title">
              {userDetail.username}'s Resources
            </div>
          </div>
          <div className="card-body">
            {/* Cars */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                Cars ({userDetail.cars.length})
              </div>
              {userDetail.cars.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>No cars</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                      <th style={{ padding: 6 }}>Name</th>
                      <th style={{ padding: 6 }}>Make</th>
                      <th style={{ padding: 6 }}>Model</th>
                      <th style={{ padding: 6 }}>Battery</th>
                      <th style={{ padding: 6 }}>Odometer</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userDetail.cars.map((car) => (
                      <tr key={car.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: 6, fontWeight: 500 }}>{car.name}</td>
                        <td style={{ padding: 6 }}>{car.make || '—'}</td>
                        <td style={{ padding: 6 }}>{car.model || '—'}</td>
                        <td style={{ padding: 6 }}>{car.battery_capacity / 100} kWh</td>
                        <td style={{ padding: 6 }}>{car.odometer.toLocaleString('de-DE')} km</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* CPOs */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                CPOs ({userDetail.cpos.length})
              </div>
              {userDetail.cpos.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>No CPOs</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                      <th style={{ padding: 6 }}>Name</th>
                      <th style={{ padding: 6 }}>Default Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userDetail.cpos.map((cpo) => (
                      <tr key={cpo.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: 6, fontWeight: 500 }}>{cpo.name}</td>
                        <td style={{ padding: 6 }}>{(cpo.default_price / 100).toFixed(2)} /kWh</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* Charges */}
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>
                Recent Charges ({userDetail.charges.length})
              </div>
              {userDetail.charges.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>No charges</div>
              ) : (
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                  <thead>
                    <tr style={{ textAlign: 'left', borderBottom: '1px solid var(--border-color)' }}>
                      <th style={{ padding: 6 }}>Date</th>
                      <th style={{ padding: 6 }}>Car</th>
                      <th style={{ padding: 6 }}>CPO</th>
                      <th style={{ padding: 6 }}>kWh</th>
                      <th style={{ padding: 6 }}>Price</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userDetail.charges.map((charge) => (
                      <tr key={charge.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: 6 }}>{new Date(charge.date).toLocaleString()}</td>
                        <td style={{ padding: 6 }}>{charge.car_name || '—'}</td>
                        <td style={{ padding: 6 }}>{charge.cpo_name || '—'}</td>
                        <td style={{ padding: 6 }}>{(charge.kwh_charged / 100).toFixed(2)}</td>
                        <td style={{ padding: 6 }}>{(charge.price_total / 100).toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
