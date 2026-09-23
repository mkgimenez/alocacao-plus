# Especificação de Nomenclatura e Regras de Negócio das Disciplinas
**Projeto:** Alocação Plus (EESC-USP)  
**Documento:** Regras para Reconhecimento, Parser e Classificação de Disciplinas e Turmas

---

## 1. Gramática Formal do Código da Disciplina

O padrão de codificação adotado na grade horária da EESC segue a seguinte estrutura:

```
<CÓDIGO DA DISCIPLINA> = <SIGLA DO DEPARTAMENTO><ID NUMÉRICO DA DISCIPLINA>[ - T<NÚMERO DA TURMA>[\[AULA DA SEMANA\]][ pv|tv]
```

---

## 2. Componentes e Regras de Validação

### 2.1. Sigla do Departamento (`<SIGLA DO DEPARTAMENTO>`)
* **Tamanho:** Exatamente **3 caracteres**.
* **Composição:** Letras ou dígitos alfanuméricos (`[A-Za-z0-9]{3}`).
* **Sanitização de Typos:** Qualquer caractere alfabético deve ser sempre tratado em **MAIÚSCULAS** (`.toUpperCase()`). Typos em minúsculas (ex.: `sem` $\rightarrow$ `SEM`) devem ser corrigidos na leitura.
* **Departamentos Comuns:**
  * **EESC:** `SEM` (Mecânica), `SET` (Estruturas), `SEL` (Elétrica e Computação), `SMM` (Materiais), `SHS` (Hidráulica e Saneamento), `STT` (Transportes), `SGS` (Geotecnia), `SAA` (Aeronáutica), `SEP` (Produção), `SRB` (Recursos Hídricos/Biotecnologia).
  * **Outras Unidades do Campus São Carlos:** `SMA` (Matemática - ICMC), `SME` (Estatística/Ciência da Computação - ICMC), `SSC`/`SCC` (Computação - ICMC), `SLC` (Física - IFSC), `SQM` (Química - IQSC), `IAU` (Arquitetura e Urbanismo).
  * *Atenção:* Existem também códigos interunidades puramente numéricos de 7 dígitos (ex.: `7600006`, `7500089`, `1800121`).

### 2.2. Identificador Numérico da Disciplina (`<ID NUMÉRICO DA DISCIPLINA>`)
* **Tamanho:** Exatamente **4 dígitos** (`\d{4}`).
* **Nível Acadêmico:**
  * **Graduação:** O primeiro dígito é **`0`** (ex.: `0403`, `0538`, `0142`).
  * **Pós-Graduação:** O primeiro dígito é diferente de zero, de **`1` a `9`** (ex.: `5864`, `5722`, `5934`, `5029`).

### 2.3. Turma (`- T<NÚMERO DA TURMA>`)
* **Ocorrência:** Opcional. Precedido de ` - T` ou `- T` ou `-T`.
* **Variações Identificadas:**
  * Turma única: `T1`, `T2`, `T04`.
  * Turmas compartilhadas/agrupadas na mesma sala: `T1 e T2`, `T2 e T3`, `T5 E T6`.
  * Algumas células trazem o sufixo `- Pós-Grad` em vez de turma (ex.: `SEP5864 - Pós-Grad`).

### 2.4. Aula da Semana (`[\[AULA DA SEMANA\]]`)
* **Ocorrência:** Opcional, indicado entre colchetes: `[1]`, `[2]`, `[3]`.
* **Significado:** Indica a ocorrência semanal daquela turma (ex.: `[1]` = 1ª aula da semana, `[2]` = 2ª aula da semana).
* *Exemplo:* `SME0341 - T2[1]` (aula 1) e `SME0341 - T2[2]` (aula 2).

### 2.5. Modalidade Vinculada (`[ pv|tv]`)
* **Ocorrência:** Opcional, ao final do código da turma.
* **Significado Oficial da Legenda:**
  * `tv` = **Teoria Vinculada**
  * `pv` = **Prática Vinculada**
* *Exemplo:* `SEM0388 - T1 tv` e `SEM0388 - T2 pv`.

---

## 3. Casos Especiais e Eventos na Grade

Além do padrão regular de disciplinas, a grade apresenta células com eventos temporários e anotações:

| Tipo | Padrão / Exemplo | Ação Recomendada |
| :--- | :--- | :--- |
| **Provas com Data** | `01/12 - prova 7600110`, `21/09 - prova SEP0175` | Evento pontual; identificar disciplina e data. |
| **Monitorias** | `SET188 - monitoria`, `Monitoria - SME0341` | Atividade de apoio discente. |
| **Projetos e Extensão** | `Projeto Pequeno Cidadão (até 10h15)` | Ocupação periódica/social de espaço. |
| **Eventos Pontuais** | `19/10 - Oficina de Biodanza`, `23/10 - XII SEMANAU` | Evento único/semanal de data fechada. |
| **Reservas Técnicas** | `16/09 - reservado para instalação de ar` | Manutenção física. |
| **Anotações Didáticas** | `SET0183 - T2 - em inglês para alunos de Intercâmbio` | Metadado adicional da turma. |

---

