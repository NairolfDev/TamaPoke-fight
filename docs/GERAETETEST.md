# Gerätetest

Was am Gerät zu prüfen ist, was headless nicht geht. Stand: alle Änderungen
seit dem letzten Flash (fw v1.5, Commit `fdb24a7`) — also die Phasen 1 bis 5
des Kampfsystems.

Die Liste ist eine Reihenfolge, keine Sammlung: ein Punkt setzt voraus, dass
der vorige durch ist. Neue Features hängen ihre Prüfschritte hinten an.

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

## 1. Migration: das alte Pokémon überlebt das Update

**Das ist der einzige Test, der nur ein einziges Mal geht.** Er braucht ein
Gerät mit Altdaten aus fw v1.5. Ist einmal `WIPE` gelaufen oder hat das Gerät
schon mit dem neuen Schema gebootet, ist die Gelegenheit vorbei. Also zuerst.

`nvsVer` steigt in diesem Update von 1 auf 2 (`pet.h:9`), `migrate()` in
`pet.cpp:634` zieht `levelsWon`, `xpMinutes` und `finalFormAt` nach.

1. **Vor** dem Flashen `STATS` absetzen und die Ausgabe sichern — Spezies,
   Level, Gene, Bindung, Streak, Medaillen, Spitzname.
2. Flashen. **Kein `WIPE`.**
3. `STATS` erneut. Zu prüfen:
   - Spezies, Gene, Spitzname, Shiny, Streak, Bindung, Medaillen unverändert
   - Level gleich oder höchstens eins daneben (`levelsWon = ageMinutes / 60`)
   - Beim Boot erscheint auf Serial `nvs 1 -> 2: levelsWon=… finalFormAt=…`
4. Der Hauptschirm zeigt das Pokémon, nicht die Starterauswahl.

Schlägt das fehl, hier anhalten und melden — alles Weitere ist dann egal.

## 2. Sprache

`LANG_DEFAULT` ist jetzt `LANG_DE` (`i18n.h:11`), gelesen wird aber
`prefs.getUChar("lang", LANG_DEFAULT)`.

- Gerät aus Punkt 1 (Altdaten): behält seine bisherige Sprache.
- Nach `WIPE`: startet auf **Deutsch**.
- In den Einstellungen durch alle sechs Sprachen schalten (ES, EN, FR, DE, IT,
  PT) und auf jeder einmal Hauptschirm, Statuskarte und Kampfschirm ansehen.
  Gesucht wird **verrutschter Text** — ein Label, das nicht zu seinem Feld
  passt, heißt, dass `StrId` und die `STRINGS`-Tabelle auseinanderlaufen.
- Kein Umlaut darf als Kästchen oder Lücke erscheinen. Der GFX-Font hat keine;
  gefundene Stellen sind Fehler in `i18n.cpp`, nicht im Font.

## 3. Starterauswahl

Fünf Starter statt drei, `STARTER_DEX` mit Pikachu (25) und Tragosso (104).

1. `WIPE` (löscht NVS und startet neu).
2. Die Auswahl zeigt **fünf Zeilen**. Zu prüfen: alle fünf Namen vollständig
   lesbar, keine am runden Rand abgeschnitten, alle fünf antippbar — auch die
   unterste.
3. Einen Starter wählen, `STATS` bestätigt die Spezies.

## 4. Hauptschirm: die Icons

Sackhauen und Ballspiel sind raus. Das **Spielen-Icon** (202/404) startet jetzt
einen Kampf.

- Füttern (140/390), Licht (264/404), Baden (326/390) tun weiter, was sie
  sollen.
- Spielen öffnet den Kampfschirm, nicht das alte Minispiel.
- Schlafend oder als Ei startet kein Kampf (`startBattle()` steigt früh aus).

## 5. Freier Kampf

`LVL 10` setzen, damit es ein paar Attacken gibt, dann über das Spielen-Icon
starten.

Zu prüfen:
- Gegner oben rechts mit Namen und Level, HP-Balken bei (252,96), eigener bei
  (58,298).
- **Beide Sprites sichtbar.** Fehlt der Gegner, war zu wenig PSRAM frei —
  `HEALTH` vor und nach dem Kampfstart vergleichen. Unter 512 KB freiem PSRAM
  kämpft die Firmware absichtlich ohne Gegnerbild, das ist kein Absturz.
