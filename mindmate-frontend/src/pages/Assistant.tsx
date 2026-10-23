import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { useNavigate } from 'react-router'
import { ArrowUpRight, Brain, BookOpen, CalendarDays, Camera, ChartNoAxesColumn, FileText, Image, Lightbulb, Maximize, Minus, Paperclip, Plug, Plus, Send, Sparkles, SquarePen, Target, X } from 'lucide-react'
import mindmateIntroEmblem from '../assets/mindmate-intro-emblem.png'
import activityEmblemReference from '../assets/activity-emblem-reference.png'
import mindmateWordmark from '../assets/mindmate-wordmark.svg'
import { GlassThemeToggle } from '../ThemeContext'
import { getFirstNameFromEmail } from '../services/userProfile'
import { sendAssistantMessage, type ChatTurn } from '../services/backend'

const quickActions = [
  { label: 'Generate Study Plan', detail: 'Personalized for your goals', icon: CalendarDays, prompt: 'Create a study plan for me.' },
  { label: 'Explain a Topic', detail: 'Simple and easy to understand', icon: Lightbulb, prompt: 'Explain a topic in a simple way.' },
  { label: 'Find Resources', detail: 'Books, videos, and more', icon: BookOpen, prompt: 'Find useful learning resources for me.' },
  { label: 'Track Progress', detail: 'See your learning journey', icon: ChartNoAxesColumn, prompt: 'Show me how I am progressing.' },
]

// A message in the open chat: `content` is what the model sees, `display` what the bubble shows.
type ChatEntry = ChatTurn & { display?: string; error?: boolean }
type SavedChat = { id: string; title: string; detail: string; updatedAt: string; messages: ChatEntry[] }

// Recent Chats are this browser's real conversations (most recent first).
const CHATS_KEY = 'mindmate-assistant-chats'
function loadChats(): SavedChat[] {
  try {
    const saved = JSON.parse(window.localStorage.getItem(CHATS_KEY) ?? '[]') as SavedChat[]
    return Array.isArray(saved) ? saved : []
  } catch { return [] }
}
function storeChats(chats: SavedChat[]) {
  try { window.localStorage.setItem(CHATS_KEY, JSON.stringify(chats.slice(0, 20))) } catch { /* storage may be unavailable */ }
}
function timeAgo(iso: string) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (Number.isNaN(minutes) || minutes < 1) return 'Just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return hours < 48 ? 'Yesterday' : `${Math.round(hours / 24)}d ago`
}

