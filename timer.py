"""
Cronometro didactico de 2 minutos construido con OpenCV.

Objetivo: que un principiante pueda leer el archivo de arriba a abajo
sin perderse. Cada bloque esta etiquetado y solo hace una cosa.

Flujo:
  1. Muestra una ventana con el tiempo restante y textos explicativos.
  2. En paralelo pregunta una tabla MySQL (hilo en background).
  3. Al terminar emite un beep, cierra OpenCV y abre Tkinter con los datos.

Controles dentro de la ventana:
  - Barra espaciadora  -> Pausar/Reanudar.
  - Tecla r            -> Reiniciar a 2 minutos.
  - Tecla q o ESC      -> Salir de inmediato.
"""
from __future__ import annotations

import os
import platform
import queue
import sys
import threading
import time
import tkinter as tk
from dataclasses import dataclass, field
from tkinter import scrolledtext
from typing import List

import cv2
import numpy as np


# --------------------------------------------------------------------------- #
# CONFIGURACION RAPIDA (modifica estos valores sin tocar el resto del codigo)
# --------------------------------------------------------------------------- #
TOTAL_SECONDS = 10
WINDOW_NAME = "Cronometro OpenCV"
WINDOW_SIZE = (960, 420)  # (ancho, alto)
BACKGROUND_COLOR = (25, 25, 25)  # BGR -> gris oscuro
HIGHLIGHT_COLOR = (255, 255, 255)  # digitos principales
TEXT_COLOR = (215, 215, 215)  # etiquetas suaves para no distraer
FONT = cv2.FONT_HERSHEY_SIMPLEX

LABELS = [
    "Tiempo restante (MM:SS)",
    "Estado actual del cronometro",
    "Controles: ESPACIO=pausa  |  R=reiniciar  |  Q/ESC=salir",
]


# --------------------------------------------------------------------------- #
# ESTRUCTURAS DE DATOS DEL CRONOMETRO
# --------------------------------------------------------------------------- #
def now() -> float:
    """Usamos time.monotonic para evitar problemas si cambia el reloj del SO."""
    return time.monotonic()


