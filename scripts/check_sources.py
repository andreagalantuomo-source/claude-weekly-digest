#!/usr/bin/env python3
"""Sonda le fonti del digest e dice quali sono raggiungibili adesso.

Passo 0b della routine. Usa solo la stdlib e rispetta HTTPS_PROXY.
Exit code 0 sempre: e' una sonda, non un gate.
"""
import json
import os
import ssl
import sys
import urllib.request

CA_BUNDLE = "/root/.ccr/ca-bundle.crt"

# (nome, url, come va letta la fonte)
#   "direct"      -> deve rispondere a urllib/curl; un KO qui rende il digest parziale
#   "webfetch"    -> blocca urllib (403 anti-bot) ma funziona via WebFetch:
#                    un 403 qui e' NORMALE e non va segnalato come fonte caduta
SOURCES = [
    ("changelog",       "https://code.claude.com/docs/en/changelog",                     "direct"),
    ("whats-new-index", "https://code.claude.com/docs/en/whats-new",                     "direct"),
    ("blog-anthropic",  "https://claude.com/blog",                                       "direct"),
    ("awesome-cc",      "https://raw.githubusercontent.com/hesreallyhim/awesome-claude-code/main/README.md", "direct"),
    ("aihero-rss",      "https://www.aihero.dev/rss.xml",                                "direct"),
    ("github-web",      "https://github.com/search?q=claude-code&type=repositories",     "webfetch"),
    ("mp-skills",       "https://github.com/mattpocock/skills/releases",                 "webfetch"),
    ("github-api",      "https://api.github.com/repos/mattpocock/skills/releases",       "webfetch"),
]


def ctx():
    if os.path.exists(CA_BUNDLE):
        return ssl.create_default_context(cafile=CA_BUNDLE)
    return ssl.create_default_context()


def probe(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "claude-weekly-digest/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx()) as r:
            return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def main():
    results = {}
    print("Sonda fonti del digest\n" + "=" * 70)
    for name, url, mode in SOURCES:
        code, err = probe(url)
        ok = code is not None and 200 <= code < 400
        results[name] = {"url": url, "status": code, "ok": ok, "error": err,
                         "mode": mode}
        detail = f"HTTP {code}" if code is not None else (err or "errore")
        if mode == "webfetch":
            mark = "OK  " if ok else "n/a "
            flag = "  (leggila via WebFetch, non con curl)"
        else:
            mark = "OK  " if ok else "KO  "
            flag = "" if ok else "  <- digest PARZIALE, segnalalo"
        print(f"{mark}{name:<17} {detail:<26}{flag}")
        print(f"    {url}")

    print("=" * 70)
    blocked = [n for n, r in results.items()
               if not r["ok"] and r["mode"] == "direct"]
    if blocked:
        print("PARZIALE — fonti attese ma non raggiungibili: " + ", ".join(blocked))
        print("Dillo in fondo alla mail e nella notifica.")
    else:
        print("Tutte le fonti a lettura diretta rispondono.")
    print("Le fonti marcate 'webfetch' vanno lette con lo strumento WebFetch:")
    print("un 403 su quelle righe e' atteso e non significa che la fonte sia caduta.")

    print("\nNote che la sonda non puo' misurare (vedi ROUTINE.md):")
    print("  - le pagine settimanali /whats-new/2026-wNN non esistono oltre la W37")
    print("  - WebFetch da 404 su www.aihero.dev: usare curl o il feed RSS")

    if "--json" in sys.argv:
        print("\n" + json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
