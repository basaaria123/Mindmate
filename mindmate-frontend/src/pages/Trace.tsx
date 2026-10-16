import { useEffect, useMemo, useState } from 'react'
import { Check, Sparkles } from 'lucide-react'
import { getTraceEvents } from '../services/api'
import type { DemoEvent } from '../services/demoState'

type ActivityCategory = 'Tasks' | 'AI Activity' | 'Plans'
type ActivityItem = {
  title: string
  time: string
  category: ActivityCategory
  state: 'complete' | 'ai' | 'upcoming'
}

const filters = ['All', 'Tasks', 'AI Activity', 'Plans'] as const
type ActivityFilter = (typeof filters)[number]

const exampleActivity: ActivityItem[] = [
  {
    title: 'Completed task: Study – Cardiovascular System',
    time: 'Today • 10:00 AM',
    category: 'Tasks',
    state: 'complete',
  },
  {
    title: 'AI generated new plan for you',
    time: 'Today • 9:45 AM',
    category: 'AI Activity',
    state: 'ai',
  },
  {
    title: 'Viewed skill gap: Respiratory System',
    time: 'Yesterday • 8:25 PM',
    category: 'AI Activity',
    state: 'upcoming',
  },
  {
    title: 'Completed task: Practice – Anatomy MCQs',
    time: 'Yesterday • 4:12 PM',
    category: 'Tasks',
    state: 'upcoming',
  },
]

function classifyEvent(event: DemoEvent): ActivityItem {
  const title = event.title.toLowerCase()
  const category: ActivityCategory = title.includes('plan')
    ? 'Plans'
    : title.includes('practice') || title.includes('task')
      ? 'Tasks'
      : 'AI Activity'
  const date = new Date(event.occurredAt)
  const time = Number.isNaN(date.getTime())
    ? 'Recently'
    : `${date.toLocaleDateString()} • ${date.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}`

  return {
    title: event.title,
    time,
    category,
    state: category === 'Plans' ? 'ai' : 'upcoming',
  }
}

function HistoryClock() {
  return (
    <div aria-hidden="true" className="mm-history-clock relative grid size-[210px] place-items-center rounded-full bg-[#eeeaff] shadow-[0_13px_23px_rgba(100,76,191,.13)]">
      <div className="mm-history-clock__mid grid size-[184px] place-items-center rounded-full border-[8px] border-[#d8d1ff] bg-[#f4f1ff] shadow-[inset_0_0_0_3px_#b6aaff]">
        <div className="mm-history-clock__face relative grid size-[144px] place-items-center rounded-full border-[4px] border-[#a79aff] bg-[#f8f7ff] shadow-[0_0_0_3px_rgba(153,137,255,.1)]">
          <span className="absolute left-1/2 top-1/2 h-[43px] w-[8px] -translate-x-1/2 -translate-y-full rotate-[27deg] origin-bottom rounded-full bg-[#7b6bf4]" />
          <span className="absolute left-1/2 top-1/2 h-[39px] w-[8px] -translate-y-1/2 rotate-[112deg] origin-left rounded-full bg-[#7b6bf4]" />
          <span className="absolute left-1/2 top-1/2 size-[12px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#7b6bf4]" />
        </div>
      </div>
    </div>
  )
}

function Trace() {
  const [filter, setFilter] = useState<ActivityFilter>('All')
  const [events, setEvents] = useState<DemoEvent[]>([])

  useEffect(() => {
    let isCurrent = true

    getTraceEvents()
      .then((savedEvents) => {
        if (isCurrent) setEvents([...savedEvents].reverse())
      })
      .catch(() => {
        // The sample activity remains available if local history cannot load.
      })

    return () => {
      isCurrent = false
    }
  }, [])

  const activity = useMemo(() => {
    const savedActivity = events.map(classifyEvent)
    const allActivity = [...exampleActivity, ...savedActivity]
    return filter === 'All'
      ? allActivity
      : allActivity.filter((item) => item.category === filter)
  }, [events, filter])

  return (
    <div className="relative isolate mx-auto w-full max-w-[1120px]">
      <div aria-hidden="true" className="pointer-events-none absolute -right-[96px] -top-[278px] -z-10 size-[260px] rounded-full bg-[#dff8f0]" />
      <div aria-hidden="true" className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff]" />

      <section className="relative min-h-[530px] overflow-hidden rounded-[20px] border border-[#e3dcff] bg-white/80 p-5 shadow-[0_12px_30px_rgba(84,63,175,0.07)]">
        <div role="tablist" aria-label="Activity filters" className="relative z-10 flex flex-wrap gap-[10px]">
          {filters.map((item) => (
            <button
              key={item}
              type="button"
              role="tab"
              aria-selected={filter === item}
              onClick={() => setFilter(item)}
              className={`h-[35px] min-w-[56px] rounded-full px-5 text-[12px] font-semibold transition ${filter === item ? 'bg-[#ded6ff] text-[#6332c7]' : 'bg-[#eef0ff] text-[#7079a6] hover:bg-[#e6e5ff]'}`}
            >
              {item}
            </button>
          ))}
        </div>

        <div className="relative mt-[59px] md:grid md:grid-cols-[minmax(0,1fr)_260px]">
          <ol className="relative z-10">
            <span aria-hidden="true" className="absolute left-[12px] top-[16px] h-[274px] w-[2px] bg-[#d7d0ff]" />
            {activity.map((item, index) => (
              <li key={`${item.title}-${index}`} className="relative flex min-h-[91px] items-start gap-[17px]">
                <span className={`relative z-10 mt-[7px] grid size-[26px] shrink-0 place-items-center rounded-full ${item.state === 'complete' ? 'bg-[#0ecb3c] text-white' : item.state === 'ai' ? 'bg-[#8c39ff] text-white' : 'border-[3px] border-[#4380ff] bg-white'}`}>
                  {item.state === 'complete' && <Check size={16} strokeWidth={3} />}
                  {item.state === 'ai' && <Sparkles size={16} strokeWidth={2.2} />}
                </span>
                <span className="min-w-0 pt-[1px]">
                  <strong className="block text-[15px] font-bold leading-5 text-[#28254f]">
                    {item.title}
                  </strong>
                  <time className="mt-[4px] block text-[13px] leading-5 text-[#737ba6]">
                    {item.time}
                  </time>
                </span>
              </li>
            ))}
          </ol>
          <div className="mm-trace-clock-position pointer-events-none absolute right-0 top-[48px] hidden md:block">
            <HistoryClock />
          </div>
        </div>
      </section>
    </div>
  )
}

export default Trace
