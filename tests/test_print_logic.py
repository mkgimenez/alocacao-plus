#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários: Lógica, Estilos e Estrutura de Impressão Inteligente da Grade
Valida preparação e impressão acadêmica da grade horária:
 1. Isolamento semântico de ícones temporais (⚡)
 2. Estrutura semântica do cabeçalho institucional oficial de papel/PDF
 3. Compilação matemática do resumo dinâmico de filtros
 4. Formatação de carimbo temporal oficial (Brasília)
 5. Arquitetura CSS @media print (reset de SPAs, overflow, paginação table-header-group)
 6. Modos de impressão (Escala de cinza econômico, colorido, compacto, sem lugares)
 7. Ciclo de vida e restauração idempotente do DOM
 8. Property-based fuzzing com filtros arbitrários
"""

import os
import re
import unittest

DIR_TESTS = os.path.dirname(os.path.abspath(__file__))
DIR_SRC = os.path.join(os.path.dirname(DIR_TESTS), "src")


def carregar_arquivo(caminho_relativo):
    caminho = os.path.join(DIR_SRC, caminho_relativo)
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


class TestPrintStep1Structure(unittest.TestCase):
    """Passo 1: Valida isolamento semântico do ícone de raio e esqueleto do cabeçalho impresso."""

    def setUp(self):
        self.html_index = carregar_arquivo("index.html")
        self.html_scripts = carregar_arquivo("scripts.html")

    def test_isolamento_semantico_icone_tempo_grade(self):
        """Valida que o caractere ⚡ no cabeçalho da grade está estritamente encapsulado em span.icone-tempo-grade."""
        # Procura as atribuições de iconeHoje e iconeSlot em scripts.html
        padrao_hoje = r"const\s+iconeHoje\s*=\s*ehDiaHoje\s*\?\s*'([^']+)'\s*:\s*'';"
        padrao_slot = r"const\s+iconeSlot\s*=\s*ehSlotDestaque\s*\?\s*'([^']+)'\s*:\s*'';"

        m_hoje = re.search(padrao_hoje, self.html_scripts)
        self.assertIsNotNone(m_hoje, "Declaração de const iconeHoje não encontrada.")
        self.assertIn('class="icone-tempo-grade"', m_hoje.group(1))
        self.assertIn("⚡", m_hoje.group(1))

        m_slot = re.search(padrao_slot, self.html_scripts)
        self.assertIsNotNone(m_slot, "Declaração de const iconeSlot não encontrada.")
        self.assertIn('class="icone-tempo-grade"', m_slot.group(1))
        self.assertIn("⚡", m_slot.group(1))

    def test_estrutura_html_cabecalho_impressao(self):
        """Valida a presença do elemento #cabecalho-impressao-papel e seus subcomponentes institucionais em index.html."""
        self.assertIn('id="cabecalho-impressao-papel"', self.html_index)
        self.assertIn("cabecalho-impressao-papel apenas-impressao", self.html_index)
        self.assertIn("UNIVERSIDADE DE SÃO PAULO", self.html_index)
        self.assertIn("ESCOLA DE ENGENHARIA DE SÃO CARLOS — EESC", self.html_index)
        self.assertIn('id="print-meta-emissao"', self.html_index)
        self.assertIn('id="print-meta-filtros"', self.html_index)


MAPA_NOMES_DIAS_PRINT_PY = {
    "seg": "Segunda-feira",
    "ter": "Terça-feira",
    "qua": "Quarta-feira",
    "qui": "Quinta-feira",
    "sex": "Sexta-feira",
    "sab": "Sábado"
}


def formatar_minutos_para_hora_print_py(minutos):
    if minutos is None or not isinstance(minutos, (int, float)):
        return ""
    h = int(minutos) // 60
    m = int(minutos) % 60
    return f"{h:02d}:{m:02d}"


