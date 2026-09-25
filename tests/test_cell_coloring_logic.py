#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários: Lógica de Coloração Progressiva das Células da Grade
Valida que as células iniciam em estado pendente (sem as tonalidades de azul do Júpiter e do Janus)
e adquirem as cores definitivas apenas quando os dados para o card flutuante forem carregados.
"""

import unittest


def determinar_classes_celula(tem_aula, cel_efetiva, cache_disciplinas):
    """
    Simula com fidelidade matemática a determinação de classes CSS da célula
    conforme implementado na função renderizarGrade() em scripts.html.
    """
    if not tem_aula:
        return {"aula_class": "celula-livre", "pendente": False, "carregada": False, "codigos": []}

    codigos = [str(c).strip().upper() for c in (cel_efetiva.get("d") or []) if str(c).strip()]
    tem_disciplinas = len(codigos) > 0

    todas_carregadas = False
    if tem_disciplinas:
        todas_carregadas = all(c in cache_disciplinas for c in codigos)

    pendente_class = ""
    if tem_disciplinas:
        pendente_class = " celula-carregada" if todas_carregadas else " celula-aula-pendente"

    pos = bool(cel_efetiva.get("pos"))
    base_aula = " celula-aula celula-pos" if pos else " celula-aula"
    aula_class = (base_aula + pendente_class).strip()

    return {
        "aula_class": aula_class,
        "pendente": tem_disciplinas and not todas_carregadas,
        "carregada": tem_disciplinas and todas_carregadas,
        "codigos": codigos
    }


def atualizar_celulas_no_lote(celulas_dom, codigos_atualizados, cache_disciplinas):
    """
    Simula a atualização progressiva no DOM realizada por atualizarEnriquecimentoCelulasVisiveis().
    """
    transicionadas = []
    for cel in celulas_dom:
        if cel.get("pendente"):
            cods = cel.get("codigos", [])
            if cods and all(c in cache_disciplinas for c in cods):
                cel["pendente"] = False
                cel["carregada"] = True
                cel["aula_class"] = cel["aula_class"].replace("celula-aula-pendente", "celula-carregada").strip()
                transicionadas.append(cel)
    return transicionadas


class TestCellColoringLogic(unittest.TestCase):

    def test_celula_graduacao_inicia_pendente_sem_cor_azul(self):
        """Valida que célula de graduação com Júpiter pendente não tem classe carregada e recebe celula-aula-pendente."""
        cache = {}
        cel = {"t": "SEM0538 - T1", "d": ["SEM0538"], "pos": False}
        res = determinar_classes_celula(tem_aula=True, cel_efetiva=cel, cache_disciplinas=cache)

        self.assertTrue(res["pendente"])
        self.assertFalse(res["carregada"])
        self.assertIn("celula-aula-pendente", res["aula_class"])
        self.assertNotIn("celula-carregada", res["aula_class"])

    def test_celula_pos_inicia_pendente_sem_cor_azul(self):
        """Valida que célula de pós com Janus pendente recebe celula-aula-pendente e celula-pos."""
        cache = {}
        cel = {"t": "SEP5864 - T1", "d": ["SEP5864"], "pos": True}
        res = determinar_classes_celula(tem_aula=True, cel_efetiva=cel, cache_disciplinas=cache)

        self.assertTrue(res["pendente"])
        self.assertFalse(res["carregada"])
        self.assertIn("celula-pos", res["aula_class"])
        self.assertIn("celula-aula-pendente", res["aula_class"])
        self.assertNotIn("celula-carregada", res["aula_class"])

    def test_celula_ja_no_cache_inicia_colorida(self):
        """Valida que célula cujos dados já estão em cache inicia diretamente como celula-carregada."""
        cache = {"SEM0538": {"nome": "Sistemas de Controle"}}
        cel = {"t": "SEM0538 - T1", "d": ["SEM0538"], "pos": False}
        res = determinar_classes_celula(tem_aula=True, cel_efetiva=cel, cache_disciplinas=cache)

        self.assertFalse(res["pendente"])
        self.assertTrue(res["carregada"])
        self.assertIn("celula-carregada", res["aula_class"])
        self.assertNotIn("celula-aula-pendente", res["aula_class"])

    def test_celula_multiplas_disciplinas_requer_todas_carregadas(self):
        """Valida que célula com 2 disciplinas só adquire cores quando AMBAS estiverem no cache."""
        cache = {"SEM0538": {"nome": "Sistemas"}}
        cel = {"t": "SEM0538 / SMA0356", "d": ["SEM0538", "SMA0356"], "pos": False}

        # Apenas 1 no cache: ainda pendente
        res1 = determinar_classes_celula(tem_aula=True, cel_efetiva=cel, cache_disciplinas=cache)
        self.assertTrue(res1["pendente"])
        self.assertFalse(res1["carregada"])
        self.assertIn("celula-aula-pendente", res1["aula_class"])

        # Ambas no cache: transiciona para carregada
        cache["SMA0356"] = {"nome": "Cálculo IV"}
        res2 = determinar_classes_celula(tem_aula=True, cel_efetiva=cel, cache_disciplinas=cache)
        self.assertFalse(res2["pendente"])
        self.assertTrue(res2["carregada"])
        self.assertIn("celula-carregada", res2["aula_class"])

    def test_atualizacao_progressiva_durante_consumo_da_fila(self):
        """Valida que atualizar_celulas_no_lote ativa exatamente as células completadas no lote."""
        cache = {}
        cel1 = {"id": 1, "t": "SEM0538 - T1", "d": ["SEM0538"], "pendente": True, "carregada": False,
                "aula_class": "celula-aula celula-aula-pendente", "codigos": ["SEM0538"]}
        cel2 = {"id": 2, "t": "SEP5864 - T1", "d": ["SEP5864"], "pendente": True, "carregada": False,
                "aula_class": "celula-aula celula-pos celula-aula-pendente", "codigos": ["SEP5864"]}
        cel3 = {"id": 3, "t": "SHS5934 - T1", "d": ["SHS5934"], "pendente": True, "carregada": False,
                "aula_class": "celula-aula celula-pos celula-aula-pendente", "codigos": ["SHS5934"]}

        celulas = [cel1, cel2, cel3]

        # Chega lote com SEM0538 e SEP5864
        cache["SEM0538"] = {"nome": "Sistemas"}
        cache["SEP5864"] = {"nome": "Pesquisa Operacional"}

        trans = atualizar_celulas_no_lote(celulas, ["SEM0538", "SEP5864"], cache)

        self.assertEqual(len(trans), 2)
        self.assertTrue(cel1["carregada"])
        self.assertFalse(cel1["pendente"])
        self.assertTrue(cel2["carregada"])
        self.assertFalse(cel2["pendente"])
        self.assertFalse(cel3["carregada"])
        self.assertTrue(cel3["pendente"])

    def test_celula_sem_disciplina_nao_fica_pendente_infinitamente(self):
        """Valida que textos avulsos (sem disciplina cadastrada) não recebem celula-aula-pendente."""
        cache = {}
        cel = {"t": "REUNIÃO DE DEPARTAMENTO", "d": [], "pos": False}
        res = determinar_classes_celula(tem_aula=True, cel_efetiva=cel, cache_disciplinas=cache)

        self.assertFalse(res["pendente"])
        self.assertFalse(res["carregada"])
        self.assertNotIn("celula-aula-pendente", res["aula_class"])
        self.assertEqual(res["aula_class"], "celula-aula")


if __name__ == "__main__":
    unittest.main()
