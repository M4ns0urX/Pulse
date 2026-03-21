# Protocolo MQTT

## Tópicos

```
pulse/
├── {totem_id}/{bracelet_id}/telemetry    QoS 1  dados de sensor (1x/s)
├── {totem_id}/{bracelet_id}/position     QoS 1  posição XYZ (1x/s)
├── {totem_id}/{bracelet_id}/alert        QoS 2  alerta (entrega garantida)
├── totem/{totem_id}/heartbeat            QoS 0  status do totem (5x/s)
└── system/emergency                      QoS 2  broadcast de emergência
```

Exemplos reais:
```
pulse/TTM-04/BRC-007/telemetry
pulse/TTM-04/BRC-007/position
pulse/TTM-04/BRC-007/alert
pulse/totem/TTM-04/heartbeat
pulse/system/emergency
```

---

## Payloads

### telemetry
```json
{
  "bracelet_id": "BRC-007",
  "worker_name": "Diego Santos",
  "timestamp": 1720000000.123,
  "sensors": {
    "spo2":        97.4,
    "bpm":         78,
    "battery":     72.1,
    "accel_g":     1.02,
    "temperature": 36.5
  },
  "status": {
    "priority":          0,
    "priority_label":    "NORMAL",
    "fall_detected":     false,
    "panic":             false,
    "immobile_seconds":  0
  },
  "totem": {
    "id":    "TTM-04",
    "zone":  "Central",
    "pos_x": 0.47,
    "pos_y": 0.50
  }
}
```

### position
```json
{
  "bracelet_id": "BRC-007",
  "timestamp": 1720000000.123,
  "position": {
    "x":        12.4,
    "y":         8.1,
    "z":        -3.2,
    "anchor":   "TTM-04",
    "zone":     "Central",
    "precision": "uwb"
  }
}
```

### alert
```json
{
  "bracelet_id":    "BRC-007",
  "worker_name":    "Diego Santos",
  "timestamp":      1720000000.123,
  "priority":       3,
  "priority_label": "CRÍTICO",
  "message":        "SpO₂ crítico 86% · BPM 134",
  "zone":           "Central",
  "nearest_totem":  "TTM-04",
  "sensors": {
    "spo2":    86.2,
    "bpm":     134,
    "battery": 45.0
  }
}
```

### heartbeat (totem)
```json
{
  "totem_id":          "TTM-04",
  "zone":              "Central",
  "timestamp":         1720000000.0,
  "online":            true,
  "workers_in_zone":   ["BRC-005", "BRC-007", "BRC-012"],
  "queue_size":        0,
  "packets_received":  1247,
  "packets_forwarded": 1245,
  "packets_dropped":   0,
  "uptime_seconds":    3600
}
```

---

## QoS por Tipo de Mensagem

| Tópico | QoS | Motivo |
|---|---|---|
| telemetry | 1 | entrega garantida, sem duplicatas críticas |
| position | 1 | entrega garantida |
| alert | 2 | exatamente uma entrega — emergência não pode duplicar ou sumir |
| heartbeat | 0 | fire-and-forget, perda aceitável |
| emergency | 2 | exatamente uma entrega |

---

## Retenção de Mensagens

Alertas críticos são publicados com `retain=True` para que novos subscribers (ex: dashboard reconectando) recebam o último estado ao se inscrever, sem esperar o próximo ciclo.

```python
client.publish(
    topic   = "pulse/TTM-04/BRC-007/alert",
    payload = json.dumps(payload),
    qos     = 2,
    retain  = True,   # último estado disponível ao reconectar
)
```
