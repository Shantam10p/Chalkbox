import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { useToast } from '../components/Toast.jsx'
import { ActionBar, AppBar, Notice, Page, Spinner } from '../components/ui.jsx'
import { useAction } from '../lib/hooks.js'

const SUBJECTS = ['Math', 'Science', 'English', 'Social Studies']
const LENGTHS = [30, 40, 60]
const LANGUAGES = ['English', 'Spanish', 'Hindi', 'Nepali', 'Tagalog']

export default function PlanNew() {
  const { current } = useClass()
  const navigate = useNavigate()
  const toast = useToast()
  const [form, setForm] = useState({
    subject: 'Math', topic: '', minutes: 40, num_questions: 8, language: 'English',
  })
  const set = (key) => (value) => setForm((f) => ({ ...f, [key]: value }))

  const [submit, busy] = useAction(async () => {
    try {
      const { id } = await api.createLesson({ ...form, class_id: current.id, topic: form.topic.trim() })
      navigate(`/plan/${id}`, { replace: true })
    } catch (error) {
      toast(error.message, 'error')
    }
  })

  const canSubmit = current && form.topic.trim().length >= 3 && !busy

  return (
    <>
      <AppBar title="New lesson" subtitle={current ? `${current.name} · Grade ${current.grade}` : ''} back="/plan" />
      <Page hasAction>
        <form
          className="stack"
          style={{ gap: 18 }}
          onSubmit={(e) => {
            e.preventDefault()
            if (canSubmit) submit()
          }}
        >
          <div className="field">
            <span>Subject</span>
            <div className="chips" role="group" aria-label="Subject">
              {SUBJECTS.map((s) => (
                <button type="button" key={s} className="chip" aria-pressed={form.subject === s} onClick={() => set('subject')(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>

          <label className="field">
            <span>Topic</span>
            <input
              className="input"
              placeholder="e.g. Subtracting fractions"
              value={form.topic}
              onChange={(e) => set('topic')(e.target.value)}
              autoFocus
              required
              minLength={3}
            />
          </label>

          <div className="field">
            <span>Lesson length</span>
            <div className="chips" role="group" aria-label="Lesson length">
              {LENGTHS.map((m) => (
                <button type="button" key={m} className="chip" aria-pressed={form.minutes === m} onClick={() => set('minutes')(m)}>
                  {m} min
                </button>
              ))}
            </div>
          </div>

          <div className="field">
            <span>Worksheet questions</span>
            <div className="stepper">
              <button type="button" aria-label="Fewer questions" onClick={() => set('num_questions')(Math.max(2, form.num_questions - 1))}>−</button>
              <output aria-live="polite">{form.num_questions}</output>
              <button type="button" aria-label="More questions" onClick={() => set('num_questions')(Math.min(20, form.num_questions + 1))}>+</button>
            </div>
          </div>

          <label className="field">
            <span>Class language <span className="hint">for local-language words in the notes</span></span>
            <select className="select" value={form.language} onChange={(e) => set('language')(e.target.value)}>
              {LANGUAGES.map((l) => <option key={l}>{l}</option>)}
            </select>
          </label>

          <Notice tone="info" icon="sparkle">
            ChalkBox writes the lesson and worksheet, then checks every answer with exact math. You approve it before printing.
          </Notice>
        </form>
      </Page>
      <ActionBar>
        <button type="button" className="btn primary" disabled={!canSubmit} onClick={submit}>
          {busy ? <Spinner /> : <Icon name="sparkle" />} Create lesson
        </button>
      </ActionBar>
    </>
  )
}
