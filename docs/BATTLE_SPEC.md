# TamaPoke — Kampfsystem

Spezifikation für die Implementierung durch einen Coding-Agenten.
Basis: `socquique/TamaPoke` v1.2, Gen 1 (151 Spezies). Version 2 der Spezifikation.

---

## 1. Ziel

Das Spiel ist aktuell ein reines Pflege-Tamagotchi. Level steigen automatisch mit
der Zeit, alle 60 Minuten eines. Diese Spezifikation macht aus dem Levelaufstieg
etwas, das man sich erkämpfen muss, und gibt dem Spieler einen Grund, das Gerät
aktiv in die Hand zu nehmen statt nur zu füttern.

### Im Umfang

- Rundenbasiertes Kampfsystem mit Attacken, Typen und Schadensberechnung
- Skalierende Levelkurve statt flacher Stunde pro Level
- Levelaufstieg nur nach gewonnenem Kampf
- Freie Kämpfe jederzeit, die XP auf das nächste Level einzahlen
- Rivale: das eigene vorherige Pokémon kehrt als Gegner zurück
- Bindung, Lieblingsbeere, Tageszeit und Shiny-Gegner als Kampfmechaniken
- Arena-Ladder mit Trainerrang als Endgame
- Deutsch als Standardsprache

### Nicht im Umfang

- LAN-/Funkkämpfe — kein WiFi im Projekt, bewusst gestrichen
- Generationen jenseits Gen 1 — alle 151 sind bereits implementiert
- Neue Sprites — das PMD-Set ist vollständig, inklusive `Attack` und `Hurt`
- Fangen, Party, Box, EV/IV

---

## 2. Ausgangslage im Code

Was wiederverwendet wird:

| Vorhanden | Ort | Nutzung im Kampf |
|---|---|---|
| ATK / DEF / SPD inkl. Gene und Training | `pet.cpp`, `atkStat()` etc. | Kampfwerte des Spielers |
| Basiswerte Gen 1 inkl. HP | `dex.h`, `DEX_TBL[].bHp` | Gegnerwerte |
| Biome pro Spezies | `dex.h`, `DEX_TBL[].biome` | Auswahl wilder Gegner |
| Echte Tageszeit aus dem RTC | `render()`, `gNight` | Auswahl wilder Gegner |
| Bindung 0–100, Tageslimit +20 | `pet.cpp`, `bond` | Schadensbonus, K.-o.-Rettung |
| Versteckte Lieblingsbeere | `pet.h`, `lovesBerry()`, `berryKnown` | Heilung im Kampf |
| `Attack`- und `Hurt`-Animation | `sdmon.h`, `PmdMon::has()` | Kampfanimation |
| Sechs Sprachen inkl. Deutsch | `i18n.cpp`, `LANG_DE` | Attackennamen, Kampftexte |
| Serielle Testkonsole | `TamaPoke.ino` | Headless-Tests |
| Tonsynth | `audio.cpp`, `sfxPlay()` | Treffer, Sieg, Niederlage |
| Medaillen-Bitmask (uint16, 8 belegt) | `pet.h` | drei neue Medaillen |

Was fehlt:

- **Typen.** `dex_data.py` speichert genau *einen* Typ pro Spezies, und zwar nur
  als UI-Akzentfarbe. Die Liste `TYPE_ACCENTS` hat 14 Einträge — **Flug fehlt
  komplett**. Doppeltypen gibt es nicht. Muss aus PokéAPI neu gezogen werden.
- **Attacken.** Kein Movepool, keine AP, keine Stärkewerte.
- **HP im Kampf.** `bHp` steht in der Tabelle, wird nirgends benutzt.
- **Gegnerinstanz.** Es existiert nur ein einziges Pokémon im Speicher.

---

## 3. Levelkurve

### 3.1 Warum nicht die echte Pokémon-Kurve

Zur Dokumentation der Entscheidung: die Medium-Fast-Kurve (`n³`), normiert auf
eine Stunde für Level 1 → 2, ergibt **24 Tage bis zur ersten Entwicklung auf
Level 16**, neun Monate bis Level 36 und **5,8 Monate für den Schritt von 99 auf
100**. Insgesamt 16 Jahre bis Level 100. In echten Pokémon-Spielen funktioniert
das, weil ein einzelner Kampf hunderte EXP gibt — hier ist Zeit die Währung, und
die skaliert nicht mit.

Übernommen wird die *Form* der Kurve, nicht ihre Steilheit.

### 3.2 Die Kurve

```
LVL_REQ[n] = 60 + (n - 1) * 5      // Minuten von Level n auf n+1, n = 1..99
```

Als generierte Tabelle `uint16_t LVL_REQ[100]` in `levels.h`, Werte 60 bis 550,
200 Byte Flash. **Keine Fließkommaberechnung auf dem Target.**

| Level | Schritt | Gesamt ab Level 1 |
|---|---|---|
| 2 | 1,0 h | 1 h |
| 16 (1. Entwicklung) | 2,2 h | 23,8 h |
| 36 (2. Entwicklung) | 3,8 h | 3,5 Tage |
| 50 (Medaille) | 5,0 h | 6,1 Tage |
| 100 (Cap) | 9,2 h | 21,0 Tage |

**Levelobergrenze ist 100.** Bei 100 friert `xpMinutes` ein, es gibt keine
Levelkämpfe mehr, freie Kämpfe geben weiter Trainingspunkte.

### 3.3 Folge für den Abschied — muss mitgeändert werden

Der Abschied verlangt heute Endstufe **und** drei Tage Gesamtalter. Mit der neuen
Kurve wird die Endstufe erst nach 3,5 Tagen erreicht — der Abschiedsbutton
erschiene also praktisch im selben Moment wie die letzte Entwicklung, ohne
Endgame-Fenster.

Neue Bedingung: **Endstufe seit mindestens einem Tag.** Neues Feld
`uint32_t finalFormAt` (Wert von `ageMinutes` beim Erreichen der Endstufe),
Prüfung `ageMinutes - finalFormAt >= 1440`. Damit bekommt jedes Pokémon seine
Abschiedsphase, unabhängig davon, wie schnell es dort angekommen ist.

