# CampusTwin AI — instrucciones del repositorio competitivo

El líder autorizó la ejecución durante ENEISOFT XVI el 7 de noviembre de 2026. Las restricciones de la organización y el contrato conceptual en `G:\PYTHON\CampusTwinAI_Planning_2026-11-06\API_CONTRACT.md` siguen vigentes.

## Objetivo y alcance

- MVP: catálogo ficticio de tres ambientes, reservas por franjas fijas, validación en backend, confirmación humana, estados de reserva y ocupación separados y al menos una IA real conectada.
- Solo el backend escribe reservas. La propuesta LLM no persiste datos.
- Datos sintéticos claramente identificados. Nunca atribuirlos a la UNMSM.
- Sin reconocimiento facial, identificación individual, captura encubierta ni almacenamiento de imágenes.
- `no_detections` no prueba ausencia. Dato ausente, expirado o fallo de cámara significa `unknown`.
- El LLM no obtiene SQL, shell, URL arbitraria ni herramientas de escritura.

## Propiedad y cambios

- Leonardo: `backend/`, raíz, API, reservas e integración.
- Marco: `frontend/`.
- David: `vision/` cuando incorpore su módulo desde su equipo.
- No sobrescribir trabajo ajeno. Los cambios a contratos requieren autorización del líder y aviso a los consumidores.

## Calidad y seguridad

- Cada integrante revisa el diff de su módulo y comunica qué prueba ejecutó y el resultado real.
- No afirmar pruebas, funciones, FPS, precisión o conexión como superadas sin evidencia.
- Mantener una sola SQLite local en el backend. No compartir una base abierta por red ni iniciar escritores paralelos.
- Los secretos solo viven en variables locales del backend o agente de visión; nunca en Git, frontend, prompts, logs o capturas. Las variables Vite son públicas.
- Preferir cambios pequeños. Después de las 14:30 solo se corrigen bloqueos P0, se ensaya y se prepara la entrega.
- No ejecutar `git reset --hard`, `git clean`, force push, borrado de ramas o reescritura de historial.
- Antes de instalar una dependencia, comprobar que es necesaria, compatible y aceptada por el equipo. Registrar su licencia.
