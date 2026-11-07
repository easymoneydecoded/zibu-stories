"""Informe de solo lectura de los dos canales de Zibu -> out/report.json (lo lanza report.yml).

Con el permiso que tienen los tokens (YouTube Data API) saca: totales del canal y, por cada video subido,
fecha, duracion, vistas, likes y comentarios. No cambia nada en YouTube.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload import youtube  # noqa: E402

out = {}
for lang in ("es", "en"):
    yt = youtube(lang)
    ch = yt.channels().list(part="snippet,statistics,contentDetails", mine=True).execute()["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, token = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50, pageToken=token).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        token = r.get("nextPageToken")
        if not token:
            break
    videos = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,statistics,contentDetails,status", id=",".join(ids[i:i + 50])).execute()
        for v in r["items"]:
            videos.append({"id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
                           "duration": v["contentDetails"]["duration"], "privacy": v["status"]["privacyStatus"],
                           "made_for_kids": v["status"].get("madeForKids"), **v["statistics"]})
    out[lang] = {"channel": ch["snippet"]["title"], "stats": ch["statistics"], "videos": videos}
    print(f"{lang}: {ch['snippet']['title']} {ch['statistics']} ({len(videos)} videos)")

Path("out").mkdir(exist_ok=True)
Path("out/report.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
