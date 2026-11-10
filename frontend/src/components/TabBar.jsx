import { NavLink } from 'react-router-dom'
import Icon from './Icon.jsx'

const TABS = [
  { to: '/', label: 'Today', icon: 'home', end: true },
  { to: '/plan', label: 'Plan', icon: 'plan' },
  { to: '/check', label: 'Check', icon: 'camera' },
  { to: '/class', label: 'Class', icon: 'class' },
  { to: '/reports', label: 'Reports', icon: 'report' },
]

export default function TabBar() {
  return (
    <nav className="tabbar no-print" aria-label="Main">
      <div className="tabbar-inner">
        {TABS.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.end}>
            <span className="tab-icon">
              <Icon name={tab.icon} size={22} />
            </span>
            {tab.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
