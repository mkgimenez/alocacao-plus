# 10. Padronização de Nomenclatura em kebab-case e Padrões Git

* **Data:** 2026-09-22
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
O repositório apresentava uma mescla de diferentes convenções de nomenclatura:
* **PascalCase com sufixos redundantes:** `AlocacaoPlus.gs`, `Config.gs`, `Index.html`, `EstilosCss.html` (sufixo "Css" em arquivo `.html`), `ScriptJs.html` (sufixo "Js" em arquivo `.html`).
* **SCREAMING_SNAKE_CASE:** `ESPECIFICACAO_DISCIPLINAS.md`.
* **snake_case:** `auth_and_test.py`.

No sistema operacional Windows (sistema de arquivos NTFS), os nomes de arquivos são insensíveis a maiúsculas e minúsculas (*case-insensitive*). No entanto, em ambientes Linux, macOS, servidores de CI/CD (ex: GitHub Actions) e no próprio Git, a distinção é estrita (*case-sensitive*).

Além disso, no Google Apps Script, a função `HtmlService.createTemplateFromFile('index')` e os comandos `include('estilos')` dependem da exata correspondência do nome do arquivo no projeto. Inconsistências de capitalização geram quebras súbitas de execução quando o código é clonado ou compilado em plataformas diferentes.

## Alternativas Consideradas
* **Manter Nomes Legados em PascalCase:** Manteria a compatibilidade com scripts antigos, mas perpetuaria a inconsistência estilística e os riscos de *case-sensitivity* entre Windows e Linux.
* **Tudo em camelCase:** Comum em JavaScript, mas atípico para nomes de arquivos em repositórios Git abertos.
* **Padronização em kebab-case / lowercase (Padrão Git/POSIX):** Utilizar minúsculas separadas por hífens para arquivos e diretórios, reservando maiúsculas apenas para marcos canônicos do Git (`README.md`).

## Decisão Adotada
Padronizar todos os nomes de arquivos do projeto seguindo os padrões POSIX e convenções do Git:
1. **Código-Fonte em `src/` (Lowercase e Kebab-case):**
   * `AlocacaoPlus.gs` $\rightarrow$ `alocacao-plus.gs`
   * `Config.gs` $\rightarrow$ `config.gs`
   * `Index.html` $\rightarrow$ `index.html` (padrão universal para arquivos raiz web)
   * `EstilosCss.html` $\rightarrow$ `estilos.html` (remoção da redundância "Css")
   * `ScriptJs.html` $\rightarrow$ `scripts.html` (remoção da redundância "Js")
2. **Atualização das Chamadas Internas no Apps Script:**
   * Em `src/alocacao-plus.gs`: chamada atualizada para `HtmlService.createTemplateFromFile('index')`.
   * Em `src/index.html`: diretivas atualizadas para `<?!= include('estilos'); ?>` e `<?!= include('scripts'); ?>`.
3. **Documentação e Utilitários:**
   * `ESPECIFICACAO_DISCIPLINAS.md` $\rightarrow$ `docs/especificacao-disciplinas.md`
   * ADRs sequenciais: `docs/adr/XXXX-nome-em-kebab-case.md`
   * Scripts Python: mantidos em `snake_case` (`tools/auth_and_test.py`) em conformidade com a PEP 8.
   * Arquivo de entrada do Git: mantido em maiúsculas (`README.md`) para renderização automática na página principal do repositório.

## Consequências
### Positivas (+)
* **Portabilidade Total:** Imunidade a falhas de capitalização entre ambientes de desenvolvimento Windows, Linux e esteiras de integração contínua.
* **Nomenclatura Limpa e Sucinta:** Eliminação de redundâncias como "Css.html" e "Js.html".
* **Conformidade com Ecossistemas Modernos:** Alinhamento com as convenções da comunidade Node.js, Git e Web Standards.

### Negativas / Trade-offs (-)
* Exigiu a refatoração atômica das chamadas `include()` e `createTemplateFromFile()` no código-fonte para evitar erros de template não encontrado.

## Referências no Código
* [src/alocacao-plus.gs](../src/alocacao-plus.gs)
* [src/index.html](../src/index.html)
* [docs/especificacao-disciplinas.md](../especificacao-disciplinas.md)
