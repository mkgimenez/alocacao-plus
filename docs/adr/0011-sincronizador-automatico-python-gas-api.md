# 11. Sincronizador Automático em Python via Apps Script REST API

* **Data:** 2026-09-22
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
Com o código-fonte isolado na pasta `src/` e padronizado em formato Git, surgiu a necessidade de manter o projeto sincronizado automaticamente com os servidores do Google Apps Script na nuvem.

Embora a ferramenta oficial do Google seja o Clasp (`@google/clasp`), sua utilização exige o ecossistema Node.js/npm, o qual não estava instalado no ambiente da máquina local. Por outro lado, o ambiente já contava nativamente com **Python 3.13** e a biblioteca oficial [`google-api-python-client`](https://github.com/googleapis/google-api-python-client) configurada.

O objetivo era viabilizar uma sincronização automática e em tempo real (modo *watch*) sem a obrigatoriedade de instalar softwares adicionais de terceiros.

## Alternativas Consideradas
* **Cópia e Colagem Manual:** Inviável no fluxo ágil de desenvolvimento; propenso a esquecimentos de atualização em arquivos parciais (`scripts.html`, `estilos.html`).
* **Instalação Obrigatória do Node.js e Clasp:** Adicionaria um runtime extra à máquina para cumprir uma função realizável via Python.
* **Script Utilitário Nativo em Python (`tools/gas_sync.py`):** Utilizar a API REST oficial do Google Apps Script (`projects.updateContent` e `projects.getContent`) em Python, implementando um monitor de arquivos com debounce em tempo real.

## Decisão Adotada
Criar o utilitário [`tools/gas_sync.py`](../../tools/gas_sync.py) baseado na **Google Apps Script REST API v1**:
1. **Comandos Suportados:**
   * `init <SCRIPT_ID>`: Salva o Script ID localmente em `.gas-config.json` (ignorado no Git).
   * `push`: Converte todos os arquivos de `src/` (`.gs` $\rightarrow$ `SERVER_JS`, `.html` $\rightarrow$ `HTML`, `appsscript.json` $\rightarrow$ `JSON`) e atualiza o projeto remoto de forma atômica.
   * `pull`: Baixa os arquivos do Apps Script na nuvem para a pasta local `src/`.
   * `watch`: Monitora alterações em `src/` calculando hashes MD5 dos arquivos a cada 1 segundo. Ao detectar um salvamento (`Ctrl + S`), aguarda 500ms (debounce) e dispara o `push` automaticamente.
   * `status`: Exibe título, data de criação e lista de arquivos remotos.
2. **Segurança e Autenticação:**
   * Utiliza OAuth 2.0 padrão via `google-auth-oauthlib`.
   * Credenciais (`credentials.json`), tokens gerados (`token_gas.json`) e configurações de ID (`.gas-config.json`) são protegidos pelo [`.gitignore`](../../.gitignore).

## Consequências
### Positivas (+)
* **Zero Softwares Extras:** Aproveita 100% o ambiente Python 3.13 já instalado no computador.
* **Feedback Instantâneo:** Edições salvas no VS Code ou qualquer editor sobem para o Google Apps Script em menos de 2 segundos.
* **Bidirecionalidade:** Suporta `push` e `pull`, permitindo recuperar alterações feitas eventualmente pelo editor web do Google.

### Negativas / Trade-offs (-)
* Requer que a conta Google tenha o arquivo `credentials.json` (ID do cliente OAuth) e que a opção "Google Apps Script API" esteja ativada no painel de configurações do Apps Script.

## Referências no Código
* [tools/gas_sync.py](../../tools/gas_sync.py)
* [docs/sincronizacao-apps-script.md](../sincronizacao-apps-script.md)
* [.gitignore](../../.gitignore)
