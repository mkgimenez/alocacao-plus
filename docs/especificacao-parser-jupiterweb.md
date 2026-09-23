# Especificação Técnica do Parser HTML do Jupiterweb

**Projeto:** Alocação Plus (EESC-USP)  
**Documento:** Regras de Parsing, Expressões Regulares e Sanitização para Dados do Jupiterweb (USP)  
**Versão de Referência:** 1.0  
**Data:** 23/09/2026

---

## 1. Visão Geral da Arquitetura do Jupiterweb

O **Jupiterweb** é o sistema acadêmico oficial da graduação da Universidade de São Paulo (USP). A consulta pública de oferecimento de turmas por disciplina é exposta pelo endpoint:

```http
GET https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=<SIGLA_DISCIPLINA>
```
*Exemplos:*  
- `https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=SMA0356` (Cálculo IV - ICMC)  
- `https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=SEM0538` (Sistemas Mecânicos - EESC)  
- `https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=7600006` (Física I - IFSC, código numérico interunidades)

### 1.1. Restrições Técnicas Fundamentais
1. **Charset e Codificação:**  
   O HTML retornado pelo Jupiterweb é codificado em **`ISO-8859-1`** (Latin-1). No Google Apps Script, o corpo da requisição DEVE ser decodificado explicitamente através de:
   ```javascript
   const html = resposta.getContentText('ISO-8859-1');
   ```
2. **Entidades HTML:**  
   O texto retornado contém uma mistura de caracteres Latin-1 e entidades HTML nomeadas (`&aacute;`, `&ccedil;`, `&atilde;`, `&eacute;`, `&otilde;`, etc.) e numéricas (`&#193;`, `&#231;`). Uma rotina de decodificação de entidades HTML deve ser executada antes de qualquer exibição ou persistência em cache.
3. **Estrutura HTML Legada:**  
   O HTML segue o padrão HTML 4.01 legado da USP (tabelas aninhadas, tags não fechadas, atributos sem aspas, ausência de semântica moderna). Por essa razão, parsers baseados em XML estrito (como `XmlService`) falham fatalmente. A extração deve ser realizada por expressões regulares (`RegExp`) e segmentação de strings otimizada para o motor V8 do Apps Script.

---

## 2. Detecção de Status e Metadados Globais

### 2.1. Disciplina Sem Oferecimento Ativo
Quando a disciplina não tem turmas cadastradas para o período letivo vigente, o Jupiterweb exibe um aviso central:
* **Padrão Encontrado:**  
  `Não existe oferecimento para a sigla informada no momento.` ou `Não existe oferecimento para a sigla`
* **Regex de Detecção (JS / V8):**
  ```javascript
  const REGEX_SEM_OFERECIMENTO = /Não existe oferecimento para a sigla/i;
  ```
* **Ação no Backend:**  
  Retornar imediatamente um objeto de **Cache Negativo** (`{ semOferecimento: true, codigo: codigo }`) e persistir no `CacheService` para evitar novas requisições desnecessárias.

### 2.2. Cabeçalho da Disciplina (Nome, Unidade e Departamento)
O topo da página exibe a sigla e o nome por extenso:
* **Exemplo:** `<b>SMA0356 - Cálculo IV</b>` ou em tabelas com tags `font`:
* **Regex de Extração de Nome da Disciplina:**
  ```javascript
  const REGEX_CABECALHO_DISCIPLINA = /<b[^>]*>\s*([A-Za-z0-9]{7})\s*-\s*([^<]+)<\/b>/i;
  ```
  - `$1`: Código oficial da disciplina (`SMA0356`).
  - `$2`: Nome por extenso (`Cálculo IV`).

---

## 3. Segmentação de Blocos de Turma

Cada turma oferecida é introduzida pela linha descritiva contendo o identificador `"Código da Turma:"`.

### 3.1. Divisão em Blocos Independentes
Em vez de tentar percorrer o HTML inteiro com uma única regex complexa, o documento é fatiado pelo delimitador do bloco de turma:
```javascript
const partesTurmas = html.split(/Código da Turma:\s*(\d+)/i);
```
- A cada iteração ímpar/par do split, obtém-se o código da turma (ex: `2026101`) e o respectivo fragmento HTML daquela turma até a próxima.

