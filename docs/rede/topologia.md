# Rede — Topologia e Resiliência

## O Problema do Cabo Único

Em topologia linear (daisy chain), a ruptura de um único segmento de cabo isola todos os totens além daquele ponto:

```
Servidor ── T01 ── T02 ──💥── T03 ── T04
                          ❌ invisível  ❌ invisível
```

Em ambiente de mina isso é inaceitável para um sistema de segurança. Quedas de rocha, maquinário e umidade podem romper cabos.

---

## Topologia Recomendada: Anel com RSTP

Os totens formam um anel fechado. O switch gerenciável usa RSTP (Rapid Spanning Tree Protocol) para detectar a ruptura e rerotear automaticamente pelo caminho inverso em menos de 1 segundo.

```
Servidor ── Switch ── T01 ── T02 ── T03 ── T04
                 └─────────────────────────────┘
                          (cabo de retorno)
```

Se o cabo entre T02 e T03 romper:

```
Servidor ── Switch ◄── T04 ◄── T03 ◄── [ruptura] ... T02 ── T01
```

O tráfego flui pelo sentido inverso automaticamente.

**Requisito:** switch gerenciável com suporte a RSTP/MSTP. Exemplos: Ubiquiti UniFi, TP-Link T-series, Cisco SG series.

---

## Power over Ethernet (PoE)

Um cabo Cat6 por totem carrega energia e dados:

```
Switch PoE ──[ Cat6 ]──► Totem
             energia
             + dados
```

**Padrão:** 802.3af (15W por porta) — suficiente para Raspi 3 + DW3000 + display OLED.

**Benefícios:**
- Elimina tomadas elétricas em cada totem
- Gerenciamento remoto (restart por software via switch)
- Monitoramento de consumo por porta
- Reduz pontos de falha elétrica

---

## LoRa — Fallback de Emergência

Um módulo LoRa barato (SX1276, ~R$30) em cada totem fica em standby. Se o keepalive Ethernet cair por mais de 10 segundos, o LoRa acorda e transmite apenas alertas críticos.

```
Operação normal → Ethernet (dados completos, baixa latência)
Ethernet cai    → LoRa ativa (só alertas críticos, latência 1–5s)
Ethernet volta  → LoRa entra em standby novamente
```

O LoRa não transmite posição UWB (sem precisão de ranging). Sua função é garantir que um **alerta crítico chegue ao servidor mesmo com cabo rompido**.

**Frequência:** 915 MHz (faixa ISM, livre de licença no Brasil — Anatel).

---

## Tabela de Decisão por Cenário

| Cenário de mina | Topologia recomendada |
|---|---|
| Pequena, poucas galerias curtas | Estrela — cabo direto de cada totem ao switch |
| Galeria longa e linear | Anel RSTP + LoRa fallback |
| Múltiplos ramais | Estrela por zona + anel dentro de cada galeria longa |
| Qualquer cenário | LoRa fallback em todos os totens (baixo custo, alta resiliência) |

---

## Cabeamento

- **Tipo:** Cat6 (melhor imunidade a ruído eletromagnético em ambiente industrial)
- **Conduíte:** duto IP67 em trechos expostos a umidade ou impacto
- **Distância máxima:** 100m por segmento Ethernet (padrão 802.3)
- **Além de 100m:** usar switch intermediário ou fibra óptica monomodo

## Endereçamento IP

```
Rede local da mina: 192.168.10.0/24

Servidor:      192.168.10.1
Switch:        192.168.10.2
T01:           192.168.10.10
T02:           192.168.10.11
...
T08:           192.168.10.17
```

IP fixo em todos os totens — sem DHCP para evitar mudança de endereço após reinício.
