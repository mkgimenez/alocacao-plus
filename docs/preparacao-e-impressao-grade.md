# Preparação e Impressão Inteligente da Grade Horária — Alocação Plus (EESC-USP)

> **Módulo:** Interface e Exportação Documental  
> **Status:** Implementado e Homologado  
> **Data de Atualização:** 30/09/2026  

---

## 1. Visão Geral

O módulo de **Preparação e Impressão Inteligente da Grade Horária** permite que docentes, funcionários e alunos exportem em PDF ou imprimam diretamente em papel a grade horária exatamente no recorte de salas, dias, horários e filtros visíveis na tela.

O recurso foi projetado com rigor institucional para atender tanto a necessidades de mural acadêmico e relatórios formais quanto a critérios severos de sustentabilidade e economia de tinta/toner.

---

## 2. Arquitetura e Decisões de Design

### 2.1 Quebra da Barreira de SPA (Single Page Application)
Aplicações SPA tradicionais fixam `html, body { height: 100vh; overflow: hidden; }` para manter barras de rolagem internas. No Alocação Plus, a folha de estilo `@media print` efetua um reset completo e em cascata de todos os containers ancestrais (`html`, `body`, `.app-main`, `.grade-section`, `.grade-scroll-wrapper`):
- `overflow: visible !important;`
- `height: auto !important; max-height: none !important;`
- `display: block !important;`

Isso permite que relatórios extensos quebrem naturalmente em múltiplas páginas sem que o navegador corte o conteúdo na primeira folha.

### 2.2 Paginação Automática e Integridade de Linhas
- `thead { display: table-header-group !important; }`: Os cabeçalhos de dias e slots de horários se repetem automaticamente no topo de cada folha impressa.
- `tr { break-inside: avoid !important; page-break-inside: avoid !important; }`: Garante que nenhuma linha de sala seja dividida ou mutilada entre páginas.
- `.tabela-grade { border-collapse: collapse !important; }`: Linhas finas, nítidas e precisas, sem bordas duplas indesejadas no papel.

---

## 3. Paletas e Modos de Impressão

### 3.1 Modo Escala de Cinza (Econômico / Tinta & Toner)
- **Fundo**: Branco puro (`#ffffff`) ou levíssimo cinza neutro (`#f8fafc`).
- **Economia**: Redução superior a 90% no consumo de toner preto em comparação com o fundo escuro do cabeçalho web.
- **Cabeçalhos**: Tons neutros claros (`#f1f5f9` / `#e2e8f0`) com bordas nítidas e tipografia preta (`#000000`).
- **Diferenciação Visual Graduação vs. Pós-Graduação**:
  - **Graduação**: Borda esquerda sólida cinza escura (`3.5px solid #475569`).
  - **Pós-Graduação**: Borda esquerda dupla preta de alto contraste (`4.5px double #0f172a`) acompanhada pelo pseudo-elemento tipográfico `::after { content: " [PÓS]"; }`. Elimina qualquer ambiguidade mesmo em fotocópias monocromáticas de baixa resolução.
  - **Links e Badges**: Fundo transparente, sem sombras ou bordas saturadas, preservando o contraste e a nitidez.

### 3.2 Modo Colorido (Fidelidade Web)
- Preserva a identidade visual institucional: azul céu (`#f0f9ff`) para graduação e azul cobalto (`#eef2ff`) para pós-graduação.
- Ativa a diretiva de calibração `-webkit-print-color-adjust: exact; print-color-adjust: exact;`.
- Proteção automática para células com enriquecimento assíncrono em andamento (`celula-aula-pendente`), garantindo que adquiram a cor de aula correta no documento final.

### 3.3 Modo de Densidade Compacta
- Reduz os paddings de células (de `4px 6px` para `2px 3px`) e tipografia (de `11px` para `8.5px - 9px`), além de otimizar a coluna de sala para `min-width: 80px`.
- Permite acomodar até 35 a 45 salas e mais de 10 horários por folha A4 Paisagem sem corte de texto.

### 3.4 Ocultação da Coluna "Lugares"
- Ao marcar esta opção, a coluna de capacidade (`.col-fixa-cap`) é completamente ocultada (`display: none !important;`), liberando 60px preciosos de espaço horizontal para os códigos e turmas.

---

## 4. Cabeçalho Institucional Oficial para Impressão

