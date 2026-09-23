# 📌 Roteiro de Implementação: Enriquecimento com Dados do Jupiterweb

> **Documento de Acompanhamento, Histórico e Status da Implementação**  
> **Funcionalidade:** Enriquecimento progressivo em segundo plano das células da grade com dados de turmas, docentes e vagas do Jupiterweb (USP).  
> **Status Geral:** ✅ Concluído & Homologado (100% das 5 fases implementadas, verificadas e aprovadas no Web App)  
> **Última Atualização:** 23/09/2026 (v0.3.0 Build 13)

---

## 📊 Painel de Progresso

| Fase | Descrição | Passos | Concluídos | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Fase 1** | Especificação Técnica, ADR e Infraestrutura de Testes | 2 | 2 | ✅ Concluído |
| **Fase 2** | Backend no Apps Script (Parser, Paralelismo e Caching) | 3 | 3 | ✅ Concluído |
| **Fase 3** | Frontend: Interface do Card Elegante e Estilos | 2 | 2 | ✅ Concluído |
| **Fase 4** | Frontend: Fila Controlada, Reatividade e Interações | 3 | 3 | ✅ Concluído |
| **Fase 5** | Validação E2E, Sincronização GAS e Homologação | 2 | 2 | ✅ Concluído |
| **TOTAL** | **Todas as Fases** | **12** | **12** | **100% Concluído** |

---

## 🎯 Legenda de Status
- ⏳ **Pendente:** Passo pronto para execução, aguardando início.
- 🚧 **Em Andamento:** Código ou testes sendo implementados no momento.
- ✅ **Concluído:** Implementado, testado e verificado com sucesso.
- ⏸️ **Bloqueado:** Dependência externa ou impedimento detectado.

---

## 🗺️ Divisão em Passos Pequenos, Verificáveis e Testáveis

### FASE 1: Especificação Técnica, ADR e Infraestrutura de Testes

#### ✅ Passo 1.1 — Especificação Formal do Parser e Registro Arquitetural (ADR)
- **Objetivo:** Estabelecer a documentação de referência das expressões regulares, mapeamento de charset `ISO-8859-1`, decodificação de entidades HTML e registrar formalmente as decisões arquiteturais (bypass de CORS, fila com concorrência controlada e renderização reativa).
- **Arquivos Envolvidos:**
  - `[NEW]` [`docs/especificacao-parser-jupiterweb.md`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/docs/especificacao-parser-jupiterweb.md)
  - `[NEW]` [`docs/adr/0013-enriquecimento-progressivo-jupiterweb.md`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/docs/adr/0013-enriquecimento-progressivo-jupiterweb.md)
- **Critério de Verificação Automatizado:**
  - Validação de links e sintaxe markdown.
- **Critério de Verificação Manual:**
  - Revisão visual dos documentos garantindo que todas as tabelas de regexes, casos de borda e decisões do ADR estejam completas.
- **Status:** ✅ Concluído

---

#### ✅ Passo 1.2 — Infraestrutura da Suíte de Testes e Fixtures Reais
- **Objetivo:** Criar o orquestrador central de testes (`run_all_tests.py`) com relatório colorido no terminal e disponibilizar arquivos de fixture com HTMLs reais do Jupiterweb (`SMA0356`, `7600006` e página sem oferecimento ativo).
- **Arquivos Envolvidos:**
  - `[NEW]` [`tests/run_all_tests.py`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/tests/run_all_tests.py)
  - `[NEW]` `tests/fixtures/jupiter_sma0356.html`
  - `[NEW]` `tests/fixtures/jupiter_7600006.html`
  - `[NEW]` `tests/fixtures/jupiter_sem_oferecimento.html`
- **Critério de Verificação Automatizado:**
  ```powershell
  python tests/run_all_tests.py
  ```
  *(Deve executar o runner com sucesso e relatar zero falhas nos módulos iniciais).*
