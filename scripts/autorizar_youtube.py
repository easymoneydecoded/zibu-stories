"""Autoriza un canal de YouTube y guarda las credenciales como secrets del repo (sin mostrarlas).

Uso (en la terminal, desde la carpeta Infantil):  python scripts/autorizar_youtube.py en|es

Usa el cliente OAuth del canal de finanzas (YOUTUBE_CLIENT_ID/SECRET de Youtube/.env): su proyecto de
Google Cloud ya publica videos publicos (los proyectos nuevos sin auditar solo pueden subir en privado).
Abre el navegador: elige tu cuenta y despues el CANAL correcto (Zibu and Friends para en, Zibu y sus
amigos para es). Guarda con `gh secret set` YT_CLIENT_ID, YT_CLIENT_SECRET y YT_REFRESH_<LANG>.
"""
import subprocess
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

REPO = "easymoneydecoded/zibu-stories"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/yt-analytics.readonly"]   # estadisticas (scripts/report.py), solo lectura
ENV = Path(__file__).resolve().parent.parent.parent / "Youtube" / ".env"


def leer_env(nombre: str) -> str:
    for linea in ENV.read_text(encoding="utf-8").splitlines():
        if linea.startswith(nombre + "="):
            return linea.split("=", 1)[1].strip().strip('"')
    sys.exit(f"No encuentro {nombre} en {ENV}")


def secret(nombre: str, valor: str) -> None:
    subprocess.run(["gh", "secret", "set", nombre, "-R", REPO], input=valor.encode(), check=True)
    print(f"   ✓ {nombre}")


def main(lang: str) -> None:
    cid, csecret = leer_env("YOUTUBE_CLIENT_ID"), leer_env("YOUTUBE_CLIENT_SECRET")
    flow = InstalledAppFlow.from_client_config({"installed": {
        "client_id": cid, "client_secret": csecret,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth", "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["http://localhost:8080/"]}}, scopes=SCOPES)
    canal = "Zibu and Friends" if lang == "en" else "Zibu y sus amigos"
    print(f"Se abre el navegador: elige tu cuenta y despues el canal «{canal}».")
    creds = flow.run_local_server(port=8080, access_type="offline", prompt="consent", open_browser=True)
    secret("YT_CLIENT_ID", cid)
    secret("YT_CLIENT_SECRET", csecret)
    secret(f"YT_REFRESH_{lang.upper()}", creds.refresh_token)
    print(f"Canal «{canal}» autorizado.")


if __name__ == "__main__":
    main(sys.argv[1])
