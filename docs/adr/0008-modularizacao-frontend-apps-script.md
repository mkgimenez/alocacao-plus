# 8. Modularização do Frontend no Apps Script com include()

* **Data:** 2026-09-21
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
Aplicações Web construídas sobre o Google Apps Script (`HtmlService`) possuem uma idiossincrasia histórica: a plataforma não oferece nativamente suporte a módulos ES6 (`import`/`export`), empacotadores modernos (Webpack/Vite) ou servidores de arquivos estáticos separados para CSS e JS.

Por essa razão, muitos projetos em Apps Script acabam condensando todo o código em um único arquivo monolítico `Index.html`, contendo milhares de linhas misturando tags HTML, blocos de estilo CSS e lógica de script.

No **Alocação Plus**, a interface possui alta complexidade:
* **HTML:** Estrutura semântica de cards, cabeçalho, tabelas responsivas e toasts (~225 linhas).
* **CSS:** Folhas de estilo completas, tokens de cores institucionais EESC-USP, animações, estados de loading e regras responsivas (~700 linhas).
* **JavaScript:** Gerenciamento de estado reativo, matriz de horário, filtros temporais e manipulação de DOM (~1200 linhas).

Concentrar esse ecossistema em um único arquivo tornaria a manutenção insustentável, inviabilizaria revisões de código (*code review*) no Git e multiplicaria conflitos de merge.

## Alternativas Consideradas
* **Arquivo Monolítico Único (`Index.html`):** Risco crítico de manutenibilidade e baixa legibilidade.
* **Compilador Externo (Babel + Webpack/Rollup):** Embora viável, adiciona uma esteira complexa de build com `node_modules`, scripts de empacotamento e curva de aprendizado para novos colaboradores da universidade.
* **Padrão Oficial de Inclusão Parcial (`HtmlService` + `include`):** Padrão recomendado pela documentação do Google Apps Script, permitindo arquivos separados unidos no momento da renderização pelo motor de templates.

## Decisão Adotada
Adotar o padrão de modularização nativo do Apps Script através da função auxiliar `include()`:
1. **Função Helper no Backend (`src/alocacao-plus.gs`):**
   ```javascript
   function include(filename) {
     return HtmlService.createHtmlOutputFromFile(filename).getContent();
   }
   ```
2. **Separação Rígida de Responsabilidades em `src/`:**
   * **`index.html`:** Apenas marcação HTML semântica e esqueleto visual.
   * **`estilos.html`:** Bloco `<style>` isolado com todo o Design System, variáveis CSS e regras de mídia.
   * **`scripts.html`:** Bloco `<script>` isolado com o estado global, comunicação com o backend e manipuladores de eventos.
3. **Inclusão Dinâmica via Sintaxe de Template Não-Escapada:**
   * No cabeçalho de `index.html`: `<?!= include('estilos'); ?>`
   * No rodapé de `index.html`: `<?!= include('scripts'); ?>`
4. **Avaliação na Inicialização (`doGet`):**
   * O método `HtmlService.createTemplateFromFile('index').evaluate()` processa as diretivas `<?!= ... ?>` do servidor e entrega ao navegador um documento final limpo e unificado.

## Consequências
### Positivas (+)
* **Separação Limpa de Preocupações:** Permite editar estilos visuais sem risco de quebrar a lógica de negócio do JavaScript ou a marcação HTML.
* **Histórico Git Legível:** Commits e diffs isolados (ex: ajustes puramente visuais afetam apenas `src/estilos.html`).
* **Zero Dependências Externas:** Não exige Node.js, empacotadores ou configurações adicionais para funcionar diretamente no editor do Apps Script.

### Negativas / Trade-offs (-)
* Arquivos parciais exigem a presença de tags envolventes `<style>...</style>` e `<script>...</script>` em seus respectivos arquivos `.html`.

## Referências no Código
* [src/alocacao-plus.gs](../src/alocacao-plus.gs) (função `include`, função `doGet`)
* [src/index.html](../src/index.html)
* [src/estilos.html](../src/estilos.html)
* [src/scripts.html](../src/scripts.html)
