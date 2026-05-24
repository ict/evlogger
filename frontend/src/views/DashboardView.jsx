import { useEffect, useMemo, useState } from 'react';
import Spinner from '../components/Spinner.jsx';
import TimeframeBar from '../components/TimeframeBar.jsx';
import LineChart from '../components/charts/LineChart.jsx';
import BarChart from '../components/charts/BarChart.jsx';
import { getTimeframeRange } from '../format.js';

const CPO_PALETTE = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899', '#14b8a6', '#a855f7'];

export default function DashboardView({ api, selectedCarId, cars, tf, setTf, fromDate, setFromDate, toDate, setToDate }) {
  const [tfCharges, setTfCharges] = useState([]);
  const [tfLoading, setTfLoading] = useState(false);

  useEffect(() => {
    if (!api || !selectedCarId) return;
    const range = getTimeframeRange(tf, fromDate, toDate);
    setTfLoading(true);
    api.getCharges(range)
      .then((all) => setTfCharges((all || []).filter((c) => c.car_id === selectedCarId)))
      .catch(() => {})
      .finally(() => setTfLoading(false));
  }, [api, tf, fromDate, toDate, selectedCarId]);

  const car = cars.find((c) => c.id === selectedCarId);
  const stats = useMemo(() => {
    const c = [...tfCharges].sort((a, b) => new Date(a.date) - new Date(b.date));
    const totalKwh = c.reduce((s, x) => s + x.kwh_charged, 0) / 100;
    const withOdo = c.filter((x) => x.car_odometer).sort((a, b) => a.car_odometer - b.car_odometer);
    const odos = withOdo.map((x) => x.car_odometer);
    const maxOdo = odos.length ? odos[odos.length - 1] : 0;
    const totalDist = odos.length > 1 ? odos[odos.length - 1] - odos[0] : 0;
    const cap = car?.battery_capacity || 0;
    let segKwh = 0, segKm = 0, segCost = 0, segCostKm = 0;
    // Fuel-log convention: charge i refills energy consumed in segment (i-1, i).
    // SoC delta corrects when consecutive charges don't refill to same level.
    for (let i = 1; i < withOdo.length; i++) {
      const a = withOdo[i - 1], b = withOdo[i];
      const km = b.car_odometer - a.car_odometer;
      if (km <= 0) continue;
      const haveSoc = cap > 0 && a.car_soc_after != null && b.car_soc_after != null;
      const consumed = haveSoc
        ? b.kwh_charged / 100 + cap * (a.car_soc_after - b.car_soc_after) / 100
        : b.kwh_charged / 100;
      if (consumed <= 0) continue;
      segKm += km;
      segKwh += consumed;
      if (b.price_total != null) {
        segCost += b.price_total / 100;
        segCostKm += km;
      }
    }
    const avgCons = segKm > 0 ? (segKwh / segKm * 100) : 0;
    const acKwh = c.filter((x) => x.charge_type === 'AC').reduce((s, x) => s + x.kwh_charged, 0) / 100;
    const dcKwh = c.filter((x) => x.charge_type === 'DC').reduce((s, x) => s + x.kwh_charged, 0) / 100;
    const totalCost = c.filter((x) => x.price_total != null).reduce((s, x) => s + (x.price_total || 0), 0) / 100;
    const pricedKwh = c.filter((x) => x.price_total != null).reduce((s, x) => s + x.kwh_charged, 0) / 100;
    const avgPpkwh = pricedKwh > 0 ? totalCost / pricedKwh : 0;
    const costPer100km = segCostKm > 0 ? (segCost / segCostKm * 100) : 0;
    return { totalKwh, maxOdo, totalDist, avgCons, acKwh, dcKwh, totalCost, avgPpkwh, costPer100km, count: c.length };
  }, [tfCharges, car?.battery_capacity]);

  const chartData = useMemo(() => {
    const sorted = [...tfCharges].sort((a, b) => new Date(a.date) - new Date(b.date));
    const byMonth = {};
    sorted.forEach((c) => {
      const key = c.date.substring(0, 7);
      if (!byMonth[key]) byMonth[key] = [];
      byMonth[key].push(c);
    });
    const months = Object.keys(byMonth).sort();
    const labels = months.map((m) => { const [y, mo] = m.split('-'); return `${mo}/${y.slice(2)}`; });

    const withOdo = sorted.filter((c) => c.car_odometer);
    const segments = {};
    for (let i = 1; i < withOdo.length; i++) {
      const km = withOdo[i].car_odometer - withOdo[i - 1].car_odometer;
      const kwh = withOdo[i].kwh_charged / 100;
      if (km > 0) {
        const mo = withOdo[i].date.substring(0, 7);
        if (!segments[mo]) segments[mo] = [];
        segments[mo].push({ kwh, km });
      }
    }
    const rawCons = months.map((m) => {
      const segs = segments[m];
      if (!segs?.length) return null;
      const totalKwh = segs.reduce((s, x) => s + x.kwh, 0);
      const totalKm = segs.reduce((s, x) => s + x.km, 0);
      return totalKm > 0 ? parseFloat((totalKwh / totalKm * 100).toFixed(2)) : null;
    });
    const consData = rawCons.map((v, i) => {
      const neighbours = [rawCons[i - 1], v, rawCons[i + 1]].filter((x) => x != null);
      if (!neighbours.length) return null;
      return parseFloat((neighbours.reduce((s, x) => s + x, 0) / neighbours.length).toFixed(2));
    });

    const kmData = months.map((m) => {
      const mc = byMonth[m];
      const odos = mc.filter((c) => c.car_odometer).map((c) => c.car_odometer);
      if (odos.length < 2) return 0;
      return Math.max(...odos) - Math.min(...odos);
    });

    const priceData = months.map((m) => {
      const mc = byMonth[m].filter((c) => c.price_per_kwh);
      if (!mc.length) return null;
      return parseFloat((mc.reduce((s, c) => s + c.price_per_kwh, 0) / mc.length / 100).toFixed(3));
    });

    const byCpo = {};
    sorted.forEach((c) => {
      const n = c.cpo_name || c.cpo_id;
      byCpo[n] = (byCpo[n] || 0) + c.kwh_charged / 100;
    });
    const cpoEntries = Object.entries(byCpo).sort((a, b) => b[1] - a[1]).slice(0, 10);

    return {
      labels, consData, kmData, priceData,
      cpoLabels: cpoEntries.map((e) => e[0]),
      cpoValues: cpoEntries.map((e) => parseFloat(e[1].toFixed(1))),
    };
  }, [tfCharges]);

  if (!selectedCarId) return (
    <div className="empty-state"><div className="empty-state-icon">🚗</div><div className="empty-state-text">No car selected. Add a car to get started.</div></div>
  );

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div className="section-title">{car ? `${car.name}` : 'Dashboard'}</div>
          {car?.make && <div style={{ fontSize: 12.5, color: 'var(--text-muted)', marginTop: 2 }}>{car.make} {car.model} · {car.battery_capacity} kWh battery</div>}
        </div>
        <TimeframeBar value={tf} onChange={setTf} fromDate={fromDate} toDate={toDate} onFrom={setFromDate} onTo={setToDate} />
      </div>

      {tfLoading ? <Spinner /> : (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-label">Avg. Consumption</div>
              <div className="stat-value" style={{ color: 'var(--accent)' }}>{stats.avgCons > 0 ? stats.avgCons.toFixed(1) : '—'}<span className="stat-unit">kWh/100km</span></div>
              <div className="stat-sub">{stats.count} sessions in period</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Distance recorded</div>
              <div className="stat-value">{stats.totalDist > 0 ? stats.totalDist.toLocaleString('de-DE') : '—'}<span className="stat-unit">km</span></div>
              <div className="stat-sub">Odometer: {stats.maxOdo > 0 ? stats.maxOdo.toLocaleString('de-DE') + ' km' : '—'}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total charged</div>
              <div className="stat-value">{stats.totalKwh.toFixed(1)}<span className="stat-unit">kWh</span></div>
              <div style={{ marginTop: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 5 }}>
                  <span style={{ color: '#0369a1', fontWeight: 600 }}>AC {(stats.acKwh + stats.dcKwh) > 0 ? (stats.acKwh / (stats.acKwh + stats.dcKwh) * 100).toFixed(0) : 0}%</span>
                  <span style={{ color: '#b45309', fontWeight: 600 }}>DC {(stats.acKwh + stats.dcKwh) > 0 ? (stats.dcKwh / (stats.acKwh + stats.dcKwh) * 100).toFixed(0) : 0}%</span>
                </div>
                <div style={{ height: 5, borderRadius: 3, overflow: 'hidden', background: 'var(--bg)', display: 'flex' }}>
                  <div style={{ background: '#0ea5e9', height: '100%', width: `${(stats.acKwh + stats.dcKwh) > 0 ? stats.acKwh / (stats.acKwh + stats.dcKwh) * 100 : 0}%` }}></div>
                  <div style={{ background: '#f59e0b', height: '100%', flex: 1 }}></div>
                </div>
                <div style={{ display: 'flex', fontSize: 11, color: 'var(--text-muted)', justifyContent: 'space-between', marginTop: 4 }}>
                  <span>{stats.acKwh.toFixed(1)} kWh</span>
                  <span>{stats.dcKwh.toFixed(1)} kWh</span>
                </div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Total cost</div>
              <div className="stat-value">{stats.totalCost.toFixed(2)}<span className="stat-unit">€</span></div>
              <div className="stat-sub">avg {stats.avgPpkwh > 0 ? stats.avgPpkwh.toFixed(3) + ' €/kWh' : '—'}</div>
              {stats.costPer100km > 0 && <div style={{ marginTop: 6, fontSize: 12.5, color: 'var(--accent)', fontWeight: 600 }}>{stats.costPer100km.toFixed(2)} €/100km</div>}
            </div>
          </div>

          <div className="charts-grid">
            <div className="chart-card">
              <div className="chart-card-header"><div className="chart-card-title">Consumption <span className="chart-card-unit">kWh/100 km</span></div></div>
              <div className="chart-canvas-wrap">
                {chartData.labels.length > 0
                  ? <LineChart labels={chartData.labels} values={chartData.consData.map((v) => v ?? 0)} unit="kWh/100km" seasonal={true} />
                  : <div className="empty-state" style={{ padding: 30 }}><div style={{ fontSize: 12, color: 'var(--text-light)' }}>Not enough odometer data</div></div>}
              </div>
            </div>
            <div className="chart-card">
              <div className="chart-card-header"><div className="chart-card-title">kWh per CPO <span className="chart-card-unit">kWh</span></div></div>
              <div className="chart-canvas-wrap">
                {chartData.cpoLabels.length > 0
                  ? <BarChart labels={chartData.cpoLabels} values={chartData.cpoValues} unit="kWh" horizontal={true} colors={CPO_PALETTE.slice(0, chartData.cpoLabels.length)} />
                  : <div className="empty-state" style={{ padding: 30 }}><div style={{ fontSize: 12, color: 'var(--text-light)' }}>No data</div></div>}
              </div>
            </div>
            <div className="chart-card">
              <div className="chart-card-header"><div className="chart-card-title">Price per kWh <span className="chart-card-unit">€/kWh</span></div></div>
              <div className="chart-canvas-wrap">
                {chartData.labels.length > 0
                  ? <LineChart labels={chartData.labels} values={chartData.priceData.map((v) => v ?? 0)} unit="€/kWh" color="#f97316" yMin={0} />
                  : <div className="empty-state" style={{ padding: 30 }}><div style={{ fontSize: 12, color: 'var(--text-light)' }}>No price data</div></div>}
              </div>
            </div>
            <div className="chart-card">
              <div className="chart-card-header"><div className="chart-card-title">km driven <span className="chart-card-unit">per month</span></div></div>
              <div className="chart-canvas-wrap">
                {chartData.labels.length > 0
                  ? <BarChart labels={chartData.labels} values={chartData.kmData} unit="km" color="#22c55e" />
                  : <div className="empty-state" style={{ padding: 30 }}><div style={{ fontSize: 12, color: 'var(--text-light)' }}>No odometer data</div></div>}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