Inserido no elemento `#cabecalho-impressao-papel` e visível exclusivamente na impressão (`.apenas-impressao`), o cabeçalho compõe:
1. **Identificação Institucional**:
   - `UNIVERSIDADE DE SÃO PAULO`
   - `ESCOLA DE ENGENHARIA DE SÃO CARLOS — EESC`
   - `Alocação Plus — Grade Horária e Ocupação de Salas`
2. **Carimbo Temporal e Versão**:
   - Data e hora de emissão no fuso oficial (Horário de Brasília): `Emitido em DD/MM/AAAA às HH:mm`.
   - Versão do sistema (`Alocação Plus vX.Y.Z`).
3. **Resumo Dinâmico dos Filtros Ativos**:
   - Compilação dos critérios selecionados pelo usuário (dias, faixas de horários, blocos, salas específicas, capacidade mínima, modo salas livres, termos de busca e contadores de salas e horários).
   - Opcionalmente desmarcável no modal de pré-impressão (`chk-print-cabecalho`).

---

## 5. Neutralização de Destaques Temporais e de Interação

Na folha de papel ou no PDF, todos os destaques de tempo real ou interação são estritamente removidos:
- **Ícones de Tempo (`⚡`)**: Encapsulados em `<span class="icone-tempo-grade">` e ocultados em `@media print`.
- **Cabeçalhos do Dia e Slot Vigentes**: As classes `.dia-hoje-atual` e `.col-slot-atual` perdem o fundo amarelo e bordas douradas, reassumindo as cores padrão dos demais cabeçalhos.
- **Destaque da Busca Textual**: A classe `.celula-destacada-busca` tem seu fundo amarelo e bordas removidos.
- **Célula Clicada Recente**: A classe `.celula-ativa-modal` perde a borda amarela de foco.

---

## 6. Atalhos de Teclado e Ciclo de Vida do DOM

- **`Ctrl + P` / `Cmd + P`**: Interceptado globalmente para abrir o **Modal de Preparação de Impressão** em vez de disparar a impressão crua e desconfigurada do navegador.
- **`Enter` no Modal**: Confirma as opções e dispara `window.print()`.
- **`Escape` no Modal**: Cancela e fecha a janela de configuração.
- **Proteção contra Grade Vazia**: Se não houver salas visíveis com os filtros selecionados, o sistema exibe um Toast informativo e não abre o modal.
- **Alerta de Colunas Inteligente**: Se houver mais de 25 slots de horários ativos, o modal emite um aviso orientando o usuário a ajustar a escala na pré-visualização de impressão (ex: 70-80%) ou filtrar menos dias.
- **Restauração Transparente**: O listener `window.onafterprint` limpa atomicamente todas as classes do `body` (`modo-impressao-ativo`, `impressao-grayscale`, `impressao-compacta`, etc.) sem recarregar a página e sem alterar a seleção de filtros ou busca.

---

## 7. Cobertura de Testes Automatizados

O módulo é 100% testado pela suíte automatizada `tests/test_print_logic.py`, integrada ao executor central `tests/run_all_tests.py`:
- Validação de isolamento semântico do ícone de raio.
- Validação estrutural do cabeçalho institucional em `src/index.html`.
- Testes unitários da compilação de resumo de filtros para todos os cenários possíveis.
- Property-based fuzzing com 300 variações aleatórias de filtros garantindo 0 exceções.
- Testes sintáticos das regras fundamentais de `@media print`, resets de SPA e classes de controle.
- Simulação do ciclo de vida, restauração de classes do `body` e atalhos de teclado.
- Conformidade estrutural e de posicionamento espacial dos botões conforme o [ADR 0024](adr/0024-padronizacao-posicionamento-e-estilos-de-botoes-em-modais-e-acoes.md).

---

## 8. Padronização de Interface e Botões (ADR 0024)

Em estrita consonância com o [ADR 0024](adr/0024-padronizacao-posicionamento-e-estilos-de-botoes-em-modais-e-acoes.md):
- **Botão de Disparo**: O botão `🖨️ Imprimir Grade` na barra de ações compartilha a classe `.btn-reset` (`.btn-imprimir-grade`), mantendo harmonia com o botão de limpar filtros.
- **Rodapé do Modal de Configuração**:
  - `🖨️ Imprimir / Salvar PDF` posicionado no canto **esquerdo** com a classe `.btn-link-externo-jupiter` (`.btn-imprimir-confirmar`).
  - `Cancelar` posicionado no canto **direito** com a classe `.btn-fechar-modal`.

