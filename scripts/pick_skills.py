#!/usr/bin/env python3
"""Candidate skill/risorse da awesome-claude-code, escluse quelle gia' inviate.

Passo 1c della routine.

    python3 scripts/pick_skills.py --top 15
    python3 scripts/pick_skills.py --record owner/repo,owner/repo2 --date 2026-10-26

L'ordinamento e' un SUGGERIMENTO: la scelta finale la fa l'agente leggendo i
candidati. Si puo' scegliere fuori dai primi N.
"""
import argparse
import csv
import os
import re
import ssl
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEDGER = os.path.join(ROOT, "state", "skills-inviate.csv")
README_URL = ("https://raw.githubusercontent.com/hesreallyhim/"
              "awesome-claude-code/main/README.md")
CA_BUNDLE = "/root/.ccr/ca-bundle.crt"

LEDGER_FIELDS = ["id", "nome", "url", "data_invio", "sezione"]

# Profilo: skill, hook, rules, MCP/connettori, memoria, routine,
# brain/knowledge, comandi slash, plugin. Non un principiante.
POSITIVE = {
    "hook": 6, "hooks": 6, "skill": 4, "skills": 4, "plugin": 4,
    "mcp": 5, "memory": 6, "memoria": 6, "context": 4, "persistent": 4,
    "slash": 5, "command": 2, "rules": 4, "claude.md": 5, "agents.md": 4,
    "knowledge": 5, "routine": 4, "cron": 3, "schedule": 3,
    "subagent": 3, "orchestrat": 3, "settings": 3, "config": 2,
    "local-first": 3, "install": 2, "recall": 3, "engram": 3,
}
# Materiale didattico: non e' un principiante, queste voci non lo interessano.
NEGATIVE = {
    "beginner": -14, "newcomer": -14, "getting started": -14,
    "getting-started": -14, "introduction": -10, "introductory": -10,
    "tutorial": -10, "learning path": -14, "self-assessment": -10,
    "quiz": -10, "primer": -12, "explainer": -10, "mental-models": -8,
    "teaching": -8, "teaches the tool": -10, "chapter-based": -12,
    "everything you need to know": -12, "walkthrough": -6,
    "single-page reference": -8, "conceptual": -8, "orientation": -6,
    "copy-paste templates": -6, "progressive learning": -12,
    "awesome list": -12, "curated list": -10, "cheatsheet": -6, "101": -8,
    "windows": -4, "gitlab": -4, "self-hosted runner": -4, "enterprise sso": -4,
    "video": -3, "carousel": -4, "seo": -4, "linkedin": -4, "recipe": -4,
    "genealogy": -5, "microcontroller": -4, "firmware": -4,
    "pixel-art": -5, "game": -3,
}

# Un keyword-stuffing di temi ("slash commands, memory, skills, subagents, MCP,
# hooks, plugins...") e' tipico delle guide introduttive, non di uno strumento
# installabile: il contributo delle keyword positive viene percio' limitato.
POSITIVE_CAP = 16

# Sezioni del README piu' vicine al profilo
SECTION_BONUS = {
    "skills": 6, "memory & context persistence": 7, "configuration": 4,
    "mods": 5, "agent orchestration": 4, "providers, runtime & integration infrastructure": 3,
    "observability & monitoring": 2, "documentation, knowledge & learning": 3,
    "security": 2, "testing": 1, "linting": 1, "multi-purpose": 2,
    "open source contribution & maintenance": 2, "infrastructure & devops": 1,
    "from anthropic": 3, "start here": -4, "lists & collections": -6,
    "creative media": -6, "design & ui/ux": -3, "writing & prose quality": -1,
    "alternative clients": -3, "status lines": -2,
    "remote control, notifications & voice i/o": 1,
    "research & scientific inquiry": -2, "the claude code ticker - a sample of claude code projects around github": -4,
}

ENTRY_RE = re.compile(r"^- \[(?P<name>[^\]]+)\]\((?P<url>[^)]+)\)(?P<rest>.*)$")


def ctx():
    if os.path.exists(CA_BUNDLE):
        return ssl.create_default_context(cafile=CA_BUNDLE)
    return ssl.create_default_context()


