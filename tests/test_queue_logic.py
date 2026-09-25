#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários e Property Fuzzing: Máquina de Estados da Fila do Jupiterweb
Valida o gerenciamento de prioridades (0=urgente, 1=visível, 2=oculto),
controle estrito de concorrência (máx 1 lote em voo), deduplicação,
promoção no clique e resiliência a falhas.
"""

import random
import string
import unittest


class GerenciadorFilaJupiter:
    """
    Modelo de referência da Máquina de Estados da Fila de Requisições do Jupiterweb.
    Espelha a lógica JavaScript executada no frontend do cliente.
    """

    def __init__(self, tamanho_lote=3, pausa_ms=250):
        self.tamanho_lote = tamanho_lote
        self.pausa_ms = pausa_ms
        self.cache = {}                 # codigo -> dados
        self.fila = []                  # list of dict: {"codigo": str, "prioridade": int, "ordem": int}
        self.em_voo = False
        self.lote_atual = []            # list of str (códigos em voo)
        self.callbacks_urgentes = set() # códigos que aguardam abertura de modal imediato
        self._contador_ordem = 0

    def esta_em_cache(self, codigo):
        return codigo in self.cache

    def limpar_cache(self):
        """Limpa integralmente o cache local, esvazia a fila e reseta requisições em voo."""
        self.cache.clear()
        self.fila.clear()
        self.callbacks_urgentes.clear()
        self.lote_atual.clear()
        self.em_voo = False
        self._contador_ordem = 0

    def adicionar(self, codigo, prioridade=2):
        """
        Adiciona código à fila se não estiver em cache nem em voo.
        Se já estiver na fila, promove a prioridade se a nova for maior (número menor).
        """
        if not codigo or not isinstance(codigo, str):
            return False

        codigo = codigo.strip().upper()
        if not codigo or self.esta_em_cache(codigo):
            return False

        # Se já está no lote em voo, atualiza urgência se prioridade for 0
        if self.em_voo and codigo in self.lote_atual:
            if prioridade == 0:
                self.callbacks_urgentes.add(codigo)
            return False

        # Verifica se já está na fila
        for item in self.fila:
            if item["codigo"] == codigo:
                if prioridade < item["prioridade"]:
                    item["prioridade"] = prioridade
                    self._reordenar_fila()
                if prioridade == 0:
                    self.callbacks_urgentes.add(codigo)
                return True

        # Novo item
        self._contador_ordem += 1
        self.fila.append({
            "codigo": codigo,
            "prioridade": prioridade,
            "ordem": self._contador_ordem
        })
        if prioridade == 0:
            self.callbacks_urgentes.add(codigo)

        self._reordenar_fila()
        return True

    def promover_urgente(self, codigo):
        """Promove um código para prioridade 0 (urgente - clique do usuário)."""
        return self.adicionar(codigo, prioridade=0)

    def atualizar_visibilidade(self, codigos_visiveis, todos_codigos=None):
        """
        Reavalia prioridades da fila com base nos elementos visíveis na grade.
        Prioridade 0 (urgente) é preservada.
        Visíveis recebem Prioridade 1.
        Ocultos recebem Prioridade 2.
        Novos códigos visíveis são enfileirados automaticamente com Prioridade 1.
        """
        # Preserva a ordem original de inserção
        lista_visiveis = []
        set_visiveis = set()
        for c in (codigos_visiveis or []):
            if c and isinstance(c, str):
                cn = c.strip().upper()
                if cn and cn not in set_visiveis:
                    set_visiveis.add(cn)
                    lista_visiveis.append(cn)

        # Atualiza itens já existentes na fila
        for item in self.fila:
            if item["prioridade"] == 0:
                continue  # Preserva prioridade urgente
            if item["codigo"] in set_visiveis:
                item["prioridade"] = 1
            else:
                item["prioridade"] = 2

        # Adiciona novos códigos visíveis ainda não presentes (preservando ordem)
        for cod in lista_visiveis:
            if not self.esta_em_cache(cod) and not (self.em_voo and cod in self.lote_atual):
                if not any(item["codigo"] == cod for item in self.fila):
                    self._contador_ordem += 1
                    self.fila.append({
                        "codigo": cod,
                        "prioridade": 1,
                        "ordem": self._contador_ordem
                    })

        # Adiciona demais códigos como prioridade 2 se informados (preservando ordem)
        if todos_codigos:
            vistos_todos = set()
            for cod_raw in todos_codigos:
                if not cod_raw or not isinstance(cod_raw, str):
                    continue
                cod = cod_raw.strip().upper()
                if cod and cod not in set_visiveis and cod not in vistos_todos and not self.esta_em_cache(cod):
                    vistos_todos.add(cod)
                    if not (self.em_voo and cod in self.lote_atual):
                        if not any(item["codigo"] == cod for item in self.fila):
                            self._contador_ordem += 1
                            self.fila.append({
                                "codigo": cod,
                                "prioridade": 2,
                                "ordem": self._contador_ordem
                            })

        self._reordenar_fila()

    def _reordenar_fila(self):
        """Ordena fila por prioridade ascendente (0, 1, 2) e depois por ordem de inserção FIFO."""
        self.fila.sort(key=lambda x: (x["prioridade"], x["ordem"]))

    def proximo_lote(self):
        """
        Retorna o próximo lote de até `tamanho_lote` códigos para requisição.
        Se já houver uma requisição em voo ou a fila estiver vazia, retorna None.
        """
        if self.em_voo or not self.fila:
            return None

        tamanho = min(self.tamanho_lote, len(self.fila))
        lote_itens = self.fila[:tamanho]
        self.fila = self.fila[tamanho:]

        self.em_voo = True
        self.lote_atual = [item["codigo"] for item in lote_itens]
        return list(self.lote_atual)

    def concluir_lote(self, respostas_por_codigo):
        """
        Processa retorno bem-sucedido do lote.
        Armazena em cache e libera a flag `em_voo`.
        Retorna lista de códigos que tinham callback urgente pendente.
        """
        if not self.em_voo:
            return []

        urgentes_atendidos = []
        for codigo, dados in respostas_por_codigo.items():
            cod_norm = codigo.strip().upper()
            self.cache[cod_norm] = dados
            if cod_norm in self.callbacks_urgentes:
                urgentes_atendidos.append(cod_norm)
                self.callbacks_urgentes.remove(cod_norm)

        # Se algum código do lote não veio na resposta, re-enfileira como prioridade 2
        for cod_em_voo in self.lote_atual:
            if cod_em_voo not in self.cache:
                self.adicionar(cod_em_voo, prioridade=2)

        self.em_voo = False
        self.lote_atual = []
        return urgentes_atendidos

    def falhar_lote(self, reordenar_no_fim=True):
        """
        Trata erro de rede ou timeout do lote em voo.
        Libera `em_voo` e re-enfileira os itens para não haver perda.
        """
        if not self.em_voo:
            return

        codigos_falhados = list(self.lote_atual)
        self.em_voo = False
        self.lote_atual = []

        if reordenar_no_fim:
            for cod in codigos_falhados:
                if cod not in self.cache:
                    # Se era urgente, mantém prioridade 0 para tentar no próximo ciclo
                    pri = 0 if cod in self.callbacks_urgentes else 2
                    self.adicionar(cod, prioridade=pri)

    def calcular_progresso(self, universo_codigos):
        """
        Calcula o progresso percentual (0 a 100) do carregamento dinâmico
        com base no universo de códigos da grade e no estado da fila/cache.
        Retorna (percentual, em_execucao).
        """
        if not universo_codigos:
            return 0, False

        universo_set = set(c.strip().upper() for c in universo_codigos if c and isinstance(c, str))
        total = len(universo_set)
        if total == 0:
            return 0, False

        concluidas = sum(1 for c in universo_set if c in self.cache)
        em_execucao = len(self.fila) > 0 or self.em_voo

        if concluidas >= total:
            return 100, em_execucao

        if not em_execucao:
            return 0, False

        pct = min(99, int((concluidas / total) * 100))
        return pct, True


class TestQueueLogic(unittest.TestCase):
    """Testes unitários e invariantes da fila de enriquecimento progressivo."""

    def setUp(self):
        self.gerenciador = GerenciadorFilaJupiter(tamanho_lote=3, pausa_ms=250)

    def test_adicao_e_ordenacao_por_prioridade(self):
        """Testa se os itens são consumidos respeitando rigorosamente as prioridades 0, 1 e 2."""
        self.gerenciador.adicionar("DISC_C", prioridade=2)
        self.gerenciador.adicionar("DISC_B", prioridade=1)
        self.gerenciador.adicionar("DISC_A", prioridade=0)

        # A ordem na fila deve ser DISC_A (0), DISC_B (1), DISC_C (2)
        self.assertEqual(
            [item["codigo"] for item in self.gerenciador.fila],
            ["DISC_A", "DISC_B", "DISC_C"]
        )

    def test_preservacao_fifo_mesma_prioridade(self):
        """Testa se itens com a mesma prioridade respeitam a ordem de chegada (FIFO)."""
        self.gerenciador.adicionar("DISC_1", prioridade=1)
        self.gerenciador.adicionar("DISC_2", prioridade=1)
        self.gerenciador.adicionar("DISC_3", prioridade=1)

        lote = self.gerenciador.proximo_lote()
        self.assertEqual(lote, ["DISC_1", "DISC_2", "DISC_3"])

    def test_deduplicacao_e_upgrade_de_prioridade(self):
        """Testa se reinserção com prioridade maior atualiza sem duplicar elemento."""
        self.gerenciador.adicionar("SMA0356", prioridade=2)
        self.gerenciador.adicionar("7600006", prioridade=2)
        self.assertEqual(len(self.gerenciador.fila), 2)

        # Promove SMA0356 para visível (prioridade 1)
        self.gerenciador.adicionar("SMA0356", prioridade=1)
        self.assertEqual(len(self.gerenciador.fila), 2, "Não deve duplicar código na fila")
        self.assertEqual(self.gerenciador.fila[0]["codigo"], "SMA0356")
        self.assertEqual(self.gerenciador.fila[0]["prioridade"], 1)

        # Tentativa de rebaixar prioridade deve ser ignorada
        self.gerenciador.adicionar("SMA0356", prioridade=2)
        self.assertEqual(self.gerenciador.fila[0]["prioridade"], 1, "Prioridade não deve regredir")

    def test_cache_hit_impede_adicao(self):
        """Testa se código já presente no cache é ignorado na adição."""
        self.gerenciador.cache["SMA0356"] = {"turmas": []}
        adicionou = self.gerenciador.adicionar("SMA0356", prioridade=0)
        self.assertFalse(adicionou)
        self.assertEqual(len(self.gerenciador.fila), 0)

    def test_controle_estrito_concorrencia_uma_requisicao_em_voo(self):
        """Garante que nunca ocorrem duas requisições simultâneas em trânsito."""
        self.gerenciador.adicionar("DISC_1", prioridade=1)
        self.gerenciador.adicionar("DISC_2", prioridade=1)
        self.gerenciador.adicionar("DISC_3", prioridade=1)
        self.gerenciador.adicionar("DISC_4", prioridade=1)

        lote1 = self.gerenciador.proximo_lote()
        self.assertEqual(lote1, ["DISC_1", "DISC_2", "DISC_3"])
        self.assertTrue(self.gerenciador.em_voo)

        # Enquanto em_voo == True, proximo_lote deve retornar None
        lote_concorrente = self.gerenciador.proximo_lote()
        self.assertIsNone(lote_concorrente, "Não deve permitir segundo lote em trânsito simultâneo")

        # Conclui o lote 1
        urgentes = self.gerenciador.concluir_lote({
            "DISC_1": {"turmas": []},
            "DISC_2": {"turmas": []},
            "DISC_3": {"turmas": []}
        })
        self.assertFalse(self.gerenciador.em_voo)
        self.assertEqual(urgentes, [])

        # Agora o segundo lote pode ser retirado
        lote2 = self.gerenciador.proximo_lote()
        self.assertEqual(lote2, ["DISC_4"])

    def test_promocao_urgente_no_clique(self):
        """Testa se um clique do usuário promove a disciplina instantaneamente para Prioridade 0."""
        self.gerenciador.adicionar("DISC_1", prioridade=1)
        self.gerenciador.adicionar("DISC_2", prioridade=1)
        self.gerenciador.adicionar("DISC_3", prioridade=2)
        self.gerenciador.adicionar("DISC_4", prioridade=2)

        # Usuário clica em DISC_4 (estava em prioridade 2 no fim da fila)
        self.gerenciador.promover_urgente("DISC_4")

        # DISC_4 deve ir para o início absoluto da fila
        lote = self.gerenciador.proximo_lote()
        self.assertIn("DISC_4", lote)
        self.assertEqual(lote[0], "DISC_4", "Elemento urgente deve ser o primeiro do lote")

        # Conclusão do lote deve sinalizar que o item urgente foi atendido
        urgentes = self.gerenciador.concluir_lote({
            "DISC_4": {"turmas": ["01"]},
            "DISC_1": {"turmas": []},
            "DISC_2": {"turmas": []}
        })
        self.assertIn("DISC_4", urgentes)

    def test_reordenacao_dinamica_ao_mudar_filtros_visibilidade(self):
        """Testa se a troca de filtros na grade reordena a fila dinamicamente."""
        # Estado inicial: DISC_1 e DISC_2 visíveis; DISC_3 e DISC_4 ocultas
        self.gerenciador.atualizar_visibilidade(
            codigos_visiveis=["DISC_1", "DISC_2"],
            todos_codigos=["DISC_1", "DISC_2", "DISC_3", "DISC_4"]
        )
        self.assertEqual(self.gerenciador.fila[0]["codigo"], "DISC_1")
        self.assertEqual(self.gerenciador.fila[1]["codigo"], "DISC_2")

        # Usuário muda o filtro: agora DISC_3 e DISC_4 tornam-se visíveis
        self.gerenciador.atualizar_visibilidade(
            codigos_visiveis=["DISC_3", "DISC_4"]
        )
        # DISC_3 e DISC_4 devem ser promovidas para a frente de DISC_1 e DISC_2
        codigos_ordenados = [item["codigo"] for item in self.gerenciador.fila]
        self.assertEqual(codigos_ordenados[:2], ["DISC_3", "DISC_4"])
        self.assertEqual(codigos_ordenados[2:], ["DISC_1", "DISC_2"])

    def test_tolerancia_e_recuperacao_de_falha_de_rede(self):
        """Testa resiliência se a requisição do lote falhar (ex: timeout do GAS)."""
        self.gerenciador.adicionar("DISC_1", prioridade=1)
        self.gerenciador.adicionar("DISC_2", prioridade=1)

        lote = self.gerenciador.proximo_lote()
        self.assertEqual(lote, ["DISC_1", "DISC_2"])
        self.assertTrue(self.gerenciador.em_voo)

        # Falha na requisição
        self.gerenciador.falhar_lote(reordenar_no_fim=True)
        self.assertFalse(self.gerenciador.em_voo, "Flag em_voo deve ser liberada após falha")

        # Os itens devem ter voltado para a fila para nova tentativa posterior
        codigos_restantes = [item["codigo"] for item in self.gerenciador.fila]
        self.assertIn("DISC_1", codigos_restantes)
        self.assertIn("DISC_2", codigos_restantes)

    def test_limpar_cache_completo(self):
        """Testa se limpar_cache esvazia cache, fila, callbacks e zera requisições em trânsito."""
        self.gerenciador.cache["SMA0356"] = {"turmas": []}
        self.gerenciador.adicionar("SEM0538", prioridade=1)
        self.gerenciador.promover_urgente("7600006")
        self.gerenciador.proximo_lote()

        self.assertTrue(self.gerenciador.em_voo)
        self.assertEqual(len(self.gerenciador.cache), 1)

        # Executa limpeza completa (simulando clique em Atualizar Dados)
        self.gerenciador.limpar_cache()

        self.assertFalse(self.gerenciador.em_voo)
        self.assertEqual(len(self.gerenciador.cache), 0)
        self.assertEqual(len(self.gerenciador.fila), 0)
        self.assertEqual(len(self.gerenciador.callbacks_urgentes), 0)
        self.assertEqual(len(self.gerenciador.lote_atual), 0)

    def test_progresso_carregamento_dinamico(self):
        """Valida a progressão de 0% a 100% durante o ciclo de vida dos lotes."""
        universo = ["DISC_1", "DISC_2", "DISC_3", "DISC_4"]

        # Sem itens enfileirados e sem requisição em voo: em_execucao é False
        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 0)
        self.assertFalse(em_exec)

        # Enfileira as 4 disciplinas
        for c in universo:
            self.gerenciador.adicionar(c, prioridade=1)

        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 0)
        self.assertTrue(em_exec)

        # Despacha lote 1 (3 itens: DISC_1, DISC_2, DISC_3)
        lote1 = self.gerenciador.proximo_lote()
        self.assertEqual(len(lote1), 3)
        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 0)  # Ainda não concluídos
        self.assertTrue(em_exec)

        # Conclui lote 1 (3 de 4 carregados = 75%)
        self.gerenciador.concluir_lote({c: {"ok": True} for c in lote1})
        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 75)
        self.assertTrue(em_exec)  # Ainda resta DISC_4 na fila

        # Despacha lote 2 (1 item: DISC_4)
        lote2 = self.gerenciador.proximo_lote()
        self.assertEqual(lote2, ["DISC_4"])
        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 75)
        self.assertTrue(em_exec)

        # Conclui lote 2 (4 de 4 = 100%)
        self.gerenciador.concluir_lote({"DISC_4": {"ok": True}})
        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 100)
        self.assertFalse(em_exec)

    def test_progresso_com_cache_preexistente(self):
        """Valida que cache preexistente inicia a porcentagem de forma proporcional."""
        universo = ["DISC_A", "DISC_B", "DISC_C", "DISC_D"]
        # Pré-popula 2 de 4 disciplinas
        self.gerenciador.cache["DISC_A"] = {"ok": True}
        self.gerenciador.cache["DISC_B"] = {"ok": True}

        # Enfileira apenas as pendentes
        self.gerenciador.adicionar("DISC_C", prioridade=1)
        self.gerenciador.adicionar("DISC_D", prioridade=1)

        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 50)
        self.assertTrue(em_exec)

    def test_progresso_nunca_exibe_100_com_pendencia(self):
        """Garante que com itens pendentes o percentual não arredonda prematuramente para 100%."""
        universo = [f"D_{i:03d}" for i in range(100)]
        for i in range(99):
            self.gerenciador.cache[f"D_{i:03d}"] = {"ok": True}
        self.gerenciador.adicionar("D_099", prioridade=1)

        pct, em_exec = self.gerenciador.calcular_progresso(universo)
        self.assertEqual(pct, 99)
        self.assertTrue(em_exec)


class TestQueueFuzzing(unittest.TestCase):
    """Teste de Propriedades e Fuzzing Aleatório na Máquina de Estados da Fila."""

    def test_fuzzing_invariantes_da_fila(self):
        """Executa 1.000 operações estocásticas aleatórias e valida as invariantes do sistema."""
        gerenciador = GerenciadorFilaJupiter(tamanho_lote=random.randint(2, 4))
        codigos_universo = [f"DISC_{i:03d}" for i in range(50)]

        for ciclo in range(1000):
            acao = random.choice([
                "adicionar_aleatorio",
                "promover_urgente",
                "atualizar_visibilidade",
                "solicitar_proximo_lote",
                "concluir_lote",
                "falhar_lote"
            ])

            if acao == "adicionar_aleatorio":
                cod = random.choice(codigos_universo)
                pri = random.choice([1, 2])
                gerenciador.adicionar(cod, prioridade=pri)

            elif acao == "promover_urgente":
                cod = random.choice(codigos_universo)
                gerenciador.promover_urgente(cod)

            elif acao == "atualizar_visibilidade":
                amostra = random.sample(codigos_universo, k=random.randint(5, 15))
                gerenciador.atualizar_visibilidade(amostra)

            elif acao == "solicitar_proximo_lote":
                gerenciador.proximo_lote()

            elif acao == "concluir_lote":
                if gerenciador.em_voo:
                    respostas = {cod: {"fuzzed": True} for cod in gerenciador.lote_atual}
                    gerenciador.concluir_lote(respostas)

            elif acao == "falhar_lote":
                if gerenciador.em_voo:
                    gerenciador.falhar_lote()

            # --- Validação de Invariantes ---
            # Invariante 1: em_voo é True se e somente se lote_atual não está vazio
            if gerenciador.em_voo:
                self.assertGreater(len(gerenciador.lote_atual), 0)
                self.assertLessEqual(len(gerenciador.lote_atual), gerenciador.tamanho_lote)
            else:
                self.assertEqual(len(gerenciador.lote_atual), 0)

            # Invariante 2: Sem duplicações na fila
            codigos_na_fila = [item["codigo"] for item in gerenciador.fila]
            self.assertEqual(len(codigos_na_fila), len(set(codigos_na_fila)), "Fila contém códigos duplicados")

            # Invariante 3: Elementos cacheados nunca devem estar na fila
            for cod_f in codigos_na_fila:
                self.assertNotIn(cod_f, gerenciador.cache, f"Código cacheado {cod_f} permaneceu na fila")

            # Invariante 4: Fila está estritamente ordenada por prioridade (não decrescente)
            prioridades = [item["prioridade"] for item in gerenciador.fila]
            for i in range(len(prioridades) - 1):
                self.assertLessEqual(
                    prioridades[i],
                    prioridades[i + 1],
                    f"Prioridades fora de ordem: {prioridades}"
                )


if __name__ == "__main__":
    unittest.main()
