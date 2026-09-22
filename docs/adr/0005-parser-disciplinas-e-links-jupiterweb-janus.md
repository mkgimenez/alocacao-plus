# 5. Parser de Disciplinas e Hiperlinks com Jupiterweb e Janus

* **Data:** 2026-09-19
* **Status:** Aceito
* **Decisores:** Equipe Técnica SCAE / EESC-USP

## Contexto e Problema
As células da grade horária oficial contêm anotações compactas combinando código da disciplina, turma, aula da semana e modalidade pedagógica, conforme documentado em [`docs/especificacao-disciplinas.md`](../especificacao-disciplinas.md):
* Exemplos: `SEM0538 - T1`, `SEP5864 - Pós-Grad`, `SMA0304 - T3[2]`, `SEM0388 - T1 tv`, `7600110`.

Ao consultar a alocação de uma sala, alunos e professores frequentemente precisam conferir:
1. Ementa e pré-requisitos da disciplina.
2. Docentes responsáveis pela turma.
3. Número de vagas oferecidas e alunos inscritos.

Anteriormente, o usuário era obrigado a copiar o código, abrir o portal da USP em outra aba e pesquisar manualmente. Além disso, a USP possui dois sistemas acadêmicos distintos e independentes:
* **Jupiterweb:** Sistema de graduação.
* **Janus:** Sistema de pós-graduação.

Direcionar um código de pós-graduação para o Jupiterweb (ou vice-versa) resulta em erro de "Disciplina não encontrada".

## Alternativas Consideradas
* **Exibir apenas texto estático:** Não aproveita o potencial de hiperconectividade da web e mantém a sobrecarga de busca manual para os usuários.
* **Web scraping em tempo real dos portais da USP:** Lento, sujeito a bloqueios por firewall da USP e quebraria sempre que a USP alterasse o HTML dos portais.
* **Parser com classificação sintática e geração de links diretos:** Utilizar a regra de codificação da USP para identificar o nível acadêmico e injetar hyperlinks para as URLs públicas parametrizadas oficiais.

## Decisão Adotada
Implementar o parser `formatarTextoComLinksHtml` no backend com as seguintes regras de negócio:
1. **Expressão Regular de Captura:**
   ```regex
   /\b([A-Za-z]{3})(\d{3,4})\b|\b(\d{7})\b/g
   ```
2. **Classificação Automática de Nível Acadêmico:**
   * **Graduação (Jupiterweb):** Códigos com 3 letras e 4 dígitos iniciando por `0` (ex: `SEM0538`, `SMA0304`) ou códigos puramente numéricos de 7 dígitos (ex: `7600110`, disciplinas interunidades).  
     *URL Base:* `https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis=`
   * **Pós-Graduação (Janus):** Códigos com 3 letras e 4 dígitos iniciando por `1` a `9` (ex: `SEP5864`, `SHS5991`).  
     *URL Base:* `https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis=`
3. **Preservação de Conteúdo e Identidade Visual:**
   * O texto visível original da célula permanece 100% inalterado.
   * Células com eventos pontuais (ex: `01/12 - prova 7600110`) têm o código linkado preservando a anotação de prova e data.
   * O estilo padrão do navegador para links (azul `#1155cc` sublinhado) é explicitamente neutralizado via CSS (`.link-disc`), preservando as cores semânticas da planilha (azul para outras unidades, cereja para provas, vermelho para pendências).
   * Inclusão de atributos de acessibilidade e segurança: `target="_blank"` e `rel="noopener noreferrer"`.

## Consequências
### Positivas (+)
* **Acesso Imediato à Informação:** Com apenas um clique na célula da grade, o usuário abre a ficha completa da turma no sistema acadêmico oficial correto.
* **Diferenciação Visual Sutil:** Classes CSS distintas (`.link-grad` e `.link-pos`) com tooltips explicativos ("Consultar SEM0538 no Jupiterweb (Graduação USP)").
* **Segurança:** Todas as strings são sanitizadas via `escapeHtml()` antes da concatenação, eliminando riscos de XSS.

### Negativas / Trade-offs (-)
* Depende da estabilidade dos endpoints de consulta pública do Jupiterweb e Janus. Se a Reitoria da USP alterar o padrão de URLs, as URLs base precisarão ser atualizadas (atenuado pelo ADR 0007, que permite essa alteração via aba `_Config`).

## Referências no Código
* [src/alocacao-plus.gs](../src/alocacao-plus.gs) (função `formatarTextoComLinksHtml`)
* [src/estilos.html](../src/estilos.html) (classes `.link-disc`, `.link-grad`, `.link-pos`)
* [docs/especificacao-disciplinas.md](../especificacao-disciplinas.md)
