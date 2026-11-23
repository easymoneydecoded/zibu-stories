"""Rehace con IA las miniaturas de los episodios ya publicados y las sube a YouTube (lo lanza rethumb.yml).

  python scripts/rethumb.py es,pt,en

Para cada episodio: imagen base (ai_thumb) + titulo por idioma comprobado por Gemini -> thumbnails.set en su video.
El video de cada canal se busca por titulo (es/en, que estan en el guion) o por fecha de publicacion (pt, cuyo guion
traducido no se guarda). Lo hecho se apunta en stories/rethumb.json: si la cuota de YouTube se acaba a mitad, la
siguiente ejecucion sigue por donde iba. Al final avisa por Telegram.
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_thumb as A  # noqa: E402
from upload import CHANNEL, telegram, youtube  # noqa: E402

BASE = Path(__file__).resolve().parent.parent
STATE = BASE / "stories" / "rethumb.json"
EXCLUDE = {"ep002-waiting-our-turn-bear"}          # no se publico
THUMB_EP001 = {"en": ["The Lost", "Little Star!"], "es": ["¡La estrellita", "perdida!"], "pt": ["A estrelinha", "perdida!"]}


def videos(yt) -> list[dict]:
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    up = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        r = yt.playlistItems().list(part="contentDetails", playlistId=up, maxResults=50, pageToken=tok).execute()
        ids += [i["contentDetails"]["videoId"] for i in r["items"]]
        tok = r.get("nextPageToken")
        if not tok:
            break
    out = []
    for i in range(0, len(ids), 50):
        for v in yt.videos().list(part="snippet,contentDetails", id=",".join(ids[i:i + 50])).execute()["items"]:
            m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", v["contentDetails"]["duration"])
            secs = int(m[1] or 0) * 3600 + int(m[2] or 0) * 60 + int(m[3] or 0)
            out.append({"id": v["id"], "title": v["snippet"]["title"], "date": v["snippet"]["publishedAt"][:10],
                        "secs": secs})
    return [v for v in out if v["secs"] < 20 * 60]   # fuera los recopilatorios


def emparejar(lang: str, eps: list[dict], vids: list[dict]) -> dict[str, str]:
    """episodio -> id del video en ese canal."""
    libres, res = list(vids), {}
    norm = lambda t: re.sub(r"\W+", "", t.lower())  # noqa: E731
    for e in eps:   # 1) por titulo exacto (es/en)
        t = (e["story"].get("youtube", {}).get(lang) or {}).get("title")
        v = next((v for v in libres if t and norm(v["title"]) == norm(t[:100])), None)
        if v:
            res[e["id"]] = v["id"]
            libres.remove(v)
    for e in eps:   # 2) por fecha (el mismo dia o el siguiente)
        if e["id"] in res:
            continue
        d = date.fromisoformat(e["date"])
        v = next((v for dd in (d, d + timedelta(days=1)) for v in libres if v["date"] == dd.isoformat()), None)
        if v:
            res[e["id"]] = v["id"]
            libres.remove(v)
    return res


def lineas_pt(story: dict) -> list[str] | None:
    """El guion traducido al portugues no se guarda: se traducen solo las 2 lineas de la miniatura (Gemini gratis)."""
    es = (story.get("thumb") or {}).get("es")
    k = A.env_key("GEMINI_API_KEY")
    if not es or not k:
        return None
    body = {"contents": [{"parts": [{"text":
        "Translate these 2 short lines of a kids' cartoon thumbnail from Spanish to Brazilian Portuguese. Same style "
        "(uppercase if uppercase, keep ! marks), max 16 characters per line. Answer ONLY a JSON array of 2 strings.\n"
        + json.dumps(es, ensure_ascii=False)}]}]}
    for model in ("gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              params={"key": k}, json=body, timeout=60)
            txt = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
            lines = json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
            if isinstance(lines, list) and len(lines) == 2:
                return [str(x)[:18] for x in lines]
        except Exception:  # noqa: BLE001
            continue
    return None


def dos_lineas(texto: str) -> list[str]:
    """Para episodios antiguos sin texto de miniatura: el titulo partido en 2 lineas parecidas."""
    pal = texto.replace("Zibu y ", "").replace("Zibu and ", "").split()
    mejor = min(range(1, max(2, len(pal))), key=lambda i: abs(len(" ".join(pal[:i])) - len(" ".join(pal[i:]))))
    return [" ".join(pal[:mejor]), " ".join(pal[mejor:])] if len(pal) > 1 else [texto, ""]


def main(langs: list[str]) -> None:
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    ledger = json.loads((BASE / "stories" / "ledger.json").read_text(encoding="utf-8"))
    eps = [{"id": "ep001-lost-star", "date": "2026-11-02"}] + [{"id": x["id"], "date": x["date"]} for x in ledger]
    hoy = date.today().isoformat()
    eps = [e for e in eps if e["id"] not in EXCLUDE and (BASE / "stories" / f"{e['id']}.json").exists()
           and e["date"] < "2026-11-23"]   # desde el 23-nov las miniaturas ya salen con IA
    for e in eps:
        e["story"] = json.loads((BASE / "stories" / f"{e['id']}.json").read_text(encoding="utf-8"))
        if e["id"] == "ep001-lost-star":
            e["story"]["thumb"] = dict(THUMB_EP001, scene=2)
    yts = {l: youtube(l) for l in langs}
    mapa = {l: emparejar(l, eps, videos(yts[l])) for l in langs}
    hechas, fallos, cuota = 0, [], False
    for e in eps:
        pend = [l for l in langs if not state.get(e["id"], {}).get(l) and e["id"] in mapa[l]]
        if not pend:
            continue
        st = e["story"]
        st.setdefault("thumb", {})
        for l in ("es", "en"):
            if not st["thumb"].get(l) and st.get("title", {}).get(l):
                st["thumb"][l] = [x for x in dos_lineas(st["title"][l]) if x]
        if "pt" in pend and not st["thumb"].get("pt"):
            st["thumb"]["pt"] = lineas_pt(st)
        guest = st["guest"].get("species") or st["guest"]["id"]
        base = A.openai(st, BASE / "public" / "ref" / f"cast-{guest}.png")
        if not base:
            fallos.append(f"{e['id']} (imagen)")
            continue
        A.texted(st, base, langs=pend)
        for l in pend:
            f = BASE / "public" / "ep" / e["id"] / f"thumb-ai-{l}.png"
            if not f.exists():
                fallos.append(f"{e['id']} {l} (titulo)")
                continue
            try:
                yts[l].thumbnails().set(videoId=mapa[l][e["id"]], media_body=MediaFileUpload(str(f), mimetype="image/png")).execute()
            except HttpError as err:
                if "quota" in str(err).lower():
                    cuota = True
                    break
                fallos.append(f"{e['id']} {l} ({str(err)[:80]})")
                continue
            state.setdefault(e["id"], {})[l] = mapa[l][e["id"]]
            hechas += 1
            STATE.write_text(json.dumps(state, indent=1), encoding="utf-8")
            print(f"   ✓ {e['id']} [{l}] -> {mapa[l][e['id']]}")
        if cuota:
            break
    if not hechas and not fallos and not cuota:
        print("Nada pendiente")
        return
    total = sum(1 for e in eps for l in langs if e["id"] in mapa[l])
    listas = sum(len(v) for v in state.values())
    msg = (f"🎨 Zibu: {hechas} miniaturas antiguas cambiadas por las nuevas con IA ({listas}/{total} en total, "
           f"canales {', '.join(CHANNEL[l] for l in langs)}).")
    if cuota:
        msg += "\nSe acabo la cuota diaria de YouTube: sigo solo manana."
    if fallos:
        msg += f"\nNo salieron: {', '.join(fallos[:10])}"
    print(msg)
    telegram(msg)


if __name__ == "__main__":
    main(sys.argv[1].split(","))
