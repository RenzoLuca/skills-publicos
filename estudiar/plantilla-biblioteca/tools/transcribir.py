"""Transcribe un video o audio local en la GPU (faster-whisper, large-v3-turbo).

Uso: python transcribir.py <video|audio> <salida.txt> [--idioma es|en] [--cpu]

Lee el archivo directo (PyAV), sin crear audio intermedio: no ocupa espacio extra.
Salida: una línea por segmento "[mm:ss] texto" (o [h:mm:ss] si pasa de 1 h).
"""
import argparse
import glob
import os
import site
import sys
import time

# Las DLL de CUDA vienen en los paquetes pip nvidia-cublas-cu12 / nvidia-cudnn-cu12.
for base in site.getsitepackages() + [site.getusersitepackages()]:
    for bin_dir in glob.glob(os.path.join(base, "nvidia", "*", "bin")):
        os.add_dll_directory(bin_dir)
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]

from faster_whisper import BatchedInferencePipeline, WhisperModel  # noqa: E402

MODELO = "large-v3-turbo"


def marca(seg):
    seg = int(seg)
    h, m, s = seg // 3600, seg % 3600 // 60, seg % 60
    return f"[{h}:{m:02d}:{s:02d}]" if h else f"[{m:02d}:{s:02d}]"


def cargar(cpu):
    if not cpu:
        try:
            return WhisperModel(MODELO, device="cuda", compute_type="float16"), "GPU"
        except Exception as e:  # sin CUDA usable: seguimos en CPU, pero avisando
            print(f"AVISO: GPU no disponible ({e}). Sigo en CPU: será lento.", file=sys.stderr)
    return WhisperModel(MODELO, device="cpu", compute_type="int8"), "CPU"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("salida")
    p.add_argument("--idioma", default=None, help="es / en; si se omite, lo detecta")
    p.add_argument("--cpu", action="store_true")
    a = p.parse_args()

    t0 = time.time()
    modelo, donde = cargar(a.cpu)
    # Por lotes en GPU (~3x más rápido); en CPU el modo normal rinde igual y gasta menos RAM.
    if donde == "GPU":
        segmentos, info = BatchedInferencePipeline(modelo).transcribe(
            a.entrada, language=a.idioma, batch_size=8, beam_size=5,
        )
    else:
        segmentos, info = modelo.transcribe(
            a.entrada, language=a.idioma, vad_filter=True, beam_size=5,
            condition_on_previous_text=False,
        )
    os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
    with open(a.salida, "w", encoding="utf-8") as f:
        for s in segmentos:
            f.write(f"{marca(s.start)} {s.text.strip()}\n")
    dur = time.time() - t0
    print(f"OK {donde} | idioma {info.language} | audio {info.duration/60:.1f} min | "
          f"tardó {dur/60:.1f} min | {a.salida}")


if __name__ == "__main__":
    main()