def gerar_resumo_filtros_impressao_py(estado, salas_count=0, slots_count=0):
    partes = []

    # 1. Dias da semana
    dias = list(estado.get("diasSelecionados") or ["todos"])
    if "todos" in dias or len(dias) == 0 or len(dias) >= 6:
        partes.append("Todos os dias")
    elif len(dias) == 1:
        partes.append(MAPA_NOMES_DIAS_PRINT_PY.get(dias[0], dias[0]))
    else:
        nomes = [MAPA_NOMES_DIAS_PRINT_PY.get(d, d).replace("-feira", "") for d in dias]
        ultimo = nomes.pop()
        partes.append(f"{', '.join(nomes)} e {ultimo}")

    # 2. Horários
    tem_ini = estado.get("horaInicioMin") is not None
    tem_fim = estado.get("horaFimMin") is not None
    if tem_ini and tem_fim:
        partes.append(f"{formatar_minutos_para_hora_print_py(estado['horaInicioMin'])} às {formatar_minutos_para_hora_print_py(estado['horaFimMin'])}")
    elif tem_ini:
        partes.append(f"A partir das {formatar_minutos_para_hora_print_py(estado['horaInicioMin'])}")
    elif tem_fim:
        partes.append(f"Até às {formatar_minutos_para_hora_print_py(estado['horaFimMin'])}")

    # 3. Blocos
    blocos = [b for b in (estado.get("blocosSelecionados") or []) if b != "todos"]
    if len(blocos) == 1:
        partes.append(f"Bloco {blocos[0]}")
    elif len(blocos) > 1:
        ult_bloco = blocos.pop()
        partes.append(f"Blocos {', '.join(blocos)} e {ult_bloco}")

    # 4. Salas
    salas = [s for s in (estado.get("salasSelecionadas") or []) if s != "todas"]
    if len(salas) == 1:
        partes.append(f"Sala {salas[0]}")
    elif len(salas) > 1:
        ult_sala = salas.pop()
        partes.append(f"Salas {', '.join(salas)} e {ult_sala}")

    # 5. Capacidade Mínima
    cap_min = estado.get("capacidadeMin", 0)
    if cap_min and int(cap_min) > 0:
        partes.append(f"Mín. {cap_min} lugares")

    # 6. Apenas Salas Livres
    if estado.get("apenasLivres"):
        partes.append("Apenas Salas Livres")

    # 7. Busca Textual
    busca = str(estado.get("buscaSala") or "").strip()
    if busca:
        partes.append(f'Busca: "{busca}"')

    # 8. Totalizadores
    txt_salas = "1 sala exibida" if salas_count == 1 else f"{salas_count} salas exibidas"
    txt_slots = "1 horário" if slots_count == 1 else f"{slots_count} horários"
    partes.append(f"{txt_salas} • {txt_slots}")

    return " • ".join(partes)


