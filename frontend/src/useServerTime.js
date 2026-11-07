import { useEffect, useState } from 'react'
import { scheduleOccupancyDeadlines, serverTimeAt } from './catalogLifetime'

// Keep the clock reading in state: rendering must remain pure.
export default function useServerTime(clock, rooms) {
  const [reading, setReading] = useState(null)
  useEffect(() => {
    if (!clock) return
    return scheduleOccupancyDeadlines(clock, rooms, {
      now: () => performance.now(),
      setTimeout: (callback, delay) => window.setTimeout(callback, delay),
      clearTimeout: (handle) => window.clearTimeout(handle),
    }, (now) => setReading({ clock, now }))
  }, [clock, rooms])
  // Unknown until the effect supplies a fresh reading; never grant stale data validity.
  return serverTimeAt(clock, reading && reading.clock === clock ? reading.now : null)
}
