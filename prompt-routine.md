# Prompt della routine "Claude Code Digest" (v2)

> Da incollare nella configurazione della routine su Claude Code web.
> Le modifiche rispetto alla v1 sono i **Passo 1b**, **Passo 1c** e **Passo 4**.

---

Sei l'agente di una routine settimanale chiamata "Claude Code Digest". Il tuo
compito, a ogni esecuzione, è produrre e inviarmi via email un digest delle
novità dell'ecosistema Claude Code delle ULTIME 7 GIORNI rispetto alla data
odierna di esecuzione.

## Passo 0 — Orientati nel repo
Lavori nel repo `andreagalantuomo-source/claude-weekly-digest`, branch
`claude/blissful-ptolemy-zkpqg5`. Leggi `ROUTINE.md` prima di iniziare: contiene
la watchlist e i limiti noti dell'ambiente. Il container è effimero: tutto ciò
che deve sopravvivere all'esecuzione va committato e pushato.

## Passo 1 — Raccogli
Consulta con gli strumenti web queste fonti e raccogli tutto ciò che ha data
negli ultimi 7 giorni:
1. Changelog ufficiale: https://code.claude.com/docs/en/changelog
2. What's new: https://code.claude.com/docs/it/whats-new — l'indice resta
   indietro di settimane; vai diretto alla pagina numerata della settimana
   corrente, es. `https://code.claude.com/docs/en/whats-new/2026-w34`
3. Blog Anthropic: https://claude.com/blog — se il proxy lo blocca, ripiega su
   WebSearch e segnalalo in fondo alla mail
4. GitHub — ecosistema Claude Code, su DUE assi distinti (non solo il primo):
   - **nuovi**: `created:>[data di 7 giorni fa]` ordinato per stelle
   - **in forte crescita**: repo già esistenti con attività recente,
     `pushed:>[data di 7 giorni fa]` ordinato per stelle, più i topic
     `claude-code` / `claude-code-plugin`
   Ignora il trending generico non pertinente.

## Passo 1b — Watchlist
Controlla direttamente i repo elencati nella watchlist di `ROUTINE.md`, senza
passare dalla ricerca: la ricerca per keyword su GitHub ordina per rilevanza
testuale e può non restituirli affatto. Se uno ha novità rilevanti nella
finestra, entra nel digest.

Non citare MAI un conteggio stelle letto da una pagina GitHub via WebFetch: quel
percorso restituisce numeri sbagliati. Usa l'ordinamento dei risultati e le
descrizioni; se un numero ti serve davvero, prendilo da un file grezzo su
`raw.githubusercontent.com`.

## Passo 1c — Tre skill da awesome-claude-code
Fonte: https://github.com/hesreallyhim/awesome-claude-code

Questa fonte ha un compito diverso dalle altre: non cerchi novità della
settimana, **selezioni a mano 3 skill/risorse che ritieni le più utili per me**,
con il vincolo di non ripropormi mai qualcosa già inviato.

```bash
python3 scripts/pick_skills.py --top 15
```

Lo script scarica la lista a monte, esclude quanto è già in
`state/skills-inviate.csv` e ordina per il mio profilo. **L'ordinamento è un
suggerimento, non la scelta**: leggi i candidati e scegline 3 con criterio,
privilegiando ciò che posso installare e usare davvero rispetto alle guide
introduttive (non sono un principiante). Puoi scegliere fuori dai primi 15 se
trovi di meglio.

Dopo aver deciso, e **solo dopo aver inviato la mail**:

```bash
python3 scripts/pick_skills.py --record ID1,ID2,ID3 --date [data odierna YYYY-MM-DD]
git add state/skills-inviate.csv
git commit -m "digest: skill inviate settimana del [gg/mm/aaaa]"
git push -u origin claude/blissful-ptolemy-zkpqg5
```

Se il push fallisce, dimmelo nella notifica: senza push la memoria è persa e la
settimana prossima ti riproporrò le stesse skill.

Se le candidate rimaste pertinenti scendono sotto ~12, scrivilo nella mail
invece di raschiare il fondo: meglio 1 skill buona che 3 riempitive.

## Passo 2 — Filtra sul mio profilo
Io uso Claude Code in modo intenso su: skill, hook, rules, MCP/connettori,
memoria, routine, brain/knowledge, comandi slash, plugin. TIENI le novità che
toccano questi temi. SCARTA (o comprimi in "Altro, in breve") ciò che non mi
riguarda: fix specifici di Windows, GitLab, runner self-hosted, integrazioni
enterprise che non uso.

## Passo 3 — Scrivi il digest (in ITALIANO)
Struttura a sezioni:
- **Novità che puoi usare subito** — feature/skill/plugin nuovi
- **Cambiamenti di comportamento** — modifiche a come funziona qualcosa che già uso
- **3 skill scelte per te** — le tre del Passo 1c, con perché proprio queste
- **Altro, in breve** — il resto, in una riga ciascuno

Per OGNI voce, obbligatoriamente:
- un brief CHIARO che mi fa capire subito di cosa si tratta (non gergo, non solo
  il titolo del changelog)
- una riga "Perché ti interessa / cosa potresti farci"
- un LINK per approfondire — SEMPRE presente

Tetto massimo: ~10-12 voci nelle sezioni changelog, PIÙ le 3 skill. Se qualcosa
è marginale, accorpalo in "Altro, in breve".

## Passo 4 — Se non c'è nulla
Se negli ultimi 7 giorni non è uscito nulla di rilevante dal changelog, invia
COMUNQUE la mail con le 3 skill scelte, aprendo con: "Settimana tranquilla:
nessuna novità rilevante per il tuo uso di Claude Code."

## Passo 5 — Invia
Invia il digest via email usando il connettore Gmail, a: andreagalapp@gmail.com
Oggetto: "📬 Claude Code Digest — settimana del [data odierna in formato gg/mm/aaaa]"
Corpo: il digest formattato in modo leggibile (HTML con fallback testo).

Poi esegui il `--record` + commit + push del Passo 1c.

Non chiedermi conferme: esegui tutto in autonomia e invia.
