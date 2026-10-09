const MOCK_CPOS = [
  { id: 'cpo1', name: 'Tesla Supercharger', default_price: 42, owner_id: 'demo' },
  { id: 'cpo2', name: 'Ionity', default_price: 79, owner_id: 'demo' },
  { id: 'cpo3', name: 'EnBW', default_price: 45, owner_id: 'demo' },
  { id: 'cpo4', name: 'REWE Charging', default_price: 39, owner_id: 'demo' },
  { id: 'cpo5', name: 'Allego', default_price: 52, owner_id: 'demo' },
];
const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const monthsAgo = (n, day = 1) => { const d = new Date(); d.setMonth(d.getMonth() - n); d.setDate(day); d.setHours(12, 0, 0, 0); return d; };
const rnd = (a, b) => Math.floor(a + Math.random() * (b - a));
const MOCK_CARS = [
  { id: 'car1', name: 'Model Y', make: 'Tesla', model: 'Model Y LR', color: '#dc2626', odometer: 18000, battery_capacity: 75, owner_id: 'demo',
    purchase_price: 4890000, purchase_date: ymd(monthsAgo(26, 12)), purchase_odometer: 4200, sale_price: null, sale_date: null, sale_odometer: null, retired: false },
  { id: 'car2', name: 'ID.4 Pro', make: 'Volkswagen', model: 'ID.4 Pro', color: '#2563eb', odometer: 8000, battery_capacity: 77, owner_id: 'demo',
    purchase_price: 4290000, purchase_date: ymd(monthsAgo(8, 3)), purchase_odometer: 1800, sale_price: null, sale_date: null, sale_odometer: null, retired: false },
  { id: 'car3', name: 'Zoe', make: 'Renault', model: 'Zoe R135', color: '#16a34a', odometer: 0, battery_capacity: 52, owner_id: 'demo',
    purchase_price: 2450000, purchase_date: ymd(monthsAgo(52, 5)), purchase_odometer: 0, sale_price: 1180000, sale_date: ymd(monthsAgo(16, 20)), sale_odometer: 0, retired: true },
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

  // Retired car: charges from purchase until shortly before the sale date
  const car3 = MOCK_CARS.find((c) => c.id === 'car3');
  let odo3 = 0;
  const end3 = new Date(car3.sale_date + 'T12:00:00');
  const cursor = new Date(car3.purchase_date + 'T12:00:00'); cursor.setDate(cursor.getDate() + 6);
  for (let n = 0; cursor <= end3; n++) {
    const d = new Date(cursor); d.setHours(18, rnd(0, 59));
    odo3 += rnd(350, 700);
    const isDC = n % 5 === 4;
    const kwh = isDC ? rnd(2200, 3800) : rnd(1500, 3200);
    const cpoId = isDC ? 'cpo3' : ['cpo4', 'cpo5'][rnd(0, 2)];
    const ppk = Math.max(30, cpoPrices[cpoId] + rnd(-5, 6));
    list.push({
      id: `ch${uid++}`, date: d.toISOString(), car_id: 'car3', car_name: 'Zoe',
      car_odometer: odo3, car_soc_after: 80 + rnd(0, 20),
      kwh_charged: kwh, cpo_id: cpoId, cpo_name: cpoNames[cpoId],
      price_total: Math.round(kwh * ppk / 100), charge_type: isDC ? 'DC' : 'AC', note: null,
      owner_id: 'demo', price_per_kwh: ppk,
    });
    cursor.setDate(cursor.getDate() + rnd(9, 17));
  }
  car3.odometer = car3.sale_odometer = odo3 + rnd(20, 120);

  return list.sort((a, b) => new Date(b.date) - new Date(a.date));
}

function generateMockExpenses(cars) {
  const list = [];
  let uid = 1;
  const add = (car, date, category, amount, note = null) => {
    const end = car.sale_date ? new Date(car.sale_date + 'T23:59:59') : new Date();
    date.setHours(rnd(8, 18), rnd(0, 59), 0, 0);
    if (date > end) return;
    list.push({ id: `ex${uid++}`, owner_id: 'demo', date: date.toISOString(), car_id: car.id, car_name: car.name, category, amount, note });
  };
  const at = (start, days) => { const d = new Date(start); d.setDate(d.getDate() + days); return d; };
  for (const car of cars) {
    const start = new Date(car.purchase_date + 'T12:00:00');
    const end = car.sale_date ? new Date(car.sale_date + 'T12:00:00') : new Date();
    const years = Math.ceil((end - start) / (365 * 864e5));
    for (let y = 0; y < years; y++) {
      const yStart = at(start, y * 365 + 2);
      add(car, yStart, 'insurance', rnd(52000, 78000), 'Annual premium');
      add(car, at(yStart, 3), 'tax', rnd(4000, 9500), 'Vehicle tax');
      add(car, at(start, y * 365 + rnd(250, 340)), 'maintenance', rnd(9000, 32000), y % 2 ? 'Service' : 'Inspection');
      for (let i = 0; i < rnd(4, 9); i++) add(car, at(start, y * 365 + rnd(10, 360)), 'tolls_parking', rnd(200, 2800), Math.random() > 0.5 ? 'Parking' : null);
      for (let i = 0; i < 3; i++) add(car, at(start, y * 365 + rnd(10, 360)), 'cleaning', rnd(800, 2800), i === 0 ? 'Car wash' : null);
    }
    for (let m = 20; m < years * 12; m += 24) add(car, at(start, m * 30 + rnd(0, 20)), 'tires', rnd(42000, 78000), 'Tire change');
    add(car, at(start, 25), 'accessories', rnd(3000, 14000), 'Floor mats');
    if (years >= 2) add(car, at(start, rnd(400, 600)), 'accessories', rnd(4000, 18000), 'Roof rack');
    if (years >= 2) add(car, at(start, rnd(300, 500)), 'other', rnd(2000, 9000), 'Registration fee');
  }
  return list.sort((a, b) => new Date(b.date) - new Date(a.date));
}

