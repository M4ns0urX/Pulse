# Templates Visuais

Componentes HTML standalone para uso em apresentações, dashboards e protótipos do Pulse. Cada arquivo é independente — abre direto no browser, sem dependências externas.

---

## Templates disponíveis

| Arquivo                                | Descrição                                                                        | Estados                   |
| -------------------------------------- | -------------------------------------------------------------------------------- | ------------------------- |
| [`ecg-monitor.html`](ecg-monitor.html) | Monitor de ECG em tempo real estilo monitor hospitalar, com grade de fundo e BPM | Saudável · Alto · Crítico |

---

## ecg-monitor.html

Monitor cardíaco animado com forma de onda ECG real (complexo P-QRS-T), rolagem contínua e grade estilo osciloscópio.

### Preview

```
┌─────────────────────────────────────────────┐  72
│  · · · · · · · · · · · · · · · · · · · · ·  │ BPM
│  · · · · · · /\· · · · · · · · · · · · · ·  │
│  · · · · · ·/  \· · ·/\· · · · · · · · · ·  │
│  · · · /\· /    \·  /  \· · · · · · · · · ·  │
│  · · ·/  \/      \/    ·\· · · · · · · · · ·  │
└─────────────────────────────────────────────┘
```

Forma de onda P-QRS-T fisiologicamente correta:

- **Onda P** — despolarização atrial (pequena deflexão positiva)
- **Complexo QRS** — despolarização ventricular (pico principal)
- **Onda T** — repolarização ventricular (deflexão positiva suave)

### Estados

| Estado     | BPM     | Cor                | Uso                            |
| ---------- | ------- | ------------------ | ------------------------------ |
| `saudavel` | 72 bpm  | Verde `#00ff00`    | Trabalhador em condição normal |
| `alto`     | 120 bpm | Laranja `#ff8800`  | BPM elevado — atenção          |
| `critico`  | 150 bpm | Vermelho `#ff5500` | BPM crítico — emergência       |

### Como usar

Abra o arquivo diretamente no browser:

```bash
# Windows
start ecg-monitor.html

# macOS
open ecg-monitor.html

# Linux
xdg-open ecg-monitor.html
```

### Como customizar

Todas as variáveis estão no bloco `<script>` do arquivo:

```javascript
// BPM alvo de cada estado
const states = {
  saudavel: { bpm: 72, color: "#00ff00", bs: 1.0 },
  alto: { bpm: 120, color: "#ff8800", bs: 0.5 },
  critico: { bpm: 150, color: "#ff5500", bs: 0.25 },
};

// Tamanho da onda (proporção da altura da tela)
const AMP_SCALE = 0.13; // aumenta para onda maior

// Posição vertical da linha de base (0 = topo, 1 = fundo)
const CENTER_Y_RATIO = 0.52;

// Velocidade de rolagem (pixels por segundo)
const scrollPx = 180 * dt; // padrão ECG clínico: 25mm/s
```

**Trocar estado via botões na tela:**

- `S` — saudável (verde, 72 bpm)
- `A` — alto (laranja, 120 bpm)
- `C` — crítico (vermelho, 150 bpm)

**Esconder/mostrar grade:** botão `Grid` no canto inferior direito.

**Mudar estado por código:**

```javascript
setState("critico"); // aciona o estado crítico programaticamente
```

### Integração futura

Este template foi feito para ser conectado ao WebSocket da API do Pulse:

```javascript
const ws = new WebSocket("ws://servidor-local:8000/ws/live");
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  targBPM = data.bpm;

  if (data.priority === 3) setState("critico");
  else if (data.priority >= 1) setState("alto");
  else setState("saudavel");
};
```

---

## Como adicionar um novo template

1. Cria o arquivo HTML na pasta `templates/`
2. Usa nome em kebab-case descritivo: `nome-do-template.html`
3. Documenta aqui no README seguindo o mesmo padrão:
   - Descrição de uma linha
   - Preview em ASCII ou texto
   - Tabela de estados/variantes
   - Seção de customização com as variáveis principais
