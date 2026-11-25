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
        "lila": "Lila, the pink bunny with long ears and a purple bow on one ear (the bow is always there)",
        "piglet": ("Percy, a cute pink piglet: a round pink head with TWO pointy pink ears (one on each side, both always "
                   "visible), big round eyes with WHITE eyeballs and dark brown pupils, a round pink snout with two "
                   "nostrils, rosy cheeks, a small round pink body with a lighter belly, short arms and short legs. "
                   "No bow, no accessories")}
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



# Invitados (2026-11-25): descripcion exacta para que la IA no mezcle rasgos entre caras. Ojos SIEMPRE blancos.
GUESTS = {
    "puppy": "a cute brown puppy (clearly a DOG, not a bear): round light-brown head with two LONG droopy darker brown ears that hang down beside the cheeks like a beagle (no round ears on top of the head), a white patch around one eye, big round eyes with white eyeballs and dark pupils, a cream muzzle with a small black nose, rosy cheeks, small round brown body with a cream belly, short arms and legs, NO tail visible",
    "kitten": "a cute orange kitten: round orange head with two POINTY ears, big round eyes with white eyeballs and dark pupils, a tiny pink nose with whiskers, rosy cheeks, small round orange body with a cream belly, short arms and legs, NO tail visible",
    "bear": "a cute brown bear cub: round brown head with two small ROUND ears, big round eyes with white eyeballs and dark pupils, a light tan muzzle with a dark nose, rosy cheeks, small round brown body with a tan belly, short arms and legs",
    "duckling": "a cute yellow duckling: round yellow head with a small orange feather tuft on top, big round eyes with white eyeballs and dark pupils, a small orange beak, rosy cheeks, small round yellow body, little wings and orange feet",
    "frog": "a cute green frog: round green head with two big round eyes on top (white eyeballs and dark pupils), a wide smile, two clear PINK BLUSH circles on the cheeks (always present), small round green body with a light green belly, short arms and dark green feet",
    "owl": "a cute brown owl chick: round brown head with two small pointed ear tufts, big round eyes with white eyeballs and dark pupils, a small orange beak, rosy cheeks, small round brown body with a cream belly, little wings and feet",
    "mouse": "a cute grey mouse: round grey head with two BIG round pink-lined ears, big round eyes with white eyeballs and dark pupils, a tiny pink nose with whiskers, rosy cheeks, small round grey body with a light belly, short arms and legs, a thin pink tail exactly as in the reference",
    "elephant": "a cute baby elephant: round light blue-grey head with two big round floppy ears and a short curled trunk, big round eyes with white eyeballs and dark pupils, rosy cheeks, small round blue-grey body, short thick legs",
    "giraffe": "a cute baby giraffe: yellow with orange-brown spots, a round head on a short neck, two small horns with round tips and two little ears, big round eyes with white eyeballs and dark pupils, rosy cheeks, small round body, short legs",
}

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
       "river": ("a sparkling blue river that crosses the MIDDLE distance from left to right, with a wide flat "
                 "grassy bank in the whole foreground (the water never reaches the bottom of the image)"),
       "hill": "a big grassy hill top under a wide sky", "beach": "a sunny beach with sand, sea and a palm tree",
       "sky": "a dreamy sky above the clouds", "room": ("INDOORS: a cozy colorful kids' bedroom with a bed, a rug on the floor and a window; the walls are plain "
                 "(no sun, moon, clouds or stars painted inside the room, the sky is only visible through the window)")}
TIMES = {"day": "bright daylight with a smiling sun and fluffy clouds", "sunset": "warm golden sunset light",
         "night": "a magical night with a smiling moon and twinkling stars"}


