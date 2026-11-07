# Informe de QA de la candidata

Base integrada `108201e5d754885e3b479d9df3e62054c7b9bca9`. En integración: backend 75/75 y frontend 23/23; lint y build frontend correctos. Reserva aislada: 201, reintento idempotente 200, conflicto 409 y reserva visible en Secretaría. T31 backend aislado: muestra sintética aceptada 202, people_detected y unknown/stale tras 16,03 s, sin cambio administrativo. T53: evidencia comunicada de pestaña oculta 26,28 s y GET 86,4 ms tras recuperar visibilidad.

Responsive: 18 combinaciones cargaron sin desbordamiento horizontal global medido; revisión completa de controles y superposiciones pendiente. Solicitud vacía y franja iniciada bloquearon POST; fechas vacía, pasada y fuera de horizonte pendientes. La suite de visión no se ejecutó por ausencia de numpy/ultralytics en el entorno consultado. No se acredita inferencia real YOLO ni DeepSeek real. Telemetría sintética no demuestra cámara, precisión ni FPS. Despliegue y smoke tests públicos pendientes.
