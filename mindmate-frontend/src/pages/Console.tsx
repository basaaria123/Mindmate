import {
  Activity,
  CheckCircle2,
  Clock3,
  Cpu,
  Wifi,
  Zap,
} from 'lucide-react'

const activityItems = [
  {
    time: 'Just now',
    title: 'Frontend workspace started',
    detail: 'MINDMATE local preview is available',
    icon: CheckCircle2,
    color: 'text-emerald-300',
  },
  {
    time: 'A moment ago',
    title: 'Navigation is ready',
    detail: 'Eight workspace screens are registered',
    icon: Activity,
    color: 'text-cyan-300',
  },
  {
    time: 'A moment ago',
    title: 'Mock data mode enabled',
    detail: 'Screen content is using sample data',
    icon: Zap,
    color: 'text-amber-300',
  },
]

function Console() {
  return (
    <div className="mx-auto max-w-6xl">
      <div className="mb-8">
        <p className="text-sm font-medium uppercase tracking-[0.18em] text-cyan-300">
          System monitor
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight text-white">
          Console
        </h1>
        <p className="mt-2 text-sm text-slate-400">
          A local overview of the MINDMATE frontend and its current activity.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Frontend</p>
            <Activity size={18} className="text-emerald-300" />
          </div>
          <p className="mt-4 text-xl font-semibold text-white">Running</p>
          <p className="mt-1 text-xs text-slate-500">Local development server</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Data source</p>
            <Cpu size={18} className="text-violet-300" />
          </div>
          <p className="mt-4 text-xl font-semibold text-white">Mock data</p>
          <p className="mt-1 text-xs text-slate-500">Backend connection comes later</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Connection</p>
            <Wifi size={18} className="text-cyan-300" />
          </div>
          <p className="mt-4 text-xl font-semibold text-white">Local only</p>
          <p className="mt-1 text-xs text-slate-500">This preview runs on your computer</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Recent events</p>
            <Clock3 size={18} className="text-amber-300" />
          </div>
          <p className="mt-4 text-xl font-semibold text-white">3</p>
          <p className="mt-1 text-xs text-slate-500">Sample events shown below</p>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900/50">
        <div className="border-b border-slate-800 px-5 py-4">
          <h2 className="font-semibold text-white">Activity log</h2>
          <p className="mt-1 text-sm text-slate-400">
            Example events for the local frontend preview.
          </p>
        </div>

        <div className="divide-y divide-slate-800">
          {activityItems.map((item) => {
            const Icon = item.icon

            return (
              <div
                key={item.title}
                className="flex items-start gap-4 px-5 py-5"
              >
                <Icon size={19} className={`mt-0.5 ${item.color}`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-slate-200">
                    {item.title}
                  </p>
                  <p className="mt-1 text-sm text-slate-400">{item.detail}</p>
                </div>
                <span className="shrink-0 text-xs text-slate-500">{item.time}</span>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}

export default Console