def bg(lugar: str, momento: str) -> None:
    (V2 / "bg").mkdir(parents=True, exist_ok=True)
    raw = edit_multi([V2 / "bg" / "garden-day.png"],   # mismo estilo que el jardin ya aprobado
                     f"Same art style as the reference image. A wide background illustration for a preschool cartoon, WITHOUT any characters or animals: "
                     f"{BGS[lugar]}, {'daytime, soft sunlight coming in through the window' if lugar == 'room' else TIMES[momento]}. The bottom 25% is open flat ground where characters will stand "
                     "(no big objects there). Polished 2D cartoon style with soft shading, bright saturated colors, depth. "
                     "ABSOLUTELY NO text.", quality="high")
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = im.size
    th = round(w * 9 / 16)
    im.crop((0, (h - th) // 2, w, (h - th) // 2 + th)).resize((1920, 1080), Image.LANCZOS).save(
        V2 / "bg" / f"{lugar}-{momento}.png")
    print("  fondo", lugar, momento)


OBJETOS = {
    "ball": "a red and white beach ball", "balloon": "a shiny red balloon with a curly string", "kite": "a colorful diamond kite with a tail of bows",
    "gift": "a blue gift box with a yellow ribbon and bow", "apple": "a shiny red apple with a green leaf", "cookie": "a round chocolate chip cookie",
    "cupcake": "a cupcake with pink frosting and a cherry on top", "flower": "a pink flower with a yellow center and a green stem with leaves",
    "butterfly": "a purple and pink butterfly with open wings", "umbrella": "an open pink umbrella with a curved handle",
    "shell": "a pink scallop seashell", "star": "a big shiny yellow star with a happy face", "teddy": "a small brown teddy bear toy sitting",
    "drum": "a red toy drum with two drumsticks", "toycar": "a small red toy car", "bucket": "a blue beach bucket with a yellow spade",
    "crayons": "a bundle of five colorful crayons", "banana": "a yellow banana", "wateringcan": "a green watering can",
    "basket": "a wicker picnic basket with a red and white checked cloth",
}


def prop(que: str) -> None:
    (V2 / "props").mkdir(parents=True, exist_ok=True)
    for _ in range(4):
        raw = prop_raw(que)
        if raw and not toca_borde(Image.open(io.BytesIO(raw)).convert("RGBA"), []):
            break
        print(f"   ! {que}: cortado por el borde, repito")
    recorte(raw).save(V2 / "props" / f"{que}.png")
    print("  objeto", que)


def prop_raw(que: str) -> bytes | None:
    return edit_multi([V2 / "chars3" / "piglet" / "happy_closed.png"],
                     f"IMPORTANT: the reference image only shows the ART STYLE; do not draw that character. Draw ONE object "
                     f"sticker for a preschool cartoon: {OBJETOS.get(que, que)}. Centered, complete, with empty margin all "
                     "around (nothing touches the edges: a margin of at least 80 pixels on every side; for a balloon include the whole balloon and its string), solid and opaque (only the background is transparent), on a fully "
                     "TRANSPARENT background, no characters, no shadow. Polished 2D cartoon style with soft shading, bright "
                     "colors. NO text.", size="1024x1024", quality="medium", transparent=True)




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
    "sad": ("sad: worried eyebrows and a small frown, but the eyes drawn EXACTLY like the reference (white eyeballs "
            "with the same pupils, same colors)"),
    "laugh": ("laughing with joy: very big happy smile, eyes OPEN and sparkling (same eyes as the reference, not "
              "closed), arms DOWN and relaxed exactly like the reference"),
}


def toca_borde(im: Image.Image, cajas: list[tuple[int, int]]) -> bool:
    """Una figura con pixeles opacos en el borde de la imagen esta cortada."""
    a = im.getchannel("A").point(lambda v: 255 if v > 128 else 0)
    w, h = a.size
    px = a.load()
    borde = sum(1 for y in range(h) for x in (0, 1, w - 2, w - 1) if px[x, y]) + \
        sum(1 for x in range(w) for y in (0, 1, h - 2, h - 1) if px[x, y])
    return borde > 15


def color_medio(im: Image.Image) -> tuple[float, float, float]:
    px = [p for p in im.convert("RGBA").resize((96, 96)).getdata() if p[3] > 200]
    return tuple(sum(p[i] for p in px) / max(1, len(px)) for i in range(3))


