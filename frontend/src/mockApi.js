const MOCK_CPOS = [
  { id: 'cpo1', name: 'Tesla Supercharger', default_price: 42, owner_id: 'demo' },
  { id: 'cpo2', name: 'Ionity', default_price: 79, owner_id: 'demo' },
  { id: 'cpo3', name: 'EnBW', default_price: 45, owner_id: 'demo' },
  { id: 'cpo4', name: 'REWE Charging', default_price: 39, owner_id: 'demo' },
  { id: 'cpo5', name: 'Allego', default_price: 52, owner_id: 'demo' },
];
const MOCK_CARS = [
  { id: 'car1', name: 'Model Y', make: 'Tesla', model: 'Model Y LR', color: '#dc2626', odometer: 18000, battery_capacity: 75, owner_id: 'demo' },
  { id: 'car2', name: 'ID.4 Pro', make: 'Volkswagen', model: 'ID.4 Pro', color: '#2563eb', odometer: 8000, battery_capacity: 77, owner_id: 'demo' },
];

function generateMockCharges() {
  const list = [];
  let uid = 1;
  const cpoPrices = { cpo1: 42, cpo2: 79, cpo3: 45, cpo4: 39, cpo5: 52 };
  const cpoNames = { cpo1: 'Tesla Supercharger', cpo2: 'Ionity', cpo3: 'EnBW', cpo4: 'REWE Charging', cpo5: 'Allego' };

  let odo1 = 8500;
  const start1 = new Date(); start1.setMonth(start1.getMonth() - 13); start1.setDate(1);

  for (let m = 0; m < 14; m++) {
    const base = new Date(start1); base.setMonth(base.getMonth() + m);
    const sessions = m % 3 === 1 ? 3 : 2;
    for (let s = 0; s < sessions; s++) {
      const day = 3 + s * Math.floor(26 / sessions) + (s === 0 ? 0 : 1);
      const d = new Date(base); d.setDate(Math.min(day, 28));
      d.setHours(s === 0 ? 9 + Math.floor(Math.random() * 4) : 20, Math.floor(Math.random() * 59));
      const isDC = s === 0;
      const km = Math.floor(600 + Math.random() * 700);
      odo1 += km;
      const kwh = isDC
        ? Math.floor((32 + Math.random() * 28) * 100)
        : Math.floor((14 + Math.random() * 16) * 100);
      const cpoId = isDC ? ['cpo1', 'cpo2', 'cpo3'][Math.floor(Math.random() * 3)] : 'cpo4';
      const ppk = Math.max(30, cpoPrices[cpoId] + Math.floor((Math.random() - 0.5) * 12));
      const total = Math.round(kwh * ppk / 100);
      list.push({
        id: `ch${uid++}`, date: d.toISOString(), car_id: 'car1', car_name: 'Model Y',
        car_odometer: odo1, car_soc_after: 78 + Math.floor(Math.random() * 22),
        kwh_charged: kwh, cpo_id: cpoId, cpo_name: cpoNames[cpoId],
        price_total: total, charge_type: isDC ? 'DC' : 'AC',
        note: isDC && Math.random() > 0.6 ? 'Long trip' : null,
        owner_id: 'demo', price_per_kwh: ppk,
      });
    }
  }

  let odo2 = 3200;
  const start2 = new Date(); start2.setMonth(start2.getMonth() - 7); start2.setDate(1);
  for (let m = 0; m < 7; m++) {
    const base = new Date(start2); base.setMonth(base.getMonth() + m);
    for (let s = 0; s < 2; s++) {
      const day = 2 + s * 14; const d = new Date(base); d.setDate(Math.min(day, 27));
      d.setHours(s === 0 ? 11 : 19, Math.floor(Math.random() * 59));
      const isDC = s === 0;
      odo2 += Math.floor(500 + Math.random() * 600);
      const kwh = isDC
        ? Math.floor((38 + Math.random() * 32) * 100)
        : Math.floor((18 + Math.random() * 18) * 100);
      const cpoId = isDC ? ['cpo2', 'cpo3', 'cpo5'][Math.floor(Math.random() * 3)] : 'cpo3';
      const ppk = Math.max(32, cpoPrices[cpoId] + Math.floor((Math.random() - 0.5) * 10));
      const total = Math.round(kwh * ppk / 100);
      list.push({
        id: `ch${uid++}`, date: d.toISOString(), car_id: 'car2', car_name: 'ID.4 Pro',
        car_odometer: odo2, car_soc_after: 72 + Math.floor(Math.random() * 28),
        kwh_charged: kwh, cpo_id: cpoId, cpo_name: cpoNames[cpoId],
        price_total: total, charge_type: isDC ? 'DC' : 'AC', note: null,
        owner_id: 'demo', price_per_kwh: ppk,
      });
    }
  }

  return list.sort((a, b) => new Date(b.date) - new Date(a.date));
}