## 4. Legenda Oficial de Formatação da Planilha

Conforme registrado nas linhas 60 a 68 da grade oficial:
* **Cor Azul:** Disciplina pertencente a outra unidade da USP (fora da EESC).
* **Cor Cereja:** Evento de data única / avaliação pontual.
* **Cor Vermelho:** Questão ou alocação pendente de confirmação.
* **Letra P (na Capacidade da Sala):** Sala com **Pranchetas** de desenho (ex.: `45 P`).

---

## 5. Exemplo de Implementação de Parser (JavaScript / Apps Script)

```javascript
/**
 * Extrai e estrutura os dados de uma célula da grade
 * @param {string} textoConteudo - Texto original da célula
 * @returns {Object|null} Objeto estruturado com os dados ou null se vazio/evento
 */
function parsearCelulaDisciplina(textoConteudo) {
  if (!textoConteudo || typeof textoConteudo !== 'string') return null;
  const texto = textoConteudo.trim();

  // Regex para capturar: Sigla (3), ID (4), Turma, Aula da semana [x], e modalidade (pv|tv)
  const regexPadrao = /^([A-Za-z0-9]{3})(\d{4})(?:\s*-\s*T([^\s\[\]]+(?:\s+e\s+[^\s\[\]]+)?))?(?:\[(\d+)\])?(?:\s+(pv|tv))?/i;
  const match = texto.match(regexPadrao);

  if (!match) {
    // Casos especiais (eventos com data, pós-grad sem T, etc.)
    return {
      ehDisciplinaRegular: false,
      textoOriginal: texto
    };
  }

  const siglaDept = match[1].toUpperCase();
  const idNum = match[2];
  const turma = match[3] || null;
  const aulaSemana = match[4] ? parseInt(match[4], 10) : null;
  const modalidade = match[5] ? match[5].toLowerCase() : null;

  // Regra de nível acadêmico pelo primeiro dígito
  const nivel = idNum.startsWith('0') ? 'Graduação' : 'Pós-Graduação';

  return {
    ehDisciplinaRegular: true,
    codigoCompleto: siglaDept + idNum,
    departamento: siglaDept,
    idNumero: idNum,
    nivel: nivel,
    turma: turma,
    aulaSemana: aulaSemana,
    modalidade: modalidade === 'tv' ? 'Teoria Vinculada' : (modalidade === 'pv' ? 'Prática Vinculada' : null),
    textoOriginal: texto
  };
}
```

---

## 6. Integração com Sistemas Públicos da USP (Jupiterweb e Janus)

Para enriquecer a grade com links diretos aos detalhes das disciplinas (turmas oferecidas, quantidade de alunos matriculados, docentes responsáveis, requisitos e ementa):

### 6.1. URLs Oficiais por Nível Acadêmico
* **Graduação (códigos de 7 dígitos ou 3 letras + 4 dígitos iniciando por `0`):**
  ```
  https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=<CÓDIGO DA DISCIPLINA>
  ```
  *Exemplo:* `https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=SEM0538`
* **Pós-Graduação (códigos de 3 letras + 4 dígitos iniciando por `1` a `9`):**
  ```
  https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=<CÓDIGO DA DISCIPLINA>
  ```
  *Exemplo:* `https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=SEP5864`

### 6.2. Regra de Preservação e Apresentação
* O texto visível original da célula é integralmente mantido (ex: `SEM0538 - T1`, `SHS5991 - Pós-Grad`, `SMA0304 - T3[2]`).
* **Anulação de Estilos Padrão de Hyperlink:** Links no Google Sheets recebem, por padrão, sublinhado e cor azul (`#1155cc`). O parser do **Plus** anula explicitamente esse comportamento através de `TextStyle`, definindo `.setUnderline(false)` e restaurando a cor de fonte original (`.setForegroundColor(corOriginal)`), além de pesos e famílias tipográficas.
* Preserva integralmente as mesclagens de horário (aulas com 2 ou mais blocos), cores de fundo, bordas e as cores semânticas da legenda oficial (azul para outras unidades, cereja para avaliações e vermelho para pendências).

### 6.3. Enriquecimento Progressivo com Dados Oficiais do Jupiterweb
* **Hover:** Exibição do nome do docente responsável (`Docente: [Nome]` ou `Docentes: [Nome 1], [Nome 2]`).
* **Clique:** Abertura do **Card Modal Elegante** contendo seleção de turmas por pills, horários oficiais com docentes e observações.
* **Atalhos Preservados:** Cliques com teclas modificadoras (`Ctrl+Clique`, `Cmd+Clique`) ou botão do meio abrem diretamente a URL em nova aba.
* **Documentação Técnica e Decisões de Arquitetura:**
  * [Especificação do Parser HTML e Charset ISO-8859-1](especificacao-parser-jupiterweb.md)
  * [ADR 0013 — Enriquecimento Progressivo de Disciplinas com Dados do Jupiterweb](adr/0013-enriquecimento-progressivo-jupiterweb.md)
  * [Roteiro de Implementação e Histórico de Validação](implementacao-enriquecimento-jupiterweb.md)

---
*Documento gerado e versionado para o projeto Alocação Plus.*