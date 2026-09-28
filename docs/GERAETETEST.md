# Gerätetest

Was am Gerät zu prüfen ist, weil es headless nicht geht.

**Auf dem Gerät liegt `d8c8a40` (Phase 5).** Die NVS-Migration 1 → 2 ist dort
schon gelaufen. Ungetestet ist damit alles, was danach kam:

| Commit | Was davon ans Gerät muss |
|---|---|
| `8e6312f` | Konsolenbefehle `BOND`, `ENE`, `FOE` |
| `2b51fdd` | Ballspiel entfernt, Hinweisband, Kampfbutton mit zwei Zuständen, Levelkampf-Leiste, Aufstiegsfeier, Gewicht −5 im Kampf |
| `fc0ed9a` | anstehende Attacke überlebt den Neustart |
| `2391b28` | langer Druck im Hinweisband löst kein Freilassen aus |
| *dieser* | Commit-Hash in Bootzeile und `HEALTH` |

Teil A ist die Pflicht — das ist neu und noch nie auf Hardware gelaufen.
Teil B liegt schon drauf, wurde aber nie systematisch durchgegangen; das ist
Nacharbeit, wenn Zeit ist.

## Vor dem Anfangen

**Serielle Konsole, 115200 Baud, Zeilenende LF.** Die Firmware liest bis `\n`
und trimmt; ohne LF passiert nichts.

**Das Öffnen des Ports löst über DTR/RTS einen Reset aus.** Alles, was nicht in
NVS steht, ist beim nächsten Verbinden weg. Zusammengehörige Befehle gehören
deshalb in **eine** Sitzung — nicht Port auf, ein Befehl, Port zu.

**Nur ein Programm darf COM3 halten.** Erst flashen, dann Monitor schließen,
dann Sprites schicken (`python3 tools/send_sd.py --port COM3`).

Nach dem Flash kann sich der Port neu anmelden — mit `arduino-cli board list`
nachsehen, nicht raten.

---

# Teil A — neu seit dem Flash

## A1. Welcher Stand liegt überhaupt drauf?

Der erste Test, weil jeder folgende davon abhängt. `FW_VERSION` steht seit
Phase 0 auf `1.5` und sagt deshalb nichts; der kurze Commit-Hash kommt jetzt
automatisch beim Kompilieren dazu.

1. Beim Booten erscheint auf Serial `TamaPoke fw v1.5 (<hash>)`.
2. `HEALTH` endet auf `fw=1.5/<hash>`.
3. Der Hash muss dem entsprechen, was `git rev-parse --short HEAD` im Repo
   sagt — also dem Stand, den du gerade geflasht hast.

Steht dort **`unbekannt`**, wurde ohne `tools\build.ps1` gebaut und der Hash
fehlt im Binary. Steht dort ein Hash mit **`-dirty`**, war der Arbeitsbaum beim
Bauen nicht sauber — dann ist der Flash *nicht* reproduzierbar, der Hash allein
sagt nicht, was drin ist.

Ab hier gilt: nach jedem weiteren Flash einmal `HEALTH` und den Hash lesen,
bevor irgendetwas anderes geprüft wird. Genau diese Verwechslung hat schon
einmal eine Stunde mit der Werksdemo gekostet.

## A2. Das Spielen-Icon startet den Kampf

Das Ballspiel ist weg (`Pet::playResult` samt `gameHi`/`strHi` entfernt). Auf
dem geflashten Stand `d8c8a40` startet das Spielen-Icon noch das Ballspiel —
nach dem Flash muss es den Kampf öffnen.

- Spielen (202/404) → Kampfschirm, kein Minispiel.
- Füttern (140/390), Licht (264/404), Baden (326/390) tun weiter das ihre.
- Schlafend oder als Ei startet kein Kampf.
- `STATS` nach einem Kampf: `peso=` ist gefallen, siehe A4.

Die alten NVS-Schlüssel `ghi` und `shi` bleiben als Waisen liegen. Das ist
Absicht und braucht keine Migration — nur nachsehen, dass nichts anderes
verrutscht ist: `STATS` muss Streak, Bindung und Medaillen unverändert zeigen.

## A3. Hinweisband und Levelkampf

Der sichtbare Teil von `2b51fdd`. `LVL 5` setzen, dann warten, bis eine Stufe
offen ist (für den Test `MINUTES_PER_LEVEL` in `pet.h` runtersetzen).

