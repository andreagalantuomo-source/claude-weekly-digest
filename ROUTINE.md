# ROUTINE.md — Claude Code Digest

Supporto operativo per la routine settimanale "Claude Code Digest".
Branch di lavoro: `claude/sleepy-curie-a758cj`.

## Profilo del destinatario

Uso intenso di Claude Code su: **skill, hook, rules, MCP/connettori, memoria,
routine, brain/knowledge, comandi slash, plugin**. Non è un principiante: le
guide introduttive non interessano, interessa ciò che si installa e si usa.

Da scartare o comprimere in "Altro, in breve": fix specifici di Windows,
GitLab, runner self-hosted, integrazioni enterprise non usate.

## Fonti

| # | Fonte | URL | Note |
|---|-------|-----|------|
| 1 | Changelog ufficiale | https://code.claude.com/docs/en/changelog | Fonte principale. Pagina enorme (>1M caratteri): le release recenti sono in cima, il primo blocco da 100k basta per la finestra di 7 giorni. |
| 2 | What's new | https://code.claude.com/docs/en/whats-new | Vedi "Limiti noti". |
| 3 | Blog Anthropic | https://claude.com/blog | Redirect 308 su curl, ma WebFetch lo segue e funziona. |
| 4 | GitHub ecosistema | ricerca su github.com | Due assi: `created:>DATA` (nuovi) e `pushed:>DATA` + topic `claude-code` / `claude-code-plugin` (in crescita). |
| 5 | awesome-claude-code | https://github.com/hesreallyhim/awesome-claude-code | Passo 1c. Scaricare il README da `raw.githubusercontent.com`. |
| 6 | Matt Pocock | https://www.aihero.dev/posts | Passo 1d. Vedi "Limiti noti". |
| 7 | mattpocock/skills | https://github.com/mattpocock/skills/releases | Passo 1d, copertura parziale. |

## Watchlist (Passo 1b)

Da controllare direttamente, senza passare dalla ricerca per keyword.

- `hesreallyhim/awesome-claude-code` — la lista di riferimento dell'ecosistema
- `mattpocock/skills` — la suite di skill di Matt Pocock
- `obra/superpowers` — bundle di skill per l'intero SDLC
- `diet103/claude-code-infrastructure-showcase` — hook che selezionano le skill
- `huggingface/funes` — memoria durevole cross-agent
- `plur-ai/plur` — memoria engram local-first in YAML
- `thedotmack/claude-mem` — memoria persistente fra sessioni
- `BetaBots-LLC/callimachus` — indice ricercabile della cronologia agenti
- `gilles-g/localpr` — review locale in stile pull request
- `Wolfe-Jam/faf-cli` — CLAUDE.md / AGENTS.md generati dallo stack reale

## Limiti noti dell'ambiente

Verificati il 2026-10-26. `scripts/check_sources.py` li rimisura a ogni run:
fidarsi dello script, non di queste note.

- **Pagine settimanali di What's new: inesistenti oltre la W37.**
  `/docs/en/whats-new/2026-wNN` restituisce 404 per tutte le settimane da W38 a
  W44. Non è un blocco di rete: le pagine non sono state pubblicate. L'indice
  `/docs/en/whats-new` si ferma anch'esso alla Week 37 (7–11 settembre 2026).
  Il changelog resta quindi la fonte primaria. Riprovare ogni settimana.
- **WebFetch dà 404 su `www.aihero.dev`** mentre `curl` sullo stesso URL dà 200.
  Usare `curl` per quel dominio. Per le date dei post la via buona è
  **`https://www.aihero.dev/rss.xml`**: l'HTML di `/posts` è un bundle Next.js
  da 2 MB senza date in chiaro, il feed RSS ha `pubDate` per ogni voce.
  Attenzione: il feed non è ordinato per data, va ordinato a mano.
- **`api.github.com` risponde 403** attraverso il proxy. Per le release usare
  WebFetch sulla pagina HTML `github.com/<owner>/<repo>/releases`.
- **Conteggi stelle**: mai citarli da una pagina GitHub letta via WebFetch,
  restituisce numeri sbagliati. Usare l'ordinamento dei risultati e le
  descrizioni; se serve un numero, prenderlo da un file grezzo su
  `raw.githubusercontent.com`.

## Stato persistente

- `state/skills-inviate.csv` — ledger delle skill già inviate (Passo 1c)
- `state/aihero-inviati.csv` — ledger dei post Matt Pocock già inviati (Passo 1d)
- `state/mp-skills-releases.json` — ultime release viste di `mattpocock/skills`

Il container è effimero: **senza commit + push la memoria è perduta** e la
settimana dopo si ripropongono le stesse cose.
