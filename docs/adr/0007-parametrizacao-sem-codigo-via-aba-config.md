# 7. Parametrização sem Código via Aba de Configuração (_Config)

* **Data:** 2026-09-21
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
A cada novo semestre letivo, o SVGRAD gera uma nova planilha oficial ou atualiza o nome da aba da grade. Além disso, links de sistemas institucionais (Jupiterweb/Janus) ou tempos ideais de retenção de cache podem necessitar de ajustes ao longo do ano.

Se esses parâmetros ficassem fixos no código-fonte JavaScript (`.gs`):
1. Toda virada de semestre exigiria a intervenção de um desenvolvedor para editar o código e realizar uma nova implantação (*redeploy*) do Web App.
2. A equipe administrativa da EESC (secretarias e serviço de graduação) ficaria dependente da área técnica para tarefas triviais de configuração.
3. Erros manuais de sintaxe ao editar o código poderiam paralisar o sistema em períodos críticos de matrícula.

## Alternativas Consideradas
* **Variáveis no Código (`Config.gs` rígido):** Solução simples, mas que perpetua a dependência técnica e o risco de erros de sintaxe por usuários leigos.
* **Uso de `ScriptProperties` via Interface do Apps Script:** A interface de propriedades do Google Apps Script é técnica, escondida dentro do menu de configurações do projeto e inacessível para quem só tem acesso de visualizador/editor à planilha.
* **Aba Dedicada na Planilha (`_Config`):** Utilizar uma aba visível na própria planilha hospedeira, com formatação amigável, instruções passo a passo e leitura automatizada pelo script.

## Decisão Adotada
Implementar o módulo centralizado de parametrização sem código (`src/config.gs`):
1. **Auto-inicialização (`inicializarAbaConfiguracoes`):**
   * Se a aba `_Config` não existir, o sistema cria a aba automaticamente com cabeçalhos estilizados, larguras calibradas e linhas congeladas.
   * Insere os parâmetros padrão com descrições claras:
     * *URL ou ID da Planilha FONTE* (suporta link completo do Docs ou apenas o ID alfanumérico).
     * *Nome da Aba da FONTE* (ex: `Grade_Horarios_Salas`).
     * *URL Base Jupiterweb (Graduação)*.
     * *URL Base Janus (Pós-Graduação)*.
     * *Tempo de Cache (minutos)* (com validação entre 1 e 1440).
2. **Parser Robusto e Defensivo (`obterConfiguracoes`):**
   * Converte URLs completas em IDs através de regex (`extrairSpreadsheetId`).
   * Fallback defensivo: se o ID configurado estiver vazio ou corrompido, utiliza automaticamente o ID oficial padrão (`DEFAULT_CONFIG.FONTE_URL_OU_ID`), impedindo a interrupção do serviço.
3. **Cache de Configuração:**
   * Os parâmetros lidos são guardados no `CacheService` (`ALOCACAO_PLUS_CONFIG_V2`) para evitar leituras repetitivas da aba de configuração a cada requisição.
   * Limpeza instantânea do cache via menu da planilha (`💡 Plus > 🧹 Limpar Cache`) ou pelo frontend.

## Consequências
### Positivas (+)
* **Autonomia Total da Equipe Administrativa:** A transição de semestres é feita colando a nova URL na célula correspondente, sem tocar em uma única linha de código.
* **Imunidade a Falhas de Preenchimento:** Mecanismos de fallback garantem que o sistema continue operando mesmo se alguém apagar acidentalmente o conteúdo de uma célula na aba.
* **Instruções Integradas:** A terceira coluna da aba serve como manual de instrução contextual para os operadores.

### Negativas / Trade-offs (-)
* Alterações manuais na aba `_Config` demoram até expirar o cache para surtir efeito, a menos que o administrador clique em "Limpar Cache" no menu.

## Referências no Código
* [src/config.gs](../src/config.gs) (funções `extrairSpreadsheetId`, `inicializarAbaConfiguracoes`, `obterConfiguracoes`, `limparCacheConfiguracoes`)
* [src/alocacao-plus.gs](../src/alocacao-plus.gs)
