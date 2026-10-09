// Pure cost calculations. Units: all money values are integer cents (1/100 €), except
// *PerKm fields which are € per km (float). Distances are km. Dates are ISO strings.
import { EXPENSE_CATEGORIES, EXPENSE_CATEGORY_MAP } from './components/icons.jsx';

const catKey = (c) => (EXPENSE_CATEGORY_MAP[c] ? c : 'other');
const forCar = (list, carId) => (list || []).filter((x) => x.car_id === carId);
const yearOf = (d) => new Date(d).getFullYear();

// cents; charges without price_total count as 0
export const sumCharging = (charges) => charges.reduce((s, c) => s + (c.price_total || 0), 0);
export const sumExpenses = (expenses) => expenses.reduce((s, e) => s + (e.amount || 0), 0);

// { categoryKey: cents } — unknown categories are folded into 'other'
export function expensesByCategory(expenses) {
  const out = {};
  expenses.forEach((e) => { const k = catKey(e.category); out[k] = (out[k] || 0) + (e.amount || 0); });
  return out;
}

// [{ key, label, amount }] sorted by amount desc, zero entries removed (cents)
export function categoryBreakdown(expenses) {
  const by = expensesByCategory(expenses);
  return Object.entries(by)
    .filter(([, amount]) => amount > 0)
    .map(([key, amount]) => ({ key, label: EXPENSE_CATEGORY_MAP[key].label, amount }))
    .sort((a, b) => b.amount - a.amount);
}

// Expenses of one car within { from_date, to_date } (ISO strings, either optional)
export function expensesInRange(expenses, carId, range = {}) {
  const from = range.from_date ? new Date(range.from_date) : null;
  const to = range.to_date ? new Date(range.to_date) : null;
  return forCar(expenses, carId).filter((e) => {
    const d = new Date(e.date);
    return (!from || d >= from) && (!to || d <= to);
  });
}

// { [year]: { charging, expenses, byCategory } } for one car (cents). Union of years.
export function yearlyCosts(charges, expenses, carId) {
  const out = {};
  const slot = (y) => (out[y] ||= { charging: 0, expenses: 0, byCategory: {} });
  forCar(charges, carId).forEach((c) => { slot(yearOf(c.date)).charging += c.price_total || 0; });
  forCar(expenses, carId).forEach((e) => {
    const s = slot(yearOf(e.date));
    const k = catKey(e.category);
    s.expenses += e.amount || 0;
    s.byCategory[k] = (s.byCategory[k] || 0) + (e.amount || 0);
  });
  return out;
}

// Categories with any spend for this car, in the fixed category order
export function usedCategories(expenses, carId) {
  const by = expensesByCategory(forCar(expenses, carId));
  return EXPENSE_CATEGORIES.filter((c) => by[c.key] > 0);
}

// Whole calendar months owned (purchase_date -> sale_date or now); null without purchase_date
export function ownershipMonths(car, now = new Date()) {
  if (!car?.purchase_date) return null;
  const s = new Date(car.purchase_date + 'T00:00:00');
  const e = car.sale_date ? new Date(car.sale_date + 'T00:00:00') : now;
  const m = (e.getFullYear() - s.getFullYear()) * 12 + (e.getMonth() - s.getMonth()) - (e.getDate() < s.getDate() ? 1 : 0);
  return Math.max(0, m);
}

// Lifetime total cost of ownership for one car. Money in cents, perKm in €/km.
export function computeTco(car, charges, expenses, now = new Date()) {
  const cs = forCar(charges, car.id);
  const es = forCar(expenses, car.id);
  const retired = !!car.retired;
  const charging = sumCharging(cs);
  const exp = sumExpenses(es);
  const hasPurchase = car.purchase_price != null;
  // active: purchase price counted in full; retired: purchase − sale
  const capital = hasPurchase ? car.purchase_price - (retired ? (car.sale_price ?? 0) : 0) : null;

  const maxCharge = cs.reduce((m, c) => Math.max(m, c.car_odometer || 0), 0);
  const endOdo = retired ? (car.sale_odometer || maxCharge) : Math.max(car.odometer || 0, maxCharge);
  const km = Math.max(0, endOdo - (car.purchase_odometer ?? 0));

  const running = charging + exp;
  const months = ownershipMonths(car, now);
  return {
    retired, hasPurchase, charging, expenses: exp, byCategory: categoryBreakdown(es),
    capital, km, running,
    allIn: hasPurchase ? running + capital : null,
    runningPerKm: km > 0 ? running / 100 / km : null,
    allInPerKm: hasPurchase && km > 0 ? (running + capital) / 100 / km : null,
    months,
    depreciationPerYear: retired && hasPurchase && months > 0 ? capital / (months / 12) : null,
  };
}
