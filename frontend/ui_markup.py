"""HTML/CSS markup helpers for the Streamlit frontend."""

import html


def car_hero_html(car: dict, avg_consumption: float | None = None, price_per_100_km: float | None = None) -> str:
    """Render the car-details hero panel (painted silhouette + instruments) as HTML."""
    color = (car.get('Color') or 'gray').strip() or 'gray'
    make = car.get('Make') or ''
    model = car.get('Model') or ''
    name = car.get('Name') or ''
    title = ' '.join(p for p in (make, model) if p) or name or '—'
    odo = int(car.get('Odometer') or 0)
    odo_digits = f'{odo:06d}' if odo < 1_000_000 else str(odo)
    battery = int(car.get('Battery Capacity') or 0)

    digit_cells = ''.join(f'<span class="cl-odo-digit">{d}</span>' for d in odo_digits)

    plate_raw = (name or 'EV').upper()
    plate_text = html.escape(plate_raw[:12] if len(plate_raw) > 12 else plate_raw)
    title_safe = html.escape(title)
    name_safe = html.escape(name)
    color_safe = html.escape(color, quote=True)
    consumption_text = f'{avg_consumption:.1f}' if avg_consumption is not None else '—'
    price_100_text = f'{price_per_100_km:.2f}' if price_per_100_km is not None else '—'

    return f"""
<div class="cl-hero">
  <div class="cl-hero-left">
    <div class="cl-title-row">
      <div class="cl-title">{title_safe}</div>
    </div>
    <div class="cl-hero-stats">
      <div class="cl-card cl-odo-card">
        <div class="cl-card-label">ODOMETER</div>
        <div class="cl-odo">
          <div class="cl-odo-reels">{digit_cells}</div>
          <div class="cl-odo-unit">km</div>
        </div>
      </div>
      <div class="cl-card cl-batt-card">
        <div class="cl-card-label">BATTERY</div>
        <div class="cl-batt">
          <svg viewBox="0 0 160 60" xmlns="http://www.w3.org/2000/svg" class="cl-batt-svg">
            <rect x="2" y="6" width="140" height="48" rx="6" ry="6"
                  fill="none" stroke="currentColor" stroke-width="3"/>
            <rect x="144" y="20" width="10" height="20" rx="2" ry="2" fill="currentColor"/>
            <rect x="8" y="12" width="128" height="36" rx="3" ry="3" fill="#bdeccf"/>
            <rect x="8" y="12" width="128" height="12" rx="3" ry="3" fill="#ffffff" opacity="0.18"/>
          </svg>
          <div class="cl-batt-value">{battery}<span class="cl-batt-unit">kWh</span></div>
        </div>
      </div>
      <div class="cl-card cl-stat-card">
        <div class="cl-card-label">AVG CONSUMPTION</div>
        <div class="cl-stat-value cl-consumption-value">
          <span class="cl-consumption-glyph">⚡</span>{consumption_text}<span class="cl-stat-unit">kWh / 100 km</span>
        </div>
      </div>
      <div class="cl-card cl-stat-card">
        <div class="cl-card-label">PRICE / 100 KM</div>
        <div class="cl-stat-value cl-price-value">
          <span class="cl-currency-glyph">$</span>{price_100_text}<span class="cl-stat-unit">EUR / 100 km</span>
        </div>
      </div>
    </div>
  </div>
  <div class="cl-hero-right">
    <svg class="cl-car" viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" aria-label="{name_safe}">
      <defs>
        <radialGradient id="cl-ground" cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stop-color="#8d9ab0" stop-opacity="0.30"/>
          <stop offset="100%" stop-color="#000" stop-opacity="0"/>
        </radialGradient>
        <linearGradient id="cl-window" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#f7f3ff"/>
          <stop offset="100%" stop-color="#dfebff"/>
        </linearGradient>
        <linearGradient id="cl-wheel" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#7f879a"/>
          <stop offset="100%" stop-color="#656d82"/>
        </linearGradient>
      </defs>
      <ellipse cx="320" cy="222" rx="250" ry="7" fill="url(#cl-ground)"/>
      <g>
        <path d="M 60,196
                 L 60,172
                 Q 64,150 86,141
                 L 198,112
                 Q 252,44 356,44
                 Q 465,44 540,123
                 Q 594,132 612,163
                 Q 620,177 620,196
                 Z" fill="{color_safe}" opacity="0.72"/>
        <path d="M 60,196
                 L 60,172
                 Q 64,150 86,141
                 L 198,112
                 Q 252,44 356,44
                 Q 465,44 540,123
                 Q 594,132 612,163
                 Q 620,177 620,196
                 Z" fill="#ffffff" opacity="0.22"/>
        <path d="M 215,110
                 Q 265,60 350,60
                 Q 433,60 495,113
                 Q 434,122 342,122
                 Q 260,122 215,110
                 Z" fill="url(#cl-window)" opacity="0.95"/>
        <ellipse cx="92" cy="158" rx="16" ry="11" fill="#fff9cf"/>
        <circle cx="174" cy="196" r="45" fill="url(#cl-wheel)"/>
        <circle cx="500" cy="196" r="45" fill="url(#cl-wheel)"/>
        <circle cx="174" cy="196" r="24" fill="#f8f9ff"/>
        <circle cx="500" cy="196" r="24" fill="#f8f9ff"/>
        <circle cx="174" cy="196" r="8" fill="#ccd3e8"/>
        <circle cx="500" cy="196" r="8" fill="#ccd3e8"/>
      </g>
    </svg>
    <div class="cl-plate" title="{name_safe}">
      <div class="cl-plate-eu">
        <div class="cl-plate-stars">★</div>
        <div class="cl-plate-country">EU</div>
      </div>
      <div class="cl-plate-text">{plate_text}</div>
    </div>
  </div>
</div>
<style>
.cl-hero {{
  display: flex; gap: 12px; align-items: center;
  padding: 10px 12px; margin-bottom: 8px;
  border-radius: 12px;
  background: linear-gradient(165deg, rgba(255, 233, 240, 0.72), rgba(226, 241, 255, 0.55));
  border: 1px solid rgba(192, 203, 223, 0.75);
}}
.cl-hero-left {{ flex: 1.15 1 0; min-width: 0; display: flex; flex-direction: column; gap: 6px; }}
.cl-hero-stats {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }}
.cl-hero-right {{
  flex: 0.95 1 0; min-width: 0;
  display: flex; flex-direction: column; justify-content: center; align-items: center;
  gap: 2px;
}}
.cl-title-row {{ display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; }}
.cl-title {{ font-size: 1.18rem; font-weight: 700; letter-spacing: 0.35px; line-height: 1.1; }}
.cl-car {{ width: 100%; height: auto; max-height: 122px; display: block; }}
.cl-plate {{
  align-self: center; display: inline-flex; align-items: stretch;
  margin-top: 0;
  background: #f7f7f5; color: #111;
  border: 2px solid #111; border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.25), inset 0 -2px 0 rgba(0,0,0,0.08);
  overflow: hidden;
  font-family: "Helvetica Neue", Arial, ui-sans-serif, sans-serif;
  transform: scale(0.72);
  transform-origin: center top;
}}
.cl-plate-eu {{
  background: #003399; color: #ffcc00;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 4px 8px; min-width: 28px;
  border-right: 2px solid #111;
}}
.cl-plate-stars {{ font-size: 0.7rem; line-height: 1; letter-spacing: 1px; }}
.cl-plate-country {{ font-size: 0.75rem; font-weight: 700; letter-spacing: 1px; margin-top: 2px; }}
.cl-plate-text {{
  padding: 6px 18px;
  font-size: 1.8rem; font-weight: 800; letter-spacing: 4px;
  font-family: "Courier New", ui-monospace, Menlo, monospace;
  line-height: 1;
}}
.cl-card {{
  padding: 8px 10px; border-radius: 10px;
  background: rgba(255, 255, 255, 0.44);
  border: 1px solid rgba(188, 198, 220, 0.55);
}}
.cl-card-label {{
  font-size: 0.62rem; letter-spacing: 1.6px; opacity: 0.72;
  margin-bottom: 4px; font-weight: 700;
}}
.cl-odo {{ display: flex; align-items: center; gap: 10px; }}
.cl-odo-reels {{ display: inline-flex; gap: 3px; }}
.cl-odo-digit {{
  display: inline-block; width: 1.25em; text-align: center;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 1.05rem; font-weight: 700; color: #f5f6ff;
  background: #6b7388; border-radius: 3px;
  padding: 1px 0;
  box-shadow: inset 0 0 6px rgba(53, 59, 72, 0.68), 0 1px 0 rgba(255,255,255,0.35);
  position: relative;
}}
.cl-odo-digit::after {{
  content: ""; position: absolute; left: 0; right: 0; top: 50%;
  height: 1px; background: rgba(255,255,255,0.18);
}}
.cl-odo-unit {{ font-size: 0.9rem; opacity: 0.7; letter-spacing: 1px; }}
.cl-batt {{ position: relative; display: flex; align-items: center; }}
.cl-batt-svg {{ width: 118px; height: 44px; color: rgba(127,127,127,0.7); }}
.cl-batt-value {{
  position: absolute; left: 0; width: 106px; top: 50%;
  transform: translateY(-50%); text-align: center;
  font-weight: 700; font-size: 0.92rem; color: #35524a;
  text-shadow: 0 1px 2px rgba(255,255,255,0.5);
}}
.cl-batt-unit {{ font-size: 0.75rem; font-weight: 600; margin-left: 3px; opacity: 0.9; }}
.cl-stat-value {{
  display: flex; align-items: baseline; gap: 6px;
  font-weight: 700; font-size: 1.02rem; line-height: 1.1;
  color: #2f425d;
}}
.cl-stat-unit {{ font-size: 0.72rem; opacity: 0.78; font-weight: 600; }}
.cl-consumption-value {{ color: #2b5a51; }}
.cl-consumption-glyph {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.2rem; height: 1.2rem; border-radius: 999px;
  background: linear-gradient(135deg, #7dd7ce, #4db9af);
  color: #ffffff; font-size: 0.78rem; font-weight: 800;
  box-shadow: 0 1px 2px rgba(33, 102, 95, 0.25);
}}
.cl-price-value {{ color: #34507a; }}
.cl-currency-glyph {{
  display: inline-flex; align-items: center; justify-content: center;
  width: 1.2rem; height: 1.2rem; border-radius: 999px;
  background: linear-gradient(135deg, #80c8a5, #4ea58b);
  color: #ffffff; font-size: 0.78rem; font-weight: 800;
  box-shadow: 0 1px 2px rgba(35, 78, 67, 0.25);
}}
@media (max-width: 980px) {{
  .cl-hero-left {{ flex: 1 1 0; }}
  .cl-hero-right {{ flex: 0.9 1 0; }}
}}
@media (max-width: 640px) {{
  .cl-hero {{ flex-direction: column; }}
  .cl-hero-left {{ width: 100%; }}
  .cl-hero-right {{ width: 100%; }}
  .cl-car {{ max-height: 112px; }}
}}
</style>
"""


def compact_layout_css() -> str:
    """Reduce Streamlit chrome spacing so content starts higher on the page."""
    return """
<style>
[data-testid="stHeader"] {
  height: 0;
  background: transparent;
}
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
#MainMenu,
footer {
  display: none;
}
[data-testid="stAppViewContainer"] > .main .block-container,
[data-testid="stMainBlockContainer"] {
  padding-top: 0.35rem !important;
  padding-bottom: 0.9rem !important;
}
[data-testid="stSidebarHeader"] {
  display: none;
}
[data-testid="stSidebarUserContent"],
[data-testid="stSidebarContent"] {
  padding-top: 0.45rem;
}
</style>
"""
