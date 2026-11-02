"""Sube un episodio renderizado a su canal de YouTube y avisa por Telegram.

Uso: python scripts/upload.py <episode-id> en|es   (out/<id>-<lang>.mp4 y out/<id>-<lang>.png)

Cada canal tiene su refresh token (el canal se elige al autorizar con scripts/autorizar_youtube.py): YT_REFRESH_EN y YT_REFRESH_ES,
con YT_CLIENT_ID y YT_CLIENT_SECRET del proyecto de Google Cloud del canal de finanzas.
Avisos (opcional): TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

BASE = Path(__file__).resolve().parent.parent
CHANNEL = {"en": "Zibu and Friends", "es": "Zibu y sus amigos"}


def telegram(text: str) -> None:
    token, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if token and chat:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30,
                      data={"chat_id": chat, "text": text, "disable_web_page_preview": "true"})


def youtube(lang: str):
    creds = Credentials(None, refresh_token=os.environ[f"YT_REFRESH_{lang.upper()}"],
                        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token",
                        scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"])
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def main(episode: str, lang: str) -> None:
    story = json.loads((BASE / "stories" / f"{episode}.json").read_text(encoding="utf-8"))
    meta = story["youtube"][lang]
    video, thumb = BASE / "out" / f"{episode}-{lang}.mp4", BASE / "out" / f"{episode}-{lang}.png"
    yt = youtube(lang)
    body = {
        "snippet": {"title": meta["title"][:100], "description": meta["description"][:4900],
                    "tags": meta["tags"][:20], "categoryId": "1",  # Cine y animacion
                    "defaultLanguage": lang, "defaultAudioLanguage": lang},
        # Contenido para ninos: obligatorio por COPPA (sin comentarios ni anuncios personalizados)
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True, "embeddable": True},
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(video), mimetype="video/mp4", resumable=True,
                                                        chunksize=8 * 1024 * 1024))
    resp, intentos = None, 0
    while resp is None:
        try:
            status, resp = req.next_chunk()
            if status:
                print(f"   subiendo {lang}: {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status not in (500, 502, 503, 504) or intentos >= 5:
                raise
            intentos += 1
            time.sleep(2 ** intentos)
    vid = resp["id"]
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb), mimetype="image/png")).execute()
    except HttpError as e:  # sin verificar el canal por telefono YouTube no deja poner miniaturas
        print(f"   ! miniatura no subida: {e}")
    url = f"https://www.youtube.com/watch?v={vid}"
    print(f"Publicado en {CHANNEL[lang]}: {url}")
    telegram(f"🧸 Nuevo episodio en {CHANNEL[lang]}:\n{meta['title']}\n{url}")


if __name__ == "__main__":
    try:
        main(sys.argv[1], sys.argv[2])
    except Exception as e:
        telegram(f"⚠️ Zibu: fallo subiendo {sys.argv[1]} ({sys.argv[2]}): {type(e).__name__}: {e}"[:3500])
        raise
