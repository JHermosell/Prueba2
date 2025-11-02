"""
timer.py

Ventana con cronómetro de 2 minutos usando OpenCV.

Controles:
  - Barra espaciadora: pausar/reanudar
  - r: reiniciar a 2:00
  - q o ESC: salir

Al terminar reproduce un beep en Windows (winsound) o hace un beep de consola como fallback.
"""
from __future__ import annotations

import time
import os
import platform
import sys

import cv2
import numpy as np
import logging
import ctypes
from ctypes import wintypes

# Configuración de logging para depuración
LOG_PATH = os.path.abspath('timer_debug.log')
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)


def set_window_title_windows(title: str) -> None:
    """Busca ventanas propiedad del proceso actual y establece su título (Wide) usando SetWindowTextW.

    Esto fuerza la barra de la ventana a mostrar acentos correctamente en Windows.
    """
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        EnumWindows = user32.EnumWindows
        GetWindowThreadProcessId = user32.GetWindowThreadProcessId
        SetWindowTextW = user32.SetWindowTextW
        GetWindowTextW = user32.GetWindowTextW
        GetWindowTextLengthW = user32.GetWindowTextLengthW
        GetCurrentProcessId = kernel32.GetCurrentProcessId

        pid = GetCurrentProcessId()

        EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _enum(hwnd, lParam):
            lpdw = wintypes.DWORD()
            GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw))
            if lpdw.value == pid:
                try:
                    # Read current window text
                    length = GetWindowTextLengthW(hwnd)
                    buf = ctypes.create_unicode_buffer(length + 1)
                    GetWindowTextW(hwnd, buf, length + 1)
                    before = buf.value
                    logger.info(f'set_window_title_windows: hwnd={hwnd}, before_title={before!r}')
                    # Attempt to set wide title
                    res = SetWindowTextW(hwnd, title)
                    # Read back
                    length2 = GetWindowTextLengthW(hwnd)
                    buf2 = ctypes.create_unicode_buffer(length2 + 1)
                    GetWindowTextW(hwnd, buf2, length2 + 1)
                    after = buf2.value
                    logger.info(f'set_window_title_windows: hwnd={hwnd}, SetWindowTextW_res={res}, after_title={after!r}')
                except Exception:
                    logger.exception(f'set_window_title_windows: exception handling hwnd={hwnd}')
            return True

        EnumWindows(EnumProc(_enum), 0)
        logger.info(f'set_window_title_windows: attempted to set title to "{title}"')
    except Exception:
        logger.exception('set_window_title_windows failed')


TOTAL_SECONDS = 10  # 10 segundos
WINDOW_NAME = "Cronómetro1"
# Log the actual bytes/ords to help diagnose encoding issues
logger = logging.getLogger(__name__)


def format_time(sec: int) -> str:
    sec = max(0, sec)
    m = sec // 60
    s = sec % 60
    return f"{m:02d}:{s:02d}"


def beep_end():
    try:
        if platform.system() == 'Windows':
            import winsound

            # frecuencia 1000Hz, duración 700ms
            winsound.Beep(1000, 700)
            logger.info('beep_end: winsound.Beep called')
        else:
            # Intenta emitir campana ASCII
            sys.stdout.write('\a')
            sys.stdout.flush()
            logger.info('beep_end: ascii bell emitted')
    except Exception:
        # fallback silencioso
        logger.exception('beep_end: exception')
        pass