@dataclass
class TimerState:
    """Estado minimo necesario del cronometro."""

    total_seconds: int
    remaining: int = field(init=False)
    paused: bool = field(default=False, init=False)
    finished: bool = field(default=False, init=False)
    _end_time: float = field(default=0.0, init=False, repr=False)

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Vuelve al estado inicial y reinicia el conteo."""
        self.remaining = self.total_seconds
        self.paused = False
        self.finished = False
        self._end_time = now() + self.total_seconds

    def toggle_pause(self) -> None:
        """Invierte la pausa. Al reanudar recalcula el tiempo final."""
        self.paused = not self.paused
        if not self.paused:
            self._end_time = now() + self.remaining

    def tick(self) -> bool:
        """Actualiza el tiempo restante. Devuelve True cuando llega a 0."""
        if self.paused or self.finished:
            return False
        self.remaining = max(0, int(self._end_time - now()))
        if self.remaining == 0:
            self.finished = True
            return True
        return False


# --------------------------------------------------------------------------- #
# DIBUJO DE LA VENTANA (separamos fondo estatico y textos dinamicos)
# --------------------------------------------------------------------------- #
def put_text_with_outline(
    img: np.ndarray,
    text: str,
    org: tuple[int, int],
    scale: float,
    color: tuple[int, int, int],
    thickness: int = 5,
    outline_color: tuple[int, int, int] = (0, 0, 0),
    outline_extra: int = 2,
) -> None:
    """Solo para los digitos: relleno blanco con contorno negro marcado."""
    cv2.putText(img, text, org, FONT, scale, outline_color, thickness + outline_extra, cv2.LINE_AA)
    cv2.putText(img, text, org, FONT, scale, color, thickness, cv2.LINE_AA)


def center_text(img: np.ndarray, text: str, y: int, scale: float, color, thickness: int = 2) -> None:
    width, _ = cv2.getTextSize(text, FONT, scale, thickness)[0]
    x = (img.shape[1] - width) // 2
    cv2.putText(img, text, (x, y), FONT, scale, color, thickness, cv2.LINE_AA)


def build_background() -> np.ndarray:
    """Dibuja una plantilla con etiquetas fijas."""
    canvas = np.full((WINDOW_SIZE[1], WINDOW_SIZE[0], 3), BACKGROUND_COLOR, dtype=np.uint8)
    center_text(canvas, LABELS[0], 70, 0.9, TEXT_COLOR)
    center_text(canvas, LABELS[2], 360, 0.75, TEXT_COLOR)
    cv2.rectangle(canvas, (120, 110), (WINDOW_SIZE[0] - 120, 310), (90, 90, 90), 2)
    return canvas


BACKGROUND_FRAME = build_background()


def render_frame(state: TimerState) -> np.ndarray:
    """Copia el fondo y agrega los textos variables."""
    frame = BACKGROUND_FRAME.copy()
    minutes, seconds = divmod(state.remaining, 60)
    digits = f"{minutes:02d}:{seconds:02d}"
    width, _ = cv2.getTextSize(digits, FONT, 3.8, 5)[0]
    x = (frame.shape[1] - width) // 2
    put_text_with_outline(frame, digits, (x, 210), 3.8, HIGHLIGHT_COLOR)

    if state.finished:
        status = "Tiempo cumplido"
    else:
        status = "Pausado" if state.paused else "En marcha"
    center_text(frame, f"{LABELS[1]} -> {status}", 300, 0.85, TEXT_COLOR)
    return frame


# --------------------------------------------------------------------------- #
# UTILIDADES DE SONIDO Y BASE DE DATOS
# --------------------------------------------------------------------------- #
def beep_end() -> None:
    """Emite un beep sencillo. Ignora errores para no interrumpir el flujo."""
    try:
        if platform.system() == "Windows":
            import winsound

            winsound.Beep(1100, 600)
        else:
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        pass


def fetch_table_async(result_queue: queue.Queue, table: str = "tbl001") -> None:
    """Lanza un hilo muy simple que consulta MySQL y deja el resultado en la cola."""

    def worker() -> None:
        try:
            import mysql.connector

            conn = mysql.connector.connect(
                host=os.environ.get("DB_HOST", "127.0.0.1"),
                port=int(os.environ.get("DB_PORT", "3306")),
                user=os.environ.get("DB_USER", "root"),
                password=os.environ.get("DB_PASS", "123456"),
                database=os.environ.get("DB_NAME", "pruebas02"),
            )
            cursor = conn.cursor()
            cursor.execute(f"SHOW COLUMNS FROM `{table}`")
            columns = [row[0] for row in cursor.fetchall()]
            cursor.execute(f"SELECT * FROM `{table}` ORDER BY id_registro")
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
            result_queue.put({"columns": columns, "rows": rows})
        except Exception as exc:
            result_queue.put({"error": str(exc)})

    threading.Thread(target=worker, daemon=True).start()


def show_table_window(result_queue: queue.Queue) -> None:
    """Abre una ventana Tkinter con el resultado (o error) de la consulta."""
    root = tk.Tk()
    root.title("Resultado de la consulta MySQL")

    text = scrolledtext.ScrolledText(root, width=110, height=25, font=("Consolas", 10))
    text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    text.insert(tk.END, "Consulta ejecutada en paralelo al cronometro\n")
    text.insert(tk.END, "-" * 80 + "\n\n")

    try:
        result = result_queue.get_nowait()
    except queue.Empty:
        result = {"error": "El hilo aun no termina o no devolvio datos."}

    if "error" in result:
        text.insert(tk.END, f"Error al obtener datos: {result['error']}\n")
    else:
        columns: List[str] = result["columns"]
        rows = result["rows"]
        header = " | ".join(columns)
        text.insert(tk.END, header + "\n")
        text.insert(tk.END, "-" * len(header) + "\n")
        for row in rows:
            text.insert(tk.END, " | ".join(str(cell) for cell in row) + "\n")

    text.configure(state=tk.DISABLED)
    root.mainloop()


# --------------------------------------------------------------------------- #
# BUCLE PRINCIPAL DEL CRONOMETRO
# --------------------------------------------------------------------------- #
def handle_key(key: int, state: TimerState) -> bool:
    """Procesa la tecla presionada. Devuelve False si hay que cerrar el bucle."""
    if key in (ord("q"), 27):
        return False
    if key == ord(" "):
        state.toggle_pause()
    elif key == ord("r"):
        state.reset()
    return True


def run_timer(total_seconds: int) -> None:
    """Loop principal: dibuja frames, maneja teclas y dispara la base de datos."""
    state = TimerState(total_seconds)
    result_queue: queue.Queue = queue.Queue()
    fetch_table_async(result_queue)

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, *WINDOW_SIZE)

    beep_sent = False
    while True:
        if state.tick() and not beep_sent:
            beep_end()
            beep_sent = True

        frame = render_frame(state)
        cv2.imshow(WINDOW_NAME, frame)

        key = cv2.waitKey(100) & 0xFF
        if key != 0xFF and not handle_key(key, state):
            break

    cv2.destroyAllWindows()
    show_table_window(result_queue)


# --------------------------------------------------------------------------- #
# ENTRADA DEL PROGRAMA
# --------------------------------------------------------------------------- #
def main() -> None:
    print("Iniciando cronometro de 2 minutos. Controlalo en la ventana OpenCV.")
    run_timer(TOTAL_SECONDS)


if __name__ == "__main__":
    main()
