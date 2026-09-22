# 6. Filtragem e Gestão de Estado Reativa 100% no Navegador

* **Data:** 2026-09-20
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
O Alocação Plus oferece múltiplos eixos simultâneos de filtragem:
1. **Dias:** Todos, dia específico ou atalho *"Focar em Hoje"*.
2. **Horários:** Intervalo customizado ("A partir das" / "Até"), atalho *"Agora"* (horário corrente do relógio) ou *"Qualquer Horário"*.
3. **Espaço Físico:** Blocos didáticos e seleção de salas específicas.
4. **Capacidade:** Lugares mínimos exigidos (ex: turmas de 30+, 50+ ou 80+ alunos).
5. **Modo Ocupação:** Alternância *"🚪 Apenas Salas Livres"*.
6. **Busca Textual:** Campo de texto livre com destaque e modo de foco *"🎯 Apenas colunas com resultado"*.

Se cada clique em um filtro disparasse uma chamada de rede ao servidor Google Apps Script (`google.script.run`), a latência de ida e volta (500ms a 2000ms) tornaria o uso da ferramenta truncado, além de esgotar cotas de invocação de script.

## Alternativas Consideradas
* **Filtragem no Servidor com Parâmetros (`obterGradeComFiltros(params)`):** Exigiria dezenas de requisições por sessão, inviabilizando buscas conforme a digitação (*type-ahead*) e gerando atraso perceptível para os usuários.
* **Paginação Clássica de Resultados:** Quebraria a visualização matricial da grade semanal, impedindo que o usuário tenha a visão panorâmica do campus.
* **Arquitetura *Single-Page Application* (SPA) com Estado Global no Cliente:** Carregar a matriz estruturada uma única vez na inicialização e executar 100% dos cálculos, filtragens e manipulações visuais em memória no navegador.

## Decisão Adotada
Implementar um padrão de arquitetura de estado reativo no cliente (`src/scripts.html`):
1. **Estado Centralizado (`estadoApp`):**
   ```javascript
   const estadoApp = {
     carregando: true,
     dadosBrutos: null,
     diasSelecionados: new Set(['todos']),
     blocosSelecionados: new Set(['todos']),
     salasSelecionadas: new Set(['todas']),
     horaInicioMin: null,
     horaFimMin: null,
     capacidadeMin: 0,
     apenasLivres: false,
     buscaSala: '',
     focarColunasMatch: true
   };
   ```
2. **Carga Única Inicial:** O frontend invoca `obterDadosGradeWeb(false)` apenas na inicialização (ou sob demanda no botão de sincronização).
3. **Processamento em Memória (`renderizarGrade`):**
   * Avalia dinamicamente a visibilidade de cada coluna (cruzamento de dia da semana, faixa de minutos e ocorrência de termos buscados).
   * Avalia a visibilidade de cada linha de sala (bloco, sala específica, capacidade mínima numérica e verificação se a sala está livre em todos os horários ativos).
   * Renderiza a tabela HTML via manipulação de fragmentos DOM, minimizando *reflows* de tela.
4. **Atualização Reativa de Indicadores:** Atualiza instantaneamente badges de resumo nos cards de filtro e o contador geral ("Exibindo X salas e Y horários").

## Consequências
### Positivas (+)
* **Latência Zero:** Qualquer seleção de filtro, clique em chip ou caractere digitado na busca produz feedback visual imediato (< 16ms, 60 FPS).
* **Economia Extrema de Recursos:** Após o carregamento inicial, a interação do usuário não consome absolutamente nenhuma cota do Google Apps Script.
* **Experiência Offline-like:** Se a conexão de rede oscilar durante o uso, o usuário continua conseguindo navegar, filtrar e encontrar salas livres com os dados já carregados.

### Negativas / Trade-offs (-)
* O navegador do cliente necessita de memória para armazenar a matriz JSON (~200 KB descomprimido, volume desprezível para dispositivos móveis modernos).

## Referências no Código
* [src/scripts.html](../src/scripts.html) (objeto `estadoApp`, funções `renderizarGrade`, `filtrarGrade`, `alternarDia`, `selecionarHorarioAgora`, `aoBuscarSala`)
* [src/index.html](../src/index.html)
