import { NavLink } from 'react-router-dom'
import { Shield, List, Activity } from 'lucide-react'

const links = [
  { to: '/', label: 'Dashboard', icon: Activity },
  { to: '/findings', label: 'Findings', icon: List },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col min-h-screen">
      <div className="p-5 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-emerald-400" />
          <span className="text-lg font-semibold">CloudGuard</span>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                isActive
                  ? 'bg-emerald-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`
            }
          >
            <Icon className="w-4 h-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
