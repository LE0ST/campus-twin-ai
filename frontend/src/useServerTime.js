import { useEffect, useState } from 'react'
import { serverTimeAt } from './catalogLifetime'

// Keep the clock reading in state: rendering must remain pure.
export default function useServerTime(clock) {
  const [monotonicNow, setMonotonicNow] = useState(null)
  useEffect(() => {
    if (!clock) return
    const update = () => setMonotonicNow(performance.now())
    const firstTick = window.setTimeout(update, 0)
    const interval = window.setInterval(update, 250)
    return () => {
      window.clearTimeout(firstTick)
      window.clearInterval(interval)
    }
  }, [clock])
  // Unknown until the effect supplies a fresh reading; never grant stale data validity.
  return serverTimeAt(clock, monotonicNow)
}
