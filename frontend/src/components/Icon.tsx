import type { ReactNode } from 'react';

/** Juego de íconos propio: trazo 1.75, esquinas redondeadas, retícula de 24 px. */
const PATHS = {
  pothole: <><path d="M2.5 18.5 6 8.5h12l3.5 10Z" /><path d="M8 15.2c.5-1.5 2.1-2.4 4-2.4s3.5.9 4 2.4c-.4 1.3-2 2-4 2s-3.6-.7-4-2Z" /><path d="m16.6 13.4 1.9-1.3M7.4 13.5l-1.7-.9M12 12.8l.4-1.7" /></>,
  manhole: <><ellipse cx="12" cy="16.5" rx="8.5" ry="3.8" /><ellipse cx="12" cy="16.5" rx="5.2" ry="2.1" /><ellipse cx="15" cy="6.8" rx="4.6" ry="2.1" transform="rotate(-16 15 6.8)" /><path d="M11.6 7.6l6.6-1.9" /></>,
  water: <><path d="M3 15c1.5 0 1.5-1 3-1s1.5 1 3 1 1.5-1 3-1 1.5 1 3 1 1.5-1 3-1 1.5 1 3 1" /><path d="M3 19c1.5 0 1.5-1 3-1s1.5 1 3 1 1.5-1 3-1 1.5 1 3 1 1.5-1 3-1 1.5 1 3 1" /><path d="M12 3.5s-3 3.4-3 5.5a3 3 0 0 0 6 0c0-2.1-3-5.5-3-5.5Z" /></>,
  road: <><path d="M8 3 5 21M16 3l3 18" /><path d="M12 4v2.5M12 10.5v3M12 17.5V20" /></>,
  pin: <><path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11Z" /><circle cx="12" cy="10" r="2.4" /></>,
  locate: <><circle cx="12" cy="12" r="7" /><circle cx="12" cy="12" r="2.5" /><path d="M12 2.5V5M12 19v2.5M2.5 12H5M19 12h2.5" /></>,
  search: <><circle cx="11" cy="11" r="6.5" /><path d="m16 16 4.5 4.5" /></>,
  arrowRight: <><path d="M5 12h14" /><path d="m13 6 6 6-6 6" /></>,
  arrowLeft: <><path d="M19 12H5" /><path d="m11 6-6 6 6 6" /></>,
  chevronLeft: <path d="m15 6-6 6 6 6" />,
  chevronRight: <path d="m9 6 6 6-6 6" />,
  clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7.5V12l3 2" /></>,
  calendar: <><rect x="3.5" y="5" width="17" height="15.5" rx="2.5" /><path d="M3.5 10h17M8 3v4M16 3v4" /></>,
  alert: <><path d="M10.3 4.2 2.9 17.5A2 2 0 0 0 4.6 20.5h14.8a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0Z" /><path d="M12 9.5v4M12 17v.01" /></>,
  info: <><circle cx="12" cy="12" r="8.5" /><path d="M12 11v5M12 8v.01" /></>,
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  checkCircle: <><circle cx="12" cy="12" r="8.5" /><path d="m8.5 12.2 2.4 2.4 4.6-4.9" /></>,
  xCircle: <><circle cx="12" cy="12" r="8.5" /><path d="m9.2 9.2 5.6 5.6M14.8 9.2l-5.6 5.6" /></>,
  ban: <><circle cx="12" cy="12" r="8.5" /><path d="m6 6 12 12" /></>,
  wrench: <path d="M14.5 6.5a4 4 0 0 0 5 5L13 18a2.1 2.1 0 0 1-3-3l6.5-6.5a4 4 0 0 0-2-2ZM14.5 6.5 17 4a4 4 0 0 1 3 3l-2.5 2.5" />,
  inbox: <><path d="M3.5 13.5 6 5.5h12l2.5 8" /><path d="M3.5 13.5V18a1.5 1.5 0 0 0 1.5 1.5h14a1.5 1.5 0 0 0 1.5-1.5v-4.5h-5a3.5 3.5 0 0 1-7 0Z" /></>,
  history: <><path d="M4 12a8 8 0 1 0 2.4-5.7L4 8.5" /><path d="M4 4v4.5h4.5M12 8v4l2.8 1.8" /></>,
  user: <><circle cx="12" cy="8.5" r="3.5" /><path d="M5 20c.8-3.5 3.6-5.5 7-5.5s6.2 2 7 5.5" /></>,
  logout: <><path d="M14 4.5H6.5a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2H14" /><path d="M10 12h10M16.5 8.5 20 12l-3.5 3.5" /></>,
  plus: <path d="M12 5v14M5 12h14" />,
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  close: <path d="m6 6 12 12M18 6 6 18" />,
  shield: <><path d="M12 3.5 5 6v5.5c0 4.3 3 7.6 7 9 4-1.4 7-4.7 7-9V6Z" /><path d="m9 12 2.2 2.2L15.5 10" /></>,
  layers: <><path d="m12 4 8.5 4.5L12 13 3.5 8.5Z" /><path d="m3.5 12.5 8.5 4.5 8.5-4.5" /><path d="m3.5 16.5 8.5 4.5 8.5-4.5" /></>,
  chart: <><path d="M4 20h16" /><path d="M7 16v-5M12 16V7M17 16v-8" /></>,
  rain: <><path d="M7 15.5a4.5 4.5 0 1 1 1-8.9 5.5 5.5 0 0 1 10.4 2A3.5 3.5 0 0 1 17.5 15.5Z" /><path d="m8.5 18.5-1 2M12.5 18.5l-1 2M16.5 18.5l-1 2" /></>,
  thumbsUp: <><path d="M7.5 10.5v9H4.5v-9Z" /><path d="M7.5 10.5 11 4a2 2 0 0 1 3 1.8L13.5 9.5H19a1.6 1.6 0 0 1 1.6 1.9l-1.4 6.6a2 2 0 0 1-2 1.5H7.5" /></>,
  moon: <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" />,
  sun: <><circle cx="12" cy="12" r="3.8" /><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4" /></>,
  edit: <><path d="M4.5 19.5h4l10-10a2.8 2.8 0 0 0-4-4l-10 10Z" /><path d="m13.5 6.5 4 4" /></>,
  camera: <><path d="M4 8.5A1.5 1.5 0 0 1 5.5 7H8l1.2-2h5.6L16 7h2.5A1.5 1.5 0 0 1 20 8.5v9a1.5 1.5 0 0 1-1.5 1.5h-13A1.5 1.5 0 0 1 4 17.5Z" /><circle cx="12" cy="13" r="3.4" /></>,
  download: <><path d="M12 4v11" /><path d="m7.5 11 4.5 4.5 4.5-4.5" /><path d="M5 19.5h14" /></>,
  map: <><path d="m3.5 6.5 5.5-2 6 2 5.5-2v13l-5.5 2-6-2-5.5 2Z" /><path d="M9 4.5v13M15 6.5v13" /></>,
  list: <path d="M8.5 6.5H20M8.5 12H20M8.5 17.5H20M4 6.5h.01M4 12h.01M4 17.5h.01" />,
  bell: <><path d="M6 16.5V11a6 6 0 1 1 12 0v5.5l1.5 2h-15Z" /><path d="M10 20.5a2.2 2.2 0 0 0 4 0" /></>,
  repeat: <><path d="M4.5 11V9.5a3 3 0 0 1 3-3h11" /><path d="m15.5 3.5 3 3-3 3" /><path d="M19.5 13v1.5a3 3 0 0 1-3 3h-11" /><path d="m8.5 20.5-3-3 3-3" /></>,
  trash: <><path d="M4.5 7h15M10 11v6M14 11v6M6.5 7l1 12.5h9l1-12.5M9.5 7V4.5h5V7" /></>,
} satisfies Record<string, ReactNode>;

export type IconName = keyof typeof PATHS;

export function Icon({ name, size = 20, className }: { name: IconName; size?: number; className?: string }) {
  return (
    <svg className={className ? `icon ${className}` : 'icon'} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      {PATHS[name]}
    </svg>
  );
}
