"""
Pulse — Servidor com IA de Comportamento
=========================================
Cada worker tem um ciclo de vida realista:

  ENTRANDO  → caminha da entrada até sua câmara de trabalho
  TRABALHANDO → fica na câmara por alguns minutos (BPM cai, SpO2 estável)
  PATRULHANDO → caminha pelos corredores da sua zona
  SOCORRENDO  → se um colega entra em CRÍTICO, vai até ele
  SAINDO      → ao fim do turno, caminha de volta à entrada

Sinais vitais inteligentes:
  - BPM sobe ao se mover rápido, cai ao parar
  - SpO2 cai levemente em zonas mais profundas (simula gases)
  - Fadiga acumula ao longo do turno — BPM basal sobe com o tempo
"""

import threading
import time
import random
import asyncio
import json
import websockets
from collections import deque
import math

# ══════════════════════════════════════════════════════════
#  WORKERS
# ══════════════════════════════════════════════════════════
WORKER_NAMES = [
    "Carlos Souza",   "Marcos Lima",    "João Ferreira",  "André Costa",
    "Paulo Mendes",   "Ricardo Alves",  "Diego Santos",   "Fábio Rocha",
    "Tiago Nunes",    "Lucas Barbosa",  "Roberto Cruz",   "Henrique Dias",
    "Sérgio Pinto",   "Fernando Luz",   "Gustavo Reis",   "Claudio Moura",
    "Eduardo Vaz",    "Leandro Fox",    "Márcio Belo",    "Renato Melo",
]
workers_def = [{"id": f"BRC-{i+1:03d}", "nome": WORKER_NAMES[i]} for i in range(20)]

# ══════════════════════════════════════════════════════════
#  MAPA DA MINA
#  Nós conectados por arestas — grafo para pathfinding
# ══════════════════════════════════════════════════════════
#
#  E=Entrada  A=Câmara A  X=Cruzamento  B=Câmara B
#  L=Lavra    C=Câmara C  N=Nó intermediário
#
#  Profundidade (0=raso, 1=fundo) afeta SpO2

NOS = {
    "ENTRADA":   {"x": 0.08, "y": 0.55, "profund": 0.0, "tipo": "camara"},
    "N01":       {"x": 0.14, "y": 0.55, "profund": 0.1, "tipo": "corredor"},
    "N02":       {"x": 0.20, "y": 0.55, "profund": 0.1, "tipo": "corredor"},
    "CAMARA_A":  {"x": 0.30, "y": 0.55, "profund": 0.2, "tipo": "camara"},
    "N03":       {"x": 0.30, "y": 0.45, "profund": 0.3, "tipo": "corredor"},
    "N04":       {"x": 0.30, "y": 0.35, "profund": 0.4, "tipo": "corredor"},
    "TOPO_N":    {"x": 0.30, "y": 0.22, "profund": 0.5, "tipo": "camara"},
    "N05":       {"x": 0.42, "y": 0.22, "profund": 0.5, "tipo": "corredor"},
    "N06":       {"x": 0.38, "y": 0.55, "profund": 0.3, "tipo": "corredor"},
    "N07":       {"x": 0.46, "y": 0.55, "profund": 0.3, "tipo": "corredor"},
    "CRUZAMENTO":{"x": 0.55, "y": 0.55, "profund": 0.4, "tipo": "camara"},
    "N08":       {"x": 0.55, "y": 0.45, "profund": 0.5, "tipo": "corredor"},
    "N09":       {"x": 0.55, "y": 0.35, "profund": 0.6, "tipo": "corredor"},
    "TOPO_B":    {"x": 0.55, "y": 0.22, "profund": 0.7, "tipo": "camara"},
    "N10":       {"x": 0.65, "y": 0.22, "profund": 0.7, "tipo": "corredor"},
    "N11":       {"x": 0.75, "y": 0.22, "profund": 0.8, "tipo": "corredor"},
    "CAMARA_B":  {"x": 0.88, "y": 0.22, "profund": 0.9, "tipo": "camara"},
    "N12":       {"x": 0.63, "y": 0.55, "profund": 0.5, "tipo": "corredor"},
    "N13":       {"x": 0.72, "y": 0.55, "profund": 0.6, "tipo": "corredor"},
    "N14":       {"x": 0.80, "y": 0.55, "profund": 0.7, "tipo": "corredor"},
    "LAVRA":     {"x": 0.88, "y": 0.55, "profund": 0.9, "tipo": "camara"},
    "N15":       {"x": 0.88, "y": 0.45, "profund": 0.9, "tipo": "corredor"},
    "N16":       {"x": 0.88, "y": 0.35, "profund": 0.9, "tipo": "corredor"},
    "N17":       {"x": 0.55, "y": 0.63, "profund": 0.5, "tipo": "corredor"},
    "N18":       {"x": 0.55, "y": 0.72, "profund": 0.6, "tipo": "corredor"},
    "N19":       {"x": 0.65, "y": 0.80, "profund": 0.7, "tipo": "corredor"},
    "N20":       {"x": 0.75, "y": 0.80, "profund": 0.8, "tipo": "corredor"},
    "CAMARA_C":  {"x": 0.88, "y": 0.80, "profund": 0.9, "tipo": "camara"},
    "N21":       {"x": 0.88, "y": 0.72, "profund": 0.9, "tipo": "corredor"},
    "N22":       {"x": 0.88, "y": 0.65, "profund": 0.9, "tipo": "corredor"},
    "FUNDO_S":   {"x": 0.55, "y": 0.80, "profund": 0.8, "tipo": "camara"},
}

