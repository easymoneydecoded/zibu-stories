"""Recopilatorios largos de Zibu ("1 hora de cuentos") para el publico que lo ve en la tele (lo lanza compilation.yml).

  python scripts/compilation.py plan es,pt [n]        -> JSON con los episodios a renderizar: [{"lang","ep"}, ...]
  python scripts/compilation.py meta <ep> <lang>      -> out/<ep>-<lang>.meta.json (titulo, tags) tras renderizar
  python scripts/compilation.py join <lang>           -> une out/*-<lang>.mp4, hace la miniatura, sube y apunta en
                                                         stories/compilations.json

Por que: casi la mitad de las vistas en espanol y portugues son en TV, donde se deja puesto un video largo; las horas de
visualizacion son lo que falta para monetizar. Cada recopilatorio junta N episodios que aun no han salido en uno.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))
LEDGER = BASE / "stories" / "compilations.json"        # antiguo (un solo archivo)
LEDGER_DIR = BASE / "stories" / "compilations"         # uno por recopilatorio: es y pt se apuntan sin pisarse
EXCLUDE = {"ep002-waiting-our-turn-bear"}   # no se llego a publicar (su historia necesitaba un tobogan que no se dibuja)
OUT = BASE / "out"
TXT = {
    "es": {"badge": "1 HORA", "line": "DE CUENTOS", "title": "1 Hora de Zibu y sus Amigos 🎈 {n} Cuentos Infantiles para Aprender | Dibujos Animados",
           "intro": "¡{n} cuentos seguidos de Zibu y sus amigos para ver juntos! Ideal para la tele. 📺\n\nCapítulos:",
           "tags": ["zibu", "cuentos infantiles", "dibujos animados", "1 hora", "cuentos para niños", "recopilación"],
           "end": "#ZibuYSusAmigos #CuentosInfantiles #DibujosAnimados"},
    "pt": {"badge": "1 HORA", "line": "DE HISTÓRIAS", "title": "1 Hora de Zibu e seus Amigos 🎈 {n} Histórias Infantis para Aprender | Desenho Animado",
           "intro": "{n} histórias seguidas do Zibu e seus amigos para assistir juntos! Ideal para a TV. 📺\n\nCapítulos:",
           "tags": ["zibu", "histórias infantis", "desenho animado", "1 hora", "desenho infantil", "compilação"],
           "end": "#ZibuESeusAmigos #HistoriasInfantis #DesenhoAnimado"},
    "en": {"badge": "1 HOUR", "line": "OF STORIES", "title": "1 Hour of Zibu and Friends 🎈 {n} Stories for Kids to Learn | Cartoons for Toddlers",
           "intro": "{n} Zibu and Friends stories in a row to watch together! Great for the TV. 📺\n\nChapters:",
           "tags": ["zibu", "kids stories", "cartoons for kids", "1 hour", "toddler videos", "compilation"],
           "end": "#ZibuAndFriends #KidsStories #Cartoons"},
}


def ledger() -> list[dict]:
    viejo = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else []
    return viejo + [json.loads(f.read_text(encoding="utf-8")) | {"_file": str(f)}
                    for f in sorted(LEDGER_DIR.glob("*.json"))]


def apuntar(entry: dict) -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    f = Path(entry.pop("_file", "")) if entry.get("_file") else LEDGER_DIR / f"{entry['lang']}-{entry['date']}-{entry['video']}.json"
    f.write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")


TITULO_IA = {"es": ["¡1 HORA", "DE CUENTOS!"], "pt": ["1 HORA DE", "HISTÓRIAS!"], "en": ["1 HOUR OF", "STORIES!"]}


def ai_thumbnail(lang: str, eps: list[str], minutes: int, dest: Path) -> bool:
    """Miniatura con IA: Zibu, Lila y los invitados de los cuentos juntos de fiesta + '1 HORA DE CUENTOS' dibujado por
    la IA y comprobado por Gemini (como las miniaturas de los episodios). False si no se pudo."""
    import io
    import ai_thumb as A
    from branding_ai import edit_multi
    from PIL import Image
    especies, objetos = [], []
    for ep in eps:
        f = BASE / "stories" / f"{ep}.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text(encoding="utf-8"))
        sp = st["guest"].get("species") or st["guest"]["id"]
        if sp not in especies:
            especies.append(sp)
        objetos += [(p.get("what") if isinstance(p, dict) else p) for sc in st["scenes"] for p in sc.get("props", [])]
    refs = [BASE / "public" / "ref" / f"cast-{sp}.png" for sp in especies[:4]]
    refs = [r for r in refs if r.exists()] or [BASE / "public" / "ref" / "cast-puppy.png"]
    cosas = ", ".join(list(dict.fromkeys(o for o in objetos if o))[:4]) or "balloons and a kite"
    prompt = ("A YouTube thumbnail, 16:9, for a 1-hour compilation of preschool cartoon stories. Zibu (round blue monster "
              "with big eyes and a yellow ball antenna) and Lila (pink bunny with a purple bow) together with ALL their "
              f"friends from the reference images ({', '.join(especies[:4])}), celebrating together in a sunny meadow "
              f"under a rainbow, with some of the story objects ({cosas}), confetti and sparkles. Everyone happy, "
              "laughing and waving at the viewer, characters large and filling the lower two thirds and the right side. "
              "Full cheerful landscape (hills, flowers, clouds). The upper-left area is only soft sky (a title goes "
              "there). Keep everything important away from the top and bottom 10% (the image is cropped to 16:9). "
              "Polished 2D cartoon style exactly like the references, same character designs. NO text or letters.")
    raw = edit_multi(refs, prompt, quality="medium")
    if not raw:
        return False
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    th = round(w * 9 / 16)
    base = img.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((1280, 720), Image.LANCZOS)
    lines = TITULO_IA[lang] if minutes >= 55 else [f"{minutes} MIN", TITULO_IA[lang][1]]
    for _ in range(3):
        t = A.openai_title(lines)
        if not t:
            break
        pega = Image.open(io.BytesIO(t)).convert("RGBA")
        caja = pega.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
        if not caja:
            continue
        lienzo = base.convert("RGBA")
        pega, pos = A.colocar(lienzo, pega.crop(caja))
        lienzo.alpha_composite(pega, pos)
        buf = io.BytesIO()
        lienzo.convert("RGB").save(buf, "PNG")
        if A.verify(buf.getvalue(), lines):
            dest.write_bytes(buf.getvalue())
            return True
    return False


def rethumb() -> None:
    """Pone la miniatura con IA a los recopilatorios ya publicados que aun tienen la antigua."""
    from googleapiclient.http import MediaFileUpload
    from upload import CHANNEL, telegram, youtube
    for c in ledger():
        if c.get("ai") or not c.get("video"):
            continue
        dest = OUT / f"compilation-{c['lang']}-{c['video']}.png"
        OUT.mkdir(exist_ok=True)
        if not ai_thumbnail(c["lang"], c["episodes"], c.get("minutes", 60), dest):
            print(f"   ! no salio la miniatura de {c['video']}")
            continue
        youtube(c["lang"]).thumbnails().set(videoId=c["video"],
                                             media_body=MediaFileUpload(str(dest), mimetype="image/png")).execute()
        c["ai"] = True
        apuntar(c)
        print(f"   ✓ recopilatorio {c['lang']} {c['video']}")
        telegram(f"🎨 Miniatura nueva con IA en el recopilatorio de {CHANNEL[c['lang']]}: "
                 f"https://www.youtube.com/watch?v={c['video']}")


def plan(langs: list[str], n: int) -> list[dict]:
    """Los n episodios mas antiguos de cada idioma que aun no estan en ningun recopilatorio de ese idioma."""
    eps = [e["id"] for e in json.loads((BASE / "stories" / "ledger.json").read_text(encoding="utf-8"))]
    out = []
    for lang in langs:
        usados = {ep for c in ledger() if c["lang"] == lang for ep in c["episodes"]}
        libres = [e for e in eps if e not in usados and e not in EXCLUDE and (BASE / "stories" / f"{e}.json").exists()]
        if len(libres) >= n:
            out += [{"lang": lang, "ep": e} for e in libres[:n]]
        else:
            print(f"{lang}: solo {len(libres)} episodios libres (hacen falta {n}), no hay recopilatorio", file=sys.stderr)
    return out


def meta(ep: str, lang: str) -> None:
    story = json.loads((BASE / "stories" / f"{ep}.json").read_text(encoding="utf-8"))
    yt = story["youtube"][lang]
    (OUT / f"{ep}-{lang}.meta.json").write_text(json.dumps(
        {"ep": ep, "title": story["title"][lang], "yt_title": yt["title"], "tags": yt.get("tags", []),
         "learn": story.get("lesson", {}).get(lang, "")}, ensure_ascii=False), encoding="utf-8")


def ffmpeg(*args: str) -> str:
    return subprocess.run(["npx", "remotion", "ffmpeg", *args], cwd=BASE, check=True, capture_output=True,
                          text=True, shell=sys.platform == "win32").stderr


def duration(mp4: Path) -> float:
    err = subprocess.run(["npx", "remotion", "ffmpeg", "-i", str(mp4)], cwd=BASE, capture_output=True, text=True,
                         shell=sys.platform == "win32").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def stamp(sec: float) -> str:
    sec = int(sec)
    return f"{sec // 3600}:{sec % 3600 // 60:02d}:{sec % 60:02d}" if sec >= 3600 else f"{sec // 60:02d}:{sec % 60:02d}"


def thumbnail(lang: str, pngs: list[Path], minutes: int, dest: Path) -> None:
    """Mosaico 2x2 con las miniaturas de los episodios y un sello grande '1 HORA DE CUENTOS'."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), "#ffd54a")
    for i, p in enumerate(pngs[:4]):
        t = Image.open(p).convert("RGB").resize((W // 2, H // 2))
        img.paste(t, ((i % 2) * W // 2, (i // 2) * H // 2))
    d = ImageDraw.Draw(img)

    def font(size):
        for f in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/seguibl.ttf",
                  "C:/Windows/Fonts/arialbd.ttf"):
            if Path(f).exists():
                return ImageFont.truetype(f, size)
        return ImageFont.load_default()

    t = TXT[lang]
    badge = t["badge"] if minutes >= 55 else f"{minutes} MIN"
    cx, cy, r = W // 2, H // 2, 205
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill="#ff5d8f", outline="white", width=14)
    for text, size, dy in ((badge, 112, -48), (t["line"], 46, 62)):
        f = font(size)
        while d.textlength(text, font=f) > 1.62 * r and size > 20:   # que no se salga del circulo
            size -= 4
            f = font(size)
        w = d.textlength(text, font=f)
        d.text((cx - w / 2, cy + dy - size / 2), text, font=f, fill="white", stroke_width=5, stroke_fill="#7a1f3d")
    img.save(dest)


def join(lang: str) -> None:
    metas = sorted(OUT.glob(f"*-{lang}.meta.json"), key=lambda p: p.name)
    items = [json.loads(p.read_text(encoding="utf-8")) for p in metas]
    items = [m | {"mp4": OUT / f"{m['ep']}-{lang}.mp4", "png": OUT / f"{m['ep']}-{lang}.png"} for m in items]
    items = [m for m in items if m["mp4"].exists()]
    if len(items) < 3:
        raise SystemExit(f"{lang}: solo {len(items)} episodios renderizados, no hay recopilatorio")
    n = len(items)
    lista = OUT / f"comp-{lang}.txt"
    lista.write_text("".join(f"file '{m['mp4'].resolve().as_posix()}'\n" for m in items), encoding="utf-8")
    video = OUT / f"compilation-{lang}.mp4"
    ffmpeg("-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
           "-movflags", "+faststart", str(video))
    t, caps = 0.0, []
    for m in items:
        caps.append(f"{stamp(t)} {m['title']}")
        t += duration(m["mp4"])
    minutes = round(t / 60)
    thumb = OUT / f"compilation-{lang}.png"
    ai = ai_thumbnail(lang, [m["ep"] for m in items], minutes, thumb)
    if not ai:   # sin IA: el mosaico de siempre
        thumbnail(lang, [m["png"] for m in items if m["png"].exists()], minutes, thumb)

    tx = TXT[lang]
    title = tx["title"].format(n=n)
    if minutes < 55:   # el titulo promete una hora: si no llega, se dice cuanto dura
        title = title.replace("1 Hora", f"{minutes} Minutos").replace("1 Hour", f"{minutes} Minutes")
    if len(title) > 100:
        title = title[:99].rsplit(" ", 1)[0] + "…"
    desc = "\n".join([tx["intro"].format(n=n), *caps, "", tx["end"]])
    from upload import limpiar_tags   # el mismo limite de 500 caracteres que en los episodios
    tags = limpiar_tags(tx["tags"] + [tg for m in items for tg in m["tags"]])
    print(f"{lang}: {n} episodios, {stamp(t)} -> {video.name}\n{title}\n{desc}")

    import os
    if os.getenv("DRY_RUN") == "1":
        return
    from upload import CHANNEL, YT_LANG, telegram, youtube
    from googleapiclient.http import MediaFileUpload
    yt = youtube(lang)
    body = {"snippet": {"title": title, "description": desc[:4900], "tags": tags, "categoryId": "1",
                        "defaultLanguage": YT_LANG.get(lang, lang), "defaultAudioLanguage": YT_LANG.get(lang, lang)},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": True, "embeddable": True}}
    req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(
        str(video), mimetype="video/mp4", resumable=True, chunksize=16 * 1024 * 1024))
    resp = None
    while resp is None:
        status, resp = req.next_chunk()
        if status:
            print(f"   subiendo: {int(status.progress() * 100)}%")
    vid = resp["id"]
    try:
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb), mimetype="image/png")).execute()
    except Exception as e:
        print(f"   ! miniatura no subida: {e}")
    url = f"https://www.youtube.com/watch?v={vid}"
    apuntar({"lang": lang, "date": date.today().isoformat(), "video": vid, "episodes": [m["ep"] for m in items],
             "minutes": minutes, "ai": ai})
    print(f"Publicado en {CHANNEL[lang]}: {url}")
    telegram(f"📺 Recopilatorio de {minutes} min en {CHANNEL[lang]}:\n{title}\n{url}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "plan":
        print(json.dumps(plan(sys.argv[2].split(","), int(sys.argv[3]) if len(sys.argv) > 3 else 6)))
    elif cmd == "meta":
        meta(sys.argv[2], sys.argv[3])
    elif cmd == "join":
        join(sys.argv[2])
    elif cmd == "rethumb":
        rethumb()
