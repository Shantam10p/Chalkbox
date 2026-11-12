// Thin wrapper around the ChalkBox hub API. Every screen talks to the hub through this file.

async function request(method, path, body) {
  const options = { method, headers: {} }
  if (body instanceof FormData) {
    options.body = body
  } else if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }
  const response = await fetch(`/api${path}`, options)
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    // A session that expired mid-use sends the app back to the sign-in screen.
    if (response.status === 401 && !path.startsWith('/auth/')) {
      window.dispatchEvent(new Event('chalkbox:signed-out'))
    }
    const detail = data?.detail
    const error = new Error(typeof detail === 'string' ? detail : `Request failed (${response.status})`)
    error.status = response.status
    throw error
  }
  return data
}

const get = (path) => request('GET', path)
const post = (path, body = {}) => request('POST', path, body)

export const api = {
  status: () => get('/status'),

  // Sign in / out
  me: () => get('/auth/me'),
  login: (username, password) => post('/auth/login', { username, password }),
  logout: () => post('/auth/logout'),

  // Student's own work (student accounts only)
  myOverview: () => get('/me'),
  myWork: () => get('/me/work'),
  myWorkDetail: (id) => get(`/me/work/${id}`),
  myWorkImageUrl: (id) => `/api/me/work/${id}/image`,
  myPractice: () => get('/me/practice'),
  myProgress: () => get('/me/progress'),
  helperHistory: () => get('/me/helper'),
  askHelper: (message) => post('/me/helper', { message }),
  studentHelperChats: (studentId) => get(`/students/${studentId}/helper`),

  // Classes and students
  classes: () => get('/classes'),
  class: (id) => get(`/classes/${id}`),
  studentProfile: (id) => get(`/students/${id}/profile`),

  // Worksheets and the Check flow
  worksheet: (id) => get(`/worksheets/${id}`),
  worksheetSummary: (id) => get(`/worksheets/${id}/summary`),
  submissions: (worksheetId) => get(`/worksheets/${worksheetId}/submissions`),
  uploadPhotos: (worksheetId, files) => {
    const form = new FormData()
    for (const file of files) form.append('files', file)
    return post(`/worksheets/${worksheetId}/submissions`, form)
  },
  submission: (id) => get(`/submissions/${id}`),
  submissionImageUrl: (id) => `/api/submissions/${id}/image`,
  reviewSubmission: (id, corrections) => post(`/submissions/${id}/review`, { corrections }),
  approveSubmission: (id, changes = {}) => post(`/submissions/${id}/approve`, changes),
  retrySubmission: (id) => post(`/submissions/${id}/retry`),

  // Lessons (Plan flow)
  lessons: (classId) => get(`/lessons?class_id=${classId}`),
  lesson: (id) => get(`/lessons/${id}`),
  createLesson: (body) => post('/lessons', body),
  approveLesson: (id, edits = {}) => post(`/lessons/${id}/approve`, edits),
  retryLesson: (id) => post(`/lessons/${id}/retry`),
  deleteLesson: (id) => request('DELETE', `/lessons/${id}`),

  // Follow-up: practice sheets and parent reports
  practiceSheets: (worksheetId) => get(`/worksheets/${worksheetId}/practice`),
  createPractice: (worksheetId, body = {}) => post(`/worksheets/${worksheetId}/practice`, body),
  approvePractice: (id, edits = {}) => post(`/practice/${id}/approve`, edits),
  reports: (classId) => get(`/classes/${classId}/reports`),
  createReports: (classId, body = {}) => post(`/classes/${classId}/reports`, body),
  approveReport: (id, edits = {}) => post(`/reports/${id}/approve`, edits),
}
