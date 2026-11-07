import { equipmentLabels, occupancyInfo, reservationLabel, localDateLabel, slotLabel } from '../roomPresentation'

export function RoomMap({ rooms, selectedId, onSelect, date }) {
  return <section className="control-panel map-panel" aria-labelledby="map-title">
    <div className="panel-heading"><div><h2 id="map-title">Croquis del pabellón piloto</h2><p>Distribución conceptual · Ambientes de ejemplo</p></div><span className="date-chip">{localDateLabel(date)}</span></div>
    <div className="floor-plan" aria-label="Selecciona un ambiente en el croquis">
      {rooms.map((room, index) => {
        const physical = occupancyInfo(room)
        const selected = room.room_id === selectedId
        return <button key={room.room_id} type="button" aria-pressed={selected} aria-label={`Seleccionar ${room.name}`}
          className={`map-room map-room-${index + 1} ${selected ? 'selected' : ''} ${room.reservation_state === 'reserved' ? 'reserved' : ''}`}
          onClick={() => onSelect(room.room_id)}>
          <span className="map-room-id">{room.room_id}</span><strong>{room.name}</strong>
          <span className="map-badges"><span>{reservationLabel(room)}</span><span className={`physical-badge ${physical.tone}`}>{physical.short}</span></span>
        </button>
      })}
      <div className="floor-corridor" aria-hidden="true">PASILLO / CIRCULACIÓN</div>
    </div>
    <p className="map-help"><span className="legend-square" />Ambiente seleccionado<span className="map-help-separator">·</span>Elige una sala para ver su detalle</p>
  </section>
}

export function RoomDetail({ room, slot, onBook, actionLabel = 'Ver disponibilidad', children }) {
  if (!room) return <aside className="control-panel room-detail"><h2>Detalle del ambiente</h2><p className="empty-copy">Selecciona una sala para consultar sus datos.</p></aside>
  const physical = occupancyInfo(room)
  return <aside className="control-panel room-detail" aria-labelledby="detail-title">
    <h2 id="detail-title">Detalle del ambiente</h2>
    <div className="detail-name"><span className="selection-badge">SELECCIONADO</span><h3>{room.name}</h3><p>{room.room_id} · {room.capacity} personas</p></div>
    <div className="detail-section"><p className="detail-label">Disponibilidad administrativa</p><strong className={`detail-status ${room.reservation_state === 'reserved' ? 'blue-text' : room.bookable ? 'green-text' : 'neutral-text'}`}><i />{reservationLabel(room)} · {slotLabel(slot)}</strong>{room.disabled_reason && <p className="detail-caption">{room.disabled_reason}</p>}</div>
    <div className="detail-section"><p className="detail-label">Ocupación observada ahora</p><strong className={`detail-status ${physical.tone}`}><i />{physical.label}</strong><p className="detail-caption">{physical.known ? `Cámara en vivo · Lectura ${new Date(room.occupancy.observed_at).toLocaleTimeString('es-PE', { timeZone: 'America/Lima' })}` : 'Sin una medición actual válida'}</p></div>
    <div className="equipment-summary">{room.capacity} puestos · {(room.equipment || []).map((item) => equipmentLabels[item] || item).join(' · ')}</div>
    {room.recorded_sample && <p className="recorded-note">Existe una muestra grabada; no representa la ocupación actual.</p>}
    {children}
    {onBook && <button className="primary-button" type="button" onClick={onBook}>{actionLabel}<span aria-hidden="true">→</span></button>}
  </aside>
}

export function SummaryCards({ rooms, ready }) {
  const monitored = rooms.filter((room) => occupancyInfo(room).known).length
  const data = [
    { label: 'Ambientes del piloto', value: rooms.length, note: 'Espacios sintéticos', icon: '▦', color: 'blue' },
    { label: 'Reservas en esta franja', value: rooms.filter((room) => room.reservation_state === 'reserved').length, note: 'Estado administrativo', icon: '▣', color: 'green' },
    { label: 'Ambientes con lectura vigente', value: monitored, note: 'Ocupación física observada', icon: '◉', color: 'amber' },
  ]
  return <section className="summary-grid" aria-label="Resumen de la franja seleccionada">{data.map((item) => <article className="summary-card" key={item.label}><span className={`summary-icon ${item.color}`} aria-hidden="true">{item.icon}</span><div><p>{item.label}</p><strong>{ready ? String(item.value).padStart(2, '0') : '—'}</strong><small>{item.note}</small></div></article>)}</section>
}
