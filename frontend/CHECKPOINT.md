# Checkpoint de frontend — Marco / QuantumByte

Registro: 7 de noviembre de 2026, 10:17 America/Lima.
Rama: `frontend/catalogo-estados`.
Commit base: `390e5c122a20768e3649dc0c7919e4d2602b6702`.

## Incluido

- Navegación por vistas con URL hash, opción activa y soporte de recarga/Atrás/Adelante.
- Panel de disponibilidad con croquis seleccionable, detalle del ambiente y estados administrativos y físicos separados.
- Carga, error, reintento y descarte de respuestas atrasadas del catálogo. Actualización de salas cada 3 segundos.
- Búsqueda por capacidad y equipo; reserva con confirmación humana y bloqueo de envío. Reutilización de request_id ante reintento del mismo contenido en la sesión.
- Vista del asistente y revisión de su propuesta antes de abrir la confirmación.
- Selector de demostración Usuario común / Secretaría, preferencia local y posibilidad de elegir de nuevo.
- Agenda administrativa del día: ocho franjas y tres salas a partir de la API existente; fallos y totales parciales explícitos.
- Registro desde una celda disponible, listado y filtro de reservas confirmadas del día.
- Identidad QuantumByte, emblema de San Marcos, favicon y movimientos con soporte de reducción de animaciones.
- Adaptación a pantallas estrechas y etiquetas/foco de teclado en controles principales.

## Arranque

Desde `frontend/`, con Node/npm compatibles con el lockfile:

```powershell
npm.cmd ci
$env:CAMPUSTWIN_API_TARGET="http://<IP_DEL_BACKEND>:8000"
npm.cmd run dev -- --host 127.0.0.1
```

La variable real es `CAMPUSTWIN_API_TARGET`, leída por la configuración de Vite. Sin ella, el proxy usa `http://127.0.0.1:8000`. Las solicitudes del navegador usan `/api` en el mismo origen. El backend sirve la compilación según el README del repositorio.

## Verificación

Ejecutados para este checkpoint:

- `npm.cmd run build`: PASS.
- `npm.cmd run lint`: PASS, sin advertencias del linter.
- `git diff --check`: PASS.

Observados durante la implementación de esta sesión:

- API accesible desde React y catálogo de tres salas recibido a través del proxy.
- Navegación, selección de sala, filtros, confirmación requerida y bloqueo por capacidad.
- Selección/cambio de perfil, persistencia al recargar y regreso al selector inicial.
- Secretaría consultó las ocho franjas reales; una celda abrió R02/S18 en el formulario, sin crear reserva durante esa revisión.
- Casos de agenda parcial, respuestas inválidas y almacenamiento de perfil bloqueado comprobados con solicitudes de prueba aisladas.
- Diseño revisado a 320, 390 y 1440 px; tabla de agenda con desplazamiento interno en móvil.

No ejecutado como parte de este checkpoint: nueva reserva real, aprobación/rechazo administrativo, envío de correo, llamada exitosa al proveedor LLM o inferencia real de cámara. Estos resultados no se presumen por la presencia de la interfaz.

## Límites para integración

- El selector de perfil cambia la interfaz de demostración; no autentica ni concede permisos de servidor.
- La agenda usa solo las cinco rutas existentes. El listado se deriva de reservas confirmadas por fecha/franja; no hay solicitudes pendientes ni buzón de correo conectado.
- El backend mantiene su identidad de demostración. Datos de solicitante y autorización de Secretaría requieren contrato acordado por Leonardo.
- Revisar [SECRETARIA-INTEGRACION.md](SECRETARIA-INTEGRACION.md) para el siguiente trabajo de backend y [public/brand/README.md](public/brand/README.md) para procedencia de imágenes.
- Este checkpoint modifica únicamente `frontend/`. Leonardo mantiene la integración a `main` y la autoridad del contrato.
