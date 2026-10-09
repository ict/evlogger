const MOCK_CPOS = [
  { id: 'cpo0', name: 'Home Wallbox', default_price: 31, owner_id: 'demo' },
  { id: 'cpo1', name: 'Tesla Supercharger', default_price: 49, owner_id: 'demo' },
  { id: 'cpo2', name: 'Ionity', default_price: 69, owner_id: 'demo' },
  { id: 'cpo3', name: 'EnBW', default_price: 59, owner_id: 'demo' },
  { id: 'cpo4', name: 'REWE Charging', default_price: 39, owner_id: 'demo' },
  { id: 'cpo5', name: 'Allego', default_price: 55, owner_id: 'demo' },
];
const ymd = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const monthsAgo = (n, day = 1) => { const d = new Date(); d.setMonth(d.getMonth() - n); d.setDate(day); d.setHours(12, 0, 0, 0); return d; };
const MOCK_CARS = [
  { id: 'car1', name: 'Model Y', make: 'Tesla', model: 'Model Y LR', color: '#dc2626', odometer: 0, battery_capacity: 75, owner_id: 'demo',
    purchase_price: 4590000, purchase_date: ymd(monthsAgo(26, 12)), purchase_odometer: 12400, sale_price: null, sale_date: null, sale_odometer: null, retired: false },
  { id: 'car2', name: 'ID.4 Pro', make: 'Volkswagen', model: 'ID.4 Pro', color: '#2563eb', odometer: 0, battery_capacity: 77, owner_id: 'demo',
    purchase_price: 3790000, purchase_date: ymd(monthsAgo(8, 3)), purchase_odometer: 9800, sale_price: null, sale_date: null, sale_odometer: null, retired: false },
  { id: 'car3', name: 'Zoe', make: 'Renault', model: 'Zoe R135', color: '#16a34a', odometer: 0, battery_capacity: 52, owner_id: 'demo',
    purchase_price: 3290000, purchase_date: ymd(monthsAgo(52, 5)), purchase_odometer: 0, sale_price: 1390000, sale_date: ymd(monthsAgo(16, 20)), sale_odometer: null, retired: true },
];

// How each demo car is driven, charged and paid for
const PROFILES = {
  car1: {
    seed: 11, consumption: 16.5, commute: 36, weekend: [0, 80], tripEvery: 55, trip: [320, 680],
    home: true, dc: ['cpo1', 'cpo1', 'cpo2'], insurance: [108000, 4000], adac: true,
    subscription: { monthly: true, amount: 999, note: 'Premium Connectivity' },
    // Tesla: no fixed service plan, cabin filter yearly, HU every two years
    maintenance: (y) => [['Cabin filter', 7900], ...(y % 2 === 1 ? [['HU / TÜV inspection', 15900]] : [])],
    summerTiresKm: 38000, tireSet: 118000, winterSet: 162000,
    oneOff: [[3, 'tax', 12850, 'Registration & plates'], [9, 'accessories', 12900, 'All-weather floor mats'], [60, 'accessories', 24900, 'Mobile charging cable'], [420, 'accessories', 39900, 'Roof box']],
  },
  car2: {
    seed: 22, consumption: 18.5, commute: 26, weekend: [0, 70], tripEvery: 75, trip: [280, 520],
    home: false, ac: ['cpo4', 'cpo4', 'cpo3'], dc: ['cpo2', 'cpo3', 'cpo5'], insurance: [86000, 0], adac: false,
    subscription: { monthly: false, amount: 9900, note: 'We Connect Plus' },
    maintenance: () => [],
    summerTiresKm: 45000, tireSet: 96000, winterSet: 138000,
    oneOff: [[2, 'tax', 9800, 'Registration & plates'], [14, 'accessories', 8900, 'Trunk liner']],
  },
  car3: {
    seed: 33, consumption: 15.5, commute: 22, weekend: [0, 50], tripEvery: 120, trip: [200, 360],
    home: true, dc: ['cpo3', 'cpo5'], insurance: [56000, 2500], adac: true,
    // Renault requires a yearly service for the battery warranty
    maintenance: (y) => [['Annual service', 18900 + y * 1500], ...(y === 2 ? [['HU / TÜV inspection', 14900], ['12V battery', 16900]] : [])],
    summerTiresKm: 40000, tireSet: 52000, winterSet: 68000,
    oneOff: [[3, 'tax', 11900, 'Registration & plates'], [5, 'accessories', 98000, 'Wallbox incl. installation'], [30, 'accessories', 6900, 'Floor mats']],
  },
};