export function makeMockApi() {
  let charges = generateMockCharges();
  let cars = JSON.parse(JSON.stringify(MOCK_CARS));
  let cpos = JSON.parse(JSON.stringify(MOCK_CPOS));
  let expenses = generateMockExpenses(cars);
  let apiTokens = [];
  let nextId = 200;
  const delay = () => new Promise((r) => setTimeout(r, 80));
  const nid = () => `m${nextId++}`;
  const checkRetired = (carId, date) => {
    const car = cars.find((c) => c.id === carId);
    if (car?.sale_date && String(date).slice(0, 10) > car.sale_date) throw new Error(`car was retired on ${car.sale_date}`);
  };

  return {
    async login() { return { access_token: 'demo', token_type: 'bearer' }; },
    async getMe() { return { username: 'demo', full_name: 'Demo User', email: 'demo@chargelogger.app' }; },
    async getCars() { await delay(); return cars; },
    async createCar(d) { await delay(); const c = { ...d, id: nid(), owner_id: 'demo', retired: !!d.sale_date }; cars.push(c); return c; },
    async updateCar(id, d) { await delay(); const i = cars.findIndex((c) => c.id === id); if (i >= 0) { cars[i] = { ...cars[i], ...d }; cars[i].retired = !!cars[i].sale_date; } return cars[i]; },
    async deleteCar(id) { await delay(); cars = cars.filter((c) => c.id !== id); charges = charges.filter((c) => c.car_id !== id); expenses = expenses.filter((e) => e.car_id !== id); return null; },
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
      checkRetired(d.car_id, d.date);
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
        checkRetired(d.car_id ?? charges[i].car_id, d.date ?? charges[i].date);
        const cpo = cpos.find((c) => c.id === d.cpo_id);
        const car = cars.find((c) => c.id === d.car_id);
        const ppk = d.price_total && d.kwh_charged ? Math.round(d.price_total / d.kwh_charged * 100) : (cpo?.default_price || 0);
        charges[i] = { ...charges[i], ...d, car_name: car?.name, cpo_name: cpo?.name, price_per_kwh: ppk };
        return charges[i];
      }
    },
    async deleteCharge(id) { await delay(); charges = charges.filter((c) => c.id !== id); return null; },
    async getExpenses(p = {}) {
      await delay();
      let list = [...expenses];
      if (p.car_id) list = list.filter((e) => e.car_id === p.car_id);
      if (p.category) list = list.filter((e) => e.category === p.category);
      if (p.from_date) list = list.filter((e) => new Date(e.date) >= new Date(p.from_date));
      if (p.to_date) list = list.filter((e) => new Date(e.date) <= new Date(p.to_date));
      list.sort((a, b) => new Date(b.date) - new Date(a.date));
      const off = p.offset || 0;
      return list.slice(off, off + (p.limit || 500));
    },
    async createExpense(d) {
      await delay();
      checkRetired(d.car_id, d.date);
      const car = cars.find((c) => c.id === d.car_id);
      const e = { ...d, id: nid(), owner_id: 'demo', car_name: car?.name };
      expenses.unshift(e); return e;
    },
    async updateExpense(id, d) {
      await delay();
      const i = expenses.findIndex((e) => e.id === id);
      if (i < 0) return undefined;
      checkRetired(d.car_id ?? expenses[i].car_id, d.date ?? expenses[i].date);
      const car = cars.find((c) => c.id === (d.car_id ?? expenses[i].car_id));
      expenses[i] = { ...expenses[i], ...d, car_name: car?.name };
      return expenses[i];
    },
    async deleteExpense(id) { await delay(); expenses = expenses.filter((e) => e.id !== id); return null; },
    async listApiTokens() { await delay(); return apiTokens; },
    async createApiToken(d) {
      await delay();
      const t = { id: nid(), name: d.name, preview: 'demo_abc', created_at: new Date().toISOString(), last_used_at: null, expires_at: d.expires_at || null };
      apiTokens.push(t);
      return { ...t, token: 'demo_' + Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2) };
    },
    async deleteApiToken(id) { await delay(); apiTokens = apiTokens.filter((t) => t.id !== id); return { result: 'ok' }; },
  };
}
