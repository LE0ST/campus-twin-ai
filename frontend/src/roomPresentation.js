export const equipmentLabels = { pc: 'PCs', projector: 'Proyector', whiteboard: 'Pizarra', wifi: 'Wi-Fi' }

export function reservationLabel(room) {
  if (room.reservation_state === 'reserved') return 'Reservada'
  return room.bookable ? 'Disponible' : 'No reservable'
}

export function occupancyInfo(room, now = Date.now()) {
  const sample = room.occupancy
  const unknown = { label: 'Ocupación desconocida', short: 'Sin lectura', tone: 'neutral', known: false }
  if (!sample || sample.state === 'unknown') {
    return { ...unknown, short: sample?.reason === 'no_sensor' ? 'Sin sensor' : 'Sin lectura' }
  }
  const validUntil = Date.parse(sample.expires_at)
  if (sample.mode !== 'live_camera' || !Number.isFinite(validUntil) || validUntil <= now ||
      !Number.isInteger(sample.count) || sample.count < 0) return unknown
  if (sample.state === 'no_detections' && sample.count === 0) {
    return { label: 'Sin personas detectadas', short: 'Sin detecciones', tone: 'amber', known: true }
  }
  if (sample.state === 'people_detected' && sample.count > 0) {
    const label = `${sample.count} ${sample.count === 1 ? 'persona detectada' : 'personas detectadas'}`
    return { label, short: label, tone: 'green', known: true }
  }
  return unknown
}

export function localDateLabel(date) {
  const parsed = new Date(`${date}T12:00:00-05:00`)
  return Number.isNaN(parsed.getTime()) ? 'Elige una fecha' : parsed.toLocaleDateString('es-PE', { timeZone: 'America/Lima', day: '2-digit', month: 'short' })
}

export function slotLabel(slot) {
  const hour = Number(slot.slice(1))
  return `${String(hour).padStart(2, '0')}:00–${String(hour + 1).padStart(2, '0')}:00`
}
