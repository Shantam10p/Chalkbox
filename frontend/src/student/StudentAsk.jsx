import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import Icon from '../components/Icon.jsx'
import SignOutButton from '../components/SignOutButton.jsx'
import { AppBar, ErrorState, Notice, Spinner } from '../components/ui.jsx'
import { useLoad } from '../lib/hooks.js'

const SUGGESTIONS = [
  'Can you explain adding fractions?',
  'Give me a hint for my practice',
  'Why was my answer wrong?',
]
const MAX_CHARS = 500

// The course helper: answers questions about class topics with hints, never full answers.
// The teacher can read every conversation.
export default function StudentAsk() {
  const history = useLoad(() => api.helperHistory(), 'helper')
  const [messages, setMessages] = useState(null)
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const endRef = useRef(null)

  const shown = messages ?? history.data ?? []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [shown.length, sending])

  const send = async (text) => {
    const message = text.trim()
    if (!message || sending) return
    const base = messages ?? history.data ?? []
    setMessages([...base, { id: `me-${Date.now()}`, role: 'student', content: message }])
    setDraft('')
    setError(null)
    setSending(true)
    try {
      const reply = await api.askHelper(message)
      setMessages((current) => [...current, reply])
    } catch (e) {
      setError(e.message)
      setDraft(message)
      setMessages(base)
    } finally {
      setSending(false)
    }
  }

  return (
    <>
      <AppBar title="Ask ChalkBox" subtitle="Help with your schoolwork" actions={<SignOutButton />} />
      <main className="page chat-page">
        <Notice tone="info" icon="chat">
          Ask about what you're learning in class. I give hints, not answers. Your teacher can see these chats.
        </Notice>

        {history.error && <ErrorState message={history.error} onRetry={history.reload} />}

        {shown.length === 0 && !history.loading && (
          <div className="stack">
            <p className="small muted">Try asking:</p>
            <div className="chips">
              {SUGGESTIONS.map((s) => (
                <button type="button" key={s} className="chip" onClick={() => send(s)} disabled={sending}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="chat-log" aria-live="polite">
          {shown.map((m) => (
            <div key={m.id} className={`bubble ${m.role === 'student' ? 'mine' : 'theirs'}`}>
              {m.content}
            </div>
          ))}
          {sending && (
            <div className="bubble theirs typing" aria-label="ChalkBox is thinking">
              <Spinner /> Thinking…
            </div>
          )}
          <div ref={endRef} />
        </div>
        {error && <Notice tone="error">{error}</Notice>}
      </main>

      <form
        className="composer no-print"
        onSubmit={(e) => {
          e.preventDefault()
          send(draft)
        }}
      >
        <div className="composer-inner">
          <textarea
            className="input composer-input"
            rows={1}
            value={draft}
            maxLength={MAX_CHARS}
            placeholder="Ask about your lesson…"
            aria-label="Your question"
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send(draft)
              }
            }}
          />
          <button type="submit" className="icon-btn send-btn" aria-label="Send" disabled={sending || !draft.trim()}>
            <Icon name="send" />
          </button>
        </div>
      </form>
    </>
  )
}
