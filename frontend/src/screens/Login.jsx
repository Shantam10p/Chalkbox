import { useState } from 'react'
import { useAuth } from '../components/AuthContext.jsx'
import Icon from '../components/Icon.jsx'
import { Notice, Spinner } from '../components/ui.jsx'

export default function Login() {
  const { login } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await login(username.trim(), password)
    } catch (err) {
      setError(err.message)
      setPassword('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login">
      <div className="login-brand">
        <span className="login-logo"><Icon name="book" size={30} /></span>
        <h1 className="brand">ChalkBox</h1>
        <p className="muted">Your school's AI teaching hub</p>
      </div>

      <form className="card stack login-card" onSubmit={submit}>
        <label className="field">
          <span>Username</span>
          <input
            className="input"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            autoFocus
            required
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            className="input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && <Notice tone="error">{error}</Notice>}
        <button type="submit" className="btn primary block" disabled={busy || !username.trim() || !password}>
          {busy ? <Spinner /> : <Icon name="lock" />} Sign in
        </button>
      </form>

      <p className="tiny muted login-foot">
        <Icon name="wifiOff" size={14} /> Runs on your school's ChalkBox. No internet needed.
      </p>
    </main>
  )
}
