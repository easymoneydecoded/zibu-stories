"""Piezas dibujadas con IA para el estilo nuevo de los episodios (EpisodeV2): personajes con varias caras, fondos y
objetos, todos como imagenes con fondo transparente (salvo los fondos) en public/v2/.

  python scripts/v2_assets.py char zibu|lila|<especie>   -> public/v2/chars/<quien>/{idle,talk,blink,surprised,sad}.png
  python scripts/v2_assets.py bg garden day              -> public/v2/bg/garden-day.png
  python scripts/v2_assets.py prop balloon               -> public/v2/props/balloon.png

Cada personaje se genera primero de pie y sonriendo (idle) a partir de su hoja de referencia (public/ref) y las demas
caras se piden EDITANDO esa imagen ("solo cambia la boca..."), para que se parezcan entre si.
"""
import io
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from branding_ai import BASE, edit_multi  # noqa: E402

V2 = BASE / "public" / "v2"
STYLE = ("Polished 2D cartoon style for a preschool show, soft shading and gentle highlights, bright saturated colors, "
         "clean shapes, exactly like the reference image (same design, colors, eyes and proportions; do not redesign). "
         "NO text.")
DESC = {"zibu": ("Zibu, the round blue monster: his head and body are ONE single round ball (no neck, no torso), "
                 "with big eyes, a yellow ball antenna on top, two small arms and two small feet"),
        "lila": "Lila, the pink bunny with long ears and a purple bow on one ear (the bow is always there)"}
CARAS = {
    "talk": "mouth wide open as if talking happily (the rest of the face the same)",
    "blink": "both eyes closed in a happy relaxed way, mouth closed smile",
    "surprised": "surprised face: eyes wide open, round open mouth, eyebrows raised",
    "sad": "sad face: eyebrows down and worried, small frown, mouth closed",
}


def recorte(raw: bytes) -> Image.Image:
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    return im.crop(im.getchannel("A").point(lambda a: 255 if a > 24 else 0).getbbox())


def char(quien: str) -> None:
    out = V2 / "chars" / quien
    out.mkdir(parents=True, exist_ok=True)
    especie = "puppy" if quien in DESC else quien
    ref = BASE / "public" / "ref" / f"cast-{especie}.png"
    desc = DESC.get(quien, f"the {quien} from the reference image (only the {quien}, not Zibu or Lila)")
    base_p = out / "idle.png"
    if not base_p.exists():
        raw = edit_multi([ref], f"A character sticker of {desc}: full body from head to feet, front view, standing "
                                "naturally, gentle happy smile with the mouth closed, eyes open looking at the viewer, "
                                "arms relaxed, on a fully TRANSPARENT background (no scenery, no shadow, no frame). " + STYLE,
                         size="1024x1024", quality="medium", transparent=True)
        recorte(raw).save(base_p)
        print("  idle", quien)
    for cara, que in CARAS.items():
        f = out / f"{cara}.png"
        if f.exists():
            continue
        raw = edit_multi([base_p], "Redraw EXACTLY this same character with the same pose, size, framing, colors and "
                                   f"style. ONLY change the face: {que}. Fully TRANSPARENT background. " + STYLE,
                         size="1024x1024", quality="medium", transparent=True)
        recorte(raw).save(f)
        print(" ", cara, quien)


ORDEN = ["idle", "talk", "blink", "surprised", "sad"]


