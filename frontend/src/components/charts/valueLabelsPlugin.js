import { Chart } from 'chart.js';

const CHART_FONT = 'Plus Jakarta Sans';

function fmt(v, decimals) {
  // Match the stat cards: whole numbers get thousands separators, decimals use a dot.
  return decimals === 0 ? Math.round(Number(v)).toLocaleString('de-DE') : Number(v).toFixed(decimals);
}

let registered = false;
export function ensureValueLabelsPluginRegistered() {
  if (registered) return;
  Chart.register({
    id: 'valueLabels',
    afterDatasetsDraw(chart) {
      const cfg = chart.options.plugins?.valueLabels;
      if (!cfg?.enabled) return;
      const { ctx, chartArea } = chart;
      const horizontal = chart.options.indexAxis === 'y';
      const decimals = cfg.decimals ?? 0;
      const unit = cfg.unit ? ' ' + cfg.unit : '';

      ctx.save();
      ctx.font = `600 11px "${CHART_FONT}", system-ui, sans-serif`;
      ctx.textAlign = horizontal ? 'left' : 'center';
      ctx.textBaseline = horizontal ? 'middle' : 'bottom';

      const draw = (raw, px, py) => {
        const text = fmt(raw, decimals) + unit;
        const w = ctx.measureText(text).width;
        let x = px, y = py;
        let inside = false;

        if (horizontal) {
          if (x + 6 + w > chartArea.right) { x = x - 6 - w; inside = true; ctx.textAlign = 'left'; }
          else { x = x + 6; ctx.textAlign = 'left'; }
        } else {
          if (y - 6 < chartArea.top) { y = y + 16; inside = true; }
          else { y = y - 6; }
        }

        ctx.fillStyle = inside ? '#ffffff' : (cfg.color || '#475569');
        ctx.fillText(text, x, y);
      };

      if (cfg.stacked && !horizontal) {
        // One label per stack: the sum of visible segments, placed above the topmost one.
        const n = chart.data.labels.length;
        for (let i = 0; i < n; i++) {
          let total = 0, top = null, x = null;
          chart.data.datasets.forEach((ds, di) => {
            const meta = chart.getDatasetMeta(di);
            const v = ds.data[i];
            if (meta.hidden || v == null || !meta.data[i]) return;
            total += Number(v);
            if (v > 0 && (top == null || meta.data[i].y < top)) { top = meta.data[i].y; x = meta.data[i].x; }
          });
          if (top != null && total > 0) draw(total, x, top);
        }
      } else {
        chart.data.datasets.forEach((ds, di) => {
          const meta = chart.getDatasetMeta(di);
          if (meta.hidden) return;
          meta.data.forEach((el, i) => {
            const raw = ds.data[i];
            if (raw == null) return;
            draw(raw, el.x, el.y);
          });
        });
      }
      ctx.restore();
    },
  });
  registered = true;
}
