#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários e Property Fuzzing: Algoritmo de Casamento de Turmas (Turma Matcher)
Valida a extração de turmas de células da grade e o casamento com a estrutura do Jupiterweb.
"""

import random
import re
import string
import unittest


def extrair_info_turma_celula(texto_celula):
    """
    Espelho do algoritmo de extração de metadados da célula da grade.
    Retorna dicionário com:
      - eh_valida (bool)
      - codigo (str)
      - eh_pos (bool)
      - turmas_solicitadas (list de str normalizadas em 2 dígitos: ['01', '02'])
      - aula_semana (int ou None)
      - modalidade (str ou None)
      - eh_evento (bool)
    """
    if not texto_celula or not isinstance(texto_celula, str):
        return {"eh_valida": False, "codigo": "", "eh_pos": False, "turmas_solicitadas": [], "eh_evento": False}

    texto = texto_celula.strip()
    if not texto:
        return {"eh_valida": False, "codigo": "", "eh_pos": False, "turmas_solicitadas": [], "eh_evento": False}

    # Detecta anotações de eventos, provas, monitorias ou reservas
    padrao_evento = re.search(r'\b(prova|monitoria|reservado|projeto|oficina|semanau|palestra)\b', texto, re.IGNORECASE)
    eh_evento = bool(padrao_evento)

    # Captura código da disciplina: 3 letras + 3 a 4 dígitos OU 7 dígitos
    match_cod = re.search(r'\b([A-Za-z]{3})(\d{3,4})\b|\b(\d{7})\b', texto)
    if not match_cod:
        return {
            "eh_valida": False,
            "codigo": "",
            "eh_pos": False,
            "turmas_solicitadas": [],
            "eh_evento": eh_evento,
            "texto_original": texto
        }

    if match_cod.group(1) and match_cod.group(2):
        sigla = match_cod.group(1).upper()
        num = match_cod.group(2)
        if len(num) == 3:
            num = '0' + num
        codigo = sigla + num
        eh_pos = not num.startswith('0')
    else:
        codigo = match_cod.group(3)
        eh_pos = False  # 7 dígitos são da graduação

    # Extrai turma(s)
    # Casos: - T1, - T01, - T1 e T2, - T1 e 2, - T10, T2[1], T1 tv, T2 pv
    turmas = []
    # Busca segmento após "- T" ou "T"
    padrao_turma = re.search(r'(?:-\s*)?T\s*(\d{1,2})(?:\s*(?:e|E|\/)\s*T?\s*(\d{1,2}))?', texto)
    if padrao_turma:
        t1 = padrao_turma.group(1)
        turmas.append(t1.zfill(2))
        if padrao_turma.group(2):
            t2 = padrao_turma.group(2)
            turmas.append(t2.zfill(2))

    # Aula da semana [1], [2]
    match_aula = re.search(r'\[(\d+)\]', texto)
    aula_semana = int(match_aula.group(1)) if match_aula else None

    # Modalidade vinculada: tv ou pv
    match_mod = re.search(r'\b(pv|tv)\b', texto, re.IGNORECASE)
    modalidade = match_mod.group(1).lower() if match_mod else None

    return {
        "eh_valida": True,
        "codigo": codigo,
        "eh_pos": eh_pos,
        "turmas_solicitadas": turmas,
        "aula_semana": aula_semana,
        "modalidade": modalidade,
        "eh_evento": eh_evento,
        "texto_original": texto
    }


def casar_turma_com_dados(dados_disciplina, info_celula):
    """
    Realiza o casamento entre a intenção da célula e os dados do Júpiter.
    Gera o texto de hover e a turma padrão para o card modal.
    """
    if not dados_disciplina or not info_celula or not info_celula.get("eh_valida"):
        return {"sucesso": False, "label_hover": "", "turma_padrao": None}

    if info_celula.get("eh_pos"):
        return {"sucesso": False, "label_hover": "Disciplina de Pós-Graduação (Janus)", "turma_padrao": None}

    if dados_disciplina.get("semOferecimento"):
        return {"sucesso": False, "sem_oferecimento": True, "label_hover": "Sem oferecimento no semestre", "turma_padrao": None}

    turmas_jupiter = dados_disciplina.get("turmas", {})
    if not turmas_jupiter:
        return {"sucesso": False, "label_hover": "Sem turmas cadastradas", "turma_padrao": None}

    turmas_solicitadas = info_celula.get("turmas_solicitadas", [])

    # Caso 1: Célula especificou turma(s)
    if turmas_solicitadas:
        turmas_encontradas = []
        docentes_set = set()

        for t_sol in turmas_solicitadas:
            # Procura por chave '01' ou '1' ou por objeto com numero == t_sol
            t_obj = turmas_jupiter.get(t_sol) or turmas_jupiter.get(str(int(t_sol)))
            if not t_obj:
                for k, v in turmas_jupiter.items():
                    if str(v.get("numero", "")).zfill(2) == t_sol:
                        t_obj = v
                        break

            if t_obj:
                turmas_encontradas.append(t_obj)
                for d in t_obj.get("docentes", []):
                    if d and d != "A Designar" and d != "-":
                        docentes_set.add(d)

        turma_padrao = turmas_encontradas[0]["numero"] if turmas_encontradas else turmas_solicitadas[0]

        if not docentes_set:
            label_hover = "Docente: A designar"
        elif len(docentes_set) == 1:
            label_hover = f"Docente: {next(iter(docentes_set))}"
        else:
            lista_nomes = sorted(list(docentes_set))
            label_hover = f"Docentes: {', '.join(lista_nomes)}"

        return {
            "sucesso": True,
            "turma_padrao": str(turma_padrao).zfill(2),
            "turmas_encontradas": turmas_encontradas,
            "label_hover": label_hover,
            "docentes": sorted(list(docentes_set))
        }

    # Caso 2: Célula NÃO especificou turma (ex: SMA0300)
    todas_turmas = list(turmas_jupiter.values())
    if len(todas_turmas) == 1:
        t_unica = todas_turmas[0]
        docentes = [d for d in t_unica.get("docentes", []) if d and d != "A Designar" and d != "-"]
        if not docentes:
            label_hover = "Docente: A designar"
        elif len(docentes) == 1:
            label_hover = f"Docente: {docentes[0]}"
        else:
            label_hover = f"Docentes: {', '.join(docentes)}"
        return {
            "sucesso": True,
            "turma_padrao": str(t_unica.get("numero", "01")).zfill(2),
            "label_hover": label_hover,
            "docentes": docentes
        }
    else:
        primeira_turma = todas_turmas[0] if todas_turmas else {}
        return {
            "sucesso": True,
            "turma_padrao": str(primeira_turma.get("numero", "01")).zfill(2),
            "label_hover": "Docentes: Várias turmas",
            "docentes": []
        }


class TestTurmaMatching(unittest.TestCase):
    """Casos de teste unitário e de borda para o casamento de turmas."""

    def setUp(self):
        self.dados_sma0356 = {
            "codigo": "SMA0356",
            "nome": "Cálculo IV",
            "semOferecimento": False,
            "turmas": {
                "01": {"numero": "01", "codigoTurma": "2026101", "docentes": ["Ana Claudia Nabarro"]},
                "02": {"numero": "02", "codigoTurma": "2026102", "docentes": ["Sérgio Luís Zani"]},
                "03": {"numero": "03", "codigoTurma": "2026103", "docentes": ["A Designar"]},
                "04": {"numero": "04", "codigoTurma": "2026104", "docentes": ["Prof Teórico", "Prof Prático"]}
            }
        }

    def test_turma_simples(self):
        """Valida célula com turma única (T1 -> 01)."""
        info = extrair_info_turma_celula("SMA0356 - T1")
        self.assertTrue(info["eh_valida"])
        self.assertEqual(info["codigo"], "SMA0356")
        self.assertEqual(info["turmas_solicitadas"], ["01"])
        self.assertFalse(info["eh_pos"])

        resultado = casar_turma_com_dados(self.dados_sma0356, info)
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["turma_padrao"], "01")
        self.assertEqual(resultado["label_hover"], "Docente: Ana Claudia Nabarro")

    def test_turmas_compostas(self):
        """Valida célula com turmas compartilhadas (T1 e T2)."""
        info = extrair_info_turma_celula("SMA0356 - T1 e T2")
        self.assertEqual(info["turmas_solicitadas"], ["01", "02"])

        resultado = casar_turma_com_dados(self.dados_sma0356, info)
        self.assertTrue(resultado["sucesso"])
        self.assertIn("Ana Claudia Nabarro", resultado["label_hover"])
        self.assertIn("Sérgio Luís Zani", resultado["label_hover"])
        self.assertTrue(resultado["label_hover"].startswith("Docentes:"))

    def test_aula_semana_e_modalidade(self):
        """Valida sufixos de ocorrência semanal [1] e modalidades pv/tv."""
        info1 = extrair_info_turma_celula("SME0341 - T2[1]")
        self.assertEqual(info1["turmas_solicitadas"], ["02"])
        self.assertEqual(info1["aula_semana"], 1)

        info2 = extrair_info_turma_celula("SEM0388 - T1 tv")
        self.assertEqual(info2["turmas_solicitadas"], ["01"])
        self.assertEqual(info2["modalidade"], "tv")

    def test_celula_sem_turma_multiplas(self):
        """Valida célula sem turma quando existem várias turmas no Júpiter."""
        info = extrair_info_turma_celula("SMA0356")
        self.assertEqual(info["turmas_solicitadas"], [])

        resultado = casar_turma_com_dados(self.dados_sma0356, info)
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["label_hover"], "Docentes: Várias turmas")

    def test_celula_sem_turma_unica(self):
        """Valida célula sem turma quando existe apenas UMA turma no Júpiter."""
        dados_turma_unica = {
            "codigo": "SET0183",
            "semOferecimento": False,
            "turmas": {
                "01": {"numero": "01", "docentes": ["Márcio Roberto Silva"]}
            }
        }
        info = extrair_info_turma_celula("SET0183")
        resultado = casar_turma_com_dados(dados_turma_unica, info)
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["label_hover"], "Docente: Márcio Roberto Silva")

    def test_docente_a_designar(self):
        """Valida comportamento para turmas sem docente atribuído."""
        info = extrair_info_turma_celula("SMA0356 - T3")
        resultado = casar_turma_com_dados(self.dados_sma0356, info)
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["label_hover"], "Docente: A designar")

    def test_disciplina_pos_graduacao(self):
        """Valida que códigos de pós-graduação (Janus) são sinalizados e excluídos da fila."""
        info = extrair_info_turma_celula("SEP5864 - Pós-Grad")
        self.assertTrue(info["eh_pos"])
        self.assertEqual(info["codigo"], "SEP5864")

        resultado = casar_turma_com_dados(self.dados_sma0356, info)
        self.assertFalse(resultado["sucesso"])
        self.assertIn("Pós-Graduação", resultado["label_hover"])

    def test_codigo_sete_digitos(self):
        """Valida código puramente numérico interunidades (7 dígitos)."""
        info = extrair_info_turma_celula("7600006 - T1")
        self.assertEqual(info["codigo"], "7600006")
        self.assertFalse(info["eh_pos"])
        self.assertEqual(info["turmas_solicitadas"], ["01"])

    def test_eventos_e_provas(self):
        """Valida detecção de eventos e provas."""
        info1 = extrair_info_turma_celula("01/12 - prova 7600110")
        self.assertTrue(info1["eh_evento"])
        self.assertEqual(info1["codigo"], "7600110")

        info2 = extrair_info_turma_celula("Monitoria - SME0341")
        self.assertTrue(info2["eh_evento"])
        self.assertEqual(info2["codigo"], "SME0341")

    def test_property_fuzzing_estabilidade(self):
        """Property-Based Fuzzing com 1.000 strings aleatórias garantindo 0 crashes/exceções."""
        letras = string.ascii_letters + string.digits + " \t\r\n-_/[]().,"
        for _ in range(1000):
            tamanho = random.randint(0, 80)
            texto_aleatorio = "".join(random.choice(letras) for _ in range(tamanho))
            # O extrator NUNCA deve lançar exceção
            info = extrair_info_turma_celula(texto_aleatorio)
            self.assertIsInstance(info, dict)
            self.assertIn("eh_valida", info)

            # O casador NUNCA deve lançar exceção
            resultado = casar_turma_com_dados(self.dados_sma0356, info)
            self.assertIsInstance(resultado, dict)


if __name__ == "__main__":
    unittest.main()
