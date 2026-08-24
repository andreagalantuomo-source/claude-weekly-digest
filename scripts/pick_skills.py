#!/usr/bin/env python3
"""
Candidati skill da awesome-claude-code, esclusi quelli gia' inviati.

Uso:
  python3 scripts/pick_skills.py                  # elenca i candidati, ranked
  python3 scripts/pick_skills.py --all            # ignora il ranking di profilo
  python3 scripts/pick_skills.py --record ID1,ID2,ID3 --date 2026-08-30

Il ledger (state/skills-inviate.csv) e' la memoria fra le esecuzioni: il
container e' effimero, quindi va committato e pushato dopo ogni invio.
"""

import argparse
import csv
import io
import os
import sys
import urllib.request

CSV_URL = (
    "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/"
    "main/THE_RESOURCES_TABLE_NEW.csv"
)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "state", "skills-inviate.csv")
LEDGER_COLS = ["ID", "Display Name", "Link", "Category", "Data Invio", "Note"]

# Profilo di Andrea: pesi per il ranking dei candidati.
PROFILE = {
    "skill": 5, "skills": 5, "hook": 5, "hooks": 5, "rules": 4,
    "mcp": 5, "connector": 4, "connettor": 4,
    "memory": 5, "memoria": 5, "context persistence": 5, "knowledge": 4, "brain": 4,
    "routine": 4, "slash command": 4, "slash-command": 4, "plugin": 5,
    "orchestrat": 3, "subagent": 3, "agent team": 3,
}
# Temi che l'utente ha esplicitamente escluso dal digest.
PENALTY = {
    "windows": -4, "gitlab": -4, "self-hosted runner": -4, "enterprise sso": -4,
    "jetbrains": -2, "bedrock": -3, "vertex": -3,
}

# Andrea e' un utente esperto: vuole roba installabile, non percorsi didattici.
# Le categorie puramente esplicative partono penalizzate (non escluse: una voce
# "From Anthropic" davvero notevole puo' comunque emergere).
CATEGORY_BIAS = {
    "Start Here": -18,
    "Documentation, Knowledge & Learning": -10,
    "From Anthropic": -6,
    "Alternative Clients": -6,
    "Skills": +8,
    "Memory & Context Persistence": +6,
    "Agent Orchestration": +3,
}


def fetch_rows():
    with urllib.request.urlopen(CSV_URL, timeout=60) as r:
        text = r.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


def load_ledger():
    if not os.path.exists(LEDGER):
        return {}
    with open(LEDGER, newline="", encoding="utf-8") as f:
        return {r["ID"]: r for r in csv.DictReader(f)}


def score(row):
    hay = " ".join([
        row.get("Category", ""), row.get("Sub-Category", ""),
        row.get("Display Name", ""), row.get("Description", ""),
    ]).lower()
    s = sum(w for k, w in {**PROFILE, **PENALTY}.items() if k in hay)
    return s + CATEGORY_BIAS.get(row.get("Category", ""), 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", help="ID separati da virgola, da segnare come inviati")
    ap.add_argument("--date", help="data invio YYYY-MM-DD (per --record)")
    ap.add_argument("--note", default="", help="nota libera (per --record)")
    ap.add_argument("--all", action="store_true", help="non applicare il ranking di profilo")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    rows = fetch_rows()
    ledger = load_ledger()
    by_id = {r["ID"]: r for r in rows}

    if args.record:
        if not args.date:
            sys.exit("--record richiede --date YYYY-MM-DD")
        ids = [i.strip() for i in args.record.split(",") if i.strip()]
        unknown = [i for i in ids if i not in by_id]
        if unknown:
            sys.exit(f"ID non presenti nel CSV a monte: {unknown}")
        dupes = [i for i in ids if i in ledger]
        if dupes:
            sys.exit(f"RIFIUTO: gia' inviati in passato: {dupes}")
        newfile = not os.path.exists(LEDGER)
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        with open(LEDGER, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=LEDGER_COLS)
            if newfile:
                w.writeheader()
            for i in ids:
                r = by_id[i]
                w.writerow({
                    "ID": i, "Display Name": r["Display Name"], "Link": r["Link"],
                    "Category": r["Category"], "Data Invio": args.date, "Note": args.note,
                })
        print(f"Registrati {len(ids)} invii in {os.path.relpath(LEDGER, ROOT)}")
        print("RICORDA: git add/commit/push, altrimenti la memoria va persa.")
        return

    pool = [r for r in rows
            if r["ID"] not in ledger
            and r.get("Active", "").upper() == "TRUE"
            and r.get("Stale", "").upper() != "TRUE"]

    print(f"Voci a monte: {len(rows)} | gia' inviate: {len(ledger)} | "
          f"candidate disponibili: {len(pool)}")
    if len(pool) < 12:
        print("!! POOL QUASI ESAURITO: segnalalo nella mail invece di raschiare il fondo.")

    ranked = pool if args.all else sorted(pool, key=score, reverse=True)
    for r in ranked[: args.top]:
        s = "" if args.all else f"[score {score(r):>3}] "
        print(f"\n{s}{r['ID']}  —  {r['Display Name']}")
        print(f"  cat:  {r['Category']}"
              + (f" / {r['Sub-Category']}" if r["Sub-Category"] else ""))
        print(f"  link: {r['Link']}")
        print(f"  desc: {(r['Description'] or '')[:260]}")


if __name__ == "__main__":
    main()
