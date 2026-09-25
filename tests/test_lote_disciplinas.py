#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários: Despachante Heterogêneo obterLoteDisciplinas
Valida classificação de códigos, pipeline de 2 etapas do Janus,
caching multinível e tolerância a falhas em lotes mistos.
"""

import re
import unittest
from tests.test_janus_parser import parsear_html_janus_disciplina, parsear_html_janus_turma, montar_objeto_janus
from tests.test_jupiter_parser import parsear_html_jupiterweb


class SimuladorCacheService:
    """Mock em memória do ScriptCache do Google Apps Script."""

    def __init__(self):
        self.armazenamento = {}

    def get(self, key):
        return self.armazenamento.get(key)

    def put(self, key, value, ttl=21600):
        self.armazenamento[key] = str(value)

    def remove(self, key):
        self.armazenamento.pop(key, None)

    def removeAll(self, keys):
        for k in keys:
            self.remove(k)


def obter_lote_disciplinas_simulado(lista_codigos, cache, provedor_http):
    """
    Espelho do algoritmo de obterLoteDisciplinas do Apps Script.
    provedor_http(url) retorna (status_code, body_text).
    """
    if not lista_codigos or not isinstance(lista_codigos, list):
        return {"sucesso": False, "msg": "Parâmetro lista_codigos inválido."}

    regex_grad = re.compile(r'^([A-Za-z]{3}0\d{3}|\d{7})$')
    regex_pos = re.compile(r'^[A-Za-z]{3}[1-9]\d{3}$')

    codigos_validos = []
    vistos = set()
    for c in lista_codigos:
        cod = str(c).strip().upper()
        if (regex_grad.match(cod) or regex_pos.match(cod)) and cod not in vistos:
            vistos.add(cod)
            codigos_validos.append(cod)

    codigos_validos = codigos_validos[:10]
    if not codigos_validos:
        return {"sucesso": True, "dados": {}}

    PREFIXO_JUPITER = "JUP_V19_"
    PREFIXO_JANUS = "JAN_V3_"
    resultado = {}
    pendentes_grad = []
    pendentes_pos = []

    # 1. Consulta Cache
    for cod in codigos_validos:
        eh_pos = bool(regex_pos.match(cod))
        cache_key = (PREFIXO_JANUS if eh_pos else PREFIXO_JUPITER) + cod
        cached = cache.get(cache_key)
        if cached:
            import json
            try:
                resultado[cod] = json.loads(cached)
            except Exception:
                if eh_pos:
                    pendentes_pos.append(cod)
                else:
                    pendentes_grad.append(cod)
        else:
            if eh_pos:
                pendentes_pos.append(cod)
            else:
                pendentes_grad.append(cod)

    # 2. Pendências de Graduação (1 Etapa)
    import json
    for cod in pendentes_grad:
        url = f"https://uspdigital.usp.br/jupiterweb/obterTurma?sgldis={cod}"
        status, html = provedor_http(url)
        cache_key = PREFIXO_JUPITER + cod
        if status == 200:
            parsed = parsear_html_jupiterweb(cod, html)
            resultado[cod] = parsed
            cache.put(cache_key, json.dumps(parsed), 21600)
        else:
            obj_err = {"codigo": cod, "nome": "", "semOferecimento": True, "erro": True}
            resultado[cod] = obj_err
            cache.put(cache_key, json.dumps(obj_err), 3600)

    # 3. Pendências de Pós-Graduação (2 Etapas Diretas)
    if pendentes_pos:
        oferecimentos_para_buscar = []
        for cod in pendentes_pos:
            url = f"https://uspdigital.usp.br/janus/DisciplinaAux?tipo=T&sgldis={cod}"
            status, html = provedor_http(url)
            cache_key = PREFIXO_JANUS + cod
            if status == 200:
                parsed_disc = parsear_html_janus_disciplina(cod, html)
                if parsed_disc.get("semOferecimento") or not parsed_disc.get("oferecimentos"):
                    obj_sem = {
                        "codigo": cod,
                        "nome": parsed_disc.get("nome", ""),
                        "sistema": "janus",
                        "semOferecimento": True,
                        "turmas": {}
                    }
                    resultado[cod] = obj_sem
                    cache.put(cache_key, json.dumps(obj_sem), 21600)
                else:
                    for ofe in parsed_disc["oferecimentos"]:
                        oferecimentos_para_buscar.append({
                            "cod": cod,
                            "ofe": ofe,
                            "nome": parsed_disc.get("nome", "")
                        })
            else:
                obj_err = {"codigo": cod, "nome": "", "sistema": "janus", "semOferecimento": True, "erro": True, "turmas": {}}
                resultado[cod] = obj_err
                cache.put(cache_key, json.dumps(obj_err), 3600)

        # Etapa 2: TurmaDet
        if oferecimentos_para_buscar:
            turmas_por_codigo = {}
            for item in oferecimentos_para_buscar:
                cod = item["cod"]
                ofe = item["ofe"]
                if cod not in turmas_por_codigo:
                    turmas_por_codigo[cod] = {"nome": item["nome"], "turmas": {}}

                url_t = f"https://uspdigital.usp.br/janus/TurmaDet?sgldis={cod}&ofe={ofe}&"
                status_t, html_t = provedor_http(url_t)
                if status_t == 200:
                    parsed_turma = parsear_html_janus_turma(cod, html_t, ofe)
                    if parsed_turma:
                        turmas_por_codigo[cod]["turmas"][parsed_turma["numero"]] = parsed_turma

            for cod, info_t in turmas_por_codigo.items():
                cache_key = PREFIXO_JANUS + cod
                t_map = info_t["turmas"]
                obj_janus = {
                    "codigo": cod,
                    "nome": info_t["nome"],
                    "sistema": "janus",
                    "semOferecimento": len(t_map) == 0,
                    "turmas": t_map
                }
                resultado[cod] = obj_janus
                cache.put(cache_key, json.dumps(obj_janus), 21600)

    return {"sucesso": True, "dados": resultado}


class TestLoteDisciplinas(unittest.TestCase):
    """Testes unitários para o despachante de lote com mocks."""

    def setUp(self):
        import os
        dir_fixtures = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
        self.fixtures = {}
        for nome in [
            "janus_SEP5864_disciplina.html", "janus_SEP5864_TurmaDet.html",
            "janus_SHS5991_disciplina.html", "janus_SHS5991_TurmaDet.html",
            "janus_SEM5900_disciplina.html", "jupiter_sma0356.html"
        ]:
            p = os.path.join(dir_fixtures, nome)
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    self.fixtures[nome] = f.read()

        self.cache = SimuladorCacheService()

    def provedor_mock(self, url):
        if "jupiterweb/obterTurma?sgldis=SMA0356" in url:
            return 200, self.fixtures.get("jupiter_sma0356.html", "")
        if "janus/DisciplinaAux?tipo=T&sgldis=SEP5864" in url:
            return 200, self.fixtures.get("janus_SEP5864_disciplina.html", "")
        if "janus/TurmaDet?sgldis=SEP5864&ofe=1" in url:
            return 200, self.fixtures.get("janus_SEP5864_TurmaDet.html", "")
        if "janus/DisciplinaAux?tipo=T&sgldis=SEM5900" in url:
            return 200, self.fixtures.get("janus_SEM5900_disciplina.html", "")
        if "ERRO" in url:
            return 500, "Internal Server Error"
        return 404, "Not Found"

    def test_lote_misto_graduacao_e_pos(self):
        """Valida lote contendo disciplina de graduação (SMA0356) e de pós (SEP5864)."""
        res = obter_lote_disciplinas_simulado(["SMA0356", "SEP5864"], self.cache, self.provedor_mock)
        self.assertTrue(res["sucesso"])
        dados = res["dados"]

        self.assertIn("SMA0356", dados)
        self.assertEqual(dados["SMA0356"]["codigo"], "SMA0356")
        self.assertIn("01", dados["SMA0356"]["turmas"])
        self.assertEqual(dados["SMA0356"]["turmas"]["01"]["matriculados"], 15)

        self.assertIn("SEP5864", dados)
        self.assertEqual(dados["SEP5864"]["sistema"], "janus")
        self.assertIn("01", dados["SEP5864"]["turmas"])
        self.assertEqual(dados["SEP5864"]["turmas"]["01"]["docentes"], ["Fabio Muller Guerrini"])
        self.assertEqual(dados["SEP5864"]["turmas"]["01"]["vagas"], 15)

        # Segunda chamada deve atingir o cache preservando matriculados e vagas
        res_cache = obter_lote_disciplinas_simulado(["SMA0356", "SEP5864"], self.cache, lambda u: (500, "Nao deve chamar"))
        self.assertTrue(res_cache["sucesso"])
        self.assertIn("SMA0356", res_cache["dados"])
        self.assertEqual(res_cache["dados"]["SMA0356"]["turmas"]["01"]["matriculados"], 15)
        self.assertIn("SEP5864", res_cache["dados"])
        self.assertEqual(res_cache["dados"]["SEP5864"]["turmas"]["01"]["vagas"], 15)

    def test_lote_pos_sem_oferecimento(self):
        """Valida cache negativo de disciplina de pós sem oferecimento (SEM5900)."""
        res = obter_lote_disciplinas_simulado(["SEM5900"], self.cache, self.provedor_mock)
        self.assertTrue(res["sucesso"])
        dados = res["dados"]
        self.assertIn("SEM5900", dados)
        self.assertTrue(dados["SEM5900"]["semOferecimento"])

    def test_resiliencia_a_falha_de_rede(self):
        """Valida que falha HTTP não interrompe o lote e gera entrada de erro."""
        res = obter_lote_disciplinas_simulado(["SEP9999"], self.cache, lambda u: (500, "Erro"))
        self.assertTrue(res["sucesso"])
        self.assertIn("SEP9999", res["dados"])
        self.assertTrue(res["dados"]["SEP9999"]["erro"])


if __name__ == "__main__":
    unittest.main()
