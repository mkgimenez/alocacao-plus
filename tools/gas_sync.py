#!/usr/bin/env python3
"""
gas_sync.py - Sincronizador Automático do Alocação Plus com o Google Apps Script
Utiliza a Google Apps Script REST API v1 para push, pull, monitoramento (watch) e controle de versão.

Uso:
    python tools/gas_sync.py push              # Envia arquivos de src/ para o Apps Script
    python tools/gas_sync.py pull              # Baixa arquivos do Apps Script para src/
    python tools/gas_sync.py watch             # Monitora src/ e sincroniza automaticamente a cada Ctrl+S (incrementa build)
    python tools/gas_sync.py bump [patch|minor|major|<versao>]  # Promove versão e reseta build (ex: bump patch)
    python tools/gas_sync.py build             # Incrementa manualmente o número de build
    python tools/gas_sync.py version           # Exibe informações da versão e build atuais
    python tools/gas_sync.py idea "Sua ideia"  # Anota rapidamente uma ideia/tarefa na Inbox do BACKLOG.md
    python tools/gas_sync.py status            # Exibe informações do projeto no Apps Script
    python tools/gas_sync.py init <SCRIPT_ID>  # Configura o Script ID do projeto
"""

import os
import sys
import time
import json
import hashlib
import argparse
from pathlib import Path