# Arestas do grafo (conexões entre nós)
ARESTAS = [
    ("ENTRADA",  "N01"),    ("N01",    "N02"),
    ("N02",      "CAMARA_A"),
    ("CAMARA_A", "N03"),    ("N03",    "N04"),    ("N04",    "TOPO_N"),
    ("TOPO_N",   "N05"),    ("N05",    "TOPO_B"),
    ("CAMARA_A", "N06"),    ("N06",    "N07"),    ("N07",    "CRUZAMENTO"),
    ("CRUZAMENTO","N08"),   ("N08",    "N09"),    ("N09",    "TOPO_B"),
    ("TOPO_B",   "N10"),    ("N10",    "N11"),    ("N11",    "CAMARA_B"),
    ("CAMARA_B", "N16"),    ("N16",    "N15"),    ("N15",    "LAVRA"),
    ("CRUZAMENTO","N12"),   ("N12",    "N13"),    ("N13",    "N14"),
    ("N14",      "LAVRA"),
    ("LAVRA",    "N22"),    ("N22",    "N21"),    ("N21",    "CAMARA_C"),
    ("CRUZAMENTO","N17"),   ("N17",    "N18"),    ("N18",    "FUNDO_S"),
    ("FUNDO_S",  "N19"),    ("N19",    "N20"),    ("N20",    "CAMARA_C"),
]

# Monta adjacência
grafo = {n: [] for n in NOS}
for a, b in ARESTAS:
    grafo[a].append(b)
    grafo[b].append(a)

# Câmaras de trabalho disponíveis
CAMARAS = ["CAMARA_A", "CAMARA_B", "CAMARA_C", "LAVRA", "TOPO_N", "TOPO_B", "FUNDO_S", "CRUZAMENTO"]

# ══════════════════════════════════════════════════════════
#  PATHFINDING — BFS simples
# ══════════════════════════════════════════════════════════
def bfs(origem, destino):
    """Retorna lista de nós do caminho mais curto entre origem e destino."""
    if origem == destino:
        return [origem]
    fila   = deque([[origem]])
    vistos = {origem}
    while fila:
        caminho = fila.popleft()
        atual   = caminho[-1]
        for vizinho in grafo.get(atual, []):
            if vizinho not in vistos:
                novo = caminho + [vizinho]
                if vizinho == destino:
                    return novo
                vistos.add(vizinho)
                fila.append(novo)
    return [origem]   # fallback: fica no lugar

