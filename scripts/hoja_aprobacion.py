"""Hojas para aprobar los dibujos nuevos antes de usarlos en un video.

  python scripts/hoja_aprobacion.py chars <n> puppy kitten  -> out/aprobar-chars-<n>.png (+ -magenta)
  python scripts/hoja_aprobacion.py props                     -> out/aprobar-objetos.png (+ -magenta)
  python scripts/hoja_aprobacion.py bgs                       -> out/aprobar-fondos.png

Fondo verde para verlas; la copia en magenta sirve para cazar huecos transparentes (ojos sin blanco) o figuras
cortadas por el borde: cualquier rosa dentro de una cara es un fallo.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent.parent
V2 = BASE / "public" / "v2"
OUT = BASE / "out"
CARAS = ["happy_closed", "happy_open", "happy_blink", "neutral_closed", "neutral_open", "surprised_closed",
         "surprised_open", "sad_closed", "sad_open", "laugh_closed", "laugh_open"]
NOMBRE = {"happy_closed": "feliz cerrada", "happy_open": "feliz abierta", "happy_blink": "parpadeo",
          "neutral_closed": "normal cerrada", "neutral_open": "normal abierta", "surprised_closed": "sorpresa cerrada",
          "surprised_open": "sorpresa abierta", "sad_closed": "triste cerrada", "sad_open": "triste abierta",
          "laugh_closed": "risa cerrada", "laugh_open": "risa abierta"}


def fuente(t: int) -> ImageFont.FreeTypeFont:
    for f in ("C:/Windows/Fonts/arialbd.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        if Path(f).exists():
            return ImageFont.truetype(f, t)
    return ImageFont.load_default()


def encajar(im: Image.Image, w: int, h: int) -> Image.Image:
    esc = min(w / im.width, h / im.height)
    return im.resize((max(1, round(im.width * esc)), max(1, round(im.height * esc))), Image.LANCZOS)


def rejilla(filas: list[tuple[str, list[tuple[str, Path]]]], cw: int, ch: int, salida: str) -> None:
    cols = max(len(f[1]) for f in filas)
    izq, cab, eti = 170, 10, 34
    W, H = izq + cols * cw, cab + len(filas) * (ch + eti)
    for color, suf in (("#3cb043", ""), ("#ff00ff", "-magenta")):
        hoja = Image.new("RGB", (W, H), color)
        d = ImageDraw.Draw(hoja)
        for r, (titulo, celdas) in enumerate(filas):
            y = cab + r * (ch + eti)
            d.text((12, y + ch // 2), titulo, fill="white", font=fuente(30), stroke_width=3, stroke_fill="black")
            for c, (rotulo, p) in enumerate(celdas):
                x = izq + c * cw
                if p.exists():
                    im = encajar(Image.open(p).convert("RGBA"), cw - 16, ch - 10)
                    hoja.paste(im, (x + (cw - im.width) // 2, y + ch - im.height), im)
                else:
                    d.text((x + 20, y + ch // 2), "FALTA", fill="red", font=fuente(28))
                d.text((x + cw // 2, y + ch + 4), rotulo, fill="white", font=fuente(20), anchor="ma",
                       stroke_width=2, stroke_fill="black")
        hoja.save(OUT / f"{salida}{suf}.png")
        print(OUT / f"{salida}{suf}.png")


def chars(quienes: list[str], n: int) -> None:
    filas = [(q, [(NOMBRE[c], V2 / "chars3" / q / f"{c}.png") for c in CARAS]) for q in quienes]
    rejilla(filas, 190, 230, f"aprobar-chars-{n}")


def props() -> None:
    ps = sorted((V2 / "props").glob("*.png"))
    filas = [(f"{i // 7 + 1}", [(p.stem, p) for p in ps[i:i + 7]]) for i in range(0, len(ps), 7)]
    rejilla(filas, 240, 240, "aprobar-objetos")


def bgs() -> None:
    fs = sorted((V2 / "bg").glob("*.png"))
    cw, ch, eti = 640, 360, 40
    cols = 3
    filas = (len(fs) + cols - 1) // cols
    hoja = Image.new("RGB", (cols * (cw + 10) + 10, filas * (ch + eti + 10) + 10), "#222222")
    d = ImageDraw.Draw(hoja)
    for i, f in enumerate(fs):
        x, y = 10 + (i % cols) * (cw + 10), 10 + (i // cols) * (ch + eti + 10)
        hoja.paste(Image.open(f).convert("RGB").resize((cw, ch), Image.LANCZOS), (x, y))
        d.text((x + cw // 2, y + ch + 6), f.stem, fill="white", font=fuente(26), anchor="ma")
    hoja.save(OUT / "aprobar-fondos.png")
    print(OUT / "aprobar-fondos.png")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "chars":
        chars(sys.argv[3:], int(sys.argv[2]))
    elif cmd == "props":
        props()
    else:
        bgs()