# Garante suporte seguro a UTF-8 e emojis no terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError as e:
    print(f"❌ Erro ao importar bibliotecas Google: {e}")
    print("Execute: pip install google-api-python-client google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

# Diretórios e arquivos base
ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT_DIR / "src"
CONFIG_FILE = ROOT_DIR / ".gas-config.json"
CLASP_FILE = ROOT_DIR / ".clasp.json"
TOKEN_FILE = ROOT_DIR / "token_gas.json"
VERSION_FILE = ROOT_DIR / "version.json"
SRC_VERSION_FILE = SRC_DIR / "version.gs"
BACKLOG_FILE = ROOT_DIR / "BACKLOG.md"
CREDENTIALS_FILES = [
    ROOT_DIR / "credentials.json",
    ROOT_DIR / "tools" / "credentials.json"
]

# Escopos da API do Google Apps Script
SCOPES = [
    'https://www.googleapis.com/auth/script.projects',
    'https://www.googleapis.com/auth/script.deployments'
]


# ==============================================================================
# GESTÃO DE VERSÃO E COMPILAÇÃO (SemVer + Build Automático)
# ==============================================================================

def carregar_versao():
    """Lê version.json na raiz do projeto ou cria estrutura padrão caso inexistente."""
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Aviso ao ler '{VERSION_FILE.name}': {e}")

    # Padrão inicial caso não exista
    dados = {
        "major": 0,
        "minor": 1,
        "patch": 3,
        "build": 0,
        "version": "v0.1.3",
        "full_version": "v0.1.3 (build 0)",
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    salvar_versao(dados)
    return dados


def salvar_versao(dados):
    """Grava as informações de versão no version.json da raiz."""
    try:
        with open(VERSION_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except Exception as e:
        print(f"⚠️  Erro ao salvar '{VERSION_FILE.name}': {e}")


def gerar_version_gs(dados):
    """Gera o arquivo src/version.gs com as constantes globais do Google Apps Script."""
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    hora_formatada = time.strftime("%d/%m/%Y %H:%M")
    versao = dados.get("version", "v0.1.3")
    build_num = dados.get("build", 0)
    full = dados.get("full_version", f"{versao} (build {build_num})")

    conteudo = f"""/**
 * version.gs - Informações de Versão e Compilação do Alocação Plus
 * Arquivo gerado automaticamente pelo gas_sync.py - Não edite manualmente.
 */

const APP_VERSION = '{versao}';
const APP_BUILD = {build_num};
const APP_BUILD_TIME = '{hora_formatada}';
const APP_FULL_VERSION = '{full}';
"""
    try:
        with open(SRC_VERSION_FILE, "w", encoding="utf-8") as f:
            f.write(conteudo)
    except Exception as e:
        print(f"⚠️  Erro ao gerar '{SRC_VERSION_FILE.name}': {e}")


def incrementar_build():
    """Incrementa o contador de build a cada alteração do watch e atualiza os arquivos."""
    dados = carregar_versao()
    dados["build"] = int(dados.get("build", 0)) + 1
    dados["full_version"] = f"{dados['version']} (build {dados['build']})"
    dados["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    salvar_versao(dados)
    gerar_version_gs(dados)
    return dados


def executar_bump(tipo="patch"):
    """
    Promove a versão semântica e reseta o contador de build para 0.
    Suporta: patch, minor, major ou string explícita (ex: 0.2.0 ou v0.2.0).
    """
    dados = carregar_versao()
    tipo_str = str(tipo or "patch").strip().lower()

    if tipo_str == "patch":
        dados["patch"] = int(dados.get("patch", 0)) + 1
        dados["build"] = 0
    elif tipo_str == "minor":
        dados["minor"] = int(dados.get("minor", 0)) + 1
        dados["patch"] = 0
        dados["build"] = 0
    elif tipo_str == "major":
        dados["major"] = int(dados.get("major", 0)) + 1
        dados["minor"] = 0
        dados["patch"] = 0
        dados["build"] = 0
    else:
        # Tenta interpretar versão numérica direta (ex: 0.2.0 ou v0.2.0)
        limpa = tipo_str.lstrip("v")
        partes = limpa.split(".")
        if len(partes) == 3 and all(p.isdigit() for p in partes):
            dados["major"] = int(partes[0])
            dados["minor"] = int(partes[1])
            dados["patch"] = int(partes[2])
            dados["build"] = 0
        elif len(partes) == 2 and all(p.isdigit() for p in partes):
            dados["major"] = int(partes[0])
            dados["minor"] = int(partes[1])
            dados["patch"] = 0
            dados["build"] = 0
        else:
            print(f"❌ Formato de versão inválido: '{tipo}'")
            print("💡 Use: patch, minor, major ou X.Y.Z (ex: python tools/gas_sync.py bump 0.2.0)")
            return None

    dados["version"] = f"v{dados['major']}.{dados['minor']}.{dados['patch']}"
    dados["full_version"] = f"{dados['version']} (build {dados['build']})"
    dados["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")

    salvar_versao(dados)
    gerar_version_gs(dados)

    print("\n" + "=" * 60)
    print("🚀 VERSÃO PROMOVIDA COM SUCESSO!")
    print("=" * 60)
    print(f"🏷️  Nova Versão:      {dados['version']}")
    print(f"🔨 Contador de Build: {dados['build']} (resetado)")
    print(f"📋 Versão Completa:  {dados['full_version']}")
    print(f"📁 Arquivo salvo:    {VERSION_FILE.name}")
    print(f"📄 Arquivo gerado:   src/{SRC_VERSION_FILE.name}")
    print("=" * 60)
    print("💡 A nova versão será enviada ao Apps Script na próxima sincronização (push ou watch).\n")
    return dados


def mostrar_versao():
    """Exibe no terminal a versão e build atuais."""
    dados = carregar_versao()
    print("\n" + "=" * 55)
    print("📦 INFORMAÇÕES DE VERSÃO — ALOCAÇÃO PLUS")
    print("=" * 55)
    print(f"🏷️  Versão Base:     {dados.get('version', 'N/D')}")
    print(f"🔨 Build Atual:     {dados.get('build', 0)}")
    print(f"📋 Versão Completa: {dados.get('full_version', 'N/D')}")
    print(f"🕒 Última alteração:{dados.get('last_updated', 'N/D')}")
    print("=" * 55 + "\n")


def adicionar_ideia_backlog(texto=None):
    """Adiciona uma ideia ou anotação rápida de 1 sentença na Inbox do BACKLOG.md."""
    if not BACKLOG_FILE.exists():
        print(f"❌ Arquivo '{BACKLOG_FILE.name}' não encontrado na raiz do projeto.")
        return

    if not texto:
        print("\n💡 Adicionar Ideia ao Backlog (1 sentença):")
        try:
            texto = input("> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada.")
            return

    texto = (texto or "").strip()
    if not texto:
        print("⚠️  Nenhuma ideia informada. Operação cancelada.")
        return

    # Remove marcadores duplicados caso o usuário tenha digitado "- [ ] " ou "- "
    if texto.startswith("- [ ] "):
        texto = texto[6:].strip()
    elif texto.startswith("- "):
        texto = texto[2:].strip()

    nova_linha = f"- [ ] {texto}\n"

    try:
        conteudo = BACKLOG_FILE.read_text(encoding="utf-8")
        marcador = "## 📥 Inbox (Captura Rápida)"

        if marcador in conteudo:
            partes = conteudo.split(marcador, 1)
            cabecalho = partes[0] + marcador
            resto = partes[1]

            # Encontra onde termina eventual bloco de comentário <!-- ... -->
            idx_inicio_corpo = 0
            if "-->" in resto:
                idx_inicio_corpo = resto.find("-->") + 3

            bloco_comentario = resto[:idx_inicio_corpo]
            depois = resto[idx_inicio_corpo:].lstrip("\r\n")

            # Limpa placeholder vazio se existir
            if depois.startswith("- [ ] \n") or depois.startswith("- [ ]\r\n"):
                depois = depois.split("\n", 1)[1]
            elif depois.strip() == "- [ ]":
                depois = ""

            novo_conteudo = f"{cabecalho}{bloco_comentario}\n\n{nova_linha}{depois}"
            BACKLOG_FILE.write_text(novo_conteudo, encoding="utf-8")
        else:
            with open(BACKLOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n{nova_linha}")

        print("\n" + "=" * 60)
        print("✨ IDEIA ADICIONADA À INBOX DO BACKLOG COM SUCESSO!")
        print("=" * 60)
        print(f"📝 Anotação: {nova_linha.strip()}")
        print(f"📁 Arquivo:  {BACKLOG_FILE.name}")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"❌ Erro ao atualizar '{BACKLOG_FILE.name}': {e}")



def imprimir_instrucoes_credentials():
    """Exibe instruções amigáveis caso o credentials.json não seja encontrado."""
    print("\n" + "=" * 70)
    print("⚠️  ARQUIVO 'credentials.json' NÃO ENCONTRADO")
    print("=" * 70)
    print("""
Para sincronizar com o Google Apps Script via API, o Google exige um arquivo
OAuth 2.0 Client ID (gratuito) da sua conta Google Cloud:

1. Acesse o Google Cloud Console:
   👉 https://console.cloud.google.com/

2. Crie ou selecione um projeto (ex: 'Alocacao Plus EESC').

3. No menu lateral, acesse 'APIs e Serviços' > 'Biblioteca':
   - Pesquise por 'Google Apps Script API' e clique em ATIVAR.

4. Em 'Tela de permissão OAuth' (menu esquerdo):
   - Escolha 'Externo' (ou Interno se possuir Google Workspace USP).
   - Preencha o nome do app e seu e-mail.

5. Em 'Credenciais' (menu esquerdo):
   - Clique em '+ CRIAR CREDENCIAIS' > 'ID do cliente OAuth'.
   - Tipo de aplicativo: 'Aplicativo para computador' (Desktop App).
   - Nome: 'Alocacao Plus Sync'.
   - Clique em Criar e faça o DOWNLOAD do arquivo JSON.

6. Renomeie o arquivo baixado para 'credentials.json' e salve em:
   📂 {}

7. Certifique-se de que a API do Apps Script está ATIVADA na sua conta:
   👉 https://script.google.com/home/usersettings
""".format(ROOT_DIR / "credentials.json"))
    print("=" * 70 + "\n")


def obter_caminho_credentials():
    """Localiza o arquivo credentials.json ou client_secret_*.json."""
    for cand in CREDENTIALS_FILES:
        if cand.exists():
            return cand

    # Procura arquivos client_secret_*.json
    for path in [ROOT_DIR, ROOT_DIR / "tools"]:
        for f in path.glob("client_secret*.json"):
            return f
    return None


def obter_script_id():
    """Recupera o Script ID a partir de .gas-config.json, .clasp.json ou variável de ambiente."""
    env_id = os.environ.get("GAS_SCRIPT_ID")
    if env_id:
        return env_id.strip()

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("scriptId"):
                    return data["scriptId"].strip()
        except Exception:
            pass

    if CLASP_FILE.exists():
        try:
            with open(CLASP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("scriptId"):
                    return data["scriptId"].strip()
        except Exception:
            pass

    return None


def salvar_script_id(script_id):
    """Salva o script_id no arquivo de configuração local."""
    data = {"scriptId": script_id.strip(), "rootDir": "./src"}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Script ID salvo com sucesso em '{CONFIG_FILE.name}'!")


def autenticar():
    """Realiza autenticação OAuth 2.0 e retorna o client autenticado."""
    creds = None
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            print(f"⚠️  Aviso ao ler token existente: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("🔄 Renovando token OAuth...")
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️  Falha ao renovar token: {e}")
                creds = None

        if not creds:
            cred_path = obter_caminho_credentials()
            if not cred_path:
                imprimir_instrucoes_credentials()
                return None

            print("\n" + "=" * 68)
            print("🔑 AUTENTICAÇÃO GOOGLE OAUTH 2.0")
            print("=" * 68)
            print("1. Seu navegador será aberto automaticamente na página de login do Google.")
            print("2. Selecione sua conta e autorize as permissões solicitadas.")
            print("👉 IMPORTANTE: NÃO feche esta janela e NÃO pressione Ctrl+C!")
            print("   O terminal precisa continuar rodando até receber a resposta do Google.")
            print("=" * 68 + "\n")

            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            try:
                creds = flow.run_local_server(
                    port=0,
                    open_browser=True,
                    authorization_prompt_message="Acesse o link abaixo caso o navegador não abra automaticamente:\n{url}\n"
                )
            except KeyboardInterrupt:
                print("\n\n⚠️ O servidor local foi interrompido.")
                print("Se você já concluiu o login no navegador e viu a tela 'Não consigo chegar a esta página':")
                print("👉 Copie a URL completa da barra de endereços do seu navegador (começa com http://localhost...)")
                url_colada = input("Cole a URL aqui (ou tecle Enter para cancelar): ").strip()
                if url_colada and "code=" in url_colada:
                    try:
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(url_colada)
                        code = parse_qs(parsed.query).get('code', [None])[0]
                        if code:
                            flow.redirect_uri = f"http://localhost:{parsed.port}/"
                            flow.fetch_token(code=code)
                            creds = flow.credentials
                            print("✅ Autorização recuperada com sucesso!")
                    except Exception as ex_token:
                        print(f"❌ Não foi possível extrair o token: {ex_token}")
                        return None
                else:
                    return None
            except Exception as e:
                print(f"❌ Erro na autenticação: {e}")
                return None

        if creds:
            with open(TOKEN_FILE, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
            print(f"💾 Token salvo com sucesso em '{TOKEN_FILE.name}'.")

    return creds


def carregar_arquivos_locais():
    """Lê os arquivos de src/ e converte no formato aceito pelo Google Apps Script."""
    if not SRC_DIR.exists():
        print(f"❌ Diretório 'src/' não encontrado em {SRC_DIR}")
        return []

    # Garante que o arquivo version.gs existe antes da sincronização
    if not SRC_VERSION_FILE.exists():
        gerar_version_gs(carregar_versao())

    files_payload = []
    
    # 1. Manifesto obrigatório appsscript.json
    manifest_path = SRC_DIR / "appsscript.json"
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            files_payload.append({
                "name": "appsscript",
                "type": "JSON",
                "source": f.read()
            })
    else:
        print("⚠️  Aviso: 'src/appsscript.json' não encontrado. Usando manifesto padrão.")
        manifest_default = {
            "timeZone": "America/Sao_Paulo",
            "dependencies": {},
            "exceptionLogging": "STACKDRIVER",
            "runtimeVersion": "V8"
        }
        files_payload.append({
            "name": "appsscript",
            "type": "JSON",
            "source": json.dumps(manifest_default, indent=2)
        })

    # 2. Arquivos .gs e .html
    for file_path in sorted(SRC_DIR.iterdir()):
        if file_path.is_file() and file_path.name != "appsscript.json":
            stem = file_path.stem
            ext = file_path.suffix.lower()

            if ext == ".gs" or ext == ".js":
                file_type = "SERVER_JS"
            elif ext == ".html":
                file_type = "HTML"
            else:
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            files_payload.append({
                "name": stem,
                "type": file_type,
                "source": content
            })

    return files_payload


def converter_arquivo_para_payload(caminho_ou_nome):
    """Converte um arquivo local em objeto File esperado pela API do Apps Script."""
    p = Path(caminho_ou_nome)
    if not p.is_file():
        p_src = SRC_DIR / p.name
        if p_src.is_file():
            p = p_src
        else:
            for ext in [".gs", ".html", ".json", ".js"]:
                cand = SRC_DIR / f"{p.name}{ext}"
                if cand.is_file():
                    p = cand
                    break

    if not p.is_file():
        return None

    name = p.stem
    ext = p.suffix.lower()

    if p.name == "appsscript.json":
        ftype = "JSON"
        name = "appsscript"
    elif ext in [".gs", ".js"]:
        ftype = "SERVER_JS"
    elif ext == ".html":
        ftype = "HTML"
    else:
        return None

    try:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
        return {"name": name, "type": ftype, "source": content}
    except Exception as e:
        print(f"⚠️  Erro ao ler '{p.name}': {e}")
        return None


def push(service, script_id, arquivos_especificos=None, cache_remoto=None):
    """
    Envia arquivos para o Google Apps Script.
    Se 'arquivos_especificos' for fornecido, atualiza APENAS esses arquivos no Apps Script,
    preservando os demais arquivos remotos inalterados.
    """
    hora_agora = time.strftime("%H:%M:%S")

    # Caso 1: Envio seletivo / diferencial (apenas os arquivos alterados)
    if arquivos_especificos:
        if isinstance(arquivos_especificos, (str, Path)):
            arquivos_especificos = [arquivos_especificos]

        nomes_formatados = [Path(a).name for a in arquivos_especificos]
        nomes_str = ", ".join(nomes_formatados)
        print(f"[{hora_agora}] 🚀 Atualizando no Apps Script: {nomes_str}...")

        # Obtém arquivos remotos atuais (do cache_remoto em memória se disponível, ou busca da API)
        if cache_remoto is not None and isinstance(cache_remoto, list) and len(cache_remoto) > 0:
            lista_arquivos = cache_remoto
        else:
            try:
                res = service.projects().getContent(scriptId=script_id).execute()
                lista_arquivos = res.get("files", [])
            except Exception as e:
                print(f"⚠️  Aviso ao consultar arquivos remotos: {e}. Usando arquivos locais.")
                lista_arquivos = carregar_arquivos_locais()

        atualizados_sucesso = []
        for item in arquivos_especificos:
            payload_item = converter_arquivo_para_payload(item)
            if payload_item:
                encontrado = False
                for idx, rem in enumerate(lista_arquivos):
                    if rem.get("name") == payload_item["name"]:
                        lista_arquivos[idx] = payload_item
                        encontrado = True
                        break
                if not encontrado:
                    lista_arquivos.append(payload_item)
                atualizados_sucesso.append(payload_item["name"])

        if not atualizados_sucesso:
            print("⚠️  Nenhum arquivo válido encontrado para atualizar.")
            return False

        try:
            body = {"files": lista_arquivos}
            service.projects().updateContent(scriptId=script_id, body=body).execute()
            hora_fim = time.strftime("%H:%M:%S")
            print(f"[{hora_fim}] ✅ Atualizado com sucesso no Apps Script:")
            for a in atualizados_sucesso:
                print(f"   📝 {a}")
            return True
        except HttpError as error:
            print(f"❌ Erro HTTP ao atualizar conteúdo no Apps Script: {error}")
            if error.resp.status == 403:
                print("💡 Verifique se a API do Apps Script está ATIVADA em: https://script.google.com/home/usersettings")
            elif error.resp.status == 404:
                print(f"💡 Script ID '{script_id}' não encontrado ou sem permissão de acesso.")
            return False
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return False

    # Caso 2: Envio completo de todos os arquivos de src/
    files = carregar_arquivos_locais()
    if not files:
        print("❌ Nenhum arquivo encontrado para envio.")
        return False

    nomes_arquivos = [f"{f['name']} ({f['type']})" for f in files]
    print(f"[{hora_agora}] 🚀 Enviando {len(files)} arquivos para o Apps Script ({script_id})...")

    try:
        body = {"files": files}
        result = service.projects().updateContent(scriptId=script_id, body=body).execute()
        hora_fim = time.strftime("%H:%M:%S")
        print(f"[{hora_fim}] ✅ Sincronizado com sucesso! ({len(result.get('files', []))} arquivos em nuvem)")
        for n in nomes_arquivos:
            print(f"   • {n}")
        return True
    except HttpError as error:
        print(f"❌ Erro HTTP ao atualizar conteúdo no Apps Script: {error}")
        if error.resp.status == 403:
            print("💡 Verifique se a API do Apps Script está ATIVADA em: https://script.google.com/home/usersettings")
        elif error.resp.status == 404:
            print(f"💡 Script ID '{script_id}' não encontrado ou sem permissão de acesso.")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def pull(service, script_id):
    """Baixa o conteúdo do Apps Script e atualiza os arquivos em src/."""
    hora_agora = time.strftime("%H:%M:%S")
    print(f"[{hora_agora}] 📥 Baixando arquivos do Apps Script ({script_id})...")
    SRC_DIR.mkdir(parents=True, exist_ok=True)

    try:
        content = service.projects().getContent(scriptId=script_id).execute()
        files = content.get("files", [])
        if not files:
            print("⚠️  Nenhum arquivo retornado do projeto remoto.")
            return False

        for f in files:
            name = f.get("name")
            ftype = f.get("type")
            source = f.get("source", "")

            if ftype == "JSON" and name == "appsscript":
                target = SRC_DIR / "appsscript.json"
            elif ftype == "SERVER_JS":
                target = SRC_DIR / f"{name}.gs"
            elif ftype == "HTML":
                target = SRC_DIR / f"{name}.html"
            else:
                target = SRC_DIR / f"{name}.txt"

            with open(target, "w", encoding="utf-8") as out:
                out.write(source)
            print(f"   ✓ Salvo: src/{target.name} ({ftype})")

        print("✅ Pull concluído com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro no pull: {e}")
        return False


def status(service, script_id):
    """Exibe informações sobre o projeto vinculado no Google Apps Script."""
    print(f"\n🔍 Consultando projeto '{script_id}'...")
    try:
        proj = service.projects().get(scriptId=script_id).execute()
        content = service.projects().getContent(scriptId=script_id).execute()
        files = content.get("files", [])

        print("=" * 60)
        print(f"📋 Título do Projeto: {proj.get('title', 'N/D')}")
        print(f"🆔 Script ID:        {proj.get('scriptId')}")
        print(f"📅 Criado em:        {proj.get('createTime', 'N/D')}")
        print(f"🕒 Última alteração: {proj.get('updateTime', 'N/D')}")
        print(f"📦 Total de Arquivos:{len(files)}")
        print("-" * 60)
        for f in files:
            print(f"   • {f.get('name')} [{f.get('type')}]")
        print("=" * 60 + "\n")
        return True
    except Exception as e:
        print(f"❌ Erro ao obter status: {e}")
        return False


def calcular_hash_pasta(pasta):
    """Calcula um hash dos conteúdos de todos os arquivos em src/ para detecção de alterações."""
    hashes = {}
    for p in pasta.glob("*"):
        if p.is_file():
            try:
                with open(p, "rb") as f:
                    hashes[p.name] = hashlib.md5(f.read()).hexdigest()
            except Exception:
                pass
    return hashes


def watch(service, script_id):
    """Modo monitor: observa src/ e atualiza no Apps Script APENAS os arquivos alterados a cada Ctrl+S."""
    dados_v = carregar_versao()
    gerar_version_gs(dados_v)

    print("\n" + "=" * 65)
    print("👀 MODO WATCHER ATIVADO — ALOCAÇÃO PLUS")
    print(f"📂 Monitorando alterações em: {SRC_DIR}")
    print(f"☁️  Destino: Apps Script ({script_id})")
    print(f"🏷️  Versão Atual: {dados_v.get('full_version', dados_v.get('version', 'v0.1.3'))}")
    print("💡 Pressione Ctrl+C a qualquer momento para interromper.")
    print("=" * 65 + "\n")

    # Inicializa cache remoto com os arquivos atuais
    try:
        res = service.projects().getContent(scriptId=script_id).execute()
        cache_remoto = res.get("files", [])
    except Exception:
        cache_remoto = carregar_arquivos_locais()

    # Primeiro envio garantido (completo)
    push(service, script_id)
    estado_anterior = calcular_hash_pasta(SRC_DIR)

    try:
        while True:
            time.sleep(1.0)
            estado_atual = calcular_hash_pasta(SRC_DIR)

            modificados = []
            for nome, h in estado_atual.items():
                if nome not in estado_anterior or estado_anterior[nome] != h:
                    modificados.append(nome)

            for nome in estado_anterior:
                if nome not in estado_atual:
                    modificados.append(f"{nome} (removido)")

            if modificados:
                hora = time.strftime("%H:%M:%S")

                # Se apenas o version.gs mudou (ex: comando 'bump' rodado em outro terminal)
                if modificados == ["version.gs"]:
                    dados_v = carregar_versao()
                    print(f"\n[{hora}] 🏷️  Versão atualizada: {dados_v.get('full_version', '')}")
                else:
                    print(f"\n[{hora}] ✏️  Alteração detectada: {', '.join(modificados)}")
                    dados_v = incrementar_build()
                    print(f"[{hora}] 🔨 Build atualizado: {dados_v.get('full_version', '')}")
                    if "version.gs" not in modificados:
                        modificados.append("version.gs")

                # Debounce de 0.5s para agrupamento de salvamentos
                time.sleep(0.5)

                # Atualiza SOMENTE os arquivos modificados no Apps Script
                push(service, script_id, arquivos_especificos=modificados, cache_remoto=cache_remoto)
                estado_anterior = calcular_hash_pasta(SRC_DIR)

    except KeyboardInterrupt:
        print("\n\n🛑 Monitoramento encerrado pelo usuário. Até logo!")


def main():
    parser = argparse.ArgumentParser(
        description="Sincronizador Automático do Alocação Plus com o Google Apps Script"
    )
    parser.add_argument(
        "comando",
        choices=["push", "pull", "watch", "status", "init", "bump", "build", "version", "idea", "backlog"],
        nargs="?",
        default="push",
        help="Ação a executar: push (padrão), pull, watch, status, init, bump, build, version ou idea/backlog"
    )
    parser.add_argument(
        "parametro",
        nargs="?",
        default=None,
        help="Parâmetro adicional (ex: Script ID no 'init', arquivo específico no 'push' ou texto da ideia)"
    )
    parser.add_argument(
        "--script-id",
        dest="script_id_flag",
        help="Especifica manualmente o Script ID da operação"
    )

    args = parser.parse_args()

    # Comandos locais que não exigem autenticação prévia nem conexão de rede
    if args.comando == "version":
        mostrar_versao()
        return

    if args.comando == "build":
        dados = incrementar_build()
        print(f"\n🔨 Build incrementado: {dados.get('full_version', '')}\n")
        return

    if args.comando == "bump":
        tipo = args.parametro or "patch"
        executar_bump(tipo)
        return

    if args.comando in ("idea", "backlog"):
        adicionar_ideia_backlog(args.parametro)
        return

    # Comando init não requer autenticação prévia
    if args.comando == "init":
        script_id = args.parametro or args.script_id_flag
        if not script_id:
            print("Digite ou cole o Script ID do seu projeto Google Apps Script:")
            print("(Obtido em: Editor do Apps Script > ⚙️ Configurações do Projeto > Script ID)")
            script_id = input("Script ID: ").strip()

        if script_id:
            salvar_script_id(script_id)
        else:
            print("❌ Script ID inválido.")
        return

    # Obtém o script_id configurado
    script_id = args.script_id_flag or obter_script_id()
    if not script_id:
        print("\n⚠️  Script ID não configurado!")
        print("Para configurar, execute:")
        print("   python tools/gas_sync.py init <SEU_SCRIPT_ID>")
        print("\nOu forneça via parâmetro:")
        print("   python tools/gas_sync.py push --script-id <SEU_SCRIPT_ID>")
        print("\nComo encontrar o Script ID:")
        print("1. Abra seu script no Google Sheets (Extensões > Apps Script) ou em script.google.com.")
        print("2. Clique no ícone de engrenagem ⚙️ (Configurações do projeto) no menu à esquerda.")
        print("3. Copie o campo 'Script ID'.\n")
        return

    # Autentica na API do Google
    creds = autenticar()
    if not creds:
        return

    try:
        service = build("script", "v1", credentials=creds)
    except Exception as e:
        print(f"❌ Erro ao inicializar serviço Google Apps Script: {e}")
        return

    # Executa o comando selecionado
    if args.comando == "push":
        push(service, script_id, arquivos_especificos=args.parametro)
    elif args.comando == "pull":
        pull(service, script_id)
    elif args.comando == "status":
        status(service, script_id)
    elif args.comando == "watch":
        watch(service, script_id)


if __name__ == "__main__":
    main()
