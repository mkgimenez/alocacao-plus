# Ferramentas e Utilitários Locais — Alocação Plus

Esta pasta contém scripts de automação, diagnóstico e sincronização para desenvolvimento local do projeto **Alocação Plus (EESC-USP)**.

---

## 🛠️ Scripts Disponíveis

### 1. `gas_sync.py` — Sincronizador Automático com Google Apps Script
Utilitário principal para sincronizar os arquivos da pasta `src/` com a nuvem do Apps Script em tempo real (modo *watch*), sob demanda (*push*) ou no sentido inverso (*pull*).

* **Guia Completo:** Consulte [`docs/sincronizacao-apps-script.md`](../docs/sincronizacao-apps-script.md).
* **Comandos Rápidos:**
  ```powershell
  # 1. Configurar o ID do projeto (apenas na primeira vez)
  python tools/gas_sync.py init <SEU_SCRIPT_ID>

  # 2. Modo monitoramento em tempo real (salvou Ctrl+S, incrementa build e sincroniza!)
  python tools/gas_sync.py watch

  # 3. Consultar versão e build atuais
  python tools/gas_sync.py version

  # 4. Promover versão semântica e resetar build para 0
  python tools/gas_sync.py bump patch    # Correções de bugs (ex: v0.1.3 -> v0.1.4)
  python tools/gas_sync.py bump minor    # Novas funcionalidades (ex: v0.1.3 -> v0.2.0)
  python tools/gas_sync.py bump major    # Grandes versões / estável (ex: v0.1.3 -> v1.0.0)
  python tools/gas_sync.py bump 0.2.5    # Versão manual arbitrária

  # 5. Envio manual sob demanda (push)
  python tools/gas_sync.py push

  # 6. Download da nuvem (pull)
  python tools/gas_sync.py pull

  # 7. Informações do projeto remoto no Apps Script
  python tools/gas_sync.py status
  ```

---

### 2. `auth_and_test.py` — Diagnóstico de Conectividade com Planilhas Google
Script Python utilizando `gspread` e `google-auth` para testar o acesso direto às planilhas Google Sheets:
* Planilha **FONTE** (SVGRAD): `1AxLSuJPAGSZjvg36VaN8-mW9eogsacl2`
* Planilha **PLUS**: `1ZSa4RmZm0GSiAPrHwE1M1cB1vzI1hdg30bGkTA-R66U`

* **Execução:**
  ```powershell
  python tools/auth_and_test.py
  ```

---

## 🔒 Segurança e Credenciais
Os arquivos `credentials.json`, `token*.json` e `.gas-config.json` são estritamente protegidos pelo [`.gitignore`](../.gitignore) e nunca devem ser versionados.
