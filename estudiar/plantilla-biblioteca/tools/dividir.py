"""Divide una transcripción "[mm:ss] texto" en tramos de ~15-20 min, cortando en la pausa más larga.

Uso: python dividir.py <transcripcion.txt> <carpeta_salida>

- Videos de 30 min o menos: un solo tramo.
- Un último tramo de menos de 7 min se junta con el anterior.
Escribe tramo-01.txt, tramo-02.txt… e imprime el rango de cada uno.
"""
import os
import re
import sys

MIN_T, MAX_T, SOLO, RESTO = 15 * 60, 20 * 60, 30 * 60, 7 * 60


def seg(linea):
    m = re.match(r"\[(?:(\d+):)?(\d+):(\d\d)\]", linea)
    if not m:
        return None
    h, mm, s = m.groups()
    return int(h or 0) * 3600 + int(mm) * 60 + int(s)


def fmt(t):
    h, m, s = t // 3600, t % 3600 // 60, t % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def main():
    origen, destino = sys.argv[1], sys.argv[2]
    with open(origen, encoding="utf-8") as f:
        filas = [(seg(l), l) for l in f if seg(l) is not None]
    if not filas:
        sys.exit("No hay líneas con [mm:ss]")
    total = filas[-1][0]

    cortes = [0]  # índices de fila donde empieza cada tramo
    if total > SOLO:
        while True:
            ini = filas[cortes[-1]][0]
            if total - ini <= MAX_T + RESTO:
                break
            ventana = [j for j in range(cortes[-1] + 1, len(filas))
                       if MIN_T <= filas[j][0] - ini <= MAX_T]
            if not ventana:
                break
            # la mayor pausa entre dos líneas dentro de la ventana
            j = max(ventana, key=lambda k: filas[k][0] - filas[k - 1][0])
            cortes.append(j)
    cortes.append(len(filas))

    os.makedirs(destino, exist_ok=True)
    for n in range(len(cortes) - 1):
        bloque = filas[cortes[n]:cortes[n + 1]]
        nombre = os.path.join(destino, f"tramo-{n + 1:02d}.txt")
        with open(nombre, "w", encoding="utf-8") as f:
            f.writelines(l for _, l in bloque)
        print(f"tramo {n + 1:02d}: {fmt(bloque[0][0])} - {fmt(bloque[-1][0])} -> {nombre}")


if __name__ == "__main__":
    main()
