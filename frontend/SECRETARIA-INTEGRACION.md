# Vista de Secretaría — alcance e integración

## Implementado en frontend

- Elección entre Usuario común y Secretaría / Administrador; selector siempre disponible en el encabezado.
- La preferencia se conserva localmente. Es un perfil de demostración, no un inicio de sesión ni autorización del servidor.
- Agenda del día: se combinan las ocho consultas existentes `GET /api/rooms?date=...&slot_id=...`.
- Indicadores derivados exclusivamente de consultas válidas. Si falta una franja, se presenta como sin datos y los totales conocidos se señalan como parciales.
- Lista de reservas confirmadas del día, con sala, franja y código que devuelve la API. No se inventa un solicitante.
- Una celda disponible abre el formulario existente `POST /api/reservations` con sala y franja seleccionadas. Registrar sigue requiriendo confirmación humana.
- Una celda reservada abre su detalle. El servidor sigue controlando las reglas de reserva.

## Coordinación necesaria con Leonardo

El backend actual solo tiene confirmaciones; no entrega solicitudes pendientes ni correos. Su usuario de demostración es fijo. Para gestionar el trabajo de recepción y aprobación hay que acordar y versionar el contrato de:

1. Identidad del solicitante y rol administrativo validado en el backend.
2. Registro y consulta de solicitudes: laboratorio, fecha, franja, participantes, equipamiento, solicitante y estado.
3. Aprobación/rechazo con responsable, motivo y marcas temporales; rechazo de doble reserva validado por el servidor.
4. Canal de respuesta o integración con correo, si entra en el alcance del equipo.

Los nombres de endpoints y esquemas nuevos deben ser acordados por el líder antes de implementarlos. No hay acciones de aprobar, rechazar o enviar correo simuladas como si estuvieran integradas.

## Mensaje para el equipo

Marco tiene lista la selección Usuario/Secretaría y una agenda administrativa basada en las ocho franjas de la API existente. Secretaría puede consultar y abrir el registro de una reserva. Para continuar con solicitudes por correo y aprobación necesitamos que Leonardo defina el contrato de solicitudes pendientes, identidad del solicitante y autorización administrativa. El selector actual cambia la interfaz de demostración; no concede permisos en el backend.
