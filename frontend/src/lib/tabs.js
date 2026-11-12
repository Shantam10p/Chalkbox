// Bottom navigation for each kind of account.

export const TEACHER_TABS = [
  { to: '/', label: 'Today', icon: 'home', end: true },
  { to: '/plan', label: 'Plan', icon: 'plan' },
  { to: '/check', label: 'Check', icon: 'camera' },
  { to: '/class', label: 'Class', icon: 'class' },
  { to: '/reports', label: 'Reports', icon: 'report' },
]

export const STUDENT_TABS = [
  { to: '/', label: 'My work', icon: 'home', end: true },
  { to: '/practice', label: 'Practice', icon: 'book' },
  { to: '/progress', label: 'Progress', icon: 'chart' },
]
