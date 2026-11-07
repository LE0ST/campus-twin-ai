# Informe de aseguramiento de calidad

## 1. Evidencia de integración (7 de noviembre de 2026)

La base integrada `108201e5d754885e3b479d9df3e62054c7b9bca9` reportó **75/75 pruebas backend** y **23/23 frontend**, con lint y compilación correctos.

| Comprobación | Resultado comunicado |
| --- | --- |
| Reserva ficticia | HTTP 201 |
| Reintento idempotente | HTTP 200 |
| Conflicto de reserva | HTTP 409 |
| Agenda de Secretaría | Reserva visible |
| Telemetría sintética T31 | HTTP 202; estado `people_detected` |
| Caducidad de lectura | `unknown/stale` tras 16,03 s |
| Reactivación T53 | Pestaña oculta 26,28 s; nueva consulta en 86,4 ms |
| Diseño adaptable | 18 combinaciones sin desbordamiento horizontal global observado |

Se comprobó el bloqueo de solicitudes vacías y franjas ya iniciadas. Quedaron pendientes casos adicionales de fechas vacías, pasadas y fuera de horizonte, así como revisión completa de controles y superposiciones.

## 2. Validación Docker local

Terra informó compilación de imagen, endpoints, reserva ficticia, idempotencia, conflicto y persistencia con **volumen local**. La persistencia local **no demuestra persistencia en Render Free**. Ver [informe Docker](DOCKER_VALIDATION.md).

## 3. Evidencia posterior del despliegue y la cámara

- El servicio Render fue verificado en estado **Live** para el commit `d01687d`.
- El usuario confirmó respuestas reales del asistente DeepSeek en la demo pública.
- David ejecutó YOLO11n con webcam USB: el registro mostró detecciones de 1 y 2 personas. Su instalación de PyTorch no disponía de CUDA, por lo que el detector continuó en CPU.
- Los primeros envíos de telemetría devolvieron **401** por token incorrecto. Tras corregirlo, el usuario confirmó recepción de telemetría en Render.

Estas observaciones son reportes de ejecución y comprobaciones puntuales; no equivalen a una prueba automatizada completa ni a una evaluación de precisión de YOLO.

## 4. Pendientes y limitaciones

- Comprobar visualmente el cambio de conteo en `R01` y su caducidad durante una demostración pública.
- Revisar accesibilidad, controles y diseño adaptable de forma integral.
- Ejecutar nuevamente toda la batería de pruebas si se modifica código funcional.
- No existe autenticación institucional ni control real de permisos.
- SQLite en Render Free es efímero y no garantiza persistencia.
- No se ha acreditado precisión, tasa de fotogramas ni robustez del detector en diferentes condiciones.
