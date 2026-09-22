# Guia de Sincronização Automática com o Google Apps Script

> **Projeto:** Alocação Plus (EESC-USP)  
> **Ferramenta:** [`tools/gas_sync.py`](../tools/gas_sync.py)  
> **Protocolo:** Google Apps Script REST API v1  

---

## 1. Visão Geral

Este guia descreve como sincronizar o código-fonte local presente na pasta `src/` diretamente com os servidores do **Google Apps Script**, utilizando o script nativo em Python [`tools/gas_sync.py`](../tools/gas_sync.py).

O sincronizador permite trabalhar localmente no seu editor favorito (VS Code, Cursor, PyCharm, etc.), com destaque de sintaxe, extensões e Git, enquanto as alterações são enviadas para a nuvem **automaticamente a cada salvamento (`Ctrl + S`)**.

---

## 2. Pré-requisitos da Conta Google (Configuração Única)

Para permitir que scripts locais enviem código para o Google Apps Script em nome da sua conta, o Google exige duas etapas de liberação de segurança:

### Passo 2.1: Ativar a API no seu Usuário
1. Acesse: [script.google.com/home/usersettings](https://script.google.com/home/usersettings)
2. No item **Google Apps Script API**, alterne a chave para **Ativada (ON)**.

---

### Passo 2.2: Criar as Credenciais OAuth 2.0 (Google Cloud Console)
1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um novo projeto ou selecione um projeto existente (ex: *"Alocacao Plus EESC"*).
3. No menu lateral, acesse **APIs e Serviços** > **Biblioteca**:
   * Pesquise por **Google Apps Script API** e clique em **Ativar**.
4. No menu lateral, acesse **APIs e Serviços** > **Tela de permissão OAuth**:
   * Escolha o tipo de usuário: **Externo** (ou **Interno** caso esteja usando e-mail institucional `@usp.br` do Google Workspace).
   * Preencha o nome do aplicativo (ex: *"Alocação Plus Sync"*) e informe seu e-mail para suporte.
   * Clique em **Salvar e Continuar** até finalizar.
5. No menu lateral, acesse **APIs e Serviços** > **Credenciais**:
   * Clique em **+ Criar Credenciais** > **ID do cliente OAuth**.
   * Em **Tipo de aplicativo**, selecione: **Aplicativo para computador** (*Desktop App*).
   * Dê um nome (ex: *"Sincronizador Desktop"*) e clique em **Criar**.
6. Na janela que se abrir, clique em **Fazer download do JSON** (ícone de seta para baixo).
7. Renomeie o arquivo baixado para **`credentials.json`** e salve-o na raiz do projeto `alocacao-plus/` (ou dentro da pasta `tools/`).

> [!NOTE]
> O arquivo `credentials.json` já está registrado no [`.gitignore`](../.gitignore), garantindo que suas chaves secretas nunca sejam enviadas para o repositório Git.

---

## 3. Como Obter o Script ID do Projeto

O **Script ID** é o identificador único do seu projeto na nuvem do Google:

1. Abra a planilha vinculada ao Alocação Plus no Google Sheets.
2. Acesse o menu superior: **Extensões** > **Apps Script** (ou acesse diretamente pelo [script.google.com](https://script.google.com/)).
3. No menu lateral esquerdo do editor do Apps Script, clique no ícone de engrenagem ⚙️ (**Configurações do projeto**).
4. Localize a seção **IDs** e copie o conteúdo do campo **Script ID** (uma sequência longa alfanumérica, por exemplo: `1ZSa4RmZm0GSiAPrHwE1M1cB1vzI1hdg30bGkTA-R66U...`).

---

## 4. Configuração Inicial do Projeto

Com o Script ID em mãos, abra o terminal no diretório do projeto e execute:

```powershell
python tools/gas_sync.py init <SEU_SCRIPT_ID>
```

* O Script ID será gravado no arquivo de configuração local `.gas-config.json` (também protegido pelo `.gitignore`).
* Você só precisa fazer isso **uma única vez**.

---

## 5. Fluxo de Trabalho no Dia a Dia

### 5.1. Modo Automático em Tempo Real (`watch`) — **Recomendado**

Para desenvolver com sincronização instantânea em segundo plano:

```powershell
python tools/gas_sync.py watch
```

**Como opera:**
1. O script realiza uma primeira sincronização completa para garantir que a nuvem está atualizada.
2. Em seguida, entra em modo monitor (*polling* de 1 segundo sobre a pasta `src/`).
3. Toda vez que você salvar qualquer arquivo (`alocacao-plus.gs`, `index.html`, `estilos.html`, etc.), ele detecta a alteração e atualiza **apenas o arquivo modificado** na nuvem, preservando todos os demais inalterados:
   ```text
   [13:58:00] ✏️  Alteração detectada: alocacao-plus.gs
   [13:58:01] 🚀 Atualizando no Apps Script: alocacao-plus.gs...
   [13:58:03] ✅ Atualizado com sucesso no Apps Script:
      📝 alocacao-plus
   ```
4. Pressione `Ctrl + C` no terminal quando desejar interromper o monitoramento.

---

### 5.2. Envio Manual Sob Demanda (`push`)

Você pode enviar todos os arquivos de uma vez ou atualizar **apenas um arquivo específico**:

```powershell
# Envio completo de todos os arquivos
python tools/gas_sync.py push

# Envio seletivo de apenas um arquivo alterado
python tools/gas_sync.py push alocacao-plus.gs
python tools/gas_sync.py push index.html
```

---

### 5.3. Baixar Alterações da Nuvem (`pull`)

Se você ou outro membro da equipe fizer edições diretamente pelo editor web do Google Apps Script e você desejar trazer essas mudanças para o seu computador:

```powershell
python tools/gas_sync.py pull
```

* Esse comando sobrescreve os arquivos em `src/` com o conteúdo exato que está rodando na nuvem.

---

### 5.4. Consultar Status e Auditoria (`status`)

Para verificar quais arquivos estão na nuvem, data da última alteração e título do projeto:

```powershell
python tools/gas_sync.py status
```

---

### 5.5. Controle de Versão e Compilação (`version` e `bump`)

O projeto implementa **Versionamento Semântico (SemVer)** com **Contador de Build Automático**:

1. **Como consultar a versão atual:**
   ```powershell
   python tools/gas_sync.py version
   ```

2. **Como funciona o incremento automático no `watch`:**
   - Durante o desenvolvimento diário, toda vez que um arquivo de `src/` for modificado e salvo (`Ctrl + S`), o `gas_sync.py watch` incrementa o contador de **`build`** (ex: `v0.1.3 (build 1)`, `v0.1.3 (build 2)`).
   - O arquivo `src/version.gs` é regravado e enviado automaticamente junto com o código.
   - O `watch` possui proteção integrada contra loops infinitos: alterações geradas pelo próprio versionador não re-disparam eventos em cascata.

3. **Como promover uma versão formal (`bump`):**
   Quando você terminar um conjunto de correções ou uma funcionalidade e quiser subir a versão oficial (o contador de build é resetado automaticamente para 0):
   ```powershell
   # Correção de bugs / ajustes finos:
   python tools/gas_sync.py bump patch    # Ex: v0.1.3 -> v0.1.4

   # Novas funcionalidades compatíveis:
   python tools/gas_sync.py bump minor    # Ex: v0.1.3 -> v0.2.0

   # Lançamento estável / grandes marcos:
   python tools/gas_sync.py bump major    # Ex: v0.1.3 -> v1.0.0

   # Versão customizada arbitrária:
   python tools/gas_sync.py bump 0.3.0
   ```

4. **Exibição na Interface:**
   No rodapé do Web App (`src/index.html`), o scriptlet `<?= APP_FULL_VERSION ?>` exibe em tempo real o badge de versão ativo (ex: `v0.1.3 (build 14)`), permitindo que você e os usuários saibam exatamente qual compilação está em execução no navegador.

---

## 6. Mapeamento de Arquivos Local $\leftrightarrow$ Nuvem

O Google Apps Script trata arquivos sem extensão e com tipos formais. O `gas_sync.py` realiza essa tradução de forma transparente:

| Arquivo Local (`src/`) | Nome no Apps Script | Tipo na API do Google | Descrição |
| :--- | :--- | :--- | :--- |
| `src/appsscript.json` | `appsscript` | `JSON` | Manifesto de configuração do Apps Script |
| `src/alocacao-plus.gs` | `alocacao-plus` | `SERVER_JS` | Backend, parsing da planilha e cache |
| `src/config.gs` | `config` | `SERVER_JS` | Gestão de configurações e aba `_Config` |
| `src/version.gs` | `version` | `SERVER_JS` | Constantes de versão geradas pelo Python |
| `src/index.html` | `index` | `HTML` | Estrutura semântica da interface Web App |
| `src/estilos.html` | `estilos` | `HTML` | Design System e estilos modulares |
| `src/scripts.html` | `scripts` | `HTML` | Scripts do cliente e reatividade |

---

## 7. Resolução de Problemas Comuns

### Erro: `HttpError 403: "Google Apps Script API has not been used in project..."`
* **Causa:** A API não foi ativada no projeto do Google Cloud.
* **Solução:** Acesse a [Biblioteca do Google Cloud Console](https://console.cloud.google.com/apis/library/script.googleapis.com) e clique em **Ativar**.

### Erro: `HttpError 403: "User has not enabled the Apps Script API..."`
* **Causa:** A chave geral do usuário está desligada.
* **Solução:** Acesse [script.google.com/home/usersettings](https://script.google.com/home/usersettings) e ative a opção **Google Apps Script API**.

### Erro: `HttpError 404: "Requested entity was not found"`
* **Causa:** O Script ID informado está incorreto ou sua conta Google não possui permissão de edição sobre o script.
* **Solução:** Reconfira o Script ID em *Configurações do Projeto* no Apps Script e reconfigure com `python tools/gas_sync.py init <ID_CORRETO>`.

### O navegador não abre para login OAuth
* **Causa:** Token expirado ou corrompido.
* **Solução:** Exclua o arquivo `token_gas.json` gerado na raiz e execute o comando novamente para abrir uma nova janela de autorização.
