# CLAUDE.md — TamaPoke Battle Fork

Arbeitsanweisungen für Claude Code in diesem Repo. Lies das vor jeder Änderung.

## Was das hier ist

Firmware für ein Tamagotchi auf dem **Waveshare ESP32-S3-Touch-AMOLED-1.75**
(rundes 466×466 AMOLED, CO5300 über QSPI, CST9217 Touch über I2C). Arduino-C++,
kein PlatformIO. Sprites liegen auf der microSD, nicht im Flash.

Upstream: `socquique/TamaPoke`. Dieser Fork fügt ein Kampfsystem hinzu.

## Sprache

- **Code-Kommentare: Deutsch.** Der Upstream ist auf Spanisch kommentiert.
  Bestehende spanische Kommentare in Dateien, die du sowieso anfasst, mit
  übersetzen. Keine Massen-Übersetzungs-Commits, die den Diff unlesbar machen.
- **Bezeichner: Englisch** (`battleWins`, nicht `kampfSiege`). Konsistent mit
  dem bestehenden Code.
- **UI-Strings: niemals hardcoden.** Alles läuft über `i18n.h` / `i18n.cpp`.
- Der GFX-Font hat **keine Umlaute**. UI-Text ist ASCII-Großbuchstaben:
  `STAERKE`, nicht `STÄRKE`. Das gilt für alle sechs Sprachen.

## Build

```bash
FQBN="esp32:esp32:esp32s3:CDCOnBoot=cdc,FlashSize=16M,PSRAM=opi,PartitionScheme=app3M_fat9M_16MB"
arduino-cli compile --fqbn "$FQBN" .
arduino-cli upload -p /dev/ttyACM0 --fqbn "$FQBN" .
```

**Nach jeder Änderung kompilieren.** Ein Compile-Fehler auf einem Embedded-Target
kostet den Nutzer einen Flash-Zyklus zum Merken. Nie ungetesteten Code committen.

Benötigte Libraries: `Arduino_GFX` (moononournation), `SensorLib` (Lewis He),
`XPowersLib` (Lewis He), `ESP_I2S` (im ESP32-Core enthalten).

### Der Sketch-Ordner muss `TamaPoke` heißen

Arduino verlangt, dass die Haupt-`.ino` genauso heißt wie ihr Ordner. Das Repo
heißt `TamaPoke-fight`, der Sketch `TamaPoke.ino` — ein `compile .` im Repo-Ordner
bricht deshalb mit *„main file missing from sketch"* ab. Einmalig eine Junction
anlegen und **von dort** bauen:

```
cmd /c mklink /J "C:\Users\oberh\Webseits\TamaPoke" "C:\Users\oberh\Webseits\TamaPoke-fight"
```

Gilt auch für Worktrees unter `.claude/worktrees/` — deren Ordnername passt nie.

### Windows

