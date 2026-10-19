import { useEffect, useState, type FormEvent } from 'react'
import {
  BookOpenCheck,
  CheckCircle2,
  CircleUserRound,
  FileText,
  Pencil,
  Trash2,
  Goal,
  Lightbulb,
  Save,
  SlidersHorizontal,
  Workflow,
} from 'lucide-react'
import { getDemoState, saveWeaknessToMemoryApi } from '../services/api'
import { deleteMemoryItem, editMemoryItem, getMemoryItems, type MemoryItem } from '../services/backend'
import { useLoad } from '../hooks/useLoad'
import { RefTag } from '../components/RefText'
import type { DemoState } from '../services/demoState'

type MemoryTab = 'Saved Info' | 'Preferences' | 'Insights'

const tabs: MemoryTab[] = ['Saved Info', 'Preferences', 'Insights']

const TYPE_LABELS: Record<string, string> = {
  goal: 'Goal',
  decision: 'Decision',
  skill: 'Skill',
  evidence: 'Evidence',
  weakness: 'Weakness',
  constraint: 'Constraint',
  preference: 'Preference',
  profile: 'Profile',
  learning_insight: 'Insight',
  note: 'Note',
}

const TYPE_ORDER = ['goal', 'decision', 'weakness', 'skill', 'evidence', 'constraint', 'preference', 'learning_insight', 'note', 'profile']

function rank(item: MemoryItem) {
  const value = item.payload?.priority_rank
  return typeof value === 'number' ? value : 99
}

function summarize(items: MemoryItem[], type: string, empty: string) {
  const values = items
    .filter((item) => item.type === type)
    .sort((a, b) => rank(a) - rank(b))
    .map((item) => item.content.split(' — because')[0].split(' (')[0])
  return values.length ? values.slice(0, 3).join(', ') + (values.length > 3 ? ` +${values.length - 3} more` : '') : empty
}