1. **Hinweisband** `KAMPF BEREIT` auf dem Hauptschirm, x 113–353, y 106–134.
   Es pulsiert (Breite atmet ±3 px).
2. Band **antippen** → der Kampf startet direkt.
3. Im Kampfschirm die **Levelkampf-Leiste** bei (143,56)–(323,74).
4. Kampf gewinnen → **Aufstiegsfeier**: das Wort groß bei y 150, die neue
   Levelzahl pulsierend bei y 208.
5. `STATS` bestätigt das neue Level, das Band ist weg.
6. Ein zweiter Sieg direkt danach gibt **keinen** zweiten Aufstieg (kein
   Banking) — er gibt XP.

## A4. Langer Druck im Hinweisband

`2391b28`. Genau dorthin tippen Spieler künftig.

- Stufe offen, Finger 3 s ruhig im Band halten → **kein** Freilassen-Dialog.
- Stufe offen, 3 s auf dem Sprite darunter (etwa y 200) → Dialog erscheint wie
  gehabt.
- Keine Stufe offen, 3 s im Band → Dialog erscheint. Dort liegt dann blosse
  Pet-Zone, es darf kein Bedienweg verloren gehen.

## A5. Kampfkosten mit Gewicht

`battleCost()` zieht bei **jedem** Kampf ab, auch bei Flucht: −15 Energie,
−8 Futter, −5 Hygiene, **−5 Gewicht**. Das Gewicht ist der neue Teil — es
ersetzt den Abbau des entfernten Ballspiels und ist der einzige aktive Hebel
gegen Bonbons (+12 pro Stück).

1. `STATS`, die vier Werte notieren.
2. Kampf starten und **fliehen**.
3. `STATS` — genau um diese Beträge gefallen.
4. Ein paar Bonbons füttern, dann zwei Kämpfe: das Gewicht muss wieder sinken.
5. Sieg: +8 Freude, Bindung +1, ein Trainingspunkt auf ATK, DEF oder SPD
   (zufällig, in `STATS` als `tr=`), dazu XP oder Aufstieg.
6. Niederlage: −5 Freude, **kein** Versäumnis (`desc=` bleibt gleich), sofort
   wieder kämpfbar.

## A6. Kampfbutton auf der Statuskarte

Nach oben wischen, Seite 1. Der Button hat zwei Zustände auf derselben Fläche
(96,300)–(370,340): normal (freier Kampf) und auffällig, wenn eine Stufe offen
ist. Beide antippen, beide müssen den Kampf starten. Das Layout darf beim
Wechsel nicht springen.

## A7. Die neuen Konsolenbefehle

`8e6312f`. Sie sind das Werkzeug für alles Weitere.

- `BOND 99` → `bond=99 rettung=33%`. Dann mehrere Kämpfe: die K.-o.-Rettung
  muss sich zeigen, das Pokémon bleibt bei 1 HP stehen. Einmal pro Kampf.
- `BOND 0` → keine Rettung.
- `ENE 10` → `ene=10 erschoepft=1`. Im Kampf erscheint `ERSCHOEPFT`, ATK und
  SPD sind um 25 % gesenkt. Der Kampf startet **trotzdem** — Erschöpfung
  sperrt nicht.
- `ENE 80` → kein Band.
- `FOE 25` → fester Gegner Pikachu. `FOE 25 1` → shiny. `FOE 0` → wieder
  zufällig. Damit sind Kämpfe reproduzierbar.

## A8. Anstehende Attacke überlebt den Neustart

`fc0ed9a`. Auf ein Level bringen, auf dem eine neue Attacke ansteht
(`moves.h`), bei vier belegten Slots.

- Nach dem Aufstiegssieg öffnet der Lerndialog. Alle vier alten Attacken plus
  der Ablehnen-Knopf antippbar und im Radius.
- **Der eigentliche Test:** Dialog offen lassen und **vor** der Entscheidung
  neu starten (Reset oder Port neu öffnen). Der Dialog muss **wiederkommen**.
  Tut er das nicht, ist die Attacke verloren — das Level steigt kein zweites
  Mal, und der Spieler merkt es nie. Der Schlüssel heißt `pendmv`.
- Ersetzen: Statuskarte zeigt die neue Attacke im gewählten Slot. Neustart →
  bleibt so, der Dialog kommt **nicht** wieder.
- Ablehnen: alles bleibt. Neustart → der Dialog kommt **nicht** wieder.

