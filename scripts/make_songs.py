"""Genera las canciones fijas de Zibu con ElevenLabs Music (API) en ingles, espanol y portugues.

Uso: python scripts/make_songs.py [nombre ...]      (sin nombres: todas las que falten)
     python scripts/make_songs.py --force intro      (regenera aunque ya exista)

Requiere ELEVENLABS_API_KEY (en Infantil/.env o en el entorno). Salida: public/songs/<nombre>-<lang>.mp3
Se generan una vez y se reutilizan en todos los episodios (como las series infantiles de verdad).
"""
import os
import sys
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "public" / "songs"
URL = "https://api.elevenlabs.io/v1/music?output_format=mp3_44100_128"
MODELS = ["music_v2_5", "music_v1"]

KIDS = ["children's song for toddlers", "cartoon", "major key", "simple catchy melody", "clear sung lyrics"]
NEGATIVE = ["sad", "dark", "aggressive", "explicit", "heavy drums", "distorted guitar", "rap"]

FRIENDS_CHORUS = {
    "en": "Friends, friends, we learn something new,\nEvery day with me and you!\n"
          "Friends, friends, hold my hand,\nThe best friends in the land!",
    "es": "Amigos, amigos, algo nuevo hoy,\n¡aprendo contigo a donde voy!\n"
          "Amigos, amigos, dame la mano,\n¡los mejores del verano!",
    "pt": "Amigos, amigos, vamos aprender,\nalgo novo todo dia pra crescer!\n"
          "Amigos, amigos, me dá a mão,\nos melhores do coração!"}

# (estilos, [(seccion, duracion_ms, {lang: letra})])
SONGS = {
    "intro": (["very short cheerful theme song", "ukulele", "xylophone", "hand claps", "bright friendly female vocal",
               "120 BPM", "nursery rhyme style"],
              [("Theme", 15000, {
                  "en": "Hello, hello, it's Zibu time!\nA little blue friend with a happy smile!\n"
                        "Zibu, Zibu, one, two, three,\nCome and play with me!",
                  "es": "¡Hola, hola, llegó Zibu!\nUn amiguito chiquito y azul.\n"
                        "Zibu, Zibu, uno, dos y tres,\n¡ven a jugar otra vez!",
                  "pt": "Olá, olá, chegou o Zibu!\nUm amiguinho pequeno e azul!\n"
                        "Zibu, Zibu, um, dois e três,\nvem brincar mais uma vez!"})]),
    "dance": (["upbeat children's dance song", "bouncy beat", "ukulele", "xylophone", "hand claps",
               "happy energetic female vocal with kids choir", "125 BPM", "action song"],
              [("Verse", 24000, {
                  "en": "Jump, jump, jump with me!\nClap, clap, one, two, three!\n"
                        "Spin around and touch the ground,\nWiggle, wiggle, all around!",
                  "es": "¡Salta, salta, salta conmigo!\n¡Aplaude, aplaude, uno, dos, tres!\n"
                        "Da una vuelta, toca el suelo,\n¡muévete de la cabeza a los pies!",
                  "pt": "Pula, pula, pula comigo!\nBate palma, um, dois, três!\n"
                        "Dá uma volta, toca o chão,\nmexe, mexe, outra vez!"}),
               ("Chorus", 26000, {
                  "en": "Dance with Zibu, dance with Lila,\nDance, dance, everybody!\n"
                        "Dance with Zibu, dance with Lila,\nDance, dance, everybody!",
                  "es": "¡Baila con Zibu, baila con Lila,\nbaila, baila, todo el mundo!\n"
                        "¡Baila con Zibu, baila con Lila,\nbaila, baila, todo el mundo!",
                  "pt": "Dança com o Zibu, dança com a Lila,\ndança, dança, todo mundo!\n"
                        "Dança com o Zibu, dança com a Lila,\ndança, dança, todo mundo!"})]),
    # Cancion del medio del episodio (escena "song"): generica sobre amistad y aprender, vale para cualquier leccion
    "friends": (["happy sing-along children's song", "ukulele", "xylophone", "glockenspiel", "hand claps",
                 "cheerful female vocal with kids choir", "110 BPM", "catchy repetitive chorus"],
                [("Verse 1", 22000, {
                    "en": "When I play with all my friends,\nThe fun and laughing never ends.\n"
                          "We share, we help, we try our best,\nTogether we're the very best!",
                    "es": "Cuando juego con mis amigos,\nla alegría va conmigo.\n"
                          "Compartimos, nos ayudamos,\n¡y juntitos aprendemos!",
                    "pt": "Quando eu brinco com os amigos,\na alegria vem comigo.\n"
                          "A gente divide e se ajuda,\ne juntinhos tudo muda!"}),
                 ("Chorus", 23000, FRIENDS_CHORUS),
                 ("Verse 2", 22000, {
                    "en": "If I'm sad, you make me smile,\nWe can sing and dance a while.\n"
                          "If we make a big mistake,\nWe say sorry, give a shake!",
                    "es": "Si estoy triste, tú me alegras,\ncantamos juntos, ¡qué fiesta!\n"
                          "Si un error a veces hago,\npido perdón y te abrazo.",
                    "pt": "Se estou triste, você me alegra,\ncantamos juntos, que festa!\n"
                          "Se eu fizer algo errado,\npeço desculpa e dou um abraço apertado!"}),
                 ("Chorus", 23000, FRIENDS_CHORUS)]),
    "bye": (["gentle sweet goodbye song", "soft ukulele", "glockenspiel", "warm female vocal", "calm happy melody",
             "100 BPM", "lullaby feel"],
            [("Goodbye", 35000, {
                "en": "The story's done, the sun goes down,\nWe had such fun with all our friends around.\n"
                      "Wave your hand and say goodbye,\nSee you soon, under the sky!\nBye-bye, bye-bye!",
                "es": "El cuento terminó, el sol se va,\n¡qué bien la pasamos, qué felicidad!\n"
                      "Mueve la manita y di adiós,\n¡hasta pronto, amigos, de los dos!\n¡Adiós, adiós!",
                "pt": "A história acabou, o sol vai se pôr,\nque dia feliz, cheio de amor!\n"
                      "Acena a mãozinha e diz tchau,\naté logo, amigos, foi legal!\nTchau, tchau!"})]),
}
VOICE = {"en": "English vocal", "es": "Latin American Spanish vocal, native Spanish pronunciation",
         "pt": "Brazilian Portuguese vocal, native Brazilian pronunciation"}