**`finalFormAt` muss auch beim Schlüpfen gesetzt werden, nicht nur beim
Entwickeln.** 25 der 151 Spezies haben überhaupt keine Entwicklung und
schlüpfen direkt in ihre Endstufe:

> Porenta, Onix, Kicklee, Nockchan, Schlurp, Chaneira, Tangela, Kangama,
> Pantimos, Sichlor, Rossana, Elektek, Magmar, Pinsir, Tauros, Lapras, Ditto,
> Porygon, Aerodactyl, Relaxo — dazu die fünf Legendären Arktos, Zapdos,
> Lavados, Mewtu und Mew, die zwar nicht als wilde Gegner auftreten, aber aus
> einem Ei schlüpfen können.

Wird das Feld nur in `evolve()` gefüllt, bleibt es bei diesen 25 für immer 0,
die Prüfung greift nie und **sie können sich nie verabschieden**. Der
Lebenszyklus bräche für ein Sechstel des Dex still ab.

Also: in `hatch()` prüfen, ob `DEX_TBL[speciesId].evolvesTo == 0`, und dann
`finalFormAt = ageMinutes` setzen. Dasselbe gilt für die Migration aus 5.4 —
ein alter Spielstand, der bereits in der Endstufe steht, bekommt
`finalFormAt = ageMinutes`, sonst verliert er sein Abschiedsfenster.

---

## 4. Levelaufstieg durch Kampf

### 4.1 Das Problem mit der naiven Lösung

`level()` ist heute eine reine Funktion der Zeit:

```c
uint8_t level() const { return 1 + ageMinutes / MINUTES_PER_LEVEL; }
```

`ageMinutes` treibt aber **nicht nur** das Level, sondern auch den Statusverfall,
den Kack-Rhythmus, die Gewichtsverbrennung, das Schlüpfen und den Lebenszyklus.
Wer `ageMinutes` anhält, friert das komplette Spiel ein.

### 4.2 Lösung: zwei Zähler

`ageMinutes` läuft **unverändert weiter**. Daneben neu:

```c
uint8_t level() const { return 1 + levelsWon; }
uint16_t lvlReq() const { return level() >= 100 ? 0xFFFF : LVL_REQ[level()]; }
bool levelPending() const { return xpMinutes >= lvlReq(); }
```

- `xpMinutes` zählt pro Spielminute um 1 hoch und **stoppt bei `lvlReq()`**.
  Kein Banking, keine Warteschlange — immer genau eine offene Stufe.
- Ist die Grenze erreicht, erscheint der Kampfbutton. Der nächste gewonnene
  Kampf ist der Levelkampf: `xpMinutes -= lvlReq()`, `levelsWon++`.
- Wer nie kämpft, bleibt auf Level 1. Sein Pokémon hungert, koddert und altert
  trotzdem. Der Druck kommt aus dem Pflegespiel, nicht aus einem Timer.

### 4.3 XP aus freien Kämpfen

Ist **kein** Level offen, zahlt jeder gewonnene Kampf direkt auf `xpMinutes` ein:

```c
xpGain = lvlReq() * 12 / 100;   // pauschal, unabhängig vom Gegnerlevel
```

Das sind rund **acht Kämpfe pro Level**. Damit ist aktives Spielen etwa zwei-
bis dreimal schneller als reines Warten, ohne das Warten wertlos zu machen.

*Entspannt (2026-10-11):* früher `12 + 4 · (Gegnerlevel − Spielerlevel)` %.
Seit wilde Gegner nie über dem Spieler stehen und die Mitleidsregel (§6.7)
Gegner abschwächt, hätte das das Leveln verlangsamt — deshalb pauschal.

Ist ein Level offen, gibt es keine XP mehr — der nächste Sieg *ist* der
Levelaufstieg. Kein Moduswechsel in der UI nötig.

### 4.4 Anzupassende Stellen

| Stelle | Änderung |
|---|---|
| `pet.h:121` `level()` | auf `levelsWon` umstellen |
| `pet.cpp:139` Levelsound | feuert beim Sieg, nicht beim Tick |
| `pet.cpp:349` Abschiedsbedingung | auf `finalFormAt` umstellen (3.3) |
| `TamaPoke.ino:1549` Fortschrittsbalken | `xpMinutes` gegen `lvlReq()` |
| `TamaPoke.ino:347` `LVL`-Konsolenbefehl | setzt `levelsWon` |
| Fortschrittsseite der Statuskarte | neuer Zustand „KAMPF BEREIT" |

---

## 5. Datenmodell

### 5.1 Typen (`tools/type_data.py` → `types.h`)

15 Gen-1-Typen: `NORMAL, KAMPF, FLUG, GIFT, BODEN, GESTEIN, KAEFER, GEIST, FEUER,
WASSER, PFLANZE, ELEKTRO, PSYCHO, EIS, DRACHE`.

Wirksamkeit als `uint8_t TYPE_CHART[15][15]`, kodiert `0 = 0×, 1 = ½×, 2 = 1×,
4 = 2×`. Anwendung als `(dmg * chart) / 2` in Integerarithmetik.

Gen-1-Chart, nur die Abweichungen von 1×:

