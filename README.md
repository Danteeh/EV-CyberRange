# EV-CyberRange

Simulador de estaciones de carga para vehículos eléctricos.

## Objetivo

Desarrollar un simulador visual e interactivo de estaciones de carga
para vehículos eléctricos, permitiendo representar y controlar
virtualmente el comportamiento de una estación de carga.

## Tecnologías principales

- EVerest
- SteVe
- OCPP
- MQTT
- Docker
- Python
- JavaScript / TypeScript

## Arquitectura prevista

```text
┌─────────────────────────────┐
│     Interfaz del simulador  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│       Aplicación propia     │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│          EVerest            │
│     Estación virtual EVSE   │
└──────────────┬──────────────┘
               │
             OCPP
               │
               ▼
┌─────────────────────────────┐
│           SteVe             │
│            CSMS             │
└─────────────────────────────┘
