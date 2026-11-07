# Integración de frontend / Secretaría / visión

Fecha: 7 de noviembre de 2026, America/Lima. Rama: frontend/catalogo-estados. Base del diff: d35a41643ee007500671ac82419757477630fc6a.

## Alcance conservado

Agenda de ocho franjas, reservas confirmadas, indicadores reales, registro y detalle. Sin solicitudes pendientes, aprobación/rechazo, correo ni nuevos endpoints. El perfil de Secretaría está identificado como demostración sin autenticación ni permisos reales.

## Pruebas con el backend real de Leonardo

- GET /api/health mediante el proxy local: HTTP 200, api_version 1.0.
- OpenAPI real consultado: siguen las cinco rutas existentes.
- GET /api/rooms: R01/R02/R03, capacidades 6/8/4 y ocho franjas del contrato.
- Agenda administrativa: 8/8 consultas satisfactorias, 24 celdas obtenidas del backend.
- El registro abierto desde R03/S17 precargó correctamente ambiente y franja y requirió marcar la confirmación.
- Se creó mediante la interfaz una reserva sintética: R03, 07/11/2026, S17 (17:00–18:00), 2 asistentes, sin equipos requeridos.
- Código confirmado y persistido por el backend: be99439e-f7bb-4024-bd0c-652afa8f8647.
- Un segundo POST para la misma sala/fecha/franja con request_id diferente devolvió HTTP 409, error.code reservation_conflict. El código de la reserva original se mantuvo.
- La agenda mostró 1 reserva y 17 combinaciones disponibles en la lectura posterior; la lista permitió filtrar y abrir el detalle del código.
- El navegador usa solicitudes /api en el mismo origen. La integración mediante Vite no requiere cambiar CORS del backend.

La reserva de prueba permanece en la base de demostración: R03/S17. No se intentó cancelarla ni alterar directamente SQLite. Estos datos no representan una reserva institucional.

## Telemetría de David: datos observados

Al comienzo de la revisión se observó R01 con source_id vision-david, mode live_camera, state unknown, reason stale, count null. El frontend presentó «Ocupación desconocida», «Lectura vencida», la hora de la muestra y su fuente, sin convertir la ausencia de lectura vigente en cero.

David confirmó por medio de Marco que había detenido el script para actualizar su pipeline y que reanudó envíos cada 3 segundos, con HTTP 202 Accepted. Esa respuesta HTTP es información proporcionada por David; el frontend comprobó el resultado consultando el backend.

Tras reanudarse el flujo, cuatro respuestas reales consecutivas mostraron:

| server_time UTC | observed_at UTC | expires_at UTC | Estado | Conteo |
| --- | --- | --- | --- | --- |
| 15:32:59.420400Z | 15:32:55Z | 15:33:10Z | people_detected | 1 |
| 15:33:02.503578Z | 15:32:58Z | 15:33:13Z | people_detected | 1 |
| 15:33:05.539059Z | 15:33:01Z | 15:33:16Z | people_detected | 1 |
| 15:33:08.607023Z | 15:33:04Z | 15:33:19Z | people_detected | 1 |

La interfaz mostró 1 persona detectada en R01, una lectura vigente en el indicador, la fuente vision-david y la hora local de actualización. R02/R03 permanecieron desconocidos por no_sensor. Se verificó la transición stale → lectura vigente; no se midió precisión del detector ni FPS.

Para comparar la expiración, la interfaz utiliza server_time de la respuesta, evitando depender del reloj de otra laptop. La consulta de salas continúa cada 3 segundos. Errores o timeout retiran disponibilidad y permiten reintentar.

## Verificaciones reproducibles

Desde frontend/:

- npm.cmd run test: 11 pruebas, 11 PASS. Incluyen TTL al límite de 15 s, cero detecciones, conteo positivo, error, grabación, dato inválido, perfiles y agenda parcial. Las 11 pruebas ya están incluidas en de36bf2; este cierre corrige el conteo del informe.
- npm.cmd run build: PASS.
- npm.cmd run lint: PASS.
- git diff --check: PASS.

