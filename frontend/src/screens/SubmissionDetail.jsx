import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { useToast } from '../components/Toast.jsx'
import {
  ActionBar, AppBar, ErrorState, Loading, Notice, Page, ScoreRing, Spinner, StatusBadge,
} from '../components/ui.jsx'
import { GRADED_BY_LABEL, isBusy } from '../lib/format.js'
import { useAction, useLoad, usePolling } from '../lib/hooks.js'

// ---------------------------------------------------------------- shared pieces

function Photo({ submissionId }) {
  const [open, setOpen] = useState(false)
  return (
    <button
      type="button"
      className={`photo-frame${open ? '' : ' collapsed'}`}
      style={{ padding: 0, cursor: 'zoom-in', width: '100%' }}
      onClick={() => setOpen((o) => !o)}
      aria-label={open ? 'Shrink photo' : 'Show the whole photo'}
    >
      <img src={api.submissionImageUrl(submissionId)} alt="Photo of the student's worksheet" />
    </button>
  )
}

const STEPS = [
  { key: 'reading', label: 'Reading the handwriting' },
  { key: 'grading', label: 'Marking every answer' },
  { key: 'done', label: 'Writing feedback for the student' },
]

function Progress({ status }) {
  const active = status === 'grading' ? 1 : status === 'reading' ? 0 : -1
  return (
    <div className="card stack" style={{ gap: 16 }}>
      <div className="row">
        <div className="spinner" />
        <b>{status === 'queued' ? 'Waiting for its turn…' : 'ChalkBox is working on this sheet'}</b>
      </div>
      <div className="steps">
        {STEPS.map((step, i) => (
          <div key={step.key} className={`step${i < active ? ' done' : i === active ? ' active' : ''}`}>
            <span className="step-dot">{i < active ? <Icon name="check" size={16} /> : i + 1}</span>
            {step.label}
          </div>
        ))}
      </div>
      <p className="small muted">This page updates by itself. You can photograph the next sheet meanwhile.</p>
    </div>
  )
}

// ---------------------------------------------------------------- checkpoint 1: readings

