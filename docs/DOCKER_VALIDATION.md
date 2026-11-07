# Informe de validación Docker

Aplicación base: `f004ac30af709b6f9335d057700f23d3191cd768`. Pruebas del 7 de noviembre de 2026, sin claves reales y usando contenedor local y volumen exclusivo; no se ha desplegado en Render.

| Prueba | Resultado y evidencia |
|---|---|
| Build | PASS: `docker build -t campustwin-infra-qa:locked .`, con bases por digest, `npm ci` y restricciones Python fijadas. |
| API y frontend | PASS: `/api/health`, `/api/rooms`, `/` y asset JS HTTP 200. Navegador mostró la portada y catálogo desde el mismo origen, sin errores de consola observados. |
| Reserva | PASS: base del volumen QA, reserva ficticia R02/S18 del 08/11/2026: HTTP 201; reintento mismo request_id 200 con el mismo ID; nuevo request_id 409. |
| Persistencia | PASS local: tras reiniciar el mismo contenedor con el mismo volumen, R02 seguía reservada con ID `c5da8ce5-6db8-4dbc-816f-148b9977ff4d`. No acredita persistencia en Render. |
| SQLite | PASS local: `database_list` apunta a `/var/data/campustwin.db`, `journal_mode=wal`, `foreign_keys=1` mediante `backend.main.connect`, `integrity_check=ok`. |
| Secretos y bases en imagen | PASS limitado: en `/app` de un contenedor nuevo no se encontraron archivos SQLite ni `.env` ni coincidencias de patrones típicos de clave; `/var/data` estaba vacío en la imagen. No es una auditoría exhaustiva de todas las capas o credenciales posibles. El contexto se limita por `.dockerignore`. |
| Regresión | PASS: 75 tests backend y 23 frontend con el entorno local existente. |
| Render y URL pública | NOT TESTED: no se ha creado ni aplicado infraestructura. |

El volumen local de QA contiene dos reservas sintéticas y se conserva para inspección. No usarlo para producción. La prueba no cubre DeepSeek ni cámara YOLO reales.