```
NORMAL   → ½ GESTEIN                     | 0× GEIST
KAMPF    → 2× NORMAL, GESTEIN, EIS       | ½ FLUG, GIFT, KAEFER, PSYCHO | 0× GEIST
FLUG     → 2× KAMPF, KAEFER, PFLANZE     | ½ GESTEIN, ELEKTRO
GIFT     → 2× KAEFER, PFLANZE            | ½ GIFT, BODEN, GESTEIN, GEIST
BODEN    → 2× GIFT, GESTEIN, FEUER, ELEKTRO | ½ KAEFER, PFLANZE | 0× FLUG
GESTEIN  → 2× FLUG, KAEFER, FEUER, EIS   | ½ KAMPF, BODEN
KAEFER   → 2× GIFT, PFLANZE, PSYCHO      | ½ KAMPF, FLUG, GEIST, FEUER
GEIST    → 2× GEIST, PSYCHO              | 0× NORMAL
FEUER    → 2× KAEFER, PFLANZE, EIS       | ½ GESTEIN, FEUER, WASSER, DRACHE
WASSER   → 2× BODEN, GESTEIN, FEUER      | ½ WASSER, PFLANZE, DRACHE
PFLANZE  → 2× BODEN, GESTEIN, WASSER     | ½ FLUG, GIFT, KAEFER, FEUER, PFLANZE, DRACHE
ELEKTRO  → 2× FLUG, WASSER               | ½ PFLANZE, ELEKTRO, DRACHE | 0× BODEN
PSYCHO   → 2× KAMPF, GIFT                | ½ PSYCHO
EIS      → 2× FLUG, BODEN, PFLANZE, DRACHE | ½ WASSER, EIS
DRACHE   → 2× DRACHE
```

**Geist gegen Psycho:** in Rot/Blau durch einen Programmierfehler `0×`. Oben
steht die korrigierte Fassung. Über `#define GEN1_GHOST_BUG 1` in `types.h`
zurückschaltbar — dann bleibt Psycho so absurd stark wie im Original.

`dex_data.py` bekommt zwei neue Felder je Spezies (`type1`, `type2`), gezogen
über PokéAPI (`/pokemon/{id}` → `types[]`). Die bestehende Akzentfarbe leitet
sich künftig aus `type1` ab, damit es keine zwei Wahrheiten gibt.

### 5.2 Attacken (`tools/move_data.py` → `moves.h`)

Quelle: PokéAPI, Version-Group `red-blue`, Learn-Method `level-up`.

```c
struct Move {
  const char *name;   // über i18n
  uint8_t type;
  uint8_t power;      // 0 = Statusattacke
  uint8_t accuracy;   // 0-100
  uint8_t maxPp;
  uint8_t effect;
};
```

**Reduktion auf ~60 Attacken.** Die vollen 165 sind für vier Slots auf einem
Rundscreen unnötig und kosten Flash. Auswahlregel: alle Angriffsattacken mit
Stärke ≥ 40, die mindestens eine Spezies per Level-up lernt, plus die
Statuseffekte unten. Der Generator gibt die Abdeckung pro Typ aus, damit kein
Typ ohne brauchbare Attacke dasteht.

| Effekt-ID | Wirkung |
|---|---|
| 0 | keiner |
| 1 | 10 % Paralyse: Ziel −25 % SPD, 25 % Aussetzchance |
| 2 | 10 % Brand: Ziel −1/16 HP pro Runde |
| 3 | 30 % Gift: Ziel −1/16 HP pro Runde |
| 4 | erhöhte Volltrefferquote (12,5 % statt 4 %) |
| 5 | zwei bis fünf Treffer |
| 6 | Anwender heilt 50 % des zugefügten Schadens |
| 7 | senkt gegnerische DEF um eine Stufe |
| 8 | erhöht eigene ATK um eine Stufe |

Statusveränderungen gelten **nur bis Kampfende** und werden nicht persistiert.
Ein vergiftetes Pokémon darf das Pflegespiel nicht kaputtmachen.

**Attackennamen** über die bestehende Lokalisierungs-Pipeline:
`tools/gen_move_names.py` → `tools/move_names.py`, analog zum vorhandenen
`gen_names.py` für Speziesnamen. Deutsch und Französisch haben eigene Namen, die
übrigen Sprachen nutzen die englischen — dieselbe Regel wie bei den Spezies.
Alles ASCII-Großbuchstaben ohne Umlaute (`GLUT`, `RASIERBLATT`, `DONNERSCHOCK`).

### 5.3 Movepool und Erlernen

`moves.h` enthält je Spezies eine sortierte Learnset-Liste `{level, moveId}`.

- Beim Schlüpfen: die bis zu vier zuletzt lernbaren Attacken auf oder unter dem
  aktuellen Level.
- Bei jedem Levelaufstieg wird geprüft, ob eine neue Attacke ansteht. Sind alle
  vier Slots belegt, öffnet sich ein Dialog: **vergessen und ersetzen** oder
  **ablehnen**. Das passt zur Design-Philosophie des Projekts — Entwicklung und
  Abschied laufen genauso, der Spieler entscheidet und sieht zu.
- Bei der Entwicklung bleiben die Attacken erhalten.
- **Movepools erben über die Entwicklungskette:** hat eine Spezies auf ihrem
  Level selbst nichts zu lernen, zählt das Learnset der Vorstufe (Metapod erbt
  so die Attacke von Raupy).
- **STAB-Garantie:** wer per Level keine Attacke seines eigenen Typs lernt,
  bekommt im Generator eine passende TM (`tools/gen_move_data.py`). Pikachu
  hat dadurch immer eine Elektro-Attacke.
- **Verzweifler ist Move-ID 1** (`MOVE_STRUGGLE`), steht in keinem Movepool
  und ist der letzte Ausweg: sind alle AP leer oder ist der Pool leer (Ditto),
  kämpft das Pokémon damit.
- **Fixschaden-Attacken** (Drachenwut, Nachtnebel, Geowurf, Psywelle) haben in
  Gen 1 keine Stärke und fielen sonst aus dem Pool. Der Generator gibt ihnen
  eine feste Stärke (`POWER_OVERRIDE`); die Engine kennt keinen Fixschaden.
- Die anstehende Attacke (`pendingMove`) liegt in NVS. Ein Neustart zwischen
  Aufstieg und Entscheidung verliert sie nicht, und „ablehnen" wird gespeichert.

### 5.4 Neue Felder in `Pet` (`pet.h`)

