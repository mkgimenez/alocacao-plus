#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários: Lógica de Troca de Sala Inteligente (Pesquisa de Salas Livres)
Valida a extração de demanda (Graduação e Pós-Graduação), cálculo temporal com colspan,
normalização de dias, resolução de contexto hierárquico e simulação de filtragem.
"""

import re
import unittest
import unicodedata


def extrair_demanda_turma(turma_obj, eh_pos=False):
    """
    Extrai a demanda de alunos ou vagas da turma.
    Graduação: matriculados (Jupiterweb).
    Pós-Graduação: vagas (Janus).
    Garante proteção estrita contra o bug do 0 falsy e fallbacks adequados.
    """
    if not turma_obj or not isinstance(turma_obj, dict):
        return 0

    if eh_pos:
        vagas = turma_obj.get("vagas")
        if vagas is not None:
            try:
                return max(0, int(vagas))
            except (ValueError, TypeError):
                return 0
        return 0
    else:
        matriculados = turma_obj.get("matriculados")
        if matriculados is not None:
            try:
                return max(0, int(matriculados))
            except (ValueError, TypeError):
                return 0
        return 0


def normalizar_dia_semana(dia_str):
    """
    Normaliza representações textuais variadas de dias da semana para as chaves
    canônicas do sistema: 'seg', 'ter', 'qua', 'qui', 'sex', 'sab'.
    """
    if not dia_str:
        return None

    texto = str(dia_str).strip().lower()
    # Remove acentuação
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

    if re.search(r"\b(seg|segunda|2a|2ª)\b", texto):
        return "seg"
    if re.search(r"\b(ter|terca|3a|3ª)\b", texto):
        return "ter"
    if re.search(r"\b(qua|quarta|4a|4ª)\b", texto):
        return "qua"
    if re.search(r"\b(qui|quinta|5a|5ª)\b", texto):
        return "qui"
    if re.search(r"\b(sex|sexta|6a|6ª)\b", texto):
        return "sex"
    if re.search(r"\b(sab|sabado)\b", texto):
        return "sab"

    return None


def converter_hora_texto_para_minutos(hora_str):
    """Converte '08:00' ou '8:00' para minutos desde 00:00 (ex: 480)."""
    if not hora_str:
        return None
    match = re.match(r"^(\d{1,2}):(\d{2})$", str(hora_str).strip())
    if not match:
        return None
    h, m = int(match.group(1)), int(match.group(2))
    return h * 60 + m


def calcular_faixa_horarios_celula(c_orig, cs_real, todos_slots):
    """
    Calcula o dia e o intervalo [horaInicioMin, horaFimMin] a partir da célula na grade
    e seu colspan real sobre os slots canônicos da planilha.
    """
    if not todos_slots or c_orig < 0 or c_orig >= len(todos_slots):
        return None

    cs = max(1, cs_real or 1)
    end_idx = min(c_orig + cs - 1, len(todos_slots) - 1)

    slot_ini = todos_slots[c_orig]
    slot_fim = todos_slots[end_idx]

    return {
        "dia": slot_ini.get("dia"),
        "horaInicioMin": slot_ini.get("horaInicioMin"),
        "horaFimMin": slot_fim.get("horaFimMin"),
        "textoInicio": slot_ini.get("textoInicio"),
        "textoFim": slot_fim.get("textoFim"),
    }


def resolver_contexto_troca_sala(celula_info, turma_obj, todos_slots, matriz_grade, eh_pos=False):
    """
    Algoritmo central de resolução de contexto com hierarquia estrita:
    1. Célula clicada na grade (dia e faixa com suporte a colspan);
    2. Horário da turma ativa no mesmo dia (se houver);
    3. Primeiro horário cadastrado da turma ativa;
    4. Demanda de matriculados/vagas resiliente.
    """
    demanda = extrair_demanda_turma(turma_obj, eh_pos)

    # 1. Tenta extrair a partir da célula da grade
    if celula_info and "cIdx" in celula_info and "rIdx" in celula_info:
        r_idx = celula_info["rIdx"]
        c_idx = celula_info["cIdx"]

        if 0 <= r_idx < len(matriz_grade) and 0 <= c_idx < len(todos_slots):
            linha = matriz_grade[r_idx]
            cel = linha[c_idx] if c_idx < len(linha) else None
            cs_real = (cel.get("cs") or 1) if cel else 1

            faixa = calcular_faixa_horarios_celula(c_idx, cs_real, todos_slots)
            if faixa and faixa["dia"] and faixa["horaInicioMin"] is not None:
                # Verifica se a turma ativa possui horários oficiais
                horarios_turma = turma_obj.get("horarios", []) if turma_obj else []
                # Se a turma ativa tiver horários, procura se ela também tem aula no mesmo dia
                horario_mesmo_dia = None
                for h in horarios_turma:
                    if normalizar_dia_semana(h.get("dia")) == faixa["dia"]:
                        horario_mesmo_dia = h
                        break

                return {
                    "dia": faixa["dia"],
                    "horaInicioMin": faixa["horaInicioMin"],
                    "horaFimMin": faixa["horaFimMin"],
                    "demanda": demanda,
                    "origem": "celula",
                    "salaOrigemIdx": r_idx,
                    "mesmoDiaNaTurma": bool(horario_mesmo_dia)
                }

    # 2. Fallback: Horários oficiais cadastrados na turma ativa
    horarios_turma = turma_obj.get("horarios", []) if turma_obj else []
    if horarios_turma:
        primeiro = horarios_turma[0]
        dia_norm = normalizar_dia_semana(primeiro.get("dia"))
        h_ini = converter_hora_texto_para_minutos(primeiro.get("inicio"))
        h_fim = converter_hora_texto_para_minutos(primeiro.get("fim"))

        if dia_norm and h_ini is not None and h_fim is not None:
            return {
                "dia": dia_norm,
                "horaInicioMin": h_ini,
                "horaFimMin": h_fim,
                "demanda": demanda,
                "origem": "turma",
                "salaOrigemIdx": None,
                "mesmoDiaNaTurma": True
            }

    # 3. Caso de falha total: sem dia nem horário
    return {
        "dia": None,
        "horaInicioMin": None,
        "horaFimMin": None,
        "demanda": demanda,
        "origem": "indefinido",
        "salaOrigemIdx": None,
        "mesmoDiaNaTurma": False
    }


def simular_filtragem_grade_troca_sala(salas, matriz_grade, todos_slots, filtros):
    """
    Simula o motor de filtragem de scripts.html para validação de salas livres.
    """
    dia_alvo = filtros.get("dia")
    h_ini = filtros.get("horaInicioMin")
    h_fim = filtros.get("horaFimMin")
    cap_min = filtros.get("capacidadeMin", 0)
    apenas_livres = filtros.get("apenasLivres", False)

    # 1. Filtra slots elegíveis
    slots_ativos = []
    for c_idx, slot in enumerate(todos_slots):
        if dia_alvo and slot.get("dia") != dia_alvo:
            continue
        if h_ini is not None and slot.get("horaFimMin", 0) <= h_ini:
            continue
        if h_fim is not None and slot.get("horaInicioMin", 0) >= h_fim:
            continue
        slots_ativos.append({"slot": slot, "cIdx": c_idx})

    # 2. Filtra salas
    salas_visiveis = []
    for r_idx, sala in enumerate(salas):
        # Filtro de capacidade mínima
        if cap_min > 0 and sala.get("capacidadeNum", 0) < cap_min:
            continue

        linha_cels = matriz_grade[r_idx] if r_idx < len(matriz_grade) else []

        # Filtro de apenas livres
        if apenas_livres and slots_ativos:
            ocupada = False
            for item in slots_ativos:
                c = item["cIdx"]
                cel = linha_cels[c] if c < len(linha_cels) else None
                if cel and cel.get("t") and cel.get("t").strip():
                    ocupada = True
                    break
            if ocupada:
                continue

        salas_visiveis.append({"sala": sala, "rIdx": r_idx})

    return {
        "slotsAtivos": slots_ativos,
        "salasVisiveis": salas_visiveis
    }


class TestTrocaSalaLogic(unittest.TestCase):
    """Suíte de testes para a inteligência de troca de sala."""

    def setUp(self):
        # Configuração de grade sintética realista da EESC-USP
        self.slots = [
            {"col": 3, "dia": "ter", "horaInicioMin": 480, "horaFimMin": 600, "textoInicio": "08:00", "textoFim": "10:00"},
            {"col": 4, "dia": "ter", "horaInicioMin": 620, "horaFimMin": 720, "textoInicio": "10:20", "textoFim": "12:00"},
            {"col": 5, "dia": "ter", "horaInicioMin": 860, "horaFimMin": 970, "textoInicio": "14:20", "textoFim": "16:10"},
            {"col": 6, "dia": "qui", "horaInicioMin": 480, "horaFimMin": 600, "textoInicio": "08:00", "textoFim": "10:00"},
            {"col": 7, "dia": "qui", "horaInicioMin": 620, "horaFimMin": 720, "textoInicio": "10:20", "textoFim": "12:00"},
        ]

        self.salas = [
            {"idx": 0, "nome": "Sala 101 - Pequena", "capacidadeNum": 30, "bloco": "Bloco A"},
            {"idx": 1, "nome": "Sala 102 - Média", "capacidadeNum": 50, "bloco": "Bloco A"},
            {"idx": 2, "nome": "Sala 201 - Grande (Origem)", "capacidadeNum": 60, "bloco": "Bloco B"},
            {"idx": 3, "nome": "Sala 202 - Grande (Livre)", "capacidadeNum": 70, "bloco": "Bloco B"},
        ]

        # Grade:
        # Sala 0: Livre
        # Sala 1: Ocupada no slot 0 (08:00-10:00 Terça)
        # Sala 2 (Origem): Aula SMA0356 com 45 alunos no slot 0
        # Sala 3: Livre
        self.matriz_grade = [
            [None, None, None, None, None],
            [{"t": "OUTRA01", "cs": 1}, None, None, None, None],
            [{"t": "SMA0356 - T01\nCálculo II", "d": ["SMA0356"], "cs": 1}, None, None, None, None],
            [None, None, None, None, None],
        ]

    def test_extracao_demanda_graduacao_matriculados(self):
        """Valida que turmas de graduação usam a chave matriculados."""
        turma = {"numero": "01", "matriculados": 45, "vagas": 60}
        demanda = extrair_demanda_turma(turma, eh_pos=False)
        self.assertEqual(demanda, 45)

    def test_extracao_demanda_pos_vagas(self):
        """Valida que turmas de pós-graduação usam a chave vagas."""
        turma = {"numero": "01", "matriculados": 15, "vagas": 25}
        demanda = extrair_demanda_turma(turma, eh_pos=True)
        self.assertEqual(demanda, 25)

    def test_protecao_zero_falsy_graduacao_e_pos(self):
        """Garante que turmas com 0 alunos ou 0 vagas retornam exatamente 0 e não fallback."""
        turma_grad_zero = {"matriculados": 0}
        turma_pos_zero = {"vagas": 0}
        self.assertEqual(extrair_demanda_turma(turma_grad_zero, eh_pos=False), 0)
        self.assertEqual(extrair_demanda_turma(turma_pos_zero, eh_pos=True), 0)

    def test_fallback_demanda_ausente_ou_skeleton(self):
        """Valida resiliência para dados nulos ou em carregamento."""
        self.assertEqual(extrair_demanda_turma(None, eh_pos=False), 0)
        self.assertEqual(extrair_demanda_turma({}, eh_pos=False), 0)
        self.assertEqual(extrair_demanda_turma({"matriculados": None}, eh_pos=False), 0)
        self.assertEqual(extrair_demanda_turma({"matriculados": "inválido"}, eh_pos=False), 0)

    def test_normalizacao_extensiva_dias_semana(self):
        """Valida normalização robusta de todas as variantes de dias em português."""
        casos = [
            ("seg", "seg"), ("Segunda", "seg"), ("Segunda-feira", "seg"), ("SEGUNDA-FEIRA", "seg"),
            ("ter", "ter"), ("Terça", "ter"), ("terca", "ter"), ("Terça-feira", "ter"), ("3ª", "ter"),
            ("qua", "qua"), ("Quarta", "qua"), ("quarta-feira", "qua"), ("4ª", "qua"),
            ("qui", "qui"), ("Quinta", "qui"), ("quinta-feira", "qui"), ("5ª", "qui"),
            ("sex", "sex"), ("Sexta", "sex"), ("sexta-feira", "sex"), ("6ª", "sex"),
            ("sab", "sab"), ("Sábado", "sab"), ("sabado", "sab"),
            ("domingo", None), ("inválido", None), ("", None), (None, None)
        ]
        for entrada, esperado in casos:
            self.assertEqual(normalizar_dia_semana(entrada), esperado, f"Falha ao normalizar '{entrada}'")

    def test_faixa_horarios_celula_slot_simples(self):
        """Valida cálculo de horário para célula de slot simples (cs=1)."""
        faixa = calcular_faixa_horarios_celula(0, 1, self.slots)
        self.assertEqual(faixa["dia"], "ter")
        self.assertEqual(faixa["horaInicioMin"], 480)
        self.assertEqual(faixa["horaFimMin"], 600)

    def test_faixa_horarios_celula_com_colspan(self):
        """Valida cálculo de horário para célula mesclada de 4h (cs=2: 08:00 às 12:00)."""
        faixa = calcular_faixa_horarios_celula(0, 2, self.slots)
        self.assertEqual(faixa["dia"], "ter")
        self.assertEqual(faixa["horaInicioMin"], 480)
        self.assertEqual(faixa["horaFimMin"], 720)  # Término do slot 1 (12:00)

    def test_prioridade_celula_clicada_com_multiplos_horarios(self):
        """Turma com aulas em Terça e Quinta: ao clicar na Terça, resolve a Terça."""
        turma = {
            "numero": "01",
            "matriculados": 45,
            "horarios": [
                {"dia": "Quinta-feira", "inicio": "08:00", "fim": "10:00"},
                {"dia": "Terça-feira", "inicio": "08:00", "fim": "10:00"}
            ]
        }
        celula_info = {"rIdx": 2, "cIdx": 0}  # Slot 0 é Terça 08:00-10:00

        ctx = resolver_contexto_troca_sala(celula_info, turma, self.slots, self.matriz_grade, eh_pos=False)
        self.assertEqual(ctx["dia"], "ter")
        self.assertEqual(ctx["horaInicioMin"], 480)
        self.assertEqual(ctx["horaFimMin"], 600)
        self.assertEqual(ctx["demanda"], 45)
        self.assertEqual(ctx["origem"], "celula")
        self.assertTrue(ctx["mesmoDiaNaTurma"])

    def test_troca_de_aba_para_turma_com_outro_horario(self):
        """Ao alternar para turma sem célula correspondente, assume o horário oficial da turma."""
        turma_nova = {
            "numero": "02",
            "matriculados": 35,
            "horarios": [
                {"dia": "Quinta-feira", "inicio": "10:20", "fim": "12:00"}
            ]
        }
        # Célula info ausente ou desvinculada
        ctx = resolver_contexto_troca_sala(None, turma_nova, self.slots, self.matriz_grade, eh_pos=False)
        self.assertEqual(ctx["dia"], "qui")
        self.assertEqual(ctx["horaInicioMin"], 620)
        self.assertEqual(ctx["horaFimMin"], 720)
        self.assertEqual(ctx["demanda"], 35)
        self.assertEqual(ctx["origem"], "turma")

    def test_simulacao_filtragem_salas_livres_capacidade(self):
        """
        Valida que o algoritmo retorna apenas salas livres com capacidade >= demanda.
        Sala 0: cap 30 (Livre, mas menor que 45 -> EXCLUÍDA)
        Sala 1: cap 50 (Ocupada -> EXCLUÍDA)
        Sala 2: cap 60 (Sala de origem ocupada pela própria aula -> EXCLUÍDA)
        Sala 3: cap 70 (Livre e cap >= 45 -> RETORNADA)
        """
        filtros = {
            "dia": "ter",
            "horaInicioMin": 480,
            "horaFimMin": 600,
            "capacidadeMin": 45,
            "apenasLivres": True
        }

        res = simular_filtragem_grade_troca_sala(self.salas, self.matriz_grade, self.slots, filtros)
        salas_result = res["salasVisiveis"]

        self.assertEqual(len(salas_result), 1)
        self.assertEqual(salas_result[0]["sala"]["nome"], "Sala 202 - Grande (Livre)")
        self.assertEqual(salas_result[0]["sala"]["capacidadeNum"], 70)

    def test_exclusao_sala_origem_natural(self):
        """Garante que a sala original onde a aula acontece nunca é sugerida como sala livre."""
        filtros = {
            "dia": "ter",
            "horaInicioMin": 480,
            "horaFimMin": 600,
            "capacidadeMin": 0,  # Sem restrição de capacidade
            "apenasLivres": True
        }

        res = simular_filtragem_grade_troca_sala(self.salas, self.matriz_grade, self.slots, filtros)
        nomes_visiveis = [s["sala"]["nome"] for s in res["salasVisiveis"]]

        # Salas 1 e 2 estão ocupadas, logo apenas 0 e 3 são livres
        self.assertNotIn("Sala 201 - Grande (Origem)", nomes_visiveis)
        self.assertNotIn("Sala 102 - Média", nomes_visiveis)
        self.assertIn("Sala 101 - Pequena", nomes_visiveis)
        self.assertIn("Sala 202 - Grande (Livre)", nomes_visiveis)

    def test_fuzzing_estabilidade_troca_sala(self):
        """Property-based fuzzing com 200 iterações aleatórias garantindo 0 exceções."""
        import random
        dias = ["seg", "ter", "qua", "qui", "sex", "sab", "desconhecido", ""]

        for i in range(200):
            dia = random.choice(dias)
            matriculados = random.choice([None, 0, 15, 60, "80", -5, "abc"])
            vagas = random.choice([None, 0, 25, 40, "50", -2, "xyz"])
            eh_pos = random.choice([True, False])

            turma = {
                "numero": str(random.randint(1, 99)),
                "matriculados": matriculados,
                "vagas": vagas,
                "horarios": [
                    {"dia": dia, "inicio": "08:00", "fim": "10:00"}
                ] if random.choice([True, False]) else []
            }

            c_idx = random.randint(-2, 10)
            r_idx = random.randint(-2, 10)
            cel_info = {"rIdx": r_idx, "cIdx": c_idx} if random.choice([True, False]) else None

            ctx = resolver_contexto_troca_sala(cel_info, turma, self.slots, self.matriz_grade, eh_pos)
            self.assertIsInstance(ctx, dict)
            self.assertIn("demanda", ctx)
            self.assertGreaterEqual(ctx["demanda"], 0)


if __name__ == "__main__":
    unittest.main()
