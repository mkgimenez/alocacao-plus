# 0016. Autocomplete Inteligente no Campo de Busca com Sugestões de Departamentos, Disciplinas e Docentes

* **Data:** 2026-09-24
* **Status:** Aceito
* **Decisores:** Equipe de Arquitetura e Engenharia de Frontend (Alocação Plus / EESC-USP)

---

## Contexto e Problema

A caixa de busca textual do **Alocação Plus** realiza filtragem multicritério reativa (siglas, nomes oficiais de disciplinas, turmas resilientes, docentes, modalidades e observações). No entanto:
1. Alunos e docentes muitas vezes desconhecem os códigos de 3 letras de cada departamento (ex: `SEM` para Engenharia Mecânica, `SET` para Estruturas, `SEP` para Produção, `SMA` para Matemática);
2. Dificilmente estudantes memorizam códigos alfanuméricos de disciplinas (ex: saber que "Cálculo IV" é `SMA0356`, "Mecânica dos Sólidos" é `SEM0538` ou "Resistência dos Materiais" é `SET0188`);
3. Usuários digitavam nomes informais como "mecânica" ou "elétrica" e dependiam de ocorrências textuais exatas em células ou no cache;
4. Não havia mecanismo de descoberta nem sugestão rápida de nomes de professores frequentes ou dos principais departamentos da EESC ao focar no campo de busca.

---

## Alternativas Consideradas

* **Alternativa 1: Datalist HTML5 nativo (`<datalist>`):**
  - *Desvantagens:* Não suporta categorização visual por seções (Departamentos vs. Disciplinas vs. Docentes), não permite chips estilizados com tags institucionais (EESC, ICMC, IFSC), não suporta micro-animações táteis nem atalhos rápidos com botões personalizados.
* **Alternativa 2: Biblioteca externa pesada (ex: Select2, Choices.js, Awesomplete):**
  - *Desvantagens:* Adiciona dependências externas no Google Apps Script, aumenta peso de carga da página e quebra a consistência do Design System e das micro-animações do projeto.
* **Alternativa 3: Popover customizado nativo Vanilla JS com catálogo curado e indexação progressiva (Adotada):**
  - *Vantagens:* Zero dependências externas, 100% aderente ao Design System tátil (`cubic-bezier(0.34, 1.56, 0.64, 1)`), navegação integral por teclado (`↑`, `↓`, `Enter`, `Esc`), categorização rica em três níveis (🏛️ Departamentos, 📚 Disciplinas e 👨‍🏫 Docentes), suporte a busca por sinônimos/keywords ("mecânica" $\rightarrow$ `SEM`), indexação em tempo de execução dos docentes e disciplinas conforme lotes são concluídos.

---

## Decisão Adotada

1. **Catálogo Curado de Departamentos e Áreas (`CATALOGO_DEPARTAMENTOS`):**
   - Mapeia siglas oficiais da EESC (`SEM`, `SEL`, `SET`, `SEP`, `SMM`, `SHS`, `SGS`, `SAA`, `STT`, `SRB`) e de outras unidades da USP em São Carlos (`SMA`, `SME`, `SSC`, `SCC`, `760`, `SLC`, `FMT`, `FFI`, `SQM`, `QFL`, `QIQ`, `QOQ`, `IAU`).
   - Cada departamento conta com `sigla`, `nome`, `apelido`, `unidade` e `keywords` para busca semântica (ex: "calculo" sugere `SMA`, "fisica" sugere `760`).

2. **Chips Rápidos de Disciplinas (`DISCIPLINAS_SEMENTE` + Indexação Dinâmica):**
   - Semente estática com ~30 disciplinas troncais da Engenharia (Cálculos I a IV, Físicas I a IV, Mecânica Geral, Resistência dos Materiais, Circuitos, etc.) para resposta instantânea.
   - Enriquecimento progressivo alimentado por `concluirLoteJupiter(dadosRecebidos)` e pelas células da grade com `cel.d`.
   - Limite de até 5 disciplinas mais pontuadas por consulta (evitando saturação visual).

3. **Indexação Dinâmica e Semente de Docentes:**
   - Inicializa com uma base de docentes notáveis/frequentes da EESC para resposta instantânea no 1º milissegundo.
   - Conforme o background worker de disciplinas (Jupiterweb e Janus) conclui lotes, executa `indexarDocentesDeDadosDisciplina(codigo, dados)`, normalizando nomes (limpeza de títulos `Prof.`, `Dr.`, `Profa.`, `Dra.` e marcadores `(R)`), incorporando-os imediatamente ao mapa de busca em memória.

4. **Interface Flutuante e Micro-Interações:**
   - Contêiner `#busca-sugestoes-dropdown` ancorado com `position: absolute` logo abaixo do input de busca.
   - Chips táteis com feedback mecânico no hover (`translateY(-1px)`) e clique (`scale(0.95)` em 0.05s).
   - Suporte completo a navegação por teclado (`ArrowDown`, `ArrowUp`, `Enter`, `Escape`), seleção por clique sem perda precoce de foco (`mousedown` com `preventDefault`) e fechamento ao clicar fora.

---

## Consequências

### Positivas (+)
* **Velocidade de Busca:** Ao digitar `calculo`, o usuário vê o departamento `SMA` e os chips das disciplinas (`SMA0301 • Cálculo I`, `SMA0356 • Cálculo IV`). Ao digitar `resistencia`, vê `SET0188 • Resistência dos Materiais I`.
* **Acessibilidade Semântica e Teclado:** Operável 100% por teclado com atributos ARIA (`role="combobox"`, `aria-autocomplete="list"`).
* **Escalabilidade Infinita:** Novas disciplinas e professores cadastrados na grade são automaticamente reconhecidos e sugeridos sem manutenção de código.
* **Resiliência e Cobertura:** 14 testes unitários e fuzzing com 500 buscas aleatórias garantem 100% de estabilidade (62 testes passando na suíte completa).

### Negativas / Mitigações (-)
* **Poluição visual em telas pequenas:** Mitigada definindo limites de até 6 departamentos, até 5 disciplinas e até 6 docentes por consulta, além de fechamento automático ao selecionar ou pressionar `Esc`.
