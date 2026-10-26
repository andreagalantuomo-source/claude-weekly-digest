#!/usr/bin/env python3
"""Novita' in mattpocock/skills da quando l'abbiamo guardato l'ultima volta.

Passo 1d (copertura parziale) della routine.

    python3 scripts/track_mp_skills.py            # mostra le versioni nuove
    python3 scripts/track_mp_skills.py --record   # segna come viste

Legge il CHANGELOG da raw.githubusercontent.com: il proxy dell'ambiente
blocca sia api.github.com sia le pagine github.com per i repo non configurati,
mentre raw.githubusercontent.com passa.
"""
import argparse
import json
import os
import re
import ssl
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE = os.path.join(ROOT, "state", "mp-skills-releases.json")
RAW = "https://raw.githubusercontent.com/mattpocock/skills/main"
CHANGELOG_URL = f"{RAW}/CHANGELOG.md"
PLUGIN_URL = f"{RAW}/.claude-plugin/plugin.json"
RELEASES_PAGE = "https://github.com/mattpocock/skills/releases"
CA_BUNDLE = "/root/.ccr/ca-bundle.crt"


def ctx():
    if os.path.exists(CA_BUNDLE):
        return ssl.create_default_context(cafile=CA_BUNDLE)
    return ssl.create_default_context()


def get(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "claude-weekly-digest/1.0"})
    with urllib.request.urlopen(req, timeout=45, context=ctx()) as r:
        return r.read().decode("utf-8", "replace")


def vkey(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3] or [0])


def parse_changelog(md):
    """[(versione, corpo)] dalla piu' recente, su heading '## x.y.z'."""
    parts = re.split(r"^## +(\d+\.\d+\.\d+[^\s]*)\s*$", md, flags=re.M)
    out = []
    for i in range(1, len(parts) - 1, 2):
        out.append((parts[i].strip(), parts[i + 1].strip()))
    return out


def summarize(body, limit=6):
    """Le voci del changelog, ripulite da link, hash e ringraziamenti."""
    items = []
    for raw in re.split(r"\n(?=- \[#)", body):
        t = raw.strip()
        if not t.startswith("- ["):
            continue
        t = re.sub(r"^- \[#(\d+)\]\([^)]*\)\s*", r"(#\1) ", t)
        t = re.sub(r"\[`[0-9a-f]{7,}`\]\([^)]*\)\s*", "", t)
        t = re.sub(r"Thanks \[@[^\]]+\]\([^)]*\)!\s*-\s*", "", t)
        t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", t)
        t = re.sub(r"\s+", " ", t).strip()
        first = t.split(". ")[0]
        items.append(first[:300] + ("..." if len(first) > 300 else ""))
        if len(items) >= limit:
            break
    return items


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    return {"last_seen_version": None, "seen": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true",
                    help="segna come viste le versioni attuali (dopo l'invio)")
    a = ap.parse_args()

    st = load_state()
    seen = set(st.get("seen") or [])
    last = st.get("last_seen_version")

    versions = parse_changelog(get(CHANGELOG_URL))
    if not versions:
        print("CHANGELOG non interpretabile: controlla il formato a monte.")
        return 1
    current = json.loads(get(PLUGIN_URL)).get("version", versions[0][0])

    if last is None:
        new = [versions[0]]
        print(f"Primo run: nessuno stato precedente. Versione corrente {current}.")
        print("Non c'e' un 'prima' con cui confrontare: non trattarla come")
        print("novita' della settimana, verifica la data su " + RELEASES_PAGE)
    else:
        new = [(v, b) for v, b in versions
               if v not in seen and vkey(v) > vkey(last)]

    print(f"versione corrente: {current}   ultima vista: {last or '-'}")
    print("=" * 70)
    if not new:
        print("NESSUNA VERSIONE NUOVA: ometti la voce dal digest.")
    else:
        for v, body in new:
            print(f"\n## {v}")
            for it in summarize(body):
                print(f"  - {it}")
        print("\n" + "=" * 70)
        print(f"Pagina release (per le date, via WebFetch): {RELEASES_PAGE}")

    if a.record:
        st["last_seen_version"] = current
        st["seen"] = sorted(set(seen) | {v for v, _ in versions}, key=vkey)
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f:
            json.dump(st, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"\nstato aggiornato: {STATE} (last_seen_version={current})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
