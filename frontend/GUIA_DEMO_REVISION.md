# CampusTwin AI: guía de frontend y estado para revisión

**Documento revisado — 7 de noviembre de 2026, hora de Lima.** Responsable del frontend: Marco. Este commit publica documentación; las correcciones de código descritas siguen locales y todavía no están incluidas en la rama publicada ni disponibles para que Leonardo las integre.

## Propósito y alcance

CampusTwin AI es un prototipo con tres ambientes sintéticos para consultar reservas y una estimación de ocupación. La vista de Secretaría permite consultar la agenda de ocho franjas, revisar reservas confirmadas y registrar una reserva mediante confirmación humana. El selector de perfil es de demostración: no autentica ni concede permisos administrativos reales.

La vista de usuario incluye el panel de ambientes, búsqueda, formulario de reserva, ocupación observada y asistente. No se implementan correos, solicitudes pendientes, aprobaciones ni rechazos. No se han medido tiempos de ahorro ni se representa disponibilidad real de la UNMSM.

## Arranque y conexión

1. Leonardo inicia el backend integrado y confirma su dirección y puerto. Su servidor es el único dueño de las reservas y de la base de demostración.
2. En `frontend/`, instalar dependencias si aún no están presentes: `npm ci`.
3. Configurar `CAMPUSTWIN_API_TARGET` localmente para apuntar al backend acordado; `frontend/.env.development.local` es una opción ignorada por Git. Si el backend corre en la misma máquina, el proxy usa por defecto `http://127.0.0.1:8000`.
4. Ejecutar `npm run dev` en `frontend/` y abrir la dirección que informe Vite. El navegador consulta `/api` mediante ese proxy. Para una compilación: `npm run build`.
5. Mantener secretos y tokens únicamente en el entorno del backend o de visión, no en el frontend ni en Git. El frontend solo necesita la dirección del backend, sin credenciales.

## Recorrido para la demostración

1. Elegir «Usuario común» o «Secretaría / Administrador» en el selector identificado como perfil de demostración.
2. Elegir una fecha y franja futura válida. Consultar los tres ambientes y, en Secretaría, las ocho franjas. La reserva administrativa y la ocupación observada son estados independientes.
3. Desde una celda disponible, revisar ambiente, asistentes y equipos; marcar la confirmación y registrar. El backend valida y entrega el código. No enviar una reserva de prueba sin coordinar qué franja se usará en la demostración.
4. En ocupación, una lectura positiva indica personas detectadas; cero significa «Sin detecciones», no que la sala esté vacía. R02/R03 no tienen sensor en el escenario probado. Una señal vencida muestra ocupación desconocida y no cambia la reserva.
5. Si el asistente y proveedor están disponibles, pedir una propuesta en una franja libre. La propuesta no reserva hasta la confirmación. Si el servicio falla, utilizar el formulario manual e indicar la limitación.

## Revisión de estabilidad local — 14:23–14:30

- Se añadió un reloj monotónico derivado de `server_time` para que una lectura caduque sin depender de una respuesta nueva ni del reloj de pared del cliente. Se descuenta de forma conservadora el tiempo transcurrido por la consulta.
- Se invalida el catálogo al ocultar o reanudar la página; se limpia la confirmación y la propuesta, y Secretaría vuelve a consultar las ocho franjas. Se ignoran respuestas de una sesión anterior.
- Se corrigió una variable de la agenda que impedía consultar sus franjas tras el cambio de ciclo de vida.
- **T31, prueba local sintética:** en el navegador se vio R01 reservado con una persona detectada; al retener nuevas respuestas, cambió a «Ocupación desconocida» y «La última lectura venció», manteniendo «Reservada». La muestra sintética tenía 6 segundos de vigencia restante al recibirse; su duración total era 15 segundos. No usó la cámara ni el backend real.
- **T53, pruebas automáticas parciales:** los tests de los manejadores de ocultación, reanudación y restauración pasan. Todavía debe verificarse con una suspensión real de pestaña y una consulta retenida que la interfaz invalide antes de mostrar datos anteriores y que la confirmación quede deshabilitada. Ocultar el panel del navegador de pruebas no cambió `document.visibilityState`, por lo que ese intento no constituye la prueba T53.
- **Secretaría, prueba local sintética:** la interfaz cargó 8/8 franjas, una reserva de ejemplo y 23 celdas disponibles. Estos valores no proceden del backend de Leonardo.
- **Desconexión simulada:** tras el timeout de la consulta, la interfaz mostró error y deshabilitó la reserva. No se realizó ninguna escritura en la base compartida.
- `npm test`: **14/14 PASS**, pruebas automáticas de funciones y manejadores con datos de prueba; `npm run build`: PASS; `npm run lint`: PASS. No sustituyen la prueba real de T53 ni el ensayo de punta a punta.

## Evidencia anterior y pendientes con el equipo

Antes de estos cambios, T28 y T30 se comprobaron con el backend real y la cámara de David; detalles y horas en [INTEGRATION-REPORT.md](INTEGRATION-REPORT.md). La reserva sintética registrada en R01/S14 entonces fue `8589a939-c97d-4956-be31-283701ec963a`. El estado actual de la base debe consultarse de nuevo.

En la revisión de las 14:25, `http://10.96.239.62:8000/api/health` no respondió desde esta laptop. Pedir a Leonardo la dirección actual y confirmación de que está ejecutando la versión integrada antes de repetir la prueba de red. No reiniciar su servidor ni crear un segundo escritor sobre su base sin coordinarlo.

Con Leonardo y David, verificar en la versión candidata: catálogo, reserva real de demostración y conflicto, propuesta real del asistente y confirmación, lectura de cámara, T53 con pestaña realmente suspendida, y conectividad. Registrar resultados reales; ninguna prueba no ejecutada se considera aprobada.

## Entrega

La documentación revisada está publicada en la rama de frontend. Los cambios de código permanecen locales y necesitan su propio commit para que Leonardo pueda revisarlos e integrarlos. Según el cronograma del equipo: pruebas y ensayo 14:30–15:00, diapositivas y video 15:00–15:20, verificación de subida 15:20–15:45 y cierre 16:00. Confirmar el canal y los requisitos de entrega con el comité.
