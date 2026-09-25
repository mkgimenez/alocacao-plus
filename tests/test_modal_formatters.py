#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários: Formatador de Alunos / Vagas do Modal da Grade Horária
Valida o comportamento do frontend para turmas de Graduação e Pós-Graduação,
garantindo proteção rigorosa contra o bug do 0 falsy e fallbacks adequados.
"""

import re
import unittest


def formatar_dados_alunos_modal(dados, turma_obj, codigo_ativo=""):
    """
    Função de referência espelhando exatamente a lógica de frontend em scripts.html.
    """
    eh_pos = (
        (dados and dados.get("sistema") == "janus")
        or bool(re.match(r"^[A-Za-z]{3}[1-9]\d{3}$", (dados.get("codigo") if dados else "") or codigo_ativo))
    )

    if eh_pos:
        titulo = "👥 Número de Vagas"
        tem_vagas = turma_obj.get("vagas") is not None if turma_obj else False
        valor = str(turma_obj["vagas"]) if tem_vagas else "Não informado"
    else:
        titulo = "👥 Alunos Matriculados"
        tem_matr = turma_obj.get("matriculados") is not None if turma_obj else False
        valor = str(turma_obj["matriculados"]) if tem_matr else "Não informado"

    return titulo, valor


class TestModalFormatters(unittest.TestCase):
    """Valida formatação e textos de alunos matriculados e vagas no modal."""

    def test_graduacao_com_matriculados_positivo(self):
        """Valida disciplina de graduação com alunos matriculados > 0."""
        dados = {"codigo": "SMA0356", "sistema": "jupiter"}
        turma = {"numero": "01", "matriculados": 67}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Alunos Matriculados")
        self.assertEqual(valor, "67")

    def test_graduacao_com_zero_matriculados_protecao_falsy(self):
        """Garante que 0 alunos matriculados exibe '0' e NÃO 'Não informado'."""
        dados = {"codigo": "SMA0356", "sistema": "jupiter"}
        turma = {"numero": "02", "matriculados": 0}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Alunos Matriculados")
        self.assertEqual(valor, "0")

    def test_graduacao_sem_tabela_matriculados_fallback(self):
        """Valida que quando matriculados é None, exibe 'Não informado'."""
        dados = {"codigo": "SMA0356", "sistema": "jupiter"}
        turma = {"numero": "03", "matriculados": None}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Alunos Matriculados")
        self.assertEqual(valor, "Não informado")

    def test_graduacao_chave_inexistente_fallback(self):
        """Valida fallback se o campo matriculados não estiver presente no objeto."""
        dados = {"codigo": "7600006", "sistema": "jupiter"}
        turma = {"numero": "01"}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Alunos Matriculados")
        self.assertEqual(valor, "Não informado")

    def test_pos_graduacao_por_sistema_com_vagas(self):
        """Valida disciplina de pós via sistema=='janus'."""
        dados = {"codigo": "SEP5864", "sistema": "janus"}
        turma = {"numero": "01", "vagas": 25}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Número de Vagas")
        self.assertEqual(valor, "25")

    def test_pos_graduacao_por_regex_sigla(self):
        """Valida identificação de pós pela sigla Janus (ex: SHS5934)."""
        dados = {"codigo": "SHS5934"}
        turma = {"numero": "04", "vagas": 25}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Número de Vagas")
        self.assertEqual(valor, "25")

    def test_pos_graduacao_zero_vagas_protecao_falsy(self):
        """Garante que 0 vagas na pós exibe '0' e NÃO 'Não informado'."""
        dados = {"codigo": "SEM5900", "sistema": "janus"}
        turma = {"numero": "01", "vagas": 0}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Número de Vagas")
        self.assertEqual(valor, "0")

    def test_pos_graduacao_sem_vagas_fallback(self):
        """Valida que quando vagas é None, exibe 'Não informado'."""
        dados = {"codigo": "SEM5900", "sistema": "janus"}
        turma = {"numero": "01", "vagas": None}
        titulo, valor = formatar_dados_alunos_modal(dados, turma)
        self.assertEqual(titulo, "👥 Número de Vagas")
        self.assertEqual(valor, "Não informado")


if __name__ == "__main__":
    unittest.main()
