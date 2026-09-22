# 💡 Alocação Plus — EESC-USP

> **Sistema Inteligente de Consulta de Horários e Ocupação de Salas**  
> *Escola de Engenharia de São Carlos — Universidade de São Paulo*

[![Google Apps Script](https://img.shields.io/badge/Google%20Apps%20Script-4285F4?logo=google&logoColor=white)](https://developers.google.com/apps-script)
[![EESC USP](https://img.shields.io/badge/EESC-USP-104880)](https://eesc.usp.br)
[![Status](https://img.shields.io/badge/Status-Produ%C3%A7%C3%A3o-success)]()

---

## 📖 Visão Geral

O **Alocação Plus** é uma aplicação web autônoma projetada para modernizar e acelerar a consulta da grade horária e a ocupação de salas de aula na **EESC-USP**. Conectando-se de forma dinâmica à planilha oficial mantida pelo **SVGRAD** (Serviço de Graduação), o sistema consolida dados em tempo real, preserva mesclagens de horário e provê uma experiência de busca instantânea tanto para computadores quanto para dispositivos móveis.

---

## 🚀 Principais Recursos

- **⚡ Desempenho Instantâneo:** Resposta em milissegundos através de caching multinível particionado (*chunking*) no `CacheService`.
- **🎯 Filtragem Multicritério Reativa:**
  - **Dias da Semana:** Visualização completa ou foco rápido no dia atual (*"Focar em Hoje"*).
  - **Horários Flexíveis:** Faixas horárias customizadas, atalho *"Agora"* (horário corrente) ou qualquer horário.
  - **Blocos e Salas:** Reconhecimento automático dos blocos didáticos (`Bloco A`, `Bloco C`, `Laranja`, `Anfiteatros`, etc.).
  - **Capacidade Mínima:** Filtros numéricos e atalhos rápidos (`30+`, `50+`, `80+` lugares).
  - **🚪 Modo Salas Livres:** Identifica instantaneamente quais salas estão desocupadas no intervalo selecionado.
- **🔍 Busca Inteligente:** Pesquisa por código de disciplina, nome de docente ou termos livres, com alternância de foco em colunas com resultado.
- **🔗 Integração com Portais Acadêmicos da USP:**
  - **Graduação:** Hiperlinks automáticos para turmas no [Jupiterweb](https://uspdigital.usp.br/jupiterweb/).
  - **Pós-Graduação:** Hiperlinks diretos para o sistema [Janus](https://uspdigital.usp.br/janus/).
- **⚙️ Parametrização sem Código:** A equipe acadêmica pode alternar IDs de planilhas e tempos de cache via aba `_Config` sem tocar no código-fonte.

---

## 📁 Estrutura do Repositório

O projeto segue as convenções modernas de versionamento Git e isolamento de código do Google Apps Script:

```
alocacao-plus/
├── .gitignore                     # Proteção de tokens, credenciais e caches
├── README.md                      # Documentação central do projeto
├── version.json                   # Fonte da verdade do versionamento (SemVer + Build)
│
├── src/                           # Código-fonte executado no Google Apps Script
│   ├── alocacao-plus.gs           # Backend, endpoints, parsing de matriz e cache
│   ├── config.gs                  # Gestão de parâmetros e criação da aba _Config
│   ├── version.gs                 # Constantes de versão geradas automaticamente
│   ├── index.html                 # Estrutura semântica da interface Web App
│   ├── estilos.html               # Folhas de estilo modulares (Design System EESC)
│   ├── scripts.html               # Estado reativo e manipulação DOM no cliente
│   └── appsscript.json            # Manifesto de configuração do Apps Script (V8)
│
├── docs/                          # Documentação e especificações de regras de negócio
│   ├── especificacao-disciplinas.md # Gramática de códigos de turmas e cores oficiais
│   ├── sincronizacao-apps-script.md # Guia completo do sincronizador e versionamento
│   └── adr/                       # Architectural Decision Records (ADRs)
│       ├── README.md              # Índice cronológico e template de decisões
│       └── 0001-*.md              # Registros de decisões técnicas individuais
│
├── tools/                         # Utilitários locais de diagnóstico e automação
│   ├── gas_sync.py                # Sincronizador Apps Script REST API v1 e CLI de versão
│   └── auth_and_test.py           # Script Python para teste de acesso OAuth às planilhas
│
└── assets/                        # Identidade visual institucional e logotipos EESC
```

---

## 🛠️ Instalação e Implantação

### Opção 1: Via Google Apps Script Web Editor (Manual)

1. Abra a planilha do Google Sheets onde o Plus será implantado.
2. Acesse **Extensões** > **Apps Script**.
3. Crie os arquivos correspondentes na pasta `src/`:
   - `alocacao-plus.gs` e `config.gs` (como arquivos de script).
   - `index.html`, `estilos.html` e `scripts.html` (como arquivos HTML).
   - Ajuste o `appsscript.json` nas configurações do projeto caso necessário.
4. Clique em **Implantar** > **Nova Implantação**.
5. Selecione **Tipo:** `Aplicativo da Web`:
   - **Executar como:** `Eu` (sua conta).
   - **Quem tem acesso:** `Qualquer pessoa` (ou `Qualquer pessoa na USP`).
6. Copie a URL gerada e compartilhe com a comunidade acadêmica.

### Opção 2: Sincronização Automática e Versionamento via Python (Push, Watch & Bump) ⚡

Utilize o utilitário nativo [`tools/gas_sync.py`](tools/gas_sync.py) que aproveita seu ambiente Python:

> 📘 **Manual Completo:** Para o passo a passo de como obter o `credentials.json` no Google Cloud Console e o ciclo de versionamento, consulte o [**Guia de Sincronização Automática**](docs/sincronizacao-apps-script.md).

1. **Vincule seu projeto do Apps Script:**
   ```bash
   python tools/gas_sync.py init <SEU_SCRIPT_ID>
   ```
   *(O Script ID pode ser copiado em: Editor do Apps Script > ⚙️ Configurações do projeto > Script ID)*

2. **Modo Automático com Incremento de Build (Watch):**
   ```bash
   python tools/gas_sync.py watch
   ```
   *Qualquer alteração salva em `src/` (`Ctrl + S`) é detectada, incrementa o contador de **build** (ex: `v0.1.3 (build 1)` ➔ `(build 2)`), regenera `src/version.gs` e sincroniza em menos de 2 segundos!*

3. **Controle e Promoção de Versão (SemVer):**
   ```bash
   python tools/gas_sync.py version       # Consulta a versão e build atuais
   python tools/gas_sync.py bump patch    # Correção de bug: v0.1.3 ➔ v0.1.4 (build reseta para 0)
   python tools/gas_sync.py bump minor    # Nova feature:   v0.1.3 ➔ v0.2.0 (build reseta para 0)
   python tools/gas_sync.py bump major    # Grande versão:  v0.1.3 ➔ v1.0.0 (build reseta para 0)
   ```

4. **Envio sob demanda:**
   ```bash
   python tools/gas_sync.py push
   ```

### Opção 3: Via Google Clasp (Node.js)

1. Instale o Clasp globalmente:
   ```bash
   npm install -g @google/clasp
   ```
2. Realize login com sua conta Google:
   ```bash
   clasp login
   ```
3. Vincule o repositório local ao projeto Apps Script (`.clasp.json`):
   ```json
   {
     "scriptId": "SEU_SCRIPT_ID_AQUI",
     "rootDir": "./src"
   }
   ```
4. Envie as alterações ou ative o monitoramento:
   ```bash
   clasp push --watch
   ```

---

## 🏛️ Decisões de Arquitetura (ADR)

As decisões de engenharia, restrições superadas da plataforma Google e compensações técnicas (*trade-offs*) estão documentadas na pasta [`docs/adr/`](docs/adr/README.md).

Consulte os registros para entender o histórico da migração da Sidebar para Web App, a estratégia de particionamento de cache para superar o limite de 100KB do Apps Script, a gramática de disciplinas e muito mais.

---

## 📄 Licença e Créditos

Desenvolvido para a **Escola de Engenharia de São Carlos (EESC-USP)**.  
Integração de dados com o Serviço de Graduação (**SVGRAD**).
