import { useMemo } from 'react';
import Spinner from '../components/Spinner.jsx';
import BarChart from '../components/charts/BarChart.jsx';
import { yearlyCosts, usedCategories } from '../costs.js';

function Delta({ val, prev, lowerIsBetter, unit, decimals = 2 }) {
  if (prev == null || prev === 0) return null;
  const diff = val - prev;
  if (Math.abs(diff) < 0.005) return null;
  const better = lowerIsBetter ? diff < 0 : diff > 0;
  const neutral = !lowerIsBetter && diff > 0 && unit === 'km';
  const color = neutral ? 'var(--text-muted)' : better ? 'var(--green)' : 'var(--red)';
  const arrow = diff > 0 ? '↑' : '↓';
  return (
    <div style={{ marginTop: 6, fontSize: 12.5, fontWeight: 600, color, display: 'flex', alignItems: 'center', gap: 3 }}>
      <span>{arrow}</span>
      <span>{Math.abs(diff).toFixed(decimals)}{unit ? ' ' + unit : ''}</span>
    </div>
  );
}

function YearRow({ data, showExpenses }) {
  const { year, totalDist, totalPrice, otherCosts, totalCost, pricePer100km, kwhPer100km, prev, count } = data;
  const d = (val, pv, show, decimals = 2) => (prev && show ? <Delta val={val} prev={pv} lowerIsBetter={true} unit="€" decimals={decimals} /> : null);
  const cards = [
    { label: 'Total Distance',   value: totalDist > 0 ? totalDist.toLocaleString('de-DE') + ' km' : '—', delta: prev && totalDist > 0 ? <Delta val={totalDist} prev={prev.totalDist} lowerIsBetter={false} unit="km" decimals={0} /> : null },
    { label: showExpenses ? 'Charging' : 'Total Price', value: totalPrice > 0 ? totalPrice.toFixed(2) + ' €' : '—', delta: d(totalPrice, prev?.totalPrice, totalPrice > 0) },
    ...(showExpenses ? [
      { label: 'Other costs', value: otherCosts > 0 ? otherCosts.toFixed(2) + ' €' : '—', delta: d(otherCosts, prev?.otherCosts, otherCosts > 0) },
      { label: 'Total', value: totalCost > 0 ? totalCost.toFixed(2) + ' €' : '—', delta: d(totalCost, prev?.totalCost, totalCost > 0) },
    ] : []),
    { label: 'Price per 100 km', value: pricePer100km > 0 ? pricePer100km.toFixed(2) + ' €' : '—',       delta: d(pricePer100km, prev?.pricePer100km, pricePer100km > 0) },
    { label: 'kWh / 100 km',     value: kwhPer100km > 0 ? kwhPer100km.toFixed(2) : '—',                   delta: prev && kwhPer100km > 0 ? <Delta val={kwhPer100km} prev={prev.kwhPer100km} lowerIsBetter={true} unit="kWh" decimals={2} /> : null },
  ];
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.3px', marginBottom: 12, color: 'var(--text)' }}>
        {year}
        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-light)', marginLeft: 10 }}>{count} session{count !== 1 ? 's' : ''}</span>
      </div>
      <div className={`stats-grid${showExpenses ? ' stats-grid-3' : ''}`}>
        {cards.map((c) => (
          <div key={c.label} className="stat-card">
            <div className="stat-label">{c.label}</div>
            <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.5px', lineHeight: 1, color: 'var(--text)' }}>{c.value}</div>
            {c.delta}
          </div>
        ))}
      </div>
    </div>
  );
}

