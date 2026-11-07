# Vista de Secretaría — alcance aprobado para la hackathon

Leonardo confirmó que se conserva la ampliación de Secretaría dentro del contrato API 1.0 existente.

## Incluido

- Agenda de las ocho franjas y las tres salas sintéticas, consultada mediante GET /api/rooms.
- Reservas confirmadas del día, indicadores derivados de respuestas reales y filtro por sala/horario/código.
- Registro desde una celda disponible mediante el formulario existente y POST /api/reservations, con confirmación humana.
- Detalle de la reserva con sala, franja y código devuelto por el backend.
- Estado físico independiente del estado administrativo; telemetría de David vigente, expirada, sin sensor o con error.
- Selector explícitamente rotulado «Perfil de demostración» y «Sin autenticación ni permisos reales». La preferencia local solo cambia la interfaz.

## Fuera del alcance de esta hackathon

No se implementan solicitudes pendientes, aprobaciones, rechazos, correos, autenticación ni permisos administrativos reales. No se añaden rutas ni se cambia el contrato de Leonardo.

## Conexión local

La variable es CAMPUSTWIN_API_TARGET. Puede indicarse en el entorno de Vite o en frontend/.env.development.local, ignorado por Git. El navegador usa /api en el mismo origen; la URL de la laptop de Leonardo queda solo en la configuración local.

## Revisión

Ver [INTEGRATION-REPORT.md](INTEGRATION-REPORT.md) para pruebas ejecutadas, evidencia de telemetría y la reserva sintética que quedó registrada. La revisión e integración a main corresponde a Leonardo.
