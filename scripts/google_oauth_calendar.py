import os
import sys
import json
import pathlib
import urllib.parse

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/calendar.events']
SECRETS_DIR = pathlib.Path('.secrets')
TOKEN_PATH = SECRETS_DIR / 'calendar_token.json'

AUTH_BASE = 'https://accounts.google.com/o/oauth2/v2/auth'
TOKEN_URL = 'https://oauth2.googleapis.com/token'

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def fail(msg: str) -> int:
    print('MIMIR Bifrost: ' + msg)
    return 2


def main() -> int:
    from core.config.settings import Settings
    s = Settings()
    cid = s.google_oauth_client_id or os.environ.get('GOOGLE_OAUTH_CLIENT_ID', '')
    csec = s.google_oauth_client_secret or os.environ.get('GOOGLE_OAUTH_CLIENT_SECRET', '')
    if not cid or not csec:
        return fail('Faltan GOOGLE_OAUTH_CLIENT_ID / SECRET en .env. No llamo a Google (fail closed).')

    SECRETS_DIR.mkdir(exist_ok=True)

    # Si ya hay token, probar lectura directamente
    if TOKEN_PATH.exists():
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
        except ImportError:
            return fail('Instala: pip install google-api-python-client google-auth-oauthlib')
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        svc = build('calendar', 'v3', credentials=creds)
        evs = svc.events().list(calendarId='primary', maxResults=5, singleEvents=True, orderBy='startTime').execute()
        items = evs.get('items', [])
        print('OK lectura. Eventos: ' + str(len(items)))
        for e in items:
            print('- ' + str(e.get('summary', '(sin titulo)')) + ' ' + str(e.get('start', {})))
        return 0

    # Construir URL de autorización manualmente (evita fallos de redirect_uri en la librería)
    params = {
        'client_id': cid,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
    }
    auth_url = AUTH_BASE + '?' + urllib.parse.urlencode(params)
    print('Paso: abre esta URL en tu navegador, autoriza SOLO lectura de Calendar:')
    print(auth_url)
    print()
    print('Si sale app no verificada, pulsa Avanzado / Ir (tu propia app en test).')

    if len(sys.argv) > 1:
        code = sys.argv[1].strip()
        print('Usando codigo pasado como argumento.')
    else:
        code = input('Pega aqui el codigo de autorizacion: ').strip()

    # Intercambiar codigo por token
    try:
        import httpx
    except ImportError:
        return fail('Instala httpx: pip install httpx')

    data = {
        'code': code,
        'client_id': cid,
        'client_secret': csec,
        'redirect_uri': 'urn:ietf:wg:oauth:2.0:oob',
        'grant_type': 'authorization_code',
    }
    resp = httpx.post(TOKEN_URL, data=data, timeout=30.0)
    if resp.status_code != 200:
        print('Error obteniendo token:', resp.status_code, resp.text)
        return 2
    token_data = resp.json()
    # google.auth requiere client_id/client_secret/token_uri al recargar; los inyectamos
    token_data['client_id'] = cid
    token_data['client_secret'] = csec
    token_data['token_uri'] = TOKEN_URL
    TOKEN_PATH.write_text(json.dumps(token_data), encoding='utf-8')
    print('Token guardado solo local en .secrets/calendar_token.json (no va a git).')
    print('Reejecuta el script para probar list_events readonly.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
