"""Banner y avatar de los canales hechos con IA (OpenAI gpt-image), iguales en los 3 idiomas salvo el texto.

  python scripts/branding_ai.py scene     -> out/canal-ia/banner-base.png (escena sin texto)
  python scripts/branding_ai.py titles    -> out/canal-ia/banner-<lang>.jpg (escena + nombre del canal, comprobado)
  python scripts/branding_ai.py avatar    -> out/canal-ia/avatar.png (Zibu, sin texto: igual en los 3 canales)

El banner de YouTube es 2560x1440 pero en el movil solo se ve la franja central de 1546x423: ahi van Zibu, Lila y el
nombre; alrededor (lo que se ve en la tele) el resto de amigos y el paisaje. Usa las mismas piezas que ai_thumb.py.
"""
import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ai_thumb as A  # noqa: E402

BASE = A.BASE
OUT = BASE / "out" / "canal-ia"
NAME = {"es": ["Zibu", "y sus amigos"], "pt": ["Zibu", "e seus amigos"], "en": ["Zibu", "and Friends"]}
REFS = ["puppy", "kitten", "duckling", "frog"]   # Zibu y Lila salen en todas; cada una trae un amigo distinto
STYLE = ("Polished 2D cartoon style with soft shading, exactly like the reference images: same character designs, "
         "shapes, colors and eyes. Do not redesign them. Bright, saturated, cheerful colors, soft glow and depth. "
         "ABSOLUTELY NO text, letters, numbers or logos.")


def edit_multi(refs: list[Path], prompt: str, size: str = "1536x1024", quality: str = "high",
               transparent: bool = False) -> bytes | None:
    import os
    import requests
    k = A.env_key("OPENAI_IMAGE_KEY")
    files = [("image[]", (p.name, open(p, "rb"), "image/png")) for p in refs]
    import time
    for intento in range(5):
        files = [("image[]", (p.name, open(p, "rb"), "image/png")) for p in refs]
        r = requests.post("https://api.openai.com/v1/images/edits", timeout=400, headers={"Authorization": f"Bearer {k}"},
                          files=files, data={"model": os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1-mini"),
                                             "prompt": prompt, "size": size, "quality": quality, "n": "1",
                                             **({"background": "transparent", "output_format": "png"}
                                                if transparent else {})})
        if r.status_code == 200:
            import base64
            return base64.b64decode(r.json()["data"][0]["b64_json"])
        print(f"   ! HTTP {r.status_code} {r.text[:200]}")
        if r.status_code == 429 and "rate" in r.text.lower():   # demasiado rapido: esperar y repetir
            time.sleep(25 * (intento + 1))
    return None


def scene() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    # guia 3:2 con franjas grises arriba y abajo (lo que se recorta a 16:9), como en las miniaturas
    guia = Image.new("RGB", (1536, 1024), "#ffffff")
    guia.paste(Image.open(BASE / "public" / "ref" / "cast-puppy.png").convert("RGB").resize((1536, 864)), (0, 80))
    d = ImageDraw.Draw(guia)
    d.rectangle((0, 0, 1536, 79), fill="#d9d9d9")
    d.rectangle((0, 944, 1536, 1024), fill="#d9d9d9")
    guia_p = OUT / "guia.png"
    guia.save(guia_p)
    refs = [guia_p] + [BASE / "public" / "ref" / f"cast-{s}.png" for s in REFS[1:]]
    prompt = (
        "A wide, magical, joyful YouTube channel banner for a preschool cartoon called Zibu. Scene: a sunny fantasy "
        "meadow with a big bright rainbow arching across the sky, fluffy clouds, a smiling sun, rolling green hills, "
        "colorful flowers, little trees and sparkles. CHARACTERS: Zibu (round blue monster with big eyes and a yellow "
        "ball antenna) on the LEFT of the central strip, waving happily; Lila (pink bunny with a purple bow) on the "
        "RIGHT of the central strip, smiling; and their friends (the puppy, the kitten, the duckling and the frog from "
        "the reference images) playing further out on the far left and far right edges of the meadow. LAYOUT (very "
        "important): the image will be cropped to 16:9 (the gray bands of the first reference are cut off). Phones "
        "only show the horizontal strip in the middle (about 36% of the height and 60% of the width, centered): Zibu "
        "and Lila must be fully inside that strip, at its left and right ends, and the CENTER of the strip must stay "
        "free (just the rainbow and soft sky) because the channel name goes there. " + STYLE)
    raw = edit_multi(refs, prompt)
    guia_p.unlink(missing_ok=True)
    if not raw:
        raise SystemExit("no se pudo generar la escena")
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    th = round(w * 9 / 16)
    img = img.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((2560, 1440), Image.LANCZOS)
    img.save(OUT / "banner-base.png")
    print("escena:", OUT / "banner-base.png")