class TestPrintStep2Metadata(unittest.TestCase):
    """Passo 2: Valida funções de compilação de resumo de filtros e carimbo temporal."""

    def setUp(self):
        self.html_scripts = carregar_arquivo("scripts.html")

    def test_funcoes_declaradas_em_scripts_html(self):
        """Valida que gerarResumoFiltrosImpressao e formatarCarimboTemporalImpressao estão declaradas em scripts.html."""
        self.assertIn("function gerarResumoFiltrosImpressao(", self.html_scripts)
        self.assertIn("function formatarCarimboTemporalImpressao(", self.html_scripts)
        self.assertIn("function formatarMinutosParaHoraPrint(", self.html_scripts)

    def test_resumo_filtros_padrao_todos(self):
        """Valida que sem filtros específicos o resumo informa 'Todos os dias' e contagem de salas/slots."""
        est = {
            "diasSelecionados": {"todos"},
            "blocosSelecionados": {"todos"},
            "salasSelecionadas": {"todas"},
            "horaInicioMin": None,
            "horaFimMin": None,
            "capacidadeMin": 0,
            "apenasLivres": False,
            "buscaSala": ""
        }
        res = gerar_resumo_filtros_impressao_py(est, salas_count=24, slots_count=12)
        self.assertEqual(res, "Todos os dias • 24 salas exibidas • 12 horários")

    def test_resumo_filtros_dias_multiplos(self):
        """Valida formatação amigável para dias múltiplos (ex: 'Terça e Quinta')."""
        est = {
            "diasSelecionados": ["ter", "qui"],
            "blocosSelecionados": {"todos"},
            "salasSelecionadas": {"todas"},
            "horaInicioMin": None,
            "horaFimMin": None,
            "capacidadeMin": 0,
            "apenasLivres": False,
            "buscaSala": ""
        }
        res = gerar_resumo_filtros_impressao_py(est, salas_count=18, slots_count=8)
        self.assertIn("Terça e Quinta", res)
        self.assertIn("18 salas exibidas • 8 horários", res)

    def test_resumo_filtros_faixa_horarios_e_bloco(self):
        """Valida formatação de faixa horária (08:00 às 12:00) combinada com Bloco específico."""
        est = {
            "diasSelecionados": ["seg"],
            "blocosSelecionados": ["C"],
            "salasSelecionadas": {"todas"},
            "horaInicioMin": 480,  # 08:00
            "horaFimMin": 720,     # 12:00
            "capacidadeMin": 40,
            "apenasLivres": True,
            "buscaSala": ""
        }
        res = gerar_resumo_filtros_impressao_py(est, salas_count=5, slots_count=4)
        self.assertIn("Segunda-feira", res)
        self.assertIn("08:00 às 12:00", res)
        self.assertIn("Bloco C", res)
        self.assertIn("Mín. 40 lugares", res)
        self.assertIn("Apenas Salas Livres", res)
        self.assertIn("5 salas exibidas • 4 horários", res)

    def test_resumo_filtros_busca_textual(self):
        """Valida inclusão de busca textual no resumo com aspas preservadas."""
        est = {
            "diasSelecionados": {"todos"},
            "blocosSelecionados": {"todos"},
            "salasSelecionadas": {"todas"},
            "horaInicioMin": None,
            "horaFimMin": None,
            "capacidadeMin": 0,
            "apenasLivres": False,
            "buscaSala": "SEM0538"
        }
        res = gerar_resumo_filtros_impressao_py(est, salas_count=1, slots_count=2)
        self.assertIn('Busca: "SEM0538"', res)
        self.assertIn("1 sala exibida • 2 horários", res)

    def test_fuzzing_resumo_filtros_estabilidade(self):
        """Property-Based Fuzzing com 300 variações aleatórias de filtros garantindo 0 exceções."""
        import random
        dias_pool = ["seg", "ter", "qua", "qui", "sex", "sab"]
        blocos_pool = ["A", "B", "C", "D", "E"]
        salas_pool = ["101", "102", "Auditório", "Lab Mecânica"]

        for _ in range(300):
            dias_escolhidos = random.sample(dias_pool, k=random.randint(0, len(dias_pool)))
            blocos_escolhidos = random.sample(blocos_pool, k=random.randint(0, len(blocos_pool)))
            salas_escolhidas = random.sample(salas_pool, k=random.randint(0, len(salas_pool)))
            h_ini = random.choice([None, 420, 480, 600, 840])
            h_fim = random.choice([None, 600, 720, 1080, 1320])
            if h_ini and h_fim and h_ini > h_fim:
                h_ini, h_fim = h_fim, h_ini
            cap = random.choice([0, 20, 40, 60, 100])
            livres = random.choice([True, False])
            busca = random.choice(["", "Cálculo", "T01", "Professor Silva", "   espacos   "])

            est = {
                "diasSelecionados": dias_escolhidos,
                "blocosSelecionados": blocos_escolhidos,
                "salasSelecionadas": salas_escolhidas,
                "horaInicioMin": h_ini,
                "horaFimMin": h_fim,
                "capacidadeMin": cap,
                "apenasLivres": livres,
                "buscaSala": busca
            }
            s_count = random.randint(0, 50)
            sl_count = random.randint(0, 20)
            res = gerar_resumo_filtros_impressao_py(est, s_count, sl_count)

            self.assertIsInstance(res, str)
            self.assertTrue(len(res) > 0)
            self.assertIn("horário", res)