# ══════════════════════════════════════════════════════════
#  TOTENS
# ══════════════════════════════════════════════════════════
TOTENS = {
    "T-01": {"x": 0.08, "y": 0.55, "raio": 0.10},
    "T-02": {"x": 0.20, "y": 0.55, "raio": 0.10},
    "T-03": {"x": 0.30, "y": 0.55, "raio": 0.10},
    "T-04": {"x": 0.30, "y": 0.38, "raio": 0.10},
    "T-05": {"x": 0.30, "y": 0.22, "raio": 0.10},
    "T-06": {"x": 0.55, "y": 0.55, "raio": 0.10},
    "T-07": {"x": 0.55, "y": 0.38, "raio": 0.10},
    "T-08": {"x": 0.55, "y": 0.22, "raio": 0.10},
    "T-09": {"x": 0.72, "y": 0.55, "raio": 0.10},
    "T-10": {"x": 0.88, "y": 0.22, "raio": 0.10},
    "T-11": {"x": 0.88, "y": 0.55, "raio": 0.10},
    "T-12": {"x": 0.88, "y": 0.80, "raio": 0.10},
    "T-13": {"x": 0.55, "y": 0.68, "raio": 0.10},
    "T-14": {"x": 0.55, "y": 0.80, "raio": 0.10},
}

# ══════════════════════════════════════════════════════════
#  LIMIARES NR-22
# ══════════════════════════════════════════════════════════
SPO2_CRIT=88.0; SPO2_URG=91.0; SPO2_WARN=94.0
BPM_HI_C=132;   BPM_LO_C=42;   BPM_HI_U=115;  BPM_HI_W=98
BAT_CRIT=8;      BAT_WARN=18

# ══════════════════════════════════════════════════════════
#  ESTADO GLOBAL
# ══════════════════════════════════════════════════════════
estado  = {}
alertas = deque(maxlen=50)
lock    = threading.Lock()
turno_ev = {"quedas":0, "panicos":0, "sem_sinal":0, "inicio":time.time()}

def calc_prio(spo2, bpm, bat, queda, panico):
    if queda or panico or spo2<SPO2_CRIT or bpm>BPM_HI_C or bpm<BPM_LO_C: return "CRÍTICO"
    if spo2<SPO2_URG  or bpm>BPM_HI_U  or bat<BAT_CRIT: return "URGENTE"
    if spo2<SPO2_WARN or bpm>BPM_HI_W  or bat<BAT_WARN: return "ATENÇÃO"
    return "NORMAL"

def totem_cobre(x, y):
    for tid, t in TOTENS.items():
        if math.hypot(x-t["x"], y-t["y"]) <= t["raio"]:
            return tid
    return None

def push_alerta(wid, nome, prio, msg):
    alertas.appendleft({"ts":time.strftime("%H:%M:%S"),"wid":wid,"nome":nome,"prioridade":prio,"mensagem":msg})

def dist_nos(a, b):
    na, nb = NOS[a], NOS[b]
    return math.hypot(na["x"]-nb["x"], na["y"]-nb["y"])

