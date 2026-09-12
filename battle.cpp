#include "battle.h"

#include <Arduino.h>

// Kampf-Engine, Abschnitt 6 der Spezifikation. Siehe battle.h.
//
// Gen-1-Stufenmultiplikatoren als Bruch, damit stat * num / den reicht.
// Index ist stage + 6, also -6 .. +6.
static const uint8_t STAGE_NUM[13] = { 2, 2, 2, 2, 2, 2, 2, 3, 4, 5, 6, 7, 8 };
static const uint8_t STAGE_DEN[13] = { 8, 7, 6, 5, 4, 3, 2, 2, 2, 2, 2, 2, 2 };

static inline uint16_t applyStage(uint16_t v, int8_t stage) {
  if (stage < -6) stage = -6;
  if (stage > 6) stage = 6;
  uint32_t r = (uint32_t)v * STAGE_NUM[stage + 6] / STAGE_DEN[stage + 6];
  return r < 1 ? 1 : (uint16_t)r;
}

uint16_t fighterAtk(const Fighter &f) {
  uint32_t v = applyStage(f.atk, f.atkStage);
  if (f.exhausted) v = v * 75 / 100;  // 6.5: ENE < 20
  return v < 1 ? 1 : (uint16_t)v;
}

uint16_t fighterDef(const Fighter &f) {
  return applyStage(f.def, f.defStage);  // DEF bleibt von Erschoepfung frei
}

uint16_t fighterSpe(const Fighter &f) {
  uint32_t v = f.spe;
  if (f.status == ST_PARA) v = v * 75 / 100;  // Paralyse: -25 % SPD
  if (f.exhausted) v = v * 75 / 100;
  return v < 1 ? 1 : (uint16_t)v;
}

// --- Aufbau ---------------------------------------------------------------

uint16_t battleMaxHp(uint8_t baseHp, uint8_t geneAtk, uint8_t level) {
  return (uint16_t)(((uint32_t)baseHp * 2 + geneAtk) * level / 100 + level + 10);
}

static void fighterClearBattleState(Fighter &f) {
  f.status = ST_NONE;
  f.atkStage = 0;
  f.defStage = 0;
  f.hp = f.maxHp;
}

void fighterFromPet(Fighter &f, const Pet &p) {
  int16_t dex = p.speciesId < 1 ? 1 : p.speciesId;
  f.dex = (uint16_t)dex;
  f.level = p.level();
  f.type1 = DEX_TBL[dex].type1;
  f.type2 = DEX_TBL[dex].type2;
  f.maxHp = battleMaxHp(DEX_TBL[dex].bHp, p.geneAtk, f.level);
  f.atk = p.atkStat();
  f.def = p.defStat();
  f.spe = p.speStat();
  f.moveCount = movesForLevel(dex, f.level, f.moves);
  for (uint8_t i = 0; i < MOVE_SLOTS; i++)
    f.pp[i] = i < f.moveCount ? MOVE_TBL[f.moves[i]].maxPp : 0;
  f.bond = p.bond;
  f.berryLeft = p.berryKnown ? 1 : 0;
  f.endureLeft = 1;
  f.exhausted = p.energy < 20;
  f.isPlayer = true;
  f.shiny = p.shiny;
  f.isRival = false;
  fighterClearBattleState(f);
}

void fighterFromDex(Fighter &f, uint16_t dex, uint8_t level, bool shiny,
                    bool grudge) {
  if (dex < 1 || dex > DEX_COUNT) dex = 1;
  if (level < 1) level = 1;
  const DexEntry &de = DEX_TBL[dex];
  f.dex = dex;
  f.level = level;
  f.type1 = de.type1;
  f.type2 = de.type2;
  // 6.1: Gene fest auf 100 %, ausser beim Rivalen
  f.maxHp = battleMaxHp(de.bHp, 100, level);
  f.atk = (uint16_t)de.bAtk + level;
  f.def = (uint16_t)de.bDef + level;
  f.spe = (uint16_t)de.bSpe + level;
  if (grudge) f.atk = (uint16_t)((uint32_t)f.atk * 110 / 100);  // 5.5: Groll
  f.moveCount = movesForLevel(dex, level, f.moves);
  for (uint8_t i = 0; i < MOVE_SLOTS; i++)
    f.pp[i] = i < f.moveCount ? MOVE_TBL[f.moves[i]].maxPp : 0;
  f.bond = 0;
  f.berryLeft = 0;
  f.endureLeft = 0;  // die Bindung gehoert dem Spieler
  f.exhausted = false;
  f.isPlayer = false;
  f.shiny = shiny;
  f.isRival = grudge;
  fighterClearBattleState(f);
}

