#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suíte de Testes Automatizados — Filtragem Avançada de Células (Alocação Plus)
Valida a lógica de casamento inteligente da caixa de busca:
  1. Sigla da disciplina;
  2. Nome da disciplina;
  3. Turma com regex resiliente (T01, t01, T1, t1, T-01, t-1, etc.);
  4. Nome do docente (inclusive múltiplos docentes e co-docência);
  5. Modalidade Teórica ou Prática (direto do card: tipo || 'Teórica');
  6. Período Semestral ou Anual (direto do card: periodo || 'Semestral');
  7. Qualquer palavra do campo de observações;
  8. Combinações multi-token e casos de borda/fuzzing.
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


def extrair_tokens_busca(termo_norm):
    if not termo_norm:
        return []
    tratado = re.sub(r'\b(?:turma|t)\s*[\-_]?\s*(\d{1,2})\b', r't\1', str(termo_norm), flags=re.IGNORECASE)
    return [t for t in tratado.split() if t]


def extrair_numero_turma_busca(token):
    if not token:
        return None
    m = re.match(r'^(?:turma\s*|t\s*[\-_]?\s*)0*(\d{1,2})$', str(token).strip(), re.IGNORECASE)
    return int(m.group(1)) if m else None


def celula_corresponde_a_busca(cel, tokens, cache_jupiter=None):
    """
    Espelho Python fiel de celulaCorrespondeABusca (src/scripts.html).
    """
    if not cel or not tokens:
        return False

    cache = cache_jupiter or {}

    # Metadados estáticos da célula
    t_norm = normalizar_texto(cel.get("t", ""))
    nums = []
    for t in cel.get("turmas", []):
        try:
            nums.append(int(t))
        except (ValueError, TypeError):
            pass

    if not nums and cel.get("t"):
        for m in re.finditer(r'(?:-\s*)?T\s*[\-_]?\s*(\d{1,2})', cel["t"], re.IGNORECASE):
            try:
                n = int(m.group(1))
                if n not in nums:
                    nums.append(n)
            except (ValueError, TypeError):
                pass
        if not nums:
            for m in re.finditer(r'\b[A-Za-z]{3}5\d{3}\s*-\s*(\d{1,2})\b', cel["t"], re.IGNORECASE):
                try:
                    n = int(m.group(1))
                    if n not in nums:
                        nums.append(n)
                except (ValueError, TypeError):
                    pass

    tem_turma = len(nums) > 0
    raw_t = cel.get("t", "")
    tem_tv = bool(re.search(r'\btv\b', raw_t, re.I) or re.search(r'teoric', raw_t, re.I))
    tem_pv = bool(re.search(r'\bpv\b', raw_t, re.I) or re.search(r'pratic', raw_t, re.I))
    cods_norm = [normalizar_texto(c) for c in cel.get("d", [])]

    # Coleta dados das disciplinas associadas
    dados_lista = []
    for cod in cel.get("d", []):
        c_upper = str(cod).strip().upper()
        if c_upper in cache:
            dados_lista.append(cache[c_upper])

    # Identifica turmas relevantes para a célula
    turmas_relevantes = []
    todas_turmas_jupiter = []

    for dados in dados_lista:
        turmas_dict = dados.get("turmas", {})
        turmas_objs = list(turmas_dict.values())
        todas_turmas_jupiter.extend(turmas_objs)

        if tem_turma:
            casadas = []
            for tobj in turmas_objs:
                num_t = None
                try:
                    num_t = int(tobj.get("numero", 0))
                except (ValueError, TypeError):
                    pass
                if num_t in nums:
                    casadas.append(tobj)
                elif tobj.get("codigoTurma"):
                    cod_t = str(tobj.get("codigoTurma"))
                    if any(cod_t.endswith(str(n).zfill(2)) for n in nums):
                        casadas.append(tobj)

            if casadas:
                turmas_relevantes.extend(casadas)
            else:
                turmas_relevantes.extend(turmas_objs)
        else:
            turmas_relevantes.extend(turmas_objs)

    turmas_para_busca = turmas_relevantes if turmas_relevantes else todas_turmas_jupiter

    # Avalia se CADA token é satisfeito pela célula
    for tok in tokens:
        casou_token = False

        # 1. Token de Turma Resiliente
        num_turma_busca = extrair_numero_turma_busca(tok)
        if num_turma_busca is not None:
            if tem_turma:
                if num_turma_busca in nums:
                    continue
                return False

            if cel.get("t"):
                re_num = re.search(r'(?:^|[^\w])(?:turma\s*|t\s*[\-_]?\s*)0*' + str(num_turma_busca) + r'(?:\b|[^\d])', cel["t"], re.IGNORECASE)
                if re_num:
                    continue

            if turmas_para_busca:
                if any(int(tj.get("numero", -1)) == num_turma_busca for tj in turmas_para_busca):
                    continue
            return False

        # 2. Token de Modalidade (Teórica/Prática para Graduação, Presencial/Remota/Híbrida para Pós)
        eh_teorica = tok in ("teorica", "teorico", "teoricas", "teoricos", "tv")
        eh_pratica = tok in ("pratica", "pratico", "praticas", "praticos", "pv")
        eh_presencial = tok in ("presencial", "presenciais")
        eh_remota = tok in ("remota", "remoto", "remotas", "remotos", "ead", "online")
        eh_hibrida = tok in ("hibrida", "hibrido", "hibridas", "hibridos")

        if eh_teorica:
            if tem_tv:
                continue
            if any("teor" in normalizar_texto(tj.get("tipo", "Teorica")) or "te" in normalizar_texto(tj.get("tipo", "Teorica")) for tj in turmas_para_busca):
                continue

        if eh_pratica:
            if tem_pv:
                continue
            if any("prat" in normalizar_texto(tj.get("tipo", "Teorica")) or "pr" in normalizar_texto(tj.get("tipo", "Teorica")) for tj in turmas_para_busca):
                continue

        if eh_presencial:
            if any("presenc" in normalizar_texto(tj.get("tipo", "")) for tj in turmas_para_busca):
                continue

        if eh_remota:
            if any("remot" in normalizar_texto(tj.get("tipo", "")) or "ead" in normalizar_texto(tj.get("tipo", "")) or "online" in normalizar_texto(tj.get("tipo", "")) for tj in turmas_para_busca):
                continue

        if eh_hibrida:
            if any("hibrid" in normalizar_texto(tj.get("tipo", "")) for tj in turmas_para_busca):
                continue

        # 3. Token de Período (direto do card: periodo || 'Semestral')
        eh_semestral = tok in ("semestral", "semestrais", "semestre")
        eh_anual = tok in ("anual", "anuais", "ano")

        if eh_semestral:
            if "semestr" in t_norm:
                continue
            if turmas_para_busca and any("semestr" in normalizar_texto(tj.get("periodo", "Semestral")) for tj in turmas_para_busca):
                continue

        if eh_anual:
            if "anual" in t_norm or re.search(r'\bano\b', t_norm):
                continue
            if turmas_para_busca and any("anual" in normalizar_texto(tj.get("periodo", "Semestral")) for tj in turmas_para_busca):
                continue

        # 4. Busca Geral: Sigla, Nome, Programa, Docentes, Local, Observações e Texto da Célula
        if tok in t_norm:
            continue

        if any(tok in c for c in cods_norm):
            continue

        casou_metadados = False
        for dados in dados_lista:
            if dados.get("nome") and tok in normalizar_texto(dados["nome"]):
                casou_metadados = True
                break
            if dados.get("codigo") and tok in normalizar_texto(dados["codigo"]):
                casou_metadados = True
                break
            if dados.get("programa") and tok in normalizar_texto(dados["programa"]):
                casou_metadados = True
                break
        if casou_metadados:
            continue

        for tj in turmas_para_busca:
            # Docentes
            docs = tj.get("docentes", [])
            if any(tok in normalizar_texto(d) for d in docs):
                casou_metadados = True
                break

            # Horários com docentes ou local
            if tj.get("horarios"):
                for hor in tj["horarios"]:
                    if hor.get("docente") and tok in normalizar_texto(hor["docente"]):
                        casou_metadados = True
                        break
                    if hor.get("local") and tok in normalizar_texto(hor["local"]):
                        casou_metadados = True
                        break
                if casou_metadados:
                    break

            # Local da turma
            if tj.get("local") and tok in normalizar_texto(tj["local"]):
                casou_metadados = True
                break

            # Observações
            obs = tj.get("observacoes", "")
            if obs and tok in normalizar_texto(obs):
                casou_metadados = True
                break

            # Tipo e período textuais
            if tj.get("tipo") and tok in normalizar_texto(tj["tipo"]):
                casou_metadados = True
                break
            if tj.get("periodo") and tok in normalizar_texto(tj["periodo"]):
                casou_metadados = True
                break

        if casou_metadados:
            continue

        return False

    return True


