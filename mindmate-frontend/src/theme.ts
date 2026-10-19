import { createContext, useContext } from 'react'

export type ThemeContextValue = {
  sleepMode: boolean
  toggleSleepMode: () => void
}

export const ThemeContext = createContext<ThemeContextValue | null>(null)

export function useMindMateTheme() {
  const theme = useContext(ThemeContext)
  if (!theme) throw new Error('useMindMateTheme must be used inside ThemeProvider')
  return theme
}