// 6.3: die Spanne schrumpft am Boden, statt unten abgeschnitten zu werden.
void foeLevelRange(uint8_t playerLevel, uint8_t spread, uint8_t *low,
                   uint8_t *high) {
  int16_t reach = (int16_t)spread;
  if (reach > playerLevel - 1) reach = playerLevel - 1;
  if (reach < 0) reach = 0;
  int16_t lo = (int16_t)playerLevel - reach;
  if (lo < 1) lo = 1;
  if (low) *low = (uint8_t)lo;
  if (high) *high = (uint8_t)(playerLevel + reach);
}

uint8_t pickFoeLevel(uint8_t playerLevel, uint8_t spread) {
  uint8_t lo, hi;
  foeLevelRange(playerLevel, spread, &lo, &hi);
  return hi == lo ? lo : (uint8_t)(lo + random(hi - lo + 1));
}

uint16_t pickWildDex(int8_t biome) {
  uint16_t cand[DEX_COUNT];
  uint16_t n = 0;
  for (uint16_t d = 1; d <= DEX_COUNT; d++) {
    if (DEX_TBL[d].rarity == R_LEGENDARIO) continue;  // 6.3: ausgeschlossen
    if (biome >= 0 && DEX_TBL[d].biome != (uint8_t)biome) continue;
    cand[n++] = d;
  }
  if (n == 0) return pickWildDex(-1);  // Biom leer: ganzer Dex
  return cand[random(n)];
}

// --- Schaden --------------------------------------------------------------

uint16_t battleDamage(const Fighter &a, const Fighter &d, uint8_t move,
                      uint8_t roll, bool crit) {
  const Move &m = MOVE_TBL[move];
  if (m.power == 0) return 0;

  uint32_t dmg = ((uint32_t)(2 * a.level / 5 + 2) * m.power * fighterAtk(a) /
                  fighterDef(d)) / 50 + 2;

  // STAB 3/2 bei Typuebereinstimmung, sonst 2/2
  uint8_t stab = (m.type == a.type1 || m.type == a.type2) ? 3 : 2;
  dmg = dmg * stab / 2;

  // Wirksamkeit in zwei Schritten, genau wie 6.4 es schreibt. NICHT ueber
  // typeMult() aus types.h: das kombiniert beide Typen und rundet erst am
  // Ende, was bei Doppeltypen andere Werte liefert als der Prototyp.
  dmg = dmg * TYPE_MULT_RAW(m.type, d.type1) / 2;
  if (d.type2 < TYPE_COUNT) dmg = dmg * TYPE_MULT_RAW(m.type, d.type2) / 2;

  // Bindungsbonus, max +20 %. Nur der Spieler; der Rivale hat stattdessen
  // seinen Groll-Bonus auf die ATK.
  if (a.isPlayer) dmg = dmg * (100 + a.bond / 5) / 100;

  dmg = dmg * roll / 255;
  if (crit) dmg *= 2;
  return dmg > 0xFFFF ? 0xFFFF : (uint16_t)dmg;
}

// --- KI -------------------------------------------------------------------

static uint8_t usableSlots(const Fighter &f, uint8_t out[MOVE_SLOTS]) {
  uint8_t n = 0;
  for (uint8_t i = 0; i < f.moveCount; i++)
    if (f.pp[i] > 0) out[n++] = i;
  return n;
}

// Schadensschaetzung ohne Zufall: mittlerer Wurf, kein Volltreffer
static uint16_t estimate(const Fighter &a, const Fighter &d, uint8_t move) {
  return battleDamage(a, d, move, 236, false);
}

int8_t battleChooseMove(const Fighter &user, const Fighter &foe, uint8_t ai) {
  uint8_t slots[MOVE_SLOTS];
  uint8_t n = usableSlots(user, slots);
  if (n == 0) return SLOT_STRUGGLE;

  if (ai == AI_WILD) return (int8_t)slots[random(n)];

  if (ai == AI_ARENA) {
    if (random(100) < 60) {
      uint8_t best = 0;
      for (uint8_t k = 0; k < n; k++) {
        uint8_t m = typeMult(MOVE_TBL[user.moves[slots[k]]].type, foe.type1,
                             foe.type2);
        if (m > best) best = m;
      }
      uint8_t top[MOVE_SLOTS], t = 0;
      for (uint8_t k = 0; k < n; k++)
        if (typeMult(MOVE_TBL[user.moves[slots[k]]].type, foe.type1,
                     foe.type2) == best)
          top[t++] = slots[k];
      return (int8_t)top[random(t)];
    }
    return (int8_t)slots[random(n)];
  }

  // AI_ELITE: Statusattacken solange der Gegner ueber 70 % HP hat, sonst
  // immer die schadensstaerkste Attacke.
  if ((uint32_t)foe.hp * 100 / foe.maxHp > 70) {
    for (uint8_t k = 0; k < n; k++) {
      uint8_t eff = MOVE_TBL[user.moves[slots[k]]].effect;
      // nur solange die Stufe sich noch bewegen kann, sonst dreht die KI
      // endlos Schwerttanz statt anzugreifen
      if (eff == 8 && user.atkStage < 6) return (int8_t)slots[k];
      if (eff == 7 && foe.defStage > -6) return (int8_t)slots[k];
    }
  }
  int8_t bestSlot = SLOT_STRUGGLE;
  uint16_t bestDmg = 0;
  for (uint8_t k = 0; k < n; k++) {
    uint8_t mv = user.moves[slots[k]];
    if (MOVE_TBL[mv].power == 0) continue;
    uint16_t e = estimate(user, foe, mv);
    if (bestSlot == SLOT_STRUGGLE || e > bestDmg) {
      bestDmg = e;
      bestSlot = (int8_t)slots[k];
    }
  }
  if (bestSlot == SLOT_STRUGGLE) return (int8_t)slots[random(n)];
  return bestSlot;
}

