import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import Icon from '../components/Icon.jsx'
import { useToast } from '../components/Toast.jsx'
import { ActionBar, AppBar, Bar, EmptyState, ErrorState, Loading, Page, Spinner, Stat } from '../components/ui.jsx'
import { percent } from '../lib/format.js'
import { useAction, useLoad } from '../lib/hooks.js'

const GROUPS = [
  { key: 'reteach', title: 'Needs reteaching', tone: 'bad', hint: 'Under 50%' },
  { key: 'practice', title: 'Needs practice', tone: 'warn', hint: '50–79%' },
  { key: 'ready', title: 'Ready to move on', tone: 'ok', hint: '80% or more' },
]

function accuracyTone(accuracy) {
  if (accuracy == null) return undefined
  if (accuracy < 0.5) return 'bad'
  return accuracy < 0.8 ? 'warn' : undefined
}

export default function WorksheetSummary() {
  const { worksheetId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { data: summary, error, reload } = useLoad(() => api.worksheetSummary(worksheetId), worksheetId)

  const [makePractice, making] = useAction(async () => {
    try {
      const { practice_ids } = await api.createPractice(worksheetId)
      toast(`Writing ${practice_ids.length} practice sheet${practice_ids.length > 1 ? 's' : ''}…`)
      navigate(`/class/worksheets/${worksheetId}/practice`)
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  if (error) return (<><AppBar title="Class results" back="/class" /><Page><ErrorState message={error} onRetry={reload} /></Page></>)
  if (!summary) return (<><AppBar title="Class results" back="/class" /><Loading /></>)

  const hasData = summary.graded > 0

  return (
    <>
      <AppBar title={summary.title} subtitle="Class results" back="/class" />
      <Page hasAction={hasData}>
        {!hasData ? (
          <div className="card">
            <EmptyState
              icon="chart"
              title="No marked sheets yet"
              action={<Link className="btn primary" to={`/check/${worksheetId}`}><Icon name="camera" /> Check sheets</Link>}
            >
              Results appear here as soon as ChalkBox has marked some sheets.
            </EmptyState>
          </div>
        ) : (
          <>
            <div className="grid-3">
              <Stat value={percent(summary.average)} label="Class average" />
              <Stat value={summary.graded} label="Sheets marked" />
              <Stat value={summary.approved} label="Approved" />
            </div>

            <section className="card stack">
              <div className="card-title" style={{ marginBottom: 0 }}><Icon name="alert" /> Most common mistakes</div>
              {summary.top_mistakes.length === 0 && <p className="muted small">No repeated mistakes. Nice work, class!</p>}
              {summary.top_mistakes.map((m) => (
                <div key={m.id} className="stack" style={{ gap: 6 }}>
                  <div className="spread">
                    <b className="small">{m.description}</b>
                    <span className="badge bad">{m.count}</span>
                  </div>
                  <Bar ratio={m.share} tone="bad" />
                  <span className="tiny muted">{m.students.join(', ')}</span>
                </div>
              ))}
            </section>

            <section className="stack">
              <h2 className="section-title">Groups</h2>
              {GROUPS.map((g) => (
                <details className="card disclosure" key={g.key} open={g.key === 'reteach'}>
                  <summary>
                    <span className="row">
                      <span className={`badge ${g.tone}`}>{summary.groups[g.key].length}</span>
                      {g.title}
                      <span className="tiny muted">{g.hint}</span>
                    </span>
                    <Icon name="chevron" size={18} className="chev" />
                  </summary>
                  <ul className="list">
                    {summary.groups[g.key].map((s) => (
                      <li key={s.submission_id}>
                        <Link className="list-item" to={`/submissions/${s.submission_id}`} style={{ padding: '10px 0', minHeight: 48 }}>
                          <span className="grow">{s.student}</span>
                          <span className="badge">{s.score}</span>
                        </Link>
                      </li>
                    ))}
                    {summary.groups[g.key].length === 0 && <li className="small muted" style={{ padding: '8px 0' }}>Nobody</li>}
                  </ul>
                </details>
              ))}
            </section>

            <section className="card stack">
              <div className="card-title" style={{ marginBottom: 0 }}><Icon name="chart" /> Questions</div>
              {summary.questions.map((q) => (
                <div key={q.number} className="stack" style={{ gap: 6 }}>
                  <div className="spread">
                    <span className="small"><b>Q{q.number}</b> {q.text}</span>
                    <span className="small strong">{percent(q.accuracy)}</span>
                  </div>
                  <Bar ratio={q.accuracy} tone={accuracyTone(q.accuracy)} />
                </div>
              ))}
            </section>

            <Link className="btn block" to={`/class/worksheets/${worksheetId}/practice`}>
              <Icon name="book" /> View practice sheets
            </Link>
          </>
        )}
      </Page>
      {hasData && (
        <ActionBar>
          <Link className="btn" to="/plan/new">
            <Icon name="plan" /> Next lesson
          </Link>
          <button type="button" className="btn primary" onClick={makePractice} disabled={making}>
            {making ? <Spinner /> : <Icon name="sparkle" />} Make practice
          </button>
        </ActionBar>
      )}
    </>
  )
}
