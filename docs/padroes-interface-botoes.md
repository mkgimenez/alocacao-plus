# 🎨 Guia de Padronização de Botões e Micro-Interações ("Efeitos Fofinhos")

Este guia documenta o padrão visual e comportamental de botões do **Alocação Plus**, estabelecendo as regras para manter a consistência estética, tátil e de acessibilidade em novas funcionalidades.

---

## 🧸 O que são os "Efeitos Fofinhos"?

O termo "efeito fofinho" refere-se à sensação tátil suave, física e responsiva gerada pela combinação de:
1. **Transição em Curva de Mola (Spring Physics):** Aceleração natural que evita movimentos mecânicos lineares;
2. **Elevação Suave no Hover (`translateY(-1px)`):** O botão parece levitar discretamente quando o cursor se aproxima;
3. **Sombras Difusas Aconchegantes:** Projeção sutil de sombra com o tom azul institucional (`rgba(16, 72, 128, ...)`);
4. **Afundamento Mecânico no Clique (`scale(0.96)` ou `scale(0.95)`):** Feedback instantâneo (`0.05s`) ao toque ou clique, imitando o pressionamento de uma tecla real;
5. **Anel de Foco Acessível (`:focus-visible`):** Destaque limpo de foco por teclado sem poluir o clique do mouse.

---

## 📐 O Padrão Universal de Transição (CSS)

Sempre que criar um botão ou elemento clicável semelhante, aplique a regra de transição padrão:

```css
transition: background-color 0.18s cubic-bezier(0.4, 0, 0.2, 1),
            border-color 0.18s cubic-bezier(0.4, 0, 0.2, 1),
            color 0.18s cubic-bezier(0.4, 0, 0.2, 1),
            box-shadow 0.18s cubic-bezier(0.4, 0, 0.2, 1),
            transform 0.12s cubic-bezier(0.34, 1.56, 0.64, 1);
```

E garanta os metadados de toque móvel:
```css
cursor: pointer;
user-select: none;
-webkit-tap-highlight-color: transparent;
touch-action: manipulation;
```

---

## 🏷️ Tipos de Botão no Sistema

### 1. Botão Primário Sólido (`.btn-fechar-modal`)
Utilizado para ações definitivas ou de fechamento principal.