// --- Runde ----------------------------------------------------------------

static uint8_t critChance(uint8_t move) {
  // 4 %, mit Effekt 4 erhoehte Volltrefferquote (12,5 %). In Promille, damit
  // 12,5 % ohne Kommazahl darstellbar bleibt.
  return MOVE_TBL[move].effect == 4 ? 125 : 40;
}

static uint8_t multiHits() {
  // Gen-1-Verteilung fuer Effekt 5: 2 und 3 Treffer je 37,5 %, 4 und 5 je 12,5 %
  long r = random(8);
  if (r < 3) return 2;
  if (r < 6) return 3;
  return r == 6 ? 4 : 5;
}

// Nur ein Status gleichzeitig, wie in Gen 1. Sonst stapeln sich Gift und
// Brand und der Rundenschaden kippt das Balancing.
static bool applyStatus(Fighter &t, uint8_t kind, uint8_t chance) {
  if (t.status != ST_NONE || random(100) >= chance) return false;
  t.status = kind;
  return true;
}

// 6.5: K.-o.-Rettung durch Bindung, einmal pro Kampf, Chance bond / 3 Prozent
static bool survives(Fighter &t) {
  if (t.endureLeft == 0 || t.bond == 0) return false;
  if (random(100) >= t.bond / 3) return false;
  t.endureLeft--;
  return true;
}

// Eine Aktion. Schreibt das Ereignis und gibt true zurueck, wenn das Ziel faellt.
static bool takeTurn(Fighter &att, Fighter &def, int8_t slot, BattleEvent &e) {
  e.actor = att.isPlayer ? 0 : 1;
  e.damage = 0;
  e.effMult = 4;
  e.status = ST_NONE;
  e.crit = e.missed = e.skipped = e.endured = e.fainted = false;
  e.berry = e.stageOnly = false;

  uint8_t move;
  if (slot == SLOT_STRUGGLE) {
    move = MOVE_STRUGGLE;  // keine AP mehr: Verzweifler greift immer
  } else {
    move = att.moves[slot];
    att.pp[slot]--;
  }
  e.move = move;

  // Paralyse: 25 % Aussetzchance
  if (att.status == ST_PARA && random(100) < 25) {
    e.skipped = true;
    return false;
  }

  const Move &m = MOVE_TBL[move];
  if (random(100) >= m.accuracy) {
    e.missed = true;
    return false;
  }

  // reine Statusattacke (Stufenveraenderung, Staerke 0)
  if (m.power == 0) {
    e.stageOnly = true;
    if (m.effect == 7 && def.defStage > -6) def.defStage--;
    else if (m.effect == 8 && att.atkStage < 6) att.atkStage++;
    return false;
  }

  e.effMult = typeMult(m.type, def.type1, def.type2);
  uint8_t hits = m.effect == 5 ? multiHits() : 1;
  uint32_t total = 0;
  for (uint8_t h = 0; h < hits; h++) {
    if (def.hp == 0) break;
    bool crit = random(1000) < critChance(move);
    uint8_t roll = (uint8_t)(217 + random(39));
    uint16_t dmg = battleDamage(att, def, move, roll, crit);
    // Mindestschaden 1, damit eine Attacke nie voellig wirkungslos ist - aber
    // Immunitaet bleibt Immunitaet. Ohne die Ausnahme knabbert eine
    // 0x-Attacke pro Runde 1 HP ab und kann einen immunen Gegner ueber das
    // 30-Runden-Limit sogar besiegen. e.effMult ist genau dann 0, wenn einer
    // der beiden Chart-Faktoren 0 ist - da gibt es keine Rundungsfrage.
    if (dmg < 1 && e.effMult != 0) dmg = 1;
    if (crit) e.crit = true;
    total += dmg;
    if (dmg >= def.hp) {
      def.hp = 0;
      if (survives(def)) {
        def.hp = 1;
        e.endured = true;
      }
    } else {
      def.hp -= dmg;
    }
  }
  e.damage = total > 0xFFFF ? 0xFFFF : (uint16_t)total;

  // Nebenwirkungen
  switch (m.effect) {
    case 1: if (applyStatus(def, ST_PARA, 10)) e.status = ST_PARA; break;
    case 2: if (applyStatus(def, ST_BURN, 10)) e.status = ST_BURN; break;
    case 3: if (applyStatus(def, ST_POISON, 30)) e.status = ST_POISON; break;
    case 6: {  // Anwender heilt 50 % des zugefuegten Schadens
      uint32_t heal = att.hp + total / 2;
      att.hp = heal > att.maxHp ? att.maxHp : (uint16_t)heal;
      break;
    }
    case 7: if (def.defStage > -6) def.defStage--; break;
    case 8: if (att.atkStage < 6) att.atkStage++; break;
    default: break;
  }

  e.fainted = (def.hp == 0);
  return e.fainted;
}

