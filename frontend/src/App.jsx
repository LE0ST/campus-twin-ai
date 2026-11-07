import { useEffect, useRef, useState } from 'react'
import DashboardLayout from './components/DashboardLayout'
import { RoomMap, RoomDetail, SummaryCards } from './components/RoomPanel'
import { equipmentLabels, occupancyInfo, reservationLabel, slotLabel } from './roomPresentation'
import './App.css'
import './branding.css'
import './admin.css'
import ProfileChooser from './components/ProfileChooser'
import AdminDashboard from './components/AdminDashboard'
import { limaDate, lastAllowedDate, selectionError } from './assistantDate'
import { readProfile, saveProfile, clearProfile, viewForProfile } from './profile'

const slots = ['S09', 'S10', 'S11', 'S14', 'S15', 'S16', 'S17', 'S18']
const pages = {
  admin: ['Panel de Secretaría', 'Organiza las reservas del laboratorio y consulta la disponibilidad de todo el día.'],
  spaces: ['Disponibilidad inteligente', 'Consulta ambientes, confirma reservas y conoce la ocupación observada.'],
  booking: ['Reserva tu ambiente', 'Revisa la sala, el horario y los requisitos antes de confirmar.'],
  search: ['Encuentra tu espacio', 'Busca una sala disponible según la capacidad y el equipamiento que necesitas.'],
  occupancy: ['Ocupación observada', 'La reserva de un ambiente y su ocupación física son estados independientes.'],
  assistant: ['Reserva asistida por IA', 'Describe lo que necesitas; revisa la propuesta antes de crear una reserva.'],
}
const readView = () => Object.hasOwn(pages, window.location.hash.slice(1)) ? window.location.hash.slice(1) : 'spaces'

function errorMessage(body, fallback) {
  return typeof body?.error?.message === 'string' ? body.error.message : typeof body?.detail === 'string' ? body.detail : fallback
}

function Requirements({ people, setPeople, equipment, toggleEquipment, busy }) {
  return <div className="requirements-fields">
    <label className="input-label">Asistentes<input type="number" min="1" max="100" required value={people} disabled={busy} onChange={(e) => setPeople(e.target.value === '' ? '' : Number(e.target.value))} /></label>
    <fieldset className="equipment-options" disabled={busy}><legend>Equipo requerido</legend><div className="checks">{Object.entries(equipmentLabels).map(([value, label]) => <label key={value}><input type="checkbox" checked={equipment.includes(value)} onChange={() => toggleEquipment(value)} />{label}</label>)}</div></fieldset>
  </div>
}

