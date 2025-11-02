# Proyecto2 — Entorno virtual y dependencias

Este repositorio contiene la configuración mínima para trabajar en un proyecto de visión por computador.

## Entorno virtual
Se creó un entorno virtual llamado `venv` en la raíz del proyecto.

Activar en PowerShell (desde la raíz del proyecto):

```powershell
. .\venv\Scripts\Activate.ps1
```

Activar en cmd.exe:

```cmd
.\venv\Scripts\activate.bat
```

Desactivar:

```powershell
deactivate
```

## Dependencias
He instalado las siguientes librerías como ejemplo: `numpy`, `matplotlib`, `opencv-python`, `torch`, `torchvision`.
El archivo `requirements.txt` fue generado con `pip freeze`.

Instalar desde `requirements.txt`:

```powershell
pip install -r requirements.txt
```

Nota sobre PyTorch: si necesitas soporte CUDA específico, instala la versión adecuada siguiendo las instrucciones oficiales en https://pytorch.org/ (puede requerir seleccionar un índice o wheel diferente).

## VS Code
He configurado el intérprete del workspace para que apunte al Python del venv. Si VS Code no lo detecta automáticamente, selecciona manualmente:

Paleta (Ctrl+Shift+P) → "Python: Select Interpreter" → elegir `C:\Users\Huananzhi-X79\VisualAI\Proyecto2\venv\Scripts\python.exe`

## Comprobación rápida
Con el venv activado, prueba:

```powershell
python -c "import numpy, matplotlib, cv2, torch; print(numpy.__version__, matplotlib.__version__, cv2.__version__, torch.__version__)"
type .\requirements.txt
```

## Preguntas / siguientes pasos
- ¿Quieres que añada un script de ejemplo (`example.py`) que cargue una imagen con OpenCV y muestre un plot básico?
- ¿Generamos un `README` más detallado con instrucciones de desarrollo (pre-commit, formato, tests)?

---
Archivo generado automáticamente por la configuración del workspace.

