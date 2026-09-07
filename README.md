# AlanPaint

Editor de imágenes de escritorio creado por **Erik Ala Álvarez** con VibeCode. Desarrollado con Python, PySide6 y Pillow.

## Versión 2.0

- Interfaz moderna en español, herramientas con iconos y paleta de colores.
- Pincel, borrador blanco, líneas, rectángulos, elipses y texto multilínea.
- Recorte libre o con proporciones 1:1, 4:3, 16:9 y 9:16, con cuadrícula y vista sombreada.
- Filtros con miniaturas y vista previa: blanco y negro, sepia, invertir, desenfoque, nitidez, póster y auto contraste.
- Brillo, contraste y saturación ajustables mediante deslizadores.
- Girar, voltear y cambiar tamaño conservando la proporción.
- Cuentagotas, colores hexadecimales y tamaño de pincel configurable.
- Deshacer y rehacer todas las ediciones, incluidos recortes y transformaciones.
- Zoom del 1% al 1600%, ajuste a ventana y desplazamiento del lienzo.
- Abrir imágenes al arrastrarlas sobre la ventana. Conserva transparencia y corrige orientación EXIF.

## Empezar

En Windows, abre **dist/AlanPaint.exe**. Para ejecutar desde el código:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe main.py
```

Requiere Python 3.10 o superior y una versión compatible de PySide6. También puedes abrir una imagen desde la línea de comandos:

```powershell
.\venv\Scripts\python.exe main.py "C:\Fotos\imagen.png"
```

## Editar una imagen

1. Pulsa **Abrir imagen** o arrastra un archivo a la ventana.
2. Selecciona una herramienta a la izquierda. En **Herramienta**, ajusta pincel, relleno y tamaño del texto.
3. Para recortar, selecciona **Recortar**, elige una proporción y arrastra sobre la imagen. **Enter** aplica; **Esc** cancela. Puedes volver a arrastrar para cambiar la selección.
4. En **Filtros y ajustes**, elige un filtro y mueve los deslizadores. **Aplicar cambios** conserva el resultado; **Restablecer** descarta la vista previa. Elegir otra herramienta también descarta la vista previa pendiente.
5. Pulsa **Guardar**. Guardar aplica los filtros que se están previsualizando. El editor pregunta por los cambios pendientes antes de cerrar, abrir otra imagen o crear un lienzo nuevo.

## Atajos

| Acción | Atajo |
|---|---|
| Nuevo / Abrir / Guardar | Ctrl+N / Ctrl+O / Ctrl+S |
| Guardar como | Ctrl+Shift+S |
| Deshacer / Rehacer | Ctrl+Z / Ctrl+Y o Ctrl+Shift+Z |
| Pincel / Borrador | B / E |
| Línea / Rectángulo / Elipse | L / R / O |
| Texto / Recortar | T / C |
| Cuentagotas / Mover | I / H |
| Aplicar / Cancelar recorte | Enter / Esc |
| Acercar / Alejar | Ctrl+rueda o Ctrl++ / Ctrl+- |
| Ajustar a ventana / Tamaño real | Ctrl+0 / Ctrl+1 |
| Mover temporalmente | Espacio + arrastrar o botón central |

## Formatos y memoria

Abre y guarda PNG, JPEG, WebP, BMP, GIF estático y TIFF. PNG, WebP y TIFF conservan transparencia; JPEG y BMP usan fondo blanco al exportar una imagen transparente. El borrador pinta de blanco.

El historial guarda regiones para los dibujos y las imágenes necesarias para filtros y transformaciones. Conserva hasta 20 operaciones con un presupuesto aproximado de 128 MiB; siempre retiene la última operación aunque exceda el presupuesto. La vista previa de filtros se limita a 1200 × 900 píxeles; al aplicar se usa la resolución original. Las imágenes grandes requieren más memoria.

## Pruebas y ejecutable

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
.\venv\Scripts\python.exe -m pip install pyinstaller
.\venv\Scripts\python.exe -m PyInstaller --noconfirm AlanPaint.spec
```

Las pruebas usan QtTest en modo offscreen y verifican trazos, recortes, historial, zoom, filtros, transparencia y guardado. PyInstaller genera `dist/AlanPaint.exe`.

Consulta [CHANGELOG.md](CHANGELOG.md) para ver los cambios de la versión 2.0.