## A9. Die zwei neuen Medaillen

`MED_FIRSTWIN` und `MED_SHINYWIN`, Bits 8 und 9. `MED_COUNT` ist 10.

**Zuerst das Wichtigste: die alten Bits dürfen nicht verrutscht sein.** Die
neuen Medaillen hängen hinten dran, aber das muss am Gerät bestätigt werden —
ein verschobenes Bit zeigt eine andere Medaille an, als vergeben wurde, und das
ist nachträglich nicht mehr unterscheidbar.

1. `STATS` **vor** dem Flash gibt `medals=0x…`. Notieren.
2. Nach dem Flash muss `STATS` **denselben** Wert in den unteren acht Bits
   zeigen. `medals=0x8F` bleibt `0x8F` — nur oben können Bits dazukommen.
3. Die Medaillenseite muss dieselben Medaillen als erreicht zeigen wie vorher.
   Verschiebt sich eine, ist die Bitreihenfolge kaputt.

Dann die neuen:

- `MED_FIRSTWIN` kommt, sobald `battlesWon >= 1`. Sie hängt am Zähler, nicht am
  Aufruf — ein Gerät, das schon gewonnene Kämpfe mitbringt, bekommt sie
  **nachträglich beim ersten `checkMedals()`**, also gleich beim Booten. Auf
  einem Gerät mit Kampfhistorie ist sie damit sofort da, das ist Absicht.
- `MED_SHINYWIN`: `FOE 25 1` setzt einen shiny Pikachu als festen Gegner, dann
  gewinnen. Die Medaille erscheint mit der üblichen Feier. `FOE 0` danach
  wieder auf Zufall stellen.
- Beide überleben einen Neustart (`medals` liegt unter `medal` in NVS).
- Eine verlorene Kampf gegen einen Shiny gibt sie **nicht**.

### Layout der Medaillenseite

Das Raster ist neu: zwei Spalten mal **fünf** Reihen, Kachel 180×40 bei
x 48/238, y 100 + Reihe·54. Die letzte Reihe endet bei y 356, die
Seitenanzeige sitzt bei 374.

- Alle **zehn** Kacheln sichtbar, keine überlappt die Seitenanzeige.
- Nichts ragt über den runden Rand. Engste Stelle ist rechnerisch die obere
  Ecke der ersten Reihe mit **3,9 px** Luft — das ist knapp, also genau dort
  hinsehen.
- Der Kacheltext wird pro Kachel so groß gesetzt, wie er passt (dasselbe
  Verfahren wie bei den Attackenbuttons). In jeder Sprache passt der längste
  Text mindestens bei der kleinen Größe, **es darf nirgends abgeschnitten
  sein**. Auf Deutsch fallen drei von zehn auf die kleine Größe, auf
  Portugiesisch nur eine — gemischte Größen im Raster sind erwartet.
- Der Kopf zeigt jetzt `%u/10`.
- Alle sechs Sprachen einmal durchschalten.

Nebenbei behebt das Raster zwei Fehler des alten: dort ragte die oberste
Kachelreihe 13 px über den Rand, und auf Deutsch und Italienisch lief der
Text 16 px über die Kachel hinaus.

---

# Teil B — liegt drauf, nie systematisch geprüft

Nacharbeit. Nichts davon ist neu, aber auch nichts davon ist abgehakt.

## B1. Hat mein Pokémon den Phase-5-Flash überlebt?

Offener Punkt, den nur du beantworten kannst. Wenn ja: die Migration 1 → 2 hat
funktioniert und dieser Abschnitt ist abgehakt. Wenn nein, gehört hierher, was
genau verloren war — dann steckt in `migrate()` (`pet.cpp:634`) ein Fehler, der
gefunden werden muss, bevor je wieder ein Schema geändert wird.

`STATS` zeigt den heutigen Stand: Spezies, Level, Gene, Bindung, Streak,
Medaillen, Spitzname.

## B2. Sprache

`LANG_DEFAULT` ist `LANG_DE` (`i18n.h:11`), gelesen wird
`prefs.getUChar("lang", LANG_DEFAULT)` — bestehende Geräte behalten also ihre
Einstellung, nur Neuinstallationen starten deutsch.