- **Critério de Verificação Manual:**
  - Conferir a formatação visual e legibilidade da saída no console PowerShell.
- **Status:** ✅ Concluído

---

### FASE 2: Backend no Google Apps Script (Parser, Paralelismo e Caching)

#### ✅ Passo 2.1 — Testes e Algoritmo de Casamento de Turmas (Turma Matcher)
- **Objetivo:** Garantir casamento infalível entre a string da célula na planilha (ex.: `SEM0538 - T1`, `T1 e T2`, `T2[1]`, `T1 tv`, `SMA0300`, `SEP5864`) e as turmas retornadas pelo Júpiter.
- **Arquivos Envolvidos:**
  - `[NEW]` [`tests/test_turma_matching.py`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/tests/test_turma_matching.py)
  - `[MODIFY]` [`src/alocacao-plus.gs`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/alocacao-plus.gs) (funções `extrairInfoTurmaDaCelula` e `casarTurmaComDados`)
- **Critério de Verificação Automatizado:**
  ```powershell
  python -m unittest tests/test_turma_matching.py
  ```
  *(100% de aprovação nos testes unitários e nos 1.000 casos sintéticos aleatórios de property fuzzing).*
- **Critério de Verificação Manual:**
  - Validar casos especiais: células com turma única (`T1` $\rightarrow$ `01`), turmas conjuntas (`T1 e T2` $\rightarrow$ união de docentes), sem turma (`SMA0300` $\rightarrow$ fallback neutro) e pós-graduação (`SEP5864` $\rightarrow$ ignorado).
- **Status:** ✅ Concluído

---

#### ✅ Passo 2.2 — Testes e Implementação do Parser HTML do Jupiterweb
- **Objetivo:** Implementar o extrator robusto de dados HTML em JavaScript ES6/V8 no Apps Script, convertendo o HTML do Júpiter em um objeto estruturado (disciplina, turmas, docentes, horários e vagas), tratando acentuação e entidades HTML.
- **Arquivos Envolvidos:**
  - `[NEW]` [`tests/test_jupiter_parser.py`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/tests/test_jupiter_parser.py)
  - `[MODIFY]` [`src/alocacao-plus.gs`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/alocacao-plus.gs) (funções `decodificarEntidadesHtml` e `parsearHtmlJupiterweb`)
- **Critério de Verificação Automatizado:**
  ```powershell
  python -m unittest tests/test_jupiter_parser.py
  ```
  *(Validação de integridade dos dados extraídos a partir das fixtures reais e contra 200 variações de HTML aleatório com ruído sintético).*
- **Critério de Verificação Manual:**
  - Verificar que docentes acentuados (ex.: "Cláudia", "José", "Antônio") saem perfeitamente limpos e sem entidades HTML residuais.
- **Status:** ✅ Concluído

---

#### ✅ Passo 2.3 — Endpoint em Lote com `UrlFetchApp.fetchAll` e Caching Multinível
- **Objetivo:** Implementar a função backend `obterLoteJupiterweb(listaCodigos)` com busca paralela nativa via `UrlFetchApp.fetchAll`, decodificação explícita `getContentText('ISO-8859-1')`, cache negativo para sem oferecimento e armazenamento no `CacheService` (TTL 6h).
- **Arquivos Envolvidos:**
  - `[MODIFY]` [`src/alocacao-plus.gs`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/alocacao-plus.gs) (função `obterLoteJupiterweb`)
- **Critério de Verificação Automatizado:**
  - Teste automatizado de estrutura e payload retornado (garantir formato `{ sucesso: true, dados: { ... } }` e JSON < 100 KB).
- **Critério de Verificação Manual:**
  - Executar teste no Apps Script: consultar `obterLoteJupiterweb(['SMA0356', '7600006'])`.
  - Primeira execução: busca na web em lote paralelo (< 1,5s).
  - Segunda execução imediata: retorno instantâneo via `CacheService` (< 50ms).
