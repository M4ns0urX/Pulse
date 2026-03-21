# Pulse 💓

Sistema de localização em tempo real e monitoramento de sinais vitais de trabalhadores em mineradoras, conforme **NR-22**.

Arquitetura distribuída em três camadas: bracelete wearable → totens fixos → servidor local. Sem dependência de GPS ou conectividade externa para operação crítica.

---

## Arquitetura

```
┌─────────────────────────────────────┐
│  BRACELETE  (ESP32-S3 + DW3000)     │  ← usa o trabalhador no antebraço
│  SpO₂ · BPM · IMU · UWB · BLE      │
└────────────┬─────────────┬──────────┘
             │ UWB ranging │ BLE telemetria
             ▼             ▼
┌─────────────────────────────────────┐
│  TOTEM  (Raspi 3 + DW3000 anchor)   │  ← fixo na parede, a cada 15–20m
│  Fila de prioridade · PoE · Nobreak │
└──────────────────┬──────────────────┘
                   │ Ethernet (anel RSTP)
                   ▼
┌─────────────────────────────────────┐
│  MINI SERVER  (Proxmox)             │  ← local na mina
│  InfluxDB · Grafana · FastAPI       │
│  WireGuard VPN  →  SaaS (futuro)   │
└─────────────────────────────────────┘
```

## Repositório

```
pulse/
├── docs/
│   ├── arquitetura.md       # visão técnica completa do sistema
│   ├── nr22.md              # conformidade com a norma regulamentadora
│   ├── roadmap.md           # fases de desenvolvimento
│   ├── hardware/
│   │   ├── bracelete.md     # ESP32, DW3000, sensores, pinagem, BOM
│   │   ├── totem.md         # Raspi 3, PoE, nobreak, posicionamento
│   │   └── servidor.md      # Proxmox, VMs, stack de software
│   └── rede/
│       ├── topologia.md     # Ethernet, anel RSTP, LoRa fallback
│       └── mqtt.md          # tópicos, QoS, estrutura dos payloads
│
├── simulator/               # simulação Python — sem hardware necessário
│   ├── bracelet/
│   └── main.py
│
├── server/                  # backend do servidor local
│   ├── processor/           # consome MQTT → grava InfluxDB
│   └── api/                 # FastAPI REST + WebSocket
│
├── dashboard/               # frontend web (MVP funcional)
│
└── firmware/                # código ESP32 — fase futura
    └── esp32/
```

## Stack

| Camada | Tecnologia |
|---|---|
| Microcontrolador | ESP32-S3, firmware Arduino/ESP-IDF |
| Localização | UWB DW3000 (Qorvo) — precisão 10–30cm |
| Telemetria | BLE 5.0 nativo do ESP32 |
| Sensores | MAX30102 (SpO₂/BPM), LSM6DSO (IMU) |
| Gateway | Raspberry Pi 3B+, Python 3.11 |
| Rede | Ethernet Cat6, PoE 802.3af, RSTP |
| Broker | Mosquitto MQTT 2.x |
| Storage | InfluxDB 2.x (série temporal) |
| Backend | FastAPI + asyncio |
| Dashboard | Grafana + HTML/JS |
| Infra | Docker Compose, Proxmox VE |
| VPN | WireGuard |

## Quick Start — Simulação

```bash
git clone https://github.com/seu-usuario/pulse
cd pulse

# roda o simulador (sem dependências externas)
python3 simulator/passo1_bracelete.py

# ou sobe a stack completa com Docker
docker compose up -d
python3 simulator/main.py --workers 20
```

## Documentação

- [Arquitetura técnica](docs/arquitetura.md)
- [Conformidade NR-22](docs/nr22.md)
- [Hardware — Bracelete](docs/hardware/bracelete.md)
- [Hardware — Totem](docs/hardware/totem.md)
- [Hardware — Servidor](docs/hardware/servidor.md)
- [Rede e resiliência](docs/rede/topologia.md)
- [Protocolo MQTT](docs/rede/mqtt.md)
- [Roadmap](docs/roadmap.md)

## Conformidade NR-22

Limiares implementados conforme a norma:

| Sensor | Normal | Atenção | Urgente | Crítico |
|---|---|---|---|---|
| SpO₂ | ≥ 94% | 91–94% | 88–91% | < 88% |
| BPM | 60–98 | 98–115 | 115–132 | > 132 ou < 42 |
| Bateria | ≥ 20% | 18–20% | 8–18% | < 8% |
| Queda | — | — | — | accel > 3.5g + imobilidade |
