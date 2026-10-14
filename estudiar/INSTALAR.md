# Instalar /estudiar

Un skill de [Claude Code](https://claude.com/claude-code) que **te enseña** libros y videos en una
sesión interactiva, en vez de darte resúmenes. Hace preguntas antes, te enseña idea por idea, te pide
explicarlo con tus palabras y te toma un quiz. Además, programa los repasos para que no olvides
(repaso espaciado).

## Requisitos
- **Claude Code** (plan Pro o superior).
- **Windows** con **Python 3.10+**. Al instalarlo, marca "Add python.exe to PATH".
- Opcional: una tarjeta **NVIDIA**, para transcribir videos más rápido. Sin ella también funciona,
  solo más lento.

## Pasos
1. Descarga esta carpeta `estudiar` completa. Si no usas git, pásale el link de esta carpeta a
   https://download-directory.github.io para bajarla en ZIP.
2. Cópiala en tu carpeta de skills: `C:\Users\<tu usuario>\.claude\skills\estudiar\`.
   Tiene que quedar `...\skills\estudiar\SKILL.md`.
3. Instala las librerías en PowerShell:
   ```
   python -m pip install faster-whisper "av<17" yt-dlp fsrs pymupdf ebooklib
   ```
   Solo si tienes NVIDIA, agrega:
   ```
   python -m pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
   ```
4. Abre Claude Code y escribe `/estudiar` seguido de un link de YouTube o la ruta de un PDF.
   - La primera vez crea tu biblioteca en `C:\Users\<tu usuario>\Biblioteca\`.
   - Ahí quedan tus fichas, tarjetas y avance. **Es tuya**: no se sube a ningún lado.

## Comandos
| Escribe | Qué hace |
|---|---|
| `/estudiar <link o ruta>` | Prepara la fuente y empieza la primera sesión |
| `/estudiar` o "sigamos" | Retoma donde te quedaste |
| `/estudiar repaso` | Repaso del día (tarjetas que te tocan) |
| `/estudiar estado` | Qué estás estudiando y cómo vas |

## Infografías (opcional)
Al aprobar una unidad, puede generar una infografía con Nano Banana (Google Flow). Para eso necesitas
instalar `gflow-cli` e iniciar sesión en Google Flow. Si no lo tienes, el skill se la salta y te queda
la ficha escrita.
