export function limaDate(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-US', { timeZone: 'America/Lima', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(now)
  const get = (type) => parts.find((part) => part.type === type).value
  return `${get('year')}-${get('month')}-${get('day')}`
}

export function lastAllowedDate(today) {
  const date = new Date(`${today}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + 7)
  return date.toISOString().slice(0, 10)
}

export function selectionError(date, slot, now = new Date()) {
  const today = limaDate(now)
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(`${date}T00:00:00Z`)) || new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) !== date) return 'Elige una fecha válida.'
  if (date < today || date > lastAllowedDate(today)) return 'Elige una fecha entre hoy y los próximos 7 días.'
  if (!['S09', 'S10', 'S11', 'S14', 'S15', 'S16', 'S17', 'S18'].includes(slot)) return 'Elige una franja válida.'
  // Lima is UTC−05:00; compare against the actual start, including the exact boundary.
  if (now >= new Date(`${date}T${slot.slice(1)}:00:00-05:00`)) return 'La franja ya comenzó; elige otra.'
  return ''
}
