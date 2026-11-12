import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Icon from './Icon.jsx'
import { STATUS, initials } from '../lib/format.js'

export function AppBar({ title, subtitle, back, actions }) {
  const navigate = useNavigate()
  return (
    <header className="appbar">
      <div className="appbar-inner">
        {back && (
          <button
            type="button"
            className="icon-btn"
            aria-label="Back"
            onClick={() => (typeof back === 'string' ? navigate(back) : navigate(-1))}
          >
            <Icon name="back" />
          </button>
        )}
        <h1>
          {title}
          {subtitle && <span className="subtitle">{subtitle}</span>}
        </h1>
        {actions}
      </div>
    </header>
  )
}

// The home-screen greeting: plain typography on the page (date, headline, one meta line).
export function Greeting({ title, meta }) {
  const [now] = useState(() => new Date()) // read once, so the date stays stable across re-renders
  return (
    <section className="greeting" aria-label="Greeting">
      <div className="greeting-top">
        <time dateTime={now.toISOString().slice(0, 10)}>
          {now.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })}
        </time>
        <span className="offline-pill" title="Runs on your school's ChalkBox. No internet needed.">
          <Icon name="wifiOff" size={13} /> Offline
        </span>
      </div>
      <h2>{title}</h2>
      {meta && <p>{meta}</p>}
    </section>
  )
}

// `roomy`: extra space below the top bar (used on the Plan and Check lists).
export function Page({ children, hasAction = false, roomy = false }) {
  const classes = ['page', hasAction && 'has-action', roomy && 'roomy'].filter(Boolean).join(' ')
  return <main className={classes}>{children}</main>
}

export function ActionBar({ children }) {
  return (
    <div className="action-bar no-print">
      <div className="action-bar-inner">{children}</div>
    </div>
  )
}

export function StatusBadge({ status }) {
  const meta = STATUS[status] ?? { label: status, tone: 'neutral' }
  return (
    <span className={`badge ${meta.tone}${meta.busy ? ' busy' : ''}`} aria-live="polite">
      <span className="dot" />
      {meta.label}
    </span>
  )
}

export function Notice({ tone = 'info', icon, children }) {
  const fallback = { info: 'info', warn: 'alert', error: 'alert', ok: 'check' }[tone]
  return (
    <div className={`notice ${tone}`} role={tone === 'error' ? 'alert' : undefined}>
      <Icon name={icon ?? fallback} size={20} />
      <div>{children}</div>
    </div>
  )
}

export function Loading({ label = 'Loading…' }) {
  return (
    <div className="loading" role="status">
      <div className="spinner lg" />
      <span>{label}</span>
    </div>
  )
}

export function Skeleton({ count = 3 }) {
  return (
    <div className="stack" aria-hidden="true">
      {Array.from({ length: count }, (_, i) => (
        <div className="skeleton" key={i} />
      ))}
    </div>
  )
}

export function ErrorState({ message, onRetry }) {
  return (
    <Notice tone="error">
      <div className="stack">
        <span>{message}</span>
        {onRetry && (
          <button type="button" className="btn small" onClick={onRetry}>
            <Icon name="refresh" size={18} /> Try again
          </button>
        )}
      </div>
    </Notice>
  )
}

export function EmptyState({ icon = 'info', title, children, action }) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon name={icon} size={28} />
      </div>
      <h3>{title}</h3>
      {children && <p className="small">{children}</p>}
      {action}
    </div>
  )
}

export function Avatar({ name, large = false }) {
  return (
    <span className={`avatar${large ? ' lg' : ''}`} aria-hidden="true">
      {initials(name)}
    </span>
  )
}

export function ListLink({ to, onClick, leading, title, meta, trailing }) {
  const content = (
    <>
      {leading}
      <div className="grow">
        <div className="title ellipsis">{title}</div>
        {meta && <div className="meta">{meta}</div>}
      </div>
      {trailing}
      {to && <Icon name="chevron" size={18} className="chev" />}
    </>
  )
  if (to) {
    return (
      <Link className="list-item" to={to}>
        {content}
      </Link>
    )
  }
  return (
    <button type="button" className="list-item" onClick={onClick}>
      {content}
    </button>
  )
}

export function Stat({ value, label }) {
  return (
    <div className="stat">
      <span className="value">{value}</span>
      <span className="label">{label}</span>
    </div>
  )
}

export function Bar({ ratio, tone }) {
  const width = Math.max(0, Math.min(1, ratio ?? 0)) * 100
  return (
    <div className={`bar${tone ? ` ${tone}` : ''}`} role="presentation">
      <span style={{ width: `${width}%` }} />
    </div>
  )
}

export function ScoreRing({ correct, total }) {
  const p = total ? Math.round((correct / total) * 100) : 0
  return (
    <div className="score-ring" style={{ '--p': p }} aria-label={`Score ${correct} out of ${total}`}>
      <div>{total ? `${correct}/${total}` : '–'}</div>
    </div>
  )
}

export function Spinner() {
  return <span className="spinner" aria-hidden="true" />
}
