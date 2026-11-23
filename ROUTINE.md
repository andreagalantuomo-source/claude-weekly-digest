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
| `state/aihero-inviati.csv` | Ledger dei post aihero.dev già inviati. Fonte **attiva**, vedi sotto. |
| `state/mattpocock-skills-version.txt` | Ultima release vista di `mattpocock/skills`. |
| `scripts/pick_skills.py` | Scarica la lista a monte, esclude il ledger, ordina per profilo. |
| `scripts/track_mp_skills.py` | Diff del CHANGELOG di `mattpocock/skills` rispetto all'ultima vista. |
| `scripts/check_sources.py` | Sonda tutte le fonti e dice quali sono raggiungibili **adesso**. |

Nota su `check_sources.py`: ogni fonte ha nella tabella `SOURCES` un flag
`expected` che è la **baseline documentata qui**. Dal 14/09/2026 tutte e sei
sono a `True`, perché tutte risultano raggiungibili (riconfermato il 28/09/2026,
il 05/10/2026, il 12/10/2026, il 19/10/2026, il 02/11/2026, il 09/11/2026, il 16/11/2026 e il
23/11/2026: sei OK su sei, nessuna sorpresa).

**Il falso OK sul blog, con una correzione (19/10/2026).** La regola "i post sono
su `claude.dev` e `claude.com/blog/<slug>` da' 404" vale per i post **nuovi**, non
per tutti: il 19/10 `https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more`
ha risposto **200** via `urllib`. Quindi i post vecchi restano leggibili su
`claude.com` e un link a uno di quelli non e' rotto: va solo verificato con una GET.

**Attenzione al falso OK sul blog (12/10/2026).** La sonda del blog interroga
`https://claude.com/blog`, che risponde 200 e continua a servire l'indice, ma i
**post** si sono spostati su `claude.dev`: `claude.com/blog/<slug>` ora da' 404 e
`claude.dev` e' bloccato dalla policy di rete. Quindi "blog OK" non significa piu'
"post leggibili": vedi il punto 1 dei limiti dell'ambiente. Quando una fonte cambia
stato in modo stabile, va aggiornato anche quel flag: altrimenti lo script
annuncia ogni settimana un "ora raggiungibile" che non è una novità.

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

## I tool `search_*` del server GitHub MCP possono non esserci (09/11/2026)

**Novita' operativa importante.** Il 09/11/2026 la sessione e' partita con una
nota di sistema esplicita: *«the GitHub MCP `search_*` tools are not available in
this session»*. Quindi `search_commits` e `search_repositories` — su cui si
appoggiano il Passo 1b e il Passo 1 — **non erano chiamabili**.

Il ripiego funziona e va usato senza esitare: la CLI `gh`, che in questa sessione
e' preconfigurata per il proxy.

```bash
gh api -X GET search/commits      -f q='repo:owner/name committer-date:>2026-11-02' -f per_page=50
gh api -X GET search/repositories -f q='claude-code created:>2026-11-02' -f sort=stars -f order=desc -f per_page=12
gh api -X GET search/repositories -f q='topic:claude-code pushed:>2026-11-02'       -f sort=stars -f order=desc -f per_page=12
```

Note pratiche raccolte il 09/11:

- Funziona anche su repo **fuori** dallo scope della sessione: gli endpoint di
  ricerca non sono ristretti (stessa proprieta' gia' documentata per i tool MCP).
- `repo:owner/name` con la **grafia sbagliata** restituisce `422 Validation
  Failed` con il messaggio «the listed users and repositories cannot be
  searched», non un risultato vuoto. Non e' un problema di permessi: e' il repo
  che non esiste con quel nome. Capitato su `maxritter/claude-codepro` e
  `avifenesh/agentsys`, due candidati skill che per questo sono stati scartati.
  **Ricapitato il 16/11/2026** su `kenryu42/claude-code-safety-net`, che era gia'
  stato scelto come terza skill: scartato e sostituito con `JeongJaeSoon/agent-guard`.
  Morale operativa: **verificare con `repo:` i candidati skill PRIMA di scrivere la
  mail**, non dopo — il CSV di awesome-claude-code contiene voci il cui repo non
  esiste piu', e `Active: TRUE` / `Stale: FALSE` nel CSV non lo rilevano.
- Passare l'output a `python3 -c` per filtrare: il JSON grezzo e' enorme.
  Filtrare via gli autori `github-actions[bot]` subito, come con i tool MCP.
- **16/11/2026 — i conteggi stelle sbagliati NON sono solo quelli di `topic:`.**
  Anche `gh api search/repositories -f q='repo:owner/name'` li restituisce falsi:
  il 16/11 dava `303968` per `affaan-m/ECC`, `148561` per `Graphify-Labs/graphify`,
  `141736` per `garrytan/gstack`, `120527` per `JuliusBrussee/caveman` e `118035`
  per `addyosmani/agent-skills` — tutti valori da top-50 di GitHub, per repo che
  non lo sono. Nella stessa sessione la query `created:>` dava invece cifre
  plausibili (365, 362, 345...) e le `repo:` su repo piccoli pure (13, 30, 72, 205,
  6733). Non c'e' un percorso affidabile: **la regola pratica e' non citare nessun
  conteggio stelle in mail**, dirlo in fondo alla mail e descrivere i repo invece
  di quantificarli. E' quello che e' stato fatto il 16/11.
- **I conteggi stelle di `topic:... pushed:>` sono poco credibili.** Il 09/11 la
  query per topic restituiva valori come `444527` e `299807` per repo nati nel
  2026, contro cifre plausibili (`4168`, `1159`, `164`) sulle query
  `created:>`/`repo:`. Non e' chiaro cosa conti quel campo in quella query:
  **non citare quei numeri in mail**, usare l'ordinamento e la descrizione — che
  e' esattamente la regola gia' valida per `WebFetch`, estesa a questo caso.

- **23/11/2026 — i conteggi di `created:>` sembrano plausibili, ma la regola resta.**
  La query `claude-code created:>2026-11-16` ha dato cifre credibili (2224, 518, 467,
  400...) e la query `topic:` non e' stata nemmeno interrogata per le stelle. Non e'
  una prova che il percorso sia affidabile: il 16/11 anche `repo:` dava cifre
  plausibili sui repo piccoli e assurde sui grandi. **Regola invariata: nessun
  conteggio stelle in mail**, e la riga che lo dice in fondo.
