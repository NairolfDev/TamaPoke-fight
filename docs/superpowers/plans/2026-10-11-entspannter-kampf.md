# Entspannter Kampf — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** TamaPoke soll ein chilliges, einfaches Spiel sein: kein Kampf darf zur Wand werden, niemand bleibt dauerhaft hängen, und die Regeln werden einfacher statt komplizierter.

**Architecture:** Drei Strukturfehler werden behoben, nicht einzelne Zahlen gedreht. (1) Eine Mitleidsregel ohne Deckel senkt nach jeder Niederlage in Folge das Gegnerlevel auf drei Viertel — ein Sieg ist nach wenigen Versuchen garantiert. (2) Die Arena verlangt keine drei Siege am Stück mehr: Fortschritt wird pro Gegner gespeichert, jeder Arenakampf ist ein ganz normaler Kampf mit vollen HP. (3) Arena-Teams ohne Typ-Sackgassen, ohne Rivalen, nach gemessener Schwierigkeit sortiert. Dazu: wilde Gegner nie über Spielerlevel, XP unabhängig vom Gegnerlevel, Rivale auf Spielerlevel mit milder KI.

**Tech Stack:** Arduino-C++ (ESP32-S3, arduino-cli 1.5.2, Core esp32 3.3.11), Python 3.13 für `tools/battle_sim.py` (Zwilling der Engine), Build über `tools\build.ps1`.

**Spec:** `docs/BATTLE_SPEC.md` (§4.3, §5.5, §6.3, §6.6, §6.7, §7, §8) plus die Richtungsentscheidung des Nutzers vom 2026-10-11: *„es soll ein chilliges einfaches Spiel sein und nicht so eine krasse Herausforderung"*. Dieser Plan ändert die Spec; Task 6 zieht sie nach.

## Warum diese Änderungen — die Messungen

Alle Zahlen aus `battle_sim.py`, Spieler mit zufälliger Spezies, Elite-KI, ohne Training und Bindung.

**Heute, Arena-Rang geschafft (drei Siege am Stück, keine Heilung):**
Rang 1: 18 %, Rang 5: 5 %, Rang 8: 1 %. Mit voller Bindung und Beere Rang 8 höchstens 13 %.

**Ursache 1 — Multiplikation.** Wer einen Einzelkampf zu 70 % gewinnt, schafft drei am Stück nur zu 34 %. Selbst mit Heilung, Gegnern unter Spielerlevel und schwacher KI bleibt Rang 1 bei 36 %.

**Ursache 2 — Typ-Sackgassen.** Pikachu/Raichu (25/26) haben nur Elektro-Attacken, Boden ist immun: Rang 1 (Gestein/Boden) und Rang 8 (Boden) sind für sie **unmöglich**, egal wie oft man es versucht. Tragosso/Knogga (104/105) haben nur Boden-Attacken, Flug ist immun. Pikachu und Tragosso sind **Starter**.

**Ursache 3 — kein Sicherheitsnetz.** §6.7 beschreibt eine Mitleidsregel, `lossStreak` wird gezählt und gespeichert — aber **nirgends angewendet**. Und eine Mitleidsregel mit Deckel (−8 Level) reicht nicht: sehr schwache Spezies (Karpador, Raupy) verlieren auch dann noch.

**Ursache 4 — XP strafen schwache Gegner.** `xpGainFor()` rechnet `12 + 4·(Gegnerlevel − Spielerlevel)` %. Senkt man die Gegnerlevel, sinken die XP — das Leveln würde *langsamer*, also das Gegenteil von chillig.

**Mit allen Änderungen dieses Plans (Erkundungslauf, Seed 1):**

| | Sieg beim 1. Versuch | Versuche im Schnitt | 90 % brauchen höchstens | schlimmster Fall |
|---|---|---|---|---|
| Levelkampf Lv 15 | 59 % | 1,65 | 3 | 7 |
| Levelkampf Lv 30 | 63 % | 1,52 | 3 | 6 |
| Levelkampf Lv 50 | 67 % | 1,42 | 2 | 5 |
| Rivale Lv 30 | 57 % | 2,09 | 3 | — |
| Arena, ganzer Rang (3 = perfekt) | 39–77 % je Kampf | 4,0–6,5 Kämpfe | 6–11 Kämpfe | — |

Null Typ-Sackgassen im neuen Teamsatz, geprüft für jede Spezies auf Level 5–50.

## Global Constraints

- **Alle Quelldateien sind CRLF.** Mehrzeilige Patches als Python-Skript**datei** im Scratchpad (nie als Heredoc), binär lesen, auf `\n` normalisieren, jedes Muster auf **genau einen** Treffer prüfen und sonst abbrechen, Original-Zeilenende zurückschreiben. Danach `git diff` lesen.
- **Build nur über** `tools\build.ps1` aus einer normalen PowerShell im Repo-Ordner. Gegenprobe: das geänderte Konstrukt im Binary `build\battle\TamaPoke.ino.bin` suchen, nicht der Größe glauben.
- **Jede Engine-Änderung in `battle.cpp` UND `tools/battle_sim.py`.** Danach `python3 tools/battle_sim.py --self-test` grün und die Referenz `python3 tools/battle_sim.py --n 20000 --level 25 --player-ai elite --ai wild --bond 0 --spread 0` bei 56,19 % ± 3 (also 53,2–59,2 %). Die Referenz ist gleichstufig und ändert sich durch diesen Plan **nicht** — weicht sie ab, ist etwas kaputt.
- **Kommentare deutsch, Bezeichner englisch, keine hartkodierten UI-Strings.** Dieser Plan braucht keine neuen UI-Strings.
- **Neue NVS-Felder:** Default in `load()`, Schlüssel ≤ 15 Zeichen, Key-Value, kein `nvsVer`-Schritt, kein `WIPE`.
- **Nicht flashen.** Nur `main`, kleine Commits, jeder kompiliert, danach pushen. Commit-Ende: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Prüfschritte jedes Tasks** werden in `docs/GERAETETEST.md` vor `# Teil B` angehängt.
- **Balancing entscheidet der Nutzer.** Verfehlt Task 6 ein Ziel, wird gemeldet, nicht nachjustiert.

## Review Focus

1. **Altgerät mit `arenaRank` > 0 aus dem alten Teamsatz:** die Ränge werden neu sortiert, der gespeicherte Rang bedeutet weiter „so viele Ränge geschafft". Erwartet: kein Absturz, der nächste Rang ist `arenaRank + 1` im neuen Satz, `arenaStep` fehlt in NVS und ist 0. Test in Task 5, Schritt 1.
2. **`lossStreak` am Anschlag (255) oder Spielerlevel 1:** das Gegnerlevel darf nie 0 werden — Level 0 zerbricht die HP-Formel. Test in Task 1, Schritt 1.
3. **Erschöpfungsspirale:** jede Niederlage kostet −15 Energie, unter 20 Energie gelten −25 % ATK/SPD, das macht die nächste Niederlage wahrscheinlicher. Erwartet: die Mitleidsregel ist schneller als die Spirale, auch mit Energie 10 ist ein Levelkampf im Schnitt in ≤ 3 Versuchen gewonnen. Test im Abnahmebericht, Task 6.
4. **Level 100:** Gegner nie über Spielerlevel, Rivale nicht über 100, Arenagegner nicht über 100. Test in Task 2 (Schleife bis 100) und Task 5.
5. **Immunität beim Rivalen:** der Rivale ist ein beliebiges früheres Pokémon, eine Typ-Sackgasse ist dort möglich (z. B. früheres Onix gegen neues Pikachu). Erwartet: der Rivale ist optional und kein Fortschrittstor; der Tag wird nur durch einen **Sieg** verbraucht, ein Spieler kann also einfach nicht antreten. Dokumentiert in Task 4, kein Test — das ist eine Eigenschaft, kein Fehler.

---

## Datei-Landkarte

