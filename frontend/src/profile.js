export const PROFILE_KEY = 'campustwin.demo.profile.v1'
export const PROFILE_LABELS = { user: 'Usuario común', admin: 'Secretaría / Administrador' }

export function readProfile(storage) {
  try {
    const value = (storage || window.localStorage).getItem(PROFILE_KEY)
    return Object.hasOwn(PROFILE_LABELS, value) ? value : null
  } catch { return null }
}

export function saveProfile(profile) {
  try { window.localStorage.setItem(PROFILE_KEY, profile) } catch { /* La selección sigue funcionando en memoria. */ }
}

export function clearProfile() {
  try { window.localStorage.removeItem(PROFILE_KEY) } catch { /* Solo se restablece la selección de esta demostración. */ }
}

export function viewForProfile(view, profile) {
  return view === 'admin' && profile !== 'admin' ? 'spaces' : view
}
