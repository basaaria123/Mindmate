export function getFirstNameFromEmail() {
  try {
    const savedProfile = window.localStorage.getItem('mindmate-user-profile')
    const email = savedProfile
      ? (JSON.parse(savedProfile) as { email?: string }).email?.trim()
      : undefined
    const firstName = email?.split('@')[0]?.split(/[._+-]/)[0]?.trim()

    if (!firstName) return 'Learner'
    return firstName.charAt(0).toLocaleUpperCase() + firstName.slice(1)
  } catch {
    return 'Learner'
  }
}
