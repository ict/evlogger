import ChartCanvas from './ChartCanvas.jsx';

const ACCENT = 'oklch(0.52 0.19 252)';
const ACCENT_FILL = 'rgba(99,102,241,0.1)';
const CHART_FONT = 'Plus Jakarta Sans';

const BASE_OPTS = {
  responsive: true, maintainAspectRatio: false,
  plugins: { legend: { display: false }, tooltip: { bodyFont: { family: CHART_FONT }, titleFont: { family: CHART_FONT } } },
  scales: {
    x: { grid: { display: false }, ticks: { font: { family: CHART_FONT, size: 11 }, color: '#94a3b8' } },
    y: { grid: { color: '#f1f5f9', drawBorder: false }, ticks: { font: { family: CHART_FONT, size: 11 }, color: '#94a3b8' } },
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
