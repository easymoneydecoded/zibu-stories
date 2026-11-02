"""Guarda en GitHub (secrets del repo zibu-stories) la clave de Gemini y el bot de Telegram, sin mostrarlos.

Uso (en la terminal, desde la carpeta Infantil):  python scripts/configurar_secrets.py

- GEMINI_API_KEY: la de CarteraPasiva/.env
- TELEGRAM_BOT_TOKEN: el de Youtube/.env (tu bot de avisos personal)
- TELEGRAM_CHAT_ID: tu chat con ese bot. Antes de ejecutar, mandale cualquier mensaje al bot desde Telegram.
"""
import subprocess
import sys
from pathlib import Path

import requests

REPO = "easymoneydecoded/zibu-stories"
BASE = Path(__file__).resolve().parent.parent


def leer_env(ruta: Path, nombre: str) -> str:
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith(nombre + "="):
            return linea.split("=", 1)[1].strip().strip('"')
    sys.exit(f"No encuentro {nombre} en {ruta}")


def secret(nombre: str, valor: str) -> None:
    subprocess.run(["gh", "secret", "set", nombre, "-R", REPO], input=valor.encode(), check=True)
    print(f"   ✓ {nombre}")


def main() -> None:
    secret("GEMINI_API_KEY", leer_env(BASE.parent / "CarteraPasiva" / ".env", "GEMINI_API_KEY"))
    token = leer_env(BASE.parent / "Youtube" / ".env", "TELEGRAM_BOT_TOKEN")
    secret("TELEGRAM_BOT_TOKEN", token)
    updates = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=30).json().get("result", [])
    chats = {u["message"]["chat"]["id"] for u in updates if u.get("message", {}).get("chat", {}).get("type") == "private"}
    if not chats:
        sys.exit("No veo ningun mensaje tuyo al bot: mandale un mensaje desde Telegram y vuelve a ejecutar el script.")
    chat = str(sorted(chats)[-1])
    secret("TELEGRAM_CHAT_ID", chat)
    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", timeout=30,
                  data={"chat_id": chat, "text": "🧸 Zibu: los avisos de los episodios llegaran aqui."})
    print("Listo. Te ha llegado un mensaje de prueba a Telegram.")


if __name__ == "__main__":
    main()
