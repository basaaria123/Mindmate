// Offline mock for backend.ts. Answers come from personaSnapshot.json, a set of
// real backend responses for the demo persona (exported with the backend's own
// seed), loaded only in mock mode. Edits and deletes persist in localStorage.
import type { FitResult, Gap, Goal, MemoryItem, Opportunity, PracticeSession, Plan, PlanTask, ReplanResult } from './backend'
import { loadDemoState } from './demoState'

type Snapshot = {
  goals: Goal[]
  plan: Plan
  opportunities: Opportunity[]
  gaps: Record<string, Gap[]>
  memory: MemoryItem[]
  memory_after_practice: MemoryItem[]
  practice_question: Omit<PracticeSession, 'id'>
  replan: Record<string, ReplanResult>
}

const KEY = 'mindmate-persona-mock'
type LocalState = { deleted: number[]; edits: Record<string, string>; taskStatus: Record<string, string>; replanned: string | null }

let snapshotPromise: Promise<Snapshot> | null = null
function snapshot(): Promise<Snapshot> {
  snapshotPromise ??= import('./personaSnapshot.json').then((module) => module.default as unknown as Snapshot)
  return snapshotPromise
}

function local(): LocalState {
  try {
    const saved = window.localStorage.getItem(KEY)
    if (saved) return { deleted: [], edits: {}, taskStatus: {}, replanned: null, ...(JSON.parse(saved) as Partial<LocalState>) }
  } catch {
    // fall through to defaults when storage is unavailable
  }
  return { deleted: [], edits: {}, taskStatus: {}, replanned: null }
}

function save(state: LocalState) {
  try { window.localStorage.setItem(KEY, JSON.stringify(state)) } catch { /* storage may be unavailable */ }
}

function wait(ms = 250) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function practiceDone(): boolean {
  return Boolean(loadDemoState().latestPractice)
}

export async function getGoals(): Promise<Goal[]> {
  await wait()
  return (await snapshot()).goals
}

export async function getActivePlan(): Promise<Plan> {
  await wait()
  const snap = await snapshot()
  const state = local()
  const plan = state.replanned ? snap.replan[state.replanned].plan : snap.plan
  return { ...plan, tasks: plan.tasks.map((task) => ({ ...task, status: state.taskStatus[String(task.id)] ?? task.status })) }
}

export async function replanPlan(availableMinutes?: number): Promise<ReplanResult> {
  await wait(500)
  if (!practiceDone()) {
    throw new Error('Submit a practice answer first so there is new evidence to plan around.')
  }
  const key = String(availableMinutes && [30, 45].includes(availableMinutes) ? availableMinutes : 60)
  const state = local()
  save({ ...state, replanned: key, taskStatus: {} })
  return (await snapshot()).replan[key]
}

export async function setTaskStatus(taskId: number, status: 'todo' | 'done'): Promise<PlanTask> {
  await wait(120)
  const state = local()
  save({ ...state, taskStatus: { ...state.taskStatus, [String(taskId)]: status } })
  const plan = await getActivePlan()
  const task = plan.tasks.find((item) => item.id === taskId)
  if (!task) throw new Error('Task not found.')
  return { ...task, status }
}

export async function getOpportunities(): Promise<Opportunity[]> {
  await wait()
  return (await snapshot()).opportunities
}

export async function assessStoredFit(opportunityId: number): Promise<FitResult> {
  await wait(400)
  const opportunity = (await snapshot()).opportunities.find((item) => item.id === opportunityId)
  if (!opportunity?.fit) throw new Error('Opportunity not found.')
  const gaps = (await snapshot()).gaps[String(opportunityId)] ?? []
  return {
    id: opportunity.fit.id,
    score: opportunity.fit.score,
    band: opportunity.fit.band,
    top_gap: opportunity.fit.top_gap,
    refs: [],
    judged_by: 'deterministic',
    per_requirement: opportunity.requirements.map((req) => {
      const gap = gaps.find((item) => item.requirement === req.name)
      return { requirement: req.name, weight: req.weight, mandatory: req.mandatory, coverage: gap ? gap.coverage : 'demonstrated', evidence_refs: gap ? gap.refs : [], explanation: gap ? gap.rationale : 'Demonstrated with evidence.' }
    }),
  }
}

export async function getGaps(opportunityId: number): Promise<Gap[]> {
  await wait()
  return (await snapshot()).gaps[String(opportunityId)] ?? []
}

export async function getMemoryItems(): Promise<MemoryItem[]> {
  await wait()
  const snap = await snapshot()
  const state = local()
  const items = practiceDone() ? snap.memory_after_practice : snap.memory
  return items
    .filter((item) => !state.deleted.includes(item.id))
    .map((item) => (state.edits[String(item.id)] ? { ...item, content: state.edits[String(item.id)] } : item))
}

export async function editMemoryItem(id: number, content: string): Promise<MemoryItem> {
  await wait(150)
  const state = local()
  save({ ...state, edits: { ...state.edits, [String(id)]: content } })
  const item = (await getMemoryItems()).find((entry) => entry.id === id)
  if (!item) throw new Error('Memory item not found.')
  return item
}

export async function deleteMemoryItem(id: number): Promise<void> {
  await wait(150)
  const state = local()
  save({ ...state, deleted: [...state.deleted, id] })
}

export async function startPractice(topic?: string): Promise<PracticeSession> {
  await wait()
  const question = (await snapshot()).practice_question
  return { id: 0, ...question, topic: topic || question.topic }
}
