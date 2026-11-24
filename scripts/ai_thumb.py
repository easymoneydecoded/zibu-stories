"""Imagen de IA para la miniatura de un episodio: OpenAI (OPENAI_IMAGE_KEY, gpt-image) o Gemini (GEMINI_IMAGE_KEY).

  python scripts/ai_thumb.py stories/<id>.json      -> public/ep/<id>/thumb-ai.png (1280x720, sin texto)

Una sola imagen por episodio sirve para los 3 idiomas: el texto lo pone encima la composicion AIThumb de Remotion.
Referencia de personajes: public/ref/cast-<especie>.png (Still CastSheet), para que la IA respete el diseno de Zibu,
Lila y el invitado tal como salen en el video. Clave: GEMINI_IMAGE_KEY (proyecto de Google con facturacion, distinto
del de los guiones, que sigue en el plan gratuito). Si algo falla, sale sin error y el episodio usa la miniatura de
siempre (Still Thumbnail).
"""
import base64
import io
import json
import os
import sys
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
MODELS = [m for m in (os.getenv("AI_THUMB_MODEL"), "gemini-3.1-flash-image", "gemini-2.5-flash-image",
                      "gemini-3-pro-image") if m]
BG = {"garden": "a sunny flower garden with soft green hills", "forest": "a friendly bright forest clearing",
      "river": "a sparkling blue river bank with stepping stones", "hill": "a grassy hill top under a big sky",
      "sky": "a soft sky with fluffy clouds", "house": "a cozy colorful living room"}
TIME = {"day": "bright daylight", "sunset": "warm golden sunset light", "night": "a magical night with glowing stars"}


def key() -> str | None:
    k = os.getenv("GEMINI_IMAGE_KEY")
    env = BASE / ".env"
    if not k and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("GEMINI_IMAGE_KEY="):
                k = line.split("=", 1)[1].strip().strip('"')
    return k or None


def prompt(story: dict) -> str:
    guest = story["guest"].get("species") or story["guest"]["id"]
    name = story["guest"]["name"]["en"]
    hook = " ".join(story.get("hook", {}).get("en", [])) if isinstance(story.get("hook"), dict) else ""
    if not hook:
        hk = next((s for s in story["scenes"] if s.get("type") == "hook"), None)
        hook = " ".join(ln["en"] for ln in hk["lines"]) if hk else ""
    idx = int(story.get("thumb", {}).get("scene", 2))
    sc = story["scenes"][min(max(idx, 0), len(story["scenes"]) - 1)]
    props = sorted({(p.get("what") if isinstance(p, dict) else p) for s in story["scenes"] for p in s.get("props", [])} - {None})
    return (
        "Create a YouTube thumbnail image, 16:9 landscape, for a preschool cartoon (children aged 2-5).\n"
        f"Episode: \"{story['title']['en']}\". Exciting moment: {hook}\n"
        f"Characters, EXACTLY as in the reference image (same shapes, colors, eyes and proportions, flat 2D cartoon "
        f"style with soft shading): Zibu (round blue monster with big eyes and a yellow ball antenna), Lila (pink bunny "
        f"with a purple bow) and {name} the {guest}. Do not redesign them and do not add new characters.\n"
        f"Story objects to feature, big and clear: {', '.join(props[:3]) or 'none'}.\n"
        f"Setting: {BG.get(sc.get('bg'), 'a sunny garden')}, {TIME.get(sc.get('time'), 'bright daylight')}. "
        "Show a full, rich and cheerful landscape behind the characters, never a plain background: rolling green "
        "hills, colorful flowers and little bushes in the foreground, a few fluffy clouds and a smiling sun or soft "
        "light in the sky (in the upper-left only soft sky and light clouds).\n"
        "The main object keeps its normal, round, natural proportions (never stretched or squashed) and is shown "
        "COMPLETE, with a safety margin of at least 15% from every edge of the image.\n"
        "Composition: the upper-left area (about 45% wide, 40% tall) is ONLY plain sky: a title is added there "
        "later, so nothing important goes there (no object, no face, no balloon). The characters are LARGE, close-up, "
        "in the lower part and the right side, with very expressive faces (surprised or laughing). They INTERACT with "
        "the main story object, which is big and clearly visible on the RIGHT half of the image: someone holds it, "
        "reaches for it or points at it, so the action of the story is clear at a glance (for example a balloon "
        "escaping upwards on the right while Zibu stretches to catch it and the guest holds the string). Bright, "
        "saturated, cheerful colors, soft glow and depth, high contrast so it reads at a small size. The image will "
        "be cropped to 16:9: keep every important element (the object, faces, ears, antenna) away from the top and "
        "bottom 10% of the image.\n"
        "ABSOLUTELY NO text, letters, numbers, logos or watermarks anywhere in the image.")


