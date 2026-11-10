import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { useToast } from '../components/Toast.jsx'
import { ActionBar, AppBar, Avatar, EmptyState, ErrorState, Loading, Page, Spinner, Stat } from '../components/ui.jsx'
import { percent, shortDate } from '../lib/format.js'
import { useAction, useLoad } from '../lib/hooks.js'

const TREND = {
  improving: { label: 'Improving', tone: 'ok' },
  slipping: { label: 'Slipping', tone: 'bad' },
  steady: { label: 'Steady', tone: 'info' },
}

export default function StudentProfile() {
  const { studentId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { current } = useClass()
  const { data: profile, error, reload } = useLoad(() => api.studentProfile(studentId), studentId)

  const [writeNote, writing] = useAction(async () => {
    try {
      await api.createReports(current.id, { student_ids: [Number(studentId)] })
      toast('Writing the parent note…')
      navigate('/reports')
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  if (error) return (<><AppBar title="Student" back="/class" /><Page><ErrorState message={error} onRetry={reload} /></Page></>)
  if (!profile) return (<><AppBar title="Student" back="/class" /><Loading /></>)

  const { student, history, top_mistakes: mistakes } = profile
  const trend = TREND[profile.trend]

  return (
    <>
      <AppBar title={student.name} back="/class" />
      <Page hasAction={history.length > 0}>
        <div className="card row" style={{ gap: 14 }}>
          <Avatar name={student.name} large />
          <div className="grow stack" style={{ gap: 4 }}>
            <b style={{ fontSize: '1.1rem' }}>{student.name}</b>
            <span className="small muted">Family language: {student.language}</span>
            {trend && <span className={`badge ${trend.tone}`} style={{ width: 'fit-content' }}>{trend.label}</span>}
          </div>
        </div>

        {history.length === 0 ? (
          <div className="card">
            <EmptyState icon="chart" title="No marked work yet">
              Once this student's worksheets are checked, their progress shows up here.
            </EmptyState>
          </div>
        ) : (
          <>
            <div className="grid-2">
              <Stat value={percent(profile.average)} label="Average score" />
              <Stat value={history.length} label="Worksheets" />
            </div>

            <section className="card stack">
              <div className="card-title" style={{ marginBottom: 0 }}><Icon name="alert" /> Keeps getting wrong</div>
              {mistakes.length === 0 ? (
                <p className="small muted">No repeated mistakes. 🎉</p>
              ) : (
                mistakes.map((m) => (
                  <div className="spread" key={m.id}>
                    <span className="small">{m.description}</span>
                    <span className="badge bad">{m.count}×</span>
                  </div>
                ))
              )}
            </section>

            <h2 className="section-title">History</h2>
            <ul className="card flush list">
              {[...history].reverse().map((h) => (
                <li key={h.submission_id}>
                  <Link className="list-item" to={`/submissions/${h.submission_id}`}>
                    <div className="grow">
                      <div className="title">{h.title}</div>
                      <div className="meta">{shortDate(h.date)}</div>
                    </div>
                    <span className="badge">{h.score}</span>
                    <Icon name="chevron" size={18} className="chev" />
                  </Link>
                </li>
              ))}
            </ul>
          </>
        )}
      </Page>
      {history.length > 0 && (
        <ActionBar>
          <button type="button" className="btn primary" onClick={writeNote} disabled={writing || !current}>
            {writing ? <Spinner /> : <Icon name="report" />} Write parent note
          </button>
        </ActionBar>
      )}
    </>
  )
}
