import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { ArrowRight, Check, ChevronRight, CircleHelp, ClipboardPlus, Diamond, RefreshCw, Target, Zap } from 'lucide-react'
import { Link } from 'react-router'
import { submitPracticeAnswer } from '../services/api'
import type { PracticeResult } from '../services/demoState'

type TaskStatus = 'pending' | 'completed'
type Task = { id: number; title: string; type: 'Study' | 'Practice' | 'Revision'; due: string; status: TaskStatus; icon: 'none' | 'bolt' | 'refresh' | 'diamond' | 'help' }

const initialTasks: Task[] = [
  { id: 1, title: 'Study – Cardiovascular System', type: 'Study', due: 'Due Today • 10:00 AM', status: 'pending', icon: 'none' },
  { id: 2, title: 'Practice – Anatomy MCQs', type: 'Practice', due: 'Due Today • 4:00 PM', status: 'pending', icon: 'bolt' },
  { id: 3, title: 'Revise – Liver & Biliary System', type: 'Revision', due: 'Tomorrow • 9:00 AM', status: 'pending', icon: 'refresh' },
  { id: 4, title: 'Complete – General Anaesthesia Notes', type: 'Study', due: 'Tomorrow • 2:00 PM', status: 'completed', icon: 'diamond' },
  { id: 5, title: 'Solve – Previous Year Questions', type: 'Practice', due: 'Tomorrow • 5:00 PM', status: 'completed', icon: 'help' },
]

