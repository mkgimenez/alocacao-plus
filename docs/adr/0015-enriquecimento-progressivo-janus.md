# 15. Enriquecimento Progressivo de Disciplinas com Dados do Janus (Pós-Graduação)

* **Data:** 2026-09-24
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
A grade de horários da EESC-USP disponibiliza códigos e turmas de graduação e de pós-graduação. Com o sucesso da implementação do enriquecimento progressivo do Jupiterweb (ADR 0013), surgiu a demanda de replicar **100% dessa experiência** para as disciplinas de Pós-Graduação (Janus):
1. **Hover:** Exibir o nome do(s) docente(s) responsável(is) em tooltip reativo ao passar o mouse sobre a célula;
2. **Clique:** Abrir o **Card Modal Elegante** com os detalhes completos da pós-graduação (docentes, horários oficiais, local de aula, datas de início/término e modalidade);
3. **Preservar a velocidade instantânea (0ms)** de abertura da grade horária, sem travamentos ou concorrência excessiva.

Contudo, a arquitetura do Janus impõe particularidades técnicas específicas:
* **Separabilidade de Catálogo e Turmas:** Diferente do Jupiterweb, o Janus não entrega as turmas em uma página única. A listagem ocorre em `DisciplinaAux` e os detalhes da turma em páginas dedicadas.
* **Casca Intermediária JSF Desnecessária:** O link gerado em `DisciplinaAux` aponta para `publico/turma/<SIGLA>/<OFE>`, que carrega um documento JSF de ~50 KB contendo apenas um `<iframe>` para `../TurmaDet?sgldis=<SIGLA>&ofe=<OFE>&`.
* **Rótulos Dinâmicos via DWR (`.intl_*`):** Os textos descritivos das tags são gerados em tempo de execução no cliente. No HTML estático retornado pelo servidor, os textos são vazios, exigindo ancoragem estrita em classes CSS.
* **Codificação Windows-1252:** Presença de caracteres tipográficos específicos (como travessão *en-dash* byte `0x96`) e entidades numéricas decimais.

## Alternativas Consideradas
* **Carregamento da Casca Intermediária JSF (Descartado):** Realizar 3 etapas HTTP por turma (DisciplinaAux $\rightarrow$ casca JSF $\rightarrow$ TurmaDet). Descartado por onerar a rede em ~50 KB extras por turma e duplicar o tempo de resposta.
* **Carregamento Síncrono no Backend (Descartado):** Inviável, pois destruiria o tempo de resposta instantâneo (0ms) da grade.
* **Pipeline Otimizado em 2 Etapas Diretas com Bypass da Casca (Escolhido):** O backend realiza apenas 2 chamadas HTTP diretas por disciplina com oferecimento ativo (`DisciplinaAux` seguida diretamente de `TurmaDet`), com cache multinível de 6h e controle estrito de 1 requisição em trânsito por usuário.

## Decisão Adotada
Implementar o pipeline de enriquecimento do Janus com as seguintes diretrizes:

1. **Pipeline Otimizado em 2 Etapas Diretas:**
   - **Etapa 1:** Consulta paralela a `https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=<SIGLA>` via `UrlFetchApp.fetchAll`. Extrai o nome da disciplina e os IDs de oferecimento ativos.
   - **Etapa 2:** Resolução direta sem casca JSF: consulta paralela a `https://uspdigital.usp.br/janus/TurmaDet?sgldis=<SIGLA>&ofe=<OFE>&`. Extrai docentes, tabela de horários com locais, datas de início/término e modalidade.
2. **Parser Resiliente Ancorado em Classes CSS (`.intl_*`):**
   - Extração imune a internacionalização, ancorando em `.intl_docenteMinistrante`, `.intl_horario`, `.intl_local`, `.intl_dataInicial`, `.intl_formaOferecimento`.
3. **Estratégia de Cache Multinível e Chaves Canônicas:**
   - **Nível 1 (Servidor):** `CacheService` com prefixo `JAN_V1_` e TTL de 6h (21.600s). Cache negativo de 6h para disciplinas sem oferecimento ativo.
   - **Nível 2 (Cliente):** `sessionStorage` e RAM (`estadoApp.cacheJupiter` / `obterCacheDisciplina`).
   - Invalidação forçada limpa simultaneamente chaves `JUP_V18_` e `JAN_V1_`.
   - Turmas indexadas canonicamente com 2 dígitos (`"01"`), evitando duplicação de abas no modal.
4. **Fila Reativa Serializada e Controle de Concorrência:**
   - A fila de requisições consome lotes mistos de até 3 disciplinas, mantendo rigorosamente **no máximo 1 requisição em voo por usuário**.
5. **Card Modal Adaptativo e Preservação do ADR 0014:**
   - Cabeçalho dinâmico alternando entre `Graduação` e `Pós-Graduação (Janus)` com estilo visual semântico (`.badge-nivel-pos`).
   - Preservação integral das micro-animações táteis e alturas de caixa dos botões (`.btn-link-externo-jupiter`, `.btn-filtrar-disciplina`, `.btn-fechar-modal`).
   - Exibição de badge discreto de Local na tabela de horários com `flex-wrap: wrap;` para evitar quebras em telas estreitas (iPhone XR).

## Consequências
### Positivas (+)
* **Paridade Funcional Total:** Usuários contam com a mesma riqueza de detalhes, hover e modais tanto para graduação quanto para pós-graduação.
* **Economia de Rede de 50%:** Bypass da casca JSF poupa 50 KB e elimina 1 salto HTTP por oferecimento.
* **Resiliência a Mudanças:** A ancoragem em classes `.intl_*` previne quebras decorrentes de variações de texto ou idioma no Janus.
* **Zero Impacto no Tempo Inicial:** A grade abre em 0ms; todo o enriquecimento é progressivo em segundo plano.

### Negativas / Trade-offs (-)
* Disciplinas de pós com múltiplos oferecimentos demandam requisições proporcionais na Etapa 2 (mitigado pelo paralelismo de `fetchAll` e cache de 6 horas).

## Referências no Código
* [src/alocacao-plus.gs](../../src/alocacao-plus.gs) (funções `parsearHtmlJanusDisciplina`, `parsearHtmlJanusTurma`, `obterLoteDisciplinas`)
* [src/scripts.html](../../src/scripts.html) (fila reativa unificada e modal adaptativo)
* [src/estilos.html](../../src/estilos.html) (estilos do modal e `.badge-nivel-pos`)
* [docs/especificacao-parser-janus.md](../especificacao-parser-janus.md)
