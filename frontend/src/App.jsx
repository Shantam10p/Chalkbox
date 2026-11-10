import { Outlet, Route, Routes } from 'react-router-dom'
import { ClassProvider } from './components/ClassContext.jsx'
import TabBar from './components/TabBar.jsx'
import { ToastProvider } from './components/Toast.jsx'
import { AppBar, EmptyState, Page } from './components/ui.jsx'
import CheckHome from './screens/CheckHome.jsx'
import ClassHome from './screens/ClassHome.jsx'
import Home from './screens/Home.jsx'
import LessonDetail from './screens/LessonDetail.jsx'
import PlanList from './screens/PlanList.jsx'
import PlanNew from './screens/PlanNew.jsx'
import PracticeList from './screens/PracticeList.jsx'
import { PrintPractice, PrintReports, PrintWorksheet } from './screens/Print.jsx'
import Reports from './screens/Reports.jsx'
import StudentProfile from './screens/StudentProfile.jsx'
import SubmissionDetail from './screens/SubmissionDetail.jsx'
import WorksheetCheck from './screens/WorksheetCheck.jsx'
import WorksheetSummary from './screens/WorksheetSummary.jsx'

function Shell() {
  return (
    <div className="shell">
      <Outlet />
      <TabBar />
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

export default function App() {
  return (
    <ToastProvider>
      <ClassProvider>
        <Routes>
          <Route element={<Shell />}>
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
    </ToastProvider>
  )
}
