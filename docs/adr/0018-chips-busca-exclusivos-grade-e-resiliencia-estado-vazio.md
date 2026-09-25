# 0018. Chips da Busca Baseados Exclusivamente na Grade Atual e Resiliência do Estado Vazio

* **Data:** 2026-09-25
* **Status:** Aceito
* **Decisores:** Equipe de Arquitetura e Engenharia de Frontend (Alocação Plus / EESC-USP)

---

## Contexto e Problema

O motor de autocomplete inteligente no campo de busca (introduzido na v1.4.0 e formalizado no ADR 0016) utilizava constantes estáticas de sementes (`DOCENTES_SEMENTE` e `DISCIPLINAS_SEMENTE`) para garantir sugestões no primeiro milissegundo de abertura do webapp.

Com a operação em produção, identificaram-se limitações e desalinhamentos de expectativa:

1. **Chips Fantasmas e Quebra de Expectativa:**
   Docentes históricos (ex: *Carlos Dias Maciel*) ou matérias não oferecidas no semestre (ex: *SMA0355 — Cálculo III*) apareciam como chips sugeridos. Ao clicar no chip, a grade aplicava o filtro e exibia "0 salas encontradas", gerando frustração.
2. **Indexação Indiscriminada de Docentes por Matéria:**
   Ao enriquecer uma disciplina via Júpiterweb/Janus, todos os professores de todas as turmas cadastradas na USP eram indexados no dropdown, inclusive turmas de outros campi ou turmas não alocadas nas salas físicas da EESC.
3. **Departamentos Desconectados do Semestre:**
   O catálogo completo de departamentos aparecia no estado inicial, mesmo para departamentos sem nenhuma aula alocada na grade ativa.
4. **Mensagem Genérica e Falta de Feedback durante o Carregamento Assíncrono:**
   Se o usuário realizasse uma busca por docente ou matéria enquanto os dados do Júpiterweb/Janus ainda estavam sendo enriquecidos em segundo plano, a mensagem do estado vazio informava apenas para buscar por outro termo, sem esclarecer que os dados ainda estavam sendo sincronizados.
5. **Problema de Contraste Visual no Botão "Ver Todas as Salas":**
   O botão `.btn-primary-outline` do container `#estado-vazio` possuía cor de texto branca (`#ffffff`) sobre fundo branco, ficando ilegível.

---

## Decisão Adotada

### 1. Eliminação Integral de Dados Semente Estáticos
- Descontinuadas e removidas as listas estáticas `DOCENTES_SEMENTE` e `DISCIPLINAS_SEMENTE`.
- `mapaDocentesIndexados` e `mapaDisciplinasIndexadas` iniciam vazios e são derivados **exclusivamente** da matriz da grade em execução e dos dados em cache ou recebidos em lote via Júpiterweb/Janus.

### 2. Extração Canônica e Determinística de Turmas (`extrairTurmasNumericasDaCelula`)
- Unificação da rotina de extração de números inteiros de turmas a partir de `cel.turmas` e análise textual resiliente em `cel.t` (suporte a `T01`, `Turma 1`, `T1/T2`, pós-graduação `SEP5864 - 1` e `SHS5991 / 02`).
- Reutilização da mesma função canônica dentro de `celulaCorrespondeABusca`, garantindo consistência total (DRY) entre a indexação e a filtragem da grade.

### 3. Mapeamento da Grade em $O(1)$ (`extrairDisciplinasETurmasDaGrade`)
- Varredura em passo único da matriz da grade oficial apurando:
  - Mapa de códigos de disciplinas com conjunto de turmas ativas e flag `temSemTurma`;
  - Volume real de aulas alocadas por sigla departamental ativa (deduplicando departamentos por célula para evitar contagem inflada);
  - Suporte completo a departamentos puramente numéricos do IFSC (ex: `7600006` mapeando para o departamento `760`).

### 4. Filtragem Estrita de Docentes por Turma Alocada (`indexarDocentesDeDadosDisciplina`)
- Docentes só são indexados se a disciplina pertencer à grade ativa do semestre.
- Se a disciplina contiver turmas específicas alocadas e nenhuma ocorrência genérica (`infoGrade.turmas.size > 0 && !infoGrade.temSemTurma`), apenas os professores das turmas alocadas são indexados.
- Preservação de fallback seguro: caso a disciplina possua aulas sem número de turma indicado na planilha da EESC, todas as turmas cadastradas são aceitas para evitar falsos negativos.
- Suporte a `t.numero || t.ofe` (compatibilidade plena com Júpiterweb e Janus).

### 5. Departamentos Vivos e Ordenados por Frequência
- No estado vazio da busca (`termo === ''`), os departamentos são filtrados para exibir exclusivamente os que possuem aulas no semestre, ordenados descendentemente pelo volume real de aulas alocadas.
- Na busca textual, nenhum departamento inativo é sugerido.
- Em caso de foco na busca antes da chegada da grade (*cold start*), exibe indicador sutil `"⏳ Carregando Grade..."`.

### 6. Resiliência do Estado Vazio e Feedback de Carregamento
- Quando um termo de busca não retornar nenhuma sala (`temBusca === true`), o sistema verifica se a fila assíncrona do Júpiterweb/Janus está ativa (`estadoApp.filaJupiter.length > 0 || estadoApp.jupiterRequisicaoEmVoo`).
- Em caso positivo, exibe instrução contextual clara orientando o usuário a aguardar o término do carregamento para tentar novamente.

### 7. Correção de Contraste e Acessibilidade do Botão `.btn-primary-outline`
- Ajustada a cor do botão no estado de repouso para `#104880` (azul institucional da EESC) com borda `1.5px solid #104880` e fundo transparente.
- No `:hover`, o botão transita para fundo `#104880` com texto branco (`#ffffff`), garantindo legibilidade imediata sobre o fundo claro da aplicação.

---

## Consequências

### Positivas (+)
* **Fim dos Chips Fantasmas:** 100% dos chips sugeridos (departamentos, matérias e docentes) correspondem a aulas alocadas na grade ativa do semestre.
* **Zero Ocorrências de "0 Salas Encontradas" no Clique:** Todo chip sugerido possui salas reais correspondentes na visualização.
* **Transparência de Carregamento:** O usuário entende claramente quando um resultado ainda não apareceu porque os dados em lote ainda estão sendo baixados em segundo plano.
* **Acessibilidade e Usabilidade:** O botão "Ver Todas as Salas" possui contraste WCAG perfeito e feedback visual evidente.
* **Qualidade Assegurada:** A suíte de testes passou de 72 para 83 testes automatizados (100% de sucesso), cobrindo casos típicos, bordas, IFSC 760, pós-graduação e estabilidade via fuzzing.
