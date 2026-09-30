# 26. Correção de Ergonomia e Boas Práticas de UX no Posicionamento e Estilos de Botões em Modais de Confirmação

* **Data:** 2026-09-30
* **Status:** Aceito (Emenda/Substituição parcial do ADR 0024)
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
O [ADR 0024](0024-padronizacao-posicionamento-e-estilos-de-botoes-em-modais-e-acoes.md) formalizou regras de posicionamento e estilos de botões após a criação do Modal de Informações da Disciplina e do Modal de Preparação da Impressão. No entanto, generalizou inadvertidamente a estrutura de um diálogo puramente informativo para diálogos de ação e confirmação, incorrendo em dois problemas de Usabilidade e Ergonomia Cognitiva:

1. **Posicionamento Espacial Invertido (Violação do Fluxo LTR / Diagrama de Gutenberg):**
   - O ADR 0024 estipulava que botões de ação afirmativa/confirmação deveriam ficar no canto inferior esquerdo, enquanto botões de fechamento/cancelamento ficavam no canto inferior direito.
   - Nas convenções consolidadas da indústria de UX (Nielsen Norman Group, Google Material Design, Apple Human Interface Guidelines, Microsoft Fluent), a leitura ocidental da esquerda para a direita (LTR) e de cima para baixo culmina na chamada *"terminal area"* (canto inferior direito).
   - O botão que avança o fluxo (`Confirmar`, `Imprimir`, `Salvar`) deve ser o ponto final do processo decisório (extremo direito). A ação de cancelamento/desistência (`Cancelar`, `Voltar`) deve anteceder o botão afirmativo, posicionando-se à esquerda dele.

2. **Inversão de Hierarquia e Peso Visual:**
   - O ADR 0024 atribuía ao botão `Cancelar` a variante sólida primária institucional (`.btn-fechar-modal`, azul escuro `#104880` com texto branco) e ao botão de submissão `Imprimir / Salvar PDF` a variante secundária outline (`.btn-imprimir-confirmar`, fundo branco e borda suave).
   - Esse contraste reverso atraía o foco visual do usuário diretamente para a ação de desistência, provocando atrito e risco de cliques acidentais.

## Decisão Adotada
Revisar e corrigir a convenção arquitetural de botões e diálogos do sistema **Alocação Plus (EESC-USP)**:

### 1. Separação Semântica: Modais de Ação/Confirmação vs. Modais Informativos

* **Modais de Ação e Confirmação (ex.: Modal de Impressão da Grade):**
  - **Lado Esquerdo:** Ação de saída/desistência (`Cancelar`, `Voltar`). Utiliza a classe secundária outline `.btn-cancelar-modal` (fundo branco `#ffffff`, texto `var(--primary)`, borda suave).
  - **Lado Direito (Terminal):** Ação afirmativa/primária (`Confirmar`, `Imprimir / Salvar PDF`, `Salvar`). Utiliza o estilo institucional primário sólido `.btn-imprimir-confirmar` (fundo `var(--primary)`, borda `var(--primary)`, texto branco `#ffffff`, sombra de elevação).

* **Modais Puramente Informativos (ex.: Card de Informações da Disciplina):**
  - **Lado Esquerdo:** Ações e links contextuais de navegação externa ou filtros (`Abrir no Jupiterweb ↗`, `Trocar de Sala ⇄`, `Filtrar disciplina`).
  - **Lado Direito:** Botão de fechamento (`Fechar`), atuando como saída de leitura em estilo secundário outline (`.btn-fechar-modal`, fundo branco `#ffffff`, texto `var(--primary)` e borda suave), evitando destaque desproporcional para uma ação de encerramento e mantendo as ações operacionais do card valorizadas.

### 2. Hierarquia Visual Consistente
* Botões afirmativos de submissão/confirmação (`.btn-imprimir-confirmar`) carregam a maior proeminência visual (sólido institucional com preenchimento `var(--primary)` e texto branco).
* Botões de cancelamento ou fechamento (`.btn-cancelar-modal`, `.btn-fechar-modal`) e ações auxiliares operam com estilo secundário outline, preservando clareza sem poluição cognitiva.

### 3. Preservação de Micro-Interações e Acessibilidade
* Todas as classes de botão (`.btn-cancelar-modal`, `.btn-imprimir-confirmar`, `.btn-fechar-modal`) mantêm as micro-interações táteis ("efeitos fofinhos") padronizadas: transição spring, elevação no hover (`translateY(-1px)`), compressão no clique (`scale(0.96)`) e suporte estrito a `@media (prefers-reduced-motion: reduce)`.

## Consequências
### Positivas (+)
* **Conformidade com Boas Práticas Mundiais:** Alinhamento direto com as diretrizes do Nielsen Norman Group e dos principais Design Systems (Material, Apple HIG).
* **Redução de Erros Operacionais:** O usuário não é induzido a cancelar uma ação achando que o botão escuro à direita executa a operação.
* **Leitura Natural e Confortável:** O olhar varre os parâmetros configuráveis e encontra naturalmente a submissão no canto inferior direito.

### Negativas / Trade-offs (-)
* Requer atualização dos testes automatizados de posicionamento no DOM (`tests/test_print_logic.py`).

## Referências no Código
* [`src/index.html`](../../src/index.html) (Rodapé de `#modal-impressao-grade`)
* [`src/estilos.html`](../../src/estilos.html) (Classes `.btn-cancelar-modal`, `.btn-imprimir-confirmar`, `.btn-fechar-modal`)
* [`tests/test_print_logic.py`](../../tests/test_print_logic.py) (`test_conformidade_botoes_adr_0026`)
* [`docs/padroes-interface-botoes.md`](../padroes-interface-botoes.md)
* [`docs/adr/0024-padronizacao-posicionamento-e-estilos-de-botoes-em-modais-e-acoes.md`](0024-padronizacao-posicionamento-e-estilos-de-botoes-em-modais-e-acoes.md)
