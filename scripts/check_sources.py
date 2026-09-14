#!/usr/bin/env python3
"""
Sonda le fonti della routine e dice quali sono raggiungibili da questo ambiente.

Da eseguire all'inizio di ogni esecuzione: la policy di rete dell'ambiente puo'
cambiare, e una fonte che oggi e' bloccata puo' tornare disponibile (o viceversa)
senza preavviso. Meglio saperlo prima di scrivere il digest che dopo.

  python3 scripts/check_sources.py
"""

import concurrent.futures
import urllib.error
import urllib.request

SOURCES = [
    ("changelog Claude Code", "https://code.claude.com/docs/en/changelog", True),
    ("what's new (settimana)", "https://code.claude.com/docs/en/whats-new", True),
    ("blog Anthropic", "https://claude.com/blog", True),
    ("awesome-claude-code (CSV)",
     "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/"
     "main/THE_RESOURCES_TABLE_NEW.csv", True),
    ("mattpocock/skills (CHANGELOG)",
     "https://raw.githubusercontent.com/mattpocock/skills/main/CHANGELOG.md", True),
    ("aihero.dev (post di Matt Pocock)", "https://www.aihero.dev/posts", True),
]


def probe(item):
    name, url, expected = item
    req = urllib.request.Request(url, method="GET",
                                 headers={"User-Agent": "claude-weekly-digest"})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return name, url, expected, True, f"HTTP {r.status}"
    except urllib.error.HTTPError as e:
        # Risponde: il dominio e' raggiungibile anche se l'URL da' errore.
        return name, url, expected, True, f"HTTP {e.code}"
    except Exception as e:
        return name, url, expected, False, f"{type(e).__name__}: {str(e)[:80]}"


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(probe, SOURCES))

    blocked_unexpected = []
    recovered = []
    print(f"{'FONTE':<34} {'STATO':<8} DETTAGLIO")
    print("-" * 78)
    for name, url, expected, ok, detail in results:
        print(f"{name:<34} {'OK' if ok else 'BLOCCATA':<8} {detail}")
        if expected and not ok:
            blocked_unexpected.append(name)
        if not expected and ok:
            recovered.append(name)

    if blocked_unexpected:
        print("\n!! Fonti attese ma NON raggiungibili: "
              + ", ".join(blocked_unexpected))
        print("   Segnalalo nella mail e nella notifica: il digest e' parziale.")
    if recovered:
        print("\n>> Fonti prima bloccate e ora RAGGIUNGIBILI: " + ", ".join(recovered))
        print("   Attiva la sezione corrispondente e aggiorna ROUTINE.md.")
    if not blocked_unexpected and not recovered:
        print("\nNessuna sorpresa: stato identico a quello documentato in ROUTINE.md.")


if __name__ == "__main__":
    main()
