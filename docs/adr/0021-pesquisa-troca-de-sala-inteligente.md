# 21. Pesquisa Inteligente de Troca de Sala (Modo Salas Livres Automatizado)

* **Data:** 2026-09-25
* **Status:** **Aceito**
* **Decisores:** Equipe Alocação Plus (EESC-USP)

## Contexto e Problema

No fluxo operacional de gestão das aulas na EESC-USP, coordenadores de curso, docentes e secretarias de departamento frequentemente necessitam remanejar uma turma para uma sala alternativa livre, seja por superlotação de matriculados, manutenções emergenciais na sala original ou necessidade de infraestrutura física específica.

Com a integração oficial dos dados de **Alunos Matriculados** (Jupiterweb) e **Número de Vagas** (Janus) no card modal flutuante de informações da disciplina (ADR 0020), o sistema passou a dispor de todos os parâmetros para automatizar a busca por uma sala livre adequada.

Entretanto, esse processo manual exigia que o usuário:
1. Memorizasse ou anotasse a demanda de alunos;
2. Fechasse o card da disciplina;
3. Limpasse a busca textual (já que a busca textual desativa o modo de salas livres);
4. Selecionasse manualmente o dia da semana da aula;
5. Ajustasse os dropdowns de horário inicial e final;
6. Digitasse a capacidade mínima necessária no filtro;
7. Ativasse o botão "🚪 Apenas Salas Livres".

Além de lento e sujeito a erros de transcrição, o fluxo manual enfrentava conflitos operacionais quando:
- A disciplina possui múltiplos horários na semana (ex: Terça e Quinta);
- A aula ocupa múltiplos slots mesclados (`colspan > 1`);
- O usuário alterna entre abas de turmas dentro do card;
- Filtros prévios de blocos ou salas individuais restringem indevidamente os resultados;
- A sala original (onde a aula acontece) precisava ser excluída das alternativas livres.

## Decisão Adotada

Implementamos a funcionalidade **Pesquisa Inteligente de Troca de Sala**, acionada diretamente pelo botão `Trocar de Sala ⇄` no rodapé do card modal da disciplina.

### 1. Elemento Visual, Simbologia e Layout
- **Caractere Tipográfico:** Adotado o símbolo Unicode `⇄` (`U+21C4` - *Rightwards Arrow Over Leftwards Arrow*), garantindo harmonia estética com o botão vizinho `Abrir no Jupiterweb ↗` (`U+2197`).
- **Posicionamento Sequencial:** O botão `Trocar de Sala ⇄` é posicionado como o 2º elemento no rodapé do modal, imediatamente após o link externo (`Abrir no Jupiterweb ↗` / `Abrir no Janus ↗`).
- **Otimização de Espaço Horizontal:** O botão de filtragem foi renomeado de `"Filtrar grade por <DISCIPLINA>"` para **`"Filtrar <DISCIPLINA>"`** (ex: *Filtrar SMA0356*), economizando mais de 60px e permitindo que todos os 4 botões se acomodem confortavelmente em uma única linha no desktop.
- **Hierarquia Visual:** Estilo outline secundário em conformidade com [`docs/padroes-interface-botoes.md`](../padroes-interface-botoes.md), com micro-animações táteis (`translateY(-1px)` no hover, `scale(0.96)` no clique e curva `cubic-bezier(0.34, 1.56, 0.64, 1)`).
- **Responsividade:** Rodapé com `flex-wrap: wrap; gap: 8px;` e disposição vertical em dispositivos móveis (`flex-direction: column-reverse;`), garantindo que o botão fique ao alcance do polegar.
- **Barra de Ações da Grade:** A mensagem *"Carregando dados do Jupiterweb/Janus"* e sua barra de progresso foram realocadas para o lado direito do espaço livre, imediatamente à esquerda do botão `"🧹 Limpar Filtros"`.

