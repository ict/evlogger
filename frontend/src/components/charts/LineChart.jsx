import ChartCanvas from './ChartCanvas.jsx';

const ACCENT = 'var(--accent)';
const ACCENT_FILL = 'var(--chart-fill)';
const CHART_FONT = 'Plus Jakarta Sans';

const BASE_OPTS = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { bodyFont: { family: CHART_FONT }, titleFont: { family: CHART_FONT } } },
  scales: {
    x: { grid: { display: false }, ticks: { font: { family: CHART_FONT, size: 11 }, color: 'var(--chart-tick)' } },
    y: { grid: { color: 'var(--chart-grid)', drawBorder: false }, ticks: { font: { family: CHART_FONT, size: 11 }, color: 'var(--chart-tick)' } },
  },
};

export default function LineChart({ labels, values, unit, color, seasonal, yMin }) {
  const c = color || ACCENT;
  const data = {
    labels,
    datasets: [{
      data: values, borderColor: c, backgroundColor: ACCENT_FILL,
      borderWidth: 2, fill: true, tension: 0.35,
      pointRadius: values.length < 20 ? 3 : 0, pointHoverRadius: 5,
      pointBackgroundColor: c,
    }],
  };
  const options = {
    ...BASE_OPTS,
    plugins: {
      ...BASE_OPTS.plugins,
      seasonalBg: seasonal ? { labels } : {},
      tooltip: { ...BASE_OPTS.plugins.tooltip, callbacks: { label: (ctx) => `${ctx.parsed.y.toFixed(2)} ${unit || ''}` } },
    },
    scales: {
      ...BASE_OPTS.scales,
      y: { ...BASE_OPTS.scales.y, ...(yMin != null ? { min: yMin, beginAtZero: yMin === 0 } : {}) },
    },
  };
  return <ChartCanvas type="line" data={data} options={options} />;
}
