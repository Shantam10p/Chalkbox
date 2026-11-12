import { NavLink } from 'react-router-dom'
import { TEACHER_TABS } from '../lib/tabs.js'
import Icon from './Icon.jsx'

// Bottom tab bar on phones; a left navigation rail (with the brand) from 960px up.
export default function TabBar({ tabs = TEACHER_TABS }) {
  return (
    <nav className="tabbar no-print" aria-label="Main">
      <div className="tabbar-inner">
        <span className="rail-brand brand" aria-hidden="true">ChalkBox</span>
        {tabs.map((tab) => (
          <NavLink key={tab.to} to={tab.to} end={tab.end}>
            <span className="tab-icon">
              <Icon name={tab.icon} size={21} strokeWidth={1.8} />
            </span>
            {tab.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
