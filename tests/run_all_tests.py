#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orquestrador Central da Suíte de Testes Automatizados — Alocação Plus
Executa todos os testes unitários, testes de propriedades e fuzzing do projeto.
"""

import os
import sys
import time
import unittest

# Ativa suporte a UTF-8 e cores ANSI no console Windows
if sys.platform == "win32":
    os.system("")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

COR_VERDE = "\033[92m"
COR_VERMELHO = "\033[91m"
COR_AMARELO = "\033[93m"
COR_AZUL = "\033[94m"
COR_CIANO = "\033[96m"
COR_NEGRITO = "\033[1m"
COR_RESET = "\033[0m"


class RelatorioTestesColorido(unittest.TextTestResult):
    """Formatador customizado para exibição amigável e colorida dos testes."""

    def startTest(self, test):
        super().startTest(test)
        nome_metodo = test._testMethodName
        doc = test.shortDescription() or nome_metodo
        classe = test.__class__.__name__
        sys.stdout.write(f"  • {COR_CIANO}{classe}{COR_RESET}::{nome_metodo} ({doc})... ")
        sys.stdout.flush()

    def addSuccess(self, test):
        super().addSuccess(test)
        sys.stdout.write(f"{COR_VERDE}OK{COR_RESET}\n")

    def addError(self, test, err):
        super().addError(test, err)
        sys.stdout.write(f"{COR_VERMELHO}ERRO{COR_RESET}\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        sys.stdout.write(f"{COR_VERMELHO}FALHA{COR_RESET}\n")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        sys.stdout.write(f"{COR_AMARELO}IGNORADO ({reason}){COR_RESET}\n")


class RunnerTestesColorido(unittest.TextTestRunner):
    resultclass = RelatorioTestesColorido


def executar_testes(arquivos_alvo=None):
    diretorio_base = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(diretorio_base))

    print(f"\n{COR_NEGRITO}{COR_AZUL}============================================================{COR_RESET}")
    print(f"{COR_NEGRITO}{COR_AZUL}🧪 SUÍTE DE TESTES AUTOMATIZADOS — ALOCAÇÃO PLUS (EESC-USP){COR_RESET}")
    print(f"{COR_NEGRITO}{COR_AZUL}============================================================{COR_RESET}\n")

    loader = unittest.TestLoader()

    if arquivos_alvo:
        suite = unittest.TestSuite()
        for alvo in arquivos_alvo:
            if os.path.isfile(alvo):
                nome_modulo = os.path.splitext(os.path.basename(alvo))[0]
                suite.addTests(loader.loadTestsFromName(f"tests.{nome_modulo}"))
            else:
                suite.addTests(loader.loadTestsFromName(alvo))
    else:
        suite = loader.discover(start_dir=diretorio_base, pattern="test_*.py")

    total_testes = suite.countTestCases()
    if total_testes == 0:
        print(f"{COR_AMARELO}ℹ️ Nenhum teste encontrado em 'tests/test_*.py' ainda.{COR_RESET}")
        print(f"  Diretório de testes e fixtures configurados com sucesso.\n")
        return True

    print(f"📦 Total de testes descobertos: {COR_NEGRITO}{total_testes}{COR_RESET}\n")

    inicio = time.time()
    runner = RunnerTestesColorido(verbosity=0)
    resultado = runner.run(suite)
    duracao = time.time() - inicio

    print(f"\n{COR_NEGRITO}{COR_AZUL}------------------------------------------------------------{COR_RESET}")
    if resultado.wasSuccessful():
        print(f"{COR_NEGRITO}{COR_VERDE}✅ TODOS OS TESTES PASSARAM COM SUCESSO!{COR_RESET}")
    else:
        print(f"{COR_NEGRITO}{COR_VERMELHO}❌ HOUVE FALHAS OU ERROS NA EXECUÇÃO!{COR_RESET}")

    print(f"⏱️  Tempo total: {duracao:.2f}s")
    print(f"📊 Executados: {resultado.testsRun} | Falhas: {len(resultado.failures)} | Erros: {len(resultado.errors)} | Ignorados: {len(resultado.skipped)}")
    print(f"{COR_NEGRITO}{COR_AZUL}============================================================{COR_RESET}\n")

    return resultado.wasSuccessful()


if __name__ == "__main__":
    argumentos = sys.argv[1:]
    sucesso = executar_testes(argumentos if argumentos else None)
    sys.exit(0 if sucesso else 1)
