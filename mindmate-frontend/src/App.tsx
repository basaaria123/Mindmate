import { useState } from 'react'
import {
  Activity,
  Bell,
  Brain,
  ChevronRight,
  Dumbbell,
  GitBranch,
  Home,
  Map,
  Menu,
  ScanSearch,
  Search,
  Terminal,
  Workflow,
  X,
} from 'lucide-react'
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from 'react-router'
import Boot from './pages/Boot'
import Console from './pages/Console'
import GapMap from './pages/GapMap'
import Memory from './pages/Memory'
import Pipeline from './pages/Pipeline'
import Scanner from './pages/Scanner'
import Sim from './pages/Sim'
import Trace from './pages/Trace'

const screens = [
  { path: '/boot', label: 'Boot', icon: Home },
  { path: '/console', label: 'Console', icon: Terminal },
  { path: '/memory', label: 'Memory', icon: Brain },
  { path: '/scanner', label: 'Scanner', icon: ScanSearch },
  { path: '/gap-map', label: 'Gap Map', icon: Map },
  { path: '/pipeline', label: 'Pipeline', icon: Workflow },
  { path: '/sim', label: 'Sim', icon: Dumbbell },
  { path: '/trace', label: 'Trace', icon: GitBranch },
]

function AppLayout() {
  const location = useLocation()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  const currentScreen =
    screens.find((screen) => screen.path === location.pathname) ?? screens[0]

  return (
    <div
      className="min-h-screen text-slate-100"
      style={{
        backgroundColor: '#080B18',
        backgroundImage:
          'radial-gradient(ellipse 48% 78% at 100% 12%, rgba(196,181,253,0.82) 0%, rgba(109,90,230,0.46) 28%, rgba(8,11,24,0) 72%), linear-gradient(145deg, transparent 0%, transparent 67%, rgba(255,255,255,0.76) 76%, rgba(167,139,250,0.28) 84%, transparent 92%), linear-gradient(180deg, #080B18 0%, #0B1022 100%)',
        backgroundAttachment: 'fixed',
      }}
    >
      <div className="flex min-h-screen">
        {mobileNavOpen && (
          <button
            type="button"
            aria-label="Close navigation menu"
            className="fixed inset-0 top-16 z-40 bg-black/60 md:hidden"
            onClick={() => setMobileNavOpen(false)}
          />
        )}

        <aside
          className={`${
            mobileNavOpen
              ? 'fixed inset-y-16 left-0 z-50 flex w-64'
              : 'hidden'
          } shrink-0 border-r border-slate-800 bg-[#0c111c] p-4 md:static md:flex md:w-64 md:flex-col`}
        >
          <div className="flex items-center gap-3 px-2 py-3">
            <div className="grid size-10 place-items-center rounded-xl bg-[#A78BFA] text-slate-950">
              <Activity size={21} />
            </div>

            <div>
              <p className="font-bold tracking-[0.18em] text-white">
                MINDMATE
              </p>
              <p className="text-xs text-slate-500">Learning system</p>
            </div>
          </div>

          <p className="mb-3 mt-9 px-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            Workspace
          </p>

          <nav className="space-y-1" aria-label="Main navigation">
            {screens.map((screen) => {
              const Icon = screen.icon

              return (
                <NavLink
                  key={screen.path}
                  to={screen.path}
                  onClick={() => setMobileNavOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                      isActive
                        ? 'bg-violet-400/10 text-violet-300'
                        : 'text-slate-400 hover:bg-slate-800/70 hover:text-white'
                    }`
                  }
                >
                  <Icon size={17} />
                  <span>{screen.label}</span>
                </NavLink>
              )
            })}
          </nav>

          <div className="mt-auto rounded-xl border border-slate-800 bg-slate-900/70 p-4">
            <p className="text-xs font-medium text-slate-300">Local preview</p>
            <p className="mt-1 text-xs text-slate-500">
              Frontend development mode
            </p>
            <div className="mt-3 flex items-center gap-2 text-xs text-emerald-300">
              <span className="size-2 rounded-full bg-emerald-400" />
              Connected
            </div>
          </div>
        </aside>

        <div className="min-w-0 flex-1">
          <header className="relative z-20 flex h-16 items-center justify-between border-b border-slate-800 bg-[#0c111c]/95 px-4 sm:px-8">
            <div className="flex items-center gap-3">
              <button
                type="button"
                aria-label={mobileNavOpen ? 'Close menu' : 'Open menu'}
                aria-expanded={mobileNavOpen}
                className="rounded-lg border border-slate-800 p-2 text-slate-300 hover:bg-slate-800 md:hidden"
                onClick={() => setMobileNavOpen((open) => !open)}
              >
                {mobileNavOpen ? <X size={18} /> : <Menu size={18} />}
              </button>

              <span className="text-sm text-slate-500">MINDMATE</span>
              <ChevronRight size={14} className="text-slate-600" />
              <span className="text-sm font-medium text-slate-200">
                {currentScreen.label}
              </span>
            </div>

            <div className="flex items-center gap-3">
              <div className="hidden items-center gap-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2 text-xs text-slate-500 sm:flex">
                <Search size={14} />
                <span>Search workspace</span>
              </div>

              <button
                className="rounded-lg border border-slate-800 p-2 text-slate-400 hover:bg-slate-800"
                type="button"
                aria-label="Notifications"
              >
                <Bell size={17} />
              </button>

              <div className="grid size-8 place-items-center rounded-full bg-violet-400/20 text-xs font-semibold text-violet-200">
                M
              </div>
            </div>
          </header>

          <main className="p-5 sm:p-8">
            <Routes>
              <Route path="/" element={<Navigate to="/boot" replace />} />
              <Route path="/boot" element={<Boot />} />
              <Route path="/console" element={<Console />} />
              <Route path="/memory" element={<Memory />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/gap-map" element={<GapMap />} />
              <Route path="/pipeline" element={<Pipeline />} />
              <Route path="/sim" element={<Sim />} />
              <Route path="/trace" element={<Trace />} />
              <Route path="*" element={<Navigate to="/boot" replace />} />
            </Routes>
          </main>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  )
}

export default App