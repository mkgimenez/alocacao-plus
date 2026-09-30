#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários e Fuzzing: Lógica de Resolução Temporal de Horários e Intervalos da Grade
Valida a identificação matemática de:
 1. Aulas ativas em andamento (⚡)
 2. Intervalos entre períodos letivos (recessos e almoço com contagem regressiva) (⏳)
 3. Pré-expediente matutino (A INICIAR) e pós-expediente
 4. Proteção contra falsos intervalos em grades filtradas por busca ou horário
 5. Fuzzing cobrindo todos os 1.440 minutos do dia (00:00 às 23:59)
"""

import unittest


def formatar_tempo_restante_grade(minutos):
    """Converte minutos restantes em texto amigável e legível."""
    if minutos <= 0:
        return ""
    if minutos < 60:
        return f"em {minutos} min"
    h = minutos // 60
    m = minutos % 60
    return f"em {h}h" if m == 0 else f"em {h}h {m}min"


def resolver_estado_temporal_grade(slots_ativos, todos_slots=None, agora_min=None, dia_semana="seg"):
    """
    Simula com rigor matemático a função obterEstadoTemporalGrade() de scripts.html.

    slots_ativos: lista de dicts [{'slot': slot_obj, 'cIdx': col_idx}] visíveis
    todos_slots: grade mestra de slots da universidade (dados.slots)
    agora_min: minuto atual do dia (0 a 1439)
    dia_semana: 'seg', 'ter', 'qua', 'qui', 'sex', 'sab' ou 'dom'
    """
    if dia_semana not in ("seg", "ter", "qua", "qui", "sex", "sab") or not slots_ativos:
        return {"tipo": "fora_dia", "idxSlot": -1, "slot": None, "textoTooltip": "", "icone": "", "tagLabel": ""}

    if agora_min is None:
        agora_min = 480  # Default 08:00

    # 1. Base mestra do dia (todos os slots da universidade hoje)
    fonte_mestra = todos_slots if (todos_slots and len(todos_slots) > 0) else [item["slot"] for item in slots_ativos]
    slots_mestre_hoje = [
        s for s in fonte_mestra
        if s.get("dia") == dia_semana and s.get("horaInicioMin") is not None and s.get("horaFimMin") is not None
    ]
    if not slots_mestre_hoje:
        return {"tipo": "fora_dia", "idxSlot": -1, "slot": None, "textoTooltip": "", "icone": "", "tagLabel": ""}

    slots_mestre_hoje.sort(key=lambda s: s["horaInicioMin"])

    # Mapeamento dos slots visíveis hoje com seus índices em slots_ativos
    slots_visiveis_hoje = []
    for idx, item in enumerate(slots_ativos):
        s = item.get("slot")
        if s and s.get("dia") == dia_semana and s.get("horaInicioMin") is not None:
            slots_visiveis_hoje.append({"idx": idx, "slot": s})
    slots_visiveis_hoje.sort(key=lambda x: x["slot"]["horaInicioMin"])

    # 2. Verificação de AULA ATIVA na universidade
    slot_aula_mestre = None
    for s in slots_mestre_hoje:
        if s["horaInicioMin"] <= agora_min < s["horaFimMin"]:
            slot_aula_mestre = s
            break

    if slot_aula_mestre:
        # A universidade está em aula neste instante
        idx_visivel = next((item["idx"] for item in slots_visiveis_hoje if item["slot"]["horaInicioMin"] == slot_aula_mestre["horaInicioMin"]), -1)
        rotulo = slot_aula_mestre.get("label") or slot_aula_mestre.get("textoInicio", "")
        return {
            "tipo": "aula",
            "idxSlot": idx_visivel,
            "slot": slot_aula_mestre if idx_visivel != -1 else None,
            "textoTooltip": f"{rotulo} (Horário Atual em Andamento)" if idx_visivel != -1 else "",
            "icone": "⚡ " if idx_visivel != -1 else "",
            "tagLabel": ""
        }

    # 3. Verificação de PRÉ-EXPEDIENTE (antes da 1ª aula do campus)
    primeiro_mestre = slots_mestre_hoje[0]
    if agora_min < primeiro_mestre["horaInicioMin"]:
        diff = primeiro_mestre["horaInicioMin"] - agora_min
        idx_visivel = slots_visiveis_hoje[0]["idx"] if slots_visiveis_hoje else -1
        slot_alvo = slots_visiveis_hoje[0]["slot"] if slots_visiveis_hoje else None
        rotulo = slot_alvo.get("label") or slot_alvo.get("textoInicio", "") if slot_alvo else ""
        txt_inicio = slot_alvo.get("textoInicio", "") if slot_alvo else ""
        info_tempo = formatar_tempo_restante_grade(diff)
        info_fmt = f" ({info_tempo})" if info_tempo else ""
        return {
            "tipo": "pre_expediente",
            "idxSlot": idx_visivel,
            "slot": slot_alvo,
            "textoTooltip": f"{rotulo} (Aulas iniciam às {txt_inicio}{info_fmt})",
            "icone": "⚡ " if idx_visivel != -1 else "",
            "tagLabel": ""
        }

    # 4. Verificação de PÓS-EXPEDIENTE (após a última aula do campus)
    ultimo_mestre = slots_mestre_hoje[-1]
    if agora_min >= ultimo_mestre["horaFimMin"]:
        return {"tipo": "pos_expediente", "idxSlot": -1, "slot": None, "textoTooltip": "", "icone": "", "tagLabel": ""}

    # 5. Verificação de INTERVALO REAL (entre dois slots da universidade)
    prox_slot_mestre = next((s for s in slots_mestre_hoje if s["horaInicioMin"] > agora_min), None)
    if prox_slot_mestre:
        diff = prox_slot_mestre["horaInicioMin"] - agora_min
        idx_visivel = next((item["idx"] for item in slots_visiveis_hoje if item["slot"]["horaInicioMin"] == prox_slot_mestre["horaInicioMin"]), -1)
        slot_alvo = prox_slot_mestre if idx_visivel != -1 else None
        rotulo = prox_slot_mestre.get("label") or prox_slot_mestre.get("textoInicio", "")
        txt_inicio = prox_slot_mestre.get("textoInicio", "")
        info_tempo = formatar_tempo_restante_grade(diff)
        info_fmt = f" ({info_tempo})" if info_tempo else ""
        return {
            "tipo": "intervalo",
            "idxSlot": idx_visivel,
            "slot": slot_alvo,
            "textoTooltip": f"{rotulo} (Intervalo em andamento — Próxima aula às {txt_inicio}{info_fmt})",
            "icone": "⚡ " if idx_visivel != -1 else "",
            "tagLabel": ""
        }

    return {"tipo": "fora_dia", "idxSlot": -1, "slot": None, "textoTooltip": "", "icone": "", "tagLabel": ""}


class TestIntervaloSlotLogic(unittest.TestCase):

    def setUp(self):
        # Grade padrão EESC (Segunda-feira)
        self.grade_eesc = [
            {"col": 3, "dia": "seg", "horaInicioMin": 480, "horaFimMin": 600, "textoInicio": "08:00", "textoFim": "10:00", "label": "08:00 - 10:00"},
            {"col": 4, "dia": "seg", "horaInicioMin": 620, "horaFimMin": 720, "textoInicio": "10:20", "textoFim": "12:00", "label": "10:20 - 12:00"},
            {"col": 5, "dia": "seg", "horaInicioMin": 860, "horaFimMin": 970, "textoInicio": "14:20", "textoFim": "16:10", "label": "14:20 - 16:10"},
            {"col": 6, "dia": "seg", "horaInicioMin": 980, "horaFimMin": 1080, "textoInicio": "16:20", "textoFim": "18:00", "label": "16:20 - 18:00"},
            {"col": 7, "dia": "seg", "horaInicioMin": 1140, "horaFimMin": 1240, "textoInicio": "19:00", "textoFim": "20:40", "label": "19:00 - 20:40"},
            {"col": 8, "dia": "seg", "horaInicioMin": 1250, "horaFimMin": 1350, "textoInicio": "20:50", "textoFim": "22:30", "label": "20:50 - 22:30"},
        ]
        self.slots_ativos_completos = [{"slot": s, "cIdx": i} for i, s in enumerate(self.grade_eesc)]

    def test_aula_ativa_horario_em_andamento(self):
        """Valida que às 08:30 detecta aula em andamento, ícone de raio e índice 0."""
        res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=510, dia_semana="seg")
        self.assertEqual(res["tipo"], "aula")
        self.assertEqual(res["idxSlot"], 0)
        self.assertEqual(res["icone"], "⚡ ")
        self.assertIn("Horário Atual em Andamento", res["textoTooltip"])

    def test_intervalo_matutino_curto(self):
        """Valida recesso matutino (10:05 entre 10:00 e 10:20): aponta para slot 10:20 com ícone ⚡ e 15 min."""
        res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=605, dia_semana="seg")
        self.assertEqual(res["tipo"], "intervalo")
        self.assertEqual(res["idxSlot"], 1)
        self.assertEqual(res["icone"], "⚡ ")
        self.assertEqual(res["tagLabel"], "")
        self.assertIn("em 15 min", res["textoTooltip"])

    def test_intervalo_almoco_formatacao_horas_minutos(self):
        """Valida almoço (12:30 às 14:20 = 110 min): exibe formatação elegante 'em 1h 50min'."""
        res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=750, dia_semana="seg")
        self.assertEqual(res["tipo"], "intervalo")
        self.assertEqual(res["idxSlot"], 2)
        self.assertIn("em 1h 50min", res["textoTooltip"])

    def test_fronteira_exata_termino_de_aula(self):
        """Valida que exatamente às 10:00:00 (fim da aula) transiciona imediatamente para intervalo."""
        res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=600, dia_semana="seg")
        self.assertEqual(res["tipo"], "intervalo")
        self.assertEqual(res["idxSlot"], 1)
        self.assertIn("em 20 min", res["textoTooltip"])

    def test_fronteira_exata_inicio_de_aula(self):
        """Valida que exatamente às 10:20:00 (início da aula) ativa a aula com raio ⚡."""
        res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=620, dia_semana="seg")
        self.assertEqual(res["tipo"], "aula")
        self.assertEqual(res["idxSlot"], 1)
        self.assertEqual(res["icone"], "⚡ ")

    def test_pre_expediente_matutino(self):
        """Valida pré-expediente às 07:45: aponta para a 1ª aula (08:00) com ícone ⚡."""
        res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=465, dia_semana="seg")
        self.assertEqual(res["tipo"], "pre_expediente")
        self.assertEqual(res["idxSlot"], 0)
        self.assertEqual(res["icone"], "⚡ ")
        self.assertEqual(res["tagLabel"], "")
        self.assertIn("em 15 min", res["textoTooltip"])

    def test_pos_expediente_noturno(self):
        """Valida pós-expediente às 23:00 (após 22:30): nenhuma coluna destacada."""
        res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=1380, dia_semana="seg")
        self.assertEqual(res["tipo"], "pos_expediente")
        self.assertEqual(res["idxSlot"], -1)

    def test_protecao_filtro_busca_nao_gera_falso_intervalo(self):
        """
        CENÁRIO CRÍTICO:
        Usuário buscou 'Cálculo', exibindo apenas 08:00 (idx 0) e 16:20 (idx 1).
        Às 11:00 (durante aula das 10:20 que está oculta):
        NÃO pode marcar 16:20 como intervalo! Deve retornar aula com idxSlot=-1.
        """
        slots_visiveis_filtrados = [
            {"slot": self.grade_eesc[0], "cIdx": 0},  # 08:00 - 10:00
            {"slot": self.grade_eesc[3], "cIdx": 3},  # 16:20 - 18:00
        ]
        res = resolver_estado_temporal_grade(slots_visiveis_filtrados, self.grade_eesc, agora_min=660, dia_semana="seg")
        self.assertEqual(res["tipo"], "aula")
        self.assertEqual(res["idxSlot"], -1)  # Nenhuma coluna destacada como falso intervalo!

    def test_fuzzing_estabilidade_todos_os_minutos_do_dia(self):
        """Property-Based Testing: Executa para todos os 1.440 minutos do dia e valida invariantes."""
        tipos_validos = {"aula", "intervalo", "pre_expediente", "pos_expediente", "fora_dia"}
        for minuto in range(1440):
            res = resolver_estado_temporal_grade(self.slots_ativos_completos, self.grade_eesc, agora_min=minuto, dia_semana="seg")
            self.assertIn(res["tipo"], tipos_validos)
            if res["idxSlot"] != -1:
                self.assertTrue(0 <= res["idxSlot"] < len(self.slots_ativos_completos))


if __name__ == "__main__":
    unittest.main()
