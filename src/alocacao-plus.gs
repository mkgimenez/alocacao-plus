/**
 * Alocação Plus - Script de Integração, Filtros e Automação 
 * Conecta a planilha PLUS à planilha FONTE (apenas leitura).
 * Arquitetura 100% dinâmica: blocos, salas e dias são lidos diretamente da planilha.
 */

const CONFIG = {
  FONTE_ID: '1AxLSuJPAGSZjvg36VaN8-mW9eogsacl2',
  NOME_ABA_FONTE: 'Grade_Horarios_Salas'
};

/**
 * Ponto de entrada do Web App no Google Apps Script (HTTP GET)
 * Renderiza o template 'Index.html' modularizado com CSS e JS
 */
function doGet(e) {
  return HtmlService.createTemplateFromFile('index')
    .evaluate()
    .setTitle('Alocação Plus - EESC-USP')
    .setFaviconUrl('https://eesc.usp.br/imgs/favicon/favicon.png')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1.0')
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

/**
 * Função auxiliar para inclusão de templates parciais (HTML, CSS, JS)
 * Padrão oficial recomendado pela documentação do Google Apps Script
 */
function include(filename) {
  return HtmlService.createHtmlOutputFromFile(filename).getContent();
}

/**
 * Cria o menu na planilha ao abrir com apenas as opções essenciais
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('💡 Plus')
    .addItem('🌐 Abrir Web App', 'mostrarLinkWebApp')
    .addItem('🧹 Limpar Cache', 'menuLimparCache')
    .addToUi();
}

/**
 * Exibe modal com o link oficial do Web App para fácil compartilhamento
 */
function mostrarLinkWebApp() {
  const url = ScriptApp.getService().getUrl();
  const ui = SpreadsheetApp.getUi();
  if (!url) {
    ui.alert(
      '🌐 Implantação do Web App',
      'O Web App ainda não foi implantado neste projeto.\n\nPara implantar:\n1. Clique no botão azul "Implantar" (canto superior direito do Apps Script).\n2. Selecione "Nova Implantação" > "Aplicativo da Web".\n3. Defina "Executar como: Eu" e "Quem tem acesso: Qualquer pessoa".',
      ui.ButtonSet.OK
    );
  } else {
    const html = HtmlService.createHtmlOutput(
      '<div style="font-family: sans-serif; padding: 15px; text-align: center;">' +
      '<h3 style="color: #104880; margin-top: 0;">🌐 Web App Alocação Plus</h3>' +
      '<p style="color: #475569; font-size: 13px;">Compartilhe este link com quem for consultar a grade:</p>' +
      '<input type="text" value="' + url + '" style="width: 100%; padding: 8px; font-size: 12px; margin: 10px 0; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box;" readonly onclick="this.select();">' +
      '<br><br>' +
      '<a href="' + url + '" target="_blank" style="display: inline-block; background: #104880; color: white; padding: 9px 18px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 12px;">Abrir Web App no Navegador 🚀</a>' +
      '</div>'
    ).setWidth(460).setHeight(220);
    ui.showModalDialog(html, '💡 Alocação Plus Web App');
  }
}

/**
 * Ação de menu para limpar cache do sistema e remover acionadores legados
 */
function menuLimparCache() {
  removerAcionadoresLegados();
  if (typeof limparCacheConfiguracoes === 'function') {
    limparCacheConfiguracoes();
  }
  SpreadsheetApp.getActiveSpreadsheet().toast('Cache limpo com sucesso!', '💡 Plus', 3);
}

/**
 * Ponto de entrada residual para acionador instalável legado.
 * Ao ser executado, remove a si próprio e encerra sem abrir painéis ou criar abas.
 */
function executarAberturaInstalada() {
  removerAcionadoresLegados();
}

/**
 * Remove acionadores instaláveis legados vinculados à planilha
 */
function removerAcionadoresLegados() {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    if (!ss) return;
    const triggers = ScriptApp.getUserTriggers(ss);
    triggers.forEach(t => {
      const handler = t.getHandlerFunction();
      if (handler === 'executarAberturaInstalada' || handler === 'abrirPainelLateral') {
        ScriptApp.deleteTrigger(t);
      }
    });
  } catch (e) {
    Logger.log('Aviso ao remover acionadores legados: ' + e.message);
  }
}

