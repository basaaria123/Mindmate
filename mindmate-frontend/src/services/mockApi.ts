import {
  addMemoryNote,
  loadDemoState,
  runReplan,
  savePracticeResult,
  saveWeaknessToMemory,
  type DemoEvent,
  type DemoState,
  type PracticeResult,
} from './demoState'

export type UserProfile = {
  name: string
  goal: string
  targetRole: string
  dailyMinutes: number
}

export type MemoryEntry = {
  id: string
  type: string
  content: string
  createdAt: string
}

const PROFILE_KEY = 'mindmate-profile'

function wait(milliseconds = 300): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

export async function getProfile(): Promise<UserProfile> {
  await wait()

  try {
    const saved = window.localStorage.getItem(PROFILE_KEY)
    if (saved) return JSON.parse(saved) as UserProfile
  } catch {
    // Fall back to the demo profile when local storage is unavailable.
  }

  return {
    name: 'MindMate learner',
    goal: 'Learn faster, Build skills, Stay organized',
    targetRole: 'Student',
    dailyMinutes: 60,
  }
}

export async function updateProfile(profile: UserProfile): Promise<UserProfile> {
  await wait()
  window.localStorage.setItem(PROFILE_KEY, JSON.stringify(profile))
  return profile
}

export async function getMemory(): Promise<DemoState> {
  await wait()
  return loadDemoState()
}

export async function createMemoryEntry(entry: Omit<MemoryEntry, 'id' | 'createdAt'>): Promise<MemoryEntry> {
  await wait()
  const savedEntry: MemoryEntry = {
    ...entry,
    id: String(Date.now()),
    createdAt: new Date().toISOString(),
  }
  addMemoryNote(entry.content)
  return savedEntry
}

export async function evaluatePractice(answer: string): Promise<PracticeResult> {
  await wait()
  const cleanAnswer = answer.trim()
  if (cleanAnswer.length < 10) {
    throw new Error('Please write at least 10 characters before submitting.')
  }

  const hasEnoughDetail = cleanAnswer.split(/\s+/).length >= 30
  const result: PracticeResult = {
    answer: cleanAnswer,
    score: hasEnoughDetail ? 72 : 48,
    weakness: 'Performance profiling and validating improvements',
    feedback: hasEnoughDetail
      ? 'Good detail. For this demo, MINDMATE suggests adding how you would profile the page and compare results before and after a change.'
      : 'Try adding more steps. For this demo, MINDMATE suggests describing how you would profile the page and validate a change.',
    submittedAt: new Date().toISOString(),
  }
  savePracticeResult(result)
  return result
}

export async function saveWeakness(): Promise<DemoState> {
  await wait()
  if (!saveWeaknessToMemory()) {
    throw new Error('Submit a practice answer before saving a weakness.')
  }
  return loadDemoState()
}

export async function replan(): Promise<DemoState> {
  await wait()
  if (!runReplan()) {
    throw new Error('Submit a practice answer and save its weakness to Memory first.')
  }
  return loadDemoState()
}

export async function getAgentEvents(): Promise<DemoEvent[]> {
  await wait()
  return loadDemoState().trace
}
