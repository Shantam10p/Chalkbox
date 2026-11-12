import { Outlet, Route, Routes } from 'react-router-dom'
import { AuthProvider, useAuth } from './components/AuthContext.jsx'
import { ClassProvider } from './components/ClassContext.jsx'
import TabBar from './components/TabBar.jsx'
import { STUDENT_TABS, TEACHER_TABS } from './lib/tabs.js'
import { ToastProvider } from './components/Toast.jsx'
import { AppBar, EmptyState, Loading, Page } from './components/ui.jsx'
import CheckHome from './screens/CheckHome.jsx'
import ClassHome from './screens/ClassHome.jsx'
import Home from './screens/Home.jsx'
import LessonDetail from './screens/LessonDetail.jsx'
import Login from './screens/Login.jsx'
import PlanList from './screens/PlanList.jsx'
import PlanNew from './screens/PlanNew.jsx'
import PracticeList from './screens/PracticeList.jsx'
import { PrintPractice, PrintReports, PrintWorksheet } from './screens/Print.jsx'
import Reports from './screens/Reports.jsx'
import StudentProfile from './screens/StudentProfile.jsx'
import SubmissionDetail from './screens/SubmissionDetail.jsx'
import WorksheetCheck from './screens/WorksheetCheck.jsx'
import WorksheetSummary from './screens/WorksheetSummary.jsx'
import StudentAsk from './student/StudentAsk.jsx'
import { StudentHome, StudentPractice, StudentProgress, StudentWork } from './student/StudentScreens.jsx'

function Shell({ tabs }) {
  return (
    <div className="shell">
      <Outlet />
      <TabBar tabs={tabs} />
    </div>
  )
}

function NotFound() {
  return (
    <>
      <AppBar title="Not found" back="/" />
      <Page>
        <div className="card">
          <EmptyState icon="alert" title="This page doesn't exist" />
        </div>
      </Page>
    </>
  )
}

function TeacherApp() {
  return (
    <ClassProvider>
      <Routes>
        <Route element={<Shell tabs={TEACHER_TABS} />}>
          <Route index element={<Home />} />
          <Route path="plan" element={<PlanList />} />
          <Route path="plan/new" element={<PlanNew />} />
          <Route path="plan/:lessonId" element={<LessonDetail />} />
          <Route path="check" element={<CheckHome />} />
          <Route path="check/:worksheetId" element={<WorksheetCheck />} />
          <Route path="submissions/:submissionId" element={<SubmissionDetail />} />
          <Route path="class" element={<ClassHome />} />
          <Route path="class/worksheets/:worksheetId" element={<WorksheetSummary />} />
          <Route path="class/worksheets/:worksheetId/practice" element={<PracticeList />} />
          <Route path="class/students/:studentId" element={<StudentProfile />} />
          <Route path="reports" element={<Reports />} />
          <Route path="*" element={<NotFound />} />
        </Route>
        <Route path="print/worksheet/:worksheetId" element={<PrintWorksheet />} />
        <Route path="print/practice/:worksheetId" element={<PrintPractice />} />
        <Route path="print/reports" element={<PrintReports />} />
      </Routes>
    </ClassProvider>
  )
}

function StudentApp() {
  return (
    <Routes>
      <Route element={<Shell tabs={STUDENT_TABS} />}>
        <Route index element={<StudentHome />} />
        <Route path="work/:submissionId" element={<StudentWork />} />
        <Route path="ask" element={<StudentAsk />} />
        <Route path="practice" element={<StudentPractice />} />
        <Route path="progress" element={<StudentProgress />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

// Shows the sign-in screen, or the teacher or student app depending on who signed in.
function Gate() {
  const { user, checking } = useAuth()
  if (checking) return <Loading label="Opening ChalkBox…" />
  if (!user) return <Login />
  // `key` resets every screen's state when a different person signs in.
  return user.role === 'teacher' ? <TeacherApp key={user.id} /> : <StudentApp key={user.id} />
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Gate />
      </AuthProvider>
    </ToastProvider>
  )
}
