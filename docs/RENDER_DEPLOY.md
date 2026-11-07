# Despliegue de CampusTwin AI en Render Free

## Servicio público verificado

| Parámetro | Valor |
| --- | --- |
| URL | https://campustwin-ai-demo.onrender.com |
| Identificador | `srv-dbnp5q49v7es73dcp1jg` |
| Nombre | `campustwin-ai-demo` |
| Plan | **Gratuito (Free)** |
| Región | Ohio |
| Entorno | Docker |
| Rama principal | `main` |
| Despliegue comprobado | `d01687d54909857cdba2b8e74ca41656a728f095`, estado **Live**, 7 de noviembre de 2026 |
| Despliegue automático | Desactivado |

Los cambios posteriores exclusivamente documentales no requieren una nueva compilación para que la aplicación siga funcionando. El estado **Live** no sustituye una prueba funcional completa.

## Arquitectura del despliegue

El `Dockerfile` compila React/Vite en una etapa Node y sirve el frontend compilado y la API desde FastAPI en un mismo origen. Render proporciona el puerto mediante `PORT`.

La variable `CAMPUSTWIN_DB=/tmp/campustwin-demo.db` dirige SQLite al almacenamiento temporal. **No existe un disco persistente**: reinicios, suspensiones o nuevos despliegues pueden eliminar las reservas de demostración. No se deben prometer respaldos ni persistencia permanente.

El archivo `render.yaml` es una referencia de configuración. **No aplicar un Blueprint para crear un segundo servicio** si ya se utiliza el servicio existente.

## Variables y secretos

Configurar en el panel **Environment** de Render:

| Variable | Uso |
| --- | --- |
| `DEEPSEEK_API_KEY` | Clave privada para el asistente |
| `DEEPSEEK_MODEL` | Modelo configurado, `deepseek-flash` |
| `VISION_INGEST_TOKEN` | Secreto que comparte el backend con el emisor autorizado |
| `CAMPUSTWIN_DB` | `/tmp/campustwin-demo.db` |

No publicar los valores secretos en el repositorio, capturas ni registros. Cambiar variables puede provocar un reinicio y la pérdida de datos efímeros.

## Conexión con la cámara

YOLO11n se ejecuta en una laptop externa, no en Render. El programa envía conteos anónimos a `POST /api/telemetry` mediante autenticación Bearer. Se espera **HTTP 202** para una medición aceptada y **401** si el token no coincide.

El equipo informó que la cámara detectó personas con PyTorch en CPU, que las primeras solicitudes devolvieron 401 y que, tras corregir el token, la telemetría llegó a Render. La verificación visual del cambio de conteo en `R01` debe realizarse por separado.

## Lista de comprobación

1. Confirmar que Render está en **Live** y que el SHA coincide con el despliegue deseado.
2. Verificar `GET /api/health` con HTTP 200.
3. Abrir `/` y comprobar que los recursos del frontend cargan.
4. Consultar `GET /api/rooms` con fecha y franja válidas.
5. Probar reservas exclusivamente ficticias y sus respuestas 201, 200 y 409.
6. Verificar el asistente con una solicitud de demostración.
7. Confirmar telemetría 202 y actualización visible de `R01`.
8. Informar a los evaluadores de los límites de privacidad, permisos y persistencia.

## Alternativa de pago no implementada

Terra validó localmente un contenedor con volumen y propuso Starter con disco de 1 GB, con costo estimado de USD 7,25 mensuales antes de cargos adicionales. **No se autorizó ni creó ese servicio de pago**. La evidencia local se conserva en [validación Docker](DOCKER_VALIDATION.md).
