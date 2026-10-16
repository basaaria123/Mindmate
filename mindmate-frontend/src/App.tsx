import { useState, type CSSProperties } from 'react'
import {
  Activity,
  Bell,
  Bookmark,
  ChartNoAxesColumn,
  CheckSquare,
  ChevronRight,
  Clock3,
  Home,
  Menu,
  PanelLeft,
  Plus,
  ScanSearch,
  Search,
  Settings,
  Sparkles,
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
import SettingsPage from './pages/Settings'
import Onboarding from './pages/Onboarding'
import Assistant from './pages/Assistant'
import { GlassThemeToggle, ThemeProvider } from './ThemeContext'
import mindmateWordmark from './assets/mindmate-wordmark.svg'
import mindmateIntroEmblem from './assets/mindmate-intro-emblem.png'

const screens = [
  { path: '/boot', label: 'Home', icon: Home },
  { path: '/sim', label: 'Tasks & Practice', icon: CheckSquare },
  { path: '/pipeline', label: 'Plan & Progress', icon: ChartNoAxesColumn },
  { path: '/console', label: 'AI Activity', icon: Sparkles },
  { path: '/memory', label: 'My Memory', icon: Bookmark },
  { path: '/gap-map', label: 'Skill Gaps', icon: Activity },
  { path: '/scanner', label: 'Opportunities', icon: ScanSearch },
  { path: '/trace', label: 'Activity History', icon: Clock3 },
  { path: '/settings', label: 'Settings', icon: Settings },
]

function AppLayout() {
  const location = useLocation()
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const currentScreen =
    screens.find((screen) => screen.path === location.pathname) ?? screens[0]
  const activeScreenIndex = Math.max(
    screens.findIndex((screen) => screen.path === currentScreen.path),
    0,
  )

  if (location.pathname === '/assistant') {
    return <Assistant />
  }

  return (
    <div className="app-shell min-h-screen bg-[#f1efff] p-2 text-[#211d54]">
      <div className="flex min-h-[calc(100vh-16px)] overflow-hidden rounded-2xl border border-violet-200 bg-[#f7f5ff] shadow-sm">
        {mobileNavOpen && (
          <button
            type="button"
            aria-label="Close navigation menu"
            className="fixed inset-0 top-16 z-40 bg-black/30 md:hidden"
            onClick={() => setMobileNavOpen(false)}
          />
        )}

        <aside
          className={`${
            mobileNavOpen
              ? 'fixed inset-y-2 left-2 z-50 flex w-[186px] rounded-l-2xl'
              : 'hidden'
          } ${
            sidebarCollapsed && !mobileNavOpen
              ? 'md:w-[68px]'
              : 'md:w-[208px]'
          } shrink-0 border-r border-violet-100 bg-white px-2.5 pb-3 pt-4 md:sticky md:top-2 md:h-[calc(100vh-16px)] md:flex md:flex-col`}
        >
          <div
            className={`flex h-12 items-center overflow-hidden ${
              sidebarCollapsed && !mobileNavOpen
                ? 'justify-center'
                : 'gap-1'
            }`}
          >
            <img
              src={mindmateIntroEmblem}
              alt="MindMate"
              className="h-10 w-10 shrink-0 rounded-full object-cover"
            />

            {(!sidebarCollapsed || mobileNavOpen) && (
              <img
                src={mindmateWordmark}
                alt="MindMate"
                className="h-8 min-w-0 flex-1 object-contain object-left"
              />
            )}

            {(!sidebarCollapsed || mobileNavOpen) && (
              <button
                type="button"
                aria-label="Collapse sidebar"
                aria-expanded={!sidebarCollapsed}
                onClick={() => setSidebarCollapsed(true)}
                className="hidden size-8 shrink-0 place-items-center rounded-lg text-violet-500 hover:bg-violet-50 md:grid"
              >
                <PanelLeft size={19} />
              </button>
            )}
          </div>

          <div
            className="mm-screen-nav mt-4"
            data-collapsed={sidebarCollapsed && !mobileNavOpen}
            style={{ '--mm-active-screen': activeScreenIndex } as CSSProperties}
          >
            <span className="mm-screen-nav__bubble" aria-hidden="true">
              <span className="mm-screen-nav__shine" />
            </span>
            <nav className="space-y-1" aria-label="Main navigation">
              {screens.map(({ path, label, icon: Icon }) => (
              <NavLink
                key={path}
                title={
                  sidebarCollapsed && !mobileNavOpen ? label : undefined
                }
                to={path}
                onClick={() => setMobileNavOpen(false)}
                className={({ isActive }) =>
                  `relative z-[1] flex h-[42px] items-center rounded-xl text-[13px] transition-colors duration-300 ${
                    sidebarCollapsed && !mobileNavOpen
                      ? 'mx-auto w-[44px] justify-center px-0'
                      : 'gap-2.5 px-2'
                  } ${
                    isActive
                      ? 'text-white'
                      : 'text-[#5f638d] hover:bg-violet-50 hover:text-violet-700'
                  }`
                }
              >
                <Icon size={18} />
                {(!sidebarCollapsed || mobileNavOpen) && <span>{label}</span>}
              </NavLink>
              ))}
            </nav>
          </div>

          <div className="mt-auto">
            {sidebarCollapsed && !mobileNavOpen && (
              <button
                type="button"
                aria-label="Expand sidebar"
                title="Expand sidebar"
                onClick={() => setSidebarCollapsed(false)}
                className="mx-auto mb-2 grid size-9 place-items-center rounded-lg text-violet-500 hover:bg-violet-50"
              >
                <PanelLeft size={18} />
              </button>
            )}

            {sidebarCollapsed && !mobileNavOpen && (
              <div className="border-t border-violet-100 pt-3">
                <button
                  type="button"
                  aria-label="Expand sidebar"
                  title="Expand sidebar"
                  onClick={() => setSidebarCollapsed(false)}
                  className="mx-auto grid size-10 place-items-center rounded-xl bg-violet-50 text-violet-600 hover:bg-violet-100"
                >
                  <ChevronRight size={19} />
                </button>
              </div>
            )}

            {(!sidebarCollapsed || mobileNavOpen) && (
              <div className="border-t border-violet-100 pt-3">
                <NavLink
                  to="/assistant"
                  className="flex h-[52px] items-center gap-2 rounded-xl bg-[#f1edff] px-2 text-violet-800 hover:bg-[#e9e2ff]"
                >
                  <span className="grid size-9 place-items-center rounded-xl bg-violet-100">
                    <img
                      src={mindmateIntroEmblem}
                      alt=""
                      className="size-8 rounded-full object-cover"
                    />
                  </span>

                  <span className="min-w-0 flex-1">
                    <strong className="block text-xs">AI Assistant</strong>
                    <small className="block text-[10px] text-violet-500">
                      Ask anything
                    </small>
                  </span>

                  <ChevronRight size={16} />
                </NavLink>
              </div>
            )}
          </div>
        </aside>

        <div className="flex min-w-0 flex-1 flex-col">
          <header
            className={`mm-workspace-header relative z-20 flex h-[82px] shrink-0 items-center justify-between gap-4 border-b border-violet-100 bg-gradient-to-r from-[#fbfaff] to-[#f0edff] ${
              location.pathname === '/memory' ? 'px-[31px]' : 'px-[27px]'
            }`}
          >
            <button
              type="button"
              aria-label={mobileNavOpen ? 'Close menu' : 'Open menu'}
              aria-expanded={mobileNavOpen}
              className="rounded-lg p-2 text-violet-600 hover:bg-white md:hidden"
              onClick={() => setMobileNavOpen((open) => !open)}
            >
              {mobileNavOpen ? <X size={19} /> : <Menu size={19} />}
            </button>

            {location.pathname === '/pipeline' ||
            location.pathname === '/console' ||
            location.pathname === '/memory' ||
            location.pathname === '/gap-map' ||
            location.pathname === '/scanner' ||
            location.pathname === '/trace' ? (
              <div
                className={`min-w-0 ${
                  location.pathname === '/memory'
                    ? 'translate-y-[18px]'
                    : 'translate-y-[22px]'
                }`}
              >
                <h1
                  className={`font-bold leading-tight text-[#211e58] ${
                    location.pathname === '/memory'
                      ? 'text-[29px]'
                      : 'text-[27px]'
                  }`}
                >
                  {location.pathname === '/pipeline'
                    ? 'Plan & Progress'
                    : location.pathname === '/console'
                      ? 'AI Activity'
                      : location.pathname === '/memory'
                        ? 'My Memory'
                        : location.pathname === '/gap-map'
                          ? 'Skill Gaps'
                          : location.pathname === '/scanner'
                            ? 'Opportunities'
                            : 'Activity History'}
                </h1>

                <p
                  className={`mt-1 text-[#646b9d] ${
                    location.pathname === '/memory'
                      ? 'text-[15px]'
                      : 'text-sm'
                  }`}
                >
                  {location.pathname === '/pipeline'
                    ? 'See your stages and next steps clearly.'
                    : location.pathname === '/console'
                      ? 'See what the AI is doing, in real time.'
                      : location.pathname === '/memory'
                        ? 'Your saved info, preferences and insights.'
                        : location.pathname === '/gap-map'
                          ? 'Find what to improve and get next steps.'
                          : location.pathname === '/scanner'
                            ? 'Discover relevant jobs, projects and more.'
                            : 'Review your past tasks and AI actions.'}
                </p>
              </div>
            ) : (
              <label className="flex h-[44px] w-full max-w-[440px] items-center gap-2 rounded-full border border-violet-200 bg-white/80 px-4 text-[#8187b5] shadow-[0_1px_3px_rgba(74,55,150,.04)]">
                <Search size={17} />
                <input
                  className="w-full bg-transparent text-sm outline-none placeholder:text-[#898eb8]"
                  placeholder="Search anything..."
                  aria-label="Search anything"
                />
              </label>
            )}

            <div className="flex shrink-0 items-center gap-4">
              {location.pathname === '/sim' && (
                <button
                  type="button"
                  onClick={() =>
                    window.dispatchEvent(new Event('mindmate:new-task'))
                  }
                  className="hidden h-10 items-center gap-2 rounded-2xl bg-gradient-to-r from-[#8237ef] to-[#5f64f2] px-4 text-sm font-semibold text-white shadow-sm hover:brightness-105 sm:inline-flex"
                >
                  <Plus size={19} />
                  New Task
                </button>
              )}

              <button
                type="button"
                aria-label="Notifications"
                className="relative grid size-[38px] place-items-center rounded-full border border-violet-100 bg-white/85 p-2 text-[#6256ed] shadow-sm transition hover:bg-violet-50 hover:text-violet-800"
              >
                <Bell size={21} />
                <span className="absolute right-1.5 top-1.5 size-2 rounded-full border border-white bg-rose-500" />
              </button>

              <div aria-label="Signed in profile" className="grid size-[38px] place-items-center rounded-full border-2 border-white bg-gradient-to-br from-[#a288ff] to-[#7658f6] text-sm font-semibold text-white shadow-md">
                S
              </div>

              <GlassThemeToggle />
            </div>
          </header>

          <main
            className={`min-h-0 flex-1 bg-[#f4f2ff] pb-[22px] ${
              location.pathname === '/memory'
                ? 'px-3 pt-[63px] md:px-[31px]'
                : location.pathname === '/pipeline' ||
                    location.pathname === '/console' ||
                    location.pathname === '/gap-map' ||
                    location.pathname === '/scanner' ||
                    location.pathname === '/trace'
                  ? 'px-3 pt-[63px] md:px-[27px]'
                  : location.pathname === '/settings'
                    ? 'px-3 pt-[36px] md:px-[27px]'
                  : location.pathname === '/sim'
                    ? 'px-3 pt-[6px] md:px-[27px]'
                    : 'px-3 pt-[10px] md:px-[20px]'
            }`}
          >
            <div className="sr-only" aria-live="polite">
              {currentScreen.label}
            </div>

            <Routes>
              <Route path="/" element={<Navigate to="/welcome" replace />} />
              <Route path="/boot" element={<Boot />} />
              <Route path="/console" element={<Console />} />
              <Route path="/memory" element={<Memory />} />
              <Route path="/scanner" element={<Scanner />} />
              <Route path="/gap-map" element={<GapMap />} />
              <Route path="/pipeline" element={<Pipeline />} />
              <Route path="/sim" element={<Sim />} />
              <Route path="/trace" element={<Trace />} />
              <Route path="/settings" element={<SettingsPage />} />
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
    <ThemeProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </ThemeProvider>
  )
}

function AppRoutes() {
  const location = useLocation()

  if (location.pathname === '/welcome') {
    return <Onboarding />
  }

  return <AppLayout />
}

export default App