def sobre_blanco(im: Image.Image) -> bytes:
    fondo = Image.new("RGBA", im.size, "white")
    fondo.alpha_composite(im)
    buf = io.BytesIO()
    fondo.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


def mismo_diseno(ref: Image.Image, cand: Image.Image, solo_boca: bool = False) -> tuple[bool, str]:
    """Misma ficha de personaje (orejas, color, contorno, cola...) salvo la cara. Primero el color medio (rapido) y
    luego Gemini mira las dos imagenes."""
    a, b = color_medio(ref), color_medio(cand)
    dist = sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5
    if dist > 18:   # los aprobados (Zibu, Lila, Percy) no pasan de 16
        return False, f"color distinto ({dist:.0f})"
    import base64
    import json
    import re
    import requests
    import ai_thumb as A
    k = A.env_key("GEMINI_API_KEY")
    body = {"contents": [{"parts": [
        {"text": ("Image 1 and image 2 are two frames of a talking animation: they must be IDENTICAL except the "
                  "MOUTH (closed in one, open in the other). The eyes, eyebrows, cheeks and everything else must be "
                  "the same. " if solo_boca else
                  "Image 1 is the reference cartoon character. Image 2 should be EXACTLY the same character design "
                  "with only a different facial expression. Ignore the eyes, eyebrows (eyebrows appearing or "
                  "disappearing is part of the expression) and mouth. ") + "Compare everything else "
                 "strictly: head shape, ear shape and size, colors and shade, outline thickness, spots or markings, "
                 "body shape, arm pose, tail (present in one but not the other counts as different), accessories. "
                 'Answer only JSON: {"same": true or false, "diff": "short reason"}'},
        {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(sobre_blanco(ref)).decode()}},
        {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(sobre_blanco(cand)).decode()}}]}]}
    import time
    for model in ("gemini-3.5-flash", "gemini-2.5-flash", "gemini-3.5-flash-lite") * 3:
        try:
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                              params={"key": k}, json=body, timeout=90)
        except requests.RequestException:
            continue
        if r.status_code == 200:
            txt = "".join(p.get("text", "") for p in r.json()["candidates"][0]["content"]["parts"])
            m = re.search(r"\{.*\}", txt, re.S)
            if m:
                try:
                    j = json.loads(m.group(0))
                    return bool(j.get("same")), str(j.get("diff", ""))
                except ValueError:
                    pass
        time.sleep(8)   # Gemini gratis: si va saturado se espera; nunca se da por bueno sin mirarlo
    return False, "Gemini no contesto"


def pareja(quien: str, expr: str, refs: list[Path], intentos: int = 4,
           base: Image.Image | None = None) -> list[Image.Image]:
    desc = DESC.get(quien) or (f"{GUESTS[quien]}. No bow, no accessories" if quien in GUESTS
                               else f"the {quien} from the reference image (only the {quien}; it has no bow or accessories)")
    extra = expr == "happy"
    n = 3 if extra else 2
    caras = ("1) mouth CLOSED; 2) mouth OPEN as if talking (the only difference is the mouth)" +
             ("; 3) eyes closed in a happy blink, mouth closed (everything else identical, including any bow or "
              "accessory)" if extra else ""))
    nuevo = quien in GUESTS and not (BASE / "public" / "ref" / f"guest-{quien}.png").exists() and expr == "happy"
    nota = ("IMPORTANT: the reference image only shows the ART STYLE (another character); draw the animal described "
            "here, not the one in the reference. ") if nuevo else ""
    if base is not None:
        nota += ("The reference image IS this character: copy its design EXACTLY (same head and ear shape, same "
                 "colors and shade, same outline, same markings, tail only if the reference shows one); only the "
                 "facial expression changes. ")
    prompt = (f"{nota}{n} drawings of {desc}, side by side in one row, IDENTICAL in everything (same size, same full-body "
              f"standing pose facing the viewer with the arms down and relaxed exactly like the reference image, same "
              f"position, same expression: {EXPR[expr]}) except the mouth: "
              f"{caras}. Big empty margin around every figure: NOTHING may touch or cross the edges of the image "
              "(ears, antenna and feet fully inside, at least 60 pixels from every edge). "
              "Only the BACKGROUND is transparent: the eyes keep solid opaque WHITE eyeballs. "
              "Fully TRANSPARENT background, no scenery, no text, no shadows. " + STYLE)
    for _ in range(intentos + 2):
        raw = edit_multi(refs, prompt, size="1536x1024", quality="high", transparent=True)
        if not raw:
            continue
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
            if base is not None:
                ok, motivo = mismo_diseno(base, figs[0])
                if not ok:
                    raise ValueError(f"no es el mismo diseno: {motivo}")
            ok, motivo = mismo_diseno(figs[0], figs[1], solo_boca=True)
            if not ok:
                raise ValueError(f"la boca abierta cambia algo mas: {motivo}")
            if len(figs) > 2:
                ok, motivo = mismo_diseno(figs[0], figs[2])
                if not ok:
                    raise ValueError(f"el parpadeo cambia el diseno: {motivo}")
            return figs
        except ValueError as e:
            print(f"   ! {quien} {expr}: {e}, repito")
    raise SystemExit(f"no salio {quien} {expr}")