class TestSearchFilter(unittest.TestCase):
    """Testes exaustivos para todos os 7 critérios e combinações."""

    def setUp(self):
        self.cache = {
            "SMA0356": {
                "codigo": "SMA0356",
                "nome": "Cálculo IV",
                "semOferecimento": False,
                "turmas": {
                    "01": {
                        "numero": "01",
                        "codigoTurma": "2026101",
                        "tipo": "Teórica",
                        "periodo": "Semestral",
                        "docentes": ["Ana Claudia Nabarro"],
                        "observacoes": "Engenharia Mecatrônica"
                    },
                    "02": {
                        "numero": "02",
                        "codigoTurma": "2026102",
                        "tipo": "Prática",
                        "periodo": "Semestral",
                        "docentes": ["Sérgio Luís Zani"],
                        "observacoes": "Engenharia Civil D15"
                    }
                }
            },
            "STT0410": {
                "codigo": "STT0410",
                "nome": "Mecânica dos Solos",
                "semOferecimento": False,
                "turmas": {
                    "01": {
                        "numero": "01",
                        "codigoTurma": "2026101",
                        "tipo": "Teórica",
                        "periodo": "Semestral",
                        "docentes": ["Carlos Dias Maciel", "Marcelo Becker"],
                        "observacoes": "Produção Turma A"
                    },
                    "02": {
                        "numero": "02",
                        "codigoTurma": "2026102",
                        "tipo": "Prática",
                        "periodo": "Anual",
                        "docentes": ["Docente Anual"],
                        "observacoes": "Laboratório de Geotecnia"
                    }
                }
            },
            "SEP5864": {
                "codigo": "SEP5864",
                "nome": "Pesquisa Operacional Aplicada",
                "programa": "Engenharia de Produção",
                "nivel": "pos",
                "semOferecimento": False,
                "turmas": {
                    "01": {
                        "numero": "01",
                        "codigoTurma": "2026101",
                        "tipo": "Presencial",
                        "periodo": "Semestral",
                        "docentes": ["Carlos Dias Maciel"],
                        "observacoes": "Mestrado e Doutorado",
                        "horarios": [
                            {
                                "dia": "Ter",
                                "horario": "14:00 às 18:00",
                                "local": "sala de aula",
                                "docente": "Carlos Dias Maciel"
                            }
                        ]
                    }
                }
            },
            "SHS5991": {
                "codigo": "SHS5991",
                "nome": "Modelagem Hidrológica Avançada",
                "programa": "Engenharia Hidráulica e Saneamento",
                "nivel": "pos",
                "semOferecimento": False,
                "turmas": {
                    "01": {
                        "numero": "01",
                        "codigoTurma": "2026101",
                        "tipo": "Remota",
                        "periodo": "Semestral",
                        "docentes": ["Eduardo Mario Mendiondo"],
                        "observacoes": "Aulas síncronas via Google Meet",
                        "horarios": [
                            {
                                "dia": "Qui",
                                "horario": "08:00 às 12:00",
                                "local": "online Meet",
                                "docente": "Eduardo Mario Mendiondo"
                            }
                        ]
                    }
                }
            }
        }

        # Célula Turma 1 de SMA0356
        self.cel_t1 = {
            "t": "SMA0356 - T1 tv",
            "d": ["SMA0356"],
            "turmas": ["01"]
        }

        # Célula Turma 2 de SMA0356
        self.cel_t2 = {
            "t": "SMA0356 - T02 pv",
            "d": ["SMA0356"],
            "turmas": ["02"]
        }

        # Célula Turma Composta (T1 e T2)
        self.cel_composta = {
            "t": "SMA0356 - T1 e T2",
            "d": ["SMA0356"],
            "turmas": ["01", "02"]
        }

        # Célula Co-docência (Carlos Maciel e Marcelo Becker)
        self.cel_codocencia = {
            "t": "STT0410 - T1",
            "d": ["STT0410"],
            "turmas": ["01"]
        }

        # Célula Turma Anual
        self.cel_anual = {
            "t": "STT0410 - T2",
            "d": ["STT0410"],
            "turmas": ["02"]
        }

        # Célula sem turma especificada
        self.cel_sem_turma = {
            "t": "SMA0356",
            "d": ["SMA0356"],
            "turmas": []
        }

        # Célula Pós-Graduação (Janus) Presencial
        self.cel_pos_presencial = {
            "t": "SEP5864 - 1",
            "d": ["SEP5864"],
            "turmas": ["01"],
            "pos": True
        }

        # Célula Pós-Graduação (Janus) Remota
        self.cel_pos_remota = {
            "t": "SHS5991 - 1",
            "d": ["SHS5991"],
            "turmas": ["01"],
            "pos": True
        }

    def test_criterio_1_sigla_disciplina(self):
        """1. Sigla da disciplina: maiúsculas, minúsculas, prefixos e códigos numéricos."""
        for q in ["SMA0356", "sma0356", "sma", "356"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Falhou para busca '{q}'")

        # Sigla inexistente deve falhar
        tokens_errados = extrair_tokens_busca(normalizar_texto("SET0999"))
        self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tokens_errados, self.cache))

    def test_criterio_2_nome_disciplina(self):
        """2. Nome da disciplina: com e sem acentos, maiúsculas e minúsculas."""
        for q in ["Cálculo IV", "calculo iv", "calculo", "IV", "Calculo"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Falhou para nome '{q}'")

        # Nome de outra disciplina não deve casar
        tokens_errados = extrair_tokens_busca(normalizar_texto("Termodinâmica"))
        self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tokens_errados, self.cache))

    def test_criterio_3_turma_resiliente(self):
        """3. Turma com regex resiliente: T01, t01, T1, t1, T-01, t-1, T 01, t 1, turma 1."""
        variacoes_t1 = ["T01", "t01", "T1", "t1", "T-01", "t-1", "T 01", "t 1", "turma 1", "turma 01", "T_01", "t_1"]
        for q in variacoes_t1:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Falhou para variação de turma: '{q}'")
            # T1 não deve casar com célula T2!
            self.assertFalse(celula_corresponde_a_busca(self.cel_t2, tokens, self.cache), f"T1 não deveria casar com T2 para '{q}'")

        # Teste com T2
        variacoes_t2 = ["T02", "t02", "T2", "t2", "T-02", "t-2", "turma 2"]
        for q in variacoes_t2:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t2, tokens, self.cache), f"Falhou T2 para '{q}'")
            self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"T2 não deveria casar com T1 para '{q}'")

        # Turma composta casa com T1 e casa com T2, mas não com T3
        tok_t1 = extrair_tokens_busca(normalizar_texto("T1"))
        tok_t2 = extrair_tokens_busca(normalizar_texto("T2"))
        tok_t3 = extrair_tokens_busca(normalizar_texto("T3"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_composta, tok_t1, self.cache))
        self.assertTrue(celula_corresponde_a_busca(self.cel_composta, tok_t2, self.cache))
        self.assertFalse(celula_corresponde_a_busca(self.cel_composta, tok_t3, self.cache))

    def test_criterio_4_docentes_multiplos_e_codocencia(self):
        """4. Nome do docente: único, múltiplos e co-docência."""
        # Docente único da T1
        for q in ["Ana Claudia", "Claudia", "Nabarro", "Ana"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Falhou docente T1 '{q}'")

        # Docente da T2 não deve casar na célula da T1
        tok_zani = extrair_tokens_busca(normalizar_texto("Zani"))
        self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tok_zani, self.cache))
        self.assertTrue(celula_corresponde_a_busca(self.cel_t2, tok_zani, self.cache))

        # Co-docência na mesma turma (Carlos Maciel e Marcelo Becker)
        for q in ["Carlos", "Maciel", "Becker", "Carlos Maciel", "Carlos Becker", "Marcelo"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_codocencia, tokens, self.cache), f"Falhou co-docente '{q}'")

    def test_criterio_5_modalidade_teorica_e_pratica(self):
        """5. Modalidade Teórica ou Prática (diretamente como no Card: tipo || 'Teórica' e tv/pv)."""
        # Célula Teórica (SMA0356 T1)
        for q in ["Teórica", "teorica", "teorico", "tv"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Falhou teórica '{q}'")
            self.assertFalse(celula_corresponde_a_busca(self.cel_t2, tokens, self.cache), f"Teórica não deveria casar com T2 para '{q}'")

        # Célula Prática (SMA0356 T2)
        for q in ["Prática", "pratica", "pratico", "pv"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t2, tokens, self.cache), f"Falhou prática '{q}'")
            self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Prática não deveria casar com T1 para '{q}'")

    def test_criterio_6_periodo_semestral_e_anual(self):
        """6. Período Semestral ou Anual (diretamente como no Card: periodo || 'Semestral')."""
        # Célula Semestral (SMA0356 T1)
        for q in ["Semestral", "semestral", "semestre"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Falhou semestral '{q}'")

        # Célula Anual (STT0410 T2)
        for q in ["Anual", "anual", "ano"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_anual, tokens, self.cache), f"Falhou anual '{q}'")
            # Célula semestral não deve casar com anual
            self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Semestral não deveria casar com anual '{q}'")

    def test_criterio_7_observacoes(self):
        """7. Qualquer palavra do campo observações."""
        # Observação da T1: "Engenharia Mecatrônica"
        for q in ["Mecatrônica", "mecatronica", "Engenharia"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"Falhou observação T1 '{q}'")

        # Observação da T2: "Engenharia Civil D15"
        for q in ["Civil", "civil", "D15", "d15"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_t2, tokens, self.cache), f"Falhou observação T2 '{q}'")
            self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache), f"D15 não deveria casar com T1")

        # Observação STT0410 T1: "Produção Turma A"
        for q in ["Produção", "producao", "Turma A"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_codocencia, tokens, self.cache), f"Falhou obs '{q}'")

    def test_combinacoes_multi_token(self):
        """8. Combinações multi-token cruzando múltiplos critérios simultâneos."""
        # Sigla + Turma + Modalidade
        tokens = extrair_tokens_busca(normalizar_texto("SMA0356 T-01 Teórica"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache))
        self.assertFalse(celula_corresponde_a_busca(self.cel_t2, tokens, self.cache))

        # Docente + Observação
        tokens = extrair_tokens_busca(normalizar_texto("Claudia Mecatrônica"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_t1, tokens, self.cache))

        # Co-docente + Período Semestral
        tokens = extrair_tokens_busca(normalizar_texto("Carlos Becker Semestral"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_codocencia, tokens, self.cache))

        # Uma palavra errada na combinação deve invalidar o match (AND estrito)
        tokens_invalido = extrair_tokens_busca(normalizar_texto("SMA0356 T1 Zani"))
        self.assertFalse(celula_corresponde_a_busca(self.cel_t1, tokens_invalido, self.cache))

    def test_celula_sem_turma_especificada(self):
        """Célula genérica sem turma (ex: SMA0356 simples) casa com ambas as turmas cadastradas."""
        tok_t1 = extrair_tokens_busca(normalizar_texto("T1"))
        tok_t2 = extrair_tokens_busca(normalizar_texto("T2"))
        tok_t3 = extrair_tokens_busca(normalizar_texto("T3"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_sem_turma, tok_t1, self.cache))
        self.assertTrue(celula_corresponde_a_busca(self.cel_sem_turma, tok_t2, self.cache))
        self.assertFalse(celula_corresponde_a_busca(self.cel_sem_turma, tok_t3, self.cache))

    def test_criterio_pos_graduacao_modalidade_presencial_e_remota(self):
        """Valida que tokens de modalidade de pós (Presencial, Remota, EAD, etc.) casam com células do Janus."""
        # SEP5864 é Presencial
        for q in ["Presencial", "presencial", "presenciais"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_pos_presencial, tokens, self.cache), f"Falhou presencial '{q}'")
            self.assertFalse(celula_corresponde_a_busca(self.cel_pos_remota, tokens, self.cache), f"Remota não deve casar com '{q}'")

        # SHS5991 é Remota
        for q in ["Remota", "remoto", "ead", "online"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_pos_remota, tokens, self.cache), f"Falhou remota '{q}'")
            self.assertFalse(celula_corresponde_a_busca(self.cel_pos_presencial, tokens, self.cache), f"Presencial não deve casar com '{q}'")

    def test_criterio_pos_graduacao_local_de_aula(self):
        """Valida que buscar pelo local (sala de aula, Meet) encontra a célula de pós correspondente."""
        # SEP5864 horário tem local "sala de aula"
        tok_sala = extrair_tokens_busca(normalizar_texto("sala de aula"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_pos_presencial, tok_sala, self.cache))

        # SHS5991 horário tem local "online Meet"
        tok_meet = extrair_tokens_busca(normalizar_texto("Meet"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_pos_remota, tok_meet, self.cache))
        self.assertFalse(celula_corresponde_a_busca(self.cel_pos_presencial, tok_meet, self.cache))

    def test_criterio_pos_graduacao_programa(self):
        """Valida busca pelo nome do Programa de Pós-Graduação (Engenharia de Produção, Hidráulica)."""
        tok_prod = extrair_tokens_busca(normalizar_texto("Produção"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_pos_presencial, tok_prod, self.cache))

        tok_hidr = extrair_tokens_busca(normalizar_texto("Hidráulica"))
        self.assertTrue(celula_corresponde_a_busca(self.cel_pos_remota, tok_hidr, self.cache))
        self.assertFalse(celula_corresponde_a_busca(self.cel_pos_presencial, tok_hidr, self.cache))

    def test_criterio_pos_graduacao_turma_resiliente(self):
        """Valida casamento de turma em células de pós (SEP5864 - 1 casando com T1, t01, turma 1)."""
        for q in ["T1", "t01", "turma 1", "T-1"]:
            tokens = extrair_tokens_busca(normalizar_texto(q))
            self.assertTrue(celula_corresponde_a_busca(self.cel_pos_presencial, tokens, self.cache), f"Falhou turma pós '{q}'")

        # Turma inexistente (T2)
        tok_t2 = extrair_tokens_busca(normalizar_texto("T2"))
        self.assertFalse(celula_corresponde_a_busca(self.cel_pos_presencial, tok_t2, self.cache))

    def test_fuzzing_estabilidade(self):
        """Property-based Fuzzing com 500 buscas aleatórias garantindo 0 crashes/exceções."""
        for _ in range(500):
            tamanho = random.randint(1, 40)
            termo = "".join(random.choices(string.ascii_letters + string.digits + " -_[]/\\", k=tamanho))
            tokens = extrair_tokens_busca(normalizar_texto(termo))
            # Garante que roda e retorna booleano sem levantar nenhuma exceção
            res = celula_corresponde_a_busca(self.cel_t1, tokens, self.cache)
            self.assertIsInstance(res, bool)
            res_pos = celula_corresponde_a_busca(self.cel_pos_presencial, tokens, self.cache)
            self.assertIsInstance(res_pos, bool)


if __name__ == "__main__":
    unittest.main()
