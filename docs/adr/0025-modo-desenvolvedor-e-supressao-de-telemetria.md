# 0025. Modo Desenvolvedor e Autoexclusão de Telemetria via Parâmetro de URL (?dev=1)

* **Data:** 2026-09-30
* **Status:** Aceito
* **Decisores:** Equipe Alocação Plus / EESC-USP

## Contexto e Problema

O Alocação Plus conta com um sistema de telemetria nativo, silencioso e assíncrono que registra visitas na aba oculta `_Metricas` da planilha oficial no Google Sheets (calculando KPIs como total de consultas, visitantes únicos, acessos hoje e percentual mobile/desktop).

Contudo, durante as etapas frequentes de desenvolvimento, testes manuais, homologação e manutenção diária realizadas pelo administrador do sistema, as métricas de acesso eram impactadas, inflando artificialmente os números de visitas e a distribuição estatística real dos usuários finais (docentes, alunos e funcionários da EESC-USP).

Fazia-se necessária uma forma simples, robusta e persistente de permitir que o desenvolvedor/administrador autoexclua seu navegador e seus dispositivos das métricas de acesso, sem exigir login da USP (preservando o acesso anônimo do público geral) e sem onerar as cotas diárias de execução do Google Apps Script.

## Alternativas Consideradas

* **Alternativa 1 (Autenticação Google no Web App):** Exigir login da USP (`Session.getActiveUser().getEmail()`) para checar se o visitante é o administrador.
  * *Rejeitada:* O Web App é configurado intencionalmente para "Executar como: Proprietário" e "Acesso: Qualquer pessoa", visando eliminar barreiras e fricção de acesso para alunos e visitantes. Exigir login degradaria severamente a usabilidade do produto.
* **Alternativa 2 (Lista estática de IDs Anônimos no Backend):** Filtrar o ID anônimo no backend (`alocacao-plus.gs`).
  * *Rejeitada:* Cada limpeza de cookies ou uso de aba anônima gera um novo identificador, exigindo manutenção manual constante de listas de IDs.
* **Alternativa 3 (Parâmetro de URL + Persistência em `localStorage` com Supressão no Cliente - ESCOLHIDA):** O usuário acessa uma única vez com `?dev=1` (ou `?dev=true`). O frontend processa o parâmetro, salva a preferência em `localStorage.setItem('alocacao_plus_ignorar_telemetria', 'true')`, notifica com Toast amigável e exibe uma tag visual `DEV` no cabeçalho.
  * Em acessos subsequentes no mesmo dispositivo, mesmo sem o parâmetro na URL, a função `registrarAcessoSilencioso()` detecta a preferência salva e aborta imediatamente, sem enviar chamadas RPC (`google.script.run`) ao Apps Script.
  * Para reativar (ex: ao testar a própria telemetria), basta acessar `?dev=0` (ou `?dev=false`).

## Decisão

Implementar o mecanismo da **Alternativa 3** com arquitetura multicamada:

1. **Captura no Servidor (`doGet`):** O ponto de entrada HTTP captura `e.parameter.dev` e injeta com segurança na inicialização do template HTML (`window.__APP_DEV_PARAM`).
2. **Resolução no Cliente (`configurarModoDesenvolvedor`):**
   * Avalia sequencialmente `window.__APP_DEV_PARAM`, `location.search` (`URLSearchParams`) e a API assíncrona oficial do Apps Script (`google.script.url.getLocation`);
   * Ativa com `1` ou `true`, persistindo em `localStorage`;
   * Desativa com `0` ou `false`, limpando o `localStorage`;
   * Notifica o operador com feedback Toast instantâneo (`exibirToast`);
   * Exibe/oculta o elemento semântico `#badge-dev-mode` (`DEV`) estilizado no Design System EESC ao lado da versão.
3. **Supressão Total no Cliente:** `registrarAcessoSilencioso()` verifica prioritariamente a chave no `localStorage` antes de qualquer verificação de ambiente ou throttle de sessão, garantindo 0 requisições e 0ms de consumo de cota de API.
4. **Proteção de Retaguarda no Backend:** `registrarAcessoWeb(payload)` em `alocacao-plus.gs` rejeita imediatamente payloads marcados com flags de teste (`isDev` ou `ignorar`).

## Consequências

### Positivas
* **Precisão Estatística:** As métricas em `_Metricas` passam a refletir 100% de acessos genuínos dos usuários da comunidade USP.
* **Zero Overhead:** Nenhuma requisição de rede ou processamento no servidor Apps Script é disparado durante sessões de desenvolvimento.
* **Persistência Confortável:** Configurado uma única vez por navegador/aparelho; não exige digitação contínua de parâmetros em URLs.
* **Transparência e Controle:** A tag visual `DEV` e os toasts oferecem clareza imediata sobre o estado ativo de telemetria.
* **Reversibilidade Simples:** Reativável a qualquer momento via `?dev=0`.

### Negativas / Limitações
* Se o administrador limpar todos os dados de navegação/cookies do navegador ou utilizar navegação anônima sem informar `?dev=1`, a flag do `localStorage` não estará presente. Nesses casos, basta reabrir com `?dev=1`.
