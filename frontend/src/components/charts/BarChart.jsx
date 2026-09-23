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

export default function BarChart({ labels, values, unit, color, colors, horizontal, showValues, valueDecimals = 0, valueUnit }) {
  const base = color || ACCENT;
  // Alpha suffix only works on hex; other notations (oklch(), rgb()) would become invalid.
  const bgColors = colors ? colors : Array(values.length).fill(base.startsWith('#') ? base + 'cc' : base);
  const data = {
    labels,
    datasets: [{ data: values, backgroundColor: bgColors, borderRadius: 4, borderSkipped: false }],
  };
  const axis = horizontal ? 'y' : 'x';
  const options = {
    ...BASE_OPTS, indexAxis: axis,
    scales: showValues && !horizontal
      ? { ...BASE_OPTS.scales, y: { ...BASE_OPTS.scales.y, grace: '10%' } }
      : BASE_OPTS.scales,
    layout: showValues ? { padding: horizontal ? { right: 44 } : { top: 18 } } : undefined,
    plugins: {
      ...BASE_OPTS.plugins,
      tooltip: { ...BASE_OPTS.plugins.tooltip, callbacks: { label: (ctx) => `${(horizontal ? ctx.parsed.x : ctx.parsed.y).toFixed(1)} ${unit || ''}` } },
      valueLabels: { enabled: !!showValues, decimals: valueDecimals, unit: valueUnit },
    },
  };
  return <ChartCanvas type="bar" data={data} options={options} />;
}
