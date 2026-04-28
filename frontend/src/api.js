export function makeApi(baseUrl, token) {
  const base = baseUrl.replace(/\/$/, '');
  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const req = async (path, opts = {}) => {
    const res = await fetch(base + path, {
      ...opts,
      headers: { 'Content-Type': 'application/json', ...authHeaders, ...(opts.headers || {}) },
    });
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      if (res.status === 401) throw Object.assign(new Error('Unauthorized'), { status: 401 });
      const msg = Array.isArray(data.detail) ? data.detail.map((d) => d.msg).join(', ') : (data.detail || `HTTP ${res.status}`);
      throw new Error(msg);
    }
    return data;
  };

  return {
    login(username, password) {
      const body = new URLSearchParams({ username, password, grant_type: 'password' });
      return fetch(base + '/users/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body,
      }).then((r) => r.json().then((d) => (r.ok ? d : Promise.reject(new Error(d.detail || 'Login failed')))));
    },
    getMe: () => req('/users/me'),
    getCars: () => req('/car/?limit=100'),
    createCar: (d) => req('/car/', { method: 'POST', body: JSON.stringify(d) }),
    updateCar: (id, d) => req(`/car/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
    deleteCar: (id) => req(`/car/${id}`, { method: 'DELETE' }),
    getCpos: () => req('/cpo/?limit=100'),
    createCpo: (d) => req('/cpo/', { method: 'POST', body: JSON.stringify(d) }),
    updateCpo: (id, d) => req(`/cpo/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
    deleteCpo: (id) => req(`/cpo/${id}`, { method: 'DELETE' }),
    getCharges(p = {}) {
      const q = new URLSearchParams({ limit: p.limit || 500, offset: p.offset || 0 });
      if (p.from_date) q.set('from_date', p.from_date);
      if (p.to_date) q.set('to_date', p.to_date);
      return req(`/charge/?${q}`);
    },
    createCharge: (d) => req('/charge/', { method: 'POST', body: JSON.stringify(d) }),
    updateCharge: (id, d) => req(`/charge/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
    deleteCharge: (id) => req(`/charge/${id}`, { method: 'DELETE' }),
  };
}