function Memory() {
  const [activeTab, setActiveTab] = useState<MemoryTab>('Saved Info')
  const [demoState, setDemoState] = useState<DemoState | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const memory = useLoad(getMemoryItems)
  const [typeFilter, setTypeFilter] = useState('all')
  const [editing, setEditing] = useState<{ id: number; content: string } | null>(null)
  const [busyId, setBusyId] = useState<number | null>(null)

  useEffect(() => {
    let isCurrent = true

    getDemoState()
      .then((state) => {
        if (isCurrent) setDemoState(state)
      })
      .catch(() => {
        if (isCurrent) setErrorMessage('Could not load saved learning information.')
      })

    return () => {
      isCurrent = false
    }
  }, [])

  const latestPractice = demoState?.latestPractice ?? null
  const practiceNote = latestPractice
    ? `Practice focus: ${latestPractice.weakness}`
    : null
  const hasSavedPracticeNote = Boolean(
    practiceNote && demoState?.memoryNotes.includes(practiceNote),
  )

  async function savePracticeInsight() {
    setIsSaving(true)
    setErrorMessage(null)

    try {
      const updatedState = await saveWeaknessToMemoryApi()
      setDemoState(updatedState)
      memory.reload()
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Could not save this insight.',
      )
    } finally {
      setIsSaving(false)
    }
  }

  const items = memory.data ?? []
  const keyInformation = [
    { title: 'Goals', detail: summarize(items, 'goal', 'No goals saved yet'), Icon: Goal, iconBg: 'bg-[#d9f9e9]', iconColor: 'bg-[#10bd8c] text-white' },
    { title: 'Skills', detail: summarize(items, 'skill', 'No skills saved yet'), Icon: Workflow, iconBg: 'bg-[#d9f7f3]', iconColor: 'bg-[#14b8a6] text-white' },
    { title: 'Decisions (the why)', detail: summarize(items, 'decision', 'No decisions saved yet'), Icon: BookOpenCheck, iconBg: 'bg-[#fff0d8]', iconColor: 'bg-[#f59e0b] text-white' },
    { title: 'Weaknesses to work on', detail: summarize(items, 'weakness', 'None recorded yet'), Icon: CircleUserRound, iconBg: 'bg-[#ffebe7]', iconColor: 'bg-[#ff7864] text-white' },
  ]
  const types = TYPE_ORDER.filter((type) => items.some((item) => item.type === type))
  const listed = items
    .filter((item) => typeFilter === 'all' || item.type === typeFilter)
    .sort((a, b) => TYPE_ORDER.indexOf(a.type) - TYPE_ORDER.indexOf(b.type))
  const preferences = items.filter((item) => item.type === 'preference')

  async function saveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!editing || !editing.content.trim()) return
    setBusyId(editing.id)
    setErrorMessage(null)
    try {
      const updated = await editMemoryItem(editing.id, editing.content.trim())
      memory.setData(items.map((item) => (item.id === updated.id ? updated : item)))
      setEditing(null)
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not save the change.')
    } finally {
      setBusyId(null)
    }
  }

  async function removeItem(item: MemoryItem) {
    if (!window.confirm(`Delete this memory? MindMate will stop using it.\n\n${item.content}`)) return
    setBusyId(item.id)
    setErrorMessage(null)
    try {
      await deleteMemoryItem(item.id)
      memory.setData(items.filter((entry) => entry.id !== item.id))
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Could not delete this memory.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="relative isolate mx-auto w-full max-w-[1120px]">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-[96px] -top-[278px] -z-10 size-[260px] rounded-full bg-[#dff8f0]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-[190px] -right-24 -z-10 size-[300px] rounded-full bg-[#e6ddff]"
      />

      <section className="relative min-h-[530px] overflow-hidden rounded-[20px] border border-[#e3dcff] bg-white/80 p-5 shadow-[0_12px_30px_rgba(84,63,175,0.07)]">
        <div aria-hidden="true" className="pointer-events-none absolute right-[60px] top-[18px] h-[75px] w-[54px] rotate-[9deg] rounded-[11px] border-[3px] border-white bg-[#f7f4ff] pt-[10px] shadow-[0_5px_12px_rgba(98,74,180,0.16)]">
          <span className="ml-[7px] block h-[5px] w-[34px] rounded-full bg-[#a584ff]" />
          <span className="ml-[6px] mt-[6px] block h-[5px] w-[33px] rounded-full bg-[#a584ff]" />
          <span className="ml-[5px] mt-[6px] block h-[5px] w-[29px] rounded-full bg-[#a584ff]" />
          <span className="ml-[4px] mt-[6px] block h-[5px] w-[16px] rounded-full bg-[#a584ff]" />
        </div>

        <div role="tablist" aria-label="Memory sections" className="relative z-10 flex gap-[9px]">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={activeTab === tab}
              onClick={() => setActiveTab(tab)}
              className={`h-[35px] min-w-[133px] rounded-full px-5 text-[12px] font-semibold transition ${activeTab === tab ? 'bg-[#ded6ff] text-[#6332c7]' : 'bg-[#eef0ff] text-[#7079a6] hover:bg-[#e6e5ff]'}`}
            >
              {tab}
            </button>
          ))}
        </div>

        {errorMessage && (
          <p role="alert" className="mt-3 text-xs text-rose-600">{errorMessage}</p>
        )}

        {activeTab === 'Saved Info' && (
          <div role="tabpanel" className="relative z-10 mt-[21px]">
            <h2 className="mb-[12px] text-[18px] font-bold leading-6 text-[#242052]">
              Your Key Information
            </h2>
            <div className="grid gap-[13px] sm:grid-cols-2">
              {keyInformation.map(({ title, detail, Icon, iconBg, iconColor }) => (
                <article
                  key={title}
                  className="flex min-h-[125px] items-center gap-4 rounded-[16px] border border-[#e4ddff] bg-white/55 px-[18px] py-4"
                >
                  <span className={`grid size-[55px] shrink-0 place-items-center rounded-[17px] ${iconBg}`}>
                    <span className={`grid size-[37px] place-items-center rounded-[11px] ${iconColor}`}>
                      <Icon size={20} strokeWidth={2} />
                    </span>
                  </span>
                  <span className="min-w-0">
                    <strong className="block text-[13px] font-bold leading-5 text-[#27244f]">
                      {title}
                    </strong>
                    <span className="mt-[4px] block text-[13px] leading-[18px] text-[#727ba8]">
                      {detail}
                    </span>
                  </span>
                </article>
              ))}
            </div>

            <div className="mb-[9px] mt-[21px] flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-[18px] font-bold leading-6 text-[#242052]">Everything MindMate remembers</h2>
              <select aria-label="Filter memory by type" value={typeFilter} onChange={(event) => setTypeFilter(event.target.value)} className="h-9 rounded-xl border border-violet-200 bg-white px-3 text-[12px] text-[#2b2856] outline-none focus:border-violet-500">
                <option value="all">All ({items.length})</option>
                {types.map((type) => <option key={type} value={type}>{TYPE_LABELS[type] ?? type} ({items.filter((item) => item.type === type).length})</option>)}
              </select>
            </div>
            {memory.loading && <p role="status" className="text-[13px] text-[#727ba8]">Loading your memory…</p>}
            {memory.error && <p role="alert" className="text-[13px] text-rose-600">Could not load memory: {memory.error}</p>}
            {!memory.loading && !memory.error && listed.length === 0 && <p className="text-[13px] text-[#727ba8]">Nothing saved yet. Complete onboarding or a practice session.</p>}
            <div className="space-y-2">
              {listed.map((item) => (
                <article key={item.id} className="flex min-h-[59px] items-center gap-3 rounded-[13px] border border-[#e4ddff] bg-[#faf9ff] px-4 py-3">
                  <span className="grid size-[29px] shrink-0 place-items-center rounded-[9px] bg-[#aa88ff] text-white">
                    <FileText size={16} />
                  </span>
                  {editing?.id === item.id ? (
                    <form onSubmit={saveEdit} className="flex min-w-0 flex-1 flex-wrap items-center gap-2">
                      <label className="sr-only" htmlFor={`edit-${item.id}`}>Edit memory</label>
                      <input id={`edit-${item.id}`} autoFocus value={editing.content} onChange={(event) => setEditing({ id: item.id, content: event.target.value })} className="min-w-[200px] flex-1 rounded-lg border border-violet-300 bg-white px-3 py-1.5 text-[13px] text-[#2b2856] outline-none focus:border-violet-500" />
                      <button type="submit" disabled={busyId === item.id} className="rounded-lg bg-[#8254f6] px-3 py-1.5 text-[12px] font-semibold text-white disabled:opacity-60">Save</button>
                      <button type="button" onClick={() => setEditing(null)} className="rounded-lg px-2 py-1.5 text-[12px] text-[#727ba8] hover:bg-violet-50">Cancel</button>
                    </form>
                  ) : (
                    <>
                      <p className="min-w-0 flex-1 text-[13px] text-[#2b2856]">
                        <span className="mr-2 rounded-md bg-[#eee8ff] px-1.5 py-[1px] text-[11px] font-semibold text-[#6332c7]">{TYPE_LABELS[item.type] ?? item.type}</span>
                        {item.content}
                      </p>
                      {item.ref && <RefTag value={item.ref} />}
                      <button type="button" aria-label={`Edit: ${item.content}`} title="Edit" onClick={() => setEditing({ id: item.id, content: item.content })} className="grid size-8 shrink-0 place-items-center rounded-lg text-[#8a91bd] hover:bg-violet-50 hover:text-violet-700"><Pencil size={15} /></button>
                      <button type="button" aria-label={`Delete: ${item.content}`} title="Delete" disabled={busyId === item.id} onClick={() => void removeItem(item)} className="grid size-8 shrink-0 place-items-center rounded-lg text-[#8a91bd] hover:bg-rose-50 hover:text-rose-600 disabled:opacity-50"><Trash2 size={15} /></button>
                    </>
                  )}
                </article>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'Preferences' && (
          <div role="tabpanel" className="relative z-10 mt-[21px]">
            <h2 className="mb-[12px] text-[18px] font-bold leading-6 text-[#242052]">Your Preferences</h2>
            {preferences.length === 0 && !memory.loading && <p className="text-[13px] text-[#727ba8]">No preferences saved yet. They are captured during onboarding.</p>}
            <div className="grid gap-[13px] sm:grid-cols-2">
              {preferences.map((item) => {
                const [title, ...rest] = item.content.split(':')
                return <PreferenceCard key={item.id} title={title.charAt(0).toUpperCase() + title.slice(1)} value={rest.join(':').replace(/[[\]']/g, '').trim() || item.content} Icon={SlidersHorizontal} />
              })}
            </div>
          </div>
        )}

        {activeTab === 'Insights' && (
          <div role="tabpanel" className="relative z-10 mt-[21px]">
            <h2 className="mb-[12px] text-[18px] font-bold leading-6 text-[#242052]">Learning Insights</h2>
            {latestPractice ? (
              <article className="rounded-[16px] border border-[#e4ddff] bg-white/55 p-5">
                <div className="flex items-start gap-4">
                  <span className="grid size-[55px] shrink-0 place-items-center rounded-[17px] bg-[#eee8ff] text-[#8758ef]">
                    <Lightbulb size={24} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h3 className="font-bold text-[#27244f]">{latestPractice.weakness}</h3>
                    <p className="mt-2 text-sm leading-6 text-[#727ba8]">{latestPractice.feedback}</p>
                    <button
                      type="button"
                      onClick={savePracticeInsight}
                      disabled={hasSavedPracticeNote || isSaving}
                      className="mt-4 inline-flex items-center gap-2 rounded-full bg-[#8254f6] px-4 py-2 text-sm font-semibold text-white hover:bg-[#7040e8] disabled:cursor-default disabled:opacity-60"
                    >
                      {hasSavedPracticeNote ? <CheckCircle2 size={16} /> : <Save size={16} />}
                      {isSaving ? 'Saving...' : hasSavedPracticeNote ? 'Saved to Memory' : 'Save this insight'}
                    </button>
                  </div>
                </div>
              </article>
            ) : (
              <div className="flex min-h-[150px] items-center gap-4 rounded-[16px] border border-[#e4ddff] bg-white/55 p-5">
                <span className="grid size-[55px] place-items-center rounded-[17px] bg-[#eee8ff] text-[#8758ef]"><Lightbulb size={24} /></span>
                <p className="text-sm text-[#727ba8]">Complete a practice session to see a personalized learning insight here.</p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  )
}

function PreferenceCard({
  title,
  value,
  Icon,
}: {
  title: string
  value: string
  Icon: typeof Goal
}) {
  return (
    <article className="flex min-h-[125px] items-center gap-4 rounded-[16px] border border-[#e4ddff] bg-white/55 px-[18px] py-4">
      <span className="grid size-[55px] shrink-0 place-items-center rounded-[17px] bg-[#eee8ff] text-[#8254f6]"><Icon size={23} /></span>
      <span>
        <strong className="block text-[13px] font-bold text-[#27244f]">{title}</strong>
        <span className="mt-1 block text-[13px] text-[#727ba8]">{value}</span>
      </span>
    </article>
  )
}

export default Memory