```c
uint32_t xpMinutes    = 0;   // Fortschritt, friert bei lvlReq() ein
uint8_t  levelsWon    = 0;   // level() = 1 + levelsWon
uint32_t finalFormAt  = 0;   // ageMinutes beim Erreichen der Endstufe
uint8_t  moves[4]     = {0}; // Attacken-IDs, 0 = leerer Slot
uint8_t  pp[4]        = {0};
uint16_t battlesWon   = 0;
uint16_t battlesLost  = 0;
uint8_t  lossStreak   = 0;   // Niederlagen in Folge, Mitleidsregel 6.7
uint8_t  pendingMove  = 0;   // anstehende Attacke, NVS "pendmv" (5.3)
Rival    rival;              // Rivalenblock, NVS "rival" (5.5)
uint32_t rivalDay     = 0;   // Tag des letzten Rivalen-SIEGS, als today()+1
uint8_t  arenaRank    = 0;   // 0-8, geschaffte Ränge, gehört dem Spieler
uint8_t  arenaStep    = 0;   // 0-2, besiegte Gegner im laufenden Rang
uint8_t  nvsVer       = 2;
```

Alle Felder nach Schema 2 sind neue Schlüssel mit Default in `load()`.
Preferences ist Key-Value: alte Stände lesen sie als Default, ein
`nvsVer`-Schritt war dafür nicht nötig. Medaillen-Bits werden nur hinten
angehängt (`MED_FIRSTWIN` 8, `MED_SHINYWIN` 9, `MED_ARENA` 10).

**Migration von Schema 1:** vorhandene Spielstände haben `ageMinutes` und daraus
abgeleitete Level. Beim ersten Start mit Schema 2:
`levelsWon = ageMinutes / 60`, `xpMinutes = 0`, `finalFormAt = ageMinutes` falls
bereits Endstufe, Attacken aus dem Learnset nachziehen. Der Nutzer behält sein
Pokémon. **Kein `WIPE`.**

**Achtung, nie am Gerät mit Altdaten gelaufen.** Beim Flash von Phase 5 ging
das Pokémon verloren — nicht durch `migrate()`, sondern weil das 16-MB-
Vollabbild `merged.bin` ab `0x0` geschrieben wurde. Es enthält an der Stelle
der NVS-Partition nur `0xFF`. Seitdem flasht `flash.bat` nur die Teile aus
`flash_args`, und `tools/check_flash.py` prüft vorher, dass NVS unberührt
bleibt.

### 5.5 Rivale (eigener NVS-Block)

```c
struct Rival {
  uint16_t dex;
  uint8_t  geneAtk, geneDef, geneSpe;
  char     nick[12];
  bool     shiny;
  uint8_t  endKind;   // CER_FAREWELL / CER_RELEASE / CER_RUNAWAY
  uint8_t  moves[4];
  bool     set;
};
```

- **Startwert, solange `set == false`:** Glumanda (Dex 4), Gene alle 100,
  kein Spitzname, `endKind = CER_FAREWELL`. Der erste Rivale ist also für jeden
  Spieler dasselbe Glumanda.
- Bei **jedem** Ende des Lebenszyklus — Abschied, Freilassen *und* Weglaufen —
  wird das scheidende Pokémon in den Rivalenslot geschrieben, in seiner
  aktuellen Form mit seinen Genen, seinem Namen und seinem Shiny-Status.
- **Weggelaufene Rivalen bekommen +10 % ATK.** Groll. Das Pokémon, das dich
  verlassen hat, kommt stärker zurück.
- Der Rivale kämpft auf **Spielerlevel**, mit der Arena-KI (§6.6, `RIVAL_AI`).

Auftritt: einmal pro echtem Kalendertag als Option im freien Kampf, mit
**doppelter XP**. `rivalDay` wird nur durch einen **Sieg** gesetzt — nach einer
Niederlage darf man sofort nochmal.

*Entspannt (2026-10-11):* früher Spielerlevel + 2, Elite-KI, Tag schon beim
Kampfstart verbraucht, und der Rivale war dritter Gegner der Arenaränge 3, 6
und 8. Dort konnte er eine Typ-Sackgasse sein (früheres Onix gegen neues
Pikachu), deshalb ist er aus der Arena raus.

---

## 6. Kampf-Engine

**Leitlinie (2026-10-11):** TamaPoke ist ein entspanntes Spiel. Kein Kampf darf
zur Wand werden. Prüfstein ist `python3 tools/battle_sim.py --entspannt` — er
misst Versuche bis zum Sieg und prüft feste Ziele (Plan
`docs/superpowers/plans/2026-10-11-entspannter-kampf.md`).

Getrennt in `battle.h` / `battle.cpp`. **Keine Rendering-Aufrufe in dieser
Datei** — die Engine muss headless über die serielle Konsole laufen.

### 6.1 Gegner

```c
struct Foe {
  uint16_t dex; uint8_t level, type1, type2;
  uint16_t maxHp, hp, atk, def, spe;
  uint8_t moves[4], pp[4];
  bool shiny, isRival;
};
```

Basiswerte aus `DEX_TBL`, Gene fest auf 100 % (außer beim Rivalen), Attacken aus
dem Learnset auf seinem Level.

### 6.2 HP

```
maxHp = ((bHp * 2 + geneAtk) * level) / 100 + level + 10
```

An die Gen-1-Formel angelehnt, ohne EV-Term. Ein eigenes HP-Gen gibt es nicht;
`geneAtk` wird mitverwendet, damit kein weiteres Feld nötig wird.

### 6.3 Auswahl wilder Gegner

Zwei Filter, die beide auf bereits vorhandene Daten zugreifen:

- **Biome** aus `DEX_TBL[].biome` — das Feld steuert heute schon den Hintergrund.
  Wer auf einer Wiese steht, trifft Wiesen-Pokémon.
- **Tageszeit** aus dem RTC, dieselbe Berechnung, die `render()` für den Himmel
  benutzt:

| Zeit | Gewichtete Typen |
|---|---|
| Tag | Normal, Pflanze, Käfer, Flug |
| Dämmerung | Gift, Boden, Gestein |
| Nacht | Geist, Psycho, Eis |

Legendäre sind ausgeschlossen. Das Gegnerlevel liegt **nie über dem
Spielerlevel** (entspannt, 2026-10-11):

```
spread      = min(2, spielerLevel - 1)
gegnerLevel = spielerLevel - 0..spread   // nie darüber, Untergrenze 1
```

