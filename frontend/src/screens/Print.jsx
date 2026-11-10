import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { Loading } from '../components/ui.jsx'
import { useLoad } from '../lib/hooks.js'

// Paper versions of worksheets, practice sheets and parent notes. No app chrome.

function Toolbar({ label }) {
  const navigate = useNavigate()
  return (
    <div className="print-toolbar">
      <button type="button" className="btn small" onClick={() => navigate(-1)}>
        <Icon name="back" size={18} /> Back
      </button>
      <span className="grow" />
      <button type="button" className="btn small primary" onClick={() => window.print()}>
        <Icon name="print" size={18} /> {label}
      </button>
    </div>
  )
}

function PaperQuestion({ q }) {
  return (
    <div className="sheet-q">
      <span className="n">{q.number}.</span>
      <span className="text">{q.text}</span>
      {q.type === 'choice' && (
        <div className="options">{(q.options ?? []).map((o) => <span key={o}>◯ {o}</span>)}</div>
      )}
      {q.type === 'short_answer' ? (
        <div className="lines"><span /><span /></div>
      ) : (
        <div className="answer-line">
          <span>{q.type === 'choice' ? 'Answer:' : 'Answer:'}</span>
          <span className="answer-box" />
        </div>
      )}
    </div>
  )
}

function PaperSheet({ title, subtitle, name = '', intro, questions }) {
  return (
    <article className="sheet">
      <header className="sheet-head">
        <div>
          <div className="sheet-brand">ChalkBox</div>
          <h1>{title}</h1>
        </div>
        <span>{subtitle}</span>
      </header>
      <div className="name-box">Name: <span className="box">{name}</span></div>
      {intro && <p className="sheet-intro">{intro}</p>}
      {questions.map((q) => <PaperQuestion key={q.number} q={q} />)}
    </article>
  )
}

export function PrintWorksheet() {
  const { worksheetId } = useParams()
  const { current } = useClass()
  const { data: worksheet } = useLoad(() => api.worksheet(worksheetId), worksheetId)
  if (!worksheet) return <Loading />
  return (
    <div className="print-page">
      <Toolbar label="Print worksheet" />
      <PaperSheet
        title={worksheet.title}
        subtitle={current ? `${current.name} · Sheet #${worksheet.id}` : `Sheet #${worksheet.id}`}
        questions={worksheet.questions}
      />
    </div>
  )
}

export function PrintPractice() {
  const { worksheetId } = useParams()
  const { data } = useLoad(
    async () => ({ worksheet: await api.worksheet(worksheetId), sheets: await api.practiceSheets(worksheetId) }),
    worksheetId,
  )
  if (!data) return <Loading />
  const sheets = data.sheets.filter((s) => s.status === 'approved')
  return (
    <div className="print-page">
      <Toolbar label={`Print ${sheets.length} sheet${sheets.length === 1 ? '' : 's'}`} />
      {sheets.length === 0 && <p style={{ padding: 24 }}>No approved practice sheets yet.</p>}
      {sheets.map((s) => (
        <PaperSheet
          key={s.id}
          title={`Practice: ${data.worksheet.title}`}
          subtitle="Just for you"
          name={s.student_name}
          intro={s.content?.intro}
          questions={s.content?.questions ?? []}
        />
      ))}
    </div>
  )
}

export function PrintReports() {
  const { current } = useClass()
  const classId = current?.id
  const { data: reports } = useLoad(() => (classId ? api.reports(classId) : null), classId)
  if (!reports) return <Loading />
  const latest = Object.values(
    reports.filter((r) => r.status === 'approved').reduce((acc, r) => ({ ...acc, [r.student_id]: !acc[r.student_id] || acc[r.student_id].id < r.id ? r : acc[r.student_id] }), {}),
  )
  return (
    <div className="print-page">
      <Toolbar label={`Print ${latest.length} note${latest.length === 1 ? '' : 's'}`} />
      {latest.map((r) => (
        <article className="sheet" key={r.id}>
          <header className="sheet-head">
            <div>
              <div className="sheet-brand">ChalkBox · {current.name}</div>
              <h1>Progress note: {r.student_name}</h1>
            </div>
            <span>{current.teacher}</span>
          </header>
          <p className="sheet-note">{r.text}</p>
        </article>
      ))}
    </div>
  )
}
