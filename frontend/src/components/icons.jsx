// Icon paths adapted from Lucide (https://lucide.dev), ISC licensed.
const mk = (children) => function Icon({ size = 18, ...props }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>
      {children}
    </svg>
  );
};

export const InsuranceIcon = mk(<><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" /><path d="m9 12 2 2 4-4" /></>);
export const TaxIcon = mk(<><line x1="3" x2="21" y1="22" y2="22" /><line x1="6" x2="6" y1="18" y2="11" /><line x1="10" x2="10" y1="18" y2="11" /><line x1="14" x2="14" y1="18" y2="11" /><line x1="18" x2="18" y1="18" y2="11" /><polygon points="12 2 20 7 4 7" /></>);
// Custom wheel: tyre, rim, hub and spokes
export const TiresIcon = mk(<><circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="1.5" /><path d="M12 6v4.5M12 13.5V18M6 12h4.5M13.5 12H18" /></>);
export const TollsParkingIcon = mk(<><rect width="18" height="18" x="3" y="3" rx="2" /><path d="M9 17V7h4a3 3 0 0 1 0 6H9" /></>);
export const CleaningIcon = mk(<><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" /><path d="M20 3v4" /><path d="M22 5h-4" /><path d="M4 17v2" /><path d="M5 18H3" /></>);
export const MaintenanceIcon = mk(<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.106-3.105c.32-.322.863-.22.983.218a6 6 0 0 1-8.259 7.057l-7.91 7.91a1 1 0 0 1-2.999-3l7.91-7.91a6.001 6.001 0 0 1 7.057-8.259c.438.12.54.662.219.984z" />);
export const AccessoriesIcon = mk(<><path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z" /><path d="M12 22V12" /><polyline points="3.29 7 12 12 20.71 7" /><path d="m7.5 4.27 9 5.15" /></>);
export const OtherIcon = mk(<><path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z" /><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8" /><path d="M12 17.5v-11" /></>);

export const EXPENSE_CATEGORIES = [
  { key: 'insurance', label: 'Insurance', Icon: InsuranceIcon, color: '#0369a1' },
  { key: 'tax', label: 'Tax', Icon: TaxIcon, color: '#64748b' },
  { key: 'tires', label: 'Tires', Icon: TiresIcon, color: '#374151' },
  { key: 'tolls_parking', label: 'Tolls & Parking', Icon: TollsParkingIcon, color: '#6366f1' },
  { key: 'cleaning', label: 'Cleaning', Icon: CleaningIcon, color: '#06b6d4' },
  { key: 'maintenance', label: 'Maintenance', Icon: MaintenanceIcon, color: '#f97316' },
  { key: 'accessories', label: 'Accessories', Icon: AccessoriesIcon, color: '#a855f7' },
  { key: 'other', label: 'Other', Icon: OtherIcon, color: '#9ca3af' },
];

export const EXPENSE_CATEGORY_MAP = Object.fromEntries(EXPENSE_CATEGORIES.map((c) => [c.key, c]));

export function CategoryIcon({ category, size = 18, ...props }) {
  const { Icon } = EXPENSE_CATEGORY_MAP[category] || EXPENSE_CATEGORY_MAP.other;
  return <Icon size={size} {...props} />;
}

export function CategoryChip({ category, size = 28 }) {
  const c = EXPENSE_CATEGORY_MAP[category] || EXPENSE_CATEGORY_MAP.other;
  return (
    <span title={c.label} style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0, width: size, height: size, borderRadius: 8, background: c.color, color: '#fff' }}>
      <c.Icon size={Math.round(size * 0.58)} />
    </span>
  );
}