function Sim() {
  const [tasks, setTasks] = useState(initialTasks)
  const [filter, setFilter] = useState<'All' | 'Pending' | 'Completed'>('All')
  const [addTaskOpen, setAddTaskOpen] = useState(false)
  const [newTaskName, setNewTaskName] = useState('')
  const [activeTask, setActiveTask] = useState<Task | null>(null)
  const [answer, setAnswer] = useState('')
  const [result, setResult] = useState<PracticeResult | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    const openNewTask = () => setAddTaskOpen(true)
    window.addEventListener('mindmate:new-task', openNewTask)
    return () => window.removeEventListener('mindmate:new-task', openNewTask)
  }, [])

  const filteredTasks = useMemo(() => tasks.filter((task) => filter === 'All' || task.status === filter.toLowerCase()), [tasks, filter])
  const counts = { All: tasks.length, Pending: tasks.filter((task) => task.status === 'pending').length, Completed: tasks.filter((task) => task.status === 'completed').length }

  function toggleTask(taskId: number) {
    setTasks((current) => current.map((task) => task.id === taskId ? { ...task, status: task.status === 'pending' ? 'completed' : 'pending' } : task))
  }

  function addTask(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!newTaskName.trim()) return
    setTasks((current) => [{ id: Date.now(), title: newTaskName.trim(), type: 'Study', due: 'Due Today • New task', status: 'pending', icon: 'none' }, ...current])
    setNewTaskName('')
    setAddTaskOpen(false)
  }

  async function submitAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSubmitting(true)
    setErrorMessage(null)
    try { setResult(await submitPracticeAnswer(answer)) }
    catch (error) { setErrorMessage(error instanceof Error ? error.message : 'Could not submit your answer.') }
    finally { setIsSubmitting(false) }
  }

  return <div className="mx-auto max-w-[1200px]">
    <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-[29px] font-bold tracking-tight text-[#211e58]">My Tasks</h1>
      <button type="button" onClick={() => setAddTaskOpen(true)} className="inline-flex h-10 items-center gap-2 rounded-2xl bg-gradient-to-r from-[#8237ef] to-[#5f64f2] px-4 text-sm font-semibold text-white shadow-sm hover:brightness-105 sm:hidden"><ClipboardPlus size={18}/>New Task</button>
    </div>
    <div className="mb-3 flex items-center gap-3" role="tablist" aria-label="Filter tasks">
      {(['All', 'Pending', 'Completed'] as const).map((tab) => <button type="button" role="tab" aria-selected={filter === tab} key={tab} onClick={() => setFilter(tab)} className={`h-[34px] rounded-full px-5 text-xs font-medium transition ${filter === tab ? 'bg-gradient-to-r from-[#8237ef] to-[#6260f2] text-white shadow-sm' : 'text-[#686d9a] hover:bg-white'}`}>{tab} ({counts[tab]})</button>)}
    </div>

    <div className="grid gap-4 lg:grid-cols-[1.85fr_.9fr]">
      <section className="rounded-[22px] border border-violet-200 bg-white px-5 shadow-[0_8px_24px_rgba(82,62,163,.07)] sm:px-[22px]" aria-label={`${filter} tasks`}>
        {filteredTasks.map((task) => <div key={task.id} className={`flex min-h-[103px] items-center gap-2 border-b border-[#f0edfb] last:border-0 ${task.status === 'completed' ? 'text-slate-400' : ''}`}>
          <button type="button" aria-label={`${task.status === 'pending' ? 'Mark complete' : 'Mark pending'}: ${task.title}`} onClick={() => toggleTask(task.id)} className={`grid size-6 shrink-0 place-items-center rounded-full border-2 ${task.status === 'completed' ? 'border-slate-300 text-slate-400' : 'border-[#ad96ff] text-[#8257fb]'}`}>{task.status === 'completed' && <Check size={14}/>}</button>
          {task.icon !== 'none' && <span className={`hidden size-8 shrink-0 place-items-center rounded-lg text-white sm:grid ${task.icon === 'bolt' ? 'bg-emerald-500' : task.icon === 'refresh' ? 'bg-emerald-500' : task.icon === 'diamond' ? 'bg-amber-500' : 'bg-violet-500'}`}>{task.icon === 'bolt' ? <Zap size={18} fill="none"/> : task.icon === 'refresh' ? <RefreshCw size={18}/> : task.icon === 'diamond' ? <Diamond size={18}/> : <CircleHelp size={18}/>}</span>}
          <button type="button" onClick={() => { setActiveTask(task); setResult(null); setAnswer('') }} className="min-w-0 flex-1 py-3 text-left"><span className="block text-[13px] font-semibold leading-5 text-[#201e55]">{task.title}</span><span className="mt-1 block text-[10px] text-[#8790bc]">Simple</span></button>
          <span className={`hidden shrink-0 rounded-xl px-4 py-1.5 text-[11px] sm:inline-flex ${task.type === 'Practice' ? 'bg-[#dcfae9] text-[#16a35b]' : task.type === 'Revision' ? 'bg-[#edf5ff] text-[#3281ee]' : 'bg-[#f0e9ff] text-[#8053f7]'}`}>{task.type}</span>
          <span className={`hidden min-w-[132px] shrink-0 text-right text-[10px] sm:block ${task.due.includes('Due Today') && task.status === 'pending' ? 'text-red-500' : 'text-[#69709e]'}`}>{task.due}</span>
          <button type="button" aria-label={`Open ${task.title}`} onClick={() => { setActiveTask(task); setResult(null); setAnswer('') }} className="grid size-7 shrink-0 place-items-center text-[#8a91bd] hover:text-violet-600"><ChevronRight size={19}/></button>
        </div>)}
        {filteredTasks.length === 0 && <div className="grid min-h-48 place-items-center text-sm text-slate-500">No {filter.toLowerCase()} tasks right now.</div>}
      </section>

      <aside className="grid gap-4 lg:grid-cols-1 sm:grid-cols-2">
        <section className="min-h-[242px] rounded-[22px] border border-violet-200 bg-white p-5 shadow-[0_8px_24px_rgba(82,62,163,.07)]">
          <h2 className="text-[18px] font-bold text-[#211e58]">Your Study Streak</h2>
          <div className="mt-4 flex items-center gap-4"><span className="grid size-[54px] place-items-center rounded-[18px] bg-[#fff0ac] text-[30px]">🔥</span><div><p className="text-[30px] font-bold leading-8 text-[#211e58]">5 Days</p><p className="mt-1 text-[13px] text-[#7a80a7]">Keep going!</p></div></div>
          <div className="mt-5 flex h-[66px] items-end justify-center gap-6">{[20,35,53,73].map((height,index)=><div key={height} style={{height}} className={`w-9 rounded-t-md ${index<2?'bg-[#ded6ff]':'bg-[#8c4df3]'}`}/>)}</div>
        </section>
        <section className="flex min-h-[260px] flex-col rounded-[22px] border border-violet-200 bg-white p-5 shadow-[0_8px_24px_rgba(82,62,163,.07)]">
          <h2 className="text-[18px] font-bold text-[#211e58]">Today’s Focus</h2><div className="mt-6 flex items-start gap-4"><span className="grid size-[53px] shrink-0 place-items-center rounded-[17px] bg-[#eee8ff] text-violet-600"><Target size={29} strokeWidth={1.7}/></span><p className="text-sm leading-5 text-[#33365d]">Complete at least 2 tasks today.</p></div><div className="mt-auto flex items-center gap-5 pt-8"><div className="h-[10px] flex-1 overflow-hidden rounded-full bg-[#e4e4e8]"><div className="h-full w-1/2 rounded-full bg-gradient-to-r from-[#8f3ef3] to-[#6562f1]"/></div><span className="text-sm text-[#656b97]">1 / 2</span></div>
        </section>
      </aside>
    </div>

    {activeTask && <div className="fixed inset-0 z-[80] grid place-items-center bg-[#201a48]/35 p-4" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setActiveTask(null) }}><section role="dialog" aria-modal="true" aria-labelledby="task-dialog-title" className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-3xl bg-white p-6 shadow-2xl"><div className="flex items-start justify-between gap-4"><div><p className="text-xs font-semibold uppercase tracking-wider text-violet-600">{activeTask.type} task</p><h2 id="task-dialog-title" className="mt-2 text-xl font-bold text-[#211e58]">{activeTask.title}</h2></div><button type="button" aria-label="Close task" onClick={() => setActiveTask(null)} className="rounded-lg px-2 py-1 text-2xl leading-none text-slate-400 hover:bg-violet-50">×</button></div>
        {activeTask.type === 'Practice' && <><p className="mt-4 text-sm leading-6 text-slate-600">How would you investigate a difficult topic you are learning and check that you understand it?</p>{result ? <div className="mt-5 rounded-2xl bg-violet-50 p-4"><p className="font-semibold text-violet-800">Answer recorded · Demo score {result.score}</p><p className="mt-2 text-sm text-slate-700">{result.feedback}</p><p className="mt-3 text-sm font-medium text-amber-700">Practice area detected: {result.weakness}</p><div className="mt-4 flex flex-wrap gap-3"><Link to="/memory" onClick={() => setActiveTask(null)} className="rounded-xl border border-violet-200 bg-white px-4 py-2 text-sm font-semibold text-violet-700">Save to My Memory</Link><Link to="/pipeline" onClick={() => setActiveTask(null)} className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-sm font-semibold text-white">Review plan <ArrowRight size={15}/></Link></div></div> : <form onSubmit={submitAnswer} className="mt-4"><label htmlFor="practice-answer" className="mb-2 block text-sm font-semibold text-slate-700">Your answer</label><textarea id="practice-answer" required minLength={10} rows={5} value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="Write your answer here…" className="w-full resize-y rounded-xl border border-violet-200 p-3 text-sm outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-100"/>{errorMessage && <p role="alert" className="mt-2 text-sm text-red-600">{errorMessage}</p>}<button disabled={isSubmitting || answer.trim().length < 10} className="mt-4 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-500 px-5 py-3 text-sm font-semibold text-white disabled:opacity-50">{isSubmitting ? 'Checking…' : 'Submit answer'}</button></form>}</>}
        {activeTask.type !== 'Practice' && <><p className="mt-4 text-sm text-slate-600">This task is ready in your learning plan.</p><div className="mt-5 flex gap-3"><button type="button" onClick={() => { toggleTask(activeTask.id); setActiveTask(null) }} className="rounded-xl bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white">{activeTask.status === 'pending' ? 'Mark complete' : 'Mark pending'}</button><Link to="/pipeline" onClick={() => setActiveTask(null)} className="rounded-xl border border-violet-200 px-4 py-2.5 text-sm font-semibold text-violet-700">View plan</Link></div></>}
      </section></div>}

    {addTaskOpen && <div className="fixed inset-0 z-[80] grid place-items-center bg-[#201a48]/35 p-4"><form onSubmit={addTask} className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between"><h2 className="text-xl font-bold text-[#211e58]">Create a new task</h2><button type="button" aria-label="Close" onClick={() => setAddTaskOpen(false)} className="px-2 text-2xl text-slate-400">×</button></div><label htmlFor="new-task" className="mt-5 block text-sm font-medium text-slate-700">Task name</label><input id="new-task" autoFocus required value={newTaskName} onChange={(event) => setNewTaskName(event.target.value)} placeholder="e.g. Review lecture notes" className="mt-2 w-full rounded-xl border border-violet-200 px-4 py-3 outline-none focus:border-violet-500"/><button className="mt-5 w-full rounded-xl bg-gradient-to-r from-violet-600 to-indigo-500 py-3 font-semibold text-white">Add task</button></form></div>}
  </div>
}

export default Sim
