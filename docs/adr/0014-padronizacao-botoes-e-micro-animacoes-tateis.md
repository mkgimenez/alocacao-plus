# 14. Padronização Visual de Botões e Micro-Animações Táteis ("Efeitos Fofinhos")

* **Data:** 2026-09-24
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
A interface do **Alocação Plus** adota uma identidade visual moderna, suave e responsiva com micro-animações táteis ("efeitos fofinhos") nos botões e chips de filtros da página principal. Essas animações proporcionam um feedback físico acolhedor através de elevação em hover (`translateY(-1px)`), sombras suaves e compressão rápida ao clique (`scale(0.96)` ou `scale(0.95)` em 0.05s).

Entretanto, com a evolução das funcionalidades — em especial a introdução do Card Flutuante (Modal de Informações da Disciplina do Jupiterweb) e a subsequente adição do botão de filtragem rápida —, surgiram inconsistências visuais e de comportamento entre os componentes:
1. **Discrepância Dimensional no Rodapé do Modal:** O botão "Fechar" utilizava `border: none;` e `padding: 7px 18px`, enquanto os botões irmãos ("Abrir no Jupiterweb" e "Filtrar grade por disciplina") utilizavam `border: 1px solid var(--primary-border);` e `padding: 7px 14px/16px`. Isso resultava em uma diferença física de 2px de altura entre os botões da mesma linha, quebrando o ritmo visual da interface.
2. **Comportamento Rígido e Inconsistente:** Ao passar o mouse sobre o botão de fechar, nas pills de turma ou no link externo do Jupiterweb, não havia elevação ou sombra correspondente à física dos botões da página principal; o clique parecia estático e sem feedback tátil.
3. **Pills de Turma Ativas sem Hover:** Quando uma turma estava ativa no modal (`.btn-pill-turma.ativa`), a interação de hover ficava congelada sem variação de tonalidade ou elevação.
4. **Alinhamento do Rodapé:** Os botões ficavam distribuídos via `space-between` simples, deixando o botão central ("Filtrar") isolado no meio do card em vez de agrupado ergonomicamente às ações à direita.

## Decisão Adotada
Padronizar a especificação de botões e micro-interações do sistema sob as seguintes diretrizes universais de Design System:

1. **Curva Universal de Transição com Efeito Mola (Spring Physics):**
   Todos os botões do sistema devem utilizar a combinação:
   ```css
   transition: background-color 0.18s cubic-bezier(0.4, 0, 0.2, 1),
               border-color 0.18s cubic-bezier(0.4, 0, 0.2, 1),
               color 0.18s cubic-bezier(0.4, 0, 0.2, 1),
               box-shadow 0.18s cubic-bezier(0.4, 0, 0.2, 1),
               transform 0.12s cubic-bezier(0.34, 1.56, 0.64, 1);
   ```

2. **Estados Táteis Padronizados:**
   * **Repouso:** Sombra suave base `0 1px 2px rgba(16, 72, 128, 0.04)`.
   * **Hover:** Elevação vertical de 1px (`transform: translateY(-1px)`) combinada com sombra expandida `0 2px 5px` (ou `0 3px 6px` para botões primários sólidos) e iluminação de fundo.
   * **Active (Pressionado):** Contração instantânea (`transform: scale(0.96)` ou `scale(0.95)` para pills/chips) com duração forçada de `transition-duration: 0.05s`, conferindo a sensação de um botão mecânico real.
   * **Focus Visible:** Foco por teclado com anel difuso de 2px `box-shadow: 0 0 0 2px rgba(...)`.

3. **Igualdade Dimensional e Modelo de Caixa:**
   * Todos os botões em linha (ex.: rodapé do modal) devem compartilhar a mesma altura de caixa, utilizando sempre borda explícita de `1px solid` (mesmo para variantes sólidas, usando `border: 1px solid var(--primary);`).
   * Alinhamento uniforme com `display: inline-flex; align-items: center; justify-content: center; line-height: 1.25;`.

4. **Hierarquia e Disposição do Rodapé:**
   * O link externo informativo (`.btn-link-externo-jupiter`) permanece alinhado à esquerda.
   * O botão de ação secundária/filtro (`.btn-filtrar-disciplina`) recebe `margin-left: auto`, posicionando-o lado a lado com o botão de fechamento (`.btn-fechar-modal`) à direita.
   * No mobile (`<= 540px`), todos os elementos preenchem 100% da largura com `margin-left: 0 !important`.

5. **Acessibilidade Universal:**
   * Inclusão de todos os novos seletores interativos na consulta `@media (prefers-reduced-motion: reduce)`, desativando transições e transformações para usuários com restrições motoras ou vestibulares.

## Consequências
### Positivas (+)
* **Consistência Visual Total:** O card flutuante agora segue exatamente a mesma linguagem de design suave e tátil do restante do sistema.
* **Alinhamento Físico Perfeito:** A discrepância de altura de 2px foi eliminada, garantindo simetria de pixels no rodapé.
* **Feedback Intuitivo ao Usuário:** A sensação tátil instantânea reforça visualmente o estado clicável de cada componente.

### Negativas / Trade-offs (-)
* Requer que novos botões criados futuramente no projeto sigam este padrão documentado em [`docs/padroes-interface-botoes.md`](../padroes-interface-botoes.md).

## Referências no Código
* [`src/estilos.html`](../../src/estilos.html) (classes `.modal-btn-fechar`, `.btn-pill-turma`, `.btn-link-externo-jupiter`, `.btn-filtrar-disciplina`, `.btn-fechar-modal`)
* [`docs/padroes-interface-botoes.md`](../padroes-interface-botoes.md) (Guia Prático de Componentes de Botão)
