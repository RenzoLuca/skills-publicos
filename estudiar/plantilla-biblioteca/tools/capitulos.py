"""Corta un libro PDF o EPUB en un .txt por capítulo.

Uso: python capitulos.py <libro.pdf|libro.epub> <carpeta_salida> [--nivel 1]

PDF: usa el índice (marcadores) del archivo al nivel indicado; cada página va marcada "[p. N]" para
citar. Sin índice → bloques de 20 páginas (avisa). PDF escaneado (sin texto) → avisa: necesita OCR.
EPUB: un archivo por capítulo del índice de lectura. EPUB con DRM → avisa (no se puede leer).
Imprime: NN | título | páginas | palabras.
"""
import argparse
import os
import re
import sys
import unicodedata


def slug(t, n=40):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:n].strip("-") or "capitulo"


def guardar(dest, n, titulo, texto, extra=""):
    nombre = os.path.join(dest, f"{n:02d}-{slug(titulo)}.txt")
    with open(nombre, "w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n\n{texto}")
    print(f"{n:02d} | {titulo} | {extra} | {len(texto.split())} palabras")


def pdf(ruta, dest, nivel):
    import pymupdf
    doc = pymupdf.open(ruta)
    paginas = [doc[i].get_text() for i in range(len(doc))]
    if sum(len(p.strip()) for p in paginas) < 100 * max(1, len(doc) // 10):
        sys.exit("AVISO: el PDF casi no tiene texto (escaneado). Necesita OCR antes de estudiarlo.")
    toc = [(t, p) for lv, t, p in doc.get_toc() if lv <= nivel and p > 0]
    if not toc:
        print("AVISO: el PDF no tiene índice; corto en bloques de 20 páginas.")
        toc = [(f"Páginas {i + 1}-{min(i + 20, len(doc))}", i + 1) for i in range(0, len(doc), 20)]
    for n, (titulo, ini) in enumerate(toc, 1):
        fin = toc[n][1] - 1 if n < len(toc) else len(doc)
        fin = max(fin, ini)
        texto = "".join(f"\n[p. {i}]\n{paginas[i - 1]}" for i in range(ini, fin + 1))
        guardar(dest, n, titulo.strip(), texto, f"p. {ini}-{fin}")


def epub(ruta, dest):
    import zipfile
    with zipfile.ZipFile(ruta) as z:
        if "META-INF/encryption.xml" in z.namelist():
            sys.exit("AVISO: el EPUB tiene DRM. Hace falta una copia sin DRM.")
    import ebooklib
    from ebooklib import epub as ep
    libro = ep.read_epub(ruta, {"ignore_ncx": False})
    n = 0
    for idref, _ in libro.spine:
        item = libro.get_item_with_id(idref)
        if not item or item.get_type() != ebooklib.ITEM_DOCUMENT:
            continue
        html = item.get_content().decode("utf-8", "ignore")
        m = re.search(r"<h[1-3][^>]*>(.*?)</h[1-3]>", html, re.S | re.I)
        texto = re.sub(r"<(br|/p|/h\d|/div|/li)[^>]*>", "\n", html, flags=re.I)
        texto = re.sub(r"<[^>]+>", "", texto)
        texto = re.sub(r"\n\s*\n+", "\n\n", texto).strip()
        if len(texto.split()) < 150:  # portadas, créditos, separadores
            continue
        n += 1
        titulo = re.sub(r"<[^>]+>|\s+", " ", m.group(1)).strip() if m else f"Sección {n}"
        guardar(dest, n, titulo, texto, item.get_name())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("libro")
    p.add_argument("destino")
    p.add_argument("--nivel", type=int, default=1, help="nivel del índice del PDF (1 = capítulos)")
    a = p.parse_args()
    os.makedirs(a.destino, exist_ok=True)
    if a.libro.lower().endswith(".pdf"):
        pdf(a.libro, a.destino, a.nivel)
    elif a.libro.lower().endswith(".epub"):
        epub(a.libro, a.destino)
    else:
        sys.exit("Formato no soportado (solo PDF o EPUB). Kindle (.azw/.kfx) con DRM no se puede.")


if __name__ == "__main__":
    main()
