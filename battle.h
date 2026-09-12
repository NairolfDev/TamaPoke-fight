#pragma once
#include <stdint.h>

#include "dex.h"
#include "moves.h"
#include "pet.h"
#include "types.h"

// Kampf-Engine nach docs/BATTLE_SPEC.md Abschnitt 6.
//
// Portiert aus tools/battle_sim.py. Die Formeln muessen dort und hier
// identisch rechnen: die Abnahme aus Abschnitt 10, Phase 3 vergleicht die
// Siegquote von BSIM auf dem Geraet mit der des Python-Prototyps.
//
// **Keine Rendering-Aufrufe in dieser Datei.** Die Engine laeuft headless
// ueber die serielle Konsole; die UI leitet ihre Texte und Animationen aus
// den BattleEvent-Feldern ab.
//
// Reine Integerarithmetik, kein Float. Zwischenergebnisse in uint32_t.

#define BATTLE_MAX_ROUNDS 30  // 6.4: kein Ausdauer-Patt auf einem Akkugeraet
#define BATTLE_MAX_EVENTS 4   // Beere + zwei Angriffe, plus Reserve

// KI-Stufen (6.6)
enum : uint8_t {
  AI_WILD,   // zufaellige Attacke mit AP > 0
  AI_ARENA,  // zu 60 % bester Typvorteil, sonst zufaellig
  AI_ELITE,  // staerkste Attacke; Statusattacken oberhalb 70 % HP
};

// Statuszustaende. Gelten nur bis Kampfende und werden nie persistiert -
// ein vergiftetes Pokemon darf das Pflegespiel nicht kaputtmachen (5.2).
enum : uint8_t { ST_NONE, ST_PARA, ST_BURN, ST_POISON };

// Ausgang aus Sicht des Spielers
enum : uint8_t { BR_ONGOING, BR_WIN, BR_LOSS, BR_DRAW };

// Slot-Sonderwerte fuer battleRound()
#define SLOT_STRUGGLE (-1)  // keine AP mehr: Verzweifler
#define SLOT_BERRY (-2)     // Lieblingsbeere statt Angriff (kostet die Runde)

struct Fighter {
  uint16_t dex;
  uint8_t level;
  uint8_t type1, type2;
  uint16_t maxHp, hp;
  uint16_t atk, def, spe;
  uint8_t moves[MOVE_SLOTS];
  uint8_t pp[MOVE_SLOTS];
  uint8_t moveCount;
  uint8_t status;
  int8_t atkStage, defStage;
  uint8_t bond;        // nur Spieler: Schadensbonus und K.-o.-Rettung
  uint8_t berryLeft;   // nur Spieler, nur wenn berryKnown
  uint8_t endureLeft;  // K.-o.-Rettung, einmal pro Kampf
  bool exhausted;      // ENE < 20: ATK und SPD -25 % (6.5)
  bool isPlayer;
  bool shiny;
  bool isRival;
};

// Was in einer Aktion passiert ist. Die Engine schreibt, die UI liest.
struct BattleEvent {
  uint8_t actor;    // 0 = Spieler, 1 = Gegner
  uint8_t move;     // benutzte Attacke
  uint16_t damage;  // Summe ueber alle Treffer der Aktion
  uint8_t effMult;  // Wirksamkeit als Zaehler ueber 4: 0,1,2,4,8,16
  uint8_t status;   // neu zugefuegter Status, sonst ST_NONE
  bool crit;
  bool missed;
  bool skipped;    // Paralyse-Aussetzer
  bool endured;    // Bindung hat den K. o. verhindert
  bool fainted;    // Ziel ist umgefallen
  bool berry;      // Beere benutzt, kein Angriff
  bool stageOnly;  // reine Statusattacke (Staerke 0)
};

// --- Aufbau ---------------------------------------------------------------

// 6.2: maxHp = ((bHp * 2 + geneAtk) * level) / 100 + level + 10.
// Ein eigenes HP-Gen gibt es nicht, geneAtk wird mitbenutzt.
uint16_t battleMaxHp(uint8_t baseHp, uint8_t geneAtk, uint8_t level);

// Spielerseite aus dem Pet: Werte kommen aus atkStat()/defStat()/speStat(),
// also inklusive Gene und Trainingspunkten.
void fighterFromPet(Fighter &f, const Pet &p);

// 6.1: Gegner mit Genen fest auf 100 %, Attacken aus dem Learnset seines
// Levels. grudge = weggelaufener Rivale, +10 % ATK (5.5).
void fighterFromDex(Fighter &f, uint16_t dex, uint8_t level, bool shiny,
                    bool grudge);

// 6.3: Gegnerlevel Spielerlevel +/- spread, Spanne schrumpft am Boden.
void foeLevelRange(uint8_t playerLevel, uint8_t spread, uint8_t *low,
                   uint8_t *high);
uint8_t pickFoeLevel(uint8_t playerLevel, uint8_t spread);

// 6.3: zufaellige nicht-legendaere Spezies. Mit biome >= 0 auf das Biom
// gefiltert, sonst aus dem ganzen Dex.
uint16_t pickWildDex(int8_t biome);

// --- Rechnen --------------------------------------------------------------

// 6.4: Schadensformel. roll ist 217..255, crit verdoppelt. Reine Funktion
// ohne Zufall, damit sie gegen den Python-Prototyp pruefbar bleibt.
uint16_t battleDamage(const Fighter &a, const Fighter &d, uint8_t move,
                      uint8_t roll, bool crit);

uint16_t fighterAtk(const Fighter &f);
uint16_t fighterDef(const Fighter &f);
uint16_t fighterSpe(const Fighter &f);

// 6.6: Slot-Index der gewaehlten Attacke, oder SLOT_STRUGGLE ohne AP.
int8_t battleChooseMove(const Fighter &user, const Fighter &foe, uint8_t ai);

// --- Ablauf ---------------------------------------------------------------

// Eine Runde: beide handeln in SPD-Reihenfolge, danach Rundenschaden.
// plSlot ist der Slot des Spielers, SLOT_STRUGGLE oder SLOT_BERRY.
// Gibt BR_ONGOING, BR_WIN, BR_LOSS oder BR_DRAW zurueck.
uint8_t battleRound(Fighter &pl, Fighter &fo, int8_t plSlot, uint8_t foeAi,
                    BattleEvent ev[BATTLE_MAX_EVENTS], uint8_t *evCount);

// Ganzer Kampf ohne UI, fuer BSIM. rounds darf 0 sein.
uint8_t battleRun(Fighter &pl, Fighter &fo, uint8_t plAi, uint8_t foeAi,
                  uint8_t *rounds);
