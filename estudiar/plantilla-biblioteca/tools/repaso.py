"""Repaso espaciado de la biblioteca con FSRS (agenda cada tarjeta para cuando la recordarías al 90 %).

Uso:
  python repaso.py hoy [--max 20]                      tarjetas que tocan hoy, mezcladas entre fuentes (JSON)
  python repaso.py resultado <id> mal|dificil|bien|facil   registra la respuesta y agenda la próxima
  python repaso.py agregar <nuevas.json>               añade [{unidad, pregunta, respuesta}, ...] (1.er repaso: mañana)
  python repaso.py resumen                             total, tocan hoy, por unidad

Por qué FSRS y no intervalos fijos: rinde igual con ~20-30 % menos repasos (cerebro Ciencia del
Aprendizaje, investigacion/m4-transferencia.md). Mezclar fuentes en el repaso = intercalado (m1).
"""
import datetime as dt
import json
import os
import random
import sys

from fsrs import Card, Rating, Scheduler

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "repaso", "tarjetas.json")
# Sin pasos de aprendizaje de minutos: la tarjeta nace después del quiz aprobado en la sesión.
PLAN = Scheduler(desired_retention=0.9, learning_steps=(), relearning_steps=())
NOTAS = {"mal": Rating.Again, "dificil": Rating.Hard, "bien": Rating.Good, "facil": Rating.Easy}
NUEVAS_POR_DIA = 20  # más de 15-25 nuevas al día acumula una carga de repasos inmanejable (m4)
HOY = dt.date.today()


def leer():
    with open(RUTA, encoding="utf-8-sig") as f:
        return json.load(f)


def escribir(t):
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(t, f, ensure_ascii=False, indent=1)


def toca(c):
    return dt.date.fromisoformat(c["proxima"]) <= HOY


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "hoy"
    t = leer()
    if cmd == "hoy":
        tope = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 20
        due = sorted((c for c in t if toca(c)), key=lambda c: c["proxima"])[:tope]
        random.shuffle(due)
        print(json.dumps([{k: c[k] for k in ("id", "unidad", "pregunta", "respuesta")} for c in due],
                         ensure_ascii=False, indent=1))
    elif cmd == "resultado":
        cid, nota = int(sys.argv[2]), sys.argv[3]
        c = next((c for c in t if c["id"] == cid), None)
        if c is None or nota not in NOTAS:
            sys.exit(f"Uso: resultado <id> {'|'.join(NOTAS)}")
        card, _ = PLAN.review_card(Card.from_dict(c["fsrs"]) if c.get("fsrs") else Card(), NOTAS[nota])
        c["fsrs"] = card.to_dict()
        c["proxima"] = card.due.astimezone().date().isoformat()
        c.setdefault("historial", []).append(f"{HOY.isoformat()}:{nota}")
        escribir(t)
        print(f"#{cid} {nota} -> próxima {c['proxima']}")
    elif cmd == "agregar":
        with open(sys.argv[2], encoding="utf-8-sig") as f:
            nuevas = json.load(f)
        hoy_ya = sum(1 for c in t if c.get("creada") == HOY.isoformat())
        if hoy_ya + len(nuevas) > NUEVAS_POR_DIA:
            print(f"AVISO: hoy serían {hoy_ya + len(nuevas)} tarjetas nuevas (tope {NUEVAS_POR_DIA}).")
        sig = max((c["id"] for c in t), default=0) + 1
        for i, n in enumerate(nuevas):
            t.append({"id": sig + i, "unidad": n["unidad"], "pregunta": n["pregunta"],
                      "respuesta": n["respuesta"], "creada": HOY.isoformat(),
                      "proxima": (HOY + dt.timedelta(days=1)).isoformat()})
        escribir(t)
        print(f"+{len(nuevas)} tarjetas (total {len(t)})")
    elif cmd == "resumen":
        por = {}
        for c in t:
            por.setdefault(c["unidad"], [0, 0])
            por[c["unidad"]][0] += 1
            por[c["unidad"]][1] += toca(c)
        print(f"Total {len(t)} | tocan hoy {sum(toca(c) for c in t)}")
        for u, (n, d) in sorted(por.items()):
            print(f"  {u}: {n} tarjetas, {d} hoy")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