def api_key() -> str:
    key = os.getenv("ELEVENLABS_API_KEY")
    env = BASE / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
    if not key:
        sys.exit("Falta ELEVENLABS_API_KEY en Infantil/.env")
    return key


def payload(model: str, styles: list[str], sections, lang: str) -> dict:
    estilos = KIDS + styles + [VOICE[lang]]
    if model == "music_v1":
        return {"model_id": model, "composition_plan": {
            "positive_global_styles": estilos, "negative_global_styles": NEGATIVE,
            "sections": [{"section_name": name, "positive_local_styles": [], "negative_local_styles": [],
                          "duration_ms": ms, "lines": letra[lang].split("\n")} for name, ms, letra in sections]}}
    return {"model_id": model, "composition_plan": {"chunks": [
        {"text": f"[{name}]\n{letra[lang]}", "duration_ms": ms, "positive_styles": estilos, "negative_styles": NEGATIVE}
        for name, ms, letra in sections]}}


def generar(nombre: str, lang: str, key: str) -> None:
    styles, sections = SONGS[nombre]
    for model in MODELS:
        r = requests.post(URL, headers={"xi-api-key": key}, json=payload(model, styles, sections, lang), timeout=600)
        if r.status_code == 200 and r.content:
            dest = OUT / f"{nombre}-{lang}.mp3"
            dest.write_bytes(r.content)
            print(f"   ✓ {dest.name} ({len(r.content) / 1024:.0f} KB, {model})")
            return
        print(f"   ! {nombre}-{lang} con {model}: HTTP {r.status_code} {r.text[:300]}")
    raise RuntimeError(f"No se pudo generar {nombre}-{lang}")


def main(args: list[str]) -> None:
    force = "--force" in args
    nombres = [a for a in args if a != "--force"] or list(SONGS)
    OUT.mkdir(parents=True, exist_ok=True)
    key = api_key()
    for nombre in nombres:
        for lang in ("es", "en", "pt"):  # primero espanol: es el canal que mejor arranca
            if (OUT / f"{nombre}-{lang}.mp3").exists() and not force:
                print(f"   . {nombre}-{lang}.mp3 ya existe")
                continue
            generar(nombre, lang, key)


if __name__ == "__main__":
    main(sys.argv[1:])