/**
 * Extrai o nome do bloco dinamicamente a partir do nome da sala
 * Ex: "A - 01" -> "Bloco A", "Laranja - 20" -> "Laranja", "Anfiteatro 1" -> "Anfiteatros"
 */
function extrairNomeBloco(nomeSala) {
  if (!nomeSala) return 'Outros';
  const s = String(nomeSala).trim();

  if (s.includes(' - ')) {
    const prefixo = s.split(' - ')[0].trim();
    if (prefixo.length <= 2) return 'Bloco ' + prefixo.toUpperCase();
    return prefixo;
  } else if (s.includes('-')) {
    const prefixo = s.split('-')[0].trim();
    if (prefixo.length <= 2) return 'Bloco ' + prefixo.toUpperCase();
    return prefixo;
  } else {
    const prefixo = s.replace(/\d+.*$/, '').trim();
    if (prefixo.toLowerCase() === 'anfiteatro') return 'Anfiteatros';
    return prefixo || 'Outros';
  }
}

/**
 * Detecta dinamicamente a configuração de colunas dos dias da semana a partir da Linha 2
 */
function obterConfigDiasGrade(sheet) {
  const lastCol = sheet.getLastColumn();
  const row2 = sheet.getRange(2, 1, 1, lastCol).getValues()[0];

  const diasEncontrados = [];
  for (let c = 2; c < row2.length; c++) {
    const val = String(row2[c]).trim();
    if (val) {
      let chave = 'seg';
      const lower = val.toLowerCase();
      if (lower.includes('seg')) chave = 'seg';
      else if (lower.includes('ter')) chave = 'ter';
      else if (lower.includes('qua')) chave = 'qua';
      else if (lower.includes('qui')) chave = 'qui';
      else if (lower.includes('sex')) chave = 'sex';
      else if (lower.includes('s') && lower.includes('b')) chave = 'sab';

      diasEncontrados.push({
        colInicio: c + 1,
        nome: val,
        chave: chave
      });
    }
  }

  const config = {};
  for (let i = 0; i < diasEncontrados.length; i++) {
    const colFim = (i + 1 < diasEncontrados.length) ? diasEncontrados[i + 1].colInicio - 1 : lastCol;
    const numCols = colFim - diasEncontrados[i].colInicio + 1;
    config[diasEncontrados[i].chave] = {
      nome: diasEncontrados[i].nome,
      colInicio: diasEncontrados[i].colInicio,
      numCols: numCols
    };
  }

  return config;
}

/**
 * Converte texto de horário (ex: '08:00 - 10:00', '14h às 16h', '19:15') em minutos a partir de 00:00
 */
