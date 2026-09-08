#!/usr/bin/env python3
"""Genera moves.h (ataques + movepools) para el firmware.

  python3 tools/gen_moves.py

Fuentes: tools/move_data.py y tools/move_names.py (de gen_move_data.py).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from move_data import MOVES, LEARNSETS, PREVO
from move_names import MOVE_NAMES

LANG_ORDER = ('ES', 'EN', 'FR', 'DE', 'IT', 'PT')  # orden de Lang en i18n.h


def main():
    o = []
    o.append('#pragma once\n#include <stdint.h>\n#include "i18n.h"  // gLang\n'
             '#include "types.h"\n\n')
    o.append('// GENERADO por tools/gen_moves.py desde tools/move_data.py - no editar\n\n')
    o.append(f'#define MOVE_COUNT {len(MOVES)}\n')
    o.append('#define MOVE_SLOTS 4  // huecos de ataque por bicho\n')
    o.append('#define MOVE_STRUGGLE 1  // ultimo recurso: sin AP o sin movepool\n\n')

    o.append(
        '// efecto: 0 ninguno | 1 paralisis 10% | 2 quemadura 10% | 3 veneno 30%\n'
        '// 4 mas criticos | 5 golpes multiples | 6 drena 50% | 7 baja DEF rival\n'
        '// 8 sube ATK propio. Ver docs/BATTLE_SPEC.md 5.2.\n')
    o.append('struct Move {\n'
             '  uint8_t type;\n'
             '  uint8_t power;      // 0 = ataque de estado\n'
             '  uint8_t accuracy;   // 0-100\n'
             '  uint8_t maxPp;\n'
             '  uint8_t effect;\n'
             '};\n\n')

    o.append('static const Move MOVE_TBL[MOVE_COUNT + 1] = {\n')
    o.append('  { T_NORMAL, 0, 0, 0, 0 },  // 0: hueco vacio\n')
    for mid in sorted(MOVES):
        slug, tipo, pw, acc, pp, eff = MOVES[mid]
        o.append(f'  {{ T_{tipo.upper()}, {pw}, {acc}, {pp}, {eff} }},'
                 f'  // {mid} {slug}\n')
    o.append('};\n\n')

    # nombres: PT no existe en PokeAPI, reutiliza el ingles
    for lg in ('ES', 'EN', 'FR', 'DE', 'IT'):
        li = LANG_ORDER.index(lg)
        o.append(f'static const char *const MOVE_NAME_{lg}[MOVE_COUNT + 1] = {{\n')
        o.append('  "",\n')
        for mid in sorted(MOVES):
            o.append(f'  "{MOVE_NAMES[mid][li]}",\n')
        o.append('};\n')
    o.append('\n// PT no tiene nombres propios en PokeAPI: usa los ingleses.\n')
    o.append('static const char *const *const MOVE_NAMES_BY_LANG[LANG_COUNT] = {\n'
             '  MOVE_NAME_ES, MOVE_NAME_EN, MOVE_NAME_FR,\n'
             '  MOVE_NAME_DE, MOVE_NAME_IT, MOVE_NAME_EN,\n'
             '};\n\n')

    # movepools aplanados: un solo array + indice por especie
    plano, off = [], [0]
    for num in range(1, 152):
        for lv, mid in LEARNSETS[num]:
            plano.append((min(lv, 255), mid))
        off.append(len(plano))

    o.append('struct LearnEntry { uint8_t level, move; };\n\n')
    o.append(f'// {len(plano)} pares (nivel, ataque) de las 151, seguidos\n')
    o.append(f'static const LearnEntry LEARN_ALL[{len(plano)}] = {{\n')
    for i in range(0, len(plano), 6):
        fila = ', '.join('{%d,%d}' % p for p in plano[i:i + 6])
        o.append(f'  {fila},\n')
    o.append('};\n\n')
    o.append('// LEARN_OFF[dex] .. LEARN_OFF[dex+1] delimita el movepool de esa especie\n')
    o.append(f'static const uint16_t LEARN_OFF[DEX_COUNT + 2] = {{\n')
    off_full = [0] + off  # indice 0 sin usar, igual que DEX_TBL
    for i in range(0, len(off_full), 12):
        o.append('  ' + ', '.join(str(v) for v in off_full[i:i + 12]) + ',\n')
    o.append('};\n\n')

    o.append('// especie de la que evoluciona cada una (0 = forma base)\n')
    o.append('static const uint8_t MOVE_PREVO[DEX_COUNT + 1] = {\n  0,\n')
    pv = [PREVO.get(n, 0) for n in range(1, 152)]
    for i in range(0, len(pv), 12):
        o.append('  ' + ', '.join(str(v) for v in pv[i:i + 12]) + ',\n')
    o.append('};\n\n')

    o.append(
        'static inline const char *moveName(uint8_t id) {\n'
        '  if (id > MOVE_COUNT) return "";\n'
        '  return MOVE_NAMES_BY_LANG[gLang][id];\n'
        '}\n\n')
    o.append(
        '// Los cuatro ataques mas recientes que la especie sabe a ese nivel.\n'
        '// Rellena out[] con 0 en los huecos libres y devuelve cuantos hay.\n'
        'static inline uint8_t movesForLevel(int16_t dex, uint8_t level,\n'
        '                                    uint8_t out[MOVE_SLOTS]) {\n'
        '  for (uint8_t i = 0; i < MOVE_SLOTS; i++) out[i] = 0;\n'
        '  if (dex < 1 || dex > DEX_COUNT) return 0;\n'
        '  uint8_t n = 0;\n'
        '  // sube por la cadena evolutiva: al evolucionar se conservan los\n'
        '  // ataques, asi que un Dragoran tambien cuenta con los de Dratini\n'
        '  for (int16_t sp = dex; sp >= 1 && n < MOVE_SLOTS; sp = MOVE_PREVO[sp]) {\n'
        '    // de atras adelante: el movepool esta ordenado por nivel\n'
        '    for (uint16_t i = LEARN_OFF[sp + 1]; i > LEARN_OFF[sp] && n < MOVE_SLOTS; ) {\n'
        '      i--;\n'
        '      if (LEARN_ALL[i].level > level) continue;\n'
        '      bool dup = false;\n'
        '      for (uint8_t k = 0; k < n; k++)\n'
        '        if (out[k] == LEARN_ALL[i].move) { dup = true; break; }\n'
        '      if (!dup) out[n++] = LEARN_ALL[i].move;\n'
        '    }\n'
        '    if (MOVE_PREVO[sp] == 0) break;\n'
        '  }\n'
        '  if (n == 0) { out[0] = MOVE_STRUGGLE; return 1; }\n'
        '\n'
        '  // Garantiza al menos un ataque del tipo propio (STAB). Sin esto, un\n'
        '  // Pikachu de nivel alto pelea solo con ataques normales.\n'
        '  uint8_t t1 = DEX_TBL[dex].type1, t2 = DEX_TBL[dex].type2;\n'
        '  bool tiene = false;\n'
        '  for (uint8_t k = 0; k < n; k++)\n'
        '    if (MOVE_TBL[out[k]].type == t1 || MOVE_TBL[out[k]].type == t2) tiene = true;\n'
        '  if (!tiene) {\n'
        '    uint8_t mejor = 0;\n'
        '    for (int16_t sp = dex; sp >= 1; sp = MOVE_PREVO[sp]) {\n'
        '      for (uint16_t i = LEARN_OFF[sp]; i < LEARN_OFF[sp + 1]; i++) {\n'
        '        uint8_t m = LEARN_ALL[i].move;\n'
        '        if (LEARN_ALL[i].level > level) continue;\n'
        '        if (MOVE_TBL[m].type != t1 && MOVE_TBL[m].type != t2) continue;\n'
        '        if (MOVE_TBL[m].power > MOVE_TBL[mejor].power) mejor = m;\n'
        '      }\n'
        '      if (MOVE_PREVO[sp] == 0) break;\n'
        '    }\n'
        '    if (mejor) {\n'
        '      uint8_t flojo = 0;  // sacrifica el mas debil de los elegidos\n'
        '      for (uint8_t k = 1; k < n; k++)\n'
        '        if (MOVE_TBL[out[k]].power < MOVE_TBL[out[flojo]].power) flojo = k;\n'
        '      out[n < MOVE_SLOTS ? n++ : flojo] = mejor;\n'
        '    }\n'
        '  }\n'
        '  return n;\n'
        '}\n\n')
    o.append(
        '// Ataque que toca aprender justo a ese nivel (0 = ninguno).\n'
        'static inline uint8_t newMoveAt(int16_t dex, uint8_t level) {\n'
        '  if (dex < 1 || dex > DEX_COUNT) return 0;\n'
        '  for (uint16_t i = LEARN_OFF[dex]; i < LEARN_OFF[dex + 1]; i++)\n'
        '    if (LEARN_ALL[i].level == level) return LEARN_ALL[i].move;\n'
        '  return 0;\n'
        '}\n')

    path = os.path.join(os.path.dirname(__file__), '..', 'moves.h')
    open(path, 'w').write(''.join(o))
    print(f'guardado {os.path.normpath(path)} '
          f'({len(MOVES)} ataques, {len(plano)} entradas de movepool)')


if __name__ == '__main__':
    main()
