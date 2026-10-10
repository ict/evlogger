import { Chart } from 'chart.js';

const COLORS = {
  winter: 'rgba(147,197,253,0.22)',
  spring: 'rgba(134,239,172,0.2)',
  summer: 'rgba(253,224,71,0.18)',
  fall: 'rgba(251,146,60,0.18)',
};
// Softer tints on dark surfaces, where the light-mode alphas read as muddy.
const COLORS_DARK = {
  winter: 'rgba(147,197,253,0.07)',
  spring: 'rgba(134,239,172,0.06)',
  summer: 'rgba(253,224,71,0.05)',
  fall: 'rgba(251,146,60,0.06)',
};
const season = (mo) => (mo === 12 || mo <= 2 ? 'winter' : mo <= 5 ? 'spring' : mo <= 8 ? 'summer' : 'fall');

let registered = false;
export function ensureSeasonalPluginRegistered() {
  if (registered) return;
  Chart.register({
    id: 'seasonalBg',
    beforeDraw(chart) {
      const labels = chart.options.plugins?.seasonalBg?.labels;
      if (!labels?.length) return;
      const { ctx, chartArea, scales: { x } } = chart;
      if (!x || !chartArea) return;
      const { left, right, top, bottom } = chartArea;
      const colors = document.documentElement.dataset.theme === 'dark' ? COLORS_DARK : COLORS;
      ctx.save();
      labels.forEach((lbl, i) => {
        const mo = parseInt(lbl.split('/')[0]);
        const x0 = i === 0 ? left : x.getPixelForValue(i - 0.5);
        const x1 = i === labels.length - 1 ? right : x.getPixelForValue(i + 0.5);
        ctx.fillStyle = colors[season(mo)];
        ctx.fillRect(Math.max(left, x0), top, Math.min(right, x1) - Math.max(left, x0), bottom - top);
      });
      ctx.restore();
    },
  });
  registered = true;
}
