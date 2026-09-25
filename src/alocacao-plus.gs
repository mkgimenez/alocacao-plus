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
 * Cria o menu na planilha ao abrir com opções essenciais
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('💡 Plus')
    .addItem('🌐 Abrir Web App', 'mostrarLinkWebApp')
    .addItem('📊 Abrir Métricas', 'abrirAbaMetricas')
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

const MAPA_ENTIDADES_HTML_GAS = {
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
  '&ndash;': '–',
  '&#8211;': '–',
  '\u0096': '–',
  '&#193;': 'Á', '&#225;': 'á',
  '&#201;': 'É', '&#233;': 'é',
  '&#205;': 'Í', '&#237;': 'í',
  '&#211;': 'Ó', '&#243;': 'ó',
  '&#218;': 'Ú', '&#250;': 'ú',
  '&#199;': 'Ç', '&#231;': 'ç',
  '&#195;': 'Ã', '&#227;': 'ã',
  '&#213;': 'Õ', '&#245;': 'õ'
};

/**
 * Converte entidades HTML comuns e numéricas para caracteres acentuados legíveis
 */
function decodificarEntidadesHtml(texto) {
  if (!texto) return '';
  let res = String(texto);
  for (const entidade in MAPA_ENTIDADES_HTML_GAS) {
    if (res.includes(entidade)) {
      res = res.split(entidade).join(MAPA_ENTIDADES_HTML_GAS[entidade]);
    }
  }
  res = res.replace(/&#(\d+);/g, (_, dec) => String.fromCharCode(parseInt(dec, 10)));
  return res.replace(/\s+/g, ' ').trim();
}

/**
 * Parser da Etapa 1 do Janus: Página DisciplinaAux.
 * Extrai nome da disciplina, detecta se há oferecimento ativo e coleta IDs de oferecimento (ofe).
 *
 * @param {string} codigo - Sigla da disciplina (ex: "SEP5864")
 * @param {string} html - Conteúdo HTML da página DisciplinaAux
 * @returns {Object} { codigo, nome, semOferecimento, oferecimentos: string[] }
 */
function parsearHtmlJanusDisciplina(codigo, html) {
  if (!html || typeof html !== 'string') {
    return { codigo: codigo, nome: '', semOferecimento: true, oferecimentos: [] };
  }

  // 1. Detecção de disciplina sem oferecimento ativo
  if (/N(?:ã|a|&atilde;|&#227;)o\s+existem\s+oferecimentos/i.test(html)) {
    return { codigo: codigo, nome: '', semOferecimento: true, oferecimentos: [] };
  }

  // 2. Extração do Nome da Disciplina (ancorado na linha contendo o código)
  let nomeDisciplina = '';
  const regexAncorada = new RegExp(codigo + '[\\s\\S]*?<td[^>]*width=["\']?67%["\']?[^>]*>[\\s\\S]*?<div[^>]*>[\\s\\S]*?<font[^>]*>([\\s\\S]*?)<\\/font>', 'i');
  const mNome = html.match(regexAncorada);
  if (mNome) {
    nomeDisciplina = decodificarEntidadesHtml(mNome[1].replace(/<[^>]+>/g, ' '));
  } else {
    // Fallback 1: Busca em coluna width="67%" descartando a palavra "Nome"
    const mNomesTodos = html.match(/<td[^>]*width=["']?67%["']?[^>]*>[\s\S]*?<div[^>]*>[\s\S]*?<font[^>]*>([\s\S]*?)<\/font>/gi) || [];
    for (let i = 0; i < mNomesTodos.length; i++) {
      const matchSub = mNomesTodos[i].match(/<font[^>]*>([\s\S]*?)<\/font>/i);
      if (matchSub) {
        const candLimpo = decodificarEntidadesHtml(matchSub[1].replace(/<[^>]+>/g, ' '));
        if (candLimpo && candLimpo.toLowerCase() !== 'nome') {
          nomeDisciplina = candLimpo;
          break;
        }
      }
    }
    // Fallback 2: Busca por alinhamento à esquerda descartando "Nome"
    if (!nomeDisciplina) {
      const mLeft = html.match(/<td[^>]*align=["']?left["']?[^>]*>[\s\S]*?<div[^>]*>[\s\S]*?<font[^>]*>([\s\S]*?)<\/font>/gi) || [];
      for (let j = 0; j < mLeft.length; j++) {
        const matchLeftSub = mLeft[j].match(/<font[^>]*>([\s\S]*?)<\/font>/i);
        if (matchLeftSub) {
          const candLeftLimpo = decodificarEntidadesHtml(matchLeftSub[1].replace(/<[^>]+>/g, ' '));
          if (candLeftLimpo && candLeftLimpo.toLowerCase() !== 'nome') {
            nomeDisciplina = candLeftLimpo;
            break;
          }
        }
      }
    }
  }

  // 3. Coleta de IDs de oferecimento (publico/turma/<codigo>/<ofe>)
  const oferecimentos = [];
  const padraoLink = /publico\/turma\/[A-Za-z0-9]+\/(\d+)/gi;
  let matchOfe;
  while ((matchOfe = padraoLink.exec(html)) !== null) {
    const num = String(parseInt(matchOfe[1], 10));
    if (!oferecimentos.includes(num)) {
      oferecimentos.push(num);
    }
  }

  if (oferecimentos.length === 0) {
    return { codigo: codigo, nome: nomeDisciplina, semOferecimento: true, oferecimentos: [] };
  }

  return {
    codigo: codigo,
    nome: nomeDisciplina,
    semOferecimento: false,
    oferecimentos: oferecimentos
  };
}

/**
 * Parser da Etapa 2 do Janus: Página TurmaDet.
 * Extrai datas, modalidade, docentes ministrantes, horários e locais ancorando em classes .intl_*.
 *
 * @param {string} codigo - Sigla da disciplina (ex: "SEP5864")
 * @param {string} html - Conteúdo HTML da página TurmaDet
 * @param {string|number} numTurma - Número do oferecimento (ex: "1")
 * @returns {Object|null} Objeto da turma com schema canônico
 */
function parsearHtmlJanusTurma(codigo, html, numTurma) {
  if (!html || typeof html !== 'string') return null;

  const num = numTurma !== undefined && numTurma !== null ? String(numTurma) : '1';
  const numCan = /^\d+$/.test(num) ? num.padStart(2, '0') : num;
  const codigoTurma = codigo + '-' + num;

  // 1. Datas e Cálculo de Período
  let inicio = '';
  let fim = '';
  const mIni = html.match(/class=['"][^'"]*intl_dataInicial[^'"]*['"][^>]*>[\s\S]*?(\d{2}\/\d{2}\/\d{4})/i);
  if (mIni) inicio = mIni[1].trim();

  const mFim = html.match(/class=['"][^'"]*intl_dataFinal[^'"]*['"][^>]*>[\s\S]*?(\d{2}\/\d{2}\/\d{4})/i);
  if (mFim) fim = mFim[1].trim();

  let periodo = 'Semestral';
  if (inicio && fim) {
    try {
      const partesIni = inicio.split('/');
      const partesFim = fim.split('/');
      const dIni = new Date(parseInt(partesIni[2], 10), parseInt(partesIni[1], 10) - 1, parseInt(partesIni[0], 10));
      const dFim = new Date(parseInt(partesFim[2], 10), parseInt(partesFim[1], 10) - 1, parseInt(partesFim[0], 10));
      const diffDias = Math.round((dFim.getTime() - dIni.getTime()) / (1000 * 60 * 60 * 24));
      if (diffDias > 185) {
        periodo = 'Anual';
      }
    } catch (ePeriodo) {
      periodo = 'Semestral';
    }
  }

  // 2. Modalidade / Forma de Oferecimento (.intl_formaOferecimento)
  let tipoTurma = 'Presencial';
  const mForma = html.match(/class=['"][^'"]*intl_formaOferecimento[^'"]*['"][^>]*>[\s\S]*?<font[^>]*>(?:<span[^>]*>)?\s*([^\s<]+)/i);
  if (mForma) {
    const formaRaw = decodificarEntidadesHtml(mForma[1]).toLowerCase();
    if (formaRaw.includes('presenc')) {
      tipoTurma = 'Presencial';
    } else if (formaRaw.includes('remot') || formaRaw.includes('dist') || formaRaw.includes('ead')) {
      tipoTurma = 'Remota';
    } else if (formaRaw.includes('hibrid')) {
      tipoTurma = 'Híbrida';
    } else {
      tipoTurma = decodificarEntidadesHtml(mForma[1]);
    }
  }

  // 3. Docentes Ministrantes (.intl_docenteMinistrante)
  const docentes = [];
  const mDocBloco = html.match(/class=['"][^'"]*intl_docenteMinistrante[^'"]*['"][\s\S]*?<\/table>/i);
  if (mDocBloco) {
    const blocoHtml = mDocBloco[0];
    const reLinhasDoc = /<td[^>]*nowrap[^>]*>[\s\S]*?<font[^>]*>(?:<span[^>]*>)?([\s\S]*?)(?:<\/span>)?<\/font>/gi;
    let mLinha;
    while ((mLinha = reLinhasDoc.exec(blocoHtml)) !== null) {
      const docLimpo = decodificarEntidadesHtml(mLinha[1].replace(/<[^>]+>/g, ' '));
      if (docLimpo && docLimpo !== '-' && docLimpo.toLowerCase() !== 'a designar' && !docentes.includes(docLimpo)) {
        docentes.push(docLimpo);
      }
    }
  }

  // 4. Tabela de Horários e Locais (.intl_horario / .intl_local)
  const horarios = [];
  const locaisEncontrados = [];
  const mHorBloco = html.match(/class=['"][^'"]*(?:intl_horario|intl_local)[^'"]*['"][\s\S]*?<table[^>]*>([\s\S]*?)<\/table>/i);
  if (mHorBloco) {
    const tabelaHorarios = mHorBloco[1];
    const reTr = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
    let mTr;
    while ((mTr = reTr.exec(tabelaHorarios)) !== null) {
      const conteudoTr = mTr[1];
      const reTd = /<td[^>]*>([\s\S]*?)<\/td>/gi;
      const tds = [];
      let mTd;
      while ((mTd = reTd.exec(conteudoTr)) !== null) {
        tds.push(mTd[1]);
      }

      if (tds.length >= 3) {
        const dia = decodificarEntidadesHtml(tds[0].replace(/<[^>]+>/g, ' '));
        const horaStr = decodificarEntidadesHtml(tds[1].replace(/<[^>]+>/g, ' '));
        const local = decodificarEntidadesHtml(tds[2].replace(/<[^>]+>/g, ' '));

        let inicioHora = '';
        let fimHora = '';
        if (horaStr.includes('-')) {
          const partesHora = horaStr.split('-');
          inicioHora = partesHora[0].trim();
          fimHora = partesHora.length > 1 ? partesHora[1].trim() : '';
        } else if (/às|as/i.test(horaStr)) {
          const partesHora = horaStr.split(/\s+(?:às|as)\s+/i);
          inicioHora = partesHora[0].trim();
          fimHora = partesHora.length > 1 ? partesHora[1].trim() : '';
        } else {
          inicioHora = horaStr.trim();
        }

        if (local && !locaisEncontrados.includes(local)) {
          locaisEncontrados.push(local);
        }

        horarios.push({
          dia: dia,
          inicio: inicioHora,
          fim: fimHora,
          docente: docentes.length > 0 ? docentes[0] : 'A Designar',
          professores: docentes.slice(),
          local: local
        });
      }
    }
  }

  // 5. Idioma ministrado (.intl_idiomaMinistrado)
  let idioma = 'Português';
  const mIdioma = html.match(/intl_idiomaMinistrado[\s\S]*?<span[^>]*class=['"]txt_arial_10pt_black['"][^>]*>([^<]+)<\/span>/i);
  if (mIdioma) {
    const rawId = decodificarEntidadesHtml(mIdioma[1]).trim();
    if (/ingl|engl/i.test(rawId)) {
      idioma = 'Inglês';
    } else if (/portug/i.test(rawId)) {
      idioma = 'Português';
    } else if (/espanh|span/i.test(rawId)) {
      idioma = 'Espanhol';
    } else if (/franc/i.test(rawId)) {
      idioma = 'Francês';
    } else if (rawId) {
      idioma = rawId;
    }
  }

  // 6. Número de Vagas (ancorado em intl_numeroVagas ou Número de vagas)
  let vagas = null;
  const mVagasBloco = html.match(/(?:intl_numeroVagas|N[uú]mero\s+de\s+[Vv]agas)[\s\S]*?<table[^>]*>([\s\S]*?)<\/table>/i);
  if (mVagasBloco) {
    const tabelaConteudo = mVagasBloco[1];
    const reTr = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
    const linhasTr = [];
    let mTr;
    while ((mTr = reTr.exec(tabelaConteudo)) !== null) {
      linhasTr.push(mTr[1]);
    }

    if (linhasTr.length > 0) {
      let idxTotal = -1;
      const reTdCab = /<td[^>]*>([\s\S]*?)<\/td>/gi;
      const tdsCab = [];
      let mTd;
      while ((mTd = reTdCab.exec(linhasTr[0])) !== null) {
        tdsCab.push(mTd[1]);
      }

      for (let idx = 0; idx < tdsCab.length; idx++) {
        const textoCab = decodificarEntidadesHtml(tdsCab[idx].replace(/<[^>]+>/g, ' ')).trim();
        if (/total/i.test(textoCab) || tdsCab[idx].toLowerCase().includes('intl_total')) {
          idxTotal = idx;
          break;
        }
      }

      if (idxTotal === -1 && tdsCab.length > 0) {
        idxTotal = tdsCab.length - 1;
      }

      for (let r = 1; r < linhasTr.length; r++) {
        const reTdDados = /<td[^>]*>([\s\S]*?)<\/td>/gi;
        const tdsDados = [];
        let mVal;
        while ((mVal = reTdDados.exec(linhasTr[r])) !== null) {
          tdsDados.push(mVal[1]);
        }
        if (tdsDados.length === 0) continue;

        if (idxTotal >= 0 && idxTotal < tdsDados.length) {
          const valRaw = decodificarEntidadesHtml(tdsDados[idxTotal].replace(/<[^>]+>/g, ' ')).trim();
          const valLimpo = valRaw.replace(/[^\d]/g, '');
          if (valLimpo) {
            vagas = parseInt(valLimpo, 10);
            break;
          }
        }

        if (vagas === null) {
          for (let c = tdsDados.length - 1; c >= 0; c--) {
            const valRaw = decodificarEntidadesHtml(tdsDados[c].replace(/<[^>]+>/g, ' ')).trim();
            const valLimpo = valRaw.replace(/[^\d]/g, '');
            if (valLimpo) {
              vagas = parseInt(valLimpo, 10);
              break;
            }
          }
          if (vagas !== null) break;
        }
      }
    }
  }

  let obs = '';
  if (locaisEncontrados.length > 0) {
    obs = 'Local: ' + locaisEncontrados.sort().join(', ');
  }

  return {
    codigoTurma: codigoTurma,
    numero: numCan,
    ofe: String(parseInt(num, 10) || num),
    tipo: tipoTurma,
    periodo: periodo,
    inicio: inicio,
    fim: fim,
    docentes: docentes,
    horarios: horarios,
    idioma: idioma,
    observacoes: obs,
    vagas: vagas
  };
}

/**
 * Parser de HTML do Jupiterweb no Apps Script (V8)
 * Extrai turmas, horários oficiais e docentes.
 */
function parsearHtmlJupiterweb(codigo, html) {
  if (!html || typeof html !== 'string') {
    return { codigo: codigo, nome: '', semOferecimento: true, turmas: {} };
  }

  // 1. Verifica ausência de oferecimento ativo
  if (/existe\s+oferecimento\s+para\s+a\s+sigla/i.test(html)) {
    return { codigo: codigo, nome: '', semOferecimento: true, turmas: {} };
  }

  // 2. Extrai cabeçalho (Nome da Disciplina)
  let nomeDisciplina = '';
  const matchCab = html.match(/(?:[A-Za-z]{3}\d{4}|\d{7})\s*-\s*([^<]+)<\/b>/i);
  if (matchCab) {
    nomeDisciplina = decodificarEntidadesHtml(matchCab[1]);
  }

  // 3. Segmenta blocos de turmas
  const padraoSplit = /C(?:[oó\u00f3\ufffd]|&oacute;)?digo\s+da\s+Turma:[\s\S]*?<td[^>]*>[\s\S]*?(\d{7})/gi;
  const partes = html.split(padraoSplit);

  if (partes.length < 2) {
    return { codigo: codigo, nome: nomeDisciplina, semOferecimento: true, turmas: {} };
  }

  const turmas = {};

  for (let i = 1; i < partes.length; i += 2) {
    const codTurma = String(partes[i]).trim();
    const chunk = partes[i + 1] || '';

    // Número limpo da turma (últimos 2 dígitos, ex: 2026201 -> 01)
    const numTurma = codTurma.length >= 2 ? codTurma.slice(-2) : codTurma;

    // Início e Fim
    let inicio = '';
    let fim = '';
    const mInicio = chunk.match(/In&iacute;cio:[\s\S]*?<td[^>]*>[\s\S]*?(\d{2}\/\d{2}\/\d{4})/i);
    if (mInicio) inicio = mInicio[1];
    const mFim = chunk.match(/Fim:[\s\S]*?<td[^>]*>[\s\S]*?(\d{2}\/\d{2}\/\d{4})/i);
    if (mFim) fim = mFim[1];

    // Período (Semestral ou Anual)
    let periodo = 'Semestral';
    if (inicio && fim) {
      const pIni = inicio.split('/');
      const pFim = fim.split('/');
      if (pIni.length === 3 && pFim.length === 3) {
        const dtIni = new Date(parseInt(pIni[2], 10), parseInt(pIni[1], 10) - 1, parseInt(pIni[0], 10));
        const dtFim = new Date(parseInt(pFim[2], 10), parseInt(pFim[1], 10) - 1, parseInt(pFim[0], 10));
        const diffDias = (dtFim - dtIni) / (1000 * 60 * 60 * 24);
        if (diffDias > 185) {
          periodo = 'Anual';
        }
      }
    }

    // Tipo da Turma
    let tipoTurma = 'Teórica';
    const mTipo = chunk.match(/Tipo\s+da\s+Turma:[\s\S]*?<td[^>]*><font[^>]*><span[^>]*>\s*([^\s<]+)/i);
    if (mTipo) {
      const tipoRaw = decodificarEntidadesHtml(mTipo[1]);
      if (tipoRaw.includes('Pr')) tipoTurma = 'Prática';
      else if (tipoRaw.includes('Te')) tipoTurma = 'Teórica';
      else tipoTurma = tipoRaw;
    }

    // Observações
    let observacoes = '';
    const mObs = chunk.match(/Observa[^\:]*?:[\s\S]*?<td[^>]*><font[^>]*><span[^>]*>([\s\S]*?)<\/span>/i);
    if (mObs) {
      observacoes = decodificarEntidadesHtml(mObs[1].replace(/<[^>]+>/g, ' '));
    }

    // Horários e Docentes
    const horarios = [];
    const docentesSet = new Set();
    const linhasHorario = chunk.match(/<tr[^>]*txt_verdana_8pt_gray[^>]*>[\s\S]*?<\/tr>/gi) || [];

    let ultimoHorario = null;

    linhasHorario.forEach(lh => {
      const colunas = (lh.match(/<td[^>]*>([\s\S]*?)<\/td>/gi) || []).map(c => {
        return decodificarEntidadesHtml(c.replace(/<[^>]+>/g, ' ')).trim();
      });

      if (colunas.length >= 4) {
        const dia = colunas[0];
        const horaIni = colunas[1];
        const horaFim = colunas[2];
        let prof = colunas[3];

        if (prof) {
          // Remove prefixos de papéis do Júpiter como (R) ou (P) e espaços extras
          prof = prof.replace(/^\([A-Za-z]\)\s*/, '').trim();
        }

        const temHorario = Boolean(horaIni && horaFim && /\d{2}:\d{2}/.test(horaIni));

        if (temHorario) {
          let nomeDoc = 'A Designar';
          if (prof && prof !== '-' && !prof.includes('Prof(a)')) {
            docentesSet.add(prof);
            nomeDoc = prof;
          }
          ultimoHorario = {
            dia: dia,
            inicio: horaIni,
            fim: horaFim,
            docente: nomeDoc,
            professores: (nomeDoc !== 'A Designar') ? [nomeDoc] : []
          };
          horarios.push(ultimoHorario);
        } else if (prof && prof !== '-' && !prof.includes('Prof(a)')) {
          // Linha de continuação com professor adicional no mesmo horário (co-docência)
          docentesSet.add(prof);
          if (ultimoHorario) {
            if (!ultimoHorario.professores) {
              ultimoHorario.professores = (ultimoHorario.docente && ultimoHorario.docente !== 'A Designar')
                ? [ultimoHorario.docente]
                : [];
            }
            if (!ultimoHorario.professores.includes(prof)) {
              ultimoHorario.professores.push(prof);
              ultimoHorario.docente = ultimoHorario.professores.join(', ');
            }
          }
        }
      }
    });

    const docentesLista = docentesSet.size > 0 ? Array.from(docentesSet).sort() : ['A Designar'];

    // Alunos Matriculados (soma apenas das categorias com colspan=2, ignora linhas filhas de unidades)
    let matriculados = null;
    const mMatr = chunk.match(/Matriculado/i);
    if (mMatr) {
      const posMatr = mMatr.index;
      const trechoTabela = chunk.substring(posMatr).split(/<\/table>/i)[0];
      const reTr = /<tr[^>]*>([\s\S]*?)<\/tr>/gi;
      let mTr;
      let totalMatriculados = 0;
      let teveCategoria = false;
      while ((mTr = reTr.exec(trechoTabela)) !== null) {
        const trHtml = mTr[1];
        const reTd = /<td([^>]*)>([\s\S]*?)<\/td>/gi;
        const tds = [];
        let mTd;
        while ((mTd = reTd.exec(trHtml)) !== null) {
          tds.push({ attrs: mTd[1], html: mTd[2] });
        }
        if (tds.length === 5) {
          if (/colspan\s*=\s*['"]?\s*2\s*['"]?/i.test(tds[0].attrs)) {
            const catTexto = decodificarEntidadesHtml(tds[0].html.replace(/<[^>]+>/g, ' ')).trim();
            const catLower = catTexto.toLowerCase();
            if (catTexto && catLower !== 'vagas' && catLower !== 'matriculados' && catLower !== 'inscritos' && catLower !== 'pendentes') {
              teveCategoria = true;
              const valRaw = decodificarEntidadesHtml(tds[4].html.replace(/<[^>]+>/g, ' ')).trim();
              const valLimpo = valRaw.replace(/[^\d]/g, '');
              if (valLimpo) {
                totalMatriculados += parseInt(valLimpo, 10);
              }
            }
          }
        }
      }
      if (teveCategoria) {
        matriculados = totalMatriculados;
      }
    }

    turmas[numTurma] = {
      codigoTurma: codTurma,
      numero: numTurma,
      tipo: tipoTurma,
      periodo: periodo,
      inicio: inicio,
      fim: fim,
      docentes: docentesLista,
      horarios: horarios,
      observacoes: observacoes,
      matriculados: matriculados
    };
  }

  return {
    codigo: codigo,
    nome: nomeDisciplina,
    semOferecimento: Object.keys(turmas).length === 0,
    turmas: turmas
  };
}

/**
 * Extrai dados estruturados de turma, sigla e modalidade a partir do texto de uma célula
 * Ex: "SEM0538 - T1 e T2" -> { ehValida: true, codigo: "SEM0538", ehPos: false, turmasSolicitadas: ["01", "02"], ... }
 */
function extrairInfoTurmaDaCelula(textoCelula) {
  if (!textoCelula || typeof textoCelula !== 'string') {
    return { ehValida: false, codigo: '', ehPos: false, turmasSolicitadas: [], ehEvento: false };
  }

  const texto = textoCelula.trim();
  if (!texto) {
    return { ehValida: false, codigo: '', ehPos: false, turmasSolicitadas: [], ehEvento: false };
  }

  const padraoEvento = /\b(prova|monitoria|reservado|projeto|oficina|semanau|palestra)\b/i;
  const ehEvento = padraoEvento.test(texto);

  const regexCod = /\b([A-Za-z]{3})(\d{3,4})\b|\b(\d{7})\b/;
  const matchCod = texto.match(regexCod);
  if (!matchCod) {
    return { ehValida: false, codigo: '', ehPos: false, turmasSolicitadas: [], ehEvento: ehEvento, textoOriginal: texto };
  }

  let codigo = '';
  let ehPos = false;

  if (matchCod[1] && matchCod[2]) {
    const sigla = matchCod[1].toUpperCase();
    let num = matchCod[2];
    if (num.length === 3) num = '0' + num;
    codigo = sigla + num;
    ehPos = !num.startsWith('0');
  } else if (matchCod[3]) {
    codigo = matchCod[3];
    ehPos = false;
  }

  const turmas = [];
  // 1. Padrão com T ou Turma explícito (ex: - T1, - T01, T1 e T2, Turma 1)
  const padraoTurma = /(?:-\s*|\/\s*)?(?:T\s*[\-_]?\s*|Turma\s+)(\d{1,2})(?:\s*(?:e|E|\/)\s*T?\s*[\-_]?\s*(\d{1,2}))?/i;
  const matchTurma = texto.match(padraoTurma);
  if (matchTurma) {
    if (matchTurma[1]) turmas.push(matchTurma[1].padStart(2, '0'));
    if (matchTurma[2]) turmas.push(matchTurma[2].padStart(2, '0'));
  } else if (!ehEvento) {
    // 2. Padrão numérico isolado após hífen ou barra (ex: "SEP5864 - 1" ou "SEP5864 / 1")
    const padraoNumPos = /(?:-\s*|\/\s*)(\d{1,2})(?:\s*(?:e|E|\/)\s*(\d{1,2}))?(?:\s*$|\s+(?:pv|tv|pós|pos|\/))/i;
    const matchNum = texto.match(padraoNumPos);
    if (matchNum) {
      if (matchNum[1]) turmas.push(matchNum[1].padStart(2, '0'));
      if (matchNum[2]) turmas.push(matchNum[2].padStart(2, '0'));
    }
  }

  const matchAula = texto.match(/\[(\d+)\]/);
  const aulaSemana = matchAula ? parseInt(matchAula[1], 10) : null;

  const matchMod = texto.match(/\b(pv|tv)\b/i);
  const modalidade = matchMod ? matchMod[1].toLowerCase() : null;

  return {
    ehValida: true,
    codigo: codigo,
    ehPos: ehPos,
    turmasSolicitadas: turmas,
    aulaSemana: aulaSemana,
    modalidade: modalidade,
    ehEvento: ehEvento,
    textoOriginal: texto
  };
}

/**
 * Realiza o casamento entre a intenção da célula e os dados do Júpiter ou Janus.
 * Retorna { sucesso, turmaPadrao, labelHover, docentes, turmasEncontradas }
 */
function casarTurmaComDados(dadosDisciplina, infoCelula) {
  if (!dadosDisciplina || !infoCelula || !infoCelula.ehValida) {
    return { sucesso: false, labelHover: '', turmaPadrao: null };
  }

  if (dadosDisciplina.semOferecimento) {
    const nomeSis = infoCelula.ehPos ? 'Janus' : 'Jupiterweb';
    return { sucesso: false, semOferecimento: true, labelHover: 'Sem oferecimento no ' + nomeSis, turmaPadrao: null };
  }

  const turmasDisciplina = dadosDisciplina.turmas || {};
  const listaChaves = Object.keys(turmasDisciplina);
  if (listaChaves.length === 0) {
    return { sucesso: false, labelHover: 'Sem turmas cadastradas', turmaPadrao: null };
  }

  const turmasSolicitadas = infoCelula.turmasSolicitadas || [];

  if (turmasSolicitadas.length > 0) {
    const turmasEncontradas = [];
    const docentesSet = new Set();

    turmasSolicitadas.forEach(tSol => {
      let tObj = turmasDisciplina[tSol] || turmasDisciplina[String(parseInt(tSol, 10))];
      if (!tObj) {
        for (const k of listaChaves) {
          const v = turmasDisciplina[k];
          if (v && (String(v.numero).padStart(2, '0') === tSol || String(v.codigoTurma || '').endsWith(tSol))) {
            tObj = v;
            break;
          }
        }
      }

      if (tObj) {
        turmasEncontradas.push(tObj);
        (tObj.docentes || []).forEach(d => {
          if (d && d !== 'A Designar' && d !== '-') {
            docentesSet.add(d);
          }
        });
      }
    });

    const turmaPadrao = turmasEncontradas.length > 0 ? turmasEncontradas[0].numero : turmasSolicitadas[0];
    let labelHover = '';

    if (docentesSet.size === 0) {
      labelHover = 'Docente: A designar';
    } else if (docentesSet.size === 1) {
      labelHover = 'Docente: ' + Array.from(docentesSet)[0];
    } else {
      const listaNomes = Array.from(docentesSet).sort();
      labelHover = 'Docentes: ' + listaNomes.join(', ');
    }

    return {
      sucesso: true,
      turmaPadrao: String(turmaPadrao).padStart(2, '0'),
      turmasEncontradas: turmasEncontradas,
      labelHover: labelHover,
      docentes: Array.from(docentesSet).sort()
    };
  }

  // Célula sem turma especificada (ex: SMA0300 ou SEP5864)
  const todasTurmas = Object.values(turmasDisciplina);
  if (todasTurmas.length === 1) {
    const tUnica = todasTurmas[0];
    const docs = (tUnica.docentes || []).filter(d => d && d !== 'A Designar' && d !== '-');
    let labelHover = '';
    if (docs.length === 0) {
      labelHover = 'Docente: A designar';
    } else if (docs.length === 1) {
      labelHover = 'Docente: ' + docs[0];
    } else {
      labelHover = 'Docentes: ' + docs.join(', ');
    }
    return {
      sucesso: true,
      turmaPadrao: String(tUnica.numero || '01').padStart(2, '0'),
      labelHover: labelHover,
      docentes: docs
    };
  } else {
    const primeiraTurma = todasTurmas[0] || {};
    return {
      sucesso: true,
      turmaPadrao: String(primeiraTurma.numero || '01').padStart(2, '0'),
      labelHover: 'Docentes: Várias turmas',
      docentes: []
    };
  }
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
    const titulo = 'Consultar ' + item.codigo + ' (' + sistemaNome + ') • Clique para ver detalhes';
    const attrData = ' data-codigo="' + escapeHtml(item.codigo) + '" role="button" tabindex="0"';

    htmlResult += '<a href="' + linkUrl + '" target="_blank" rel="noopener noreferrer" class="' + classeCss + '"' + attrData + ' title="' + escapeHtml(titulo) + '">' + escapeHtml(item.textoEncontrado) + '</a>';

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
    const codigosGraduacaoEncontrados = new Set();
    const codigosPosEncontrados = new Set();

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

        if (parsed.codigos.length > 0) {
          celObj.d = parsed.codigos;
          parsed.codigos.forEach(cd => {
            const cNorm = String(cd).trim().toUpperCase();
            if (cNorm) {
              if (parsed.ehPos) {
                codigosPosEncontrados.add(cNorm);
              } else {
                codigosGraduacaoEncontrados.add(cNorm);
              }
            }
          });
        }
        if (parsed.ehPos) celObj.pos = true;
        const infoTurma = extrairInfoTurmaDaCelula(rawText);
        if (infoTurma && infoTurma.turmasSolicitadas && infoTurma.turmasSolicitadas.length > 0) {
          celObj.turmas = infoTurma.turmasSolicitadas;
        }
        if (merge && merge.colspan > 1) celObj.cs = merge.colspan;
        if (merge && merge.rowspan > 1) celObj.rs = merge.rowspan;
        if (corBg) celObj.bg = corBg;

        linhaArray.push(celObj);
      }
      matrizGradeOtimizada.push(linhaArray);
    }

    // Se for atualização forçada, invalida também o cache do Jupiterweb e Janus no ScriptCache
    if (forcarAtualizacao && (codigosGraduacaoEncontrados.size > 0 || codigosPosEncontrados.size > 0)) {
      try {
        const PREFIXO_CACHE_JUPITER = 'JUP_V19_';
        const PREFIXO_CACHE_JANUS = 'JAN_V3_';
        const chavesParaRemover = [
          ...Array.from(codigosGraduacaoEncontrados).map(c => PREFIXO_CACHE_JUPITER + c),
          ...Array.from(codigosPosEncontrados).map(c => 'JAN_V1_' + c),
          ...Array.from(codigosPosEncontrados).map(c => PREFIXO_CACHE_JANUS + c)
        ];
        for (let i = 0; i < chavesParaRemover.length; i += 100) {
          cache.removeAll(chavesParaRemover.slice(i, i + 100));
        }
        Logger.log('Invalidação forçada do cache (Júpiter + Janus): ' + chavesParaRemover.length + ' chaves removidas do ScriptCache.');
      } catch (eLimpeza) {
        Logger.log('Aviso ao invalidar chaves no CacheService: ' + eLimpeza.message);
      }
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

/**
 * Endpoint assíncrono chamado pelo Frontend para obter turmas do Jupiterweb em lote
 * Realiza busca paralela via UrlFetchApp.fetchAll com decodificação ISO-8859-1
 * e armazenamento em ScriptCache (TTL de 6 horas) com suporte a cache negativo.
 * 
 * @param {Array<string>} listaCodigos - Lista de códigos de graduação (ex: ["SMA0356", "7600006"])
 * @returns {Object} { sucesso: boolean, dados: { [codigo]: objetoDisciplina } }
/**
 * Endpoint assíncrono chamado pelo Frontend para obter turmas em lote
 * (Graduação via Jupiterweb e Pós-Graduação via Janus em pipeline otimizado de 2 etapas).
 * Utiliza busca paralela via UrlFetchApp.fetchAll e armazenamento em ScriptCache (TTL de 6h).
 * 
 * @param {Array<string>} listaCodigos - Lista de códigos (ex: ["SMA0356", "SEP5864", "7600006"])
 * @returns {Object} { sucesso: boolean, dados: { [codigo]: objetoDisciplina } }
 */
function obterLoteDisciplinas(listaCodigos) {
  try {
    if (!listaCodigos || !Array.isArray(listaCodigos)) {
      return { sucesso: false, msg: 'Parâmetro listaCodigos deve ser uma lista de códigos.' };
    }

    const regexGrad = /^([A-Za-z]{3}0\d{3}|\d{7})$/;
    const regexPos = /^[A-Za-z]{3}[1-9]\d{3}$/;

    // Filtra e normaliza códigos válidos
    const codigosValidos = Array.from(new Set(
      listaCodigos
        .map(c => String(c).trim().toUpperCase())
        .filter(c => regexGrad.test(c) || regexPos.test(c))
    )).slice(0, 10); // Limite de segurança: máx 10 por lote

    if (codigosValidos.length === 0) {
      return { sucesso: true, dados: {} };
    }

    const cache = CacheService.getScriptCache();
    const PREFIXO_CACHE_JUPITER = 'JUP_V19_';
    const PREFIXO_CACHE_JANUS = 'JAN_V3_';
    const resultado = {};
    const pendentesGrad = [];
    const pendentesPos = [];

    // 1. Consulta o CacheService para cada código
    codigosValidos.forEach(cod => {
      const ehPos = regexPos.test(cod);
      const cacheKey = (ehPos ? PREFIXO_CACHE_JANUS : PREFIXO_CACHE_JUPITER) + cod;
      const cached = cache.get(cacheKey);
      if (cached) {
        try {
          resultado[cod] = JSON.parse(cached);
        } catch (e) {
          if (ehPos) pendentesPos.push(cod);
          else pendentesGrad.push(cod);
        }
      } else {
        if (ehPos) pendentesPos.push(cod);
        else pendentesGrad.push(cod);
      }
    });

    // 2. Processa Pendências do Jupiterweb (Graduação - 1 Etapa)
    if (pendentesGrad.length > 0) {
      const requisicoesGrad = pendentesGrad.map(cod => ({
        url: 'https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=' + encodeURIComponent(cod),
        method: 'get',
        muteHttpExceptions: true
      }));

      const respostasGrad = UrlFetchApp.fetchAll(requisicoesGrad);

      for (let i = 0; i < pendentesGrad.length; i++) {
        const cod = pendentesGrad[i];
        const resp = respostasGrad[i];
        const cacheKey = PREFIXO_CACHE_JUPITER + cod;

        if (resp && resp.getResponseCode() === 200) {
          const html = resp.getContentText('ISO-8859-1');
          const dadosParsed = parsearHtmlJupiterweb(cod, html);
          resultado[cod] = dadosParsed;

          try {
            const jsonStr = JSON.stringify(dadosParsed);
            if (jsonStr.length < 95000) {
              cache.put(cacheKey, jsonStr, 21600);
            }
          } catch (eCache) {
            Logger.log('Aviso ao salvar no cache para ' + cod + ': ' + eCache.message);
          }
        } else {
          const objErro = { codigo: cod, nome: '', semOferecimento: true, erro: true };
          resultado[cod] = objErro;
          try { cache.put(cacheKey, JSON.stringify(objErro), 3600); } catch (e) {}
        }
      }
    }

    // 3. Processa Pendências do Janus (Pós-Graduação - 2 Etapas Diretas)
    if (pendentesPos.length > 0) {
      // 3.1. Etapa 1: Busca DisciplinaAux para extrair nome e oferecimentos
      const requisicoesJanusEtapa1 = pendentesPos.map(cod => ({
        url: 'https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=' + encodeURIComponent(cod),
        method: 'get',
        muteHttpExceptions: true
      }));

      const respostasJanusEtapa1 = UrlFetchApp.fetchAll(requisicoesJanusEtapa1);
      const oferecimentosParaBuscar = []; // { cod, ofe, nomeDisc }

      for (let i = 0; i < pendentesPos.length; i++) {
        const cod = pendentesPos[i];
        const resp = respostasJanusEtapa1[i];
        const cacheKey = PREFIXO_CACHE_JANUS + cod;

        if (resp && resp.getResponseCode() === 200) {
          let html = '';
          try {
            html = resp.getContentText('windows-1252');
          } catch (eChar) {
            html = resp.getContentText('ISO-8859-1');
          }

          const parsedDisc = parsearHtmlJanusDisciplina(cod, html);

          if (parsedDisc.semOferecimento || !parsedDisc.oferecimentos || parsedDisc.oferecimentos.length === 0) {
            const objSemOf = {
              codigo: cod,
              nome: parsedDisc.nome || '',
              sistema: 'janus',
              semOferecimento: true,
              turmas: {}
            };
            resultado[cod] = objSemOf;
            try { cache.put(cacheKey, JSON.stringify(objSemOf), 21600); } catch (e) {}
          } else {
            // Guarda para a Etapa 2
            parsedDisc.oferecimentos.forEach(ofeNum => {
              oferecimentosParaBuscar.push({
                cod: cod,
                ofe: ofeNum,
                nomeDisc: parsedDisc.nome
              });
            });
          }
        } else {
          const objErro = { codigo: cod, nome: '', sistema: 'janus', semOferecimento: true, erro: true, turmas: {} };
          resultado[cod] = objErro;
          try { cache.put(cacheKey, JSON.stringify(objErro), 3600); } catch (e) {}
        }
      }

      // 3.2. Etapa 2: Bypass da casca JSF - busca direta em TurmaDet
      if (oferecimentosParaBuscar.length > 0) {
        const requisicoesJanusEtapa2 = oferecimentosParaBuscar.map(item => ({
          url: 'https://uspdigital.usp.br/janus/TurmaDet?sgldis=' + encodeURIComponent(item.cod) + '&ofe=' + encodeURIComponent(item.ofe) + '&',
          method: 'get',
          muteHttpExceptions: true
        }));

        const respostasJanusEtapa2 = UrlFetchApp.fetchAll(requisicoesJanusEtapa2);
        const turmasPorCodigo = {}; // { [cod]: { nome, turmasMap } }

        for (let j = 0; j < oferecimentosParaBuscar.length; j++) {
          const item = oferecimentosParaBuscar[j];
          const resp = respostasJanusEtapa2[j];

          if (!turmasPorCodigo[item.cod]) {
            turmasPorCodigo[item.cod] = {
              nome: item.nomeDisc,
              turmasMap: {}
            };
          }

          if (resp && resp.getResponseCode() === 200) {
            let htmlTurma = '';
            try {
              htmlTurma = resp.getContentText('windows-1252');
            } catch (eChar) {
              htmlTurma = resp.getContentText('ISO-8859-1');
            }

            const parsedTurma = parsearHtmlJanusTurma(item.cod, htmlTurma, item.ofe);
            if (parsedTurma) {
              const chaveCanonica = parsedTurma.numero;
              turmasPorCodigo[item.cod].turmasMap[chaveCanonica] = parsedTurma;
            }
          }
        }

        // Monta o objeto final de cada disciplina de pós e persiste no cache
        for (const cod in turmasPorCodigo) {
          const infoObj = turmasPorCodigo[cod];
          const cacheKey = PREFIXO_CACHE_JANUS + cod;
          const turmasMap = infoObj.turmasMap;
          const temTurmas = Object.keys(turmasMap).length > 0;

          const objJanus = {
            codigo: cod,
            nome: infoObj.nome || '',
            sistema: 'janus',
            semOferecimento: !temTurmas,
            turmas: turmasMap
          };

          resultado[cod] = objJanus;

          try {
            const jsonStr = JSON.stringify(objJanus);
            if (jsonStr.length < 95000) {
              cache.put(cacheKey, jsonStr, 21600);
            }
          } catch (eCache) {
            Logger.log('Aviso ao salvar cache Janus para ' + cod + ': ' + eCache.message);
          }
        }
      }
    }

    return { sucesso: true, dados: resultado };

  } catch (err) {
    Logger.log('Erro em obterLoteDisciplinas: ' + err.stack);
    return { sucesso: false, msg: 'Erro ao consultar turmas: ' + err.message };
  }
}

/**
 * Alias de retrocompatibilidade para o endpoint legada do Jupiterweb.
 * Redireciona para o despachante unificado obterLoteDisciplinas.
 */
function obterLoteJupiterweb(listaCodigos) {
  return obterLoteDisciplinas(listaCodigos);
}

// ============================================================================
// 📊 TELEMETRIA E ESTATÍSTICAS DE ACESSO (NATIVO NO GOOGLE SHEETS)
// ============================================================================

/**
 * Ativa a aba '_Metricas' na interface do Google Sheets (ou cria caso não exista)
 */
function abrirAbaMetricas() {
  const ss = obterPlanilhaAtivaOuPlus();
  if (!ss) return;
  let sheet = ss.getSheetByName('_Metricas');
  if (!sheet) {
    sheet = inicializarAbaMetricas(ss);
  }
  if (sheet) {
    ss.setActiveSheet(sheet);
  }
}

/**
 * Retorna a planilha ativa ou abre a planilha PLUS pelo ID oficial
 */
function obterPlanilhaAtivaOuPlus() {
  let ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) {
    try {
      ss = SpreadsheetApp.openById('1ZSa4RmZm0GSiAPrHwE1M1cB1vzI1hdg30bGkTA-R66U');
    } catch (e) {
      Logger.log('Aviso: Não foi possível abrir a planilha PLUS por ID: ' + e.message);
    }
  }
  return ss;
}

/**
 * Cria ou formata a aba '_Metricas' com dashboard de KPIs e tabela de registros
 */
function inicializarAbaMetricas(ss) {
  if (!ss) ss = obterPlanilhaAtivaOuPlus();
  if (!ss) return null;

  let sheet = ss.getSheetByName('_Metricas');
  if (!sheet) {
    sheet = ss.insertSheet('_Metricas');
  }

  // Se a aba acabou de ser criada ou está vazia, monta a estrutura completa
  if (sheet.getLastRow() < 4) {
    sheet.clear();

    // 1. Painel Resumo / KPIs (Linhas 1 e 2)
    const kpiTitulos = [['Total de Consultas', 'Visitantes Únicos', 'Acessos Hoje', '% Mobile', '% Desktop']];
    sheet.getRange(1, 1, 1, 5).setValues(kpiTitulos)
      .setFontWeight('bold')
      .setFontSize(9)
      .setBackground('#f1f5f9')
      .setFontColor('#475569')
      .setHorizontalAlignment('center')
      .setVerticalAlignment('middle');

    // Fórmulas em inglês para compatibilidade padrão da API do Apps Script
    const kpiFormulas = [[
      '=IF(COUNTA(A5:A)>0, COUNTA(A5:A), 0)',
      '=IF(COUNTA(F5:F)>0, COUNTUNIQUE(F5:F), 0)',
      '=IF(COUNTA(B5:B)>0, COUNTIF(B5:B, TEXT(TODAY(), "yyyy-mm-dd")), 0)',
      '=IF(COUNTA(D5:D)>0, COUNTIF(D5:D, "Mobile") / COUNTA(D5:D), 0)',
      '=IF(COUNTA(D5:D)>0, COUNTIF(D5:D, "Desktop") / COUNTA(D5:D), 0)'
    ]];
    sheet.getRange(2, 1, 1, 5).setFormulas(kpiFormulas)
      .setFontWeight('bold')
      .setFontSize(14)
      .setFontColor('#104880')
      .setBackground('#ffffff')
      .setHorizontalAlignment('center')
      .setVerticalAlignment('middle');

    // Formatos numéricos dos KPIs
    sheet.getRange(2, 1, 1, 3).setNumberFormat('#,##0');
    sheet.getRange(2, 4, 1, 2).setNumberFormat('0.0%');
    sheet.setRowHeight(1, 24);
    sheet.setRowHeight(2, 34);
    sheet.setRowHeight(3, 14);

    // 2. Cabeçalho da Tabela de Registros (Linha 4)
    const colunasLog = [['Data e Hora', 'Data', 'Hora', 'Dispositivo', 'Tipo de Visita', 'ID Anônimo', 'Resolução']];
    sheet.getRange(4, 1, 1, 7).setValues(colunasLog)
      .setFontWeight('bold')
      .setFontSize(10)
      .setBackground('#104880')
      .setFontColor('#ffffff')
      .setHorizontalAlignment('center')
      .setVerticalAlignment('middle');
    sheet.setRowHeight(4, 28);

    // Ajusta largura das colunas para visualização agradável
    sheet.setColumnWidth(1, 160); // Data e Hora
    sheet.setColumnWidth(2, 100); // Data
    sheet.setColumnWidth(3, 80);  // Hora
    sheet.setColumnWidth(4, 110); // Dispositivo
    sheet.setColumnWidth(5, 160); // Tipo de Visita
    sheet.setColumnWidth(6, 170); // ID Anônimo
    sheet.setColumnWidth(7, 110); // Resolução

    // Congela as primeiras 4 linhas (KPIs + Cabeçalho fixos na rolagem)
    sheet.setFrozenRows(4);
  }

  return sheet;
}

/**
 * Endpoint backend chamado pelo cliente em background para registrar estatísticas de acesso.
 * Protegido por LockService para evitar concorrência de escritas simultâneas na planilha.
 */
function registrarAcessoWeb(payload) {
  const lock = LockService.getScriptLock();
  const temLock = lock.tryLock(2500);
  if (!temLock) {
    // Se o lock não foi obtido em 2.5s, encerra silenciosamente
    return { sucesso: false, motivo: 'timeout_lock' };
  }

  try {
    const ss = obterPlanilhaAtivaOuPlus();
    if (!ss) return { sucesso: false, motivo: 'sem_planilha' };

    let sheet = ss.getSheetByName('_Metricas');
    if (!sheet) {
      sheet = inicializarAbaMetricas(ss);
    }
    if (!sheet) return { sucesso: false, motivo: 'falha_aba' };

    const dados = payload || {};
    const agora = new Date();
    const tz = Session.getScriptTimeZone() || 'America/Sao_Paulo';
    const dataHoraStr = Utilities.formatDate(agora, tz, 'dd/MM/yyyy HH:mm:ss');
    const dataStr = Utilities.formatDate(agora, tz, 'yyyy-MM-dd');
    const horaStr = Utilities.formatDate(agora, tz, 'HH:mm');

    const dispositivo = String(dados.dispositivo || 'Desktop').substring(0, 20);
    const tipoVisita = String(dados.tipoVisita || 'Visita').substring(0, 30);
    const idAnonimo = String(dados.idAnonimo || 'anon').substring(0, 50);
    const resolucao = String(dados.resolucao || '').substring(0, 30);

    sheet.appendRow([
      dataHoraStr,
      dataStr,
      horaStr,
      dispositivo,
      tipoVisita,
      idAnonimo,
      resolucao
    ]);

    // Formatação e alinhamento da linha recém-adicionada
    const ultimaLinha = sheet.getLastRow();
    if (ultimaLinha >= 5) {
      sheet.getRange(ultimaLinha, 1, 1, 7)
        .setFontSize(9)
        .setHorizontalAlignment('center')
        .setVerticalAlignment('middle');
      sheet.getRange(ultimaLinha, 5).setHorizontalAlignment('left'); // Tipo de visita
      sheet.getRange(ultimaLinha, 6).setFontFamily('monospace');     // ID Anônimo
    }

    return { sucesso: true };
  } catch (err) {
    Logger.log('Erro ao registrar métrica de acesso: ' + err.message);
    return { sucesso: false, erro: err.message };
  } finally {
    try {
      lock.releaseLock();
    } catch (e) {}
  }
}
