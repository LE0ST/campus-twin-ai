// Anchor server time to a monotonic clock; wall-clock changes cannot extend a reading.
export function createServerClock(serverTime, startedAt, receivedAt) {
  const serverAt = Date.parse(serverTime)
  if (!Number.isFinite(serverAt) || !Number.isFinite(startedAt) || !Number.isFinite(receivedAt) || receivedAt < startedAt) {
    throw new Error('La respuesta no incluye una hora de servidor válida.')
  }
  // Advance by the full round trip conservatively instead of granting time in transit.
  return { serverAt: serverAt + receivedAt - startedAt, receivedAt }
}

export function serverTimeAt(clock, monotonicNow) {
  if (!clock || !Number.isFinite(clock.serverAt) || !Number.isFinite(clock.receivedAt) ||
      !Number.isFinite(monotonicNow) || monotonicNow < clock.receivedAt) return Infinity
  return clock.serverAt + monotonicNow - clock.receivedAt
}

// Each catalog owns its deadlines and its timers. A disposed catalog cannot publish.
export function scheduleOccupancyDeadlines(clock, rooms, timer, publish) {
  let active = true
  const handles = new Set()
  const update = () => { if (active) publish(timer.now()) }
  update()
  for (const room of rooms || []) {
    const sample = room?.occupancy
    const expires = Date.parse(sample?.expires_at)
    if (sample?.mode !== 'live_camera' || !Number.isFinite(expires) ||
        !Number.isFinite(clock?.serverAt) || !Number.isFinite(clock?.receivedAt)) continue
    const deadline = clock.receivedAt + expires - clock.serverAt
    const schedule = () => {
      if (!active) return
      const remaining = deadline - timer.now()
      if (remaining <= 0) { update(); return }
      const handle = timer.setTimeout(() => {
        handles.delete(handle)
        if (!active) return
        update()
        schedule() // A timer may fire before its deadline.
      }, Math.min(Math.ceil(remaining), 2147483647))
      handles.add(handle)
    }
    schedule()
  }
  return () => { active = false; for (const handle of handles) timer.clearTimeout(handle); handles.clear() }
}

export function subscribePageLifetime(page, host, invalidate) {
  const visibility = () => invalidate(page.visibilityState !== 'hidden')
  const freeze = () => invalidate(false)
  const restore = (event) => { if (event.persisted) visibility() }
  page.addEventListener('visibilitychange', visibility)
  page.addEventListener('freeze', freeze)
  page.addEventListener('resume', visibility)
  host.addEventListener('pageshow', restore)
  return () => {
    page.removeEventListener('visibilitychange', visibility)
    page.removeEventListener('freeze', freeze)
    page.removeEventListener('resume', visibility)
    host.removeEventListener('pageshow', restore)
  }
}
