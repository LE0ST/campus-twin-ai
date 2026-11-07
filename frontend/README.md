# Interfaz web de CampusTwin AI

Frontend desarrollado con **React 19 y Vite**, como parte del prototipo académico independiente de QuantumByte para ENEISOFT XVI 2026.

## Funcionalidades

- Pantalla inicial de selección de perfil de demostración.
- Catálogo de ambientes, búsqueda, horarios y reservas ficticias.
- Panel de Secretaría con agenda.
- Asistente de IA con revisión y confirmación humana.
- Visualización de ocupación observada mediante telemetría recibida del backend.

> **Aviso:** los perfiles no autentican usuarios ni conceden permisos administrativos reales. La información de ambientes y reservas es ficticia.

## Ejecutar en desarrollo

Desde la raíz del repositorio, iniciar el backend FastAPI en el puerto 8000. Después:

```powershell
cd frontend
npm ci
npm run dev
```

Vite utiliza el proxy `/api` hacia el backend local. Para modificar el destino de desarrollo, configurar `CAMPUSTWIN_API_TARGET` al iniciar Vite.

## Comprobaciones

```powershell
npm test
npm run lint
npm run build
```

El directorio `dist/` generado por `npm run build` puede servirse desde FastAPI. El despliegue público usa Docker en Render Free.

## Documentación relacionada

- [README principal](../README.md)
- [Arquitectura](../docs/ARCHITECTURE.md)
- [Informe de pruebas](../docs/QA_REPORT.md)
- [Guion de demostración](../docs/DEMO.md)