| Spielerlevel | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Gegnerlevel | 1 | 1–2 | 1–3 | 2–4 | 3–5 |

Davor galt `Spielerlevel ± spread`; die folgenden Absätze und die Messreihe
beschreiben diese ältere, symmetrische Fassung.

Ab Level 4 ist das dasselbe wie eine feste Spanne von ± 2; darunter ist es
symmetrisch statt nach oben verschoben.

**Warum nicht einfach unten abschneiden.** Eine abgeschnittene Spanne bleibt oben
stehen: mit fester Spanne ± 2 und Untergrenze 2 träfe ein Spieler auf Level 1 nur
Gegner der Level 2–3, auf Level 2 die Level 2–4. Das mittlere Gegnerlevel liegt
damit systematisch über dem Spielerlevel, und zwar genau dort, wo der Spieler am
wenigsten Attacken und den kleinsten Statspielraum hat. Gemessen waren das
**36,9 % Siegquote auf Level 1 und 40,5 % auf Level 2** — die beiden ersten
Kämpfe eines jeden Spielers waren die schwersten des ganzen Spiels.

Eine Untergrenze zu senken kuriert davon nur das Symptom und nur auf Level 1. Die
schrumpfende Spanne behebt die Ursache: das mittlere Gegnerlevel ist auf **jedem**
Level exakt das Spielerlevel. Auf Level 1 heißt das ein gleichstufiger Gegner —
die Spanne ist dort null, nicht abgeschnitten.

Der schwächere Gegner bleibt dabei erhalten, sobald es ihn überhaupt geben kann:
ab Level 2 nach unten, ab Level 4 in voller Breite. Er ist die Verschnaufpause
zwischen zwei harten Kämpfen.

Gemessen vor dem 2026-10-11 mit `--spread 2` (symmetrisch), je 20 000
Kämpfe, Spieler gegen wilde KI:

| Level | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 |
|---|---|---|---|---|---|---|---|---|
| Siegquote | 51,2 % | 49,9 % | 54,7 % | 51,0 % | 55,4 % | 52,8 % | 54,3 % | 54,7 % |

Kein Ausreißer nach unten, alles im Korridor 45–65 %. Nachzurechnen mit
`python3 tools/battle_sim.py --level <n> --spread 2`. Ohne `--spread` kämpft der
Simulator gleichstufig, so wie es die Abnahme in §10, Phase 3 verlangt.

**Shiny-Gegner:** 1 zu 64. Sieg gibt die Medaille `MED_SHINYWIN` und verdoppelt
einmalig die Shiny-Chance des nächsten Eis.

### 6.4 Rundenablauf

1. Beide wählen eine Attacke — Spieler per Touch, Gegner per KI (6.6).
2. Reihenfolge nach SPD, bei Gleichstand Zufall.
3. Trefferwurf gegen `accuracy`.
4. Schaden:

```
dmg = (((2 * level / 5 + 2) * power * atk / def) / 50 + 2)
dmg = dmg * stab / 2                  // stab = 3 bei Typübereinstimmung, sonst 2
dmg = dmg * chart1 / 2
dmg = dmg * chart2 / 2                // zweiter Typ, sonst neutral
dmg = dmg * (100 + bond / 5) / 100    // Bindungsbonus, max +20 %
dmg = dmg * (217 + random(39)) / 255
```

Volltreffer bei 4 % (12,5 % bei Effekt 4): `dmg *= 2`.
Alles Integer, `uint32_t` als Zwischentyp gegen Überlauf. Der Bindungsbonus gilt
nur für den Spieler; der Rivale hat stattdessen seinen Groll-Bonus.

Die Typfaktoren werden **zweistufig** angewendet, mit Abrunden nach jeder
Stufe — so wie oben geschrieben. `battle.cpp` benutzt dafür bewusst nicht
`typeMult()` aus `types.h`; die Begründung steht in `tools/gen_types.py`.

**Mindestschaden 1** — außer bei Immunität. Ist der Typfaktor 0, bleibt der
Schaden 0. Immunität ist Immunität.

5. Statuseffekt anwenden, Rundenschaden durch Gift und Brand am Rundenende.
6. Bei HP 0 ist der Kampf vorbei — außer die Bindung rettet (6.5).

Maximal **30 Runden**. Danach gewinnt, wer prozentual mehr HP übrig hat. Kein
Ausdauer-Patt auf einem Akkugerät.

### 6.5 Bindung, Beere, Erschöpfung

**Bindung rettet vor K.o.:** einmal pro Kampf, Chance `bond / 3` Prozent (also
bis zu 33 % bei maximaler Bindung), überlebt das Pokémon einen tödlichen Treffer
mit 1 HP. Ereignistext: `%s HAELT DURCH!`

**Lieblingsbeere heilt:** ein Itemslot im Kampf, belegt mit der Lieblingsbeere
der Spezies — **aber nur, wenn `berryKnown == true` ist**. Einmal pro Kampf,
heilt 50 % der maximalen HP. Wer die Lieblingssorte noch nicht entdeckt hat,
hat einen leeren Slot. Damit bekommt das bestehende Beeren-Rätsel endlich eine
handfeste Belohnung.

**Erschöpfung statt Verbot:** Kämpfen ist **immer** erlaubt, auch mit leerer
Energie. Unter `ENE < 20` gelten ATK und SPD mit −25 %. Kein hartes Blockieren.
Ausnahme: schlafende Pokémon und Eier kämpfen nicht.

### 6.6 Gegner-KI

Drei Stufen, bewusst simpel:

- **Wild:** zufällige Attacke mit AP > 0.
- **Arena Rang 1–4:** wie wild.
- **Arena Rang 5–8 und Rivale:** zu 60 % die Attacke mit dem besten
  Typvorteil, sonst zufällig.
- **Elite** (stärkste Attacke, Statusattacken über 70 % HP) bleibt nur das
  Spielerverhalten im Simulator und in `BSIM`. Kein Gegner im Spiel nutzt sie
  mehr (entspannt, 2026-10-11).

### 6.7 Ausgang

