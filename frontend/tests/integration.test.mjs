import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { occupancyInfo, reservationLabel } from '../src/roomPresentation.js'
import { AGENDA_SLOTS, fetchAgenda, summarizeAgenda } from '../src/agenda.js'
import { readProfile, viewForProfile } from '../src/profile.js'

const now = Date.parse('2026-11-07T15:00:00Z')
const sample = (overrides = {}) => ({ occupancy: { state: 'no_detections', count: 0, mode: 'live_camera', source_id: 'vision-david', observed_at: '2026-11-07T15:00:00Z', expires_at: '2026-11-07T15:00:15Z', ...overrides } })

describe('Ocupación de David y caducidad', () => {
  it('presenta cero detecciones como inferencia vigente, sin afirmar una sala vacía', () => {
    const reading = occupancyInfo(sample(), now)
    assert.equal(reading.label, 'Sin personas detectadas')
    assert.equal(reading.known, true)
    assert.match(reading.sourceLabel, /vision-david/)
    assert.equal(reading.observedAt, '10:00:00')
  })
  it('caduca al alcanzar los 15 segundos y conserva hora/fuente, sin mostrar el conteo anterior', () => {
    assert.equal(occupancyInfo(sample(), now + 14999).known, true)
    const expired = occupancyInfo(sample(), now + 15000)
    assert.equal(expired.known, false)
    assert.equal(expired.label, 'Ocupación desconocida')
    assert.match(expired.detail, /venció/)
    assert.match(expired.sourceLabel, /vision-david/)
    assert.equal(expired.observedAt, '10:00:00')
  })
  it('respeta el estado stale enviado por el backend aunque el reloj del cliente sea anterior', () => {
    const expired = occupancyInfo(sample({ state: 'unknown', reason: 'stale', count: null }), now - 60000)
    assert.equal(expired.known, false)
    assert.equal(expired.short, 'Lectura vencida')
  })
  it('muestra un conteo positivo válido', () => {
    const reading = occupancyInfo(sample({ state: 'people_detected', count: 3 }), now)
    assert.equal(reading.label, '3 personas detectadas')
    assert.equal(reading.known, true)
  })
  it('no convierte ausencia, error de cámara o conteos inválidos en cero', () => {
    for (const count of [null, -1, 0.5, '0']) assert.equal(occupancyInfo(sample({ count }), now).known, false)
    assert.equal(occupancyInfo({}, now).known, false)
    assert.equal(occupancyInfo(sample({ state: 'unknown', reason: 'camera_error', count: null }), now).known, false)
    assert.equal(occupancyInfo(sample({ state: 'people_detected', count: 0 }), now).known, false)
    assert.equal(occupancyInfo(sample({ observed_at: 'invalid' }), now).known, false)
  })
  it('distingue una grabación y un ambiente sin sensor de ocupación actual', () => {
    assert.match(occupancyInfo(sample({ mode: 'authorized_clip' }), now).detail, /grabación/)
    const noSensor = { occupancy: { state: 'unknown', reason: 'no_sensor', count: null } }
    const reading = occupancyInfo(noSensor, now)
    assert.equal(reading.label, 'Ocupación desconocida')
    assert.equal(reading.short, 'Desconocida')
    assert.match(reading.detail, /no tiene sensor/)
  })
  it('muestra el conteo real de R01 y ocupación desconocida en R02/R03', () => {
    const r01 = occupancyInfo(sample({ state: 'people_detected', count: 1 }), now)
    assert.equal(r01.label, '1 persona detectada')
    assert.equal(r01.observedAt, '10:00:00')
    for (const room_id of ['R02', 'R03']) {
      const room = { room_id, occupancy: { state: 'unknown', reason: 'no_sensor', count: null } }
      assert.equal(occupancyInfo(room, now).label, 'Ocupación desconocida')
    }
  })
  it('mantiene independiente la reserva administrativa', () => {
    const room = { ...sample(), reservation_state: 'reserved', bookable: false }
    assert.equal(reservationLabel(room), 'Reservada')
    assert.equal(occupancyInfo(room, now).known, true)
    assert.equal(reservationLabel({ reservation_state: 'available', bookable: false }), 'No reservable')
  })
})

describe('Perfiles de demostración', () => {
  it('rechaza preferencias inválidas o inaccesibles y mantiene la vista correspondiente', () => {
    assert.equal(readProfile({ getItem: () => 'admin' }), 'admin')
    assert.equal(readProfile({ getItem: () => 'invalid' }), null)
    assert.equal(readProfile({ getItem: () => { throw new Error('Storage blocked') } }), null)
    assert.equal(viewForProfile('admin', 'user'), 'spaces')
    assert.equal(viewForProfile('admin', 'admin'), 'admin')
  })
})

describe('Agenda administrativa sin endpoints adicionales', () => {
  it('consulta las ocho franjas y marca fallos parciales sin inventar disponibilidad', async () => {
    const requested = []
    const rows = await fetchAgenda('2026-11-07', undefined, async (url) => {
      const query = new URL(url, 'http://example.test').searchParams
      assert.equal(query.get('date'), '2026-11-07')
      const slot = query.get('slot_id')
      requested.push(slot)
      return { ok: slot !== 'S15', json: async () => ({ date: '2026-11-07', slot_id: slot, rooms: ['R01', 'R02', 'R03'].map((room_id) => ({ room_id, bookable: !(slot === 'S10' && room_id === 'R01'), reservation_state: slot === 'S10' && room_id === 'R01' ? 'reserved' : 'available' })) }) }
    })
    assert.deepEqual(requested, AGENDA_SLOTS)
    const result = summarizeAgenda(rows)
    assert.equal(result.consulted, 7)
    assert.equal(result.partial, true)
    assert.equal(result.reservations.length, 1)
    assert.equal(result.available, 20)
    assert.equal(rows.find((row) => row.slotId === 'S15').state, 'error')
  })
  it('rechaza respuestas de otra fecha o con salas faltantes', async () => {
    const rows = await fetchAgenda('2026-11-07', undefined, async () => ({ ok: true, json: async () => ({ date: '2026-11-08', slot_id: 'S10', rooms: [] }) }))
    assert.equal(summarizeAgenda(rows).consulted, 0)
    assert.equal(summarizeAgenda(rows).available, 0)
    assert.equal(rows.every((row) => row.state === 'error'), true)
  })
})