function parsearFaixaHorario(rawText) {
  if (!rawText) return { inicioMin: null, fimMin: null, textoInicio: '', textoFim: '' };

  // Tratamento específico para o turno da noite (ex: 'noite')
  if (/noite/i.test(rawText)) {
    return { inicioMin: 19 * 60, fimMin: 23 * 60, textoInicio: '19:00', textoFim: '23:00' };
  }

  const p = /(\d{1,2})(?:[hH](\d{1,2})?|:(\d{2}))?\s*(?:-|às|as|a|\/)\s*(\d{1,2})(?:[hH](\d{1,2})?|:(\d{2}))?/i;
  const match = String(rawText).match(p);

  if (match) {
    const h1 = parseInt(match[1], 10);
    const m1 = parseInt(match[2] || match[3] || '0', 10);
    const h2 = parseInt(match[4], 10);
    const m2 = parseInt(match[5] || match[6] || '0', 10);

    const inicioMin = h1 * 60 + m1;
    const fimMin = h2 * 60 + m2;
    const textoInicio = (h1 < 10 ? '0' : '') + h1 + ':' + (m1 < 10 ? '0' : '') + m1;
    const textoFim = (h2 < 10 ? '0' : '') + h2 + ':' + (m2 < 10 ? '0' : '') + m2;

    return { inicioMin: inicioMin, fimMin: fimMin, textoInicio: textoInicio, textoFim: textoFim };
  }

  const pUni = /(\d{1,2})(?:[hH](\d{1,2})?|:(\d{2}))?/i;
  const matchUni = String(rawText).match(pUni);
  if (matchUni) {
    const h1 = parseInt(matchUni[1], 10);
    const m1 = parseInt(matchUni[2] || matchUni[3] || '0', 10);
    const inicioMin = h1 * 60 + m1;
    const fimMin = inicioMin + 110;
    const textoInicio = (h1 < 10 ? '0' : '') + h1 + ':' + (m1 < 10 ? '0' : '') + m1;
    const h2 = Math.floor(fimMin / 60);
    const m2 = fimMin % 60;
    const textoFim = (h2 < 10 ? '0' : '') + h2 + ':' + (m2 < 10 ? '0' : '') + m2;

    return { inicioMin: inicioMin, fimMin: fimMin, textoInicio: textoInicio, textoFim: textoFim };
  }

  return { inicioMin: null, fimMin: null, textoInicio: String(rawText), textoFim: '' };
}

/**
 * Detecta dinamicamente a estrutura completa de horários da Linha 3 mapeada por dia da Linha 2
 */
function obterEstruturaHorariosGrade(sheet) {
  const lastCol = sheet.getLastColumn();
  if (lastCol < 3) return { dias: {}, mapaPorDia: {}, listaSlots: [] };

  const row3 = sheet.getRange(3, 1, 1, lastCol).getDisplayValues()[0];
  const diasConfig = obterConfigDiasGrade(sheet);

  const listaSlots = [];
  const mapaPorDia = {};

  Object.keys(diasConfig).forEach(chaveDia => {
    mapaPorDia[chaveDia] = [];
    const diaInfo = diasConfig[chaveDia];
    const colIni = diaInfo.colInicio;
    const colFim = colIni + diaInfo.numCols - 1;

    for (let c = colIni; c <= colFim; c++) {
      const rawText = String(row3[c - 1] || '').trim();
      const infoTempo = parsearFaixaHorario(rawText);

      const slotObj = {
        col: c,
        dia: chaveDia,
        label: rawText || ('Col ' + c),
        horaInicioMin: infoTempo.inicioMin,
        horaFimMin: infoTempo.fimMin,
        textoInicio: infoTempo.textoInicio,
        textoFim: infoTempo.textoFim
      };

      listaSlots.push(slotObj);
      mapaPorDia[chaveDia].push(slotObj);
    }
  });

  return {
    dias: diasConfig,
    mapaPorDia: mapaPorDia,
    listaSlots: listaSlots
  };
}

/**
 * Extrai a lista precisa de salas e blocos da grade (a partir da linha 4 até a legenda)
 */
function obterDadosSalasEBlocos(sheet) {
  const lastRow = sheet.getLastRow();
  const range = sheet.getRange(1, 1, lastRow, 2).getValues();
  const salas = [];
  const blocosSet = new Set();

  for (let i = 0; i < range.length; i++) {
    const linhaReal = i + 1;
    if (linhaReal < 4) continue; // Linhas 1 a 3 são cabeçalhos

    const nome = String(range[i][0]).trim();
    const cap = String(range[i][1]).trim();

    // Encerra ao encontrar célula vazia ou o início da Legenda
    if (!nome || nome.toLowerCase().startsWith('legenda')) {
      break;
    }

    const bloco = extrairNomeBloco(nome);
    blocosSet.add(bloco);

    salas.push({
      nome: nome,
      capacidade: cap,
      bloco: bloco,
      linha: linhaReal
    });
  }

  return {
    salas: salas,
    blocos: Array.from(blocosSet)
  };
}



