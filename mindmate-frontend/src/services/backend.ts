// Typed client for the MindMate backend (docs/contracts/backend-api.md).
// With VITE_API_BASE_URL set every call goes to FastAPI; without it, the same
// functions answer from a snapshot of real backend responses for the demo
// persona (personaSnapshot.json), so the UI can be built and demoed offline.
import { request, useMocks } from './api'
import * as mock from './personaMock'

export type Goal = {
  ref: string
  id: number
  title: string
  target_role: string | null
  deadline: string | null
  hours_per_day: number | null
  priority_rank: number
  status: string
}

export type PlanTask = {
  id: number
  ref: string
  title: string
  minutes: number
  priority: 'High' | 'Medium' | 'Low' | string
  day_number: number
  order_index: number
  deadline: string | null
  status: 'todo' | 'done' | 'deferred' | 'dropped' | string
  why: string
  refs: string[]
  must_keep: boolean
  priority_score: number | null
}

export type Plan = {
  id: number
  ref: string
  version: number
  daily_budget_minutes: number
  rationale: string | null
  refs: string[]
  minutes_by_day: Record<string, number>
  tasks: PlanTask[]
}

export type DiffEntry = {
  title: string
  to_day?: number
  from_day?: number | null
  to_rank?: number
  from_rank?: number
  minutes?: number
  priority_score?: number
  must_keep?: boolean
  refs: string[]
}

export type ReplanResult = {
  plan: Plan
  diff: { before: string[]; after: string[]; added: DiffEntry[]; moved: DiffEntry[]; deferred: DiffEntry[]; kept?: DiffEntry[] }
  rationale: string
  rationale_detail?: string
  explained_by?: string
  refs: string[]
  daily_budget_minutes: number
}

export type Opportunity = {
  id: number
  ref: string
  title: string
  org: string | null
  deadline: string | null
  type: string
  requirements: { name: string; weight: string; mandatory: boolean }[]
  summary: string | null
  fit?: { score: number; band: string; top_gap: string | null; id: number }
  target?: boolean
}

export type RequirementScore = {
  requirement: string
  weight: string
  coverage: 'demonstrated' | 'partial' | 'not_shown' | string
  evidence_refs: string[]
  explanation: string
  mandatory: boolean
}

export type FitResult = {
  id: number
  score: number
  band: string
  per_requirement: RequirementScore[]
  top_gap: string | null
  refs: string[]
  judged_by: string
}

export type Gap = {
  requirement: string
  impact_score: number
  weight: string
  coverage: string
  mandatory: boolean
  refs: string[]
  rationale: string
  recommended_focus: string
}

export type MemoryItem = {
  id: number
  type: string
  content: string
  payload: Record<string, unknown>
  source: string
  ref: string | null
  tags: string[]
  createdAt: string
  updatedAt?: string
  deletedAt: string | null
}

export type PracticeSession = {
  id: number
  topic: string
  question: string
  expected_concepts: string[]
  question_source?: string
}

export type BackendStatus = { llm_available: boolean; llm_mode: string; source: 'backend' | 'mock' }

export async function getGoals(): Promise<Goal[]> {
  if (useMocks) return mock.getGoals()
  return (await request<{ goals: Goal[] }>('/goals')).goals
}

export async function getActivePlan(): Promise<Plan | null> {
  if (useMocks) return mock.getActivePlan()
  return (await request<{ active: Plan | null }>('/plans')).active
}

export async function replanPlan(availableMinutes?: number, reason?: string): Promise<ReplanResult> {
  if (useMocks) return mock.replanPlan(availableMinutes)
  return request<ReplanResult>('/plans/replan', {
    method: 'POST',
    body: JSON.stringify({ ...(availableMinutes ? { available_minutes: availableMinutes } : {}), ...(reason ? { reason } : {}) }),
  })
}

export async function setTaskStatus(taskId: number, status: 'todo' | 'done'): Promise<PlanTask> {
  if (useMocks) return mock.setTaskStatus(taskId, status)
  return request<PlanTask>(`/plans/tasks/${taskId}`, { method: 'PATCH', body: JSON.stringify({ status }) })
}

export async function getOpportunities(): Promise<Opportunity[]> {
  if (useMocks) return mock.getOpportunities()
  return (await request<{ opportunities: Opportunity[] }>('/opportunities')).opportunities
}

export async function assessStoredFit(opportunityId: number): Promise<FitResult> {
  if (useMocks) return mock.assessStoredFit(opportunityId)
  return request<FitResult>(`/opportunities/${opportunityId}/fit`, { method: 'POST', body: JSON.stringify({}) })
}

export type GapReport = { fit: { score: number; band: string } | null; gaps: Gap[] }

export async function getGaps(opportunityId: number): Promise<GapReport> {
  if (useMocks) return mock.getGaps(opportunityId)
  return request<GapReport>('/skills/gaps', { method: 'POST', body: JSON.stringify({ opportunity_id: opportunityId }) })
}

export async function getMemoryItems(): Promise<MemoryItem[]> {
  if (useMocks) return mock.getMemoryItems()
  return (await request<{ items: MemoryItem[] }>('/memory')).items
}

export async function editMemoryItem(id: number, content: string): Promise<MemoryItem> {
  if (useMocks) return mock.editMemoryItem(id, content)
  return request<MemoryItem>(`/memory/${id}`, { method: 'PATCH', body: JSON.stringify({ content }) })
}

export async function deleteMemoryItem(id: number): Promise<void> {
  if (useMocks) return mock.deleteMemoryItem(id)
  await request<unknown>(`/memory/${id}`, { method: 'DELETE' })
}

export async function startPractice(topic?: string): Promise<PracticeSession> {
  if (useMocks) return mock.startPractice(topic)
  return request<PracticeSession>('/practice/start', { method: 'POST', body: JSON.stringify(topic ? { topic } : {}) })
}

export async function importProfile(profile: unknown): Promise<void> {
  if (useMocks) return
  await request<unknown>('/profile/import', { method: 'POST', body: JSON.stringify(profile) })
}

export async function getBackendStatus(): Promise<BackendStatus> {
  if (useMocks) return { llm_available: false, llm_mode: 'mock', source: 'mock' }
  const status = await request<{ llm_available: boolean; llm_mode: string }>('/admin/status')
  return { llm_available: status.llm_available, llm_mode: status.llm_mode, source: 'backend' }
}

export function hasActiveWeakness(items: MemoryItem[]): boolean {
  return items.some((item) => item.type === 'weakness' && !item.deletedAt)
}
