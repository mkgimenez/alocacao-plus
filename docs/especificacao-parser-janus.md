# Especificação Técnica do Parser HTML do Janus (Pós-Graduação)

**Projeto:** Alocação Plus (EESC-USP)  
**Documento:** Regras de Parsing, Expressões Regulares, Otimização de Rede e Sanitização para Dados do Janus (USP)  
**Versão de Referência:** 1.0  
**Data:** 24/09/2026  

---

## 1. Visão Geral da Arquitetura do Janus

O **Janus** é o sistema acadêmico oficial da pós-graduação da Universidade de São Paulo (USP). Diferentemente do Jupiterweb (onde uma única URL devolve todas as turmas de uma vez), o Janus separa a consulta em duas páginas:

1. **Página de Catálogo / Busca de Oferecimento:**
   ```http
   GET https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=<SIGLA_DISCIPLINA>
   ```
   *Exemplos:*
   - `https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=SEP5864` (Design Science Research - Engenharia de Produção)
   - `https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=SHS5991` (Sistemas Biológicos - Hidráulica e Saneamento)
   - `https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=SEM5900` (Sem oferecimento ativo)

2. **Bypass da Casca Intermediária JSF (Otimização de Rede):**
   Na página `DisciplinaAux`, o link de turma possui o formato relativo:
   ```html
   <a target="_parent" href="publico/turma/SEP5864/1"><img src="imagens/icone/clock.gif" border="0"></a>
   ```
   Acessar essa URL intermediária resulta em um documento JSF pesado de ~50 KB contendo essencialmente um `<iframe>`:
   ```html
   <IFRAME name="casca" id="casca" src="../TurmaDet?sgldis=SEP5864&ofe=1&" frameBorder="0" width="800" height="700" scrolling="auto"></IFRAME>
   ```
   A página interna `TurmaDet` é pública, leve, rápida e acessível diretamente via GET sem cookies ou sessão JSF:
   ```http
   GET https://uspdigital.usp.br/janus/TurmaDet?sgldis=<SIGLA>&ofe=<OFE>&
   ```
   O pipeline do Alocação Plus executa **rigorosamente 2 etapas HTTP diretas**:
   - **Etapa 1:** `DisciplinaAux?tipo=T&sgldis=...` (extrai nome e IDs de oferecimento);
   - **Etapa 2:** `TurmaDet?sgldis=...&ofe=...` (extrai docentes, horários, locais, datas e modalidade).

---

## 2. Codificação, Charset e Entidades Tipográficas

1. **Charset e Decodificação:**
   O HTML do Janus declara `charset=iso-8859-1`, mas frequentemente contém caracteres tipográficos da tabela **Windows-1252** (por exemplo, travessão *en-dash* `–`, byte `0x96`, presente em `SHS5991`).
   - No Google Apps Script:
     ```javascript
     let html = '';
     try {
       html = resp.getContentText('windows-1252');
     } catch (eCharset) {
       html = resp.getContentText('ISO-8859-1');
     }
     ```
   - No caso de decodificação ISO-8859-1, bytes `0x80` a `0x9F` devem ser mapeados para caracteres Unicode (ex.: `\u0096` $\rightarrow$ `\u2013` `–`).

2. **Entidades Numéricas e Nomeadas:**
   O Janus renderiza caracteres acentuados tanto em texto direto quanto em entidades HTML decimais (`&#193;`, `&#227;`, `&#231;`) e nomeadas (`&oacute;`). Uma função de expansão de entidades deve ser aplicada a todos os textos extraídos.

---

## 3. Ancoragem Estrita em Classes CSS (`.intl_*`)

O Janus emprega a biblioteca DWR (`RotuloControleDWR.js`) para internacionalização dinâmica no navegador. No HTML estático retornado para o servidor (Apps Script / Python), **os textos de cabeçalho estão vazios**:
```html
<span class='label intl_docenteMinistrante'></span>
<span class='label intl_horario'></span> / <span class='label intl_local'></span>:
<span class='label intl_dataInicial'></span>:
<span class='label intl_formaOferecimento'></span>:
```

> ⚠️ **REGRA FUNDAMENTAL DO PARSER:** Expressões regulares **jamais** devem buscar por textos em português (`"Docente Ministrante"`, `"Data Inicial"`, etc.), mas sim ancorar estritamente nas classes CSS semânticas (`intl_docenteMinistrante`, `intl_horario`, `intl_local`, `intl_dataInicial`, `intl_formaOferecimento`).

---

## 4. Regras de Extração — Etapa 1: `DisciplinaAux`

### 4.1. Detecção de Disciplina Sem Oferecimento Ativo
Quando a disciplina não tem turmas oferecidas no momento:
* **Padrão Encontrado:** `Não existem oferecimentos para a disciplina <SIGLA>.`
* **Regex de Detecção:**
  ```javascript
  const REGEX_SEM_OFERECIMENTO_JANUS = /N(?:ã|a|&atilde;|&#227;)o\s+existem\s+oferecimentos/i;
  ```
