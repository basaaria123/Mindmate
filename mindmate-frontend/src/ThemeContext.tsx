import { createContext, useContext, useState, type ReactNode } from 'react'
import { Moon, Sun } from 'lucide-react'

type ThemeContextValue = {
  sleepMode: boolean
  toggleSleepMode: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [sleepMode, setSleepMode] = useState(() =>
    typeof window !== 'undefined' && window.localStorage.getItem('mindmate-theme') === 'sleep',
  )

  function toggleSleepMode() {
    setSleepMode((current) => {
      const next = !current
      window.localStorage.setItem('mindmate-theme', next ? 'sleep' : 'day')
      return next
    })
  }

  return (
    <ThemeContext.Provider value={{ sleepMode, toggleSleepMode }}>
      <div className="mindmate-theme" data-theme={sleepMode ? 'sleep' : 'day'}>
        {children}
      </div>
    </ThemeContext.Provider>
  )
}

export function useMindMateTheme() {
  const theme = useContext(ThemeContext)
  if (!theme) throw new Error('useMindMateTheme must be used inside ThemeProvider')
  return theme
}

export function GlassThemeToggle() {
  const { sleepMode, toggleSleepMode } = useMindMateTheme()

  return (
    <button
      type="button"
      role="switch"
      aria-checked={sleepMode}
      aria-label={sleepMode ? 'Switch to day mode' : 'Switch to sleep mode'}
      title={sleepMode ? 'Switch to day mode' : 'Switch to sleep mode'}
      onClick={toggleSleepMode}
      className="mm-glass-toggle"
      data-sleep={sleepMode}
    >
      <span className="mm-glass-toggle__thumb" aria-hidden="true">
        {sleepMode ? <Moon size={16} fill="currentColor" /> : <Sun size={17} />}
      </span>
      <span className={`mm-glass-toggle__option ${!sleepMode ? 'is-active' : ''}`}>
        <Sun size={14} /> Day
      </span>
      <span className={`mm-glass-toggle__option ${sleepMode ? 'is-active' : ''}`}>
        <Moon size={13} /> Sleep
      </span>
    </button>
  )
}