**Sieg:**
- Bei offenem Level: Levelaufstieg, gegebenenfalls Dialog für eine neue Attacke
- Sonst: XP nach 4.3
- `+8 JOY`, `+1 Bindung`, `lossStreak = 0`
- Zusätzlich `+1 Trainingspunkt` auf einen zufälligen Kampfwert (`trAtk` /
  `trDef` / `trSpe`)

**Niederlage:**
- `−5 JOY`
- **Kein Care-Slip-up.** Slip-ups verzögern die Entwicklung und kühlen die
  Bindung — Kämpfen darf nicht bestrafen, was Pflege belohnt.
- Sofortiger erneuter Versuch erlaubt
- `lossStreak++`. **Mitleidsregel:** jeder Gegner — wild, Rivale, Arena —
  kommt auf `Level × (3/4)^lossStreak`, Untergrenze 1, **ohne Deckel**
  (`pityLevel()`). Ein Sieg setzt zurück. Früher „ab 3: −1 je weiterer, max −4",
  das wurde nie angewendet und hätte sehr schwache Spezies nicht gerettet.
  Niemand soll auf Stufe 7 festhängen, weil ihm ein Typ fehlt.

**Kosten in jedem Fall**, unabhängig vom Ausgang und auch bei Flucht:
`−15 ENE`, `−8 FOOD`, `−5 HYG`, `−5 Gewicht`. Das Gewicht ersetzt den Abbau des
entfernten Ballspiels — ohne ihn gäbe es gegen Bonbons (+12) keinen aktiven
Hebel. Energie regeneriert nur im Schlaf mit +6/min — daraus ergibt sich von
selbst der Rhythmus „vier, fünf Kämpfe, dann ein Nickerchen". AP füllen sich
beim Aufwachen komplett auf.

---

## 7. Arena-Ladder

Endgame nach den freien Kämpfen. Erreichbar über ein neues Icon im unteren Bogen.

Acht Ränge, je drei Pokémon eines Typthemas. **Jeder Arenakampf ist ein
gewöhnlicher Kampf** — volle HP, normale Kosten, normale XP, Beere, Flucht.
Der Fortschritt wird **pro Gegner** gespeichert (`arenaStep`, 0–2): wer
verliert, tritt einfach wieder gegen denselben Gegner an. Der dritte Sieg
schließt den Rang ab. Kein Rivale in der Arena.

| Rang | Thema | Team | Gegnerlevel | KI |
|---|---|---|---|---|
| 1 | Wasser | Sterndu, Goldini, Starmie | Spieler −2 | wild |
| 2 | Elektro | Voltobal, Pikachu, Lektrobal | Spieler −2 | wild |
| 3 | Pflanze | Tangela, Ultrigaria, Giflor | Spieler −1 | wild |
| 4 | Gift | Smogon, Sleimok, Smogmog | Spieler −1 | wild |
| 5 | Gestein | Amonitas, Kabuto, Kabutops | Spieler −1 | arena |
| 6 | Psycho | Kadabra, Pantimos, Hypno | Spielerlevel | arena |
| 7 | Kampf | Rasaff, Machomei, Kicklee | Spielerlevel | arena |
| 8 | Feuer | Fukano, Gallopa, Arkani | Spielerlevel | arena |

Sortiert nach gemessener Schwierigkeit. **Kein Gegner, gegen den eine Spezies
gar keinen Schaden machen kann** — kein Boden (Pikachu wäre immun-gesperrt),
kein Flug-Doppeltyp (Tragosso). `battle_sim.py --self-test` prüft das für alle
151 Spezies auf Level 5–50. Die Mitleidsregel (§6.7) gilt auch hier.

Belohnung: Rang 1–2 +2, Rang 3–5 +3, Rang 6–8 +5 Trainingspunkte, zufällig
auf ATK/DEF/SPD verteilt. Rang 8 gibt `MED_ARENA`.

`arenaRank` und `arenaStep` persistieren über Generationswechsel hinweg — sie
gehören dem Spieler, nicht dem Pokémon, genau wie Streak und Rekorde.

**Drei neue Medaillen** (`MED_COUNT` von 8 auf 11, die uint16-Bitmask hat Platz
für 16): `MED_FIRSTWIN` (erster Sieg), `MED_SHINYWIN` (Shiny-Gegner besiegt),
`MED_ARENA` (Rang 8).

Gemessen mit `--entspannt`, Spieler Lv 30: ein ganzer Rang braucht im Schnitt
3,95 (Wasser) bis 6,31 (Feuer) Kämpfe, 3 wären perfekt; 90 % schaffen jeden
Rang in höchstens 12.

*Entspannt (2026-10-11):* früher drei Siege am Stück ohne Zwischenheilung,
Gegner Spieler +1 bis +3, Rivale in Rang 3/6/8, Boden-Teams in Rang 1 und 8.
Rang 1 schaffte so jeder Fünfte, Rang 8 jeder Hundertste, und für Pikachu
waren Rang 1 und 8 unmöglich. „Bessere Ei-Chance" (nie beziffert) gestrichen.

---

## 8. Kampf-UI

Runder Screen, 466×466, Mittelpunkt `CX 233`. Die Ecken sind abgeschnitten.

- Gegner oben rechts, leicht verkleinert (`scale` runtersetzen), HP-Balken darüber
- Eigenes Pokémon unten links, HP-Balken darunter
- Attackenbuttons auf dem unteren Bogen — dieselben Ankerpunkte, die heute die
  Icon-Buttons nutzen. AP-Anzeige je Slot, Typfarbe als Button-Akzent, damit man
  den Vorteil sieht, ohne die Tabelle im Kopf zu haben.

  **So viele Buttons wie Attacken, keine vier festen Slots.** `movesForLevel()`
  liefert eins bis vier; die Buttons verteilen sich über die verfügbare
  Bogenbreite — bei einer Attacke ein breiter Button, bei vier die schmale
  Viererreihe.

  Begründung: auf Level 1 und 2 hat **die Hälfte aller Spezies nur eine
  Attacke** — 82 von 146 auf Level 2, siehe die Messreihe zu §6.3. Drei
  ausgegraute Platzhalter daneben sehen nach einem Defekt aus, und der erste
  Kampf ist der, der über den Einstieg entscheidet. Ein breiter Button ist auf
  einem runden Touchscreen zudem leichter zu treffen als ein Viertel. Der
  Nebeneffekt passt zur Engine: sind alle AP leer, fällt sie auf Verzweifler
  zurück, und die Reihe kollabiert von selbst auf genau einen Button.
