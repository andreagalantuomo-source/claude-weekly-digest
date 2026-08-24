# Claude Code Digest — configurazione della routine

Repo di supporto alla routine settimanale "Claude Code Digest".
Serve a **una cosa sola**: dare alla routine una memoria che sopravviva fra
un'esecuzione e l'altra.

## Perché serve un repo

La routine gira in un container effimero: viene clonato il repo, si esegue il
task, il container viene distrutto. Niente di quello che resta su disco
sopravvive. Quindi la richiesta "non ripropormi le stesse skill la settimana
dopo" **non è realizzabile senza uno stato persistito**: l'unico posto che
sopravvive è il repo, e solo se il file viene committato e pushato.

Da qui: `state/skills-inviate.csv` è il ledger. Se un'esecuzione invia 3 skill
ma non pusha il ledger, la settimana dopo le riproporrà.

## File

| File | Ruolo |
| --- | --- |
| `state/skills-inviate.csv` | Ledger delle skill già inviate. **Va pushato dopo ogni invio.** |
| `scripts/pick_skills.py` | Scarica la lista a monte, esclude il ledger, ordina per profilo. |

### Uso

```bash
python3 scripts/pick_skills.py --top 15          # candidati, ranked
python3 scripts/pick_skills.py --record ID1,ID2,ID3 --date 2026-08-30
git add state/skills-inviate.csv && git commit -m "digest: skill settimana ..." && git push
```

`--record` **rifiuta** un ID già presente nel ledger: è la rete di sicurezza
contro i duplicati, indipendente dal giudizio del modello.

La fonte a monte (`THE_RESOURCES_TABLE_NEW.csv` di awesome-claude-code) si legge
via `raw.githubusercontent.com`, che restituisce i byte esatti. È importante:
vedi "Limiti dell'ambiente".

## Watchlist — repo e autori da controllare sempre

La ricerca per keyword su GitHub è inaffidabile per la scoperta: ordina per
rilevanza testuale, non per notorietà. Repo noti e pertinenti possono non
comparire in nessuna delle prime pagine. La contromisura è una watchlist
controllata a ogni esecuzione, **a prescindere dal ranking di ricerca**.

- `mattpocock/skills` — skill di Matt Pocock (grill-with-docs, tdd, to-spec, handoff…)
- `obra/superpowers`
- `anthropics/claude-code`
- `hesreallyhim/awesome-claude-code` — anche come fonte, vedi sotto

Aggiungere qui qualsiasi autore/repo che si voglia non perdere.

## Limiti dell'ambiente (verificati il 24/08/2026)

1. **`claude.com` è bloccato dal proxy di egress** (`EGRESS_BLOCKED`). Il blog di
   Anthropic non è leggibile in modo diretto: ripiego su `WebSearch`. Per
   risolverlo davvero va aggiunto `claude.com` ai domini consentiti
   dell'ambiente remoto.
2. **`api.github.com` è ristretto allo scope del repo.** Le API GitHub su repo di
   terzi rispondono "access to this repository is not enabled for this session".
   Niente conteggi stelle esatti per repo esterni.
3. **`WebFetch` su pagine GitHub sbaglia i numeri.** Le pagine HTML passano da un
   modello riassuntore che ha restituito valori palesemente falsi (es. "242k
   stars" e "234.5k stars" per repo che non li hanno). **Non citare mai un
   conteggio stelle preso da `WebFetch`.** Usare l'ordinamento dei risultati
   (affidabile) e le descrizioni, oppure `raw.githubusercontent.com` per i file
   grezzi.

## Prompt della routine

Il prompt vive nella configurazione della routine su Claude Code web, non in
questo repo: va aggiornato da lì. Testo corrente in `prompt-routine.md`.
