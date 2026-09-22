# 2. Migração de Painel Lateral (Sidebar) para Web App Autônomo

* **Data:** 2026-09-17
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
A versão inicial do sistema operava como um script vinculado (*container-bound*) a uma cópia da planilha ("Grade Plus"), utilizando a interface nativa do Google Sheets:
1. **Painel Lateral (*Sidebar*):** Renderizado via `SpreadsheetApp.getUi().showSidebar()`, com largura fixa e limitada a cerca de 340 pixels.
2. **Manipulação Direta da Planilha:** Para filtrar disciplinas, o script executava laços no Apps Script chamando `sheet.hideRow()` e `sheet.hideColumn()` diretamente na aba da grade.
3. **Acionador Automático:** Utilizava acionadores instaláveis `onOpen` para tentar abrir o painel assim que o usuário acessava a planilha.

Essa abordagem gerou graves gargalos operacionais:
* **Espaço insuficiente:** Uma grade horária de 6 dias (segunda a sábado) com até 14 faixas de horário e mais de 40 salas é impossível de navegar confortavelmente em uma barra lateral de 340px.
* **Lentidão extrema:** Ocultar e exibir dezenas de linhas e colunas via API do Google Sheets levava de 8 a 15 segundos por filtro selecionado.
* **Conflito de concorrência:** Como a planilha é compartilhada, as ações de ocultar/exibir linhas de um usuário alteravam a visualização para todos os outros usuários conectados no mesmo instante.
* **Atrito de segurança e autorização (OAuth):** Visitantes e alunos recebiam telas de alerta com pedido de autorização para executar scripts ao abrir o arquivo.

## Alternativas Consideradas
* **Diálogo Modal Centralizado (`showModalDialog`):** Maior que a sidebar, mas bloqueia a navegação na planilha e ainda sofre com os problemas de concorrência e autorização.
* **Filtros Nativos e Tabela Dinâmica do Sheets:** Não suporta a complexidade de mesclagens de horário (aulas de 2 ou 4 blocos) nem o cruzamento dinâmico de salas livres no intervalo corrente.
* **Web App Autônomo via Google Apps Script (`HtmlService`):** Publicar a aplicação como Aplicativo da Web independente com URL própria, lendo a planilha de fundo em modo somente leitura.

## Decisão Adotada
Desacoplar a interface da planilha Google e transformar o **Alocação Plus** em um **Web App autônomo** servido via `doGet(e)`:
1. A interface é renderizada como uma aplicação web completa (SPA), responsiva e de largura total no navegador.
2. A implantação é configurada com:
   * **Executar como:** *Eu* (conta mantenedora do sistema).
   * **Quem tem acesso:** *Qualquer pessoa* (ou restrito a contas USP).
3. A planilha oficial do SVGRAD permanece intacta como fonte de dados em segundo plano (`SpreadsheetApp.openById`), sem sofrer ocultação de linhas ou edições concorrentes.
4. Na planilha, foram mantidas apenas ações essenciais de menu (`onOpen`: link do Web App e botão de limpar cache), com remoção automática de acionadores instaláveis legados (`removerAcionadoresLegados()`).

## Consequências
### Positivas (+)
* **Experiência de Usuário Fluida:** Interface moderna, responsiva para celulares, tablets e monitores ultrawide.
* **Fim dos Conflitos de Concorrência:** Cada usuário executa seu próprio estado no navegador; centenas de consultas simultâneas ocorrem de forma isolada.
* **Zero Fricção de Login/Permissões:** Como o Web App roda sob a identidade do implantador, alunos e docentes não recebem solicitações de autorização intrusivas.
* **Segurança e Preservação dos Dados:** A planilha oficial do SVGRAD fica 100% protegida contra alterações acidentais de layout ou conteúdo.

### Negativas / Trade-offs (-)
* O usuário não consulta os dados dentro das células do Google Sheets, necessitando abrir a URL do Web App (mitigado pelo menu "💡 Plus > 🌐 Abrir Web App" na própria planilha).

## Referências no Código
* [src/alocacao-plus.gs](../src/alocacao-plus.gs) (funções `doGet`, `mostrarLinkWebApp`, `removerAcionadoresLegados`)
* [src/index.html](../src/index.html)
