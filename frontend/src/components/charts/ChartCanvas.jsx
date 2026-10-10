import { useEffect, useMemo, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import { ensureSeasonalPluginRegistered } from './seasonalPlugin.js';
import { ensureValueLabelsPluginRegistered } from './valueLabelsPlugin.js';
import { cssVar, useTheme } from '../../theme.js';

let baseRegistered = false;
function ensureBase() {
  if (baseRegistered) return;
  Chart.register(...registerables);
  ensureSeasonalPluginRegistered();
  ensureValueLabelsPluginRegistered();
  baseRegistered = true;
}

// Canvas can't read CSS variables, so swap 'var(--x)' strings for the current theme's values.
function resolveVars(v) {
  if (typeof v === 'string') return v.startsWith('var(--') ? cssVar(v.slice(4, -1)) || v : v;
  if (Array.isArray(v)) return v.map(resolveVars);
  if (v && typeof v === 'object' && Object.getPrototypeOf(v) === Object.prototype) {
    return Object.fromEntries(Object.entries(v).map(([k, x]) => [k, resolveVars(x)]));
  }
  return v;
}

export default function ChartCanvas({ type, data, options }) {
  ensureBase();
  const ref = useRef(null);
  const inst = useRef(null);
  const { theme } = useTheme();
  const key = useMemo(() => JSON.stringify({ type, data, options }), [type, data, options]);

  useEffect(() => {
    if (!ref.current) return;
    if (inst.current) { inst.current.destroy(); inst.current = null; }
    inst.current = new Chart(ref.current, { type, data: resolveVars(data), options: resolveVars(options) });
    return () => { if (inst.current) { inst.current.destroy(); inst.current = null; } };
  }, [key, theme]);

  return <canvas ref={ref}></canvas>;
}