// Rundenschaden durch Gift und Brand: je 1/16 der maximalen HP
static void endOfRound(Fighter &f) {
  if (f.hp == 0) return;
  if (f.status != ST_BURN && f.status != ST_POISON) return;
  uint16_t tick = f.maxHp / 16;
  if (tick < 1) tick = 1;
  f.hp = tick >= f.hp ? 0 : (uint16_t)(f.hp - tick);
}

static uint8_t outcome(const Fighter &pl, const Fighter &fo) {
  if (pl.hp > 0 && fo.hp == 0) return BR_WIN;
  if (pl.hp == 0 && fo.hp > 0) return BR_LOSS;
  if (pl.hp == 0 && fo.hp == 0) return BR_DRAW;  // beide gleichzeitig unten
  return BR_ONGOING;
}

uint8_t battleRound(Fighter &pl, Fighter &fo, int8_t plSlot, uint8_t foeAi,
                    BattleEvent ev[BATTLE_MAX_EVENTS], uint8_t *evCount) {
  uint8_t n = 0;
  int8_t foSlot = battleChooseMove(fo, pl, foeAi);

  // Die Beere kostet die Runde: heilt 50 % der maximalen HP (6.5)
  bool usedBerry = (plSlot == SLOT_BERRY && pl.berryLeft > 0);
  if (usedBerry) {
    pl.berryLeft--;
    uint32_t heal = pl.hp + pl.maxHp / 2;
    pl.hp = heal > pl.maxHp ? pl.maxHp : (uint16_t)heal;
    if (ev && n < BATTLE_MAX_EVENTS) {
      BattleEvent &e = ev[n++];
      e.actor = 0; e.move = 0; e.damage = 0; e.effMult = 4; e.status = ST_NONE;
      e.crit = e.missed = e.skipped = e.endured = e.fainted = false;
      e.stageOnly = false;
      e.berry = true;
    }
  }

  // Reihenfolge nach SPD, bei Gleichstand Zufall
  uint16_t ps = fighterSpe(pl), fs = fighterSpe(fo);
  bool playerFirst = ps > fs ? true : (ps < fs ? false : (random(2) == 0));

  for (uint8_t turn = 0; turn < 2; turn++) {
    bool playerActs = (turn == 0) == playerFirst;
    if (pl.hp == 0 || fo.hp == 0) break;
    if (playerActs) {
      if (usedBerry) continue;  // Beere war die Aktion
      BattleEvent tmp;
      takeTurn(pl, fo, plSlot, tmp);
      if (ev && n < BATTLE_MAX_EVENTS) ev[n++] = tmp;
    } else {
      BattleEvent tmp;
      takeTurn(fo, pl, foSlot, tmp);
      if (ev && n < BATTLE_MAX_EVENTS) ev[n++] = tmp;
    }
  }

  endOfRound(pl);
  endOfRound(fo);
  if (evCount) *evCount = n;
  return outcome(pl, fo);
}

uint8_t battleRun(Fighter &pl, Fighter &fo, uint8_t plAi, uint8_t foeAi,
                  uint8_t *rounds) {
  for (uint8_t r = 1; r <= BATTLE_MAX_ROUNDS; r++) {
    int8_t slot = battleChooseMove(pl, fo, plAi);
    uint8_t res = battleRound(pl, fo, slot, foeAi, nullptr, nullptr);
    if (res != BR_ONGOING) {
      if (rounds) *rounds = r;
      return res;
    }
  }
  if (rounds) *rounds = BATTLE_MAX_ROUNDS;
  // 30 Runden vorbei: es gewinnt, wer prozentual mehr HP uebrig hat
  uint32_t p = (uint32_t)pl.hp * 100 / pl.maxHp;
  uint32_t f = (uint32_t)fo.hp * 100 / fo.maxHp;
  if (p > f) return BR_WIN;
  if (p < f) return BR_LOSS;
  return BR_DRAW;
}