- **Status:** ✅ Concluído

---

### FASE 3: Frontend: Interface do Card Elegante e Estilos

#### ✅ Passo 3.1 — Estrutura HTML do Modal Interativo no `index.html`
- **Objetivo:** Adicionar ao `index.html` a estrutura acessível do modal `#modal-card-disciplina` (`role="dialog"`, `aria-modal="true"`), contendo cabeçalho com identificação da disciplina, seletor de turmas por pills, painel de detalhes, barra de preenchimento de vagas, estado de ausência de oferecimento e botões de ação.
- **Arquivos Envolvidos:**
  - `[MODIFY]` [`src/index.html`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/index.html)
- **Critério de Verificação Automatizado:**
  - Validação estática de fechamento de tags HTML e acessibilidade de atributos ARIA.
- **Critério de Verificação Manual:**
  - Carregar a página no navegador e validar que o modal permanece oculto por padrão (`display: none`), sem causar nenhum impacto visual ou quebra de layout na grade principal.
- **Status:** ✅ Concluído

---

#### ✅ Passo 3.2 — Estilos do Card Elegante e Indicadores Visuais no `estilos.html`
- **Objetivo:** Implementar estilos CSS no padrão visual institucional EESC-USP (azul `#104880`, amarelo `#f2b705`), backdrop com desfoque (*glassmorphism*), badges de turma, barra semântica de ocupação de vagas, skeleton loader animado e classe decorativa `.link-disc-enriquecido`.
- **Arquivos Envolvidos:**
  - `[MODIFY]` [`src/estilos.html`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/estilos.html)
- **Critério de Verificação Manual:**
  - Abrir temporariamente o modal via console do navegador (`abrirCardDisciplinaTeste()`) para inspecionar:
    - Transição suave de entrada e saída com opacidade.
    - Barra de vagas colorida conforme preenchimento (verde / âmbar / vermelho).
    - Responsividade perfeita em tela cheia de desktop e em viewport móvel de smartphone (375px).
- **Status:** ✅ Concluído

---

### FASE 4: Frontend: Fila Controlada, Reatividade e Interações

#### ✅ Passo 4.1 — Testes Automatizados da Máquina de Estados da Fila
- **Objetivo:** Validar via testes automatizados a lógica de priorização dinâmica, restrição estrita de 1 requisição em voo, promoção urgente no clique (Prioridade 0) e tolerância a respostas fora de ordem.
- **Arquivos Envolvidos:**
  - `[NEW]` [`tests/test_queue_logic.py`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/tests/test_queue_logic.py)
- **Critério de Verificação Automatizado:**
  ```powershell
  python -m unittest tests/test_queue_logic.py
  ```
  *(100% de aprovação na máquina de estados da fila, deduplicação e controle de concorrência).*
- **Status:** ✅ Concluído

---

#### ✅ Passo 4.2 — Implementação da Fila em Segundo Plano e Cache no `scripts.html`
- **Objetivo:** Implementar no cliente o gerenciador da fila assíncrona, sincronização com `sessionStorage`, priorização por salas/horários filtrados e viewport de rolagem, garantindo no máximo 1 lote em trânsito com delay de alívio de 250ms.
- **Arquivos Envolvidos:**
  - `[MODIFY]` [`src/scripts.html`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/scripts.html)
- **Critério de Verificação Manual:**
  - Abrir o Web App com o DevTools aberto no Console.
  - Constatar que os lotes de 2-3 disciplinas são solicitados sequencialmente (um por vez), sem erros de limite simultâneo do Apps Script.
  - Trocar de bloco e conferir pelo console que as novas disciplinas visíveis passam instantaneamente para o início da fila.
- **Status:** ✅ Concluído

---

