#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados — Autocomplete Inteligente no Campo de Busca
Valida o catálogo de departamentos, indexação de docentes e motor de sugestões
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

DOCENTES_SEMENTE = [
    {"nome": "Carlos Alberto Fortulan", "depto": "SEM"},
    {"nome": "Marcelo Becker", "depto": "SEM"},
    {"nome": "Glauco Augusto de Paula Caurin", "depto": "SEM"},
    {"nome": "Paulo Seleghim Junior", "depto": "SEM"},
    {"nome": "Fernando Martini Catalano", "depto": "SEM/SAA"},
    {"nome": "Zilda de Castro Silveira", "depto": "SEM"},
    {"nome": "Adriano Almeida Gonçalves Siqueira", "depto": "SEM"},
    {"nome": "Carlos De Marqui Junior", "depto": "SAA/SEM"},
    {"nome": "Daniel Varela Magalhães", "depto": "SEM"},
    {"nome": "Álvaro Manoel de Souza Soares", "depto": "SEM"},

    {"nome": "Carlos Dias Maciel", "depto": "SEL"},
    {"nome": "Denis Vinicius Coury", "depto": "SEL"},
    {"nome": "Mario Oleskovicz", "depto": "SEL"},
    {"nome": "Marcelo Andrade da Costa Vieira", "depto": "SEL"},
    {"nome": "Eduardo Nobuhiro Asada", "depto": "SEL"},
    {"nome": "João Paulo do Carmo", "depto": "SEL"},
    {"nome": "Luís Fernando Costa Alberto", "depto": "SEL"},
    {"nome": "Mário Alexandre Gazziro", "depto": "SEL"},
    {"nome": "Sebastião E. Neto da Silva", "depto": "SEL"},

    {"nome": "Sérgio Persival Baroncini Proença", "depto": "SET"},
    {"nome": "Vladimir Guilherme Haach", "depto": "SET"},
    {"nome": "Maximiliano dos Santos Anversa", "depto": "SET"},
    {"nome": "José Samuel Giongo", "depto": "SET"},
    {"nome": "Jorge Munaiar Neto", "depto": "SET"},
    {"nome": "Luciana Maria Bonvino Figueiredo", "depto": "SET"},
    {"nome": "Rodrigo Ribeiro Paccola", "depto": "SET"},

    {"nome": "Aldo Roberto Ometto", "depto": "SEP"},
    {"nome": "Daisy Aparecida do Carmo Curtolo", "depto": "SEP"},
    {"nome": "Daniel Capaldo Amaral", "depto": "SEP"},
    {"nome": "Mateus Cecilio Gerolamo", "depto": "SEP"},
    {"nome": "Janaina Mascarenhas Hornos da Costa", "depto": "SEP"},
    {"nome": "Edisio Alves de Aguiar Junior", "depto": "SEP"},

    {"nome": "Carlos Alberto Della Rovere", "depto": "SMM"},
    {"nome": "Haroldo Cavalcanti Pinto", "depto": "SMM"},
    {"nome": "Antonio Jorge Abdalla", "depto": "SMM"},
    {"nome": "Edson Antonio Ticianelli", "depto": "IQSC/SMM"},

    {"nome": "Edson Cezar Wendland", "depto": "SHS"},
    {"nome": "Maria do Carmo Calijuri", "depto": "SHS"},
    {"nome": "Rodrigo de Melo Porto", "depto": "SHS"},
    {"nome": "Lyda Patricia Sabogal Paz", "depto": "SHS"},

    {"nome": "Lázaro Valentin Zuquette", "depto": "SGS"},
    {"nome": "Tacio Mauro Pereira de Campos", "depto": "SGS"},
    {"nome": "Maria Eugenia Gimenez Boscov", "depto": "SGS"},

    {"nome": "Alvaro Martins Abdalla", "depto": "SAA"},
    {"nome": "Hernan Dario Ceron Muñoz", "depto": "SAA"},
    {"nome": "James Waterhouse", "depto": "SAA"},

    {"nome": "Cira Souza Pitombo", "depto": "STT"},
    {"nome": "José Leomar Fernandes Júnior", "depto": "STT"},
    {"nome": "Antônio Nélson Rodrigues da Silva", "depto": "STT"},
    {"nome": "Ana Paula Camargo Larocca", "depto": "STT"},

    {"nome": "Daniel Smania", "depto": "SMA"},
    {"nome": "Hildebrando Munhoz Rodrigues", "depto": "SMA"},
    {"nome": "Alexandre Nolasco de Carvalho", "depto": "SMA"},
    {"nome": "Ana Claudia Nabarro", "depto": "SMA"},
    {"nome": "Tiago Picon", "depto": "SMA"},
    {"nome": "Reginaldo Demarque", "depto": "SMA"},

    {"nome": "Francisco Louzada Neto", "depto": "SME"},
    {"nome": "Cynthia de Oliveira Lage Ferreira", "depto": "SME"},
    {"nome": "Juliana Cobre", "depto": "SME"},
    {"nome": "José Alberto Cuminato", "depto": "SME"},

    {"nome": "Vanderlei Salvador Bagnato", "depto": "IFSC"},
    {"nome": "Tito José Bonagamba", "depto": "IFSC"},
    {"nome": "Yvonne Primerano Mascarenhas", "depto": "IFSC"},
    {"nome": "Luiz Vitor de Souza Filho", "depto": "IFSC"},
    {"nome": "Euclydes Marega Junior", "depto": "IFSC"}
]


