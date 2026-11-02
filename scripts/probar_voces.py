"""Muestras de voces de Kokoro para elegir narrador y personajes.

Uso: python scripts/probar_voces.py   -> out/voces/*.wav y out/voces/todas.wav (todas seguidas)
"""
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "out" / "voces"
SR = 24000

EN = "Oh wow! Look at that! A tiny little star... fell right into the garden! Should we go and see it? Let's go!"
ES = "¡Oh, mira eso! Una estrellita muy pequeñita... ¡se cayó en el jardín! ¿Vamos a verla? ¡Vamos!"

# (nombre, voz, idioma, texto, velocidad, subida de tono en semitonos)
PRUEBAS = [
    ("en_narradora_heart", "af_heart", "en-us", EN, 0.95, 0),
    ("en_narradora_bella", "af_bella", "en-us", EN, 0.95, 0),
    ("en_narradora_emma_uk", "bf_emma", "en-gb", EN, 0.95, 0),
    ("en_zibu_puck_agudo", "am_puck", "en-us", EN, 1.0, 4),
    ("en_zibu_heart_agudo", "af_heart", "en-us", EN, 1.0, 5),
    ("en_nina_sky_agudo", "af_sky", "en-us", EN, 1.0, 3),
    ("es_narradora_dora", "ef_dora", "es", ES, 0.95, 0),
    ("es_narrador_alex", "em_alex", "es", ES, 0.95, 0),
    ("es_zibu_dora_agudo", "ef_dora", "es", ES, 1.0, 5),
]


def subir_tono(x: np.ndarray, semitonos: float) -> np.ndarray:
    """Remuestreo simple: sube el tono y acelera a la vez (se compensa generando mas lento)."""
    if not semitonos:
        return x
    f = 2 ** (semitonos / 12)
    idx = np.arange(0, len(x) - 1, f)
    return np.interp(idx, np.arange(len(x)), x).astype(np.float32)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    k = Kokoro(str(BASE / "models" / "kokoro-v1.0.onnx"), str(BASE / "models" / "voices-v1.0.bin"))
    todas = []
    for nombre, voz, lang, texto, speed, tono in PRUEBAS:
        f = 2 ** (tono / 12)
        audio, sr = k.create(texto, voice=voz, speed=speed / f, lang=lang)
        audio = subir_tono(audio, tono)
        sf.write(OUT / f"{nombre}.wav", audio, sr)
        todas += [audio, np.zeros(int(sr * 1.2), dtype=np.float32)]
        print(f"{nombre}: {len(audio) / sr:.1f} s")
    sf.write(OUT / "todas.wav", np.concatenate(todas), SR)


if __name__ == "__main__":
    main()