- Durch alle sechs Sprachen schalten (ES, EN, FR, DE, IT, PT) und auf jeder
  Hauptschirm, Statuskarte und Kampfschirm ansehen. Gesucht wird **verrutschter
  Text** — ein Label, das nicht zu seinem Feld passt, heißt, dass `StrId` und
  die `STRINGS`-Tabelle auseinanderlaufen.
- Kein Umlaut darf als Kästchen oder Lücke erscheinen.

## B3. Starterauswahl

Fünf Starter inkl. Pikachu (25) und Tragosso (104). Nur nach `WIPE` sichtbar —
also erst machen, wenn B1 beantwortet und das Pokémon entbehrlich ist.

Alle fünf Namen vollständig lesbar, keiner am runden Rand abgeschnitten, alle
fünf antippbar — auch die unterste Zeile.

## B4. Freier Kampf

- Gegner oben rechts mit Namen und Level, HP-Balken bei (252,96), eigener bei
  (58,298).
- **Beide Sprites sichtbar.** Fehlt der Gegner, war zu wenig PSRAM frei —
  `HEALTH` vor und nach dem Kampfstart vergleichen. Unter 512 KB freiem PSRAM
  kämpft die Firmware absichtlich ohne Gegnerbild, das ist kein Absturz.
- Attackenbuttons: **so viele wie Attacken**, gleichmäßig über die Breite,
  keine grauen Platzhalter. Labels lesbar, notfalls gekürzt, aber nicht über
  den Buttonrand hinaus.
- AP-Zähler zählt runter. Alle AP leer → **genau ein** Verzweifler-Button.
- Fluchtbutton beendet den Kampf.
- Nach dem Kampf ist der Gegnersprite entladen: `HEALTH` zeigt wieder das
  PSRAM von vorher.

## B5. AP zwischen den Kämpfen

1. Kampf mit halbleeren AP beenden.
2. Neuer Kampf → die AP stehen noch da.
3. Schlafen lassen und aufwecken → alle AP voll (`refillPp`).
4. Zwischendurch Reset → die AP sind immer noch da, nicht zurückgesetzt.

## B6. Statuskarte, restliche Seiten

- Werteseite: Gewicht dabei, ändert sich nach Kämpfen.
- Medaillenseite: siehe A9, die ist neu.
- Fortschrittsseite zeigt das nächste Level und ob eine Stufe offen ist.
- Auf allen vier Seiten: nichts am runden Rand abgeschnitten.

## B7. BSIM-Abnahme

Der einzige Punkt, der die Engine gegen den Simulator stellt.

```
LVL 25
BSIM 2000 25
```

Referenz aus `tools/battle_sim.py` (Level 25, Spieler elite gegen wild,
bond 0, spread 0): **55,6 %** mit Standardseed. Das Gerät muss **±3
Prozentpunkte** treffen, also 52,6 bis 58,6 %. Weicht es mehr ab, laufen
Engine und Simulator auseinander — dann ist eine Änderung nur in einer der
beiden Dateien gelandet.

Dazu die Heap-Probe: `HEALTH` vor und nach `BSIM 1000 25`. `heap=` und `min=`
dürfen **kein einziges Byte** gewandert sein. Die Engine allokiert nichts.

## B8. Anti-Burn-in und der runde Rand

- 90 s nicht anfassen → Schirm dimmt (Stufe 1). 5 min → fast aus (Stufe 2).
- Der Tipp, der aufweckt, darf **nichts auslösen** (`swallowGesture`) —
  besonders nicht im Hinweisband und nicht auf einem Icon.
- Neue Elemente gegen den Rand: Mittelpunkt (233,233), Radius 231.
  Rechnerisch liegen alle drin, aber das AMOLED hat die letzte Stimme:
  Jeweils der größte Eckabstand:
  - Hinweisband (113,106)–(353,134) → **174,7** bei Ecke (353,106)
  - Levelkampf-Leiste (143,56)–(323,74) → **198,6** bei (323,56)
  - Kampfbutton Statuskarte (96,300)–(370,340) → **173,8** bei (370,340)
  - Attackenbuttons und Fluchtbutton auf dem unteren Bogen
  - `drawStreakBadge()` bei (26,16) → **299,9**, also 69 px **außerhalb**
    Radius 231. Kann dort nicht sichtbar sein. Nachsehen, nicht anfassen.

---

## Was hier nicht steht

Phase 6 (Rivale), Phase 7 (Arena) und die Lieblingsbeere im Kampf sind noch
nicht gebaut. Ihre Prüfschritte kommen dazu, sobald sie es sind.
