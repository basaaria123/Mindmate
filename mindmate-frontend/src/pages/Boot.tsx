import {
  ArrowRight,
  BookOpen,
  Brain,
  CirclePlay,
  Target,
  TrendingUp,
} from 'lucide-react'
import { Link } from 'react-router'

const quickLinks = [
  {
    label: 'Practice',
    description: 'Try a practice question',
    path: '/sim',
    icon: CirclePlay,
  },
  {
    label: 'Review memory',
    description: 'See what MINDMATE has learned',
    path: '/memory',
    icon: Brain,
  },
  {
    label: 'View skill gaps',
    description: 'Explore areas to strengthen',
    path: '/gap-map',
    icon: Target,
  },
]

function Boot() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="text-sm font-medium text-violet-300">WEDNESDAY · YOUR WORKSPACE</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Welcome to MINDMATE
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400">
          Your learning workspace is ready. Start with a practice session, review
          your learning memory, or explore your skill map.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Learning plan</p>
            <BookOpen size={18} className="text-violet-300" />
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">Not started</p>
          <p className="mt-1 text-xs text-slate-500">Your plan will appear here</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Skills tracked</p>
            <Target size={18} className="text-violet-300" />
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">0</p>
          <p className="mt-1 text-xs text-slate-500">Skills in your profile</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Practice sessions</p>
            <CirclePlay size={18} className="text-emerald-300" />
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">0</p>
          <p className="mt-1 text-xs text-slate-500">Sessions completed</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Recent progress</p>
            <TrendingUp size={18} className="text-amber-300" />
          </div>
          <p className="mt-4 text-2xl font-semibold text-white">—</p>
          <p className="mt-1 text-xs text-slate-500">Complete a session to begin</p>
        </div>
      </section>

      <section className="mt-8">
        <div className="mb-4">
          <h2 className="text-lg font-semibold text-white">Quick actions</h2>
          <p className="mt-1 text-sm text-slate-400">
            Choose where you want to start.
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          {quickLinks.map((item) => {
            const Icon = item.icon

            return (
              <Link
                key={item.path}
                to={item.path}
                className="group flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900/50 p-5 transition hover:border-violet-300/40 hover:bg-slate-900"
              >
                <div className="flex items-center gap-4">
                  <div className="rounded-xl bg-slate-800 p-3 text-violet-300">
                    <Icon size={20} />
                  </div>
                  <div>
                    <p className="font-medium text-white">{item.label}</p>
                    <p className="mt-1 text-sm text-slate-400">{item.description}</p>
                  </div>
                </div>
                <ArrowRight
                  size={18}
                  className="text-slate-500 transition group-hover:translate-x-1 group-hover:text-violet-300"
                />
              </Link>
            )
          })}
        </div>
      </section>
    </div>
  )
}

export default Boot