| Datei | Verantwortung | Tasks |
|---|---|---|
| `battle.h` / `battle.cpp` | Engine: Gegnerlevel, Mitleid, Arenateams | 1, 2, 4, 5 |
| `pet.h` / `pet.cpp` | Zustand: XP, Rivalenlevel, Arena-Fortschritt | 2, 4, 5 |
| `TamaPoke.ino` | Kampfstart, Konsole | 1, 5 |
| `tools/battle_sim.py` | Zwilling + Selbsttest + Abnahmebericht | 1–6 |
| `docs/BATTLE_SPEC.md` | Spec nachziehen | 6 |
| `docs/GERAETETEST.md` | Prüfschritte am Gerät | 1–5 |

Nicht in diesem Plan: der UI-Einstieg in Rivalen- und Arenakampf (B6/D6). Er wird durch diesen Plan **einfacher** — ein Arenakampf ist danach ein gewöhnlicher Kampf gegen einen festen Gegner und läuft durch das vorhandene `btFinish()`.

---

### Task 1: Mitleidsregel ohne Deckel

Nach jeder Niederlage in Folge kämpft der nächste Gegner auf drei Vierteln des Levels, Untergrenze 1. Gilt für jeden Kampf. Ersetzt die nie angewendete Regel aus §6.7 („ab 3: −1 je weiterer, max −4").

**Files:**
- Modify: `tools/battle_sim.py` (neue Funktion vor `def make_player`, Selbsttest vor `# Ein Kampf laeuft durch`)
- Modify: `battle.h` (Deklaration nach `uint8_t pickFoeLevel(...)`)
- Modify: `battle.cpp` (Definition nach `pickFoeLevel()`)
- Modify: `TamaPoke.ino:466` (`battleCmd`) und `TamaPoke.ino:1386` (`startBattle`)
- Modify: `docs/GERAETETEST.md`

**Interfaces:**
- Consumes: `Pet::lossStreak` (`uint8_t`, existiert, wird von `battleWin()` auf 0 gesetzt und von `battleLoss()` erhöht)
- Produces: C `uint8_t pityLevel(uint8_t level, uint8_t lossStreak)`; Python `pity_level(level, loss_streak) -> int`. Beide nie < 1, für `lossStreak == 0` unverändert.

- [ ] **Step 1: Selbsttest schreiben, der fehlschlägt**

In `tools/battle_sim.py` vor der Zeile `    # Ein Kampf laeuft durch und endet mit gueltigem Ergebnis` einfügen:

```python
    # Mitleid: jede Niederlage in Folge -> drei Viertel des Levels, nie 0
    assert pity_level(30, 0) == 30
    assert pity_level(30, 1) == 22
    assert pity_level(30, 2) == 16
    assert pity_level(2, 1) == 1
    assert pity_level(1, 5) == 1, 'Level 0 zerbricht die HP-Formel'
    assert pity_level(100, 255) == 1
    for lv in range(1, 101):
        prev = lv
        for k in range(12):
            cur = pity_level(lv, k)
            assert 1 <= cur <= prev, (lv, k)
            prev = cur
```

- [ ] **Step 2: Selbsttest laufen lassen, er muss scheitern**

Run: `python3 tools/battle_sim.py --self-test`
Expected: `NameError: name 'pity_level' is not defined`

- [ ] **Step 3: Python-Funktion einfügen**

In `tools/battle_sim.py` direkt vor `def make_player(dex, level, rng, bond=0, energy=100, berry=False):` einfügen:

```python
# Mitleid (ersetzt 6.7 "ab 3: -1 je weiterer, max -4"): jede Niederlage in
# Folge senkt das Gegnerlevel auf drei Viertel. Ohne Deckel - nur so ist ein
# Sieg auch mit sehr schwachen Spezies nach wenigen Versuchen garantiert.
def pity_level(level, loss_streak):
    for _ in range(loss_streak):
        if level <= 1:
            break
        level = level * 3 // 4
    return max(1, level)


```

- [ ] **Step 4: Selbsttest laufen lassen**

Run: `python3 tools/battle_sim.py --self-test`
Expected: `Selbsttest OK`

- [ ] **Step 5: Engine-Zwilling in C**

`battle.h`, direkt nach der Zeile `uint8_t pickFoeLevel(uint8_t playerLevel, uint8_t spread);`:

```c
// Mitleid: jede Niederlage in Folge senkt das Gegnerlevel auf drei Viertel,
// Untergrenze 1. Ohne Deckel, damit niemand haengen bleibt.
uint8_t pityLevel(uint8_t level, uint8_t lossStreak);
```

`battle.cpp`, direkt nach der schließenden `}` von `uint8_t pickFoeLevel(...)`:

```c

uint8_t pityLevel(uint8_t level, uint8_t lossStreak) {
  uint16_t l = level;
  for (uint8_t i = 0; i < lossStreak && l > 1; i++) l = l * 3 / 4;
  return l < 1 ? 1 : (uint8_t)l;
}
```

- [ ] **Step 6: Anwenden in Kampfstart und Konsole**

`TamaPoke.ino`, in `startBattle()`:

```c
  fighterFromDex(btFo, dex, pickFoeLevel(btPl.level, 2), shiny);
```
ersetzen durch
```c
  // Mitleid: nach Niederlagen in Folge kommt ein schwaecherer Gegner
  fighterFromDex(btFo, dex, pityLevel(pickFoeLevel(btPl.level, 2), pet.lossStreak),
                 shiny);
```

`TamaPoke.ino`, in `battleCmd()`:

```c
  fighterFromDex(fo, dex, pickFoeLevel(pl.level, 2), shiny);
```
ersetzen durch
```c
  fighterFromDex(fo, dex, pityLevel(pickFoeLevel(pl.level, 2), pet.lossStreak),
                 shiny);
```

`STATS` soll den Zähler zeigen, damit man es am Gerät sieht. In `handleSerial()` die Zeile

```c
    Serial.printf("shiny=%d streak=%u/%u bond=%u medals=0x%X(%u) nick=%s\n",
                  pet.shiny, pet.streak, pet.bestStreak, pet.bond, pet.medals,
                  pet.totalMedals, pet.nick);
```
ersetzen durch
```c
    Serial.printf("shiny=%d streak=%u/%u bond=%u medals=0x%X(%u) nick=%s pech=%u\n",
                  pet.shiny, pet.streak, pet.bestStreak, pet.bond, pet.medals,
                  pet.totalMedals, pet.nick, pet.lossStreak);
```

- [ ] **Step 7: Bauen und gegenprüfen**

Run: `tools\build.ps1` (PowerShell, Repo-Ordner)
Expected: Exitcode 0, `Sketch uses …`
Gegenprobe: `python3 -c "print(open('build/battle/TamaPoke.ino.bin','rb').read().count(b'pech=%u'))"` → `1`
Referenzmessung (siehe Global Constraints) → 53,2–59,2 %.

- [ ] **Step 8: Prüfschritte anhängen**

In `docs/GERAETETEST.md` vor `# Teil B` einfügen:

```markdown
## A14. Mitleidsregel

Nach jeder Niederlage in Folge kommt der nächste Gegner auf drei Vierteln des
Levels, Untergrenze 1. Ein Sieg setzt zurück.

1. `LVL 30`, `STATS` → `pech=0`.
2. `ENE 100`, dann absichtlich verlieren (fliehen zählt **nicht**, nur ein
   verlorener Kampf). `STATS` → `pech=1`.
3. `BATTLE 25` → der Gegner steht auf etwa 22 statt 28–30. Noch eine
   Niederlage → etwa 16.
4. Einen Kampf gewinnen → `pech=0`, die Gegner sind wieder auf 28–30.
5. Neustart zwischendurch → `pech` bleibt (liegt unter `lstrk` in NVS).
```

- [ ] **Step 9: Commit**

```bash
git add battle.h battle.cpp TamaPoke.ino tools/battle_sim.py docs/GERAETETEST.md
git commit -m "Mitleidsregel: Gegnerlevel drei Viertel je Niederlage in Folge" -m "lossStreak wurde seit Phase 5 gezaehlt, aber nie angewendet. Ohne Deckel, Untergrenze 1." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push origin main
```

---

### Task 2: Wilde Gegner nie über Spielerlevel, XP unabhängig vom Gegnerlevel

Gegnerlevel `Spielerlevel − 2 … Spielerlevel` statt `± 2`. Damit schwächere Gegner das Leveln nicht verlangsamen, gibt jeder Sieg pauschal 12 % von `lvlReq()` — so viel wie heute ein gleichstarker Gegner, also weiter rund acht Kämpfe pro Level.

**Files:**
- Modify: `tools/battle_sim.py` (`foe_level_range`, Kommentar darüber, Selbsttest-Block „Gegnerlevel nach 6.3")
- Modify: `battle.cpp` (`foeLevelRange`), `battle.h` (Kommentar)
- Modify: `pet.h` (`xpGainFor`)
- Modify: `docs/GERAETETEST.md`

**Interfaces:**
- Consumes: nichts Neues
- Produces: `foeLevelRange(pl, spread, &lo, &hi)` liefert jetzt `hi == pl`; Python `foe_level_range(pl, spread) -> (max(1, pl - spread), pl)`. `Pet::xpGainFor(uint8_t)` ignoriert sein Argument (Signatur bleibt, Aufrufer bleiben unverändert).

- [ ] **Step 1: Selbsttest umschreiben, er muss scheitern**

In `tools/battle_sim.py` diesen Block ersetzen (Anfang bis einschließlich der `{1, 2, 3}`-Zeile):

```python
    # Gegnerlevel nach 6.3: die Spanne schrumpft nahe am Boden.
    assert foe_level_range(1) == (1, 1), 'Lv1 kaempft gleichstufig'
    assert foe_level_range(2) == (1, 3)
    assert foe_level_range(3) == (1, 5)
    assert foe_level_range(4) == (2, 6), 'ab Lv4 volle Spanne'
    assert foe_level_range(5) == (3, 7)
    assert foe_level_range(25) == (23, 27)
    # Kern der Regel: auf jedem Level symmetrisch um das Spielerlevel, und
    # nie unter 1. Genau das leistete die alte Untergrenze 2 nicht.
    for lv in range(1, 60):
        low, high = foe_level_range(lv)
        assert lv - low == high - lv, 'unsymmetrisch auf Level %d' % lv
        assert low >= 1, 'Untergrenze 1 verletzt auf Level %d' % lv
    # spread 0 heisst gleichstufig
    assert foe_level_range(1, 0) == (1, 1)
    assert foe_level_range(25, 0) == (25, 25)
    # gezogene Level bleiben in der Spanne und schoepfen sie aus
    rng = random.Random(11)
    assert {pick_foe_level(1, rng) for _ in range(200)} == {1}
    assert {pick_foe_level(2, rng) for _ in range(400)} == {1, 2, 3}
```

durch

```python
    # Gegnerlevel nach 6.3 (entspannt): nie ueber dem Spielerlevel, bis zu
    # spread darunter, nie unter 1.
    assert foe_level_range(1) == (1, 1), 'Lv1 kaempft gleichstufig'
    assert foe_level_range(2) == (1, 2)
    assert foe_level_range(3) == (1, 3)
    assert foe_level_range(4) == (2, 4)
    assert foe_level_range(25) == (23, 25)
    for lv in range(1, 101):
        low, high = foe_level_range(lv)
        assert high == lv, 'Gegner ueber Spielerlevel auf Level %d' % lv
        assert low >= 1, 'Untergrenze 1 verletzt auf Level %d' % lv
    # spread 0 heisst gleichstufig - darauf steht die BSIM-Referenz
    assert foe_level_range(1, 0) == (1, 1)
    assert foe_level_range(25, 0) == (25, 25)
    rng = random.Random(11)
    assert {pick_foe_level(1, rng) for _ in range(200)} == {1}
    assert {pick_foe_level(2, rng) for _ in range(400)} == {1, 2}
```

Run: `python3 tools/battle_sim.py --self-test`
Expected: `AssertionError` bei `foe_level_range(2) == (1, 2)`

- [ ] **Step 2: Python umstellen**

Den Kommentarblock über `FOE_LEVEL_SPREAD = 2` (beginnt mit `# 6.3: Gegnerlevel ist Spielerlevel +/- spread.`, endet mit `# Spielerlevel. Harte Untergrenze ist 1.`) ersetzen durch:

```python
# 6.3 (entspannt): Gegnerlevel liegt zwischen Spielerlevel - spread und dem
# Spielerlevel, nie darueber. Nahe am Boden schrumpft die Spanne, harte
# Untergrenze ist 1.
```

Und in `foe_level_range` die Zeile

```python
    return max(1, player_level - reach), player_level + reach
```
ersetzen durch
```python
    return max(1, player_level - reach), player_level
```

Run: `python3 tools/battle_sim.py --self-test` → `Selbsttest OK`

- [ ] **Step 3: C-Zwilling**

`battle.cpp`, in `foeLevelRange`:

```c
  if (high) *high = (uint8_t)(playerLevel + reach);
```
ersetzen durch
```c
  if (high) *high = playerLevel;  // 6.3 entspannt: nie ueber dem Spieler
```

Und den Kommentar direkt über `void foeLevelRange(` (`// 6.3: die Spanne schrumpft am Boden, statt unten abgeschnitten zu werden.`) ersetzen durch:

```c
// 6.3 (entspannt): Gegnerlevel zwischen Spielerlevel - spread und dem
// Spielerlevel, nie darueber. Die Spanne schrumpft am Boden, Untergrenze 1.
```

`battle.h`: die Zeile `// 6.3: Gegnerlevel Spielerlevel +/- spread, Spanne schrumpft am Boden.` ersetzen durch `// 6.3 (entspannt): Gegnerlevel Spielerlevel - spread bis Spielerlevel.`

- [ ] **Step 4: XP pauschal**

`pet.h`, in `xpGainFor`:

```c
    int pct = 12 + 4 * ((int)foeLevel - (int)level());
    if (pct < 5) pct = 5;
    if (pct > 25) pct = 25;
    return (uint16_t)((uint32_t)lvlReq() * pct / 100);
```
ersetzen durch
```c
    // 4.3 (entspannt): pauschal 12 % pro Sieg, rund acht Kaempfe pro Level.
    // Haengt nicht mehr am Gegnerlevel - sonst wuerden die schwaecheren
    // Gegner und die Mitleidsregel das Leveln verlangsamen.
    (void)foeLevel;
    return (uint16_t)((uint32_t)lvlReq() * 12 / 100);
```

- [ ] **Step 5: Bauen, gegenprüfen, Referenz**

Run: `tools\build.ps1` → Exitcode 0.
Gegenprobe: Flash-Größe muss sich gegenüber Task 1 um mehr als 65 Byte unterscheiden (der Klemmcode in `xpGainFor` fällt weg); zusätzlich `git diff battle.cpp` zeigt die `*high`-Zeile.
Run: `python3 tools/battle_sim.py --self-test` → `Selbsttest OK`
Referenzmessung → 53,2–59,2 % (spread 0, unverändert).

- [ ] **Step 6: Prüfschritte anhängen**

```markdown
## A15. Gegner nie über Spielerlevel, XP pauschal

1. `LVL 20`, `pech=0` (siehe A14). Zehnmal `BATTLE 25` → das Gegnerlevel in der
   ersten Zeile liegt **immer** zwischen 18 und 20, nie bei 21 oder 22.
2. `LVL 1` → `BATTLE 25` kämpft immer auf Level 1.
3. Statuskarte Seite 4: XP-Balken notieren, einen freien Kampf gewinnen → der
   Balken wächst um rund ein Achtel, egal welches Level der Gegner hatte.
```

- [ ] **Step 7: Commit**

```bash
git add battle.h battle.cpp pet.h tools/battle_sim.py docs/GERAETETEST.md
git commit -m "Wilde Gegner nie ueber Spielerlevel, XP pauschal 12 Prozent" -m "Schwaechere Gegner duerfen das Leveln nicht verlangsamen." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push origin main
```

---

### Task 3: Selbsttest — keine Typ-Sackgassen

Eine Prüfung, die jede künftige Teamänderung absichert: kein Arenagegner darf für irgendeine Spezies auf irgendeinem Level unverwundbar sein. Sie schlägt **heute** fehl (Pikachu gegen Rang 1/8, Tragosso gegen niemanden mehr nach Task 5) und wird in Task 5 grün.

**Files:**
- Modify: `tools/battle_sim.py` (Selbsttest)

**Interfaces:**
- Consumes: `ARENA_TEAMS` (Liste von 3-Tupeln), `moves_for_level(dex, level)`, `move_power(move_id)`, `effectiveness(move_id, defender)`, `Combatant(dex, level)`, `BASE_STATS`
- Produces: Funktion `arena_dead_ends() -> list[(rank, foe_dex, player_dex, level)]`, von Task 5 und 6 benutzt

- [ ] **Step 1: Funktion und Prüfung schreiben**

In `tools/battle_sim.py` direkt nach der Definition von `ARENA_TEAMS` (und dem darauf folgenden Leerzeilenblock) einfügen:

```python
def arena_dead_ends():
    """Paarungen, in denen der Spieler einem Arenagegner keinen Schaden
    machen kann - jede Attacke hat Staerke 0 oder ist wirkungslos. Ein
    solcher Rang waere fuer diese Spezies fuer immer gesperrt."""
    out = []
    for rank, team in enumerate(ARENA_TEAMS, 1):
        for dex in team:
            if not dex:
                continue
            foe = Combatant(dex, 30)
            for p in BASE_STATS:
                for lv in (5, 10, 20, 30, 40, 50):
                    if all(move_power(m) == 0 or effectiveness(m, foe) == 0
                           for m in moves_for_level(p, lv)):
                        out.append((rank, dex, p, lv))
    return out
```

Im Selbsttest, direkt vor `    # Ein Kampf laeuft durch und endet mit gueltigem Ergebnis`:

```python
    # Keine Typ-Sackgassen: jede Spezies kann jeden Arenagegner verletzen.
    # Sonst ist ein Rang fuer sie gesperrt, egal wie oft sie es versucht.
    dead = arena_dead_ends()
    assert not dead, 'Sackgassen (Rang, Gegner, Spieler, Lv): %s' % dead[:6]
```

- [ ] **Step 2: Laufen lassen, muss scheitern**

Run: `python3 tools/battle_sim.py --self-test`
Expected: `AssertionError: Sackgassen (Rang, Gegner, Spieler, Lv): [(1, 74, 25, 5), …]`

- [ ] **Step 3: Nicht committen**

Der rote Selbsttest gehört in denselben Commit wie seine Lösung (Task 5). Nichts committen, direkt weiter mit Task 4; Task 5 nimmt `tools/battle_sim.py` mit.

---

### Task 4: Rivale entspannt

Der Rivale kämpft auf Spielerlevel statt +2, mit der Arena-KI statt der Elite-KI, und der Tag wird nur durch einen **Sieg** verbraucht — nach einer Niederlage darf man sofort nochmal. Der Rivale bleibt aus der Arena draußen (Task 5).

**Files:**
- Modify: `pet.h` (`rivalLevel`, Kommentar zu `markRivalFought`)
- Modify: `battle.h` (neue Konstante `RIVAL_AI`)
- Modify: `tools/battle_sim.py` (`rival_level`, `simulate`, CLI-Ausgabe, Selbsttest)
- Modify: `docs/GERAETETEST.md` (A11 anpassen)

**Interfaces:**
- Consumes: nichts Neues
- Produces: `Pet::rivalLevel()` liefert `level()`; `#define RIVAL_AI AI_ARENA` in `battle.h` — der spätere UI-Einstieg (B6) startet den Rivalenkampf mit `RIVAL_AI` und ruft `pet.markRivalFought()` **nur bei Sieg** in `btFinish()`.

- [ ] **Step 1: Selbsttest anpassen, muss scheitern**

In `tools/battle_sim.py` im Selbsttest:

```python
    assert rival_level(25) == 27 and rival_level(99) == 100
    rng = random.Random(5)
    assert pick_rival(10, rng, 4, False).dex == 4
    assert pick_rival(10, rng, 0, False).level == 12
```
ersetzen durch
```python
    assert rival_level(25) == 25 and rival_level(100) == 100
    rng = random.Random(5)
    assert pick_rival(10, rng, 4, False).dex == 4
    assert pick_rival(10, rng, 0, False).level == 10
```

Run: `python3 tools/battle_sim.py --self-test` → scheitert bei `rival_level(25) == 25` (Task 3 ist noch rot und steht davor — die Reihenfolge der Asserts entscheidet, was zuerst meldet; beide Fehler sind erwartet).

- [ ] **Step 2: Python umstellen**

```python
# 5.5: der Rivale kaempft immer auf Spielerlevel + 2, gedeckelt bei 100.
def rival_level(player_level):
    return min(player_level + 2, 100)
```
ersetzen durch
```python
# 5.5 (entspannt): der Rivale kaempft auf Spielerlevel.
def rival_level(player_level):
    return player_level
```

In `simulate`:

```python
            ai = AI_ELITE   # 6.6: Rivale = staerkste Attacke
```
ersetzen durch
```python
            ai = AI_ARENA   # 6.6 (entspannt): Rivale waehlt wie Arena 1-4
```

Im Docstring von `simulate` den Satz `Spielerlevel + 2, mit der Elite-KI aus 6.6 - foe_ai gilt dann nicht.` ersetzen durch `Spielerlevel, mit der Arena-KI - foe_ai gilt dann nicht.`

In `main()`:

```python
        print('%d Kaempfe, Level %d gegen Rivale %s auf Lv %d%s (KI: elite)'
```
ersetzen durch
```python
        print('%d Kaempfe, Level %d gegen Rivale %s auf Lv %d%s (KI: arena)'
```

Und im `--rival`-Hilfetext `'zufaelliges frueheres Pokemon. Level Spieler+2, Elite-KI')` ersetzen durch `'zufaelliges frueheres Pokemon. Level Spieler, Arena-KI')`.

- [ ] **Step 3: C-Seite**

`pet.h`:

```c
  // 5.5: einmal pro echtem Kalendertag. markRivalFought() beim Kampfstart,
  // damit Flucht und Niederlage den Tag ebenfalls verbrauchen.
```
ersetzen durch
```c
  // 5.5: einmal pro echtem Kalendertag. markRivalFought() nur nach einem
  // SIEG - nach einer Niederlage darf man gleich nochmal (entspannt).
```

```c
  uint8_t rivalLevel() const {  // 5.5: immer Spielerlevel + 2
    uint16_t l = level() + 2;
    return l > LEVEL_CAP ? LEVEL_CAP : (uint8_t)l;
  }
```
ersetzen durch
```c
  uint8_t rivalLevel() const { return level(); }  // 5.5 (entspannt)
```

`battle.h`, direkt nach dem `enum`-Block mit `AI_WILD, AI_ARENA, AI_ELITE`:

```c
// 6.6 (entspannt): der Rivale waehlt wie Arena Rang 1-4, nicht wie die Elite.
#define RIVAL_AI AI_ARENA
```

- [ ] **Step 4: Prüfschritte anpassen**

In `docs/GERAETETEST.md`, Abschnitt A11, Schritt 1: `darunter die Kampfwerte auf **Spielerlevel + 2**` ersetzen durch `darunter die Kampfwerte auf **Spielerlevel**`. Am Ende von A11 ergänzen:

```markdown
Entspannt (Plan 2026-10-11): der Rivale kämpft auf Spielerlevel mit der
Arena-KI, und nur ein **Sieg** verbraucht den Tag. Prüfbar, sobald der
UI-Einstieg (B6) gebaut ist.
```

- [ ] **Step 5: Nicht committen**

Der Selbsttest ist noch rot (Task 3). Weiter mit Task 5, ein gemeinsamer Commit nach Task 5 hält jeden Commit grün.

---

### Task 5: Arena entschärft

Fortschritt pro Gegner, jeder Arenakampf ist ein gewöhnlicher Kampf (volle HP, normale Kosten, normale XP, Flucht erlaubt), kein Rivale, neue Teams ohne Sackgassen, nach Schwierigkeit sortiert, Gegner unter oder auf Spielerlevel, milde KI.

**Neue Ränge** (Reihenfolge nach gemessener Schwierigkeit, leicht → schwer):

| Rang | Thema | Team | Gegnerlevel | KI |
|---|---|---|---|---|
| 1 | Wasser | 120 Sterndu, 118 Goldini, 121 Starmie | Spieler −2 | wild |
| 2 | Elektro | 100 Voltobal, 25 Pikachu, 101 Lektrobal | Spieler −2 | wild |
| 3 | Pflanze | 114 Tangela, 70 Ultrigaria, 45 Giflor | Spieler −1 | wild |
| 4 | Gift | 109 Smogon, 89 Sleimok, 110 Smogmog | Spieler −1 | wild |
| 5 | Gestein | 138 Amonitas, 140 Kabuto, 141 Kabutops | Spieler −1 | arena |
| 6 | Psycho | 64 Kadabra, 122 Pantimos, 97 Hypno | Spielerlevel | arena |
| 7 | Kampf | 57 Rasaff, 68 Machomei, 106 Kicklee | Spielerlevel | arena |
| 8 | Feuer | 58 Fukano, 78 Gallopa, 59 Arkani | Spielerlevel | arena |

Gestein ohne Boden-Doppeltyp (Pikachu), kein Flug-Doppeltyp (Tragosso), Boden ganz raus.

**Files:**
- Modify: `battle.h`, `battle.cpp` (Arenablock)
- Modify: `pet.h`, `pet.cpp` (`arenaStep`, `arenaFoeBeaten`)
- Modify: `TamaPoke.ino` (`arenaCmd`)
- Modify: `tools/battle_sim.py` (Arenablock, CLI, Selbsttest)
- Modify: `docs/GERAETETEST.md` (A13 ersetzen)

**Interfaces:**
- Consumes: `pityLevel()` (Task 1), `arena_dead_ends()` (Task 3), `RIVAL_AI` (Task 4, hier nicht benutzt)
- Produces:
  - C `extern const uint16_t ARENA_TEAMS[ARENA_RANKS][3];` (kein 0 mehr)
  - C `uint8_t arenaFoeLevel(uint8_t rank, uint8_t playerLevel);` — Untergrenze 1, nie über 100
  - C `uint8_t arenaFoeAi(uint8_t rank);` — `AI_WILD` für 1–4, `AI_ARENA` für 5–8
  - C `void arenaFoe(Fighter &f, uint8_t rank, uint8_t idx, uint8_t playerLevel, uint8_t lossStreak);`
  - C `Pet::arenaStep` (`uint8_t`, 0–2, Gegner im laufenden Rang bereits besiegt), `void Pet::arenaFoeBeaten();`
  - entfernt: `arenaNextFight()`, `arenaRun()` (C und Python), `Rival`-Parameter von `arenaFoe`
  - Python `ARENA_TEAMS`, `ARENA_THEMES`, `ARENA_LEVEL_OFFSET`, `arena_foe_level`, `arena_ai`, `arena_rank_fights(pdex, level, rank, rng, berry=False, bond=0) -> int`

- [ ] **Step 1: Selbsttest-Block für die Arena ersetzen**

In `tools/battle_sim.py` den Block von `    # 7: Arena. Teams typtreu und ohne Legendaere, Level nach Tabelle,` bis einschließlich `    assert (res, k) == ('win', 3) or (res == 'loss' and 1 <= k <= 3)` ersetzen durch:

```python
    # 7 (entspannt): Teams typtreu, ohne Legendaere, ohne Rivalen; Level nie
    # ueber dem Spieler, nie unter 1; Fortschritt pro Gegner.
    for rank, (team, theme) in enumerate(zip(ARENA_TEAMS, ARENA_THEMES), 1):
        assert len(team) == 3 and 0 not in team, 'kein Rivale in der Arena'
        for dex in team:
            assert TYPE_ID[theme] in species_types(dex), (rank, dex)
            assert dex not in LEGENDARY
    assert ARENA_THEMES == ['water', 'electric', 'grass', 'poison', 'rock',
                            'psychic', 'fighting', 'fire']
    assert arena_foe_level(1, 20) == 18 and arena_foe_level(5, 20) == 19
    assert arena_foe_level(8, 20) == 20 and arena_foe_level(8, 100) == 100
    assert arena_foe_level(1, 1) == 1, 'Untergrenze 1'
    assert arena_ai(4) == AI_WILD and arena_ai(5) == AI_ARENA
    rng = random.Random(4)
    k = arena_rank_fights(6, 30, 1, rng)
    assert 3 <= k <= 3 * ARENA_TRY_CAP, k
```

Run: `python3 tools/battle_sim.py --self-test`
Expected: scheitert (`ARENA_THEMES` hat die alte Reihenfolge bzw. `arena_rank_fights` fehlt).

- [ ] **Step 2: Python-Arenablock ersetzen**

In `tools/battle_sim.py` den gesamten Block von `# Wie ARENA_TEAMS in battle.cpp: Gestein, Wasser, Elektro, Pflanze, Gift,` bis einschließlich der `return wins, reached`-Zeile von `simulate_arena` ersetzen durch (`arena_dead_ends()` aus Task 3 bleibt **nach** `ARENA_TEAMS` stehen — beim Ersetzen mitnehmen):

```python
# Wie ARENA_TEAMS in battle.cpp, nach gemessener Schwierigkeit sortiert.
# Kein Rivale, kein Boden (Pikachu waere immun-gesperrt), kein Flug-Doppel-
# typ (Tragosso). arena_dead_ends() im Selbsttest haelt das fest.
ARENA_TEAMS = [(120, 118, 121), (100, 25, 101), (114, 70, 45), (109, 89, 110),
               (138, 140, 141), (64, 122, 97), (57, 68, 106), (58, 78, 59)]
ARENA_THEMES = ['water', 'electric', 'grass', 'poison', 'rock', 'psychic',
                'fighting', 'fire']
ARENA_LEVEL_OFFSET = [-2, -2, -1, -1, -1, 0, 0, 0]
ARENA_TRY_CAP = 30   # nur fuer die Messung: so viele Versuche pro Gegner max.


def arena_foe_level(rank, player_level):
    return max(1, min(player_level + ARENA_LEVEL_OFFSET[rank - 1], 100))


def arena_ai(rank):
    return AI_WILD if rank <= 4 else AI_ARENA
```

Dann `arena_dead_ends()` aus Task 3 unverändert hier einfügen, danach:

```python


def arena_rank_fights(pdex, level, rank, rng, berry=False, bond=0):
    """Wie viele Kaempfe braucht diese Spezies fuer den ganzen Rang? Jeder
    Arenakampf ist ein gewoehnlicher Kampf mit vollen HP; ein Sieg hakt den
    Gegner ab, eine Niederlage erhoeht das Pech (Mitleidsregel)."""
    fights = 0
    streak = 0
    for dex in ARENA_TEAMS[rank - 1]:
        for _ in range(ARENA_TRY_CAP):
            fights += 1
            player = make_player(pdex, level, rng, bond, 100, berry)
            foe = make_foe(dex, pity_level(arena_foe_level(rank, level), streak))
            if run_battle(player, foe, rng, AI_ELITE, arena_ai(rank))[0] == 'win':
                streak = 0
                break
            streak += 1
    return fights
```

- [ ] **Step 3: Python-CLI umstellen**

In `main()` den `if args.arena is not None:`-Block (bis einschließlich seines `return 0`) ersetzen durch:

```python
    if args.arena is not None:
        xs = sorted(arena_rank_fights(args.player_dex or rng.choice(WILD_POOL),
                                      args.level, args.arena, rng, args.berry,
                                      args.bond)
                    for _ in range(args.n))
        print('%d Laeufe, Rang %d (%s), Spielerlevel %d, Gegner Lv %d, KI %s'
              % (args.n, args.arena, ARENA_THEMES[args.arena - 1], args.level,
                 arena_foe_level(args.arena, args.level), arena_ai(args.arena)))
        avg10 = sum(xs) * 10 // args.n
        print('Kaempfe fuer den Rang  Schnitt %d.%d  90 %% <= %d  max %d  (3 = perfekt)'
              % (avg10 // 10, avg10 % 10, xs[int(0.9 * len(xs))], xs[-1]))
        return 0
```

Und den Hilfetext von `--arena`:

```python
                    help='Arenarang 1-8 (7): drei Kaempfe ohne Zwischen'
                         'heilung. Der Rivale in 3/6/8 kommt aus --rival '
                         '(Vorgabe 4 = Glumanda)')
```
ersetzen durch
```python
                    help='Arenarang 1-8 (7, entspannt): wie viele Kaempfe '
                         'braucht man fuer alle drei Gegner, Fortschritt pro '
                         'Gegner, Mitleidsregel an')
```

Run: `python3 tools/battle_sim.py --self-test`
Expected: `Selbsttest OK` — damit sind auch Task 3 (Sackgassen) und Task 4 (Rivale) grün.

- [ ] **Step 4: Engine-Zwilling in C**

`battle.h`, den Arena-Block von `#define ARENA_RANKS 8` bis einschließlich der `arenaRun`-Deklaration ersetzen durch:

```c
#define ARENA_RANKS 8
// Drei Pokemon je Rang, nach gemessener Schwierigkeit sortiert: Wasser,
// Elektro, Pflanze, Gift, Gestein, Psycho, Kampf, Feuer. Kein Rivale, und
// kein Gegner, gegen den eine Spezies gar keinen Schaden machen kann -
// battle_sim.py --self-test prueft das fuer alle 151.
extern const uint16_t ARENA_TEAMS[ARENA_RANKS][3];

// rank ist 1-8. Gegnerlevel Spieler -2/-1/0, nie unter 1. KI 1-4 wild,
// 5-8 arena.
uint8_t arenaFoeLevel(uint8_t rank, uint8_t playerLevel);
uint8_t arenaFoeAi(uint8_t rank);
// Gegner idx (0-2) des Rangs, mit Mitleidsregel. Ein Arenakampf ist ein
// gewoehnlicher Kampf: volle HP, normale Kosten, normale XP.
void arenaFoe(Fighter &f, uint8_t rank, uint8_t idx, uint8_t playerLevel,
              uint8_t lossStreak);
```

`battle.cpp`, den Block von `// 7: Gestein, Wasser, Elektro, Pflanze, Gift, Psycho, Feuer, Boden.` bis einschließlich der schließenden `}` von `arenaRun` ersetzen durch:

```c
// 7 (entspannt): nach gemessener Schwierigkeit sortiert, leicht -> schwer.
const uint16_t ARENA_TEAMS[ARENA_RANKS][3] = {
  { 120, 118, 121 },  // Wasser: Sterndu, Goldini, Starmie
  { 100, 25, 101 },   // Elektro: Voltobal, Pikachu, Lektrobal
  { 114, 70, 45 },    // Pflanze: Tangela, Ultrigaria, Giflor
  { 109, 89, 110 },   // Gift: Smogon, Sleimok, Smogmog
  { 138, 140, 141 },  // Gestein: Amonitas, Kabuto, Kabutops
  { 64, 122, 97 },    // Psycho: Kadabra, Pantimos, Hypno
  { 57, 68, 106 },    // Kampf: Rasaff, Machomei, Kicklee
  { 58, 78, 59 },     // Feuer: Fukano, Gallopa, Arkani
};

static const int8_t ARENA_LEVEL_OFFSET[ARENA_RANKS] = { -2, -2, -1, -1, -1, 0, 0, 0 };

uint8_t arenaFoeLevel(uint8_t rank, uint8_t playerLevel) {
  int16_t l = (int16_t)playerLevel + ARENA_LEVEL_OFFSET[rank - 1];
  if (l < 1) l = 1;
  return l > LEVEL_CAP ? LEVEL_CAP : (uint8_t)l;
}

uint8_t arenaFoeAi(uint8_t rank) { return rank <= 4 ? AI_WILD : AI_ARENA; }

void arenaFoe(Fighter &f, uint8_t rank, uint8_t idx, uint8_t playerLevel,
              uint8_t lossStreak) {
  fighterFromDex(f, ARENA_TEAMS[rank - 1][idx],
                 pityLevel(arenaFoeLevel(rank, playerLevel), lossStreak), false);
}
```

- [ ] **Step 5: Fortschritt pro Gegner im Pet**

`pet.h`, nach `  uint8_t arenaRank = 0;`:

```c
  // 7 (entspannt): Gegner im laufenden Rang (arenaRank + 1), die schon
  // besiegt sind, 0-2. Fortschritt pro Gegner statt drei Siege am Stück.
  uint8_t arenaStep = 0;
```

`pet.h`, die Zeile
```c
  void setArenaRank(uint8_t r) { arenaRank = r > 8 ? 8 : r; save(); }  // Konsole
```
ersetzen durch
```c
  void setArenaRank(uint8_t r) { arenaRank = r > 8 ? 8 : r; arenaStep = 0; save(); }  // Konsole
  // 7: ein Arenagegner ist gefallen. Der dritte schliesst den Rang ab.
  void arenaFoeBeaten();
```

`pet.cpp`, direkt nach der schließenden `}` von `Pet::arenaWin`:

```c

void Pet::arenaFoeBeaten() {
  if (arenaRank >= 8) return;
  if (++arenaStep < 3) {
    save();
    return;
  }
  arenaStep = 0;
  arenaWin(arenaRank + 1);  // speichert selbst
}
```

`pet.cpp`, nach `  prefs.putUChar("arena", arenaRank);`:
```c
  prefs.putUChar("arstep", arenaStep);
```
und nach `  arenaRank = prefs.getUChar("arena", 0);`:
```c
  arenaStep = prefs.getUChar("arstep", 0);
  if (arenaStep > 2) arenaStep = 0;  // kaputter Wert: Rang neu beginnen
```

- [ ] **Step 6: Konsole**

`TamaPoke.ino`, die ganze Funktion `void arenaCmd() { … }` samt ihrem dreizeiligen Kommentar darüber ersetzen durch:

```c
// 7: Rang, Fortschritt und naechster Gegner, dazu dieser eine Kampf
// headless. Kaempft mit einer Kopie des Spielers - Pet, AP und Rang bleiben.
void arenaCmd() {
  Serial.printf("arenarang %u/8 schritt %u/3\n", pet.arenaRank, pet.arenaStep);
  if (pet.arenaRank >= ARENA_RANKS || pet.isEgg()) {
    Serial.println("DONE");
    return;
  }
  uint8_t rank = pet.arenaRank + 1;
  Fighter pl, fo;
  fighterFromPet(pl, pet);
  arenaFoe(fo, rank, pet.arenaStep, pl.level, pet.lossStreak);
  Serial.printf("rang %u gegner %u/3: %s Lv%u, ki %s\n", rank,
                pet.arenaStep + 1, DEX_TBL[fo.dex].name, fo.level,
                arenaFoeAi(rank) == AI_WILD ? "wild" : "arena");
  uint8_t rounds = 0;
  uint8_t res = battleRun(pl, fo, AI_ELITE, arenaFoeAi(rank), &rounds);
  Serial.printf("probekampf: %s nach %u runden\n",
                res == BR_WIN ? "WIN" : res == BR_LOSS ? "LOSS" : "DRAW", rounds);
  Serial.println("DONE");
}
```

- [ ] **Step 7: Bauen, gegenprüfen, Referenz**

Run: `tools\build.ps1` → Exitcode 0.
Gegenprobe: `python3 -c "print(open('build/battle/TamaPoke.ino.bin','rb').read().count(b'schritt %u/3'))"` → `1`
Run: `python3 tools/battle_sim.py --self-test` → `Selbsttest OK`
Referenzmessung → 53,2–59,2 %.
`git grep -n "arenaNextFight\|arenaRun\|run_arena\|simulate_arena\|arena_next_fight"` → **keine** Treffer.

- [ ] **Step 8: A13 in GERAETETEST ersetzen**

Den Abschnitt `## A13. Arena: Rang, Konsole, Medaille` bis vor `## A14.` ersetzen durch:

```markdown
## A13. Arena: Rang, Fortschritt pro Gegner, Medaille

Phase 7 (§7), entspannt, noch ohne eigenes Icon. Rang unter `arena`,
Fortschritt im laufenden Rang unter `arstep`, beides gehört dem Spieler.

1. **Altgerät:** hat das Gerät schon einen `arena`-Wert aus dem alten
   Teamsatz, zeigt `ARENA` ihn weiter als „so viele Ränge geschafft",
   `schritt 0/3`, kein Absturz.
2. `ARENA 0`, dann `ARENA` → `arenarang 0/8 schritt 0/3`, `rang 1 gegner 1/3:
   Sterndu Lv<Spieler−2>, ki wild`, dazu ein Probekampf. Nichts am Pet ändert
   sich (`STATS` vorher/nachher gleich).
3. `ARENA 4` → Rang 5 Gestein: `Amonitas`, Gegner auf Spieler −1, `ki arena`.
4. `ARENA 7` → Rang 8 Feuer: `Fukano` auf Spielerlevel.
5. Mit `pech=2` (zwei Niederlagen, siehe A14) zeigt `ARENA` den Gegner auf
   gut der Hälfte seines Levels.
6. Statuskarte Seite 4: `ARENA 7/8` bei y 284, bei Rang 0 grau.
7. Neustart → Rang und Schritt sind noch da. Generationswechsel (`BYE`,
   schlüpfen) → beide **noch da**.
8. `ARENA 0` zurücksetzen.

**Medaillenseite mit elf Medaillen:** zwei Spalten mal sechs Reihen, Kachel
180×32, letzte Reihe endet bei 332, engste Stelle 227,9 px vom Mittelpunkt.
Der Kopf zeigt `%u/11`.

Der echte Arenakampf auf dem Bildschirm, `arenaFoeBeaten()` und `MED_ARENA`
brauchen den Einstieg aus D6.
```

- [ ] **Step 9: Commit (Tasks 3, 4, 5 zusammen)**

```bash
git add battle.h battle.cpp pet.h pet.cpp TamaPoke.ino tools/battle_sim.py docs/GERAETETEST.md
git commit -m "Arena und Rivale entspannt: Fortschritt pro Gegner, keine Sackgassen" -m "Arena: jeder Kampf gewoehnlich mit vollen HP, Fortschritt pro Gegner, kein Rivale, Teams ohne Typ-Sackgassen (Pikachu und Tragosso waren in Rang 1/8 dauerhaft gesperrt), nach Schwierigkeit sortiert, Gegner Spieler -2/-1/0, KI wild/arena. Rivale auf Spielerlevel mit Arena-KI, Tag nur durch Sieg verbraucht. Selbsttest prueft Sackgassen fuer alle 151." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push origin main
```

---

### Task 6: Abnahmebericht und Spec

Ein Befehl, der die ganze „Chilligkeit" in Zahlen zeigt und gegen Ziele prüft — damit jede spätere Änderung sofort sieht, ob sie das Spiel wieder härter macht. Danach die Spec auf Stand.

**Ziele** (der Nutzer bestätigt sie mit diesem Plan; verfehlt → melden, nicht nachjustieren):

| Messung | Ziel |
|---|---|
| Levelkampf Lv 5/15/30/50: Versuche im Schnitt | ≤ 2,0 |
| Levelkampf: 90 % brauchen höchstens | ≤ 4 Versuche |
| Levelkampf erschöpft (Energie 10), Lv 30: Schnitt | ≤ 3,0 |
| Rivale Lv 30: Versuche im Schnitt | ≤ 3,0 |
| Arena, jeder Rang auf Lv 30: Kämpfe im Schnitt | ≤ 7,0 (3 = perfekt) |
| Arena: 90 % brauchen höchstens | ≤ 12 Kämpfe |
| Typ-Sackgassen in der Arena | 0 |

**Files:**
- Modify: `tools/battle_sim.py` (neue Funktion `chill_report`, CLI-Schalter `--entspannt`)
- Modify: `docs/BATTLE_SPEC.md`

**Interfaces:**
- Consumes: `pity_level`, `foe_level_range`, `pick_foe_level`, `rival_level`, `arena_rank_fights`, `arena_dead_ends`, `make_player`, `make_foe`, `make_rival`, `run_battle`, `AI_ARENA`, `AI_WILD`, `AI_ELITE`, `WILD_POOL`
- Produces: `python3 tools/battle_sim.py --entspannt` mit Exitcode 0 bei allen Zielen, sonst 1

- [ ] **Step 1: Bericht schreiben**

In `tools/battle_sim.py` direkt vor `def self_test():`:

```python
def _tries_until_win(make, rng, cap=30):
    """make(streak) -> (player, foe, ai), neu gewuerfelt pro Versuch."""
    for streak in range(cap):
        player, foe, ai = make(streak)
        if run_battle(player, foe, rng, AI_ELITE, ai)[0] == 'win':
            return streak + 1
    return cap


def _summary(xs):
    xs = sorted(xs)
    return sum(xs) / len(xs), xs[int(0.9 * len(xs))], xs[-1]


def chill_report(n=2000, seed=1):
    """Ist das Spiel entspannt? Prueft die Ziele aus dem Plan
    docs/superpowers/plans/2026-10-11-entspannter-kampf.md."""
    rng = random.Random(seed)
    ok = True

    def check(name, value, limit, fmt='%.2f'):
        nonlocal ok
        good = value <= limit
        ok = ok and good
        print('  %-44s ' % name + fmt % value + '   Ziel <= ' + fmt % limit
              + ('   OK' if good else '   VERFEHLT'))

    print('Levelkampf (Gegner neu pro Versuch, Mitleidsregel)')
    for lv, energy in ((5, 100), (15, 100), (30, 100), (50, 100), (30, 10)):
        xs = []
        for _ in range(n):
            pdex = rng.choice(WILD_POOL)
            def make(streak, pdex=pdex):
                foe_lv = pity_level(pick_foe_level(lv, rng, 2), streak)
                return (make_player(pdex, lv, rng, energy=energy),
                        make_foe(rng.choice(WILD_POOL), foe_lv), AI_WILD)
            xs.append(_tries_until_win(make, rng))
        avg, p90, worst = _summary(xs)
        tag = 'Lv %d%s' % (lv, ', erschoepft' if energy < 20 else '')
        check('%s: Versuche im Schnitt' % tag, avg, 3.0 if energy < 20 else 2.0)
        if energy >= 20:
            check('%s: 90 %% brauchen hoechstens' % tag, p90, 4, '%d')

    print('Rivale Lv 30 (frueheres Pokemon, Arena-KI)')
    xs = []
    for _ in range(n):
        pdex, rdex = rng.choice(WILD_POOL), rng.choice(WILD_POOL)
        genes = tuple(90 + rng.randrange(21) for _ in range(3))
        def make(streak, pdex=pdex, rdex=rdex, genes=genes):
            return (make_player(pdex, 30, rng),
                    make_rival(rdex, pity_level(rival_level(30), streak), genes),
                    AI_ARENA)
        xs.append(_tries_until_win(make, rng))
    check('Rivale: Versuche im Schnitt', _summary(xs)[0], 3.0)

    print('Arena Lv 30 (Kaempfe fuer den ganzen Rang, 3 = perfekt)')
    for rank in range(1, 9):
        xs = [arena_rank_fights(rng.choice(WILD_POOL), 30, rank, rng)
              for _ in range(n // 4)]
        avg, p90, worst = _summary(xs)
        check('Rang %d (%s): Kaempfe im Schnitt' % (rank, ARENA_THEMES[rank - 1]),
              avg, 7.0)
        check('Rang %d: 90 %% brauchen hoechstens' % rank, p90, 12, '%d')

    check('Typ-Sackgassen in der Arena', len(arena_dead_ends()), 0, '%d')
    print('ENTSPANNT' if ok else '!!! mindestens ein Ziel verfehlt - melden')
    return ok


```

In `main()` nach der `--self-test`-Option:

```python
    ap.add_argument('--entspannt', action='store_true',
                    help='Abnahmebericht: ist das Spiel entspannt?')
```

und nach dem Block `if args.self_test: … return 0`:

```python
    if args.entspannt:
        return 0 if chill_report() else 1
```

- [ ] **Step 2: Bericht laufen lassen**

Run: `python3 tools/battle_sim.py --entspannt`
Expected: jede Zeile `OK`, Schluss `ENTSPANNT`, Exitcode 0. Laufzeit einige Minuten.
**Verfehlt eine Zeile:** nicht nachjustieren. Ausgabe vollständig an den Nutzer melden, Plan hier anhalten.

- [ ] **Step 3: Selbsttest und Referenz**

Run: `python3 tools/battle_sim.py --self-test` → `Selbsttest OK`
Referenzmessung → 53,2–59,2 %.

- [ ] **Step 4: Spec nachziehen**

`docs/BATTLE_SPEC.md`, jeweils den bestehenden Absatz ersetzen:

- **§4.3:** statt der Formel `pct = 12 + 4 * (foeLevel - level())` →
  „Jeder gewonnene Kampf ohne offenes Level zahlt pauschal **12 %** von `lvlReq()` ein, rund acht Kämpfe pro Level. Unabhängig vom Gegnerlevel — schwächere Gegner und die Mitleidsregel dürfen das Leveln nicht verlangsamen."
- **§5.5:** „Der Rivale skaliert mit: sein Level ist immer `Spielerlevel + 2`." → „Der Rivale kämpft auf **Spielerlevel** mit der Arena-KI (§6.6)." Den Auftritt „als letzter Gegner der Arenaränge 3, 6 und 8" streichen. Ergänzen: „`rivalDay` wird nur durch einen **Sieg** gesetzt — nach einer Niederlage darf man sofort nochmal."
- **§6.3:** Formelblock ersetzen durch `gegnerLevel = Spielerlevel - 0..2   // nie darüber, Untergrenze 1`. Die Messreihe mit `--spread 2` (Korridor 45–65 %) als „vor dem Plan vom 2026-10-11" kennzeichnen.
- **§6.6:** „Arena Rang 1–4" → „Arena Rang 1–4: zufällige Attacke (wie wild)". „Arena Rang 5–8 und Rivale: immer die schadensstärkste Attacke …" → „Arena Rang 5–8 und Rivale: zu 60 % die Attacke mit dem besten Typvorteil, sonst zufällig." Die Elite-KI bleibt nur als Spielerverhalten im Simulator.
- **§6.7:** die Zeile „`lossStreak++`. Ab 3: Gegnerlevel −1 je weiterer Niederlage, bis maximal −4." ersetzen durch „`lossStreak++`. **Mitleidsregel:** jeder Gegner kommt auf `Level × (3/4)^lossStreak`, Untergrenze 1, ohne Deckel. Gilt für jeden Kampf. Ein Sieg setzt zurück."
- **§7:** ganzen Abschnitt durch die Fassung aus diesem Plan ersetzen: Tabelle der acht Ränge aus Task 5, „Jeder Arenakampf ist ein gewöhnlicher Kampf mit vollen HP, normalen Kosten und XP. Der Fortschritt wird **pro Gegner** gespeichert (`arenaStep`); wer verliert, tritt einfach wieder gegen denselben Gegner an. Kein Rivale in der Arena. Kein Gegner, gegen den eine Spezies keinen Schaden machen kann — `battle_sim.py --self-test` prüft das." Belohnung: +2/+3/+5 Trainingspunkte je nach Rang, `MED_ARENA` bei Rang 8. „Bessere Ei-Chance" und „Medaille" bei 6–7 streichen. `MED_COUNT` 11.
- **§8:** „Fluchtbutton nur bei freien Kämpfen, nicht in der Arena" → „Fluchtbutton in jedem Kampf. Flucht aus der Arena kostet wie jede Flucht, der Fortschritt bleibt."
- Neuer Absatz am Anfang von §6: „**Leitlinie (2026-10-11):** TamaPoke ist ein entspanntes Spiel. Kein Kampf darf zur Wand werden. Prüfstein ist `python3 tools/battle_sim.py --entspannt`."

- [ ] **Step 5: Commit**

```bash
git add tools/battle_sim.py docs/BATTLE_SPEC.md
git commit -m "Abnahmebericht --entspannt und Spec auf den entspannten Stand" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push origin main
```

- [ ] **Step 6: Bericht an den Nutzer**

Die vollständige Ausgabe von `--entspannt`, die Commits mit Flash-Größe, und was am Gerät offen ist (A13–A15, Einstiege B6/D6).

---

## Self-Review

**Spec-Abdeckung** (gegen die Richtungsentscheidung und die vier Ursachen):
- Ursache 1 Multiplikation → Task 5 (Fortschritt pro Gegner, volle HP). ✓
- Ursache 2 Sackgassen → Task 3 (Prüfung) + Task 5 (neue Teams, kein Rivale in der Arena). ✓
- Ursache 3 kein Sicherheitsnetz → Task 1 (Mitleidsregel, ohne Deckel). ✓
- Ursache 4 XP strafen schwache Gegner → Task 2 (pauschal 12 %). ✓
- „einfacher statt komplizierter" → entfernt: Zwischenheilungs-Logik, `arenaRun`, `arenaNextFight`, Rivale in der Arena, Fluchtverbot, Ei-Chance; nichts kommt hinzu außer `arenaStep`. ✓
- Rivale → Task 4. ✓ Spec → Task 6. ✓

**Platzhalter:** keine „TBD", jeder Code-Schritt hat Code, jede Prüfung einen Befehl und ein erwartetes Ergebnis.

**Typ-Konsistenz:** `pityLevel(uint8_t, uint8_t)` in Task 1 → benutzt in Task 5 `arenaFoe` mit `pet.lossStreak` (`uint8_t`). `arenaFoe(..., uint8_t lossStreak)` in `battle.h`, `battle.cpp`, `arenaCmd` gleich. `arena_dead_ends()` in Task 3 definiert, in Task 5 Selbsttest und Task 6 benutzt. `ARENA_TRY_CAP` in Task 5 definiert und im Selbsttest benutzt. `arena_rank_fights(pdex, level, rank, rng, berry, bond)` in Task 5 mit dieser Reihenfolge, in Task 6 mit `(pdex, 30, rank, rng)` aufgerufen. `RIVAL_AI` in Task 4 definiert, erst von B6 benutzt.

**Review Focus:** Altgerät-Rang (Task 5 Schritt 8, Punkt 1), Level 0 (Task 1 Schritt 1), Erschöpfungsspirale (Task 6 Zeile „erschöpft"), Level 100 (Task 2 Schleife bis 100, Task 5 `arena_foe_level(8, 100)`), Rivalen-Immunität (dokumentiert, Task 4).
