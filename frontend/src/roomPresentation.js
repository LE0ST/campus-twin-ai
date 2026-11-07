export const equipmentLabels = { pc: 'PCs', projector: 'Proyector', whiteboard: 'Pizarra', wifi: 'Wi-Fi' }

export function reservationLabel(room) {
  if (room.reservation_state === 'reserved') return 'Reservada'
  return room.bookable ? 'Disponible' : 'No reservable'
}

export function occupancyInfo(room, now = Date.now()) {
  const sample = room.occupancy
  const observed = Date.parse(sample?.observed_at)
  const observedAt = Number.isFinite(observed) ? new Date(observed).toLocaleTimeString('es-PE', { timeZone: 'America/Lima', hour12: false }) : null
  const sourceLabel = sample?.source_id && sample?.mode === 'live_camera' ? `Fuente: ${sample.source_id} · Cámara en vivo` : null
  const unknown = (reason) => ({
    label: 'Ocupación desconocida', short: reason === 'no_sensor' ? 'Desconocida' : reason === 'stale' ? 'Lectura vencida' : 'Sin lectura',
    tone: 'neutral', known: false, observedAt, sourceLabel,
    detail: ({ no_sensor: 'Este ambiente no tiene sensor.', no_data: 'Esperando la primera lectura autorizada.', stale: 'La última lectura venció. Esperando una nueva medición.', camera_error: 'La cámara reportó un error. No hay un conteo válido.', recorded_sample: 'Una grabación no representa la ocupación actual.', invalid: 'La medición recibida no es válida.' })[reason] || 'Sin una medición actual válida.',
  })
  if (!sample) return unknown('no_data')
  if (sample.mode === 'authorized_clip') return unknown('recorded_sample')
  if (sample.state === 'unknown') return unknown(sample.reason)
  const validUntil = Date.parse(sample.expires_at)
  if (Number.isFinite(validUntil) && validUntil <= now) return unknown('stale')
  if (sample.mode !== 'live_camera' || !Number.isFinite(validUntil) || !Number.isFinite(observed) ||
      !Number.isInteger(sample.count) || sample.count < 0) return unknown('invalid')
  const metadata = { known: true, observedAt, sourceLabel, detail: 'Medición autorizada y vigente.' }
  if (sample.state === 'no_detections' && sample.count === 0) {
    return { ...metadata, label: 'Sin personas detectadas', short: 'Sin detecciones', tone: 'amber' }
  }
  if (sample.state === 'people_detected' && sample.count > 0) {
    const label = `${sample.count} ${sample.count === 1 ? 'persona detectada' : 'personas detectadas'}`
    return { ...metadata, label, short: label, tone: 'green' }
  }
  return unknown('invalid')
}

export function localDateLabel(date) {
  const parsed = new Date(`${date}T12:00:00-05:00`)
  return Number.isNaN(parsed.getTime()) ? 'Elige una fecha' : parsed.toLocaleDateString('es-PE', { timeZone: 'America/Lima', day: '2-digit', month: 'short' })
}

export function slotLabel(slot) {
  const hour = Number(slot.slice(1))
  return `${String(hour).padStart(2, '0')}:00–${String(hour + 1).padStart(2, '0')}:00`
}
