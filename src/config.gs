/**
 * Config.gs - Gestão Centralizada e Parametrização do Alocação Plus
 * Permite que administradores alterem links e opções via aba '_Config' sem tocar no código.
 */

const DEFAULT_CONFIG = {
  NOME_ABA_CONFIG: '_Config',
  FONTE_URL_OU_ID: '1AxLSuJPAGSZjvg36VaN8-mW9eogsacl2',
  FONTE_ABA: 'Grade_Horarios_Salas',
  URL_JUPITER: 'https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=',
  URL_JANUS: 'https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=',
  CACHE_MINUTOS: 60
};

/**
 * Extrai o ID da planilha a partir de uma URL completa ou retorna o próprio ID
 * Suporta formatos como:
 * - https://docs.google.com/spreadsheets/d/1AxLSuJPAGSZjvg36VaN8-mW9eogsacl2/edit#gid=0
 * - 1AxLSuJPAGSZjvg36VaN8-mW9eogsacl2
 */
function extrairSpreadsheetId(str) {
  if (!str) return '';
  const s = String(str).trim();
  const match = s.match(/\/spreadsheets\/d\/([a-zA-Z0-9-_]+)/i);
  if (match && match[1]) {
    return match[1];
  }
  return s;
}

/**
 * Cria ou atualiza a aba '_Config' com layout limpo e intuitivo
 */
function inicializarAbaConfiguracoes(ss) {
  if (!ss) {
    ss = SpreadsheetApp.getActiveSpreadsheet();
  }
  if (!ss) return null;

  let sheet = ss.getSheetByName(DEFAULT_CONFIG.NOME_ABA_CONFIG);
  if (!sheet) {
    sheet = ss.insertSheet(DEFAULT_CONFIG.NOME_ABA_CONFIG);
  }

  const cabecalhos = [['Parâmetro de Configuração', 'Valor Atual', 'Descrição / Instruções']];
  const dados = [
    ['URL ou ID da Planilha FONTE', DEFAULT_CONFIG.FONTE_URL_OU_ID, 'Cole o link completo ou o ID da planilha do SVGRAD.'],
    ['Nome da Aba da FONTE', DEFAULT_CONFIG.FONTE_ABA, 'Nome exato da aba na planilha FONTE (ex: Grade_Horarios_Salas).'],
    ['URL Base Jupiterweb (Graduação)', DEFAULT_CONFIG.URL_JUPITER, 'Prefixo para turmas de graduação.'],
    ['URL Base Janus (Pós-Graduação)', DEFAULT_CONFIG.URL_JANUS, 'Prefixo para turmas de pós-graduação.'],
    ['Tempo de Cache (minutos)', DEFAULT_CONFIG.CACHE_MINUTOS, 'Tempo que a grade fica em memória para respostas instantâneas (1 a 1440).']
  ];

  sheet.getRange(1, 1, 1, 3).setValues(cabecalhos)
    .setFontWeight('bold')
    .setBackground('#1e40af')
    .setFontColor('#ffffff')
    .setHorizontalAlignment('center');

  sheet.getRange(2, 1, dados.length, 3).setValues(dados)
    .setFontWeight('normal');

  sheet.getRange(2, 1, dados.length, 1).setFontWeight('bold').setBackground('#f8fafc');
  sheet.getRange(2, 2, dados.length, 1).setBackground('#ffffff');
  sheet.getRange(2, 3, dados.length, 1).setFontColor('#64748b').setFontSize(9);

  sheet.setColumnWidth(1, 260);
  sheet.setColumnWidth(2, 360);
  sheet.setColumnWidth(3, 400);
  sheet.setFrozenRows(1);

  return sheet;
}

/**
 * Lê e retorna todas as configurações ativas
 * Utiliza cache em memória para evitar leituras repetitivas da planilha
 */
function obterConfiguracoes(forcarRecarregar) {
  const cache = CacheService.getScriptCache();
  const cacheKey = 'ALOCACAO_PLUS_CONFIG_V2'; // Chave atualizada para invalidar cache anterior

  if (!forcarRecarregar) {
    const cachedData = cache.get(cacheKey);
    if (cachedData) {
      try {
        return JSON.parse(cachedData);
      } catch (e) {
        // Falha no parse, reconstrói
      }
    }
  }

  let config = Object.assign({}, DEFAULT_CONFIG);

  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    if (ss) {
      let sheet = ss.getSheetByName(DEFAULT_CONFIG.NOME_ABA_CONFIG);
      if (!sheet) {
        // Se a aba não existe, cria automaticamente com os valores padrão
        sheet = inicializarAbaConfiguracoes(ss);
      }

      if (sheet) {
        const valores = sheet.getDataRange().getValues();
        for (let i = 1; i < valores.length; i++) {
          const param = String(valores[i][0] || '').trim().toLowerCase();
          const val = String(valores[i][1] || '').trim();

          if (!val) continue;

          // 'aba' DEVE vir antes de 'fonte', pois a linha é 'Nome da Aba da FONTE'
          if (param.includes('aba')) {
            config.FONTE_ABA = val;
          } else if (param.includes('jupiter')) {
            config.URL_JUPITER = val;
          } else if (param.includes('janus')) {
            config.URL_JANUS = val;
          } else if (param.includes('cache')) {
            const min = parseInt(val, 10);
            if (!isNaN(min) && min > 0) {
              config.CACHE_MINUTOS = min;
            }
          } else if (param.includes('fonte') || param.includes('planilha') || param.includes('url') || param.includes('id')) {
            config.FONTE_URL_OU_ID = val;
          }
        }
      }
    }
  } catch (err) {
    Logger.log('Aviso ao carregar configurações da planilha: ' + err.message);
  }

  // Sanitiza o ID da planilha FONTE
  config.FONTE_ID = extrairSpreadsheetId(config.FONTE_URL_OU_ID);

  // Proteção de integridade: se o ID for igual ao nome da aba ou inválido, usa o padrão oficial
  if (!config.FONTE_ID || config.FONTE_ID === config.FONTE_ABA) {
    config.FONTE_ID = DEFAULT_CONFIG.FONTE_URL_OU_ID;
    config.FONTE_URL_OU_ID = DEFAULT_CONFIG.FONTE_URL_OU_ID;
  }

  // Guarda em cache por 6 horas (limite do CacheService do GAS é 21600s)
  try {
    cache.put(cacheKey, JSON.stringify(config), 21600);
  } catch (errCache) {
    Logger.log('Aviso de cache: ' + errCache.message);
  }

  return config;
}

/**
 * Limpa o cache para que alterações na aba '_Config' tenham efeito imediato
 */
function limparCacheConfiguracoes() {
  const cache = CacheService.getScriptCache();
  cache.remove('ALOCACAO_PLUS_CONFIG_V1');
  cache.remove('ALOCACAO_PLUS_CONFIG_V2');
  cache.remove('ALOCACAO_PLUS_GRADE_WEB_CACHE');
  cache.remove('ALOCACAO_PLUS_GRADE_WEB_CACHE_chunks');
  for (let i = 0; i <= 30; i++) {
    cache.remove('ALOCACAO_PLUS_GRADE_WEB_CACHE_' + i);
  }
  return { success: true, msg: 'Cache limpo com sucesso!' };
}
