# 0017. Coloração Progressiva da Grade, Priorização Geométrica no Viewport 2D e Consolidação do Card Modal

* **Data:** 2026-09-25
* **Status:** Aceito
* **Decisores:** Equipe de Arquitetura e Engenharia de Frontend (Alocação Plus / EESC-USP)

---

## Contexto e Problema

O **Alocação Plus** realiza o enriquecimento assíncrono de turmas, docentes e vagas conectando-se em segundo plano ao Jupiterweb (graduação) e ao Janus (pós-graduação). Com a evolução do sistema, identificaram-se três desafios centrais de usabilidade e performance perceptível:

1. **Ilusão de Prontidão nas Células da Grade:**  
   As células com aulas cadastradas iniciavam com as cores definitivas (azul céu para graduação e azul cobalto para pós-graduação). Isso criava a falsa expectativa de que os dados do card flutuante já estavam prontos para consulta imediata, quando na verdade ainda estavam na fila assíncrona.
2. **Priorização 1D Ineficiente na Fila de Segundo Plano:**  
   O escalonador ordenava as disciplinas apenas por linha de sala (1D). Isso fazia com que horários fora da tela à direita (noites e finais de tarde) fossem carregados antes das salas seguintes visíveis na primeira dobra, desperdiçando requisições em itens que o usuário não estava visualizando.
3. **Fila Estática durante a Rolagem:**  
   Ao rolar a página vertical ou horizontalmente, a ordem da fila não se adaptava ao novo campo de visão (*viewport*).
4. **Ruído Visual de Links Externos:**  
   Os botões de disciplinas continham o ícone indicador `↗` (link externo em nova aba). No entanto, o fluxo padrão agora sempre intercepta o clique para abrir o **Card Modal Elegante** interno (com prioridade 0 e esqueleto *shimmer*). A seta tornava a interface confusa ao sugerir uma navegação para fora da aplicação. Além disso, o rodapé continha uma linha extra de consultas diretas externas pouco utilizada.

---

## Decisão Adotada

### 1. Coloração Progressiva das Células (.celula-aula-pendente)
- Células que possuem disciplinas pendentes de carregamento iniciam com estilo discreto e neutro em tons de ardósia/cinza (`.celula-aula-pendente`), sem as cores temáticas do Jupiterweb e Janus.
- Conforme os lotes são concluídos pelo worker em segundo plano, as células afetadas recebem a classe `.link-disc-enriquecido`, disparando uma transição CSS suave (`transition: 0.4s`) para as tonalidades azuladas oficiais.
- Aplicação de micro-animação tátil (`celula-recem-carregada`) que sinaliza discretamente a prontidão do card modal sem causar distração.
- Preservação integral do cache: células cujos dados já estão em memória renderizam com suas cores plenas imediatamente ao alternar filtros ou dias.

### 2. Viewport 2D Geométrico & Consumo na Ordem Natural de Leitura
- Reestruturação de `extrairCodigosVisiveisEAgendar()` para calcular a interseção exata 2D entre as linhas de salas visíveis (`tr:not([style*="display: none"])`) e as colunas de horários visíveis no container com rolagem (`tabela-container`).
- Classificação estrita em 3 níveis de prioridade:
  - **Prioridade 0 (Urgência Máxima):** Clicada pelo usuário no momento;
  - **Prioridade 1 (Viewport 2D):** Células visíveis na tela, consumidas rigorosamente de cima para baixo e da esquerda para a direita (`posicaoVisual = rowIdx * 100 + colIdx`);
  - **Prioridade 2 (Fora do Viewport):** Células fora da tela (extensões horizontais ou abaixo da rolagem) e salas ocultas por filtros.

### 3. Reordenação Dinâmica Fiel com Scroll Listener
- Inclusão de detector de rolagem no container da grade com debounce ágil de **150ms** (`atualizarVisibilidadeFilaJupiter()`).
- Ao rolar a grade em qualquer eixo, a fila é reordenada dinamicamente, promovendo instantaneamente para a frente as disciplinas que acabaram de entrar no campo de visão.

### 4. Promoção Instantânea no Clique & Card Skeleton
- Ao clicar em uma disciplina pendente, a função `abrirCardDisciplina()` agenda o código imediatamente com **Prioridade 0** (furando toda a fila) e abre o Card Modal no estado de esqueleto animado (*skeleton shimmer*).
- Assim que o lote de 1 elemento responde, o modal substitui o esqueleto pelos dados completos sem recarregar a tela.

### 5. Higienização Visual da Grade e Rodapé
- Remoção do pseudo-elemento `::after` (`content: '\00a0↗'`) dos botões de disciplinas nas células. O ícone `↗` permanece ativo exclusivamente nos botões do rodapé do Card Modal ("*Abrir no Jupiterweb ↗*" / "*Abrir no Janus ↗*"), que de fato navegam para fora.
- Atualização do atributo `title` para `Consultar <código> (<sistema>) • Clique para ver detalhes`.
- Remoção da linha redundante de links externos do rodapé, centralizando a assinatura institucional e o badge de versão.

---

## Consequências

### Positivas (+)
* **Clareza de Estado:** O usuário sabe visualmente exatamente quais disciplinas já possuem dados enriquecidos e quais estão aguardando carregamento.
* **Percepção de Velocidade Drástica:** O Viewport 2D prioriza exatamente o que os olhos do usuário estão vendo, eliminando desperdício em horários da noite enquanto o usuário lê a manhã.
* **UX Sem Interrupções:** Clicar em qualquer disciplina não navega para fora; abre o modal de imediato e exibe os dados assim que o worker responde.
* **Cobertura Completa:** Criação de `tests/test_cell_coloring_logic.py` e expansão de `tests/test_queue_logic.py`, atingindo 72 testes automatizados com 100% de sucesso.

### Negativas / Mitigações (-)
* **Micro-Reflow no Scroll:** A reordenação ao rolar exige leitura de dimensões DOM (`getBoundingClientRect` ou `scrollLeft`/`clientWidth`). Mitigado com debounce de 150ms e cache de índices de colunas visíveis.

---

## Referências no Código
* [`src/estilos.html`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/estilos.html) (`.celula-aula-pendente`, `.celula-recem-carregada`, remoção de `::after`)
* [`src/scripts.html`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/scripts.html) (`extrairCodigosVisiveisEAgendar`, `atualizarVisibilidadeFilaJupiter`, `reordenarFilaJupiter`)
* [`src/alocacao-plus.gs`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/alocacao-plus.gs) (marcação de classes e atributo `title`)
* [`src/index.html`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/index.html) (limpeza do rodapé)
* [`tests/test_cell_coloring_logic.py`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/tests/test_cell_coloring_logic.py)
* [`tests/test_queue_logic.py`](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/tests/test_queue_logic.py)