- Attackenbuttons: **so viele wie das Pokémon Attacken hat**, gleichmäßig über
  die Breite. Keine grauen Platzhalter. Jedes Label lesbar, notfalls gekürzt —
  aber nicht über den Buttonrand hinaus.
- AP-Zähler unter jedem Label zählt runter.
- Sind alle AP leer, bleibt **genau ein** Verzweifler-Button.
- Fluchtbutton vorhanden und er beendet den Kampf.
- Nach dem Kampf ist der Gegnersprite wieder entladen: `HEALTH` zeigt wieder
  das PSRAM von vorher.

Feste Gegner für reproduzierbare Läufe: `FOE 25` (Pikachu), `FOE 25 1`
(shiny), `FOE 0` schaltet zurück auf Zufall.

## 6. Kampfkosten und Belohnung

`battleCost()` zieht bei **jedem** Kampf ab, auch bei Flucht: −15 Energie,
−8 Futter, −5 Hygiene, −5 Gewicht.

1. `STATS`, Werte notieren.
2. Kampf starten und **fliehen**.
3. `STATS` — die vier Werte müssen genau um diese Beträge gefallen sein.
4. Kampf gewinnen: +8 Freude, Bindung +1, ein Trainingspunkt auf ATK, DEF oder
   SPD (zufällig, in `STATS` als `tr=…`), dazu XP oder Aufstieg.
5. Kampf verlieren: −5 Freude, **kein** Versäumnis (`desc=` in `STATS` bleibt
   gleich), sofort wieder kämpfbar.

## 7. Erschöpfung und Bindung

Kämpfen ist nie gesperrt, Erschöpfung kostet nur Werte.

- `ENE 10`, dann Kampf: das Band `ERSCHOEPFT` erscheint, ATK und SPD sind um
  25 % gesenkt. Der Kampf startet trotzdem.
- `ENE 80`: kein Band.
- `BOND 99`, dann mehrere Kämpfe: die K.o.-Rettung (33 % Chance, einmal pro
  Kampf) muss sich zeigen — das Pokémon bleibt bei 1 HP stehen.
- `BOND 0`: keine Rettung.

## 8. Levelaufstieg

Level steigt **nur** durch gewonnene Kämpfe. Genau eine Stufe ist offen, kein
Banking, `xpMinutes` friert ein, solange die Stufe offen ist.

1. `LVL 5`, dann warten, bis `LVL_REQ` erfüllt ist (`lvlReq()` steht in der
   `LVL`-Ausgabe). Für den Test `MINUTES_PER_LEVEL` in `pet.h` runtersetzen.
2. **Hinweisband** `KAMPF BEREIT` erscheint auf dem Hauptschirm bei
   x 113–353, y 106–134. Es pulsiert.
3. Band **antippen** → der Kampf startet direkt.
4. Im Kampfschirm steht die **Levelkampf-Leiste** bei (CX−90, 56), 180×18.
5. Kampf gewinnen → **Aufstiegsfeier**: das Wort groß bei y 150, die neue
   Levelzahl pulsierend bei y 208.
6. `STATS` bestätigt das neue Level. Das Band ist weg.
7. Ein zweiter Sieg direkt danach gibt **keinen** zweiten Aufstieg (kein
   Banking) — er gibt XP.

### 8b. Langdruck im Hinweisband

Genau dorthin tippen Spieler künftig. Ein 3-Sekunden-Druck im Band darf den
Freilassen-Dialog **nicht** auslösen, solange eine Stufe offen ist.

- Stufe offen, Finger 3 s ruhig im Band halten → kein `SOLTAR?`-Dialog.
- Stufe offen, 3 s auf dem Sprite darunter (etwa y 200) → Dialog erscheint
  wie gehabt.
- Keine Stufe offen, 3 s im Band → Dialog erscheint (dort ist dann nur die
  Pet-Zone).

## 9. Lerndialog

Steigt das Level und sind alle vier Attackenslots belegt, kommt die Wahl:
vergessen und ersetzen oder ablehnen.

