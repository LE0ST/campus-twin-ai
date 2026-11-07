import { useEffect, useState } from 'react'
import { AGENDA_SLOTS, ROOM_IDS, fetchAgenda, summarizeAgenda } from '../agenda'
import { localDateLabel, slotLabel } from '../roomPresentation'

export default function AdminDashboard({ date, onBook, onInspect }) {
  const [reload, setReload] = useState(0)
  const [agenda, setAgenda] = useState({ key: null, rows: [] })
  const [filter, setFilter] = useState('')
  const key = `${date}/${reload}`
  const ready = agenda.key === key
  const rows = ready ? agenda.rows : []
  const summary = summarizeAgenda(rows)
  const count = (value) => !ready || !summary.consulted ? '—' : `${summary.partial ? '≥ ' : ''}${String(value).padStart(2, '0')}`
  const reservations = summary.reservations.filter((room) => `${room.name} ${room.room_id} ${room.reservation_id || ''} ${slotLabel(room.slotId)}`.toLocaleLowerCase('es').includes(filter.toLocaleLowerCase('es')))
  const roomNames = Object.fromEntries(rows.flatMap((row) => row.rooms.map((room) => [room.room_id, room.name])))

  useEffect(() => {
    let active = true
    const controller = new AbortController()
    const timeout = window.setTimeout(() => controller.abort(), 12000)
    fetchAgenda(date, controller.signal).then((result) => {
      if (active) setAgenda({ key, rows: result })
    }).finally(() => window.clearTimeout(timeout))
    return () => { active = false; controller.abort(); window.clearTimeout(timeout) }
  }, [date, key])

  return <div className="admin-dashboard">
    <section className="admin-intro-card"><div><span className="admin-kicker">SECRETARÍA · PERFIL DE DEMOSTRACIÓN</span><h2>La agenda, en un solo vistazo.</h2><p>Sin autenticación real ni permisos administrativos. Las reservas son registros de demostración, no institucionales.</p></div><button type="button" className="primary-button" onClick={() => onBook()}>Registrar una reserva <span aria-hidden="true">+</span></button></section>
    <section className="summary-grid" aria-label="Resumen administrativo del día">
      <article className="summary-card"><span className="summary-icon blue" aria-hidden="true">▣</span><div><p>Reservas registradas</p><strong>{count(summary.reservations.length)}</strong><small>Para la fecha seleccionada</small></div></article>
      <article className="summary-card"><span className="summary-icon green" aria-hidden="true">◷</span><div><p>Espacios por reservar</p><strong>{count(summary.available)}</strong><small>Combinaciones de sala y franja</small></div></article>
      <article className="summary-card"><span className="summary-icon amber" aria-hidden="true">▦</span><div><p>Franjas consultadas</p><strong>{ready ? `${summary.consulted} / ${AGENDA_SLOTS.length}` : '—'}</strong><small>{ready && summary.partial ? 'Consulta parcial: faltan datos' : 'Cobertura de la agenda del día'}</small></div></article>
    </section>
    <section className="control-panel agenda-panel" aria-labelledby="agenda-title">
      <div className="panel-heading"><div><h2 id="agenda-title">Agenda de laboratorios</h2><p>{localDateLabel(date)} · Horario de Lima · Selecciona una celda para ver su detalle</p></div><button type="button" className="agenda-refresh" disabled={!ready} onClick={() => setReload((value) => value + 1)}>{ready ? 'Actualizar agenda' : 'Consultando…'}</button></div>
      {!ready && <p className="catalog-feedback" role="status">Consultando las ocho franjas del día…</p>}
      {ready && summary.partial && <p className="inline-warning" role="alert">{summary.consulted ? 'La agenda está incompleta. Las celdas sin datos no indican disponibilidad.' : 'No pudimos conectar con el backend. La disponibilidad permanece desconocida.'} Usa «Actualizar agenda» para reintentar.</p>}
      <div className="agenda-scroll" role="region" aria-label="Agenda de salas por horario" tabIndex="0"><table className="agenda-table"><caption className="visually-hidden">Disponibilidad de R01, R02 y R03 por franja para {date}</caption><thead><tr><th scope="col">Horario</th>{ROOM_IDS.map((id) => <th scope="col" key={id}><span>{id}</span><small>{roomNames[id] || 'Ambiente del piloto'}</small></th>)}</tr></thead><tbody>{AGENDA_SLOTS.map((slotId) => {
        const row = rows.find((item) => item.slotId === slotId)
        return <tr key={slotId}><th scope="row">{slotLabel(slotId)}</th>{ROOM_IDS.map((id) => {
          const room = row?.state === 'ready' ? row.rooms.find((item) => item.room_id === id) : null
          const label = !room ? ready ? 'Sin datos' : 'Consultando' : room.reservation_state === 'reserved' ? 'Reservada' : room.bookable ? 'Disponible' : 'No reservable'
          const tone = !room ? 'unknown' : room.reservation_state === 'reserved' ? 'reserved' : room.bookable ? 'available' : 'unavailable'
          return <td key={id}><button type="button" className={`agenda-cell ${tone}`} disabled={!room} aria-label={`${id}, ${slotLabel(slotId)}, ${label}`} onClick={() => room.bookable ? onBook(id, slotId) : onInspect(id, slotId)}><span className="agenda-cell-dot" />{label}{room?.reservation_id && <small>{room.reservation_id}</small>}</button></td>
        })}</tr>
      })}</tbody></table></div>
      <div className="agenda-legend"><span><i className="available" />Disponible para registrar</span><span><i className="reserved" />Reserva confirmada</span><span><i className="unknown" />Sin datos o no reservable</span></div>
    </section>
    <section className="control-panel daily-reservations" aria-labelledby="day-reservations-title"><div className="panel-heading"><div><h2 id="day-reservations-title">Reservas de la fecha seleccionada</h2><p>Registros confirmados que devuelve el backend.</p></div><label className="reservation-search"><span className="visually-hidden">Filtrar reservas del día</span><input type="search" placeholder="Buscar sala, horario o código" value={filter} onChange={(event) => setFilter(event.target.value)} /></label></div>
      {!ready ? <p className="empty-copy">Consultando reservas…</p> : !summary.consulted ? <p className="empty-copy">Las reservas se mostrarán cuando la conexión se recupere.</p> : !reservations.length ? <p className="empty-copy">{filter ? 'Ninguna reserva consultada coincide con la búsqueda.' : summary.partial ? 'No hay reservas en las franjas consultadas. Faltan franjas por verificar.' : 'No hay reservas registradas para esta fecha.'}</p> : <ul className="reservation-list">{reservations.map((room) => <li key={`${room.room_id}/${room.slotId}`}><span className="reservation-time">{slotLabel(room.slotId)}</span><div><strong>{room.name}</strong><small>{room.room_id} · {room.reservation_id || 'Reserva confirmada'}</small></div><span className="selection-badge">CONFIRMADA</span><button type="button" className="text-button" onClick={() => onInspect(room.room_id, room.slotId)}>Ver detalle →</button></li>)}</ul>}
    </section>
  </div>
}