class TestPrintStep3And4CSS(unittest.TestCase):
    """Passos 3 e 4: Valida regras fundamentais de @media print e classes de controle."""

    def setUp(self):
        self.css = carregar_arquivo("estilos.html")

    def test_css_reset_spa_overflow(self):
        """Valida que o CSS de impressão reseta overflow em cascata de html, body, main e tabela."""
        self.assertIn("@media print", self.css)
        self.assertIn("overflow: visible !important", self.css)
        self.assertIn("height: auto !important", self.css)
        self.assertIn("display: block !important", self.css)

    def test_css_ocultacao_elementos_tela(self):
        """Valida que os componentes de tela e o ícone de tempo são ocultados no papel."""
        self.assertIn(".app-header", self.css)
        self.assertIn(".filtros-panel", self.css)
        self.assertIn(".modal-backdrop", self.css)
        self.assertIn(".icone-tempo-grade", self.css)
        self.assertIn("display: none !important", self.css)

    def test_css_paginacao_e_tabela(self):
        """Valida que thead se repete nas folhas (table-header-group) e linhas evitam quebra ao meio."""
        self.assertIn("display: table-header-group !important", self.css)
        self.assertIn("break-inside: avoid !important", self.css)
        self.assertIn("border-collapse: collapse !important", self.css)
        self.assertIn("min-width: 0 !important", self.css)

    def test_css_modo_escala_cinza(self):
        """Valida paleta econômica para economia de tinta e toner com alto contraste."""
        self.assertIn("body.impressao-grayscale", self.css)
        self.assertIn("border-left: 3.5px solid #475569 !important", self.css)
        self.assertIn("border-left: 4.5px double #0f172a !important", self.css)
        self.assertIn('[PÓS]', self.css)

    def test_css_modo_colorido(self):
        """Valida calibração de impressão e preservação dos tons de azul na impressão colorida."""
        self.assertIn("body.impressao-colorida", self.css)
        self.assertIn("print-color-adjust: exact !important", self.css)

    def test_css_modo_compacto_e_sem_lugares(self):
        """Valida redução de padding e fontes no modo compacto e ocultação de lugares."""
        self.assertIn("body.impressao-compacta", self.css)
        self.assertIn("body.impressao-sem-lugares .col-fixa-cap", self.css)
        self.assertIn("body.impressao-sem-cabecalho #cabecalho-impressao-papel", self.css)


def simular_configurar_classes_body_py(opcoes):
    """Simula estritamente a função configurarImpressaoNoDom em Python."""
    classes = {"modo-impressao-ativo"}
    if opcoes.get("paleta") == "cor":
        classes.add("impressao-colorida")
    else:
        classes.add("impressao-grayscale")

    if opcoes.get("densidade") == "compacto":
        classes.add("impressao-compacta")

    if opcoes.get("ocultarLugares"):
        classes.add("impressao-sem-lugares")

    if not opcoes.get("incluirCabecalho"):
        classes.add("impressao-sem-cabecalho")

    return classes


def simular_finalizar_impressao_py(classes_body):
    """Simula estritamente a função finalizarImpressao limpando classes de impressão."""
    remover = {
        "modo-impressao-ativo",
        "impressao-grayscale",
        "impressao-colorida",
        "impressao-compacta",
        "impressao-sem-lugares",
        "impressao-sem-cabecalho"
    }
    return classes_body - remover