La configuración local del proxy se comprobó con Vite: CAMPUSTWIN_API_TARGET apunta al backend anunciado por Leonardo. frontend/.env.development.local está ignorado por Git y no se publica en el commit.

## Límites de esta revisión

Los tests automáticos usan respuestas sintéticas aisladas; las observaciones de agenda, reserva y telemetría anteriores sí corresponden al backend compartido. No se probaron correos, aprobaciones, rechazo ni autenticación porque están fuera del alcance. El selector no controla autorización de servidor.

## Cierre de revisión en navegador

- La vista de ocupación mostró posteriormente 4 personas detectadas en R01, con lectura de las 10:35:30 de Lima. Se comprobó que el conteo visible cambia cuando cambia la telemetría.
- Consola del navegador sin errores de JavaScript ni CORS en el flujo revisado.
- A 320 px, el ancho de contenido y el ancho útil coincidieron (305 px con barra vertical); no hubo desbordamiento horizontal.
- El texto visible junto al selector dice «Perfil de demostración» y «Sin autenticación ni permisos reales».

## Cierre de T28 y T30 con David y Leonardo

Pruebas realizadas el 7 de noviembre de 2026. Horas locales de Lima (UTC−5). Se consultó el backend real mediante el proxy del frontend; no se capturaron ni guardaron imágenes de la cámara.

### T28 — detección positiva y cero detecciones: PASS

| Consulta del servidor (UTC) | Observación (Lima) | Estado de R01 | Conteo |
| --- | --- | --- | --- |
| 15:45:30.998690Z | 10:45:28 | people_detected | 1 |
| 15:46:40.343122Z | 10:46:38 | no_detections | 0 |

La interfaz mostró primero «1 persona detectada» y después «Sin personas detectadas» / «Sin detecciones». No se presentó el cero como prueba de que el ambiente estuviera vacío. Fuente vision-david, modo live_camera.

### T30 — emisor detenido y lectura vencida: PASS

Marco confirmó que David detuvo el emisor. La consulta del servidor a las 15:50:08.038342Z devolvió para R01:

- state: unknown; reason: stale; count: null.
- observed_at: 2026-11-07T15:48:48Z (10:48:48 de Lima).
- received_at: 2026-11-07T15:48:49.506952Z.
- expires_at: 2026-11-07T15:49:03Z (10:49:03 de Lima), 15 segundos después de observed_at.

El frontend mostró «Lectura vencida», «Ocupación desconocida» y «La última lectura venció. Esperando una nueva medición». No mostró cero como sustituto de una lectura vencida. Se comprobó el estado posterior al vencimiento; no se midió el instante exacto de la transición en pantalla.

Se compararon los 24 cruces de tres ambientes y ocho franjas antes y después: estados administrativos e identificadores sin cambios. Permanecieron las reservas confirmadas:

- R01/S14: 8589a939-c97d-4956-be31-283701ec963a.
- R03/S17: be99439e-f7bb-4024-bd0c-652afa8f8647.

Leonardo confirmó adicionalmente la visualización independiente de «Reservada» y el conteo real en R01. Las consultas de T28/T30 descritas arriba se hicieron en S18, disponible; la comparación de reservas incluyó también S14. No se crearon ni modificaron reservas durante estas dos pruebas.

### Verificación para integrar y alcance congelado

Reejecutados npm.cmd test (11/11 PASS), npm.cmd run build y npm.cmd run lint para este cierre. El cambio de cierre solo actualiza este informe; mantiene el código y las 11 pruebas del commit de36bf2. No añade funcionalidades ni cambia el backend, el contrato API o el perfil de demostración.

T28/T30 verifican el flujo con consultas periódicas activas. No certifican T31/T53: siguen pendientes la caducidad independiente cuando se bloquea el polling y la invalidación inmediata al volver de una pestaña suspendida. El tiempo utilizado por la presentación se actualiza con cada respuesta del catálogo; no hay un temporizador monotónico independiente ni un manejador visibilitychange. Esta limitación debe mantenerse visible en la revisión de estabilidad.
