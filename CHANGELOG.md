# AlanPaint 2.0

- Interfaz en español, iconos vectoriales, paleta de colores y panel de propiedades.
- Recorte con vista sombreada, cuadrícula y proporciones libre, 1:1, 4:3, 16:9 y 9:16. Arrastra para seleccionar; Enter aplica y Esc cancela.
- Filtros con miniaturas y vista previa: blanco y negro, sepia, invertir, suave, nítido, póster y auto contraste.
- Brillo, contraste y saturación ajustables. «Aplicar cambios» confirma; «Restablecer» descarta la vista previa. Guardar también aplica la vista previa pendiente.
- Girar 90°, voltear horizontalmente y cambiar tamaño conservando proporción.
- Pincel y figuras con posiciones correctas, trazos largos y parches transparentes que conservan el fondo.
- Texto multilínea, cuentagotas, tamaño de pincel y colores hexadecimales.
- Deshacer y rehacer dibujo, texto, filtros, recorte y transformaciones, incluso al mezclarlos.
- Zoom real del 1% al 1600%, ajuste a ventana y desplazamiento con Espacio + arrastrar.
- Apertura al arrastrar archivos, transparencia PNG/WebP/TIFF y orientación EXIF.
- Aviso de cambios pendientes al abrir, crear o cerrar. Corrección de extensiones duplicadas al guardar.

## Desarrollo

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe main.py
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas simulan eventos de ratón y teclado mediante QtTest en modo offscreen y comparan píxeles, dimensiones, transparencia y archivos exportados. El historial conserva hasta 20 operaciones con un presupuesto aproximado de 128 MiB; siempre conserva la última operación aunque exceda ese presupuesto. La vista previa de filtros usa como máximo 1200 × 900 píxeles; al aplicar se procesa la resolución original.

## Ejecutable de Windows

```powershell
.\venv\Scripts\python.exe -m pip install pyinstaller
.\venv\Scripts\python.exe -m PyInstaller --noconfirm AlanPaint.spec
```

El resultado está en `dist/AlanPaint.exe`. También acepta una ruta de imagen como argumento. El borrador pinta de blanco y GIF se edita como imagen estática. Seleccionar otra herramienta descarta los filtros aún sin aplicar.