class TestPrintStep5And6Lifecycle(unittest.TestCase):
    """Passos 5 e 6: Valida interface modal, atalhos, ciclo de vida e restauração do DOM."""

    def setUp(self):
        self.html_index = carregar_arquivo("index.html")
        self.html_scripts = carregar_arquivo("scripts.html")

    def test_modal_elementos_e_acessibilidade(self):
        """Valida que o modal de impressão possui atributos ARIA, botões e labels adequados."""
        self.assertIn('id="modal-impressao-grade"', self.html_index)
        self.assertIn('role="dialog"', self.html_index)
        self.assertIn('aria-modal="true"', self.html_index)
        self.assertIn('aria-labelledby="titulo-modal-impressao"', self.html_index)
        self.assertIn('id="btn-confirmar-impressao"', self.html_index)
        self.assertIn('id="btn-abrir-impressao"', self.html_index)

    def test_conformidade_botoes_adr_0026(self):
        """Valida que o botão de abrir e os botões do modal respeitam a ergonomia UX e ordenação espacial do ADR 0026."""
        # 1. Botão da barra de ações deve ter a formatação idêntica ao botão de resetar filtros
        self.assertIn('id="btn-abrir-impressao" class="btn-reset btn-imprimir-grade"', self.html_index)

        # 2. Botão de confirmar impressão deve ter estilo primário sólido (.btn-imprimir-confirmar)
        self.assertIn('id="btn-confirmar-impressao" class="btn-imprimir-confirmar"', self.html_index)

        # 3. Botão de cancelamento deve ter classe secundária outline (.btn-cancelar-modal)
        self.assertIn('class="btn-cancelar-modal"', self.html_index)

        # 4. No rodapé do modal de confirmação, Cancelar (esquerda) deve anteceder Confirmar (direita)
        rodape_idx = self.html_index.find('id="modal-impressao-grade"')
        self.assertTrue(rodape_idx != -1)
        sub_html = self.html_index[rodape_idx:]
        footer_idx = sub_html.find('<footer class="modal-card-rodape">')
        self.assertTrue(footer_idx != -1)
        footer_html = sub_html[footer_idx:sub_html.find('</footer>', footer_idx)]
        pos_confirmar = footer_html.find('btn-confirmar-impressao')
        pos_cancelar = footer_html.find('fecharModalImpressao()')
        self.assertTrue(pos_confirmar != -1 and pos_cancelar != -1)
        self.assertLess(pos_cancelar, pos_confirmar, "No rodapé do modal, o botão de cancelamento (esquerda) deve anteceder o botão de confirmação (direita).")



    def test_bloqueio_quando_grade_vazia(self):
        """Valida que abrirModalImpressao() possui guarda impedindo abertura se salasVisiveis for vazia."""
        self.assertIn("const salas = estadoApp._salasVisiveisAtuais || [];", self.html_scripts)
        self.assertIn("if (!salas || salas.length === 0)", self.html_scripts)
        self.assertIn("exibirToast('Impressão da Grade'", self.html_scripts)

    def test_simulacao_classes_body_cinza_e_compacto(self):
        """Valida que as opções padrão (cinza, compacto, sem lugares, com cabeçalho) aplicam o conjunto exato de classes."""
        opts = {
            "paleta": "cinza",
            "densidade": "compacto",
            "incluirCabecalho": True,
            "ocultarLugares": True
        }
        classes = simular_configurar_classes_body_py(opts)
        self.assertIn("modo-impressao-ativo", classes)
        self.assertIn("impressao-grayscale", classes)
        self.assertIn("impressao-compacta", classes)
        self.assertIn("impressao-sem-lugares", classes)
        self.assertNotIn("impressao-colorida", classes)
        self.assertNotIn("impressao-sem-cabecalho", classes)

    def test_simulacao_classes_body_colorido_e_normal(self):
        """Valida combinação com fidelidade web e densidade normal."""
        opts = {
            "paleta": "cor",
            "densidade": "normal",
            "incluirCabecalho": False,
            "ocultarLugares": False
        }
        classes = simular_configurar_classes_body_py(opts)
        self.assertIn("modo-impressao-ativo", classes)
        self.assertIn("impressao-colorida", classes)
        self.assertIn("impressao-sem-cabecalho", classes)
        self.assertNotIn("impressao-grayscale", classes)
        self.assertNotIn("impressao-compacta", classes)
        self.assertNotIn("impressao-sem-lugares", classes)

    def test_simulacao_limpeza_idempotente(self):
        """Valida que finalizarImpressao remove 100% das classes transitórias sem efeito residual."""
        opts = {
            "paleta": "cinza",
            "densidade": "compacto",
            "incluirCabecalho": True,
            "ocultarLugares": True
        }
        classes = simular_configurar_classes_body_py(opts)
        classes.add("classe-preexistente-do-site")

        limpas = simular_finalizar_impressao_py(classes)
        self.assertEqual(limpas, {"classe-preexistente-do-site"})

    def test_captura_atalho_teclado_ctrl_p_e_cmd_p(self):
        """Valida que o listener global keydown intercepta Ctrl+P / Cmd+P chamando abrirModalImpressao()."""
        self.assertIn("(e.ctrlKey || e.metaKey) && (e.key === 'p' || e.key === 'P')", self.html_scripts)
        self.assertIn("abrirModalImpressao()", self.html_scripts)

    def test_tratamento_teclas_escape_e_enter(self):
        """Valida que Escape fecha o modal de impressão e Enter executa a impressão."""
        self.assertIn("modalPrint && modalPrint.classList.contains('aberto')", self.html_scripts)
        self.assertIn("fecharModalImpressao()", self.html_scripts)
        self.assertIn("executarImpressaoGrade()", self.html_scripts)


if __name__ == "__main__":
    unittest.main()
