# 19. Otimização de Espaço Vertical, Camadas Sticky da Grade e Refinamento do Cabeçalho

* **Data:** 2026-09-25
* **Status:** **Aceito**
* **Decisores:** Equipe Alocação Plus (EESC-USP)

## Contexto e Problema

1. **Sobreposição no Scroll Horizontal:** Durante a rolagem horizontal da tabela de horários, os cabeçalhos superiores dos dias da semana (`.th-dia-header`) sobrepunham visualmente os cabeçalhos fixos das colunas de Salas e Lugares (`.col-fixa-sala`, `.col-fixa-cap`). O comportamento esperado era que as células deslizassem por baixo das colunas fixas, assim como já ocorria com a linha de cabeçalhos das horas.
2. **Restrição de Espaço Vertical:** A grade de horários é o componente central da aplicação. Em telas de notebooks e resoluções padrão, a presença de elementos verticais redundantes (como uma linha exclusiva para rodapé `.app-footer` e outra linha isolada apenas para o contador de resultados `.barra-resultados`) reduzia a área visível da tabela, forçando rolagem vertical desnecessária.
3. **Consistência Visual no Cabeçalho:** O botão "Atualizar Dados" apresentava divergência de estilos em relação ao design system do projeto, e a informação de versão encontrava-se isolada no rodapé inferior.

## Alternativas Consideradas

* **Alternativa 1 (Ocultar rodapé apenas no desktop):** Manter o rodapé visível apenas em telas menores. Descartada pois em dispositivos móveis a área vertical da grade é ainda mais crítica.
* **Alternativa 2 (Empilhar informações de resultado abaixo da busca):** Descartada pois continuaria consumindo altura vertical da tela.
* **Alternativa 3 (Ajuste simplificado de z-index sem !important):** Descartada pois regras herdadas de tabelas com múltiplos `position: sticky` podiam causar intermitência de renderização entre navegadores.

## Decisão Adotada

1. **Camadas Sticky Rigorosas (`z-index`):**
   - Elevado o `z-index` dos cabeçalhos fixos da primeira linha (`th.col-fixa-sala` e `th.col-fixa-cap`) para `35 !important`.
   - Definido explicitamente o `z-index: 25` para os cabeçalhos de dias da semana (`.th-dia-header`), garantindo que tanto os dias quanto as horas deslizem perfeitamente sob os cabeçalhos fixos durante a rolagem horizontal.
2. **Maximização Vertical do Viewport:**
   - Remoção completa do container `.app-footer`, eliminando margens e preenchimentos que consumiam espaço vertical útil.
   - Migração da identificação de versão (`<?= APP_FULL_VERSION ?>`) para o cabeçalho principal, ao lado do título "Alocação Plus", sem borda de pílula e alinhada à linha de base.
   - Eliminação da linha avulsa `<div class="barra-resultados">`, realocando o contador informativo (`#txt-contador-resultados`) e o indicador de carregamento dinâmico em lote (`#status-carregamento-dinamico`) para dentro da barra de ações (`.barra-acoes-grade .acoes-esquerda`), imediatamente à direita da caixa de busca.
3. **Padronização Visual:**
   - Refatoração do botão "Atualizar Dados" com a classe `.btn-header-recarregar`, harmonizando bordas, cores institucionais e micro-interação tátil com os padrões de interface da aplicação.

## Consequências

### Positivas
* **Mais salas e horários visíveis simultaneamente:** Ganho acumulado de ~50px a ~70px de altura útil, aumentando a densidade informacional sem sensação de aperto.
* **Rolagem horizontal polida:** Fim do artefato visual de cabeçalhos de dias passando sobre os rótulos de Salas e Lugares.
* **Layout coeso e limpo:** A barra de ações agora concentra busca, filtros rápidos, contagem e status de carregamento em segundo plano em uma única faixa horizontal fluida.

### Negativas / Mitigações
* Em telas muito estreitas (mobile), os elementos da barra de ações precisam de espaço para quebrar em linhas adicionais. Isso foi mitigado com regras responsivas em `@media (max-width: 768px)` utilizando `flex-direction: column` e alinhamentos adaptados.