- Auf ein Level bringen, auf dem eine neue Attacke ansteht (`LVL n` und die
  Movepool-Tabelle in `moves.h`), vier Slots belegt.
- Nach dem Aufstiegssieg öffnet der Dialog. Alle vier alten Attacken plus der
  Ablehnen-Knopf müssen antippbar sein und im Radius liegen.
- Ersetzen: `STATS`/Statuskarte zeigt die neue Attacke im gewählten Slot.
- Ablehnen: alles bleibt, wie es war.
- **Der Dialog darf nicht wiederkommen**, wenn man ihn einmal entschieden hat
  — auch nicht nach einem Neustart.
- Gegenprobe, und die ist der eigentliche Punkt: Dialog aufgehen lassen und
  **vor** der Entscheidung neu starten (Reset oder Port neu öffnen). Der
  Dialog muss **wiederkommen**. Tut er das nicht, ist die anstehende Attacke
  verloren — das Level steigt kein zweites Mal, und der Spieler merkt es nie.
  `pendingMove` liegt dafür unter dem NVS-Schlüssel `pendmv`.

## 10. AP zwischen den Kämpfen

AP bleiben über den Kampf hinaus stehen und füllen sich erst beim Aufwachen.

1. Einen Kampf mit halbleeren AP beenden.
2. Neuen Kampf starten → die AP stehen noch da, wo sie waren.
3. Schlafen lassen und aufwecken → alle AP voll.
4. Zwischendurch neu starten (Reset) → die AP sind immer noch da, nicht
   zurückgesetzt.

## 11. Statuskarte

Nach oben wischen, dann seitlich durch die vier Seiten.

- **Seite 1** hat den Kampfbutton. Er hat **zwei Zustände**: normal (freier
  Kampf) und der auffällige, wenn eine Stufe offen ist. Beide antippen.
- Seite mit den Werten: Gewicht ist dabei und ändert sich nach Kämpfen.
- Medaillenseite: die acht Medaillen, `MED_COUNT` stimmt mit der Anzahl
  gezeichneter Felder überein.
- Fortschrittsseite zeigt das nächste Level und ob eine Stufe offen ist.
- Auf allen vier Seiten: nichts am runden Rand abgeschnitten.

## 12. BSIM-Abnahme

Der einzige Punkt, der die Engine gegen den Simulator stellt. Er ist der
Grund, warum `battle_sim.py` existiert.

Auf dem Gerät:

```
LVL 25
BSIM 2000 25
```

Referenz aus `tools/battle_sim.py` (Level 25, Spieler elite gegen wild,
bond 0, spread 0): **55,6 %** mit Standardseed. Das Gerät muss **±3
Prozentpunkte** treffen, also 52,6 bis 58,6 %.

Weicht es mehr ab, laufen Engine und Simulator auseinander — dann ist eine
Änderung nur in einer der beiden Dateien gelandet.

Dazu die Heap-Probe: `HEALTH` vor und nach `BSIM 1000 25`. `heap=` und `min=`
dürfen **kein einziges Byte** gewandert sein. Die Engine allokiert nichts.

## 13. Anti-Burn-in und der runde Rand

Zum Schluss, weil es Zeit braucht.

- 90 s nicht anfassen → Schirm dimmt (Stufe 1). 5 min → fast aus (Stufe 2).
- Der Tipp, der aufweckt, darf **nichts auslösen** (`swallowGesture`) —
  besonders nicht im Hinweisband und nicht auf einem Icon.
- Alle neuen Elemente gegen den Rand prüfen: Mittelpunkt (233,233), Radius
  231. Rechnerisch liegen alle im Radius, aber das AMOLED hat die letzte
  Stimme:
  - Hinweisband: Ecken (113,106) und (353,134) → 175 bzw. 155 Abstand
  - Levelkampf-Leiste: (143,56)–(323,74) → 194 bzw. 179
  - Attackenbuttons und Fluchtbutton auf dem unteren Bogen
  - Starterauswahl, fünfte Zeile

---

## Was hier nicht steht

Phase 6 (Rivale), Phase 7 (Arena) und die Lieblingsbeere im Kampf sind noch
nicht gebaut. Ihre Prüfschritte kommen dazu, sobald sie es sind.
