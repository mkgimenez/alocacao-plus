import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import gspread

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

FONTE_ID = '1AxLSuJPAGSZjvg36VaN8-mW9eogsacl2'
PLUS_ID = '1ZSa4RmZm0GSiAPrHwE1M1cB1vzI1hdg30bGkTA-R66U'

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"Aviso: Erro ao carregar {TOKEN_FILE}: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                print("Atualizando token expirado...")
                creds.refresh(Request())
            except Exception as e:
                print(f"Erro ao renovar token: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                candidates = [f for f in os.listdir('.') if f.startswith('client_secret') and f.endswith('.json')]
                if candidates:
                    cred_path = candidates[0]
                else:
                    print(f"ERRO: Arquivo '{CREDENTIALS_FILE}' não encontrado no diretório atual.")
                    print("Por favor, adicione o arquivo 'credentials.json' (OAuth 2.0 Client ID) gerado no Google Cloud Console.")
                    return None
            else:
                cred_path = CREDENTIALS_FILE

            print("Iniciando fluxo de autenticação OAuth 2.0 via navegador...")
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        print(f"Token salvo com sucesso em '{TOKEN_FILE}'.")

    return creds

def test_access(creds):
    client = gspread.authorize(creds)
    
    print("\n" + "="*50)
    print("TESTE DE ACESSO ÀS PLANILHAS")
    print("="*50)

    print(f"\n[1] Verificando acesso à FONTE (ID: {FONTE_ID})...")
    try:
        sh_fonte = client.open_by_key(FONTE_ID)
        print(f" -> Sucesso! Título da FONTE: '{sh_fonte.title}'")
        worksheets = [ws.title for ws in sh_fonte.worksheets()]
        print(f" -> Abas encontradas ({len(worksheets)}): {', '.join(worksheets)}")
    except Exception as e:
        print(f" -> Falha ao acessar FONTE: {e}")

    print(f"\n[2] Verificando acesso à PLUS (ID: {PLUS_ID})...")
    try:
        sh_plus = client.open_by_key(PLUS_ID)
        print(f" -> Sucesso! Título da PLUS: '{sh_plus.title}'")
        worksheets = [ws.title for ws in sh_plus.worksheets()]
        print(f" -> Abas encontradas ({len(worksheets)}): {', '.join(worksheets)}")
    except Exception as e:
        print(f" -> Falha ao acessar PLUS: {e}")

    print("\n" + "="*50)

if __name__ == '__main__':
    credentials = get_credentials()
    if credentials:
        test_access(credentials)
