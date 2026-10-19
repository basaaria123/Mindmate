import { useState, type FormEvent, type ReactNode } from 'react'
import {
  Atom, Bell, BookOpen, Box, ChevronDown, ChevronRight, Database, GitBranch,
  Globe2, Headset, Info, KeyRound, LogOut, MessageSquare, Moon, Network,
  Pencil, ShieldCheck, SlidersHorizontal, Sparkles, Hash,
} from 'lucide-react'
import { useNavigate } from 'react-router'
import mindmateEmblem from '../assets/mindmate-intro-emblem.png'
import { useMindMateTheme } from '../theme'

type StoredProfile = { name?: string; firstName?: string; lastName?: string; email?: string }

function getStoredProfile(): StoredProfile {
  try {
    const raw = window.localStorage.getItem('mindmate-user-profile')
    return raw ? (JSON.parse(raw) as StoredProfile) : {}
  } catch {
    return {}
  }
}

function readableName(email: string) {
  return (email.split('@')[0] ?? '')
    .replace(/[._+-]+/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function SettingsPage() {
  const navigate = useNavigate()
  const { sleepMode, toggleSleepMode } = useMindMateTheme()
  const [profile, setProfile] = useState<StoredProfile>(getStoredProfile)
  const [isEditingProfile, setIsEditingProfile] = useState(false)
  const [profileError, setProfileError] = useState('')
  const [profileDraft, setProfileDraft] = useState({ firstName: '', lastName: '', email: '' })
  const email = profile.email || 'Sign in to add your email'
  const name = profile.name || (profile.email ? readableName(profile.email) : 'MindMate learner')
  const initials = name.split(/\s+/).filter(Boolean).slice(0, 2)
    .map((part) => part[0]?.toUpperCase()).join('') || 'M'
  const [language, setLanguage] = useState('English')

  function openProfileEditor() {
    const nameParts = (profile.name ?? '').trim().split(/\s+/).filter(Boolean)
    const fallbackName = profile.email ? readableName(profile.email).split(' ') : []
    setProfileDraft({
      firstName: profile.firstName || nameParts[0] || fallbackName[0] || '',
      lastName: profile.lastName || nameParts.slice(1).join(' ') || fallbackName.slice(1).join(' '),
      email: profile.email || '',
    })
    setProfileError('')
    setIsEditingProfile(true)
  }

  function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const firstName = profileDraft.firstName.trim()
    const lastName = profileDraft.lastName.trim()
    const nextProfile: StoredProfile = {
      ...profile,
      firstName,
      lastName,
      name: `${firstName} ${lastName}`.trim(),
      email: profileDraft.email.trim(),
    }

    try {
      window.localStorage.setItem('mindmate-user-profile', JSON.stringify(nextProfile))
      setProfile(nextProfile)
      setIsEditingProfile(false)
      window.dispatchEvent(new Event('mindmate:profile-updated'))
    } catch {
      setProfileError('Your changes could not be saved on this device. Please try again.')
    }
  }

  function logOut() {
    window.localStorage.removeItem('mindmate-user-profile')
    navigate('/welcome')
  }

  return (
    <div className="mm-settings-page space-y-5 pb-2">
      <header className="flex items-center gap-3 px-1 pt-1">
        <span className="grid size-12 place-items-center rounded-2xl bg-violet-100 text-violet-600"><SlidersHorizontal size={25} /></span>
        <div>
          <h1 className="text-2xl font-bold leading-tight text-[#211e58] sm:text-[28px]">Settings</h1>
          <p className="mt-1 text-sm text-[#7379a8]">Manage your account, preferences and application settings.</p>
        </div>
      </header>
      <section className="mm-settings-hero relative min-h-[226px] overflow-hidden rounded-[22px] border border-violet-200/80 bg-gradient-to-r from-white via-[#f5f1ff] to-[#e5dcff] p-5 shadow-[0_12px_35px_rgba(93,73,173,.08)] sm:p-6">
        <div className="pointer-events-none absolute -right-8 -top-24 size-72 rounded-full bg-violet-300/25 blur-3xl" />
        <div className="pointer-events-none absolute right-[12%] top-4 size-2 rounded-full bg-white shadow-[0_0_18px_8px_rgba(255,255,255,.95)]" />
        <div className="pointer-events-none absolute right-[22%] top-16 size-1.5 rounded-full bg-white shadow-[0_0_14px_6px_rgba(255,255,255,.9)]" />
        <div className="pointer-events-none absolute bottom-0 right-0 h-44 w-[54%] bg-gradient-to-l from-violet-200/35 to-transparent" />
        <div className="relative z-10 flex h-full flex-col justify-between gap-5 sm:flex-row sm:items-end">
          <div className="max-w-[650px]">

            <div className="flex max-w-[600px] items-center gap-4 rounded-2xl border border-white/90 bg-white/85 p-3 shadow-[0_8px_22px_rgba(82,62,156,.08)] backdrop-blur sm:min-w-[460px]">
              <div className="grid size-[58px] shrink-0 place-items-center rounded-full bg-gradient-to-br from-[#a58bff] to-[#7252ed] text-lg font-semibold text-white shadow-md">{initials}</div>
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-base font-bold text-[#211e58]">{name}</h2>
                <p className="truncate text-sm text-[#7b81ad]">{email}</p>
                <span className="mt-1 inline-flex rounded-full bg-violet-100 px-2.5 py-0.5 text-[11px] font-semibold text-violet-700">MindMate account</span>
              </div>
              <button type="button" onClick={openProfileEditor} className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-gradient-to-r from-[#8953f5] to-[#6259ed] px-3 py-2 text-xs font-semibold text-white shadow-sm hover:brightness-105">
                <Pencil size={14} /> <span className="hidden sm:inline">Edit Profile</span>
              </button>
            </div>
          </div>
          <div className="pointer-events-none absolute right-5 top-2 hidden h-[190px] w-[230px] items-center justify-center sm:flex lg:right-12 lg:w-[270px]">
            <div className="absolute size-44 rounded-full bg-white/60 shadow-[0_0_65px_32px_rgba(255,255,255,.65)] lg:size-52" />
            <img src={mindmateEmblem} alt="" className="relative z-10 size-44 rounded-full object-cover drop-shadow-[0_12px_18px_rgba(116,82,211,.35)] lg:size-52" />
            <Sparkles className="absolute right-5 top-4 text-white drop-shadow-[0_0_8px_rgba(144,100,255,.9)]" size={24} />
            <Sparkles className="absolute bottom-5 left-4 text-white drop-shadow-[0_0_8px_rgba(144,100,255,.9)]" size={17} />
          </div>
        </div>
      </section>

      {isEditingProfile && (
        <div className="fixed inset-0 z-[120] grid place-items-center overflow-y-auto bg-slate-950/60 p-4 backdrop-blur-sm" onMouseDown={(event) => { if (event.target === event.currentTarget) setIsEditingProfile(false) }}>
          <section role="dialog" aria-modal="true" aria-labelledby="edit-profile-title" className={`w-full max-w-md rounded-2xl border p-6 shadow-2xl ${sleepMode ? 'border-[#393451] bg-[#171b30] text-white' : 'border-violet-100 bg-white text-[#211e58]'}`}>
            <h2 id="edit-profile-title" className="text-xl font-bold">Edit Profile</h2>
            <p className={`mt-1 text-sm ${sleepMode ? 'text-[#aaa6cb]' : 'text-[#7379a8]'}`}>Update your account name and email address.</p>
            <form onSubmit={saveProfile} className="mt-5 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-medium">First name
                  <input autoFocus required value={profileDraft.firstName} onChange={(event) => setProfileDraft((draft) => ({ ...draft, firstName: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-violet-200 bg-white px-3 py-2.5 text-sm text-[#211e58] outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20" />
                </label>
                <label className="block text-sm font-medium">Last name
                  <input required value={profileDraft.lastName} onChange={(event) => setProfileDraft((draft) => ({ ...draft, lastName: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-violet-200 bg-white px-3 py-2.5 text-sm text-[#211e58] outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20" />
                </label>
              </div>
              <label className="block text-sm font-medium">Email address
                <input type="email" autoComplete="email" required value={profileDraft.email} onChange={(event) => setProfileDraft((draft) => ({ ...draft, email: event.target.value }))} className="mt-1.5 w-full rounded-xl border border-violet-200 bg-white px-3 py-2.5 text-sm text-[#211e58] outline-none focus:border-violet-500 focus:ring-2 focus:ring-violet-500/20" />
              </label>
              {profileError && <p role="alert" className="text-sm text-rose-500">{profileError}</p>}
              <div className="flex justify-end gap-3 pt-1">
                <button type="button" onClick={() => setIsEditingProfile(false)} className={`rounded-xl border px-4 py-2 text-sm font-semibold ${sleepMode ? 'border-[#393451] text-[#e7e3ff] hover:bg-white/5' : 'border-violet-200 text-[#6256a5] hover:bg-violet-50'}`}>Cancel</button>
                <button type="submit" className="rounded-xl bg-gradient-to-r from-[#8953f5] to-[#6259ed] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:brightness-105">Save changes</button>
              </div>
            </form>
          </section>
        </div>
      )}

      <div className="grid gap-4 xl:grid-cols-2">
        <SettingsPanel icon={<ShieldCheck />} title="Credentials & Connections" subtitle="Manage your API keys and connected services.">
          <SettingsRow icon={<KeyRound />} label="OpenAI API Key" status="Connected" />
          <SettingsRow icon={<GitBranch />} label="GitHub" status="Connected" />
          <SettingsRow icon={<Network />} label="Notion" status="Connected" />
          <SettingsRow icon={<Atom />} label="Slack" status="Not connected" muted />
        </SettingsPanel>

        <SettingsPanel icon={<SlidersHorizontal />} title="Preferences" subtitle="Customize your experience and app behavior.">
          <div className="flex min-h-[68px] items-center gap-4 border-b border-violet-100 px-4 py-3">
            <Moon className="shrink-0 text-[#24215f]" size={22} />
            <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-[#29265f]">Dark Mode</p><p className="mt-0.5 text-xs text-[#8086b2]">Switch between light and dark themes.</p></div>
            <button type="button" role="switch" aria-checked={sleepMode} aria-label="Dark Mode" onClick={toggleSleepMode} className={`relative h-7 w-12 rounded-full transition ${sleepMode ? 'bg-violet-700' : 'bg-violet-300'}`}>
              <span className={`absolute top-1 size-5 rounded-full bg-white shadow transition-all ${sleepMode ? 'left-[26px]' : 'left-1'}`} />
            </button>
          </div>
          <div className="flex min-h-[68px] items-center gap-4 border-b border-violet-100 px-4 py-3">
            <Globe2 className="shrink-0 text-[#24215f]" size={22} />
            <div className="min-w-0 flex-1"><p className="text-sm font-semibold text-[#29265f]">Language</p><p className="mt-0.5 text-xs text-[#8086b2]">Choose your preferred language.</p></div>
            <label className="sr-only" htmlFor="settings-language">Language</label>
            <span className="relative">
              <select id="settings-language" value={language} onChange={(event) => setLanguage(event.target.value)} className="appearance-none rounded-xl border border-violet-200 bg-white py-2 pl-3 pr-9 text-xs font-medium text-[#393665] outline-none focus:border-violet-400">
                <option>English</option><option>Hindi</option><option>Telugu</option>
              </select>
              <ChevronDown className="pointer-events-none absolute right-2.5 top-2.5 text-[#777da8]" size={14} />
            </span>
          </div>
          <SettingsRow icon={<Bell />} label="Notifications" description="Manage your notification preferences." />
        </SettingsPanel>

        <SettingsPanel icon={<Info />} title="Application Details" subtitle="View information about the app and your workspace.">
          <SettingsRow icon={<Box />} label="Version" value="v1.0.0" />
          <SettingsRow icon={<Database />} label="Environment" value="Production" />
          <SettingsRow icon={<Hash />} label="Workspace ID" value="mm_47fa2c9e" />
          <SettingsRow icon={<Bell />} label="Last login" value="Today" />
        </SettingsPanel>

        <SettingsPanel icon={<Headset />} title="Support & Help" subtitle="Get help, share feedback or contact the team.">
          <SettingsRow icon={<BookOpen />} label="Help Center" />
          <SettingsRow icon={<MessageSquare />} label="Send Feedback" />
          <SettingsRow icon={<Headset />} label="Contact Support" />
        </SettingsPanel>
      </div>

      <button type="button" onClick={logOut} className="flex w-full items-center gap-4 rounded-2xl border border-rose-100 bg-gradient-to-r from-rose-50 to-white px-5 py-4 text-left shadow-sm transition hover:border-rose-200 hover:shadow-md">
        <span className="grid size-11 place-items-center rounded-xl bg-white text-pink-500"><LogOut size={23} /></span>
        <span className="min-w-0 flex-1"><strong className="block text-sm font-bold text-pink-600">Log out</strong><span className="mt-0.5 block text-xs text-[#8588ae]">Sign out from your account on this device.</span></span>
        <ChevronRight className="text-pink-400" size={20} />
      </button>
    </div>
  )
}

function SettingsPanel({ icon, title, subtitle, children }: { icon: ReactNode; title: string; subtitle: string; children: ReactNode }) {
  return (
    <section className="mm-settings-panel rounded-[20px] border border-violet-200/80 bg-white/90 p-4 shadow-[0_8px_24px_rgba(95,76,170,.06)] sm:p-5">
      <div className="mb-3 flex items-center gap-3">
        <span className="grid size-10 shrink-0 place-items-center rounded-full bg-violet-50 text-violet-700">{icon}</span>
        <div className="min-w-0"><h2 className="text-sm font-bold text-[#28255e] sm:text-base">{title}</h2><p className="mt-0.5 text-xs text-[#8086b2]">{subtitle}</p></div>
      </div>
      <div className="mm-settings-rows overflow-hidden rounded-xl border border-violet-100 bg-white/70">{children}</div>
    </section>
  )
}

function SettingsRow({ icon, label, description, status, value, muted = false }: { icon: ReactNode; label: string; description?: string; status?: string; value?: string; muted?: boolean }) {
  return (
    <button type="button" className="flex min-h-[52px] w-full items-center gap-3 border-b border-violet-100 px-3 py-2.5 text-left last:border-0 hover:bg-violet-50/70">
      <span className="grid size-7 shrink-0 place-items-center text-[#26245d]">{icon}</span>
      <span className="min-w-0 flex-1"><span className="block truncate text-xs font-medium text-[#343163] sm:text-sm">{label}</span>{description && <span className="mt-0.5 block truncate text-[11px] text-[#898fb8]">{description}</span>}</span>
      {status && <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold ${muted ? 'bg-violet-50 text-violet-500' : 'bg-emerald-50 text-emerald-600'}`}>{status}</span>}
      {value && <span className="text-[11px] text-[#848ab2] sm:text-xs">{value}</span>}
      {!status && !value && <ChevronRight size={17} className="shrink-0 text-[#8188b5]" />}
      {status && <ChevronRight size={16} className="shrink-0 text-[#8188b5]" />}
    </button>
  )
}

export default SettingsPage
