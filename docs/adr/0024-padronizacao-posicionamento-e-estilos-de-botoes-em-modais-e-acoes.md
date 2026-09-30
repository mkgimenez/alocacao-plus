# 24. Padronização de Posicionamento e Estilos de Botões em Modais e Barras de Ação

* **Data:** 2026-09-30
* **Status:** Substituído parcialmente pelo ADR 0026
* **Decisores:** Equipe Técnica SCAE / EESC-USP

> ⚠️ **Nota de Atualização (ADR 0026):** As diretrizes da Seção 1 (posicionamento de confirmação à esquerda e cancelamento à direita com estilo primário invertido) foram revogadas e corrigidas pelo [ADR 0026](0026-correcao-ergonomia-ux-botoes-modais-confirmacao.md). Em modais de ação/confirmação, `Cancelar` (secundário outline) posiciona-se à esquerda e `Confirmar` (primário sólido institucional) posiciona-se no canto inferior direito terminal.

## Contexto e Problema
Com a expansão contínua da aplicação e a introdução de novos diálogos modais (como o **Modal de Informações da Disciplina** e o **Modal de Preparação e Impressão da Grade**), bem como botões utilitários adicionais na barra superior de ações, tornou-se essencial formalizar uma convenção arquitetural e espacial estrita para o posicionamento e estilização de botões.

Anteriormente, enquanto o Card de Disciplinas posicionava suas ações informativas e operacionais (`Abrir no Jupiterweb`, `Trocar de Sala`, `Filtrar disciplina`) à esquerda/centro e o botão de fechamento (`Fechar`) à direita, novos componentes corriam o risco de inverter essa ordem espacial ou introduzir variantes estilísticas divergentes, quebrando a consistência ergonômica e cognitiva do usuário.

## Decisão Adotada
Fica estabelecida como convenção arquitetural universal e mandatória para todo o sistema **Alocação Plus (EESC-USP)**:

### 1. Regra de Posicionamento Espacial em Modais e Diálogos
* **Lado Direito (Ações Neutras, de Cancelamento e Fechamento):**
  - Botões de fechar, cancelar, voltar ou descartar (`Fechar`, `Cancelar`, `Voltar`) devem **sempre ficar posicionados no lado direito** do rodapé de modais e diálogos.
  - Devem utilizar a classe canônica `.btn-fechar-modal` (estilo sólido institucional com fundo `var(--primary)` e texto branco).
* **Lado Esquerdo ou Centralizado (Ações Positivas, Confirmações e Operações):**
  - Botões de ação positiva, confirmação, submissão ou navegação (`OK`, `Confirmar`, `Imprimir / Salvar PDF`, `Salvar`, `Abrir no Jupiterweb`, `Trocar de Sala`, `Filtrar`) devem **sempre ficar posicionados no lado esquerdo ou centralizados**, conforme a necessidade do leiaute.
  - Devem utilizar o estilo secundário outline padronizado (`.btn-link-externo-jupiter`, `.btn-imprimir-confirmar`), com fundo branco `#ffffff`, texto `var(--primary)` e borda suave `1px solid var(--primary-border)`.

### 2. Regra de Estilização de Botões na Barra de Ações Rápidas
* Botões operacionais complementares situados na barra superior de ações (como o botão `🖨️ Imprimir Grade`) devem **compartilhar a mesma formatação visual e tátil do botão `🧹 Limpar Filtros`** (`.btn-reset`, `.btn-imprimir-grade`):
  - Fundo neutro claro `#f1f5f9`;
  - Texto `#475569`;
  - Borda discreta `1px solid var(--border-dark)`;
  - Padding uniforme `6px 12px`, tipografia de 12px com peso 600;
  - Micro-animações táteis no hover (`translateY(-1px)`, sombra suave) e active (`scale(0.96)`).

### 3. Responsividade em Dispositivos Móveis
* Em viewports estreitos (`<= 540px`), os rodapés de modais preservam a convenção adotando `flex-direction: column-reverse`, garantindo que a ação de fechamento permaneça no topo ou de fácil alcance táctil com largura de 100%.

## Consequências
### Positivas (+)
* **Previsibilidade Cognitiva Máxima:** O usuário sabe instantaneamente que o canto direito inferior é o ponto seguro de fuga/fechamento, enquanto o lado esquerdo abriga as ações de prosseguimento e confirmação.
* **Harmonia Visual:** A barra de ações da grade e os rodapés de modais possuem ritmo estético simétrico e integrado ao Design System do projeto.
* **Manutenibilidade:** Elimina debates de leiaute em novas features — a regra de disposição espacial e hierarquia de classes é única e auditável.

### Negativas / Trade-offs (-)
* Exige que novos diálogos ou telas mantenham estrita disciplina sem alterar a ordem dos elementos filhos no flexbox.

## Referências no Código
* [`src/index.html`](../../src/index.html) (Rodapé de `#modal-card-disciplina` e `#modal-impressao-grade`)
* [`src/estilos.html`](../../src/estilos.html) (Seletores `.btn-reset`, `.btn-imprimir-grade`, `.btn-link-externo-jupiter`, `.btn-imprimir-confirmar`, `.btn-fechar-modal`)
* [`docs/padroes-interface-botoes.md`](../padroes-interface-botoes.md)
