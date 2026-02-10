# 🏗️ Compilar AlanPaint como EXE (Ligero)

Esta guía explica cómo compilar AlanPaint en un ejecutable lo más pequeño posible.

---

## ⚠️ Nota sobre el Tamaño

AlanPaint usa **PySide6 (Qt)** y **Pillow**, que son bibliotecas grandes. El tamaño mínimo típico es:

| Método | Tamaño Aproximado |
|--------|-------------------|
| PyInstaller básico | 50-80 MB |
| Con virtualenv limpio | 40-60 MB |
| Con exclusión de módulos | 30-50 MB |
| Con UPX + exclusión | 25-40 MB |

**Para lograr ~2MB**, sería necesario reescribir la aplicación usando bibliotecas más pequeñas como `tkinter` (incluido en Python) en lugar de Qt.

---

## 🚀 Método Recomendado (Más Pequeño)

### Paso 1: Crear entorno virtual LIMPIO

```bash
# Crear venv nuevo
python -m venv venv_build

# Activar
venv_build\Scripts\activate

# SOLO instalar lo mínimo necesario
pip install PySide6 Pillow pyinstaller
```

### Paso 2: Compilar con exclusiones

```bash
# Excluir módulos no usados de Qt y Pillow
pyinstaller --onefile --windowed --name AlanPaint \
    --exclude-module=PySide6.QtSvg \
    --exclude-module=PySide6.QtSql \
    --exclude-module=PySide6.QtNetwork \
    --exclude-module=PySide6.QtXml \
    --exclude-module=PySide6.QtOpenGL \
    --exclude-module=PySide6.QtWebEngine \
    --exclude-module=PIL.PdfParser \
    --exclude-module=PIL.ImageSequence \
    --exclude-module=PIL.GimpPalette \
    --exclude-module=PIL.GimpGradient \
    --exclude-module=PIL.Jpeg2KImagePlugin \
    main.py
```

---

## 📦 Método con Virtualenv Isolado (Más Control)

### Paso 1: Crear entorno limpio

```bash
# Crear venv en la carpeta del proyecto
python -m venv alanpaint_env

# Activar
alanpaint_env\Scripts\activate

# Instalar solo lo necesario
pip install --no-cache-dir PySide6 Pillow pyinstaller
```

### Paso 2: Generar spec personalizado

Crea `alanpaint.spec`:

```python
# alanpaint.spec - Optimizado para tamaño mínimo
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Qt módulos no usados
        'PySide6.QtSvg',
        'PySide6.QtSql', 
        'PySide6.QtNetwork',
        'PySide6.QtXml',
        'PySide6.QtOpenGL',
        'PySide6.QtWebEngine',
        'PySide6.QtPrintSupport',
        'PySide6.QtHelp',
        'PySide6.QtMultimedia',
        'PySide6.QtBluetooth',
        'PySide6.QtLocation',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtWebChannel',
        'PySide6.QtWebKit',
        'PySide6.QtWebKitWidgets',
        'PySide6.QtX11Extras',
        'PySide6.QtXmlPatterns',
        'PySide6.QtXmlPatterns',
        # PIL módulos no usados
        'PIL.PdfParser',
        'PIL.ImageSequence',
        'PIL.GimpPalette',
        'PIL.GimpGradient',
        'PIL.Jpeg2KImagePlugin',
        'PIL.FpxImagePlugin',
        'PIL.MicImagePlugin',
        'PIL.Hdf5Plugin',
        'PIL.FliImagePlugin',
        'PIL.FpxImagePlugin',
        'PIL.MpegImagePlugin',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AlanPaint',
    debug=False,
    bootloader=False,
    strip=True,  # ⚠️ Quitar símbolos
    upx=True,    # ⚠️ Comprimir con UPX
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=True,
    upx=True,
    upx_exclude=[],
    name='AlanPaint',
)
```

### Paso 3: Compilar

```bash
pyinstaller alanpaint.spec
```

---

## 📉 Técnicas Avanzadas de Reducción

### 1. Instalar UPX (Compresión)

```bash
# Descargar UPX desde: https://upx.github.io/
# Descomprimir y agregar al PATH, o usar:
# --upx-dir=C:\ruta\a\upx
```

### 2. Usar PyOxidizer (Más pequeño que PyInstaller)

```bash
pip install pyoxidizer
pyoxidize init
# Editar pyoxidizer.toml para excluir módulos
pyoxidize build
```

### 3. Nuitka (Compilador Python → C)

```bash
pip install nuitka
nuitka --onefile --windowed --include-module=PIL --include-module=PySide6 main.py
```

---

## 🔧 Solución de Problemas

### Error: "Missing modules"
```bash
# Añadir módulos faltantes
--hidden-import=PIL --hidden-import=PySide6.QtCore ...
```

### Error: Qt platform plugin
```bash
# Incluir plugins
--add-data="venv/Lib/site-packages/PySide6/plugins;PySide6/plugins"
```

### El exe no ejecuta
```bash
# Verificar que todo esté en el venv limpio
deactivate
venv_build\Scripts\activate
pip list
```

---

## 📊 Comparación de Herramientas

| Herramienta | Tamaño | Velocidad | Dificultad |
|-------------|--------|-----------|------------|
| PyInstaller | 40-80 MB | Rápido | Fácil |
| PyOxidizer | 30-50 MB | Medio | Media |
| Nuitka | 25-45 MB | Lento | Difícil |
| C/GTK/Tkinter | 2-5 MB | Rápido | Muy difícil |

---

## 💡 Alternativa para 2MB

Para lograr un exe de ~2MB, sería necesario reescribir usando:

- **tkinter** (incluido en Python) - 5-10 MB
- **PySimpleGUI** - 10-15 MB

Esto requeriría cambios significativos en el código.

---

## ✅ Resultado Final

```bash
# Comando óptimo
pyinstaller --onefile --windowed --name AlanPaint \
    --exclude-module=PySide6.QtSvg \
    --exclude-module=PySide6.QtNetwork \
    --exclude-module=PIL.PdfParser \
    main.py

# Resultado esperado: ~35-50 MB
```

El exe estará en: `dist/AlanPaint.exe`
