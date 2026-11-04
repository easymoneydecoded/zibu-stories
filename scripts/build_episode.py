"""Prepara un episodio para Remotion: voces (Kokoro), musica, efectos y timeline.

Uso: python scripts/build_episode.py stories/ep001-lost-star.json en|es

Salida en public/ep/<id>/<lang>/: una pista .wav por frase, musica.wav y timeline.json
(escenas con sus fotogramas de inicio y fin, frases, movimientos, textos y efectos).
"""
import json
import os
import sys
import time
import wave
from pathlib import Path

import numpy as np
import requests
from kokoro_onnx import Kokoro

BASE = Path(__file__).resolve().parent.parent
FPS = 30
SR = 24000            # Kokoro genera a 24 kHz; la musica y los efectos tambien
GAP = 0.8             # silencio entre frases (s): ritmo pausado, para ninos pequenos
SCENE_LEAD = 0.9      # antes de la primera frase de cada escena
SCENE_TAIL = 0.7      # despues de la ultima
MIN_MOVE = 1.6        # un desplazamiento dura al menos esto aunque la frase sea corta
BPM = 112             # musica; la cancion va a compas
BEAT = 60 / BPM
BAR = 4 * BEAT        # en la cancion cada verso ocupa 2 compases (empieza siempre en un compas)

# Voz de cada personaje: (voz de Kokoro, velocidad, subida de tono en semitonos)
VOICES = {
    "en": {"narrator": ("af_bella", 0.92, 0), "zibu": ("am_puck", 1.0, 4),
           "lila": ("af_sky", 1.0, 3), "star": ("af_heart", 1.0, 6)},
    "es": {"narrator": ("ef_dora", 0.92, 0), "zibu": ("ef_dora", 1.0, 5),
           "lila": ("ef_dora", 1.06, 2), "star": ("ef_dora", 1.0, 8)},
}
# Voz del invitado segun su especie: {idioma: (voz, velocidad, semitonos)}
GUEST_VOICES = {
    "star": {"en": ("af_heart", 1.0, 6), "es": ("ef_dora", 1.0, 8)},
    "puppy": {"en": ("am_echo", 1.02, 4), "es": ("em_alex", 1.02, 5)},
    "kitten": {"en": ("af_nicole", 1.0, 5), "es": ("ef_dora", 1.04, 7)},
    "bear": {"en": ("am_michael", 0.95, 1), "es": ("em_alex", 0.95, 1)},
    "duckling": {"en": ("af_jessica", 1.05, 6), "es": ("ef_dora", 1.06, 9)},
    "frog": {"en": ("am_fenrir", 1.0, 3), "es": ("em_alex", 1.0, 4)},
    "piglet": {"en": ("af_kore", 1.0, 4), "es": ("ef_dora", 1.0, 6)},
    "owl": {"en": ("bm_george", 0.92, 0), "es": ("em_alex", 0.92, -1)},
    "mouse": {"en": ("af_sky", 1.08, 7), "es": ("ef_dora", 1.1, 10)},
}
LANG_CODE = {"en": "en-us", "es": "es"}
MIN_TOTAL = 8 * 60 + 5   # YouTube permite anuncios a mitad del video desde 8 min
MAX_PAD = 75             # lo que se puede alargar la fiesta final para llegar al minimo


def cancion(nombre: str, lang: str) -> dict | None:
    """Cancion fija de Zibu (public/songs, scripts/make_songs.py): {src, dur} o None si no existe."""
    ruta = BASE / "public" / "songs" / f"{nombre}-{lang}.mp3"
    if not ruta.exists():
        return None
    from mutagen.mp3 import MP3
    return {"src": f"songs/{ruta.name}", "dur": MP3(ruta).info.length}


def subir_tono(x: np.ndarray, semitonos: float) -> np.ndarray:
    if not semitonos:
        return x
    idx = np.arange(0, len(x) - 1, 2 ** (semitonos / 12))
    return np.interp(idx, np.arange(len(x)), x).astype(np.float32)


def recortar(x: np.ndarray, umbral: float = 0.01) -> np.ndarray:
    """Quita el silencio del principio y del final (deja 50 ms)."""
    voz = np.where(np.abs(x) > umbral)[0]
    if not len(voz):
        return x
    pad = int(SR * 0.05)
    return x[max(0, voz[0] - pad):voz[-1] + pad]


def guardar_wav(ruta: Path, x: np.ndarray) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(x, -1, 1) * 32767).astype("<i2").tobytes())


