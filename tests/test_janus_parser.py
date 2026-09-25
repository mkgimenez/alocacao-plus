#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários e Fuzzing: Parser HTML do Janus (Pós-Graduação USP)
Valida a extração de metadados, oferecimentos, turmas, docentes, horários e locais
a partir de fixtures reais e documentos sintéticos.
"""

from datetime import datetime
import html as html_lib
import os
import random
import re
import string
import unittest

DIR_FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def decodificar_entidades(texto):
    """Decodifica entidades HTML nomeadas e numéricas e normaliza espaços e caracteres tipográficos."""
    if not texto:
        return ""
    texto = html_lib.unescape(texto)
    # Trata bytes ou caracteres tipográficos Windows-1252 / Unicode comuns
    texto = texto.replace("\ufffd", "").replace("&nbsp;", " ").replace("\xa0", " ")
    texto = texto.replace("\u0096", "–")  # en-dash Windows-1252 (0x96)
    return " ".join(texto.split())


def parsear_html_janus_disciplina(codigo, html):
    """
    Parser da Etapa 1: Página DisciplinaAux.
    Extrai nome da disciplina, detecta se há oferecimento ativo e coleta IDs de oferecimento (ofe).
    """
    if not html or not isinstance(html, str):
        return {
            "codigo": codigo,
            "nome": "",
            "semOferecimento": True,
            "oferecimentos": []
        }

    # 1. Detecção de disciplina sem oferecimento ativo
    if re.search(r'N(?:ã|a|&atilde;|&#227;)o\s+existem\s+oferecimentos', html, re.I):
        return {
            "codigo": codigo,
            "nome": "",
            "semOferecimento": True,
            "oferecimentos": []
        }

    # 2. Extração do Nome da Disciplina (ancorado na linha contendo o código)
    nome_disciplina = ""
    padrao_com_cod = rf'{re.escape(codigo)}[\s\S]*?<td[^>]*width=["\']?67%["\']?[^>]*>[\s\S]*?<div[^>]*>[\s\S]*?<font[^>]*>([\s\S]*?)</font>'
    m_nome = re.search(padrao_com_cod, html, re.I)
    if m_nome:
        nome_disciplina = decodificar_entidades(re.sub(r'<[^>]+>', ' ', m_nome.group(1)))
    else:
        # Fallback 1: Busca em coluna width="67%" descartando a palavra "Nome"
        m_nomes_todos = re.findall(r'<td[^>]*width=["\']?67%["\']?[^>]*>[\s\S]*?<div[^>]*>[\s\S]*?<font[^>]*>([\s\S]*?)</font>', html, re.I)
        for cand in m_nomes_todos:
            cand_limpo = decodificar_entidades(re.sub(r'<[^>]+>', ' ', cand))
            if cand_limpo and cand_limpo.lower() != "nome":
                nome_disciplina = cand_limpo
                break

        # Fallback 2: Busca por alinhamento à esquerda descartando "Nome"
        if not nome_disciplina:
            m_left = re.findall(r'<td[^>]*align=["\']?left["\']?[^>]*>[\s\S]*?<div[^>]*>[\s\S]*?<font[^>]*>([\s\S]*?)</font>', html, re.I)
            for cand in m_left:
                cand_limpo = decodificar_entidades(re.sub(r'<[^>]+>', ' ', cand))
                if cand_limpo and cand_limpo.lower() != "nome":
                    nome_disciplina = cand_limpo
                    break

    # 3. Coleta de IDs de oferecimento (publico/turma/<codigo>/<ofe>)
    oferecimentos = []
    padrao_link = r'publico/turma/[A-Za-z0-9]+/(\d+)'
    matches_ofe = re.findall(padrao_link, html, re.I)
    for m in matches_ofe:
        num = str(int(m))  # remove zeros à esquerda
        if num not in oferecimentos:
            oferecimentos.append(num)

    if not oferecimentos:
        return {
            "codigo": codigo,
            "nome": nome_disciplina,
            "semOferecimento": True,
            "oferecimentos": []
        }

    return {
        "codigo": codigo,
        "nome": nome_disciplina,
        "semOferecimento": False,
        "oferecimentos": oferecimentos
    }


def parsear_html_janus_turma(codigo, html, num_turma="1"):
    """
    Parser da Etapa 2: Página TurmaDet.
    Extrai datas, modalidade, docentes ministrantes, horários e locais ancorando em classes .intl_*.
    """
    if not html or not isinstance(html, str):
        return None

    num_can = str(int(num_turma)).zfill(2) if str(num_turma).isdigit() else str(num_turma)
    codigo_turma = f"{codigo}-{num_turma}"

    # 1. Datas e Cálculo de Período
    inicio = ""
    fim = ""
    m_ini = re.search(r"class=['\"][^'\"]*intl_dataInicial[^'\"]*['\"][^>]*>[\s\S]*?(\d{2}/\d{2}/\d{4})", html, re.I)
    if m_ini:
        inicio = m_ini.group(1).strip()

    m_fim = re.search(r"class=['\"][^'\"]*intl_dataFinal[^'\"]*['\"][^>]*>[\s\S]*?(\d{2}/\d{2}/\d{4})", html, re.I)
    if m_fim:
        fim = m_fim.group(1).strip()

    periodo = "Semestral"
    if inicio and fim:
        try:
            d_ini = datetime.strptime(inicio, "%d/%m/%Y")
            d_fim = datetime.strptime(fim, "%d/%m/%Y")
            dias = (d_fim - d_ini).days
            if dias > 185:
                periodo = "Anual"
            else:
                periodo = "Semestral"
        except Exception:
            periodo = "Semestral"

    # 2. Modalidade / Forma de Oferecimento (.intl_formaOferecimento)
    tipo_turma = "Presencial"
    m_forma = re.search(r"class=['\"][^'\"]*intl_formaOferecimento[^'\"]*['\"][^>]*>[\s\S]*?<font[^>]*>(?:<span[^>]*>)?\s*([^\s<]+)", html, re.I)
    if m_forma:
        forma_raw = decodificar_entidades(m_forma.group(1))
        if "presenc" in forma_raw.lower():
            tipo_turma = "Presencial"
        elif "remot" in forma_raw.lower() or "dist" in forma_raw.lower() or "ead" in forma_raw.lower():
            tipo_turma = "Remota"
        elif "hibrid" in forma_raw.lower():
            tipo_turma = "Híbrida"
        else:
            tipo_turma = forma_raw

    # 3. Docentes Ministrantes (.intl_docenteMinistrante)
    docentes = []
    m_doc_bloco = re.search(r"class=['\"][^'\"]*intl_docenteMinistrante[^'\"]*['\"][\s\S]*?</table>", html, re.I)
    if m_doc_bloco:
        bloco_html = m_doc_bloco.group(0)
        linhas_doc = re.findall(r"<td[^>]*nowrap[^>]*>[\s\S]*?<font[^>]*>(?:<span[^>]*>)?([\s\S]*?)(?:</span>)?</font>", bloco_html, re.I)
        for d_raw in linhas_doc:
            doc_limpo = decodificar_entidades(re.sub(r'<[^>]+>', ' ', d_raw))
            if doc_limpo and doc_limpo != "-" and doc_limpo.lower() != "a designar" and doc_limpo not in docentes:
                docentes.append(doc_limpo)

    # 4. Tabela de Horários e Locais (.intl_horario / .intl_local)
    horarios = []
    locais_encontrados = set()
    m_hor_bloco = re.search(r"class=['\"][^'\"]*(?:intl_horario|intl_local)[^'\"]*['\"][\s\S]*?<table[^>]*>([\s\S]*?)</table>", html, re.I)
    if m_hor_bloco:
        linhas_tr = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", m_hor_bloco.group(1), re.I)
        for tr in linhas_tr:
            tds = re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr, re.I)
            if len(tds) >= 3:
                dia = decodificar_entidades(re.sub(r'<[^>]+>', ' ', tds[0]))
                hora_str = decodificar_entidades(re.sub(r'<[^>]+>', ' ', tds[1]))
                local = decodificar_entidades(re.sub(r'<[^>]+>', ' ', tds[2]))

                inicio_hora = ""
                fim_hora = ""
                if "-" in hora_str:
                    partes_hora = [h.strip() for h in hora_str.split("-")]
                    inicio_hora = partes_hora[0]
                    fim_hora = partes_hora[1] if len(partes_hora) > 1 else ""
                elif "às" in hora_str or "as" in hora_str:
                    partes_hora = re.split(r'\s+às\s+|\s+as\s+', hora_str, flags=re.I)
                    inicio_hora = partes_hora[0].strip()
                    fim_hora = partes_hora[1].strip() if len(partes_hora) > 1 else ""
                else:
                    inicio_hora = hora_str

                if local:
                    locais_encontrados.add(local)

                horarios.append({
                    "dia": dia,
                    "inicio": inicio_hora,
                    "fim": fim_hora,
                    "docente": docentes[0] if docentes else "A Designar",
                    "professores": list(docentes) if docentes else [],
                    "local": local
                })

    # 5. Idioma ministrado (.intl_idiomaMinistrado)
    idioma = "Português"
    m_idioma = re.search(r"intl_idiomaMinistrado[\s\S]*?<span[^>]*class=['\"]txt_arial_10pt_black['\"][^>]*>([^<]+)</span>", html, re.I)
    if m_idioma:
        raw_id = decodificar_entidades(m_idioma.group(1)).strip()
        if re.search(r"ingl|engl", raw_id, re.I):
            idioma = "Inglês"
        elif re.search(r"portug", raw_id, re.I):
            idioma = "Português"
        elif re.search(r"espanh|span", raw_id, re.I):
            idioma = "Espanhol"
        elif re.search(r"franc", raw_id, re.I):
            idioma = "Francês"
        elif raw_id:
            idioma = raw_id

    # 6. Número de Vagas (ancorado em intl_numeroVagas ou Número de vagas)
    vagas = None
    m_vagas_bloco = re.search(r"(?:intl_numeroVagas|N[uú]mero\s+de\s+[Vv]agas)[\s\S]*?<table[^>]*>([\s\S]*?)</table>", html, re.I)
    if m_vagas_bloco:
        tabela_conteudo = m_vagas_bloco.group(1)
        linhas_tr = re.findall(r"<tr[^>]*>([\s\S]*?)</tr>", tabela_conteudo, re.I)
        if linhas_tr:
            # Analisa cabeçalho procurando coluna 'Total'
            idx_total = -1
            tds_cab = re.findall(r"<td[^>]*>([\s\S]*?)</td>", linhas_tr[0], re.I)
            for idx, c in enumerate(tds_cab):
                texto_cab = decodificar_entidades(re.sub(r"<[^>]+>", " ", c)).strip()
                if re.search(r"total", texto_cab, re.I) or "intl_total" in c.lower():
                    idx_total = idx
                    break

            if idx_total == -1 and tds_cab:
                idx_total = len(tds_cab) - 1

            for tr in linhas_tr[1:]:
                tds_dados = re.findall(r"<td[^>]*>([\s\S]*?)</td>", tr, re.I)
                if not tds_dados:
                    continue
                if 0 <= idx_total < len(tds_dados):
                    val_raw = decodificar_entidades(re.sub(r"<[^>]+>", " ", tds_dados[idx_total])).strip()
                    val_limpo = re.sub(r"[^\d]", "", val_raw)
                    if val_limpo:
                        vagas = int(val_limpo)
                        break
                if vagas is None:
                    for td in reversed(tds_dados):
                        val_raw = decodificar_entidades(re.sub(r"<[^>]+>", " ", td)).strip()
                        val_limpo = re.sub(r"[^\d]", "", val_raw)
                        if val_limpo:
                            vagas = int(val_limpo)
                            break
                    if vagas is not None:
                        break

    # Observações
    obs = ""
    if locais_encontrados:
        obs = f"Local: {', '.join(sorted(locais_encontrados))}"

    return {
        "codigoTurma": codigo_turma,
        "numero": num_can,
        "ofe": str(int(num_turma)) if str(num_turma).isdigit() else str(num_turma),
        "tipo": tipo_turma,
        "periodo": periodo,
        "inicio": inicio,
        "fim": fim,
        "docentes": docentes,
        "horarios": horarios,
        "idioma": idioma,
        "observacoes": obs,
        "vagas": vagas
    }


def montar_objeto_janus(codigo, dados_disciplina, turmas_det_dict):
    """Combina resultado da Etapa 1 e Etapa 2 no schema canônico interoperável."""
    if not dados_disciplina or dados_disciplina.get("semOferecimento"):
        return {
            "codigo": codigo,
            "nome": dados_disciplina.get("nome", "") if dados_disciplina else "",
            "sistema": "janus",
            "semOferecimento": True,
            "turmas": {}
        }

    turmas = {}
    for num_ofe, t_det in turmas_det_dict.items():
        if t_det:
            chave_canonica = t_det.get("numero", str(num_ofe).zfill(2))
            turmas[chave_canonica] = t_det

    return {
        "codigo": codigo,
        "nome": dados_disciplina.get("nome", ""),
        "sistema": "janus",
        "semOferecimento": len(turmas) == 0,
        "turmas": turmas
    }


class TestJanusParser(unittest.TestCase):
    """Validação contra fixtures reais e testes sintéticos."""

    def carregar_fixture(self, nome_arquivo):
        caminho = os.path.join(DIR_FIXTURES, nome_arquivo)
        with open(caminho, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def test_disciplina_sep5864_completa(self):
        """Valida parsing completo de SEP5864 (disciplina e TurmaDet)."""
        html_disc = self.carregar_fixture("janus_SEP5864_disciplina.html")
        info_disc = parsear_html_janus_disciplina("SEP5864", html_disc)

        self.assertFalse(info_disc["semOferecimento"])
        self.assertEqual(info_disc["codigo"], "SEP5864")
        self.assertIn("Design Science Research", info_disc["nome"])
        self.assertEqual(info_disc["oferecimentos"], ["1"])

        html_turma = self.carregar_fixture("janus_SEP5864_TurmaDet.html")
        info_turma = parsear_html_janus_turma("SEP5864", html_turma, "1")

        self.assertIsNotNone(info_turma)
        self.assertEqual(info_turma["numero"], "01")
        self.assertEqual(info_turma["codigoTurma"], "SEP5864-1")
        self.assertEqual(info_turma["tipo"], "Presencial")
        self.assertEqual(info_turma["periodo"], "Semestral")
        self.assertEqual(info_turma["inicio"], "03/08/2026")
        self.assertEqual(info_turma["fim"], "23/08/2026")
        self.assertEqual(info_turma["docentes"], ["Fabio Muller Guerrini"])
        self.assertEqual(len(info_turma["horarios"]), 3)
        self.assertEqual(info_turma["horarios"][0]["dia"], "Segunda")
        self.assertEqual(info_turma["horarios"][0]["inicio"], "08:00")
        self.assertEqual(info_turma["horarios"][0]["fim"], "11:00")
        self.assertEqual(info_turma["horarios"][0]["local"], "Engenharia de Produção")
        self.assertEqual(info_turma["idioma"], "Português")
        self.assertEqual(info_turma["observacoes"], "Local: Engenharia de Produção")
        self.assertEqual(info_turma["vagas"], 15)

        # Objeto unificado
        obj_completo = montar_objeto_janus("SEP5864", info_disc, {"1": info_turma})
        self.assertEqual(obj_completo["sistema"], "janus")
        self.assertIn("01", obj_completo["turmas"])
        self.assertNotIn("1", obj_completo["turmas"])  # Chaves canônicas com 2 dígitos
        self.assertEqual(obj_completo["turmas"]["01"]["vagas"], 15)

    def test_disciplina_shs5991_com_travessao(self):
        """Valida SHS5991 com travessão tipográfico e local 'sala de aula'."""
        html_disc = self.carregar_fixture("janus_SHS5991_disciplina.html")
        info_disc = parsear_html_janus_disciplina("SHS5991", html_disc)

        self.assertFalse(info_disc["semOferecimento"])
        self.assertIn("Sistemas Biológicos de Tratamento", info_disc["nome"])
        self.assertIn("–", info_disc["nome"])  # en-dash preservado
        self.assertEqual(info_disc["oferecimentos"], ["1"])

        html_turma = self.carregar_fixture("janus_SHS5991_TurmaDet.html")
        info_turma = parsear_html_janus_turma("SHS5991", html_turma, "1")

        self.assertEqual(info_turma["numero"], "01")
        self.assertEqual(info_turma["periodo"], "Semestral")
        self.assertEqual(info_turma["docentes"], ["Marcia Helena Rissato Zamariolli Damianovic"])
        self.assertEqual(len(info_turma["horarios"]), 1)
        self.assertEqual(info_turma["horarios"][0]["dia"], "Quinta")
        self.assertEqual(info_turma["horarios"][0]["inicio"], "08:30")
        self.assertEqual(info_turma["horarios"][0]["fim"], "12:30")
        self.assertEqual(info_turma["horarios"][0]["local"], "sala de aula")
        self.assertEqual(info_turma["vagas"], 25)

    def test_disciplina_sem5900_sem_oferecimento(self):
        """Valida disciplina sem oferecimento no semestre (SEM5900)."""
        html_disc = self.carregar_fixture("janus_SEM5900_disciplina.html")
        info_disc = parsear_html_janus_disciplina("SEM5900", html_disc)

        self.assertTrue(info_disc["semOferecimento"])
        self.assertEqual(info_disc["oferecimentos"], [])

        obj_completo = montar_objeto_janus("SEM5900", info_disc, {})
        self.assertTrue(obj_completo["semOferecimento"])
        self.assertEqual(obj_completo["turmas"], {})

    def test_disciplina_shs5934_turma_4_ingles(self):
        """Valida que a turma 4 de SHS5934 é extraída com idioma 'Inglês'."""
        html_turma = self.carregar_fixture("janus_SHS5934_TurmaDet_4.html")
        info_turma = parsear_html_janus_turma("SHS5934", html_turma, "4")
        self.assertIsNotNone(info_turma)
        self.assertEqual(info_turma["numero"], "04")
        self.assertEqual(info_turma["codigoTurma"], "SHS5934-4")
        self.assertEqual(info_turma["idioma"], "Inglês")
        self.assertEqual(info_turma["vagas"], 25)

    def test_parse_vagas_exemplo_sintetico(self):
        """Valida o exemplo exato do usuário: Regulares (20) + Especiais (5) + Total (25) = 25 vagas."""
        html_sintetico = """
        <span class='label intl_numeroVagas'></span>:
        <table>
          <tr>
            <td><span class='label intl_alunosRegulares'></span></td>
            <td><span class='label intl_alunosEspeciais'></span></td>
            <td>Total</td>
          </tr>
          <tr>
            <td>20</td>
            <td>5</td>
            <td>25</td>
          </tr>
        </table>
        """
        info = parsear_html_janus_turma("TESTE01", html_sintetico, "1")
        self.assertIsNotNone(info)
        self.assertEqual(info["vagas"], 25)

    def test_parse_vagas_sem_cabecalho_total_e_zero(self):
        """Valida fallback quando cabeçalho não tem Total, turma com 0 vagas e HTML sem tabela."""
        # 1. Fallback quando o cabeçalho não tem a palavra 'Total'
        html_sem_texto = """
        <span class='label intl_numeroVagas'></span>
        <table>
          <tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
          <tr><td>10</td><td>5</td><td>15</td></tr>
        </table>
        """
        info_fallback = parsear_html_janus_turma("TESTE02", html_sem_texto, "1")
        self.assertEqual(info_fallback["vagas"], 15)

        # 2. Turma com 0 vagas
        html_zero = """
        Número de vagas:
        <table>
          <tr><td>Total</td></tr>
          <tr><td>0</td></tr>
        </table>
        """
        info_zero = parsear_html_janus_turma("TESTE03", html_zero, "1")
        self.assertEqual(info_zero["vagas"], 0)

        # 3. Sem tabela de vagas
        html_sem_vagas = "<div>Turma sem número de vagas</div>"
        info_sem = parsear_html_janus_turma("TESTE04", html_sem_vagas, "1")
        self.assertIsNone(info_sem["vagas"])

    def test_property_fuzzing_estabilidade(self):
        """Fuzzing com 200 documentos aleatórios e corrompidos garantindo 0 exceções."""
        caracteres = string.ascii_letters + string.digits + " <>=\"'/:;-_[]().,\n\r\t"
        for _ in range(200):
            tam = random.randint(0, 300)
            html_sintetico = "".join(random.choice(caracteres) for _ in range(tam))

            # Parser de disciplina
            res1 = parsear_html_janus_disciplina("SEP9999", html_sintetico)
            self.assertIsInstance(res1, dict)
            self.assertIn("semOferecimento", res1)

            # Parser de turma
            res2 = parsear_html_janus_turma("SEP9999", html_sintetico, "1")
            if res2 is not None:
                self.assertIsInstance(res2, dict)
                self.assertIn("numero", res2)


if __name__ == "__main__":
    unittest.main()
