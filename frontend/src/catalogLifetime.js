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