def fetch_readme():
    req = urllib.request.Request(
        README_URL, headers={"User-Agent": "claude-weekly-digest/1.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx()) as r:
        return r.read().decode("utf-8", "replace")


def entry_id(url):
    """ID stabile: owner/repo in minuscolo, altrimenti l'host+path."""
    m = re.match(r"https?://github\.com/([^/\s]+)/([^/\s#?]+)", url)
    if m:
        return f"{m.group(1)}/{m.group(2)}".lower().removesuffix(".git")
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/").lower()


def parse(md):
    out, section = [], ""
    for line in md.splitlines():
        h = re.match(r"^#{2,4}\s+(.*)$", line)
        if h:
            section = h.group(1).strip()
            continue
        m = ENTRY_RE.match(line.strip())
        if not m:
            continue
        url = m.group("url").strip()
        if not url.startswith("http"):
            continue
        rest = m.group("rest")
        # descrizione = testo dopo l'ultimo " - ", ripulito dai badge
        desc = rest.split(" - ", 1)[1] if " - " in rest else rest
        desc = re.sub(r"<[^>]+>", " ", desc)
        desc = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", desc)
        desc = re.sub(r"&amp;", "&", desc)
        desc = re.sub(r"\s+", " ", desc).strip(" -")
        out.append({"id": entry_id(url), "nome": m.group("name").strip(),
                    "url": url, "desc": desc, "sezione": section})
    # dedup per id, tenendo la descrizione piu' lunga
    best = {}
    for e in out:
        cur = best.get(e["id"])
        if cur is None or len(e["desc"]) > len(cur["desc"]):
            best[e["id"]] = e
    return list(best.values())


# Segnali che la voce e' qualcosa da installare e usare, non da leggere.
ACTIONABLE = {
    "cli": 3, "mcp server": 4, "plugin": 3, "install": 3, "npx": 3,
    "pip install": 3, "binary": 3, "daemon": 2, "tui": 2, "local-first": 3,
    "zero config": 2, "zero deps": 2, "stdlib": 2, "marketplace": 2,
    "autofix": 3, "linter": 3, "lsp": 3, "sqlite": 2, "hook": 3,
}


def score(e):
    hay = (e["nome"] + " " + e["desc"]).lower()
    s = SECTION_BONUS.get(e["sezione"].lower(), 0)

    pos = sum(v for k, v in POSITIVE.items() if k in hay)
    s += min(pos, POSITIVE_CAP)

    s += sum(v for k, v in NEGATIVE.items() if k in hay)
    s += sum(v for k, v in ACTIONABLE.items() if k in hay)

    # una voce che e' solo una pagina di documentazione non si installa
    if not re.match(r"https?://github\.com/", e["url"]):
        s -= 6
    if len(e["desc"]) > 160:
        s += 2          # descrizioni curate = voci curate
    if len(e["desc"]) < 40:
        s -= 2
    return s


def read_ledger():
    if not os.path.exists(LEDGER):
        return {}
    with open(LEDGER, newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f) if r.get("id")}


def write_ledger(rows):
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=LEDGER_FIELDS)
        w.writeheader()
        for r in sorted(rows.values(), key=lambda r: (r["data_invio"], r["id"])):
            w.writerow({k: r.get(k, "") for k in LEDGER_FIELDS})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--record", help="ID separati da virgola, da marcare come inviati")
    ap.add_argument("--date", help="data di invio YYYY-MM-DD")
    a = ap.parse_args()

    md = fetch_readme()
    entries = parse(md)
    sent = read_ledger()

    if a.record:
        if not a.date:
            ap.error("--record richiede --date")
        by_id = {e["id"]: e for e in entries}
        for raw in a.record.split(","):
            i = raw.strip().lower()
            if not i:
                continue
            e = by_id.get(i, {})
            sent[i] = {"id": i, "nome": e.get("nome", i), "url": e.get("url", ""),
                       "data_invio": a.date, "sezione": e.get("sezione", "")}
            print(f"registrata: {i}")
        write_ledger(sent)
        print(f"ledger: {LEDGER} ({len(sent)} voci)")
        return 0

    pool = [e for e in entries if e["id"] not in sent]
    print(f"voci nel README: {len(entries)}   gia' inviate: {len(sent)}   "
          f"candidate: {len(pool)}")
    pertinent = [e for e in pool if score(e) > 0]
    if not pertinent:
        print("\nNESSUNA CANDIDATA PERTINENTE: ometti del tutto la sezione skill.")
        return 0
    print(f"candidate con punteggio positivo: {len(pertinent)}\n" + "=" * 70)
    for e in sorted(pertinent, key=score, reverse=True)[:a.top]:
        print(f"[{score(e):+3d}] {e['id']}  ({e['sezione']})")
        print(f"      {e['nome']} — {e['url']}")
        print(f"      {e['desc'][:300]}")
        print()
    print("=" * 70)
    print("L'ordinamento e' un suggerimento. Scegli con criterio, anche fuori lista.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
