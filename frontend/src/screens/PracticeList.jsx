import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import Icon from '../components/Icon.jsx'
import QuestionList from '../components/Questions.jsx'
import { useToast } from '../components/Toast.jsx'
import { ActionBar, AppBar, Avatar, EmptyState, ErrorState, Loading, Page, Spinner, StatusBadge } from '../components/ui.jsx'
import { isBusy } from '../lib/format.js'
import { useAction, useLoad, usePolling } from '../lib/hooks.js'

function Sheet({ sheet, onChange }) {
  const toast = useToast()
  const [approve, approving] = useAction(async () => {
    try {
      await api.approvePractice(sheet.id)
      onChange()
    } catch (e) {
      toast(e.message, 'error')
    }
  })
  const questions = sheet.content?.questions ?? []

  return (
    <details className="card disclosure">
      <summary>
        <span className="row grow" style={{ minWidth: 0 }}>
          <Avatar name={sheet.student_name} />
          <span className="grow ellipsis">{sheet.student_name}</span>
          <StatusBadge status={sheet.status} />
        </span>
      </summary>
      <div className="stack" style={{ marginTop: 10 }}>
        {sheet.status === 'error' && <ErrorState message={sheet.error} />}
        {sheet.content?.intro && <p className="small" style={{ fontStyle: 'italic' }}>{sheet.content.intro}</p>}
        {questions.length > 0 && <QuestionList questions={questions} />}
        {sheet.status === 'ready' && (
          <button type="button" className="btn primary block" onClick={approve} disabled={approving}>
            {approving ? <Spinner /> : <Icon name="check" />} Approve sheet
          </button>
        )}
      </div>
    </details>
  )
}

export default function PracticeList() {
  const { worksheetId } = useParams()
  const toast = useToast()
  const { data: sheets, error, reload } = useLoad(() => api.practiceSheets(worksheetId), worksheetId)
  usePolling(reload, (sheets ?? []).some((s) => isBusy(s.status)), 4000)

  const ready = (sheets ?? []).filter((s) => s.status === 'ready')
  const approved = (sheets ?? []).filter((s) => s.status === 'approved')
  const working = (sheets ?? []).filter((s) => isBusy(s.status)).length

  const [approveAll, approvingAll] = useAction(async () => {
    try {
      await Promise.all(ready.map((s) => api.approvePractice(s.id)))
      toast(`Approved ${ready.length} sheet${ready.length > 1 ? 's' : ''}`)
      await reload()
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  const back = `/class/worksheets/${worksheetId}`
  if (error) return (<><AppBar title="Practice sheets" back={back} /><Page><ErrorState message={error} onRetry={reload} /></Page></>)
  if (!sheets) return (<><AppBar title="Practice sheets" back={back} /><Loading /></>)

  // Show only each student's newest sheet.
  const latest = Object.values(
    sheets.reduce((acc, s) => ({ ...acc, [s.student_id]: !acc[s.student_id] || acc[s.student_id].id < s.id ? s : acc[s.student_id] }), {}),
  ).sort((a, b) => a.student_name.localeCompare(b.student_name))

  return (
    <>
      <AppBar title="Practice sheets" subtitle="One per student, aimed at their mistakes" back={back} />
      <Page hasAction={ready.length > 0 || approved.length > 0}>
        {working > 0 && (
          <div className="card row">
            <div className="spinner" />
            <span className="small">Writing {working} sheet{working > 1 ? 's' : ''}. Every answer is checked by code.</span>
          </div>
        )}
        {latest.length === 0 ? (
          <div className="card">
            <EmptyState icon="book" title="No practice sheets yet">
              Open the class results and tap “Make practice”.
            </EmptyState>
          </div>
        ) : (
          latest.map((s) => <Sheet key={s.id} sheet={s} onChange={reload} />)
        )}
      </Page>
      {(ready.length > 0 || approved.length > 0) && (
        <ActionBar>
          {approved.length > 0 && (
            <Link className="btn" to={`/print/practice/${worksheetId}`}>
              <Icon name="print" /> Print {approved.length}
            </Link>
          )}
          {ready.length > 0 && (
            <button type="button" className="btn primary" onClick={approveAll} disabled={approvingAll}>
              {approvingAll ? <Spinner /> : <Icon name="check" />} Approve all ({ready.length})
            </button>
          )}
        </ActionBar>
      )}
    </>
  )
}
