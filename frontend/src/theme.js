import { useEffect, useState } from 'react';

// Theme preference: 'system' | 'light' | 'dark'. Applied as data-theme on <html>;
// index.html sets it before first paint so there is no light flash.
const KEY = 'evlogger-theme';
const MODES = ['system', 'light', 'dark'];
const media = window.matchMedia('(prefers-color-scheme: dark)');

export function getThemePref() {
  try {
    const v = localStorage.getItem(KEY);
    return MODES.includes(v) ? v : 'system';
  } catch {
    return 'system';
  }
}

export function resolveTheme(pref = getThemePref()) {
  return pref === 'system' ? (media.matches ? 'dark' : 'light') : pref;
}

function apply(pref) {
  document.documentElement.dataset.theme = resolveTheme(pref);
  window.dispatchEvent(new Event('evlogger-theme'));
}

export function setThemePref(pref) {
  try {
    localStorage.setItem(KEY, pref);
  } catch {
    // private mode etc.: still switch for this page view
  }
  apply(pref);
}

export function nextThemePref(pref) {
  return MODES[(MODES.indexOf(pref) + 1) % MODES.length];
}

media.addEventListener('change', () => {
  if (getThemePref() === 'system') apply('system');
});

// Re-renders on theme changes; returns { pref, theme } with theme = resolved 'light' | 'dark'.
export function useTheme() {
  const [state, setState] = useState(() => ({ pref: getThemePref(), theme: resolveTheme() }));
  useEffect(() => {
    const on = () => setState({ pref: getThemePref(), theme: resolveTheme() });
    window.addEventListener('evlogger-theme', on);
    return () => window.removeEventListener('evlogger-theme', on);
  }, []);
  return state;
}

export function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