- **Verifica dei candidati skill, 23/11**: sei candidati verificati con
  `repo:owner/name` prima di scrivere la mail (`gowtham012/pinpoint`,
  `automatis-tools/agents-can-communicate`, `mennanov/blockwatch`, `haabe/mycelium`,
  `serpro69/capy`, `zircote/workflows-plugin`): **tutti e sei esistono**, nessun 422.
  Nota: il CSV scrive `gowtham012/pinpoint` ma la grafia vera e' **`gowtham012/PinPoint`**
  — GitHub risolve comunque, quindi il link del CSV non e' rotto.
- **23/11/2026 — i candidati scartati per 422 restano nel pool e ritornano.**
  `avifenesh/agentsys` e `maxritter/claude-codepro`, scartati il 09/11 perche' il repo
  non esisteva con quella grafia, erano **di nuovo** in cima al ranking di
  `pick_skills.py` (score 21 e 19). Lo script non sa del 422. Conviene ricordarselo e
  non riverificarli ogni settimana: se un repo ha dato 422 una volta, si salta.

## Watchlist — repo e autori da controllare sempre

La ricerca per keyword su GitHub è inaffidabile per la scoperta: ordina per
rilevanza testuale, non per notorietà. Repo noti e pertinenti possono non
comparire in nessuna delle prime pagine. La contromisura è una watchlist
controllata a ogni esecuzione, **a prescindere dal ranking di ricerca**.