# ══════════════════════════════════════════════════════════
#  THREAD DE SIMULAÇÃO COM IA
# ══════════════════════════════════════════════════════════
def simular(worker):
    wid  = worker["id"]
    nome = worker["nome"]

    # ── estado fisiológico base ──────────────────────────
    spo2_base = 97.0 + random.uniform(-1, 1)
    bpm_base  = 68.0 + random.uniform(-5, 10)
    spo2      = spo2_base
    bpm       = bpm_base
    bat       = 80.0 + random.uniform(0, 20)

    # ── estado de comportamento ──────────────────────────
    # Estados: "entrando", "indo", "trabalhando", "patrulhando", "socorrendo", "saindo"
    estado_behav  = "entrando"
    no_atual      = "ENTRADA"
    destino_no    = random.choice(CAMARAS)
    rota          = bfs("ENTRADA", destino_no)
    rota_idx      = 0                          # índice do próximo nó na rota
    prog          = 0.0                        # progresso entre nó atual e próximo (0–1)
    vel_base      = random.uniform(0.025, 0.045)
    vel           = vel_base

    # posição real interpolada
    pos_x = NOS["ENTRADA"]["x"]
    pos_y = NOS["ENTRADA"]["y"]

    # trabalho
    trabalho_dur   = 0      # quanto tempo já trabalhou (ticks)
    trabalho_alvo  = random.randint(60, 180)   # ticks para trabalhar

    # fadiga acumulada
    fadiga         = 0.0    # 0–1, sobe com o tempo de turno

    # emergência
    socorro_alvo   = None

    # status
    queda          = False
    panico         = False
    prev_p         = "NORMAL"
    prev_totem     = None
    status_since   = time.time()
    ultimo_totem   = None
    ultimo_totem_ts= None

    # atraso de entrada escalonado
    time.sleep(random.uniform(0, 8))

    while True:
        tick_start = time.time()

        # ── fadiga (sobe 0.001 por tick ≈ 1% a cada 100s) ──
        fadiga = min(1.0, fadiga + 0.0008)

        # ── verificar se há colega em CRÍTICO próximo ──────
        colega_critico = None
        with lock:
            for wid2, s2 in estado.items():
                if wid2 != wid and s2.get("prioridade") == "CRÍTICO":
                    d = math.hypot(pos_x - s2["x"], pos_y - s2["y"])
                    if d < 0.30:   # dentro de 30% do mapa
                        colega_critico = s2
                        break

        if colega_critico and estado_behav not in ("socorrendo", "saindo") and not queda and not panico:
            # encontra o nó mais próximo do colega em CRÍTICO
            nx, ny = colega_critico["x"], colega_critico["y"]
            no_mais_proximo = min(NOS, key=lambda n: math.hypot(NOS[n]["x"]-nx, NOS[n]["y"]-ny))
            if no_mais_proximo != no_atual:
                estado_behav = "socorrendo"
                socorro_alvo = no_mais_proximo
                rota = bfs(no_atual, socorro_alvo)
                rota_idx = 0
                prog = 0.0

        # ── máquina de estados de comportamento ────────────
        if estado_behav == "entrando":
            # chega até a câmara destino
            if rota_idx >= len(rota) - 1:
                estado_behav  = "trabalhando"
                trabalho_dur  = 0
                trabalho_alvo = random.randint(60, 180)
            else:
                _avancar()

        elif estado_behav == "trabalhando":
            trabalho_dur += 1
            vel = 0   # parado
            if trabalho_dur >= trabalho_alvo:
                # escolhe próxima ação: patrulhar ou ir para outra câmara
                if random.random() < 0.4:
                    estado_behav = "patrulhando"
                    destino_no   = random.choice(CAMARAS)
                    rota         = bfs(no_atual, destino_no)
                    rota_idx     = 0
                else:
                    estado_behav = "patrulhando"
                    destino_no   = no_atual   # fica na mesma zona patrulhando
                    rota         = [no_atual]
                    rota_idx     = 0

        elif estado_behav == "patrulhando":
            vel = vel_base * (0.8 + random.uniform(0, 0.4))
            if rota_idx >= len(rota) - 1:
                # chegou — decide: trabalhar, ir para outro lugar ou sair
                r = random.random()
                if fadiga > 0.8 or bat < 20:
                    # cansado ou bateria baixa → volta para entrada
                    estado_behav = "saindo"
                    rota = bfs(no_atual, "ENTRADA")
                    rota_idx = 0
                elif r < 0.5:
                    estado_behav  = "trabalhando"
                    trabalho_dur  = 0
                    trabalho_alvo = random.randint(40, 120)
                else:
                    destino_no = random.choice(CAMARAS)
                    rota = bfs(no_atual, destino_no)
                    rota_idx = 0
            else:
                _avancar()

        elif estado_behav == "socorrendo":
            vel = vel_base * 1.4   # corre para ajudar
            if rota_idx >= len(rota) - 1:
                estado_behav = "patrulhando"
                destino_no   = no_atual
                rota         = [no_atual]
                rota_idx     = 0
            else:
                _avancar()

        elif estado_behav == "saindo":
            vel = vel_base
            if rota_idx >= len(rota) - 1:
                # saiu da mina — resetar para novo turno após pausa
                time.sleep(random.uniform(10, 30))
                no_atual      = "ENTRADA"
                pos_x         = NOS["ENTRADA"]["x"]
                pos_y         = NOS["ENTRADA"]["y"]
                destino_no    = random.choice(CAMARAS)
                rota          = bfs("ENTRADA", destino_no)
                rota_idx      = 0
                prog          = 0.0
                estado_behav  = "entrando"
                fadiga        = 0.0   # descansou
                bpm_base      = 68.0 + random.uniform(-5, 10)
                continue
            else:
                _avancar()

        def _avancar():
            nonlocal prog, rota_idx, no_atual, pos_x, pos_y
            prog += vel
            if prog >= 1.0:
                prog = 0.0
                no_atual  = rota[rota_idx + 1]
                rota_idx += 1
            if rota_idx < len(rota) - 1:
                na = NOS[rota[rota_idx]]
                nb = NOS[rota[rota_idx + 1]]
                pos_x = na["x"] + (nb["x"] - na["x"]) * prog
                pos_y = na["y"] + (nb["y"] - na["y"]) * prog

        # ── sinais vitais inteligentes ──────────────────────
        # profundidade do nó atual afeta SpO2
        prof_atual = NOS[no_atual]["profund"]

        # BPM: sobe ao se mover, cai ao parar
        bpm_target = bpm_base + fadiga * 15   # fadiga eleva BPM basal
        if vel > 0:
            bpm_target += vel * 200 + random.gauss(0, 3)   # esforço físico
        else:
            bpm_target -= 5   # repouso
        bpm += (bpm_target - bpm) * 0.1 + random.gauss(0, 0.8)

        # SpO2: cai em profundidade
        spo2_target = spo2_base - prof_atual * 4   # até -4% nas zonas mais fundas
        spo2 += (spo2_target - spo2) * 0.05 + random.gauss(0, 0.15)

        # Bateria: drena
        bat -= 0.006 + vel * 0.01   # gasta mais ao se mover

        # Clamp
        spo2 = max(80.0, min(100.0, spo2))
        bpm  = max(35.0, min(160.0, bpm))
        bat  = max(0.0,  min(100.0, bat))

        # ── queda aleatória ─────────────────────────────────
        if not queda and random.random() < 0.00025:
            queda = True
            vel = 0
            turno_ev["quedas"] += 1
            push_alerta(wid, nome, "CRÍTICO", "⚠ queda detectada — acelerômetro 4.2g")
            def _rec(w=wid):
                time.sleep(random.uniform(12, 22))
                with lock:
                    if w in estado: estado[w]["queda"] = False
            threading.Thread(target=_rec, daemon=True).start()

        # ── bateria crítica ──────────────────────────────────
        if bat < BAT_CRIT and prev_p != "CRÍTICO":
            push_alerta(wid, nome, "CRÍTICO", f"🔋 bateria crítica {bat:.0f}%")

        # ── worker para se não estiver NORMAL ───────────────
        p = calc_prio(spo2, bpm, bat, queda, panico)
        if p != "NORMAL":
            vel = 0

        # ── totem e visibilidade ─────────────────────────────
        tid = totem_cobre(pos_x, pos_y)
        if tid:
            ultimo_totem    = tid
            ultimo_totem_ts = time.strftime("%H:%M:%S")
        if prev_totem and not tid:
            turno_ev["sem_sinal"] += 1
            push_alerta(wid, nome, "ATENÇÃO", f"📡 saiu da cobertura — último: {prev_totem}")
        prev_totem = tid

        # ── prioridade e alerta ──────────────────────────────
        if p != prev_p:
            status_since = time.time()
            if p != "NORMAL":
                push_alerta(wid, nome, p, {
                    "CRÍTICO": f"spo₂ {spo2:.0f}% · bpm {bpm:.0f}",
                    "URGENTE": f"spo₂ baixo {spo2:.0f}%",
                    "ATENÇÃO": "sinais fora da faixa",
                }[p])
        prev_p = p

        # ── estado compartilhado ─────────────────────────────
        with lock:
            estado[wid] = {
                "id": wid, "nome": nome,
                "spo2": round(spo2, 1), "bpm": round(bpm, 1), "bat": round(bat, 1),
                "x": round(pos_x, 3), "y": round(pos_y, 3),
                "prioridade":      p,
                "totem":           tid,
                "visivel":         tid is not None,
                "queda":           queda,
                "panico":          panico,
                "imobil":          vel == 0 and p != "NORMAL",
                "status_dur":      int(time.time() - status_since),
                "ultimo_totem":    ultimo_totem,
                "ultimo_totem_ts": ultimo_totem_ts,
                "comportamento":   estado_behav,   # extra: visível no modal
                "fadiga":          round(fadiga, 2),
                "no_atual":        no_atual,
            }

        # ── tick de 1 segundo ────────────────────────────────
        elapsed = time.time() - tick_start
        time.sleep(max(0, 1.0 - elapsed))