def save(story: dict, raw: bytes, who: str, name: str = "thumb-ai.png", top: float = 0.5) -> Path:
    """top: donde cae el recorte 16:9 en vertical (0 = arriba, 0.5 = centrado)."""
    from PIL import Image
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size   # recorte central a 16:9 y 1280x720
    tw, th = (w, round(w * 9 / 16)) if w * 9 / 16 <= h else (round(h * 16 / 9), h)
    y0 = round((h - th) * top)
    img = img.crop(((w - tw) // 2, y0, (w + tw) // 2, y0 + th)).resize((1280, 720))
    out = BASE / "public" / "ep" / story["id"] / name
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"   . miniatura IA ({who}): {out.relative_to(BASE)}")
    return out


def env_key(name: str) -> str | None:
    k = os.getenv(name)
    env = BASE / ".env"
    if not k and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{name}="):
                k = line.split("=", 1)[1].strip().strip('"')
    return k or None


def openai_edit(image: Path, text: str) -> tuple[bytes, str] | None:
    """OpenAI (gpt-image): imagen nueva a partir de una de referencia. ~0,01-0,04 $ por imagen."""
    k = env_key("OPENAI_IMAGE_KEY")
    if not k:
        return None
    # el mismo modelo dos veces: a veces OpenAI devuelve un 500 pasajero
    for model in [m for m in (os.getenv("OPENAI_IMAGE_MODEL"), "gpt-image-1-mini", "gpt-image-1-mini") if m]:
        try:
            with open(image, "rb") as fh:
                r = requests.post("https://api.openai.com/v1/images/edits", timeout=300,
                                  headers={"Authorization": f"Bearer {k}"},
                                  files={"image[]": (image.name, fh, "image/png")},
                                  data={"model": model, "prompt": text, "size": "1536x1024",
                                        "quality": os.getenv("OPENAI_IMAGE_QUALITY", "medium"), "n": "1"})
        except requests.RequestException as e:
            print(f"   ! {model}: {e}")
            continue
        if r.status_code != 200:
            print(f"   ! {model}: HTTP {r.status_code} {r.text[:250]}")
            continue
        data = (r.json().get("data") or [{}])[0].get("b64_json")
        if data:
            return base64.b64decode(data), model
        print(f"   ! {model}: la respuesta no trae imagen")
    return None


def openai(story: dict, ref: Path) -> Path | None:
    # OpenAI genera en 3:2 y la miniatura es 16:9: se le manda la referencia en 3:2 con franjas grises arriba y abajo
    # (las que se recortan) para que coloque todo en la banda central y no corte ni deforme el objeto
    from PIL import Image, ImageDraw
    guia = Image.new("RGB", (1536, 1024), "#ffffff")
    guia.paste(Image.open(ref).convert("RGB").resize((1536, 864)), (0, 80))
    d = ImageDraw.Draw(guia)
    d.rectangle((0, 0, 1536, 79), fill="#d9d9d9")
    d.rectangle((0, 944, 1536, 1024), fill="#d9d9d9")
    marco = ref.parent.parent / "ep" / story["id"] / "ref-32.png"
    marco.parent.mkdir(parents=True, exist_ok=True)
    guia.save(marco)
    texto = prompt(story) + ("\nThe gray bands at the top and bottom of the reference image mark the part that will "
                             "be cut off: put ALL characters and objects inside the central area between them and "
                             "use the bands only for more sky (top) and grass or flowers (bottom).")
    hecho = openai_edit(marco, texto)
    marco.unlink(missing_ok=True)
    return save(story, *hecho) if hecho else None


def text_prompt(lines: list[str]) -> str:
    quoted = " / ".join(f'"{t}"' for t in lines)
    return ("A title logo for a preschool YouTube cartoon thumbnail, on a fully TRANSPARENT background (nothing else: "
            "no characters, no scenery, no frame, no box). Exactly these words with exactly this spelling, accents and "
            f"punctuation, on {len(lines)} lines: {quoted}. Chunky rounded bubbly 3D cartoon letters, first line bright "
            "yellow, second line white, both with a thick dark purple outline and a soft drop shadow, slightly tilted, "
            "big and centered, filling most of the image, like the title of a top preschool channel.")


def openai_title(lines: list[str]) -> bytes | None:
    """El titulo solo, como pegatina PNG con fondo transparente (se pega luego sobre la imagen base)."""
    k = env_key("OPENAI_IMAGE_KEY")
    if not k:
        return None
    for model in [m for m in (os.getenv("OPENAI_IMAGE_MODEL"), "gpt-image-1-mini", "gpt-image-1-mini") if m]:
        try:
            r = requests.post("https://api.openai.com/v1/images/generations", timeout=300,
                              headers={"Authorization": f"Bearer {k}"},
                              json={"model": model, "prompt": text_prompt(lines), "size": "1536x1024",
                                    "background": "transparent", "output_format": "png",
                                    "quality": os.getenv("OPENAI_IMAGE_QUALITY", "medium"), "n": 1})
        except requests.RequestException as e:
            print(f"   ! titulo {model}: {e}")
            continue
        if r.status_code != 200:
            print(f"   ! titulo {model}: HTTP {r.status_code} {r.text[:250]}")
            continue
        data = (r.json().get("data") or [{}])[0].get("b64_json")
        if data:
            return base64.b64decode(data)
    return None


def norm(t: str) -> str:
    return "".join(ch for ch in t.upper() if ch.isalnum())


def verify(img: bytes, lines: list[str]) -> bool:
    """Gemini (gratis) lee el titulo de la imagen: tiene que coincidir letra a letra (acentos incluidos)."""
    k = env_key("GEMINI_API_KEY")
    if not k:
        print("   ! sin GEMINI_API_KEY no se puede comprobar el texto: no se usa la version con texto")
        return False
    body = {"contents": [{"parts": [
        {"text": "Transcribe exactly the title text written in this image, keeping every accent and punctuation mark. "
                 "Answer only with the text, nothing else."},
        {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(img).decode()}}]}]}
    for model in ("gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"):
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              params={"key": k}, json=body, timeout=120)
            if r.status_code != 200:
                continue
            leido = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
            ok = norm(leido) == norm(" ".join(lines))
            print(f"   . comprobacion ({model}): {'OK' if ok else 'NO coincide'} -> {leido.strip()[:80]!r}")
            return ok
        except (requests.RequestException, KeyError, IndexError):
            continue
    print("   ! no pude comprobar el texto con Gemini")
    return False


