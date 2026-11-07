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

- npm.cmd run test: 10 pruebas, 10 PASS. Incluyen TTL al límite de 15 s, cero detecciones, conteo positivo, error, grabación, dato inválido, perfiles y agenda parcial.
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
