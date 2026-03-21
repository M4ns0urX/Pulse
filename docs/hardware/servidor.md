# Hardware — Servidor Local

## Hardware Recomendado

| Componente | Especificação |
|---|---|
| CPU | Intel N100 ou N305 (quad/octa-core, TDP 6–15W) |
| RAM | 16GB DDR5 |
| Armazenamento OS | SSD NVMe 256GB |
| Armazenamento dados | HDD 1TB ou SSD SATA 512GB (histórico InfluxDB) |
| Rede | 2x Ethernet Gigabit (LAN mina + uplink VPN) |
| Alimentação | UPS/nobreak dedicado (mínimo 30min de autonomia) |

Opções de mini desktop: Beelink EQ12, MinisForum UM350, Minix NEO N42C-4.

---

## Virtualização — Proxmox VE

Todos os serviços rodam isolados em containers LXC ou VMs dentro do Proxmox:

```
Proxmox VE
├── LXC: mosquitto       (256MB RAM)   broker MQTT
├── LXC: influxdb        (2GB RAM)     banco de série temporal
├── LXC: processor       (512MB RAM)   consome MQTT → InfluxDB
├── LXC: api             (512MB RAM)   FastAPI REST + WebSocket
├── LXC: grafana         (512MB RAM)   dashboard visual
└── VM:  wireguard       (256MB RAM)   VPN para acesso externo
```

Benefícios do Proxmox:
- Snapshots e backups automáticos por container
- Restart automático de serviços em falha
- Isolamento de falhas entre serviços
- Fácil migração para hardware mais potente

---

## Stack de Software

### Mosquitto MQTT
Broker central. Todos os totens publicam aqui, todos os serviços consumem daqui.

```
# tópicos principais
pulse/+/+/telemetry    QoS 1  dados de sensor
pulse/+/+/position     QoS 1  posição XYZ
pulse/+/+/alert        QoS 2  alertas (entrega garantida)
pulse/totem/+/heartbeat QoS 0  status dos totens
pulse/system/emergency  QoS 2  emergência geral
```

### InfluxDB 2.x
Banco de dados de série temporal. Armazena toda a telemetria.

- **Retention policy:** 90 dias (ajustável)
- **Measurements:** `worker_telemetry`, `worker_alerts`, `totem_status`
- **Tags:** bracelet_id, worker_name, zone, totem_id, priority

### FastAPI
API REST + WebSocket para o dashboard web.

```
GET  /api/workers              lista todos os workers com último status
GET  /api/workers/{id}         detalhe de um worker
GET  /api/alerts               últimos alertas
GET  /api/totems               status de todos os totens
WS   /ws/live                  stream em tempo real (WebSocket)
```

### Grafana
Dashboard visual conectado diretamente ao InfluxDB via datasource Flux.

Painéis principais:
- Mapa de calor da mina com posição dos trabalhadores
- Série temporal de SpO₂ e BPM por trabalhador
- Tabela de alertas ativos
- Status dos totens (uptime, pacotes/s)

### WireGuard VPN
Túnel seguro para acesso externo ao dashboard e futura integração SaaS.

```
# cada mineradora terá seu próprio peer
[Peer]
PublicKey = <chave-publica-cliente>
AllowedIPs = 10.10.X.0/24
```

---

## BOM — Servidor

| Item | Custo estimado (R$) |
|---|---|
| Mini desktop (N100, 16GB, 256GB) | R$ 900–1.400 |
| Switch PoE gerenciável 8–16 portas | R$ 400–700 |
| UPS nobreak para servidor | R$ 300–500 |
| HDD 1TB adicional | R$ 200–350 |
| **Total** | **R$ 1.800–2.950** |
