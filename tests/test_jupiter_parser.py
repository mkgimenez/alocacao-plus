#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários e Fuzzing: Parser HTML do Jupiterweb
Valida a extração de metadados, turmas, docentes e horários a partir de HTML real e sintético.
"""

import html as html_lib
import os
import random
import re
import string
import unittest

DIR_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def decodificar_entidades(texto):
    """Decodifica entidades HTML nomeadas e numéricas e limpa espaços."""
    if not texto:
        return ""
    texto = html_lib.unescape(texto)
    # Trata caracteres de substituição comuns
    texto = texto.replace("\ufffd", "").replace("&nbsp;", " ")
    return " ".join(texto.split())


def parsear_html_jupiterweb(codigo, html):
    """
    Parser Python de referência que espelha exatamente a implementação JavaScript do Apps Script.
    """
    if not html or not isinstance(html, str):
        return {"codigo": codigo, "semOferecimento": True, "turmas": {}, "nome": ""}

    # 1. Verifica se não há oferecimento
    if re.search(r'existe\s+oferecimento\s+para\s+a\s+sigla', html, re.I):
        return {
            "codigo": codigo,
            "nome": "",
            "semOferecimento": True,
            "turmas": {}
        }

    # 2. Extrai cabeçalho (Código e Nome da Disciplina)
    nome_disciplina = ""
    match_cab = re.search(r'(?:[A-Za-z]{3}\d{4}|\d{7})\s*-\s*([^<]+)</b>', html, re.I)
    if match_cab:
        nome_disciplina = decodificar_entidades(match_cab.group(1))

    # 3. Segmenta blocos de turmas
    padrao_split = r'C(?:[oó\u00f3\ufffd]|&oacute;)?digo\s+da\s+Turma:[\s\S]*?<td[^>]*>[\s\S]*?(\d{7})'
    partes = re.split(padrao_split, html, flags=re.I)

    if len(partes) < 2:
        return {
            "codigo": codigo,
            "nome": nome_disciplina,
            "semOferecimento": True,
            "turmas": {}
        }

    turmas = {}

    for i in range(1, len(partes), 2):
        cod_turma = partes[i].strip()
        chunk = partes[i + 1]

        # Número limpo da turma (últimos 2 dígitos, ex: 2026201 -> 01)
        num_turma = cod_turma[-2:] if len(cod_turma) >= 2 else cod_turma

        # Período: Início e Fim
        inicio = ""
        fim = ""
        m_inicio = re.search(r'In&iacute;cio:[\s\S]*?<td[^>]*>[\s\S]*?(\d{2}/\d{2}/\d{4})', chunk, re.I)
        if m_inicio:
            inicio = m_inicio.group(1)

        m_fim = re.search(r'Fim:[\s\S]*?<td[^>]*>[\s\S]*?(\d{2}/\d{2}/\d{4})', chunk, re.I)
        if m_fim:
            fim = m_fim.group(1)

        # Tipo da turma
        tipo_turma = "Teórica"
        m_tipo = re.search(r'Tipo\s+da\s+Turma:[\s\S]*?<td[^>]*><font[^>]*><span[^>]*>\s*([^\s<]+)', chunk, re.I)
        if m_tipo:
            tipo_raw = decodificar_entidades(m_tipo.group(1))
            if "Pr" in tipo_raw:
                tipo_turma = "Prática"
            elif "Te" in tipo_raw:
                tipo_turma = "Teórica"
            else:
                tipo_turma = tipo_raw

        # Observações
        observacoes = ""
        m_obs = re.search(r'Observa[^\:]*?:[\s\S]*?<td[^>]*><font[^>]*><span[^>]*>([\s\S]*?)</span>', chunk, re.I)
        if m_obs:
            observacoes = decodificar_entidades(re.sub(r'<[^>]+>', ' ', m_obs.group(1)))

        # Tabela de Horários e Docentes
        horarios = []
        docentes_set = set()
        ultimo_horario = None

        linhas_horario = re.findall(r'<tr[^>]*txt_verdana_8pt_gray[^>]*>[\s\S]*?</tr>', chunk, re.I)
        for lh in linhas_horario:
            colunas = re.findall(r'<td[^>]*>([\s\S]*?)</td>', lh, re.I)
            if len(colunas) >= 4:
                cols_limpas = [decodificar_entidades(re.sub(r'<[^>]+>', ' ', c)).strip() for c in colunas]
                dia = cols_limpas[0]
                hora_ini = cols_limpas[1]
                hora_fim = cols_limpas[2]
                prof = re.sub(r'^\([A-Za-z]\)\s*', '', cols_limpas[3]).strip()

                tem_horario = bool(hora_ini and hora_fim and re.match(r'\d{2}:\d{2}', hora_ini))

                if tem_horario:
                    if prof and prof != "-" and "Prof(a)" not in prof:
                        docentes_set.add(prof)
                        nome_doc = prof
                    else:
                        nome_doc = "A Designar"

                    ultimo_horario = {
                        "dia": dia,
                        "inicio": hora_ini,
                        "fim": hora_fim,
                        "docente": nome_doc,
                        "professores": [nome_doc] if nome_doc != "A Designar" else []
                    }
                    horarios.append(ultimo_horario)
                elif prof and prof != "-" and "Prof(a)" not in prof:
                    # Linha de continuação com professor adicional no mesmo horário (co-docência)
                    docentes_set.add(prof)
                    if ultimo_horario:
                        if not ultimo_horario.get("professores"):
                            ultimo_horario["professores"] = [ultimo_horario["docente"]] if ultimo_horario.get("docente") != "A Designar" else []
                        if prof not in ultimo_horario["professores"]:
                            ultimo_horario["professores"].append(prof)
                            ultimo_horario["docente"] = ", ".join(ultimo_horario["professores"])

        docentes_lista = sorted(list(docentes_set)) if docentes_set else ["A Designar"]

        # Período: Semestral ou Anual
        periodo = "Semestral"
        if inicio and fim:
            try:
                from datetime import datetime
                d_ini = datetime.strptime(inicio, "%d/%m/%Y")
                d_fim = datetime.strptime(fim, "%d/%m/%Y")
                if (d_fim - d_ini).days > 185:
                    periodo = "Anual"
            except Exception:
                pass

        # Alunos Matriculados (soma apenas das categorias com colspan=2, ignora linhas filhas)
        matriculados = None
        m_matr = re.search(r'Matriculado', chunk, re.I)
        if m_matr:
            trecho_tabela = re.split(r'</table>', chunk[m_matr.start():], flags=re.I)[0]
            linhas_tr = re.findall(r'<tr[^>]*>([\s\S]*?)</tr>', trecho_tabela, re.I)
            total_matriculados = 0
            teve_categoria = False
            for tr in linhas_tr:
                tds = re.findall(r'<td([^>]*)>([\s\S]*?)</td>', tr, re.I)
                if len(tds) == 5:
                    attrs_td0 = tds[0][0]
                    if re.search(r'colspan\s*=\s*[\'"]?\s*2\s*[\'"]?', attrs_td0, re.I):
                        cat_texto = decodificar_entidades(re.sub(r'<[^>]+>', ' ', tds[0][1])).strip()
                        if cat_texto and cat_texto.lower() not in ("vagas", "matriculados", "inscritos", "pendentes"):
                            teve_categoria = True
                            val_raw = decodificar_entidades(re.sub(r'<[^>]+>', ' ', tds[4][1])).strip()
                            val_limpo = re.sub(r'[^\d]', '', val_raw)
                            if val_limpo:
                                total_matriculados += int(val_limpo)
            if teve_categoria:
                matriculados = total_matriculados

        turmas[num_turma] = {
            "codigoTurma": cod_turma,
            "numero": num_turma,
            "tipo": tipo_turma,
            "periodo": periodo,
            "inicio": inicio,
            "fim": fim,
            "docentes": docentes_lista,
            "horarios": horarios,
            "observacoes": observacoes,
            "matriculados": matriculados
        }

    return {
        "codigo": codigo,
        "nome": nome_disciplina,
        "semOferecimento": len(turmas) == 0,
        "turmas": turmas
    }


class TestJupiterParser(unittest.TestCase):
    """Testes unitários e de robustez para o parser do Jupiterweb."""

    @classmethod
    def setUpClass(cls):
        with open(os.path.join(DIR_FIXTURES, "jupiter_sma0356.html"), "rb") as f:
            cls.html_sma0356 = f.read().decode("iso-8859-1")

        with open(os.path.join(DIR_FIXTURES, "jupiter_7600006.html"), "rb") as f:
            cls.html_7600006 = f.read().decode("iso-8859-1")

        with open(os.path.join(DIR_FIXTURES, "jupiter_sem_oferecimento.html"), "rb") as f:
            cls.html_sem_oferecimento = f.read().decode("iso-8859-1")

        with open(os.path.join(DIR_FIXTURES, "jupiter_stt0410.html"), "rb") as f:
            cls.html_stt0410 = f.read().decode("iso-8859-1")

    def test_parse_disciplina_multiplos_docentes_stt0410(self):
        """Valida extração de múltiplos docentes na mesma aula e remoção de (R) (caso real STT0410 T2)."""
        dados = parsear_html_jupiterweb("STT0410", self.html_stt0410)

        self.assertEqual(dados["codigo"], "STT0410")
        self.assertEqual(dados["nome"], "Geomática II")
        self.assertFalse(dados["semOferecimento"])
        self.assertIn("02", dados["turmas"])

        t2 = dados["turmas"]["02"]
        # Deve conter ambos os docentes
        self.assertIn("Paulo Cesar Lima Segantine", t2["docentes"])
        self.assertIn("Lucas Brandão Monteiro de Assis", t2["docentes"])
        self.assertEqual(len(t2["docentes"]), 2)

        # Não deve conter prefixo (R)
        for doc in t2["docentes"]:
            self.assertFalse(doc.startswith("(R)"))

        # Horário deve listar ambos os professores
        h = t2["horarios"][0]
        self.assertEqual(h["dia"], "qua")
        self.assertEqual(h["inicio"], "14:20")
        self.assertEqual(h["fim"], "17:00")
        self.assertIn("Lucas Brandão Monteiro de Assis", h.get("professores", []))
        self.assertIn("Paulo Cesar Lima Segantine", h.get("professores", []))

        # Matriculados STT0410
        self.assertEqual(dados["turmas"]["01"]["matriculados"], 33)
        self.assertEqual(t2["matriculados"], 34)

    def test_parse_disciplina_sma0356(self):
        """Valida extração completa da disciplina SMA0356 (9 turmas)."""
        dados = parsear_html_jupiterweb("SMA0356", self.html_sma0356)

        self.assertEqual(dados["codigo"], "SMA0356")
        self.assertEqual(dados["nome"], "Cálculo IV")
        self.assertFalse(dados["semOferecimento"])
        self.assertEqual(len(dados["turmas"]), 9)

        # Valida Turma 01
        self.assertIn("01", dados["turmas"])
        t1 = dados["turmas"]["01"]
        self.assertEqual(t1["codigoTurma"], "2026201")
        self.assertEqual(t1["inicio"], "03/08/2026")
        self.assertEqual(t1["fim"], "12/12/2026")
        self.assertEqual(t1["tipo"], "Teórica")
        self.assertIn("Ana Claudia Nabarro", t1["docentes"])
        self.assertTrue(len(t1["horarios"]) >= 2)
        self.assertNotIn("vagas", t1)
        # Matriculados: Obrigatória (8) + Optativa Eletiva (5) + Optativa Livre (2) = 15
        self.assertEqual(t1["matriculados"], 15)

        # Turma 02: Obrigatória (59) + Optativa Eletiva (8) + Optativa Livre (2) = 69
        self.assertEqual(dados["turmas"]["02"]["matriculados"], 69)

        # Turma 07: Obrigatória (30) + Alunos Especiais (1 com hífen em pendentes) = 31
        self.assertEqual(dados["turmas"]["07"]["matriculados"], 31)

    def test_parse_disciplina_7600006_numerica(self):
        """Valida extração de código puramente numérico 7600006 (8 turmas)."""
        dados = parsear_html_jupiterweb("7600006", self.html_7600006)

        self.assertEqual(dados["codigo"], "7600006")
        self.assertEqual(dados["nome"], "Física II")
        self.assertFalse(dados["semOferecimento"])
        self.assertEqual(len(dados["turmas"]), 8)
        self.assertIn("01", dados["turmas"])

        # Turma 04: Obrigatória (108) + Optativa Livre (1) = 109
        self.assertEqual(dados["turmas"]["04"]["matriculados"], 109)
        # Turma 06: Obrigatória (39) + Alunos Especiais (1) = 40
        self.assertEqual(dados["turmas"]["06"]["matriculados"], 40)

    def test_parse_matriculados_exemplo_sintetico(self):
        """Valida o caso de teste exato do usuário: categorias somadas e linhas subordinadas ignoradas."""
        html_sintetico = """
        <b>SMA0356 - Cálculo IV</b>
        Código da Turma: <td nowrap>2026201</td>
        <table border="0">
          <tr bgcolor="#658CCF">
            <td colspan="2">&nbsp;</td>
            <td>Vagas</td><td>Inscritos</td><td>Pendentes</td><td>Matriculados</td>
          </tr>
          <tr>
            <td colspan="2">Obrigatória</td><td>70</td><td>65</td><td>0</td><td>65</td>
          </tr>
          <tr>
            <td width="28">&nbsp;&nbsp;&nbsp;</td><td>EESC - Engenharia Mecânica</td>
            <td>60</td><td>60</td><td>0</td><td>60</td>
          </tr>
          <tr>
            <td colspan="2">Optativa Livre</td><td>2</td><td>1</td><td>0</td><td>1</td>
          </tr>
          <tr>
            <td width="28">&nbsp;&nbsp;&nbsp;</td><td>Qualquer Unidade da USP</td>
            <td>2</td><td>0</td><td>0</td><td>0</td>
          </tr>
          <tr>
            <td colspan="2">Extracurricular</td><td>1</td><td>1</td><td>0</td><td>1</td>
          </tr>
        </table>
        """
        dados = parsear_html_jupiterweb("SMA0356", html_sintetico)
        self.assertIn("01", dados["turmas"])
        # Obrigatória (65) + Optativa Livre (1) + Extracurricular (1) = 67
        self.assertEqual(dados["turmas"]["01"]["matriculados"], 67)

    def test_parse_matriculados_zero_e_ausente(self):
        """Valida distinção entre turma com 0 alunos e HTML sem tabela de matriculados."""
        # 1. Turma com tabela e 0 matriculados
        html_zero = """
        <b>MAT0100 - Introdução</b>
        Código da Turma: <td>2026101</td>
        <table>
          <tr><td colspan="2">&nbsp;</td><td>Vagas</td><td>Inscritos</td><td>Pendentes</td><td>Matriculados</td></tr>
          <tr><td colspan="2">Obrigatória</td><td>30</td><td>0</td><td>0</td><td>0</td></tr>
        </table>
        """
        dados_zero = parsear_html_jupiterweb("MAT0100", html_zero)
        self.assertEqual(dados_zero["turmas"]["01"]["matriculados"], 0)

        # 2. Turma sem tabela de matriculados
        html_sem_tab = """
        <b>MAT0100 - Introdução</b>
        Código da Turma: <td>2026102</td>
        <div>Sem dados de vagas</div>
        """
        dados_sem_tab = parsear_html_jupiterweb("MAT0100", html_sem_tab)
        self.assertIsNone(dados_sem_tab["turmas"]["02"]["matriculados"])

    def test_parse_sem_oferecimento(self):
        """Valida detecção de página sem oferecimento ativo (cache negativo)."""
        dados = parsear_html_jupiterweb("SMA0000", self.html_sem_oferecimento)

        self.assertTrue(dados["semOferecimento"])
        self.assertEqual(len(dados["turmas"]), 0)

    def test_parse_periodo_semestral(self):
        """Valida extração correta de período Semestral."""
        dados = parsear_html_jupiterweb("SMA0356", self.html_sma0356)
        self.assertIn("01", dados["turmas"])
        self.assertEqual(dados["turmas"]["01"]["periodo"], "Semestral")

    def test_parse_fuzzing_estabilidade(self):
        """Fuzzing com 200 documentos HTML aleatórios e corrompidos garantindo 0 exceções."""
        for _ in range(200):
            tamanho = random.randint(10, 5000)
            ruido = "".join(random.choices(string.printable, k=tamanho))
            # Pode misturar com fragmentos válidos
            if random.random() > 0.5:
                ruido += "Código da Turma: 2026201 <tr><td colspan=2>Obrigatória</td><td>30</td></tr>"

            res = parsear_html_jupiterweb("TESTE99", ruido)
            self.assertIsInstance(res, dict)
            self.assertIn("semOferecimento", res)
            self.assertIn("turmas", res)


if __name__ == "__main__":
    unittest.main()
