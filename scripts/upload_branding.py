"""Sube el banner de cada canal (public/branding/banner-<lang>.jpg, hecho con scripts/branding_ai.py).

  python scripts/upload_branding.py es,pt,en       (lo lanza branding.yml: los tokens solo estan en GitHub)

La foto de perfil (public/branding/avatar.png) NO se puede cambiar por la API de YouTube: se sube a mano en
YouTube Studio > Personalizacion > Marca > Foto.
"""
import sys
from pathlib import Path

from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload import CHANNEL, telegram, youtube  # noqa: E402

BASE = Path(__file__).resolve().parent.parent

for lang in sys.argv[1].split(","):
    yt = youtube(lang)
    banner = BASE / "public" / "branding" / f"banner-{lang}.jpg"
    url = yt.channelBanners().insert(media_body=MediaFileUpload(str(banner), mimetype="image/jpeg")).execute()["url"]
    ch = yt.channels().list(part="brandingSettings", mine=True).execute()["items"][0]
    bs = ch["brandingSettings"]
    bs.setdefault("image", {})["bannerExternalUrl"] = url
    yt.channels().update(part="brandingSettings", body={"id": ch["id"], "brandingSettings": bs}).execute()
    print(f"Banner nuevo en {CHANNEL[lang]}")
    telegram(f"🌈 Banner nuevo en {CHANNEL[lang]}")
