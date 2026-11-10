import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { useToast } from '../components/Toast.jsx'
import { ActionBar, AppBar, Avatar, EmptyState, ErrorState, Page, Skeleton, Spinner, StatusBadge } from '../components/ui.jsx'
import { isBusy } from '../lib/format.js'
import { useAction, useLoad, usePolling } from '../lib/hooks.js'

function Note({ report, onChange }) {
  const toast = useToast()
  // The parent remounts this note (via `key`) when new text arrives, so this starts fresh.
  const [text, setText] = useState(report.text ?? '')

  const [approve, approving] = useAction(async () => {
    try {
      await api.approveReport(report.id, { text })
      toast(`Note for ${report.student_name} approved`)
      onChange()
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  return (
    <details className="card disclosure" open={report.status === 'ready'}>
      <summary>
        <span className="row grow" style={{ minWidth: 0 }}>
          <Avatar name={report.student_name} />
          <span className="grow" style={{ minWidth: 0 }}>
            <span className="ellipsis" style={{ display: 'block' }}>{report.student_name}</span>
            <span className="tiny muted">{report.language}</span>
          </span>
          <StatusBadge status={report.status} />
        </span>
      </summary>
      <div className="stack" style={{ marginTop: 10 }}>
        {report.status === 'error' && <ErrorState message={report.error} />}
        {isBusy(report.status) && <p className="small muted">Writing the note in {report.language}…</p>}
        {(report.status === 'ready' || report.status === 'approved') && (
          <>
            <textarea
              className="textarea"
              value={text}
              onChange={(e) => setText(e.target.value)}
              readOnly={report.status === 'approved'}
              aria-label={`Note for ${report.student_name}`}
              style={{ minHeight: 160 }}
            />
            {report.status === 'ready' && (
              <button type="button" className="btn primary block" onClick={approve} disabled={approving}>
                {approving ? <Spinner /> : <Icon name="check" />} Approve note
              </button>
            )}
          </>
        )}
      </div>
    </details>
  )
}

export default function Reports() {
  const { current } = useClass()
  const toast = useToast()
  const classId = current?.id
  const { data: reports, error, reload } = useLoad(() => (classId ? api.reports(classId) : null), classId)
  usePolling(reload, (reports ?? []).some((r) => isBusy(r.status)), 4000)

  const [writeAll, writing] = useAction(async () => {
    try {
      const { report_ids } = await api.createReports(classId)
      toast(`Writing ${report_ids.length} parent note${report_ids.length > 1 ? 's' : ''}…`)
      await reload()
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  // Newest note per student.
  const latest = Object.values(
    (reports ?? []).reduce((acc, r) => ({ ...acc, [r.student_id]: !acc[r.student_id] || acc[r.student_id].id < r.id ? r : acc[r.student_id] }), {}),
  ).sort((a, b) => a.student_name.localeCompare(b.student_name))
  const approved = latest.filter((r) => r.status === 'approved').length

  return (
    <>
      <AppBar title="Parent notes" subtitle="Written in each family's language" />
      <Page hasAction>
        {error && <ErrorState message={error} onRetry={reload} />}
        {!reports ? (
          <Skeleton />
        ) : latest.length === 0 ? (
          <div className="card">
            <EmptyState icon="report" title="No parent notes yet">
              ChalkBox writes a short, kind note for each family about how their child is doing, in their own language.
            </EmptyState>
          </div>
        ) : (
          latest.map((r) => <Note key={`${r.id}-${r.status}`} report={r} onChange={reload} />)
        )}
      </Page>
      <ActionBar>
        {approved > 0 && (
          <Link className="btn" to="/print/reports">
            <Icon name="print" /> Print {approved}
          </Link>
        )}
        <button type="button" className="btn primary" onClick={writeAll} disabled={writing || !classId}>
          {writing ? <Spinner /> : <Icon name="sparkle" />} Write notes for class
        </button>
      </ActionBar>
    </>
  )
}
