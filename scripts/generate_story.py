"""Escribe un episodio nuevo de Zibu con Gemini (plan gratuito), lo valida y lo revisa.

Uso: python scripts/generate_story.py            -> stories/epNNN-<slug>.json y lo anade a stories/ledger.json
Requiere GEMINI_API_KEY. Opcional: GEMINI_MODEL.

Para que no se repita: el invitado, la leccion y lo que se aprende se eligen entre los que no se han
usado en los ultimos episodios (stories/ledger.json), y Gemini recibe los titulos anteriores.
Un guion que no pasa la validacion se devuelve a Gemini con los errores; uno que no aprueba el
revisor se descarta y se escribe otro.
"""
import json
import os
import random
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
STORIES = BASE / "stories"
LEDGER = STORIES / "ledger.json"
MODELS = [os.getenv("GEMINI_MODEL")] if os.getenv("GEMINI_MODEL") else [
    "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash", "gemini-2.5-flash"]

SPECIES = ["puppy", "kitten", "bear", "duckling", "frog", "piglet", "owl", "mouse", "star"]
BGS = ["garden", "forest", "river", "hill", "sky", "beach", "room"]
TIMES = ["day", "sunset", "night"]
PROPS = ["ball", "firefly", "stone", "balloon", "bigstar", "brightstar", "apple", "flower", "butterfly", "gift",
         "cookie", "kite", "umbrella", "shell", "leaf", "cupcake"]
MOODS = ["happy", "laugh", "sad", "surprised", "scared"]
ACTIONS = ["jump", "bigjump", "wave", "shake", "spin", "glow"]
WHO = ["narrator", "zibu", "lila", "guest"]

LESSONS = [
    "sharing with friends", "saying sorry and making up", "being brave when something is new", "trying again after a mistake",
    "being patient and waiting your turn", "telling the truth", "helping someone who is sad", "teamwork",
    "being kind to someone different", "saying thank you", "taking care of nature", "listening to others",
    "it's okay to ask for help", "including everyone in the game", "taking care of your things", "calming down when angry",
    "being a good loser and a good winner", "keeping a promise", "helping at home", "being gentle with animals",
]
LEARN = [
    "counting from 1 to 5 (show the numbers)", "colors: red, blue, yellow, green (show the color words with their color)",
    "big and small, opposites (show the words)", "animal sounds (show the sound words, like 'Woof!')",
    "counting from 1 to 5 backwards, like a rocket countdown", "shapes: circle, square, triangle (show the words)",
    "emotions: happy, sad, surprised (show the words)", "up and down, in and out, opposites (show the words)",
]


