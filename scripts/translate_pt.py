"""Anade el portugues de Brasil ("pt") a un guion ya escrito y aprobado (ingles + espanol).

Uso: python scripts/translate_pt.py stories/<episodio>.json      (requiere GEMINI_API_KEY)

Todo texto con "en" y "es" (frases, palabras en pantalla, titulo, leccion, nombre del invitado, miniatura) recibe "pt";
los metadatos de YouTube se escriben aparte, ya pensados para el publico brasileno. Si el guion ya tiene "pt", no hace nada.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generate_story import gemini  # noqa: E402

LOTE = 50


def nodos(x, out: list) -> None:
    """Dicts con "en" y "es" de texto (o listas de textos), excepto los metadatos de YouTube."""
    if isinstance(x, dict):
        en, es = x.get("en"), x.get("es")
        if isinstance(en, str) and isinstance(es, str):
            out.append(x)
        elif isinstance(en, list) and isinstance(es, list) and all(isinstance(s, str) for s in es):
            out.append(x)
        for k, v in x.items():
            if k not in ("en", "es", "pt", "youtube"):
                nodos(v, out)
    elif isinstance(x, list):
        for v in x:
            nodos(v, out)


def prompt(items: list[dict]) -> str:
    return f"""Translate these lines of a cartoon for children aged 2 to 6 into natural BRAZILIAN PORTUGUESE
("pt"), as a Brazilian kids' show would say them: simple words, warm, playful, "você"/"vocês", diminutives are fine.
Keep the meaning, the exclamations and the length (spoken aloud, so short and easy). Numbers, colors, shapes and
sound words must stay consistent: if a line says "two" and another item is the on-screen word "TWO", both become
"DOIS"/"dois". Keep character names (Zibu, Lila) unchanged; other names may be adapted to Portuguese.
Items with "max": that many characters at most (thumbnail text). Items that are lists: translate each element.
Answer ONLY JSON: {{"pt": [one translation per item, in the same order, same type (text or list)]}}

ITEMS:
{json.dumps(items, ensure_ascii=False)}"""


def youtube_pt(story: dict) -> dict:
    meta = gemini(f"""Write the YouTube metadata in BRAZILIAN PORTUGUESE for this episode of "Zibu e seus amigos",
a cartoon for children aged 2 to 6. Adapt it (do not translate word for word) for Brazilian parents: what happens
and what kids learn. Same structure as the Spanish version below: title max 90 characters with an emoji,
description 5-8 lines with emojis ending with 3-5 Portuguese hashtags, 10-14 tags in Portuguese.
Answer ONLY JSON: {{"title": "...", "description": "...", "tags": ["..."]}}

SPANISH VERSION:
{json.dumps(story["youtube"]["es"], ensure_ascii=False)}
ENGLISH VERSION:
{json.dumps(story["youtube"]["en"], ensure_ascii=False)}""", max_tokens=4000, temperature=0.5)
    if not meta.get("title") or not meta.get("description") or not isinstance(meta.get("tags"), list):
        raise ValueError(f"metadatos pt incompletos: {meta}")
    meta["title"] = meta["title"][:100]
    return meta


def traducir(story: dict) -> dict:
    todos: list[dict] = []
    nodos(story, todos)
    for a in range(0, len(todos), LOTE):
        lote = todos[a:a + LOTE]
        items = [{"en": n["en"], "es": n["es"]} | ({"max": 16} if n is story.get("thumb") else {}) for n in lote]
        for intento in range(3):
            pt = gemini(prompt(items), max_tokens=16000, temperature=0.3).get("pt", [])
            ok = len(pt) == len(lote) and all(
                (isinstance(p, str) and p.strip()) if isinstance(n["en"], str)
                else (isinstance(p, list) and len(p) == len(n["en"])) for p, n in zip(pt, lote))
            if ok:
                break
            print(f"   ! traduccion incompleta (lote {a // LOTE + 1}, intento {intento + 1}): se repite")
        else:
            raise RuntimeError("Gemini no devolvio una traduccion completa")
        for n, p in zip(lote, pt):
            n["pt"] = p
    if isinstance(story.get("thumb", {}).get("pt"), list):
        story["thumb"]["pt"] = [s[:18] for s in story["thumb"]["pt"]]
    story["youtube"]["pt"] = youtube_pt(story)
    return story


def main(path: str) -> None:
    p = Path(path)
    story = json.loads(p.read_text(encoding="utf-8"))
    if story.get("youtube", {}).get("pt"):
        print(f"{p.name}: ya tiene portugues")
        return
    traducir(story)
    p.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{p.name}: portugues listo · {story['title']['pt']}")


if __name__ == "__main__":
    main(sys.argv[1])