- Beerenbutton mittig **unter** der Attackenreihe, 100×30 bei (183,388),
  ausgegraut wenn unentdeckt oder verbraucht. Links über der Reihe liegt der
  eigene HP-Balken; ein Spiegel der Fluchttaste hätte ihn verdeckt.
- Fluchtbutton in jedem Kampf. Flucht aus der Arena kostet wie jede Flucht, der Fortschritt bleibt
- Beim Rivalen: sein gespeicherter Spitzname im Header statt des Speziesnamens
- Oben eine schmale Leiste: `KAMPF BEREIT` beim Levelkampf, sonst im
  Arenakampf der Rang (`ARENA n/8`)

**Einstiege.** Freier Kampf über das Spielen-Icon. Auf Statuskarte Seite 1
teilt sich die Fläche (96,300)–(370,340) in bis zu drei gleich breite Knöpfe:
`KAMPF` immer, `RIVALE` solange er heute bereit ist, `ARENA` bis Rang 8. Bei
offener Stufe ist der Kampfknopf auffällig (`KAMPF BEREIT`), und auf dem
Hauptschirm erscheint das Hinweisband (113,106)–(353,134), das den Levelkampf
direkt startet. Ein langer Druck im Band löst kein Freilassen aus.

**Medaillenseite:** elf Medaillen, zwei Spalten mal sechs Reihen, Kachel
180×32. Der Kacheltext wird so groß gesetzt, wie er passt.

**Rand:** jedes Element liegt im Radius 231 um (233,233). Die vollständige
Tabelle mit Eckabständen steht in `docs/GERAETETEST.md`, Abschnitt B8.

**Animation** über die vorhandenen PMD-Aktionen: `Attack` (ID 6) beim Angriff,
`Hurt` (ID 5) beim Treffer, `Pose` (ID 7) beim Sieg.

**Ereignistexte** unter dem Gegner, alles über `i18n`: `SEHR EFFEKTIV!`,
`VOLLTREFFER!`, `NICHT SEHR EFFEKTIV`, `KEIN EFFEKT`, `%s WURDE PARALYSIERT`,
`%s HAELT DURCH!`, `ERSCHOEPFT`.

**Sound** über `sfxPlay()`: Treffer, Volltreffer, Siegfanfare, Niederlage.

---

## 9. Deutsch als Standard

```c
// i18n.h
#define LANG_DEFAULT LANG_DE
```

`i18n.cpp:226` lädt `prefs.getUChar("lang", LANG_DEFAULT)` — bestehende Geräte
behalten ihre Einstellung, nur Neuinstallationen starten deutsch.

Neu zu übersetzen sind alle Kampfstrings, Attackennamen und Typnamen in **allen
sechs** Sprachen. Die Tabellenstruktur in `i18n.cpp` gibt das vor; ein fehlender
Eintrag verschiebt die ganze Tabelle und liefert falschen Text.

---

## 10. Phasen

Alles auf `main`, kleine Commits, jeder kompiliert. Jede Phase muss für sich
lauffähig sein.

**Phase 0 — Fundament**
`arduino-cli` einrichten, unveränderte Baseline kompilieren und flashen,
`CLAUDE.md` übernehmen, `LANG_DEFAULT` auf Deutsch, NVS-Feld `nvsVer` einführen.
*Fertig, wenn:* das Gerät läuft wie vorher, aber auf Deutsch, Spielstand intakt.

**Phase 1 — Typdaten**
`dex_data.py` um `type1`/`type2` erweitern, `type_data.py` und `gen_types.py`
neu, `types.h` generieren, Akzentfarbe aus `type1` ableiten.
*Fertig, wenn:* die Statuskarte die Typen korrekt zeigt, inklusive Doppeltypen.

**Phase 2 — Attackendaten**
`move_data.py`, `gen_moves.py`, `gen_move_names.py`, `moves.h` mit Learnsets.
Noch keine Spiellogik.
*Fertig, wenn:* `MOVES <dex>` auf der Konsole den Movepool in der aktiven
Sprache ausgibt.

**Phase 3 — Engine, headless**
`battle.h`/`battle.cpp`, Schadensformel, Rundenlogik, KI, Bindungseffekte.
Konsolenbefehle `BATTLE <dex>` und `BSIM <n>`.
*Fertig, wenn:* 1000 simulierte Kämpfe gegen gleichstufige Gegner eine Siegquote
zwischen 45 % und 65 % ergeben. Weicht es stark ab, stimmt die Formel nicht.

**Phase 4 — Kampf-UI**
Screen, Buttons, Animationen, Sound, Ereignistexte, Beerenslot.
*Fertig, wenn:* ein freier Kampf auf der Hardware vollständig spielbar ist.

**Phase 5 — Levelkurve und Gate**
`levels.h`, `xpMinutes`/`levelsWon`, XP aus freien Kämpfen, `finalFormAt`,
Migration, Attacken-Lerndialog, alle Anpassungen aus 4.4.
*Fertig, wenn:* ein Gerät mit altem Spielstand aktualisiert wird, ohne dass das
Pokémon verloren geht.

**Phase 6 — Rivale**
Rivalen-Block in NVS, Snapshot bei allen drei Enden, Glumanda als Startwert,
täglicher Rivalenkampf.
*Fertig, wenn:* nach einem Abschied das eigene Pokémon als Gegner auftaucht.

**Phase 7 — Arena**
Acht Ränge, Trainerteams (ohne Rivalen, Fortschritt pro Gegner), Belohnungen, drei neue Medaillen.
*Fertig, wenn:* Rang 8 erreichbar ist und die Medaille vergeben wird.

