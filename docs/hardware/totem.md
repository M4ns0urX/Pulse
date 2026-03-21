# Hardware — Totem

## Componentes

| Componente | Modelo | Função |
|---|---|---|
| Computador | Raspberry Pi 3B+ | processamento local, fila de prioridade, gateway |
| Módulo UWB anchor | DW3000 (via HAT ou SPI) | anchor fixo para trilateração |
| Receptor BLE | integrado ao Raspi ou dongle USB BLE 5.0 | recebe telemetria dos braceletes |
| Alimentação | PoE 802.3af (15W) | energia via cabo de rede — sem fiação separada |
| Nobreak | LiFePO4 12V 7Ah | autonomia de 2–4h em queda de energia |
| Controlador nobreak | chaveamento automático | troca rede ↔ bateria sem interrupção |
| Display | OLED 0.96" I2C (opcional) | status local: IDs detectados, alertas |
| Caixa | IP67 aço inox ou ABS reforçado | proteção mecânica, umidade, impacto |

---

## Posicionamento

**Regras para instalação:**

- Um totem a cada **15–20m** em corredores lineares
- Nas bifurcações, um totem em cada ramal após a divisão
- Mínimo de **3 anchors com visada direta** para trilateração 2D
- Mínimo de **4 anchors em alturas diferentes** para trilateração 3D
- Altura de instalação: **1.8–2.2m** da parede ou teto

**Cobertura UWB em ambiente de mina:**

| Material da parede | Alcance estimado |
|---|---|
| Rocha seca | 15–25m |
| Rocha úmida | 10–18m |
| Concreto | 12–20m |
| Curva de corredor | reduz 30–50% — instalar anchor adicional |

---

## Power over Ethernet (PoE)

Recomendação: alimentar todos os totens via PoE 802.3af a partir de um switch central.

**Vantagens:**
- Um cabo Cat6 carrega energia (até 15W) + dados simultaneamente
- Elimina tomadas e cabos elétricos separados em cada totem
- Switch PoE gerenciável permite reiniciar totens remotamente via software
- Monitoramento de consumo por porta no switch

**Switch recomendado:** TP-Link TL-SG1218MPE ou Ubiquiti UniFi Switch 16 PoE

---

## Daemon de Prioridade (Python)

O Raspi 3 roda um daemon Python com fila de prioridade (min-heap) para garantir que emergências cheguem ao servidor antes de pacotes normais:

```python
import heapq

# priority_key negativo: -3 (crítico) sobe antes de -1 (atenção)
packet = PriorityPacket(
    priority_key = -(worker_priority),
    timestamp    = time.time(),      # desempate FIFO
    payload      = data,
)
heapq.heappush(queue, packet)
```

Comportamento por nível:

| Prioridade | Comportamento no totem |
|---|---|
| CRÍTICO (3) | flush imediato — sem sleep entre envios |
| URGENTE (2) | throttle de 20ms |
| ATENÇÃO (1) | throttle de 50ms |
| NORMAL (0) | throttle de 100ms |

Buffer local: mantém até 500 pacotes em memória caso o Ethernet caia momentaneamente. Pacotes críticos nunca são descartados.

---

## BOM — Custo Estimado por Totem

| Item | Custo estimado (R$) |
|---|---|
| Raspberry Pi 3B+ | R$ 350–450 |
| DW3000 módulo UWB | R$ 80–120 |
| LiFePO4 12V 7Ah + controlador | R$ 120–200 |
| Caixa IP67 industrial | R$ 80–150 |
| Cabo Cat6 por ponto (20m) | R$ 40–80 |
| Fixação e acessórios | R$ 20–40 |
| **Total** | **R$ 690–1.040** |
