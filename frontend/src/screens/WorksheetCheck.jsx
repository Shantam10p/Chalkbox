import { useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api.js'
import { useClass } from '../components/ClassContext.jsx'
import Icon from '../components/Icon.jsx'
import { useToast } from '../components/Toast.jsx'
import { AppBar, EmptyState, ErrorState, ListLink, Loading, Page, Spinner, StatusBadge } from '../components/ui.jsx'
import { isBusy, scoreText } from '../lib/format.js'
import { useAction, useLoad, usePolling } from '../lib/hooks.js'

const STATUS_ORDER = ['needs_review', 'graded', 'error', 'queued', 'reading', 'grading', 'approved']

function PhotoPicker({ onUpload, uploading }) {
  const cameraRef = useRef(null)
  const galleryRef = useRef(null)
  const [files, setFiles] = useState([])
  // Preview URLs are derived from the chosen files and released when they change.
  const previews = useMemo(() => files.map((f) => URL.createObjectURL(f)), [files])
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews])

  const add = (list) => setFiles((current) => [...current, ...Array.from(list ?? [])])

  return (
    <section className="card stack">
      <div className="card-title" style={{ marginBottom: 0 }}>
        <Icon name="camera" /> Add worksheet photos
      </div>
      <p className="small muted">One photo per student. Lay the sheet flat, in good light, and fill the frame.</p>
      <div className="grid-2">
        <button type="button" className="btn" onClick={() => cameraRef.current?.click()}>
          <Icon name="camera" /> Take photo
        </button>
        <button type="button" className="btn" onClick={() => galleryRef.current?.click()}>
          <Icon name="image" /> Gallery
        </button>
      </div>
      <input ref={cameraRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => { add(e.target.files); e.target.value = '' }} />
      <input ref={galleryRef} type="file" accept="image/*" multiple hidden onChange={(e) => { add(e.target.files); e.target.value = '' }} />

      {files.length > 0 && (
        <>
          <div className="photo-strip" aria-label={`${files.length} photos selected`}>
            {previews.map((src, i) => <img key={src} src={src} alt={`Selected photo ${i + 1}`} />)}
          </div>
          <div className="row">
            <button type="button" className="btn ghost small" onClick={() => setFiles([])} disabled={uploading}>Clear</button>
            <button
              type="button"
              className="btn primary grow"
              disabled={uploading}
              onClick={async () => {
                if (await onUpload(files)) setFiles([])
              }}
            >
              {uploading ? <Spinner /> : <Icon name="upload" />} Check {files.length} sheet{files.length > 1 ? 's' : ''}
            </button>
          </div>
        </>
      )}
    </section>
  )
}

export default function WorksheetCheck() {
  const { worksheetId } = useParams()
  const toast = useToast()
  const { refresh } = useClass()
  const worksheet = useLoad(() => api.worksheet(worksheetId), worksheetId)
  const subs = useLoad(() => api.submissions(worksheetId), worksheetId)
  usePolling(subs.reload, (subs.data ?? []).some((s) => isBusy(s.status)), 3000)

  const [upload, uploading] = useAction(async (files) => {
    try {
      const { submission_ids } = await api.uploadPhotos(worksheetId, files)
      toast(`${submission_ids.length} sheet${submission_ids.length > 1 ? 's' : ''} sent to ChalkBox`)
      await subs.reload()
      refresh()
      return true
    } catch (e) {
      toast(e.message, 'error')
      return false
    }
  })

  if (worksheet.error) return (<><AppBar title="Check work" back="/check" /><Page><ErrorState message={worksheet.error} /></Page></>)
  if (!worksheet.data) return (<><AppBar title="Check work" back="/check" /><Loading /></>)

  const list = [...(subs.data ?? [])].sort(
    (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status) || a.id - b.id,
  )
  const counts = list.reduce((acc, s) => ({ ...acc, [s.status]: (acc[s.status] ?? 0) + 1 }), {})
  const working = list.filter((s) => isBusy(s.status)).length

  return (
    <>
      <AppBar
        title={worksheet.data.title}
        subtitle={`${worksheet.data.questions.length} questions`}
        back="/check"
        actions={
          <Link className="icon-btn" to={`/print/worksheet/${worksheetId}`} aria-label="Print worksheet">
            <Icon name="print" />
          </Link>
        }
      />
      <Page>
        <PhotoPicker onUpload={upload} uploading={uploading} />

        {list.length > 0 && (
          <div className="row wrap">
            {counts.needs_review > 0 && <span className="badge warn">{counts.needs_review} to check</span>}
            {counts.graded > 0 && <span className="badge warn">{counts.graded} to approve</span>}
            {working > 0 && <span className="badge info busy"><span className="dot" />{working} in progress</span>}
            {counts.approved > 0 && <span className="badge ok">{counts.approved} approved</span>}
            <span className="grow" />
            <Link className="btn small" to={`/class/worksheets/${worksheetId}`}>
              <Icon name="chart" size={18} /> Class results
            </Link>
          </div>
        )}

        {subs.error && <ErrorState message={subs.error} onRetry={subs.reload} />}
        {subs.data && list.length === 0 && (
          <div className="card">
            <EmptyState icon="image" title="No sheets yet">
              Photograph the students' worksheets and ChalkBox will read and mark them.
            </EmptyState>
          </div>
        )}
        {list.length > 0 && (
          <ul className="card flush list">
            {list.map((s) => (
              <li key={s.id}>
                <ListLink
                  to={`/submissions/${s.id}`}
                  leading={
                    <img
                      src={api.submissionImageUrl(s.id)}
                      alt=""
                      loading="lazy"
                      style={{ width: 40, height: 52, objectFit: 'cover', borderRadius: 8, border: '1px solid var(--border)', flex: 'none' }}
                    />
                  }
                  title={s.student_name || s.student_name_read || `Sheet ${s.id}`}
                  meta={s.score_total ? `Score ${scoreText(s)}` : isBusy(s.status) ? 'ChalkBox is working on it' : ''}
                  trailing={<StatusBadge status={s.status} />}
                />
              </li>
            ))}
          </ul>
        )}
      </Page>
    </>
  )
}
