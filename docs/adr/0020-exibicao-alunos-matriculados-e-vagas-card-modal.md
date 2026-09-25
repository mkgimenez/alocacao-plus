# 20. Exibição de Alunos Matriculados (Jupiterweb) e Vagas Oferecidas (Janus) no Card Modal da Grade

* **Data:** 2026-09-25
* **Status:** **Aceito**
* **Decisores:** Equipe Alocação Plus (EESC-USP)

## Contexto e Problema

No card modal flutuante de informações das disciplinas da grade horária, os docentes, alunos e gestores acadêmicos necessitavam consultar a demanda de cada turma para planejar e avaliar a ocupação real das salas de aula. 

Entretanto, as regras e dados disponíveis nos sistemas acadêmicos da USP divergem entre os níveis de ensino:
1. **Graduação (Jupiterweb):** A métrica mais relevante para alocação é a quantidade de **Alunos Matriculados** de fato na turma. O HTML do Jupiterweb expõe uma tabela complexa com categorias de vagas (*Obrigatória*, *Optativa Eletiva*, etc.) e linhas subordinadas por código de curso, exigindo soma precisa sem redundâncias ou contagem duplicada.
2. **Pós-Graduação (Janus):** O sistema Janus não expõe a contagem em tempo real de matrículas confirmadas na consulta pública simplificada, mas provê a quantidade total de **Vagas Oferecidas** (*Regulares + Especiais = Total*).

Adicionalmente, havia o risco de regressão por dados em cache pré-existentes no `sessionStorage` dos navegadores dos usuários, que fariam com que todas as turmas exibissem *"Não informado"*, além do risco comum em JavaScript onde o valor `0` é tratado como *falsy* e erroneamente substituído pelo texto de fallback.

## Alternativas Consideradas

* **Alternativa 1 (Extrair a tabela completa de distribuição de vagas no Jupiterweb):** Armazenar a matriz completa de cursos e vagas por categoria. *Descartada* porque aumentaria substancialmente o tamanho do JSON trafegado, consumiria desnecessariamente memória no `CacheService` (que tem limite de 100 KB por item) e poluaria visualmente o card modal em dispositivos móveis.
* **Alternativa 2 (Rótulo genérico idêntico para Graduação e Pós-Graduação):** Utilizar um texto único como *"Vagas / Alunos"*. *Descartada* por induzir a erro conceitual, misturando alunos efetivamente inscritos com o limite máximo de vagas do edital.
* **Alternativa 3 (Transferir parsing para o cliente em tempo de clique):** *Descartada* por violar a arquitetura desacoplada do Alocação Plus e forçar o envio de documentos HTML brutos pesados aos clientes móveis.

## Decisão Adotada

1. **Parser de Graduação (`parsearHtmlJupiterweb`):**
   - Extrai o número total de matriculados somando as linhas de categoria da tabela de distribuição de vagas.
   - Identifica as linhas de categoria pela presença de `colspan="2"` (ou `colspan=2`) na primeira célula e total de 5 células `<td>`. A 4ª célula (índice 3) contém o número de matriculados.
   - Ignora rigorosamente as linhas de detalhamento subordinado por curso (que contêm 6 células `<td>` sem `colspan`), evitando dupla contagem.
   - Delimita a busca estritamente entre a ocorrência de `Matriculado` no cabeçalho e o fechamento `</table>` mais imediato.
   - Se a tabela existir, salva o inteiro `matriculados` ($\ge 0$); caso contrário, mantém `matriculados: null`.

2. **Parser de Pós-Graduação (`parsearHtmlJanusTurma`):**
   - Extrai a quantidade total de vagas da tabela identificada por `intl_numeroVagas` ou `Número de vagas` no endpoint `TurmaDet`.
   - Localiza dinamicamente a coluna `Total` / `intl_total` no cabeçalho e extrai o valor inteiro correspondente na linha de dados.
   - Retorna o inteiro `vagas` ($\ge 0$) ou `null` caso a tabela não esteja presente.

3. **Renderização Dinâmica e Acessível no Frontend (`scripts.html` / `estilos.html`):**
   - Criação de container dedicado `#modal-turma-alunos-container` com `#modal-turma-alunos-titulo` e `#modal-turma-alunos-valor` com atributo de acessibilidade `aria-live="polite"`.
   - Lógica estrita de detecção de nível de ensino (via `disciplina.sistema === 'janus'` ou regex de pós-graduação).
   - Para Graduação: Exibe `👥 Alunos Matriculados: [N]`.
   - Para Pós-Graduação: Exibe `👥 Número de Vagas: [N]`.
   - Verificação estrita de presença (`turmaObj.matriculados !== undefined && turmaObj.matriculados !== null`), assegurando que `0` seja renderizado como `"0"` e não como `"Não informado"`.
   - Estilização com largura total (`display: flex; width: 100%;`) e tipografia tabular (`font-variant-numeric: tabular-nums`), mantendo simetria geométrica com as demais seções do modal.

4. **Invalidação e Versionamento de Cache:**
   - Atualizados os prefixos do `CacheService` no servidor para `JUP_V19_` e `JAN_V3_`.
   - Atualizados os prefixos do `sessionStorage` no cliente para `alocacao_jupiter_v19_` e `alocacao_janus_v3_`, forçando a purga automática de dados anteriores e garantindo enriquecimento imediato com os novos campos.

5. **Testes Automatizados:**
   - Criação de suíte dedicada de formatadores de interface (`tests/test_modal_formatters.py`) com 8 testes cobrindo graduação, pós, fallbacks, chave ausente e proteção de `0`.
   - Expansão dos testes de parsers em `test_jupiter_parser.py` e `test_janus_parser.py` com amostras reais da EESC e fixtures sintéticas.

## Consequências

### Positivas
* **Informação instantânea e contextual:** Usuários têm visibilidade imediata da densidade de alunos por turma ao clicar em qualquer disciplina da grade.
* **Economia de rede e cache:** O payload JSON do cache acrescenta apenas uma única chave numérica por turma (`matriculados: N` ou `vagas: N`), mantendo o overhead em bytes praticamente imperceptível.
* **Resiliência a variações de layout:** Casos com 0 alunos ou turmas com formatos atípicos de HTML não quebram a interface nem geram erros de execução.

### Negativas / Mitigações
* A atualização dos prefixos de cache invalida as consultas já cacheadas nas sessões ativas dos clientes, provocando uma nova rodada de consultas em segundo plano via worker assíncrono. Como o carregamento ocorre de forma não bloqueante e com priorização geométrica do Viewport 2D, o impacto para o usuário é nulo.

## Referências no Código
* [src/alocacao-plus.gs](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/alocacao-plus.gs)
* [src/scripts.html](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/scripts.html)
* [src/index.html](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/index.html)
* [src/estilos.html](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/src/estilos.html)
* [tests/test_modal_formatters.py](file:///d:/OneDrive/EESC/Documents/SCAE/code/alocacao-plus/tests/test_modal_formatters.py)
