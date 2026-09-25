#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados — Autocomplete Inteligente no Campo de Busca
Valida o catálogo de departamentos, extração canônica de turmas,
indexação estrita baseada exclusivamente na grade atual e motor de sugestões
espelhando a lógica implementada em JavaScript (src/scripts.html).
"""

import unittest
import unicodedata
import re
import random
import string


def normalizar_texto(txt):
    if not txt:
        return ""
    txt_str = str(txt).lower()
    norm = unicodedata.normalize("NFD", txt_str)
    return "".join(c for c in norm if unicodedata.category(c) != "Mn")


def normalizar_nome_docente(nome_raw):
    if not nome_raw:
        return ""
    limpo = re.sub(r'\s*\([^)]*\)', '', str(nome_raw))
    limpo = re.sub(r'^(?:(?:Prof(?:a)?|Dr(?:a)?|Ms|Msc)\.?\s*)+', '', limpo, flags=re.IGNORECASE)
    limpo = re.sub(r'\s+', ' ', limpo).strip()
    return limpo


def extrair_turmas_numericas_da_celula(cel):
    """
    Espelho Python fiel de extrairTurmasNumericasDaCelula (src/scripts.html).
    Extrai números inteiros de turma de cel['turmas'] ou com regex resiliente em cel['t'].
    """
    if not cel:
        return []
    if "_turmasNums" in cel and isinstance(cel["_turmasNums"], list):
        return cel["_turmasNums"]

    nums = []
    if cel.get("turmas") and isinstance(cel["turmas"], list):
        for t in cel["turmas"]:
            try:
                n = int(t)
                if n not in nums:
                    nums.append(n)
            except (ValueError, TypeError):
                pass

    if not nums and cel.get("t"):
        texto = cel["t"]
        # 1. Padrão com 'T' ou 'Turma' explícito (ex: "T01", "T-01", "T 1", "Turma 2", "T01/T02")
        re_t = re.finditer(r'(?:-\s*|/\s*)?(?:T\s*[\-_]?\s*|Turma\s+)(\d{1,2})', texto, flags=re.IGNORECASE)
        for m in re_t:
            n = int(m.group(1))
            if n not in nums:
                nums.append(n)

        # 2. Padrão numérico isolado após hífen/barra para pós-graduação ou disciplinas tronco
        if not nums:
            re_num = re.finditer(r'(?:-\s*|/\s*)(\d{1,2})(?:\s*(?:e|E|/)\s*(\d{1,2}))?(?:\s*$|\s+(?:pv|tv|pós|pos|/))', texto, flags=re.IGNORECASE)
            for m in re_num:
                if m.group(1):
                    n1 = int(m.group(1))
                    if n1 not in nums:
                        nums.append(n1)
                if m.group(2):
                    n2 = int(m.group(2))
                    if n2 not in nums:
                        nums.append(n2)

    cel["_turmasNums"] = nums
    cel["_temTurma"] = len(nums) > 0
    return nums


def extrair_disciplinas_e_turmas_da_grade(grade):
    """
    Espelho Python fiel de extrairDisciplinasETurmasDaGrade (src/scripts.html).
    Retorna (mapa_disciplinas, freq_departamentos).
    """
    mapa = {}
    freq_deptos = {}

    if not grade or not isinstance(grade, list):
        return mapa, freq_deptos

    for linha in grade:
        if not isinstance(linha, list):
            continue
        for cel in linha:
            if not cel or not cel.get("d") or not isinstance(cel["d"], list):
                continue
            turmas_nums = extrair_turmas_numericas_da_celula(cel)
            deptos_vistos_na_celula = set()

            for cod_raw in cel["d"]:
                cod = str(cod_raw).strip().upper()
                if not cod:
                    continue

                sigla_depto = ""
                m_letras = re.match(r'^[A-Za-z]{3}', cod)
                if m_letras:
                    sigla_depto = m_letras.group(0).upper()
                else:
                    m_num = re.match(r'^(\d{3})\d{4}$', cod)
                    if m_num:
                        sigla_depto = m_num.group(1)

                if sigla_depto:
                    deptos_vistos_na_celula.add(sigla_depto)

                if cod not in mapa:
                    mapa[cod] = {"temSemTurma": False, "turmas": set()}

                info = mapa[cod]
                if turmas_nums:
                    for t in turmas_nums:
                        info["turmas"].add(t)
                else:
                    info["temSemTurma"] = True

            for sigla in deptos_vistos_na_celula:
                freq_deptos[sigla] = freq_deptos.get(sigla, 0) + 1

    return mapa, freq_deptos


CATALOGO_DEPARTAMENTOS = [
    {"sigla": "SEM", "nome": "Engenharia Mecânica", "apelido": "Mecânica", "unidade": "EESC", "keywords": ["mecanica", "projetos", "termica", "fluidos", "materiais", "manufatura"]},
    {"sigla": "SEL", "nome": "Engenharia Elétrica e de Computação", "apelido": "Elétrica", "unidade": "EESC", "keywords": ["eletrica", "computacao", "eletronica", "telecomunicacoes", "energia", "sistemas"]},
    {"sigla": "SET", "nome": "Engenharia de Estruturas", "apelido": "Estruturas", "unidade": "EESC", "keywords": ["estruturas", "concreto", "madeira", "metalicas", "resistencia", "estatica"]},
    {"sigla": "SEP", "nome": "Engenharia de Produção", "apelido": "Produção", "unidade": "EESC", "keywords": ["producao", "gestao", "economia", "qualidade", "logistica", "operacoes", "processos"]},
    {"sigla": "SMM", "nome": "Engenharia de Materiais", "apelido": "Materiais", "unidade": "EESC", "keywords": ["materiais", "metalurgia", "polimeros", "ceramicas", "cristalografia", "corrosao"]},
    {"sigla": "SHS", "nome": "Hidráulica e Saneamento", "apelido": "Hidráulica", "unidade": "EESC", "keywords": ["hidraulica", "saneamento", "ambiental", "agua", "esgoto", "recursos hidricos", "hidrologia"]},
    {"sigla": "SGS", "nome": "Geotecnia", "apelido": "Geotecnia", "unidade": "EESC", "keywords": ["geotecnia", "solos", "fundacoes", "mecanica dos solos", "geologia", "aterros"]},
    {"sigla": "SAA", "nome": "Engenharia Aeronáutica", "apelido": "Aeronáutica", "unidade": "EESC", "keywords": ["aeronautica", "aeroespacial", "aerodinamica", "aeronaves", "propulsao", "voo", "aviacao"]},
    {"sigla": "STT", "nome": "Engenharia de Transportes", "apelido": "Transportes", "unidade": "EESC", "keywords": ["transportes", "transito", "ferrovias", "rodovias", "aeroportos", "trafego", "logistica"]},
    {"sigla": "SRB", "nome": "Recursos Hídricos e Saneamento Ambiental", "apelido": "Biotecnologia", "unidade": "EESC", "keywords": ["biotecnologia", "biorrecurso", "saneamento ambiental"]},
    {"sigla": "SMA", "nome": "Matemática", "apelido": "Matemática", "unidade": "ICMC", "keywords": ["matematica", "calculo", "algebra", "geometria", "analise", "equacoes"]},
    {"sigla": "SME", "nome": "Estatística e Matemática Aplicada", "apelido": "Estatística", "unidade": "ICMC", "keywords": ["estatistica", "probabilidade", "analise numerica", "otimizacao", "computacao cientifica"]},
    {"sigla": "SSC", "nome": "Sistemas de Computação", "apelido": "Sistemas Comp.", "unidade": "ICMC", "keywords": ["sistemas", "redes", "arquitetura", "hardware", "computadores", "microprocessadores"]},
    {"sigla": "SCC", "nome": "Ciência da Computação", "apelido": "Ciência Comp.", "unidade": "ICMC", "keywords": ["algoritmos", "programacao", "software", "inteligencia artificial", "banco de dados"]},
    {"sigla": "760", "nome": "Física Geral e Experimental", "apelido": "Física (760)", "unidade": "IFSC", "keywords": ["fisica", "experimental", "mecanica classica", "eletromagnetismo", "otica", "termodinamica"]},
    {"sigla": "SLC", "nome": "Física e Ciências Exatas", "apelido": "Física Exatas", "unidade": "IFSC", "keywords": ["fisica", "ciencias exatas", "laboratorio de fisica"]},
    {"sigla": "FMT", "nome": "Física dos Materiais", "apelido": "Física Materiais", "unidade": "IFSC", "keywords": ["fisica", "materiais", "materia condensada"]},
    {"sigla": "FFI", "nome": "Física e Informática", "apelido": "Física Informática", "unidade": "IFSC", "keywords": ["biofisica", "computacao fisica", "informatica biomedica"]},
    {"sigla": "SQM", "nome": "Química e Química Ambiental", "apelido": "Química", "unidade": "IQSC", "keywords": ["quimica", "quimica geral", "ambiental", "laboratorio quimica"]},
    {"sigla": "QFL", "nome": "Físico-Química", "apelido": "Físico-Química", "unidade": "IQSC", "keywords": ["fisico-quimica", "termodinamica", "cinetica quimica"]},
    {"sigla": "QIQ", "nome": "Química Inorgânica e Analítica", "apelido": "Química Inorg.", "unidade": "IQSC", "keywords": ["inorganica", "analitica", "quimica analitica"]},
    {"sigla": "QOQ", "nome": "Química Orgânica e Biológica", "apelido": "Química Org.", "unidade": "IQSC", "keywords": ["organica", "bioquimica", "sintese"]},
    {"sigla": "IAU", "nome": "Arquitetura e Urbanismo", "apelido": "Arquitetura", "unidade": "IAU", "keywords": ["arquitetura", "urbanismo", "desenho", "projeto", "paisagismo", "historia arquitetura"]}
]

# Grade representativa e canônica para os testes de regressão do sistema
GRADE_CANONICA_TESTES = [
    [
        {"d": ["SEM0500"], "turmas": ["01"], "t": "SEM0500 - T01 tv"},
        {"d": ["SEM0501"], "turmas": ["01"], "t": "SEM0501 - T01"},
        {"d": ["SEM0538"], "turmas": ["01"], "t": "SEM0538 - T01"},
        {"d": ["SEL0353"], "turmas": ["01"], "t": "SEL0353 - T01"},
        {"d": ["SEL0414"], "turmas": ["01"], "t": "SEL0414 - T01"},
        {"d": ["SET0188"], "turmas": ["01"], "t": "SET0188 - T01"},
        {"d": ["SET0198"], "turmas": ["01"], "t": "SET0198 - T01"},
        {"d": ["SET0403"], "turmas": ["01"], "t": "SET0403 - T01"},
        {"d": ["SEP0142"], "turmas": ["01"], "t": "SEP0142 - T01"},
        {"d": ["SMM0193"], "turmas": ["01"], "t": "SMM0193 - T01"},
        {"d": ["SHS0360"], "turmas": ["01"], "t": "SHS0360 - T01"},
        {"d": ["SGS0100"], "turmas": ["01"], "t": "SGS0100 - T01"},
        {"d": ["SAA0100"], "turmas": ["01"], "t": "SAA0100 - T01"},
        {"d": ["STT0410"], "turmas": ["01"], "t": "STT0410 - T01"}
    ],
    [
        {"d": ["SMA0301"], "turmas": ["01"], "t": "SMA0301 - T01"},
        {"d": ["SMA0354"], "turmas": ["01"], "t": "SMA0354 - T01"},
        {"d": ["SMA0355"], "turmas": ["01"], "t": "SMA0355 - T01"},
        {"d": ["SMA0356"], "turmas": ["01"], "t": "SMA0356 - T01"},
        {"d": ["SMA0300"], "turmas": ["01"], "t": "SMA0300 - T01"},
        {"d": ["SMA0305"], "turmas": ["01"], "t": "SMA0305 - T01"},
        {"d": ["SME0340"], "turmas": ["01"], "t": "SME0340 - T01"},
        {"d": ["SME0300"], "turmas": ["01"], "t": "SME0300 - T01"},
        {"d": ["7600005"], "turmas": ["01"], "t": "7600005 - T01"},
        {"d": ["7600006"], "turmas": ["01"], "t": "7600006 - T01"},
        {"d": ["7600007"], "turmas": ["01"], "t": "7600007 - T01"},
        {"d": ["7600008"], "turmas": ["01"], "t": "7600008 - T01"},
        {"d": ["SLC0100"], "turmas": ["01"], "t": "SLC0100 - T01"},
        {"d": ["SQM0400"], "turmas": ["01"], "t": "SQM0400 - T01"},
        {"d": ["SSC0108"], "turmas": ["01"], "t": "SSC0108 - T01"},
        {"d": ["SSC0100"], "turmas": ["01"], "t": "SSC0100 - T01"},
        {"d": ["SEL0999"], "turmas": ["01"], "t": "SEL0999 - T01"}
    ]
]

CACHE_CANONICO_TESTES = {
    "SEM0500": {
        "codigo": "SEM0500", "nome": "Mecânica Geral I",
        "turmas": {
            "01": {"numero": "01", "docentes": ["Carlos Alberto Fortulan", "Marcelo Becker", "Fernando Martini Catalano"]}
        }
    },
    "SEL0353": {
        "codigo": "SEL0353", "nome": "Circuitos Elétricos I",
        "turmas": {
            "01": {"numero": "01", "docentes": ["Carlos Dias Maciel", "Denis Vinicius Coury"]}
        }
    },
    "SET0188": {
        "codigo": "SET0188", "nome": "Resistência dos Materiais I",
        "turmas": {
            "01": {"numero": "01", "docentes": ["Sérgio Persival Baroncini Proença", "Vladimir Guilherme Haach"]}
        }
    },
    "SET0198": {
        "codigo": "SET0198", "nome": "Resistência dos Materiais II",
        "turmas": {"01": {"numero": "01", "docentes": ["Sérgio Persival Baroncini Proença"]}}
    },
    "SMA0301": {"codigo": "SMA0301", "nome": "Cálculo I", "turmas": {"01": {"numero": "01", "docentes": ["Daniel Smania"]}}},
    "SMA0354": {"codigo": "SMA0354", "nome": "Cálculo II", "turmas": {"01": {"numero": "01", "docentes": ["Hildebrando Munhoz Rodrigues"]}}},
    "SMA0355": {"codigo": "SMA0355", "nome": "Cálculo III", "turmas": {"01": {"numero": "01", "docentes": ["Alexandre Nolasco de Carvalho"]}}},
    "SMA0356": {
        "codigo": "SMA0356", "nome": "Cálculo IV",
        "turmas": {
            "01": {"numero": "01", "docentes": ["Ana Claudia Nabarro", "Reginaldo Demarque"]}
        }
    },
    "7600005": {"codigo": "7600005", "nome": "Física I", "turmas": {"01": {"numero": "01", "docentes": ["Vanderlei Salvador Bagnato"]}}},
    "7600006": {"codigo": "7600006", "nome": "Física II", "turmas": {"01": {"numero": "01", "docentes": ["Tito José Bonagamba"]}}},
    "SLC0100": {"codigo": "SLC0100", "nome": "Física Experimental", "turmas": {"01": {"numero": "01", "docentes": ["Euclydes Marega Junior"]}}}
}


class AutocompleteEngine:
    """Motor de busca e autocomplete em memória espelhando src/scripts.html."""

    def __init__(self, catalogo=None, dados_grade=None, cache_jupiter=None):
        self.catalogo = catalogo or CATALOGO_DEPARTAMENTOS
        self.mapa_docentes = {}
        self.mapa_disciplinas = {}
        self.mapa_grade_disciplinas = {}
        self.departamentos_ativos = {}

        grade_inicial = dados_grade if dados_grade is not None else GRADE_CANONICA_TESTES
        cache_inicial = cache_jupiter if cache_jupiter is not None else (CACHE_CANONICO_TESTES if dados_grade is None else {})
        self.reindexar_grade(grade_inicial, cache_inicial)

    def reindexar_grade(self, dados_grade, cache_jupiter=None):
        """Reconstrói os índices exclusivamente da grade atual e dos dados em cache."""
        self.mapa_docentes.clear()
        self.mapa_disciplinas.clear()

        disciplinas, deptos = extrair_disciplinas_e_turmas_da_grade(dados_grade)
        self.mapa_grade_disciplinas = disciplinas
        self.departamentos_ativos = deptos

        # 1. Indexa códigos das disciplinas encontradas na grade
        for cod in disciplinas:
            self.indexar_disciplina(cod, None)

        # 2. Se houver dados em cache, enriquece nomes e docentes alocados
        if cache_jupiter:
            for cod, info in disciplinas.items():
                dados = cache_jupiter.get(cod)
                if dados:
                    if dados.get("nome"):
                        self.indexar_disciplina(cod, dados["nome"])
                    self.indexar_de_dados_disciplina(cod, dados)

    def indexar_disciplina(self, codigo_raw, nome_raw):
        if not codigo_raw:
            return
        cod_limpo = str(codigo_raw).strip().upper()
        nome_limpo = re.sub(r'\s+', ' ', str(nome_raw or "")).strip()
        if not cod_limpo:
            return

        if cod_limpo not in self.mapa_disciplinas:
            self.mapa_disciplinas[cod_limpo] = {
                "codigo": cod_limpo,
                "nome": nome_limpo or cod_limpo,
                "nomeNorm": normalizar_texto(nome_limpo or cod_limpo),
                "codNorm": normalizar_texto(cod_limpo)
            }
        elif nome_limpo and (not self.mapa_disciplinas[cod_limpo]["nome"] or self.mapa_disciplinas[cod_limpo]["nome"] == cod_limpo):
            reg = self.mapa_disciplinas[cod_limpo]
            reg["nome"] = nome_limpo
            reg["nomeNorm"] = normalizar_texto(nome_limpo)

    def indexar_docente(self, nome_raw, depto="", disc_codigo=None):
        nome_limpo = normalizar_nome_docente(nome_raw)
        if not nome_limpo or len(nome_limpo) < 3:
            return
        nome_baixo = normalizar_texto(nome_limpo)
        if nome_baixo in ("a designar", "-", "sem docente") or nome_baixo.startswith("sem docente"):
            return

        if nome_limpo not in self.mapa_docentes:
            self.mapa_docentes[nome_limpo] = {
                "nome": nome_limpo,
                "nomeNorm": nome_baixo,
                "depto": depto or "",
                "disciplinas": set()
            }

        reg = self.mapa_docentes[nome_limpo]
        if depto and not reg["depto"]:
            reg["depto"] = depto
        if disc_codigo:
            reg["disciplinas"].add(disc_codigo)

    def indexar_de_dados_disciplina(self, codigo, dados):
        if not dados:
            return
        cod_limpo = str(codigo or "").strip().upper()
        info_grade = self.mapa_grade_disciplinas.get(cod_limpo)

        # Descarta se a disciplina não pertencer à grade ativa
        if not info_grade:
            return

        if dados.get("nome"):
            self.indexar_disciplina(cod_limpo, dados["nome"])

        if "turmas" not in dados:
            return

        # Sigla departamental (suporta 3 letras ou 3 dígitos do IFSC como 760)
        depto = ""
        m_letras = re.match(r'^[A-Za-z]{3}', cod_limpo)
        if m_letras:
            depto = m_letras.group(0).upper()
        else:
            m_num = re.match(r'^(\d{3})\d{4}$', cod_limpo)
            if m_num:
                depto = m_num.group(1)

        # Só restringe se houver turmas cadastradas E nenhuma ocorrência sem turma na grade
        tem_turmas_restritas = len(info_grade["turmas"]) > 0 and not info_grade.get("temSemTurma", False)
        turmas_permitidas = info_grade["turmas"]

        for t in dados["turmas"].values():
            if tem_turmas_restritas:
                num_raw = t.get("numero") or t.get("ofe")
                try:
                    num_t = int(num_raw)
                except (ValueError, TypeError):
                    num_t = -1

                casa_turma = (num_t in turmas_permitidas)
                if not casa_turma and t.get("codigoTurma"):
                    casa_turma = any(str(t["codigoTurma"]).endswith(str(n).zfill(2)) for n in turmas_permitidas)

                if not casa_turma:
                    continue

            for d in t.get("docentes", []):
                self.indexar_docente(d, depto, cod_limpo)
            for h in t.get("horarios", []):
                if h.get("docente"):
                    self.indexar_docente(h["docente"], depto, cod_limpo)
                for p in h.get("professores", []):
                    self.indexar_docente(p, depto, cod_limpo)

    def buscar_sugestoes(self, termo):
        termo_str = str(termo or "").strip()
        deptos_ativos = self.departamentos_ativos or {}
        grade_carregando = not self.mapa_grade_disciplinas and not self.departamentos_ativos

        if not termo_str:
            deptos_sugeridos = []
            if not grade_carregando:
                deptos_sugeridos = [
                    d for d in self.catalogo if d["sigla"] in deptos_ativos
                ]
                deptos_sugeridos.sort(
                    key=lambda d: (-deptos_ativos.get(d["sigla"], 0), d["sigla"])
                )

            return {
                "termo": "",
                "ehVazio": True,
                "gradeCarregando": grade_carregando,
                "departamentos": deptos_sugeridos[:8],
                "disciplinas": [],
                "docentes": [],
                "acoesRapidas": [
                    {"rotulo": "⚡ Horário de Agora", "acao": "agora"},
                    {"rotulo": "⚡ Focar em Hoje", "acao": "hoje"},
                    {"rotulo": "🧹 Limpar Filtros", "acao": "limpar", "alinharDireita": True}
                ]
            }

        t_norm = normalizar_texto(termo_str)

        # 1. Departamentos (Restrito ESTRITAMENTE aos departamentos com aulas na grade ativa)
        deptos_encontrados = []
        for dep in self.catalogo:
            if dep["sigla"] not in deptos_ativos:
                continue

            s_norm = normalizar_texto(dep["sigla"])
            n_norm = normalizar_texto(dep["nome"])
            a_norm = normalizar_texto(dep["apelido"])
            pontuacao = 0

            if s_norm == t_norm:
                pontuacao = 100
            elif s_norm.startswith(t_norm):
                pontuacao = 80
            elif t_norm in s_norm:
                pontuacao = 60
            elif a_norm.startswith(t_norm) or n_norm.startswith(t_norm):
                pontuacao = 50
            elif t_norm in a_norm or t_norm in n_norm:
                pontuacao = 40
            elif any(t_norm in normalizar_texto(k) for k in dep.get("keywords", [])):
                pontuacao = 30

            if pontuacao > 0:
                deptos_encontrados.append({**dep, "pontuacao": pontuacao})

        deptos_encontrados.sort(key=lambda x: x["pontuacao"], reverse=True)

        # 2. Disciplinas (quando termo tem >= 2 caracteres)
        disciplinas_encontradas = []
        if len(termo_str) >= 2:
            for disc in self.mapa_disciplinas.values():
                pontuacao = 0
                partes_nome = disc["nomeNorm"].split()

                if disc["codNorm"] == t_norm:
                    pontuacao = 100
                elif disc["codNorm"].startswith(t_norm):
                    pontuacao = 85
                elif disc["nomeNorm"].startswith(t_norm):
                    pontuacao = 75
                elif any(p.startswith(t_norm) for p in partes_nome):
                    pontuacao = 65
                elif t_norm in disc["codNorm"]:
                    pontuacao = 55
                elif t_norm in disc["nomeNorm"]:
                    pontuacao = 45

                if pontuacao > 0:
                    disciplinas_encontradas.append({
                        "codigo": disc["codigo"],
                        "nome": disc["nome"],
                        "pontuacao": pontuacao
                    })

            disciplinas_encontradas.sort(key=lambda x: x["pontuacao"], reverse=True)

        # 3. Docentes
        docentes_encontrados = []
        for doc in self.mapa_docentes.values():
            pontuacao = 0
            partes_nome = doc["nomeNorm"].split()

            if doc["nomeNorm"].startswith(t_norm):
                pontuacao = 80
            elif any(p.startswith(t_norm) for p in partes_nome):
                pontuacao = 60
            elif t_norm in doc["nomeNorm"]:
                pontuacao = 40

            if pontuacao > 0:
                docentes_encontrados.append({
                    "nome": doc["nome"],
                    "depto": doc["depto"],
                    "pontuacao": pontuacao
                })

        docentes_encontrados.sort(key=lambda x: x["pontuacao"], reverse=True)

        return {
            "termo": termo_str,
            "ehVazio": False,
            "gradeCarregando": False,
            "departamentos": deptos_encontrados[:6],
            "disciplinas": disciplinas_encontradas[:5],
            "docentes": docentes_encontrados[:6],
            "acoesRapidas": []
        }


class TestAutocompleteLogic(unittest.TestCase):
    """Testes automatizados completos para o Autocomplete Inteligente."""

    def setUp(self):
        self.engine = AutocompleteEngine()

    def test_busca_sigla_departamento_se(self):
        """Valida que digitar 'se' prioriza SEM, SEL, SET, SEP."""
        res = self.engine.buscar_sugestoes("se")
        siglas = [d["sigla"] for d in res["departamentos"]]
        self.assertIn("SEM", siglas)
        self.assertIn("SEL", siglas)
        self.assertIn("SET", siglas)
        self.assertIn("SEP", siglas)
        for d in res["departamentos"][:4]:
            self.assertGreaterEqual(d["pontuacao"], 80)

    def test_busca_sigla_departamento_exato(self):
        """Valida que match exato (ex: 'sem') recebe pontuação máxima 100."""
        res = self.engine.buscar_sugestoes("sem")
        self.assertTrue(len(res["departamentos"]) > 0)
        primeiro = res["departamentos"][0]
        self.assertEqual(primeiro["sigla"], "SEM")
        self.assertEqual(primeiro["pontuacao"], 100)

    def test_busca_departamento_por_apelido_ou_nome(self):
        """Valida busca por nomes amigáveis: mecanica, eletrica, estruturas, calculo, fisica."""
        res_mec = self.engine.buscar_sugestoes("mecanica")
        self.assertEqual(res_mec["departamentos"][0]["sigla"], "SEM")

        res_ele = self.engine.buscar_sugestoes("eletrica")
        self.assertEqual(res_ele["departamentos"][0]["sigla"], "SEL")

        res_est = self.engine.buscar_sugestoes("estruturas")
        self.assertEqual(res_est["departamentos"][0]["sigla"], "SET")

        res_calc = self.engine.buscar_sugestoes("calculo")
        siglas_calc = [d["sigla"] for d in res_calc["departamentos"]]
        self.assertIn("SMA", siglas_calc)

        res_fis = self.engine.buscar_sugestoes("fisica")
        siglas_fis = [d["sigla"] for d in res_fis["departamentos"]]
        self.assertIn("760", siglas_fis)

    def test_busca_docentes_por_primeiro_nome(self):
        """Valida que digitar primeiro nome encontra os docentes correspondentes."""
        res = self.engine.buscar_sugestoes("carlos")
        nomes = [d["nome"] for d in res["docentes"]]
        self.assertTrue(any("Fortulan" in n for n in nomes))
        self.assertTrue(any("Maciel" in n for n in nomes))

    def test_busca_docentes_por_sobrenome(self):
        """Valida busca por qualquer sobrenome (ex: proenca, fortulan, catalano, nabarro)."""
        res_proenca = self.engine.buscar_sugestoes("proenca")
        self.assertTrue(any("Proença" in d["nome"] for d in res_proenca["docentes"]))

        res_cat = self.engine.buscar_sugestoes("catalano")
        self.assertTrue(any("Catalano" in d["nome"] for d in res_cat["docentes"]))

        res_nab = self.engine.buscar_sugestoes("nabarro")
        self.assertTrue(any("Nabarro" in d["nome"] for d in res_nab["docentes"]))

    def test_indexacao_dinamica_novos_docentes(self):
        """Valida que novos docentes recebidos em dados do Júpiter/Janus são indexados dinamicamente."""
        dados_novos = {
            "turmas": {
                "01": {
                    "numero": "01",
                    "docentes": ["Prof. Dr. Ada Lovelace (R)"],
                    "horarios": [{"docente": "Alan Turing"}]
                }
            }
        }
        self.engine.indexar_de_dados_disciplina("SSC0100", dados_novos)

        res_ada = self.engine.buscar_sugestoes("ada")
        self.assertTrue(any(d["nome"] == "Ada Lovelace" and d["depto"] == "SSC" for d in res_ada["docentes"]))

        res_turing = self.engine.buscar_sugestoes("turing")
        self.assertTrue(any(d["nome"] == "Alan Turing" and d["depto"] == "SSC" for d in res_turing["docentes"]))

    def test_ignora_docentes_invalidos(self):
        """Valida que marcadores de turmas sem docente ('A Designar', '-') são descartados."""
        self.engine.indexar_docente("A Designar", "SEM")
        self.engine.indexar_docente("-", "SEL")
        self.engine.indexar_docente("Sem docente atribuído", "SET")

        res_des = self.engine.buscar_sugestoes("designar")
        self.assertEqual(len(res_des["docentes"]), 0)

    def test_insensibilidade_a_acentos_e_caixa(self):
        """Valida busca case-insensitive e diacritic-insensitive."""
        res_com_acento = self.engine.buscar_sugestoes("SÉRGIO")
        res_sem_acento = self.engine.buscar_sugestoes("sergio")
        nomes_com = [d["nome"] for d in res_com_acento["docentes"]]
        nomes_sem = [d["nome"] for d in res_sem_acento["docentes"]]
        self.assertEqual(nomes_com, nomes_sem)

    def test_busca_disciplina_por_nome(self):
        """Valida que digitar 'calculo' sugere Cálculo I, II, III, IV."""
        res = self.engine.buscar_sugestoes("calculo")
        self.assertTrue(len(res["disciplinas"]) > 0)
        nomes = [d["nome"] for d in res["disciplinas"]]
        self.assertTrue(any("Cálculo" in n for n in nomes))

    def test_busca_disciplina_por_codigo(self):
        """Valida que digitar código exato (ex: 'sma0356') encontra a disciplina com pontuação 100."""
        res = self.engine.buscar_sugestoes("sma0356")
        self.assertTrue(len(res["disciplinas"]) > 0)
        primeira = res["disciplinas"][0]
        self.assertEqual(primeira["codigo"], "SMA0356")
        self.assertEqual(primeira["pontuacao"], 100)
        self.assertEqual(primeira["nome"], "Cálculo IV")

    def test_busca_disciplina_por_palavra_composta(self):
        """Valida que digitar palavra interna (ex: 'materiais') encontra Resistência dos Materiais."""
        res = self.engine.buscar_sugestoes("materiais")
        nomes = [d["nome"] for d in res["disciplinas"]]
        self.assertTrue(any("Resistência dos Materiais" in n for n in nomes))

    def test_indexacao_dinamica_novas_disciplinas(self):
        """Valida que disciplinas recebidas nos lotes em tempo de execução são indexadas e sugeridas."""
        dados_novos = {
            "nome": "Computação Quântica Aplicada",
            "turmas": {}
        }
        self.engine.indexar_de_dados_disciplina("SEL0999", dados_novos)

        res = self.engine.buscar_sugestoes("quantica")
        self.assertTrue(any(d["codigo"] == "SEL0999" and "Quântica" in d["nome"] for d in res["disciplinas"]))

    def test_termo_vazio_retorna_atalhos_e_departamentos(self):
        """Valida que busca vazia devolve ações rápidas e top departamentos ativos."""
        res = self.engine.buscar_sugestoes("")
        self.assertTrue(res["ehVazio"])
        self.assertEqual(len(res["acoesRapidas"]), 3)
        acoes = [a["acao"] for a in res["acoesRapidas"]]
        self.assertEqual(acoes, ["agora", "hoje", "limpar"])
        self.assertNotIn("livres", acoes)
        limpar_item = next(a for a in res["acoesRapidas"] if a["acao"] == "limpar")
        self.assertTrue(limpar_item.get("alinharDireita"))
        self.assertGreaterEqual(len(res["departamentos"]), 4)
        self.assertEqual(len(res["disciplinas"]), 0)
        self.assertEqual(len(res["docentes"]), 0)

    # -------------------------------------------------------------
    # NOVOS TESTES UNITÁRIOS PARA CADA PEÇA NOVA IMPLEMENTADA
    # -------------------------------------------------------------

    def test_extrair_turmas_numericas_da_celula(self):
        """Valida extração resiliente de turmas: cel.turmas, regex T01, T1/T2, SEP5864 - 1 e sem turma."""
        # 1. cel.turmas explícito
        cel1 = {"t": "SEM0500 - T01 tv", "turmas": ["01"]}
        self.assertEqual(extrair_turmas_numericas_da_celula(cel1), [1])

        # 2. Turmas compartilhadas no texto
        cel2 = {"t": "SMA0356 - T01/T02"}
        self.assertEqual(extrair_turmas_numericas_da_celula(cel2), [1, 2])

        # 3. Pós-graduação com hífen
        cel3 = {"t": "SEP5864 - 1"}
        self.assertEqual(extrair_turmas_numericas_da_celula(cel3), [1])

        # 4. Pós-graduação com barra e dois dígitos
        cel4 = {"t": "SHS5991 / 02"}
        self.assertEqual(extrair_turmas_numericas_da_celula(cel4), [2])

        # 5. Célula sem turma indicada
        cel5 = {"t": "SMA0300 - Geometria Analítica"}
        self.assertEqual(extrair_turmas_numericas_da_celula(cel5), [])

    def test_extrair_disciplinas_e_turmas_da_grade(self):
        """Valida agregação correta da grade em O(1), frequências e flag temSemTurma."""
        grade_mock = [
            [
                {"d": ["SEM0500"], "turmas": ["01"], "t": "SEM0500 - T01"},
                {"d": ["SMA0356"], "turmas": ["01"], "t": "SMA0356 - T01"}
            ],
            [
                {"d": ["SEM0500"], "turmas": ["02"], "t": "SEM0500 - T02"},
                {"d": ["7600006"], "t": "7600006 - Física II"}  # sem turma explícita
            ]
        ]
        disciplinas, deptos = extrair_disciplinas_e_turmas_da_grade(grade_mock)

        self.assertIn("SEM0500", disciplinas)
        self.assertEqual(disciplinas["SEM0500"]["turmas"], {1, 2})
        self.assertFalse(disciplinas["SEM0500"]["temSemTurma"])

        self.assertIn("7600006", disciplinas)
        self.assertTrue(disciplinas["7600006"]["temSemTurma"])

        self.assertEqual(deptos.get("SEM"), 2)
        self.assertEqual(deptos.get("SMA"), 1)
        self.assertEqual(deptos.get("760"), 1)
        self.assertNotIn("IAU", deptos)

    def test_disciplina_fora_da_grade_nao_gera_chip(self):
        """Valida que disciplina ausente na grade alocada não é sugerida no autocomplete."""
        grade_exclusiva = [[{"d": ["SEM0500"], "turmas": ["01"], "t": "SEM0500 - T01"}]]
        engine = AutocompleteEngine(dados_grade=grade_exclusiva)

        res = engine.buscar_sugestoes("SMA0355")
        self.assertEqual(len(res["disciplinas"]), 0)

        res2 = engine.buscar_sugestoes("SEM0500")
        self.assertEqual(len(res2["disciplinas"]), 1)
        self.assertEqual(res2["disciplinas"][0]["codigo"], "SEM0500")

    def test_docente_fora_da_grade_nao_gera_chip(self):
        """Valida que docente histórico ausente na grade ativa não gera sugestão no autocomplete."""
        grade_exclusiva = [[{"d": ["SEM0500"], "turmas": ["01"], "t": "SEM0500 - T01"}]]
        cache = {
            "SEM0500": {
                "turmas": {
                    "01": {"numero": "01", "docentes": ["Carlos Alberto Fortulan"]}
                }
            }
        }
        engine = AutocompleteEngine(dados_grade=grade_exclusiva, cache_jupiter=cache)

        # Fortulan está alocado na turma 01 de SEM0500
        res_fortulan = engine.buscar_sugestoes("Fortulan")
        self.assertEqual(len(res_fortulan["docentes"]), 1)
        self.assertEqual(res_fortulan["docentes"][0]["nome"], "Carlos Alberto Fortulan")

        # Maciel e Proença não estão na grade exclusiva -> não devem aparecer
        res_maciel = engine.buscar_sugestoes("Maciel")
        self.assertEqual(len(res_maciel["docentes"]), 0)

        res_proenca = engine.buscar_sugestoes("Proença")
        self.assertEqual(len(res_proenca["docentes"]), 0)

    def test_docente_de_turma_alocada_vs_turma_nao_alocada(self):
        """Valida que em disciplina com Turma 01 na grade e Turma 02 fora da grade, só Turma 01 é indexada."""
        grade = [[{"d": ["SEM0500"], "turmas": ["01"], "t": "SEM0500 - T01"}]]
        dados_jupiter = {
            "turmas": {
                "01": {"numero": "01", "docentes": ["Prof. Alocado Na Grade"]},
                "02": {"numero": "02", "docentes": ["Prof. Substituto Nao Alocado"]}
            }
        }
        engine = AutocompleteEngine(dados_grade=grade)
        engine.indexar_de_dados_disciplina("SEM0500", dados_jupiter)

        res_alocado = engine.buscar_sugestoes("Alocado Na Grade")
        self.assertTrue(any("Alocado Na Grade" in d["nome"] for d in res_alocado["docentes"]))

        res_nao_alocado = engine.buscar_sugestoes("Nao Alocado")
        self.assertEqual(len(res_nao_alocado["docentes"]), 0)

    def test_disciplina_sem_turma_aceita_docentes_fallback(self):
        """Valida que quando uma célula não especifica turma (temSemTurma), docentes não sofrem falso negativo."""
        grade = [[{"d": ["SMA0300"], "t": "SMA0300 - Geometria Analítica"}]]
        dados_jupiter = {
            "turmas": {
                "01": {"numero": "01", "docentes": ["Docente Turma 01"]},
                "02": {"numero": "02", "docentes": ["Docente Turma 02"]}
            }
        }
        engine = AutocompleteEngine(dados_grade=grade)
        engine.indexar_de_dados_disciplina("SMA0300", dados_jupiter)

        res1 = engine.buscar_sugestoes("Docente Turma 01")
        self.assertEqual(len(res1["docentes"]), 1)

        res2 = engine.buscar_sugestoes("Docente Turma 02")
        self.assertEqual(len(res2["docentes"]), 1)

    def test_departamento_sem_disciplina_nao_aparece(self):
        """Valida que departamento inativo na grade não aparece nem nos atalhos nem na busca textual."""
        grade = [[{"d": ["SEM0500"], "turmas": ["01"]}, {"d": ["SMA0356"], "turmas": ["01"]}]]
        engine = AutocompleteEngine(dados_grade=grade)

        # Estado vazio
        res_vazio = engine.buscar_sugestoes("")
        siglas_vazio = [d["sigla"] for d in res_vazio["departamentos"]]
        self.assertIn("SEM", siglas_vazio)
        self.assertIn("SMA", siglas_vazio)
        self.assertNotIn("IAU", siglas_vazio)
        self.assertNotIn("SEL", siglas_vazio)

        # Busca textual
        res_iau = engine.buscar_sugestoes("arquitetura")
        self.assertEqual(len(res_iau["departamentos"]), 0)

    def test_departamentos_frequentes_ordenados_por_volume(self):
        """Valida ordenação decrescente por quantidade real de aulas alocadas no semestre."""
        grade = [
            [{"d": ["SEM0500"]}, {"d": ["SEM0501"]}, {"d": ["SEM0538"]}],
            [{"d": ["SMA0356"]}, {"d": ["SMA0301"]}],
            [{"d": ["SET0188"]}]
        ]
        engine = AutocompleteEngine(dados_grade=grade)
        res = engine.buscar_sugestoes("")
        siglas = [d["sigla"] for d in res["departamentos"]]
        self.assertEqual(siglas[0], "SEM")
        self.assertEqual(siglas[1], "SMA")
        self.assertEqual(siglas[2], "SET")

    def test_disciplina_numerica_ifsc_760(self):
        """Valida extração e associação de disciplina numérica 7600006 com departamento 760."""
        grade = [[{"d": ["7600006"], "turmas": ["01"], "t": "7600006 - T01"}]]
        dados_ifsc = {
            "nome": "Física II",
            "turmas": {
                "01": {"numero": "01", "docentes": ["Tito José Bonagamba"]}
            }
        }
        engine = AutocompleteEngine(dados_grade=grade)
        engine.indexar_de_dados_disciplina("7600006", dados_ifsc)

        # Busca departamento 760
        res_depto = engine.buscar_sugestoes("760")
        self.assertTrue(any(d["sigla"] == "760" for d in res_depto["departamentos"]))

        # Busca docente do 760
        res_doc = engine.buscar_sugestoes("Bonagamba")
        self.assertTrue(any(d["nome"] == "Tito José Bonagamba" and d["depto"] == "760" for d in res_doc["docentes"]))

    def test_disciplina_pos_janus_sep5864(self):
        """Valida disciplina de pós SEP5864 com oferecimento e turma do Janus."""
        grade = [[{"d": ["SEP5864"], "turmas": ["01"], "t": "SEP5864 - 1"}]]
        dados_janus = {
            "nome": "Pesquisa Operacional Aplicada",
            "turmas": {
                "01": {
                    "codigoTurma": "SEP5864-1",
                    "ofe": "1",
                    "numero": "01",
                    "docentes": ["Carlos Dias Maciel"]
                }
            }
        }
        engine = AutocompleteEngine(dados_grade=grade)
        engine.indexar_de_dados_disciplina("SEP5864", dados_janus)

        res_disc = engine.buscar_sugestoes("SEP5864")
        self.assertEqual(len(res_disc["disciplinas"]), 1)

        res_maciel = engine.buscar_sugestoes("Maciel")
        self.assertTrue(any(d["nome"] == "Carlos Dias Maciel" and d["depto"] == "SEP" for d in res_maciel["docentes"]))

    def test_grade_carregando_vazia_nao_quebra(self):
        """Valida comportamento resiliente quando a grade ainda não foi recebida do backend."""
        engine = AutocompleteEngine(dados_grade=[])
        res = engine.buscar_sugestoes("")
        self.assertTrue(res["ehVazio"])
        self.assertTrue(res["gradeCarregando"])
        self.assertEqual(len(res["departamentos"]), 0)
        self.assertEqual(len(res["disciplinas"]), 0)
        self.assertEqual(len(res["docentes"]), 0)

    def test_property_fuzzing_estabilidade(self):
        """Fuzzing com 500 buscas aleatórias garantindo 0 exceções."""
        caracteres = string.ascii_letters + string.digits + " \t\n-.,;/áéíóúãõç!@#$%¨&*()_+"
        for _ in range(500):
            tamanho = random.randint(0, 15)
            query = "".join(random.choice(caracteres) for _ in range(tamanho))
            res = self.engine.buscar_sugestoes(query)
            self.assertIsInstance(res, dict)
            self.assertIn("departamentos", res)
            self.assertIn("disciplinas", res)
            limite_deptos = 8 if res["ehVazio"] else 6
            self.assertLessEqual(len(res["departamentos"]), limite_deptos)
            self.assertLessEqual(len(res["disciplinas"]), 5)
            self.assertLessEqual(len(res["docentes"]), 6)


if __name__ == "__main__":
    unittest.main()
