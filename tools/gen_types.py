#!/usr/bin/env python3
"""Genera types.h (tipos gen 1 + tabla de eficacia) para el firmware.

  python3 tools/gen_types.py

Fuentes: tools/type_chart.py (a mano) y tools/type_data.py (de PokeAPI).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from type_chart import TYPES, ACCENTS, NAMES, CHART, GHOST_BUG_OVERRIDE

# Lang de i18n.h: ES, EN, FR, DE, IT, PT
LANG_ORDER = ('ES', 'EN', 'FR', 'DE', 'IT', 'PT')

# codificacion entera de la tabla: se multiplica y se divide entre 2, asi que
# no hace falta coma flotante en el micro.
CODE = {0.0: 0, 0.5: 1, 1.0: 2, 2.0: 4}


def rgb565(hexcol):
    r, g, b = int(hexcol[1:3], 16), int(hexcol[3:5], 16), int(hexcol[5:7], 16)
    return (r >> 3) << 11 | (g >> 2) << 5 | (b >> 3)


def main():
    o = []
    o.append('#pragma once\n#include <stdint.h>\n#include "i18n.h"  // gLang\n\n')
    o.append('// GENERADO por tools/gen_types.py desde tools/type_chart.py - no editar\n\n')
    o.append(f'#define TYPE_COUNT {len(TYPES)}\n\n')

    o.append('enum : uint8_t {\n')
    for i in range(0, len(TYPES), 4):
        fila = ', '.join('T_' + t.upper() for t in TYPES[i:i + 4])
        o.append(f'  {fila},\n')
    o.append('  T_NONE = 255,  // segundo tipo ausente\n};\n\n')

    o.append(
        '// En rojo/azul, fantasma contra psiquico era 0x por un fallo del juego\n'
        '// original (deberia ser 2x). 0 = corregido, 1 = bug historico.\n'
        '#define GEN1_GHOST_BUG 0\n\n')

    o.append(
        '// Eficacia codificada: 0 = x0, 1 = x0.5, 2 = x1, 4 = x2.\n'
        '// Se aplica como (dmg * TYPE_CHART[atacante][defensor]) / 2, sin floats.\n')
    o.append('static const uint8_t TYPE_CHART[TYPE_COUNT][TYPE_COUNT] = {\n')
    for atk in TYPES:
        fila = []
        for dfn in TYPES:
            mult = CHART.get(atk, {}).get(dfn, 1.0)
            fila.append(str(CODE[mult]))
        o.append('  { %s },  // %s\n' % (', '.join(fila), atk))
    o.append('};\n\n')

    ga, gd, gv = GHOST_BUG_OVERRIDE
    o.append('#if GEN1_GHOST_BUG\n')
    o.append(f'// bug original: {ga} -> {gd} sin efecto\n')
    o.append(f'#define TYPE_MULT_RAW(a, d) \\\n'
             f'  (((a) == T_{ga.upper()} && (d) == T_{gd.upper()}) ? {CODE[gv]} : TYPE_CHART[a][d])\n')
    o.append('#else\n')
    o.append('#define TYPE_MULT_RAW(a, d) TYPE_CHART[a][d]\n')
    o.append('#endif\n\n')

    o.append('// color de acento por tipo (RGB565), para nombre y botones de ataque\n')
    o.append('static const uint16_t TYPE_ACCENT[TYPE_COUNT] = {\n')
    for i in range(0, len(TYPES), 4):
        fila = ', '.join('0x%04X' % rgb565(ACCENTS[t]) for t in TYPES[i:i + 4])
        o.append(f'  {fila},\n')
    o.append('};\n\n')

    o.append('// nombre del tipo por idioma\n')
    for li, lg in enumerate(LANG_ORDER):
        o.append(f'static const char *const TYPE_NAME_{lg}[TYPE_COUNT] = {{\n')
        for i in range(0, len(TYPES), 3):
            fila = ', '.join('"%s"' % NAMES[t][li] for t in TYPES[i:i + 3])
            o.append(f'  {fila},\n')
        o.append('};\n')
    o.append('\n')
    o.append('static const char *const *const TYPE_NAMES[LANG_COUNT] = {\n  %s,\n};\n\n'
             % ', '.join('TYPE_NAME_' + lg for lg in LANG_ORDER))

    o.append(
        'static inline const char *typeName(uint8_t t) {\n'
        '  if (t >= TYPE_COUNT) return "";\n'
        '  return TYPE_NAMES[gLang][t];\n'
        '}\n\n')
    o.append(
        '// Multiplicador combinado contra un defensor de uno o dos tipos.\n'
        '// Devuelve el numerador de una fraccion sobre 4: 0, 1, 2, 4, 8 o 16\n'
        '// (x0, x0.25, x0.5, x1, x2, x4). Aplicar como (dmg * m) / 4.\n'
        'static inline uint8_t typeMult(uint8_t atk, uint8_t d1, uint8_t d2) {\n'
        '  if (atk >= TYPE_COUNT || d1 >= TYPE_COUNT) return 4;\n'
        '  uint16_t m = TYPE_MULT_RAW(atk, d1) * 2;  // x2 -> base 4\n'
        '  if (d2 < TYPE_COUNT) m = (m * TYPE_MULT_RAW(atk, d2)) / 2;\n'
        '  return (uint8_t)m;\n'
        '}\n')

    path = os.path.join(os.path.dirname(__file__), '..', 'types.h')
    open(path, 'w').write(''.join(o))
    print(f'guardado {os.path.normpath(path)} ({len(TYPES)} tipos)')


if __name__ == '__main__':
    main()
