import { useMemo } from 'react';
import Spinner from '../components/Spinner.jsx';
import BarChart from '../components/charts/BarChart.jsx';

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

function YearRow({ data }) {
  const { year, totalDist, totalPrice, pricePer100km, kwhPer100km, prev, count } = data;
  const cards = [
    { label: 'Total Distance',   value: totalDist > 0 ? totalDist.toLocaleString('de-DE') + ' km' : '—', delta: prev && totalDist > 0 ? <Delta val={totalDist} prev={prev.totalDist} lowerIsBetter={false} unit="km" decimals={0} /> : null },
    { label: 'Total Price',      value: totalPrice > 0 ? totalPrice.toFixed(2) + ' €' : '—',             delta: prev && totalPrice > 0 ? <Delta val={totalPrice} prev={prev.totalPrice} lowerIsBetter={true} unit="€" decimals={2} /> : null },
    { label: 'Price per 100 km', value: pricePer100km > 0 ? pricePer100km.toFixed(2) + ' €' : '—',       delta: prev && pricePer100km > 0 ? <Delta val={pricePer100km} prev={prev.pricePer100km} lowerIsBetter={true} unit="€" decimals={2} /> : null },
    { label: 'kWh / 100 km',     value: kwhPer100km > 0 ? kwhPer100km.toFixed(2) : '—',                   delta: prev && kwhPer100km > 0 ? <Delta val={kwhPer100km} prev={prev.kwhPer100km} lowerIsBetter={true} unit="kWh" decimals={2} /> : null },
  ];
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: '-0.3px', marginBottom: 12, color: 'var(--text)' }}>
        {year}
        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-light)', marginLeft: 10 }}>{count} session{count !== 1 ? 's' : ''}</span>
      </div>
      <div className="stats-grid">
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

export default function YearlyTrendsView({ charges, loading, selectedCarId }) {
  const yearlyData = useMemo(() => {
    const carCharges = charges.filter((c) => c.car_id === selectedCarId);
    const byYear = {};
    carCharges.forEach((c) => {
      const yr = new Date(c.date).getFullYear();
      if (!byYear[yr]) byYear[yr] = [];
      byYear[yr].push(c);
    });
    const years = Object.keys(byYear).map(Number).sort();

    // Segment-based attribution: walk all charges in odometer order; each
    // segment (i → i+1) attributes kWh and cost of charge i to charge i's year.
    const segByYear = {};
    const sortedAll = [...carCharges].filter((c) => c.car_odometer)
      .sort((a, b) => a.car_odometer - b.car_odometer);
    for (let i = 1; i < sortedAll.length; i++) {
      const km = sortedAll[i].car_odometer - sortedAll[i - 1].car_odometer;
      if (km <= 0) continue;
      const src = sortedAll[i - 1];
      const yr = new Date(src.date).getFullYear();
      if (!segByYear[yr]) segByYear[yr] = { km: 0, kwh: 0, costKm: 0, cost: 0 };
      segByYear[yr].km += km;
      segByYear[yr].kwh += src.kwh_charged / 100;
      if (src.price_total != null) {
        segByYear[yr].costKm += km;
        segByYear[yr].cost += src.price_total / 100;
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

    return years.map((yr, idx) => {
      const cs = byYear[yr];
      const totalKwh = cs.reduce((s, c) => s + c.kwh_charged, 0) / 100;
      const totalPrice = cs.filter((c) => c.price_total != null).reduce((s, c) => s + c.price_total, 0) / 100;
      const m = yearMetrics(yr);

      const prev = idx > 0 ? years[idx - 1] : null;
      const prevData = prev != null ? (() => {
        const pcs = byYear[prev];
        const pm = yearMetrics(prev);
        return {
          totalDist: pm.totalDist,
          totalPrice: pcs.filter((c) => c.price_total != null).reduce((s, c) => s + c.price_total, 0) / 100,
          pricePer100km: pm.pricePer100km,
          kwhPer100km: pm.kwhPer100km,
        };
      })() : null;

      return { year: yr, totalDist: m.totalDist, totalKwh, totalPrice, pricePer100km: m.pricePer100km, kwhPer100km: m.kwhPer100km, prev: prevData, count: cs.length };
    });
  }, [charges, selectedCarId]);

  if (loading) return <Spinner />;
  if (yearlyData.length === 0) return (
    <div className="empty-state" style={{ marginTop: 60 }}>
      <div className="empty-state-icon">📅</div>
      <div className="empty-state-text">No charge data yet to display yearly trends.</div>
    </div>
  );

  const hasMultiple = yearlyData.length > 1;

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <div className="section-header" style={{ marginBottom: 20 }}>
        <div className="section-title">Yearly Trends</div>
        <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Full dataset — all time</span>
      </div>

      {yearlyData.map((d) => <YearRow key={d.year} data={d} />)}

      {hasMultiple && (
        <div className="charts-grid" style={{ marginTop: 8 }}>
          <div className="chart-card">
            <div className="chart-card-header"><div className="chart-card-title">Total Cost <span className="chart-card-unit">€ per year</span></div></div>
            <div className="chart-canvas-wrap">
              <BarChart labels={yearlyData.map((d) => String(d.year))} values={yearlyData.map((d) => parseFloat(d.totalPrice.toFixed(2)))} unit="€" color="oklch(0.52 0.19 252)" />
            </div>
          </div>
          <div className="chart-card">
            <div className="chart-card-header"><div className="chart-card-title">Price per 100 km <span className="chart-card-unit">€</span></div></div>
            <div className="chart-canvas-wrap">
              <BarChart labels={yearlyData.map((d) => String(d.year))} values={yearlyData.map((d) => parseFloat(d.pricePer100km.toFixed(2)))} unit="€/100 km" color="#f97316" />
            </div>
          </div>
          <div className="chart-card">
            <div className="chart-card-header"><div className="chart-card-title">Distance driven <span className="chart-card-unit">km per year</span></div></div>
            <div className="chart-canvas-wrap">
              <BarChart labels={yearlyData.map((d) => String(d.year))} values={yearlyData.map((d) => d.totalDist)} unit="km" color="#22c55e" />
            </div>
          </div>
          <div className="chart-card">
            <div className="chart-card-header"><div className="chart-card-title">Consumption <span className="chart-card-unit">kWh / 100 km</span></div></div>
            <div className="chart-canvas-wrap">
              <BarChart labels={yearlyData.map((d) => String(d.year))} values={yearlyData.map((d) => parseFloat(d.kwhPer100km.toFixed(2)))} unit="kWh/100 km" color="#8b5cf6" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
