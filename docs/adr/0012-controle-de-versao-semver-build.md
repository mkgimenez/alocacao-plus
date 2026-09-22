# 12. Controle de Versão Semântico (SemVer) e Contador de Build Automático

* **Data:** 2026-09-22
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
Anteriormente, o controle de versão do **Alocação Plus** estava registrado apenas de forma manual nas descrições de implantação (*deployments*) do Google Apps Script (iniciando em `v0.1.3`). Não existia registro programático no código-fonte, nos arquivos do repositório ou na interface gráfica acessada pelos usuários.

Com a adoção do sincronizador em tempo real `tools/gas_sync.py watch`, surgiu a necessidade de:
1. Armazenar a versão oficial de forma persistente e rastreável localmente.
2. Incrementar a versão de desenvolvimento de maneira automatizada a cada salvamento (`Ctrl + S`).
3. Fornecer um controle claro para que o desenvolvedor decida quando uma iteração deixa de ser apenas uma compilação de teste (*build*) e se torna uma nova versão estável (*patch*, *minor* ou *major*).
4. Exibir a versão exata no rodapé do Web App para facilitar diagnóstico e suporte.

## Alternativas Consideradas
* **Incremento do Patch a Cada Salvamento no Watch (`v0.1.3` ➔ `v0.1.4` ➔ `v0.1.5`...):** Descartado porque durante uma tarde comum de desenvolvimento são realizados dezenas ou centenas de salvamentos para ajustes finos de CSS e lógica, o que causaria inflação artificial da numeração e perda do significado semântico do *patch*.
* **Armazenamento Apenas em `PropertiesService` ou Planilha:** Descartado por depender de leitura em tempo de execução na nuvem, introduzindo latência ou dependência de rede, além de não ficar versionado junto aos arquivos locais do projeto.
* **Abordagem SemVer + Build Automático com `version.json` e `version.gs` (Escolhida):** Arquivo de metadados na raiz (`version.json`) como fonte da verdade, geração automática de scriptlet no Apps Script (`src/version.gs`), incremento de build automático no `watch` e comandos dedicados (`bump patch|minor|major`) para promoção de versão.

## Decisão Adotada
Implementar o sistema de versionamento híbrido **SemVer + Build Automático**:
1. **Estrutura de Armazenamento:**
   * **`version.json` (Raiz):** Mantém os números semânticos (`major`, `minor`, `patch`), o contador cumulativo `build`, a versão formatada e a data/hora da última sincronização.
   * **`src/version.gs` (Apps Script):** Gerado automaticamente pelo Python a cada alteração ou sincronização, exportando as constantes `APP_VERSION`, `APP_BUILD`, `APP_BUILD_TIME` e `APP_FULL_VERSION`.
2. **Ciclo de Desenvolvimento com `gas_sync.py watch`:**
   * A cada alteração em `src/`, o watcher incrementa o `build` (ex: `v0.1.3 (build 1)` ➔ `v0.1.3 (build 2)`).
   * O watcher inclui proteção contra loop infinito, garantindo que a própria regravação de `src/version.gs` não cause novos disparos em cascata.
3. **Promoção de Versão via CLI (`bump`):**
   * `python tools/gas_sync.py bump patch`: Incrementa patch (ex: `v0.1.3` ➔ `v0.1.4`) e reseta `build` para 0.
   * `python tools/gas_sync.py bump minor`: Incrementa minor (ex: `v0.1.3` ➔ `v0.2.0`) e reseta `build` para 0.
   * `python tools/gas_sync.py bump major`: Incrementa major (ex: `v0.1.3` ➔ `v1.0.0`) e reseta `build` para 0.
   * `python tools/gas_sync.py bump <versao>`: Permite definir qualquer versão arbitrária.
   * `python tools/gas_sync.py version`: Consulta o status atual de versão no terminal.
4. **Renderização no Frontend:**
   * O rodapé de `src/index.html` renderiza nativamente `<?= APP_FULL_VERSION ?>` com estilização discreta em pill badge (`.badge-versao`), assegurando total transparência para os usuários.

## Consequências
### Positivas (+)
* **Rastreabilidade Total:** Qualquer usuário ou administrador sabe exatamente qual build está rodando em tela.
* **Sem Poluição Semântica:** A numeração principal só sobe mediante ação intencional (`bump`), enquanto o `build` acompanha o ritmo ágil de salvamentos do `watch`.
* **Zero Overhead de Runtime:** As constantes são injetadas estaticamente pelo compilador/sincronizador Python diretamente no Apps Script antes do envio.
* **Independência de Conexão:** Comandos como `bump` e `version` funcionam localmente de imediato sem necessidade de chamadas de rede ou login prévio.

### Negativas / Trade-offs (-)
* O arquivo `src/version.gs` não deve ser editado manualmente, pois qualquer modificação é sobrescrita pelo sincronizador `gas_sync.py`.

## Referências no Código
* [version.json](../../version.json)
* [src/version.gs](../../src/version.gs)
* [tools/gas_sync.py](../../tools/gas_sync.py)
* [src/index.html](../../src/index.html)
* [docs/sincronizacao-apps-script.md](../sincronizacao-apps-script.md)
