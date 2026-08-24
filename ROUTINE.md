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
| `state/aihero-inviati.csv` | Ledger dei post aihero.dev già inviati. **Fonte oggi bloccata**, vedi sotto. |
| `state/mattpocock-skills-version.txt` | Ultima release vista di `mattpocock/skills`. |
| `scripts/pick_skills.py` | Scarica la lista a monte, esclude il ledger, ordina per profilo. |
| `scripts/track_mp_skills.py` | Diff del CHANGELOG di `mattpocock/skills` rispetto all'ultima vista. |
| `scripts/check_sources.py` | Sonda tutte le fonti e dice quali sono raggiungibili **adesso**. |

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

### Esaurimento del pool

Il CSV a monte viene **riscaricato a ogni esecuzione**, quindi le voci che la
community aggiunge nel tempo entrano da sole nel pool: non c'è niente da
resettare e il numero di candidate non è fisso.

Quando però non restano candidate pertinenti, la sezione skill **si omette e
basta**. Non riempirla con voci marginali, non ripescare dal ledger, non
annunciare l'esaurimento ogni settimana. Se le pertinenti sono 1 o 2, se ne
mandano 1 o 2. Lo script applica già questa regola e lo dice in output.

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

## aihero.dev — fonte ATTIVA dal 24/08/2026

Comportamento voluto: ogni settimana un brief dei post degli ultimi 7 giorni,
più 2 articoli più vecchi scelti per mettersi in pari, partendo da **febbraio
2026** ed evitando roba superata. Ledger: `state/aihero-inviati.csv`.

**Il dominio è tornato raggiungibile** (verificato il 24/08/2026). Ma il percorso
per leggerlo è uno solo:

| Percorso | Esito |
| --- | --- |
| `urllib.request` da `python3` (passa dal proxy) | **funziona**, HTTP 200 |
| `curl https://www.aihero.dev/posts` | `SSL_ERROR_SYSCALL` |
| `WebFetch` su `/posts` | HTTP 404 |

Quindi: **usare `urllib` da Python, non `curl` e non `WebFetch`.**

### Come estrarre l'elenco dei post con le date

`/posts` è una pagina Next.js da ~2 MB con dentro un indice Algolia. Le date non
stanno in `date` o `publishedAt` ma in **`published_at_timestamp`** (millisecondi
epoch). Ogni oggetto porta anche `slug`, `title`, `type` e `summary`.

```python
import re, datetime, urllib.request
h = urllib.request.urlopen(urllib.request.Request(
    "https://www.aihero.dev/posts", headers={"User-Agent": "Mozilla/5.0"}
), timeout=30).read().decode("utf-8", "replace")
for m in re.finditer(r'"published_at_timestamp":(\d+)', h):
    seg = h[m.end():m.end()+3000]
    slug = re.search(r'"slug":"([^"]+)"', seg)
    date = datetime.datetime.utcfromtimestamp(int(m.group(1))/1000).date()
```

URL di un post: `https://www.aihero.dev/<slug>`. I `type` `workshop` **non** sono
post: vivono sotto `/workshops/<slug>` e la URL piatta dà 404.

Copertura complementare: `scripts/track_mp_skills.py` legge il CHANGELOG di
`mattpocock/skills`. Attenzione: le release non escono ogni settimana (1.2.3 è
del 06/08), quindi spesso la novità della finestra sta nei **commit**, non nella
release. Vedi sotto come leggerli.

## Limiti dell'ambiente (verificati il 24/08/2026)

1. **`claude.com` è di nuovo raggiungibile.** Il blog di Anthropic si legge
   direttamente, non serve più il ripiego su `WebSearch`. `WebFetch` funziona
   sui singoli post. L'indice `https://claude.com/blog` va preso con `urllib` e
   parsato: le date sono in chiaro nel formato `August 20, 2026`, vicine
   all'`href` del post.
2. **`api.github.com` è ristretto allo scope del repo** per i tool che leggono un
   repo specifico (`list_releases`, `get_file_contents`, …): su repo di terzi
   rispondono "access to this repository is not enabled for this session".
   **Ma gli endpoint di ricerca non sono ristretti**: `search_repositories` e
   `search_commits` funzionano su tutto GitHub e restituiscono conteggi stelle e
   date affidabili. Usare quelli.
   - novità della settimana in un repo della watchlist:
     `search_commits` con `repo:owner/name committer-date:>AAAA-MM-GG`
   - repo nuovi: `search_repositories` con `created:>AAAA-MM-GG`, `sort=stars`
3. **`github.com` in HTML è bloccato** (HTTP 403), incluse le pagine
   `/releases`, `/commits` e i feed `.atom`. `raw.githubusercontent.com`
   funziona: usarlo per i file grezzi (CHANGELOG, README, CSV).
4. **`WebFetch` su pagine GitHub sbaglia i numeri.** Le pagine HTML passano da un
   modello riassuntore che ha restituito valori palesemente falsi (es. "242k
   stars" e "234.5k stars" per repo che non li hanno). **Non citare mai un
   conteggio stelle preso da `WebFetch`.** Prenderli da `search_repositories`
   (campo `stargazers_count`), che viene dall'API vera.
5. **Le pagine `whats-new/AAAA-wNN` esistono solo a settimana conclusa.** Il
   24/08/2026 (lunedì, ISO week 35) `2026-w35` dava 404 e la pagina buona era
   `2026-w34`. Calcolare la settimana ISO e, se la corrente dà 404, usare la
   precedente.

## Prompt della routine

Il prompt vive nella configurazione della routine su Claude Code web, non in
questo repo: va aggiornato da lì. Testo corrente in `prompt-routine.md`.
