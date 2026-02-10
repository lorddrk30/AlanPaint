# 🚀 AlanPaint

<div align="center">

**Lightweight Image Editor for Low-RAM Computers**

*Fast, simple, and memory-efficient*

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/PySide6-6.6+-green.svg)](https://doc.qt.io/qtforpython/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## ✨ ¿Qué es AlanPaint?

AlanPaint es un editor de imágenes ligero diseñado específicamente para computadoras con **poca memoria RAM**. Ideal para abrir y editar imágenes de forma rápida sin consumir muchos recursos.

> **Creado por Erik Ala Álvarez** con ❤️ usando VibeCode

---

## 🎯 Características Principales

### Herramientas de Dibujo
| Herramienta | Atajo | Descripción |
|-------------|-------|-------------|
| 🖌️ Pincel | `B` | Dibujo libre a mano alzada |
| 🧹 Borrador | `E` | Borra partes de la imagen (blanco) |
| 📏 Línea | `L` | Dibuja líneas rectas |
| ⬜ Rectángulo | `R` | Dibuja rectángulos |
| ⭕ Elipse | `O` | Dibuja elipses y círculos |
| 🔤 Texto | `T` | Inserta texto en la imagen |

### Filtros Integrados
- ⚫ **Escala de grises** - Convierte a blanco y negro
- 🔄 **Invertir** - Invierte los colores
- ☀️ **Brillo +/-** - Ajusta el brillo
- ◧ **Contraste +/-** - Ajusta el contraste
- ◌ **Blur** - Desenfoque suave
- ◆ **Sharpen** - Nitidez mejorada
- ▣ **Posterize** - Reduce colores
- ◈ **Sepia** - Tono vintage

### Formatos Soportados
| Formato | Extensiones | Soporte |
|---------|-------------|---------|
| PNG | `.png` | ✅ Completo |
| JPEG | `.jpg`, `.jpeg` | ✅ Completo |
| WebP | `.webp` | ✅ Completo |
| BMP | `.bmp` | ✅ Completo |
| GIF | `.gif` | ✅ Estático |
| TIFF | `.tif`, `.tiff` | ✅ Completo |

---

## 💾 Optimización de Memoria

AlanPaint está diseñado para usar **mínima RAM**:

```
┌─────────────────────────────────────────────────────┐
│                    ARQUITECTURA                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │   MASTER     │    │      PREVIEW CACHE       │  │
│  │   IMAGE      │───▶│   (escalado pantalla)   │  │
│  │  Full-Res    │    │   Actualizado solo en    │  │
│  │  1 copia     │    │   zoom/commit            │  │
│  └──────────────┘    └──────────────────────────┘  │
│         │                      ▲                   │
│         │                      │                   │
│         ▼                      │                   │
│  ┌──────────────┐    ┌──────────────────────────┐  │
│  │   OVERLAY    │    │     CANVAS UI            │  │
│  │  Temporal    │◀───│     (previsualización)   │  │
│  │  Durante drag│    │                         │  │
│  └──────────────┘    └──────────────────────────┘  │
│                                                     │
│  Undo/Redo: Solo regiones modificadas (máx 20)      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Técnicas de Ahorro de RAM
- ✅ **Una sola imagen master** en memoria
- ✅ **Preview cache** escalado solo cuando cambia zoom
- ✅ **Overlay temporal** durante arrastre del mouse
- ✅ **Undo por comandos** - guarda solo regiones, no snapshots
- ✅ **Sin PhotoImage/QPixmap duplicados**

---

## ⌨️ Atajos de Teclado

### Generales
| Atajo | Acción |
|-------|--------|
| `Ctrl + O` | Abrir imagen |
| `Ctrl + S` | Guardar |
| `Ctrl + Shift + S` | Guardar como |
| `Ctrl + Z` | Deshacer |
| `Ctrl + Y` | Rehacer |
| `Ctrl + +` | Zoom + |
| `Ctrl + -` | Zoom - |
| `Espacio` | Mantener para pan |

### Herramientas
| Atajo | Herramienta |
|-------|-------------|
| `B` | Pincel |
| `E` | Borrador |
| `L` | Línea |
| `R` | Rectángulo |
| `O` | Elipse |
| `T` | Texto |

### Mouse
| Acción | Función |
|--------|---------|
| Click + Arrastrar | Dibujar |
| Click Medio + Arrastrar | Panorámica |
| Rueda | Scroll |
| `Ctrl` + Rueda | Zoom |

---

## 📦 Instalación

### Windows y Linux

```bash
# 1. Crear entorno virtual
python -m venv venv

# 2. Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar
python main.py
```

---

## 📁 Estructura del Proyecto

```
AlanPaint/
├── main.py              # Punto de entrada
├── requirements.txt     # Dependencias
├── README.md           # Este archivo
├── create_demo.py     # Generador de imagen demo
└── alanpaint/         # Paquete principal
    ├── __init__.py
    ├── canvas.py      # Widget canvas con overlay
    ├── commands.py    # Comandos undo/redo
    ├── filters.py     # Filtros de imagen
    ├── io.py          # Carga/guardado de imágenes
    ├── tools.py       # Herramientas de dibujo
    └── ui.py          # Ventana principal
```

---

## 🖼️ Imagen Demo

Genera una imagen de prueba:

```bash
python create_demo.py
```

Esto crea `demo.png` con formas y colores de prueba.

---

## 🏗️ Compilar como EXE

¿Quieres distribuir AlanPaint como ejecutable (.exe)?

Consulta la guía completa: [BUILD_EXE.md](BUILD_EXE.md)

```bash
# Compilación básica
pip install pyinstaller
pyinstaller --onefile --windowed --name AlanPaint main.py
```

---

## 🤝 Licencia

MIT License - Libre para usar, modificar y distribuir.

---

## 💚 Acerca de

**AlanPaint** fue creado por **Erik Ala Álvarez** usando **VibeCode**, como un proyecto open source diseñado para computadoras con memoria limitada que necesitan abrir y editar imágenes de forma rápida y eficiente.

---

<div align="center">

**¡Disfruta editando imágenes sin preocuparte por la memoria! 🖼️**

</div>
