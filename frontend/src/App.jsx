import { useEffect, useState } from 'react'
import './App.css'

const today = new Date().toISOString().slice(0, 10)
const slots = ['S09', 'S10', 'S11', 'S14', 'S15', 'S16', 'S17', 'S18']
const defaultRooms = [
  { room_id: 'R01', name: 'Sala multimedia', capacity: 6, equipment: ['pc', 'projector', 'wifi'], bookable: true },
  { room_id: 'R02', name: 'Sala de estudio', capacity: 8, equipment: ['whiteboard', 'wifi'], bookable: true },
  { room_id: 'R03', name: 'Cubículo de investigación', capacity: 4, equipment: ['wifi'], bookable: true },
]

function App() {
  const [date, setDate] = useState(today)
  const [slot, setSlot] = useState('S14')
  const [rooms, setRooms] = useState(defaultRooms)
  const [people, setPeople] = useState(12)
  const [equipment, setEquipment] = useState([])
  const [confirmed, setConfirmed] = useState(false)
  const [status, setStatus] = useState('')
  const [assistantText, setAssistantText] = useState('Necesito un aula para 12 personas con proyector')
  const [proposal, setProposal] = useState(null)
  const [busy, setBusy] = useState(false)

  async function loadRooms() {
    try {
      const response = await fetch(`/api/rooms?date=${date}&slot_id=${slot}`)
      if (response.ok) setRooms((await response.json()).rooms)
    } catch { /* keep the demo catalog visible if the API is offline */ }
  }
  useEffect(() => { loadRooms() }, [date, slot])

  function toggleEquipment(item) {
    setEquipment((current) => current.includes(item) ? current.filter((x) => x !== item) : [...current, item])
  }

  async function suggest() {
    setBusy(true); setStatus(''); setProposal(null)
    try {
      const response = await fetch('/api/assistant/propose', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: assistantText, date, slot_id: slot }),
      })
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail || 'No se pudo generar la propuesta')
      setProposal(body)
      setStatus(body.message || 'Propuesta lista; revisa los datos antes de confirmar.')
    } catch (error) { setStatus(error.message) }
    finally { setBusy(false) }
  }

  async function reserve(room) {
    setBusy(true); setStatus('')
    try {
      const response = await fetch('/api/reservations', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: crypto.randomUUID(), room_id: room.room_id, date, slot_id: slot, attendees: people, required_equipment: equipment, confirmed }),
      })
      const body = await response.json()
      if (!response.ok) throw new Error(body.detail || `Error ${response.status}`)
      setStatus(`Reserva registrada para ${room.name}. Código: ${body.reservation_id || 'confirmado'}`)
      await loadRooms()
    } catch (error) { setStatus(error.message) }
    finally { setBusy(false) }
  }

  async function acceptProposal() {
    const room = rooms.find((item) => item.room_id === (proposal?.proposal?.room_id || proposal?.room_id))
    if (!room) { setStatus('La propuesta no identifica un aula disponible.'); return }
    await reserve(room)
  }

  return <div className="app-shell">
    <header className="topbar"><div className="brand"><span className="brand-mark">Q</span><span>QuantumByte <small>CampusTwin AI</small></span></div><span className="live-label"><i /> DEMO LOCAL · DATOS SINTÉTICOS</span></header>
    <main>
      <section className="intro"><div><p className="eyebrow">PLANIFICACIÓN INTELIGENTE · CAMPUS</p><h1>Encuentra el espacio<br /><em>que necesitas.</em></h1><p className="subhead">Disponibilidad y reservas en un solo lugar, con asistencia conversacional.</p></div><div className="intro-art"><div className="orbit orbit-one"/><div className="orbit orbit-two"/><div className="art-core">CT<span>AI</span></div><b className="node node-a">R01</b><b className="node node-b">R02</b><b className="node node-c">R03</b></div></section>

      <section className="control-panel"><div className="section-title"><span className="step">01</span><div><h2>Explora espacios</h2><p>Elige el horario para consultar el catálogo de demostración.</p></div></div><div className="filters"><label>Fecha<input type="date" value={date} onChange={(e) => setDate(e.target.value)} /></label><label>Bloque horario<select value={slot} onChange={(e) => setSlot(e.target.value)}>{slots.map((s) => <option key={s}>{s}</option>)}</select></label></div>
        <div className="room-grid">{rooms.map((room, i) => <article className="room-card" key={room.room_id}><div className={`room-visual room-${i + 1}`}><div className="room-shape"><span>{room.room_id}</span></div><span className="room-index">0{i + 1}</span></div><div className="room-info"><div className="room-heading"><h3>{room.name || room.room_id}</h3><span className={`availability ${room.bookable === false ? 'occupied' : ''}`}><i />{room.reservation_state === 'reserved' ? 'Reservada' : room.bookable === false ? 'No disponible' : 'Disponible'}</span></div><p className="capacity">Capacidad <strong>{room.capacity} personas</strong></p><div className="chips">{(room.equipment || []).map((tag) => <span key={tag}>{tag === 'projector' ? 'Proyector' : tag === 'whiteboard' ? 'Pizarra' : tag === 'wifi' ? 'Wi‑Fi' : tag}</span>)}</div><button className="text-button" onClick={() => reserve(room)} disabled={busy || room.bookable === false}>Reservar espacio <span>↗</span></button></div></article>)}</div>
      </section>

      <section className="lower-grid"><div className="control-panel booking"><div className="section-title"><span className="step">02</span><div><h2>Confirma tu reserva</h2><p>La ocupación de cámara no está conectada en esta demo.</p></div></div><div className="form-row"><label>Asistentes<input type="number" min="1" value={people} onChange={(e) => setPeople(Number(e.target.value))} /></label><div className="equipment"><span className="field-label">Equipo requerido</span><div className="checks">{[['projector', 'Proyector'], ['whiteboard', 'Pizarra']].map(([value, label]) => <label key={value}><input type="checkbox" checked={equipment.includes(value)} onChange={() => toggleEquipment(value)} />{label}</label>)}</div></div></div><label className="confirm"><input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} />Confirmo que los datos de la solicitud son correctos.</label></div>
        <div className="assistant-card"><div className="assistant-head"><span className="spark">✳</span><div><p className="eyebrow">ASISTENTE</p><h2>Cuéntame qué buscas</h2></div></div><p className="assistant-note">La IA puede proponer una opción. Tú revisas y confirmas antes de crear la reserva.</p><textarea value={assistantText} onChange={(e) => setAssistantText(e.target.value)} rows="3"/><button className="primary-button" onClick={suggest} disabled={busy}>{busy ? 'Procesando…' : 'Generar propuesta'} <span>→</span></button>{proposal && <div className="proposal"><b>Propuesta para revisar</b><p>{proposal.message || JSON.stringify(proposal.proposal || proposal)}</p><button onClick={acceptProposal} disabled={busy}>Confirmar reserva</button></div>}</div></section>
      {status && <div className="status" role="status">{status}</div>}
      <section className="privacy"><span>⌁</span><p><b>Privacidad primero.</b> La ocupación permanece desconocida hasta recibir telemetría autorizada. Las grabaciones de muestra no representan aforo actual.</p><span className="privacy-tag">SIN DATOS REALES</span></section>
    </main><footer><span>QUANTUMBYTE · CAMPUSTWIN AI</span><span>Prototipo para ENEISOFT XVI 2026</span></footer>
  </div>
}

export default App
