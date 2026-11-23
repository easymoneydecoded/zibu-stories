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
        f"Setting: {BG.get(sc.get('bg'), 'a sunny garden')}, {TIME.get(sc.get('time'), 'bright daylight')}.\n"
        "Composition: close-up, the characters LARGE and filling the right two thirds, very expressive faces "
        "(surprised or laughing) looking at the viewer, clear action, one main object big in the center or right (never in "
        "the upper-left corner). Bright, "
        "saturated, cheerful colors, soft glow and depth, high contrast so it reads at a small size. Keep the upper-left "
        "area (about 45% wide, 35% tall) simple and uncluttered (sky) because a title is added there later.\n"
        "ABSOLUTELY NO text, letters, numbers, logos or watermarks anywhere in the image.")


def save(story: dict, raw: bytes, who: str) -> Path:
    from PIL import Image
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    w, h = img.size   # recorte central a 16:9 y 1280x720
    tw, th = (w, round(w * 9 / 16)) if w * 9 / 16 <= h else (round(h * 16 / 9), h)
    img = img.crop(((w - tw) // 2, (h - th) // 2, (w + tw) // 2, (h + th) // 2)).resize((1280, 720))
    out = BASE / "public" / "ep" / story["id"] / "thumb-ai.png"
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


def openai(story: dict, ref: Path) -> Path | None:
    """OpenAI (gpt-image): edicion con la hoja de personajes como referencia. ~0,01-0,04 $ por imagen."""
    k = env_key("OPENAI_IMAGE_KEY")
    if not k:
        return None
    for model in [m for m in (os.getenv("OPENAI_IMAGE_MODEL"), "gpt-image-1-mini", "gpt-image-1") if m]:
        try:
            with open(ref, "rb") as fh:
                r = requests.post("https://api.openai.com/v1/images/edits", timeout=300,
                                  headers={"Authorization": f"Bearer {k}"},
                                  files={"image[]": (ref.name, fh, "image/png")},
                                  data={"model": model, "prompt": prompt(story), "size": "1536x1024",
                                        "quality": os.getenv("OPENAI_IMAGE_QUALITY", "medium"), "n": "1"})
        except requests.RequestException as e:
            print(f"   ! {model}: {e}")
            continue
        if r.status_code != 200:
            print(f"   ! {model}: HTTP {r.status_code} {r.text[:250]}")
            continue
        data = (r.json().get("data") or [{}])[0].get("b64_json")
        if data:
            return save(story, base64.b64decode(data), model)
        print(f"   ! {model}: la respuesta no trae imagen")
    return None


def generate(story_path: str) -> Path | None:
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    guest = story["guest"].get("species") or story["guest"]["id"]
    ref = BASE / "public" / "ref" / f"cast-{guest}.png"
    if ref.exists() and (hecho := openai(story, ref)):
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
    generate(sys.argv[1])
