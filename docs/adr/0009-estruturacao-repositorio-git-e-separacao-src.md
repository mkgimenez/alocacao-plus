# 9. Estruturação do Repositório Git, Isolamento em /src e Suporte a Clasp

* **Data:** 2026-09-22
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
Inicialmente, todos os arquivos do projeto estavam dispostos na raiz do repositório: scripts `.gs`, templates `.html`, especificações em Markdown (`ESPECIFICACAO_DISCIPLINAS.md`), scripts de teste em Python (`auth_and_test.py`), imagens de alta resolução em `visual/` e pastas locais de backup.

Essa disposição trazia graves inconvenientes:
1. **Poluição do Projeto no Google Apps Script:** Ao sincronizar o repositório com o Apps Script via CLI oficial (`@google/clasp`), todos os arquivos presentes no diretório raiz eram enviados para o editor do Apps Script na nuvem (ou causavam erros de compilação por conterem extensões não suportadas como `.py` ou `.jpg`).
2. **Risco de Segurança (Vazamento de Credenciais):** A ausência de um arquivo `.gitignore` configurado deixava o repositório vulnerável a commits acidentais de arquivos com credenciais OAuth 2.0 (`credentials.json`), tokens de acesso (`token.json`) e caches de execução Python (`__pycache__`).
3. **Ausência de Padrão Arquitetural Git:** Não havia separação clara entre código de produção, documentação institucional, ferramentas de desenvolvimento e ativos visuais.

## Alternativas Consideradas
* **Manter Estrutura Plana na Raiz:** Simples, mas incompatível com boas práticas de CI/CD, insegura para credenciais e desorganizada para versionamento.
* **Repositórios Separados (Multi-repo):** Criar um repositório para o script e outro para documentação/ferramentas; excessivamente burocrático para o porte do projeto.
* **Topologia Padrão Git com Diretório de Produção `/src` e Clasp:** Estruturar o projeto em diretórios especializados (`src/`, `docs/`, `tools/`, `assets/`) e configurar o Clasp com `"rootDir": "./src"`.

## Decisão Adotada
Reestruturar integralmente o repositório seguindo os padrões consagrados da comunidade de desenvolvimento:
1. **Pasta `src/` (Código de Produção):**
   * Concentra exclusivamente os arquivos enviados e executados no Google Apps Script: `alocacao-plus.gs`, `config.gs`, `index.html`, `estilos.html`, `scripts.html` e o manifesto `appsscript.json`.
   * Permite que o Clasp seja configurado com `"rootDir": "./src"`, garantindo que apenas arquivos de produção sejam enviados para a nuvem.
2. **Pasta `docs/` (Documentação e Decisões):**
   * Abriga a especificação de negócio acadêmico (`especificacao-disciplinas.md`) e os registros arquiteturais (`docs/adr/`).
3. **Pasta `tools/` (Ferramentas de Desenvolvimento):**
   * Isola scripts utilitários locais (como `auth_and_test.py` para diagnóstico OAuth).
4. **Pasta `assets/` (Identidade Visual):**
   * Centraliza logotipos oficiais da EESC e posters institucionais (antiga pasta `visual/`).
5. **Arquivos Raiz de Controle:**
   * `.gitignore`: Protege tokens de autenticação, arquivos de sistema operacional e caches.
   * `README.md`: Centralizador institucional com badges, visão geral e guia de implantação.

## Consequências
### Positivas (+)
* **Isolamento e Segurança no Deploy:** A nuvem do Apps Script recebe apenas o código de execução; documentação, testes e imagens pesadas permanecem apenas no Git.
* **Compatibilidade Imediata com Clasp:** Integração trivial com ferramentas de linha de comando e esteiras de integração contínua (GitHub Actions).
* **Proteção contra Vazamento de Segredos:** Credenciais e tokens gerados em testes locais são ignorados pelo Git de forma automática.
* **Navegabilidade Profissional:** Desenvolvedores e auditores encontram imediatamente o que procuram.

### Negativas / Trade-offs (-)
* Requer que comandos do Clasp ou scripts de build apontem explicitamente para o diretório `src/`.

## Referências no Código
* [README.md](../../README.md)
* [.gitignore](../../.gitignore)
* [src/appsscript.json](../src/appsscript.json)
