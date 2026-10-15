import { useEffect, useState, type CSSProperties, type FormEvent, type ReactNode } from 'react'
import {
  ArrowRight,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  Compass,
  Target,
  UsersRound,
} from 'lucide-react'
import { useNavigate } from 'react-router'
import {
  extractProfile,
  getProfile,
  updateProfile,
} from '../services/api'
import splashMotion from '../assets/mindmate-splash.mp4'
import mindmateWordmark from '../assets/mindmate-wordmark.svg'
import mindmateIntroEmblem from '../assets/mindmate-intro-emblem.png'
import './Onboarding.css'

type AccountMode = 'signin' | 'signup'

const ageOptions = ['Under 18', '18–24', '25–34', '35–44', '45+']
const roleOptions = ['Student', 'Professional', 'Entrepreneur', 'Researcher', 'Other']
const goalOptions = ['Learn faster', 'Build skills', 'Stay organized']

function Onboarding() {
  const navigate = useNavigate()
  const [showSplash, setShowSplash] = useState(true)
  const [splashFading, setSplashFading] = useState(false)
  const [flowStep, setFlowStep] = useState<'account' | 'profile-intro' | 'profile'>('account')
  const [accountMode, setAccountMode] = useState<AccountMode>('signin')
  const [age, setAge] = useState('18–24')
  const [role, setRole] = useState('Student')
  const [goals, setGoals] = useState<string[]>(['Learn faster', 'Build skills', 'Stay organized'])
  const [goalsExpanded, setGoalsExpanded] = useState(true)
  const [personalize, setPersonalize] = useState(true)
  const [profileDescription, setProfileDescription] = useState('')
  const [savePreferences, setSavePreferences] = useState(true)
  const [isSavingProfile, setIsSavingProfile] = useState(false)
  const [profileError, setProfileError] = useState<string | null>(null)
  useEffect(() => {
    const fallback = window.setTimeout(() => setShowSplash(false), 5000)
    return () => window.clearTimeout(fallback)
  }, [])

  useEffect(() => {
    if (flowStep !== 'profile') return
    let isCurrent = true
    getProfile()
      .then((profile) => {
        if (!isCurrent) return
        if (profile.targetRole) setRole(profile.targetRole)
        if (profile.goal) setGoals(profile.goal.split(', '))
      })
      .catch((error) => {
        if (isCurrent) {
          setProfileError(error instanceof Error ? error.message : 'Could not load your saved profile.')
        }
      })
    return () => { isCurrent = false }
  }, [flowStep])

  function handleAccountSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const emailField = accountMode === 'signin' ? 'signin-email' : 'signup-email'
    const email = String(formData.get(emailField) ?? '').trim()
    const enteredName = accountMode === 'signup'
      ? String(formData.get('signup-name') ?? '').trim()
      : email.split('@')[0].replace(/[._+-]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())

    window.localStorage.setItem(
      'mindmate-user-profile',
      JSON.stringify({ name: enteredName, email }),
    )

    if (accountMode === 'signup') setFlowStep('profile-intro')
    else navigate('/boot')
  }

  function toggleGoal(goal: string) {
    setGoals((current) =>
      current.includes(goal)
        ? current.filter((item) => item !== goal)
        : [...current, goal],
    )
  }

  async function finishSetup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setProfileError(null)
    setIsSavingProfile(true)
    try {
      let aiProfile = null
      if (profileDescription.trim()) {
        aiProfile = await extractProfile(profileDescription.trim())
        window.localStorage.setItem(
          'mindmate-ai-profile',
          JSON.stringify(aiProfile),
        )
      }
      if (savePreferences) {
        window.localStorage.setItem(
          'mindmate-profile-preferences',
          JSON.stringify({ age, role, goals, personalize }),
        )
        let name = 'MindMate learner'
        try {
          const account = JSON.parse(window.localStorage.getItem('mindmate-user-profile') ?? '{}') as { name?: string }
          name = account.name || name
        } catch {
          // Use the default display name if local account data cannot be read.
        }
        await updateProfile({ name, goal: goals.join(', '), targetRole: role, dailyMinutes: 60 })
      }
      navigate('/boot')
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : 'Could not save your profile. Please try again.')
    } finally {
      setIsSavingProfile(false)
    }
  }

  function skipSetup() {
    navigate('/boot')
  }

  if (showSplash) {
    return (
      <main className={`mm-splash${splashFading ? ' is-fading' : ''}`} aria-label="MindMate splash animation">
        <video
          className="mm-splash__video"
          src={splashMotion}
          autoPlay
          muted
          playsInline
          preload="auto"
          aria-label="MindMate animated logo"
          onEnded={() => {
            setSplashFading(true)
            window.setTimeout(() => setShowSplash(false), 450)
          }}
        />
      </main>
    )
  }

  if (flowStep === 'account') {
    return (
      <main className="mm-onboarding mm-onboarding--auth">
        <section className={`mm-auth${accountMode === 'signup' ? ' is-signup' : ''}`} aria-label="MindMate account access">
          <aside className={`mm-auth__welcome${accountMode === 'signup' ? ' is-signup' : ''}`}>
            <div className="mm-auth__welcome-content" key={accountMode}>
              <h1>{accountMode === 'signin' ? 'Hello, Friend!' : 'Welcome Back!'}</h1>
              <p>
                {accountMode === 'signin'
                  ? 'Register with your personal details to use all of site features'
                  : 'Already have an account? Sign in to continue managing your account.'}
              </p>
              <button
                className="mm-button mm-button--gloss"
                type="button"
                onClick={() => setAccountMode(accountMode === 'signin' ? 'signup' : 'signin')}
              >
                {accountMode === 'signin' ? 'SIGN UP' : 'Sign In'}
              </button>
            </div>
            <div className="mm-auth__decoration mm-auth__decoration--one" />
            <div className="mm-auth__decoration mm-auth__decoration--two" />
          </aside>

          <div className="mm-auth__form-wrap">
            <div className="mm-auth__form-content" key={`form-${accountMode}`}>
              <h2>{accountMode === 'signin' ? 'Sign In' : 'Create Account'}</h2>

              {accountMode === 'signin' ? (
                <>
                  <div className="mm-social-row" aria-label="Social sign-in options">
                    <button type="button" aria-label="Continue with Google" className="mm-social-button mm-social-button--google">G+</button>
                    <button type="button" aria-label="Continue with Facebook" className="mm-social-button mm-social-button--facebook">f</button>
                    <button type="button" aria-label="Continue with GitHub" className="mm-social-button mm-social-button--github"><svg width="21" height="21" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.387-1.333-1.756-1.333-1.756-1.09-.745.083-.729.083-.729 1.205.084 1.84 1.237 1.84 1.237 1.07 1.835 2.807 1.305 3.492.998.108-.775.418-1.305.762-1.605-2.665-.3-5.467-1.333-5.467-5.93 0-1.31.468-2.38 1.237-3.22-.124-.303-.536-1.523.117-3.176 0 0 1.008-.322 3.3 1.23a11.5 11.5 0 0 1 3.006-.404c1.02.005 2.047.138 3.006.404 2.29-1.552 3.297-1.23 3.297-1.23.655 1.653.243 2.873.12 3.176.77.84 1.235 1.91 1.235 3.22 0 4.61-2.807 5.626-5.48 5.92.43.372.814 1.102.814 2.222 0 1.604-.015 2.896-.015 3.29 0 .322.216.694.825.576C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/></svg></button>
                    <button type="button" aria-label="Continue with LinkedIn" className="mm-social-button mm-social-button--linkedin">in</button>
                  </div>
                  <p className="mm-auth__or">or use your email password</p>

                  <form className="mm-form mm-form--signin" onSubmit={handleAccountSubmit}>
                    <label className="mm-sr-only" htmlFor="signin-email">Email</label>
                    <input id="signin-email" name="signin-email" type="email" autoComplete="email" placeholder="Email" aria-label="Email" required />
                    <label className="mm-sr-only" htmlFor="signin-password">Password</label>
                    <input id="signin-password" type="password" autoComplete="current-password" placeholder="Password" aria-label="Password" minLength={6} required />
                    <button className="mm-text-button mm-form__forgot" type="button">Forget Your Password?</button>
                    <button className="mm-button mm-button--primary mm-form__submit" type="submit">
                      SIGN IN <ArrowRight size={17} />
                    </button>
                  </form>
                </>
              ) : (
                <>
                  <p className="mm-auth__subheading">Create an account to securely manage your personal details.</p>
                  <form className="mm-form mm-form--signup" onSubmit={handleAccountSubmit}>
                    <label htmlFor="signup-name">Full Name*</label>
                    <input id="signup-name" name="signup-name" autoComplete="name" placeholder="Priya Sharma" required />

                    <label htmlFor="signup-email">Email Address*</label>
                    <input id="signup-email" name="signup-email" type="email" autoComplete="email" placeholder="you@example.com" required />

                    <label htmlFor="signup-phone">Phone (optional)</label>
                    <input id="signup-phone" type="tel" autoComplete="tel" placeholder="+91 98765 43210" />
                    <span className="mm-form__hint">Used only for status updates.</span>

                    <label htmlFor="signup-password">Password*</label>
                    <input id="signup-password" type="password" autoComplete="new-password" placeholder="••••••••" minLength={6} required />
                    <span className="mm-form__hint">At least 6 characters.</span>

                    <button className="mm-button mm-button--primary mm-form__submit" type="submit">
                      <UsersRound size={18} /> Create Account
                    </button>
                  </form>
                </>
              )}
              <p className="mm-auth__demo-note">Demo only: account information is not sent to a server.</p>
            </div>
          </div>
        </section>
      </main>
    )
  }

  if (flowStep === 'profile-intro') {
    return (
      <main className="mm-onboarding mm-onboarding--profile mm-profile-intro-page">
        <div className="mm-onboarding__backdrop" aria-hidden="true" />
        <a className="mm-profile__brand" href="#intro" aria-label="MindMate">
          <img src={mindmateWordmark} alt="MindMate — Smarter minds. Brighter tomorrows." />
        </a>
        <section id="intro" className="mm-profile-intro" aria-labelledby="intro-title">
          <div className="mm-profile-intro__art" aria-hidden="true">
            <img src={mindmateIntroEmblem} alt="" />
          </div>
          <h1 id="intro-title">Tell MindMate about yourself<br/>and your needs</h1>
          <p>A few details help us make your workspace feel right for you.</p>
          <button className="mm-button mm-button--primary mm-profile-intro__button" type="button" onClick={() => setFlowStep('profile')}>
            Let’s personalize <ArrowRight size={19}/>
          </button>
        </section>
      </main>
    )
  }

  return (
    <main className="mm-onboarding mm-onboarding--profile">
      <div className="mm-onboarding__backdrop" aria-hidden="true" />

      <a className="mm-profile__brand" href="#top" aria-label="MindMate home">
        <img src={mindmateWordmark} alt="MindMate — Smarter minds. Brighter tomorrows." />
      </a>

      <section id="top" className="mm-profile" aria-labelledby="profile-title">
        <header className="mm-profile__intro">
          <h1 id="profile-title">Tell MindMate about yourself<br />and your needs</h1>
          <p>A few details help us make your workspace feel right for you.</p>
        </header>

        <form className="mm-profile-form" onSubmit={finishSetup}>
          <ProfileCard icon={<UsersRound />} title="Age group" description="Under 18 · 18–24 · 25–34 · 35–44 · 45+" delay="0ms">
            <div className="mm-choice-row">
              {ageOptions.map((option) => (
                <Choice key={option} label={option} selected={age === option} onClick={() => setAge(option)} />
              ))}
            </div>
          </ProfileCard>

          <ProfileCard icon={<BriefcaseBusiness />} title="What do you do?" delay="120ms">
            <div className="mm-choice-row">
              {roleOptions.map((option) => (
                <Choice key={option} label={option} selected={role === option} onClick={() => setRole(option)} />
              ))}
            </div>
          </ProfileCard>

          <section className={`mm-profile-card mm-profile-card--goals${goalsExpanded ? ' is-expanded' : ''}`} style={{ '--card-delay': '240ms' } as CSSProperties}>
            <div className="mm-profile-card__icon"><Target /></div>
            <div className="mm-profile-card__content">
              <button
                className="mm-profile-card__toggle"
                type="button"
                aria-expanded={goalsExpanded}
                onClick={() => setGoalsExpanded((expanded) => !expanded)}
              >
                <span>
                  <strong>Goals and preferences</strong>
                  <span className="mm-profile-card__description">Main goals, priorities, interests, and preferred working style</span>
                </span>
                <ChevronRight size={21} />
              </button>
              {goalsExpanded && (
                <div className="mm-goal-row">
                  {goalOptions.map((goal) => {
                    const selected = goals.includes(goal)
                    return (
                      <button
                        className={`mm-goal-chip ${selected ? 'is-selected' : ''}`}
                        key={goal}
                        type="button"
                        aria-pressed={selected}
                        onClick={() => toggleGoal(goal)}
                      >
                        {goal}{selected && <span aria-hidden="true">×</span>}
                      </button>
                    )
                  })}
                </div>
              )}
            </div>
          </section>
          <ProfileCard
            icon={<Target />}
            title="Tell us about yourself"
            description="Share your education, skills, interests, and career goals."
            delay="300ms"
          >
            <textarea
            className="mm-profile-description"
            style={{
              color: '#262251',
              backgroundColor: '#ffffff',
              width: '100%',
              minHeight: '150px',
              boxSizing: 'border-box',
              resize: 'vertical',
            }}
            value={profileDescription}
            onChange={(event) => setProfileDescription(event.target.value)}
            placeholder="I'm studying computer science, know Python, and want to become an AI engineer..."
            rows={6}
            maxLength={2000}aria-label="Describe your background and goals"
            />

          </ProfileCard>


          {goalsExpanded && (
            <div className="mm-preferences">
              <label className="mm-preference">
                <input type="checkbox" checked={personalize} onChange={(event) => setPersonalize(event.target.checked)} />
                <span><strong>Personalize recommendations</strong><small>Get suggestions tailored to your goals.</small></span>
              </label>
              <label className="mm-preference">
                <input type="checkbox" checked={savePreferences} onChange={(event) => setSavePreferences(event.target.checked)} />
                <span><strong>Save preferences</strong><small>Remember your choices for next time.</small></span>
              </label>
            </div>
          )}

          {profileError && <p role="alert" className="text-sm text-rose-700">{profileError}</p>}

          <footer className="mm-profile__actions">
            <p><Compass size={17} /> You can skip optional questions and choose what MindMate remembers.</p>
            <div className="mm-profile__action-buttons">
              <button className="mm-button mm-button--secondary" type="button" onClick={skipSetup}>Skip for now</button>
              <button className="mm-button mm-button--primary" type="submit" disabled={isSavingProfile}>{isSavingProfile ? 'Saving…' : 'Continue'} {!isSavingProfile && <ArrowRight size={17} />}</button>
            </div>
          </footer>
        </form>
      </section>
    </main>
  )
}

function ProfileCard({
  icon,
  title,
  description,
  delay,
  children,
}: {
  icon: ReactNode
  title: string
  description?: string
  delay: string
  children: ReactNode
}) {
  return (
    <section className="mm-profile-card" style={{ '--card-delay': delay } as CSSProperties}>
      <div className="mm-profile-card__icon">{icon}</div>
      <div className="mm-profile-card__content">
        <div className="mm-profile-card__heading">
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        {children}
      </div>
    </section>
  )
}

function Choice({
  label,
  selected,
  onClick,
}: {
  label: string
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      className={`mm-choice ${selected ? 'is-selected' : ''}`}
      type="button"
      aria-pressed={selected}
      onClick={onClick}
    >
      {selected && <Check size={15} />}
      {label}
    </button>
  )
}

export default Onboarding
