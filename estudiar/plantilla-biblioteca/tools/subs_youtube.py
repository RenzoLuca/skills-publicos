"""Transcripción de un video de YouTube SIN bajar el video.

Uso: python subs_youtube.py <url> <salida.txt>

1. Pide solo la info del video (-J) y elige subtítulos: manuales (del autor) en el idioma original,
   es o en; si no hay, los automáticos del idioma original (nunca una traducción automática).
2. Baja solo ese .vtt (unos KB) y lo pasa a "[mm:ss] texto".
3. Si no hay subtítulos: baja solo el audio, lo transcribe con transcribir.py y borra el audio.
Imprime en la 1.ª línea de salida: TITULO | CANAL | DURACION | FUENTE (manual/auto/whisper).
"""
import json
import os
import shutil
import re
import subprocess
import sys
import tempfile

YTDLP = shutil.which("yt-dlp") or "yt-dlp"  # instalar: pip install yt-dlp
AQUI = os.path.dirname(os.path.abspath(__file__))


def yt(*args):
    r = subprocess.run([YTDLP, "--no-warnings", *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"yt-dlp falló: {r.stderr.strip()[-500:]}")
    return r.stdout


def elegir(info):
    orig = (info.get("language") or "").split("-")[0]
    preferidos = [x for x in (orig, "es", "en") if x]
    manual = info.get("subtitles") or {}
    for lang in preferidos:
        for k in manual:
            if k == lang or k.startswith(lang + "-"):
                return k, "manual", False
    auto = info.get("automatic_captions") or {}
    for k in auto:  # la pista "-orig" es la del idioma hablado, no una traducción
        if k.endswith("-orig"):
            return k, "auto", True
    if orig and orig in auto:
        return orig, "auto", True
    return None, None, None


def vtt_a_txt(vtt):
    # los automáticos son "rodantes": cada línea aparece 2-3 veces en cues seguidos
    lineas, recientes, t = [], [], None
    for raw in vtt.splitlines():
        m = re.match(r"(\d+):(\d\d):(\d\d)\.\d+ -->", raw) or re.match(r"(\d\d):(\d\d)\.\d+ -->", raw)
        if m:
            g = [int(x) for x in m.groups()]
            t = g[0] * 3600 + g[1] * 60 + g[2] if len(g) == 3 else g[0] * 60 + g[1]
            continue
        txt = re.sub(r"<[^>]+>", "", raw).strip()
        if not txt or t is None or txt in recientes or raw.startswith(("WEBVTT", "Kind:", "Language:")):
            continue
        recientes = (recientes + [txt])[-3:]
        h, mm, s = t // 3600, t % 3600 // 60, t % 60
        lineas.append((f"[{h}:{mm:02d}:{s:02d}]" if h else f"[{mm:02d}:{s:02d}]") + " " + txt)
    return "\n".join(lineas) + "\n"


def main():
    url, salida = sys.argv[1], sys.argv[2]
    info = json.loads(yt("-J", "--skip-download", url))
    cab = f"{info.get('title')} | {info.get('channel')} | {int(info.get('duration') or 0)//60} min"
    lang, tipo, es_auto = elegir(info)
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        if lang:
            yt("--skip-download", "--write-auto-subs" if es_auto else "--write-subs",
               "--sub-langs", lang, "--sub-format", "vtt", "-o", os.path.join(tmp, "s"), url)
            vtts = [f for f in os.listdir(tmp) if f.endswith(".vtt")]
            if vtts:
                with open(os.path.join(tmp, vtts[0]), encoding="utf-8") as f:
                    texto = vtt_a_txt(f.read())
                with open(salida, "w", encoding="utf-8") as f:
                    f.write(texto)
                print(f"{cab} | {tipo} ({lang}) | {salida}")
                return
        # sin subtítulos: solo audio → whisper → se borra con la carpeta temporal
        yt("-f", "bestaudio", "-o", os.path.join(tmp, "audio.%(ext)s"), url)
        audio = os.path.join(tmp, os.listdir(tmp)[0])
        r = subprocess.run([sys.executable, os.path.join(AQUI, "transcribir.py"), audio, salida])
        if r.returncode != 0:
            sys.exit("transcribir.py falló")
        print(f"{cab} | whisper | {salida}")


if __name__ == "__main__":
    main()
