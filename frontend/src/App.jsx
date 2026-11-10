import { useEffect, useState } from 'react'
import { NavLink, Route, Routes } from 'react-router-dom'
import { api } from './api.js'

// Starter shell: navigation + a home screen that proves the app is talking to the hub.
// Each placeholder route below becomes a real screen next.

function Home() {
  const [status, setStatus] = useState(null)
  const [classes, setClasses] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.status(), api.classes()])
      .then(([s, c]) => {
        setStatus(s)
        setClasses(c)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="error">Can't reach the ChalkBox hub: {error}</p>
  if (!status) return <p className="muted">Connecting to the hub…</p>

  return (
    <>
      <section className="card">
        <h2>Hub</h2>
        <p className="ok">● Running offline</p>
        <p className="muted">
          Text model <code>{status.text_model.model}</code> · Vision model{' '}
          <code>{status.vision_model.model}</code> · {status.workers} worker(s)
        </p>
      </section>
      <section className="card">
        <h2>Classes</h2>
        {classes.length === 0 && <p className="muted">No classes yet. Run the seed script.</p>}
        <ul className="list">
          {classes.map((c) => (
            <li key={c.id}>
              <strong>{c.name}</strong>
              <span className="muted">
                {' '}· Grade {c.grade} · {c.teacher} · {c.student_count} students
              </span>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}

function Placeholder({ title }) {
  return (
    <section className="card">
      <h2>{title}</h2>
      <p className="muted">Coming next.</p>
    </section>
  )
}

const NAV = [
  { to: '/', label: 'Home' },
  { to: '/plan', label: 'Plan' },
  { to: '/check', label: 'Check' },
  { to: '/class', label: 'Class' },
  { to: '/reports', label: 'Reports' },
]

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <h1>ChalkBox</h1>
        <nav>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/'}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/plan" element={<Placeholder title="Plan a lesson" />} />
          <Route path="/check" element={<Placeholder title="Check worksheets" />} />
          <Route path="/class" element={<Placeholder title="Class view" />} />
          <Route path="/reports" element={<Placeholder title="Parent reports" />} />
          <Route path="*" element={<Placeholder title="Page not found" />} />
        </Routes>
      </main>
    </div>
  )
}