def titles(langs=("es", "pt", "en")) -> None:
    base = Image.open(OUT / "banner-base.png").convert("RGBA")
    for lang in langs:
        lines = NAME[lang]
        for _ in range(3):
            raw = A.openai_title(lines)
            if not raw:
                break
            pega = Image.open(io.BytesIO(raw)).convert("RGBA")
            caja = pega.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox()
            pega = pega.crop(caja)
            # en la franja segura del movil (1546x423 centrada): el nombre en el centro, sin tapar a Zibu ni a Lila
            esc = min(700 / pega.width, 360 / pega.height)
            pega = pega.resize((round(pega.width * esc), round(pega.height * esc)), Image.LANCZOS)
            img = base.copy()
            img.alpha_composite(pega, ((2560 - pega.width) // 2, (1440 - pega.height) // 2))
            buf = io.BytesIO()
            img.convert("RGB").save(buf, "PNG")
            if A.verify(buf.getvalue(), lines):
                out = OUT / f"banner-{lang}.jpg"
                img.convert("RGB").save(out, "JPEG", quality=90)   # YouTube: maximo 6 MB
                print(f"banner {lang}: {out}")
                break


def avatar() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prompt = ("A round YouTube channel profile picture: a close-up of Zibu (the round blue monster with big eyes and a "
              "yellow ball antenna from the reference image), big happy smile, waving, centered and filling most of a "
              "circle, on a warm sunny yellow-orange radial background with soft light rays and a few sparkles. "
              "Everything important inside the central circle (the corners will be cut). " + STYLE)
    raw = edit_multi([BASE / "public" / "ref" / "cast-puppy.png"], prompt, size="1024x1024")
    if not raw:
        raise SystemExit("no se pudo generar el avatar")
    Image.open(io.BytesIO(raw)).convert("RGB").resize((800, 800), Image.LANCZOS).save(OUT / "avatar.png")
    print("avatar:", OUT / "avatar.png")


def recorte(raw: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    return im.crop(im.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox())


def paisaje() -> Image.Image:
    prompt = ("A wide, magical, joyful landscape for a preschool cartoon channel banner, WITHOUT any characters or "
              "animals: a sunny fantasy meadow with a big bright rainbow arching across the whole sky, fluffy clouds, a "
              "smiling sun on the upper right, rolling green hills, colorful flowers in the foreground, little round "
              "trees and sparkles. Polished 2D cartoon style with soft shading, bright saturated colors. Keep the "
              "middle of the image calm (soft sky under the rainbow). ABSOLUTELY NO text, letters or logos.")
    raw = edit_multi([BASE / "public" / "ref" / "cast-puppy.png"], prompt)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size
    th = round(w * 9 / 16)
    return img.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((2560, 1440), Image.LANCZOS).convert("RGBA")


def pegatina(ref: str, quien: str) -> Image.Image:
    prompt = (f"A sticker of {quien}, full body from head to feet, standing, waving happily with a big smile, looking at "
              "the viewer, on a fully TRANSPARENT background (no scenery, no shadow box, no frame). " + STYLE)
    return recorte(edit_multi([BASE / "public" / "ref" / f"cast-{ref}.png"], prompt, size="1024x1024",
                              transparent=True))


def poner(img: Image.Image, peg: Image.Image, alto: int, cx: int, pie: int) -> None:
    from PIL import ImageFilter
    peg = peg.resize((round(peg.width * alto / peg.height), alto), Image.LANCZOS)
    sombra = Image.new("RGBA", img.size, (0, 0, 0, 0))   # sombra suave bajo los pies: que pisen el suelo
    ImageDraw.Draw(sombra).ellipse((cx - peg.width * 0.42, pie - 26, cx + peg.width * 0.42, pie + 14),
                                   fill=(30, 70, 20, 110))
    img.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(10)))
    img.alpha_composite(peg, (cx - peg.width // 2, pie - alto))


def montar() -> None:
    """Paisaje + pegatinas colocadas a mano: Zibu y Lila enteros dentro de la franja del movil (1546x423 centrada,
    y 508-931), el nombre en el centro de esa franja y los demas amigos fuera (se ven en la tele y el ordenador)."""
    OUT.mkdir(parents=True, exist_ok=True)
    piezas = OUT / "piezas"
    piezas.mkdir(exist_ok=True)

    def cache(nombre, hacer):   # cada pieza se genera una vez; para recolocar no hace falta pagar otra vez
        f = piezas / f"{nombre}.png"
        if not f.exists():
            hacer().save(f)
        return Image.open(f).convert("RGBA")

    img = cache("paisaje", paisaje)
    # el suelo del paisaje queda algo bajo: se amplia un 12 % anclado abajo para que la colina suba hasta los pies de
    # Zibu y Lila (que no floten en el cielo)
    g = img.resize((round(2560 * 1.12), round(1440 * 1.12)), Image.LANCZOS)
    img = g.crop(((g.width - 2560) // 2, g.height - 1440, (g.width - 2560) // 2 + 2560, g.height))
    zibu = cache("zibu", lambda: pegatina("puppy", "Zibu, the round blue monster with big eyes and a yellow ball antenna"))
    lila = cache("lila", lambda: pegatina("puppy", "Lila, the pink bunny with a purple bow"))
    amigos = [cache(s, lambda s=s: pegatina(s, f"the {s} from the reference image (only the {s}, not Zibu or Lila)"))
              for s in REFS]
    poner(img, zibu, 410, 700, 930)
    poner(img, lila, 415, 1870, 930)
    for (cx, alto), peg in zip(((150, 330), (390, 300), (2170, 300), (2410, 320)), amigos):
        poner(img, peg, alto, cx, 1230)
    img.save(OUT / "banner-base.png")
    print("banner montado:", OUT / "banner-base.png")


if __name__ == "__main__":
    {"scene": scene, "montar": montar, "titles": titles, "avatar": avatar}[sys.argv[1]]()
