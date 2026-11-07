# Propuesta de despliegue Render

Estado: configuración propuesta; no se ha creado infraestructura ni se ha validado una URL pública. La imagen construye el frontend en una etapa Node y sirve su `dist` junto con la API desde FastAPI. Las bases usan digests y `requirements-render-lock.txt` fija las versiones Python verificadas; el lock no incluye hashes de paquetes y su disponibilidad futura no está garantizada. El servicio usa un proceso Uvicorn y una instancia. La aplicación ya establece WAL y `foreign_keys` en cada conexión; no se modificó su lógica.

El Blueprint apunta explícitamente a `codex/campustwin-render-infra`, con auto-despliegue desactivado, región Ohio, plan Starter y disco de 1 GB en `/var/data`. El montaje y el volumen solo son efectivos tras la creación y comprobación real en Render. Un servicio con disco no dispone de escalado horizontal ni despliegues sin interrupción. La telemetría vive en memoria y se pierde al reiniciar; sin medición vigente se muestra `unknown`.

## Variables de ejecución

Configurar secretos en Render, nunca en el repositorio, la imagen, parámetros Docker, registros ni variables Vite:

- `CAMPUSTWIN_DB=/var/data/campustwin.db`: ruta bajo el disco montado.
- `DEEPSEEK_MODEL=deepseek-flash`: identificador configurable.
- `DEEPSEEK_API_KEY`: secreto del backend; sin clave el asistente funciona en modo degradado.
- `VISION_INGEST_TOKEN`: secreto exclusivo del backend y del emisor autorizado; sin token la ingesta no está disponible.

`sync: false` solicita valores durante la creación del Blueprint; seleccionar explícitamente el modo degradado o establecer valores seguros mediante la interfaz de Render antes de la aplicación. No copiar tokens de otras instancias. `PORT` lo suministra Render. El frontend y la API comparten origen; el proxy de desarrollo Vite no interviene en producción.

## Respaldo y recuperación

No copiar solo el archivo `.db` mientras SQLite utiliza WAL. Usar la API SQLite `backup()` para producir una copia consistente, transferirla a almacenamiento protegido fuera del servicio y verificar su recuperación con `PRAGMA integrity_check` en una base aislada. Probar periódicamente la restauración: detener escrituras de forma coordinada, respaldar el estado actual, restaurar la copia validada en el disco y comprobar integridad y funcionamiento antes de reabrir el servicio. Una restauración sobre la base activa puede descartar cambios posteriores; no hacerla sin autorización. Los snapshots de disco no sustituyen respaldos consistentes de SQLite.

## Validación pendiente antes de aplicar

1. Revisar costos y autorizar expresamente Starter y disco; verificar que el nombre del servicio no administre un recurso existente.
2. El esquema JSON oficial se validó localmente; ejecutar además `render blueprints validate render.yaml` con CLI compatible y verificar el SHA remoto y la rama seleccionada.
3. Revisar las pruebas y limitaciones del informe [DOCKER_VALIDATION.md](DOCKER_VALIDATION.md), especialmente persistencia con volumen tras reinicio e inspección de contexto e imagen.
4. Aprobar el modelo de acceso público: los perfiles son de demostración y no autentican; las reservas no son institucionales. Verificar avisos y política de acceso antes de exponer el servicio.
5. Aplicar el Blueprint solo con autorización de costos; confirmar disco montado, variables y una sola instancia. Comprobar salud, frontend, catálogo y reserva exclusivamente de prueba, persistencia y el SHA desplegado. No llamar a DeepSeek ni activar cámara sin autorización.

## Estimación

Referencia pública consultada el 7 de noviembre de 2026: Starter / 0.5 CPU y 512 MB aproximadamente USD 7/mes y disco USD 0,25/GB-mes; para 1 GB, base aproximada USD 7,25/mes, antes de impuestos, consumo adicional, tarifas del workspace, proveedor IA y cambios de precio. Confirmar en el panel antes de aprobar. Fuentes: https://render.com/pricing y https://render.com/docs/compute-plans.