export default function YearlyTrendsView({ charges, loading, expenses = [], expensesLoading, selectedCarId, cars }) {
  const yearlyData = useMemo(() => {
    const carCharges = charges.filter((c) => c.car_id === selectedCarId);
    const car = (cars || []).find((c) => c.id === selectedCarId);
    const cap = car?.battery_capacity || 0;
    const byYear = {};
    carCharges.forEach((c) => {
      const yr = new Date(c.date).getFullYear();
      if (!byYear[yr]) byYear[yr] = [];
      byYear[yr].push(c);
    });
    const costs = yearlyCosts(charges, expenses, selectedCarId);
    // Union: years with only expenses (no charges) still appear
    const years = [...new Set([...Object.keys(byYear), ...Object.keys(costs)].map(Number))].sort((a, b) => a - b);
    const cents = (yr) => costs[yr] || { charging: 0, expenses: 0, byCategory: {} };

    // Fuel-log convention: charge i refills segment (i-1, i). Attribute to charge i's year.
    // SoC-aware when both endpoints carry SoC and capacity known; fallback to raw kwh.
    const segByYear = {};
    const sortedAll = [...carCharges].filter((c) => c.car_odometer)
      .sort((a, b) => a.car_odometer - b.car_odometer);
    for (let i = 1; i < sortedAll.length; i++) {
      const a = sortedAll[i - 1], b = sortedAll[i];
      const km = b.car_odometer - a.car_odometer;
      if (km <= 0) continue;
      const haveSoc = cap > 0 && a.car_soc_after != null && b.car_soc_after != null;
      const consumed = haveSoc
        ? b.kwh_charged / 100 + cap * (a.car_soc_after - b.car_soc_after) / 100
        : b.kwh_charged / 100;
      if (consumed <= 0) continue;
      const yr = new Date(b.date).getFullYear();
      if (!segByYear[yr]) segByYear[yr] = { km: 0, kwh: 0, costKm: 0, cost: 0 };
      segByYear[yr].km += km;
      segByYear[yr].kwh += consumed;
      if (b.price_total != null) {
        segByYear[yr].costKm += km;
        segByYear[yr].cost += b.price_total / 100;
      }
    }
    const yearMetrics = (yr) => {
      const s = segByYear[yr];
      if (!s) return { totalDist: 0, kwhPer100km: 0, pricePer100km: 0 };
      return {
        totalDist: s.km,
        kwhPer100km: s.km > 0 ? s.kwh / s.km * 100 : 0,
        pricePer100km: s.costKm > 0 ? s.cost / s.costKm * 100 : 0,
      };
    };

    const yearFigures = (yr) => {
      const m = yearMetrics(yr);
      const c = cents(yr);
      const totalPrice = c.charging / 100;
      const otherCosts = c.expenses / 100;
      const totalCost = totalPrice + otherCosts;
      return {
        ...m, totalPrice, otherCosts, totalCost, byCategory: c.byCategory,
        runningPer100km: m.totalDist > 0 ? totalCost / m.totalDist * 100 : 0,
      };
    };

    return years.map((yr, idx) => {
      const cs = byYear[yr] || [];
      const totalKwh = cs.reduce((s, c) => s + c.kwh_charged, 0) / 100;
      const prev = idx > 0 ? yearFigures(years[idx - 1]) : null;
      return { year: yr, ...yearFigures(yr), totalKwh, prev, count: cs.length };
    });
  }, [charges, expenses, selectedCarId, cars]);

  const categories = useMemo(() => usedCategories(expenses, selectedCarId), [expenses, selectedCarId]);

  if (loading || expensesLoading) return <Spinner />;
  if (yearlyData.length === 0) return (
    <div className="empty-state" style={{ marginTop: 60 }}>
      <div className="empty-state-icon">📅</div>
      <div className="empty-state-text">No charge or expense data yet to display yearly trends.</div>
    </div>
  );

  const hasMultiple = yearlyData.length > 1;
  const labels = yearlyData.map((d) => String(d.year));

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div className="section-header" style={{ marginBottom: 20 }}>
        <div className="section-title">Yearly Trends</div>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Full dataset — all time</span>
      </div>

      {yearlyData.map((d) => <YearRow key={d.year} data={d} showExpenses={categories.length > 0} />)}

      {hasMultiple && (
        <div className="charts-grid" style={{ marginTop: 8 }}>
          <div className="chart-card">
            <div className="chart-card-header"><div className="chart-card-title">Price per 100 km <span className="chart-card-unit">€</span></div></div>
            <div className="chart-canvas-wrap">
              <BarChart labels={labels} values={yearlyData.map((d) => parseFloat(d.pricePer100km.toFixed(2)))} unit="€/100 km" color="#f97316" showValues valueDecimals={2} valueUnit="€" />
            </div>
          </div>
          {categories.length > 0 && (
            <div className="chart-card">
              <div className="chart-card-header"><div className="chart-card-title">Running cost per 100 km <span className="chart-card-unit">€ · charging + other</span></div></div>
              <div className="chart-canvas-wrap">
                <BarChart labels={labels} values={yearlyData.map((d) => parseFloat(d.runningPer100km.toFixed(2)))} unit="€/100 km" color="#0ea5e9" showValues valueDecimals={2} valueUnit="€" />
              </div>
            </div>
          )}
          <div className="chart-card">
            <div className="chart-card-header"><div className="chart-card-title">Distance driven <span className="chart-card-unit">km per year</span></div></div>
            <div className="chart-canvas-wrap">
              <BarChart labels={labels} values={yearlyData.map((d) => d.totalDist)} unit="km" color="#22c55e" showValues valueDecimals={0} valueUnit="km" />
            </div>
          </div>
          <div className="chart-card">
            <div className="chart-card-header"><div className="chart-card-title">Consumption <span className="chart-card-unit">kWh / 100 km</span></div></div>
            <div className="chart-canvas-wrap">
              <BarChart labels={labels} values={yearlyData.map((d) => parseFloat(d.kwhPer100km.toFixed(2)))} unit="kWh/100 km" color="#8b5cf6" showValues valueDecimals={1} valueUnit="kWh" />
            </div>
          </div>
          <div className="chart-card" style={{ gridColumn: '1 / -1' }}>
            <div className="chart-card-header"><div className="chart-card-title">Total Cost<span className="chart-card-unit">€ per year{categories.length > 0 ? ' · charging + expenses' : ''}</span></div></div>
            <div className="chart-canvas-wrap" style={{ height: categories.length > 0 ? 380 : 260 }}>
              {categories.length > 0 ? (
                <BarChart
                  labels={labels}
                  datasets={[
                    { label: 'Charging', values: yearlyData.map((d) => parseFloat(d.totalPrice.toFixed(2))), color: '#2563eb' },
                    ...categories.map((c) => ({ label: c.label, values: yearlyData.map((d) => parseFloat(((d.byCategory[c.key] || 0) / 100).toFixed(2))), color: c.color })),
                  ]}
                  stacked unit="€" showValues valueDecimals={0} valueUnit="€"
                />
              ) : (
                <BarChart labels={labels} values={yearlyData.map((d) => parseFloat(d.totalPrice.toFixed(2)))} unit="€" color="#2563eb" showValues valueDecimals={0} valueUnit="€" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
