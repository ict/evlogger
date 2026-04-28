export default function TimeframeBar({ value, onChange, fromDate, toDate, onFrom, onTo }) {
  const chips = ['1M', '3M', '6M', '1Y', 'All', 'Custom'];
  return (
    <div className="timeframe-bar">
      {chips.map((c) => (
        <button key={c} className={`chip${value === c ? ' active' : ''}`} onClick={() => onChange(c)}>{c}</button>
      ))}
      {value === 'Custom' && (
        <div className="custom-range">
          <input type="date" className="input-sm" value={fromDate} onChange={(e) => onFrom(e.target.value)} />
          <span style={{ color: 'var(--text-muted)' }}>–</span>
          <input type="date" className="input-sm" value={toDate} onChange={(e) => onTo(e.target.value)} />
        </div>
      )}
    </div>
  );
}
