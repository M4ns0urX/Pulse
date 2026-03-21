# Arquitetura Técnica

## Visão Geral

O Pulse opera em três camadas físicas independentes que se comunicam de forma hierárquica. Cada camada tem responsabilidades claras e pode operar de forma degradada se uma camada superior falhar.

```
Bracelete  →  (UWB + BLE)  →  Totem  →  (Ethernet)  →  Servidor
```

A separação de responsabilidades é intencional: o bracelete não depende do servidor para funcionar — ele alerta o trabalhador localmente via vibração. O totem não depende do servidor para priorizar — ele mantém fila local. O servidor é camada de visibilidade e histórico, não de operação crítica.

---

## Camada 1 — Bracelete

**Hardware:** ESP32-S3 Mini + DW3000 + MAX30102 + LSM6DSO + LiPo 800mAh

**Responsabilidades:**
- Leitura contínua de SpO₂, BPM e acelerômetro
- Ranging UWB com os anchors dos totens (1x por segundo)
- Publicação de telemetria via BLE para o totem mais próximo
- Alertas hápticos locais (motor de vibração) independentes da rede
- Botão de pânico com interrupção de hardware

**Protocolo dual:**

| Rádio | Função | Frequência | Consumo |
|---|---|---|---|
| UWB (DW3000) | Ranging para trilateração XYZ | 1 Hz | ~60mA burst |
| BLE 5.0 (ESP32) | Telemetria de sensores | 1 Hz contínuo | ~10mA |

O UWB é usado exclusivamente para medir distância (time-of-flight). O BLE carrega os dados de sensor. Essa separação preserva a bateria e evita saturação do canal UWB.

**Autonomia estimada:** 6–10h com 800mAh. Para turnos de 12h, usar 1200mAh ou reduzir ranging UWB para 0.5 Hz.

---

## Camada 2 — Totem

**Hardware:** Raspberry Pi 3B+ + DW3000 (anchor) + receptor BLE + PoE 802.3af + nobreak LiFePO4

**Responsabilidades:**
- Funcionar como âncora UWB fixa (posição conhecida e calibrada)
- Receber telemetria BLE dos braceletes em sua zona de cobertura
- Calcular posição XYZ dos braceletes por trilateração (mínimos 3 anchors)
- Manter fila de prioridade local — pacotes críticos sobem à frente
- Encaminhar dados ao servidor via Ethernet
- Publicar heartbeat de status a cada 5 segundos

**Fila de prioridade (min-heap):**

```python
# Pacotes críticos (p=3) chegam antes de urgentes (p=2)
# dentro do mesmo nível, FIFO por timestamp
priority_key = -(priority_level)   # negativo → crítico no topo
```

**Cobertura UWB:** raio de ~15–20m por totem em corredor de rocha. Instalar a cada 15m para garantir visada direta de pelo menos 3 anchors por posição.

**Alimentação:** PoE 802.3af (15W) via cabo Cat6. Um único cabo carrega energia e dados. Nobreak local garante operação em queda de energia por 2–4h dependendo da capacidade.

---

## Camada 3 — Servidor Local

**Hardware:** Mini desktop (Intel N100, 16GB RAM, 256GB NVMe)

**Virtualização:** Proxmox VE com containers LXC e VMs:

| Serviço | Tipo | Função | RAM |
|---|---|---|---|
| Mosquitto | LXC | broker MQTT — recebe todos os pacotes | 256MB |
| InfluxDB 2 | LXC | banco de série temporal — armazena telemetria | 2GB |
| Processor | LXC | consome MQTT, valida, grava InfluxDB | 512MB |
| FastAPI | LXC | REST + WebSocket para o dashboard | 512MB |
| Grafana | LXC | dashboard visual em tempo real | 512MB |
| WireGuard | VM | VPN para acesso externo e SaaS | 256MB |

---

## Fluxo de Dados Completo

```
1. Bracelete lê sensor (SpO₂, BPM, accel) — a cada 1s
2. Bracelete faz ranging UWB com anchors visíveis — a cada 1s
3. Bracelete publica BLE:
     pulse/{totem_id}/{bracelet_id}/telemetry
     pulse/{totem_id}/{bracelet_id}/position
4. Totem recebe, calcula trilateração, adiciona na fila de prioridade
5. Totem encaminha via MQTT over Ethernet ao broker (Mosquitto)
6. Processor consome do broker, valida limiares, grava InfluxDB
7. Se alerta → publica em pulse/system/alert (QoS 2)
8. Grafana e FastAPI leem InfluxDB e servem o dashboard
9. Dashboard exibe posição + vitais em tempo real
```

---

## Trilateração UWB

A posição XYZ de cada bracelete é calculada a partir das distâncias medidas por múltiplos anchors. Com 3 anchors no mesmo plano horizontal → posição 2D. Com 4+ anchors em alturas diferentes → posição 3D.

```
d1 = distância bracelete → anchor 1  (medida pelo DW3000 via ToF)
d2 = distância bracelete → anchor 2
d3 = distância bracelete → anchor 3

# Sistema de equações:
(x - x1)² + (y - y1)² + (z - z1)² = d1²
(x - x2)² + (y - y2)² + (z - z2)² = d2²
(x - x3)² + (y - y3)² + (z - z3)² = d3²

# Resolvido por mínimos quadrados (scipy.optimize ou Gauss-Newton)
```

Um filtro de Kalman é aplicado sobre as posições calculadas para suavizar ruído de medição e produzir trajetória contínua.