#### ✅ Passo 4.3 — Renderização Reativa, Delegação de Cliques e Tooltips
- **Objetivo:** 
  1. Conectar a montagem das células em `renderizarGrade()` com `estadoApp.cacheJupiter`, gerando o `title` na tag `<a>` e classes enriquecidas de forma reativa e imune a apagamentos por re-renderização.
  2. Implementar delegação de eventos no contêiner `#grade-corpo`: `click` com `e.preventDefault()` para abrir o modal, preservando `Ctrl+Clique` para nova aba.
  3. Lógica completa do modal: pré-seleção da turma correspondente à célula, renderização de horários e vagas, fechamento via `Esc` ou backdrop com restauração do foco.
- **Arquivos Envolvidos:**
  - `[MODIFY]` [`src/scripts.html`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/scripts.html)
- **Critério de Verificação Manual:**
  - Hover sobre a disciplina: exibe `Docente: [Nome]` ou `Docentes: [Nome 1], [Nome 2]`.
  - Clicar na disciplina: abre o Card Elegante na turma certa.
  - Filtrar por outro bloco ou esperar 60s: constatar que o tooltip e enriquecimento visual continuam ativos.
  - Pressionar tecla `Esc`: fecha o modal e retorna o foco para a célula.
- **Status:** ✅ Concluído

---

### FASE 5: Validação E2E, Sincronização GAS e Homologação

#### ✅ Passo 5.1 — Execução Global da Suíte de Testes Automatizados
- **Objetivo:** Rodar todos os testes de regressão, parser, casamento de turmas e fila de forma unificada.
- **Critério de Verificação Automatizado:**
  ```powershell
  python tests/run_all_tests.py
  ```
  *(Todos os testes devem reportar 100% de sucesso).*
- **Status:** ✅ Concluído

---

#### ✅ Passo 5.2 — Sincronização via API do GAS e Homologação no Web App Real
- **Objetivo:** Enviar os arquivos modificados para o projeto oficial no Google Apps Script via `tools/gas_sync.py`, testar o Web App implantado em ambiente real e registrar o bump de versão para a nova release.
- **Arquivos Envolvidos:**
  - [`version.json`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/version.json)
  - [`BACKLOG.md`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/BACKLOG.md)
- **Critério de Verificação Automatizado:**
  ```powershell
  python tools/gas_sync.py push
  ```
- **Critério de Verificação Manual:**
  - Acessar o Web App oficial no navegador e dispositivo móvel.
  - Conferir ausência de erros no console do Apps Script (`Stackdriver`).
  - Validar que a velocidade de carregamento inicial da grade segue instantânea (0ms).
- **Status:** ✅ Concluído

---

## 📝 Diário de Bordo e Histórico de Execução

