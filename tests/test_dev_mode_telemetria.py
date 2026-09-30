#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testes Unitários: Modo Desenvolvedor e Exclusão de Telemetria/Estatísticas (?dev=1)
Valida:
 1. Ativação via parâmetro de URL (?dev=1 ou ?dev=true) gravando no localStorage
 2. Desativação via parâmetro de URL (?dev=0 ou ?dev=false) limpando o localStorage
 3. Persistência do estado salvo no localStorage quando nenhum parâmetro é passado
 4. Supressão rigorosa de pings de telemetria quando o modo dev está ativo
 5. Proteção de retaguarda no backend (registrarAcessoWeb) para payloads marcados
"""

import unittest


class MockLocalStorage:
    def __init__(self, initial_data=None):
        self.store = dict(initial_data or {})

    def getItem(self, key):
        return self.store.get(key, None)

    def setItem(self, key, value):
        self.store[key] = str(value)

    def removeItem(self, key):
        self.store.pop(key, None)

    def clear(self):
        self.store.clear()


def simular_configurar_modo_dev(param_dev=None, url_search_dev=None, local_storage=None):
    """
    Simula com rigor a função configurarModoDesenvolvedor() de scripts.html.
    Retorna (ativo: bool, toast_tipo: str ou None, toast_titulo: str ou None).
    """
    chave_ignorar = "alocacao_plus_ignorar_telemetria"
    if local_storage is None:
        local_storage = MockLocalStorage()

    param = None
    if param_dev is not None:
        param = str(param_dev).strip()
    elif url_search_dev is not None:
        param = str(url_search_dev).strip()

    toast_info = None

    if param is not None:
        dev_lower = param.lower()
        if dev_lower in ("1", "true"):
            ja_estava_ativo = local_storage.getItem(chave_ignorar) == "true"
            local_storage.setItem(chave_ignorar, "true")
            if not ja_estava_ativo:
                toast_info = ("info", "Modo Desenvolvedor Ativado 🛠️")
        elif dev_lower in ("0", "false"):
            estava_ativo = local_storage.getItem(chave_ignorar) == "true"
            local_storage.removeItem(chave_ignorar)
            if estava_ativo:
                toast_info = ("sucesso", "Modo Desenvolvedor Desativado 📊")

    ativo = local_storage.getItem(chave_ignorar) == "true"
    return ativo, toast_info


def simular_registrar_acesso_silencioso(local_storage, google_env=True, ultimo_ping_ms=None, agora_ms=1000000):
    """
    Simula com precisão registrarAcessoSilencioso() de scripts.html.
    Retorna True se enviou a requisição backend, False se foi bloqueado/abortado.
    """
    chave_ignorar = "alocacao_plus_ignorar_telemetria"

    # 1. Checagem prioritária do modo desenvolvedor
    if local_storage.getItem(chave_ignorar) == "true":
        return False, "bloqueado_modo_dev"

    # 2. Ambiente Google
    if not google_env:
        return False, "fora_ambiente_google"

    # 3. Throttle de sessão (15 min)
    if ultimo_ping_ms is not None and (agora_ms - ultimo_ping_ms < 15 * 60 * 1000):
        return False, "throttle_sessao"

    return True, "enviado"


def simular_backend_registrar_acesso(payload):
    """Simula registrarAcessoWeb(payload) em alocacao-plus.gs."""
    if payload and (payload.get("isDev") or payload.get("ignorar")):
        return {"sucesso": True, "ignorado": True, "motivo": "modo_dev"}
    return {"sucesso": True, "gravado": True}


class TestModoDesenvolvedorTelemetria(unittest.TestCase):
    """Conjunto de testes unitários para a ativação e supressão de telemetria."""

    def test_ativacao_modo_dev_com_1(self):
        """Valida ativação via ?dev=1 e emissão de notificação Toast."""
        storage = MockLocalStorage()
        ativo, toast = simular_configurar_modo_dev(param_dev="1", local_storage=storage)
        self.assertTrue(ativo)
        self.assertEqual(storage.getItem("alocacao_plus_ignorar_telemetria"), "true")
        self.assertIsNotNone(toast)
        self.assertEqual(toast[0], "info")
        self.assertIn("Modo Desenvolvedor Ativado", toast[1])

    def test_ativacao_modo_dev_com_true(self):
        """Valida ativação alternativa via ?dev=true."""
        storage = MockLocalStorage()
        ativo, toast = simular_configurar_modo_dev(param_dev="true", local_storage=storage)
        self.assertTrue(ativo)
        self.assertEqual(storage.getItem("alocacao_plus_ignorar_telemetria"), "true")
        self.assertIsNotNone(toast)

    def test_desativacao_modo_dev_com_0(self):
        """Valida que ?dev=0 remove o flag e exibe Toast de reativação."""
        storage = MockLocalStorage({"alocacao_plus_ignorar_telemetria": "true"})
        ativo, toast = simular_configurar_modo_dev(param_dev="0", local_storage=storage)
        self.assertFalse(ativo)
        self.assertIsNone(storage.getItem("alocacao_plus_ignorar_telemetria"))
        self.assertIsNotNone(toast)
        self.assertEqual(toast[0], "sucesso")
        self.assertIn("Desativado", toast[1])

    def test_desativacao_modo_dev_com_false(self):
        """Valida que ?dev=false remove o flag."""
        storage = MockLocalStorage({"alocacao_plus_ignorar_telemetria": "true"})
        ativo, toast = simular_configurar_modo_dev(param_dev="false", local_storage=storage)
        self.assertFalse(ativo)
        self.assertIsNone(storage.getItem("alocacao_plus_ignorar_telemetria"))

    def test_persistencia_sem_parametro_na_url(self):
        """Valida que acessos subsequentes sem nenhum parâmetro continuam com telemetria desativada."""
        storage = MockLocalStorage({"alocacao_plus_ignorar_telemetria": "true"})
        ativo, toast = simular_configurar_modo_dev(param_dev=None, url_search_dev=None, local_storage=storage)
        self.assertTrue(ativo)
        self.assertIsNone(toast)  # Não reexibe toast em acessos normais para não incomodar

    def test_supressao_de_ping_em_modo_dev(self):
        """Garante que com o modo dev ativo, nenhum ping de telemetria é enviado ao Google Apps Script."""
        storage = MockLocalStorage({"alocacao_plus_ignorar_telemetria": "true"})
        enviou, motivo = simular_registrar_acesso_silencioso(storage, google_env=True)
        self.assertFalse(enviou)
        self.assertEqual(motivo, "bloqueado_modo_dev")

    def test_envio_normal_quando_modo_dev_desativado(self):
        """Garante que usuários comuns continuam sendo contabilizados perfeitamente."""
        storage = MockLocalStorage()  # sem a chave
        enviou, motivo = simular_registrar_acesso_silencioso(storage, google_env=True)
        self.assertTrue(enviou)
        self.assertEqual(motivo, "enviado")

    def test_protecao_backend_registrar_acesso(self):
        """Valida a camada de defesa em profundidade no backend registrarAcessoWeb."""
        resp_dev = simular_backend_registrar_acesso({"isDev": True})
        self.assertTrue(resp_dev["sucesso"])
        self.assertTrue(resp_dev["ignorado"])
        self.assertEqual(resp_dev["motivo"], "modo_dev")

        resp_normal = simular_backend_registrar_acesso({"dispositivo": "Desktop"})
        self.assertTrue(resp_normal["sucesso"])
        self.assertTrue(resp_normal["gravado"])


if __name__ == "__main__":
    unittest.main()
