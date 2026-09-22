# 3. Estratégia de Cache Multinível em Chunks no CacheService

* **Data:** 2026-09-18
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
A extração dos dados da grade horária na planilha oficial do SVGRAD envolve a leitura de centenas de células, formatações de cor (`getBackgrounds()`), textos de exibição (`getDisplayValues()`) e intervalos mesclados (`getMergedRanges()`). Essa operação consome entre **3 e 6 segundos** por requisição no backend do Google Apps Script.

Em horários de pico (início de semestre, períodos de matrícula e alterações de turmas), centenas de requisições simultâneas:
1. Tornariam a navegação dos alunos inaceitavelmente lenta.
2. Esgotariam rapidamente as cotas diárias de execução do Google Apps Script (limite de 90 minutos de CPU/dia no Google Workspace padrão).

Para solucionar a latência, a equipe recorreu ao serviço nativo `CacheService.getScriptCache()`. No entanto, o `CacheService` impõe uma restrição severa da plataforma:
* **Tamanho Máximo por Entrada:** Cada chave de cache suporta no máximo **100 KB** (102.400 bytes).
* **Problema:** A matriz consolidada da grade do Alocação Plus (contendo salas, faixas horárias, metadados de mesclagem e códigos formatados com links HTML) gera uma string JSON entre **130 KB e 280 KB**, estourando o limite da API e gerando erro de execução (*Value exceeds maximum allowed length*).

## Alternativas Consideradas
* **Uso de Banco de Dados Externo (ex: Firebase / Supabase):** Aumentaria a complexidade de autenticação, custos e adicionaria pontos externos de falha fora do ecossistema Google Workspace institucional da USP.
* **Armazenamento em Propriedades (`PropertiesService`):** O limite do `PropertiesService` é ainda mais restritivo (apenas 9 KB por valor e 500 KB no total do documento).
* **Redução Drástica dos Dados no Servidor:** Remover links e enviar dados criptografados/ultra-reduzidos aumentaria a complexidade do cliente e não resolveria a longo prazo caso novas salas fossem adicionadas à EESC.

## Decisão Adotada
Desenvolver um mecanismo transparente de **particionamento de cache em fatias (*chunking*)** operando sobre o `CacheService`:
1. **Gravação (`salvarCacheEmChunks`):**
   * Se o JSON for menor ou igual a 90.000 caracteres, salva normalmente na chave base.
   * Se exceder 90.000 caracteres, divide a string em fatias de 90 KB (`TAM_CHUNK = 90000`).
   * Grava cada pedaço sob o identificador `${chaveBase}_0`, `${chaveBase}_1`, etc.
   * Grava um manifesto com o total de fatias na chave `${chaveBase}_chunks`.
2. **Leitura (`obterCacheEmChunks`):**
   * Verifica a existência da chave de manifesto `_chunks`.
   * Se existir, lê iterativamente cada pedaço e reconstrói a string original integralmente.
   * Caso algum pedaço tenha expirado isoladamente, descarta o conjunto e retorna `null`, disparando uma releitura limpa da fonte.
3. **Invalidamento e TTL:**
   * Tempo de vida configurável (padrão de 60 minutos, limitado a 21.600 segundos / 6 horas, que é o limite máximo do GAS).
   * Função de purga explícita `limparCacheConfiguracoes()` acionada pelo menu da planilha e pelo botão "🔄 Atualizar Dados" na barra superior do Web App.

## Consequências
### Positivas (+)
* **Performance Sub-segundo:** O tempo de resposta do endpoint `obterDadosGradeWeb` caiu de ~4.500 ms para **menos de 200 ms** quando atendido pelo cache.
* **Resiliência a Quotas:** O backend suporta milhares de visualizações diárias consumindo uma fração ínfima de tempo de computação.
* **Transparência Arquitetural:** O restante do código consome os dados sem precisar saber se vieram em pedaços ou de uma requisição fresca.
* **Custo Zero:** Solução 100% contida no Google Apps Script sem serviços ou custos de hospedagem de terceiros.

### Negativas / Trade-offs (-)
* Requer pequenas chamadas adicionais de leitura (`cache.get`) para reconstituir os blocos (impacto inferior a 15ms).

## Referências no Código
* [src/alocacao-plus.gs](../src/alocacao-plus.gs) (funções `salvarCacheEmChunks`, `obterCacheEmChunks`, `obterDadosGradeWeb`)
* [src/config.gs](../src/config.gs) (função `limparCacheConfiguracoes`)
