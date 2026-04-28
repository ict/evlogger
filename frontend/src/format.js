export function fmtKwh(v) { return (v / 100).toFixed(1); }
export function fmtEur(v) { return (v / 100).toFixed(2); }
export function fmtDate(s) {
  return new Date(s).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: '2-digit' });
}
export function fmtDateTimeInput(s) {
  const d = new Date(s);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
export function getTimeframeRange(tf, fromDate, toDate) {
  const now = new Date();
  if (tf === 'Custom') return {
    from_date: fromDate ? new Date(fromDate).toISOString() : undefined,
    to_date: toDate ? new Date(toDate + 'T23:59:59').toISOString() : undefined,
  };
  if (tf === 'All') return {};
  const months = { '1M': 1, '3M': 3, '6M': 6, '1Y': 12 }[tf];
  const from = new Date(now);
  from.setMonth(from.getMonth() - months);
  return { from_date: from.toISOString(), to_date: now.toISOString() };
}