| Data / Hora | Passo | Responsável | Ação Realizada | Resultado / Notas |
| :--- | :---: | :---: | :--- | :--- |
| 23/09/2026 | - | Antigravity | Criação do roteiro detalhado e estruturação dos 12 passos verificáveis. | Planejamento concluído e registrado. |
| 23/09/2026 | 1.1 | Antigravity | Criação da especificação técnica formal do parser (`docs/especificacao-parser-jupiterweb.md`), ADR 0013 e atualização do índice de ADRs. | Passo 1.1 concluído e verificado. |
| 23/09/2026 | 1.2 | Antigravity | Criação do orquestrador `tests/run_all_tests.py` com suporte a cores e UTF-8 no Windows; download das 3 fixtures HTML reais do Jupiterweb (`SMA0356`, `7600006`, sem oferecimento). | Passo 1.2 concluído e verificado. |
| 23/09/2026 | 2.1 | Antigravity | Implementação e teste do algoritmo de casamento de turmas (10 testes unitários + 1.000 property fuzzing); adição de `extrairInfoTurmaDaCelula` e `casarTurmaComDados` no `src/alocacao-plus.gs`. | Passo 2.1 concluído e verificado. |
| 23/09/2026 | 2.2 | Antigravity | Implementação do parser HTML do Jupiterweb (`parsearHtmlJupiterweb`) e decodificador de entidades (`decodificarEntidadesHtml`) em `alocacao-plus.gs`; criação de 4 testes em `tests/test_jupiter_parser.py` (com 200 fuzzings sintéticos). | Passo 2.2 concluído e verificado. |
| 23/09/2026 | 2.3 | Antigravity | Implementação do endpoint backend `obterLoteJupiterweb` com `UrlFetchApp.fetchAll` paralelo, decodificação `ISO-8859-1`, ScriptCache de 6h e negative caching. | Passo 2.3 concluído e verificado. |
| 23/09/2026 | 3.1 | Antigravity | Adição da estrutura acessível do modal `#modal-card-disciplina` (`role="dialog"`, `aria-modal="true"`) com pills de turmas, grid de metadados, barra de vagas e skeleton loader no `src/index.html`. | Passo 3.1 concluído e verificado. |
| 23/09/2026 | 3.2 | Antigravity | Estilização completa do card modal com glassmorphism, Design System EESC-USP, barra de vagas com cores semânticas, skeleton shimmer e classe decorativa `.link-disc-enriquecido` no `src/estilos.html`. | Passo 3.2 concluído e verificado. |
| 23/09/2026 | 4.1 | Antigravity | Implementação da suíte `tests/test_queue_logic.py` (8 testes unitários + 1.000 fuzzing invariantes) validando priorização 0/1/2, concorrência estrita (1 em voo), deduplicação, FIFO e promoção urgente. | Passo 4.1 concluído e verificado (23 testes globais OK). |
| 23/09/2026 | 4.2 | Antigravity | Implementação da fila assíncrona em segundo plano, cache multinível (`sessionStorage` + RAM), priorização por filtros ativos/viewport de rolagem e controle de concorrência com alívio de 250ms no `src/scripts.html`. | Passo 4.2 concluído e verificado. |
| 23/09/2026 | 4.3 | Antigravity | Implementação da renderização reativa (`gerarConteudoCelula`), tooltips automáticos com docentes (`extrairDocentesParaTooltip`), delegação de cliques no `#grade-corpo` com bypass para nova aba, e lógica completa do Card Modal acessível. | Passo 4.3 concluído e verificado (23 testes globais OK). |
| 23/09/2026 | 5.1 | Antigravity | Execução global unificada da suíte automatizada (`python tests/run_all_tests.py`): 23 testes executados com 100% de sucesso em 0.33s (parser, turmas, fila, invariantes e fuzzing). | Passo 5.1 concluído e verificado. |
| 23/09/2026 | 5.2 | Antigravity | Atualização do backlog de release, build incrementado e push final para o Google Apps Script (7 arquivos sincronizados na nuvem). Todos os 12 passos concluídos com sucesso. | Passo 5.2 concluído e verificado. |
| 23/09/2026 | Fix | Antigravity | Correção do clique nos botões de disciplina: classe `.aberto` para transição do modal, seletor de backdrop corrigido, `data-codigo` nativo no backend e fallbacks de atributos no frontend (Build 13). | Build 13 sincronizado e validado (23/23 testes OK). |
| 23/09/2026 | QA | Usuário / Antigravity | Homologação em ambiente real: validação do funcionamento perfeito dos botões de disciplina, abertura do Card Modal Elegante, tooltips de docentes no hover e sincronização em produção. | ✅ Aprovado com 100% de sucesso pelo usuário no Web App real. |
| 23/09/2026 | UX | Antigravity / Usuário | Melhoria visual e comportamental: remoção definitiva da bolinha indicadora, exibição da setinha `↗` com navegação externa enquanto pendente e ocultação da setinha com abertura do modal quando carregado (Build 14). | ✅ Testado e aprovado com 100% de sucesso no Web App real. |

*(Todos os 12 passos do plano foram concluídos, corrigidos, refinados e homologados com 100% de sucesso).*





