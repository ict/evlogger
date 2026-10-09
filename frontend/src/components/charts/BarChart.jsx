import ChartCanvas from './ChartCanvas.jsx';

const ACCENT = '#2563eb';
const CHART_FONT = 'Plus Jakarta Sans';

const BASE_OPTS = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { bodyFont: { family: CHART_FONT }, titleFont: { family: CHART_FONT } } },
  scales: {
    x: { grid: { display: false }, ticks: { font: { family: CHART_FONT, size: 11 }, color: '#94a3b8' } },
    y: { grid: { color: '#f1f5f9', drawBorder: false }, ticks: { font: { family: CHART_FONT, size: 11 }, color: '#94a3b8' } },
  },
};

// Single series: `values` (+ `color`/`colors`). Multi series: `datasets` = [{ label, values, color }];
// with `stacked`, bars stack and value labels show the stack total.
export default function BarChart({ labels, values, datasets, stacked, unit, color, colors, horizontal, showValues, valueDecimals = 0, valueUnit }) {
  const multi = !!datasets;
  const base = color || ACCENT;
  // Alpha suffix only works on hex; other notations (oklch(), rgb()) would become invalid.
  const bgColors = colors ? colors : Array((values || []).length).fill(base.startsWith('#') ? base + 'cc' : base);
  const data = {
    labels,
    datasets: multi
      ? datasets.map((d) => ({ label: d.label, data: d.values, backgroundColor: d.color, borderRadius: stacked ? 0 : 4, borderSkipped: false }))
      : [{ data: values, backgroundColor: bgColors, borderRadius: 4, borderSkipped: false }],
  };
  const axis = horizontal ? 'y' : 'x';
  let scales = showValues && !horizontal
    ? { ...BASE_OPTS.scales, y: { ...BASE_OPTS.scales.y, grace: '10%' } }
    : BASE_OPTS.scales;
  if (stacked) scales = { x: { ...scales.x, stacked: true }, y: { ...scales.y, stacked: true } };
  const tooltip = multi
    ? {
        ...BASE_OPTS.plugins.tooltip, mode: 'index', intersect: false,
        callbacks: {
          label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)} ${unit || ''}`,
          footer: stacked ? (items) => `Total: ${items.reduce((s, i) => s + i.parsed.y, 0).toFixed(2)} ${unit || ''}` : undefined,
        },
      }
    : { ...BASE_OPTS.plugins.tooltip, callbacks: { label: (ctx) => `${(horizontal ? ctx.parsed.x : ctx.parsed.y).toFixed(1)} ${unit || ''}` } };
  const options = {
    ...BASE_OPTS, indexAxis: axis,
    scales,
    layout: showValues ? { padding: horizontal ? { right: 44 } : { top: 18 } } : undefined,
    plugins: {
      ...BASE_OPTS.plugins,
      legend: multi
        ? { display: true, position: 'bottom', labels: { usePointStyle: true, boxWidth: 8, boxHeight: 8, padding: 12, color: '#64748b', font: { family: CHART_FONT, size: 11 } } }
        : BASE_OPTS.plugins.legend,
      tooltip,
      valueLabels: { enabled: !!showValues, decimals: valueDecimals, unit: valueUnit, stacked: !!stacked },
    },
  };
  return <ChartCanvas type="bar" data={data} options={options} />;
}