* **Ação:** Retornar imediatamente cache negativo com TTL de 6h (`semOferecimento: true`).

### 4.2. Extração do Nome da Disciplina
Na tabela de resultados de `DisciplinaAux`:
* **Padrão Encontrado:**
  ```html
  <td align="center" width="8%"><font ...>SEP5864</font></td>
  <td width="67%" align="left"><div align="left"> <font ...>Nome da Disciplina</font></div></td>
  ```
* **Regex de Extração:**
  ```javascript
  const REGEX_NOME_JANUS = /<td[^>]*width=["']?67%["']?[^>]*>[\s\S]*?<div[^>]*>[\s\S]*?<font[^>]*>([\s\S]*?)<\/font>/i;
  ```

### 4.3. Extração dos Links de Oferecimento (`ofe`)
* **Padrão Encontrado:**
  ```html
  <a target="_parent" href="publico/turma/SEP5864/1"><img src="imagens/icone/clock.gif" border="0"></a>
  ```
* **Regex de Extração:**
  ```javascript
  const REGEX_LINK_OFE = /publico\/turma\/[A-Za-z0-9]+\/(\d+)/gi;
  ```
  Permite capturar múltiplos oferecimentos (`ofe=1`, `ofe=2`) caso existam.

---

## 5. Regras de Extração — Etapa 2: `TurmaDet`

### 5.1. Datas e Cálculo de Período
* **Padrão de Datas:**
  ```html
  <span class='label intl_dataInicial'></span>: </span></font><font ...><span ...>\s*(\d{2}\/\d{2}\/\d{4})
  <span class='label intl_dataFinal'></span>: </span></font><font ...><span ...>\s*(\d{2}\/\d{2}\/\d{4})
  ```
* **Classificação de Período:**
  - Calcula a diferença em dias entre a data final e a inicial.
  - $\le 185$ dias $\rightarrow$ `"Semestral"`;
  - $> 185$ dias $\rightarrow$ `"Anual"`.

### 5.2. Modalidade / Forma de Oferecimento
* **Padrão Encontrado:**
  ```html
  <span class='label intl_formaOferecimento'></span>: </span></font><font ...><span ...>\s*([^\s<]+)
  ```
  Valores comuns: `Presencial`, `Remoto` / `A distância`, `Híbrido`.

### 5.3. Docentes Ministrantes
* **Padrão Encontrado:** Tabela subsequente ao rótulo `intl_docenteMinistrante`:
  ```html
  <tr bgcolor=#336699> ... <span class='label intl_docenteMinistrante'></span> ... </tr>
  <tr><td bgcolor="#FFFFFF" nowrap><font ...><span ...>Nome do Docente</span></font></td></tr>
  ```
  O parser captura todos os docentes presentes nas linhas `<tr>` subsequentes até o fechamento da tabela.

### 5.4. Tabela de Horários e Locais
* **Padrão Encontrado:** Tabela de 3 colunas subsequente a `intl_horario` / `intl_local`:
  ```html
  <tr>
    <td bgcolor="#FFFFFF"><font ...><span ...>Segunda</span></font></td>
    <td bgcolor="#FFFFFF"><font ...><span ...>08:00 - 11:00</span></font></td>
    <td bgcolor="#FFFFFF"><font ...><span ...>Engenharia de Produção                  </span></font></td>
  </tr>
  ```
  - Coluna 1: Dia da semana (`Segunda`, `Terça`, `Quarta`, `Quinta`, `Sexta`, `Sábado`);
  - Coluna 2: Horário de início e término (`08:00 - 11:00`);
  - Coluna 3: Local de aula (`Engenharia de Produção` ou `sala de aula`). Espaços excedentes são limpos via `.trim()`.

---

## 6. Schema JSON Unificado

O resultado é integrado ao schema canônico do Alocação Plus com indexação de 2 dígitos:

```json
{
  "codigo": "SEP5864",
  "nome": "Design Science Research: Preparação Pedagógica, Estratégia de Pesquisa, Metodologias e Métodos",
  "sistema": "janus",
  "semOferecimento": false,
  "timestamp": "2026-09-24T15:00:00Z",
  "turmas": {
    "01": {
      "codigoTurma": "SEP5864-1",
      "numero": "01",
      "tipo": "Presencial",
      "periodo": "Semestral",
      "inicio": "03/08/2026",
      "fim": "23/08/2026",
      "docentes": ["Fabio Muller Guerrini"],
      "horarios": [
        {
          "dia": "Segunda",
          "inicio": "08:00",
          "fim": "11:00",
          "docente": "Fabio Muller Guerrini",
          "professores": ["Fabio Muller Guerrini"],
          "local": "Engenharia de Produção"
        },
        {
          "dia": "Quarta",
          "inicio": "08:00",
          "fim": "11:00",
          "docente": "Fabio Muller Guerrini",
          "professores": ["Fabio Muller Guerrini"],
          "local": "Engenharia de Produção"
        }
      ],
      "observacoes": "Local: Engenharia de Produção"
    }
  }
}
```