def pairs(quien: str) -> None:
    """public/v2/chars3/<quien>/<expr>_closed.png, <expr>_open.png y happy_blink.png, todas en el mismo lienzo."""
    out = V2 / "chars3" / quien
    out.mkdir(parents=True, exist_ok=True)
    if quien in ("zibu", "lila"):
        refs = [BASE / "public" / "ref" / "cast-puppy.png"]
    elif (BASE / "public" / "ref" / f"guest-{quien}.png").exists():
        refs = [BASE / "public" / "ref" / f"guest-{quien}.png"]       # solo el invitado, sin Zibu ni Lila
    else:   # animal nuevo sin dibujo previo: el estilo lo marca Percy (ya aprobado)
        refs = [V2 / "chars3" / "piglet" / "happy_closed.png"]
    figs_all = {}
    for expr in EXPR:
        if (out / f"{expr}_closed.png").exists():
            continue
        # despues de la primera, la referencia es SOLO su propia cara contenta (la hoja de referencia trae a Zibu y Lila
        # y la IA mezclaba rasgos: orejas de conejo en el cerdito)
        hc = out / "happy_closed.png"
        figs = pareja(quien, expr, [hc] if hc.exists() else refs,
                      base=Image.open(hc).convert("RGBA") if hc.exists() else None)
        alto = max(f.height for f in figs)   # la pareja a la misma altura: al hablar el personaje no encoge
        figs = [f.resize((round(f.width * alto / f.height), alto), Image.LANCZOS) for f in figs]
        nombres = [f"{expr}_closed", f"{expr}_open"] + (["happy_blink"] if expr == "happy" else [])
        # cada pareja en un lienzo comun (mismo ancho y alto, apoyada abajo y centrada): al hablar no se mueve nada
        W, H = max(f.width for f in figs), max(f.height for f in figs)
        for nombre, f in zip(nombres, figs):
            lienzo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            lienzo.alpha_composite(f, ((W - f.width) // 2, H - f.height))
            # el blanco de los ojos nunca transparente; en el parpadeo el ojo cerrado es piel (parpado), no blanco
            lienzo = tapar_huecos(lienzo, color_piel(lienzo) if nombre.endswith("blink") else None)
            lienzo.save(out / f"{nombre}.png")
            figs_all[nombre] = lienzo
        print(f"  {quien} {expr}")




def color_piel(im: Image.Image) -> tuple[int, int, int]:
    """Color mas comun de la cara (zona central de arriba), sin contar blancos, negros ni transparentes."""
    from collections import Counter
    im = im.convert("RGBA")
    b = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    h = b[3] - b[1]
    zona = im.crop((b[0] + (b[2] - b[0]) // 4, b[1] + h // 6, b[2] - (b[2] - b[0]) // 4, b[1] + h // 2))
    cuenta = Counter((r // 8 * 8, g // 8 * 8, bl // 8 * 8) for r, g, bl, a in zona.getdata()
                     if a > 200 and not (r > 225 and g > 225 and bl > 225) and r + g + bl > 120)
    return cuenta.most_common(1)[0][0]


def tapar_huecos(im: Image.Image, relleno: tuple[int, int, int] | None = None) -> Image.Image:
    """Al pedir fondo transparente la IA tambien deja transparente el blanco de los ojos (se ve el paisaje a traves).
    Todo hueco transparente ENCERRADO dentro de la figura (no conectado con el exterior) en la mitad de arriba
    (la cara) y pequeno se rellena de blanco."""
    from PIL import ImageDraw
    im = im.convert("RGBA")
    w, h = im.size
    m = Image.new("L", (w + 2, h + 2), 0)
    m.paste(im.getchannel("A").point(lambda v: 255 if v > 24 else 0), (1, 1))
    ImageDraw.floodfill(m, (0, 0), 128)           # el exterior conectado con el borde
    m = m.crop((1, 1, w + 1, h + 1))
    px, mp = im.load(), m.load()
    visto = set()
    caja = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    alto_fig = caja[3] - caja[1]
    for y in range(h):
        for x in range(w):
            if mp[x, y] != 0 or (x, y) in visto:
                continue
            # region del hueco (pila)
            pila, region = [(x, y)], []
            visto.add((x, y))
            while pila:
                cx, cy = pila.pop()
                region.append((cx, cy))
                for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                    if 0 <= nx < w and 0 <= ny < h and mp[nx, ny] == 0 and (nx, ny) not in visto:
                        visto.add((nx, ny))
                        pila.append((nx, ny))
            ys = [p[1] for p in region]
            en_cara = (sum(ys) / len(ys) - caja[1]) < 0.62 * alto_fig
            if en_cara and len(region) < 0.08 * w * h:
                for rx, ry in region:
                    r, g, b, a = px[rx, ry]
                    # mezcla con lo que hubiera (bordes suaves) hacia blanco opaco
                    k = a / 255
                    fr, fg, fb = relleno or (255, 255, 255)
                    px[rx, ry] = (int(r * k + fr * (1 - k)), int(g * k + fg * (1 - k)), int(b * k + fb * (1 - k)), 255)
    return im


if __name__ == "__main__" and sys.argv[1] == "pairs":   # al final: usa funciones definidas mas arriba
    pairs(sys.argv[2])


def auditar(quien: str) -> list[str]:
    """Repasa las 11 caras: cada expresion contra la cara contenta, y la boca abierta / parpadeo contra su pareja.
    Devuelve las expresiones que fallan (para apartarlas y volver a generarlas)."""
    d = V2 / "chars3" / quien
    cargar = lambda n: Image.open(d / f"{n}.png").convert("RGBA")   # noqa: E731
    base = cargar("happy_closed")
    malas = []
    for expr in EXPR:
        pares = [("happy_closed", f"{expr}_closed")] if expr != "happy" else []
        pares += [(f"{expr}_closed", f"{expr}_open")] + ([("happy_closed", "happy_blink")] if expr == "happy" else [])
        for a, b in pares:
            ok, motivo = mismo_diseno(base if a == "happy_closed" else cargar(a), cargar(b),
                                      solo_boca=b.endswith("_open"))
            print(f"  {quien} {b}: {'ok' if ok else 'MAL - ' + motivo}", flush=True)
            if not ok and expr not in malas:
                malas.append(expr)
    return malas


if __name__ == "__main__" and sys.argv[1] == "audit":
    for q in sys.argv[2:]:
        print(q, "->", auditar(q) or "todo bien", flush=True)


if __name__ == "__main__" and sys.argv[1] in ("char", "sheet", "bg", "prop"):   # al final: todo ya definido
    cmd = sys.argv[1]
    {"char": lambda: char(sys.argv[2]), "sheet": lambda: sheet(sys.argv[2]), "bg": lambda: bg(sys.argv[2], sys.argv[3]),
     "prop": lambda: prop(sys.argv[2])}[cmd]()