`arduino-cli` liegt unter `C:\Program Files\Arduino CLI\` und steht auf der
Machine-PATH. Eine Shell, die vor der Installation offen war, sieht sie nicht —
neue PowerShell öffnen, nicht die PATH-Variable von Hand basteln.

**In PowerShell brauchen Pfade mit Leerzeichen den Aufruf-Operator `&`.** Ohne ihn
behandelt PowerShell den String als Text und gibt ihn nur aus, statt ihn
auszuführen:

```powershell
& "C:\Program Files\Arduino CLI\arduino-cli.exe" core list   # richtig
"C:\Program Files\Arduino CLI\arduino-cli.exe" core list     # gibt nur den Pfad aus
```

Weitere PowerShell-Stolpersteine: `&&` und `||` gibt es in Windows PowerShell 5.1
nicht (`;` oder `if ($?) { … }`), und `2>&1` auf eine native `.exe` verpackt jede
stderr-Zeile in einen `NativeCommandError` — sieht nach Absturz aus, obwohl der
Exitcode 0 ist.

**Keine überlangen Befehlszeilen zum Kopieren geben.** Die Konsole bricht eine
eingefügte Zeile an der Fensterbreite um, und der Umbruch landet *im* String.
Ergebnis sind Fehler, die aussehen, als fehle eine Datei — `is not recognized as
the name of a cmdlet` oder `Cannot find path … because it does not exist`, mit dem
Pfad an genau der Umbruchstelle zerschnitten (`…\Local\Ar` + `duino15\…`). Die
Datei ist in Wahrheit da. Lange Aufrufe auf mehrere kurze Zeilen verteilen
(Variablen setzen, dann aufrufen) — oder den Befehl selbst ausführen, statt ihn
zum Kopieren zu geben.

Port ist `COM3`, nicht `/dev/ttyACM0`:

```
arduino-cli upload -p COM3 -b "$FQBN" --input-dir build\baseline
```

**Es kann immer nur ein Programm den COM-Port halten.** Erst flashen, Serial-
Monitor schließen, dann Sprites schicken.

**`tools/send_sd.py` braucht unter Windows zwingend `--port`:**

```
python3 tools/send_sd.py --port COM3
```

Ohne die Angabe sucht `find_port()` nach `/dev/cu.usbmodem*` — ein macOS-Pfad —
und bricht mit „no encuentro la placa" ab. Braucht `pip install pyserial`.

## Generierte Dateien — nicht von Hand editieren

| Datei | Generator | Quelle |
|---|---|---|
| `dex.h` | `tools/gen_dex.py` | `tools/dex_data.py`, `dex_stats.py`, `dex_names.py` |
| `species.h` | `tools/sprites.py emit` | in-code Primitive |
| `moves.h` | `tools/gen_moves.py` (neu) | `tools/move_data.py`, `move_names.py` |
| `types.h` | `tools/gen_types.py` (neu) | `tools/type_data.py` |
| `levels.h` | `tools/gen_levels.py` (neu) | Formel in `docs/BATTLE_SPEC.md` §3.2 |

Änderung an Dex- oder Move-Daten heißt: Python-Quelle ändern → Generator laufen
lassen → generierten Header committen. Nie umgekehrt.

## Speicher-Budget

- Framebuffer 466×466×16bit ≈ 434 KB liegt in **PSRAM**. Nicht anfassen.
- Sprites werden von der SD in PSRAM geladen (`PmdMon`). Neue Sprite-Slots für
  Gegner kosten dort Platz — vor dem Laden `heap_caps_get_free_size(MALLOC_CAP_SPIRAM)`
  prüfen.
- Neue Konstanten-Tabellen (Typen, Attacken) gehören ins Flash: `static const`
  auf File-Scope, nicht auf den Stack.
- Der Stack einer Arduino-Task ist knapp. Keine großen lokalen Arrays in
  Render-Funktionen.

## Persistenz

Zustand liegt in NVS über `Preferences` (`pet.cpp`, `save()` / `load()`).

- **Jede neue Zustandsvariable braucht einen Default in `load()`**, sonst
  bricht das Spiel beim Update eines Geräts mit Altdaten.
- Schlüssel sind auf 15 Zeichen begrenzt.
- Es gibt ein Schema-Feld `nvsVer`. Wenn du das Layout änderst: hochzählen und
  eine Migration schreiben. **Nutzer sollen für ein Update kein `WIPE` brauchen**
  — der Nutzer zieht ein echtes Pokémon groß und verliert es sonst.

## Testen ohne Hardware-Grind

Die serielle Konsole (115200) ist die Testbank. Bestehende Kommandos:
`STATS`, `SPEC <dex>`, `LVL <n>`, `HATCH`, `SHINY`, `NICK`, `BYE`, `RUN`,
`ABANDON`, `WIPE`, `BEEP`, `REG`, `EGGS`, `GAL`, `CAREDAY`, `TIME`, `RTCSET`,
`HEALTH`, `LS`, `PUT`.

**Neue Features kriegen ein Konsolen-Kommando, bevor sie eine UI kriegen.** Die
Kampflogik muss headless über Serial testbar sein (`BATTLE <dex>`, `BSIM <n>`),
bevor ein Pixel gezeichnet wird. Das ist nicht optional — sonst debuggst du
Schadensformeln über Screenshots.

Schnelltest-Konstanten in `pet.h`: `PET_TICK_MS`, `MINUTES_PER_LEVEL`,
`FAREWELL_AGE_MIN` runtersetzen.

## Rendering

- `render()` in `TamaPoke.ino` dispatcht über Bool-Flags (`gameOpen`,
  `sackOpen`, `cardOpen`, …). Neue Screens folgen dem Muster: Flag + eigene
  `renderX()` + Touch-Handling im selben Block.
- Der Screen ist **rund**. Alles in den Ecken wird abgeschnitten. Mittelpunkt
  ist `CX 233`, Buttons liegen auf dem unteren Bogen.
- Anti-Burn-in-Dimming ist aktiv. Statische Vollbild-Elemente vermeiden.

## Grenzen

- **Kein Netzwerk.** Es gibt aktuell keinen einzigen WiFi-/BLE-Aufruf im Repo.
  Nicht ohne ausdrücklichen Auftrag hinzufügen — das kostet RAM und Akku.
- Sprites sind **CC BY-NC** (PMD SpriteCollab), Pokémon ist Marke von
  Nintendo/Game Freak. Das Projekt bleibt nicht-kommerziell. Keine Store-Links,
  keine Monetarisierung, kein Rebranding als eigenes Produkt.
- Code ist MIT. Upstream-Attribution in `CREDITS.md` bleibt drin.

## Arbeitsweise

- Ein Branch pro Phase aus `docs/BATTLE_SPEC.md`, nicht alles in einen.
- Vor dem Refactor einer Datei: `git log --oneline -5 <datei>` — der Upstream
  ist aktiv, unnötige Divergenz macht spätere Merges teuer.
- Wenn ein Feature das Spielgefühl verändert (Balancing, Zeitkonstanten),
  **erst fragen**, nicht einfach entscheiden.

## Werkzeuge einrichten — dauerhaft, nicht für die Sitzung

**Alles, was du einrichtest, muss aus einer normalen PowerShell im Repo-Ordner
funktionieren und einen Neustart überleben.** Nichts in Sitzungs-, Scratchpad-
oder Temp-Verzeichnissen ablegen — das ist nach dem nächsten Start weg, und der
Nutzer steht mit einem Befehl da, der bei ihm nicht läuft.

Konkret heißt das:

- Toolchains an ihren Standardort: `arduino-cli` nach `%LOCALAPPDATA%\Arduino15`
  (Cores, Libraries, Konfiguration). Kein `ARDUINO_DIRECTORIES_DATA` auf einen
  eigenen Pfad biegen.
- Build-Artefakte nach `build/` — steht in `.gitignore` und liegt im Repo.
- Hilfskonstrukte wie die `TamaPoke`-Junction an einen festen Ort neben das Repo,
  nicht in ein Temp-Verzeichnis.
- **Vor dem Melden nachprüfen**, und zwar so, wie der Nutzer es aufruft: neue
  PowerShell, in den Repo-Ordner, Befehl ohne absoluten Pfad. Ein `core list`,
  das nur in deiner Shell funktioniert, ist nicht eingerichtet.

Ein länger laufender Hintergrund-Install ist erst fertig, wenn er fertig ist —
währenddessen zeigt `arduino-cli core list` „No platforms installed". Das Ergebnis
melden, nicht den Zwischenstand.