/**
 * Escapa caracteres especiais HTML para prevenir injeção de código
 */
function escapeHtml(texto) {
  if (!texto) return '';
  return String(texto)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/**
 * Reconhece códigos de disciplinas USP e transforma em links HTML (Jupiterweb ou Janus)
 */
function formatarTextoComLinksHtml(textoOriginal, urlJupiter, urlJanus) {
  if (!textoOriginal || typeof textoOriginal !== 'string') {
    return { html: '', codigos: [], ehPos: false };
  }

  const regex = /\b([A-Za-z]{3})(\d{3,4})\b|\b(\d{7})\b/g;
  let match;
  const encontrados = [];

  while ((match = regex.exec(textoOriginal)) !== null) {
    let cod = '';
    let isPos = false;
    if (match[1] && match[2]) {
      const sigla = match[1].toUpperCase();
      let num = match[2];
      if (num.length === 3) num = '0' + num;
      cod = sigla + num;
      // Graduação começa com '0'; Pós-Graduação começa com '1' a '9'
      isPos = !num.startsWith('0');
    } else if (match[3]) {
      cod = match[3];
      isPos = false; // 7 dígitos numéricos pertencem à graduação
    }

    encontrados.push({
      textoEncontrado: match[0],
      codigo: cod,
      ehPos: isPos,
      index: match.index,
      length: match[0].length
    });
  }

  if (encontrados.length === 0) {
    return {
      html: escapeHtml(textoOriginal),
      codigos: [],
      ehPos: false
    };
  }

  let htmlResult = '';
  let ultimoIndex = 0;
  let temPos = false;
  const codigos = [];

  encontrados.forEach(item => {
    htmlResult += escapeHtml(textoOriginal.substring(ultimoIndex, item.index));

    const baseUrl = item.ehPos ? urlJanus : urlJupiter;
    const linkUrl = baseUrl + encodeURIComponent(item.codigo);
    const classeCss = item.ehPos ? 'link-disc link-pos' : 'link-disc link-grad';
    const sistemaNome = item.ehPos ? 'Janus (Pós-Graduação USP)' : 'Jupiterweb (Graduação USP)';
    const titulo = 'Consultar ' + item.codigo + ' no ' + sistemaNome + ' • Abre em nova aba ↗';

    htmlResult += '<a href="' + linkUrl + '" target="_blank" rel="noopener noreferrer" class="' + classeCss + '" title="' + escapeHtml(titulo) + '">' + escapeHtml(item.textoEncontrado) + '</a>';

    if (item.ehPos) temPos = true;
    codigos.push(item.codigo);
    ultimoIndex = item.index + item.length;
  });

  htmlResult += escapeHtml(textoOriginal.substring(ultimoIndex));

  return {
    html: htmlResult,
    codigos: codigos,
    ehPos: temPos
  };
}

/**
 * Salva string JSON no CacheService dividindo em chunks caso exceda 90KB
 */
function salvarCacheEmChunks(cache, chaveBase, jsonStr, ttlSegundos) {
  const TAM_CHUNK = 90000;
  if (jsonStr.length <= TAM_CHUNK) {
    cache.put(chaveBase, jsonStr, ttlSegundos);
    cache.remove(chaveBase + '_chunks');
    return;
  }

  const totalChunks = Math.ceil(jsonStr.length / TAM_CHUNK);
  for (let i = 0; i < totalChunks; i++) {
    const pedaco = jsonStr.substring(i * TAM_CHUNK, (i + 1) * TAM_CHUNK);
    cache.put(chaveBase + '_' + i, pedaco, ttlSegundos);
  }
  cache.put(chaveBase + '_chunks', String(totalChunks), ttlSegundos);
  cache.remove(chaveBase);
}

/**
 * Recupera string JSON do CacheService remontando os chunks se necessário
 */
function obterCacheEmChunks(cache, chaveBase) {
  const qtdStr = cache.get(chaveBase + '_chunks');
  if (qtdStr) {
    const totalChunks = parseInt(qtdStr, 10);
    let strCompleta = '';
    for (let i = 0; i < totalChunks; i++) {
      const pedaco = cache.get(chaveBase + '_' + i);
      if (!pedaco) return null; // Expirou algum pedaço
      strCompleta += pedaco;
    }
    return strCompleta;
  }
  return cache.get(chaveBase);
}

/**
 * Endpoint principal chamado pelo Frontend do Web App via google.script.run
 * Extrai a grade completa diretamente da FONTE em memória, processa células mescladas,
 * formata links de disciplinas e gerencia cache para velocidade instantânea.
 */
function obterDadosGradeWeb(forcarAtualizacao) {
  try {
    const cfg = (typeof obterConfiguracoes === 'function')
      ? obterConfiguracoes(forcarAtualizacao)
      : {
          FONTE_ID: CONFIG.FONTE_ID,
          FONTE_ABA: CONFIG.NOME_ABA_FONTE,
          URL_JUPITER: 'https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=',
          URL_JANUS: 'https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=',
          CACHE_MINUTOS: 60
        };

    const cache = CacheService.getScriptCache();
    const cacheKey = 'ALOCACAO_PLUS_GRADE_WEB_CACHE';

    if (!forcarAtualizacao) {
      const cached = obterCacheEmChunks(cache, cacheKey);
      if (cached) {
        try {
          return { sucesso: true, dados: JSON.parse(cached), doCache: true };
        } catch (e) {
          // Parse falhou, reconstrói
        }
      }
    }

    // Conecta diretamente à planilha FONTE oficial
    const fonteSs = SpreadsheetApp.openById(cfg.FONTE_ID);
    const sheet = fonteSs.getSheetByName(cfg.FONTE_ABA);
    if (!sheet) {
      return {
        sucesso: false,
        msg: 'Aba "' + cfg.FONTE_ABA + '" não encontrada na planilha FONTE (' + cfg.FONTE_ID + '). Verifique a aba _Config.'
      };
    }

    const estrutura = obterEstruturaHorariosGrade(sheet);
    const dadosSalas = obterDadosSalasEBlocos(sheet);
    const listaSalas = dadosSalas.salas || [];

    if (listaSalas.length === 0) {
      return {
        sucesso: false,
        msg: 'Nenhuma sala encontrada na grade da planilha FONTE.'
      };
    }

    const linhaInicio = listaSalas[0].linha;
    const linhaFim = listaSalas[listaSalas.length - 1].linha;
    const numLinhas = linhaFim - linhaInicio + 1;
    const lastCol = sheet.getLastColumn();
    const numCols = lastCol - 2; // Começa na coluna 3 (C)

    if (numCols <= 0) {
      return {
        sucesso: false,
        msg: 'Colunas de horários insuficientes na planilha FONTE.'
      };
    }

    // Leitura em lote de toda a matriz da grade
    const rangeGrade = sheet.getRange(linhaInicio, 3, numLinhas, numCols);
    const matrizDisplay = rangeGrade.getDisplayValues();
    const matrizCores = rangeGrade.getBackgrounds();
    const mergedRanges = rangeGrade.getMergedRanges();

    // Mapeamento de Células Mescladas (Merges)
    // mapaMerges[r][c] guardará se a célula tem colspan/rowspan ou se está coberta
    const mapaMerges = Array.from({ length: numLinhas }, () => ({}));

    mergedRanges.forEach(mr => {
      const topR = mr.getRow() - linhaInicio;
      const topC = mr.getColumn() - 3;
      const numR = mr.getNumRows();
      const numC = mr.getNumColumns();

      if (topR >= 0 && topR < numLinhas && topC >= 0 && topC < numCols) {
        if (!mapaMerges[topR][topC]) mapaMerges[topR][topC] = {};
        mapaMerges[topR][topC].colspan = numC;
        mapaMerges[topR][topC].rowspan = numR;

        // Marca todas as células internas do retângulo como cobertas
        for (let r = 0; r < numR; r++) {
          for (let c = 0; c < numC; c++) {
            if (r === 0 && c === 0) continue; // Pula a célula de origem
            const curR = topR + r;
            const curC = topC + c;
            if (curR < numLinhas && curC < numCols) {
              if (!mapaMerges[curR][curC]) mapaMerges[curR][curC] = {};
              mapaMerges[curR][curC].coberto = true;
            }
          }
        }
      }
    });

    // Construção da Matriz Otimizada da Grade para envio ao Frontend
    const matrizGradeOtimizada = [];

    for (let r = 0; r < numLinhas; r++) {
      const linhaArray = [];
      for (let c = 0; c < numCols; c++) {
        const merge = mapaMerges[r][c];
        if (merge && merge.coberto) {
          linhaArray.push({ c: 1 }); // Indicador ultra-compacto de célula coberta
          continue;
        }

        const rawText = matrizDisplay[r] && matrizDisplay[r][c] ? matrizDisplay[r][c].trim() : '';

        if (!rawText) {
          if (merge && (merge.colspan > 1 || merge.rowspan > 1)) {
            linhaArray.push({
              cs: merge.colspan > 1 ? merge.colspan : undefined,
              rs: merge.rowspan > 1 ? merge.rowspan : undefined
            });
          } else {
            linhaArray.push(null); // Compacto: célula vazia simples
          }
          continue;
        }

        // Célula com conteúdo (aula, prova, reserva, evento)
        const parsed = formatarTextoComLinksHtml(rawText, cfg.URL_JUPITER, cfg.URL_JANUS);
        const corBg = (matrizCores[r] && matrizCores[r][c] && matrizCores[r][c].toLowerCase() !== '#ffffff')
          ? matrizCores[r][c].toLowerCase()
          : null;

        const celObj = {
          t: rawText,
          h: parsed.html
        };

        if (parsed.codigos.length > 0) celObj.d = parsed.codigos;
        if (parsed.ehPos) celObj.pos = true;
        if (merge && merge.colspan > 1) celObj.cs = merge.colspan;
        if (merge && merge.rowspan > 1) celObj.rs = merge.rowspan;
        if (corBg) celObj.bg = corBg;

        linhaArray.push(celObj);
      }
      matrizGradeOtimizada.push(linhaArray);
    }

    const agora = Utilities.formatDate(new Date(), 'America/Sao_Paulo', 'dd/MM/yyyy HH:mm:ss');

    const diasLista = Object.keys(estrutura.dias).map(chave => ({
      chave: chave,
      nome: estrutura.dias[chave].nome,
      colInicio: estrutura.dias[chave].colInicio,
      numCols: estrutura.dias[chave].numCols
    }));

    const salasLista = listaSalas.map((s, idx) => ({
      idx: idx,
      nome: s.nome,
      capacidade: s.capacidade,
      capacidadeNum: parseInt(String(s.capacidade).replace(/\D/g, ''), 10) || 0,
      bloco: s.bloco,
      linha: s.linha
    }));

    const pacoteDados = {
      timestamp: agora,
      fonteId: cfg.FONTE_ID,
      fonteAba: cfg.FONTE_ABA,
      dias: diasLista,
      slots: estrutura.listaSlots,
      estruturaHorarios: estrutura,
      salas: salasLista,
      blocos: dadosSalas.blocos,
      grade: matrizGradeOtimizada
    };

    // Salva no cache com suporte a chunks
    const ttlSegundos = Math.min((cfg.CACHE_MINUTOS || 60) * 60, 21600);
    const jsonStr = JSON.stringify(pacoteDados);
    salvarCacheEmChunks(cache, cacheKey, jsonStr, ttlSegundos);

    return { sucesso: true, dados: pacoteDados, doCache: false };

  } catch (err) {
    Logger.log('Erro em obterDadosGradeWeb: ' + err.stack);
    return { sucesso: false, msg: 'Erro ao extrair grade da FONTE: ' + err.message };
  }
}
