#!/usr/bin/env python3
"""
Automação de engajamento Instagram — Comentários & Compartilhamentos DM.

Controla Chromium via pyautogui (simulação de mouse/teclado real) para postar
comentários e compartilhar um post do Instagram para amigos via DM em loop.

Requer Wayland com XWayland ativo (DISPLAY definido) e wl-clipboard instalado.

Uso:
    ./venv/bin/python main.py
    ./venv/bin/python main.py --sem-chromium --recalibrar

Failsafe: mova o mouse para o canto superior esquerdo para parar.
"""

# mouseinfo (dependência do pyautogui) importa tkinter no load. No Arch Linux,
# tkinter requer o pacote "tk" instalado separadamente via pacman. Como não
# usamos mouseinfo, injetamos um módulo vazio para evitar o ImportError.
import sys
import types
sys.modules['mouseinfo'] = types.ModuleType('mouseinfo')

import pyautogui
import subprocess
import time
import random
import json
import os
import argparse

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3  # delay implícito entre cada chamada pyautogui

COMMENT_TEXT = "Mais um comentário 🙃"
POST_URL = "https://www.instagram.com/p/DUtop27ko2o/"
FRIENDS = (
    "rinouclem",
    "mydgellson*ac",
    "lebcarvalho*",
    "anamel.neves",
    "clarasilveira.nutri",
    "mayara.elissa",
    "marialuizapaiva4",
    "mitscherlyne",
)
CALIBRATION_FILE = os.path.join(os.path.dirname(__file__), "calibration.json")


def human_delay(min_s=0.3, max_s=0.8):
    time.sleep(random.uniform(min_s, max_s))


def clipboard_paste(text):
    """Usa wl-copy + Ctrl+V porque pyautogui.typewrite() não suporta unicode."""
    subprocess.run(
        ["wl-copy", "--", text],
        check=True,
        timeout=5,
    )
    human_delay(0.1, 0.3)
    pyautogui.hotkey("ctrl", "v")
    human_delay(0.2, 0.4)


def calibrate():
    """Calibração interativa — registra posições dos elementos da UI."""
    positions = {}

    elements = [
        ("comment_field", "Campo de comentário (onde se digita o texto)"),
        ("share_icon", "Ícone de compartilhar (avião de papel)"),
        ("share_search", "Campo de busca no modal de compartilhar"),
        ("share_first_result", "Primeiro resultado da busca no modal"),
        ("share_send", "Botão 'Enviar' no modal de compartilhar"),
    ]

    print("\n╔══════════════════════════════════════╗")
    print("║          CALIBRAÇÃO                  ║")
    print("╚══════════════════════════════════════╝")
    print("Posicione o mouse sobre cada elemento e pressione ENTER.\n")

    for key, description in elements:
        input(f"  → {description}: ")
        pos = pyautogui.position()
        positions[key] = [pos.x, pos.y]
        print(f"    Registrado: ({pos.x}, {pos.y})\n")

    with open(CALIBRATION_FILE, "w") as f:
        json.dump(positions, f, indent=2)
    print(f"Calibração salva em {CALIBRATION_FILE}\n")

    return positions


def load_calibration():
    """Carrega calibração salva, se existir."""
    if os.path.exists(CALIBRATION_FILE):
        with open(CALIBRATION_FILE) as f:
            return json.load(f)
    return None


def click_at(pos_key, positions):
    """Clica na posição calibrada. Offset ±3px para não repetir o pixel exato."""
    x, y = positions[pos_key]
    pyautogui.click(x + random.randint(-3, 3), y + random.randint(-3, 3))


def do_comment(positions):
    """Clica no campo de comentário, cola o texto e envia com Enter."""
    click_at("comment_field", positions)
    human_delay(0.8, 1.5)
    clipboard_paste(COMMENT_TEXT)
    human_delay(0.3, 0.5)
    pyautogui.press("enter")
    human_delay(1.0, 1.5)