* **Fundo:** `var(--primary)` (#104880)
* **Texto:** `#ffffff`
* **Borda:** `1px solid var(--primary)` *(obrigatório para manter igualdade de altura com botões outline)*
* **Sombra Base:** `0 1px 2px rgba(16, 72, 128, 0.16)`
* **Hover:** `background: var(--primary-hover); border-color: var(--primary-hover); transform: translateY(-1px); box-shadow: 0 3px 6px rgba(16, 72, 128, 0.25);`
* **Active:** `transform: scale(0.96); box-shadow: 0 1px 2px rgba(16, 72, 128, 0.2); transition-duration: 0.05s;`

---

### 2. Botão Secundário / Outline (`.btn-filtrar-disciplina`, `.btn-link-externo-jupiter`, `.btn-primary-outline`)
Utilizado para links externos, filtros ou ações contextuais no card.

* **Fundo:** `#ffffff`
* **Texto:** `var(--primary)` (#104880)
* **Borda:** `1px solid var(--primary-border)` (#bfd6ee)
* **Sombra Base:** `0 1px 2px rgba(16, 72, 128, 0.04)`
* **Hover:** `background: var(--primary-light); border-color: var(--primary); color: var(--primary-hover); transform: translateY(-1px); box-shadow: 0 2px 5px rgba(16, 72, 128, 0.09);`
* **Active:** `transform: scale(0.96); box-shadow: 0 1px 2px rgba(16, 72, 128, 0.12); transition-duration: 0.05s;`

---

### 3. Chips e Pills Selecionáveis (`.chip`, `.chip-sm`, `.btn-pill-turma`)
Utilizados para seleção de opções mutuamente exclusivas ou filtros múltiplos.

#### Estado Repouso (Inativo)
* **Fundo:** `#ffffff`
* **Texto:** `#334155`
* **Borda:** `1px solid var(--border-dark)` (#cbd5e1)
* **Hover:** `background: #f1f5f9; border-color: #94a3b8; color: var(--text-main); transform: translateY(-1px); box-shadow: 0 2px 5px rgba(16, 72, 128, 0.09);`
* **Active:** `transform: scale(0.95); box-shadow: 0 1px 2px rgba(16, 72, 128, 0.12); transition-duration: 0.05s;`

#### Estado Selecionado (`.ativa` ou `.active`)
* **Fundo:** `var(--primary)` (#104880)
* **Texto:** `#ffffff`
* **Borda:** `1px solid var(--primary)`
* **Sombra Base:** `0 2px 4px rgba(16, 72, 128, 0.18)`
* **Hover:** `background: var(--primary-hover); border-color: var(--primary-hover); transform: translateY(-1px); box-shadow: 0 3px 6px rgba(16, 72, 128, 0.25);`
* **Active:** `transform: scale(0.95); box-shadow: 0 1px 2px rgba(16, 72, 128, 0.2); transition-duration: 0.05s;`

---

### 4. Botão de Ícone / Fechar Topo (`.modal-btn-fechar`, `.btn-limpar-busca`)
Botões compactos de utilidade gráfica.

* **Tamanho:** `width: 32px; height: 32px;`
* **Fundo:** `transparent` com `border: 1px solid transparent;`
* **Hover:** `background: #e2e8f0; border-color: #cbd5e1; color: var(--text-main); transform: translateY(-1px); box-shadow: 0 2px 4px rgba(16, 72, 128, 0.08);`
* **Active:** `transform: scale(0.92); box-shadow: none; transition-duration: 0.05s;`

---

## 📏 Regras de Alinhamento e Modelo de Caixa

Para que botões na mesma linha nunca fiquem desalinhados:
1. **Nunca use `border: none`** em botões que dividem linha com botões de borda. Utilize `border: 1px solid var(--primary)` ou `border: 1px solid transparent` para preservar a altura exata.
2. Defina explicitamente `line-height: 1.25;` e `display: inline-flex; align-items: center; justify-content: center;`.
3. Use o raio padrão do sistema: `border-radius: var(--radius-sm);` (6px).

---

## 🧭 Regra Universal de Posicionamento Espacial (Esquerda vs. Direita)

Formalizada no **ADR 0024**, esta diretriz rege o posicionamento de ações em todo o ecossistema do **Alocação Plus**:

1. **Lado Direito — Ações de Saída, Fechamento e Cancelamento:**
   * Botões como `Fechar`, `Cancelar` e similares devem **sempre ficar no lado direito** do rodapé de modais e caixas de diálogo.
   * Empregam a variante sólida institucional `.btn-fechar-modal`.
2. **Lado Esquerdo ou Centralizado — Ações Positivas, Operações e Confirmações:**
   * Botões como `OK`, `Confirmar`, `🖨️ Imprimir / Salvar PDF`, `Abrir no Jupiterweb ↗`, `Trocar de Sala ⇄` e `Filtrar disciplina` devem **ficar posicionados no lado esquerdo ou centralizados**, conforme o fluxo de leitura do leiaute.
   * Empregam a variante outline secundária padronizada (`.btn-link-externo-jupiter`, `.btn-imprimir-confirmar`).
3. **Barra Superior de Ações Rápidas da Grade:**
   * Botões operacionais complementares (`🖨️ Imprimir Grade`) compartilham a mesma formatação visual e tátil do botão `🧹 Limpar Filtros` (`.btn-reset`, `.btn-imprimir-grade`), mantendo harmonia cromática neutra.

---

## ♿ Acessibilidade (Prefers-Reduced-Motion)

Sempre que registrar um novo botão com animações, inclua a classe na regra global de movimento reduzido em [`src/estilos.html`](../src/estilos.html):

```css
@media (prefers-reduced-motion: reduce) {
  .seu-novo-botao {
    transition: none !important;
    transform: none !important;
  }
  .seu-novo-botao:hover,
  .seu-novo-botao:active {
    transform: none !important;
  }
}
```
