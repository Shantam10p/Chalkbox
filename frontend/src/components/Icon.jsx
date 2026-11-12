// Small inline icon set (no icon font or CDN, so it works offline).
const PATHS = {
  home: 'M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6h-6v6H4a1 1 0 0 1-1-1z',
  plan: 'M6 3h9l4 4v14H6z M14 3v5h5 M9 12h7 M9 16h7',
  camera: 'M4 8h3l2-3h6l2 3h3v12H4z M12 17a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z',
  class: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5 M16 5.2a3 3 0 0 1 0 5.6 M17.5 14.7c2 .6 3.5 2.4 3.5 5.3',
  report: 'M5 4h14v12H9l-4 4z M9 9h6 M9 12h4',
  back: 'M15 5l-7 7 7 7',
  check: 'M5 12.5l4.5 4.5L19 7',
  cross: 'M6 6l12 12M18 6L6 18',
  question: 'M9.5 9a2.5 2.5 0 1 1 3.5 2.3c-.6.3-1 .9-1 1.6V14 M12 17.5v.5',
  print: 'M7 9V3h10v6 M6 17H4v-7h16v7h-2 M7 14h10v7H7z',
  upload: 'M12 16V4 M7 9l5-5 5 5 M4 20h16',
  image: 'M4 5h16v14H4z M4 16l5-5 4 4 3-3 4 4 M15 9.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3z',
  chevron: 'M9 5l7 7-7 7',
  plus: 'M12 5v14M5 12h14',
  sparkle: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z M19 16l.7 1.8 1.8.7-1.8.7L19 21l-.7-1.8-1.8-.7 1.8-.7z',
  alert: 'M12 4l9 16H3z M12 10v4 M12 17v.5',
  info: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18z M12 11v5 M12 8v.5',
  refresh: 'M20 11a8 8 0 1 0-2.3 5.7 M20 5v6h-6',
  wifiOff: 'M3 3l18 18 M8.5 16.5a5 5 0 0 1 7 0 M5 12.5a10 10 0 0 1 4.2-2.4 M12 20h.01 M15 10.4a10 10 0 0 1 4 2.1 M2 8.8A15 15 0 0 1 6.3 6 M11 5.1A15 15 0 0 1 22 8.8',
  edit: 'M4 20h4L19 9l-4-4L4 16z M14 6l4 4',
  trash: 'M4 7h16 M10 11v6 M14 11v6 M6 7l1 13h10l1-13 M9 7V4h6v3',
  logout: 'M10 4H5v16h5 M15 8l4 4-4 4 M9 12h10',
  lock: 'M6 11h12v9H6z M8 11V8a4 4 0 0 1 8 0v3',
  chat: 'M4 5h16v11H9l-5 4z M8 9h8 M8 12h5',
  send: 'M4 12l16-8-6 16-3-7z M11 13l9-9',
  flag: 'M5 21V4 M5 4h11l-2 4 2 4H5',
  users: 'M9 11a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M3 20c0-3.3 2.7-5.5 6-5.5s6 2.2 6 5.5',
  chart: 'M4 20V10 M10 20V4 M16 20v-7 M22 20H2',
  book: 'M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z M4 21V5 M8 7h7',
}

export default function Icon({ name, size = 22, strokeWidth = 1.8, className, title }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : undefined}
    >
      {title && <title>{title}</title>}
      <path d={PATHS[name] ?? PATHS.info} />
    </svg>
  )
}
