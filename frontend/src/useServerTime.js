import { useEffect, useState } from 'react'
import { serverTimeAt } from './catalogLifetime'

// Recheck expiry even when polling stalls.
export default function useServerTime(clock) {
  const [, tick] = useState(0)
  useEffect(() => {
    if (!clock) return
    const timer = window.setInterval(() => tick((value) => value + 1), 250)
    return () => window.clearInterval(timer)
  }, [clock])
  return serverTimeAt(clock, performance.now())
}
