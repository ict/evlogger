import { useEffect, useMemo, useRef } from 'react';
import { Chart, registerables } from 'chart.js';
import { ensureSeasonalPluginRegistered } from './seasonalPlugin.js';
import { ensureValueLabelsPluginRegistered } from './valueLabelsPlugin.js';

let baseRegistered = false;
function ensureBase() {
  if (baseRegistered) return;
  Chart.register(...registerables);
  ensureSeasonalPluginRegistered();
  ensureValueLabelsPluginRegistered();
  baseRegistered = true;
}

export default function ChartCanvas({ type, data, options }) {
  ensureBase();
  const ref = useRef(null);
  const inst = useRef(null);
  const key = useMemo(() => JSON.stringify({ type, data, options }), [type, data, options]);

  useEffect(() => {
    if (!ref.current) return;
    if (inst.current) { inst.current.destroy(); inst.current = null; }
    inst.current = new Chart(ref.current, { type, data, options });
    return () => { if (inst.current) { inst.current.destroy(); inst.current = null; } };
  }, [key]);

  return <canvas ref={ref}></canvas>;
}
