"""
example.py

Script de ejemplo que carga una imagen con OpenCV y la muestra con matplotlib.
Si no se proporciona una ruta, genera una imagen de prueba (gradiente + texto).
Guarda una copia en `example_output.png` en la raíz del proyecto.

Uso:
    # con imagen existente
    python example.py --image path\to\image.jpg

    # sin imagen (genera una de prueba)
    python example.py
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

import cv2
import matplotlib.pyplot as plt
import numpy as np


def load_image(path: str) -> Optional[np.ndarray]:
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        return None
    # OpenCV loads BGR, convert to RGB for matplotlib
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


def make_test_image(width: int = 640, height: int = 480) -> np.ndarray:
    # Gradient background
    x = np.linspace(0, 1, width)
    y = np.linspace(0, 1, height)
    xv, yv = np.meshgrid(x, y)
    r = (xv * 255).astype(np.uint8)
    g = (yv * 255).astype(np.uint8)
    b = (((1 - xv) * (1 - yv)) * 255).astype(np.uint8)
    img = np.dstack([r, g, b])

    # Añadir texto con OpenCV (BGR expected)
    img_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    text = "Example Image"
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img_bgr, text, (20, height - 30), font, 1.2, (255, 255, 255), 2, cv2.LINE_AA)
    img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return img


def show_and_save(img: np.ndarray, out_path: str) -> None:
    plt.figure(figsize=(8, 6))
    plt.axis('off')
    plt.imshow(img)
    plt.tight_layout()
    # Guardar imagen resultante
    plt.savefig(out_path, bbox_inches='tight', pad_inches=0)
    print(f"Saved output to: {out_path}")
    try:
        plt.show()
    except Exception:
        # En entornos sin GUI, plt.show() puede fallar; lo ignoramos
        pass


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Ejemplo: cargar imagen con OpenCV y mostrarla con matplotlib')
    p.add_argument('--image', '-i', type=str, help='Ruta a la imagen (opcional)')
    p.add_argument('--out', '-o', type=str, default='example_output.png', help='Ruta de salida para la imagen generada')
    return p.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.image:
        img = load_image(args.image)
        if img is None:
            print(f"Error: no se pudo leer la imagen en '{args.image}'", file=sys.stderr)
            return 2
    else:
        img = make_test_image()

    out_path = os.path.abspath(args.out)
    show_and_save(img, out_path)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
