export const AGENDA_SLOTS = ['S09', 'S10', 'S11', 'S14', 'S15', 'S16', 'S17', 'S18']
export const ROOM_IDS = ['R01', 'R02', 'R03']

export function summarizeAgenda(rows) {
  const successful = rows.filter((row) => row.state === 'ready')
  const reservations = successful.flatMap((row) => row.rooms.filter((room) => room.reservation_state === 'reserved').map((room) => ({ ...room, slotId: row.slotId })))
  const available = successful.reduce((count, row) => count + row.rooms.filter((room) => room.bookable).length, 0)
  return { reservations, available, consulted: successful.length, partial: successful.length < AGENDA_SLOTS.length }
}

export async function fetchAgenda(date, signal, request = fetch) {
  return Promise.all(AGENDA_SLOTS.map(async (slotId) => {
    try {
      const response = await request(`/api/rooms?${new URLSearchParams({ date, slot_id: slotId })}`, { signal })
      if (!response.ok) throw new Error('Consulta no disponible')
      const body = await response.json()
      if (body.date !== date || body.slot_id !== slotId || !Array.isArray(body.rooms) ||
          ROOM_IDS.some((id) => !body.rooms.some((room) => room?.room_id === id && typeof room.bookable === 'boolean' && ['reserved', 'available'].includes(room.reservation_state)))) throw new Error('Agenda inválida')
      return { slotId, state: 'ready', rooms: body.rooms }
    } catch { return { slotId, state: 'error', rooms: [] } }
  }))
}
