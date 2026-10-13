export type PracticeResult = {
  answer: string
  score: number
  weakness: string
  feedback: string
  submittedAt: string
}

export type DemoEvent = {
  id: string
  title: string
  detail: string
  occurredAt: string
}

export type DemoState = {
  latestPractice: PracticeResult | null
  memoryNotes: string[]
  trace: DemoEvent[]
  originalPlan: string[]
  updatedPlan: string[] | null
  replanReason: string | null
}

const STORAGE_KEY = 'mindmate-demo-state'

const DEFAULT_PLAN = [
  'Review React fundamentals',
  'Practice accessible forms',
  'Review async JavaScript',
]

function emptyDemoState(): DemoState {
  return {
    latestPractice: null,
    memoryNotes: [],
    trace: [],
    originalPlan: DEFAULT_PLAN,
    updatedPlan: null,
    replanReason: null,
  }
}

export function loadDemoState(): DemoState {
  try {
    const saved = window.localStorage.getItem(STORAGE_KEY)

    if (!saved) {
      return emptyDemoState()
    }

    const parsed = JSON.parse(saved) as Partial<DemoState>

    return {
      latestPractice: parsed.latestPractice ?? null,
      memoryNotes: Array.isArray(parsed.memoryNotes)
        ? parsed.memoryNotes
        : [],
      trace: Array.isArray(parsed.trace) ? parsed.trace : [],
      originalPlan: Array.isArray(parsed.originalPlan)
        ? parsed.originalPlan
        : DEFAULT_PLAN,
      updatedPlan: Array.isArray(parsed.updatedPlan)
        ? parsed.updatedPlan
        : null,
      replanReason: parsed.replanReason ?? null,
    }
  } catch {
    return emptyDemoState()
  }
}

function storeDemoState(state: DemoState): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

export function savePracticeResult(result: PracticeResult): void {
  const currentState = loadDemoState()

  const nextState: DemoState = {
    ...currentState,
    latestPractice: result,
    updatedPlan: null,
    replanReason: null,
    trace: [
      {
        id: String(Date.now()),
        title: 'Practice answer evaluated',
        detail: `Practice area identified: ${result.weakness}`,
        occurredAt: result.submittedAt,
      },
      ...currentState.trace,
    ],
  }

  storeDemoState(nextState)
}

export function addMemoryNote(note: string): void {
  const currentState = loadDemoState()
  if (currentState.memoryNotes.includes(note)) return

  storeDemoState({
    ...currentState,
    memoryNotes: [note, ...currentState.memoryNotes],
    trace: [
      {
        id: String(Date.now()),
        title: 'Memory item saved',
        detail: note,
        occurredAt: new Date().toISOString(),
      },
      ...currentState.trace,
    ],
  })
}

export function saveWeaknessToMemory(): boolean {
  const currentState = loadDemoState()
  const weakness = currentState.latestPractice?.weakness

  if (!weakness) {
    return false
  }

  const note = `Practice focus: ${weakness}`

  if (currentState.memoryNotes.includes(note)) {
    return true
  }

  addMemoryNote(note)
  return true
}

export function runReplan(): boolean {
  const currentState = loadDemoState()
  const weakness = currentState.latestPractice?.weakness

  if (!weakness) {
    return false
  }

  const requiredMemoryNote = `Practice focus: ${weakness}`

  if (!currentState.memoryNotes.includes(requiredMemoryNote)) {
    return false
  }

  const updatedPlan = [
    `Focus practice: ${weakness}`,
    'Profile a React page and record before-and-after measurements',
    'Repeat the practice question and compare the explanation',
  ]

  const reason =
    `MINDMATE moved “${weakness}” to the top of the plan because it was identified during practice and saved to Memory.`

  const nextState: DemoState = {
    ...currentState,
    updatedPlan,
    replanReason: reason,
    trace: [
      {
        id: String(Date.now()),
        title: 'Learning plan replanned',
        detail: reason,
        occurredAt: new Date().toISOString(),
      },
      ...currentState.trace,
    ],
  }

  storeDemoState(nextState)
  return true
}
