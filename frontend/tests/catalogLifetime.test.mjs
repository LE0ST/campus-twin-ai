import { describe, it } from 'node:test'
import assert from 'node:assert/strict'
import { createServerClock, serverTimeAt, subscribePageLifetime, scheduleOccupancyDeadlines } from '../src/catalogLifetime.js'
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

function fakeTimer() {
  let now = 0, next = 0
  const jobs = new Map()
  return {
    now: () => now,
    setTimeout(fn, delay) { const id = ++next; jobs.set(id, { fn, at: now + delay }); return id },
    clearTimeout(id) { jobs.delete(id) },
    advance(to) {
      while (true) {
        const job = [...jobs].sort((a, b) => a[1].at - b[1].at)[0]
        if (!job || job[1].at > to) break
        now = job[1].at; jobs.delete(job[0]); job[1].fn()
      }
      now = to
    },
    count: () => jobs.size,
  }
}

describe('Programación de vencimientos', () => {
  const base = Date.parse(serverTime)
  const clock = createServerClock(serverTime, 0, 0)
  const room = (expires) => ({ occupancy: { mode: 'live_camera', state: 'people_detected', count: 1,
    observed_at: serverTime, expires_at: typeof expires === 'number' ? new Date(base + expires).toISOString() : expires } })
  const setup = (rooms, timer = fakeTimer()) => {
    let now = Infinity
    const stop = scheduleOccupancyDeadlines(clock, rooms, timer, (value) => { now = serverTimeAt(clock, value) })
    return { timer, stop, known: (r) => occupancyInfo(r, now).known }
  }
  it('vence exactamente a los 15 segundos', () => {
    const r = room(15000), s = setup([r]); s.timer.advance(14999); assert.equal(s.known(r), true)
    s.timer.advance(15000); assert.equal(s.known(r), false); s.stop()
  })
  it('resuelve el caso de auditoría sin tick periódico', () => {
    const r = room(15100), s = setup([r]); s.timer.advance(15000); assert.equal(s.known(r), true)
    s.timer.advance(15150); assert.equal(s.known(r), false); s.stop()
  })
  it('programa vencimientos independientes para varias salas', () => {
    const a = room(1000), b = room(2000), s = setup([a, b])
    s.timer.advance(1000); assert.equal(s.known(a), false); assert.equal(s.known(b), true)
    s.timer.advance(2000); assert.equal(s.known(b), false); s.stop()
  })
  it('cierra lecturas vencidas e inválidas desde el primer cálculo', () => {
    const timer = fakeTimer(); timer.advance(2000)
    const a = room(1000), b = room('invalid'), s = setup([a, b], timer)
    assert.equal(s.known(a), false); assert.equal(s.known(b), false); assert.equal(timer.count(), 0); s.stop()
  })
  it('cancela temporizadores y sustituye el catálogo por una lectura nueva', () => {
    const timer = fakeTimer(), a = room(1000), old = setup([a], timer)
    old.stop(); assert.equal(timer.count(), 0)
    const b = room(3000), fresh = setup([b], timer)
    timer.advance(1000); assert.equal(fresh.known(b), true)
    timer.advance(3000); assert.equal(fresh.known(b), false); fresh.stop(); assert.equal(timer.count(), 0)
  })
  it('al reactivar recalcula la lectura vencida y no crea ocupación conocida', () => {
    const timer = fakeTimer(), r = room(1000), old = setup([r], timer)
    old.stop(); timer.advance(2000)
    const resumed = setup([r], timer); assert.equal(resumed.known(r), false); resumed.stop()
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
