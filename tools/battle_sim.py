#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 3 - Kampf-Engine als Python-Prototyp (BATTLE_SPEC.md Abschnitt 6).

Bildet die Engine nach, bevor es battle.h / battle.cpp gibt: Schadensformel,
Rundenablauf, die drei KI-Stufen, Bindungsbonus, K.-o.-Rettung und
Erschoepfungsmalus.

Alle Rechnungen laufen wie spaeter auf dem ESP32 in reiner Integerarithmetik.
Im Kampfpfad kommt kein einziger Float vor - auch die Prozentangaben der
Auswertung werden in Zehnteln ganzzahlig gerechnet. Damit wandern die Formeln
1:1 nach C++, ohne dass sich das Ergebnis verschiebt.

    python3 tools/battle_sim.py --n 1000 --level 25
"""

import argparse
import random
import sys

from dex_data import LEGENDARY
from dex_stats import BASE_STATS
from move_data import LEARNSETS, MOVES, PREVO
from type_chart import CHART, GHOST_BUG_OVERRIDE, TYPES
from type_data import SPECIES_TYPES

# --------------------------------------------------------------------------
# Typen (BATTLE_SPEC 5.1)
# --------------------------------------------------------------------------

TYPE_ID = {name: i for i, name in enumerate(TYPES)}

# 1 = historischer Rot/Blau-Bug (Geist gegen Psycho 0x), 0 = korrigiert.
# Gegenstueck zu GEN1_GHOST_BUG in types.h.
GEN1_GHOST_BUG = 0


def _build_chart():
    """Wirksamkeitstabelle als uint8: 0 = 0x, 1 = 1/2x, 2 = 1x, 4 = 2x.

    Die Floats aus type_chart.py werden hier einmalig beim Laden kodiert.
    Ab dann rechnet die Engine nur noch mit (dmg * chart) / 2.
    """
    encode = {0.0: 0, 0.5: 1, 1.0: 2, 2.0: 4}
    table = [[2] * len(TYPES) for _ in TYPES]
    for attacker, row in CHART.items():
        for defender, mult in row.items():
            table[TYPE_ID[attacker]][TYPE_ID[defender]] = encode[mult]
    if GEN1_GHOST_BUG:
        att, dfn, mult = GHOST_BUG_OVERRIDE
        table[TYPE_ID[att]][TYPE_ID[dfn]] = encode[mult]
    return table


TYPE_CHART = _build_chart()

# Gen-1-Stufenmultiplikatoren als Bruch (Zaehler, Nenner), damit
# stat * num // den reicht und keine Kommazahl noetig ist.
STAGE = {
    -6: (2, 8), -5: (2, 7), -4: (2, 6), -3: (2, 5), -2: (2, 4), -1: (2, 3),
    0: (2, 2),
    1: (3, 2), 2: (4, 2), 3: (5, 2), 4: (6, 2), 5: (7, 2), 6: (8, 2),
}

MOVE_STRUGGLE = 1   # immer verfuegbar, auch ohne AP (siehe PHASE_1_2.md)
MOVE_SLOTS = 4
MAX_ROUNDS = 30     # 6.4: kein Ausdauer-Patt auf einem Akkugeraet

# Statuszustaende - gelten nur bis Kampfende, nichts davon wird persistiert.
ST_NONE, ST_PARA, ST_BURN, ST_POISON = 0, 1, 2, 3


def species_types(dex):
    """Typ-IDs einer Spezies; type2 ist None bei Einzeltypen."""
    t1, t2 = SPECIES_TYPES[dex]
    return TYPE_ID[t1], (TYPE_ID[t2] if t2 else None)


def move_type(move_id):
    return TYPE_ID[MOVES[move_id][1]]


def move_power(move_id):
    return MOVES[move_id][2]


# --------------------------------------------------------------------------
# Movepool (Nachbau von movesForLevel() aus moves.h)
# --------------------------------------------------------------------------

def moves_for_level(dex, level):
    """Bis zu vier zuletzt lernbare Attacken auf oder unter dem Level.

    Laeuft die Entwicklungskette rueckwaerts - bei der Entwicklung bleiben
    die Attacken erhalten, sonst stuende Dragoran ohne Drachenattacke da.
    """
    out = []
    sp = dex
    while sp >= 1 and len(out) < MOVE_SLOTS:
        # von hinten nach vorn: das Learnset ist nach Level sortiert
        for lvl, move in reversed(LEARNSETS.get(sp, [])):
            if len(out) >= MOVE_SLOTS:
                break
            if lvl > level or move in out:
                continue
            out.append(move)
        if PREVO[sp] == 0:
            break
        sp = PREVO[sp]

    if not out:
        return [MOVE_STRUGGLE]

    # STAB-Garantie: ohne Attacke des eigenen Typs kaempft z. B. Pikachu
    # nur mit Normal-Attacken.
    t1, t2 = species_types(dex)
    if not any(move_type(m) in (t1, t2) for m in out):
        best = 0
        sp = dex
        while sp >= 1:
            for lvl, move in LEARNSETS.get(sp, []):
                if lvl > level or move_type(move) not in (t1, t2):
                    continue
                if move_power(move) > (move_power(best) if best else 0):
                    best = move
            if PREVO[sp] == 0:
                break
            sp = PREVO[sp]
        if best:
            if len(out) < MOVE_SLOTS:
                out.append(best)
            else:
                # opfert die schwaechste der gewaehlten Attacken
                weakest = min(range(len(out)), key=lambda k: move_power(out[k]))
                out[weakest] = best
    return out


# --------------------------------------------------------------------------
# Kaempfer (BATTLE_SPEC 6.1, 6.2)
# --------------------------------------------------------------------------

class Combatant:
    """Spieler-Pokemon oder Gegner. Werte wie in pet.cpp bzw. Foe."""

    def __init__(self, dex, level, genes=(100, 100, 100),
                 training=(0, 0, 0), bond=0, energy=100,
                 berry_known=False, grudge=False, is_player=False):
        self.dex = dex
        self.level = level
        self.is_player = is_player
        self.bond = bond
        self.type1, self.type2 = species_types(dex)

        base_hp, base_atk, base_def, base_spe = BASE_STATS[dex]
        gene_atk, gene_def, gene_spe = genes
        tr_atk, tr_def, tr_spe = training

        # calcStat() aus pet.cpp: base * gene / 100 + level + training
        self.atk = base_atk * gene_atk // 100 + level + tr_atk
        self.dfn = base_def * gene_def // 100 + level + tr_def
        self.spe = base_spe * gene_spe // 100 + level + tr_spe

        # 6.2: an Gen 1 angelehnt, ohne EV-Term. Ein eigenes HP-Gen gibt es
        # nicht, deshalb wird geneAtk mitbenutzt.
        self.max_hp = (base_hp * 2 + gene_atk) * level // 100 + level + 10
        self.hp = self.max_hp

        # 5.5: weggelaufene Rivalen kommen mit +10 % ATK zurueck. Groll.
        if grudge:
            self.atk = self.atk * 110 // 100

        self.moves = moves_for_level(dex, level)
        self.pp = [MOVES[m][4] for m in self.moves]

        # 6.5: unter ENE 20 gelten ATK und SPD mit -25 %. Kein hartes Verbot.
        self.exhausted = energy < 20

        self.status = ST_NONE
        self.atk_stage = 0
        self.def_stage = 0
        self.berry_left = 1 if (is_player and berry_known) else 0
        self.endure_left = 1 if is_player else 0   # K.-o.-Rettung, 1x pro Kampf

    # -- effektive Werte ---------------------------------------------------

    def eff_atk(self):
        num, den = STAGE[self.atk_stage]
        value = self.atk * num // den
        if self.exhausted:
            value = value * 75 // 100
        return max(1, value)

    def eff_def(self):
        num, den = STAGE[self.def_stage]
        return max(1, self.dfn * num // den)

    def eff_spe(self):
        value = self.spe
        if self.status == ST_PARA:
            value = value * 75 // 100   # Paralyse: -25 % SPD
        if self.exhausted:
            value = value * 75 // 100
        return max(1, value)

    def hp_pct(self):
        return self.hp * 100 // self.max_hp

    def alive(self):
        return self.hp > 0

    def usable_slots(self):
        return [i for i in range(len(self.moves)) if self.pp[i] > 0]


# --------------------------------------------------------------------------
# Schaden (BATTLE_SPEC 6.4)
# --------------------------------------------------------------------------

def compute_damage(attacker, defender, move, roll, crit):
    """Schadensformel. `roll` ist 217..255, `crit` verdoppelt.

    Bewusst als reine Funktion: kein RNG darin, damit sie testbar bleibt.
    Zwischenergebnisse passen in uint32 - genau wie spaeter in C++.
    """
    mtype = move_type(move)
    power = move_power(move)
    if power == 0:
        return 0

    dmg = ((2 * attacker.level // 5 + 2) * power
           * attacker.eff_atk() // defender.eff_def()) // 50 + 2

    stab = 3 if mtype in (attacker.type1, attacker.type2) else 2
    dmg = dmg * stab // 2

    dmg = dmg * TYPE_CHART[mtype][defender.type1] // 2
    if defender.type2 is not None:
        dmg = dmg * TYPE_CHART[mtype][defender.type2] // 2

    # Bindungsbonus, max +20 %. Gilt nur fuer den Spieler; der Rivale hat
    # stattdessen seinen Groll-Bonus auf die ATK.
    if attacker.is_player:
        dmg = dmg * (100 + attacker.bond // 5) // 100

    dmg = dmg * roll // 255
    if crit:
        dmg *= 2
    return dmg


def effectiveness(move, defender):
    """Wirksamkeit als Produkt der Chart-Werte (4 = neutral, kodiert)."""
    mtype = move_type(move)
    value = TYPE_CHART[mtype][defender.type1] * 2
    if defender.type2 is not None:
        value = value * TYPE_CHART[mtype][defender.type2] // 2
    return value


# --------------------------------------------------------------------------
# Gegner-KI (BATTLE_SPEC 6.6)
# --------------------------------------------------------------------------

AI_WILD, AI_ARENA, AI_ELITE = 'wild', 'arena', 'elite'


def _estimate(attacker, defender, move):
    """Schadensschaetzung ohne Zufall: mittlerer Wurf, kein Volltreffer."""
    return compute_damage(attacker, defender, move, 236, False)


def choose_move(user, foe, ai, rng):
    """Liefert den Slot-Index oder None fuer Verzweifler (keine AP mehr)."""
    slots = user.usable_slots()
    if not slots:
        return None

    if ai == AI_WILD:
        # zufaellige Attacke mit AP > 0
        return rng.choice(slots)

    if ai == AI_ARENA:
        # zu 60 % die Attacke mit dem besten Typvorteil, sonst zufaellig
        if rng.randrange(100) < 60:
            best = max(effectiveness(user.moves[i], foe) for i in slots)
            top = [i for i in slots
                   if effectiveness(user.moves[i], foe) == best]
            return rng.choice(top)
        return rng.choice(slots)

    # AI_ELITE: immer die schadensstaerkste Attacke; Statusattacken, solange
    # der Gegner ueber 70 % HP hat.
    if foe.hp_pct() > 70:
        for i in slots:
            effect = MOVES[user.moves[i]][5]
            # nur solange die Stufe sich noch bewegen kann - sonst dreht die
            # KI endlos Schwerttanz, statt anzugreifen
            if effect == 8 and user.atk_stage < 6:
                return i
            if effect == 7 and foe.def_stage > -6:
                return i
    attacking = [i for i in slots if move_power(user.moves[i]) > 0]
    if not attacking:
        return rng.choice(slots)
    return max(attacking, key=lambda i: _estimate(user, foe, user.moves[i]))


# --------------------------------------------------------------------------
# Rundenablauf (BATTLE_SPEC 6.4, 6.5)
# --------------------------------------------------------------------------

def _name(c):
    return 'SPIELER' if c.is_player else 'GEGNER'


def _crit_chance(move):
    # 4 %, mit Effekt 4 erhoehte Volltrefferquote (12,5 %). In Promille,
    # damit 12,5 % ohne Kommazahl darstellbar bleibt.
    return 125 if MOVES[move][5] == 4 else 40


def _multi_hits(rng):
    # Gen-1-Verteilung fuer Effekt 5: 2 und 3 Treffer je 37,5 %,
    # 4 und 5 Treffer je 12,5 %.
    r = rng.randrange(8)
    if r < 3:
        return 2
    if r < 6:
        return 3
    return 4 if r == 6 else 5


def _apply_status(target, kind, rng, chance, log):
    # Nur ein Status gleichzeitig, wie in Gen 1. Sonst stapeln sich Gift und
    # Brand und der Rundenschaden kippt das Balancing.
    if target.status != ST_NONE or rng.randrange(100) >= chance:
        return
    target.status = kind
    if log is not None:
        name = {ST_PARA: 'PARALYSIERT', ST_BURN: 'VERBRANNT',
                ST_POISON: 'VERGIFTET'}[kind]
        log.append('  %s WURDE %s' % (_name(target), name))


def _survives(target, rng, log):
    """K.-o.-Rettung durch Bindung: 1x pro Kampf, Chance bond / 3 Prozent."""
    if target.endure_left <= 0 or target.bond <= 0:
        return False
    if rng.randrange(100) >= target.bond // 3:
        return False
    target.endure_left -= 1
    if log is not None:
        log.append('  %s HAELT DURCH!' % _name(target))
    return True


def take_turn(attacker, defender, slot, rng, log):
    """Ein Angriff. Gibt True zurueck, wenn der Verteidiger K. o. geht."""
    if slot is None:
        move = MOVE_STRUGGLE   # keine AP mehr: Verzweifler greift immer
    else:
        move = attacker.moves[slot]
        attacker.pp[slot] -= 1

    # Paralyse: 25 % Aussetzchance
    if attacker.status == ST_PARA and rng.randrange(100) < 25:
        if log is not None:
            log.append('  %s IST PARALYSIERT UND SETZT AUS' % _name(attacker))
        return False

    slug, _, power, accuracy, _, effect = MOVES[move]
    if log is not None:
        log.append('  %s SETZT %s EIN' % (_name(attacker), slug.upper()))

    if rng.randrange(100) >= accuracy:
        if log is not None:
            log.append('  DANEBEN')
        return False

    # reine Statusattacke (Stufenveraenderung, Staerke 0)
    if power == 0:
        if effect == 7:
            defender.def_stage = max(-6, defender.def_stage - 1)
        elif effect == 8:
            attacker.atk_stage = min(6, attacker.atk_stage + 1)
        if log is not None:
            log.append('  STUFE VERAENDERT')
        return False

    hits = _multi_hits(rng) if effect == 5 else 1
    total = 0
    for _ in range(hits):
        if not defender.alive():
            break
        crit = rng.randrange(1000) < _crit_chance(move)
        roll = 217 + rng.randrange(39)
        dmg = max(1, compute_damage(attacker, defender, move, roll, crit))
        total += dmg
        if log is not None and crit:
            log.append('  VOLLTREFFER!')
        defender.hp -= dmg
        if defender.hp <= 0 and _survives(defender, rng, log):
            defender.hp = 1

    if log is not None:
        eff = effectiveness(move, defender)
        if eff == 0:
            log.append('  KEIN EFFEKT')
        elif eff > 4:
            log.append('  SEHR EFFEKTIV!')
        elif eff < 4:
            log.append('  NICHT SEHR EFFEKTIV')
        log.append('  %d SCHADEN (%d/%d)'
                   % (total, max(0, defender.hp), defender.max_hp))

    # Nebenwirkungen
    if effect == 1:
        _apply_status(defender, ST_PARA, rng, 10, log)
    elif effect == 2:
        _apply_status(defender, ST_BURN, rng, 10, log)
    elif effect == 3:
        _apply_status(defender, ST_POISON, rng, 30, log)
    elif effect == 6:
        # Anwender heilt 50 % des zugefuegten Schadens
        attacker.hp = min(attacker.max_hp, attacker.hp + total // 2)
    elif effect == 7:
        defender.def_stage = max(-6, defender.def_stage - 1)
    elif effect == 8:
        attacker.atk_stage = min(6, attacker.atk_stage + 1)

    return not defender.alive()


def _end_of_round(c, log):
    """Rundenschaden durch Gift und Brand: je 1/16 der maximalen HP."""
    if c.status in (ST_BURN, ST_POISON) and c.alive():
        c.hp -= max(1, c.max_hp // 16)
        if log is not None:
            log.append('  %s LEIDET (%d/%d)'
                       % (_name(c), max(0, c.hp), c.max_hp))


def _wants_berry(c):
    # Lieblingsbeere: einmal pro Kampf, heilt 50 % der maximalen HP.
    # ponytail: feste Schwelle statt Bewertungsfunktion - reicht fuer den
    # Prototyp; in der UI entscheidet ohnehin der Spieler selbst.
    return c.berry_left > 0 and c.hp_pct() < 30


def run_battle(player, foe, rng, player_ai=AI_ELITE, foe_ai=AI_ELITE,
               log=None):
    """Fuehrt einen Kampf aus. Liefert ('win'|'loss'|'draw', Rundenzahl)
    aus Sicht des Spielers."""
    for rnd in range(1, MAX_ROUNDS + 1):
        if log is not None:
            log.append('RUNDE %d' % rnd)

        # 1. beide waehlen
        player_berry = _wants_berry(player)
        p_slot = None if player_berry else choose_move(player, foe,
                                                       player_ai, rng)
        f_slot = choose_move(foe, player, foe_ai, rng)

        if player_berry:
            player.berry_left -= 1
            player.hp = min(player.max_hp, player.hp + player.max_hp // 2)
            if log is not None:
                log.append('  BEERE: %d/%d' % (player.hp, player.max_hp))

        # 2. Reihenfolge nach SPD, bei Gleichstand Zufall
        p_spe, f_spe = player.eff_spe(), foe.eff_spe()
        if p_spe > f_spe:
            player_first = True
        elif p_spe < f_spe:
            player_first = False
        else:
            player_first = rng.randrange(2) == 0

        order = [(player, foe, p_slot), (foe, player, f_slot)]
        if not player_first:
            order.reverse()

        # 3./4. Trefferwurf und Schaden
        for attacker, defender, slot in order:
            if not attacker.alive() or not defender.alive():
                continue
            if attacker is player and player_berry:
                continue   # die Beere kostet die Runde
            take_turn(attacker, defender, slot, rng, log)

        # 5. Rundenschaden am Rundenende
        for c in (player, foe):
            _end_of_round(c, log)

        # 6. bei HP 0 ist der Kampf vorbei
        if not player.alive() or not foe.alive():
            if player.alive():
                return 'win', rnd
            if foe.alive():
                return 'loss', rnd
            return 'draw', rnd   # beide gleichzeitig unten

    # 30 Runden vorbei: es gewinnt, wer prozentual mehr HP uebrig hat
    p, f = player.hp_pct(), foe.hp_pct()
    if p > f:
        return 'win', MAX_ROUNDS
    if p < f:
        return 'loss', MAX_ROUNDS
    return 'draw', MAX_ROUNDS


# --------------------------------------------------------------------------
# Simulation
# --------------------------------------------------------------------------

# 6.3: Legendaere sind als Gegner ausgeschlossen.
WILD_POOL = [n for n in sorted(BASE_STATS) if n not in LEGENDARY]

# 6.3: Gegnerlevel ist Spielerlevel +/- spread. Nahe am Boden *schrumpft* die
# Spanne, statt unten abgeschnitten zu werden:
#
#     spread = min(FOE_LEVEL_SPREAD, spielerLevel - 1)
#
# Eine abgeschnittene Spanne bleibt oben stehen und verschiebt das mittlere
# Gegnerlevel nach oben - genau das machte das fruehe Spiel unnoetig hart.
# Eine schrumpfende Spanne bleibt auf jedem Level symmetrisch um das
# Spielerlevel. Harte Untergrenze ist 1.
FOE_LEVEL_SPREAD = 2


def foe_level_range(player_level, spread=FOE_LEVEL_SPREAD):
    """Untere und obere Grenze des Gegnerlevels nach 6.3."""
    reach = max(0, min(spread, player_level - 1))
    # durch reach <= spielerLevel - 1 liegt low nie unter 1
    return max(1, player_level - reach), player_level + reach


def pick_foe_level(player_level, rng, spread=FOE_LEVEL_SPREAD):
    low, high = foe_level_range(player_level, spread)
    return low if high == low else low + rng.randrange(high - low + 1)


def make_player(dex, level, rng, bond=0, energy=100, berry=False):
    # Gene wie in pet.cpp beim Schluepfen: 90 + random(21)
    genes = tuple(90 + rng.randrange(21) for _ in range(3))
    return Combatant(dex, level, genes=genes, bond=bond, energy=energy,
                     berry_known=berry, is_player=True)


def make_foe(dex, level, grudge=False):
    # 6.1: Gene fest auf 100 %, ausser beim Rivalen. Das Level waehlt der
    # Aufrufer ueber pick_foe_level() - hier wird nichts mehr abgefangen.
    return Combatant(dex, level, genes=(100, 100, 100), grudge=grudge)


def simulate(n, level, rng, bond=0, energy=100, berry=False,
             player_ai=AI_ELITE, foe_ai=AI_ELITE, player_dex=None,
             foe_dex=None, spread=0):
    """spread 0 = gleichstufige Gegner, wie die Abnahme aus Phase 10 es
    verlangt. spread 2 ist die echte Begegnung aus 6.3."""
    tally = {'win': 0, 'loss': 0, 'draw': 0}
    rounds_total = 0
    timeouts = 0
    for _ in range(n):
        pdex = player_dex or rng.choice(WILD_POOL)
        fdex = foe_dex or rng.choice(WILD_POOL)
        player = make_player(pdex, level, rng, bond, energy, berry)
        foe = make_foe(fdex, pick_foe_level(level, rng, spread))
        result, rnds = run_battle(player, foe, rng, player_ai, foe_ai)
        tally[result] += 1
        rounds_total += rnds
        if rnds >= MAX_ROUNDS:
            timeouts += 1
    return tally, rounds_total, timeouts


def _pct10(part, whole):
    """Prozent in Zehnteln - haelt auch die Auswertung ganzzahlig."""
    return part * 1000 // whole if whole else 0


def _fmt(part, whole):
    p = _pct10(part, whole)
    return '%d.%d %%' % (p // 10, p % 10)


# --------------------------------------------------------------------------
# Selbsttest
# --------------------------------------------------------------------------

def self_test():
    """Kleinster Satz Pruefungen, der bei kaputter Logik fehlschlaegt."""
    # Typentabelle: Gen-1-Eigenheiten
    assert TYPE_CHART[TYPE_ID['bug']][TYPE_ID['poison']] == 4, 'Kaefer->Gift'
    assert TYPE_CHART[TYPE_ID['poison']][TYPE_ID['bug']] == 4, 'Gift->Kaefer'
    assert TYPE_CHART[TYPE_ID['ghost']][TYPE_ID['normal']] == 0
    assert TYPE_CHART[TYPE_ID['normal']][TYPE_ID['ghost']] == 0
    assert TYPE_CHART[TYPE_ID['electric']][TYPE_ID['ground']] == 0
    assert TYPE_CHART[TYPE_ID['ghost']][TYPE_ID['psychic']] == 4, 'Bug gefixt'

    # Schadensformel von Hand nachgerechnet: Level 25, Staerke 100,
    # ATK == DEF, neutral, kein Bindungsbonus, Wurf 255:
    # (2*25/5+2) = 12 -> *100 = 1200 -> *atk/def -> /50 = 24 -> +2 = 26
    a = Combatant(19, 25)                       # Rattfratz, Normal
    d = Combatant(19, 25)
    a.atk = 100
    d.dfn = 100
    assert compute_damage(a, d, 47, 255, False) == 26 * 3 // 2, 'STAB'
    a.type1, a.type2 = TYPE_ID['water'], None   # STAB weg
    assert compute_damage(a, d, 47, 255, False) == 26
    assert compute_damage(a, d, 47, 255, True) == 52, 'Volltreffer'
    assert compute_damage(a, d, 47, 217, False) == 26 * 217 // 255

    # Bindungsbonus: +20 % bei voller Bindung, und nur fuer den Spieler
    a.is_player, a.bond = True, 100
    assert compute_damage(a, d, 47, 255, False) == 26 * 120 // 100
    a.is_player = False
    assert compute_damage(a, d, 47, 255, False) == 26

    # Typwirksamkeit schlaegt durch: Wasser gegen Gestein/Boden = 4x
    onix = Combatant(95, 25)
    assert effectiveness(101, onix) == 16, 'water -> rock/ground'

    # HP-Formel, 6.2
    p = Combatant(1, 25, genes=(100, 100, 100))
    assert p.max_hp == (45 * 2 + 100) * 25 // 100 + 25 + 10

    # Movepool: leeres Learnset erbt aus der Kette, Ditto faellt auf
    # Verzweifler zurueck, Pikachu bekommt garantiert seinen STAB.
    assert moves_for_level(11, 10) == [73], 'Metapod erbt von Raupy'
    assert moves_for_level(132, 50) == [MOVE_STRUGGLE], 'Ditto'
    assert any(move_type(m) == TYPE_ID['electric']
               for m in moves_for_level(25, 25)), 'STAB-Garantie'
    for dex in BASE_STATS:
        assert moves_for_level(dex, 100), 'Spezies ohne Attacke: %d' % dex
        assert len(moves_for_level(dex, 100)) <= MOVE_SLOTS

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
    for lv in (3, 10, 50):
        low, high = foe_level_range(lv)
        rng = random.Random(lv)
        assert all(low <= pick_foe_level(lv, rng) <= high for _ in range(200))

    # Erschoepfung: ATK und SPD -25 %, DEF bleibt unberuehrt
    tired = Combatant(1, 25, energy=10)
    fit = Combatant(1, 25, energy=100)
    assert tired.eff_atk() == fit.eff_atk() * 75 // 100
    assert tired.eff_spe() == fit.eff_spe() * 75 // 100
    assert tired.eff_def() == fit.eff_def()

    # Stufen: +2 verdoppelt die ATK, -2 halbiert die DEF
    c = Combatant(1, 25)
    base_atk, base_def = c.eff_atk(), c.eff_def()
    c.atk_stage, c.def_stage = 2, -2
    assert c.eff_atk() == base_atk * 2
    assert c.eff_def() == base_def * 2 // 4

    # K.-o.-Rettung: ohne Bindung nie, und hoechstens einmal pro Kampf
    rng = random.Random(1)
    assert not _survives(Combatant(1, 25, bond=0, is_player=True), rng, None)
    saved = Combatant(1, 25, bond=99, is_player=True)
    saved.endure_left = 0
    assert not _survives(saved, rng, None), 'nur 1x pro Kampf'

    # Der Rivalen-Groll gibt +10 % ATK
    plain = Combatant(4, 25)
    angry = Combatant(4, 25, grudge=True)
    assert angry.atk == plain.atk * 110 // 100

    # Ein Kampf laeuft durch und endet mit gueltigem Ergebnis
    rng = random.Random(7)
    res, rnds = run_battle(make_player(1, 25, rng), make_foe(4, 25), rng)
    assert res in ('win', 'loss', 'draw') and 1 <= rnds <= MAX_ROUNDS

    # Alle drei KI-Stufen liefern einen benutzbaren Slot
    for ai in (AI_WILD, AI_ARENA, AI_ELITE):
        user, foe = Combatant(6, 30), Combatant(3, 30)
        assert choose_move(user, foe, ai, random.Random(3)) in range(
            len(user.moves))
    # ohne AP bleibt nur der Verzweifler
    empty = Combatant(6, 30)
    empty.pp = [0] * len(empty.pp)
    assert choose_move(empty, Combatant(3, 30), AI_ELITE,
                       random.Random(3)) is None

    print('Selbsttest OK')


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Kampfsimulator zu BATTLE_SPEC.md Abschnitt 6')
    ap.add_argument('--n', type=int, default=1000, help='Anzahl Kaempfe')
    ap.add_argument('--level', type=int, default=25, help='Level beider Seiten')
    ap.add_argument('--seed', type=int, default=None, help='Zufallssaat')
    ap.add_argument('--bond', type=int, default=0, help='Bindung 0-100')
    ap.add_argument('--energy', type=int, default=100,
                    help='Energie des Spielers (< 20 = erschoepft)')
    ap.add_argument('--berry', action='store_true',
                    help='Lieblingsbeere ist bekannt')
    # Standard ist der wilde Gegner: in Phase 3 gibt es nur freie Kaempfe,
    # Arena und Rivale kommen erst in Phase 7 bzw. 6. Der Spieler waehlt
    # dagegen wie jemand, der die Typentabelle kennt.
    ap.add_argument('--ai', choices=[AI_WILD, AI_ARENA, AI_ELITE],
                    default=AI_WILD, help='KI-Stufe des Gegners')
    ap.add_argument('--player-ai', choices=[AI_WILD, AI_ARENA, AI_ELITE],
                    default=AI_ELITE, help='Spielerverhalten')
    ap.add_argument('--player-dex', type=int, default=None,
                    help='feste Spezies des Spielers (sonst zufaellig)')
    ap.add_argument('--foe-dex', type=int, default=None,
                    help='feste Spezies des Gegners (sonst zufaellig)')
    # 0 haelt die Abnahme aus Phase 10 gleichstufig, 2 ist die echte
    # Begegnungsspanne aus 6.3.
    ap.add_argument('--spread', type=int, default=0,
                    help='Gegnerlevel Spielerlevel +/- N (0 = gleichstufig, '
                         '2 = Begegnung nach 6.3)')
    ap.add_argument('--verbose', action='store_true',
                    help='einen einzelnen Kampf mitschreiben')
    ap.add_argument('--self-test', action='store_true')
    args = ap.parse_args(argv)

    if args.self_test:
        self_test()
        return 0

    rng = random.Random(args.seed)

    if args.verbose:
        pdex = args.player_dex or rng.choice(WILD_POOL)
        fdex = args.foe_dex or rng.choice(WILD_POOL)
        player = make_player(pdex, args.level, rng, args.bond, args.energy,
                             args.berry)
        foe = make_foe(fdex, pick_foe_level(args.level, rng, args.spread))
        log = []
        result, rnds = run_battle(player, foe, rng, args.player_ai, args.ai,
                                  log)
        print('Dex %d Lv %d (%d HP) gegen Dex %d Lv %d (%d HP)'
              % (pdex, player.level, player.max_hp,
                 fdex, foe.level, foe.max_hp))
        print('\n'.join(log))
        print('Ergebnis: %s nach %d Runden' % (result, rnds))
        return 0

    tally, rounds_total, timeouts = simulate(
        args.n, args.level, rng, bond=args.bond, energy=args.energy,
        berry=args.berry, player_ai=args.player_ai, foe_ai=args.ai,
        player_dex=args.player_dex, foe_dex=args.foe_dex, spread=args.spread)

    n = args.n
    low, high = foe_level_range(args.level, args.spread)
    scope = ('gleichstufig' if low == high == args.level
             else 'Gegnerlevel %d-%d' % (low, high))
    print('%d Kaempfe, Level %d, %s (KI: %s)'
          % (n, args.level, scope, args.ai))
    print('Siege       %5d   %s' % (tally['win'], _fmt(tally['win'], n)))
    print('Niederlagen %5d   %s' % (tally['loss'], _fmt(tally['loss'], n)))
    print('Unentsch.   %5d   %s' % (tally['draw'], _fmt(tally['draw'], n)))
    avg10 = rounds_total * 10 // n
    print('Runden      %5d.%d im Schnitt, %s am Zeitlimit'
          % (avg10 // 10, avg10 % 10, _fmt(timeouts, n)))

    rate = _pct10(tally['win'], n)
    ok = 450 <= rate <= 650
    print('Abnahme 45-65 %%: %s' % ('OK' if ok else 'VERFEHLT'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
