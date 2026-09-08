# Phase 1 + 2 — fertig

Generiert und geprüft. Alle Dateien gehören in die gleichnamigen Pfade des Forks.

## Neue Dateien

| Datei | Was |
|---|---|
| `types.h` | **generiert** — 15 Gen-1-Typen, Wirksamkeitstabelle, Akzentfarben, Namen in 6 Sprachen |
| `moves.h` | **generiert** — 103 Attacken, Movepools aller 151, Helfer für Slots und Level-up |
| `dex.h` | **neu generiert** — `DexEntry` hat jetzt `type1`/`type2`, Akzentfarbe kommt aus dem echten Typ |
| `tools/type_chart.py` | von Hand — Gen-1-Tabelle, Farben, Typnamen |
| `tools/gen_type_data.py` | zieht Typen von PokéAPI → `tools/type_data.py` |
| `tools/gen_types.py` | → `types.h` |
| `tools/gen_move_data.py` | zieht Attacken + Movepools → `tools/move_data.py`, `tools/move_names.py` |
| `tools/gen_moves.py` | → `moves.h` |
| `tools/gen_dex.py` | **gepatcht** — gibt die zwei neuen Felder aus |

Neu erzeugen mit:

```
python3 tools/gen_type_data.py && python3 tools/gen_types.py
python3 tools/gen_move_data.py && python3 tools/gen_moves.py
python3 tools/gen_dex.py
```

Antworten von PokéAPI werden in `tools/.pokeapi/` gecacht (nicht committen).

## Was beim Bauen aufgefallen ist

**PokéAPI liefert moderne Daten, nicht Gen 1.** Piepi und Pixi wären sonst
Feen-Typ geworden — es gibt 15 Typen in Gen 1, keine 18. Wird über
`past_types` bzw. `past_values` korrigiert.

**Vier Spezies haben in Gen 1 keine einzige Angriffsattacke:** Safcon, Kokuna,
Abra und Ditto lernen nur Härtner, Teleport bzw. Wandler. Gelöst wie im
Original: **Verzweifler** (Move-ID 1, `MOVE_STRUGGLE`) ist immer verfügbar und
greift auch, wenn alle AP leer sind.

**Fixschaden-Attacken fielen durchs Raster.** Drachenwut, Nachtnebel,
Sternenlicht und Psywelle haben bei PokéAPI Stärke 0. Ohne sie hätte der
Drachen-Typ **null** Attacken gehabt. Sind jetzt mit passender Stärke drin
(`POWER_OVERRIDE`), weil die Engine keinen Fixschaden kennt und auch nicht
braucht.

**Entwicklungen erben den Movepool.** `movesForLevel()` läuft die
Entwicklungskette rückwärts — sonst stünde Dragoran ohne Drachenattacke da,
weil es Drachenwut nur als Dratini lernt.

**STAB-Garantie.** Wer per Level-up keine Attacke des eigenen Typs lernt,
bekommt die beste TM seines Typs auf Level 1 geschenkt — so wie man es in einer
echten Partie auch machen würde. Betrifft 10 Spezies (Voltobal, Sandan, Abra…).
Übrig bleiben 8 ohne STAB, und das ist echte Gen-1-Realität: **Gen 1 hat keine
einzige Käfer-TM** (Raupy, Smettbo, Sichlor, Pinsir), Karpador lernt gar nichts,
und Enton bekommt seine Hydropumpe erst auf Level 52.

**Geist gegen Psycho ist gefixt.** `#define GEN1_GHOST_BUG 0` in `types.h`
auf `1` setzen, wenn du den historischen Bug willst.

## Geprüft

- Zehn bekannte Typen-Paarungen gegen die Gen-1-Tabelle: alle korrekt,
  inklusive Käfer→Gift = 2× (in Gen 1 anders herum als heute)
- Alle 151 Spezies haben auf jedem Level mindestens eine benutzbare Attacke
- Doppeltypen: 62 Spezies, stichprobenartig gegen Gen 1 verglichen
- Flash-Bedarf zusammen rund **9 KB** von 3 MB — kein Thema

## Noch offen

`i18n.cpp` braucht noch die Kampf-Strings (`SEHR EFFEKTIV!` usw.) in allen
sechs Sprachen. Typ- und Attackennamen laufen bereits über eigene Tabellen in
`types.h` und `moves.h`, nicht über `i18n.cpp`.
