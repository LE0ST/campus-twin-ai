export default function ProfileChooser({ onChoose }) {
  return <main className="profile-welcome">
    <header className="welcome-header"><div className="welcome-team"><img src="/brand/quantumbyte-mark-v1.png" width="42" height="42" alt="Logo de QuantumByte" /><span>QuantumByte<small>CampusTwin AI</small></span></div></header>
    <p className="independence-notice">Prototipo académico independiente de QuantumByte. CampusTwin AI no constituye una plataforma oficial ni un canal de reservas institucional de la Universidad Nacional Mayor de San Marcos.</p>
    <section className="welcome-content" aria-labelledby="welcome-title">
      <p className="welcome-eyebrow">CAMPUSTWIN AI · DEMOSTRACIÓN</p>
      <h1 id="welcome-title">Menos correos.<br /><em>Más claridad para reservar.</em></h1>
      <p className="welcome-description">Encuentra el laboratorio que necesitas o administra la agenda desde un solo lugar. Elige con qué perfil quieres continuar.</p>
      <div className="profile-options">
        <button type="button" className="profile-option" onClick={() => onChoose('user')}><span className="profile-option-icon user-icon" aria-hidden="true">↗</span><span className="profile-option-title">Usuario común</span><span className="profile-option-copy">Consulta disponibilidad, encuentra un ambiente y confirma tu reserva.</span><span className="profile-option-action">Entrar como usuario <span aria-hidden="true">→</span></span></button>
        <button type="button" className="profile-option admin-option" onClick={() => onChoose('admin')}><span className="profile-option-icon admin-icon" aria-hidden="true">▦</span><span className="profile-option-title">Secretaría / Administrador</span><span className="profile-option-copy">Revisa la agenda del día, localiza espacios libres y registra reservas.</span><span className="profile-option-action">Entrar a Secretaría <span aria-hidden="true">→</span></span></button>
      </div>
      <p className="profile-demo-note">Catálogo y ambientes ficticios; reservas de demostración. La ocupación física puede provenir de telemetría experimental y las grabaciones son muestras registradas. Esta elección cambia la vista; no inicia sesión ni concede permisos reales. Puedes cambiar de perfil desde el encabezado.</p>
    </section>
    <footer className="welcome-footer">Prototipo local · ENEISOFT XVI · QuantumByte</footer>
  </main>
}