def trocear(im: Image.Image, n: int) -> list[Image.Image]:
    """Separa n figuras puestas en fila sobre fondo transparente, por las columnas vacias entre ellas."""
    a = im.getchannel("A").point(lambda v: 255 if v > 24 else 0)
    w, h = a.size
    px = a.load()
    llenas = [any(px[x, y] for y in range(0, h, 2)) for x in range(w)]
    trozos, ini = [], None
    for x, v in enumerate(llenas + [False]):
        if v and ini is None:
            ini = x
        elif not v and ini is not None:
            if x - ini > 25:
                trozos.append((ini, x))
            ini = None
    if len(trozos) != n:
        raise ValueError(f"esperaba {n} figuras y salen {len(trozos)}")
    anchos = sorted(x1 - x0 for x0, x1 in trozos)
    mediana = anchos[len(anchos) // 2]
    for x0, x1 in (trozos[0], trozos[-1]):   # pegada al borde Y mas estrecha que las demas: esta cortada
        if (x0 <= 3 or x1 >= w - 3) and (x1 - x0) < 0.85 * mediana:
            raise ValueError("una figura sale cortada por el borde")
    out = []
    for x0, x1 in trozos:
        t = im.crop((x0, 0, x1, h))
        out.append(t.crop(t.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()))
    return out


def sheet(quien: str, intentos: int = 3) -> None:
    """Las 5 caras en UNA sola imagen (misma pose y tamano), luego troceadas: asi no salta el dibujo al cambiar."""
    out = V2 / "chars" / quien
    out.mkdir(parents=True, exist_ok=True)
    especie = "puppy" if quien in DESC else quien
    ref = BASE / "public" / "ref" / f"cast-{especie}.png"
    desc = DESC.get(quien, f"the {quien} from the reference image (only the {quien}, not Zibu or Lila)")
    prompt = (f"A character expression sheet of {desc}: the SAME character drawn 5 times in one horizontal row, "
              "well separated with empty space between them and a wide empty margin before the first and after the "
              "last one (nothing touches the edges of the image), all exactly the same size, the same full-body "
              "standing pose facing the viewer (FRONT view in all 5, never in profile; arms relaxed, feet visible) "
              "and the same position; only the face changes: 1) gentle happy smile, mouth closed; 2) mouth wide open, "
              "talking happily; 3) eyes closed, smiling; 4) surprised, eyes wide and round open mouth; 5) sad, worried "
              "eyebrows, small frown. Every figure has ALL its parts (ears, bow, antenna...). "
              "Fully TRANSPARENT background, no scenery, no text, no numbers, no shadows. " + STYLE)
    for _ in range(intentos):
        raw = edit_multi([ref], prompt, size="1536x1024", quality="high", transparent=True)
        n_raw = len(list((BASE / "out").glob(f"v2-raw-{quien}-*.png")))
        (BASE / "out" / f"v2-raw-{quien}-{n_raw}.png").write_bytes(raw)   # para revisar sin volver a pagar
        try:
            figs = trocear(Image.open(io.BytesIO(raw)).convert("RGBA"), 5)
        except ValueError as e:
            print("   !", e)
            continue
        alto = max(f.height for f in figs)
        for cara, f in zip(ORDEN, figs):
            # todas a la misma altura de lienzo, apoyadas abajo: al cambiar de cara no se mueve nada
            lienzo = Image.new("RGBA", (max(g.width for g in figs), max(alto, f.height)), (0, 0, 0, 0))
            lienzo.alpha_composite(f, ((lienzo.width - f.width) // 2, lienzo.height - f.height))
            lienzo.save(out / f"{cara}.png")
        print("  hoja", quien)
        return
    raise SystemExit(f"no salio la hoja de {quien}")


BGS = {"garden": "a sunny flower garden with soft rolling green hills, colorful flowers and little bushes",
       "forest": "a friendly bright forest clearing with round trees and mushrooms",
       "river": "a sparkling blue river with stepping stones and grassy banks",
       "hill": "a big grassy hill top under a wide sky", "beach": "a sunny beach with sand, sea and a palm tree",
       "sky": "a dreamy sky above the clouds", "room": "a cozy colorful kids' bedroom with a bed, rug and window"}
TIMES = {"day": "bright daylight with a smiling sun and fluffy clouds", "sunset": "warm golden sunset light",
         "night": "a magical night with a smiling moon and twinkling stars"}


def bg(lugar: str, momento: str) -> None:
    (V2 / "bg").mkdir(parents=True, exist_ok=True)
    raw = edit_multi([BASE / "public" / "ref" / "cast-puppy.png"],
                     f"A wide background illustration for a preschool cartoon, WITHOUT any characters or animals: "
                     f"{BGS[lugar]}, {TIMES[momento]}. The bottom 25% is open flat ground where characters will stand "
                     "(no big objects there). Polished 2D cartoon style with soft shading, bright saturated colors, depth. "
                     "ABSOLUTELY NO text.", quality="high")
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    th = round(w * 9 / 16)
    im.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((1920, 1080), Image.LANCZOS).save(
        V2 / "bg" / f"{lugar}-{momento}.png")
    print("  fondo", lugar, momento)


def prop(que: str) -> None:
    (V2 / "props").mkdir(parents=True, exist_ok=True)
    raw = edit_multi([BASE / "public" / "ref" / "cast-puppy.png"],
                     f"A single {que} object sticker for a preschool cartoon (a red one if it can have colors), centered, "
                     "on a fully TRANSPARENT background, no characters. Polished 2D cartoon style with soft shading. NO text.",
                     size="1024x1024", quality="medium", transparent=True)
    recorte(raw).save(V2 / "props" / f"{que}.png")
    print("  objeto", que)


if __name__ == "__main__" and sys.argv[1] not in ("faces", "pairs"):
    cmd = sys.argv[1]
    {"char": lambda: char(sys.argv[2]), "sheet": lambda: sheet(sys.argv[2]), "bg": lambda: bg(sys.argv[2], sys.argv[3]),
     "prop": lambda: prop(sys.argv[2])}[cmd]()


# ---------------------------------------------------------------------------------------------------------------
# Caras por zona (2026-11-25): una figura de cuerpo entero y, para cada expresion, la IA solo redibuja la cara
# (mascara) y se pega esa zona encima. El cuerpo es identico en todas: al animar no salta nada.
# ---------------------------------------------------------------------------------------------------------------
CARAS2 = {"talk": "mouth wide open, talking happily", "blink": "both eyes closed, smiling",
          "surprised": "surprised: eyes wide, round open mouth, eyebrows up", "sad": "sad: worried eyebrows, small frown",
          "laugh": "laughing with joy, big open smile, happy closed eyes"}


def caja_cara(img_path: Path) -> tuple[int, int, int, int]:
    """Gemini (gratis) marca la zona de la cara (ojos, cejas, boca) en coordenadas 0-1000."""
    import base64
    import json
    import re
    import requests
    import ai_thumb as A
    k = A.env_key("GEMINI_API_KEY")
    body = {"contents": [{"parts": [
        {"text": "Give the bounding box of this cartoon character's FACE features area (eyebrows, eyes, nose and mouth "
                 "only, not ears or antenna) as JSON [ymin, xmin, ymax, xmax] in 0-1000 coordinates. Only the JSON."},
        {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(img_path.read_bytes()).decode()}}]}]}
    for model in ("gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite"):
        r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                          params={"key": k}, json=body, timeout=90)
        if r.status_code == 200:
            txt = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
            nums = [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?", txt)][:4]
            if len(nums) == 4:
                y0, x0, y1, x1 = nums
                return x0, y0, x1, y1
    raise SystemExit("Gemini no marco la cara")


def faces(quien: str) -> None:
    import os
    import requests
    from PIL import ImageDraw, ImageFilter
    out = V2 / "chars" / quien
    out.mkdir(parents=True, exist_ok=True)
    especie = "puppy" if quien in DESC else quien
    ref = BASE / "public" / "ref" / f"cast-{especie}.png"
    desc = DESC.get(quien, f"the {quien} from the reference image (only the {quien}, not Zibu or Lila)")
    lienzo_p = out / "idle.png"
    if not lienzo_p.exists():
        raw = edit_multi([ref], f"A character sticker of {desc}: full body from head to feet, FRONT view, standing, "
                                "arms relaxed, gentle happy smile with the mouth closed, eyes open looking at the viewer, "
                                "centered with empty margin all around (nothing touches the edges), on a fully "
                                "TRANSPARENT background, no scenery, no shadow. " + STYLE,
                         size="1024x1024", quality="high", transparent=True)
        fig = recorte(raw)
        esc = min(880 / fig.height, 880 / fig.width)
        fig = fig.resize((round(fig.width * esc), round(fig.height * esc)), Image.LANCZOS)
        lienzo = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
        lienzo.alpha_composite(fig, ((1024 - fig.width) // 2, 1004 - fig.height))
        lienzo.save(lienzo_p)
        print("  idle", quien)
    base = Image.open(lienzo_p).convert("RGBA")
    x0, y0, x1, y1 = caja_cara(lienzo_p)
    m = 0.06   # un poco de margen alrededor de la cara
    caja = (round((x0 / 1000 - m) * 1024), round((y0 / 1000 - m) * 1024),
            round((x1 / 1000 + m) * 1024), round((y1 / 1000 + m) * 1024))
    mask = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))
    ImageDraw.Draw(mask).ellipse(caja, fill=(0, 0, 0, 0))
    mask_p = out / "_mask.png"
    mask.save(mask_p)
    k = os.environ["OPENAI_IMAGE_KEY"]
    for cara, que in CARAS2.items():
        f = out / f"{cara}.png"
        if f.exists():
            continue
        for _ in range(2):
            with open(lienzo_p, "rb") as im_f, open(mask_p, "rb") as mk_f:
                r = requests.post("https://api.openai.com/v1/images/edits", timeout=300,
                                  headers={"Authorization": f"Bearer {k}"},
                                  files=[("image[]", ("idle.png", im_f, "image/png")),
                                         ("mask", ("mask.png", mk_f, "image/png"))],
                                  data={"model": "gpt-image-1-mini", "size": "1024x1024", "quality": "medium",
                                        "background": "transparent", "output_format": "png", "n": "1",
                                        "prompt": f"Same character, same drawing, same style and colors. Only redraw the "
                                                  f"face expression: {que}. Keep everything outside the face identical."})
            if r.status_code == 200:
                break
            print("   !", r.status_code, r.text[:150])
        else:
            continue
        import base64
        nueva = Image.open(io.BytesIO(base64.b64decode(r.json()["data"][0]["b64_json"]))).convert("RGBA").resize((1024, 1024))
        # solo la zona de la cara (con borde suave) sobre la figura original
        suave = Image.new("L", (1024, 1024), 0)
        ImageDraw.Draw(suave).ellipse(caja, fill=255)
        suave = suave.filter(ImageFilter.GaussianBlur(10))
        res = base.copy()
        res.paste(nueva, (0, 0), Image.composite(suave, Image.new("L", (1024, 1024), 0), nueva.getchannel("A")))
        res.save(f)
        print(" ", cara, quien)
    mask_p.unlink(missing_ok=True)


if __name__ == "__main__" and sys.argv[1] == "faces":
    faces(sys.argv[2])


# ---------------------------------------------------------------------------------------------------------------
# Parejas de caras (2026-11-25, v3): cada expresion con boca CERRADA y ABIERTA en la misma imagen, para que al hablar
# solo cambie la boca. Una imagen por expresion; si una figura toca el borde de la imagen se repite (nada de espejos).
# ---------------------------------------------------------------------------------------------------------------
EXPR = {
    "happy": "happy, gentle smile",
    "neutral": "calm and neutral, relaxed face",
    "surprised": "surprised, eyes wide open, eyebrows raised",
    "sad": "sad, worried eyebrows",
    "laugh": "laughing with joy, happy squinting eyes",
}


def toca_borde(im: Image.Image, cajas: list[tuple[int, int]]) -> bool:
    """Una figura con pixeles opacos en el borde de la imagen esta cortada."""
    a = im.getchannel("A").point(lambda v: 255 if v > 128 else 0)
    w, h = a.size
    px = a.load()
    borde = sum(1 for y in range(h) for x in (0, 1, w - 2, w - 1) if px[x, y]) + \
        sum(1 for x in range(w) for y in (0, 1, h - 2, h - 1) if px[x, y])
    return borde > 15


def pareja(quien: str, expr: str, refs: list[Path], intentos: int = 4) -> list[Image.Image]:
    desc = DESC.get(quien, f"the {quien} from the reference image (only the {quien}; it has no bow or accessories)")
    extra = expr == "happy"
    n = 3 if extra else 2
    caras = ("1) mouth CLOSED; 2) mouth OPEN as if talking (the only difference is the mouth)" +
             ("; 3) eyes closed in a happy blink, mouth closed" if extra else ""))
    prompt = (f"{n} drawings of {desc}, side by side in one row, IDENTICAL in everything (same size, same full-body "
              f"standing pose facing the viewer, same position, same expression: {EXPR[expr]}) except the mouth: "
              f"{caras}. Big empty margin around every figure: NOTHING may touch or cross the edges of the image "
              "(ears, antenna and feet fully inside, at least 60 pixels from every edge). "
              "Fully TRANSPARENT background, no scenery, no text, no shadows. " + STYLE)
    for _ in range(intentos):
        raw = edit_multi(refs, prompt, size="1536x1024", quality="high", transparent=True)
        im = Image.open(io.BytesIO(raw)).convert("RGBA")
        n_raw = len(list((BASE / "out").glob(f"v3-raw-{quien}-*.png")))
        im.save(BASE / "out" / f"v3-raw-{quien}-{n_raw}.png")
        if toca_borde(im, []):
            print(f"   ! {quien} {expr}: figura cortada por el borde, repito")
            continue
        try:
            a = im.getchannel("A").point(lambda v: 255 if v > 24 else 0)
            px = a.load()
            w, h = a.size
            llenas = [any(px[x, y] for y in range(0, h, 2)) for x in range(w)]
            trozos, ini = [], None
            for x, v in enumerate(llenas + [False]):
                if v and ini is None:
                    ini = x
                elif not v and ini is not None:
                    if x - ini > 40:
                        trozos.append((ini, x))
                    ini = None
            if len(trozos) != n:
                raise ValueError(f"salen {len(trozos)} figuras")
            figs = []
            for x0, x1 in trozos:
                t = im.crop((x0, 0, x1, h))
                figs.append(t.crop(t.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()))
            return figs
        except ValueError as e:
            print(f"   ! {quien} {expr}: {e}, repito")
    raise SystemExit(f"no salio {quien} {expr}")


def pairs(quien: str) -> None:
    """public/v2/chars3/<quien>/<expr>_closed.png, <expr>_open.png y happy_blink.png, todas en el mismo lienzo."""
    out = V2 / "chars3" / quien
    out.mkdir(parents=True, exist_ok=True)
    especie = "puppy" if quien in DESC else quien
    refs = [BASE / "public" / "ref" / f"cast-{especie}.png"]
    figs_all = {}
    for expr in EXPR:
        if (out / f"{expr}_closed.png").exists():
            continue
        # despues de la primera, la referencia es SOLO su propia cara contenta (la hoja de referencia trae a Zibu y Lila
        # y la IA mezclaba rasgos: orejas de conejo en el cerdito)
        figs = pareja(quien, expr, [out / "happy_closed.png"] if (out / "happy_closed.png").exists() else refs)
        alto = max(f.height for f in figs)   # la pareja a la misma altura: al hablar el personaje no encoge
        figs = [f.resize((round(f.width * alto / f.height), alto), Image.LANCZOS) for f in figs]
        nombres = [f"{expr}_closed", f"{expr}_open"] + (["happy_blink"] if expr == "happy" else [])
        # cada pareja en un lienzo comun (mismo ancho y alto, apoyada abajo y centrada): al hablar no se mueve nada
        W, H = max(f.width for f in figs), max(f.height for f in figs)
        for nombre, f in zip(nombres, figs):
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            lienzo.alpha_composite(f, ((W - f.width) // 2, H - f.height))
            lienzo.save(out / f"{nombre}.png")
            figs_all[nombre] = lienzo
        print(f"  {quien} {expr}")


if __name__ == "__main__" and sys.argv[1] == "pairs":
    pairs(sys.argv[2])