def do_share_dm_all(positions, friends):
    """Abre o modal de share uma vez, seleciona todos os amigos e envia em batch."""
    click_at("share_icon", positions)
    human_delay(0.8, 1.2)

    for i, friend in enumerate(friends):
        click_at("share_search", positions)
        human_delay(0.2, 0.4)

        # Limpar busca anterior antes de digitar o próximo nome
        if i > 0:
            pyautogui.hotkey("ctrl", "a")
            human_delay(0.1, 0.2)
            pyautogui.press("backspace")
            human_delay(0.2, 0.4)

        clipboard_paste(friend)
        human_delay(0.8, 1.2)
        click_at("share_first_result", positions)
        human_delay(0.4, 0.7)
        print(f"    + {friend}")

    click_at("share_send", positions)
    human_delay(1.0, 1.5)
    pyautogui.press("escape")
    human_delay(0.5, 0.8)


def open_chromium(url):
    """Força Chromium em X11 via --ozone-platform (pyautogui usa Xlib, não funciona em Wayland nativo)."""
    print("Abrindo Chromium em modo X11...")
    subprocess.Popen(
        ["chromium", "--ozone-platform=x11", url],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser(description="Automação de engajamento Instagram")
    parser.add_argument(
        "--comentarios",
        type=int,
        default=0,
        help="Número máximo de comentários (0 = infinito)",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=1.5,
        help="Delay mínimo entre ciclos em segundos (default: 1.5)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=1.5,
        help="Delay máximo entre ciclos em segundos (default: 1.5)",
    )
    parser.add_argument(
        "--recalibrar",
        action="store_true",
        help="Forçar recalibração mesmo se já existir",
    )
    parser.add_argument(
        "--sem-chromium",
        action="store_true",
        help="Não abrir Chromium (usar janela já aberta)",
    )

    args = parser.parse_args()

    if not args.sem_chromium:
        open_chromium(POST_URL)

    input("\nFaça login se necessário e aguarde o post carregar.\nPressione ENTER quando pronto...")

    positions = None if args.recalibrar else load_calibration()
    if positions:
        print(f"\nCalibração anterior encontrada: {CALIBRATION_FILE}")
        usar = input("Usar calibração salva? (S/n): ").strip().lower()
        if usar == "n":
            positions = calibrate()
    else:
        positions = calibrate()

    print("\n╔══════════════════════════════════════╗")
    print("║        INICIANDO AUTOMAÇÃO           ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Comentário: {COMMENT_TEXT}")
    print(f"  Amigos DM:  {', '.join(FRIENDS)}")
    print(f"  Delay:      {args.delay_min:.0f}-{args.delay_max:.0f}s entre ciclos")
    print(f"  Limite:     {args.comentarios if args.comentarios else 'infinito'} comentários")
    print(f"\n  FAILSAFE: mova o mouse para o canto superior esquerdo para PARAR\n")

    input("Pressione ENTER para começar...")

    cycle = 0
    try:
        while True:
            cycle += 1
            cycle_start = time.time()
            print(f"\n--- Ciclo {cycle} ---")

            print(f"  Comentando (100x)...")
            for c in range(1, 101):
                do_comment(positions)
                print(f"    comentário {c}/100")
                time.sleep(0.2)
            print(f"  OK - 100 comentários enviados")

            if FRIENDS:
                for s in range(1, 3):
                    human_delay(0.5, 1.0)
                    print(f"  Compartilhamento {s}/2 com {len(FRIENDS)} amigos...")
                    do_share_dm_all(positions, FRIENDS)
                    print(f"  OK - compartilhamento {s}/2 concluído")

            elapsed = time.time() - cycle_start
            print(f"  Ciclo {cycle} concluído em {elapsed:.1f}s")

            time.sleep(1.5)

    except KeyboardInterrupt:
        print(f"\n\nParado pelo usuário (Ctrl+C) após {cycle} ciclos.")
    except pyautogui.FailSafeException:
        print(f"\n\nFAILSAFE ativado! Parado após {cycle} ciclos.")

    print("Fim.")


if __name__ == "__main__":
    main()
