# Módulo de Visión — CampusTwin AI (QuantumByte)

**Responsable:** David Yalle (Agente V - Antigravity)  
**Contrato:** API v1.0 ([API_CONTRACT.md](../API_CONTRACT.md))  
**Rama:** `vision` | **Directorio:** `vision/`

---

## 1. Hardware y Configuración Validada
- **Equipo:** Laptop Windows 11 x64, Ryzen 7 7735HS, 16 GB RAM.
- **GPU:** NVIDIA GeForce RTX 4060 Laptop GPU (8 GB VRAM) con CUDA 12.4.
- **Cámara:** Webcam USB EMEET S600 verificada en el índice 1 (640×480).
- **Modelo:** YOLO11n (`yolo11n.pt`, AGPL-3.0, `imgsz=640`), filtrado exclusivo a `classes=[0]` (personas).

---

## 2. Privacidad por Diseño
- **Sin biometría:** Únicamente conteo anónimo agregado en memoria.
- **Sin almacenamiento:** Prohibido guardar fotogramas en disco o enviarlos al servidor.
- **Transporte estricto:** Solo se transmiten valores numéricos enteros en $[0, 100]$ y marcas de tiempo UTC con sufijo `Z`.

---

## 3. Uso y Ejecución

### Variables de Entorno (Sin persistir secretos en Git):
```powershell
$env:VISION_INGEST_TOKEN = "<token-de-ingesta-de-leonardo>"
$env:CAMPUS_TWIN_BACKEND_URL = "http://10.96.239.62:8000"
```

### Ejecución en Modo Producción (GPU por defecto):
```powershell
python vision/main.py --backend http://10.96.239.62:8000 --camera 1
```

### Ejecución en Modo Respaldo (Fallback CPU):
```powershell
python vision/main.py --backend http://10.96.239.62:8000 --camera 1 --device cpu
```

### Ejecución sobre Clip Autorizado (Contingencia):
```powershell
python vision/main.py --backend http://10.96.239.62:8000 --clip ruta/al/clip.mp4
```

---

## 4. Ejecución de Pruebas Unitarias
```powershell
python -m unittest vision/test_vision.py
```
