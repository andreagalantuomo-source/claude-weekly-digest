#!/usr/bin/env python3
"""
Novita' in mattpocock/skills dall'ultima esecuzione.

Il blog di Matt Pocock (aihero.dev) e' bloccato dalla policy di rete
dell'ambiente, ma il CHANGELOG del suo repo di skill e' leggibile via
raw.githubusercontent.com. I suoi post "Skills Changelog: ..." raccontano
esattamente queste release, quindi questa e' una copertura parziale ma reale
della stessa sostanza.

Il changelog e' generato da changesets: niente date, ma versioni ordinate dalla
piu' recente. Il confronto e' quindi per versione, non per data.

  python3 scripts/track_mp_skills.py            # cosa e' uscito dall'ultima volta
  python3 scripts/track_mp_skills.py --record   # segna la versione corrente come vista
"""

import argparse
import os
import re
import urllib.request

URL = "https://raw.githubusercontent.com/mattpocock/skills/main/CHANGELOG.md"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "state", "mattpocock-skills-version.txt")


def fetch():
    with urllib.request.urlopen(URL, timeout=60) as r:
        return r.read().decode("utf-8")


def versions(text):
    """[(versione, corpo)] dalla piu' recente."""
    marks = [(m.group(1), m.start()) for m in re.finditer(r"^## (\d+\.\d+\.\d+)$", text, re.M)]
    out = []
    for i, (v, start) in enumerate(marks):
        end = marks[i + 1][1] if i + 1 < len(marks) else len(text)
        out.append((v, text[start:end].strip()))
    return out


def vkey(v):
    return tuple(int(x) for x in v.split("."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true",
                    help="segna la versione in cima come gia' vista")
    args = ap.parse_args()

    vs = versions(fetch())
    if not vs:
        raise SystemExit("Nessuna versione trovata: il formato del CHANGELOG e' cambiato.")
    latest = vs[0][0]

    seen = None
    if os.path.exists(STATE):
        seen = open(STATE, encoding="utf-8").read().strip() or None

    if args.record:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f:
            f.write(latest + "\n")
        print(f"Segnata come vista la versione {latest}.")
        print("RICORDA: git add/commit/push, altrimenti la memoria va persa.")
        return

    if seen is None:
        print(f"Nessuno stato precedente. Versione corrente: {latest}.")
        print("Prima esecuzione: riporta solo l'ultima release, non tutto lo storico.\n")
        print(vs[0][1][:2000])
        return

    fresh = [(v, body) for v, body in vs if vkey(v) > vkey(seen)]
    if not fresh:
        print(f"Nessuna novita': ancora alla {seen}. Ometti la voce dal digest.")
        return

    print(f"Vista l'ultima volta: {seen} -> ora {latest}. "
          f"Nuove release: {', '.join(v for v, _ in fresh)}\n")
    for v, body in fresh:
        print(body[:2500])
        print("\n" + "-" * 70 + "\n")


if __name__ == "__main__":
    main()
