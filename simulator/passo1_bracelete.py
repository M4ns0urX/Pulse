import time
import random

# ── configurações do bracelete ──────────────────────────────
BRACELET_ID = "BRC-001"
WORKER_NAME = "Carlos Souza"

# limiares NR-22
SPO2_CRITICO = 88.0
BPM_ALTO     = 130
BPM_BAIXO    = 42

# ── estado inicial ──────────────────────────────────────────
spo2    = 97.0   # % oxigenação
bpm     = 75.0   # batimentos por minuto
bateria = 85.0   # % bateria

# ── loop principal ──────────────────────────────────────────
print(f"Pulse iniciado — {BRACELET_ID} / {WORKER_NAME}")
print("-" * 50)

while True:
    # simula leitura dos sensores (drift gaussiano)
    spo2    += random.gauss(0, 0.3)
    bpm     += random.gauss(0, 1.5)
    bateria -= 0.05

    # mantém nos limites fisiológicos
    spo2    = max(80.0, min(100.0, spo2))
    bpm     = max(35.0, min(160.0, bpm))
    bateria = max(0.0,  min(100.0, bateria))

    # define prioridade
    if spo2 < SPO2_CRITICO or bpm > BPM_ALTO or bpm < BPM_BAIXO:
        prioridade = "CRÍTICO"
    elif spo2 < 92 or bpm > 110:
        prioridade = "URGENTE"
    elif spo2 < 95 or bpm > 95:
        prioridade = "ATENÇÃO"
    else:
        prioridade = "NORMAL"

    print(
        f"[{time.strftime('%H:%M:%S')}]  "
        f"SpO2: {spo2:5.1f}%  "
        f"BPM: {bpm:5.1f}  "
        f"Bat: {bateria:5.1f}%  "
        f"→  {prioridade}"
    )

    time.sleep(1)
