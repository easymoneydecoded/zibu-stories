"""Autoriza un canal de YouTube y guarda las credenciales como secrets del repo (sin mostrarlas).

Uso: python scripts/autorizar_youtube.py <client_secret.json> en|es

Abre el navegador: elige la cuenta y despues el CANAL correcto (Zibu and Friends para en,
Zibu y sus amigos para es). Guarda con `gh secret set` YT_CLIENT_ID, YT_CLIENT_SECRET y YT_REFRESH_<LANG>.
"""
import json
import subprocess
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

REPO = "easymoneydecoded/zibu-stories"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]


def secret(name: str, value: str) -> None:
    subprocess.run(["gh", "secret", "set", name, "-R", REPO], input=value.encode(), check=True)
    print(f"   ✓ secret {name} guardado")


def main(client_file: str, lang: str) -> None:
    cfg = json.load(open(client_file, encoding="utf-8"))
    c = cfg.get("installed") or cfg.get("web")
    flow = InstalledAppFlow.from_client_config({"installed": {
        "client_id": c["client_id"], "client_secret": c["client_secret"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8090/"]}}, scopes=SCOPES)
    canal = "Zibu and Friends" if lang == "en" else "Zibu y sus amigos"
    print(f"Se abre el navegador: elige tu cuenta y despues el canal «{canal}».")
    creds = flow.run_local_server(port=8090, access_type="offline", prompt="consent", open_browser=True)
    secret("YT_CLIENT_ID", c["client_id"])
    secret("YT_CLIENT_SECRET", c["client_secret"])
    secret(f"YT_REFRESH_{lang.upper()}", creds.refresh_token)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