function ReviewReadings({ submission, onDone }) {
  const toast = useToast()
  const flagged = submission.review?.flagged ?? []
  const [values, setValues] = useState(() => Object.fromEntries(flagged.map((f) => [f.question, f.read_as ?? ''])))

  const [send, sending] = useAction(async () => {
    const corrections = Object.fromEntries(
      flagged.filter((f) => (values[f.question] ?? '') !== (f.read_as ?? '')).map((f) => [f.question, values[f.question]]),
    )
    try {
      await api.reviewSubmission(submission.id, corrections)
      toast('Thanks! ChalkBox is finishing the marking.')
      onDone()
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  return (
    <>
      <Page hasAction>
        <Notice tone="warn" icon="alert">
          ChalkBox wasn't sure it read {flagged.length === 1 ? 'one answer' : `${flagged.length} answers`} correctly.
          Look at the photo and fix anything that's wrong.
        </Notice>
        <Photo submissionId={submission.id} />
        {flagged.map((f) => (
          <label key={f.question} className="card field">
            <span className="spread">
              <span>Question {f.question}: <span className="muted" style={{ fontWeight: 500 }}>{f.text}</span></span>
              <span className="badge warn">{Math.round((f.confidence ?? 0) * 100)}% sure</span>
            </span>
            <span className="hint">What the student wrote</span>
            <input
              className="input answer"
              value={values[f.question] ?? ''}
              onChange={(e) => setValues((v) => ({ ...v, [f.question]: e.target.value }))}
              placeholder="(blank)"
              autoComplete="off"
            />
          </label>
        ))}
      </Page>
      <ActionBar>
        <button type="button" className="btn primary" onClick={send} disabled={sending}>
          {sending ? <Spinner /> : <Icon name="check" />} Confirm and continue
        </button>
      </ActionBar>
    </>
  )
}

// ---------------------------------------------------------------- checkpoint 2: results

function Mark({ correct }) {
  if (correct === true) return <span className="q-num ok" aria-label="Correct"><Icon name="check" size={18} /></span>
  if (correct === false) return <span className="q-num bad" aria-label="Wrong"><Icon name="cross" size={18} /></span>
  return <span className="q-num unknown" aria-label="Undecided"><Icon name="question" size={18} /></span>
}

function Results({ submission, worksheet, students, onApproved }) {
  const toast = useToast()
  const questions = useMemo(
    () => Object.fromEntries((worksheet?.questions ?? []).map((q) => [String(q.number), q])),
    [worksheet],
  )
  const mistakes = worksheet?.misconceptions ?? {}
  const approved = submission.status === 'approved'

  const [overrides, setOverrides] = useState({})
  const [feedback, setFeedback] = useState(submission.feedback ?? '')
  const [studentId, setStudentId] = useState(submission.student_id ?? '')
  // The screen remounts Results (via `key`) whenever the status changes, so edits start fresh.

  const marks = submission.answers.map((a) => ({
    ...a,
    final: a.question_no in overrides ? overrides[a.question_no] : a.correct,
  }))
  const correct = marks.filter((a) => a.final === true).length
  const undecided = marks.filter((a) => a.final == null).length

  const [approve, approving] = useAction(async () => {
    try {
      await api.approveSubmission(submission.id, {
        student_id: studentId === '' ? null : Number(studentId),
        overrides,
        feedback,
      })
      toast('Marks saved')
      onApproved()
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  const toggle = (number, value) => setOverrides((o) => ({ ...o, [number]: value }))

  return (
    <>
      <Page hasAction={!approved}>
        <div className="card row" style={{ gap: 16 }}>
          <ScoreRing correct={correct} total={marks.length} />
          <div className="grow stack" style={{ gap: 6 }}>
            <label className="field">
              <span className="small">Student</span>
              <select
                className="select"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                disabled={approved}
              >
                <option value="">Choose student…</option>
                {students.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </label>
            {submission.student_name_read && (
              <span className="tiny muted">Name on sheet: “{submission.student_name_read}”</span>
            )}
          </div>
        </div>

        {!submission.student_id && !approved && (
          <Notice tone="warn">ChalkBox couldn't match the name on the sheet. Choose the student above.</Notice>
        )}
        {undecided > 0 && !approved && (
          <Notice tone="warn" icon="question">
            {undecided} answer{undecided > 1 ? 's need' : ' needs'} your decision. Tap ✓ or ✗.
          </Notice>
        )}

        <Photo submissionId={submission.id} />

        <div className="card flush">
          {marks.map((a) => {
            const q = questions[a.question_no] ?? {}
            const expected = q.answer ?? q.rubric
            return (
              <div className="q-row" key={a.question_no}>
                <div className="q-head">
                  <Mark correct={a.final} />
                  <div className="grow stack" style={{ gap: 6 }}>
                    <span className="small muted">Q{a.question_no} · {q.text}</span>
                    <div className="answer-pair">
                      <span>Wrote: <b>{a.student_answer || '(blank)'}</b></span>
                      {expected && q.type !== 'short_answer' && <span className="muted">Answer: <b>{expected}</b></span>}
                    </div>
                  </div>
                  {!approved && (
                    <div className="segmented" role="group" aria-label={`Mark question ${a.question_no}`}>
                      <button type="button" className="yes" aria-pressed={a.final === true} aria-label="Correct" onClick={() => toggle(a.question_no, true)}>
                        <Icon name="check" size={18} />
                      </button>
                      <button type="button" className="no" aria-pressed={a.final === false} aria-label="Wrong" onClick={() => toggle(a.question_no, false)}>
                        <Icon name="cross" size={18} />
                      </button>
                    </div>
                  )}
                </div>
                {(a.misconception || a.explanation) && a.final === false && (
                  <div className="why">
                    {a.misconception && a.misconception !== 'other' && (
                      <b style={{ display: 'block' }}>{mistakes[a.misconception] ?? a.misconception}</b>
                    )}
                    {a.explanation}
                  </div>
                )}
                <div className="row wrap" style={{ gap: 6 }}>
                  <span className={`badge${a.graded_by === 'ai' ? ' info' : ''}`}>
                    {a.question_no in overrides ? GRADED_BY_LABEL.teacher : GRADED_BY_LABEL[a.graded_by] ?? a.graded_by}
                  </span>
                  {a.teacher_fixed && <span className="badge">Reading fixed by you</span>}
                </div>
              </div>
            )
          })}
        </div>

        <label className="card field">
          <span>Feedback for the student</span>
          <textarea
            className="textarea"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            readOnly={approved}
          />
          {!approved && <span className="hint">Edit anything before approving. This goes home with the student.</span>}
        </label>
      </Page>

      {!approved && (
        <ActionBar>
          <button
            type="button"
            className="btn primary"
            onClick={approve}
            disabled={approving || undecided > 0 || studentId === ''}
          >
            {approving ? <Spinner /> : <Icon name="check" />} Approve marks
          </button>
        </ActionBar>
      )}
    </>
  )
}

// ---------------------------------------------------------------- screen

export default function SubmissionDetail() {
  const { submissionId } = useParams()
  const navigate = useNavigate()
  const toast = useToast()
  const { current } = useClass()
  const sub = useLoad(() => api.submission(submissionId), submissionId)
  const worksheetId = sub.data?.worksheet_id
  const worksheet = useLoad(() => (worksheetId ? api.worksheet(worksheetId) : null), worksheetId)
  usePolling(sub.reload, isBusy(sub.data?.status), 3000)

  const [retry, retrying] = useAction(async () => {
    try {
      await api.retrySubmission(submissionId)
      await sub.reload()
    } catch (e) {
      toast(e.message, 'error')
    }
  })

  const backTo = worksheetId ? `/check/${worksheetId}` : '/check'
  const s = sub.data
  const title = s?.student_name || s?.student_name_read || (s ? `Sheet ${s.id}` : 'Worksheet')

  return (
    <>
      <AppBar title={title} subtitle={worksheet.data?.title} back={backTo} actions={s && <StatusBadge status={s.status} />} />
      {sub.error ? (
        <Page><ErrorState message={sub.error} onRetry={sub.reload} /></Page>
      ) : !s ? (
        <Loading />
      ) : isBusy(s.status) ? (
        <Page><Progress status={s.status} /><Photo submissionId={s.id} /></Page>
      ) : s.status === 'error' ? (
        <Page>
          <ErrorState message={s.error || 'ChalkBox could not check this sheet.'} onRetry={retrying ? undefined : retry} />
          <Photo submissionId={s.id} />
        </Page>
      ) : s.status === 'needs_review' ? (
        <ReviewReadings submission={s} onDone={sub.reload} />
      ) : (
        <Results
          key={`${s.id}-${s.status}`}
          submission={s}
          worksheet={worksheet.data}
          students={current?.students ?? []}
          onApproved={() => navigate(backTo)}
        />
      )}
    </>
  )
}
