import { useEffect, useState } from 'react'
import {
  BookOpenCheck,
  CheckCircle2,
  CircleUserRound,
  FileText,
  Goal,
  Lightbulb,
  Save,
  SlidersHorizontal,
  Workflow,
} from 'lucide-react'
import { getDemoState, saveWeaknessToMemoryApi } from '../services/api'
import type { DemoState } from '../services/demoState'

type MemoryTab = 'Saved Info' | 'Preferences' | 'Insights'

const tabs: MemoryTab[] = ['Saved Info', 'Preferences', 'Insights']

const keyInformation = [
  {
    title: 'Learning Goals',
    detail: <>Become a skilled<br />Anesthesia Professional</>,
    Icon: Goal,
    iconBg: 'bg-[#d9f9e9]',
    iconColor: 'bg-[#10bd8c] text-white',
  },
  {
    title: 'Interests',
    detail: 'Medicine, AI & Tech',
    Icon: Workflow,
    iconBg: 'bg-[#d9f7f3]',
    iconColor: 'bg-[#14b8a6] text-white',
  },
  {
    title: 'Preferred Study Style',
    detail: 'Visual + Practice',
    Icon: BookOpenCheck,
    iconBg: 'bg-[#fff0d8]',
    iconColor: 'bg-[#f59e0b] text-white',
  },
  {
    title: 'Focus Subjects',
    detail: <>Anatomy, Physiology,<br />Pathology</>,
    Icon: CircleUserRound,
    iconBg: 'bg-[#ffebe7]',
    iconColor: 'bg-[#ff7864] text-white',
  },
]

function Memory() {
  const [activeTab, setActiveTab] = useState<MemoryTab>('Saved Info')
  const [demoState, setDemoState] = useState<DemoState | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

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
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Could not save this insight.',
      )
    } finally {
      setIsSaving(false)
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

            <h2 className="mb-[9px] mt-[21px] text-[18px] font-bold leading-6 text-[#242052]">
              Recent Notes
            </h2>
            <div className="space-y-2">
              <article className="flex min-h-[59px] items-center gap-3 rounded-[13px] border border-[#e4ddff] bg-[#faf9ff] px-4 py-3">
                <span className="grid size-[29px] shrink-0 place-items-center rounded-[9px] bg-[#aa88ff] text-white">
                  <FileText size={16} />
                </span>
                <p className="min-w-0 flex-1 truncate text-[13px] text-[#2b2856]">
                  You prefer short summaries and simple explanations...
                </p>
                <time className="shrink-0 text-[11px] text-[#727ba8]">Apr 22</time>
              </article>
              {demoState?.memoryNotes.map((note) => (
                <article key={note} className="flex min-h-[59px] items-center gap-3 rounded-[13px] border border-[#e4ddff] bg-[#faf9ff] px-4 py-3">
                  <span className="grid size-[29px] shrink-0 place-items-center rounded-[9px] bg-[#aa88ff] text-white">
                    <FileText size={16} />
                  </span>
                  <p className="min-w-0 flex-1 truncate text-[13px] text-[#2b2856]">{note}</p>
                  <time className="shrink-0 text-[11px] text-[#727ba8]">Saved</time>
                </article>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'Preferences' && (
          <div role="tabpanel" className="relative z-10 mt-[21px]">
            <h2 className="mb-[12px] text-[18px] font-bold leading-6 text-[#242052]">Your Preferences</h2>
            <div className="grid gap-[13px] sm:grid-cols-2">
              <PreferenceCard title="Study style" value="Visual + Practice" Icon={SlidersHorizontal} />
              <PreferenceCard title="Learning goals" value="Build confidence and practical skills" Icon={Goal} />
              <PreferenceCard title="Interests" value="Medicine, AI & Tech" Icon={Workflow} />
              <PreferenceCard title="Focus subjects" value="Anatomy, Physiology, Pathology" Icon={BookOpenCheck} />
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