### 2. Resolução Hierárquica de Contexto e Horários
Para resolver com precisão disciplinas com múltiplos horários semanais e alternância de abas de turmas no modal, estabelecemos uma precedência estrita:
1. **Prioridade 1 (Slot da Célula Disparadora):** Se a abertura do card partiu do clique em uma célula da grade, o dia da semana e a faixa horária daquela célula específica são preservados como contexto primário.
2. **Cálculo Preciso de Faixa com Mesclagem (`colspan`):** O início e término da aula são calculados a partir dos slots canônicos da planilha (`dados.slots[cIdx].horaInicioMin` até `dados.slots[cIdx + cs - 1].horaFimMin`), imune a filtros que truncam o `colspan` visível no DOM.
3. **Alternância de Abas:** Caso o usuário troque de aba para uma turma com horários diferentes:
   - Se a nova turma também tiver aula no mesmo dia da célula original, o dia é mantido;
   - Caso não haja aulas no mesmo dia, o sistema adota o primeiro horário cadastrado na nova turma (`turmaObj.horarios[0]`).
4. **Fallback:** Se os dados do Júpiter/Janus ainda estiverem carregando (Skeleton) ou em caso de ausência de oferecimento, a pesquisa utiliza o dia e horário da célula da grade e assume capacidade 0 ("Todas").

### 3. Extração Resiliente de Demanda
- **Graduação:** Utiliza o campo `matriculados`.
- **Pós-Graduação:** Utiliza o campo `vagas`.
- **Proteção Falsy de Zero:** Valores `0` são preservados e tratados como capacidade 0 ("Todas as capacidades").
- **Dados Ausentes:** Fallback para 0 sem disparar exceções `TypeError`, acompanhado de Toast orientador.

### 4. Limpeza Silenciosa e Aplicação Atômica de Filtros
- Substituída a rotina tradicional de limpeza por `limparBuscaSilenciosa()`, evitando renderização intermediária prematura e roubo de foco do teclado.
- Redefinição atômica do estado da aplicação:
  - `estadoApp.blocosSelecionados = {'todos'}`;
  - `estadoApp.salasSelecionadas = {'todas'}`;
  - `estadoApp.diasSelecionados = {diaResolvido}`;
  - `estadoApp.horaInicioMin` e `horaFimMin` mapeados para os slots mais próximos;
  - `estadoApp.capacidadeMin = demanda`;
  - `estadoApp.apenasLivres = true`.
- Atualização sincronizada de todos os controles visuais (chips de dias, blocos, salas, dropdowns de início/fim e badge de capacidade).
- Disparo de **uma única renderização** da grade (`aplicarFiltrosEAtualizarVisualizacao()`).

### 5. Navegação, Acessibilidade e Feedback
- Fechamento suave do modal sem tentar devolver foco a elemento removido da grade (`ultimoElementoFocado = null`).
- Rolagem suave (`scrollIntoView({ behavior: 'smooth' })`) até o container da grade.
- Exibição de Toast informativo contextualizado: *"Exibindo salas livres para substituir [Sala Origem] (alunos ≥ N) em [Dia] ([Horário])."*

### 6. Testes Automatizados
- Criação de suíte de testes unitários dedicada em [`tests/test_troca_sala_logic.py`](../../tests/test_troca_sala_logic.py) com 12 testes cobrindo extração de demanda, normalização de dias, cálculo de `colspan`, hierarquia de horários, simulação de filtragem e property-based fuzzing com 200 iterações.

## Consequências

### Positivas
- **Produtividade Imediata:** Redução de um fluxo manual de 7 etapas para um único clique no card da disciplina.
- **Precisão Operacional:** Eliminação de erros manuais de digitação de horários ou capacidade.
- **Robustez:** Imunidade a filtros prévios, múltiplos horários na semana e células mescladas de longa duração.
- **Consciência Cognitiva:** Ocultação natural da sala de origem ocupada e Toast descritivo da busca aplicada.

### Negativas / Mitigações
- O acionamento da troca de sala redefine filtros prévios de blocos específicos para "Todos". Isso foi decidido deliberadamente para ampliar as alternativas de salas livres no campus, já que restrições de bloco poderiam ocultar salas vizinhas idênticas a poucos metros.

## Referências no Código
* [src/index.html](../../src/index.html)
* [src/estilos.html](../../src/estilos.html)
* [src/scripts.html](../../src/scripts.html)
* [tests/test_troca_sala_logic.py](../../tests/test_troca_sala_logic.py)
