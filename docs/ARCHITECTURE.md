# Arquitectura

React/Vite muestra catálogo, perfiles de demostración, reserva, ocupación y asistente. Las consultas `/api/rooms` distinguen estado administrativo y ocupación física. FastAPI valida fecha y franja de Lima, capacidad, equipos y confirmación; es el único escritor de reservas en SQLite. La confirmación está sujeta a disponibilidad y unicidad.

`POST /api/assistant/propose` valida restricciones, consulta DeepSeek mediante herramientas limitadas, verifica candidatos y no escribe reservas. `POST /api/reservations` realiza el registro confirmado. El agente opcional de visión emite conteos agregados a `POST /api/telemetry` con token; backend expira lecturas y frontend programa su caducidad y recarga al recuperar visibilidad. No se identifica a personas ni se guardan imágenes. Sin muestra vigente, ocupación desconocida.

Responsabilidades: Leonardo backend e integración; Marco frontend; David visión. Los cambios de contrato requieren autorización del líder y aviso a consumidores. SQLite local requiere un solo escritor: una instalación pública requiere persistencia y topología validadas antes de desplegar.
