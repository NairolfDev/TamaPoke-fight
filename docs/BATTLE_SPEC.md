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
pct    = 12 + 4 * (foeLevel - level());   // begrenzt auf 5..25
xpGain = lvlReq() * pct / 100;
```

Bei gleichstarkem Gegner sind das 12 % — also rund **acht Kämpfe pro Level**.
Stärkere Gegner zahlen mehr, schwächere weniger. Damit ist aktives Spielen
etwa zwei- bis dreimal schneller als reines Warten, ohne das Warten wertlos
zu machen.

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

### 5.4 Neue Felder in `Pet` (`pet.h`)

```c
uint32_t xpMinutes    = 0;   // Fortschritt, friert bei lvlReq() ein
uint8_t  levelsWon    = 0;   // level() = 1 + levelsWon
uint32_t finalFormAt  = 0;   // ageMinutes beim Erreichen der Endstufe
uint8_t  moves[4]     = {0}; // Attacken-IDs, 0 = leerer Slot
uint8_t  pp[4]        = {0};
uint16_t battlesWon   = 0;
uint16_t battlesLost  = 0;
uint8_t  lossStreak   = 0;   // Mitleidsstaffelung, siehe 6.5
uint8_t  arenaRank    = 0;   // 0-8, gehört dem Spieler
uint32_t rivalDay     = 0;   // letzter Tag mit Rivalenkampf
uint8_t  nvsVer       = 2;
```

**Migration von Schema 1:** vorhandene Spielstände haben `ageMinutes` und daraus
abgeleitete Level. Beim ersten Start mit Schema 2:
`levelsWon = ageMinutes / 60`, `xpMinutes = 0`, `finalFormAt = ageMinutes` falls
bereits Endstufe, Attacken aus dem Learnset nachziehen. Der Nutzer behält sein
Pokémon. **Kein `WIPE`.**

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
- Der Rivale skaliert mit: sein Level ist immer `Spielerlevel + 2`.

Auftritte:
- als **letzter Gegner** der Arenaränge 3, 6 und 8
- einmal pro echtem Kalendertag als Option im freien Kampf, mit **doppelter XP**
  (`rivalDay` verhindert das Farmen)

---

## 6. Kampf-Engine

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

Legendäre sind ausgeschlossen. Gegnerlevel `Spielerlevel ± 2`, minimal 2.

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
- **Arena Rang 1–4:** zu 60 % die Attacke mit dem besten Typvorteil, sonst zufällig.
- **Arena Rang 5–8 und Rivale:** immer die schadensstärkste Attacke; nutzt
  Statusattacken, solange der Gegner über 70 % HP hat.

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
- `lossStreak++`. Ab 3: Gegnerlevel −1 je weiterer Niederlage, bis maximal −4.
  Niemand soll auf Stufe 7 festhängen, weil ihm ein Typ fehlt.

**Kosten in jedem Fall**, unabhängig vom Ausgang: `−15 ENE`, `−8 FOOD`,
`−5 HYG`. Energie regeneriert nur im Schlaf mit +6/min — daraus ergibt sich von
selbst der Rhythmus „vier, fünf Kämpfe, dann ein Nickerchen". AP füllen sich
beim Aufwachen komplett auf.

---

## 7. Arena-Ladder

Endgame nach den freien Kämpfen. Erreichbar über ein neues Icon im unteren Bogen.

Acht Ränge. Jeder Rang ist ein Trainer mit **drei** Pokémon eines Typthemas.
Der Spieler kämpft ohne Zwischenheilung gegen alle drei — HP und AP bleiben
zwischen den Kämpfen bestehen, das ist die eigentliche Schwierigkeit. Die
Lieblingsbeere steht einmal **pro Kampf** zur Verfügung, nicht pro Rang.

In den Rängen 3, 6 und 8 ist der dritte Gegner der **Rivale**.

| Rang | Gegnerlevel | Belohnung |
|---|---|---|
| 1–2 | Spieler +1 | +2 Trainingspunkte |
| 3–5 | Spieler +2 | +3 Trainingspunkte, bessere Ei-Chance |
| 6–8 | Spieler +3 | +5 Trainingspunkte, Medaille |

`arenaRank` persistiert über Generationswechsel hinweg — er gehört dem Spieler,
nicht dem Pokémon, genau wie Streak und Rekorde.

**Drei neue Medaillen** (`MED_COUNT` von 8 auf 11, die uint16-Bitmask hat Platz
für 16): `MED_FIRSTWIN` (erster Sieg), `MED_ARENA` (Rang 8), `MED_SHINYWIN`
(Shiny-Gegner besiegt).

---

## 8. Kampf-UI

Runder Screen, 466×466, Mittelpunkt `CX 233`. Die Ecken sind abgeschnitten.

- Gegner oben rechts, leicht verkleinert (`scale` runtersetzen), HP-Balken darüber
- Eigenes Pokémon unten links, HP-Balken darunter
- Vier Attackenbuttons auf dem unteren Bogen — dieselben Ankerpunkte, die heute
  die Icon-Buttons nutzen. AP-Anzeige je Slot, Typfarbe als Button-Akzent, damit
  man den Vorteil sieht, ohne die Tabelle im Kopf zu haben
- Beerenbutton in der Mitte, ausgegraut wenn unentdeckt oder verbraucht
- Fluchtbutton nur bei freien Kämpfen, nicht in der Arena
- Beim Rivalen: sein gespeicherter Spitzname im Header statt des Speziesnamens

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

Ein Branch pro Phase. Jede Phase muss für sich kompilieren und lauffähig sein.

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
Acht Ränge, Trainerteams, Rivale in 3/6/8, Belohnungen, drei neue Medaillen.
*Fertig, wenn:* Rang 8 erreichbar ist und die Medaille vergeben wird.

**Phase 8 — Härtung**
Soak-Test 24 h über `HEALTH` (Uptime und Heap sind bereits instrumentiert),
Heap-Prüfung nach je 50 Kämpfen, Balancing nachziehen.

---

## 11. Getroffene Entscheidungen

Alles hier ist bewusst so entschieden und jederzeit umkehrbar:

1. **Geist-gegen-Psycho-Bug ist gefixt.** Über `GEN1_GHOST_BUG` zurückschaltbar.
2. **Niederlage kostet nur Ressourcen**, keinen Slip-up, sofortiger Retry,
   Staffelung ab drei Niederlagen. Ein Tamagotchi, das fürs Verlieren bestraft,
   wird schnell freudlos.
3. **~60 Attacken statt 165.** Fühlt es sich zu dünn an, hebt der Generator die
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

---

## 12. Rechtliches

Der Firmware-Code ist MIT. Die Sprites stammen von PMD SpriteCollab und stehen
unter **CC BY-NC 4.0**, Pokémon ist Marke von Nintendo / Game Freak / The Pokémon
Company. Basiswerte, Typen und Attackendaten kommen von PokéAPI.

Das Projekt bleibt damit **nicht-kommerziell**. Kein Verkauf, keine Werbung, kein
Rebranding. Die Upstream-Attribution in `CREDITS.md` bleibt bestehen.
