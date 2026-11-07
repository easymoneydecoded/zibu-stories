"""Informe de solo lectura de los dos canales de Zibu -> out/report.json (lo lanza report.yml).

Con el permiso que tienen los tokens (YouTube Data API) saca: totales del canal y, por cada video subido,
fecha, duracion, vistas, likes y comentarios. No cambia nada en YouTube.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from upload import youtube  # noqa: E402

def analytics(lang: str) -> dict:
    """YouTube Analytics (necesita el permiso yt-analytics.readonly: scripts/autorizar_youtube.py)."""
    import os
    from datetime import date, timedelta
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(None, refresh_token=os.environ[f"YT_REFRESH_{lang.upper()}"],
                        client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                        token_uri="https://oauth2.googleapis.com/token")   # sin scopes: los que se concedieron
    ya = build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)
    rng = {"startDate": "2026-11-01", "endDate": date.today().isoformat()}
    queries = {
        "daily": dict(dimensions="day", metrics="views,estimatedMinutesWatched,averageViewDuration,subscribersGained",
                      sort="day"),
        "videos": dict(dimensions="video", metrics="views,estimatedMinutesWatched,averageViewDuration,"
                       "averageViewPercentage,subscribersGained", sort="-views", maxResults=50),
        "traffic": dict(dimensions="insightTrafficSourceType", metrics="views,estimatedMinutesWatched", sort="-views"),
        "suggested_by": dict(dimensions="insightTrafficSourceDetail", metrics="views",
                             filters="insightTrafficSourceType==RELATED_VIDEO", sort="-views", maxResults=15),
        "search_terms": dict(dimensions="insightTrafficSourceDetail", metrics="views",
                             filters="insightTrafficSourceType==YT_SEARCH", sort="-views", maxResults=15),
        "country": dict(dimensions="country", metrics="views", sort="-views", maxResults=10),
        "device": dict(dimensions="deviceType", metrics="views,estimatedMinutesWatched", sort="-views"),
        "playback": dict(dimensions="insightPlaybackLocationType", metrics="views", sort="-views"),
    }
    res = {}
    for name, kw in queries.items():
        try:
            r = ya.reports().query(ids="channel==MINE", **rng, **kw).execute()
            cols = [h["name"] for h in r.get("columnHeaders", [])]
            res[name] = [dict(zip(cols, x)) for x in r.get("rows", [])]
        except Exception as e:  # sin permiso de Analytics: el resto del informe sigue
            return {"error": str(e)[:200]}
    # Curva de retencion de cada episodio: que fraccion sigue viendo en cada punto del video
    res["retention"] = {}
    for v in res.get("videos", [])[:6]:
        try:
            r = ya.reports().query(ids="channel==MINE", **rng, dimensions="elapsedVideoTimeRatio",
                                   metrics="audienceWatchRatio,relativeRetentionPerformance",
                                   filters=f"video=={v['video']}").execute()
            res["retention"][v["video"]] = [[round(x[0], 2), round(x[1], 3), x[2]] for x in r.get("rows", [])]
        except Exception as e:
            res["retention"][v["video"]] = str(e)[:150]
    return res


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
    out[lang] = {"channel": ch["snippet"]["title"], "stats": ch["statistics"], "videos": videos,
                 "analytics": analytics(lang)}
    print(f"{lang}: {ch['snippet']['title']} {ch['statistics']} ({len(videos)} videos)")

Path("out").mkdir(exist_ok=True)
Path("out/report.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
