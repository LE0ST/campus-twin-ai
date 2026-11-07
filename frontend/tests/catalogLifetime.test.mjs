import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { createServerClock, serverTimeAt, subscribePageLifetime } from '../src/catalogLifetime.js'
import { occupancyInfo } from '../src/roomPresentation.js'

const serverTime = '2026-11-07T15:00:00.000Z'

describe('Caducidad de lecturas sin nuevas respuestas', () => {
  it('avanza el tiempo del servidor con un reloj monotónico', () => {
    const clock = createServerClock(serverTime, 100, 130)
    const received = Date.parse(serverTime) + 30
    assert.equal(serverTimeAt(clock, 130), received)
    assert.equal(serverTimeAt(clock, 1630), received + 1500)
  })
  it('vence la lectura aunque no lleguen nuevas consultas', () => {
    const clock = createServerClock(serverTime, 100, 130)
    const received = serverTimeAt(clock, 130)
    const room = { occupancy: {
      state: 'people_detected', count: 1, mode: 'live_camera',
      observed_at: new Date(received).toISOString(),
      expires_at: new Date(received + 15000).toISOString(),
    } }
    assert.equal(occupancyInfo(room, serverTimeAt(clock, 15129)).known, true)
    assert.equal(occupancyInfo(room, serverTimeAt(clock, 15130)).known, false)
    assert.equal(occupancyInfo(room, serverTimeAt(clock, 15130)).short, 'Lectura vencida')
  })
  it('rechaza marcas horarias inválidas o un reloj que retrocede', () => {
    assert.throws(() => createServerClock('invalid', 0, 10))
    assert.throws(() => createServerClock(serverTime, 11, 10))
    assert.equal(serverTimeAt(null, 500), Infinity)
    assert.equal(serverTimeAt(createServerClock(serverTime, 5, 10), 9), Infinity)
  })
})

function eventTarget() {
  const listeners = new Map()
  return {
    addEventListener(name, callback) {
      if (!listeners.has(name)) listeners.set(name, new Set())
      listeners.get(name).add(callback)
    },
    removeEventListener(name, callback) { listeners.get(name)?.delete(callback) },
    emit(name, event = {}) { for (const callback of listeners.get(name) || []) callback(event) },
  }
}
describe('Suspensión y reactivación de la pestaña', () => {
  it('invalida datos, restaura la sesión y limpia los listeners', () => {
    const page = { ...eventTarget(), visibilityState: 'visible' }
    const host = eventTarget()
    const states = []
    const unsubscribe = subscribePageLifetime(page, host, (visible) => states.push(visible))
    page.visibilityState = 'hidden'; page.emit('visibilitychange')
    page.visibilityState = 'visible'; page.emit('visibilitychange')
    page.emit('freeze')
    page.emit('resume')
    host.emit('pageshow', { persisted: true })
    host.emit('pageshow', { persisted: false })
    assert.deepEqual(states, [false, true, false, true, true])
    unsubscribe()
    page.emit('visibilitychange')
    host.emit('pageshow', { persisted: true })
    assert.deepEqual(states, [false, true, false, true, true])
  })
})
