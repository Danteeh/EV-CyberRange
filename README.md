# EV-CyberRange

Simulador de ciberseguridad OT para infraestructura de carga de vehículos eléctricos.

## Estructura del Proyecto

```
EV-CyberRange/
├── frontend/           # React + Vite - UI del simulador
│   ├── src/
│   │   ├── components/ # Componentes React
│   │   ├── store.js    # Estado global (Zustand)
│   │   └── ...
│   └── package.json
│
└── simulator/
    └── backend/        # FastAPI - API del simulador
        ├── app/
        │   ├── routers/      # Endpoints API
        │   ├── mqtt_bridge.py # Bridge MQTT hacia EVerest
        │   ├── state_store.py # Estado de la estación
        │   ├── attack_engine.py # Motor de ataques
        │   └── models.py     # Modelos de datos
        └── requirements.txt
```

## Requisitos

- Node.js 18+
- Python 3.11+
- Docker Desktop (para EVerest/MQTT/SteVe)
- WSL2 con Ubuntu (para EVerest)

## Instalación Rápida

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd simulator/backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Estado

Este proyecto está en desarrollo activo. El frontend y backend son funcionales; EVerest y la integración OCPP se configuran por separado.

## Licencia

MIT
