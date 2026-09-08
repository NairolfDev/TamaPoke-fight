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