# ---------------------------------------------------------------------------
# Gemini
# ---------------------------------------------------------------------------
def gemini(prompt: str, max_tokens: int = 16000, temperature: float = 0.9) -> dict:
    key = os.environ["GEMINI_API_KEY"]
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": temperature,
                                 "responseMimeType": "application/json"}}
    for model in MODELS:
        for intento in range(3):
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                                  headers={"x-goog-api-key": key}, json=body, timeout=300)
            except requests.RequestException as ex:
                print(f"   ! Gemini {model}: {type(ex).__name__}")
                continue
            if r.status_code == 200:
                b = r.json()
                parts = b["candidates"][0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
                m = re.search(r"\{.*\}", text, re.S)
                if not m:
                    raise ValueError(f"Gemini ({model}) no devolvio JSON: {text[:200]}")
                print(f"   . Gemini ok ({model})")
                return json.loads(m.group(0))
            if r.status_code in (429, 500, 503):
                time.sleep(10 * (intento + 1))
                continue
            print(f"   ! Gemini {model}: {r.status_code} {r.text[:200]}")
            break
    raise RuntimeError("Gemini: ningun modelo disponible")


# ---------------------------------------------------------------------------
# Validacion
# ---------------------------------------------------------------------------
def validar(s: dict) -> list[str]:
    e = []
    for k in ("slug", "title", "lesson", "guest", "thumb", "youtube", "scenes"):
        if k not in s:
            e.append(f"falta '{k}'")
    if e:
        return e
    if s["guest"].get("species") not in SPECIES:
        e.append("guest.species no valido")
    for lang in ("en", "es"):
        if not s["guest"].get("name", {}).get(lang):
            e.append(f"guest.name.{lang} vacio")
        yt = s["youtube"].get(lang, {})
        if not yt.get("title") or len(yt["title"]) > 100:
            e.append(f"youtube.{lang}.title vacio o de mas de 100 caracteres")
        if not yt.get("description") or not isinstance(yt.get("tags"), list):
            e.append(f"youtube.{lang} sin description o tags")
        if not isinstance(s["thumb"].get(lang), list) or len(s["thumb"][lang]) != 2:
            e.append(f"thumb.{lang} debe ser una lista de 2 textos cortos")
    sc = s["scenes"]
    tipos = [x.get("type", "story") for x in sc]
    if tipos[:1] != ["title"] or tipos[-1:] != ["dance"] or tipos.count("song") != 1 or tipos.count("recap") != 1:
        e.append("estructura: la primera escena debe ser 'title', la ultima 'dance', y debe haber 1 'song' y 1 'recap'")
    if not 6 <= tipos.count("story") <= 10:
        e.append(f"debe haber entre 6 y 10 escenas de historia (hay {tipos.count('story')})")
    total = 0
    for i, x in enumerate(sc):
        where = f"escena {i} ({x.get('id')})"
        if x.get("bg") not in BGS or x.get("time") not in TIMES:
            e.append(f"{where}: bg/time no validos")
        cast = {c.get("who") for c in x.get("cast", [])}
        if not cast <= {"zibu", "lila", "guest"} or not cast:
            e.append(f"{where}: cast solo puede tener zibu, lila y guest")
        lines = x.get("lines", [])
        total += len(lines)
        for p in x.get("props", []):
            if p.get("what") not in PROPS:
                e.append(f"{where}: prop '{p.get('what')}' no existe")
            if not isinstance(p.get("at", 0), int) or not 0 <= p.get("at", 0) < len(lines):
                e.append(f"{where}: prop.at fuera de rango")
            if "until" in p and not (isinstance(p["until"], int) and p.get("at", 0) < p["until"] < len(lines)):
                e.append(f"{where}: prop.until fuera de rango")
        for j, ln in enumerate(lines):
            lw = f"{where} frase {j}"
            if ln.get("who") not in WHO or (ln["who"] != "narrator" and ln["who"] not in cast):
                e.append(f"{lw}: 'who' debe ser narrator o alguien del cast de la escena")
            for lang in ("en", "es"):
                t = ln.get(lang)
                if not isinstance(t, str) or not t.strip() or len(t) > 170:
                    e.append(f"{lw}: texto {lang} vacio o demasiado largo")
            if ln.get("mood") and ln["mood"] not in MOODS:
                e.append(f"{lw}: mood no valido")
            if ln.get("action") and ln["action"] not in ACTIONS:
                e.append(f"{lw}: action no valida")
            for m in ln.get("moves", []):
                if m.get("who") not in cast or not isinstance(m.get("to"), (int, float)) or not -0.7 <= m["to"] <= 1.7:
                    e.append(f"{lw}: move no valido")
            if "show" in ln and not (isinstance(ln["show"], dict) and ln["show"].get("en") and ln["show"].get("es")):
                e.append(f"{lw}: show debe tener en y es")
    if total < 115:
        e.append(f"demasiado corto: {total} frases (minimo 115) para llegar a 8 minutos")
    return e[:25]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
SERIE = """You write episodes for "Zibu and Friends", an animated YouTube series for children aged 2 to 6.
Everything is written in ENGLISH ("en") and natural neutral LATIN AMERICAN SPANISH ("es": use "ustedes", never "vosotros").
CHARACTERS (only these): zibu (a cheerful, curious round blue monster with an antenna, the main character),
lila (a kind, gentle pink bunny, Zibu's best friend, sometimes a bit shy), guest (this episode's guest) and the
narrator (a warm storyteller, voice only).
SAFETY: nothing scary, violent, sad for long, or dangerous to imitate (no fire, no going into water alone, no
strangers, no climbing dangerous places). No brands, no real people, no other cartoon characters."""


def formato() -> str:
    return f"""SCENE FORMAT (JSON). Allowed values:
- "bg": {", ".join(BGS)} (room = a cozy bedroom). "time": {", ".join(TIMES)}.
- "cast": [{{"who": "zibu"|"lila"|"guest", "x": 0..1 (horizontal position; -0.2 or 1.3 = off screen),
  "y": 0..1 only for a guest that floats or flies}}]
- "lines": [{{"who": "narrator"|someone in the cast, "en", "es", optional "mood": {"|".join(MOODS)},
  optional "action": {"|".join(ACTIONS)}, optional "moves": [{{"who", "to": x, optional "toY": y}}] to walk, enter or
  leave, optional "show": {{"en", "es", optional "color": "#hex"}} to show a big word or number, optional "pause": seconds}}]
- "props": [{{"what": {"|".join(PROPS)}, "x", "y" (0..1, center of the object), "at": index of the line where it
  appears, optional "until": index of the line where it disappears, optional "anim": "bounce"|"float", optional "color"}}]
Lines are SHORT (most under 12 words), simple, warm, with exclamations and "..." pauses so the voices sound
expressive. The narrator describes what happens; the characters talk a lot. Characters move: use "moves" to make
them enter, walk and leave, "action" to jump, wave or spin, and "mood" so their faces show emotions."""


def prompt_esquema(species: str, lesson: str, learn: str, anteriores: list[str]) -> str:
    return f"""{SERIE}

Plan a NEW episode. The guest is a {species}. Lesson: {lesson}. Learning moment: {learn}.
It must be different from these previous episodes: {"; ".join(anteriores) or "none yet"}.
The story: a beginning, a small problem, two or three tries to solve it, a happy solution and the lesson said
clearly near the end. Include the learning moment in one scene (big words/numbers on screen).

Return ONLY JSON:
{{"slug": "kebab-case, 2-4 words", "title": {{"en", "es"}}, "lesson": {{"en", "es"}},
 "guest": {{"species": "{species}", "name": {{"en", "es"}}}},
 "thumb": {{"en": [2 very short lines for the thumbnail], "es": [2 very short lines], "scene": index of the most colorful story scene (1-based position in the full episode, the title scene is 0)}},
 "youtube": {{"en": {{"title": "max 90 chars, with an emoji, says what kids learn", "description": "5-8 lines with emojis: what happens and what kids learn, ages 2-6, ends with 3-5 hashtags", "tags": [10-14 tags]}}, "es": {{same in Spanish}}}},
 "story": [7 story scenes: {{"id": "kebab-case", "bg": one of {", ".join(BGS)}, "time": one of {", ".join(TIMES)}, "cast": ["zibu", "lila", "guest" as needed], "summary": "2-3 sentences of what happens"}}],
 "song": {{"en": "song title", "es": "song title"}}}}
Use at least 3 different bg values."""


def prompt_escenas(plan: dict, idx: list[int], previas: list[dict], ejemplo: str) -> str:
    resumen = [{"n": i + 1, **{k: s[k] for k in ("id", "bg", "time", "cast", "summary")}} for i, s in enumerate(plan["story"])]
    final = previas[-1]["lines"][-3:] if previas else []
    return f"""{SERIE}

EPISODE PLAN: {json.dumps({k: plan[k] for k in ("title", "lesson", "guest")}, ensure_ascii=False)}
STORY SCENES: {json.dumps(resumen, ensure_ascii=False)}
The previous scene ended with: {json.dumps(final, ensure_ascii=False)}

Write story scenes number {", ".join(str(i + 1) for i in idx)} in full, 12 to 16 lines each.
{formato()}

EXAMPLE scene from a previous episode: {ejemplo}

Return ONLY JSON: {{"scenes": [one object per scene with "id", "bg", "time", "cast", optional "props", "lines"]}}"""


def prompt_final(plan: dict, historia: list[dict]) -> str:
    texto = [ln["en"] for s in historia for ln in s["lines"]]
    return f"""{SERIE}

EPISODE: {json.dumps({k: plan[k] for k in ("title", "lesson", "guest", "song")}, ensure_ascii=False)}
THE STORY (English lines): {json.dumps(texto, ensure_ascii=False)}

Write the last three scenes. {formato()}
1. "song" scene ({{"id": "song", "type": "song", "bg": "sky" or the most colorful bg, "time", "cast" with zibu, lila,
   guest}}): an ORIGINAL simple song about this story. 4-line chorus + 4-line verse (sung by zibu and lila in turns) +
   chorus, then zibu says "One more time! Sing with us!", then the whole song again, then one happy line by the
   guest. Lines rhyme in each language. Chorus lines are sung by the narrator. About 26 lines.
2. "recap" scene ({{"id": "recap", "type": "recap", "bg", "time": "day", "cast" with zibu and lila}}): the narrator
   says "Did you like the story? Let's remember it together!", then asks 5 questions about the story, each one with
   "pause": 2.5 followed by the answer (use "show" for numbers or words). Also one moment where zibu or lila invites
   the kids to do something with them (jump, clap, count) in 4-5 short lines. Last: the lesson.
3. "dance" scene ({{"id": "dance", "type": "dance", "bg", "time": "sunset", "cast" with zibu, lila, guest}}):
   zibu "Dance party! Dance with us, friends!" with "pause": 14; lila or the guest one fun line with "pause": 10;
   zibu says goodbye ("See you next time, friends!") with "action": "wave"; lila "Bye-bye!" with "pause": 3.

Return ONLY JSON: {{"scenes": [song, recap, dance]}}"""


def prompt_revisar(s: dict) -> str:
    return f"""You are a strict reviewer for a YouTube channel for children aged 2 to 6. Review this episode script.
Reject it if: anything is inappropriate, scary, violent or dangerous to imitate; the story is incoherent or has no
clear problem and solution; the lesson is missing; the counting/colors/words shown do not match what is said;
the Spanish is not natural Latin American Spanish or does not match the English; the song does not rhyme or is
boring; it feels like a low-effort, repetitive template.
Answer ONLY JSON: {{"approved": true|false, "issues": ["short description of each problem"]}}

SCRIPT:
{json.dumps(s, ensure_ascii=False)}"""


def ejemplo_corto() -> str:
    """Una escena del episodio 1 como ejemplo de formato (el invitado ahi se llama "star"; ahora es "guest")."""
    ep = json.loads((STORIES / "ep001-lost-star.json").read_text(encoding="utf-8"))
    return json.dumps(ep["scenes"][2], ensure_ascii=False).replace('"star"', '"guest"')


def escribir(species: str, lesson: str, learn: str, anteriores: list[str]) -> dict:
    """Esquema -> escenas de la historia de dos en dos -> cancion, repaso y baile."""
    plan = gemini(prompt_esquema(species, lesson, learn, anteriores), max_tokens=8000)
    ejemplo = ejemplo_corto()
    historia: list[dict] = []
    n = len(plan["story"])
    for a in range(0, n, 2):
        idx = list(range(a, min(a + 2, n)))
        historia += gemini(prompt_escenas(plan, idx, historia, ejemplo))["scenes"][:len(idx)]
    final = gemini(prompt_final(plan, historia))["scenes"]
    titulo = {"id": "title", "type": "title", "bg": historia[0]["bg"], "time": historia[0]["time"],
              "cast": [{"who": "zibu", "x": 0.5}],
              "lines": [{"who": "narrator", "en": plan["title"]["en"] + "!", "es": "¡" + plan["title"]["es"].strip("¡!") + "!", "pause": 1.0}]}
    story = {k: plan[k] for k in ("slug", "title", "lesson", "guest", "thumb", "youtube")}
    story["scenes"] = [titulo] + historia + final
    for sc in story["scenes"]:  # el cast puede venir como lista de nombres
        sc["cast"] = [c if isinstance(c, dict) else {"who": c, "x": 0.3 + 0.2 * i} for i, c in enumerate(sc["cast"])]
    return story


# ---------------------------------------------------------------------------
def elegir(opciones: list[str], usados: list[str], ventana: int) -> str:
    libres = [o for o in opciones if o not in usados[-ventana:]] or opciones
    return random.choice(libres)


def main() -> None:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")) if LEDGER.exists() else []
    species = elegir(SPECIES, [x["guest"] for x in ledger], 5)
    lesson = elegir(LESSONS, [x["lesson"] for x in ledger], 14)
    learn = elegir(LEARN, [x["learn"] for x in ledger], 3)
    anteriores = [x["title"] for x in ledger[-40:]]
    print(f"Episodio nuevo: invitado {species} · leccion '{lesson}' · aprende '{learn}'")

    for intento in range(1, 4):
        try:
            story = escribir(species, lesson, learn, anteriores)
        except (KeyError, TypeError, ValueError, IndexError) as ex:
            print(f"   ! respuesta de Gemini incompleta ({type(ex).__name__}: {ex}), se repite")
            continue
        errores = validar(story)
        if errores:  # se corrige solo cada escena con errores (pedir el guion entero tarda demasiado)
            print(f"   ! validacion ({len(errores)} errores), se pide corregir: {errores[:3]}")
            por_escena: dict[int, list[str]] = {}
            for err in errores:
                m = re.match(r"escena (\d+)", err)
                if m:
                    por_escena.setdefault(int(m.group(1)), []).append(err)
            for i, errs in por_escena.items():
                try:
                    story["scenes"][i] = gemini(f"{formato()}\n\nFix these problems in this scene and return ONLY the "
                                                "corrected scene JSON:\n- " + "\n- ".join(errs) + "\n\nSCENE:\n"
                                                + json.dumps(story["scenes"][i], ensure_ascii=False))
                except (RuntimeError, ValueError) as ex:
                    print(f"   ! no se pudo corregir la escena {i}: {ex}")
            errores = validar(story)
        if errores:
            print(f"   ! sigue sin pasar la validacion: {errores[:5]}")
            continue
        review = gemini(prompt_revisar(story), max_tokens=4000, temperature=0.2)
        if not review.get("approved"):
            print(f"   ! rechazado por el revisor: {review.get('issues')}")
            continue
        n = len(ledger) + 2  # ep001 se hizo a mano y no esta en el registro
        story["id"] = f"ep{n:03d}-{re.sub(r'[^a-z0-9-]', '', story['slug'].lower())[:40]}"
        path = STORIES / f"{story['id']}.json"
        path.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
        ledger.append({"id": story["id"], "date": date.today().isoformat(), "title": story["title"]["en"],
                       "guest": species, "lesson": lesson, "learn": learn})
        LEDGER.write_text(json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Guion listo: {path.name} · {story['title']['en']} / {story['title']['es']}")
        if os.getenv("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
                f.write(f"episode={story['id']}\n")
        return
    sys.exit("No se pudo escribir un guion valido en 3 intentos")


if __name__ == "__main__":
    main()