def colocar(img, pega):
    """Busca donde pegar el titulo (arriba, mitad izquierda) tapando lo minimo: solo cielo y nubes, no el sol, ni
    antenas, ni personajes, ni el objeto. Prueba varias posiciones y tamanos y se queda con el mas grande que tape
    poco; si nada queda limpio, el que menos tape."""
    from PIL import Image
    peq = img.convert("RGB").resize((320, 180))
    px = peq.load()
    libre = [[(b > 200 and g > 160) or (r > 215 and g > 215 and b > 215) for x in range(320)
              for r, g, b in [px[x, y]]] for y in range(180)]
    mejor = None
    for maxw in (600, 540, 480, 420):
        esc = min(maxw / pega.width, 270 / pega.height)
        w, h = round(pega.width * esc), round(pega.height * esc)
        alfa = pega.getchannel("A").resize((max(1, w // 4), max(1, h // 4)))
        a = alfa.load()
        opacos = [(i, j) for j in range(alfa.height) for i in range(alfa.width) if a[i, j] > 60]
        for y in range(12, 200, 12):
            for x in range(20, 700 - w if 700 - w > 20 else 21, 16):
                tapa = sum(not libre[min(179, y // 4 + j)][min(319, x // 4 + i)] for i, j in opacos) / max(1, len(opacos))
                nota = tapa + y / 4000          # a igualdad, mas arriba
                if mejor is None or nota < mejor[0]:
                    mejor = (nota, maxw, x, y)
            if mejor and mejor[0] < 0.03:
                break
        if mejor and mejor[0] < 0.03:
            break
    _, maxw, x, y = mejor
    esc = min(maxw / pega.width, 270 / pega.height)
    return pega.resize((round(pega.width * esc), round(pega.height * esc))), (x, y)


def texted(story: dict, base: Path, langs=("es", "pt", "en"), tries: int = 2) -> None:
    """Version con el titulo dibujado por la IA (pegatina transparente sobre la imagen base, que no se toca), una por
    idioma, solo si Gemini confirma que el texto esta bien escrito."""
    from PIL import Image
    for lang in langs:
        lines = (story.get("thumb") or {}).get(lang)
        if not lines:
            continue
        if lang != "es":   # los signos de apertura solo existen en espanol ("¡MÃOS MACIAS!" en portugues esta mal)
            lines = [l.replace("¡", "").replace("¿", "").strip() for l in lines]
        for _ in range(tries):
            raw = openai_title(lines)
            if not raw:
                break
            pega = Image.open(io.BytesIO(raw)).convert("RGBA")
            caja = pega.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
            if not caja:
                continue
            pega = pega.crop(caja)
            img = Image.open(base).convert("RGBA").resize((1280, 720))
            pega, pos = colocar(img, pega)
            img.alpha_composite(pega, pos)
            buf = io.BytesIO()
            img.convert("RGB").save(buf, "PNG")
            if verify(buf.getvalue(), lines):
                out = BASE / "public" / "ep" / story["id"] / f"thumb-ai-{lang}.png"
                out.write_bytes(buf.getvalue())
                print(f"   . miniatura IA con titulo ({lang}): {out.relative_to(BASE)}")
                break


def generate(story_path: str) -> Path | None:
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    guest = story["guest"].get("species") or story["guest"]["id"]
    ref = BASE / "public" / "ref" / f"cast-{guest}.png"
    if ref.exists() and (hecho := openai(story, ref)):
        if os.getenv("AI_THUMB_TEXT", "1") == "1":
            texted(story, hecho)
        return hecho
    k = key()
    if not k:
        print("   . sin clave de imagen que funcione: miniatura de siempre")
        return None
    parts = [{"text": prompt(story)}]
    if ref.exists():
        parts.append({"inline_data": {"mime_type": "image/png", "data": base64.b64encode(ref.read_bytes()).decode()}})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE", "TEXT"], "imageConfig": {"aspectRatio": "16:9"}}}
    for model in MODELS:
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              params={"key": k}, json=body, timeout=240)
        except requests.RequestException as e:
            print(f"   ! {model}: {e}")
            continue
        if r.status_code != 200:
            print(f"   ! {model}: HTTP {r.status_code} {r.text[:200]}")
            continue
        for p in r.json().get("candidates", [{}])[0].get("content", {}).get("parts", []):
            data = (p.get("inlineData") or p.get("inline_data") or {}).get("data")
            if data:
                return save(story, base64.b64decode(data), model)
        print(f"   ! {model}: la respuesta no trae imagen")
    return None


if __name__ == "__main__":
    # python scripts/ai_thumb.py stories/X.json            -> imagen base + version con titulo (es, en; pt si ya esta)
    # python scripts/ai_thumb.py stories/X.json --text pt  -> solo la version con titulo de ese idioma (el pt se
    #                                                         traduce en su job de render, despues de la base)
    if len(sys.argv) > 3 and sys.argv[2] == "--text":
        st = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
        b = BASE / "public" / "ep" / st["id"] / "thumb-ai.png"
        if b.exists():
            texted(st, b, langs=(sys.argv[3],))
    else:
        generate(sys.argv[1])
