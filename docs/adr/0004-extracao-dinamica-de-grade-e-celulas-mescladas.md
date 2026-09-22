# 4. Extração Dinâmica da Grade e Preservação de Células Mescladas

* **Data:** 2026-09-18
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
A planilha oficial de alocação de salas do SVGRAD não é formatada como uma tabela de banco de dados relacional, mas sim como um calendário matricial visual:
* **Linha 2:** Cabeçalho com os dias da semana (Segunda a Sábado), com cada dia abrangendo um número variável de colunas.
* **Linha 3:** Faixas de horário expressas em formatos heterogêneos (ex: `08:00 - 10:00`, `14h às 16h`, `19:15`, `noite`).
* **Linhas 4 em diante:** Listagem de salas físicas (Coluna A) e capacidades (Coluna B), finalizando quando se inicia a seção de legenda.
* **Células Mescladas (*Merged Cells*):** Aulas com duração de 4 horas ou disciplinas que utilizam blocos duplos de horário utilizam mesclagem horizontal e/ou vertical.

Em versões legadas, colunas e faixas horárias eram fixadas no código (*hardcoded*). Quando o SVGRAD adicionava uma sala temporária, mudava o horário noturno ou incluía um novo bloco didático, a aplicação quebrava. Além disso, a API do Google Sheets retorna o valor da célula apenas na coordenada superior esquerda de uma mesclagem, deixando as células cobertas com valor vazio `""`. Em uma tabela HTML padrão, isso destruía o alinhamento das colunas.

## Alternativas Consideradas
* **Exigir reestruturação da planilha do SVGRAD:** Inviável administrativamente; a equipe acadêmica precisa manter o fluxo de trabalho visual tradicional ao qual está habituada há anos.
* **Ignorar mesclagens e duplicar o texto em células repetidas:** Destrói a clareza visual de blocos de aula contínuos e induz o usuário a erro sobre o início e término da disciplina.
* **Introspecção dinâmica em tempo de execução com mapa de merges:** Inspecionar a estrutura real da planilha a cada carga e serializar as mesclagens em atributos `colspan` e `rowspan` compatíveis com HTML.

## Decisão Adotada
Implementar uma arquitetura de leitura 100% dinâmica no backend:
1. **Detecção Dinâmica de Dias (`obterConfigDiasGrade`):** Analisa a Linha 2 da planilha para identificar as colunas exatas de início e a largura de cada dia da semana (`seg`, `ter`, `qua`, `qui`, `sex`, `sab`).
2. **Parser Temporal em Minutos (`parsearFaixaHorario`):** Converte qualquer formato textual de horário em minutos a partir de `00:00` (ex: `08:00 - 10:00` vira `inicioMin: 480, fimMin: 600`), permitindo comparações matemáticas precisas no cliente.
3. **Mapeamento Dinâmico de Salas e Blocos (`obterDadosSalasEBlocos`):** Varre as salas da Linha 4 até o início da Legenda e extrai automaticamente o bloco didático a partir do prefixo da sala (`extrairNomeBloco`: "A - 01" $\rightarrow$ "Bloco A", "Laranja - 20" $\rightarrow$ "Laranja", "Anfiteatro" $\rightarrow$ "Anfiteatros").
4. **Mapeador Bidimensional de Mesclagens:**
   * Utiliza `rangeGrade.getMergedRanges()` para detectar todos os retângulos fundidos.
   * A célula de origem recebe as propriedades `cs` (*colspan*) e `rs` (*rowspan*).
   * Todas as células internas cobertas recebem o marcador compacto `{ c: 1 }`.
   * No frontend, células marcadas com `c: 1` não geram tags `<td>`, permitindo que o navegador renderize a mesclagem geometricamente perfeita.

## Consequências
### Positivas (+)
* **Resiliência a Mudanças Semestrais:** A aplicação adapta-se automaticamente caso o SVGRAD altere o número de colunas, insira salas ou remova blocos.
* **Fidelidade Visual:** A grade renderizada no Web App espelha com precisão cirúrgica o formato oficial da EESC.
* **Payload Otimizado:** O uso de tokens curtos (`t`, `h`, `cs`, `rs`, `c: 1`) reduz em mais de 60% o volume de dados trafegado entre servidor e cliente.

### Negativas / Trade-offs (-)
* O cálculo inicial de mesclagens consome tempo de processamento, tornando o cache do ADR 0003 obrigatório para viabilizar essa flexibilidade.

## Referências no Código
* [src/alocacao-plus.gs](../src/alocacao-plus.gs) (funções `obterConfigDiasGrade`, `parsearFaixaHorario`, `obterEstruturaHorariosGrade`, `obterDadosSalasEBlocos`, `extrairNomeBloco`)
* [src/scripts.html](../src/scripts.html) (função `renderizarGrade`)
