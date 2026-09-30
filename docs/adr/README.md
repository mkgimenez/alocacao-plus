# Registros de Decisões de Arquitetura (ADR) — Alocação Plus

Um **Architecture Decision Record (ADR)** é um documento curto em formato Markdown que captura uma decisão arquitetural significativa tomada no projeto, juntamente com seu contexto, motivações, alternativas descartadas e consequências (positivas e negativas).

---

## 📋 Índice Cronológico de Decisões

| ID | Título da Decisão | Status | Data |
| :--- | :--- | :---: | :---: |
| [0001](0001-registro-decisoes-arquiteturais.md) | Adoção do Registro de Decisões de Arquitetura (ADRs) | **Aceito** | 2026-09-15 |
| [0002](0002-migracao-sidebar-para-webapp-standalone.md) | Migração de Painel Lateral (Sidebar) para Web App Autônomo | **Aceito** | 2026-09-17 |
| [0003](0003-estrategia-cache-multinivel-em-chunks.md) | Estratégia de Cache Multinível em Chunks no CacheService | **Aceito** | 2026-09-18 |
| [0004](0004-extracao-dinamica-de-grade-e-celulas-mescladas.md) | Extração Dinâmica da Grade e Preservação de Células Mescladas | **Aceito** | 2026-09-18 |
| [0005](0005-parser-disciplinas-e-links-jupiterweb-janus.md) | Parser de Disciplinas e Hiperlinks com Jupiterweb e Janus | **Aceito** | 2026-09-19 |
| [0006](0006-filtragem-e-gestao-de-estado-reativa-no-cliente.md) | Filtragem e Gestão de Estado Reativa 100% no Navegador | **Aceito** | 2026-09-20 |
| [0007](0007-parametrizacao-sem-codigo-via-aba-config.md) | Parametrização sem Código via Aba de Configuração (_Config) | **Aceito** | 2026-09-21 |
| [0008](0008-modularizacao-frontend-apps-script.md) | Modularização do Frontend no Apps Script com include() | **Aceito** | 2026-09-21 |
| [0009](0009-estruturacao-repositorio-git-e-separacao-src.md) | Estruturação do Repositório Git, Isolamento em /src e Clasp | **Aceito** | 2026-09-22 |
| [0010](0010-padronizacao-nomenclatura-arquivos-kebab-case.md) | Padronização de Nomenclatura em kebab-case e Padrões Git | **Aceito** | 2026-09-22 |
| [0011](0011-sincronizador-automatico-python-gas-api.md) | Sincronizador Automático em Python via Apps Script REST API | **Aceito** | 2026-09-22 |
| [0012](0012-controle-de-versao-semver-build.md) | Controle de Versão Semântico (SemVer) e Contador de Build Automático | **Aceito** | 2026-09-22 |
| [0013](0013-enriquecimento-progressivo-jupiterweb.md) | Enriquecimento Progressivo de Disciplinas com Dados do Jupiterweb | **Aceito** | 2026-09-23 |
| [0014](0014-padronizacao-botoes-e-micro-animacoes-tateis.md) | Padronização Visual de Botões e Micro-Animações Táteis ("Efeitos Fofinhos") | **Aceito** | 2026-09-24 |
| [0015](0015-enriquecimento-progressivo-janus.md) | Enriquecimento Progressivo de Disciplinas com Dados do Janus (Pós-Graduação) | **Aceito** | 2026-09-24 |
| [0016](0016-autocomplete-inteligente-campo-busca.md) | Autocomplete Inteligente no Campo de Busca (Departamentos & Docentes) | **Aceito** | 2026-09-24 |
| [0017](0017-coloracao-progressiva-e-priorizacao-viewport-2d.md) | Coloração Progressiva da Grade, Priorização Geométrica no Viewport 2D e Consolidação do Card Modal | **Aceito** | 2026-09-25 |
| [0018](0018-chips-busca-exclusivos-grade-e-resiliencia-estado-vazio.md) | Chips da Busca Baseados Exclusivamente na Grade Atual e Resiliência do Estado Vazio | **Aceito** | 2026-09-25 |
| [0019](0019-otimizacao-espaco-vertical-e-camadas-sticky.md) | Otimização de Espaço Vertical, Camadas Sticky da Grade e Refinamento do Cabeçalho | **Aceito** | 2026-09-25 |
| [0020](0020-exibicao-alunos-matriculados-e-vagas-card-modal.md) | Exibição de Alunos Matriculados (Jupiterweb) e Vagas Oferecidas (Janus) no Card Modal da Grade | **Aceito** | 2026-09-25 |
| [0021](0021-pesquisa-troca-de-sala-inteligente.md) | Pesquisa Inteligente de Troca de Sala (Modo Salas Livres Automatizado) | **Aceito** | 2026-09-25 |
| [0022](0022-insercao-contextual-chips-disciplina-nome-sigla.md) | Inserção Contextual de Nome vs. Sigla nos Chips de Disciplinas do Autocomplete | **Aceito** | 2026-09-28 |
| [0023](0023-destaque-visual-intervalos-entre-aulas.md) | Destaque Visual de Horário Durante Intervalos e Pré-Expediente na Grade | **Aceito** | 2026-09-30 |
| [0024](0024-padronizacao-posicionamento-e-estilos-de-botoes-em-modais-e-acoes.md) | Padronização de Posicionamento e Estilos de Botões em Modais e Barras de Ação | **Aceito** | 2026-09-30 |
| [0025](0025-modo-desenvolvedor-e-supressao-de-telemetria.md) | Modo Desenvolvedor e Autoexclusão de Telemetria via Parâmetro de URL (?dev=1) | **Aceito** | 2026-09-30 |

---

## 🛠️ Como Propor um Novo ADR

1. Crie uma cópia do modelo abaixo no diretório `docs/adr/`.
2. Nomeie o arquivo sequencialmente: `XXXX-titulo-descritivo-em-kebab-case.md` (ex: `0011-autenticacao-institucional-usp.md`).
3. Preencha as seções com objetividade técnica.
4. Adicione o novo registro à tabela do índice neste `README.md`.

---

## 📝 Modelo de ADR (Template)

```markdown
# [Número]. [Título da Decisão]

* **Data:** AAAA-MM-DD
* **Status:** [Proposto | Aceito | Substituído por ADR-XXXX | Obsoleto]
* **Decisores:** [Nomes ou papéis envolvidos]

## Contexto e Problema
[Qual é o problema ou cenário técnico a ser enfrentado? Quais são as forças motivadoras e restrições técnicas da plataforma?]

## Alternativas Consideradas
* **Alternativa 1:** [Descrição breve e motivos pelos quais não foi escolhida]
* **Alternativa 2:** [Descrição breve e motivos pelos quais não foi escolhida]

## Decisão Adotada
[O que foi decidido? Qual a abordagem técnica detalhada adotada?]

## Consequências
### Positivas (+)
* [Impacto favorável 1]
* [Impacto favorável 2]

### Negativas / Trade-offs (-)
* [Limitação aceita ou custo de manutenção introduzido]

## Referências no Código
* [caminho/do/arquivo.ext](file:///...)
```