def make_frame(text: str, width: int = 640, height: int = 240) -> np.ndarray:

    # Usar supersampling con Pillow: renderizar a escala (p. ej. 6x) y reducir para suavizar bordes
    try:
        from PIL import Image, ImageDraw, ImageFont

        # mejorar suavizado aumentando el factor de supersampling
        scale = 6
        big_w, big_h = width * scale, height * scale
        img = Image.new('RGB', (big_w, big_h), (10, 10, 10))
        draw = ImageDraw.Draw(img)

        # Calculamos un tamaño de fuente grande acorde al canvas aumentado
        fontsize = int(big_h * 0.45)
        # Intentar fuentes de sistema conocidas (Segoe UI es preferible en Windows)
        font = None
        candidates = [
            r"C:\\Windows\\Fonts\\segoeui.ttf",
            r"C:\\Windows\\Fonts\\SegoeUI.ttf",
            r"C:\\Windows\\Fonts\\seguisb.ttf",
            r"C:\\Windows\\Fonts\\arial.ttf",
            r"C:\\Windows\\Fonts\\calibri.ttf",
        ]
        chosen_font_path = None
        for fpath in candidates:
            if os.path.exists(fpath):
                try:
                    font = ImageFont.truetype(fpath, fontsize)
                    chosen_font_path = fpath
                    break
                except Exception:
                    continue
        if font is None:
            try:
                font = ImageFont.truetype('arial.ttf', fontsize)
                chosen_font_path = 'arial.ttf'
            except Exception:
                font = ImageFont.load_default()
        logger.info(f'Chosen font for main text: {chosen_font_path}')

        # Medir texto y centrar
        text_w, text_h = draw.textsize(text, font=font)
        x = (big_w - text_w) // 2
        y = (big_h - text_h) // 2

        # Dibujar con stroke (ajustado por escala) para bordes definidos
        stroke = max(2, int(scale * 1.5))
        try:
            draw.text((x, y), text, font=font, fill=(245, 245, 245), stroke_width=stroke, stroke_fill=(15, 15, 15))
        except TypeError:
            # Si la versión de Pillow no soporta stroke_width, dibujamos sombra y luego el texto
            draw.text((x + stroke // 2, y + stroke // 2), text, font=font, fill=(15, 15, 15))
            draw.text((x, y), text, font=font, fill=(245, 245, 245))

        # Reducir a tamaño objetivo con reescalado de alta calidad para suavizar
        img_small = img.resize((width, height), resample=Image.LANCZOS)
        arr = np.array(img_small)
        frame = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        # Añadir subtítulo dentro de la imagen (top center) para garantizar que el acento se vea
        try:
            from PIL import Image as PILImage, ImageDraw as PILImageDraw, ImageFont as PILImageFont
            img2 = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            draw2 = PILImageDraw.Draw(img2)
            sub_fontsize = max(12, int(big_h * 0.08))
            subfont = None
            for fpath in candidates:
                try:
                    if os.path.exists(fpath):
                        subfont = PILImageFont.truetype(fpath, sub_fontsize)
                        break
                except Exception:
                    continue
            if subfont is None:
                try:
                    subfont = PILImageFont.truetype('arial.ttf', sub_fontsize)
                except Exception:
                    subfont = PILImageFont.load_default()
            sub_w, sub_h = draw2.textsize(SUBTITLE, font=subfont)
            sub_x = (width - sub_w) // 2
            sub_y = int(height * 0.04)
            try:
                draw2.text((sub_x, sub_y), SUBTITLE, font=subfont, fill=(230, 230, 230), stroke_width=max(1, scale // 2), stroke_fill=(10, 10, 10))
            except TypeError:
                draw2.text((sub_x + 2, sub_y + 2), SUBTITLE, font=subfont, fill=(10, 10, 10))
                draw2.text((sub_x, sub_y), SUBTITLE, font=subfont, fill=(230, 230, 230))
            frame = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR)
        except Exception:
            # si algo falla en Pillow al añadir subtítulo, lo añadimos con OpenCV al final (más abajo)
            pass
        logger.debug(f'make_frame: rendered text="{text}" size=({width},{height}) using Pillow')
        return frame
    except Exception:
        # Fallback simple con OpenCV
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 3.0
        thickness = 6
        (w, h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        x = (width - w) // 2
        y = (height + h) // 2
        cv2.putText(frame, text, (x + 4, y + 4), font, font_scale, (30, 30, 30), thickness + 2, cv2.LINE_AA)
        cv2.putText(frame, text, (x, y), font, font_scale, (220, 220, 220), thickness, cv2.LINE_AA)
        # Añadir subtítulo con OpenCV en fallback
        try:
            subtitle_font = cv2.FONT_HERSHEY_SIMPLEX
            sf = 0.8
            st = 2
            (sw, sh), _ = cv2.getTextSize(SUBTITLE, subtitle_font, sf, st)
            sub_x = (width - sw) // 2
            sub_y = int(height * 0.08) + sh
            cv2.putText(frame, SUBTITLE, (sub_x, sub_y), subtitle_font, sf, (230, 230, 230), st, cv2.LINE_AA)
        except Exception:
            pass
    logger.debug(f'make_frame: rendered text="{text}" size=({width},{height}) using OpenCV fallback')
    return frame


def run_timer(total_seconds: int = TOTAL_SECONDS) -> int:
    paused = False
    remaining = total_seconds
    last_update = time.time()
    end_time = time.time() + remaining

    # Asegurar que no queden ventanas abiertas de ejecuciones previas
    try:
        cv2.destroyAllWindows()
        logger.info('destroyAllWindows called at start')
    except Exception:
        logger.exception('destroyAllWindows at start failed')

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 800, 300)
    # Forzar título (unicode) en la barra de la ventana si la función está disponible
    try:
        cv2.setWindowTitle(WINDOW_NAME, WINDOW_NAME)
        logger.info(f'setWindowTitle called: "{WINDOW_NAME}"')
    except Exception:
        logger.exception('setWindowTitle not available or failed')
    # Also attempt Win32 wide-set of window title to ensure Unicode
    try:
        set_window_title_windows(WINDOW_NAME)
    except Exception:
        logger.exception('set_window_title_windows call failed')

    finished = False
    finished_time = None

    logger.info(f'starting run_timer with total_seconds={total_seconds}')
    while True:
        now = time.time()

        if not paused and not finished:
            remaining = int(round(end_time - now))

        if remaining <= 0 and not finished:
            # marcar terminado y registrar tiempo de finalización
            remaining = 0
            finished = True
            finished_time = time.time()
            # emitir sonido de finalización; la ventana se actualizará en la rama `finished`
            logger.info('timer reached zero, invoking beep_end')
            beep_end()

        if finished:
            # mostrar 'Adios' durante 3 segundos
            logger.info('showing Adios frame')
            cv2.imshow(WINDOW_NAME, make_frame("Adios"))
            # salir después de 3 segundos desde finished_time
            if finished_time is not None and (now - finished_time) >= 3.0:
                logger.info('finished_time elapsed >= 3s, breaking loop')
                break
        else:
            frame = make_frame(format_time(remaining))
            logger.debug(f'displaying frame for remaining={remaining}')
            cv2.imshow(WINDOW_NAME, frame)

        # Espera corta para capturar tecla; devuelve -1 si no hay tecla
        key = cv2.waitKey(100) & 0xFF
        if key != 0xFF:
            # Espacio: pausar/reanudar
            if key == ord(' ') or key == 32:
                paused = not paused
                logger.info(f'Key pressed: SPACE -> paused={paused}')
                if not paused:
                    # ajustar end_time para reanudar desde remaining
                    end_time = time.time() + remaining
            elif key == ord('r'):
                # reiniciar
                paused = False
                remaining = total_seconds
                end_time = time.time() + remaining
                finished = False
                finished_time = None
                logger.info('Key pressed: r -> reset timer')
            elif key == ord('q') or key == 27:
                # salir con 'q' o ESC
                logger.info('Key pressed: q/ESC -> exiting')
                break

    try:
        cv2.destroyAllWindows()
        logger.info('destroyAllWindows at exit')
    except Exception:
        logger.exception('destroyAllWindows at exit failed')
    logger.info('run_timer exiting')
    return 0


def main() -> int:
    msg = "Iniciando cronometro de 10 segundos. Teclas: espacio=pause, r=reiniciar, q/ESC=salir"
    print(msg)
    logger.info(msg)
    return run_timer(TOTAL_SECONDS)


if __name__ == '__main__':
    raise SystemExit(main())