function App() {
  const [profile, setProfile] = useState(readProfile)
  const [view, setView] = useState(() => viewForProfile(readView(), readProfile()))
  const titleRef = useRef(null)
  const [clock, setClock] = useState(() => new Date())
  const today = limaDate(clock)
  const [date, setDate] = useState(() => limaDate())
  const [slot, setSlot] = useState('S14')
  const [catalog, setCatalog] = useState({ key: null, state: 'loading', rooms: [] })
  const [reloadCount, setReloadCount] = useState(0)
  const [selectedId, setSelectedId] = useState('R01')
  const [people, setPeople] = useState(2)
  const [equipment, setEquipment] = useState([])
  const [confirmed, setConfirmed] = useState(false)
  const [status, setStatus] = useState(null)
  const [assistantText, setAssistantText] = useState('Necesito una sala para 2 personas con proyector')
  const [proposal, setProposal] = useState(null)
  const [busy, setBusy] = useState(false)
  const inFlight = useRef(false)
  const pendingRequest = useRef(null)
  const catalogKey = `${date}/${slot}/${reloadCount}`
  const catalogReady = catalog.key === catalogKey && catalog.state === 'ready'
  const catalogFailed = catalog.key === catalogKey && catalog.state === 'error'
  const rooms = catalogReady ? catalog.rooms : []
  const selectedRoom = rooms.find((room) => room.room_id === selectedId) || rooms[0]
  const visibleProposal = proposal?.catalogKey === catalogKey ? proposal : null
  const proposedRoom = rooms.find((room) => room.room_id === visibleProposal?.proposal?.room_id)
  const matchingRooms = rooms.filter((room) => room.bookable && Number.isInteger(people) && people > 0 && room.capacity >= people && equipment.every((item) => room.equipment?.includes(item)))
  const compatible = !!selectedRoom && matchingRooms.includes(selectedRoom)

  useEffect(() => {
    const interval = window.setInterval(() => setClock(new Date()), 30000)
    const refreshClock = () => setClock(new Date())
    window.addEventListener('focus', refreshClock)
    return () => { window.clearInterval(interval); window.removeEventListener('focus', refreshClock) }
  }, [])

  useEffect(() => {
    const onHashChange = () => setView(viewForProfile(readView(), profile))
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [profile])

  useEffect(() => {
    titleRef.current?.focus({ preventScroll: true })
    window.scrollTo(0, 0)
  }, [view, profile])

  useEffect(() => {
    if (!profile) return
    let active = true
    let controller
    let requestNumber = 0
    let loading = false
    async function loadRooms() {
      if (loading) return
      loading = true
      controller = new AbortController()
      const currentController = controller
      const number = ++requestNumber
      const timeout = window.setTimeout(() => currentController.abort(), 10000)
      try {
        const response = await fetch(`/api/rooms?${new URLSearchParams({ date, slot_id: slot })}`, { signal: currentController.signal })
        const body = await response.json().catch(() => null)
        if (!response.ok) throw new Error(errorMessage(body, 'No pudimos consultar la disponibilidad.'))
        if (!Array.isArray(body?.rooms) || body.rooms.some((room) => !room || typeof room.room_id !== 'string' || typeof room.bookable !== 'boolean')) throw new Error('La respuesta del catálogo no es válida.')
        const serverNow = Date.parse(body.server_time)
        if (active && number === requestNumber) setCatalog({ key: catalogKey, state: 'ready', rooms: body.rooms, now: Number.isFinite(serverNow) ? serverNow : Date.now() })
      } catch (error) {
        const message = currentController.signal.aborted ? 'La consulta al backend tardó demasiado.' : error instanceof TypeError ? 'No pudimos conectar con el backend.' : error.message
        if (active && number === requestNumber) setCatalog({ key: catalogKey, state: 'error', rooms: [], message })
      } finally { window.clearTimeout(timeout); loading = false }
    }
    loadRooms()
    const interval = window.setInterval(loadRooms, 3000)
    return () => { active = false; controller?.abort(); window.clearInterval(interval) }
  }, [date, slot, catalogKey, profile])

  function changeProfile(next) {
    if (inFlight.current) return
    if (next === 'choose') {
      clearProfile(); setProfile(null); setView('spaces'); resetConfirmation(); setProposal(null); navigate('spaces'); return
    }
    if (!['user', 'admin'].includes(next)) return
    const nextView = next === 'admin' ? 'admin' : 'spaces'
    saveProfile(next); setProfile(next); setView(nextView); resetConfirmation(); setProposal(null)
    navigate(nextView)
  }

  function agendaBook(id, slotId) {
    if (slotId) changeSlot(slotId)
    if (id) selectRoom(id)
    resetConfirmation(); navigate('booking')
  }

  function agendaInspect(id, slotId) { changeSlot(slotId); selectRoom(id); navigate('spaces') }

  function navigate(next) { window.location.hash = next }
  function refreshRooms() { setReloadCount((count) => count + 1); setProposal(null) }
  function resetConfirmation() { setConfirmed(false); setStatus(null) }
  function selectRoom(id) { setSelectedId(id); resetConfirmation() }
  function changeDate(value) { setDate(value); setProposal(null); resetConfirmation() }
  function changeSlot(value) { setSlot(value); setProposal(null); resetConfirmation() }
  function changePeople(value) { setPeople(value); resetConfirmation() }
  function toggleEquipment(item) { setEquipment((current) => current.includes(item) ? current.filter((value) => value !== item) : [...current, item]); resetConfirmation() }

  async function suggest(event) {
    event.preventDefault()
    if (inFlight.current || !assistantText.trim()) return
    const error = selectionError(date, slot)
    if (error) { setStatus({ view: 'assistant', type: 'error', message: error }); return }
    inFlight.current = true; setBusy(true); setStatus(null); setProposal(null)
    try {
      const response = await fetch('/api/assistant/propose', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text: assistantText, date, slot_id: slot }) })
      const body = await response.json()
      if (!response.ok) throw new Error(errorMessage(body, 'No se pudo generar la propuesta. Puedes usar la reserva manual.'))
      setProposal({ ...body, catalogKey })
    } catch (error) { setStatus({ view: 'assistant', type: 'error', message: error.message }) }
    finally { inFlight.current = false; setBusy(false) }
  }

  async function reserve(event) {
    event.preventDefault()
    if (inFlight.current || !catalogReady || !compatible || !confirmed) return
    const error = selectionError(date, slot)
    if (error) { setStatus({ view: 'booking', type: 'error', message: error }); return }
    inFlight.current = true; setBusy(true); setStatus(null)
    const payload = { room_id: selectedRoom.room_id, date, slot_id: slot, attendees: people, required_equipment: [...equipment].sort(), confirmed: true }
    const fingerprint = JSON.stringify(payload)
    if (pendingRequest.current?.fingerprint !== fingerprint) pendingRequest.current = { fingerprint, id: crypto.randomUUID() }
    try {
      const response = await fetch('/api/reservations', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...payload, request_id: pendingRequest.current.id }) })
      const body = await response.json()
      if (!response.ok) throw new Error(errorMessage(body, `No se pudo completar la reserva (${response.status}).`))
      pendingRequest.current = null
      setStatus({ view: 'booking', type: 'success', message: `Reserva registrada para ${selectedRoom.name}. Código: ${body.reservation_id}` })
      setConfirmed(false); refreshRooms()
    } catch (error) { setStatus({ view: 'booking', type: 'error', message: error.message }) }
    finally { inFlight.current = false; setBusy(false) }
  }

  function reviewProposal() {
    const data = visibleProposal?.proposal
    if (!proposedRoom || data.date !== date || data.slot_id !== slot || !Number.isInteger(data.attendees) || !Array.isArray(data.required_equipment)) {
      setStatus({ view: 'assistant', type: 'error', message: 'La propuesta ya no coincide con la consulta. Genera una nueva.' }); return
    }
    setSelectedId(data.room_id); setPeople(data.attendees); setEquipment(data.required_equipment); resetConfirmation(); navigate('booking')
  }

  const feedback = !catalogReady && <div className="catalog-feedback" role={catalogFailed ? 'alert' : 'status'}><p>{catalogFailed ? `${catalog.message || 'No pudimos consultar la disponibilidad.'} Las reservas permanecen deshabilitadas.` : 'Consultando disponibilidad…'}</p>{catalogFailed && <button className="text-button" type="button" onClick={refreshRooms}>Reintentar</button>}</div>
  const empty = catalogReady && !rooms.length && <p className="catalog-feedback">No hay ambientes para esta consulta.</p>

  if (!profile) return <ProfileChooser onChoose={changeProfile} />

  return <DashboardLayout activeView={view} profile={profile} onProfileChange={changeProfile} busy={busy}>
    <main id="main-content" tabIndex="-1">
      <section className="intro"><div><h1 ref={titleRef} tabIndex="-1" id="page-title">{profile === 'admin' && view === 'booking' ? 'Registrar reserva' : pages[view][0]}</h1><p className="subhead">{profile === 'admin' && view === 'booking' ? 'Traslada una solicitud recibida a una reserva confirmada, después de revisar sus requisitos.' : pages[view][1]}</p></div></section>
      <div className="query-toolbar" aria-label="Fecha y horario de consulta"><div className="filters"><label>Fecha<input type="date" value={date} min={today} max={lastAllowedDate(today)} required disabled={busy} onChange={(e) => changeDate(e.target.value)} /></label>{view !== 'admin' && <label>Bloque horario<select value={slot} disabled={busy} onChange={(e) => changeSlot(e.target.value)}>{slots.map((value) => <option key={value} value={value}>{slotLabel(value)}</option>)}</select></label>}</div><span className="query-note">{view === 'admin' ? 'Agenda completa del día · Lima (UTC−5)' : 'Hora local · Lima (UTC−5)'}</span></div>
      {selectionError(date, slot, clock) && view !== 'admin' && <p className="inline-warning" role="status">{selectionError(date, slot, clock)}</p>}
      {status?.view === view && <div className={`status ${status.type}`} role={status.type === 'error' ? 'alert' : 'status'}>{status.message}</div>}
      {profile === 'admin' && view === 'admin' && <AdminDashboard date={date} onBook={agendaBook} onInspect={agendaInspect} />}
      {profile === 'admin' && view === 'booking' && <div className="admin-booking-context"><span>Registro desde Secretaría · demostración</span><button type="button" className="text-button" onClick={() => navigate('admin')}>← Volver a la agenda</button></div>}
      {view === 'spaces' && <><SummaryCards rooms={rooms} ready={catalogReady} now={catalog.now} />{feedback}{empty}{catalogReady && rooms.length > 0 && <div className="panel-grid"><RoomMap rooms={rooms} now={catalog.now} selectedId={selectedRoom?.room_id} onSelect={selectRoom} date={date} /><RoomDetail room={selectedRoom} slot={slot} now={catalog.now} onBook={() => { resetConfirmation(); navigate('booking') }} /></div>}</>}

      {view === 'booking' && <>{feedback}{empty}<div className="panel-grid booking-grid"><section className="control-panel"><div className="panel-heading"><div><h2>Confirma tu reserva</h2><p>La reserva se crea únicamente al confirmar este formulario.</p></div><span className="selection-badge">CONFIRMACIÓN HUMANA</span></div><form className="booking-form" onSubmit={reserve}>
        <label className="input-label">Ambiente<select value={selectedRoom?.room_id || ''} disabled={busy || !catalogReady || !rooms.length} onChange={(e) => selectRoom(e.target.value)}>{!rooms.length && <option value="">Sin ambientes disponibles</option>}{rooms.map((room) => <option key={room.room_id} value={room.room_id}>{room.name} · {room.capacity} personas</option>)}</select></label>
        <Requirements people={people} setPeople={changePeople} equipment={equipment} toggleEquipment={toggleEquipment} busy={busy} />
        {catalogReady && selectedRoom && !compatible && <p className="inline-warning">{!selectedRoom.bookable ? 'Esta sala no se puede reservar en la franja elegida.' : 'Revisa la cantidad de asistentes y el equipo requerido: la sala no cumple todos los requisitos.'}</p>}
        <label className="confirm"><input type="checkbox" checked={confirmed} disabled={busy || !catalogReady || !compatible} onChange={(e) => setConfirmed(e.target.checked)} />Confirmo el ambiente, la fecha, el horario y los requisitos de la reserva.</label>
        <button className="primary-button" type="submit" disabled={busy || !catalogReady || !compatible || !confirmed}>{busy ? 'Registrando reserva…' : 'Confirmar reserva'}<span aria-hidden="true">→</span></button>
      </form></section><RoomDetail room={selectedRoom} slot={slot} now={catalog.now} /></div></>}

      {view === 'search' && <><section className="control-panel"><div className="panel-heading"><div><h2>¿Qué espacio necesitas?</h2><p>La búsqueda consulta el catálogo; seleccionar una opción abre la confirmación.</p></div></div><Requirements people={people} setPeople={changePeople} equipment={equipment} toggleEquipment={toggleEquipment} busy={busy} /></section>{feedback}{catalogReady && <section className="search-results" aria-labelledby="results-title"><h2 id="results-title">{matchingRooms.length} {matchingRooms.length === 1 ? 'ambiente compatible' : 'ambientes compatibles'}</h2>{!matchingRooms.length && <p className="catalog-feedback">No hay ambientes que cumplan estos requisitos. Prueba otra franja o ajusta la búsqueda.</p>}<div className="search-grid">{matchingRooms.map((room) => <article key={room.room_id} className="control-panel search-card"><span className="map-room-id">{room.room_id}</span><h3>{room.name}</h3><span className="availability">Disponible para la franja</span><p className="capacity">Capacidad: <strong>{room.capacity} personas</strong></p><div className="chips">{room.equipment?.map((item) => <span key={item}>{equipmentLabels[item] || item}</span>)}</div><button className="primary-button" onClick={() => { selectRoom(room.room_id); navigate('booking') }}>Seleccionar ambiente<span aria-hidden="true">→</span></button></article>)}</div></section>}</>}

      {view === 'occupancy' && <>{feedback}{empty}<div className="occupancy-grid">{rooms.map((room) => { const physical = occupancyInfo(room, catalog.now); return <section className="control-panel occupancy-card" key={room.room_id}><span className="map-room-id">{room.room_id}</span><h2>{room.name}</h2><div className="state-comparison"><div className="state-box administrative"><span>RESERVA / FRANJA</span><strong>{reservationLabel(room)}</strong><small>{slotLabel(slot)}</small></div><div className={`state-box ${physical.tone}`}><span>OCUPACIÓN / AHORA</span><strong>{physical.label}</strong><small>{physical.detail}</small></div></div>{physical.observedAt && <p className="detail-caption">Última lectura: {physical.observedAt} · Lima</p>}{physical.sourceLabel && <p className="detail-caption">{physical.sourceLabel}</p>}<p className="detail-caption">Una lectura física no crea, cancela ni modifica reservas.</p>{room.recorded_sample && <p className="recorded-note">La fuente disponible es una grabación autorizada, no una cámara en vivo.</p>}<button className="text-button" onClick={() => { selectRoom(room.room_id); navigate('spaces') }}>Ver en el panel →</button></section> })}</div></>}

      {view === 'assistant' && <div className="panel-grid assistant-grid"><section className="assistant-card"><div className="assistant-head"><span className="spark" aria-hidden="true">✳</span><div><p className="eyebrow">ASISTENTE CAMPUSTWIN</p><h2>Cuéntame qué buscas</h2></div></div><p className="assistant-note">Indica cuántas personas asistirán y qué equipamiento necesitan. Se utilizarán la fecha y la franja seleccionadas arriba.</p><form onSubmit={suggest}><label className="input-label" htmlFor="assistant-request">Tu solicitud</label><textarea id="assistant-request" maxLength="500" required disabled={busy} value={assistantText} onChange={(e) => setAssistantText(e.target.value)} rows="5" /><button className="primary-button" type="submit" disabled={busy || !assistantText.trim()}>{busy ? 'Buscando una opción…' : 'Generar propuesta'}<span aria-hidden="true">→</span></button></form>{visibleProposal && <div className="assistant-response" role="status">{visibleProposal.message}</div>}<p className="assistant-disclaimer">El asistente propone; tú revisas y confirmas cada reserva.</p><button className="text-button" onClick={() => navigate('search')}>Prefiero buscar manualmente →</button></section><section className="control-panel proposal-panel"><div className="panel-heading"><h2>Propuesta de reserva</h2></div>{visibleProposal?.proposal && proposedRoom ? <><span className="pending-badge">PENDIENTE DE CONFIRMACIÓN</span><h3>{proposedRoom.name}</h3><dl className="proposal-details"><div><dt>Ambiente</dt><dd>{proposedRoom.room_id}</dd></div><div><dt>Fecha</dt><dd>{visibleProposal.proposal.date}</dd></div><div><dt>Franja</dt><dd>{slotLabel(visibleProposal.proposal.slot_id)}</dd></div><div><dt>Asistentes</dt><dd>{visibleProposal.proposal.attendees} personas</dd></div><div><dt>Equipamiento</dt><dd>{visibleProposal.proposal.required_equipment.map((item) => equipmentLabels[item] || item).join(', ') || 'Sin requisitos adicionales'}</dd></div></dl><button className="primary-button" disabled={busy || !catalogReady} onClick={reviewProposal}>Revisar y confirmar<span aria-hidden="true">→</span></button></> : <div className="proposal-empty"><span aria-hidden="true">✧</span><h3>Tu próxima reserva empieza aquí</h3><p>Cuando el asistente encuentre una opción compatible, verás sus detalles en este panel.</p></div>}</section></div>}
      <section className="privacy"><span aria-hidden="true">⌁</span><p><b>Privacidad primero.</b> La ocupación solo se muestra con lecturas autorizadas y vigentes. Cero detecciones no demuestra que una sala esté vacía.</p><span className="privacy-tag">DATOS SINTÉTICOS</span></section>
    </main>
  </DashboardLayout>
}

export default App