# ---------------------------------------------------------------------------
# Musica y efectos (sintetizados: sin derechos de terceros)
# ---------------------------------------------------------------------------
def nota(freq: float, dur: float, vol: float, forma: str = "tri") -> np.ndarray:
    t = np.arange(int(SR * dur)) / SR
    w = 2 * np.abs(2 * ((t * freq) % 1) - 1) - 1 if forma == "tri" else np.sin(2 * np.pi * freq * t)
    return w * np.minimum(1, t / 0.01) * np.exp(-3.2 * t / dur) * vol


def hz(n: int) -> float:
    return 440 * 2 ** ((n - 69) / 12)


CALMA = [72, -1, 76, -1, 79, -1, 76, -1, 74, -1, 77, -1, 76, -1, 72, -1,
         69, -1, 72, -1, 76, -1, 74, -1, 72, -1, 71, -1, 72, -1, -1, -1]
ALEGRE = [72, 76, 79, 76, 74, 76, 72, -1, 74, 77, 81, 79, 76, 74, 72, -1,
          72, 76, 79, 84, 81, 79, 76, -1, 74, 76, 74, 72, 67, 69, 72, -1]
BAJO = [48, 48, 53, 53, 55, 55, 48, 48]


def tramo_musical(segundos: float, melodia: list[int], vol: float) -> np.ndarray:
    pista = np.zeros(int(SR * (segundos + 2)))
    paso = BEAT / 2
    i = 0
    while i * paso < segundos:
        ini = int(i * paso * SR)
        n = melodia[i % len(melodia)]
        if n > 0:
            s = nota(hz(n), paso * 2.2, 0.10 * vol)
            pista[ini:ini + len(s)] += s[:len(pista) - ini]
        if i % 4 == 0:
            b = nota(hz(BAJO[(i // 4) % len(BAJO)]), BEAT * 2, 0.11 * vol, "sin")
            pista[ini:ini + len(b)] += b[:len(pista) - ini]
        if melodia is ALEGRE and i % 2 == 0:  # palmada suave en la cancion
            t = np.arange(int(SR * 0.05)) / SR
            c = np.random.default_rng(i).uniform(-1, 1, len(t)) * np.exp(-60 * t) * 0.05
            pista[ini:ini + len(c)] += c[:len(pista) - ini]
        i += 1
    return pista[:int(SR * segundos)]


def efectos() -> dict[str, np.ndarray]:
    t = np.arange(int(SR * 0.16)) / SR
    pop = np.sin(2 * np.pi * np.cumsum(500 + 1400 * t / t[-1]) / SR) * np.exp(-22 * t) * 0.5
    brillo = np.concatenate([nota(hz(n), 0.12, 0.2, "sin") for n in (84, 88, 91)] + [nota(hz(96), 0.6, 0.2, "sin")])
    t2 = np.arange(int(SR * 0.7)) / SR
    fiu = np.sin(2 * np.pi * np.cumsum(1800 - 1500 * t2 / t2[-1]) / SR) * np.exp(-3 * t2) * 0.25
    return {"pop": pop, "brillo": brillo, "fiu": fiu}


# ---------------------------------------------------------------------------
# Episodio
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ElevenLabs (solo espanol, mientras queden creditos): voces predeterminadas, una por personaje
# ---------------------------------------------------------------------------
ELEVEN_MODEL = "eleven_multilingual_v2"
# (voice_id, subida de tono en semitonos); voces predeterminadas de ElevenLabs, disponibles en todas las cuentas
ELEVEN_VOICES = {
    "narrator": ("XrExE9yKIg1WjnnlVkGX", 0),   # Matilda: calida, cuentacuentos
    "zibu": ("TX3LPaxmHKxFdv7VOQHJ", 3),       # Liam, mas agudo: monstruito alegre
    "lila": ("cgSgspJ2msm6clMCkdW9", 2),       # Jessica: conejita dulce
}
ELEVEN_GUEST = {"owl": ("JBFqnCBsd6RMkjVDRZzb", 0), "bear": ("JBFqnCBsd6RMkjVDRZzb", 2)}  # George: voz mayor
ELEVEN_GUEST_DEFAULT = ("FGY2WhTYpPnrIDTdsKH5", 4)                                      # Laura, aguda


class ElevenAgotado(Exception):
    """ElevenLabs sin creditos (o caido): el episodio se rehace entero con Kokoro, sin mezclar voces."""


def eleven_key() -> str | None:
    key = os.getenv("ELEVENLABS_API_KEY")
    env = BASE / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("ELEVENLABS_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"')
    return key or None


def tts_eleven(key: str, voice_id: str, texto: str) -> np.ndarray:
    for intento in range(3):
        try:
            r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=pcm_24000",
                              headers={"xi-api-key": key}, timeout=120,
                              json={"text": texto, "model_id": ELEVEN_MODEL,
                                    "voice_settings": {"stability": 0.4, "similarity_boost": 0.75, "style": 0.45}})
        except requests.RequestException:
            continue
        if r.status_code == 200:
            return np.frombuffer(r.content, dtype="<i2").astype(np.float32) / 32768
        if r.status_code in (401, 402, 403) or "quota" in r.text.lower():
            raise ElevenAgotado(f"HTTP {r.status_code}: {r.text[:200]}")
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(5 * (intento + 1))
            continue
        raise ElevenAgotado(f"HTTP {r.status_code}: {r.text[:200]}")
    raise ElevenAgotado("ElevenLabs no responde")


def main(story_path: str, lang: str, motor: str = "kokoro") -> None:
    story = json.loads(Path(story_path).read_text(encoding="utf-8"))
    out = BASE / "public" / "ep" / story["id"] / lang
    k = Kokoro(str(BASE / "models" / "kokoro-v1.0.onnx"), str(BASE / "models" / "voices-v1.0.bin"))
    guest = story["guest"].get("species") or story["guest"]["id"]
    voces = dict(VOICES[lang], guest=GUEST_VOICES[guest][lang], star=GUEST_VOICES[guest][lang])
    eleven = dict(ELEVEN_VOICES, guest=ELEVEN_GUEST.get(guest, ELEVEN_GUEST_DEFAULT),
                  star=ELEVEN_GUEST.get(guest, ELEVEN_GUEST_DEFAULT))
    key = eleven_key() if motor == "eleven" else None
    print(f"   . voces: {'ElevenLabs' if key else 'Kokoro'} ({lang})")

    def tts(who: str, texto: str) -> np.ndarray:
        if key:
            voice_id, tono = eleven[who]
            return recortar(subir_tono(tts_eleven(key, voice_id, texto), tono))
        voz, speed, tono = voces[who]
        audio, _ = k.create(texto, voice=voz, speed=speed / 2 ** (tono / 12), lang=LANG_CODE[lang])
        return recortar(subir_tono(audio, tono))

    t = 0.0
    scenes, sfx, musica_tramos = [], [], []
    for si, sc in enumerate(story["scenes"]):
        start = t
        song = sc.get("type") == "song"
        # el gancho y el titulo entran rapido: los primeros segundos deciden si el nino se queda
        t += 2 * BAR if song else (0.3 if si == 0 or sc.get("type") == "title" else SCENE_LEAD)
        lines = []
        tema = None  # cancion fija que suena en esta escena
        intro, baile = cancion("intro", lang), cancion("dance", lang)
        if sc.get("type") == "title" and intro:
            # La sintonia canta "Hello, it's Zibu time": el titulo solo se ve, no lo lee la narradora
            tema = {"src": intro["src"], "start": round(t * FPS), "dur": round(intro["dur"] * FPS)}
            t += intro["dur"]
            scenes.append({k2: v for k2, v in sc.items() if k2 != "lines"} |
                          {"start": round(start * FPS), "end": round((t + 0.3) * FPS), "lines": [], "song": tema})
            musica_tramos.append((start, t + 0.3, None))
            t += 0.3
            continue
        for li, ln in enumerate(sc["lines"]):
            if sc.get("type") == "dance" and baile and li == 1 and tema is None:
                # La cancion de baile entra despues de "Dance party!" y las demas frases van detras
                tema = {"src": baile["src"], "start": round(t * FPS), "dur": round(baile["dur"] * FPS)}
                t += baile["dur"] + 0.6
            audio = tts(ln["who"], ln[lang])
            dur = len(audio) / SR
            src = f"ep/{story['id']}/{lang}/s{si:02d}_l{li:02d}.wav"
            guardar_wav(BASE / "public" / src, audio)
            moves = ln.get("moves", [])
            entry = {k2: v for k2, v in ln.items() if k2 not in ("en", "es")}
            entry.update({"text": ln[lang], "src": src, "start": round(t * FPS), "dur": max(1, round(dur * FPS)),
                          "moveDur": round(max(dur, MIN_MOVE) * FPS)})
            if "show" in ln:
                entry["show"] = {"text": ln["show"][lang], "color": ln["show"].get("color")}
                sfx.append({"name": "pop", "at": entry["start"]})
            if ln.get("balloons") or ln.get("action") == "glow":
                sfx.append({"name": "brillo", "at": entry["start"]})
            lines.append(entry)
            if song:
                t += max(2, int(np.ceil(dur / BAR))) * BAR
            else:
                # con la cancion de baile, las pausas largas de la fiesta (para bailar) ya no hacen falta
                pausa = min(ln.get("pause", 0), 1.0) if sc.get("type") == "dance" and baile else ln.get("pause", 0)
                t += dur + GAP + pausa
                if moves:  # que el desplazamiento termine antes de la siguiente frase
                    t = max(t, (entry["start"] + entry["moveDur"]) / FPS + 0.3)
        for p in sc.get("props", []):
            if p.get("at", 0) > 0:
                sfx.append({"name": "pop", "at": lines[p["at"]]["start"]})
        t += 2 * BAR if song else SCENE_TAIL
        scenes.append({k2: v for k2, v in sc.items() if k2 != "lines"} |
                      {"start": round(start * FPS), "end": round(t * FPS), "lines": lines} | ({"song": tema} if tema else {}))
        if tema:  # sin musiquilla mientras suena la cancion de baile
            a0, a1 = tema["start"] / FPS, (tema["start"] + tema["dur"]) / FPS
            musica_tramos += [(start, a0, True), (a0, a1, None), (a1, t, True)]
        else:
            musica_tramos.append((start, t, song or sc.get("type") in ("dance", "hook")))

    # Despedida con su cancion al final: Zibu y Lila dicen adios con la mano
    adios = cancion("bye", lang)
    if adios:
        ultima = scenes[-1]
        start = t
        tema = {"src": adios["src"], "start": round(t * FPS), "dur": round(adios["dur"] * FPS)}
        t += adios["dur"] + 0.8
        scenes.append({"id": "bye", "type": "bye", "bg": ultima["bg"], "time": ultima["time"], "cast": ultima["cast"],
                       "start": round(start * FPS), "end": round(t * FPS), "lines": [], "song": tema})
        musica_tramos.append((start, t, None))

    # Duracion minima: se alarga la ultima escena (fiesta o despedida) con musica alegre
    total = t + 1.0
    falta = MIN_TOTAL - total
    if falta > 0:
        if falta > MAX_PAD or scenes[-1].get("type") not in ("dance", "bye"):
            raise SystemExit(f"Episodio demasiado corto: {total:.0f} s (minimo {MIN_TOTAL} s)")
        scenes[-1]["end"] += round(falta * FPS)
        musica_tramos.append((t, t + falta, True))
        total += falta

    # Musica: tranquila en la historia, alegre en la cancion (mas alta), nada donde suena una cancion fija
    musica = np.zeros(int(SR * total))
    for a, b, song in musica_tramos:
        if song is None or b - a < 0.5:
            continue
        tramo = tramo_musical(b - a, ALEGRE if song else CALMA, 2.4 if song else 1.0)
        i = int(a * SR)
        fade = min(int(SR * 0.4), len(tramo) // 4)
        tramo[:fade] *= np.linspace(0, 1, fade)
        tramo[-fade:] *= np.linspace(1, 0, fade)
        musica[i:i + len(tramo)] += tramo[:len(musica) - i]
    guardar_wav(out / "musica.wav", musica)
    for nombre, x in efectos().items():
        guardar_wav(BASE / "public" / "sfx" / f"{nombre}.wav", x)
    for sc in scenes:  # el invitado que cae desde fuera del cuadro suena con un "fiuuu"
        inicio = {c["who"]: c.get("y", 0) for c in sc["cast"]}
        for ln in sc["lines"]:
            if any(m["who"] in ("star", "guest") and inicio.get(m["who"], 0) < 0 and m.get("toY", 0) > 0.5
                   for m in ln.get("moves", [])):
                sfx.append({"name": "fiu", "at": ln["start"]})

    timeline = {"id": story["id"], "lang": lang, "title": story["title"][lang], "fps": FPS,
                "durationInFrames": round(total * FPS), "music": f"ep/{story['id']}/{lang}/musica.wav",
                "names": {"guest": story["guest"]["name"][lang]}, "guest": guest, "sfx": sfx, "scenes": scenes}
    if "thumb" in story:
        key = story["scenes"][min(max(1, int(story["thumb"].get("scene", 1))), len(story["scenes"]) - 1)]
        timeline["thumb"] = {"text": story["thumb"][lang], "bg": key["bg"], "time": key["time"]}
    (out / "timeline.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")
    n = sum(len(s["lines"]) for s in scenes)
    print(f"{story['id']} [{lang}]: {len(scenes)} escenas, {n} frases, {int(total // 60)}:{int(total % 60):02d} min")


if __name__ == "__main__":
    story_path, lang = sys.argv[1], sys.argv[2]
    # Espanol con ElevenLabs mientras queden creditos; si se acaban a mitad, el episodio entero con Kokoro
    if lang == "es" and eleven_key():
        try:
            main(story_path, lang, "eleven")
        except ElevenAgotado as e:
            print(f"   ! ElevenLabs no disponible ({e}): rehago el episodio entero con Kokoro")
            main(story_path, lang, "kokoro")
    else:
        main(story_path, lang)