// Small seeded PRNG so the demo looks the same on every load
function mulberry32(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// Day-by-day simulation: driving drains the battery (more in winter), charging refills it,
// expenses follow the calendar and the odometer. Returns charges and expenses for one car.
function simulateCar(car, p, ids) {
  const rand = mulberry32(p.seed);
  const rnd = (a, b) => Math.floor(a + rand() * (b - a));
  const pick = (arr) => arr[Math.floor(rand() * arr.length)];
  const cpoById = Object.fromEntries(MOCK_CPOS.map((c) => [c.id, c]));
  const charges = [], expenses = [];
  const start = new Date(car.purchase_date + 'T12:00:00');
  const end = car.sale_date ? new Date(car.sale_date + 'T12:00:00') : new Date();
  let odo = car.purchase_odometer || 0;
  let soc = 80;
  let lastTireChange = odo;
  // Used cars come with a set of winter tires
  let hasWinterSet = (car.purchase_odometer || 0) > 0;
  let lastHour = 0;

  const at = (d, h) => { const x = new Date(d); x.setHours(h, rnd(0, 59), 0, 0); return x.toISOString(); };
  const expense = (d, category, amount, note) => expenses.push({
    id: `ex${ids.ex++}`, owner_id: 'demo', date: at(d, rnd(9, 18)), car_id: car.id, car_name: car.name, category, amount, note,
  });
  const charge = (d, hour, cpoId, target, type) => {
    // Keep charges of one day in chronological order so the odometer never goes backwards
    hour = Math.min(23, Math.max(hour, lastHour + 1));
    const loss = type === 'AC' ? 1.1 : 1.05;
    const kwh = Math.round(((target - soc) / 100) * car.battery_capacity * loss * 100);
    if (kwh < 300) return;
    const base = cpoById[cpoId].default_price;
    const ppk = cpoId === 'cpo0' ? base : base + rnd(-3, 4);
    soc = target;
    lastHour = hour;
    charges.push({
      id: `ch${ids.ch++}`, date: at(d, hour), car_id: car.id, car_name: car.name,
      car_odometer: odo, car_soc_after: target, kwh_charged: kwh, cpo_id: cpoId, cpo_name: cpoById[cpoId].name,
      price_total: Math.round((kwh * ppk) / 100), charge_type: type, note: null, owner_id: 'demo', price_per_kwh: ppk,
    });
  };

  p.oneOff.forEach(([days, category, amount, note]) => {
    const d = new Date(start); d.setDate(d.getDate() + days);
    if (d <= end) expense(d, category, amount, note);
  });

  for (let d = new Date(start), day = 0; d <= end; d.setDate(d.getDate() + 1), day++) {
    const doy = Math.floor((d - new Date(d.getFullYear(), 0, 1)) / 864e5);
    const winter = 1 + 0.24 * Math.cos((2 * Math.PI * (doy - 15)) / 365);
    const kwhPerKm = (p.consumption * winter) / 100;
    const weekday = d.getDay() % 6 !== 0;
    const isTrip = day > 0 && rand() < 1 / p.tripEvery;
    lastHour = 0;

    // Calendar-based expenses
    const ownedYear = Math.floor(day / 365);
    if (day % 365 === 0) {
      expense(d, 'insurance', p.insurance[0] - ownedYear * p.insurance[1] + rnd(-2000, 2000), 'Annual premium');
      if (p.adac) expense(d, 'other', 9400, 'ADAC membership');
      if (p.subscription && !p.subscription.monthly) expense(d, 'subscriptions', p.subscription.amount, p.subscription.note);
    }
    if (p.subscription?.monthly && day % 30 === 0) expense(d, 'subscriptions', p.subscription.amount, p.subscription.note);
    if (day % 365 === 200) p.maintenance(ownedYear).forEach(([note, amount]) => expense(d, 'maintenance', amount, note));
    const m = d.getMonth(), dom = d.getDate();
    if (m === 9 && dom === 20) {
      if (!hasWinterSet) { expense(d, 'tires', p.winterSet, 'Winter tires on rims'); hasWinterSet = true; }
      else expense(d, 'tires', rnd(4500, 6000), 'Tire swap (winter)');
    }
    if (m === 3 && dom === 8 && hasWinterSet) {
      if (odo - lastTireChange > p.summerTiresKm) { expense(d, 'tires', p.tireSet, 'New summer tires incl. fitting'); lastTireChange = odo; }
      else expense(d, 'tires', rnd(4500, 6000), 'Tire swap (summer)');
    }
    if (rand() < 1 / 28) expense(d, 'cleaning', pick([1290, 1490, 1690, 1990]), 'Car wash');
    if (m === 4 && dom === 2) expense(d, 'cleaning', 8900, 'Interior cleaning');
    if (rand() < (weekday ? 0.06 : 0.12)) expense(d, 'tolls_parking', rnd(150, 1200), 'Parking');

    if (isTrip) {
      // Road trip: fast-charge whenever the battery gets low, park at the destination
      let remaining = rnd(p.trip[0], p.trip[1]);
      while (remaining > 0) {
        const range = Math.max(0, ((soc - 12) / 100) * car.battery_capacity / kwhPerKm);
        const leg = Math.min(remaining, range);
        odo += Math.round(leg); remaining -= leg;
        soc -= (leg * kwhPerKm / car.battery_capacity) * 100;
        if (remaining > 0) charge(d, rnd(10, 17), pick(p.dc), rnd(75, 86), 'DC');
      }
      if (rand() < 0.6) expense(d, 'tolls_parking', rnd(1500, 3200), 'Parking garage');
      if (rand() < 0.15) expense(d, 'tolls_parking', 1290, 'Austria vignette (10 days)');
    } else {
      const km = weekday ? p.commute + rnd(-8, 15) : rnd(p.weekend[0], p.weekend[1]);
      odo += km;
      soc -= (km * kwhPerKm / car.battery_capacity) * 100;
    }

    // Everyday charging: at home overnight, or at a public charger when there is no wallbox
    if (p.home && soc < 35 + rnd(0, 10)) charge(d, rnd(18, 22), 'cpo0', rand() < 0.2 ? 90 : 80, 'AC');
    else if (!p.home && soc < 28) {
      if (rand() < 0.3) charge(d, rnd(8, 19), pick(p.dc), 80, 'DC');
      else charge(d, rnd(9, 19), pick(p.ac), 85, 'AC');
    }
  }
  return { charges, expenses, odometer: odo };
}

function generateMockData() {
  const ids = { ch: 1, ex: 1 };
  const charges = [], expenses = [];
  const cars = JSON.parse(JSON.stringify(MOCK_CARS));
  for (const car of cars) {
    const sim = simulateCar(car, PROFILES[car.id], ids);
    charges.push(...sim.charges); expenses.push(...sim.expenses);
    // Like the backend, a car's odometer follows its newest charge
    car.odometer = sim.charges.length ? sim.charges[sim.charges.length - 1].car_odometer : car.purchase_odometer;
    if (car.sale_date) car.sale_odometer = sim.odometer;
  }
  const byDateDesc = (a, b) => new Date(b.date) - new Date(a.date);
  return { cars, charges: charges.sort(byDateDesc), expenses: expenses.sort(byDateDesc) };
}

export function makeMockApi() {
  const data = generateMockData();
  let charges = data.charges;
  let cars = data.cars;
  let cpos = JSON.parse(JSON.stringify(MOCK_CPOS));
  let expenses = data.expenses;
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
    async getMe() { return { username: 'demo', full_name: 'Demo User', email: 'demo@evlogger.app' }; },
    async getCars() { await delay(); return cars; },
    async createCar(d) { await delay(); const c = { ...d, id: nid(), owner_id: 'demo', retired: !!d.sale_date }; cars.push(c); return c; },
    async updateCar(id, d) {
      await delay();
      const i = cars.findIndex((c) => c.id === id);
      if (i < 0) return undefined;
      const m = { ...cars[i], ...d };
      if (!m.sale_date && (m.sale_price != null || m.sale_odometer != null)) throw new Error('sale_price and sale_odometer require a sale_date');
      if (m.sale_date) {
        if (m.purchase_date && m.sale_date < m.purchase_date) throw new Error('sale_date must not be before purchase_date');
        const maxOdo = charges.filter((c) => c.car_id === id).reduce((x, c) => Math.max(x, c.car_odometer || 0), 0);
        m.sale_odometer = m.sale_odometer ?? m.odometer;
        if (m.sale_odometer < maxOdo) throw new Error(`sale_odometer must be at least the latest charge odometer (${maxOdo})`);
        m.sale_price = m.sale_price ?? 0;
      }
      m.retired = !!m.sale_date;
      cars[i] = m;
      return m;
    },
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
