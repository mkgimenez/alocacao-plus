# 0016. Autocomplete Inteligente no Campo de Busca com Sugestões de Departamentos e Docentes

* **Data:** 2026-09-24
* **Status:** Aceito
* **Decisores:** Equipe de Arquitetura e Engenharia de Frontend (Alocação Plus / EESC-USP)

---

## Contexto e Problema

A caixa de busca textual do **Alocação Plus** realiza filtragem multicritério reativa (siglas, nomes oficiais de disciplinas, turmas resilientes, docentes, modalidades e observações). No entanto:
1. Alunos e docentes muitas vezes desconhecem os códigos de 3 letras de cada departamento (ex: `SEM` para Engenharia Mecânica, `SET` para Estruturas, `SEP` para Produção, `SMA` para Matemática);
2. Usuários digitavam nomes informais como "mecânica" ou "elétrica" e dependiam de ocorrências textuais exatas em células ou no cache;
3. Não havia mecanismo de descoberta nem sugestão rápida de nomes de professores frequentes ou dos principais departamentos da EESC ao focar no campo de busca.

---

## Alternativas Consideradas

* **Alternativa 1: Datalist HTML5 nativo (`<datalist>`):**
  - *Desvantagens:* Não suporta categorização visual por seções (Departamentos vs. Docentes), não permite chips estilizados com tags institucionais (EESC, ICMC, IFSC), não suporta micro-animações táteis nem atalhos rápidos com botões personalizados.
* **Alternativa 2: Biblioteca externa pesada (ex: Select2, Choices.js, Awesomplete):**
  - *Desvantagens:* Adiciona dependências externas no Google Apps Script, aumenta peso de carga da página e quebra a consistência do Design System e das micro-animações do projeto.
* **Alternativa 3: Popover customizado nativo Vanilla JS com catálogo curado e indexação progressiva de docentes (Adotada):**
  - *Vantagens:* Zero dependências externas, 100% aderente ao Design System tátil (`cubic-bezier(0.34, 1.56, 0.64, 1)`), navegação integral por teclado (`↑`, `↓`, `Enter`, `Esc`), categorização rica com chips rápidos, suporte a busca por sinônimos/keywords ("mecânica" $\rightarrow$ `SEM`), indexação em tempo de execução dos docentes que chegam nos lotes em segundo plano.

---

## Decisão Adotada

1. **Catálogo Curado de Departamentos e Áreas (`CATALOGO_DEPARTAMENTOS`):**
   - Mapeia siglas oficiais da EESC (`SEM`, `SEL`, `SET`, `SEP`, `SMM`, `SHS`, `SGS`, `SAA`, `STT`, `SRB`) e de outras unidades da USP em São Carlos (`SMA`, `SME`, `SSC`, `SCC`, `760`, `SLC`, `FMT`, `FFI`, `SQM`, `QFL`, `QIQ`, `QOQ`, `IAU`).
   - Cada departamento conta com `sigla`, `nome`, `apelido`, `unidade` e `keywords` para busca semântica (ex: "calculo" sugere `SMA`, "fisica" sugere `760`).

2. **Indexação Dinâmica e Semente de Docentes:**
   - Inicializa com uma base de docentes notáveis/frequentes da EESC para resposta instantânea no 1º milissegundo.
   - Conforme o background worker de disciplinas (Jupiterweb e Janus) conclui lotes, executa `indexarDocentesDeDadosDisciplina(codigo, dados)`, normalizando nomes (limpeza de títulos `Prof.`, `Dr.`, `Profa.`, `Dra.` e marcadores `(R)`), incorporando-os imediatamente ao mapa de busca em memória.

3. **Interface Flutuante e Micro-Interações:**
   - Contêiner `#busca-sugestoes-dropdown` ancorado com `position: absolute` logo abaixo do input de busca.
   - Chips táteis com feedback mecânico no hover (`translateY(-1px)`) e clique (`scale(0.95)` em 0.05s).
   - Suporte completo a navegação por teclado (`ArrowDown`, `ArrowUp`, `Enter`, `Escape`), seleção por clique sem perda precoce de foco (`mousedown` com `preventDefault`) e fechamento ao clicar fora.

---

## Consequências

### Positivas (+)
* **Velocidade de Busca:** Ao digitar `SE`, o usuário visualiza imediatamente `SEM • Mecânica`, `SEL • Elétrica`, `SET • Estruturas`, `SEP • Produção` e nomes de docentes como `Sérgio Proença`.
* **Acessibilidade Semântica e Teclado:** Operável 100% por teclado com atributos ARIA (`role="combobox"`, `aria-autocomplete="list"`).
* **Escalabilidade Infinita:** Novos professores cadastrados na grade são automaticamente reconhecidos e sugeridos sem manutenção de código.
* **Resiliência e Cobertura:** 10 novos testes unitários e fuzzing com 500 buscas aleatórias garantem 100% de estabilidade (58 testes passando na suíte completa).

### Negativas / Mitigações (-)
* **Poluição visual em telas pequenas:** Mitigada definindo limites de até 6 departamentos e até 6 docentes por consulta, além de fechamento automático ao selecionar ou pressionar `Esc`.