export function makeMockApi() {
  let cars = JSON.parse(JSON.stringify(MOCK_CARS));
  let cpos = JSON.parse(JSON.stringify(MOCK_CPOS));
  let charges = generateMockCharges();
  let nextId = 200;
  const delay = () => new Promise((r) => setTimeout(r, 80));
  const nid = () => `m${nextId++}`;

  return {
    async login() { return { access_token: 'demo', token_type: 'bearer' }; },
    async getMe() { return { username: 'demo', full_name: 'Demo User', email: 'demo@chargelogger.app' }; },
    async getCars() { await delay(); return cars; },
    async createCar(d) { await delay(); const c = { ...d, id: nid(), owner_id: 'demo' }; cars.push(c); return c; },
    async updateCar(id, d) { await delay(); const i = cars.findIndex((c) => c.id === id); if (i >= 0) cars[i] = { ...cars[i], ...d }; return cars[i]; },
    async deleteCar(id) { await delay(); cars = cars.filter((c) => c.id !== id); return null; },
    async getCpos() { await delay(); return cpos; },
    async createCpo(d) { await delay(); const c = { ...d, id: nid(), owner_id: 'demo' }; cpos.push(c); return c; },
    async updateCpo(id, d) { await delay(); const i = cpos.findIndex((c) => c.id === id); if (i >= 0) cpos[i] = { ...cpos[i], ...d }; return cpos[i]; },
    async deleteCpo(id) { await delay(); cpos = cpos.filter((c) => c.id !== id); return null; },
    async getCharges(p = {}) {
      await delay();
      let list = [...charges];
      if (p.from_date) list = list.filter((c) => new Date(c.date) >= new Date(p.from_date));
      if (p.to_date) list = list.filter((c) => new Date(c.date) <= new Date(p.to_date));
      return list;
    },
    async createCharge(d) {
      await delay();
      const cpo = cpos.find((c) => c.id === d.cpo_id);
      const car = cars.find((c) => c.id === d.car_id);
      const ppk = d.price_total && d.kwh_charged ? Math.round(d.price_total / d.kwh_charged * 100) : (cpo?.default_price || 0);
      const c = { ...d, id: nid(), owner_id: 'demo', car_name: car?.name, cpo_name: cpo?.name, price_per_kwh: ppk };
      charges.unshift(c); return c;
    },
    async updateCharge(id, d) {
      await delay();
      const i = charges.findIndex((c) => c.id === id);
      if (i >= 0) {
        const cpo = cpos.find((c) => c.id === d.cpo_id);
        const car = cars.find((c) => c.id === d.car_id);
        const ppk = d.price_total && d.kwh_charged ? Math.round(d.price_total / d.kwh_charged * 100) : (cpo?.default_price || 0);
        charges[i] = { ...charges[i], ...d, car_name: car?.name, cpo_name: cpo?.name, price_per_kwh: ppk };
        return charges[i];
      }
    },
    async deleteCharge(id) { await delay(); charges = charges.filter((c) => c.id !== id); return null; },
  };
}