### 3.2. Estrutura do Código da Turma no Jupiterweb
O código completo possui o formato `<ANO><SEMESTRE><NÚMERO>`:
* Exemplo: `2026101`
  - `2026`: Ano letivo.
  - `1`: Semestre (1º semestre).
  - `01`: Número da turma.
* **Extração do Número Limpo da Turma:**
  ```javascript
  function extrairNumeroTurma(codigoCompleto) {
    if (!codigoCompleto) return '';
    const str = String(codigoCompleto).trim();
    // Captura os últimos 2 dígitos (ex: 2026101 -> 01)
    if (str.length >= 2) {
      return str.slice(-2);
    }
    return str;
  }
  ```

### 3.3. Metadados da Turma (Início, Fim, Tipo e Observações)
Dentro de cada bloco de turma, são extraídos:
* **Data de Início e Fim:**
  ```javascript
  const REGEX_PERIODO_TURMA = /Início:\s*<b>(\d{2}\/\d{2}\/\d{4})<\/b>\s*Fim:\s*<b>(\d{2}\/\d{2}\/\d{4})<\/b>/i;
  ```
* **Tipo / Modalidade:**
  ```javascript
  const REGEX_TIPO_TURMA = /Tipo da Turma:\s*<b>([^<]+)<\/b>/i;
  ```
  *(Valores comuns: `Teórica`, `Prática`, `Teórica/Prática`).*
* **Observações:**
  ```javascript
  const REGEX_OBS_TURMA = /Observações:\s*<\/font>\s*<\/td>\s*<td[^>]*><font[^>]*>([\s\S]*?)<\/font>/i;
  ```

---

## 4. Extração de Horários e Docentes Responsáveis

A tabela de horários de cada turma lista os dias da semana, as faixas horárias e os respectivos docentes.

### 4.1. Regex para Linhas da Tabela de Horários
```javascript
const REGEX_LINHA_HORARIO = /<tr>\s*<td[^>]*><font[^>]*>\s*(Segunda|Terça|Quarta|Quinta|Sexta|Sábado)\s*<\/font><\/td>\s*<td[^>]*><font[^>]*>\s*(\d{2}:\d{2})\s*<\/font><\/td>\s*<td[^>]*><font[^>]*>\s*(\d{2}:\d{2})\s*<\/font><\/td>\s*<td[^>]*><font[^>]*>([\s\S]*?)<\/font><\/td>/gi;
```
* **Capturas:**
  - `$1`: Dia da semana (ex: `Segunda`).
  - `$2`: Horário de início (ex: `08:00`).
  - `$3`: Horário de término (ex: `10:00`).
  - `$4`: Conteúdo da coluna do docente (pode conter nomes separados por `<br>` ou `-` quando não atribuído).

### 4.2. Sanitização e Deduplicação de Docentes
1. Se a coluna contiver `-`, `&nbsp;` ou `A Designar`, normalizar para `A Designar`.
2. Se contiver múltiplos professores separados por `<br>` ou tags HTML, quebrar e limpar:
   ```javascript
   function extrairListaDocentes(colunaHtml) {
     if (!colunaHtml) return ['A Designar'];
     const textoLimpo = colunaHtml
       .replace(/<br\s*\/?>/gi, '\n')
       .replace(/<[^>]+>/g, '')
       .trim();
     
     const linhas = textoLimpo.split('\n')
       .map(s => decodificarEntidadesHtml(s).trim())
       .filter(s => s.length > 2 && s !== '-');
     
     return linhas.length > 0 ? Array.from(new Set(linhas)) : ['A Designar'];
   }
   ```

---

## 5. Extração da Distribuição de Vagas (Dispensada)

> 💡 **Nota de Simplificação (Build 15):** A captura, armazenamento e exibição da distribuição de vagas foram removidos do sistema por serem informações dispensáveis para a consulta da grade horária, reduzindo substancialmente o tamanho do JSON trafegado, simplificando o card modal e otimizando o consumo de memória no `CacheService`.

---