**Phase 8 — Härtung**
Soak-Test 24 h über `HEALTH` (Uptime, Heap und PSRAM sind instrumentiert),
`HEAP <n>` prüft Heap und PSRAM nach je 50 Kämpfen aller drei Arten
einschließlich Sprite-Laden, Balancing über `battle_sim.py --entspannt`.

**Stand (2026-10-12)**

| Phase | Code | am Gerät |
|---|---|---|
| 0 Fundament | fertig | geprüft |
| 1 Typdaten | fertig | geprüft (mit Phase 5 geflasht) |
| 2 Attackendaten | fertig | geprüft (mit Phase 5 geflasht) |
| 3 Engine | fertig, BSIM-Abnahme bestanden | `BSIM`-Gegenprobe offen |
| 4 Kampf-UI | fertig | teilweise, Beere und Kampfknöpfe neu |
| 5 Levelkurve | fertig | Migration **nie** mit Altdaten gelaufen (s. 5.4) |
| 6 Rivale | fertig | offen |
| 7 Arena | fertig | offen |
| 8 Härtung | Werkzeuge fertig (`HEAP`, `--entspannt`, Radiustabelle) | Soak-Test offen |

Was am Gerät zu prüfen ist, in Reihenfolge: `docs/GERAETETEST.md`.

---

## 11. Getroffene Entscheidungen

Alles hier ist bewusst so entschieden und jederzeit umkehrbar:

1. **Geist-gegen-Psycho-Bug ist gefixt.** Über `GEN1_GHOST_BUG` zurückschaltbar.
2. **Niederlage kostet nur Ressourcen**, keinen Slip-up, sofortiger Retry,
   und die Mitleidsregel (6.7) senkt jeden weiteren Gegner. Ein Tamagotchi,
   das fürs Verlieren bestraft, wird schnell freudlos.
3. **103 Attacken statt 165.** Fühlt es sich zu dünn an, hebt der Generator die
   Schwelle einfach an.
4. **Kein Banking von Leveln.** Genau eine offene Stufe. Wer zwei Wochen weg war,
   kämpft einmal und ist wieder im Fluss.
5. **Levelcap 100**, erreichbar in 21 Tagen — aber nur, wer den Abschied dauerhaft
   ablehnt und damit den Pokédex nicht vervollständigt. Diese Spannung ist
   gewollt und existiert im Spiel bereits.
6. **AP regenerieren beim Schlafen.** Sonst braucht es Tränke und ein Inventar,
   und das ist ein anderes Spiel.
7. **Care-Patzer wirken nicht im Kampf.** War überlegt, wurde verworfen — die
   Bestrafung über verzögerte Entwicklung reicht.
8. **Entspannt statt herausfordernd** (2026-10-11, Entscheidung des Nutzers).
   Kein Kampf darf zur Wand werden: Mitleidsregel ohne Deckel, wilde Gegner nie
   über dem Spieler, XP pauschal, Arena mit Fortschritt pro Gegner und ohne
   Typ-Sackgassen. Prüfstein ist `battle_sim.py --entspannt`.
9. **Balancing entscheidet der Nutzer.** Werkzeuge messen und melden, sie
   justieren nicht selbst.
10. **Kämpfen ist immer erlaubt**, auch erschöpft (−25 % ATK und SPD unter
    20 Energie). Nur Eier und schlafende Pokémon kämpfen nicht.
11. **Bindung:** Schaden `+bond/5` %, K.-o.-Rettung mit Chance `bond/3` %,
    einmal pro Kampf.
12. **25 einstufige Spezies** bekommen `finalFormAt` beim Schlüpfen, sonst
    könnten sie sich nie verabschieden.
13. **Kein Netzwerk, nur Gen 1.**
14. **Flashen schont den Spielstand.** Nie das Vollabbild ab `0x0`; `flash.bat`
    schreibt die Teile aus `flash_args`, `tools/check_flash.py` prüft vorher.

---

## 12. Rechtliches

Der Firmware-Code ist MIT. Die Sprites stammen von PMD SpriteCollab und stehen
unter **CC BY-NC 4.0**, Pokémon ist Marke von Nintendo / Game Freak / The Pokémon
Company. Basiswerte, Typen und Attackendaten kommen von PokéAPI.

Das Projekt bleibt damit **nicht-kommerziell**. Kein Verkauf, keine Werbung, kein
Rebranding. Die Upstream-Attribution in `CREDITS.md` bleibt bestehen.

---

## 13. Werkzeuge

| Werkzeug | Zweck |
|---|---|
| `tools\build.ps1` | Bauen mit Commit-Hash im Binary (`-dirty` bei offenen Änderungen) |
| `flash.bat` | Flashen ohne den Spielstand anzufassen, fragt nach dem Port |
| `tools/check_flash.py` | rechnet vor jedem Flash nach, dass NVS unberührt bleibt |
| `tools/check_i18n.py` | prüft, dass `StrId` und alle sechs Tabellen parallel laufen |
| `tools/battle_sim.py --self-test` | Zwilling der Engine, Pflicht nach jeder Engine-Änderung |
| `tools/battle_sim.py --entspannt` | Abnahme: ist das Spiel entspannt? |
| `tools/battle_sim.py --rival / --arena / --berry` | Messreihen |

**Konsole** (115200 Baud, LF): `STATS` (mit `pech=`), `HEALTH` (mit `psram=`
und `fw=`), `LVL <n>`, `SPEC <dex>`, `BATTLE <dex>`, `BSIM <n> [lv]`,
`BOND <n>`, `ENE <n>`, `FOE <dex> [shiny]`, `RIVAL`, `RIVAL <dex> [groll]`,
`ARENA`, `ARENA <n>`, `HEAP <n>`, dazu die Pflegebefehle aus dem Original
(`HATCH`, `SHINY`, `NICK`, `BYE`, `RUN`, `ABANDON`, `WIPE`, `TIME`, `RTCSET`,
`CAREDAY`, `REG`, `EGGS`, `GAL`, `BEEP`, `LS`, `PUT`).
