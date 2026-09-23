# 13. Enriquecimento Progressivo de Disciplinas com Dados do Jupiterweb

* **Data:** 2026-09-23
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
A grade de horários da EESC-USP disponibiliza as siglas das disciplinas e turmas (ex.: `SEM0538 - T1`, `SMA0356 - T2`), mas docentes, horários detalhados e vagas oferecidas só podiam ser consultados abrindo individualmente a página do **Jupiterweb** em outra aba do navegador.

Para enriquecer a experiência dos usuários, surgiu a demanda de:
1. Exibir o nome do docente responsável diretamente ao passar o mouse sobre a célula (**Hover**).
2. Abrir um **Card Modal Elegante** com os detalhes completos (docentes, horários oficiais, ocupação de vagas e observações) ao clicar na disciplina (**Clique**).
3. **Preservar a velocidade instantânea (0ms)** de abertura da grade horária, sem qualquer engasgo ou lentidão perceptível.

Contudo, a arquitetura impõe desafios técnicos rigorosos:
* **CORS da USP:** O navegador não consegue requisitar páginas em `https://uspdigital.usp.br` diretamente devido a políticas de Cross-Origin Resource Sharing.
* **Tempo de Resposta do Jupiterweb:** Cada requisição externa ao Júpiter leva entre 500ms e 2.000ms. Carregar dezenas de disciplinas previamente tornaria o carregamento inicial da grade inaceitavelmente lento (30 a 60 segundos).
* **Limitações de Concorrência do Google Apps Script:** O Apps Script limita execuções simultâneas por usuário (`"Too many simultaneous invocations"`). Disparos múltiplos em paralelo sem controle resultam em falhas 429/500.
* **Ciclo de Vida da Grade:** A grade do Alocação Plus é re-renderizada a cada alteração de filtro e a cada 60 segundos automaticamente para atualizar o horário atual, o que destrói e recria elementos do DOM.

## Alternativas Consideradas
* **Carregamento Síncrono Total no Backend (Descartado):** Consultar todas as disciplinas no Apps Script antes de entregar a grade ao usuário. Inviável, pois destruiria o tempo de resposta instantâneo (0ms) que é o principal diferencial do Alocação Plus.
* **Scraping Direto no Cliente (Descartado):** Bloqueado de forma intransponível pelas políticas de CORS do domínio `uspdigital.usp.br`.
* **Enriquecimento Imperativo Direto no DOM (Descartado):** Adicionar listeners e `title` diretamente em células do DOM via `document.querySelector`. Descartado porque a cada troca de filtro ou a cada 60 segundos o `innerHTML` da grade é reconstruído, apagando todos os enriquecimentos.
* **Motor Assíncrono com Fila Reativa e Controle de Concorrência (Escolhido):** O cliente renderiza a grade em 0ms; um *background worker* no navegador consome a fila com prioridade para disciplinas visíveis, mantendo **no máximo 1 requisição em voo** no Apps Script, com cache multinível e injeção reativa no `renderizarGrade()`.

## Decisão Adotada
Implementar o motor de enriquecimento progressivo com os seguintes pilares arquiteturais:

1. **Bypass de CORS e Paralelismo no Apps Script:**
   * Criação do endpoint `obterLoteJupiterweb(listaCodigos)` no arquivo [`src/alocacao-plus.gs`](../../src/alocacao-plus.gs).
   * Consulta prévia ao `CacheService`.
   * Para códigos não cacheados, execução de busca paralela no Google via `UrlFetchApp.fetchAll` com decodificação explícita `getContentText('ISO-8859-1')`.
2. **Estratégia de Cache Multinível:**
   * **Nível 1 (Servidor):** `CacheService` com TTL de 6 horas (21.600s), persistindo apenas o JSON parseado (< 100 KB).
   * **Cache Negativo:** Disciplinas sem oferecimento ativo são cacheadas como `{ semOferecimento: true }`, evitando reconsultas cíclicas.
   * **Nível 2 (Cliente):** `sessionStorage` no navegador sincronizado com `estadoApp.cacheJupiter`.
3. **Fila Dinâmica com Controle Estrito de Concorrência:**
   * A fila mantém no máximo **1 requisição em trânsito por vez** (`estadoApp.requisicaoEmVoo = true/false`), com pausa de 250ms entre lotes.
   * **Priorização Inteligente:** Células visíveis na tela (filtros ativos e viewport) têm Prioridade 1. Células ocultas têm Prioridade 2. Clicar em uma disciplina promove-a imediatamente para **Prioridade 0 (urgente)** com abertura de *skeleton loader*.
4. **Reatividade e Delegação de Eventos:**
   * A função `renderizarGrade()` verifica `estadoApp.cacheJupiter` na montagem da string do template, tornando o enriquecimento imune a re-renderizações da tabela.
   * Delegação de cliques no `#grade-corpo`: intercepta links de disciplinas com `e.preventDefault()`, preservando `Ctrl+Clique` ou botão do meio para quem desejar abrir em nova aba.
5. **Casamento Preciso de Turmas e Acessibilidade:**
   * Algoritmo de mapeamento entre a célula da grade e a turma no Júpiter (`SEM0538 - T1` $\rightarrow$ Turma `01`, `T1 e T2` $\rightarrow$ docentes unificados, célula sem turma $\rightarrow$ exibição de todas as opções).
   * Card modal acessível (`role="dialog"`, `aria-modal="true"`), com fechamento por tecla `Esc` e restauração de foco.

## Consequências
### Positivas (+)
* **Grade Instantânea Mantida (0ms):** A tabela carrega imediatamente com os dados locais do SVGRAD. O enriquecimento do Jupiterweb ocorre de forma silenciosa e transparente.
* **Estabilidade e Quota Protegida:** A fila serializada com `fetchAll` respeita rigorosamente as cotas de execução do Google Apps Script.
* **Experiência de Uso Superior:** Visualização rápida do professor pelo hover e abertura de modal completo e elegante sem sair da aplicação.
* **Resiliência a Filtros:** O estado persiste em `sessionStorage` e sobrevive a qualquer reorganização ou filtragem da grade.

### Negativas / Trade-offs (-)
* O carregamento de disciplinas secundárias fora da tela pode levar alguns minutos em conexões lentas se houver mais de 50 disciplinas distintas no semestre (mitigado pela promoção imediata ao topo da fila caso o usuário clique na célula).
* Dependência contínua do formato HTML retornado pelo Jupiterweb (mitigado por testes automatizados com fixtures reais e fuzzing sintético).

## Referências no Código
* [src/alocacao-plus.gs](../../src/alocacao-plus.gs) (funções `obterLoteJupiterweb` e `parsearHtmlJupiterweb`)
* [src/scripts.html](../../src/scripts.html) (fila progressiva, reatividade e delegação de eventos)
* [src/index.html](../../src/index.html) (estrutura do modal `#modal-card-disciplina`)
* [src/estilos.html](../../src/estilos.html) (estilos do card, badges e animações)
* [docs/especificacao-parser-jupiterweb.md](../especificacao-parser-jupiterweb.md)
* [docs/implementacao-enriquecimento-jupiterweb.md](../implementacao-enriquecimento-jupiterweb.md)