function Assistant() {
  const navigate = useNavigate()
  const firstName = getFirstNameFromEmail()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [message, setMessage] = useState('')
  const [conversation, setConversation] = useState<ChatEntry[]>([])
  const [pending, setPending] = useState(false)
  const [chats, setChats] = useState<SavedChat[]>(loadChats)
  const [chatId, setChatId] = useState(() => String(Date.now()))
  const [activeChat, setActiveChat] = useState('')
  const [expanded, setExpanded] = useState(false)
  const [attachmentMenuOpen, setAttachmentMenuOpen] = useState(false)
  const [pluginsOpen, setPluginsOpen] = useState(false)
  const [thinkHarder, setThinkHarder] = useState(false)
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const cameraInput = useRef<HTMLInputElement>(null)
  const photoInput = useRef<HTMLInputElement>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  const chatIdRef = useRef(chatId)
  const chatEnd = useRef<HTMLDivElement>(null)

  useEffect(() => { chatIdRef.current = chatId }, [chatId])
  useEffect(() => { chatEnd.current?.scrollIntoView({ block: 'end', behavior: 'smooth' }) }, [conversation, pending])

  const startNewChat = () => { setChatId(String(Date.now())); setActiveChat(''); setConversation([]); setPending(false); setMessage(''); setAttachedFiles([]); setThinkHarder(false); setPluginsOpen(false); setAttachmentMenuOpen(false) }
  const openChat = (chat: SavedChat) => { setChatId(chat.id); setActiveChat(chat.title); setConversation(chat.messages); setPending(false) }
  const rememberChat = (id: string, title: string, messages: ChatEntry[]) => {
    const lastReply = [...messages].reverse().find((entry) => entry.role === 'assistant' && !entry.error)
    const detail = (lastReply?.content ?? messages[0]?.content ?? '').replace(/\s+/g, ' ').slice(0, 60)
    const updated = [{ id, title, detail, updatedAt: new Date().toISOString(), messages }, ...chats.filter((chat) => chat.id !== id)]
    setChats(updated)
    storeChats(updated)
  }
  const handleFilesSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files ?? [])
    setAttachedFiles((current) => [...current, ...selectedFiles])
    setAttachmentMenuOpen(false)
    event.target.value = ''
  }
  const submitMessage = async () => {
    const trimmed = message.trim()
    if (pending || (!trimmed && attachedFiles.length === 0)) return
    const fileSummary = attachedFiles.map((file) => `📎 ${file.name}`).join('\n')
    const sentContent = [trimmed, fileSummary, thinkHarder ? '✦ Think harder enabled' : '']
      .filter(Boolean)
      .join('\n')
    // File contents are not uploaded; the model is told only the file names.
    const modelContent = [trimmed, attachedFiles.length ? `(Attached files, contents not shared: ${attachedFiles.map((file) => file.name).join(', ')})` : '']
      .filter(Boolean)
      .join('\n')
    const title = activeChat || (trimmed ? (trimmed.length > 30 ? `${trimmed.slice(0, 30)}…` : trimmed) : attachedFiles[0]?.name ?? 'New chat')
    const userEntry: ChatEntry = { role: 'user', content: modelContent, display: sentContent }
    const withUser = [...conversation, userEntry]
    const id = chatId
    setConversation(withUser)
    setActiveChat(title)
    setMessage('')
    setAttachedFiles([])
    setAttachmentMenuOpen(false)
    setPluginsOpen(false)
    setPending(true)
    const history: ChatTurn[] = withUser.filter((entry) => !entry.error).map(({ role, content }) => ({ role, content }))
    let next: ChatEntry[]
    try {
      const answer = await sendAssistantMessage(history, thinkHarder)
      next = [...withUser, { role: 'assistant', content: answer.reply }]
    } catch (error) {
      next = [...withUser, { role: 'assistant', content: error instanceof Error ? error.message : 'MindMate AI could not answer. Please try again.', error: true }]
    }
    if (chatIdRef.current !== id) return // the user started or opened another chat meanwhile
    setConversation(next)
    setPending(false)
    rememberChat(id, title, next)
  }

  return (
    <div className="mm-assistant-shell min-h-screen bg-[#eeeaff] p-1.5 text-[#211e58] sm:p-2.5">
      <section className={`mx-auto flex min-h-[calc(100vh-16px)] max-w-[1600px] overflow-hidden rounded-[20px] border border-violet-200 bg-[#fbfaff] shadow-[0_12px_40px_rgba(88,63,173,.10)] ${expanded ? 'min-h-[calc(100vh-16px)]' : ''}`}>
        {sidebarOpen && <aside className="flex w-[205px] shrink-0 flex-col border-r border-violet-100 bg-[#f2eeff] sm:w-[220px]">
          <div className="flex h-[62px] items-center gap-2 border-b border-violet-100 px-3">
            <button type="button" onClick={() => navigate('/boot')} aria-label="Return to MindMate workspace" title="Return to workspace" className="flex min-w-0 flex-1 items-center gap-2 rounded-lg text-left hover:opacity-80">
            <img src={mindmateIntroEmblem} alt="MindMate" className="size-9 rounded-full object-cover" />
            <img src={mindmateWordmark} alt="MindMate" className="h-7 min-w-0 flex-1 object-contain object-left" />
            </button>
            <button onClick={() => setSidebarOpen(false)} aria-label="Collapse chat sidebar" className="grid size-8 shrink-0 place-items-center rounded-lg text-violet-600 hover:bg-white"><PanelIcon /></button>
          </div>
          <p className="px-4 pt-2 text-[13px] text-[#73779e]">Your AI assistant</p>
          <p className="px-4 pt-1 text-[11px] text-[#8580a8]">Click on MindMate to go back</p>
          <button onClick={startNewChat} className="mx-3 mt-3 flex h-10 items-center gap-2 rounded-xl bg-[#e7dcff] px-3 text-[14px] font-semibold text-violet-700 hover:bg-[#ddd0ff]"><Plus size={16}/>New Chat</button>
          <div className="mt-5 px-4 text-[12px] font-medium tracking-wide text-[#8588aa]">Recent Chats</div>
          <nav className="mt-1 flex-1 space-y-1 overflow-y-auto px-2 py-1">
            {chats.length === 0 && <p className="px-2.5 py-2.5 text-[11px] text-[#777c9f]">No chats yet. Your conversations will appear here.</p>}
            {chats.map((chat) => <button key={chat.id} onClick={() => openChat(chat)} className={`w-full rounded-lg px-2.5 py-2.5 text-left hover:bg-white/80 ${chatId === chat.id ? 'bg-white/80' : ''}`}><span className="flex items-center justify-between gap-1"><strong className="truncate text-[12px] font-semibold">{chat.title}</strong><small className="shrink-0 text-[10px] text-[#898cac]">{timeAgo(chat.updatedAt)}</small></span><span className="mt-1 block truncate text-[11px] text-[#777c9f]">{chat.detail}</span></button>)}
          </nav>
          <div className="m-3 rounded-xl bg-[#e8ddff] px-3 py-3"><strong className="block text-[13px] text-violet-700">Ask. Learn. Grow.</strong><span className="mt-1 block text-[11px] text-[#77759a]">Your AI companion, every day.</span></div>
        </aside>}

        <div className="flex min-w-0 flex-1 flex-col">
          <header className="mm-assistant-header relative z-20 flex h-[62px] shrink-0 items-center justify-between border-b border-violet-100 bg-white/95 px-4 shadow-sm sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              {!sidebarOpen && <button onClick={() => setSidebarOpen(true)} aria-label="Show chat history" className="grid size-9 place-items-center rounded-lg text-violet-600 hover:bg-violet-50"><PanelIcon /></button>}
              <img src={mindmateIntroEmblem} alt="" className="size-8 rounded-full object-cover" />
              <div><h1 className="text-sm font-bold">MindMate AI</h1><p className="flex items-center gap-1 text-[11px] text-[#7c80a1]"><span className="size-1 rounded-full bg-emerald-400"/>Always here to help</p></div>
            </div>
            <div className="flex items-center gap-2"><button onClick={() => setExpanded((value) => !value)} aria-label={expanded ? 'Exit expanded view' : 'Expand assistant'} className="grid size-8 place-items-center rounded-lg text-[#7c80a1] hover:bg-violet-50"><Maximize size={15}/></button><button onClick={startNewChat} aria-label="Start a new chat" className="grid size-8 place-items-center rounded-lg text-[#7c80a1] hover:bg-violet-50"><Minus size={16}/></button><GlassThemeToggle /></div>
          </header>

          <div className="flex min-h-0 flex-1 gap-3 overflow-y-auto p-3 sm:gap-4 sm:p-4 lg:p-5">
            <main className="flex min-w-0 flex-1 flex-col rounded-2xl bg-white/70 p-3 sm:p-5">
              <section className="flex min-h-[155px] items-center gap-4 rounded-2xl px-2 py-2 sm:gap-6 sm:px-3">
                <div className="relative hidden size-[122px] shrink-0 overflow-hidden rounded-full border border-violet-200 bg-[#e9e0ff] shadow-[0_3px_14px_rgba(139,103,247,.24)] sm:block"><img src={activityEmblemReference} alt="MindMate AI emblem" className="absolute left-[-26px] top-[-19px] max-w-none w-[174px]" /></div>
                <div className="min-w-0"><h2 className="text-xl font-bold sm:text-[27px]">Hi {firstName}! <span className="text-violet-500">✦</span></h2><p className="mt-1 text-[14px] text-[#686d99]">I’m MindMate, your AI assistant.</p><p className="mt-2 text-[12px] leading-5 text-[#777c9f] sm:text-[13px]">Let’s make learning easier, plan smarter, reach goals, or just say hello!</p></div>
              </section>

              <div className="grid grid-cols-2 gap-2 xl:grid-cols-3">
                {[
                  { label: 'Plan my study schedule', icon: CalendarDays }, { label: 'Summarize my notes', icon: FileText }, { label: 'Explain a concept', icon: Lightbulb },
                  { label: 'Find resources', icon: BookOpen }, { label: 'Help with assignments', icon: SquarePen }, { label: 'Suggest career options', icon: Target },
                ].map(({ label, icon: Icon }) => <button key={label} onClick={() => setMessage(label)} className="flex min-h-8 items-center justify-center gap-1.5 rounded-full border border-violet-100 bg-[#f6f1ff] px-2 text-[11px] font-medium text-violet-700 hover:bg-[#eee5ff] sm:text-[14px]"><Icon size={12}/>{label}</button>)}
              </div>

              <div className="mt-4 flex min-h-[96px] gap-2.5"><img src={mindmateIntroEmblem} alt="" className="mt-1 size-5 rounded-full object-cover" /><div className="max-w-[510px] rounded-2xl rounded-tl-md bg-[#eee7ff] px-3.5 py-3 text-[12px] leading-[1.7] sm:px-4 sm:text-[13px]"><strong className="text-[#29245f]">Tell me what you’d like to do today, {firstName}.</strong><p className="mt-1 text-[#74789b]">I can help with your studies, plan your tasks, explain concepts, find resources, and much more. <span className="text-violet-500">✦</span></p></div></div>
              {conversation.map((entry, index) => entry.role === 'user'
                ? <div key={`${chatId}-${index}`} className="mt-2 flex justify-end"><div className="max-w-[80%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-violet-600 px-4 py-2.5 text-[13px] text-white">{entry.display ?? entry.content}</div></div>
                : <div key={`${chatId}-${index}`} className="mt-2 flex gap-2.5"><img src={mindmateIntroEmblem} alt="" className="mt-1 size-5 rounded-full object-cover" /><div role={entry.error ? 'alert' : undefined} className={`max-w-[510px] whitespace-pre-wrap rounded-2xl rounded-tl-md bg-[#eee7ff] px-3.5 py-3 text-[12px] leading-[1.7] sm:px-4 sm:text-[13px] ${entry.error ? 'text-rose-700' : 'text-[#29245f]'}`}>{entry.content}</div></div>)}
              {pending && <div className="mt-2 flex gap-2.5" role="status"><img src={mindmateIntroEmblem} alt="" className="mt-1 size-5 rounded-full object-cover" /><div className="rounded-2xl rounded-tl-md bg-[#eee7ff] px-3.5 py-3 text-[12px] leading-[1.7] text-[#74789b] sm:px-4 sm:text-[13px]"><span className="animate-pulse">MindMate is thinking…</span></div></div>}
              <div ref={chatEnd} />

              <div className="mt-auto pt-4"><div className="flex items-center justify-center gap-2 pb-3 text-[10px] text-[#9396b2]"><span className="h-px w-8 bg-violet-100"/>You can also try one of the suggestions above<span className="h-px w-8 bg-violet-100"/></div>
                <div className="relative">
                  <input ref={cameraInput} type="file" accept="image/*" capture="environment" className="sr-only" onChange={handleFilesSelected}/>
                  <input ref={photoInput} type="file" accept="image/*" multiple className="sr-only" onChange={handleFilesSelected}/>
                  <input ref={fileInput} type="file" multiple className="sr-only" onChange={handleFilesSelected}/>

                  {attachmentMenuOpen && (
                    <div role="menu" aria-label="Message tools" className="absolute bottom-[54px] left-0 z-30 w-[190px] rounded-2xl border border-violet-100 bg-white p-2 shadow-[0_10px_30px_rgba(70,54,130,.18)]">
                      <button type="button" role="menuitem" onClick={() => cameraInput.current?.click()} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[#343163] hover:bg-violet-50"><Camera size={18} className="text-violet-600"/>Camera</button>
                      <button type="button" role="menuitem" onClick={() => photoInput.current?.click()} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[#343163] hover:bg-violet-50"><Image size={18} className="text-violet-600"/>Photos</button>
                      <button type="button" role="menuitem" onClick={() => fileInput.current?.click()} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[#343163] hover:bg-violet-50"><FileText size={18} className="text-violet-600"/>Files</button>
                      <button type="button" role="menuitem" aria-expanded={pluginsOpen} onClick={() => { setPluginsOpen((open) => !open); setAttachmentMenuOpen(false) }} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[#343163] hover:bg-violet-50"><Plug size={18} className="text-violet-600"/>Plugins</button>
                      <div className="my-1 border-t border-violet-100"/>
                      <button type="button" role="menuitemcheckbox" aria-checked={thinkHarder} onClick={() => { setThinkHarder((enabled) => !enabled); setAttachmentMenuOpen(false) }} className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[#343163] hover:bg-violet-50"><Sparkles size={18} className="text-violet-600"/>Think harder{thinkHarder && <span className="ml-auto text-xs font-semibold text-violet-600">On</span>}</button>
                    </div>
                  )}

                  {pluginsOpen && (
                    <div role="status" className="absolute bottom-[54px] left-0 z-30 w-[250px] rounded-2xl border border-violet-100 bg-white p-4 shadow-[0_10px_30px_rgba(70,54,130,.18)]">
                      <div className="flex items-center justify-between gap-3"><strong className="flex items-center gap-2 text-sm text-[#343163]"><Plug size={16} className="text-violet-600"/>Plugins</strong><button type="button" aria-label="Close plugins panel" onClick={() => setPluginsOpen(false)} className="grid size-7 place-items-center rounded-full text-[#8589a8] hover:bg-violet-50"><X size={15}/></button></div>
                      <p className="mt-2 text-xs leading-5 text-[#777c9f]">No plugins are connected yet. You can still use the built-in quick actions above.</p>
                    </div>
                  )}

                  {attachedFiles.length > 0 && <div className="mb-2 flex flex-wrap gap-2" aria-label="Files attached to message">{attachedFiles.map((file, index) => <span key={`${file.name}-${file.lastModified}-${index}`} className="inline-flex max-w-[220px] items-center gap-1.5 rounded-full border border-violet-200 bg-[#f6f1ff] py-1 pl-3 pr-1.5 text-xs text-violet-800"><FileText size={13} className="shrink-0"/><span className="truncate">{file.name}</span><button type="button" aria-label={`Remove ${file.name}`} onClick={() => setAttachedFiles((current) => current.filter((_, fileIndex) => fileIndex !== index))} className="grid size-5 shrink-0 place-items-center rounded-full hover:bg-violet-100"><X size={12}/></button></span>)}</div>}
                  {thinkHarder && <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-violet-100 px-3 py-1 text-[11px] font-medium text-violet-700"><Sparkles size={12}/>Think harder is on</div>}

                  <form onSubmit={(event) => { event.preventDefault(); void submitMessage() }} className="flex h-[46px] items-center gap-2 rounded-full border border-violet-200 bg-white px-3 shadow-[0_2px_9px_rgba(120,91,194,.05)]">
                    <button type="button" aria-label="Open message tools" aria-haspopup="menu" aria-expanded={attachmentMenuOpen} onClick={() => { setAttachmentMenuOpen((open) => !open); setPluginsOpen(false) }} className="grid size-8 shrink-0 place-items-center rounded-full text-violet-500 transition hover:bg-violet-50"><Paperclip size={17}/></button>
                    <input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Type your message here..." aria-label="Type your message" className="min-w-0 flex-1 bg-transparent text-[13px] outline-none placeholder:text-[#9a9cba]"/>
                    <button type="submit" aria-label="Send message" disabled={pending || (!message.trim() && attachedFiles.length === 0)} className="grid size-[30px] shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#9851ff] to-[#6551ee] text-white hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50"><Send size={14}/></button>
                  </form>
                </div>
                <div className="mt-2 flex justify-between text-[10px] text-[#8d91ad]"><span>♧ &nbsp;Feel free to ask!</span><span>✦ &nbsp;Powered by MindMate AI</span></div>
              </div>
            </main>

            <aside className="hidden w-[205px] shrink-0 flex-col gap-3 lg:flex xl:w-[220px]">
              <section className="rounded-2xl bg-white/75 p-4"><h3 className="flex items-center gap-2 text-[14px] font-bold"><Sparkles size={15} className="text-violet-600"/>Quick Actions</h3><div className="mt-3 space-y-2.5">{quickActions.map(({ label, detail, icon: Icon, prompt }) => <button key={label} onClick={() => setMessage(prompt)} className="flex w-full items-center gap-2.5 rounded-lg p-1 text-left hover:bg-violet-50"><span className="grid size-7 shrink-0 place-items-center rounded-lg bg-[#f0e9ff] text-violet-600"><Icon size={15}/></span><span><strong className="block text-[11px] font-semibold">{label}</strong><small className="mt-0.5 block text-[10px] text-[#8589a8]">{detail}</small></span></button>)}</div></section>
              <section className="rounded-2xl bg-white/75 p-4"><h3 className="flex items-center gap-2 text-[13px] font-bold"><Brain size={16} className="text-violet-600"/>MindMate Remembers</h3><p className="mt-3 text-[11px] leading-[1.6] text-[#8589a8]">Your preferences, goals and knowledge help me get to know you better.</p><a href="/memory" className="mt-2 inline-flex items-center gap-1 rounded-full bg-[#f1eaff] px-3 py-1.5 text-[11px] font-medium text-violet-700 hover:bg-[#e9ddff]">View Memory <ArrowUpRight size={12}/></a></section>
              <div className="relative mt-auto flex min-h-[150px] items-center justify-center overflow-hidden rounded-t-full bg-[radial-gradient(circle_at_50%_75%,#ddd0ff_0%,#eee8ff_50%,transparent_72%)]"><div className="relative size-[90px] overflow-hidden rounded-full border border-violet-200 bg-[#e9e0ff] shadow-[0_4px_18px_rgba(139,103,247,.27)]"><img src={activityEmblemReference} alt="MindMate AI emblem" className="absolute left-[-19px] top-[-14px] max-w-none w-[128px]"/></div></div>
            </aside>
          </div>
        </div>
      </section>
    </div>
  )
}

function PanelIcon() { return <span className="flex size-4 items-center justify-center rounded border border-current"><span className="h-full w-[5px] border-r border-current"/></span> }

export default Assistant
