function NavigationIcon({ type }) {
  const paths = {
    spaces: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    booking: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M7 3v4m10-4v4M3 11h18m-13 5h3" /></>,
    assistant: <><path d="m12 3 2.6 6.4L21 12l-6.4 2.6L12 21l-2.6-6.4L3 12l6.4-2.6Z" /></>,
    search: <><circle cx="10" cy="10" r="6" /><path d="m15 15 5 5" /></>,
    occupancy: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></>,
    admin: <><rect x="3" y="4" width="18" height="17" rx="2" /><path d="M3 10h18M8 2v4m8-4v4M8 14h3m3 3h3" /></>,
  }

  return <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[type]}</svg>
}

const navigation = [
  ['spaces', 'Panel de espacios'],
  ['booking', 'Reservar ambiente'],
  ['search', 'Buscar ambientes'],
  ['occupancy', 'Ocupación observada'],
  ['assistant', 'Asistente IA'],
]

export default function DashboardLayout({ children, activeView, profile, onProfileChange, busy }) {
  const isAdmin = profile === 'admin'
  const menu = isAdmin ? [['admin', 'Panel de Secretaría'], ...navigation.map(([view, label]) => [view, view === 'booking' ? 'Registrar reserva' : view === 'spaces' ? 'Disponibilidad' : label])] : navigation
  return <div className="dashboard-shell">
    <a className="skip-link" href="#main-content" onClick={(event) => { event.preventDefault(); const main = document.getElementById('main-content'); main?.focus(); main?.scrollIntoView() }}>Saltar al contenido</a>
    <aside className="sidebar" aria-label="Navegación principal">
      <a className="sidebar-brand" href={isAdmin ? '#admin' : '#spaces'} aria-label="CampusTwin AI, inicio">
        <span className="brand-mark" aria-hidden="true"><span /></span>
        <span>CampusTwin<small>AI / QUANTUMBYTE</small></span>
      </a>

      <div className="navigation-group">
        <p className="navigation-label">{isAdmin ? 'GESTIÓN DE LABORATORIOS' : 'ESPACIOS'}</p>
        <nav>
          {menu.map(([view, label]) => <a key={view} className={`navigation-link ${activeView === view ? 'active' : ''}`} href={`#${view}`} aria-current={activeView === view ? 'page' : undefined}><NavigationIcon type={view} />{label}</a>)}
        </nav>
      </div>

      <div className="sidebar-bottom">
        <div className="team-signature">
          <img src="/brand/quantumbyte-mark-v1.png" alt="Logo de QuantumByte" width="52" height="52" />
          <div><span className="team-eyebrow">DESARROLLADO POR</span><strong>QuantumByte</strong><span className="team-caption">ENEISOFT XVI · 2026</span></div>
        </div>
        <div className="sidebar-note">
          <span className="demo-badge">MODO DEMOSTRACIÓN</span>
          <p>Catálogo y ambientes ficticios.<br />Reservas de demostración.</p>
        </div>
        <div className="sidebar-footer"><span className="sidebar-status-dot" />Prototipo · ENEISOFT XVI</div>
      </div>
    </aside>

    <div className="workspace">
      <header className="topbar">
        <div className="workspace-label"><strong>CampusTwin AI</strong><span>/</span><span>Gestión de espacios</span></div>
        <div className="topbar-actions">
          <span className="header-badge">DEMOSTRACIÓN</span>

          <div className="header-team"><span className="team-avatar"><img src="/brand/quantumbyte-mark-v1.png" alt="Logo de QuantumByte" width="34" height="34" /></span><span className="team-name">QuantumByte<small>CampusTwin AI</small></span></div>
        </div>
      </header>
      <div className={`profile-bar ${isAdmin ? 'admin-profile' : ''}`}>
        <div><span className="profile-view-label">{isAdmin ? 'Vista de Secretaría' : 'Vista de usuario'}</span><span className="profile-scope">Perfil de demostración</span><small className="profile-notice" id="profile-limit">Sin autenticación ni permisos administrativos reales; las reservas no son registros institucionales.</small></div>
        <label>Cambiar perfil<select aria-label="Perfil de demostración" aria-describedby="profile-limit" value={profile} disabled={busy} onChange={(event) => onProfileChange(event.target.value)}><option value="user">Usuario común</option><option value="admin">Secretaría / Administrador</option><option value="choose">Elegir de nuevo…</option></select></label>
      </div>
      <p className="independence-notice">Prototipo académico independiente de QuantumByte. CampusTwin AI no constituye una plataforma oficial ni un canal de reservas institucional de la Universidad Nacional Mayor de San Marcos.</p>
      <p className="data-notice">Catálogo y ambientes ficticios; reservas de demostración. La ocupación física puede proceder de telemetría experimental del sensor; las grabaciones son muestras registradas.</p>
      {children}
      <footer className="workspace-footer"><span>CATÁLOGO FICTICIO · RESERVAS DE DEMOSTRACIÓN</span><span className="footer-team"><img src="/brand/quantumbyte-mark-v1.png" alt="" width="20" height="20" />QuantumByte / CampusTwin AI</span></footer>
    </div>
  </div>
}