## 6. Algoritmo de Casamento de Turmas (Turma Matcher)

Para correlacionar o texto da célula na grade da EESC com os dados do Júpiter:

| Texto da Célula na Grade | Turma(s) Mapeada(s) | Comportamento no Hover | Comportamento no Card |
| :--- | :---: | :--- | :--- |
| `SEM0538 - T1` | `01` | Docente da T1 | Abre com tab T1 selecionada |
| `SEM0538 - T1 e T2` | `01`, `02` | Docentes de T1 e T2 (unificados) | Abre com T1 e exibe tab T2 |
| `SME0341 - T2[1]` | `02` | Docente da T2 (ignora `[1]`) | Abre com tab T2 selecionada |
| `SEM0388 - T1 tv` | `01` | Docente da T1 (Teórica Vinculada) | Abre com tab T1 e badge Teórica |
| `SMA0300` *(sem turma)* | *Todas* | `Docentes: Várias turmas (clique para ver)` *(ou prof da única turma)* | Abre exibindo seletor de turmas |
| `SEP5864 - Pós-Grad` | *Nenhuma* | Mantém link original Janus (ignora fila) | Não abre card do Jupiterweb |
| `01/12 - prova 7600110` | *Evento* | Identifica disciplina `7600110` | Permite consulta opcional |

---

## 7. Decodificação de Entidades HTML no Apps Script

Tabela das principais entidades encontradas no HTML do Jupiterweb:

```javascript
const MAPA_ENTIDADES_HTML = {
  '&aacute;': 'á', '&Aacute;': 'Á',
  '&eacute;': 'é', '&Eacute;': 'É',
  '&iacute;': 'í', '&Iacute;': 'Í',
  '&oacute;': 'ó', '&Oacute;': 'Ó',
  '&uacute;': 'ú', '&Uacute;': 'Ú',
  '&atilde;': 'ã', '&Atilde;': 'Ã',
  '&otilde;': 'õ', '&Otilde;': 'Õ',
  '&acirc;': 'â', '&Acirc;': 'Â',
  '&ecirc;': 'ê', '&Ecirc;': 'Ê',
  '&ocirc;': 'ô', '&Ocirc;': 'Ô',
  '&ccedil;': 'ç', '&Ccedil;': 'Ç',
  '&nbsp;': ' ',
  '&amp;': '&',
  '&quot;': '"',
  '&#193;': 'Á', '&#225;': 'á',
  '&#201;': 'É', '&#233;': 'é',
  '&#205;': 'Í', '&#237;': 'í',
  '&#211;': 'Ó', '&#243;': 'ó',
  '&#218;': 'Ú', '&#250;': 'ú',
  '&#199;': 'Ç', '&#231;': 'ç'
};

function decodificarEntidadesHtml(texto) {
  if (!texto) return '';
  let res = String(texto);
  for (const [entidade, caractere] of Object.entries(MAPA_ENTIDADES_HTML)) {
    res = res.replaceAll(entidade, caractere);
  }
  // Decodifica entidades numéricas genéricas &#XXX;
  res = res.replace(/&#(\d+);/g, (_, dec) => String.fromCharCode(parseInt(dec, 10)));
  return res;
}
```

---

## 8. Estrutura do Objeto Retornado (Payload JSON)

Para cada disciplina consultada, o backend produz e armazena em cache o seguinte formato padronizado:

```json
{
  "codigo": "SMA0356",
  "nome": "Cálculo IV",
  "semOferecimento": false,
  "timestamp": "2026-09-23T11:00:00Z",
  "turmas": {
    "01": {
      "codigoTurma": "2026101",
      "numero": "01",
      "tipo": "Teórica",
      "inicio": "23/02/2026",
      "fim": "04/07/2026",
      "docentes": ["Ana Claudia Nabarro"],
      "horarios": [
        { "dia": "Segunda", "inicio": "08:00", "fim": "10:00", "docente": "Ana Claudia Nabarro" },
        { "dia": "Quarta", "inicio": "10:00", "fim": "12:00", "docente": "Ana Claudia Nabarro" }
      ],
      "observacoes": ""
    }
  }
}
```
