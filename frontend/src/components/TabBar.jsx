import { NavLink } from 'react-router-dom'
import { TEACHER_TABS } from '../lib/tabs.js'
import Icon from './Icon.jsx'

export default function TabBar({ tabs = TEACHER_TABS }) {
  return (
    <nav className="tabbar no-print" aria-label="Main">
      <div className="tabbar-inner" style={{ gridTemplateColumns: `repeat(${tabs.length}, 1fr)` }}>
        {tabs.map((tab) => (
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
