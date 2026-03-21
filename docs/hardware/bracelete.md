# Hardware — Bracelete

## Componentes

| Componente | Modelo | Função | Interface |
|---|---|---|---|
| Microcontrolador | ESP32-S3 Mini | processamento, BLE nativo, Wi-Fi | — |
| Módulo UWB | DW3000 (Qorvo) | ranging preciso para localização XYZ | SPI |
| SpO₂ / BPM | MAX30102 | oxigenação e frequência cardíaca | I2C |
| IMU | LSM6DSO | acelerômetro + giroscópio, detecção de queda | SPI ou I2C |
| Bateria | LiPo 800mAh 3.7V | alimentação | — |
| Gerenciador de carga | TP4056 | carga segura da bateria LiPo | — |
| Regulador | AP2112K 3.3V | tensão estável para todos os módulos | — |
| Motor de vibração | Coin ERM 10mm | alerta háptico ao trabalhador | GPIO |
| Botão de pânico | Push button | acionamento manual de emergência | GPIO IRQ |
| Caixa | IP65 ABS | proteção mecânica e contra umidade | — |

---

## Pinagem — ESP32-S3 Mini

```
DW3000 UWB (SPI)
├── SCK   →  GPIO 18
├── MOSI  →  GPIO 23
├── MISO  →  GPIO 19
├── CS    →  GPIO 5
└── IRQ   →  GPIO 4  (interrupção de hardware)

MAX30102 SpO₂ (I2C)
├── SDA   →  GPIO 21
└── SCL   →  GPIO 22

LSM6DSO IMU (I2C — mesmo barramento)
├── SDA   →  GPIO 21
└── SCL   →  GPIO 22

Motor de Vibração
└── CTRL  →  GPIO 27  (via transistor NPN 2N2222 + diodo flyback)

Botão de Pânico
└── BTN   →  GPIO 0  (pull-up interno, interrupção FALLING)

Bateria / Carga
├── VBAT  →  GPIO 35  (divisor resistivo para leitura de tensão)
└── CHG   →  TP4056 externo
```

---

## Estimativa de Consumo

| Componente | Corrente média | Modo |
|---|---|---|
| ESP32-S3 (ativo + BLE TX) | ~80 mA | publicando a cada 1s |
| DW3000 UWB ranging | ~60 mA | burst de 1ms a cada 1s |
| MAX30102 SpO₂ | ~1 mA | contínuo |
| LSM6DSO IMU | ~0.6 mA | contínuo |
| Motor de vibração | ~80 mA | acionamento pontual |
| **Total operação normal** | **~85–100 mA** | sem vibração |

Com bateria de 800mAh → **autonomia estimada de 8–9h** em operação normal.

Para turno de 12h, usar bateria de 1200mAh ou reduzir frequência de ranging UWB para 0.5 Hz.

---

## Lógica de Firmware

Estrutura de tarefas FreeRTOS:

```c
// Prioridades (maior número = maior prioridade no FreeRTOS)
xTaskCreate(taskAlertEngine,   "ALERT", 2048, NULL, 5, NULL);  // máxima
xTaskCreate(taskUWBRanging,    "UWB",   4096, NULL, 3, NULL);  // alta
xTaskCreate(taskSensors,       "SENS",  4096, NULL, 2, NULL);  // média
xTaskCreate(taskBLETelemetry,  "BLE",   4096, NULL, 2, NULL);  // média
xTaskCreate(taskBatteryMonitor,"BAT",   1024, NULL, 1, NULL);  // baixa
```

Payload BLE publicado a cada 1s:

```json
{
  "id":    "BRC-001",
  "spo2":  97.2,
  "bpm":   78,
  "accel": 1.02,
  "bat":   84,
  "fall":  false,
  "panic": false,
  "p":     0
}
```

---

## BOM — Custo Estimado por Bracelete

| Item | Custo estimado (R$) |
|---|---|
| ESP32-S3 Mini | R$ 35–50 |
| DW3000 módulo UWB | R$ 80–120 |
| MAX30102 | R$ 15–25 |
| LSM6DSO IMU | R$ 18–30 |
| LiPo 800mAh | R$ 25–40 |
| TP4056 + componentes | R$ 8–15 |
| Motor de vibração | R$ 5–10 |
| PCB customizada | R$ 30–60 |
| Caixa IP65 | R$ 20–40 |
| **Total** | **R$ 236–390** |