# ══════════════════════════════════════════════════════════
#  WEBSOCKET
# ══════════════════════════════════════════════════════════
clientes = set()

async def handler(ws):
    clientes.add(ws)
    print(f"  [WS] conectado — {len(clientes)} cliente(s)")
    try:
        async def ouvir():
            async for msg in ws:
                try:
                    cmd = json.loads(msg)
                    wid = cmd.get("wid")
                    with lock:
                        if wid not in estado: return
                        if cmd["tipo"] == "panico":
                            estado[wid]["panico"] = True
                            turno_ev["panicos"] += 1
                            push_alerta(wid, estado[wid]["nome"], "CRÍTICO", "🚨 pânico acionado")
                            async def _cp(w=wid):
                                await asyncio.sleep(20)
                                with lock:
                                    if w in estado: estado[w]["panico"] = False
                            asyncio.create_task(_cp())
                        elif cmd["tipo"] == "queda":
                            estado[wid]["queda"] = True
                            turno_ev["quedas"] += 1
                            push_alerta(wid, estado[wid]["nome"], "CRÍTICO", "⚠ queda forçada")
                            async def _cq(w=wid):
                                await asyncio.sleep(15)
                                with lock:
                                    if w in estado: estado[w]["queda"] = False
                            asyncio.create_task(_cq())
                except Exception:
                    pass
        asyncio.create_task(ouvir())

        while True:
            with lock:
                totem_info = {}
                for tid, t in TOTENS.items():
                    cobre = [w for w in estado.values() if w.get("totem") == tid]
                    totem_info[tid] = {
                        **t,
                        "workers_count": len(cobre),
                        "tem_critico":   any(w["prioridade"] == "CRÍTICO" for w in cobre),
                        "tem_urgente":   any(w["prioridade"] == "URGENTE" for w in cobre),
                    }
                dur = int(time.time() - turno_ev["inicio"])
                payload = {
                    "workers": list(estado.values()),
                    "alertas": list(alertas),
                    "totens":  totem_info,
                    "turno": {
                        "duracao":   f"{dur//3600:02d}:{(dur%3600)//60:02d}",
                        "quedas":    turno_ev["quedas"],
                        "panicos":   turno_ev["panicos"],
                        "sem_sinal": turno_ev["sem_sinal"],
                    }
                }
            await ws.send(json.dumps(payload))
            await asyncio.sleep(1)

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        clientes.discard(ws)

async def main_ws():
    print("  [WS] ws://localhost:8765")
    async with websockets.serve(handler, "localhost", 8765):
        await asyncio.Future()

def run_ws():
    asyncio.run(main_ws())

# ══════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════
print("Pulse — IA de Comportamento — 20 workers")
print("-" * 52)
for w in workers_def:
    threading.Thread(target=simular, args=(w,), daemon=True).start()
    print(f"  → {w['id']} {w['nome']}")
threading.Thread(target=run_ws, daemon=True).start()
print("-" * 52)
print("http://localhost:8080/passo5_dashboard.html")
print("Ctrl+C para encerrar\n")
while True:
    time.sleep(1)
