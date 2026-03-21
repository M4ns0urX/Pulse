# Roadmap

## Fase 1 — Simulação MVP ← estamos aqui
**Objetivo:** validar arquitetura e lógica de negócio sem hardware físico.

- [x] Arquitetura técnica documentada
- [x] Dashboard web interativo com 20 braceletes simulados
- [x] Simulador Python — bracelete com sensores e prioridade
- [ ] Simulador Python — totem com fila de prioridade
- [ ] Simulador Python — pipeline completo bracelete → totem → servidor
- [ ] Stack Docker Compose (Mosquitto + InfluxDB + Grafana) rodando localmente

---

## Fase 2 — Prova de Conceito Hardware
**Objetivo:** validar comunicação UWB em ambiente real.

- [ ] Montar bracelete em protoboard (ESP32 + DW3000)
- [ ] Configurar 3 módulos DW3000 como anchors fixos
- [ ] Validar ranging UWB em corredor de teste (30–50m)
- [ ] Integrar MAX30102 e validar leitura de SpO₂ e BPM
- [ ] Validar comunicação BLE bracelete → Raspi 3

---

## Fase 3 — Integração Completa
**Objetivo:** pipeline funcionando de ponta a ponta.

- [ ] Firmware ESP32 completo (FreeRTOS, dual radio UWB+BLE)
- [ ] Daemon totem com fila de prioridade em Python
- [ ] Processor gravando no InfluxDB
- [ ] Dashboard Grafana com mapa e alertas em tempo real
- [ ] Alertas funcionando end-to-end (bracelete → vibração + dashboard)

---

## Fase 4 — Piloto em Campo
**Objetivo:** validar em mina real com trabalhadores reais.

- [ ] Selecionar área piloto (galeria de 50–100m)
- [ ] Instalar 3–5 totens com PoE e nobreak
- [ ] Operar com 5–10 trabalhadores por 1 semana
- [ ] Mapear problemas de cobertura UWB no ambiente real
- [ ] Ajustar densidade de totens e parâmetros de trilateração

---

## Fase 5 — Produto
**Objetivo:** escalar para operação completa.

- [ ] WireGuard VPN + acesso remoto ao dashboard
- [ ] API pública para integração com sistemas da mineradora
- [ ] App mobile para supervisores (alertas push)
- [ ] Relatórios automáticos de turno
- [ ] Início do modelo SaaS multi-mineradora

---

## Fase 6 — Certificação
**Objetivo:** conformidade total e comercialização.

- [ ] Avaliação de necessidade de certificação ATEX por zona
- [ ] Certificação INMETRO do dispositivo wearable
- [ ] Auditoria de conformidade NR-22
- [ ] Documentação técnica para licitações