- `mattpocock/skills` — skill di Matt Pocock (grill-with-docs, tdd, to-spec, handoff…)
- `obra/superpowers`
- `anthropics/claude-code`
- `hesreallyhim/awesome-claude-code` — anche come fonte, vedi sotto.
  `search_commits` su questo repo è una buona sonda per le novità di
  *tassonomia* dell'ecosistema, non solo per le singole risorse: il 18/10/2026
  è nata la categoria **Mods** (PR #3184) e "Open Source Software" è stata
  rinominata "Open Source Contribution & Maintenance" (#3187). Filtrare via il
  rumore dei commit `github-actions[bot]` (`chore: update repo ticker data`,
  `chore: regenerate README`), che sono la maggioranza.

Aggiungere qui qualsiasi autore/repo che si voglia non perdere.

## aihero.dev — fonte ATTIVA dal 24/08/2026

Comportamento voluto: ogni settimana un brief dei post degli ultimi 7 giorni,
più 2 articoli più vecchi scelti per mettersi in pari, partendo da **febbraio
2026** ed evitando roba superata. Ledger: `state/aihero-inviati.csv`.

**Il dominio è tornato raggiungibile** (verificato il 24/08/2026, riconfermato il
07/09/2026 — prima esecuzione in cui la sezione è stata effettivamente prodotta —
e il 14/09/2026).
Ma il percorso per leggerlo è uno solo:

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
post: vivono sotto `/workshops/<slug>` e la URL piatta dà 404. Gli altri `type`
(`article`, `skill`, `topic`, `skill-changelog`, `list`) usano la URL piatta.

Il TLS verso `www.aihero.dev` va **a intermittenza**: la stessa URL può dare
`handshake operation timed out` e poi HTTP 200 al tentativo dopo. Prevedere 2-3
retry con una pausa, non concludere che il dominio è bloccato al primo errore.

La cadenza di pubblicazione è irregolare: il 07/09/2026 l'ultimo post era del
17/08 (e per giunta un `workshop`), il 14/09/2026 era **ancora** quello, e il
21/09/2026 **pure**, il 28/09/2026 **ancora**, il 05/10/2026 **sempre** e il
12/10/2026 **di nuovo**: otto settimane senza un post
nuovo. A questo punto l'assenza di post nella finestra è il caso *normale*, non
l'eccezione — si mandano solo i 2 arretrati di recupero, dicendo in chiaro che
non è un blocco ma la cadenza. Il pool di arretrati pertinenti (data ≥ 2026-02-01,
fuori ledger, URL verificata 200) al 05/10/2026 conta ancora una dozzina di
voci, quasi tutte del blocco `skill` del 06-08/07/2026. L'elenco totale letto da
`/posts` è stabile a 37 voci: il pool si consuma solo per sottrazione del ledger
(16 voci dopo il 12/10), quindi fra circa cinque esecuzioni va previsto
l'esaurimento, a cadenza invariata. Il 12/10/2026 undici candidati arretrati sono
stati verificati con una GET: **tutti 200**, quindi il problema dei `skill-changelog`
che danno 404 resta circoscritto a quelle voci.
Il 19/10/2026 l'ultimo post era **ancora quello del 17/08**: **nona** settimana
consecutiva. Cinque candidati arretrati verificati con una GET, **tutti 200**:
`skills-codebase-design`, `skills-code-review`, `skills-domain-modeling`,
`skills-improve-codebase-architecture`, `skills-resolving-merge-conflicts`.
Mandati `codebase-design` e `domain-modeling`; il ledger e' a 18 voci, quindi
restano circa una dozzina di arretrati pertinenti (l'elenco totale e' sempre 37)
e l'esaurimento va previsto fra circa cinque esecuzioni.

Il 02/11/2026 l'ultimo post era **ancora quello del 17/08**: **decima** settimana
consecutiva. A cadenza invariata questa e' la normalita' assoluta, non una notizia:
non vale piu' spenderci righe nella mail oltre a una frase che dice che non e' un
blocco. Il pool fuori ledger e' stato ricalcolato per intero e **verificato con una
GET una per una**: 18 candidati con data >= 2026-02-01, di cui **14 a 200** e 4 a
404 — e i 4 a 404 sono *tutti* `type: skill-changelog`
(`skills-changelog-v12-...`, `skills-changelog-v1-1-...`,
`skills-changelog-v1-announcement`, `skills-changelog-handoff-prototype-review-and-writing`).
Il pattern e' ormai confermato: **i `skill-changelog` danno 404 sulla URL piatta,
gli altri `type` no.** Si possono escludere a priori senza nemmeno provarli, e il
pool pertinente reale e' quindi 14 meno il ledger. Mandati `skills-code-review` e
`skills-resolving-merge-conflicts`; ledger a **20** voci, restano ~12 arretrati
buoni (l'elenco totale e' sempre 37).

Il 09/11/2026 l'ultimo post era **ancora quello del 17/08**: **undicesima** settimana
consecutiva. L'elenco totale e' sempre **37**. Applicando la regola del 02/11
(escludere a priori `workshop` e `skill-changelog`, che danno 404 sulla URL piatta)
il pool fuori ledger era di **12** candidati, tutti con data >= 2026-02-01; sei
verificati con una GET, **tutti 200** — il filtro per `type` sostituisce bene la
verifica a tappeto, ma la GET sul candidato che si manda davvero va fatta comunque.
Mandati `skills-to-tickets` e `skills-improve-codebase-architecture`; ledger a
**22** voci, restano **10** arretrati buoni, quindi l'esaurimento e' atteso fra
circa **cinque** esecuzioni (fine dicembre 2026) a cadenza invariata. Dopo, la
sezione si omette: niente ripescaggi.

Il 16/11/2026 l'ultimo post era **ancora quello del 17/08**: **dodicesima** settimana
consecutiva, elenco totale sempre **37**. Applicando il filtro per `type` (via
`workshop` e `skill-changelog`) il pool fuori ledger era di **10** candidati, tutti
con data >= 2026-02-01; cinque verificati con una GET, **tutti 200**. Mandati
`skills-setup-matt-pocock-skills` e `skills-triage`; ledger a **24** voci, restano
**8** arretrati buoni, quindi l'esaurimento e' atteso fra circa **quattro**
esecuzioni (meta' dicembre 2026) a cadenza invariata. Dopo, la sezione si omette.
In mail la cadenza e' stata liquidata in mezza frase, come stabilito il 02/11.

Il 23/11/2026 **la siccita' e' finita**: l'indice espone un post nuovo del **18/11**,
`watch-me-ship-a-21-000-line-feature-with-mattpocock-skills~ez95n` (type `article`,
URL piatta, 200), il primo dopo **tredici** settimane. Attenzione a due cose:

1. **Lo slug puo' contenere un suffisso `~xxxxx`** (qui `~ez95n`). La URL piatta
   funziona solo con il suffisso: va preso dall'indice tale e quale, non ricostruito
   dal titolo.
2. **L'indice puo' far comparire post con data retroattiva.** `the-home-repo-pattern`
   ha data **12/11**, cioe' sarebbe stato in finestra il 16/11, ma quella settimana
   l'indice non lo mostrava (l'ultimo era ancora il 17/08). Morale: un post con data
   appena fuori finestra, assente dal ledger, va trattato come **arretrato di
   recupero**, non scartato perche' "vecchio di undici giorni" — altrimenti si perde.
   Fatto cosi' il 23/11.

Elenco totale sempre **37** voci (il post nuovo entra, uno vecchio esce dalla finestra
dell'indice). Mandati: il post della settimana piu' `the-home-repo-pattern` e
`skills-implement-spec` come recuperi; ledger a **27** voci, restano **6** arretrati
buoni dopo il filtro per `type`, quindi l'esaurimento e' atteso fra circa **tre**
esecuzioni (meta' dicembre 2026) — salvo che la ripresa della pubblicazione lo
rimandi.

Criterio di scelta che ha funzionato: appaiare l'arretrato a quello che si e' gia'
mandato, cosi' la mail puo' dire *perche'* proprio quello (`/to-tickets` dopo
`/to-spec`, `/improve-codebase-architecture` dopo `/codebase-design`, e il 16/11
`/triage` *prima* di `/to-tickets` — la catena a monte, non a valle). Il 16/11 ha
funzionato anche una seconda angolatura: **mandare il prerequisito** invece di
un'altra skill di pari livello. `/setup-matt-pocock-skills` configura il repo perche'
tutte le altre funzionino, quindi dopo una dozzina di skill singole gia' inviate e'
l'arretrato che rende utile retroattivamente tutto il resto. Le descrizioni
brevi si prendono dal `<meta name="description">` della pagina: il campo `summary`
non c'e' nell'HTML del singolo post, solo nell'indice di `/posts`.

Attenzione sulle URL dei `skill-changelog`: non tutti usano la URL piatta. Il
21/09/2026 `skills-changelog-v12-wait-what-writing-for-agents-claude-code-plugin-and-more`
dava **404** su `https://www.aihero.dev/<slug>` su cinque tentativi, mentre i
`skill` normali (`skills-wayfinder`, `skills-research`) rispondevano 200. Quindi:
**verificare sempre la URL con una GET prima di mettere un arretrato in mail**,
e se da' 404 scegliere un altro candidato invece di spedire un link rotto.

Copertura complementare: `scripts/track_mp_skills.py` legge il CHANGELOG di
`mattpocock/skills`. Attenzione: le release non escono ogni settimana (1.2.3 è
del 06/08 e al 28/09/2026 era **ancora** l'ultima), quindi spesso la novità
della finestra sta nei **commit**, non nella release: al 21/09 lo script diceva
"nessuna novità" mentre nella finestra erano nate la skill `/pr` e una revisione
sostanziale di `retro`. Regola pratica: se lo script non riporta nulla, **fare
comunque** `search_commits` con `repo:mattpocock/skills committer-date:>AAAA-MM-GG`
prima di concludere che non c'è niente da dire. Il 28/09/2026 il doppio
controllo è stato negativo da entrambe le parti (1.2.3 ancora l'ultima,
`total_count: 0` sui commit dal 21/09): in quel caso la voce si omette davvero.

Il 05/10/2026 invece lo script ha fatto da solo tutto il lavoro: **1.3.0 e 1.3.1**
(il salto da 1.2.3 arriva in blocco) promuovono `implement-spec`, `pr` e `retro`
nel bucket *Engineering* — cioè proprio le skill che il 21/09 si vedevano solo nei
commit. Conferma la regola: i commit anticipano la release di qualche settimana,
quindi quando la release arriva la sostanza può essere già stata mandata. Vale
confrontare con quanto riportato nelle settimane precedenti per non ripetersi.
Versione vista ora: **1.3.1**.

Il 12/10/2026 la regola del doppio controllo ha pagato di nuovo, in senso opposto:
`track_mp_skills.py` diceva "nessuna novita'" (ancora 1.3.1), ma `search_commits`
con `repo:mattpocock/skills committer-date:>2026-10-05` restituiva **41 commit** in
finestra, con sostanza vera: fix a `teach` (scriveva i corsi dentro
`~/.claude/skills`), `wayfinder`, `diagnosing-bugs`, `code-review`, `tdd`, `retro`,
`ask-matt`, `implement`, `wizard`, il README che passa all'install auto-aggiornante
dal marketplace `claude-plugins-official`, e una skill nuova in cantiere
(`chief-of-staff`). **Non fidarsi mai del solo script per questo repo.**

Il 02/11/2026 lo script ha visto **1.3.2** (da 1.3.1) e il doppio controllo ha dato
sostanza da **entrambe** le parti. La release: `ask-matt` legge il `SKILL.md` prima
di riassumere una skill, `chief-of-staff` passa a una **memoria a wiki** (`index.md`
+ una pagina per argomento, ingest/query/lint) scritta come registro storico con
ogni claim datato e ogni claim sul codice che cita il commit in cui era vero,
`code-review` passa `CODING_STANDARDS.md`/`CONTRIBUTING.md` al subagent Standards e
gira i subagent in foreground, `diagnosing-bugs` fase 5 fa il diff di una mutazione
forzata contro una copia pristina. In piu' `search_commits` con
`committer-date:>2026-10-26` ha dato **7 commit** (6 non-bot), di cui **4 non
coperti dalla release**: `implement-spec` con un implementer subagent fresco per
ticket (#1342), subagent che partono con un **context window nuovo invece di un
fork** (#1341), la nuova `software-factory` (#1316) e `chief-of-staff` "shared wiki
first" con `retro`/`implement-spec` ridotti a procedure (#1363). Versione vista ora:
**1.3.2**. Conferma definitiva della regola del doppio controllo: su 6 commit utili,
4 non erano nel CHANGELOG.
`repo:obra/superpowers`: ancora **zero** commit in finestra (seconda settimana).
Su `hesreallyhim/awesome-claude-code` i 51 commit in finestra erano **tutti**
`github-actions[bot]`: nessuna novita' di tassonomia.

Il 09/11/2026 il doppio controllo e' stato di nuovo **negativo da entrambe le
parti**: `track_mp_skills.py` dava ancora **1.3.2** e la ricerca commit (via
`gh api search/commits`, vedi la sezione sui tool `search_*`) dava `total_count: 0`
su `repo:mattpocock/skills committer-date:>2026-11-02`. Voce omessa.
In compenso `repo:obra/superpowers` ha dato **1** commit dopo due settimane a zero:
la release **v7.0.2** del 03/11 (tuning del brainstorming, fix al bootstrap
dell'harness e agli helper SDD, compatibilita' con i plugin OpenCode V2). Sostanza
marginale per il profilo: finita in "Altro, in breve". Su
`hesreallyhim/awesome-claude-code` i 51 commit in finestra erano **tutti**
`github-actions[bot]`, come il 02/11: nessuna novita' di tassonomia.

Il 16/11/2026 `track_mp_skills.py` dava ancora **1.3.2** (nessun `--record` fatto,
niente da registrare), ma il doppio controllo via `gh api search/commits` su
`repo:mattpocock/skills committer-date:>2026-11-09` ha dato **2** commit: la PR
**#1416**, una limatura di dizionario su `software-factory` («"job" e' la parola del
vendor CI; `explore` lascia i findings»). Sostanza minima ma non nulla: finita in una
mezza frase nella sezione Matt Pocock, non in una voce propria. Terza conferma della
regola: **lo script da solo avrebbe detto "niente".**
`repo:obra/superpowers`: **zero** commit in finestra. Su
`hesreallyhim/awesome-claude-code` i 50 commit in finestra erano **tutti**
`github-actions[bot]`: nessuna novita' di tassonomia (come il 02/11 e il 09/11).

Il 23/11/2026 `track_mp_skills.py` dava ancora **1.3.2** (niente da registrare), ma
`gh api search/commits` su `repo:mattpocock/skills committer-date:>2026-11-16` ha dato
**4** commit (2 non-merge): la description del frontmatter di `software-factory` messa
fra apici per i parser YAML severi (PR #1453) e un **controllo in CI che valida il
frontmatter di ogni `SKILL.md` con lo stesso parser dell'installer** (PR #1455).
Sostanza piccola ma citabile, finita in una riga della sezione Matt Pocock. Quarta
conferma della regola del doppio controllo. `repo:obra/superpowers`: **zero** commit in
finestra (anche il 16/11 era zero). Su `hesreallyhim/awesome-claude-code` i 50 commit in
finestra erano **tutti** `github-actions[bot]`: nessuna novita' di tassonomia, come nelle
quattro esecuzioni precedenti. Su `anthropics/claude-code` i 74 commit in finestra sono
quasi tutti `actions-user` con messaggio `chore: Update mods/`: rumore, ma indica che i
mod built-in vengono aggiornati di continuo (questa settimana e' uscito `easel`).

Il 19/10/2026 il doppio controllo e' stato **negativo da entrambe le parti**:
`track_mp_skills.py` dava ancora 1.3.1 e `search_commits` con
`repo:mattpocock/skills committer-date:>2026-10-12` restituiva `total_count: 0`.
In quel caso la voce si omette davvero (come il 28/09). Idem per
`repo:obra/superpowers`: zero commit in finestra.

## Prima di tutto: il branch con cui parte il container

**Verificato il 05/10/2026, riconfermato il 12/10/2026, il 19/10/2026 e il
09/11/2026 — leggere prima di concludere che il repo è vuoto.** Il 12/10 il container è partito su
`claude/sleepy-curie-u9hdup` e il 19/10 su `claude/sleepy-curie-iy548q`, ogni volta
con solo `README.md`: stessa situazione, stessa contromisura, e lo stato era
intatto su `claude/blissful-ptolemy-zkpqg5`. A questo punto è il caso **normale**:
il primo comando dell'esecuzione è il `fetch` + `checkout -B` qui sotto.

**Attenzione a un branch fratello con stato vecchio.** Il 19/10 `git fetch --prune`
ha portato anche `claude/sleepy-curie-7dsddi`, che contiene uno scaffolding
**completo ma fermo al 28/09/2026** (gli manca cioè la memoria di tre esecuzioni).
Non è il branch buono: la discriminante è il `git log`, dove
`claude/blissful-ptolemy-zkpqg5` ha il commit più recente. Pushare su quell'altro
forkerebbe la memoria.

### Il guasto si è verificato davvero: il fork del 26/10/2026

**Questa è la prova che il rischio non è teorico.** L'esecuzione del 26/10/2026 non
ha trovato lo stato, **ha ignorato questa procedura e ha ricostruito lo scaffolding
da zero** su `claude/sleepy-curie-a758cj`, un ramo che parte direttamente da
`Initial commit`. Conseguenza misurata il 02/11: quel digest ha rimandato
**`agnix`** e **`Claude Code Infrastructure Showcase`** (già inviate il 24/08) e i
post aihero **`how-to-kill-the-bloat`** e **`skills-writing-for-agents`** (già
inviati il 31/08). Su 5 voci, 4 erano duplicati. L'unica nuova era **PLUR**.

Si riconosce il fork da due segni: i ledger hanno **header diversi**
(`id,nome,url,data_invio,sezione` invece di `ID,Display Name,Link,Category,Data
Invio,Note`) e lo stato Matt Pocock sta in `state/mp-skills-releases.json` invece
di `state/mattpocock-skills-version.txt`. Se li vedi, sei su un ramo ricostruito,
non sul ramo buono.

Il 02/11/2026 i due rami sono stati **riuniti**: ripartendo da
`claude/blissful-ptolemy-zkpqg5` e recuperando nel ledger canonico la sola voce
legittima del fork (PLUR, `aa6f21d6`, con nota di provenienza). Serviva davvero:
`pick_skills.py` stava per riproporre PLUR quella stessa settimana.

**Quindi, prima di qualunque altra cosa**: fare il `fetch` + `checkout -B` qui
sotto, e se il working tree ha solo `README.md` **non ricostruire niente** —
cercare il ramo con il `git log` più recente fra quelli che
`mcp__github__list_branches` elenca. Prima di scegliere le skill, controllare
sempre che il ledger contenga le voci dell'esecuzione precedente: se l'ultima
`Data Invio` non è di sette giorni fa, un'esecuzione è andata a vuoto e il suo
record va recuperato dal ramo su cui è finita.

Il container della routine **non** parte necessariamente sul branch che contiene
lo stato. Il 05/10/2026 la sessione è partita con un working tree su
`claude/sleepy-curie-m3ubhp` che conteneva **solo `README.md`**: niente
`ROUTINE.md`, niente `scripts/`, niente `state/`. Il clone iniziale aveva fetchato
solo `main` e quel branch, e nessuno dei due ha lo scaffolding.

Non è una perdita di memoria: lo stato è tutto su `claude/blissful-ptolemy-zkpqg5`,
che semplicemente non era stato fetchato. La contromisura, come primo passo
assoluto:

```bash
git fetch origin claude/blissful-ptolemy-zkpqg5
git checkout -B claude/blissful-ptolemy-zkpqg5 origin/claude/blissful-ptolemy-zkpqg5
```

### 09/11/2026 — procedura applicata, e il vincolo sul branch designato

Il container e' partito su `claude/sleepy-curie-uon05v` con **solo `README.md`**,
esattamente come documentato. Due cose utili per la prossima volta:

1. **`git ls-remote --heads origin` basta e costa meno** di
   `mcp__github__list_branches`: elenca tutti i branch veri con il loro SHA, e si
   vede subito quali condividono lo stesso commit. Il 09/11 ha mostrato
   `claude/blissful-ptolemy-zkpqg5` e `claude/sleepy-curie-2ov84j` sullo **stesso**
   SHA (`2d8fa24`), cioe' la riunificazione del 02/11 era stata pushata su entrambi.
2. **Il branch designato era un discendente, non un fork.** `3cd3f37` (Initial
   commit, su cui parte il branch designato) e' antenato di `2d8fa24`, quindi
   `git merge --ff-only 2d8fa24` ha portato lo stato **in fast-forward**, senza
   merge e senza force. E' la mossa giusta quando il branch designato dalla
   sessione e' ancora vergine.

### 16/11/2026 — stessa procedura, caso piu' semplice di tutti

Il container e' partito su `claude/sleepy-curie-2230ih` con **solo `README.md`**, con
`main` fermo a `Initial commit`: il caso normale, per la quinta volta documentata.
`git fetch origin 'refs/heads/*:refs/remotes/origin/*' --prune` in un colpo ha portato
tutti i rami (sei, piu' `main`) e il `git log` ha mostrato subito il ramo buono
(`claude/blissful-ptolemy-zkpqg5`, commit `67de414` del 09/11). Lo scaffolding era
intatto e i ledger contenevano le voci del 09/11, quindi nessun recupero da fare.
Un `checkout -B` sul ramo remoto e via. Nota: fare il fetch con il refspec completo
e' meglio che `git fetch origin <branch>`, perche' fa vedere in un colpo *tutti* i
rami fratelli e quindi quale ha il log piu' recente.

### 23/11/2026 — sesta volta, e un dettaglio nuovo sul fetch

Il container e' partito su `claude/sleepy-curie-dp2clr` con **solo `README.md`** e `main`
fermo a `Initial commit`: il caso normale, sesta volta documentata. Due note:

- `git fetch origin --prune` **senza refspec** ha portato comunque tutti i rami fratelli
  (cinque `claude/sleepy-curie-*` nuovi), quindi il refspec completo del 16/11 non e'
  indispensabile; quello che conta davvero e' `git ls-remote --heads origin`, che ha
  mostrato subito `claude/blissful-ptolemy-zkpqg5` e `claude/sleepy-curie-2230ih` sullo
  **stesso** SHA (`93c2b87`) — cioe' il doppio push del 16/11 aveva funzionato.
- I ledger contenevano le voci del 16/11 (ultima `Data Invio` esattamente di sette giorni
  prima): nessun recupero da fare, nessuna esecuzione andata a vuoto.

**Il conflitto fra "branch designato" e "branch della memoria", e come si risolve.**
Le istruzioni di sistema della sessione impongono di sviluppare e pushare su un
branch designato (`claude/sleepy-curie-*`, diverso a ogni esecuzione); il prompt
della routine impone `claude/blissful-ptolemy-zkpqg5`. Non e' una scelta fra i due:
si pusha lo **stesso commit su entrambi**. Cosi' la memoria canonica resta dove la
routine la cerca e il vincolo della sessione e' rispettato, senza forkare niente —
i due riferimenti puntano allo stesso oggetto. E' quello che e' stato fatto il
09/11. **Non** scegliere solo il branch designato: la settimana dopo la memoria
sarebbe su un ramo che nessuno cerca, ed e' il guasto del 26/10.

`mcp__github__list_branches` sul repo elenca i branch veri e serve per
riconoscere la situazione. **Non ricostruire lo scaffolding da zero** e **non
pushare lo stato su un branch diverso**: forkerebbe la memoria e la settimana
dopo la routine riproporrebbe le stesse skill, che è esattamente il guasto che
questo repo esiste per prevenire.

## Limiti dell'ambiente (verificati il 24/08/2026)

0. **La classificazione di sicurezza di auto mode può andare in timeout** e
   bloccare temporaneamente il tool Bash (`claude-sonnet-5[1m] is temporarily
   unavailable`). Capitato più volte il 05/10/2026. I tool di sola lettura e
   `Read`/`Edit`/`Write` continuano a funzionare: conviene proseguire con quelli
   e riprovare Bash dopo qualche chiamata, invece di fermarsi. Gli script Python
   però girano **solo** da Bash, quindi i passi 0b/1c/1d e il push vanno
   semplicemente ritentati.

1. **Il blog si e' spostato su `claude.dev`, che e' BLOCCATO (12/10/2026).**
   L'indice `https://claude.com/blog` risponde ancora 200, ma gli `href` dei post
   puntano a `https://claude.dev/blog/<slug>`:

   | Percorso | Esito (12/10/2026) |
   | --- | --- |
   | `claude.com/blog` (indice) | 200, utile solo per scoprire gli slug |
   | `claude.com/blog/<slug>` | **404** — i vecchi URL non servono piu' i post |
   | `claude.dev/blog/<slug>` via `urllib` | **403 Tunnel connection failed** |
   | `claude.dev/...` via `WebFetch` | `getaddrinfo ENOTFOUND claude.dev` |

   **02/11/2026 — l'indice non espone piu' NIENTE.** La regex
   `r'https://claude\.dev/blog/([a-z0-9\-]+)/?'` sull'indice restituisce **zero**
   slug (il 19/10 erano tre), e anche `href="/blog/<slug>"` da' zero. `claude.dev`
   resta irraggiungibile (`URLError` via `urllib`). **Riconfermato il 09/11/2026**:
   zero slug da entrambe le regex, e `claude.dev` da' `Tunnel connection failed:
   403 Forbidden`. Due esecuzioni di fila con l'indice completamente muto: la
   fonte e' da considerare **morta**, non parziale, finche' non cambia qualcosa.
   **Terza conferma il 16/11/2026**: `claude.com/blog` risponde 200 e serve 570 KB,
   ma **zero** slug da entrambe le regex, e `claude.dev/blog` da' ancora
   `Tunnel connection failed: 403 Forbidden`. Tre esecuzioni di fila: non vale piu'
   spenderci piu' di una sonda, basta la riga di copertura parziale.
   La sonda di `check_sources.py`
   continua a dare **OK** perche' interroga `claude.com/blog`, che risponde 200 e
   serve la pagina: e' il falso OK gia' documentato, ora al suo massimo. Questa
   fonte e' **non contribuente** e la via "indice + WebSearch sullo slug" non ha
   nemmeno piu' uno slug da cui partire: niente da tentare, solo la nota in fondo
   alla mail.

   **23/11/2026 — IL BLOG E' TORNATO UTILIZZABILE, e serve un percorso nuovo.**
   Dopo tre settimane di indice completamente muto, `claude.com/blog` espone di nuovo
   contenuto. Ma **non** nel modo documentato sopra: la regex sugli `href` da' solo
   **2** slug, mentre nell'HTML ci sono **13 occorrenze di data** con il titolo
   accanto. Il percorso che funziona e' **associare ogni data al testo che la
   precede**, non cercare gli `href`:

   ```python
   h = urllib.request.urlopen(...("https://claude.com/blog")).read().decode()
   for m in re.finditer(r'[A-Z][a-z]{2,8} \d{1,2}, 2026', h):
       seg = h[max(0,m.start()-1500):m.start()+600]
       titolo = re.findall(r'>([A-Z][^<>{}]{18,120})<', seg)[-1]   # il piu' vicino
   ```

   Il 23/11 ha restituito 12 post datati fra il 10/11 e il 17/11, con i titoli
   corretti e **date affidabili** (verificate incrociando due fonti secondarie sui
   due post in finestra). Due erano in finestra e pertinenti al profilo:
   *How the Claude Code team thinks about verification* (16/11) e *Using a "chaos
   loop" to harden the Claude Docs launch* (17/11); gli altri erano billing,
   Claude Meetings, Manufacturing, J. Crew — da scartare.

   **Quello che resta rotto: leggere il post.** I link puntano a
   `claude.dev/blog/<slug>`, che da' ancora `Tunnel connection failed: 403`, e
   `claude.com/blog/<slug>` da' 404 **per i post nuovi**. Per i post vecchi invece
   risponde 200: il 23/11
   `claude.com/blog/building-verification-loops-in-claude-code-with-skills` era
   leggibile. Quindi la regola del 19/10 ("i post vecchi restano su claude.com")
   vale ancora e torna utile come link di sfondo.

   **Procedura da ora:** prendere titoli e date dall'indice col metodo
   data-vicino-al-titolo, filtrare sul profilo, e per il *contenuto* ripiegare su
   `WebSearch` sul titolo. Il 23/11 `WebSearch` sui due titoli ha dato riassunti
   di terze parti utilizzabili **e** la data (16/11 e 17/11), confermando quella
   dell'indice. In mail: linkare la URL canonica `claude.dev/blog/<slug>` — all'utente
   si apre — e **dire in chiaro che la pagina non e' stata letta** e che i dettagli
   vengono dall'indice e da fonti secondarie. Non spacciare un riassunto di terze
   parti per lettura diretta.
   Nota: `claude.com/blog/category/<nome>` serve lo **stesso** HTML dell'indice
   (stessa lunghezza byte per byte), quindi non aggiunge niente: e' un'app JS.
   **Questa fonte va da "morta" a "parziale"**: il flag `expected` in
   `check_sources.py` resta a `True` e il suo OK ora e' meno falso di prima.

   **19/10/2026 — l'indice espone pochissimo.** Cercare `href="/blog/<slug>"` sull'indice
   restituisce ora **zero** slug: gli unici link ai post sono assoluti verso
   `https://claude.dev/blog/<slug>/` e sono soltanto **tre** card "Developer blog"
   (`solving-code-review-at-anthropic`, `building-effective-agent-automations`,
   `automating-eval-design-and-hillclimbing`). Regex da usare:
   `r'https://claude\.dev/blog/([a-z0-9\-]+)/?'`. `WebSearch` sullo slug **non**
   ha dato la data per nessuno dei tre (restituisce post omonimi diversi), quindi
   la finestra di 7 giorni non e' applicabile e le voci si omettono, dicendolo in
   fondo alla mail. Finche' `claude.dev` resta bloccato questa fonte e' di fatto
   **non contribuente**, come `whats-new`.

   Quindi la procedura "indice + GET per slug" descritta sotto **non funziona piu'**:
   resta valida solo per scoprire gli slug. Finche' `claude.dev` e' bloccato il
   ripiego e' `WebSearch` sullo slug per ricavare la data, dicendo in fondo alla mail
   che la copertura del blog e' parziale. Il 12/10 l'unico slug nuovo e rilevante
   (`getting-started-with-claude-code-mods`) e' risultato del **1 ottobre**, fuori
   finestra: nessuna voce persa, ma va riverificato ogni settimana.

   Storia precedente (quando i post stavano su `claude.com`): si leggevano
   direttamente, senza bisogno di `WebSearch`. `WebFetch` funziona
   sui singoli post. L'indice `https://claude.com/blog` va preso con `urllib` e
   parsato: le date sono in chiaro nel formato `August 20, 2026`, vicine
   all'`href` del post.

   **Ma le date dell'indice non sono affidabili, e nemmeno quelle di `WebFetch`.**
   Verificato il 21/09/2026: associare a un `href` la data più vicina nell'HTML
   dell'indice ha datato `artifacts-in-claude-code` al 15/09 (vera: 18/06),
   `claude-managed-agents-memory` al 16/09 (vera: 23/04) e
   `connectors-for-everyday-life` al 16/09 (vera: 23/04) — le card dell'indice
   non hanno una data ciascuna, quindi la prossimità pesca quella di un'altra.
   `WebFetch` sul singolo post restituisce una data ma la sbaglia altrettanto
   spesso (stesso riassuntore del problema GitHub, punto 4).

   **Procedura**: usare l'indice solo per scoprire gli slug, poi per ognuno fare
   una GET con `urllib` su `https://claude.com/blog/<slug>` e prendere la data
   dal testo della pagina (`Month D, YYYY`). Solo quella regge la finestra di 7
   giorni. Il 21/09 su 10 candidati dell'indice ne sono sopravvissuti 3.
2. **`api.github.com` è ristretto allo scope del repo** per i tool che leggono un
   repo specifico (`list_releases`, `get_file_contents`, …): su repo di terzi
   rispondono "access to this repository is not enabled for this session".
   **Ma gli endpoint di ricerca non sono ristretti**: `search_repositories` e
   `search_commits` funzionano su tutto GitHub e restituiscono conteggi stelle e
   date affidabili. Usare quelli.
   - novità della settimana in un repo della watchlist:
     `search_commits` con `repo:owner/name committer-date:>AAAA-MM-GG`
   - repo nuovi: `search_repositories` con `created:>AAAA-MM-GG`, `sort=stars`

   Nota pratica (19/10/2026): `search_repositories` con `minimal_output=false`
   restituisce ~112 KB e **sfonda il limite di token** del tool, costringendo a
   rileggere il risultato da file. Usare sempre `minimal_output=true` e
   `perPage` ≤ 20; i campi che servono (`stargazers_count`, `created_at`,
   `description`, `topics`) ci sono comunque.
3. **`github.com` in HTML è bloccato** (HTTP 403), incluse le pagine
   `/releases`, `/commits` e i feed `.atom`. `raw.githubusercontent.com`
   funziona: usarlo per i file grezzi (CHANGELOG, README, CSV).
4. **`WebFetch` su pagine GitHub sbaglia i numeri.** Le pagine HTML passano da un
   modello riassuntore che ha restituito valori palesemente falsi (es. "242k
   stars" e "234.5k stars" per repo che non li hanno). **Non citare mai un
   conteggio stelle preso da `WebFetch`.** Prenderli da `search_repositories`
   (campo `stargazers_count`), che viene dall'API vera.
4b. **Il volume del changelog puo' essere enorme: filtrare per keyword, non leggere tutto.**
   Il 23/11/2026 la finestra conteneva **cinque** release (2.1.326...2.1.330) per **956**
   voci totali, di cui 367 nella sola 2.1.326 — troppo per leggerle a mano e troppo per
   stamparle tutte. Lo script che ha funzionato: estrarre i `<li>` come da punto 5 e
   filtrare con una regex sul profilo
   (`skill|hook|rule|MCP|connector|memory|CLAUDE\.md|routine|scheduled task|slash
   command|plugin|marketplace|subagent|mod|brain|knowledge`), che ha ridotto 956 a **260**
   voci pertinenti — leggibili. Il rapporto e' stabile intorno al 25-30%.
   Secondo accorgimento: interrompere il ciclo sul **primo** blocco con data fuori
   finestra, e in una passata separata stampare solo `versione | data | n. voci` per le
   prime 10-12 release, cosi' si sa subito quante release copre la finestra.
   **Terzo, importante: controllare con quale release si era chiuso il digest precedente.**
   Il 23/11 la release 2.1.326 e' del **16/11**, cioe' lo stesso giorno dell'esecuzione
   precedente: per sapere se era gia' stata coperta e' bastato leggere la mail del 16/11
   via `mcp__Gmail__search_threads` + `get_message` (diceva «433 voci in quattro release»,
   quindi si fermava a 2.1.325). **Rileggere la mail della settimana prima e' il modo
   piu' economico di evitare i doppioni al bordo della finestra**, e serve anche a non
   ripetere le stesse formule.

5. **Il `CHANGELOG.md` grezzo non ha date, la pagina docs sì.**
   `raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md` elenca le
   versioni ma non quando sono uscite: da solo non permette di applicare la
   finestra di 7 giorni. Le date stanno nella pagina docs, presa con `urllib`:
   ogni release è un blocco che si apre con `<div class="update flex flex-col
   relative`, con la versione in `data-component-part="update-label"` e la data
   (`September 4, 2026`) in `data-component-part="update-description"`.

   ```python
   blocks = re.split(r'<div class="update flex flex-col relative', html)
   # per ogni blocco: update-label -> versione, update-description -> data,
   # poi da html.find('data-component-part="update-content"') in poi, i <li>
   ```

   Attenzione: la regex "chiusa" sul div di `update-content` **non matcha** (ci
   sono div annidati). Prendere dal `find` fino a fine blocco e raccogliere i
   `<li>`, altrimenti si ottengono zero voci senza errore.

   Le ancore `#2-1-261` funzionano: usarle per linkare la singola release.

6. **Le pagine `whats-new/AAAA-wNN` escono in ritardo, e non solo di un giorno.**
   Il 24/08/2026 (lunedì, ISO week 35) `2026-w35` dava 404 e la pagina buona era
   `2026-w34`. Il 31/08/2026 (lunedì, ISO week 36) `2026-w35` dava **ancora** 404,
   pur essendo la settimana conclusa da giorni: l'indice si fermava anch'esso alla
   week 34. Quindi non basta scalare di una settimana.
   Il 07/09/2026 (ISO week 37) l'indice era **ancora fermo a `2026-w34`**: tre
   settimane di ritardo, e la fonte non ha contribuito per la terza esecuzione
   consecutiva. Il 14/09/2026 (ISO week 38) l'indice era **sempre a `2026-w34`**:
   quarta esecuzione consecutiva senza contributo, e il ritardo cresce di una
   settimana a ogni giro.
   Il 21/09/2026 (ISO week 39) l'indice si e' **sbloccato**: elenca fino a
   `2026-w37` (recuperando in un colpo w35, w36 e w37 — nota che `2026-w31` resta
   mancante). Ma il ritardo strutturale non e' sparito: `2026-w38`, cioe' la
   settimana effettivamente coperta dal digest, dava **404**. Quinta esecuzione
   consecutiva senza contributo.
   Il 28/09/2026 (ISO week 40) l'indice era **di nuovo fermo a `2026-w37`**: lo
   sblocco della settimana prima non e' diventato una cadenza. `2026-w39` (la
   settimana coperta) e `2026-w40` davano entrambe 404. Sesta esecuzione
   consecutiva senza contributo.
   Il 05/10/2026 (ISO week 41) l'indice era **ancora fermo a `2026-w37`**, con
   `2026-w39`, `2026-w40` e `2026-w41` tutte a 404. Settima esecuzione
   consecutiva senza contributo, e il ritardo e' tornato a crescere di una
   settimana a ogni giro. L'indice completo elencato: w29, w30, w32, w33, w34,
   w35, w36, w37 (restano mancanti w31 e tutto da w38 in avanti).
   A questo punto il trattamento ragionevole e' considerare questa fonte
   **strutturalmente non contribuente** e non spenderci piu' di una sonda:
   controllarla in un colpo, annotarlo in fondo alla mail, e prendere tutta la
   sostanza dal changelog grezzo.
   Il 12/10/2026 (ISO week 42) l'indice era **ancora fermo a `2026-w37`**, con
   `2026-w40`, `2026-w41` e `2026-w42` tutte a 404: ottava esecuzione consecutiva
   senza contributo. L'indice ora elenca anche le settimane vecchie (da w13 a w37,
   senza w31), ma nulla dopo w37. La sonda singola e la nota in fondo alla mail
   restano il trattamento giusto.
   Il 19/10/2026 (ISO week 43) l'indice era **ancora fermo a `2026-w37`**, con
   `2026-w40`, `2026-w41`, `2026-w42` e `2026-w43` tutte a 404: nona esecuzione
   consecutiva senza contributo. Trattamento invariato: una sonda sola e la nota
   in fondo alla mail.
   Il 02/11/2026 (ISO week 45) l'indice era **ancora fermo a `2026-w37`**, con
   `2026-w41`, `2026-w42`, `2026-w43`, `2026-w44` e `2026-w45` tutte a 404: **decima**
   esecuzione consecutiva senza contributo. Trattamento invariato.
   Il 09/11/2026 (ISO week 46) idem: indice **sempre a `2026-w37`** (elenca w13-w37
   senza w31), e `2026-w42`...`2026-w46` tutte a 404. **Undicesima** esecuzione
   consecutiva senza contributo. Undici settimane sono una prova sufficiente: non
   vale piu' nemmeno scrivere in mail *perche'* non contribuisce, basta la riga di
   copertura parziale.
   Il 16/11/2026 (ISO week 47) idem: indice **sempre a `2026-w37`** (24 settimane
   elencate, da w13 a w37 senza w31), e `2026-w43`...`2026-w47` tutte a 404.
   **Dodicesima** esecuzione consecutiva senza contributo. Trattamento invariato:
   una sonda sola e una riga di copertura parziale in fondo alla mail.
   Il 23/11/2026 (ISO week 48) idem: indice **sempre a `2026-w37`** (24 settimane,
   w13-w37 senza w31), e `2026-w44`...`2026-w48` tutte a 404. **Tredicesima**
   esecuzione consecutiva senza contributo. Trattamento invariato: una sonda sola
   e una riga di copertura parziale in fondo alla mail.
   Morale invariata: la pagina della settimana corrente non c'e' quasi mai.
   Controllarla, ma ricavare la sostanza dal changelog grezzo, che e' completo e
   datato.
   **Procedura**: leggere l'indice `https://code.claude.com/docs/en/whats-new` e
   prendere la settimana più recente che l'indice stesso elenca. Se è già stata
   coperta nel digest precedente, la fonte non contribuisce: dirlo in fondo alla
   mail e ricavare la sostanza dal changelog grezzo.
   Nota: `check_sources.py` sonda l'indice, non la pagina della settimana, quindi
   un "OK" su questa fonte **non** garantisce che la pagina settimanale esista.

## Prompt della routine

Il prompt vive nella configurazione della routine su Claude Code web, non in
questo repo: va aggiornato da lì. Testo corrente in `prompt-routine.md`.
