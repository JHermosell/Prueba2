"""
make_icon.py

Genera un icono simple de reloj (clock.ico) usando Pillow.
Se crea un ICO multi-res (256x256, 64x64, 32x32) y se guarda en la raíz del proyecto como `clock.ico`.

Ejecutar antes de compilar con PyInstaller para incluir el icono:
    python make_icon.py
"""
from PIL import Image, ImageDraw


def create_clock_icon(path: str = 'clock.ico'):
    sizes = [256, 64, 32]
    imgs = []
    for s in sizes:
        img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # fondo circular
        draw.ellipse((0, 0, s - 1, s - 1), fill=(30, 30, 30, 255))
        # marca central
        cx = cy = s // 2
        r = int(s * 0.42)
        # manecillas: hora (corta) y minuto (larga)
        # minuto (vertical up)
        draw.line((cx, cy, cx, cy - int(r * 0.8)), fill=(245, 245, 245, 255), width=max(1, s // 16))
        # hora (slight right)
        draw.line((cx, cy, cx + int(r * 0.5), cy), fill=(245, 245, 245, 255), width=max(1, s // 12))
        # central pin
        draw.ellipse((cx - s // 30, cy - s // 30, cx + s // 30, cy + s // 30), fill=(200, 30, 30, 255))
        imgs.append(img)

    # guardar como ico multi-res
    imgs[0].save(path, format='ICO', sizes=[(sizes[0], sizes[0]), (sizes[1], sizes[1]), (sizes[2], sizes[2])])
    print(f'Icono guardado en: {path}')


if __name__ == '__main__':
    create_clock_icon('clock.ico')
