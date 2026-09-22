# 1. Adoção do Registro de Decisões de Arquitetura (ADRs)

* **Data:** 2026-09-15
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
O projeto **Alocação Plus** opera em um ambiente que combina restrições severas de execução em nuvem (Google Apps Script, limites de cotas de tempo de CPU, limites de memória de cache, permissões de segurança Google Workspace) e requisitos de alta velocidade para os usuários finais (estudantes, professores e secretarias de departamento).

Ao longo do desenvolvimento, diversas decisões cruciais foram tomadas — como a transição de um painel embutido no Google Sheets para um Web App autônomo, o algoritmo de particionamento de cache para superar os 100KB do `CacheService` e a gramática formal de parser de disciplinas. 

Sem um registro formal, o raciocínio por trás dessas escolhas se perderia com a rotatividade de desenvolvedores e bolsistas, aumentando o risco de regressões ou reintrodução de soluções já descartadas por inviabilidade técnica.

## Alternativas Consideradas
* **Comentários extensos no código-fonte:** Poluem os arquivos `.gs` e `.html`, dificultam a visão holística do projeto e não registram soluções que foram tentadas e descartadas.
* **Documento único no Google Docs:** Perde a sincronia com o versionamento de código no Git, não permite diffs textuais nas alterações de design e fica isolado do repositório local.
* **Architecture Decision Records (ADRs) em Markdown:** Formato padronizado pela indústria (Nygard/MADR), versionado lado a lado com o código-fonte no repositório.

## Decisão Adotada
Adotar a prática de **Architecture Decision Records (ADR)** na pasta `docs/adr/`, utilizando arquivos numerados sequencialmente em Markdown (`XXXX-titulo-kebab-case.md`) para registrar todas as decisões de arquitetura e engenharia do sistema.

## Consequências
### Positivas (+)
* Preservação da memória técnica e clareza sobre por que certas restrições do Google Apps Script foram contornadas de determinadas maneiras.
* Facilidade para integração (*onboarding*) de novos desenvolvedores na EESC.
* Histórico rastreável e auditável de cada evolução arquitetural.

### Negativas / Trade-offs (-)
* Pequeno esforço contínuo de documentação ao introduzir mudanças estruturais significativas.

## Referências no Código
* [docs/adr/README.md](README.md)