class AutocompleteEngine:
    """Motor de busca e autocomplete em memória espelhando src/scripts.html."""

    def __init__(self, catalogo=None, docentes_semente=None):
        self.catalogo = catalogo or CATALOGO_DEPARTAMENTOS
        self.mapa_docentes = {}

        for d in (docentes_semente or DOCENTES_SEMENTE):
            self.indexar_docente(d["nome"], d.get("depto", ""), None)

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
        if not dados or "turmas" not in dados:
            return
        depto = codigo[:3].upper() if re.match(r'^[A-Za-z]{3}', str(codigo)) else ""
        for t in dados["turmas"].values():
            for d in t.get("docentes", []):
                self.indexar_docente(d, depto, codigo)
            for h in t.get("horarios", []):
                if h.get("docente"):
                    self.indexar_docente(h["docente"], depto, codigo)
                for p in h.get("professores", []):
                    self.indexar_docente(p, depto, codigo)

    def buscar_sugestoes(self, termo):
        termo_str = str(termo or "").strip()
        if not termo_str:
            return {
                "termo": "",
                "ehVazio": True,
                "departamentos": self.catalogo[:6],
                "docentes": [],
                "acoesRapidas": [
                    {"rotulo": "🚪 Salas Livres", "acao": "livres"},
                    {"rotulo": "⚡ Horário de Agora", "acao": "agora"},
                    {"rotulo": "⚡ Focar em Hoje", "acao": "hoje"}
                ]
            }

        t_norm = normalizar_texto(termo_str)

        # 1. Departamentos
        deptos_encontrados = []
        for dep in self.catalogo:
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

        # 2. Docentes
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
            "departamentos": deptos_encontrados[:6],
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
        # Deve conter os 4 departamentos da EESC com prefixo SE
        self.assertIn("SEM", siglas)
        self.assertIn("SEL", siglas)
        self.assertIn("SET", siglas)
        self.assertIn("SEP", siglas)
        # As primeiras 4 posições devem ter pontuação >= 80 (prefix match)
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
        # 1. Mecânica -> SEM
        res_mec = self.engine.buscar_sugestoes("mecanica")
        self.assertEqual(res_mec["departamentos"][0]["sigla"], "SEM")

        # 2. Elétrica -> SEL
        res_ele = self.engine.buscar_sugestoes("eletrica")
        self.assertEqual(res_ele["departamentos"][0]["sigla"], "SEL")

        # 3. Estruturas -> SET
        res_est = self.engine.buscar_sugestoes("estruturas")
        self.assertEqual(res_est["departamentos"][0]["sigla"], "SET")

        # 4. Cálculo -> SMA
        res_calc = self.engine.buscar_sugestoes("calculo")
        siglas_calc = [d["sigla"] for d in res_calc["departamentos"]]
        self.assertIn("SMA", siglas_calc)

        # 5. Física -> 760 e SLC
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
                    "docentes": ["Prof. Dr. Ada Lovelace (R)"],
                    "horarios": [{"docente": "Alan Turing"}]
                }
            }
        }
        self.engine.indexar_de_dados_disciplina("SSC0100", dados_novos)

        # Busca por Ada
        res_ada = self.engine.buscar_sugestoes("ada")
        self.assertTrue(any(d["nome"] == "Ada Lovelace" and d["depto"] == "SSC" for d in res_ada["docentes"]))

        # Busca por Turing
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

    def test_termo_vazio_retorna_atalhos(self):
        """Valida que busca vazia devolve ações rápidas e top 6 departamentos."""
        res = self.engine.buscar_sugestoes("")
        self.assertTrue(res["ehVazio"])
        self.assertEqual(len(res["acoesRapidas"]), 3)
        self.assertEqual(len(res["departamentos"]), 6)
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
            self.assertIn("docentes", res)
            self.assertLessEqual(len(res["departamentos"]), 6)
            self.assertLessEqual(len(res["docentes"]), 6)


if __name__ == "__main__":
    unittest.main()
